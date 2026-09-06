#!/usr/bin/env python3
"""Resubmit ONLY the media_broadcasting shrink (v2 ECM -> v2 MVM) after the VOV task wedged in teardown.

Mirrors vov_finish_ngo.py. media_broadcasting is large (v3.5.6 sizing-contradiction fix held it bounded
to ~421 products vs the v3.5.5 explosion to 4469), so like ngo/healthcare its VOV NOTEBOOK PROCESS wedges
in GIL-bound teardown (RUNNING, no force-exit) after the ECM model.json is fully persisted. The in-job
shrink (run_if=ALL_DONE, depends_on=vov) then stays BLOCKED because vov never reaches terminal. CLI
cancel-run cancels the WHOLE run (skips the in-job shrink), so we cancel the wedged run and submit a
dedicated shrink-only job that reads the persisted ECM and produces the MVM.

PRECONDITION GUARD (added vs finish_ngo): we ONLY cancel the wedged vov AFTER confirming the ECM
model.json is present on the volume. If the ECM is not yet written, abort — never cancel an
actively-finalizing vov that hasn't persisted its model.

Reuse-first (CLAUDE.md 3d): vov_canary_finish.submit_shrink + wait_for_completion (hang-aware MVM
detection), then M.export_industry + vov_audit_extract.extract.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M
import vov_canary_finish as C
import vov_audit_extract as A

M.AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v356"
C.SHRINK_TIMEOUT_S = 14400  # 4h cap — mb ECM (~421 products) shrink on <profile> (larger than ngo)

IND = "media_broadcasting"
PROFILE = "<profile>"
WEDGED_RUN = 287577581035900


def main():
    M.pulse(f"=== FINISH_MB start (cancel wedged vov run={WEDGED_RUN}, resubmit {IND} shrink cap={C.SHRINK_TIMEOUT_S}s) ===")
    # PRECONDITION: ECM model.json must be persisted before we cancel the vov.
    ecm_dir = C.vol_artifact_dir(IND, "ecm")
    if "model.json" not in C.ls(PROFILE, ecm_dir):
        M.pulse(f"[{IND}] ABORT finish_mb — ECM model.json NOT present at {ecm_dir}; vov still finalizing, do not cancel")
        return
    M.pulse(f"[{IND}] ECM model.json confirmed present — safe to cancel wedged vov")
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
            M.pulse(f"[{IND}] FINISH_MB AUDIT precision={sb.get('precision')} recall={sb.get('recall')} "
                    f"fulfilled={sb.get('fulfilled')}/{sb.get('total_requirements')} "
                    f"partial={sb.get('partial')} failed={sb.get('failed')}")
        except Exception as e:
            M.pulse(f"[{IND}] FINISH_MB audit failed: {str(e)[:200]}")
    M.pulse("=== FINISH_MB DONE ===")


if __name__ == "__main__":
    main()
