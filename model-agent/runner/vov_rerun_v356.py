#!/usr/bin/env python3
"""Clean v3.5.6 reruns of the 2 industries whose v3.5.5 VOV2 ECMs EXPLODED.

Root cause (fixed in v3.5.6):
  - alias=v356-sizing-contradiction-sanitizer: the LLM VIBE_PARSE hallucinated tiny max_* sizing
    values (max_domains=3 / max_total_products=18 / max_products_per_domain=6 -- the
    qualitative-smallness constants) from the next_vibes TEMPLATE PROSE ("It has THREE sections",
    "Section 3"), and the LLM+regex merge combined them with the regex-extracted EXPLICIT floor
    (min_domains=17 / min_total_products=421). The resulting CONTRADICTION (max_total_products=18 <
    min_total_products=421) made the downstream ceiling logic discard the product ceiling entirely
    -> unbounded VOV expansion. Live v3.5.5 result:
        media_broadcasting  421 -> 4465 products (10.6x, quality 50/100)
        ngo                 302 ->  835 products (2.76x)
    while the other 11 industries (clean max==min sizing) stayed at ratio <= 1.05.
  - alias=v356-source-trace-parse-tags-coerce: _parse_tags crashed `'list' object has no attribute
    'split'` on list/dict tags (media_broadcasting [source-trace-enforce ERROR] + B0040 mutator).

Both deployed + alias-verified on /Users/user@example.com/dbx_vibe_modelling_agent_v356
(<profile> + <profile>). This runs the FULL install->vov->shrink pipeline on v3.5.6, one industry per
idle workspace, in parallel, on CLEAN catalogs. Exports overwrite /tmp/vov_out/<ind> only on
success (the exploded v3.5.5 ECMs remain until then). Reuses the marathon prepare/stage/job/wait/
export/audit; does NOT touch the shared marathon state file (avoids cross-process write race).

healthcare is finishing its shrink on <profile> under vov_finish_healthcare.py; keep <profile> free here.
"""
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M
import vov_audit_extract as A

# Point every job built by the marathon at the v3.5.6 archive (find_or_create_job resets the
# existing _v355 job's notebook_task.notebook_path to this via build_job_spec).
M.AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v356"
M.INSTALL_TIMEOUT_S = 2700   # 45m: bounds the install teardown hang; vov is run_if=ALL_DONE anyway

ASSIGN = [
    ("media_broadcasting", "<profile>"),
    ("ngo", "<profile>"),
]


def run_one(ind, profile):
    tag = f"[{ind}@{profile}]"
    try:
        M.pulse(f"{tag} RERUN356 start (full install->vov->shrink on v3.5.6, clean catalog)")
        M.prepare_catalog(profile, ind)
        M.stage_files(profile, ind)
    except Exception as e:
        M.pulse(f"{tag} RERUN356 prep failed: {str(e)[:300]}")
        return
    try:
        job_id = M.find_or_create_job(profile, ind)
        run_id = M.run_now(profile, job_id)
        M.pulse(f"{tag} RERUN356 submitted job={job_id} run={run_id}")
    except Exception as e:
        M.pulse(f"{tag} RERUN356 submit failed: {str(e)[:300]}")
        return
    info = M.wait_terminal(profile, ind, run_id)
    M.pulse(f"{tag} RERUN356 terminal lc={info.get('lc')} result={info.get('result')} url={info.get('url')}")
    got = M.export_industry(profile, ind)
    M.pulse(f"{tag} RERUN356 exported ecm={got.get('ecm')} mvm={got.get('mvm')}")
    if got.get("ecm"):
        try:
            audit = A.extract(ind, profile)
            sb = (audit or {}).get("scoreboard", {})
            M.pulse(f"{tag} RERUN356 AUDIT precision={sb.get('precision')} recall={sb.get('recall')} "
                    f"fulfilled={sb.get('fulfilled')}/{sb.get('total_requirements')} "
                    f"partial={sb.get('partial')} failed={sb.get('failed')}")
        except Exception as e:
            M.pulse(f"{tag} RERUN356 audit failed: {str(e)[:160]}")
    M.pulse(f"{tag} RERUN356 DONE ecm={got.get('ecm')} mvm={got.get('mvm')}")


def main():
    M.pulse(f"=== RERUN356 start ({len(ASSIGN)} exploded industries on v3.5.6, sizing-contradiction fix) ===")
    threads = []
    for ind, profile in ASSIGN:
        t = threading.Thread(target=run_one, args=(ind, profile), name=ind, daemon=False)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    M.pulse("=== RERUN356 DONE ===")


if __name__ == "__main__":
    main()
