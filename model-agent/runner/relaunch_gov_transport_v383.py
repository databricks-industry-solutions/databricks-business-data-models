#!/usr/bin/env python3
"""v3.8.3 gov_transport base-MVM live-prove (reuse base_mvm_proof helpers, non-blocking).

Proves the SIX generic VREQ-lifecycle root-cause fixes live on <profile> (the workspace that
produced the semantic misses found in the microscopic vibe-VREQ audit, 2026-06-18):
  A v383-metric-view-not-product : KPIs emitted as domain products/tables are removed (they belong
    in metric_views); FK-safe; mandated-but-unbuilt MV names re-queued.
  B v383-per-attr-value-tag      : `gov_transport_source_attribute=<original_column>` resolves a PER-attribute
    provenance value (not the literal placeholder) on source-derived HR tables.
  C v383-lookup-match-only       : `gov_transport_business_glossary_term` attaches ONLY when the value traces
    to the 72-row CDE lexicon; zero-overlap fabrications are purged.
  D v383-closed-roster-enforce   : every HR product's subdomain is forced onto the vibe's 9-member
    closed subdomain roster; invented labels relabelled to the nearest member.
  E v383-merge-first-flag        : PSE source tables overlapping existing project products are flagged
    + re-queued for the FK-safe merge-into-existing mutation (vibe merge-first directive).
  F v383-tag-name-precedence     : the vibe-literal `original_table_name` (unprefixed) outranks the
    general `gov_transport_` prefix rule for PSE project tables.

Per the user directive (2026-06-18): samples are NOT generated (generate_samples stays "0"); catalog
name left as base_mvm_proof default. Non-blocking: agent self-launches a child; poll from the shell.
Drops vibe_gov_transport_basemvm first via prepare_catalog for a clean run.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base_mvm_proof as B  # noqa: E402

M = B.M
NEW = "/Users/user@example.com/dbx_vibe_modelling_agent_v383"
B.AGENT_PATH = NEW
M.AGENT_PATH = NEW

IND, PROF, DOMAINS = "gov_transport", "<profile>", "hr, project"


def main():
    M.prepare_catalog(PROF, IND)               # drop + recreate vibe_gov_transport_basemvm
    vibe_path = B.stage_vibe(PROF, IND)
    desc = B.read_desc(IND)
    spec = B.build_spec(IND, PROF, vibe_path, desc, DOMAINS)
    spec["name"] = f"dbx_vibe_basemvm_{IND}_v383"
    spec["tasks"][0]["notebook_task"]["notebook_path"] = NEW
    job_id = B.find_or_create_job(PROF, IND, spec)
    run_id = M.run_now(PROF, job_id)
    print(f"JOBID {job_id} RUNID {run_id} VIBE {vibe_path} AGENT {NEW}")


if __name__ == "__main__":
    main()
