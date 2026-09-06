#!/usr/bin/env python3
"""Clean v3.5.5 reruns of the 3 industries whose v3.5.4 VOV2 runs crashed/were cancelled.

Root cause (fixed in v3.5.5, alias=v355-enforce-string-product-fields-invariant): VOV/SelfFixer
mutations emitted product-level string fields (source_domains/subdomain/data_type/...) as
list/dict, so the physical-build table-tag emit crashed `'list' object has no attribute 'strip'`
in step_create_physical_schema_stage1. That killed healthcare + media_broadcasting at ~13h
(AFTER step 8d metric views succeeded) and automotive's residual/selffixer pass.

All three terminated CANCELED/rolled-back, so their partial ECMs are crash artifacts with
unrepresentative adherence (healthcare 80% but no MVM; media_broadcasting 30%; automotive ~40%).
The metamodel records were ROLLED BACK on failure, so a shrink-only salvage cannot rebuild
reliably. This runs the FULL install->vov->shrink pipeline on the v3.5.5 agent
(/Users/user@example.com/dbx_vibe_modelling_agent_v355), one industry per idle workspace,
in parallel. Exports overwrite /tmp/vov_out/<ind> only on success; prior <profile> automotive ECM
remains a recoverable fallback. Reuses the marathon's prepare/stage/job/wait/export/audit
functions; does NOT touch the shared marathon state file (avoids the cross-process write race).
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M
import vov_audit_extract as A

# install loads _metamodel in <15m; tight cap bounds the teardown hang and lets vov start sooner
# (run_if=ALL_DONE on vov means even an install teardown-timeout does not block vov).
M.INSTALL_TIMEOUT_S = 2700  # 45m

ASSIGN = [
    ("automotive", "<profile>"),
    ("healthcare", "<profile>"),
    ("media_broadcasting", "<profile>"),
]


def run_one(ind, profile):
    tag = f"[{ind}@{profile}]"
    try:
        M.pulse(f"{tag} RERUN355 start (full install->vov->shrink on v3.5.5)")
        M.prepare_catalog(profile, ind)
        M.stage_files(profile, ind)
    except Exception as e:
        M.pulse(f"{tag} RERUN355 prep failed: {str(e)[:300]}")
        return
    try:
        job_id = M.find_or_create_job(profile, ind)
        run_id = M.run_now(profile, job_id)
        M.pulse(f"{tag} RERUN355 submitted job={job_id} run={run_id}")
    except Exception as e:
        M.pulse(f"{tag} RERUN355 submit failed: {str(e)[:300]}")
        return
    info = M.wait_terminal(profile, ind, run_id)
    M.pulse(f"{tag} RERUN355 terminal lc={info.get('lc')} result={info.get('result')} url={info.get('url')}")
    got = M.export_industry(profile, ind)
    M.pulse(f"{tag} RERUN355 exported ecm={got.get('ecm')} mvm={got.get('mvm')}")
    if got.get("ecm"):
        try:
            audit = A.extract(ind, profile)
            sb = (audit or {}).get("scoreboard", {})
            M.pulse(f"{tag} RERUN355 AUDIT precision={sb.get('precision')} recall={sb.get('recall')} "
                    f"fulfilled={sb.get('fulfilled')}/{sb.get('total_requirements')} "
                    f"partial={sb.get('partial')} failed={sb.get('failed')}")
        except Exception as e:
            M.pulse(f"{tag} RERUN355 audit failed: {str(e)[:160]}")
    M.pulse(f"{tag} RERUN355 DONE ecm={got.get('ecm')} mvm={got.get('mvm')}")


def main():
    M.pulse(f"=== RERUN355 MARATHON start ({len(ASSIGN)} industries on v3.5.5) ===")
    threads = []
    for ind, profile in ASSIGN:
        t = threading.Thread(target=run_one, args=(ind, profile), name=ind, daemon=False)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    M.pulse("=== RERUN355 MARATHON DONE ===")


if __name__ == "__main__":
    main()
