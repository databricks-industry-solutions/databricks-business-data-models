#!/usr/bin/env python3
"""v4.8.8: derive user_sizing_override from the parsed vibe, not only from an LLM boolean.

    python3 runner/patch_v488_sizing_override_deterministic.py [--check]
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD = (
    '    user_sizing_override = bool(params_data.get("user_sizing_override", False))\n'
    '    if user_sizing_override:\n'
    '        logger.info(f"[MODEL-PARAMS] \u26a1 LLM signaled user_sizing_override=True '
    '\u2014 user vibes explicitly set model sizing")\n'
)

NEW = (
    '    _llm_uso = bool(params_data.get("user_sizing_override", False))\n'
    '    _vibe_uso, _vibe_uso_keys = _v488_sizing_override_from_directives(\n'
    '        (widgets_values or {}).get("sizing_directives"))\n'
    '    user_sizing_override = _llm_uso or _vibe_uso\n'
    '    if _llm_uso:\n'
    '        logger.info(f"[MODEL-PARAMS] \u26a1 LLM signaled user_sizing_override=True '
    '\u2014 user vibes explicitly set model sizing")\n'
    '    if _vibe_uso and not _llm_uso:\n'
    '        logger.info(\n'
    '            "[MODEL-PARAMS] \u26a1 [sizing-override-from-vibe FIRED v4.8.8] the LLM omitted "\n'
    '            "user_sizing_override, but the vibe parser resolved explicit sizing "\n'
    '            f"({\', \'.join(_vibe_uso_keys)}); honouring the user over the tier guardrail "\n'
    '            "(CLAUDE.md \u00a73c user-king). alias=sizing-override-from-vibe")\n'
)

HELPER = '''
_V488_SIZING_DIRECTIVE_KEYS = (
    "max_domains", "min_domains",
    "max_total_products", "min_total_products",
    "max_products_per_domain", "min_products_per_domain",
)


def _v488_sizing_override_from_directives(sizing_directives):
    """True when the user's own words already pinned a model size.

    user_sizing_override used to be read ONLY from a boolean the MODEL-PARAMS LLM had to
    remember to emit. When it forgot, the tier guardrail silently outranked the user: on
    coffee_roastery the LLM read "roughly five to seven tables per domain" correctly and
    emitted max_data_products_per_domain=7, then the guardrail clamped it back up to 10
    because the flag was absent. The vibe parser had already resolved the same sentence
    into sizing_directives, so the signal existed deterministically and was simply not
    consulted. Reading it here makes the override impossible to lose to LLM omission.

    Returns (override, keys) so the caller can log WHICH directive earned the override.
    """
    if not isinstance(sizing_directives, dict):
        return False, []
    keys = []
    for key in _V488_SIZING_DIRECTIVE_KEYS:
        value = sizing_directives.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if int(value) > 0:
            keys.append("%s=%d" % (key, int(value)))
    if sizing_directives.get("single_domain_mode"):
        keys.append("single_domain_mode=True")
    if [s for s in (sizing_directives.get("explicit_count_statements") or []) if str(s).strip()]:
        keys.append("explicit_count_statements")
    return bool(keys), keys

'''

ANCHOR = "def _clamp_and_validate_model_params("


def main(argv):
    check = "--check" in argv
    nb = json.load(open(NB))

    vcell = next(i for i, c in enumerate(nb["cells"]) if "__AGENT_VERSION__ =" in "".join(c["source"]))
    src = "".join(nb["cells"][vcell]["source"])
    assert '__AGENT_VERSION__ = "4.8.7"' in src, "expected v4.8.7 as the base version"
    nb["cells"][vcell]["source"] = src.replace('__AGENT_VERSION__ = "4.8.7"',
                                               '__AGENT_VERSION__ = "4.8.8"')

    pcell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and ANCHOR in "".join(c["source"]))
    src = "".join(nb["cells"][pcell]["source"])
    assert OLD in src, "user_sizing_override read site not found verbatim"
    assert "_v488_sizing_override_from_directives" not in src, "patch already applied"
    src = src.replace(OLD, NEW, 1)
    src = src.replace(ANCHOR, HELPER.lstrip("\n") + "\n" + ANCHOR, 1)
    nb["cells"][pcell]["source"] = src

    if check:
        print("would patch: version cell %d, params cell %d" % (vcell, pcell))
        return 0
    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("patched cell %d (helper + read site), version -> 4.8.8" % pcell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
