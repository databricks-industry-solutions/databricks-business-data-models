"""v4.9.4 - stop the FK aligner from bare-renaming a well-formed labeled FK column.

Residual from the v4.9.3 live run (coffee_roastery, catalog vibe_e2e_v493):
  retail.pos_transaction has TWO FKs to retail.shopper.shopper_id
    - cashier_shopper_id   (labeled at link time)
    - customer_shopper_id  (labeled by the SelfFixer multi_fk_missing_label pass)
  model.json shipped {cashier_shopper_id, shopper_id}; the DDL created
  {shopper_id, customer_shopper_id}. 1 broken column reference of 930.

Root cause: when a column already ends with the parent PK (cashier_shopper_id ->
shopper_id, sales_order_id -> order_id) it is ALREADY a valid role-labeled FK. The
aligner still tried to rename it to the bare PK, and when two such columns share a
parent the bare name collides, so the aligner falls into an order-dependent relabel
branch that resolves one way at the model.json serialization boundary and another way
at the DDL stage (because the SelfFixer relabels one of them in between). The two
artifacts diverge.

Fix (one guard): never rename a column that already ends with '_<parent_pk>'. It is a
well-formed, distinct FK column. Preserving it is order-independent, keeps the semantic
label the SelfFixer/linker chose, and dissolves the collision branch entirely. Only
genuinely malformed columns (operator_id -> parent roast_operator_id) are still aligned,
and that path is deterministic.
"""
import json
import pathlib
import re

NB = pathlib.Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def sub_once(src, old, new, label):
    n = src.count(old)
    assert n == 1, "%s: expected 1 occurrence, got %d" % (label, n)
    return src.replace(old, new)


def main():
    nb = json.loads(NB.read_text())

    def find(pred):
        hits = [i for i, c in enumerate(nb["cells"])
                if c.get("cell_type") == "code" and pred("".join(c["source"]))]
        assert len(hits) == 1, "expected exactly 1 cell, got %r" % (hits,)
        return hits[0]

    helper_i = find(lambda s: "def _v493_align_fk_column_names_to_parent_pk" in s)
    ver_i = find(lambda s: "__AGENT_VERSION__ = " in s and "agent-version-global" in s)

    s = "".join(nb["cells"][helper_i]["source"])

    # 1. add the preserved counter next to fk_col_fixes
    s = sub_once(
        s,
        "    fk_col_fixes = 0\n    _product_col_index = defaultdict(set)",
        "    fk_col_fixes = 0\n    fk_labeled_preserved = 0\n    _product_col_index = defaultdict(set)",
        "counter init")

    # 2. the guard: skip rename when the column already ends with '_<parent_pk>'
    s = sub_once(
        s,
        "                attr_name = attr.get('attribute', '')\n"
        "                if attr_name and actual_pk and attr_name != actual_pk:",
        "                attr_name = attr.get('attribute', '')\n"
        "                # v4.9.4: a column already ending with '_<parent_pk>' (cashier_shopper_id ->\n"
        "                # shopper_id, sales_order_id -> order_id) is a well-formed role-labeled FK.\n"
        "                # Renaming it to the bare PK destroys the label AND triggers the order-dependent\n"
        "                # collision relabel that drifted model.json vs the DDL. Preserve it.\n"
        "                _v494_well_formed_labeled = bool(\n"
        "                    attr_name and actual_pk and attr_name != actual_pk\n"
        "                    and attr_name.endswith('_' + actual_pk)\n"
        "                )\n"
        "                if _v494_well_formed_labeled:\n"
        "                    fk_labeled_preserved += 1\n"
        "                if attr_name and actual_pk and attr_name != actual_pk and not _v494_well_formed_labeled:",
        "rename guard")

    # 3. observable FIRED line before the return
    s = sub_once(
        s,
        "                        if logger:\n"
        "                            logger.debug(\"[DDL FK-NAME-FIX] Renamed FK column %s.%s \\u2192 %s\" % (_this_product_key, old_attr_name, _fk_new_name))\n"
        "    return fk_col_fixes",
        "                        if logger:\n"
        "                            logger.debug(\"[DDL FK-NAME-FIX] Renamed FK column %s.%s \\u2192 %s\" % (_this_product_key, old_attr_name, _fk_new_name))\n"
        "    if logger and fk_labeled_preserved:\n"
        "        logger.info(\n"
        "            \"  [v494-preserve-labeled-fk FIRED v4.9.4] preserved %d well-formed labeled FK \"\n"
        "            \"column(s) (already end with the parent PK) instead of bare-renaming - keeps \"\n"
        "            \"model.json and the DDL deterministic across call-sites \"\n"
        "            \"alias=v494-preserve-labeled-fk\" % fk_labeled_preserved\n"
        "        )\n"
        "    return fk_col_fixes",
        "fired line")

    nb["cells"][helper_i]["source"] = s

    ver = "".join(nb["cells"][ver_i]["source"])
    new_ver, n = re.subn(r'__AGENT_VERSION__ = "\d+\.\d+\.\d+"', '__AGENT_VERSION__ = "4.9.4"', ver, count=1)
    assert n == 1, "version constant not rewritten"
    nb["cells"][ver_i]["source"] = new_ver

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("patched helper cell=%d version cell=%d -> 4.9.4" % (helper_i, ver_i))


if __name__ == "__main__":
    main()
