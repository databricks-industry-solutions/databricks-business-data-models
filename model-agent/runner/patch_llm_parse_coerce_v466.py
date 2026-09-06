#!/usr/bin/env python3
"""v4.6.6 patcher: eliminate the issue-#21 bug class (LLM returns scalar/list where a
dict is expected -> unguarded .get/subscript -> AttributeError) by coercing every genuine
LLM-response CONSUMER parse to a dict at the parse boundary via _v466_coerce_llm_obj.

Self-verifying: aborts (writes nothing) unless every asserted replacement count matches.
Deliberately does NOT touch smart_worker_loop / cells 80/92 (type-agnostic wrappers that
guard isinstance themselves) nor model.json-from-disk parses (our own artifacts).
"""
import ast
import json
import re
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

HELPER = '''
def _v466_coerce_llm_obj(obj, site=""):
    """v4.6.6 alias=llm-parse-coerce — coerce an LLM-parsed value to a dict so a consumer
    can safely .get()/subscript it. When a non-dict (list/str/None) is dropped, emit a
    FIRED signal: that is exactly the issue-#21-class AttributeError this guard prevents.
    Reuses _coerce_dict; pure/Serverless-safe (no spark/cache/persist)."""
    if isinstance(obj, dict):
        return obj
    try:
        import logging as _v466_logging
        _v466_logging.getLogger("vibe_agent").warning(
            f"[llm-parse-coerce FIRED v4.6.6] site={site} dropped non-dict LLM value "
            f"type={type(obj).__name__} -> {{}} alias=llm-parse-coerce")
    except Exception:
        pass
    return _coerce_dict(obj)
'''

HELPER_ANCHOR = (
    "def _coerce_list_of_dicts(lst):\n"
    "    \"\"\"Filter non-dict items from a list. Safe for iterating LLM response arrays.\"\"\"\n"
    "    return [item for item in lst if isinstance(item, dict)] if isinstance(lst, list) else []\n"
)

# (cell, VAR, RHS, site_tag, expected_count, extra_lookahead)
TARGETS = [
    (86,  "data", "json.loads(raw_response) if isinstance(raw_response, str) else raw_response", "c86-honesty-direct", 1, ""),
    (86,  "data", "json.loads(output_text) if isinstance(output_text, str) else output_text", "c86-honesty-log", 1, ""),
    (90,  "data", "json.loads(response_text) if isinstance(response_text, str) else response_text", "c90-validator", 1, ""),
    (100, "parsed", "json.loads(raw_response) if isinstance(raw_response, str) else raw_response", "c100-parse-with-llm", 1, ""),
    (100, "_v216_sub_parsed", "json.loads(_v216_sub_raw) if isinstance(_v216_sub_raw, str) else _v216_sub_raw", "c100-sub-req", 1, ""),
    (100, "data", "json.loads(cleaned.strip())", "c100-audit-all", 1, ""),
    (124, "data", "response or {}", "c124-loc-fit-honesty", 1, ""),
    (142, "core_result", "json.loads(clean_json_response(raw_response))", "c142-arch-core", 1, ""),
    (144, "core_result", "json.loads(clean_json_response(raw_response))", "c144-dedup-core", 1, ""),
    (148, "core_result", "json.loads(clean_json_response(raw_response))", "c148-core", 1, ""),
    (148, "_erc_data", "json.loads(_erc_resp) if isinstance(_erc_resp, str) else _erc_resp", "c148-erc", 1, ""),
    (148, "_n3_data", "json.loads(_n3_resp) if isinstance(_n3_resp, str) else _n3_resp", "c148-n3", 1, ""),
    (148, "_dn_data", "json.loads(_dn_resp) if isinstance(_dn_resp, str) else _dn_resp", "c148-dn", 1, ""),
    (148, "_ait_data", "json.loads(_ait_resp) if isinstance(_ait_resp, str) else _ait_resp", "c148-ait", 1, ""),
    (148, "_re_data", "json.loads(_re_resp) if isinstance(_re_resp, str) else _re_resp", "c148-re", 1, ""),
    (150, "core_result", "json.loads(clean_json_response(raw_response))", "c150-qa-core", 1, ""),
    (156, "data", "json.loads(json_string)", "c156-jsonstr", 4, ""),
    (156, "data", "json.loads(products_json)", "c156-products", 1, ""),
    (156, "data", "json.loads(response_text) if isinstance(response_text, str) else response_text", "c156-judge-validate", 1, ""),
    (156, "data", "json.loads(response_text)", "c156-enrich", 1, "(?! if isinstance)"),
]


def main():
    nb = json.load(open(NB))
    cells = nb["cells"]

    def get(ci):
        s = cells[ci]["source"]
        return "".join(s) if isinstance(s, list) else s

    def put(ci, s):
        cells[ci]["source"] = s  # all cells are str in this notebook

    report = []

    # 1) insert helper (idempotent)
    c25 = get(25)
    if "_v466_coerce_llm_obj" not in c25:
        assert c25.count(HELPER_ANCHOR) == 1, f"HELPER_ANCHOR count={c25.count(HELPER_ANCHOR)} (need 1)"
        c25 = c25.replace(HELPER_ANCHOR, HELPER_ANCHOR + HELPER, 1)
        put(25, c25)
        report.append("cell25: inserted _v466_coerce_llm_obj helper")
    else:
        report.append("cell25: helper already present (skip)")

    # 2) wrap targets
    for (ci, var, rhs, tag, exp, la) in TARGETS:
        s = get(ci)
        old = f"{var} = {rhs}"
        new = f'{var} = _v466_coerce_llm_obj({rhs}, site="{tag}")'
        pat = r"(?<![\w_])" + re.escape(old) + la
        found = re.findall(pat, s)
        assert len(found) == exp, f"cell{ci} site={tag}: pattern count={len(found)} expected={exp}"
        # replace via function to avoid backref interpretation in replacement
        s2 = re.sub(pat, lambda m: new, s)
        assert s2 != s, f"cell{ci} site={tag}: no change applied"
        # guard against double-wrap
        assert "_v466_coerce_llm_obj(_v466_coerce_llm_obj" not in s2, f"cell{ci} site={tag}: double-wrap"
        put(ci, s2)
        report.append(f"cell{ci:>3} site={tag:<22} wrapped x{exp}")

    # 3) bump version
    c1 = get(1)
    assert c1.count('__AGENT_VERSION__ = "4.6.5"') == 1, "version anchor 4.6.5 not found exactly once"
    c1 = c1.replace('__AGENT_VERSION__ = "4.6.5"', '__AGENT_VERSION__ = "4.6.6"', 1)
    put(1, c1)
    report.append("cell1: __AGENT_VERSION__ 4.6.5 -> 4.6.6")

    # 4) validate every touched cell still parses (magics stripped)
    def clean(src):
        return "\n".join(("pass  # magic" if l.lstrip().startswith(("%", "!")) else l) for l in src.split("\n"))
    touched = sorted({t[0] for t in TARGETS} | {1, 25})
    for ci in touched:
        try:
            ast.parse(clean(get(ci)))
        except SyntaxError as e:
            print(f"SYNTAX ERROR after patch in cell {ci}: {e}", file=sys.stderr)
            sys.exit(2)

    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("PATCH APPLIED — all asserts passed, all touched cells parse.\n")
    print("\n".join("  " + r for r in report))
    print(f"\nTotal consumer sites wrapped: {sum(t[4] for t in TARGETS)}")


if __name__ == "__main__":
    main()
