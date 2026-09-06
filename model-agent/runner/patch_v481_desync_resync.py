"""v4.8.1 FIX 4 alias=v481-export-mirror-resync.

Live coffee_roastery run 984308838662601 logged:
    DESYNC: Memory has 1227 attrs (78 FKs), JSON has 1226 attrs (77 FKs)

step_generate_data_model_json exports from MEMORY, so model.json shipped the correct
1227/78 (verified against the artifact, JobTags and the 78 physical FK constraints).
But the on-disk PRODUCTS_FILE_PATH/ATTRIBUTES_FILE_PATH mirrors stayed one attribute
behind, and the merge + recovery readers in the NEXT step consume those files. The
drift detector only warned.

Fix: rewrite both mirrors from the final export lists at the authoritative artifact
point, reusing the drift-then-rewrite pattern already established by
`self-ref-mem-json-sync` and `bare-name-fix-json-sync`.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

ANCHOR = """
    products = products_for_export
"""

RESYNC = '''
    # The export lists above are authoritative for model.json, but the on-disk mirrors
    # feed the merge + recovery readers in the next step. Rewrite them from the final
    # export state so a stale mirror can never resurrect a dropped attribute or lose a
    # late FK. Same drift-then-rewrite contract as self-ref-mem-json-sync.
    try:
        for _v481_label, _v481_path, _v481_rows in (
            ("products", config.get('PRODUCTS_FILE_PATH'), products_for_export),
            ("attributes", config.get('ATTRIBUTES_FILE_PATH'), attributes_for_export),
        ):
            if not _v481_path or not os.path.exists(_v481_path):
                continue
            try:
                with open(_v481_path, 'r') as _v481_rf:
                    _v481_disk = json.load(_v481_rf) or []
            except Exception:
                _v481_disk = []
            _v481_disk_fks = sum(1 for _r in _v481_disk if isinstance(_r, dict) and _r.get('foreign_key_to'))
            _v481_mem_fks = sum(1 for _r in _v481_rows if isinstance(_r, dict) and _r.get('foreign_key_to'))
            if len(_v481_disk) == len(_v481_rows) and _v481_disk_fks == _v481_mem_fks:
                continue
            with open(_v481_path, 'w') as _v481_wf:
                json.dump(_v481_rows, _v481_wf, indent=2, default=str)
            logger.info(
                f"  [v481-export-mirror-resync FIRED v4.8.1] {_v481_label}: JSON mirror had "
                f"{len(_v481_disk)} rows ({_v481_disk_fks} FKs), export has {len(_v481_rows)} "
                f"({_v481_mem_fks} FKs) — rewrote mirror from the exported state so the merge/"
                f"recovery readers cannot consume stale rows. alias=v481-export-mirror-resync"
            )
    except Exception as _v481_sync_err:
        logger.warning(f"  [v481-export-mirror-resync] non-critical: {_v481_sync_err}")

    products = products_for_export
'''


def main():
    nb = json.load(open(NB))
    cell = nb["cells"][186]
    src = cell.get("source", [])
    text = "".join(src) if isinstance(src, list) else src

    if "v481-export-mirror-resync" in text:
        print("already applied")
        return 0

    assert text.count(ANCHOR) == 1, f"anchor count = {text.count(ANCHOR)}"
    cell["source"] = text.replace(ANCHOR, RESYNC, 1)

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    print("applied: v481-export-mirror-resync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
