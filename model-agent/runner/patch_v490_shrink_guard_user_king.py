#!/usr/bin/env python3
"""v4.9.0: the SelfFixer invariants guard stops blocking a shrink the user asked for.

    python3 runner/patch_v490_shrink_guard_user_king.py [--check]
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

HOLDER_ANCHOR = "_USER_PINNED_DOMAINS_RUNTIME = set()"

HOLDER = '''_USER_SIZING_BOUNDS_RUNTIME = {}


def set_user_sizing_bounds_runtime(sizing_directives, domain_count=None):
    """Publish the user's parsed size bounds for guards that run far from the parser.

    The SelfFixer runs deep inside the closed repair loop with no handle on config or
    widgets, so its invariants guard could only apply a generic rule. Mirrors the
    _USER_PINNED_DOMAINS_RUNTIME precedent rather than threading a new argument through
    every call site. alias=shrink-guard-user-king
    """
    _USER_SIZING_BOUNDS_RUNTIME.clear()
    if not isinstance(sizing_directives, dict):
        return dict(_USER_SIZING_BOUNDS_RUNTIME)

    def _pos_int(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return int(value) if int(value) > 0 else None

    for key in ("max_total_products", "min_total_products",
                "max_products_per_domain", "min_products_per_domain"):
        got = _pos_int(sizing_directives.get(key))
        if got is not None:
            _USER_SIZING_BOUNDS_RUNTIME[key] = got
    got_domains = _pos_int(domain_count)
    if got_domains is not None:
        _USER_SIZING_BOUNDS_RUNTIME["domain_count"] = got_domains
    return dict(_USER_SIZING_BOUNDS_RUNTIME)


def _v490_user_product_bounds(domain_count=None):
    """(ceiling, floor) total-product bounds the user stated, or (None, None)."""
    bounds = _USER_SIZING_BOUNDS_RUNTIME
    if not bounds:
        return None, None
    domains = domain_count or bounds.get("domain_count")
    ceiling = bounds.get("max_total_products")
    floor = bounds.get("min_total_products")
    if ceiling is None and bounds.get("max_products_per_domain") and domains:
        ceiling = bounds["max_products_per_domain"] * int(domains)
    if floor is None and bounds.get("min_products_per_domain") and domains:
        floor = bounds["min_products_per_domain"] * int(domains)
    return ceiling, floor


def shrink_is_user_requested(pre_count, post_count, domain_count=None):
    """True when losing products moves the model TOWARD the size the user asked for.

    The SelfFixer guard treated any product-count decrease as a regression. On
    coffee_roastery run 564741857926303 that rejected the same VREQ-001 mutation twelve
    times: the user asked for "roughly five to seven tables per domain", the fixer
    proposed 32 -> 28 across 4 domains (exactly seven each), and the guard blocked it
    because 28 < 32. A generic invariant outranked an explicit user directive, which is
    the CLAUDE.md 3c breach this exists to prevent, and the model shipped 9 products in
    two domains.

    Only ever permits a shrink that is BOTH downward from an over-ceiling model AND not
    below the user's own floor, so it cannot become a licence to delete.
    """
    try:
        pre_count = int(pre_count)
        post_count = int(post_count)
    except (TypeError, ValueError):
        return False
    if post_count >= pre_count:
        return False
    ceiling, floor = _v490_user_product_bounds(domain_count)
    if ceiling is None or pre_count <= ceiling:
        return False
    return floor is None or post_count >= floor


'''

OLD_GUARD = '''            regressed = (
                post_inv["fk_target_misses"] > pre_inv["fk_target_misses"]
                or post_inv["silo_count"] > pre_inv["silo_count"]
                or post_inv["product_count"] < pre_inv["product_count"]
                or post_inv["domain_count"] < pre_inv["domain_count"]
            )
'''

NEW_GUARD = '''            _shrink_ok = shrink_is_user_requested(
                pre_inv["product_count"], post_inv["product_count"],
                post_inv.get("domain_count"))
            if _shrink_ok:
                try:
                    self.logger.info(
                        f"  [shrink-guard-user-king FIRED v4.9.0] req={rid} product_count "
                        f"{pre_inv['product_count']} \\u2192 {post_inv['product_count']} is a "
                        f"REDUCTION the user asked for, not a regression \\u2014 the generic "
                        f"never-shrink rule is stood down for this mutation "
                        f"(CLAUDE.md \\u00a73c user-king). alias=shrink-guard-user-king")
                except Exception:
                    pass
            regressed = (
                post_inv["fk_target_misses"] > pre_inv["fk_target_misses"]
                or post_inv["silo_count"] > pre_inv["silo_count"]
                or (post_inv["product_count"] < pre_inv["product_count"] and not _shrink_ok)
                or post_inv["domain_count"] < pre_inv["domain_count"]
            )
'''

OLD_PUBLISH = '''    _llm_uso = bool(params_data.get("user_sizing_override", False))
    _vibe_uso, _vibe_uso_keys = _v488_sizing_override_from_directives(
        (widgets_values or {}).get("sizing_directives"))
'''

NEW_PUBLISH = '''    _llm_uso = bool(params_data.get("user_sizing_override", False))
    _sd_for_bounds = (widgets_values or {}).get("sizing_directives")
    _vibe_uso, _vibe_uso_keys = _v488_sizing_override_from_directives(_sd_for_bounds)
    try:
        _published_bounds = set_user_sizing_bounds_runtime(
            _sd_for_bounds,
            domain_count=len(list((widgets_values or {}).get("_user_specified_domains") or []))
            or None)
        if _published_bounds:
            logger.info(
                "[MODEL-PARAMS] [shrink-guard-user-king FIRED v4.9.0] published user size "
                f"bounds {_published_bounds} so the SelfFixer guard can tell a user-requested "
                "shrink from a regression. alias=shrink-guard-user-king")
    except Exception as _sub_e:
        logger.warning(f"[MODEL-PARAMS] publishing user sizing bounds failed: {_sub_e}")
'''


def main(argv):
    check = "--check" in argv
    nb = json.load(open(NB))

    vcell = next(i for i, c in enumerate(nb["cells"]) if "__AGENT_VERSION__ =" in "".join(c["source"]))
    vsrc = "".join(nb["cells"][vcell]["source"])
    assert '__AGENT_VERSION__ = "4.8.9"' in vsrc, "expected v4.8.9 as the base version"

    hcell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and HOLDER_ANCHOR in "".join(c["source"]))
    hsrc = "".join(nb["cells"][hcell]["source"])
    assert "_USER_SIZING_BOUNDS_RUNTIME" not in hsrc, "holder already applied"

    gcell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and "selffixer-invariants-guard" in "".join(c["source"]))
    gsrc = "".join(nb["cells"][gcell]["source"])
    assert OLD_GUARD in gsrc, "invariants guard block not found verbatim"

    pcell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and OLD_PUBLISH in "".join(c["source"]))
    psrc = "".join(nb["cells"][pcell]["source"])

    if check:
        print("would patch: version %d, holder %d, guard %d, publish %d"
              % (vcell, hcell, gcell, pcell))
        return 0

    nb["cells"][vcell]["source"] = vsrc.replace('__AGENT_VERSION__ = "4.8.9"',
                                                '__AGENT_VERSION__ = "4.9.0"')
    nb["cells"][hcell]["source"] = hsrc.replace(HOLDER_ANCHOR, HOLDER + HOLDER_ANCHOR, 1)
    nb["cells"][gcell]["source"] = gsrc.replace(OLD_GUARD, NEW_GUARD, 1)
    nb["cells"][pcell]["source"] = psrc.replace(OLD_PUBLISH, NEW_PUBLISH, 1)
    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("patched holder=%d guard=%d publish=%d, version -> 4.9.0" % (hcell, gcell, pcell))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
