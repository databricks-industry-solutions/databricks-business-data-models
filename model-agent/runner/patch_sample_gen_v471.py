"""v4.7.1 — root-cause fixes for the generate-sample-data path.

Applies text replacements to agent/dbx_vibe_modelling_agent.ipynb cell sources and
writes the notebook back with the file's existing serialisation (indent=1,
ensure_ascii=False, verified byte-identical on a no-op round trip) so the diff shows
only the changed code. Every replacement is asserted; the script fails loudly rather
than half-patching.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

REPLACEMENTS: list[tuple[str, str, str]] = []


def rep(alias: str, old: str, new: str) -> None:
    REPLACEMENTS.append((alias, old, new))


# ---------------------------------------------------------------- 1. version
rep(
    "agent-version-global",
    '__AGENT_VERSION__ = "4.7.0"',
    '__AGENT_VERSION__ = "4.7.1"',
)

# ------------------------------------------------- 2. pyspark type imports
rep(
    "v471-type-map-completeness (imports)",
    """from pyspark.sql.types import (  # type: ignore
    StructType, StructField, StringType, LongType, BooleanType,
    DoubleType, FloatType, DateType, TimestampType
)""",
    """from pyspark.sql.types import (  # type: ignore
    StructType, StructField, StringType, LongType, BooleanType,
    DoubleType, FloatType, DateType, TimestampType, IntegerType, DecimalType
)""",
)

# --------------------------------------------------------- 3. map_data_type
rep(
    "v471-type-map-completeness",
    """def map_data_type(logical_type, to_pyspark=False):
    if not logical_type: return StringType() if to_pyspark else "STRING"
    type_map = {"string": (StringType(), "STRING"), "boolean": (BooleanType(), "BOOLEAN"), "integer": (LongType(), "BIGINT"), "long": (LongType(), "BIGINT"), "bigint": (LongType(), "BIGINT"), "number": (DoubleType(), "DOUBLE"), "float": (FloatType(), "FLOAT"), "double": (DoubleType(), "DOUBLE"), "date": (DateType(), "DATE"), "datetime": (TimestampType(), "TIMESTAMP"), "timestamp": (TimestampType(), "TIMESTAMP"), "decimal": (DoubleType(), "DECIMAL(18,2)")}
    result = type_map.get(str(logical_type).lower().split('(')[0], (StringType(), "STRING"))
    return result[0] if to_pyspark else result[1]""",
    '''def _v471_decimal_precision(raw_type):
    """DECIMAL(p,s) -> clamped (precision, scale). alias=v471-type-map-completeness"""
    import re as _re_dec
    m = _re_dec.search(r"\\(\\s*(\\d+)\\s*(?:,\\s*(\\d+)\\s*)?\\)", str(raw_type or ""))
    if not m:
        return (18, 2)
    p = max(1, min(38, int(m.group(1))))
    s = int(m.group(2)) if m.group(2) is not None else 0
    return (p, max(0, min(s, p)))

def map_data_type(logical_type, to_pyspark=False):
    # alias=v471-type-map-completeness — INT / SMALLINT / TINYINT / NUMERIC / REAL /
    # VARCHAR / CHAR / TEXT / BOOL were absent from the table and silently resolved to
    # STRING, so those columns were CREATEd as STRING in Unity Catalog and every
    # generated sample value failed createDataFrame schema verification. DECIMAL now
    # round-trips its declared (p,s) instead of collapsing to DOUBLE / DECIMAL(18,2).
    if not logical_type: return StringType() if to_pyspark else "STRING"
    _base_t = str(logical_type).strip().lower().split('(')[0].strip()
    if _base_t in ("decimal", "numeric", "dec"):
        _p_dt, _s_dt = _v471_decimal_precision(logical_type)
        return DecimalType(_p_dt, _s_dt) if to_pyspark else f"DECIMAL({_p_dt},{_s_dt})"
    type_map = {"string": (StringType(), "STRING"), "varchar": (StringType(), "STRING"), "char": (StringType(), "STRING"), "text": (StringType(), "STRING"), "boolean": (BooleanType(), "BOOLEAN"), "bool": (BooleanType(), "BOOLEAN"), "integer": (LongType(), "BIGINT"), "int": (LongType(), "BIGINT"), "long": (LongType(), "BIGINT"), "bigint": (LongType(), "BIGINT"), "smallint": (IntegerType(), "INT"), "tinyint": (IntegerType(), "INT"), "short": (IntegerType(), "INT"), "byte": (IntegerType(), "INT"), "number": (DoubleType(), "DOUBLE"), "float": (FloatType(), "FLOAT"), "real": (DoubleType(), "DOUBLE"), "double": (DoubleType(), "DOUBLE"), "date": (DateType(), "DATE"), "datetime": (TimestampType(), "TIMESTAMP"), "timestamp": (TimestampType(), "TIMESTAMP"), "timestamp_ntz": (TimestampType(), "TIMESTAMP")}
    result = type_map.get(_base_t, (StringType(), "STRING"))
    return result[0] if to_pyspark else result[1]''',
)

# ----------------------------------- 4. schema coercion + semantic generators
_NEW_HELPERS = '''
# ── v4.7.1 sample-data realism helpers ──────────────────────────────────────
# alias=v471-schema-type-coercion / alias=v471-semantic-stdlib-values /
# alias=v471-temporal-order-coherence
# Industry-agnostic by construction: every vocabulary below is a generic business
# token set derived from the COLUMN NAME, never a vertical-specific term list.

def _v471_coerce_to_schema_type(values, atype):
    """Force a column's python values into the exact type map_data_type() puts in the
    DataFrame schema.

    spark.createDataFrame verifies every value against the schema, so one type
    contradiction (Decimal into DoubleType, int into StringType) raises and drops the
    whole product to the random fallback tier, or to zero rows.
    """
    from datetime import date as _d471, datetime as _dt471, time as _tm471
    from decimal import Decimal as _Dec471, InvalidOperation as _DecErr471
    try:
        tgt = map_data_type(atype, to_pyspark=True)
    except Exception:
        return values
    kind = type(tgt).__name__
    _q = _limit = None
    if kind == "DecimalType":
        _scale = int(getattr(tgt, "scale", 2))
        _prec = int(getattr(tgt, "precision", 18))
        _q = _Dec471(1).scaleb(-_scale)
        _limit = _Dec471(10) ** (_prec - _scale)
    out = []
    for v in values:
        try:
            if v is None:
                out.append(None)
            elif kind == "StringType":
                out.append(v if isinstance(v, str)
                           else (v.isoformat() if isinstance(v, (_dt471, _d471)) else str(v)))
            elif kind in ("LongType", "IntegerType", "ShortType", "ByteType"):
                out.append(int(v))
            elif kind in ("DoubleType", "FloatType"):
                out.append(float(v))
            elif kind == "DecimalType":
                _dv = _Dec471(str(v)).quantize(_q)
                if abs(_dv) >= _limit:
                    _dv = (_limit - _q) if _dv > 0 else -(_limit - _q)
                out.append(_dv)
            elif kind == "BooleanType":
                out.append(bool(v))
            elif kind == "DateType":
                out.append(v.date() if isinstance(v, _dt471)
                           else (v if isinstance(v, _d471) else _d471.fromisoformat(str(v)[:10])))
            elif kind == "TimestampType":
                if isinstance(v, _dt471):
                    out.append(v)
                elif isinstance(v, _d471):
                    out.append(_dt471.combine(v, _tm471()))
                else:
                    out.append(_dt471.fromisoformat(str(v)))
            else:
                out.append(v)
        except (TypeError, ValueError, ArithmeticError, _DecErr471, AttributeError):
            out.append(None)
    return out


_V471_TEMPORAL_ORDER_TOKENS = (
    ("valid_from", "valid_to"), ("effective", "expir"), ("effective", "end"),
    ("start", "end"), ("begin", "end"), ("open", "close"), ("entry", "exit"),
    ("created", "updated"), ("created", "modified"), ("created", "closed"),
    ("created", "deleted"), ("created", "resolved"), ("opened", "resolved"),
    ("order", "ship"), ("order", "deliver"), ("ship", "deliver"),
    ("issue", "expir"), ("issue", "due"), ("invoice", "payment"),
    ("hire", "termination"), ("hire", "separation"), ("join", "leave"),
    ("admission", "discharge"), ("birth", "death"), ("manufacture", "expir"),
    ("request", "approv"), ("submit", "approv"), ("submit", "review"),
    ("depart", "arriv"), ("check_in", "check_out"), ("first", "last"),
    ("from", "to"), ("min", "max"),
)


def _v471_token_pos(parts, token):
    """Position of a token inside a split column name, or -1.

    Token-boundary matching keeps 'to' on valid_to and off total/store; the
    4-character prefix rule is what lets 'ship' reach shipped_timestamp and
    'expir' reach expiration_date.
    """
    if "_" in token:
        joined = "_".join(parts)
        return joined.find(token)
    for i, p in enumerate(parts):
        if p == token or (len(token) >= 4 and p.startswith(token)):
            return i
    return -1


def _v471_token_role(parts, lo_token, hi_token):
    """'lo', 'hi' or None for one column against one ordered token pair.

    A column can carry BOTH tokens (effective_end_date holds 'effective' and
    'end'). Treating that as ambiguous left the commonest window-closing column
    in the model unconstrained, so the later token wins: the trailing token is
    the semantic head of a snake_case name.
    """
    lo_at, hi_at = _v471_token_pos(parts, lo_token), _v471_token_pos(parts, hi_token)
    if lo_at < 0 and hi_at < 0:
        return None
    if hi_at < 0:
        return 'lo'
    if lo_at < 0:
        return 'hi'
    return 'hi' if hi_at > lo_at else 'lo'


def _v471_temporal_edges(names):
    """Infer lo -> hi ordering edges between temporal column names."""
    parts = {n: [p for p in str(n).lower().split('_') if p] for n in names}
    edges = set()
    for i_a in range(len(names)):
        for i_b in range(i_a + 1, len(names)):
            a, b = names[i_a], names[i_b]
            for lo_t, hi_t in _V471_TEMPORAL_ORDER_TOKENS:
                role_a = _v471_token_role(parts[a], lo_t, hi_t)
                role_b = _v471_token_role(parts[b], lo_t, hi_t)
                if role_a == 'lo' and role_b == 'hi':
                    edges.add((a, b))
                    break
                if role_b == 'lo' and role_a == 'hi':
                    edges.add((b, a))
                    break
    return edges


def _v471_temporal_order_plan(names):
    """Return (topological column order, predecessors) for the inferred edges.

    A table with N temporal columns yields overlapping constraints
    (`actual_start < actual_end`, `scheduled_start < actual_end`, ...). Repairing
    them pair by pair moves a column that an earlier pair already placed, so the
    fix has to be applied predecessors-first. Columns caught in a naming cycle
    keep no predecessor rather than being ordered arbitrarily.
    """
    edges = _v471_temporal_edges(names)
    if not edges:
        return [], {}
    preds = {n: set() for n in names}
    succs = {n: set() for n in names}
    for lo, hi in edges:
        preds[hi].add(lo)
        succs[lo].add(hi)
    indeg = {n: len(preds[n]) for n in names}
    ready = [n for n in names if indeg[n] == 0]
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for nxt in sorted(succs[node]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
    if len(order) < len(names):
        cyclic = [n for n in names if n not in order]
        for n in cyclic:
            preds[n] = set()
            for other in names:
                preds[other].discard(n)
        order.extend(cyclic)
    return order, preds


def _v471_enforce_temporal_order(col_values, col_info, rnd):
    """Repair intra-row chronology; returns the number of values moved.

    Each temporal column is sampled independently, so roughly half of every
    start/end, created/updated and order/delivery pair came out reversed.
    """
    from datetime import date as _d471, datetime as _dt471, time as _tm471, timedelta as _td471
    names = [
        str(ci.get('col_name')) for ci in col_info
        if ci.get('col_name') in col_values
        and isinstance(col_values.get(ci.get('col_name')), list)
        and any(k in str(ci.get('attr_type') or '').upper() for k in ('DATE', 'TIMESTAMP'))
    ]
    if len(names) < 2:
        return 0
    order, preds = _v471_temporal_order_plan(names)
    if not order:
        return 0

    n_rows = min(len(col_values[n]) for n in names)
    repaired = 0
    for r in range(n_rows):
        for name in order:
            parents = preds.get(name) or ()
            if not parents:
                continue
            hv = col_values[name][r]
            if not isinstance(hv, (_d471, _dt471)):
                continue
            floor = None
            for lo_name in parents:
                lv = col_values[lo_name][r]
                if not isinstance(lv, (_d471, _dt471)):
                    continue
                lb = lv if isinstance(lv, _dt471) else _dt471.combine(lv, _tm471())
                if floor is None or lb > floor:
                    floor = lb
            if floor is None:
                continue
            is_ts = isinstance(hv, _dt471)
            if hv >= (floor if is_ts else floor.date()):
                continue
            _new = floor + _td471(days=rnd.randint(1, 365), hours=rnd.randint(0, 23))
            col_values[name][r] = _new if is_ts else _new.date()
            repaired += 1
    return repaired


_V471_WORDS = ("north", "south", "east", "west", "central", "summit", "harbor", "aurora",
               "cedar", "vertex", "orion", "atlas", "delta", "zenith", "pioneer",
               "meridian", "cobalt", "granite", "willow", "beacon")
_V471_FIRST = ("James", "Maria", "Chen", "Aisha", "Omar", "Sofia", "Liam", "Yuki", "Noah",
               "Fatima", "Lucas", "Priya", "Ethan", "Ana", "Ibrahim", "Mei", "Diego",
               "Sara", "Jonas", "Leila")
_V471_LAST = ("Okafor", "Nakamura", "Silva", "Haddad", "Novak", "Kim", "Rossi", "Dubois",
              "Fischer", "Almeida", "Kowalski", "Reyes", "Anand", "Bergstrom", "Costa",
              "Ivanov", "Mensah", "Tanaka", "Vargas", "Weber")
_V471_CITY = ("Riverton", "Lakeside", "Fairview", "Kingsport", "Elmwood", "Northgate",
              "Brookfield", "Westbury", "Ashford", "Clearwater")
_V471_STREET = ("Street", "Avenue", "Road", "Boulevard", "Lane", "Way")
_V471_MAIL = ("example.com", "mail.example.net", "corp.example.org")
_V471_ALNUM = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_V471_CATEGORICAL_POOLS = (
    (("status",), ("ACTIVE", "INACTIVE", "PENDING", "COMPLETED", "CANCELLED", "ON_HOLD")),
    (("priority",), ("LOW", "MEDIUM", "HIGH", "CRITICAL")),
    (("severity",), ("INFO", "MINOR", "MAJOR", "CRITICAL")),
    (("frequency", "cadence"), ("DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "ANNUAL")),
    (("currency",), ("USD", "EUR", "GBP", "AED", "JPY", "CAD")),
    (("channel", "method", "mode"), ("ONLINE", "IN_PERSON", "PHONE", "EMAIL", "PARTNER", "MOBILE")),
    (("uom", "unit"), ("EA", "KG", "L", "M", "BOX", "PALLET")),
    (("flag", "indicator", "ind"), ("Y", "N")),
    (("direction",), ("INBOUND", "OUTBOUND")),
    (("language", "locale"), ("EN", "FR", "DE", "ES", "AR", "ZH")),
    (("tier", "grade", "band"), ("A", "B", "C", "D")),
    (("size",), ("XS", "S", "M", "L", "XL")),
    (("gender", "sex"), ("F", "M", "X")),
    (("region",), ("EMEA", "APAC", "AMER", "LATAM")),
    (("state", "province"), ("CA", "NY", "TX", "FL", "IL", "WA", "GA", "OH", "NC", "AZ")),
    (("country",), ("US", "GB", "DE", "FR", "AE", "IN", "JP", "BR", "CA", "AU")),
    (("city", "town"), _V471_CITY),
)

_V471_DERIVED_CATEGORICAL = ("type", "category", "segment", "group", "class",
                             "classification", "reason", "source", "role", "stage",
                             "phase", "disposition", "origin")
_V471_TEXT_TOKENS = ("description", "desc", "notes", "note", "comment", "comments",
                     "summary", "remarks", "remark", "text", "message", "justification")
_V471_PERSON_HINTS = ("person", "customer", "employee", "patient", "contact", "user",
                      "member", "staff", "manager", "owner", "agent", "supervisor",
                      "guardian", "applicant", "passenger", "driver", "author")
_V471_CODE_TOKENS = ("code", "abbreviation", "abbrev", "sku", "serial", "barcode",
                     "reference", "ref", "number", "no", "num", "iso", "key", "hash",
                     "token", "identifier", "upc", "ean")

_V471_NUMERIC_RANGES = (
    (("ratio",), 0.0, 1.0, 3),
    (("rating",), 1.0, 5.0, 1),
    (("pct", "percent", "percentage", "rate", "share", "utilization", "margin",
      "yield", "occupancy"), 0.0, 100.0, 2),
    (("score", "index", "confidence", "probability"), 0.0, 100.0, 1),
    (("age",), 0.0, 95.0, 0),
    (("year", "yr"), 1990.0, 2030.0, 0),
    (("month",), 1.0, 12.0, 0),
    (("quarter",), 1.0, 4.0, 0),
    (("week",), 1.0, 52.0, 0),
    (("latitude", "lat"), -90.0, 90.0, 6),
    (("longitude", "lon", "lng"), -180.0, 180.0, 6),
    (("qty", "quantity", "count", "units", "headcount", "seats"), 1.0, 500.0, 0),
    (("amount", "amt", "price", "cost", "revenue", "fee", "charge", "balance",
      "total", "spend", "budget", "salary", "wage", "premium", "payment",
      "discount", "tax", "subtotal", "value"), 5.0, 50000.0, 2),
    (("weight", "length", "height", "width", "depth", "distance", "area",
      "capacity", "volume"), 0.5, 1000.0, 2),
    (("days",), 1.0, 365.0, 0),
    (("hours", "hrs"), 0.0, 24.0, 1),
    (("minutes", "mins"), 0.0, 1440.0, 0),
    (("seconds", "secs"), 0.0, 3600.0, 0),
    (("temperature", "temp"), -10.0, 45.0, 1),
    (("version", "sequence", "seq", "rank", "level", "attempt", "retry",
      "order", "position", "priority", "step"), 1.0, 10.0, 0),
)


def _v471_semantic_numeric_range(col_name, atype):
    """(lo, hi, scale) inferred from the column name. alias=v471-semantic-stdlib-values"""
    parts = [p for p in str(col_name or "").lower().split('_') if p]
    for tokens, lo, hi, scale in _V471_NUMERIC_RANGES:
        if any(_v471_token_pos(parts, t) >= 0 for t in tokens):
            return (lo, hi, scale)
    _u = str(atype or "").upper()
    if any(k in _u for k in ("BIGINT", "INT", "LONG", "SMALLINT", "TINYINT")):
        return (1.0, 1000.0, 0)
    return (1.0, 10000.0, 2)


def _v471_semantic_values(col_name, atype, sample_count, rnd):
    """Column-name-aware stdlib values, or None when the caller's type default wins.

    Replaces the previous Tier-3 behaviour, which handed the byte-identical list
    ['sample_00001', ...] to every string column in the model and drew every number
    from a flat 1..10000.
    """
    _u = str(atype or "STRING").upper()
    parts = [p for p in str(col_name or "").lower().split('_') if p]
    if not parts:
        return None
    last = parts[-1]

    if any(k in _u for k in ("BIGINT", "INT", "LONG", "SMALLINT", "TINYINT",
                             "DECIMAL", "NUMERIC", "DOUBLE", "FLOAT")):
        lo, hi, scale = _v471_semantic_numeric_range(col_name, atype)
        if scale <= 0:
            return [rnd.randint(int(lo), int(hi)) for _ in range(sample_count)]
        return [round(rnd.uniform(lo, hi), scale) for _ in range(sample_count)]

    if "BOOLEAN" in _u or "DATE" in _u or "TIMESTAMP" in _u:
        return None

    def _stem():
        base = parts[-2] if len(parts) > 1 else parts[0]
        return base.upper()[:8] or "VAL"

    def _abbr():
        return ("".join(p[0] for p in parts)[:4] or "V").upper()

    def _rand_code(k=4):
        return "".join(rnd.choice(_V471_ALNUM) for _ in range(k))

    for tokens, pool in _V471_CATEGORICAL_POOLS:
        if last in tokens:
            return [rnd.choice(pool) for _ in range(sample_count)]

    if last in _V471_DERIVED_CATEGORICAL:
        pool = [f"{_stem()}_{c}" for c in ("A", "B", "C", "D", "E")]
        return [rnd.choice(pool) for _ in range(sample_count)]

    if last == "email" or "email" in parts:
        return [f"{rnd.choice(_V471_FIRST).lower()}.{rnd.choice(_V471_LAST).lower()}"
                f"{rnd.randint(1, 99)}@{rnd.choice(_V471_MAIL)}" for _ in range(sample_count)]
    if last in ("phone", "mobile", "fax", "telephone", "cell", "msisdn"):
        return [f"+1-{rnd.randint(200, 989)}-{rnd.randint(200, 999)}-{rnd.randint(1000, 9999)}"
                for _ in range(sample_count)]
    if last in ("url", "website", "uri", "link", "endpoint"):
        return [f"https://www.{rnd.choice(_V471_WORDS)}{rnd.randint(1, 99)}.example.com"
                for _ in range(sample_count)]
    if last in ("postcode", "postal", "zip", "zipcode"):
        return [f"{rnd.randint(10000, 99999)}" for _ in range(sample_count)]
    if last in ("address", "street", "addressline", "line1", "line2"):
        return [f"{rnd.randint(1, 9999)} {rnd.choice(_V471_WORDS).title()} "
                f"{rnd.choice(_V471_STREET)}" for _ in range(sample_count)]

    if last in ("name", "title", "label", "fullname"):
        if any(h in parts for h in _V471_PERSON_HINTS):
            return [f"{rnd.choice(_V471_FIRST)} {rnd.choice(_V471_LAST)}"
                    for _ in range(sample_count)]
        return [f"{rnd.choice(_V471_WORDS).title()} {_stem().title()} {rnd.randint(1, 999)}"
                for _ in range(sample_count)]
    if last in ("firstname", "forename", "givenname"):
        return [rnd.choice(_V471_FIRST) for _ in range(sample_count)]
    if last in ("lastname", "surname", "familyname"):
        return [rnd.choice(_V471_LAST) for _ in range(sample_count)]

    if last in _V471_TEXT_TOKENS:
        return [f"{_stem().title()} record {i + 1}: {rnd.choice(_V471_WORDS)} "
                f"{rnd.choice(_V471_WORDS)} entry captured for reporting."
                for i in range(sample_count)]

    if last in _V471_CODE_TOKENS:
        return [f"{_abbr()}-{_rand_code(6)}" for _ in range(sample_count)]

    return [f"{_abbr()}-{i + 1:04d}-{_rand_code()}" for i in range(sample_count)]

'''

rep(
    "v471-schema-type-coercion",
    """def _coerce_decimal_to_float(values, atype):
    from decimal import Decimal as _DecCheck
    _u = (atype or "").upper()
    is_double_or_float = (("DOUBLE" in _u) or ("FLOAT" in _u)) and ("DECIMAL" not in _u)
    is_int_family = any(k in _u for k in ("BIGINT", "INT", "LONG", "SMALLINT", "TINYINT"))
    if not (is_double_or_float or is_int_family):
        return values
    out = []
    for v in values:
        if v is None:
            out.append(None)
        elif is_double_or_float and isinstance(v, _DecCheck):
            out.append(float(v))
        elif is_int_family and isinstance(v, _DecCheck):
            out.append(int(v))
        else:
            out.append(v)
    return out""",
    _NEW_HELPERS.strip("\n") + """

def _coerce_decimal_to_float(values, atype):
    \"\"\"Back-compat entry point. The chokepoint is now _v471_coerce_to_schema_type,
    which is schema-accurate rather than decimal-only.\"\"\"
    return _v471_coerce_to_schema_type(values, atype)""",
)

# ------------------------------------------------- 5. per-table PK namespace
rep(
    "v471-sample-pk-namespace (blocks)",
    "    domain_to_db_map = {_get(d, 'domain'): _get(d, 'database_name') for d in domains}\n"
    "    \n"
    "    _sample_shared_resolver = ",
    """    domain_to_db_map = {_get(d, 'domain'): _get(d, 'database_name') for d in domains}

    # alias=v471-sample-pk-namespace — every table used to start its surrogate keys at
    # 10001, so all tables shared one key space. Phase 2 then handed child row #i the
    # parent row of rank #i, which meant every FK value equalled the row's own PK and
    # every relationship in the model was a degenerate identity mapping.
    _v471_pk_blocks = {}
    for _v471_i, _v471_p in enumerate(sorted(
            products,
            key=lambda _pp: (str(_get(_pp, 'domain') or ''), str(_get(_pp, 'product') or '')))):
        _v471_pk_blocks[(_get(_v471_p, 'domain'), _get(_v471_p, 'product'))] = (_v471_i + 1) * 1000000

    def _v471_pk_base(prod_dict):
        _k471 = (prod_dict.get('domain', ''), prod_dict.get('product', ''))
        _b471 = _v471_pk_blocks.get(_k471)
        if _b471 is None:
            _b471 = (1 + (binascii.crc32(f"{_k471[0]}.{_k471[1]}".encode('utf-8')) % 900000)) * 1000000
        return _b471

    logger.info(
        f"[v471-sample-pk-namespace FIRED] allocated {len(_v471_pk_blocks)} disjoint "
        f"PK blocks (stride 1,000,000) so no two tables share a surrogate key value"
    )
    
    _sample_shared_resolver = """,
)

rep(
    "v471-sample-pk-namespace (_gen_pk)",
    """        def _gen_pk(atype, sample_count):
            import uuid as _uuid
            if _type_is_int(atype):
                return [10001 + i for i in range(sample_count)]
            # STRING / other → uuid
            return [str(_uuid.uuid4()) for _ in range(sample_count)]

        def _gen_self_ref(atype, sample_count, rnd):
            if _type_is_int(atype):
                out = [None]
                for row_idx in range(1, sample_count):
                    out.append(10001 + rnd.randint(0, row_idx - 1))
                return out""",
    """        def _gen_pk(atype, sample_count):
            import uuid as _uuid
            if _type_is_int(atype):
                # alias=v471-sample-pk-namespace — disjoint per-table key space.
                _pk_base = _v471_pk_base(p_dict)
                return [_pk_base + 1 + i for i in range(sample_count)]
            # STRING / other → uuid
            return [str(_uuid.uuid4()) for _ in range(sample_count)]

        def _gen_self_ref(atype, sample_count, rnd):
            if _type_is_int(atype):
                _pk_base = _v471_pk_base(p_dict)
                out = [None]
                for row_idx in range(1, sample_count):
                    out.append(_pk_base + 1 + rnd.randint(0, row_idx - 1))
                return out""",
)

# ------------------------------------------------------- 6. stable rnd seed
rep(
    "v471-sample-seed-stable",
    """                rnd.seed(hash(product_name) & 0xFFFFFFFF)""",
    """                # alias=v471-sample-seed-stable — str hash() is PYTHONHASHSEED-salted,
                # so the "reruns produce identical sample data" contract never held.
                rnd.seed(binascii.crc32(
                    f"{p_dict.get('domain', '')}.{product_name}".encode('utf-8')))""",
)

# ------------------------------------ 7. numeric range honours declared type
rep(
    "v471-decimal-range-clamp",
    """        def _sample_numeric(spec, atype, sample_count, rnd):""",
    """        def _sample_numeric(spec, atype, sample_count, rnd, col_name=""):""",
)

rep(
    "v471-decimal-range-clamp (bounds)",
    """            from decimal import Decimal as _Dec
            lo = _coerce_num(spec.get('min', 0), 0)
            hi = _coerce_num(spec.get('max', 1000), 1000)
            if hi <= lo:
                hi = lo + 1
            try:
                scale = int(spec.get('scale', 2))
            except (TypeError, ValueError):
                scale = 2
            scale = max(0, min(6, scale))
""",
    """            from decimal import Decimal as _Dec
            # alias=v471-decimal-range-clamp — an absent min/max used to mean a flat
            # 0..1000 for every column regardless of meaning, and the LLM's scale was
            # applied even when the declared DECIMAL(p,s) could not hold it (the value
            # then overflowed to NULL or failed schema verification).
            _sem_lo, _sem_hi, _sem_scale = _v471_semantic_numeric_range(col_name, atype)
            lo = _coerce_num(spec.get('min', _sem_lo), _sem_lo)
            hi = _coerce_num(spec.get('max', _sem_hi), _sem_hi)
            if hi <= lo:
                hi = lo + 1
            try:
                scale = int(spec.get('scale', _sem_scale))
            except (TypeError, ValueError):
                scale = _sem_scale
            scale = max(0, min(6, scale))
            _atype_decl = str(atype or "").upper()
            if ("DECIMAL" in _atype_decl) or ("NUMERIC" in _atype_decl):
                _p_cl, _s_cl = _v471_decimal_precision(atype)
                scale = min(scale, _s_cl)
                _max_mag = float(10 ** (_p_cl - _s_cl))
                lo = max(lo, -_max_mag + 1.0)
                hi = min(hi, _max_mag - 1.0)
                if hi <= lo:
                    lo, hi = 0.0, max(1.0, _max_mag - 1.0)
""",
)

rep(
    "v471-decimal-range-clamp (call site)",
    """                            col_values[name] = _sample_numeric(spec, atype, sample_count, rnd)""",
    """                            col_values[name] = _sample_numeric(spec, atype, sample_count, rnd, name)""",
)

# --------------------------------------------- 8. semantic Tier-3 defaults
rep(
    "v471-semantic-stdlib-values (_default_by_type)",
    """        def _default_by_type(atype, sample_count, rnd, widget_date_fmt, widget_ts_fmt, boolean_format):
            \"\"\"Deterministic stdlib fallback when the LLM did not describe a column
            (e.g. the JSON was missing it). Uses only random / datetime.\"\"\"
            from datetime import datetime as _dt, timedelta as _td
            if _type_is_int(atype):
                return [rnd.randint(1, 10000) for _ in range(sample_count)]
            if 'DECIMAL' in atype or 'DOUBLE' in atype or 'FLOAT' in atype:
                return [round(rnd.uniform(0.01, 9999.99), 2) for _ in range(sample_count)]""",
    """        def _default_by_type(atype, sample_count, rnd, widget_date_fmt, widget_ts_fmt, boolean_format, col_name=""):
            \"\"\"Deterministic stdlib fallback when the LLM did not describe a column
            (e.g. the JSON was missing it). Uses only random / datetime.

            alias=v471-semantic-stdlib-values — reads the COLUMN NAME first. The
            previous version returned the identical list ['sample_00001', ...] for
            every string column in the model and a flat 1..10000 draw for every
            number, which made the generated data useless for demos and joins.
            \"\"\"
            from datetime import datetime as _dt, timedelta as _td
            try:
                _sem = _v471_semantic_values(col_name, atype, sample_count, rnd)
            except Exception:
                _sem = None
            if _sem is not None:
                return _sem
            if _type_is_int(atype):
                return [rnd.randint(1, 10000) for _ in range(sample_count)]
            if 'DECIMAL' in atype or 'DOUBLE' in atype or 'FLOAT' in atype:
                return [round(rnd.uniform(0.01, 9999.99), 2) for _ in range(sample_count)]""",
)

rep(
    "v471-semantic-stdlib-values (call site)",
    """                col_values[name] = _default_by_type(
                    atype, sample_count, rnd,
                    widget_date_fmt, widget_ts_fmt, boolean_format,
                )""",
    """                col_values[name] = _default_by_type(
                    atype, sample_count, rnd,
                    widget_date_fmt, widget_ts_fmt, boolean_format, name,
                )""",
)

# ------------------------------- 9. temporal repair inside the pool assembler
rep(
    "v471-temporal-order-coherence (pool path)",
    """            # for DOUBLE/FLOAT/INT columns BEFORE Spark sees them. This handles the
            # case where pool/numeric paths leak Decimal into a DOUBLE column.
            for ci in fb_col_info:""",
    """            # alias=v471-temporal-order-coherence — every temporal column is sampled
            # independently, so ~half of each start/end, created/updated and
            # order/delivery pair came out reversed before this pass.
            try:
                _v471_repaired = _v471_enforce_temporal_order(col_values, fb_col_info, rnd)
                if _v471_repaired:
                    logger.info(
                        f"[v471-temporal-order-coherence FIRED] {_p068_product_domain}."
                        f"{_p068_product_name}: repaired {_v471_repaired} out-of-order date value(s)"
                    )
            except Exception as _v471_to_err:
                logger.debug(
                    f"[Sample Gen] temporal-order repair skipped for '{product_name}': {_v471_to_err}"
                )

            # for DOUBLE/FLOAT/INT columns BEFORE Spark sees them. This handles the
            # case where pool/numeric paths leak Decimal into a DOUBLE column.
            for ci in fb_col_info:""",
)

# -------------------------- 10. Tier-2 random fallback gets the same treatment
rep(
    "v471-semantic-stdlib-values (fallback tier)",
    """                if _fk_provider and _fk_values:
                    _p068_col_faker_values[ci['col_name']] = _fk_values
                    _p068_tier_counts["tier2"] += 1
                    logger.info(
                        f"[SAMPLE-TIER2] {_p068_product_domain}.{_p068_product_name}.{ci['col_name']}: "
                        f"faker_provider={_fk_provider}"
                    )
            rows = []""",
    """                if _fk_provider and _fk_values:
                    _p068_col_faker_values[ci['col_name']] = _fk_values
                    _p068_tier_counts["tier2"] += 1
                    logger.info(
                        f"[SAMPLE-TIER2] {_p068_product_domain}.{_p068_product_name}.{ci['col_name']}: "
                        f"faker_provider={_fk_provider}"
                    )
                    continue
                # alias=v471-semantic-stdlib-values — the random fallback tier is what
                # ships whenever the pool LLM call fails, so it needs the same
                # column-name-aware values as the primary path.
                try:
                    _v471_fb_vals = _v471_semantic_values(
                        ci['col_name'], ci['attr_type'], sample_count, _fb_random)
                except Exception:
                    _v471_fb_vals = None
                if _v471_fb_vals is not None:
                    _p068_col_faker_values[ci['col_name']] = _v471_fb_vals
                    _p068_tier_counts["tier3"] += 1
            rows = []""",
)

rep(
    "v471-sample-pk-namespace (fallback tier)",
    """                    if ci['is_pk']:
                        row_values.append(10001 + row_idx)
                    # BUG #4 — Self-ref FK: emit integer in PK range, not None/string.
                    elif ci.get('is_self_ref_fk'):
                        if ('BIGINT' in ci['attr_type'] or 'INT' in ci['attr_type'] or 'LONG' in ci['attr_type']):
                            if row_idx == 0:
                                row_values.append(None)
                            else:
                                row_values.append(10001 + _fb_random.randint(0, max(row_idx - 1, 0)))""",
    """                    if ci['is_pk']:
                        row_values.append(_v471_pk_base(p_dict) + 1 + row_idx)
                    # BUG #4 — Self-ref FK: emit integer in PK range, not None/string.
                    elif ci.get('is_self_ref_fk'):
                        if ('BIGINT' in ci['attr_type'] or 'INT' in ci['attr_type'] or 'LONG' in ci['attr_type']):
                            if row_idx == 0:
                                row_values.append(None)
                            else:
                                row_values.append(_v471_pk_base(p_dict) + 1 + _fb_random.randint(0, max(row_idx - 1, 0)))""",
)

rep(
    "v471-schema-type-coercion (fallback tier)",
    """                rows.append(tuple(row_values))
            logger.info(
                f"[SAMPLE-TIER-SUMMARY] {_p068_product_domain}.{_p068_product_name}: \"""",
    """                rows.append(tuple(row_values))
            # alias=v471-temporal-order-coherence / alias=v471-schema-type-coercion —
            # this tier wrote straight to createDataFrame, so one type contradiction
            # (int into a StringType field) failed the whole product to zero rows.
            if rows:
                _v471_ord = [ci['col_name'] for ci in fb_col_info]
                _v471_cv = {c: [r[i] for r in rows] for i, c in enumerate(_v471_ord)}
                try:
                    _v471_fb_rep = _v471_enforce_temporal_order(_v471_cv, fb_col_info, _fb_random)
                    if _v471_fb_rep:
                        logger.info(
                            f"[v471-temporal-order-coherence FIRED] {_p068_product_domain}."
                            f"{_p068_product_name}: repaired {_v471_fb_rep} out-of-order "
                            f"date value(s) (fallback tier)"
                        )
                except Exception as _v471_fb_err:
                    logger.debug(f"[Sample Gen] temporal-order repair skipped: {_v471_fb_err}")
                for ci in fb_col_info:
                    _v471_cv[ci['col_name']] = _coerce_decimal_to_float(
                        _v471_cv[ci['col_name']], ci.get('attr_type'))
                rows = [tuple(_v471_cv[c][i] for c in _v471_ord) for i in range(len(rows))]
            logger.info(
                f"[SAMPLE-TIER-SUMMARY] {_p068_product_domain}.{_p068_product_name}: \"""",
)

# ------------------------------------------------------- 11. Phase-2 rewrite
_OLD_MERGE = """                    pk_query = f"SELECT DISTINCT `{_actual_tgt_pk}` FROM {source_table} WHERE `{_actual_tgt_pk}` IS NOT NULL ORDER BY `{_actual_tgt_pk}`"
                    pk_values = [row[0] for row in spark.sql(pk_query).collect()]

                    if not pk_values:
                        logger.warning(f"[FK Update]   ⚠️  {fk_col} -> {target_domain}.{target_product}.{target_pk}: No PK values available")
                        continue

                    _fk_view_uid = hashlib.md5(f"{p_domain}.{p_product}.{fk_col}".encode()).hexdigest()[:8]
                    temp_view_name = f"temp_fk_update_{sanitize_name(p_domain)}_{sanitize_name(p_product)}_{sanitize_name(fk_col)}_{_fk_view_uid}"
                    spark.sql(f\"\"\"
                        CREATE OR REPLACE TEMP VIEW {temp_view_name} AS
                        SELECT
                            `{_actual_src_pk}` as pk,
                            ROW_NUMBER() OVER (ORDER BY `{_actual_src_pk}`) - 1 as rn
                        FROM {target_table}
                    \"\"\")

                    lookup_view_name = f"temp_fk_lookup_{sanitize_name(p_domain)}_{sanitize_name(p_product)}_{sanitize_name(fk_col)}_{_fk_view_uid}"
                    pk_values_sql = ", ".join([f"({i}, '{str(v)}')" for i, v in enumerate(pk_values)])
                    spark.sql(f\"\"\"
                        CREATE OR REPLACE TEMP VIEW {lookup_view_name} AS
                        SELECT idx, fk_value
                        FROM (VALUES {pk_values_sql}) AS t(idx, fk_value)
                    \"\"\")

                    merge_sql = f\"\"\"
                        MERGE INTO {target_table} AS target
                        USING (
                            SELECT
                                t.pk,
                                l.fk_value
                            FROM {temp_view_name} t
                            JOIN {lookup_view_name} l ON l.idx = MOD(t.rn, {len(pk_values)})
                        ) AS source
                        ON target.`{_actual_src_pk}` = source.pk
                        WHEN MATCHED THEN UPDATE SET `{actual_fk_col}` = source.fk_value
                    \"\"\"
                    
                    spark.sql(merge_sql)
                    
                    spark.sql(f"DROP VIEW IF EXISTS {temp_view_name}")
                    spark.sql(f"DROP VIEW IF EXISTS {lookup_view_name}")
                    with _fk_lock:
                        _fk_counters["update"] += 1
                        _fk_counters["success"] += 1
                    logger.info(f"[FK Update]   ✅ {fk_col} -> {target_domain}.{target_product}.{target_pk}: Updated with {len(pk_values)} available PK values")"""

_NEW_MERGE = """                    # alias=v471-fk-hash-fanout / alias=v471-selfref-acyclic
                    # The old mapping was MOD(row_number, n) against an inlined VALUES
                    # list of driver-collected PKs cast to strings. Three defects came
                    # out of that: with equal row counts it is a bijection, so every
                    # relationship in the model degenerated to 1:1; every FK column of a
                    # table resolved to the same parent rank, so the columns were
                    # perfectly correlated; and a self-referencing FK mapped each row
                    # onto itself. Quoting every PK as a string also relied on an
                    # implicit STRING->BIGINT store assignment. This is one set-based
                    # join: the parent PK keeps its native type, xxhash64 salted per FK
                    # column decorrelates the columns and gives a realistic fan-out, and
                    # a self-reference can only point at a strictly earlier row.
                    _is_self_ref = (target_domain == p_domain and target_product == p_product)
                    n_parents = spark.sql(
                        f"SELECT COUNT(DISTINCT `{_actual_tgt_pk}`) AS cnt FROM {source_table} "
                        f"WHERE `{_actual_tgt_pk}` IS NOT NULL"
                    ).collect()[0]['cnt']

                    if not n_parents:
                        logger.warning(f"[FK Update]   ⚠️  {fk_col} -> {target_domain}.{target_product}.{target_pk}: No PK values available")
                        continue

                    _fk_salt = f"{p_domain}.{p_product}.{fk_col}".replace("'", "")
                    _fk_col_type = next(
                        (f.dataType.simpleString() for f in table_schema.fields
                         if f.name == actual_fk_col),
                        "string",
                    )
                    _idx_expr = (
                        f"CASE WHEN c.rn = 0 THEN NULL ELSE "
                        f"PMOD(XXHASH64(CAST(c.pk AS STRING), '{_fk_salt}'), c.rn) END"
                        if _is_self_ref else
                        f"PMOD(XXHASH64(CAST(c.pk AS STRING), '{_fk_salt}'), {n_parents})"
                    )
                    merge_sql = f\"\"\"
                        MERGE INTO {target_table} AS target
                        USING (
                            SELECT c.pk AS pk, CAST(p.fk_value AS {_fk_col_type}) AS fk_value
                            FROM (
                                SELECT `{_actual_src_pk}` AS pk,
                                       ROW_NUMBER() OVER (ORDER BY `{_actual_src_pk}`) - 1 AS rn
                                FROM {target_table}
                            ) c
                            LEFT JOIN (
                                SELECT pkv AS fk_value,
                                       ROW_NUMBER() OVER (ORDER BY pkv) - 1 AS prn
                                FROM (
                                    SELECT DISTINCT `{_actual_tgt_pk}` AS pkv
                                    FROM {source_table}
                                    WHERE `{_actual_tgt_pk}` IS NOT NULL
                                )
                            ) p ON p.prn = {_idx_expr}
                        ) AS source
                        ON target.`{_actual_src_pk}` = source.pk
                        WHEN MATCHED THEN UPDATE SET `{actual_fk_col}` = source.fk_value
                    \"\"\"

                    spark.sql(merge_sql)

                    with _fk_lock:
                        _fk_counters["update"] += 1
                        _fk_counters["success"] += 1
                    logger.info(
                        f"[v471-fk-hash-fanout FIRED] {fk_col} -> {target_domain}.{target_product}."
                        f"{target_pk}: hashed onto {n_parents} distinct parent key(s) "
                        f"(self_ref={_is_self_ref}, cast_to={_fk_col_type})"
                    )"""

rep("v471-fk-hash-fanout (merge)", _OLD_MERGE, _NEW_MERGE)


def main() -> int:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    applied = {alias: 0 for alias, _, _ in REPLACEMENTS}
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        text = "".join(src) if isinstance(src, list) else src
        original = text
        for alias, old, new in REPLACEMENTS:
            if old in text:
                applied[alias] += text.count(old)
                text = text.replace(old, new)
        if text != original:
            cell["source"] = text.splitlines(keepends=True)

    missing = [a for a, n in applied.items() if n == 0]
    for alias, n in applied.items():
        print(f"  {'OK ' if n else 'MISS'} {alias}: {n}")
    if missing:
        print(f"\nFAILED — {len(missing)} replacement(s) did not match; notebook untouched.")
        return 1

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {NB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
