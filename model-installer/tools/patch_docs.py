"""Bring the installer notebook's own documentation in line with the sample widgets.

Run from the repo root: python3 model-installer/tools/patch_docs.py
"""
import json
import pathlib
import sys

NB = pathlib.Path(__file__).resolve().parent.parent / "data-model-installer.ipynb"

WIDGET_TABLE_OLD = """## Parameters (widgets)

Seven widgets, shown in order:

| Widget | Meaning |
|---|---|
| **1. industry** | Industry to install (40 choices). Defaults to a placeholder so you choose explicitly. |
| **2. size** | `mvm` (minimal, recommended) or `ecm` (full). |
| **3. catalog** | Base target catalog. Blank = the industry name. Hosts `_metrics` for multi-catalog layouts. |
| **4. cataloging style** | `One Catalog` (default), `Catalog per Domain`, or `Catalog per Division`. |
| **5. catalog prefix** | Optional prefix for satellite catalogs (multi-catalog styles default to `cat_` when blank). |
| **6. catalog suffix** | Optional suffix for satellite catalogs. |
| **7. local install** | Optional local/Volume folder. If set, SQL is read from here and the GitHub download is skipped. |

Advanced settings are not shown as widgets and use built-in defaults, forwarded to the
launched job automatically: **32 threads x 20-statement batches** (the measured
serverless optimum), metric views **on**, source = this repo @ `main`.
"""

WIDGET_TABLE_NEW = """## Parameters (widgets)

Nine widgets, shown in order:

| Widget | Meaning |
|---|---|
| **1. industry** | Industry to install (40 choices). Defaults to a placeholder so you choose explicitly. |
| **2. size** | `mvm` (minimal, recommended) or `ecm` (full). |
| **3. catalog** | Base target catalog. Blank = the industry name. Hosts `_metrics` for multi-catalog layouts. |
| **4. cataloging style** | `One Catalog` (default), `Catalog per Domain`, or `Catalog per Division`. |
| **5. catalog prefix** | Optional prefix for satellite catalogs (multi-catalog styles default to `cat_` when blank). |
| **6. catalog suffix** | Optional suffix for satellite catalogs. |
| **7. local install** | Optional local/Volume folder. If set, SQL is read from here and the GitHub download is skipped. |
| **8. generate samples** | `No` (default) or `Yes`. `Yes` populates every installed table with synthetic rows after the structure is in place. |
| **9. sample rows** | Rows per table when samples are on: `5`, `10` (default), `20`, `50`, `100`. Applies to every table. |

Advanced settings are not shown as widgets and use built-in defaults, forwarded to the
launched job automatically: **32 threads x 20-statement batches** (the measured
serverless optimum), metric views **on**, source = this repo @ `main`.

## Sample data

Set **8. generate samples** to `Yes` to fill the installed tables with synthetic rows.
Nothing about the install changes otherwise: samples run last, after tables, foreign
keys, tags, and metric views, and are skipped if the structural install left failures.

What the generated data guarantees:

| Guarantee | How |
|---|---|
| Primary keys are unique | Each table draws from its own key block, composite keys unique as a tuple, every key value in the type its column declares. |
| Every foreign key resolves | Parent keys are minted before any child references them, and each child copies a real parent key (whole tuple for composite keys). Cycles and self-references are ordered so no reference points at a key that does not exist yet. |
| Nothing lands half-broken | An in-memory integrity gate re-checks key uniqueness, foreign-key containment, and NOT NULL columns before the first write. If it fails, **no** table is written. |
| Values look plausible | Column names and types drive the value shape: codes come from a vocabulary, emails look like emails, decimals respect their precision and scale, and date pairs that name an order (`created`/`updated`, `start`/`end`) are generated in that order. |
| Reruns are reproducible | A fixed seed (`sample_seed`) means the same install produces the same rows. |

The structure is read back from `information_schema` after the install, so generation
targets the tables, keys, and relationships Unity Catalog actually holds, not what the
model file declared. Views, metric views, and internal schemas are never populated.

An optional pass asks a Databricks Foundation Model endpoint for realistic value pools
for free-text columns (names, descriptions, cities). It is time-boxed per table and
never used for keys: if an endpoint is slow, unavailable, or answers with garbage, that
table falls back to deterministic values and the install continues.

Advanced sample settings, forwarded to the job like the other advanced defaults:
`sample_seed` (default `20260801`), `sample_llm` (`true`), `sample_llm_endpoints`
(comma-separated, defaults to `databricks-gpt-oss-120b` and
`databricks-meta-llama-3-3-70b-instruct`), and `sample_threads` (`8`).
"""

COMMENT_OLD = """# Only FOUR widgets are shown, in order. Everything else (threads, batch size, metric
# views, source repo/ref, session id) uses the defaults in INSTALLER_DEFAULTS below and
# is forwarded automatically to the launched job, so the UI stays minimal."""

COMMENT_NEW = """# Nine widgets are shown, in order. Everything else (threads, batch size, metric views,
# source repo/ref, session id, sample tuning) uses the defaults in INSTALLER_DEFAULTS
# below and is forwarded automatically to the launched job, so the UI stays minimal."""

INTRO_OLD = ("""Install a Databricks **Industry Data Model** (catalog, schemas, tables, foreign keys,
governance tags, and metric views) into a Unity Catalog catalog of your choice.""")

INTRO_NEW = ("""Install a Databricks **Industry Data Model** (catalog, schemas, tables, foreign keys,
governance tags, metric views, and optional sample data) into a Unity Catalog catalog of
your choice.""")


def patch(cell, pairs):
    source = cell["source"]
    text = "".join(source) if isinstance(source, list) else source
    for old, new in pairs:
        if new in text:
            continue
        if old not in text:
            raise SystemExit("anchor not found:\n%s" % old[:120])
        text = text.replace(old, new, 1)
    cell["source"] = text.splitlines(keepends=True) if isinstance(source, list) else text


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    patch(nb["cells"][0], [(INTRO_OLD, INTRO_NEW),
                           (WIDGET_TABLE_OLD, WIDGET_TABLE_NEW)])
    patch(nb["cells"][1], [(COMMENT_OLD, COMMENT_NEW)])
    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print("notebook documentation updated")


if __name__ == "__main__":
    sys.exit(main())
