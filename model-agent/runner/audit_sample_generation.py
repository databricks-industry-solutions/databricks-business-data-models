"""Offline audit of the agent's sample-data generation against a published model.

Runs the notebook's REAL value generators over every product of a model.json and
simulates the Phase-2 FK MERGE exactly as the SQL does, then reports defect
counts per class. No Spark, no LLM, no cluster.

Usage:
    python3 runner/audit_sample_generation.py <model.json> [rows]
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests" / "unit-tests"))
from sample_gen_harness import build_sample_namespace, set_product  # noqa: E402

# Column-name pairs that carry an implied chronological order.
TEMPORAL_ORDER_PAIRS = [
    ("start", "end"), ("begin", "end"), ("open", "close"), ("order", "ship"),
    ("order", "deliver"), ("created", "updated"), ("created", "closed"),
    ("effective", "expir"), ("effective", "end"), ("issue", "expir"),
    ("hire", "termination"), ("admission", "discharge"), ("birth", "death"),
    ("valid_from", "valid_to"), ("from", "to"),
    ("request", "approv"), ("submit", "approv"),
    ("departure", "arrival"),
]

PLACEHOLDER_RE = re.compile(r"^sample_\d{5}$")
_DECIMAL_RE = re.compile(r"DecimalType\((\d+),\s*(\d+)\)")


def _token_role(col_name: str, lo_token: str, hi_token: str):
    """'lo', 'hi' or None for a column against one ordered token pair.

    `effective_end_date` carries both tokens of ("effective", "end"); the token
    nearer the end of the name is the semantic head, so it decides the role.
    """
    parts = [p for p in col_name.lower().split("_") if p]

    def where(token):
        if "_" in token:
            return "_".join(parts).find(token)
        for i, p in enumerate(parts):
            if p == token or (len(token) >= 4 and p.startswith(token)):
                return i
        return -1

    lo_at, hi_at = where(lo_token), where(hi_token)
    if lo_at < 0 and hi_at < 0:
        return None
    if hi_at < 0:
        return "lo"
    if lo_at < 0:
        return "hi"
    return "hi" if hi_at > lo_at else "lo"


def _decimal_fits(value: Decimal, want: str) -> bool:
    """Spark rejects a Decimal that overflows the column's precision or carries
    more fractional digits than its scale, so the audit checks both."""
    m = _DECIMAL_RE.search(want)
    if not m:
        return True
    precision, scale = int(m.group(1)), int(m.group(2))
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int) or -exponent > scale:
        return False
    return abs(value) < Decimal(10) ** (precision - scale)


def load_products(model_path):
    m = json.loads(Path(model_path).read_text())
    model = m.get("model", m)
    products, attributes_by_product = [], {}
    for d in model.get("domains", []):
        dname = d.get("name") or d.get("domain")
        for p in (d.get("products") or d.get("data_products") or []):
            pname = p.get("name") or p.get("product")
            row = {"domain": dname, "product": pname, "primary_key": p.get("primary_key", "")}
            products.append(row)
            attrs = []
            for a in p.get("attributes", []):
                attrs.append({
                    "attribute": a.get("name") or a.get("attribute"),
                    "column_name": a.get("column_name") or a.get("name"),
                    "type": a.get("type") or "STRING",
                    "foreign_key_to": a.get("foreign_key_to") or "",
                    "is_primary_key": a.get("is_primary_key", False),
                    "tags": a.get("tags") or "",
                    "value_regex": a.get("value_regex") or "",
                })
            attributes_by_product[(dname, pname)] = attrs
    return m.get("agent_version", "?"), products, attributes_by_product


def _hash64(*parts) -> int:
    """Stand-in for Spark's XXHASH64.

    Spark's hash is not reachable from python, so the audit measures the
    DISTRIBUTION the MERGE produces (fan-out, 1:1 collapse, self-reference) with
    another well-distributed 64-bit hash. Bit-exact parity with Spark is only
    observable on a live run.
    """
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(blob, digest_size=8).digest(), "big")


def simulate_phase2(rows_by_product, products, attributes_by_product, col_order):
    """Replay the Phase-2 MERGE shipped in v4.7.1.

    Child rows are ranked by their own PK; parents are ranked by their distinct
    PK value. A cross-table FK takes parent rank
    ``PMOD(hash(child_pk, salt), n_parents)``, salted per FK column so two FK
    columns of one table do not resolve to the same parent. A self-referencing
    FK takes ``PMOD(hash(child_pk, salt), child_rank)`` and NULL on rank 0, so
    it can only point at a strictly earlier row.
    """
    valid = {(p["domain"], p["product"]) for p in products}
    pk_pool = {}
    for p in products:
        key = (p["domain"], p["product"])
        rows = rows_by_product.get(key)
        if not rows:
            continue
        cols = col_order[key]
        pk_names = [c["col_name"] for c in cols if c["is_pk"]]
        if not pk_names:
            continue
        idx = [c["col_name"] for c in cols].index(pk_names[0])
        pk_pool[key] = sorted({r[idx] for r in rows if r[idx] is not None})

    assignments = defaultdict(dict)  # child_key -> fk_col -> list of parent values
    unresolved = []
    for key, attrs in attributes_by_product.items():
        if key not in rows_by_product:
            continue
        cols = col_order[key]
        names = [c["col_name"] for c in cols]
        pk_names = [c["col_name"] for c in cols if c["is_pk"]]
        if not pk_names:
            unresolved.append((key, "no-pk", ""))
            continue
        child_pks = sorted(
            r[names.index(pk_names[0])] for r in rows_by_product[key]
        )
        for a in attrs:
            fkt = str(a.get("foreign_key_to") or "").strip()
            if not fkt:
                continue
            parts = fkt.split(".")
            if len(parts) < 3:
                unresolved.append((key, "malformed-fk", fkt))
                continue
            tkey = (parts[0], parts[1])
            if tkey not in valid:
                unresolved.append((key, "target-missing", fkt))
                continue
            parent_pks = pk_pool.get(tkey)
            if not parent_pks:
                unresolved.append((key, "target-empty", fkt))
                continue
            n = len(parent_pks)
            col = a["column_name"]
            salt = f"{key[0]}.{key[1]}.{col}"
            if tkey == key:
                assignments[key][col] = {
                    pk: (None if rank == 0 else parent_pks[_hash64(pk, salt) % rank])
                    for rank, pk in enumerate(child_pks)
                }
            else:
                assignments[key][col] = {
                    pk: parent_pks[_hash64(pk, salt) % n] for pk in child_pks
                }
    return assignments, unresolved, pk_pool


def _synth_pool_spec(col_info):
    """A plausible Tier-1 LLM pool spec, so the audit covers the happy path too."""
    cols = {}
    for c in col_info:
        if c["is_pk"] or c["is_fk"] or c.get("is_self_ref_fk"):
            continue
        t = (c["attr_type"] or "").upper()
        n = c["col_name"]
        if "DATE" in t or "TIMESTAMP" in t:
            cols[n] = {"bucket": "temporal", "range_hint": "last_3y"}
        elif any(k in t for k in ("INT", "LONG", "DECIMAL", "DOUBLE", "FLOAT", "NUMERIC")):
            cols[n] = {"bucket": "numeric", "min": 1, "max": 5000, "scale": 2}
        elif "BOOLEAN" in t:
            cols[n] = {"bucket": "boolean", "true_probability": 0.4}
        else:
            cols[n] = {"bucket": "categorical",
                       "pool": [f"{n[:6].upper()}_{s}" for s in ("A", "B", "C", "D")]}
    return {"columns": cols}


def main():
    model_path = sys.argv[1]
    n_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    version, products, attributes_by_product = load_products(model_path)
    ns = build_sample_namespace(products=products, prompt_variables={
        "date_format": "yyyy-MM-dd",
        "boolean_format": "Boolean (True/False)",
        "product_sample_records": n_rows,
    })
    print(f"model={Path(model_path).parent.parent.name} agent_version={version} "
          f"products={len(products)} rows_per_product={n_rows}")

    tier1 = "--tier1" in sys.argv
    rows_by_product, col_order = {}, {}
    schema_mismatch = Counter()
    for p in products:
        key = (p["domain"], p["product"])
        attrs = attributes_by_product[key]
        set_product(ns, p)
        schema, ci = ns["_build_fallback_col_info"](attrs)
        spec = _synth_pool_spec(ci) if tier1 else {}
        rows = ns["_assemble_rows_from_pools"](
            spec, n_rows, ci, "yyyy-MM-dd", "", "Boolean (True/False)")
        rows_by_product[key] = rows
        col_order[key] = ci
        # A value whose python type contradicts the DataFrame schema type makes
        # spark.createDataFrame raise, which drops the whole product to Tier 2.
        for j, c in enumerate(ci):
            want = repr(ns["map_data_type"](c["attr_type"], to_pyspark=True))
            for v in rows[:5]:
                got = v[j]
                if got is None:
                    continue
                ok = (
                    (want in ("DoubleType", "FloatType") and isinstance(got, float))
                    or (want in ("LongType", "IntegerType") and isinstance(got, int)
                        and not isinstance(got, bool))
                    or (want == "StringType" and isinstance(got, str))
                    or (want == "BooleanType" and isinstance(got, bool))
                    or (want == "DateType" and isinstance(got, date)
                        and not isinstance(got, datetime))
                    or (want == "TimestampType" and isinstance(got, datetime))
                    or (want.startswith("DecimalType") and isinstance(got, Decimal)
                        and _decimal_fits(got, want))
                )
                if not ok:
                    schema_mismatch[f"{c['attr_type']} -> {want} got {type(got).__name__}"] += 1
                break

    # ---------- value-quality metrics ----------
    str_cols = placeholder_cols = 0
    identical_string_cols = Counter()
    total_cols = 0
    num_cols = num_generic_range = 0
    generic_range_cols = Counter()
    enum_cols = 0
    pk_values_by_type = defaultdict(list)
    for p in products:
        key = (p["domain"], p["product"])
        ci = col_order[key]
        names = [c["col_name"] for c in ci]
        rows = rows_by_product[key]
        for j, c in enumerate(ci):
            total_cols += 1
            vals = [r[j] for r in rows]
            atype = (c["attr_type"] or "").upper()
            if c["is_pk"]:
                # A composite key has several PK columns; uniqueness is a property
                # of the tuple, so they are tracked per column and zipped below.
                pk_values_by_type[key].append(vals)
            if (c.get("attr_meta") or {}).get("value_regex"):
                enum_cols += 1
            if "STRING" in atype and not c["is_pk"] and not c["is_fk"]:
                str_cols += 1
                if vals and all(isinstance(v, str) and PLACEHOLDER_RE.match(v) for v in vals):
                    placeholder_cols += 1
                    identical_string_cols[tuple(vals[:3])] += 1
            if not c["is_pk"] and not c["is_fk"] and any(
                t in atype for t in ("INT", "LONG", "DECIMAL", "DOUBLE", "FLOAT", "NUMERIC")
            ):
                num_cols += 1
                nums = [float(v) for v in vals if isinstance(v, (int, float, Decimal))]
                # The untuned fallback draws uniformly over 1..10000 (1..1000 for
                # integers), so a column landing on both ends of that span got no
                # semantic range from its name.
                lo_edge, hi_edge = (950.0, 1000.0) if any(
                    t in atype for t in ("INT", "LONG", "BIGINT", "SMALLINT")
                ) else (9000.0, 10000.0)
                if nums and min(nums) <= 2.0 and lo_edge <= max(nums) <= hi_edge:
                    num_generic_range += 1
                    generic_range_cols[c["col_name"]] += 1

    # PK values shared BETWEEN tables (the degenerate key space)
    all_pks = Counter()
    for k, cols in pk_values_by_type.items():
        for v in {v for col in cols for v in col}:
            all_pks[v] += 1
    colliding = sum(1 for v, c in all_pks.items() if c > 1)
    max_share = max(all_pks.values()) if all_pks else 0

    # duplicate keys within a table, on the full (composite) key tuple
    dup_pk_tables = [
        k for k, cols in pk_values_by_type.items()
        if cols and len(set(zip(*cols))) != len(cols[0])
    ]

    # ---------- temporal coherence ----------
    temporal_violations = 0
    temporal_pairs_checked = 0
    temporal_examples = []
    for p in products:
        key = (p["domain"], p["product"])
        ci = col_order[key]
        names = [c["col_name"] for c in ci]
        rows = rows_by_product[key]
        date_idx = [
            (i, c["col_name"]) for i, c in enumerate(ci)
            if "DATE" in (c["attr_type"] or "").upper()
            or "TIMESTAMP" in (c["attr_type"] or "").upper()
        ]
        for i, ni in date_idx:
            for j, nj in date_idx:
                if i >= j:
                    continue
                for lo_tok, hi_tok in TEMPORAL_ORDER_PAIRS:
                    role_a = _token_role(ni, lo_tok, hi_tok)
                    role_b = _token_role(nj, lo_tok, hi_tok)
                    if role_a == "lo" and role_b == "hi":
                        lo_i, hi_i = i, j
                    elif role_b == "lo" and role_a == "hi":
                        lo_i, hi_i = j, i
                    else:
                        continue
                    temporal_pairs_checked += 1
                    bad = 0
                    for r in rows:
                        lv, hv = r[lo_i], r[hi_i]
                        if lv is None or hv is None:
                            continue
                        lv2 = lv.date() if isinstance(lv, datetime) else lv
                        hv2 = hv.date() if isinstance(hv, datetime) else hv
                        if isinstance(lv2, date) and isinstance(hv2, date) and hv2 < lv2:
                            bad += 1
                    temporal_violations += bad
                    if bad and len(temporal_examples) < 6:
                        temporal_examples.append(
                            f"{key[0]}.{key[1]}: {names[lo_i]} > {names[hi_i]} in {bad}/{len(rows)} rows")
                    break

    # ---------- FK / linking metrics ----------
    assignments, unresolved, pk_pool = simulate_phase2(
        rows_by_product, products, attributes_by_product, col_order)

    fk_total = sum(
        1 for attrs in attributes_by_product.values()
        for a in attrs if str(a.get("foreign_key_to") or "").strip()
    )
    fk_assigned = sum(len(v) for v in assignments.values())
    self_ref_rows = self_ref_total = 0
    one_to_one = 0
    fanout_hist = Counter()
    fk_type_mismatch = 0
    fk_equals_own_pk_rows = fk_rows_total = 0
    for key, cols in assignments.items():
        ci = col_order[key]
        names = [c["col_name"] for c in ci]
        pkname = next((c["col_name"] for c in ci if c["is_pk"]), None)
        for col, mapping in cols.items():
            fk_rows_total += len(mapping)
            fk_equals_own_pk_rows += sum(1 for pk, v in mapping.items() if pk == v)
            linked = {pk: v for pk, v in mapping.items() if v is not None}
            distinct_parents = len(set(linked.values()))
            n_child = len(linked)
            if distinct_parents == n_child and n_child > 1:
                one_to_one += 1
            fanout_hist[round(n_child / max(1, distinct_parents))] += 1
            # self-reference: child pk == assigned parent value
            attrs = attributes_by_product[key]
            a = next((x for x in attrs if x["column_name"] == col), None)
            if a:
                parts = str(a["foreign_key_to"]).split(".")
                if len(parts) >= 2 and (parts[0], parts[1]) == key:
                    self_ref_total += n_child
                    self_ref_rows += sum(1 for pk, v in mapping.items() if pk == v)
                else:
                    tkey = (parts[0], parts[1])
                    tattrs = attributes_by_product.get(tkey, [])
                    tpk = next((x for x in tattrs if (x["column_name"] or "") == parts[2]), None)
                    if tpk and (tpk["type"] or "").split("(")[0].upper() != \
                            (a["type"] or "").split("(")[0].upper():
                        fk_type_mismatch += 1

    # ---------- report ----------
    def pct(a, b):
        return f"{a}/{b} = {100.0*a/b:.1f}%" if b else f"{a}/0"

    print(f"\n== SPARK SCHEMA FIT (tier1={tier1}) ==")
    if schema_mismatch:
        for k, v in schema_mismatch.most_common(10):
            print(f"  MISMATCH {k}: {v} columns")
    else:
        print("  no python-type / DataFrame-schema contradictions")

    print("\n== VALUE GENERATION ==")
    print(f"  columns generated                : {total_cols}")
    print(f"  STRING non-key columns           : {str_cols}")
    print(f"  ...filled with 'sample_00001'    : {pct(placeholder_cols, str_cols)}")
    print(f"  distinct placeholder value-sets  : {len(identical_string_cols)} "
          f"(1 means every such column is byte-identical)")
    print(f"  numeric non-key columns          : {num_cols}")
    print(f"  ...left on the untuned default  : {pct(num_generic_range, num_cols)}")
    for name, n in generic_range_cols.most_common(8):
        print(f"      {name}: {n} table(s)")
    print(f"  attributes carrying value_regex  : {enum_cols}")
    print("\n== PRIMARY KEYS ==")
    print(f"  tables with duplicate PKs        : {len(dup_pk_tables)}")
    print(f"  PK values shared across tables   : {pct(colliding, len(all_pks))}")
    print(f"  max tables sharing one PK value  : {max_share}")
    print("\n== TEMPORAL COHERENCE ==")
    print(f"  ordered date pairs detected      : {temporal_pairs_checked}")
    print(f"  row-level order violations       : {temporal_violations}")
    for e in temporal_examples:
        print(f"    - {e}")
    print("\n== FOREIGN KEYS / LINKING ==")
    print(f"  FK columns declared              : {fk_total}")
    print(f"  FK columns Phase-2 would fill    : {pct(fk_assigned, fk_total)}")
    print(f"  unresolved (left NULL)           : {len(unresolved)} "
          f"{Counter(u[1] for u in unresolved).most_common()}")
    print(f"  FKs collapsing to 1:1            : {pct(one_to_one, fk_assigned)}")
    print(f"  fan-out histogram (children/parent): {sorted(fanout_hist.items())}")
    print(f"  FK value == the row's own PK     : {pct(fk_equals_own_pk_rows, fk_rows_total)}")
    print(f"  self-ref FK rows pointing to self: {pct(self_ref_rows, self_ref_total)}")
    print(f"  FK type != target PK type        : {fk_type_mismatch}")


if __name__ == "__main__":
    main()
