"""v4.9.3 - resolve physical column names BEFORE model.json is serialized.

Live evidence (coffee_roastery v4.9.1, run vibe_e2e_v491):
  14:14:30  model.json written
  14:14:37  [bare-name-fix-json-sync FIRED] rewrote attributes.json with 4 renamed attrs
  14:14:38  [DDL PRE-FIX] Fixed 8 FK column/reference mismatches to match actual parent PKs

Both passes rename columns AFTER the shipped model.json already left the building, so
the published contract named 12 columns (4 + 8) that do not exist physically:
  wholesale.order_line.sales_order_id      -> DDL order_id
  roasting.roast_batch.operator_id         -> DDL roast_operator_id
  retail.store.code / .name                -> DDL store_code / store_name   ... etc.

Root cause: the physical-name decision is made inside the DDL stage, downstream of the
serialization boundary. Fix = make the decision ONCE, before any artifact is written.
The DDL stage keeps calling the same helper, which is idempotent (second call fixes 0).
"""
import json
import pathlib

NB = pathlib.Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def sub_once(src, old, new, label):
    n = src.count(old)
    assert n == 1, "%s: expected 1 occurrence, got %d" % (label, n)
    return src.replace(old, new)


# ---------------------------------------------------------------- the shared helper
HELPER = '''def _v493_align_fk_column_names_to_parent_pk(products, attributes, config, logger):
    """Rename FK columns so they match the PK they point at, and return the fix count.

    Extracted from step_create_physical_schema_stage1 so the SAME decision can run once
    before model.json serialization instead of only inside the DDL stage. Idempotent:
    once a column already equals its parent PK name the rename branch is skipped, so the
    DDL-stage call after this one reports 0.
    """
    _conv = (config.get("MODEL_CONVENTIONS") or {}).get("data_asset_naming_convention", "snake_case") if config else "snake_case"

    def _cname(name):
        return apply_convention(name, _conv) if name else name

    pk_lookup = {}
    for p in products:
        d = p.get('domain', '')
        pr = p.get('product', '')
        pk = p.get('primary_key', '')
        if d and pr and pk:
            pk_lookup["%s.%s" % (d, pr)] = pk
    fk_col_fixes = 0
    _product_col_index = defaultdict(set)
    for attr in attributes:
        _pc_key = "%s.%s" % (attr.get('domain', ''), attr.get('product', ''))
        _pc_col = attr.get('column_name', '') or attr.get('attribute', '')
        if _pc_col:
            _product_col_index[_pc_key].add(_pc_col)

    for attr in attributes:
        fk_to = attr.get('foreign_key_to', '')
        if not fk_to:
            continue
        fk_parts = fk_to.split('.')
        if len(fk_parts) >= 2:
            fk_target_key = "%s.%s" % (fk_parts[0], fk_parts[1])
            actual_pk = pk_lookup.get(fk_target_key)
            if actual_pk:
                if len(fk_parts) >= 3 and fk_parts[2] != actual_pk:
                    attr['foreign_key_to'] = "%s.%s" % (fk_target_key, actual_pk)
                    fk_col_fixes += 1
                elif len(fk_parts) < 3:
                    attr['foreign_key_to'] = "%s.%s" % (fk_target_key, actual_pk)
                    fk_col_fixes += 1
                attr_name = attr.get('attribute', '')
                if attr_name and actual_pk and attr_name != actual_pk:
                    _this_product_key = "%s.%s" % (attr.get('domain', ''), attr.get('product', ''))
                    _existing_cols = _product_col_index.get(_this_product_key, set())
                    old_attr_name = attr_name
                    _fk_new_name = actual_pk
                    if _fk_new_name in _existing_cols:
                        _fk_target_product = fk_parts[1] if len(fk_parts) >= 2 else ''
                        _fk_new_name = "%s_%s" % (_fk_target_product, actual_pk) if _fk_target_product else actual_pk
                        _fk_new_name = _cname(_fk_new_name) if _fk_new_name else _fk_new_name
                    if _fk_new_name not in _existing_cols and _fk_new_name != old_attr_name:
                        _product_col_index[_this_product_key].discard(old_attr_name)
                        attr['attribute'] = _fk_new_name
                        attr['column_name'] = _fk_new_name
                        _product_col_index[_this_product_key].add(_fk_new_name)
                        fk_col_fixes += 1
                        if logger:
                            logger.debug("[DDL FK-NAME-FIX] Renamed FK column %s.%s \\u2192 %s" % (_this_product_key, old_attr_name, _fk_new_name))
    return fk_col_fixes


def _v493_resolve_physical_column_names(widgets_values, logger, callsite):
    """Run every deterministic physical-name resolution and report what it changed.

    Called at the model.json serialization boundary so the shipped contract carries the
    same column names the DDL will create.
    """
    config = widgets_values.get("config") or {}
    attributes = widgets_values.get("attributes") or []
    products = widgets_values.get("products") or []
    try:
        _bare = _fix_bare_attribute_names(attributes, logger)
    except Exception as _e:
        _bare = 0
        if logger:
            logger.warning("  [v493-physical-names-before-modeljson] bare-name pass failed: %s: %s" % (type(_e).__name__, str(_e)[:200]))
    try:
        _fk = _v493_align_fk_column_names_to_parent_pk(products, attributes, config, logger)
    except Exception as _e:
        _fk = 0
        if logger:
            logger.warning("  [v493-physical-names-before-modeljson] fk-align pass failed: %s: %s" % (type(_e).__name__, str(_e)[:200]))
    widgets_values["attributes"] = attributes
    if logger:
        logger.info(
            "  [v493-physical-names-before-modeljson FIRED v4.9.3] callsite=%s bare_renames=%d fk_col_fixes=%d "
            "- physical names resolved BEFORE serialization so model.json matches the DDL "
            "alias=v493-physical-names-before-modeljson" % (callsite, _bare, _fk)
        )
    return _bare, _fk


'''


def main():
    nb = json.loads(NB.read_text())

    # ---- locate cells by content, never by index (indices drift) -----------------
    def find(pred):
        hits = [i for i, c in enumerate(nb["cells"])
                if c.get("cell_type") == "code" and pred("".join(c["source"]))]
        assert len(hits) == 1, "expected exactly 1 cell, got %r" % (hits,)
        return hits[0]

    ddl_i = find(lambda s: "def step_create_physical_schema_stage1" in s
                 and "mismatches to match actual parent PKs" in s)
    mj_i = find(lambda s: "def step_generate_data_model_json" in s)
    ver_i = find(lambda s: "__AGENT_VERSION__ = " in s and "agent-version-global" in s)

    # ---- 1. insert the helper ahead of the DDL stage ------------------------------
    ddl = "".join(nb["cells"][ddl_i]["source"])
    ddl = sub_once(ddl, "def step_create_physical_schema_stage1(widgets_values):",
                   HELPER + "def step_create_physical_schema_stage1(widgets_values):",
                   "helper insert")

    # ---- 2. the DDL stage now calls the helper instead of its inline copy ---------
    start = ddl.index("    pk_lookup = {}\n    for p in products:\n        d = _get(p, 'domain')")
    end_marker = 'mismatches to match actual parent PKs")\n'
    end = ddl.index(end_marker) + len(end_marker)
    inline = ddl[start:end]
    assert "fk_col_fixes = 0" in inline and len(inline) < 3000, "inline block looks wrong: %d chars" % len(inline)
    ddl = ddl[:start] + (
        "    # v4.9.3: the same resolution already ran at the model.json boundary, so this\n"
        "    # call is the idempotent backstop - it reports 0 on a healthy run.\n"
        "    fk_col_fixes = _v493_align_fk_column_names_to_parent_pk(products, attributes, config, logger)\n"
        "    if fk_col_fixes > 0:\n"
        "        logger.info(f\"[DDL PRE-FIX] Fixed {fk_col_fixes} FK column/reference mismatches to match actual parent PKs\")\n"
    ) + ddl[end:]
    nb["cells"][ddl_i]["source"] = ddl

    # ---- 3. call it at the serialization boundary ---------------------------------
    mj = "".join(nb["cells"][mj_i]["source"])
    mj = sub_once(
        mj,
        '    logger.info("--- Starting Data Model JSON Generation ---")\n'
        '    products_for_export = [dict(p) for p in widgets_values.get("products", [])]',
        '    logger.info("--- Starting Data Model JSON Generation ---")\n'
        '    # The bare-name and FK-column renames used to run only inside the DDL stage, i.e.\n'
        '    # AFTER this function had already shipped model.json - coffee_roastery v4.9.1 published\n'
        '    # 12 columns that no physical table had. Resolve them here so both artifacts agree.\n'
        '    _v493_resolve_physical_column_names(widgets_values, logger, "step_generate_data_model_json")\n'
        '    products_for_export = [dict(p) for p in widgets_values.get("products", [])]',
        "model.json boundary call")
    nb["cells"][mj_i]["source"] = mj

    # ---- 4. version bump ----------------------------------------------------------
    ver = "".join(nb["cells"][ver_i]["source"])
    import re
    new_ver, n = re.subn(r'__AGENT_VERSION__ = "\d+\.\d+\.\d+"', '__AGENT_VERSION__ = "4.9.3"', ver, count=1)
    assert n == 1, "version constant not rewritten"
    nb["cells"][ver_i]["source"] = new_ver

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("patched: helper cell=%d  modeljson cell=%d  version cell=%d" % (ddl_i, mj_i, ver_i))


if __name__ == "__main__":
    main()
