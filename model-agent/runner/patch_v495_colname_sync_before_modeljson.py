"""v4.9.5 - run the column_name<-name resync BEFORE model.json serialization.

Residual from the v4.9.4 live run (coffee_roastery, catalog vibe_e2e_v494):
  wholesale.order_line had a generic FK finished_package_id that the SelfFixer
  multi_fk_missing_label pass renamed. The sandbox mutation set name/attribute to
  'line_finished_package_id' but left column_name='finished_package_id' stale.
  model.json serializes column_name -> shipped 'finished_package_id'; the DDL runs the
  v487-colname-rename-sync pass (column_name := attribute/name) and created
  'line_finished_package_id'. 1 broken column reference of 1059.

Root cause: v4.9.3 moved the bare-name and FK-align passes ahead of model.json
serialization, but the THIRD DDL-stage pass - v487-colname-rename-sync, which harmonizes
column_name with the logical attribute name after any rename - still ran only inside the
DDL stage, i.e. AFTER model.json was written. Any rename that updates name/attribute but
not column_name (every SelfFixer sandbox rename) therefore drifts model.json vs the DDL.

Fix: run the identical colname-resync inside _v493_resolve_physical_column_names, as the
FIRST pass (before bare-name and FK-align), so the shipped model.json carries the same
physical column names the DDL will emit. Offline-validated against the v4.9.4 artifacts:
drift 1 -> 0. The DDL-stage v487 pass remains as the idempotent backstop.
"""
import json
import pathlib
import re

NB = pathlib.Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def sub_once(src, old, new, label):
    assert src.count(old) == 1, "%s: expected 1 occurrence, got %d" % (label, src.count(old))
    return src.replace(old, new)


def main():
    nb = json.loads(NB.read_text())

    def find(pred):
        hits = [i for i, c in enumerate(nb["cells"])
                if c.get("cell_type") == "code" and pred("".join(c["source"]))]
        assert len(hits) == 1, "expected exactly 1 cell, got %r" % (hits,)
        return hits[0]

    helper_i = find(lambda s: "def _v493_resolve_physical_column_names" in s)
    ver_i = find(lambda s: "__AGENT_VERSION__ = " in s and "agent-version-global" in s)

    s = "".join(nb["cells"][helper_i]["source"])

    # 1. add the colname-resync as the first pass, right after attributes/products are read
    s = sub_once(
        s,
        "    attributes = widgets_values.get(\"attributes\") or []\n"
        "    products = widgets_values.get(\"products\") or []\n"
        "    try:\n"
        "        _bare = _fix_bare_attribute_names(attributes, logger)",
        "    attributes = widgets_values.get(\"attributes\") or []\n"
        "    products = widgets_values.get(\"products\") or []\n"
        "    # v4.9.5: harmonize column_name with the logical attribute name BEFORE serialization.\n"
        "    # A SelfFixer/architect rename updates name/attribute but not column_name; model.json\n"
        "    # serializes column_name while the DDL runs this same resync (v487) and emits the logical\n"
        "    # name - so without this the two artifacts drift (coffee_roastery v4.9.4:\n"
        "    # order_line.finished_package_id in model.json vs line_finished_package_id in the DDL).\n"
        "    _colname_synced = 0\n"
        "    for _cs_a in attributes:\n"
        "        if not isinstance(_cs_a, dict):\n"
        "            continue\n"
        "        _cs_logical = _cs_a.get('attribute') or _cs_a.get('name') or ''\n"
        "        _cs_phys = _cs_a.get('column_name') or ''\n"
        "        if _cs_logical and _cs_phys and _cs_phys != _cs_logical:\n"
        "            _cs_a['column_name'] = _cs_logical\n"
        "            _colname_synced += 1\n"
        "    try:\n"
        "        _bare = _fix_bare_attribute_names(attributes, logger)",
        "colname-sync pass")

    # 2. surface it in the FIRED line
    s = sub_once(
        s,
        "    if logger:\n"
        "        logger.info(\n"
        "            \"  [v493-physical-names-before-modeljson FIRED v4.9.3] callsite=%s bare_renames=%d fk_col_fixes=%d \"\n"
        "            \"- physical names resolved BEFORE serialization so model.json matches the DDL \"\n"
        "            \"alias=v493-physical-names-before-modeljson\" % (callsite, _bare, _fk)\n"
        "        )\n"
        "    return _bare, _fk",
        "    if logger:\n"
        "        logger.info(\n"
        "            \"  [v493-physical-names-before-modeljson FIRED v4.9.3] callsite=%s bare_renames=%d fk_col_fixes=%d \"\n"
        "            \"colname_synced=%d - physical names resolved BEFORE serialization so model.json matches the DDL \"\n"
        "            \"alias=v493-physical-names-before-modeljson\" % (callsite, _bare, _fk, _colname_synced)\n"
        "        )\n"
        "        if _colname_synced:\n"
        "            logger.info(\n"
        "                \"  [v495-colname-sync-before-modeljson FIRED v4.9.5] resynced %d stale column_name(s) to the \"\n"
        "                \"logical attribute name BEFORE serialization - closes the SelfFixer-rename model.json/DDL drift \"\n"
        "                \"alias=v495-colname-sync-before-modeljson\" % _colname_synced\n"
        "            )\n"
        "    return _bare, _fk",
        "fired line")

    nb["cells"][helper_i]["source"] = s

    ver = "".join(nb["cells"][ver_i]["source"])
    new_ver, n = re.subn(r'__AGENT_VERSION__ = "\d+\.\d+\.\d+"', '__AGENT_VERSION__ = "4.9.5"', ver, count=1)
    assert n == 1, "version constant not rewritten"
    nb["cells"][ver_i]["source"] = new_ver

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("patched resolver cell=%d version cell=%d -> 4.9.5" % (helper_i, ver_i))


if __name__ == "__main__":
    main()
