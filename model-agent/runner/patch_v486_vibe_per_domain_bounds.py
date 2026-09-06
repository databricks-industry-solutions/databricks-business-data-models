#!/usr/bin/env python3
"""v4.8.6 - the vibe's per-domain product bounds must reach the generator.

The vibe parser already resolves "roughly five to seven tables per domain" into
sizing_directives{min,max}_products_per_domain. The MODEL-PARAMS apply loop is the
single place the generator's hard range (min/max_data_products_per_domain) is set,
and it never read those directives, so the tier heuristic won: coffee_roastery asked
for 5-7 and the generator was told 7-13, then obediently built 8-9.
"""
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parent.parent / "agent" / "dbx_vibe_modelling_agent.ipynb"

ANCHOR = '''    logger.info("")
    logger.info("-" * 80)
    logger.info(f"[MODEL-PARAMS] Applying LLM-determined parameters for scope '{model_scope}':")'''

CLAMP = '''    # The user's per-domain product bounds are already parsed into sizing_directives, but
    # this apply loop is the ONLY place the generator's hard range is set. Reading them
    # here steers the prompt instead of trimming the model afterwards, so the count is met
    # by construction rather than by a clamp that fights the LLM (CLAUDE.md 3c + 3a-bis).
    # alias=vibe-per-domain-bounds-clamp
    try:
        _vpb = (widgets_values or {}).get("sizing_directives") or {}
        _vpb_max = _vpb.get("max_products_per_domain")
        _vpb_min = _vpb.get("min_products_per_domain")
        _vpb_notes = []
        if _vpb_max is not None:
            _vpb_old = validated_params.get("max_data_products_per_domain")
            # only ever tighten: a heuristic that is already stricter than the user asked
            # for stays, because the user stated a ceiling, not a quota to fill.
            if _vpb_old is None or int(_vpb_old) > int(_vpb_max):
                validated_params["max_data_products_per_domain"] = int(_vpb_max)
                _vpb_notes.append(f"max_data_products_per_domain {_vpb_old} -> {int(_vpb_max)}")
        _vpb_eff_max = validated_params.get("max_data_products_per_domain")
        if _vpb_min is not None:
            _vpb_old_min = validated_params.get("min_data_products_per_domain")
            _vpb_new_min = int(_vpb_min)
            if _vpb_eff_max is not None and _vpb_new_min > int(_vpb_eff_max):
                _vpb_new_min = int(_vpb_eff_max)
            if _vpb_old_min is None or int(_vpb_old_min) != _vpb_new_min:
                validated_params["min_data_products_per_domain"] = _vpb_new_min
                _vpb_notes.append(f"min_data_products_per_domain {_vpb_old_min} -> {_vpb_new_min}")
        else:
            # a lowered ceiling can strand a heuristic floor above it; min > max would make
            # the generated range impossible to satisfy.
            _vpb_old_min = validated_params.get("min_data_products_per_domain")
            if (_vpb_eff_max is not None and _vpb_old_min is not None
                    and int(_vpb_old_min) > int(_vpb_eff_max)):
                validated_params["min_data_products_per_domain"] = int(_vpb_eff_max)
                _vpb_notes.append(f"min_data_products_per_domain {_vpb_old_min} -> {int(_vpb_eff_max)} (floor exceeded lowered ceiling)")
        if _vpb_notes:
            logger.info("[MODEL-PARAMS] \\u26a1 [vibe-per-domain-bounds-clamp FIRED v4.8.6] user vibe "
                        f"asked min={_vpb_min} max={_vpb_max} products per domain; "
                        + "; ".join(_vpb_notes)
                        + " (CLAUDE.md 3c user-king). alias=vibe-per-domain-bounds-clamp")
    except Exception as _vpb_e:
        logger.warning(f"[MODEL-PARAMS] vibe per-domain bounds clamp failed: {_vpb_e}")

'''


def main() -> int:
    nb = json.loads(NB.read_text())
    cells = nb["cells"]

    target = None
    for i, c in enumerate(cells):
        if c.get("cell_type") != "code":
            continue
        src = c["source"]
        text = "".join(src) if isinstance(src, list) else src
        if ANCHOR in text and "max_data_products_per_domain" in text:
            target = i
            break
    if target is None:
        print("FAIL: apply-loop anchor not found")
        return 1

    src = cells[target]["source"]
    was_list = isinstance(src, list)
    text = "".join(src) if was_list else src

    if "vibe-per-domain-bounds-clamp" in text:
        print("already patched")
        return 0
    if text.count(ANCHOR) != 1:
        print(f"FAIL: anchor is not unique in cell {target} (count={text.count(ANCHOR)})")
        return 1

    text = text.replace(ANCHOR, CLAMP + ANCHOR, 1)
    cells[target]["source"] = text.splitlines(keepends=True) if was_list else text

    # This fix ships in 4.8.6 alongside the metric-view rename work already staged at
    # that version, so an existing 4.8.6 is the target, not a conflict.
    bumped = False
    for c in cells:
        if c.get("cell_type") != "code":
            continue
        s = c["source"]
        wl = isinstance(s, list)
        t = "".join(s) if wl else s
        _cur = __import__("re").search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', t)
        if _cur and tuple(int(g) for g in _cur.groups()) >= (4, 8, 6):
            bumped = True
            break
        if '__AGENT_VERSION__ = "4.8.5"' in t:
            t = t.replace('__AGENT_VERSION__ = "4.8.5"', '__AGENT_VERSION__ = "4.8.6"', 1)
            c["source"] = t.splitlines(keepends=True) if wl else t
            bumped = True
            break
    if not bumped:
        print("FAIL: __AGENT_VERSION__ is neither 4.8.5 nor 4.8.6")
        return 1

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print(f"patched cell {target}; version -> 4.8.6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
