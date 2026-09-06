import json, collections

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))
cells = nb["cells"]

def get(i):
    s = cells[i].get("source", "")
    return "".join(s) if isinstance(s, list) else s

def put(i, txt):
    cells[i]["source"] = txt  # keep as string (HEAD format)

# ---- Edit A: cell 138 — skip ALL 4 gates on tiny + FIRED marker ----
A_OLD = '''    skipped = ("recommend_to_industry_peers", "propose_for_global_standard") if is_tiny else ()
    active = tuple(gate for gate in _GATE_ORDER if gate not in skipped)
    if skipped and logger:
        marker = globals().get('_V463_GATE_MARKERS', {}).get(alias, f"[{alias} FIRED v4.6.3]")
        logger.info(
            f"{marker} intentionally_tiny=True max_total_products={max_products} "
            f"max_domains={max_domains} evaluated={list(active)} skipped={list(skipped)} alias={alias}"
        )
    return active, skipped'''
A_NEW = '''    # v4.6.4 alias=tiny-trust-support-converge — on intentionally-tiny (test/smoke) scope, skip ALL
    # FOUR principal-engineer production-readiness gates, not just the two aspirational ones. trust/
    # support auto-"No" on "weak coverage / incomplete domain", which is BY DESIGN for a tiny model,
    # so keeping them active spun the architect review to the iteration ceiling and queued scale-
    # growth required_actions that contradict the user's explicit tiny vibe (§3c). Structural
    # correctness (broken FK / cycle / SSOT / hallucination) stays enforced by the authoritative
    # deterministic SA gates (§12) + the 23 architect structural TESTS, which still run and queue.
    skipped = tuple(_GATE_ORDER) if is_tiny else ()
    active = tuple(gate for gate in _GATE_ORDER if gate not in skipped)
    if skipped and logger:
        marker = globals().get('_V463_GATE_MARKERS', {}).get(alias, f"[{alias} FIRED v4.6.3]")
        logger.info(
            f"{marker} intentionally_tiny=True max_total_products={max_products} "
            f"max_domains={max_domains} evaluated={list(active)} skipped={list(skipped)} alias={alias}"
        )
        logger.info(
            "[tiny-trust-support-converge FIRED v4.6.4] intentionally_tiny=True — skipping ALL 4 "
            "production-readiness gates (trust/support/peers/global); structural correctness enforced "
            "by deterministic SA gates + 23 tests; alias=tiny-trust-support-converge"
        )
    return active, skipped'''
s138 = get(138)
assert s138.count(A_OLD) == 1, f"A_OLD count={s138.count(A_OLD)}"
put(138, s138.replace(A_OLD, A_NEW))

# ---- Edit B: cell 140 — domain early-exit scoped to active gates ----
B_OLD = '''    _REQUIRED_GATES_FOR_EARLY_EXIT = ("trust_in_production", "support_in_production")
    _all_pass = all(
        str(_gate_answers_snapshot.get(_gn, "")).strip().lower() == "yes"
        for _gn in _REQUIRED_GATES_FOR_EARLY_EXIT
    )'''
B_NEW = '''    # v4.6.4 alias=tiny-trust-support-converge — scope the early-exit requirement to the ACTIVE
    # (tier-aware) gates. On intentionally-tiny scope _gate_names excludes trust/support, so
    # requiring them 'Yes' would spin the domain review to the iteration ceiling and queue
    # scale-growth actions that violate the user's tiny vibe (§3c). all([]) == True => converge;
    # structural correctness stays enforced by the deterministic SA gates.
    _REQUIRED_GATES_FOR_EARLY_EXIT = tuple(
        _gn for _gn in ("trust_in_production", "support_in_production") if _gn in _gate_names
    )
    _all_pass = all(
        str(_gate_answers_snapshot.get(_gn, "")).strip().lower() == "yes"
        for _gn in _REQUIRED_GATES_FOR_EARLY_EXIT
    )'''
s140 = get(140)
assert s140.count(B_OLD) == 1, f"B_OLD count={s140.count(B_OLD)}"
put(140, s140.replace(B_OLD, B_NEW))

# ---- Edit C: cell 142 — global early-exit scoped to active gates (recompute, _gate_keys OOS) ----
C_OLD = '''        _REQUIRED_GATES_FOR_EARLY_EXIT = ("trust_in_production", "support_in_production")
        if all(str(_global_gate_snapshot.get(_gk, "")).strip().lower() == "yes" for _gk in _REQUIRED_GATES_FOR_EARLY_EXIT):
            logger.info(f"  ✅ Production-worthy global architect gates (trust+support) passed in iteration {_iter} — early exit")
            break'''
C_NEW = '''        # v4.6.4 alias=tiny-trust-support-converge — scope the early-exit to the ACTIVE tier-aware
        # gates (recomputed here from sizing_directives since _gate_keys is defined in the gate-report
        # helper, out of this driver scope). On intentionally-tiny scope trust/support are skipped
        # (production-readiness gates inappropriate for smoke scope; structural correctness enforced
        # by the deterministic SA gates), so the review converges instead of spinning to the ceiling
        # and queuing scale-growth actions that violate the user's tiny vibe (§3c). all([]) == True.
        _ee_active, _ee_skipped = _tier_aware_architect_gate_keys(
            (widgets_values.get("sizing_directives") or {}) if widgets_values else {}
        )
        _REQUIRED_GATES_FOR_EARLY_EXIT = tuple(
            _gk for _gk in ("trust_in_production", "support_in_production") if _gk in _ee_active
        )
        if all(str(_global_gate_snapshot.get(_gk, "")).strip().lower() == "yes" for _gk in _REQUIRED_GATES_FOR_EARLY_EXIT):
            if _REQUIRED_GATES_FOR_EARLY_EXIT:
                logger.info(f"  ✅ Production-worthy global architect gates (trust+support) passed in iteration {_iter} — early exit")
            else:
                logger.info(f"  ✅ [tiny-trust-support-converge FIRED v4.6.4] intentionally-tiny scope — production-readiness gates skipped (structural correctness enforced deterministically); converged iteration {_iter} — early exit")
            break'''
s142 = get(142)
assert s142.count(C_OLD) == 1, f"C_OLD count={s142.count(C_OLD)}"
put(142, s142.replace(C_OLD, C_NEW))

# reserialize in HEAD format (source as string, indent=1, ascii)
out = collections.OrderedDict()
out["nbformat"] = nb.get("nbformat", 4)
out["nbformat_minor"] = nb.get("nbformat_minor", 0)
out["metadata"] = nb.get("metadata", {})
new_cells = []
for cell in cells:
    ct = cell.get("cell_type", "code")
    nc = collections.OrderedDict()
    nc["cell_type"] = ct
    nc["metadata"] = cell.get("metadata", {})
    if ct == "code":
        nc["outputs"] = cell.get("outputs", [])
        nc["execution_count"] = cell.get("execution_count", None)
    s = cell.get("source", "")
    nc["source"] = "".join(s) if isinstance(s, list) else s
    for k, v in cell.items():
        if k not in nc:
            nc[k] = v
    new_cells.append(nc)
out["cells"] = new_cells
json.dump(out, open(NB, "w"), indent=1, ensure_ascii=True)
print("PATCHED OK: tiny-gate-converge 3 edits applied")
