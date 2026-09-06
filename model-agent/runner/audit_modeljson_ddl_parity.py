"""R-1 parity auditor: does model.json name the columns the DDL actually creates?

The shipped model.json is the contract consumers generate SQL from. If it names a
column the physical table does not have, every such query fails with
UNRESOLVED_COLUMN. coffee_roastery v4.9.1 shipped 12 of them.

Usage:
    python3 runner/audit_modeljson_ddl_parity.py <model_dir>

where <model_dir> holds model.json alongside a schemas/ directory of *_schema_*.sql.
Exit code 0 = parity, 1 = drift, 2 = bad input.
"""
import collections
import glob
import json
import os
import re
import sys

CREATE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"([`\w.${}]+)\s*\((.*?)\n\)\s*(?:USING|TBLPROPERTIES|COMMENT|;)",
    re.S | re.I,
)
COLUMN = re.compile(r"^`([A-Za-z_]\w*)`\s+[A-Za-z]")
NOT_A_COLUMN = ("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")


def products_of(domain):
    return domain.get("products") or domain.get("data_products") or []


def model_columns(model_json_path):
    """{'domain.table': {column: attribute_dict}} as model.json declares it."""
    payload = json.load(open(model_json_path))
    model = payload.get("model", payload)
    out = {}
    for domain in model.get("domains", []):
        dname = (domain.get("name") or "").lower()
        for product in products_of(domain):
            table = (product.get("table_name") or product.get("name") or "").lower()
            cols = {}
            for attr in product.get("attributes", []):
                col = (attr.get("column_name") or attr.get("attribute")
                       or attr.get("name") or "").lower()
                if col:
                    cols[col] = attr
            out["%s.%s" % (dname, table)] = cols
    return out


def ddl_columns(schemas_dir):
    """{'schema.table': {column, ...}} as the DDL will create it."""
    out = collections.defaultdict(set)
    for path in sorted(glob.glob(os.path.join(schemas_dir, "*_schema_*.sql"))):
        text = open(path, errors="ignore").read()
        for qualified, body in CREATE.findall(text):
            parts = [p.strip("`") for p in qualified.split(".")]
            key = ".".join(parts[-2:]).lower()
            for raw in body.split("\n"):
                line = raw.strip().rstrip(",")
                if line.upper().startswith(NOT_A_COLUMN):
                    continue
                hit = COLUMN.match(line)
                if hit:
                    out[key].add(hit.group(1).lower())
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root = argv[1]
    model_path = os.path.join(root, "model.json")
    schemas_dir = os.path.join(root, "schemas")
    for path in (model_path, schemas_dir):
        if not os.path.exists(path):
            print("missing: %s" % path)
            return 2

    declared = model_columns(model_path)
    physical = ddl_columns(schemas_dir)

    only_model = sorted(set(declared) - set(physical))
    only_ddl = sorted(set(physical) - set(declared))
    shared = sorted(set(declared) & set(physical))

    drift = []
    total_cols = 0
    for table in shared:
        total_cols += len(declared[table])
        for col, attr in sorted(declared[table].items()):
            if col not in physical[table]:
                drift.append((table, col, attr.get("foreign_key_to") or ""))

    print("=" * 72)
    print("R-1 parity: model.json vs DDL   (%s)" % root)
    print("=" * 72)
    print("  tables in model.json : %d" % len(declared))
    print("  tables in DDL        : %d" % len(physical))
    print("  columns compared     : %d" % total_cols)
    if only_model:
        print("  tables ONLY in model.json: %s" % ", ".join(only_model[:6]))
    if only_ddl:
        print("  tables ONLY in DDL       : %s" % ", ".join(only_ddl[:6]))
    if drift:
        print("\n  %d column(s) in model.json that the DDL does not create:" % len(drift))
        for table, col, fk in drift:
            print("    %-46s fk=%s" % ("%s.%s" % (table, col), fk or "-"))
    print("\n  VERDICT: %s" % ("DRIFT" if (drift or only_model or only_ddl) else "PARITY"))
    print("=" * 72)
    return 1 if (drift or only_model or only_ddl) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
