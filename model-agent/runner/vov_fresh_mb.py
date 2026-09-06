#!/usr/bin/env python3
"""Fresh isolated v3.5.6 re-run of media_broadcasting after the 9h dual-write corruption.

Two mb v3.5.6 VOV runs (multi-task 287577581035900 + standalone 1014087585229676) ran ~9h
dual-writing the SAME volume (vibe_media_broadcasting_v1) -> shared log/artifact contention,
both stalled at normalization with NO ECM model.json ever persisted. Both cancelled, catalog
dropped. This re-runs mb ALONE, clean, on v3.5.6 (sizing-contradiction + parse_tags fixes),
hang-aware via canary drive() (mb is large -> vov wedges in GIL-bound teardown like ngo/
healthcare; drive() detects ECM model.json + log idle -> cancels the wedged parent run and
submits a dedicated shrink-only job, then exports).

Reuse-first (CLAUDE.md 3d): marathon prepare/stage/job/run + canary drive() + audit extract.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M
import vov_canary_finish as C
import vov_audit_extract as A

M.AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v418"
M.INSTALL_TIMEOUT_S = 2700      # 45m: bounds install teardown hang; vov is run_if=ALL_DONE
C.SHRINK_TIMEOUT_S = 14400      # 4h cap for mb (~421p) shrink on <profile>

IND = "media_broadcasting"
PROFILE = "<profile>"


def main():
    tag = f"[{IND}@{PROFILE}]"
    M.pulse("=== FRESH_MB start (clean v3.5.6 re-run, isolated, after dual-write corruption) ===")
    try:
        M.prepare_catalog(PROFILE, IND)
        M.stage_files(PROFILE, IND)
    except Exception as e:
        M.pulse(f"{tag} FRESH_MB prep failed: {str(e)[:300]}")
        return
    try:
        job_id = M.find_or_create_job(PROFILE, IND)
        run_id = M.run_now(PROFILE, job_id)
        M.pulse(f"{tag} FRESH_MB submitted job={job_id} run={run_id}")
    except Exception as e:
        M.pulse(f"{tag} FRESH_MB submit failed: {str(e)[:300]}")
        return
    state = M.load_state()
    C.drive(IND, PROFILE, run_id, state)   # hang-aware: ECM wait -> shrink -> export
    got = M.export_industry(PROFILE, IND)
    if got.get("ecm"):
        try:
            audit = A.extract(IND, PROFILE)
            sb = (audit or {}).get("scoreboard", {})
            M.pulse(f"{tag} FRESH_MB AUDIT precision={sb.get('precision')} recall={sb.get('recall')} "
                    f"fulfilled={sb.get('fulfilled')}/{sb.get('total_requirements')} "
                    f"partial={sb.get('partial')} failed={sb.get('failed')}")
        except Exception as e:
            M.pulse(f"{tag} FRESH_MB audit failed: {str(e)[:200]}")
    M.pulse(f"{tag} === FRESH_MB DONE ecm={got.get('ecm')} mvm={got.get('mvm')} ===")


if __name__ == "__main__":
    main()
