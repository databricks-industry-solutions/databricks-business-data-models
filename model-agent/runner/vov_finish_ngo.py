#!/usr/bin/env python3
"""Resubmit ONLY the ngo shrink (v2 ECM -> v2 MVM) after the VOV task wedged in teardown.

The ngo v3.5.6 VOV finished its ECM cleanly at 09:26 (✅ step_generate_next_vibes, JobTags set,
FINAL-FLUSH periodic_flushes=779) — model.json + next_vibes fully persisted in vibe_ngo_v1._metamodel.
The VOV NOTEBOOK PROCESS then wedged in GIL-bound teardown (RUNNING, no force-exit), so the in-job
shrink (run_if=ALL_DONE, depends_on=vov) stayed BLOCKED because vov never reached a terminal state.
CLI cancel-run cancels the WHOLE run (would skip the in-job shrink too), so we cancel the wedged run
and submit a dedicated shrink-only job that reads the persisted ECM and produces the MVM.

ECM validated bounded (v3.5.6 sizing-contradiction fix held): 15 domains / 322 products / 13065 attrs
/ 2127 FKs / 243 metric views -- vs the v3.5.5 explosion to 835 products. ngo is much smaller than
healthcare so a 3h cap is ample.

Reuse-first (CLAUDE.md 3d): vov_canary_finish.submit_shrink + wait_for_completion (hang-aware MVM
detection), then M.export_industry + vov_audit_extract.extract. Mirrors vov_finish_healthcare.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M
import vov_canary_finish as C
import vov_audit_extract as A

M.AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v356"
C.SHRINK_TIMEOUT_S = 10800  # 3h cap — ngo ECM (322 products) shrink on <profile>

IND = "ngo"
PROFILE = "<profile>"
WEDGED_RUN = 737771602698581


def main():
    M.pulse(f"=== FINISH_NGO start (cancel wedged vov run={WEDGED_RUN}, resubmit {IND} shrink cap={C.SHRINK_TIMEOUT_S}s) ===")
    try:
        M._run(["databricks", "jobs", "cancel-run", str(WEDGED_RUN), "--profile", PROFILE], timeout=120)
        M.pulse(f"[{IND}] cancelled wedged vov run={WEDGED_RUN}")
    except Exception as e:
        M.pulse(f"[{IND}] cancel wedged run failed (continuing): {str(e)[:160]}")
    state = M.load_state()
    if "model.json" in C.ls(PROFILE, C.vol_artifact_dir(IND, "mvm")):
        M.pulse(f"[{IND}] mvm already present — skip shrink")
    else:
        sjob, srun = C.submit_shrink(PROFILE, IND)
        M.set_ind(state, IND, status="shrink_running", shrink_job=sjob, shrink_run=srun)
        M.pulse(f"[{IND}] shrink resubmitted job={sjob} run={srun}")
        res = C.wait_for_completion(IND, PROFILE, srun, "mvm", "shrink")
        if res == "kill":
            M.pulse(f"[{IND}] KILL during shrink wait")
            return
    got = M.export_industry(PROFILE, IND)
    status = "green" if (got.get("ecm") and got.get("mvm")) else ("partial" if got.get("ecm") else "red")
    M.set_ind(state, IND, status=status, exported=got)
    M.pulse(f"[{IND}] {status.upper()} exported ecm={got.get('ecm')} mvm={got.get('mvm')}")
    if got.get("ecm"):
        try:
            audit = A.extract(IND, PROFILE)
            sb = (audit or {}).get("scoreboard", {})
            M.pulse(f"[{IND}] FINISH_NGO AUDIT precision={sb.get('precision')} recall={sb.get('recall')} "
                    f"fulfilled={sb.get('fulfilled')}/{sb.get('total_requirements')} "
                    f"partial={sb.get('partial')} failed={sb.get('failed')}")
        except Exception as e:
            M.pulse(f"[{IND}] FINISH_NGO audit failed: {str(e)[:200]}")
    M.pulse("=== FINISH_NGO DONE ===")


if __name__ == "__main__":
    main()
