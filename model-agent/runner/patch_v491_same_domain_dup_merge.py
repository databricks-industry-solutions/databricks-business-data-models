#!/usr/bin/env python3
"""v4.9.1 — three root-cause fixes for the same-domain duplicate-product class.

Live evidence: coffee_roastery run 564741857926303 (v4.8.8) shipped BOTH
`wholesale.invoice` (3 columns: PK + 2 FKs, zero incoming links -> silo) and
`wholesale.wholesale_invoice` (39 columns). One entity became two tables, one of them a
husk. Chain of causation:

  P1  _validate_product_name_collisions Pass 2 buckets duplicates by product NAME only, so
      two products both called `invoice` in the SAME domain look exactly like a cross-domain
      namespace clash. It RENAMES one to `wholesale_invoice`. The flat attributes list keys
      rows by (domain, product), so the rename moved EVERY attribute row onto the renamed
      product and left the original as a 3-column husk. Renaming is the correct repair for a
      cross-domain clash and the WRONG repair for a same-domain duplicate: two products with
      one name in one domain are one entity, and the only sane outcome is a merge.

  P2  The v4.8.9 gates (`duplicate_product_pair`, `duplicate_product_name`) detect the pair
      but neither category is in the SelfFixer `_fixable` whitelist, so the agentic loop is
      never asked to repair it (CLAUDE.md 12.4 step 2: detection without repair is half a gate).

  P3  The architect DID diagnose the duplicate and proposed the merge, but the immutable
      guard rejected it -- `IMMUTABLE VIOLATION: Cannot merge protected product
      'wholesale.invoice'` -- because the LLM core-product pass had marked `invoice`
      protected. Two consecutive IMMUTABLE failures then tripped IMMUTABLE-EARLY-EXIT and
      the ENTIRE architect review was discarded ("did not produce valid output"), losing the
      other 9 valid recommendations with it. Protection means "do not LOSE this entity", not
      "never consolidate it": merging X into X preserves the entity, so it must be allowed.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"


def cell_with(nb, needle, start=0):
    for i in range(start, len(nb["cells"])):
        c = nb["cells"][i]
        s = c["source"] if isinstance(c["source"], str) else "".join(c["source"])
        if needle in s:
            return i, s
    raise AssertionError("no cell contains %r" % needle[:70])


def put(nb, idx, src):
    nb["cells"][idx]["source"] = src


def sub_once(src, old, new, label):
    assert src.count(old) == 1, "%s: expected 1 occurrence, got %d" % (label, src.count(old))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------- P1
STATS_OLD = '''    stats = {
        "renamed_domain_collisions": 0,
        "cross_domain_duplicates": 0,
        "fk_refs_updated": 0,
        "rename_map": {},
    }'''
STATS_NEW = '''    stats = {
        "renamed_domain_collisions": 0,
        "cross_domain_duplicates": 0,
        "same_domain_merges": 0,
        "fk_refs_updated": 0,
        "rename_map": {},
    }
    _p491_merge_drop = []'''

MERGE_OLD = '''        for dup_idx in [_i for _i in idxs if _i != _keep]:
            p = products_data[dup_idx]
            p_dom = (p.get("domain") or "").strip()
            p_name = (p.get("product") or "").strip()
            if not p_dom or not p_name:
                continue
            new_name = _canonicalise_p074(_p074_qualified_rename(p_name, p_dom))'''

MERGE_NEW = '''        for dup_idx in [_i for _i in idxs if _i != _keep]:
            p = products_data[dup_idx]
            p_dom = (p.get("domain") or "").strip()
            p_name = (p.get("product") or "").strip()
            if not p_dom or not p_name:
                continue
            # v4.9.1 alias=dup-product-same-domain-merge -- SAME name in the SAME domain is
            # ONE entity, so it merges; it does not get renamed apart. Qualifying the second
            # occurrence (the pre-v4.9.1 behaviour) manufactures a second table out of thin
            # air, and because attribute rows key by (domain, product) the rename drags EVERY
            # attribute onto the renamed product and leaves the original a PK-plus-FK husk
            # with no incoming links -- a silo the SSOT gate then reports forever. Live:
            # coffee_roastery run 564741857926303 shipped wholesale.invoice (3 cols) beside
            # wholesale.wholesale_invoice (39 cols). Merging is loss-free here precisely
            # BECAUSE the flat attribute rows already share the (domain, product) key: the
            # union is implicit and deduplicate_attributes_in_place collapses the overlap.
            _keeper_p491 = products_data[_keep]
            if (_keeper_p491.get("domain") or "").strip().lower() == p_dom.lower():
                for _field_p491 in ("description", "table_name", "primary_key", "subdomain"):
                    if not str(_keeper_p491.get(_field_p491) or "").strip():
                        _carried = str(p.get(_field_p491) or "").strip()
                        if _carried:
                            _keeper_p491[_field_p491] = p.get(_field_p491)
                # Some pipeline stages carry attributes nested on the product dict as well as
                # in the flat list; union those by name so a nested-shape caller loses nothing.
                if isinstance(p.get("attributes"), list) and p.get("attributes"):
                    _kattrs_p491 = _keeper_p491.get("attributes")
                    if not isinstance(_kattrs_p491, list):
                        _kattrs_p491 = []
                        _keeper_p491["attributes"] = _kattrs_p491
                    _seen_p491 = {
                        _v489_norm_entity(_a.get("attribute") or _a.get("name") or "")
                        for _a in _kattrs_p491 if isinstance(_a, dict)
                    }
                    for _a in p["attributes"]:
                        if not isinstance(_a, dict):
                            continue
                        _an = _v489_norm_entity(_a.get("attribute") or _a.get("name") or "")
                        if _an and _an not in _seen_p491:
                            _kattrs_p491.append(_a)
                            _seen_p491.add(_an)
                _p491_merge_drop.append(dup_idx)
                stats["same_domain_merges"] += 1
                logger.info(
                    f"  [dup-product-same-domain-merge FIRED v4.9.1] {stage_label}: "
                    f"'{p_dom}.{p_name}' declared twice in domain '{p_dom}' \\u2014 merged into the "
                    f"first occurrence instead of renaming the second apart (same name in the "
                    f"same domain is ONE entity; renaming would leave an attribute-less husk "
                    f"table). alias=dup-product-same-domain-merge"
                )
                continue
            new_name = _canonicalise_p074(_p074_qualified_rename(p_name, p_dom))'''

DROP_OLD = '''                        f"alias=dup-product-gate-separator-blind)")
            )

    # duplicate detection. Pass 2 above only matches when the raw product name is'''

DROP_NEW = '''                        f"alias=dup-product-gate-separator-blind)")
            )

    # Deferred to here so the index-based Pass 2 loop above never reads a shifted list.
    if _p491_merge_drop:
        _drop_ids_p491 = {id(products_data[_i]) for _i in _p491_merge_drop}
        _before_p491 = len(products_data)
        products_data[:] = [_p for _p in products_data if id(_p) not in _drop_ids_p491]
        _removed_p491 = _before_p491 - len(products_data)
        # FK targets address a product by "<domain>.<product>", and the merged-away duplicate
        # shared BOTH with its keeper, so every reference still resolves. Only the attribute
        # rows can now collide, and that is exactly what this pass exists to collapse.
        try:
            _dedup_p491 = deduplicate_attributes_in_place(attributes_data, logger)
        except Exception:
            _dedup_p491 = 0
        logger.info(
            f"  [dup-product-same-domain-merge FIRED v4.9.1] {stage_label}: dropped "
            f"{_removed_p491} merged duplicate product row(s); {_dedup_p491} attribute "
            f"row(s) collapsed. alias=dup-product-same-domain-merge"
        )

    # duplicate detection. Pass 2 above only matches when the raw product name is'''


# ---------------------------------------------------------------- P2
# Anchored on the line above the closing brace because the identical two-line tail also
# closes _fixable_info, the INFO-severity subset. Duplicates are error severity: they belong
# in _fixable only.
FIXABLE_OLD = """            'missing_tags', 'pii_tagging_missing',
            'missing_product_description', 'missing_attribute_description',
            'missing_domain_description', 'low_quality_description',
        }"""
FIXABLE_NEW = """            'missing_tags', 'pii_tagging_missing',
            'missing_product_description', 'missing_attribute_description',
            'missing_domain_description', 'low_quality_description',
            # v4.9.1 alias=dup-product-requeue-fixable -- the v4.8.9 gates detect same-domain
            # duplicates but the SelfFixer was never handed them, so a pair that survived the
            # deterministic merge (e.g. one arriving after the collision pass ran) had no
            # repair channel at all and just shipped.
            'duplicate_product_pair', 'duplicate_product_name',
        }"""


# ---------------------------------------------------------------- P3
IMMUT_OLD = '''            for src in (sources or []):
                src_key = f"{domain}.{src}".lower()
                if src_key in _all_protected_products_lower:
                    errors.append(f"IMMUTABLE VIOLATION: Cannot merge protected product '{src_key}'")'''

IMMUT_NEW = '''            for src in (sources or []):
                src_key = f"{domain}.{src}".lower()
                if src_key in _all_protected_products_lower:
                    # v4.9.1 alias=immutable-merge-same-entity-allowed -- protection means the
                    # ENTITY must survive, not that its duplicate rows may never be collapsed.
                    # When the source and the target normalise to the same entity the merge IS
                    # the dedup and the protected entity comes out the other side intact.
                    # Live: coffee_roastery run 564741857926303 proposed
                    # source_products=['invoice','invoice'] -> target 'invoice' to collapse a
                    # literal same-name pair; the guard rejected it twice, IMMUTABLE-EARLY-EXIT
                    # then discarded the WHOLE review including its 9 unrelated valid actions.
                    if target and _v489_norm_entity(src) == _v489_norm_entity(target):
                        logger.info(
                            f"  [immutable-merge-same-entity-allowed FIRED v4.9.1] merge source "
                            f"'{src_key}' is protected but normalises to the merge target "
                            f"'{target}' \\u2014 the entity survives the merge, so this is a dedup, "
                            f"not a deletion. alias=immutable-merge-same-entity-allowed"
                        )
                        continue
                    errors.append(f"IMMUTABLE VIOLATION: Cannot merge protected product '{src_key}'")'''


def main():
    nb = json.load(open(NB))

    i, s = cell_with(nb, "def _validate_product_name_collisions")
    s = sub_once(s, STATS_OLD, STATS_NEW, "P1 stats")
    s = sub_once(s, MERGE_OLD, MERGE_NEW, "P1 merge branch")
    s = sub_once(s, DROP_OLD, DROP_NEW, "P1 deferred drop")
    put(nb, i, s)
    print("P1 same-domain merge      -> cell %d" % i)

    i, s = cell_with(nb, "_fixable = {")
    s = sub_once(s, FIXABLE_OLD, FIXABLE_NEW, "P2 fixable")
    put(nb, i, s)
    print("P2 fixable requeue        -> cell %d" % i)

    i, s = cell_with(nb, "IMMUTABLE VIOLATION: Cannot merge protected product")
    s = sub_once(s, IMMUT_OLD, IMMUT_NEW, "P3 immutable carve-out")
    put(nb, i, s)
    print("P3 immutable same-entity  -> cell %d" % i)

    i, s = cell_with(nb, '__AGENT_VERSION__ = "4.9.0"')
    s = sub_once(s, '__AGENT_VERSION__ = "4.9.0"', '__AGENT_VERSION__ = "4.9.1"', "version")
    put(nb, i, s)
    print("version bump 4.9.0->4.9.1 -> cell %d" % i)

    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    open(NB, "a").write("\n")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
