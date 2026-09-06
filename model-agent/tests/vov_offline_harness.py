"""Offline replay harness for the v3.9.0 VOV convergence breakthroughs.

Extracts the REAL helper functions from the agent notebook (no reimplementation) and
replays them against staged v1 models + residual VReqs to measure coverage deltas
WITHOUT a Databricks run. Faithful: it execs the verbatim notebook source of the
selected function/class families, so it tests production code, not a copy.
"""
import ast
import json
import os
import re
import types

NB = os.environ.get(
    "VOV_NB",
    "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb",
)

# Function/class families the predicate transitively needs.
_KEEP_PREFIX = ("_v251_", "_v337_", "_v301_", "_vov_", "_v357_", "_v367_", "_v291_",
                "_v327_", "_v310_", "_v271_")
_KEEP_EXACT = {"sanitize_name", "RawVREQ", "VReqOutcome"}


def load_notebook_namespace(nb_path=NB):
    """Return a namespace with the real helper fns/classes exec'd from the notebook."""
    nb = json.load(open(nb_path))
    src = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    tree = ast.parse(src)
    src_lines = src.split("\n")
    keep_segments = []
    for node in tree.body:
        name = getattr(node, "name", None)
        if name is None:
            continue
        if name in _KEEP_EXACT or name.startswith(_KEEP_PREFIX):
            # Include decorator lines: ast node.lineno points at the def/class line, NOT the
            # decorator, so get_source_segment would strip @dataclass. Slice from the first
            # decorator's lineno through node.end_lineno (1-indexed inclusive).
            decos = getattr(node, "decorator_list", []) or []
            start = min([d.lineno for d in decos] + [node.lineno])
            seg = "\n".join(src_lines[start - 1:node.end_lineno])
            if seg:
                keep_segments.append(seg)
    import copy as _copy, logging as _logging
    ns = {"re": re, "json": json, "copy": _copy, "logging": _logging}
    # dataclasses / typing for RawVREQ + VReqOutcome
    exec("from dataclasses import dataclass, field\nfrom typing import Optional, Tuple, List, Dict, Any", ns)
    blob = "\n\n".join(keep_segments)
    exec(compile(blob, "<notebook-extract>", "exec"), ns)
    return ns, len(keep_segments)


def _mk_model(domains):
    return {"domains": domains}


def behavioral_test(ns):
    """§8.10 fail-pre/pass-post: the predicate must mark an already-present column+FK 'satisfied',
    an absent one 'unsatisfied', and a governance VReq 'unknown'. The pre-patch raw branch had NO
    such predicate, so EVERY one of these stayed residual (the false-negative). This proves the
    new predicate changes observable state (residual -> landed) for the satisfied case."""
    pred = ns["_vov_vreq_satisfied_in_model"]
    Raw = ns["RawVREQ"]

    def mk(intent, target):
        # RawVREQ field set varies; build defensively via kwargs that exist.
        kw = dict(vreq_id="VREQ-T", intent=intent, target=target, source_quote=intent,
                  source_chunk_id="c0", severity="high", is_user_directive=True, priority_id=None)
        import inspect
        fields = set(getattr(Raw, "__dataclass_fields__", {}).keys())
        return Raw(**{k: v for k, v in kw.items() if k in fields})

    model = _mk_model([
        {"name": "reservation", "products": [
            {"name": "booking", "primary_key": "booking_id", "attributes": [
                {"name": "booking_id", "data_type": "BIGINT"},
                {"name": "property_id", "data_type": "BIGINT", "foreign_key_to": "property.property.property_id"},
            ]},
        ]},
        {"name": "property", "products": [
            {"name": "property", "primary_key": "property_id", "attributes": [
                {"name": "property_id", "data_type": "BIGINT"},
            ]},
        ]},
    ])
    results = {}
    # 1) already-satisfied connect_table (col + FK present) -> satisfied
    v = mk("connect_table — add column property_id (BIGINT) with FK to property.property.property_id",
           "reservation.booking")
    results["satisfied_case"] = pred(v, model)[0]
    # 2) FK-target normalization tolerance: column present, FK expressed BARE (no domain prefix) and
    #    different case -> must still match the physical "property.property.property_id" (the §12 root).
    v2 = mk("connect_table — add column property_id (BIGINT) with FK to Property_Id",
            "reservation.booking")
    results["normalized_case"] = pred(v2, model)[0]
    # 3) genuinely absent column -> unsatisfied
    v3 = mk("connect_table — add column guest_id (BIGINT) with FK to guest.guest.guest_id",
            "reservation.booking")
    results["absent_case"] = pred(v3, model)[0]
    # 4) governance VReq -> unknown (conservative, never inflate)
    v4 = mk("apply glossary tag to every attribute in reservation.booking", "reservation.booking")
    results["governance_case"] = pred(v4, model)[0]
    return results


def measure_industry(ns, industry, model_path, log_path):
    """Estimate recovered residual: parse connect_table/add-column intents the loop logged, run the
    REAL predicate against the staged v1 model, count how many are already-satisfied (= recovered
    false-residual that the pre-patch raw branch would have looped forever)."""
    pred = ns["_vov_vreq_satisfied_in_model"]
    Raw = ns["RawVREQ"]
    import inspect
    fields = set(getattr(Raw, "__dataclass_fields__", {}).keys())

    def mk(intent, target):
        kw = dict(vreq_id="VREQ-X", intent=intent, target=target, source_quote=intent,
                  source_chunk_id="c", severity="high", is_user_directive=False, priority_id=None)
        return Raw(**{k: v for k, v in kw.items() if k in fields})

    m = json.load(open(model_path))
    model = m.get("model", m)
    t = open(log_path, errors="ignore").read()
    # Parse "connect_table — add column COL (TYPE) with FK to FQN on DOMAIN.PRODUCT" intents.
    intents = re.findall(
        r"(connect_table[^\n]*?on\s+([A-Za-z0-9_]+\.[A-Za-z0-9_]+))", t)
    seen = set()
    verdicts = {"satisfied": 0, "unsatisfied": 0, "unknown": 0}
    samples = []
    for full, tgt in intents:
        key = (full[:120], tgt)
        if key in seen:
            continue
        seen.add(key)
        v = mk(full, tgt)
        verdict, ev = pred(v, model)
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
        if len(samples) < 10:
            samples.append((verdict, full[:80], ev[:60]))
    return {"industry": industry, "distinct_connect_intents": len(seen),
            "verdicts": verdicts, "samples": samples}


def _parse_next_vibes_priorities(ns, vibes_path):
    """Build REAL RawVREQ objects from the FULL (untruncated) priority lines in next_vibes.txt.
    This mirrors what the raw-vibe branch feeds B3 after LLM extraction, but uses the deterministic
    source text so the offline harness can prove the B3 mechanism without an LLM."""
    RawVREQ = ns["RawVREQ"]
    t = open(vibes_path, errors="ignore").read()
    vreqs = []
    for m in re.finditer(r"- P(\d+):\s*([a-z_]+):\s*([A-Za-z0-9_]+\.[A-Za-z0-9_]+)\*{0,2}\s*"
                         r"(?:\u2014|-)\s*(.*)", t):
        pid, action, target, rest = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        intent = "%s: %s %s" % (action, target, rest)
        quote = "%s: %s** \u2014 %s" % (action, target, rest)
        vreqs.append(RawVREQ(vreq_id="VREQ-P%s" % pid, intent=intent, target=target,
                             source_quote=quote, source_chunk_id="next_vibes",
                             priority_id=int(pid)))
    return vreqs


def measure_b3_deterministic(ns, industry, model_path, vibes_path):
    """B3 proof (faithful): parse the FULL priority lines from next_vibes.txt into real RawVREQ
    objects, convert each via the REAL _vov_vreq_to_priority (B3 helper), then run the REAL
    _v251_apply_pass1_priorities against a COPY of the v1 model. Counts how many MECHANICAL VReqs
    the deterministic engine lands -- exactly the noop_failed residual the LLM sandbox left behind."""
    import copy, logging
    pass1 = ns["_v251_apply_pass1_priorities"]
    to_prio = ns["_vov_vreq_to_priority"]
    m = json.load(open(model_path))
    model = copy.deepcopy(m.get("model", m))
    vreqs = _parse_next_vibes_priorities(ns, vibes_path)
    prio, routed_to_llm = [], 0
    for v in vreqs:
        p = to_prio(v)
        if p is None:
            routed_to_llm += 1  # non-mechanical (move_product/governance) stays on LLM path
        else:
            prio.append(p)
    lg = logging.getLogger("harness")
    lg.addHandler(logging.NullHandler())
    try:
        new_model, outcomes, residual = pass1(prio, model, lg)
        applied = sum(1 for o in outcomes if getattr(o, "status", "") == "applied")
    except Exception as e:
        return {"industry": industry, "error": "%s: %s" % (type(e).__name__, str(e)[:200])}
    by_status = {}
    for o in outcomes:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    return {"industry": industry, "total_priorities": len(vreqs),
            "mechanical_to_pass1": len(prio), "routed_to_llm_path": routed_to_llm,
            "deterministically_applied": applied, "by_status": by_status,
            "residual_after": len(residual)}


if __name__ == "__main__":
    ns, n = load_notebook_namespace()
    print("extracted %d helper defs from notebook" % n)
    bt = behavioral_test(ns)
    print("\n=== BEHAVIORAL TEST (§8.10) ===")
    for k, v in bt.items():
        print("  %-18s -> %s" % (k, v))
    ok = (bt.get("satisfied_case") == "satisfied"
          and bt.get("normalized_case") == "satisfied"
          and bt.get("absent_case") == "unsatisfied"
          and bt.get("governance_case") == "unknown")
    print("  BEHAVIORAL PASS:", ok)

    print("\n=== DELTA MEASUREMENT (real v1 model + live residual intents) ===")
    stage = "/tmp/vov_stage"
    for ind in ("travel_hospitality",):
        mp = "%s/%s/model/model.json" % (stage, ind)
        lp = "/tmp/%s_vov.log" % ind
        if os.path.exists(mp) and os.path.exists(lp):
            r = measure_industry(ns, ind, mp, lp)
            print("  %s: connect_intents=%d verdicts=%s" % (r["industry"], r["distinct_connect_intents"], r["verdicts"]))
            for s in r["samples"]:
                print("     %-12s %s | %s" % s)
        else:
            print("  %s: model=%s log=%s MISSING" % (ind, os.path.exists(mp), os.path.exists(lp)))

    print("\n=== B3 DETERMINISTIC PRE-PASS PROOF (real engine on v1 model copy) ===")
    for ind in ("travel_hospitality",):
        mp = "%s/%s/model/model.json" % (stage, ind)
        vp = "%s/%s/next_vibes.txt" % (stage, ind)
        if os.path.exists(mp) and os.path.exists(vp):
            r = measure_b3_deterministic(ns, ind, mp, vp)
            print("  %s: %s" % (ind, r))
