# === Sample data generation (self-contained; reads the installed catalog) ===
"""Generate realistic sample rows for a model that has just been installed.

Source of truth is the INSTALLED CATALOG, not a model file: columns, primary keys
and foreign keys are read back from `information_schema`, which is what the install
phases just wrote. Nothing here depends on the modelling agent.

Referential integrity holds by construction rather than by repair:

    pass 1  every table's primary-key values are generated first, each table in its own
            disjoint value block. A table whose own key contains a foreign key (an order
            line keyed by order_id, line_no) borrows that part from its parent, so pass 1
            visits parents first; ordinary foreign keys impose no order.
    pass 2  every other column is filled; a foreign-key column draws from the pool of
            keys pass 1 already produced for its parent table
    pass 3  the in-memory rows are asserted (unique keys, every foreign key present in
            its parent's key pool, no null in a NOT NULL column) and only then written

Because keys exist before references are filled, an ordinary foreign-key cycle between
two tables is not a special case.

Values come from a deterministic, seeded, name-and-type aware generator. When an LLM
endpoint is reachable it is asked once per table for domain-realistic pools for the
free-text columns; any failure silently falls back to the deterministic generator, so
the LLM can improve realism but can never break a run or its reproducibility.
"""
import datetime
import decimal
import json
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

SAMPLE_ROW_CHOICES = ["5", "10", "20", "50", "100"]
SAMPLE_INTERNAL_SCHEMAS = ("information_schema", "_metrics", "_install", "_metamodel", "default")
SAMPLE_SEED = 20260801
SAMPLE_MAX_LLM_COLUMNS = 12
SAMPLE_LLM_TIMEOUT_S = 90        # per-table budget for the optional realism pass
SAMPLE_LLM_MAX_ENDPOINT_ERRORS = 3   # transient failures tolerated before giving up


# --------------------------------------------------------------------------------------
# resolved configuration
# --------------------------------------------------------------------------------------

def resolve_sample_config(wget):
    """Read the sample widgets/params through the installer's safe getter."""
    enabled = str(wget("generate_samples", "No")).strip().lower() in ("yes", "true", "1")
    raw_rows = str(wget("sample_rows", "10")).strip()
    rows = int(raw_rows) if raw_rows.isdigit() and int(raw_rows) > 0 else 10
    return {
        "enabled": enabled,
        "rows": rows,
        "seed": int(str(wget("sample_seed", str(SAMPLE_SEED))).strip() or SAMPLE_SEED),
        "threads": max(1, int(str(wget("sample_threads", "8")).strip() or 8)),
        "llm": str(wget("sample_llm", "true")).strip().lower() == "true",
        "llm_endpoints": [e.strip() for e in str(
            wget("sample_llm_endpoints",
                 "databricks-gpt-oss-120b,databricks-meta-llama-3-3-70b-instruct")
        ).split(",") if e.strip()],
    }


# --------------------------------------------------------------------------------------
# the installed model, read back from information_schema
# --------------------------------------------------------------------------------------

class SampleEntity(object):
    """One physical table plus the key metadata needed to populate it."""

    __slots__ = ("catalog", "schema", "table", "columns", "pk", "fks", "keys", "rows")

    def __init__(self, catalog, schema, table):
        self.catalog = catalog
        self.schema = schema
        self.table = table
        self.columns = []      # [{name, type, nullable, position}] in ordinal order
        self.pk = []           # primary-key column names, in key order
        self.fks = []          # [{columns: [...], parent: fqn, parent_columns: [...]}]
        self.keys = []         # pass-1 key tuples, one per row
        self.rows = []         # pass-2 assembled rows

    @property
    def fqn(self):
        return "%s.%s.%s" % (self.catalog, self.schema, self.table)

    @property
    def quoted(self):
        return "`%s`.`%s`.`%s`" % (self.catalog, self.schema, self.table)

    def column(self, name):
        for c in self.columns:
            if c["name"] == name:
                return c
        return None

    def fk_for_column(self, name):
        for fk in self.fks:
            if name in fk["columns"]:
                return fk
        return None


def _rows_of(result):
    """Spark Rows -> plain tuples, so the readers work against any Row implementation."""
    return [tuple(r) for r in result.collect()]


def _sample_read_catalog(spark, catalog, entities):
    """Add every base table of one catalog (columns + PK + FK) into `entities`."""
    skip = ", ".join("'%s'" % s for s in SAMPLE_INTERNAL_SCHEMAS)
    col_rows = _rows_of(spark.sql("""
        SELECT c.table_schema, c.table_name, c.column_name, c.full_data_type,
               c.is_nullable, c.ordinal_position
        FROM `%s`.information_schema.columns c
        JOIN `%s`.information_schema.tables t
          ON t.table_schema = c.table_schema AND t.table_name = c.table_name
        WHERE c.table_schema NOT IN (%s) AND t.table_type <> 'VIEW'
        ORDER BY c.table_schema, c.table_name, c.ordinal_position
    """ % (catalog, catalog, skip)))
    for schema, table, column, dtype, nullable, position in col_rows:
        key = "%s.%s.%s" % (catalog, schema, table)
        ent = entities.get(key)
        if ent is None:
            ent = entities[key] = SampleEntity(catalog, schema, table)
        ent.columns.append({
            "name": column,
            "type": (dtype or "STRING").strip(),
            "nullable": str(nullable).upper() in ("YES", "TRUE"),
            "position": int(position or 0),
        })

    pk_rows = _rows_of(spark.sql("""
        SELECT k.table_schema, k.table_name, k.column_name, k.ordinal_position
        FROM `%s`.information_schema.table_constraints tc
        JOIN `%s`.information_schema.key_column_usage k
          ON tc.constraint_schema = k.constraint_schema
         AND tc.constraint_name = k.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
        ORDER BY k.table_schema, k.table_name, k.ordinal_position
    """ % (catalog, catalog)))
    for schema, table, column, _pos in pk_rows:
        ent = entities.get("%s.%s.%s" % (catalog, schema, table))
        if ent is not None and column not in ent.pk:
            ent.pk.append(column)

    # referential_constraints maps a foreign key to the parent's UNIQUE/PRIMARY KEY
    # constraint, and key_column_usage lists the ordered columns of either side, so
    # matching on ordinal_position pairs child column to parent column.
    #
    # constraint_column_usage is deliberately NOT used: its constraint_schema is the
    # REFERENCED table's schema, not the schema owning the foreign key, so correlating
    # the two silently loses every cross-schema foreign key (338 of 506 on the
    # restaurants model, which then wrote unresolvable references).
    fk_rows = _rows_of(spark.sql("""
        SELECT rc.constraint_schema, rc.constraint_name,
               ck.table_schema, ck.table_name, ck.column_name, ck.ordinal_position,
               pk.table_catalog, pk.table_schema, pk.table_name, pk.column_name
        FROM `%s`.information_schema.referential_constraints rc
        JOIN `%s`.information_schema.key_column_usage ck
          ON ck.constraint_catalog = rc.constraint_catalog
         AND ck.constraint_schema = rc.constraint_schema
         AND ck.constraint_name = rc.constraint_name
        JOIN `%s`.information_schema.key_column_usage pk
          ON pk.constraint_catalog = rc.unique_constraint_catalog
         AND pk.constraint_schema = rc.unique_constraint_schema
         AND pk.constraint_name = rc.unique_constraint_name
         AND pk.ordinal_position = ck.ordinal_position
        ORDER BY rc.constraint_schema, rc.constraint_name, ck.ordinal_position
    """ % (catalog, catalog, catalog)))
    grouped = {}
    for (cschema, cname, schema, table, column, _pos,
         pcat, pschema, ptable, pcolumn) in fk_rows:
        slot = grouped.setdefault(
            (cschema, cname), {"columns": [], "parent_columns": [], "child": (schema, table),
                               "parent": "%s.%s.%s" % (pcat, pschema, ptable)})
        slot["columns"].append(column)
        slot["parent_columns"].append(pcolumn)
    for slot in grouped.values():
        schema, table = slot.pop("child")
        ent = entities.get("%s.%s.%s" % (catalog, schema, table))
        if ent is not None:
            ent.fks.append(slot)


def read_installed_model(spark, catalogs, log=None):
    """Read every installed base table across the target catalogs."""
    entities = {}
    for catalog in catalogs:
        try:
            _sample_read_catalog(spark, catalog, entities)
        except Exception as err:
            if log:
                log("  sample: could not read catalog `%s` (%s)" % (catalog, str(err)[:160]))
    for ent in entities.values():
        ent.columns.sort(key=lambda c: c["position"])
    if log:
        n_fk = sum(len(e.fks) for e in entities.values())
        n_pk = sum(1 for e in entities.values() if e.pk)
        log("  sample: %d table(s), %d with a primary key, %d foreign key(s)"
            % (len(entities), n_pk, n_fk))
    return entities


# --------------------------------------------------------------------------------------
# type helpers
# --------------------------------------------------------------------------------------

_DECIMAL_RE = re.compile(r"(?:DECIMAL|NUMERIC)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)
_INT_CEILINGS = (("TINYINT", 127), ("SMALLINT", 32767), ("BYTE", 127), ("SHORT", 32767))


def _decimal_precision(dtype):
    m = _DECIMAL_RE.search(dtype or "")
    if m:
        return int(m.group(1)), int(m.group(2))
    return 38, 0 if "DECIMAL" not in (dtype or "").upper() else 2


def type_ceiling(dtype):
    """Largest magnitude the declared type holds, or None when it cannot overflow.

    Without this a DECIMAL(5,4) column is sampled from a plausible business range,
    clamped on write and every row lands on 9.9999.
    """
    upper = (dtype or "").upper()
    if "DECIMAL" in upper or "NUMERIC" in upper:
        precision, scale = _decimal_precision(dtype)
        return float(10 ** (precision - scale)) - (float(10 ** -scale) if scale else 1.0)
    for token, ceiling in _INT_CEILINGS:
        if upper.startswith(token):
            return float(ceiling)
    if upper.startswith("INT"):
        return 2147483647.0
    return None


def type_family(dtype):
    upper = (dtype or "STRING").upper()
    if upper.startswith(("ARRAY", "MAP", "STRUCT")):
        return "complex"
    if upper.startswith("BINARY"):
        return "binary"
    if upper.startswith("BOOLEAN"):
        return "boolean"
    if upper.startswith("TIMESTAMP"):
        return "timestamp"
    if upper.startswith("DATE"):
        return "date"
    if upper.startswith(("DECIMAL", "NUMERIC")):
        return "decimal"
    if upper.startswith(("DOUBLE", "FLOAT", "REAL")):
        return "float"
    if upper.startswith(("INT", "BIGINT", "SMALLINT", "TINYINT", "LONG", "SHORT", "BYTE")):
        return "integer"
    return "string"


def _coerce(value, dtype):
    """Return `value` as the exact Python type Spark expects for `dtype`."""
    family = type_family(dtype)
    if value is None:
        return None
    if family == "decimal":
        precision, scale = _decimal_precision(dtype)
        quant = decimal.Decimal(1).scaleb(-scale)
        coerced = decimal.Decimal(str(value)).quantize(quant, rounding=decimal.ROUND_HALF_UP)
        # A DECIMAL(p,s) holds at most (p - s) integer digits. LLM value pools do not pass
        # through numeric_range's type_ceiling clamp, so an out-of-range magnitude (e.g.
        # 1234567.89 for DECIMAL(6,2)) reaches here and Spark rejects the whole write on
        # decimal-precision overflow, which skips every table that references it (live:
        # coffee_roastery wholesale.sales_rep failed, 7 dependents emptied). Clamp the
        # magnitude to what the declared precision holds so the value always fits.
        limit = decimal.Decimal(10) ** (precision - scale) - quant
        if coerced > limit:
            coerced = limit
        elif coerced < -limit:
            coerced = -limit
        return coerced
    if family == "integer":
        return int(value)
    if family == "float":
        return float(value)
    if family == "boolean":
        return bool(value)
    if family == "string":
        return value if isinstance(value, str) else str(value)
    return value


# --------------------------------------------------------------------------------------
# deterministic, name-aware value pools
# --------------------------------------------------------------------------------------

_FIRST_NAMES = ["Amara", "Liam", "Sofia", "Noah", "Yuki", "Mateo", "Aisha", "Ethan", "Priya",
                "Lucas", "Nadia", "Omar", "Elena", "Kai", "Zara", "Hugo", "Mei", "Idris",
                "Freya", "Diego", "Layla", "Anton", "Chiara", "Rafael"]
_LAST_NAMES = ["Okafor", "Nguyen", "Rossi", "Haddad", "Silva", "Kowalski", "Tanaka", "Mbeki",
               "Andersen", "Novak", "Fernandez", "Bakker", "Costa", "Petrov", "Sharma",
               "Dubois", "Larsen", "Moreau", "Ibrahim", "Weber"]
_CITIES = ["Amsterdam", "Nairobi", "Osaka", "Lisbon", "Toronto", "Dubai", "Santiago", "Oslo",
           "Cape Town", "Seoul", "Munich", "Melbourne", "Kraków", "Bogotá", "Helsinki",
           "Casablanca", "Auckland", "Bengaluru", "Montréal", "Valencia"]
_STREETS = ["Harbour Way", "Cedar Lane", "Market Street", "Willow Road", "Station Approach",
            "Granite Avenue", "Old Mill Road", "Riverside Walk", "Foundry Street",
            "Kingfisher Close"]
_COUNTRIES = ["Netherlands", "Kenya", "Japan", "Portugal", "Canada", "United Arab Emirates",
              "Chile", "Norway", "South Africa", "South Korea", "Germany", "Australia"]
_COUNTRY_CODES = ["NL", "KE", "JP", "PT", "CA", "AE", "CL", "NO", "ZA", "KR", "DE", "AU"]
_CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "AED", "ZAR", "CAD", "AUD", "CHF", "SGD"]
_LANGUAGE_CODES = ["en", "fr", "de", "es", "pt", "ar", "ja", "ko", "nl", "sw"]
_UNITS = ["kg", "g", "lb", "litre", "each", "case", "pallet", "metre", "hour"]
_DOMAIN_WORDS = ["northwind", "brightline", "harborstone", "cedarpoint", "vantage",
                 "meridian", "solstice", "clearwater"]

_CATEGORICAL_POOLS = (
    (("status",), ["active", "pending", "completed", "cancelled", "on_hold", "closed"]),
    (("state",), ["active", "inactive", "suspended", "archived"]),
    (("stage",), ["intake", "qualification", "execution", "review", "closed"]),
    (("priority",), ["low", "medium", "high", "critical"]),
    (("severity",), ["info", "minor", "major", "critical"]),
    (("tier", "grade", "class", "band"), ["standard", "premium", "enterprise", "basic"]),
    (("channel",), ["web", "mobile", "branch", "partner", "call_center", "field"]),
    (("method",), ["card", "bank_transfer", "cash", "wallet", "direct_debit"]),
    (("frequency", "cadence"), ["daily", "weekly", "monthly", "quarterly", "annual"]),
    (("currency",), _CURRENCY_CODES),
    (("country", "nationality"), _COUNTRIES),
    (("language", "locale"), _LANGUAGE_CODES),
    (("city", "town"), _CITIES),
    (("region", "zone", "area", "territory"),
     ["north", "south", "east", "west", "central", "emea", "apac", "amer"]),
    (("unit", "uom"), _UNITS),
    (("category", "type", "kind", "segment"),
     ["standard", "express", "bulk", "custom", "seasonal", "recurring"]),
    (("direction",), ["inbound", "outbound", "internal"]),
    (("source", "origin"), ["manual", "import", "api", "batch", "partner_feed"]),
    (("gender", "sex"), ["female", "male", "unspecified"]),
)
_CODE_STEM_POOLS = {"country": _COUNTRY_CODES, "currency": _CURRENCY_CODES,
                    "language": _LANGUAGE_CODES, "locale": _LANGUAGE_CODES}

# (lower token, upper token) -> the lower one must not be later than the upper one.
_TEMPORAL_ORDER_TOKENS = (
    ("start", "end"), ("begin", "end"), ("from", "to"), ("open", "close"),
    ("created", "updated"), ("created", "modified"), ("created", "closed"),
    ("issued", "expiry"), ("issue", "expiry"), ("issue", "due"), ("effective", "expiry"),
    ("valid", "expiry"), ("order", "ship"), ("order", "delivery"), ("ship", "delivery"),
    ("entry", "exit"), ("arrival", "departure"), ("admission", "discharge"),
    ("hire", "termination"), ("first", "last"), ("request", "approval"),
    ("approval", "completion"), ("booking", "checkin"), ("checkin", "checkout"),
)
# token -> (low bound, high bound, decimal places)
_NUMERIC_RANGES = (
    (("pct", "percent", "percentage", "rate", "ratio", "utilization", "margin"), 0.0, 100.0, 2),
    (("score", "rating", "index"), 0.0, 100.0, 1),
    (("latitude",), -90.0, 90.0, 6),
    (("longitude",), -180.0, 180.0, 6),
    (("temperature", "temp"), -20.0, 45.0, 1),
    (("weight", "mass"), 0.1, 2500.0, 2),
    (("height", "width", "length", "depth", "distance"), 0.1, 500.0, 2),
    (("volume", "capacity"), 1.0, 10000.0, 2),
    (("amount", "total", "value", "revenue", "cost", "price", "balance", "fee",
      "charge", "salary", "budget"), 5.0, 250000.0, 2),
    (("discount", "tax", "vat"), 0.0, 2500.0, 2),
    (("quantity", "qty", "count", "units", "items"), 1.0, 500.0, 0),
    (("age", "years"), 18.0, 85.0, 0),
    (("duration", "minutes", "elapsed"), 1.0, 480.0, 0),
    (("seconds",), 1.0, 3600.0, 0),
    (("hours",), 1.0, 24.0, 1),
    (("days",), 1.0, 365.0, 0),
    (("year",), 2015.0, 2026.0, 0),
    (("sequence", "order", "position", "rank", "step", "level"), 1.0, 20.0, 0),
    (("version",), 1.0, 9.0, 0),
)
_TEXT_TOKENS = ("description", "comment", "notes", "note", "remark", "summary",
                "justification", "reason", "detail", "instruction", "message")
_PERSON_TOKENS = ("person", "customer", "employee", "contact", "member", "patient",
                  "passenger", "student", "user", "owner", "manager", "agent", "driver",
                  "supplier", "vendor", "author", "guest", "client")


def tokens_of(column_name):
    return [t for t in re.split(r"[^a-z0-9]+", str(column_name).lower()) if t]


def categorical_pool(parts):
    """(pool, matched_via_code_suffix) for a column's tokens, else (None, False).

    Matching only the last token leaves `country_code` / `currency_code` unmatched,
    which is the commonest shape a generated model produces, so a trailing
    `code`/`cd` defers to the token before it. `country_name` stays a name.
    """
    if not parts:
        return None, False
    last = parts[-1]
    via_code = last in ("code", "cd") and len(parts) > 1
    if via_code:
        stem = parts[-2]
        if stem in _CODE_STEM_POOLS:
            return _CODE_STEM_POOLS[stem], True
    key = parts[-2] if via_code else last
    for tokens, pool in _CATEGORICAL_POOLS:
        if key in tokens:
            return pool, via_code
    for part in reversed(parts):
        for tokens, pool in _CATEGORICAL_POOLS:
            if part in tokens:
                return pool, False
    return None, False


def numeric_range(column_name, dtype):
    """(low, high, decimals) for a column, clamped to what the declared type holds."""
    parts = tokens_of(column_name)
    low, high, places = None, None, None
    for tokens, lo, hi, dp in _NUMERIC_RANGES:
        if any(p in tokens for p in parts):
            low, high, places = lo, hi, dp
            break
    if low is None:
        family = type_family(dtype)
        low, high, places = (1.0, 1000.0, 0) if family == "integer" else (1.0, 10000.0, 2)
    if type_family(dtype) == "integer":
        places = 0
    if type_family(dtype) == "decimal":
        places = min(places, _decimal_precision(dtype)[1])
    ceiling = type_ceiling(dtype)
    if ceiling is not None and high > ceiling:
        high = ceiling
        if low > high:
            low = 0.0 if high >= 0 else high
    return low, high, places


# --------------------------------------------------------------------------------------
# temporal coherence
# --------------------------------------------------------------------------------------

def _token_position(parts, token):
    for i, part in enumerate(parts):
        if part == token or (len(token) >= 4 and part.startswith(token)):
            return i
    return -1


def temporal_edges(names):
    """Directed (earlier, later) pairs implied by the column names."""
    edges = []
    for lower_token, upper_token in _TEMPORAL_ORDER_TOKENS:
        lows = [n for n in names if _token_position(tokens_of(n), lower_token) >= 0]
        highs = [n for n in names if _token_position(tokens_of(n), upper_token) >= 0]
        for low in lows:
            low_parts = tokens_of(low)
            if _token_position(low_parts, upper_token) >= 0:
                # the name carries both tokens; the later one wins its role
                if _token_position(low_parts, upper_token) > _token_position(low_parts, lower_token):
                    continue
            for high in highs:
                if high == low:
                    continue
                high_parts = tokens_of(high)
                if (_token_position(high_parts, lower_token) >= 0
                        and _token_position(high_parts, lower_token)
                        > _token_position(high_parts, upper_token)):
                    continue
                if (low, high) not in edges:
                    edges.append((low, high))
    return edges


def temporal_order_plan(names):
    """[(column, [columns it must not precede])] in an order where repairs stick.

    A repair pushes a column forward past its predecessors, so the predecessors have
    to be final first: the plan is a topological order over the name-implied edges.
    Columns in a naming cycle are dropped rather than repaired arbitrarily.
    """
    edges = temporal_edges(names)
    parents = dict((n, []) for n in names)
    for low, high in edges:
        parents[high].append(low)
    resolved, plan = set(), []
    remaining = [n for n in names]
    while remaining:
        ready = [n for n in remaining if all(p in resolved for p in parents[n])]
        if not ready:
            break
        for name in ready:
            if parents[name]:
                plan.append((name, list(parents[name])))
            resolved.add(name)
            remaining.remove(name)
    return plan


def enforce_temporal_order(row, column_types, rnd):
    """Push any date/timestamp in `row` that precedes a predecessor forward."""
    temporal = [n for n, t in column_types.items()
                if type_family(t) in ("date", "timestamp") and row.get(n) is not None]
    repaired = 0
    for name, predecessors in temporal_order_plan(temporal):
        value = row.get(name)
        if not isinstance(value, (datetime.date, datetime.datetime)):
            continue
        as_dt = value if isinstance(value, datetime.datetime) else \
            datetime.datetime.combine(value, datetime.time())
        floor = None
        for predecessor in predecessors:
            other = row.get(predecessor)
            if not isinstance(other, (datetime.date, datetime.datetime)):
                continue
            other_dt = other if isinstance(other, datetime.datetime) else \
                datetime.datetime.combine(other, datetime.time())
            if floor is None or other_dt > floor:
                floor = other_dt
        if floor is None:
            continue
        # A date may legitimately land on the same day as a timestamp predecessor, so
        # only a strictly earlier DAY counts as out of order for a date column.
        if not isinstance(value, datetime.datetime):
            if as_dt.date() >= floor.date():
                continue
        elif as_dt >= floor:
            continue
        moved = floor + datetime.timedelta(days=rnd.randint(1, 240), hours=rnd.randint(0, 23))
        row[name] = moved.date() if not isinstance(value, datetime.datetime) else moved
        repaired += 1
    return repaired


# --------------------------------------------------------------------------------------
# value generation
# --------------------------------------------------------------------------------------

def _slug(text, length=3):
    letters = re.sub(r"[^A-Z]", "", str(text).upper())
    return (letters + "XXX")[:length]


def _key_block(entity):
    """A disjoint numeric block per table so keys never collide across tables."""
    digest = 0
    for ch in entity.fqn:
        digest = (digest * 131 + ord(ch)) & 0x7FFFFFFF
    return 100000 + (digest % 8999) * 100000


def identifying_fks(entity):
    """Foreign keys whose columns are part of this table's own primary key.

    An order line keyed by (order_id, line_no) OWNS its parent's key, so that column
    cannot be minted from this table's block: it has to be a real parent key or the
    child references a row that does not exist.
    """
    if not entity.pk:
        return []
    return [fk for fk in entity.fks if any(c in entity.pk for c in fk["columns"])]


def key_generation_order(entities):
    """Table order for pass 1: a table that borrows a key comes after its parent.

    Only identifying foreign keys constrain the order, so an ordinary foreign-key
    cycle is unaffected. A cycle of identifying keys cannot be satisfied at all, so
    those tables are emitted last and fall back to their own key block.
    """
    parents = {}
    for fqn, entity in entities.items():
        needed = set()
        for fk in identifying_fks(entity):
            if fk["parent"] in entities and fk["parent"] != fqn:
                needed.add(fk["parent"])
        parents[fqn] = needed
    ordered, placed = [], set()
    remaining = list(entities.keys())
    while remaining:
        ready = [f for f in remaining if parents[f] <= placed]
        if not ready:
            ordered.extend(sorted(remaining))
            break
        for fqn in sorted(ready):
            ordered.append(fqn)
            placed.add(fqn)
            remaining.remove(fqn)
    return ordered


def _strongly_connected(nodes, parents):
    """Groups of tables that reach each other through foreign keys, Tarjan, iterative.

    Iterative because a wide model can nest deeper than the interpreter's recursion limit.
    """
    index, low, on_stack, stack, order = {}, {}, set(), [], []
    groups, counter = [], [0]
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(sorted(parents[root])))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter[0]
                    counter[0] += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(parents[child]))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                group = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    group.append(member)
                    if member == node:
                        break
                groups.append(frozenset(group))
    del order
    return groups


def _downstream_of(entities, roots):
    """Every table that reaches `roots` through foreign keys, plus the roots themselves.

    A table whose parent never got rows must not be written, and neither must ITS
    children, so the closure has to be transitive rather than one level deep.
    """
    children = {}
    for fqn, entity in entities.items():
        for fk in entity.fks:
            if fk["parent"] in entities and fk["parent"] != fqn:
                children.setdefault(fk["parent"], set()).add(fqn)
    reached, queue = set(roots), list(roots)
    while queue:
        for child in children.get(queue.pop(), ()):
            if child not in reached:
                reached.add(child)
                queue.append(child)
    return reached


def write_order(entities):
    """Waves of tables to write, parents before children, over EVERY foreign key.

    Key generation only needs identifying keys ordered, but WRITING needs all of them:
    if a child lands and its parent's insert then fails, the child's references point at
    rows that will never exist. Writing parents first means an aborted pass leaves later
    tables empty, and an empty child cannot be an orphan.

    Tables inside a foreign-key cycle cannot be layered against each other, so they share
    one wave. Condensing each cycle to a single node first keeps that concession to the
    cycle itself: everything downstream of a cycle still gets its own later wave.
    """
    parents = {}
    for fqn, entity in entities.items():
        parents[fqn] = set(fk["parent"] for fk in entity.fks
                           if fk["parent"] in entities and fk["parent"] != fqn)

    groups = _strongly_connected(sorted(entities), parents)
    group_of = dict((member, i) for i, g in enumerate(groups) for member in g)
    group_deps = {}
    for i, group in enumerate(groups):
        group_deps[i] = set(group_of[p] for member in group for p in parents[member]
                            if group_of[p] != i)

    waves, placed = [], set()
    remaining = set(range(len(groups)))
    while remaining:
        ready = sorted(i for i in remaining if group_deps[i] <= placed)
        if not ready:                       # unreachable: the condensation is acyclic
            ready = sorted(remaining)
        wave = sorted(member for i in ready for member in groups[i])
        waves.append(wave)
        placed.update(ready)
        remaining.difference_update(ready)
    return waves


def _borrowed_key_columns(entity, entities):
    """{pk column: (parent entity, position in the parent key)} for identifying keys."""
    borrowed = {}
    for fk in identifying_fks(entity):
        parent = entities.get(fk["parent"]) if entities else None
        if parent is None or parent.fqn == entity.fqn or not parent.keys or not parent.pk:
            continue
        for position, column in enumerate(fk["columns"]):
            if column not in entity.pk:
                continue
            parent_column = fk["parent_columns"][position] \
                if position < len(fk["parent_columns"]) else fk["parent_columns"][0]
            parent_position = parent.pk.index(parent_column) \
                if parent_column in parent.pk else 0
            borrowed[column] = (parent, parent_position)
    return borrowed


def _generate_borrowed_keys(entity, rows, seed, borrowed):
    """Keys for a table whose primary key contains a parent's key."""
    rnd = random.Random("%s|borrowed|%s" % (entity.fqn, seed))
    parents = sorted(set(p.fqn for p, _ in borrowed.values()))
    lead = borrowed[next(c for c in entity.pk if c in borrowed)][0]
    free = [c for c in entity.pk if c not in borrowed]
    if not free:
        # The key IS the parent's key, so this is a 1:1 extension: one row per parent
        # row at most, otherwise the key could not stay unique.
        rows = min(rows, len(lead.keys))
        picks = list(range(rows))
    else:
        picks = _fk_parent_indices(rows, len(lead.keys), rnd)
    used, keys = {}, []
    for index in range(rows):
        pick = picks[index]
        values = []
        for column in entity.pk:
            if column in borrowed:
                parent, position = borrowed[column]
                source = parent.keys[pick % len(parent.keys)]
                values.append(source[position] if position < len(source) else source[0])
            else:
                values.append(None)
        stem = tuple(v for v in values if v is not None)
        counter = used.get(stem, 0) + 1
        used[stem] = counter
        for slot, column in enumerate(entity.pk):
            if values[slot] is not None:
                continue
            column_type = (entity.column(column) or {"type": "INT"})["type"]
            family = type_family(column_type)
            if family in ("integer", "decimal", "float"):
                values[slot] = _coerce(counter, column_type)
            elif family in ("date", "timestamp"):
                moment = datetime.datetime(2025, 1, 1) + datetime.timedelta(days=counter)
                values[slot] = moment.date() if family == "date" else moment
            else:
                values[slot] = "%s-%03d" % (_slug(column, 3), counter)
        keys.append(tuple(values))
    _ = parents
    entity.keys = keys
    return keys


def _key_part(ordinal, dtype, prefix, width=6, day=None):
    """One key component, in the type its column declares.

    Every key part is minted here so none can carry a type the column cannot
    store: a string in a DATE or DECIMAL key column makes Spark reject the whole
    table on write, which surfaces as a failed install rather than as bad data.
    """
    family = type_family(dtype)
    if family in ("integer", "decimal", "float"):
        ceiling = type_ceiling(dtype)
        if ceiling is not None and ordinal > ceiling:
            # A SMALLINT or DECIMAL(5,0) key column cannot hold this table's key
            # block, and an out-of-range value fails the write for the whole table.
            # Fold into range instead; the integrity gate reports any duplicates.
            ordinal = ordinal % (int(ceiling) or 1)
        return _coerce(ordinal, dtype)
    if family in ("date", "timestamp"):
        moment = datetime.datetime(2025, 1, 1) + datetime.timedelta(
            days=(ordinal if day is None else day) % 36500)
        return moment.date() if family == "date" else moment
    if family == "boolean":
        return bool(ordinal % 2)
    return "%s-%0*d" % (prefix, width, ordinal)


def generate_keys(entity, rows, seed, entities=None):
    """Pass 1: one unique key tuple per row, typed to the declared key columns."""
    if not entity.pk:
        entity.keys = [tuple() for _ in range(rows)]
        return entity.keys
    borrowed = _borrowed_key_columns(entity, entities) if entities else {}
    if borrowed:
        return _generate_borrowed_keys(entity, rows, seed, borrowed)
    base = _key_block(entity)
    prefix = "%s%s" % (_slug(entity.schema, 2), _slug(entity.table, 3))
    keys = []
    for index in range(rows):
        ordinal = base + index
        tuple_values = []
        for depth, column_name in enumerate(entity.pk):
            column = entity.column(column_name) or {"type": "STRING"}
            # A composite key stays unique because only the LAST column carries the
            # row ordinal; the earlier ones repeat in blocks, as real keys do.
            if depth < len(entity.pk) - 1:
                part = index // max(1, (depth + 1) * 2) + 1
                tuple_values.append(_key_part(part, column["type"], prefix, 3))
            else:
                tuple_values.append(
                    _key_part(ordinal, column["type"], prefix, 6, day=index))
        keys.append(tuple(tuple_values))
    if len(entity.pk) > 1:
        # Blocked leading columns can repeat a tuple when a table has very few rows;
        # widen the last part until every tuple is distinct.
        last_type = (entity.column(entity.pk[-1]) or {"type": "STRING"})["type"]
        seen, widened, bump = set(), [], 0
        for index, key in enumerate(keys):
            # Bounded: a domain with fewer distinct values than rows (a BOOLEAN key
            # column, say) cannot be widened, and the integrity gate should report
            # that honestly rather than the loop spinning forever.
            attempts = 0
            while key in seen and attempts < rows + 16:
                bump += 1
                attempts += 1
                key = key[:-1] + (_key_part(base + bump, last_type, prefix, 6,
                                            day=rows + bump),)
            seen.add(key)
            widened.append(key)
        keys = widened
    entity.keys = keys
    return keys


def generate_all_keys(entities, rows, seed):
    """Pass 1 across the model, parents of identifying keys first."""
    for fqn in key_generation_order(entities):
        generate_keys(entities[fqn], rows, seed, entities)
    return entities


def _fk_parent_indices(rows, parent_row_count, rnd):
    """Row -> parent row index, covering every parent once before repeating.

    Straight random choice leaves parents unreferenced, which makes a demo join look
    empty; cycling a shuffled parent list first guarantees fan-out.
    """
    if parent_row_count <= 0:
        return []
    order = list(range(parent_row_count))
    rnd.shuffle(order)
    picks = []
    while len(picks) < rows:
        picks.extend(order[:min(len(order), rows - len(picks))])
        rnd.shuffle(order)
    return picks[:rows]


def generate_value(column_name, dtype, rnd, row_index, pools=None):
    """One deterministic, name-aware value for a non-key column."""
    parts = tokens_of(column_name)
    family = type_family(dtype)
    pool = (pools or {}).get(column_name)
    if pool:
        value = pool[row_index % len(pool)] if len(pool) < 4 else rnd.choice(pool)
        if family == "string":
            return str(value)

    if family == "complex":
        upper = dtype.upper()
        return {} if upper.startswith("MAP") else ([] if upper.startswith("ARRAY") else None)
    if family == "binary":
        return bytes(rnd.getrandbits(8) for _ in range(8))
    if family == "boolean":
        return rnd.random() < 0.5

    if family in ("date", "timestamp"):
        moment = (datetime.datetime(2024, 1, 1)
                  + datetime.timedelta(days=rnd.randint(0, 730),
                                       hours=rnd.randint(0, 23),
                                       minutes=rnd.randint(0, 59),
                                       seconds=rnd.randint(0, 59)))
        return moment.date() if family == "date" else moment

    if family in ("integer", "decimal", "float"):
        if any(p in ("year",) for p in parts):
            return _coerce(rnd.randint(2015, 2026), dtype)
        low, high, places = numeric_range(column_name, dtype)
        raw = rnd.uniform(low, high)
        return _coerce(round(raw, places) if places else int(round(raw)), dtype)

    # strings
    last = parts[-1] if parts else ""
    joined = "_".join(parts)
    if last in ("email",) or "email" in parts:
        return "%s.%s@%s.com" % (rnd.choice(_FIRST_NAMES).lower(),
                                 rnd.choice(_LAST_NAMES).lower(),
                                 rnd.choice(_DOMAIN_WORDS))
    if "phone" in parts or "mobile" in parts or "telephone" in parts:
        return "+%d %d %d" % (rnd.randint(1, 99), rnd.randint(100, 999), rnd.randint(100000, 999999))
    if "url" in parts or "website" in parts or "link" in parts:
        return "https://www.%s.example/%s" % (rnd.choice(_DOMAIN_WORDS), rnd.choice(parts) if parts else "page")
    if last in ("postcode", "postal", "zip", "zipcode") or "postal" in parts:
        return "%d%s" % (rnd.randint(1000, 9999), _slug(rnd.choice(_CITIES), 2))
    if "street" in parts or "address" in joined:
        return "%d %s" % (rnd.randint(1, 240), rnd.choice(_STREETS))
    if "first" in parts and "name" in parts:
        return rnd.choice(_FIRST_NAMES)
    if "last" in parts and "name" in parts or "surname" in parts:
        return rnd.choice(_LAST_NAMES)
    if last == "name" and any(p in _PERSON_TOKENS for p in parts):
        return "%s %s" % (rnd.choice(_FIRST_NAMES), rnd.choice(_LAST_NAMES))

    pool, _via_code = categorical_pool(parts)
    if pool:
        return rnd.choice(pool)

    if any(p in _TEXT_TOKENS for p in parts):
        subject = " ".join(p for p in parts if p not in _TEXT_TOKENS) or "record"
        return "%s %s for reference %s-%04d." % (
            rnd.choice(["Reviewed", "Confirmed", "Logged", "Adjusted", "Verified"]),
            subject.replace("_", " "), _slug(subject, 3), rnd.randint(1, 9999))
    if last == "name" or last == "title" or last == "label":
        stem = " ".join(p for p in parts if p not in ("name", "title", "label")) or "record"
        return "%s %s %d" % (stem.replace("_", " ").title(),
                             rnd.choice(["Alpha", "Beta", "Core", "Prime", "North"]),
                             rnd.randint(1, 99))
    if last in ("code", "cd", "ref", "reference", "number", "no", "sku", "id", "key"):
        stem = parts[-2] if len(parts) > 1 else (parts[0] if parts else "ref")
        return "%s-%06d" % (_slug(stem, 3), rnd.randint(1, 999999))
    stem = joined.replace("_", " ") or "value"
    return "%s %s" % (stem.title(), rnd.randint(100, 9999))


# --------------------------------------------------------------------------------------
# optional LLM realism pass
# --------------------------------------------------------------------------------------

_LLM_STATE = {"broken": set(), "errors": {}, "lock": threading.Lock()}
_LLM_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _llm_candidate_columns(entity):
    """Free-text columns an LLM can make more realistic than the generic generator."""
    keys = set(entity.pk)
    for fk in entity.fks:
        keys.update(fk["columns"])
    out = []
    for column in entity.columns:
        if column["name"] in keys or type_family(column["type"]) != "string":
            continue
        parts = tokens_of(column["name"])
        if parts and parts[-1] in ("id", "key", "code", "cd"):
            continue
        out.append(column["name"])
    return out[:SAMPLE_MAX_LLM_COLUMNS]


def llm_value_pools(spark, entity, columns, endpoints, rows, log=None):
    """Ask one LLM endpoint for realistic value pools. {} on any problem."""
    if not columns or not endpoints:
        return {}
    want = max(rows, 8)
    prompt = (
        "You generate realistic sample data for a data model. Table `%s`.`%s`. "
        "For each column below return a JSON array of %d distinct, realistic values "
        "that a production system would hold. Values must be plain strings, no "
        "placeholders, no numbering, no commentary. Reply with ONLY a JSON object "
        "mapping each column name to its array. Columns: %s"
        % (entity.schema, entity.table, want, ", ".join(columns)))
    literal = prompt.replace("\\", "\\\\").replace("'", "\\'")
    for endpoint in endpoints:
        with _LLM_STATE["lock"]:
            if endpoint in _LLM_STATE["broken"]:
                continue
        try:
            raw = spark.sql("SELECT ai_query('%s', '%s') AS r" % (endpoint, literal)).collect()
            text = raw[0][0] if raw else ""
            match = _LLM_JSON_RE.search(text or "")
            if not match:
                continue
            parsed = json.loads(match.group(0))
            pools = {}
            for column in columns:
                values = parsed.get(column)
                if isinstance(values, list):
                    clean = [str(v) for v in values
                             if isinstance(v, (str, int, float)) and str(v).strip()]
                    if len(clean) >= 3:
                        pools[column] = clean
            if pools:
                return pools
        except Exception as err:
            # One table's call can fail on a transient rate limit while the endpoint is
            # perfectly healthy, so retire it only after repeated failures. Retiring on
            # the first error costs every remaining table its realistic values.
            with _LLM_STATE["lock"]:
                count = _LLM_STATE["errors"].get(endpoint, 0) + 1
                _LLM_STATE["errors"][endpoint] = count
                retired = count >= SAMPLE_LLM_MAX_ENDPOINT_ERRORS
                if retired:
                    _LLM_STATE["broken"].add(endpoint)
            if log and retired:
                log("  sample: LLM endpoint %s retired after %d failures (%s) - "
                    "deterministic values"
                    % (endpoint, count, str(err).split("\n")[0][:120]))
    return {}


# --------------------------------------------------------------------------------------
# row assembly
# --------------------------------------------------------------------------------------

def generate_rows(entity, entities, rows, seed, pools=None):
    """Pass 2: assemble every row, drawing foreign keys from the parents' key pools."""
    rnd = random.Random("%s|rows|%s" % (entity.fqn, seed))
    column_types = dict((c["name"], c["type"]) for c in entity.columns)
    pk_index = dict((name, i) for i, name in enumerate(entity.pk))
    if entity.pk and entity.keys is not None:
        # A 1:1 extension table cannot hold more rows than its parent, so pass 1 is
        # the authority on how many rows this table gets.
        rows = len(entity.keys)

    fk_assignment = {}
    for fk in entity.fks:
        parent = entities.get(fk["parent"])
        fk_rnd = random.Random("%s|fk|%s|%s" % (entity.fqn, ",".join(fk["columns"]), seed))
        if parent is None or not parent.keys or not parent.pk:
            fk_assignment[tuple(fk["columns"])] = None
            continue
        if parent.fqn == entity.fqn:
            # A self reference points at an earlier row so the data has no cycle.
            picks = [None] + [fk_rnd.randint(0, i - 1) for i in range(1, rows)]
        else:
            picks = _fk_parent_indices(rows, len(parent.keys), fk_rnd)
        fk_assignment[tuple(fk["columns"])] = (parent, fk, picks)

    assembled = []
    for index in range(rows):
        row = {}
        for depth, name in enumerate(entity.pk):
            row[name] = entity.keys[index][depth] if index < len(entity.keys) else None
        for key_columns, assignment in fk_assignment.items():
            if assignment is None:
                for name in key_columns:
                    if name not in pk_index:
                        column = entity.column(name) or {"type": "STRING", "nullable": True}
                        row[name] = None if column["nullable"] else generate_value(
                            name, column["type"], rnd, index)
                continue
            parent, fk, picks = assignment
            pick = picks[index] if index < len(picks) else None
            for position, name in enumerate(key_columns):
                if name in pk_index:
                    continue
                column = entity.column(name) or {"type": "STRING", "nullable": True}
                if pick is None:
                    # first row of a self reference: null when allowed, else itself
                    row[name] = None if column["nullable"] else (
                        entity.keys[index][0] if entity.keys and entity.keys[index] else None)
                    continue
                parent_column = fk["parent_columns"][position] \
                    if position < len(fk["parent_columns"]) else fk["parent_columns"][0]
                parent_position = parent.pk.index(parent_column) \
                    if parent_column in parent.pk else 0
                value = parent.keys[pick][parent_position] \
                    if parent_position < len(parent.keys[pick]) else None
                row[name] = _coerce(value, column["type"])
        for column in entity.columns:
            name = column["name"]
            if name in row:
                continue
            row[name] = generate_value(name, column["type"], rnd, index, pools)
        enforce_temporal_order(row, column_types, rnd)
        assembled.append(row)
    entity.rows = assembled
    return assembled


# --------------------------------------------------------------------------------------
# integrity assertions - the gate before anything is written
# --------------------------------------------------------------------------------------

def assert_integrity(entities):
    """Every violation found in the assembled rows, as readable strings."""
    problems = []
    key_pools = {}
    for ent in entities.values():
        if not ent.pk or not ent.rows:
            continue
        pool = set()
        for row in ent.rows:
            pool.add(tuple(row.get(c) for c in ent.pk))
        key_pools[ent.fqn] = pool
        if len(pool) != len(ent.rows):
            problems.append("%s: primary key %s has %d duplicate row(s)"
                            % (ent.fqn, "+".join(ent.pk), len(ent.rows) - len(pool)))
        for row in ent.rows:
            for column_name in ent.pk:
                if row.get(column_name) is None:
                    problems.append("%s: primary key column %s is null"
                                    % (ent.fqn, column_name))
                    break

    for ent in entities.values():
        if not ent.rows:
            continue
        for fk in ent.fks:
            parent = entities.get(fk["parent"])
            if parent is None or not parent.pk:
                continue
            pool = key_pools.get(parent.fqn)
            if not pool:
                continue
            positions = []
            for parent_column in fk["parent_columns"]:
                positions.append(parent.pk.index(parent_column)
                                 if parent_column in parent.pk else 0)
            projected = set(tuple(key[p] for p in positions) for key in pool) \
                if positions != list(range(len(parent.pk))) else pool
            orphans = 0
            for row in ent.rows:
                values = tuple(row.get(c) for c in fk["columns"])
                if all(v is None for v in values):
                    continue
                if values not in projected:
                    orphans += 1
            if orphans:
                problems.append(
                    "%s: foreign key %s -> %s has %d row(s) with no parent key"
                    % (ent.fqn, "+".join(fk["columns"]), parent.fqn, orphans))

        for column in ent.columns:
            if column["nullable"]:
                continue
            nulls = sum(1 for row in ent.rows if row.get(column["name"]) is None)
            if nulls:
                problems.append("%s: NOT NULL column %s has %d null(s)"
                                % (ent.fqn, column["name"], nulls))
    return problems


# --------------------------------------------------------------------------------------
# write
# --------------------------------------------------------------------------------------

def write_entity(spark, entity):
    """Append the assembled rows using the table's own schema, so types cannot drift."""
    if not entity.rows:
        return 0
    schema = spark.sql("SELECT * FROM %s LIMIT 0" % entity.quoted).schema
    ordered = [tuple(row.get(field.name) for field in schema.fields) for row in entity.rows]
    frame = spark.createDataFrame(ordered, schema)
    frame.write.mode("append").saveAsTable("%s.%s.%s"
                                           % (entity.catalog, entity.schema, entity.table))
    return len(ordered)


def _llm_pools_for_model(spark, cfg, populate, rows, log):
    """Realistic value pools per table, bounded in time and reported as it goes.

    The pass is optional realism on top of a complete deterministic generator, so it is
    never allowed to decide how long an install takes: whatever has not answered inside
    the budget keeps its deterministic values. Progress is logged per wave, because a
    silent phase is indistinguishable from a hung one.
    """
    threads = max(1, cfg["threads"])
    pools_by_table = {}

    def _pools(entity):
        return entity.fqn, llm_value_pools(
            spark, entity, _llm_candidate_columns(entity),
            cfg["llm_endpoints"], rows, log)

    started = time.time()
    waves = -(-len(populate) // threads)
    budget = SAMPLE_LLM_TIMEOUT_S * waves
    pool_exec = ThreadPoolExecutor(max_workers=threads)
    try:
        pending = set(pool_exec.submit(_pools, e) for e in populate.values())
        answered, logged = 0, 0
        while pending:
            remaining = budget - (time.time() - started)
            if remaining <= 0:
                break
            done, pending = wait(pending, timeout=min(30.0, remaining))
            for future in done:
                answered += 1
                try:
                    fqn, pools = future.result()
                except Exception:
                    continue
                if pools:
                    pools_by_table[fqn] = pools
            if done and answered - logged >= threads:
                logged = answered
                log("  sample: LLM pools %d/%d table(s)  %.0fs"
                    % (answered, len(populate), time.time() - started))
        if pending:
            log("  sample: LLM pass hit its %ds budget with %d table(s) outstanding - "
                "those keep deterministic values" % (budget, len(pending)))
    finally:
        # Do not block the install on calls that are still in flight: they can only add
        # realism to tables that already have complete deterministic values.
        pool_exec.shutdown(wait=False, cancel_futures=True)
    log("  sample: LLM value pools for %d/%d table(s) in %.0fs"
        % (len(pools_by_table), len(populate), time.time() - started))
    return pools_by_table


# --------------------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------------------

def generate_sample_data(spark, cfg, catalogs, log):
    """Populate every installed table. Returns a summary dict."""
    rows = cfg["rows"]
    seed = cfg["seed"]
    log("=" * 64)
    log("SAMPLE DATA: %d row(s) per table across %s" % (rows, ", ".join(catalogs)))
    entities = read_installed_model(spark, catalogs, log)
    populate = dict((k, e) for k, e in entities.items() if e.columns)
    if not populate:
        log("  sample: no installed tables found - nothing to populate")
        return {"tables": 0, "rows": 0, "problems": [], "written": 0}

    generate_all_keys(populate, rows, seed)

    pools_by_table = {}
    if cfg.get("llm") and cfg.get("llm_endpoints"):
        pools_by_table = _llm_pools_for_model(spark, cfg, populate, rows, log)

    for entity in populate.values():
        generate_rows(entity, populate, rows, seed, pools_by_table.get(entity.fqn))

    problems = assert_integrity(populate)
    if problems:
        log("  sample: INTEGRITY CHECK FAILED - %d problem(s), nothing written"
            % len(problems))
        for problem in problems[:20]:
            log("      - %s" % problem)
        raise Exception("Sample data integrity check failed: %s"
                        % "; ".join(problems[:5]))
    log("  sample: integrity check passed (unique keys, every foreign key resolves)")

    written, failures, done = [0], [], set()
    lock = threading.Lock()

    def _write(entity):
        try:
            count = write_entity(spark, entity)
            with lock:
                written[0] += count
                done.add(entity.fqn)
        except Exception as err:
            with lock:
                failures.append((entity.fqn, str(err).split("\n")[0][:200]))

    waves = write_order(populate)
    blocked = set()
    for depth, wave in enumerate(waves):
        due = [f for f in wave if f not in blocked]
        if due:
            with ThreadPoolExecutor(max_workers=cfg["threads"]) as writer:
                list(as_completed([writer.submit(_write, populate[f]) for f in due]))
        retry = [fqn for fqn, _ in failures if fqn in due]
        if retry:
            # The live coffee_roastery run lost one table to a transient write; one retry
            # costs a second and saves the whole downstream subtree from being skipped.
            log("  sample: retrying %d table(s) that failed to write in wave %d/%d"
                % (len(retry), depth + 1, len(waves)))
            failures[:] = [f for f in failures if f[0] not in retry]
            with ThreadPoolExecutor(max_workers=cfg["threads"]) as writer:
                list(as_completed([writer.submit(_write, populate[f]) for f in retry]))
        still_failed = set(fqn for fqn, _ in failures)
        if still_failed:
            blocked = _downstream_of(populate, still_failed)
            log("  sample: %d table(s) failed - skipping %d table(s) that reference them "
                "so nothing points at a row that was never written"
                % (len(still_failed), len(blocked - still_failed - done)))

    if failures:
        log("  sample: %d table(s) failed to write" % len(failures))
        for fqn, err in failures[:20]:
            log("      - %s -> %s" % (fqn, err))
        # Only a foreign-key cycle can put a child in the same wave as a failed parent,
        # so name any such table instead of letting the orphans go unreported.
        missing = set(populate) - done
        for fqn in sorted(done):
            broken = sorted(fk["parent"] for fk in populate[fqn].fks
                            if fk["parent"] in missing and fk["parent"] != fqn)
            if broken:
                log("      ! %s was written but references unwritten %s"
                    % (fqn, ", ".join(broken)))
    failures[:] = sorted(set(failures))
    log("SAMPLE DATA: wrote %d row(s) into %d table(s)%s"
        % (written[0], len(done),
           " (%d failed, %d skipped)"
           % (len(failures), len(populate) - len(done) - len(failures))
           if failures else ""))
    return {"tables": len(populate), "rows": rows, "written": written[0],
            "failed": [f[0] for f in failures],
            "skipped": sorted(set(populate) - done - set(f[0] for f in failures)),
            "problems": []}
