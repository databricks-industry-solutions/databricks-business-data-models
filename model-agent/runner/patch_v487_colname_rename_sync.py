#!/usr/bin/env python3
"""v4.8.7 - keep an attribute's physical column_name in step with its logical name.

An attribute rename (SelfFixer multi_fk_missing_label, mutation apply, ...) rewrote
`name`/`attribute` but left `column_name` on the pre-rename value. The DDL emitter
prefers `column_name`, so the physical column kept the OLD name while model.json,
metric views, tags and samples all shipped the NEW one. That divergence is what put
1538 drifted attributes into the 108 published models and 314 unresolvable column
references into their metric views.

Three edits:
  1. both rename sites now carry column_name across (prevents new divergence)
  2. a resync pass at the DDL boundary repairs any divergence that still arrives,
     whatever produced it (closes the class, not just the two known sites)
  3. version bump
"""
import json
import pathlib
import sys

NB = pathlib.Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

DDL_ANCHOR = (
    "    if _attrs_case_fixed > 0:\n"
    "        logger.info(f\"[DDL Diagnostics] Fixed {_attrs_case_fixed} attribute(s) "
    "with case-mismatched domain/product names\")\n"
)

DDL_SYNC = '''
    _v487_desync = []
    for _v487_a in attributes:
        if not isinstance(_v487_a, dict):
            continue
        _v487_logical = _v487_a.get('attribute') or _v487_a.get('name') or ''
        _v487_phys = _v487_a.get('column_name') or ''
        if _v487_logical and _v487_phys and _v487_phys != _v487_logical:
            _v487_a['column_name'] = _v487_logical
            _v487_desync.append(
                f"{_v487_a.get('domain')}.{_v487_a.get('product')}: "
                f"{_v487_phys} -> {_v487_logical}")
    if _v487_desync:
        logger.warning(
            f"  [v487-colname-rename-sync FIRED] resynced {len(_v487_desync)} stale "
            f"column_name(s) to the current logical attribute name before DDL "
            f"(first 8: {_v487_desync[:8]}) alias=v487-colname-rename-sync")
'''

NESTED_OLD = '''            if _new_idx is None:
                _attrs[_old_idx]["name"] = _new_name
'''
NESTED_NEW = '''            if _new_idx is None:
                _attrs[_old_idx]["name"] = _new_name
                if _attrs[_old_idx].get("column_name"):
                    _attrs[_old_idx]["column_name"] = _new_name
'''

FLAT_OLD = '''                                a['attribute'] = new_value
                                _attribute_rename[_old_key] = _new_key
'''
FLAT_NEW = '''                                a['attribute'] = new_value
                                if a.get('column_name'):
                                    a['column_name'] = new_value
                                _attribute_rename[_old_key] = _new_key
'''


def patch_cell(nb, index, old, new, label):
    src = "".join(nb["cells"][index]["source"])
    if new in src:
        print("  %-22s already applied" % label)
        return src, False
    if src.count(old) != 1:
        raise AssertionError("%s: anchor found %d times (need 1)" % (label, src.count(old)))
    return src.replace(old, new, 1), True


def main():
    nb = json.loads(NB.read_text())

    src160 = "".join(nb["cells"][160]["source"])
    if "v487-colname-rename-sync" in src160:
        print("  ddl-resync            already applied")
    else:
        assert src160.count(DDL_ANCHOR) == 1, "DDL anchor not unique"
        src160 = src160.replace(DDL_ANCHOR, DDL_ANCHOR + DDL_SYNC, 1)
        nb["cells"][160]["source"] = src160
        print("  ddl-resync            inserted")

    for idx, old, new, label in [
        (60, NESTED_OLD, NESTED_NEW, "nested-rename"),
        (76, FLAT_OLD, FLAT_NEW, "flat-rename"),
    ]:
        src, changed = patch_cell(nb, idx, old, new, label)
        if changed:
            nb["cells"][idx]["source"] = src
            print("  %-22s patched" % label)

    for i, c in enumerate(nb["cells"]):
        s = "".join(c["source"])
        if "__AGENT_VERSION__ = " in s:
            s2 = s.replace('__AGENT_VERSION__ = "4.8.6"', '__AGENT_VERSION__ = "4.8.7"', 1)
            if s2 != s:
                nb["cells"][i]["source"] = s2
                print("  version               4.8.6 -> 4.8.7")
            break
    else:
        raise AssertionError("version constant not found")

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("written:", NB)
    return 0


if __name__ == "__main__":
    sys.exit(main())
