#!/usr/bin/env python3
"""v4.8.9: re-arm the duplicate-product gates that a separator-sensitive compare blinded.

    python3 runner/patch_v489_duplicate_product_gates.py [--check]
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD_I3 = '''    # I3: Duplicate product pair detection (M3)
    logger.info("  \U0001f52c Static Analysis: Checking for duplicate product pairs (domain_X vs X)...")
    for domain_name, domain_products in products_by_domain.items():
        product_names = [p.get('product', '').lower() for p in domain_products]
        for pname in product_names:
            prefixed = f"{domain_name.lower()}_{pname}"
            if prefixed in product_names and pname != prefixed:
                issues.append({
                    "category": "duplicate_product_pair",
                    "severity": "error",
                    "message": f"Domain '{domain_name}' has both '{pname}' and '{prefixed}' \u2014 SSOT violation. Merge into '{pname}'.",
                    "details": {"domain": domain_name, "product_a": pname, "product_b": prefixed},
                    "remediation_actions": ["merge"]
                })
'''

NEW_I3 = '''    # I3: Duplicate product pair detection (M3)
    # The compare used to be f"{domain}_{pname}" against pname.lower(), which is blind to
    # the separator. _validate_product_name_collisions renames a duplicate to PascalCase
    # ('WholesaleInvoice') and a later naming pass canonicalises it to snake, so whenever
    # this gate ran between those two steps it compared 'wholesale_invoice' against
    # 'wholesaleinvoice' and reported nothing. Live: coffee_roastery run 564741857926303
    # shipped wholesale.invoice AND wholesale.wholesale_invoice with the gate reporting
    # "0 errors" across all 11 passes. Normalising both sides makes the gate see the pair
    # in whatever casing the pipeline happens to be holding at the time.
    # alias=dup-product-gate-separator-blind
    logger.info("  \U0001f52c Static Analysis: Checking for duplicate product pairs (domain_X vs X)...")
    for domain_name, domain_products in products_by_domain.items():
        _by_norm = {}
        for _p in domain_products:
            _raw = (_p.get('product') or '').strip()
            if _raw:
                _by_norm.setdefault(_v489_norm_entity(_raw), []).append(_raw)
        for _norm, _raws in _by_norm.items():
            # X vs X in ONE domain. No gate covered this: the pair is not a domain-prefix
            # pair, so I3 never looked, and the collision autofix renames it apart into a
            # pair I3 then also missed. The architect reviewer saw it and prescribed the
            # merge; nothing deterministic ever confirmed it landed.
            if len(_raws) > 1:
                issues.append({
                    "category": "duplicate_product_name",
                    "severity": "error",
                    "message": f"Domain '{domain_name}' declares {len(_raws)} products that normalise to '{_norm}' ({', '.join(sorted(set(_raws)))}) \u2014 same-domain SSOT violation. Merge into one entity.",
                    "details": {"domain": domain_name, "products": sorted(set(_raws)),
                                "normalized": _norm},
                    "remediation_actions": ["merge"]
                })
        for _norm, _raws in _by_norm.items():
            _prefixed_norm = _v489_norm_entity(f"{domain_name}_{_raws[0]}")
            if _prefixed_norm == _norm or _prefixed_norm not in _by_norm:
                continue
            _pname = _raws[0]
            _prefixed = _by_norm[_prefixed_norm][0]
            issues.append({
                "category": "duplicate_product_pair",
                "severity": "error",
                "message": f"Domain '{domain_name}' has both '{_pname}' and '{_prefixed}' \u2014 SSOT violation. Merge into '{_pname}'.",
                "details": {"domain": domain_name, "product_a": _pname, "product_b": _prefixed},
                "remediation_actions": ["merge"]
            })
'''

HELPER = '''
def _v489_norm_entity(name):
    """Entity name reduced to letters and digits, for separator-blind comparison.

    'wholesale_invoice', 'WholesaleInvoice' and 'Wholesale Invoice' are the SAME entity to
    every gate that cares about duplication, but they are three different strings to a
    plain .lower() compare. Every duplicate gate must normalise before comparing or it
    silently passes whenever an upstream rename has not been canonicalised yet.
    alias=dup-product-gate-separator-blind
    """
    return re.sub(r'[^a-z0-9]', '', str(name or '').lower())

'''

HELPER_ANCHOR = "def build_products_by_domain(products_data):"

OLD_LABEL = ('''                f"  [P0.74-COLLISION-CROSSDOMAIN] {stage_label}: {old_key} \u2192 {new_key} "
                f"(duplicate of '{p_name}' in another domain)"
''')

NEW_LABEL = ('''                f"  [P0.74-COLLISION-CROSSDOMAIN] {stage_label}: {old_key} \u2192 {new_key} "
                + (f"(duplicate of '{p_name}' in another domain)"
                   if (products_data[_keep].get('domain') or '').strip().lower() != p_dom.lower()
                   else f"(SAME-DOMAIN duplicate of '{p_name}' in '{p_dom}' \u2014 renaming keeps the "
                        f"model valid but this is a merge candidate, not a namespace clash; "
                        f"the duplicate_product_pair gate owns the merge. "
                        f"alias=dup-product-gate-separator-blind)")
''')


def main(argv):
    check = "--check" in argv
    nb = json.load(open(NB))

    vcell = next(i for i, c in enumerate(nb["cells"]) if "__AGENT_VERSION__ =" in "".join(c["source"]))
    vsrc = "".join(nb["cells"][vcell]["source"])
    assert '__AGENT_VERSION__ = "4.8.8"' in vsrc, "expected v4.8.8 as the base version"

    hcell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and HELPER_ANCHOR in "".join(c["source"]))
    hsrc = "".join(nb["cells"][hcell]["source"])
    assert "_v489_norm_entity" not in hsrc, "helper already applied"

    icell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and '"duplicate_product_pair"' in "".join(c["source"]))
    isrc = "".join(nb["cells"][icell]["source"])
    assert OLD_I3 in isrc, "I3 gate block not found verbatim"

    ccell = next(i for i, c in enumerate(nb["cells"])
                 if c["cell_type"] == "code" and "P0.74-COLLISION-CROSSDOMAIN" in "".join(c["source"]))
    csrc = "".join(nb["cells"][ccell]["source"])
    assert OLD_LABEL in csrc, "collision log line not found verbatim"

    if check:
        print("would patch: version %d, helper %d, I3 %d, label %d"
              % (vcell, hcell, icell, ccell))
        return 0

    nb["cells"][vcell]["source"] = vsrc.replace('__AGENT_VERSION__ = "4.8.8"',
                                                '__AGENT_VERSION__ = "4.8.9"')
    nb["cells"][hcell]["source"] = hsrc.replace(
        HELPER_ANCHOR, HELPER.lstrip("\n") + "\n" + HELPER_ANCHOR, 1)
    nb["cells"][icell]["source"] = isrc.replace(OLD_I3, NEW_I3, 1)
    nb["cells"][ccell]["source"] = csrc.replace(OLD_LABEL, NEW_LABEL, 1)
    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("patched helper=%d I3=%d label=%d, version -> 4.8.9" % (hcell, icell, ccell))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
