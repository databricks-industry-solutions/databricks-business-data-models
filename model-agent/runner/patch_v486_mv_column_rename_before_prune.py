#!/usr/bin/env python3
"""v4.8.6 mv-column-rename-before-prune.

The physical prevalidator finds a metric view referencing a column the source table does
not have and deletes the dimension. That keeps the view installable but silently costs
analytic content, and it treats every miss as a typo. The 24 published models repaired
this session show the miss is overwhelmingly a RENAME: the metric-view generator emits
the logical column with its role prefix while the DDL naming convention normalizes it.

    origin_plant_id -> plant_id      member_identity_id -> identity_id
    dealer_account_id -> account_id  primary_x_customer_party_id -> party_id

Prevalidation is the last point where the PHYSICAL columns are known, so it is the right
place to rename. A reference is renamed only when exactly one column of the same table
matches on whole underscore-delimited segments; anything ambiguous still prunes.
"""
import json
import re
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent/dbx_vibe_modelling_agent.ipynb"

OLD_PRUNE = """                def _mvcp_prune_blocks(_seg):
                    _keptb = []; _badb = set()
                    for _blk in _mvcp_split_blocks(_seg):
                        _blkbad = set()
                        for _bl in _blk:
                            _em = _mvcp_re.match(r'\\s*expr:\\s*(.+?)\\s*$', _bl)
                            if _em:
                                _blkbad |= _mvcp_bad_in_expr(_em.group(1).strip().rstrip(',').strip())
                        if _blkbad:
                            _badb |= _blkbad
                        else:
                            _keptb.append(_blk)
                    return _keptb, _badb
"""

NEW_PRUNE = """                _mvcp_renamed_here = []
                def _mvcp_resolve(_t):
                    # The miss is usually a RENAME, not a typo: the generator emits the
                    # logical column with its role prefix (origin_plant_id) while the DDL
                    # naming convention normalized it (plant_id). Match on whole
                    # underscore-delimited segments so `status` can never become
                    # `complaint_status` unless it is the only candidate on the table.
                    # alias=mv-column-rename-before-prune
                    _cands = sorted(set(_c for _c in _src_cols
                                        if _t.endswith('_' + _c) or _c.endswith('_' + _t)))
                    if len(_cands) == 1:
                        return _cands[0]
                    if len(_cands) > 1:
                        _long = max(len(_c) for _c in _cands)
                        _best = [_c for _c in _cands if len(_c) == _long]
                        if len(_best) == 1:
                            return _best[0]
                    return None
                def _mvcp_block_name(_blk):
                    for _bl in _blk:
                        _nm = _mvcp_re.match(r'\\s*-\\s*name:\\s*\\"?([^\\"]+?)\\"?\\s*$', _bl)
                        if _nm:
                            return _nm.group(1).strip().lower()
                    return None
                def _mvcp_prune_blocks(_seg):
                    _keptb = []; _badb = set()
                    _parsed = []
                    for _blk in _mvcp_split_blocks(_seg):
                        _blkbad = set()
                        for _bl in _blk:
                            _em = _mvcp_re.match(r'\\s*expr:\\s*(.+?)\\s*$', _bl)
                            if _em:
                                _blkbad |= _mvcp_bad_in_expr(_em.group(1).strip().rstrip(',').strip())
                        _parsed.append((_blk, _blkbad))
                    # A healthy block owns its name: a renamed one that would collide with
                    # it (guest_profile_id and profile_id both -> profile_id) yields.
                    _taken = set(_n for _n in (_mvcp_block_name(_b) for _b, _d in _parsed if not _d) if _n)
                    for _blk, _blkbad in _parsed:
                        if not _blkbad:
                            _keptb.append(_blk)
                            continue
                        _map = {}
                        for _t in sorted(_blkbad):
                            _tgt = _mvcp_resolve(_t)
                            if not _tgt:
                                _map = None
                                break
                            _map[_t] = _tgt
                        if not _map:
                            _badb |= _blkbad
                            continue
                        _new = list(_blk)
                        for _old, _tgt in sorted(_map.items()):
                            _new = [_mvcp_re.sub(r'\\b%s\\b' % _mvcp_re.escape(_old), _tgt, _x) for _x in _new]
                        _nm = _mvcp_block_name(_new)
                        if _nm and _nm in _taken:
                            _badb |= _blkbad
                            continue
                        if _nm:
                            _taken.add(_nm)
                        _keptb.append(_new)
                        _mvcp_renamed_here.extend(sorted(_map.items()))
                    return _keptb, _badb
"""

# Report renames next to the prune reasons for the same view.
OLD_REASON = """                if _all_bad:
                    _vname = _extract_metric_view_name_from_statement(_stmt)
                    _drop_reasons2.append((_vname, f"physical `{_src_sch}.{_src_tbl}` missing col(s) {sorted(_all_bad)[:5]} -- pruned offending block(s), view KEPT"))"""
NEW_REASON = """                if _mvcp_renamed_here:
                    _vname = _extract_metric_view_name_from_statement(_stmt)
                    _rename_reasons2.append((_vname, sorted(set(_mvcp_renamed_here))))
                if _all_bad:
                    _vname = _extract_metric_view_name_from_statement(_stmt)
                    _drop_reasons2.append((_vname, f"physical `{_src_sch}.{_src_tbl}` missing col(s) {sorted(_all_bad)[:5]} -- pruned offending block(s), view KEPT"))"""

OLD_INIT = """            _kept2, _dropped2, _drop_reasons2 = [], [], []"""
NEW_INIT = """            _kept2, _dropped2, _drop_reasons2 = [], [], []
            _rename_reasons2 = []"""

OLD_LOG = """            if _drop_reasons2:
                logger.warning(f"  [mv-column-prevalidate-prune FIRED v3.4.5]"""
NEW_LOG = """            if _rename_reasons2:
                _rn_total = sum(len(_p) for _v, _p in _rename_reasons2)
                logger.info(f"  [mv-column-rename-before-prune FIRED v4.8.6] renamed {_rn_total} column ref(s) onto the physical column in {len(_rename_reasons2)} metric view(s); the dimension is KEPT instead of pruned alias=mv-column-rename-before-prune")
                for _vname, _pairs in _rename_reasons2:
                    logger.info(f"  [mv-column-rename-before-prune]   {_vname}: " + ", ".join(f"{_o} -> {_n}" for _o, _n in _pairs))
            if _drop_reasons2:
                logger.warning(f"  [mv-column-prevalidate-prune FIRED v3.4.5]"""


def main():
    nb = json.loads(NB.read_text())
    cell = nb["cells"][162]
    src = cell["source"]
    joined = "".join(src) if isinstance(src, list) else src

    for label, old, new in (("prune->rename", OLD_PRUNE, NEW_PRUNE),
                            ("reason capture", OLD_REASON, NEW_REASON),
                            ("init", OLD_INIT, NEW_INIT),
                            ("log", OLD_LOG, NEW_LOG)):
        hits = joined.count(old)
        assert hits == 1, "%s: expected 1 anchor, found %d" % (label, hits)
        joined = joined.replace(old, new, 1)
        print("  patched %s" % label)

    cell["source"] = joined if isinstance(src, str) else [joined]

    v = next(c for c in nb["cells"]
             if '__AGENT_VERSION__ = "' in ("".join(c["source"]) if isinstance(c["source"], list)
                                            else c["source"]))
    vsrc = "".join(v["source"]) if isinstance(v["source"], list) else v["source"]
    vsrc, n = re.subn(r'__AGENT_VERSION__ = "\d\.\d\.\d"',
                      '__AGENT_VERSION__ = "4.8.6"', vsrc, count=1)
    assert n == 1, "version constant not found"
    v["source"] = vsrc if isinstance(v["source"], str) else [vsrc]
    print("  bumped __AGENT_VERSION__ -> 4.8.6")

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
