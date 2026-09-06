#!/usr/bin/env python3
"""Driver for the v4.3.0 vov2 regen marathon.

Reuses ALL machinery in vov_v2_marathon.py (prepare_catalog, build_job_spec,
wait_terminal, export_industry, audit) per CLAUDE.md 3d; only overrides the
sanitized config globals (AGENT_VER, AGENT_PATH, ASSIGN, WAREHOUSE) with the
real 7-workspace fleet + the v4.3.0 versioned agent path. ASSIGN is read from
$DRIVER_ASSIGN (JSON) so the same driver runs the pilot and the fan-out.
"""
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M  # noqa: E402

M.AGENT_VER = "432"
M.AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v432"
M.WAREHOUSE = {
    "fe-aws": "862f1d757f0424f7",
    "fe-gcp": "d6d89fb9fd47b835",
    "fe-adp": "148ccb90800933a1",
    "my-uae": "0ece1cdc84e98661",
    "my-gcp": "2023d0a3a188bd24",
    "my-adp": "2ad1b26db73a7c6f",
    "my-aws": "7c313dcbcd3119c1",
}
M.FIXED_CATALOG = {}  # all assigned profiles are catalog-capable in this fleet

M.ASSIGN = json.loads(os.environ["DRIVER_ASSIGN"])
M._IND_PROFILE = {ind: prof for prof, inds in M.ASSIGN.items() for ind in inds}

M.STATE_FILE = os.environ.get("DRIVER_STATE", os.path.expanduser("~/claude/vibe-agent/vov2_v430_state.json"))
M.PULSE_FILE = os.environ.get("DRIVER_PULSE", os.path.expanduser("~/claude/vibe-agent/vov2_v430_pulses.txt"))
M.KILL_FILE = os.environ.get("DRIVER_KILL", os.path.expanduser("~/claude/vibe-agent/vov2_v430_KILL"))
M.DRAIN_FILE = os.environ.get("DRIVER_DRAIN", os.path.expanduser("~/claude/vibe-agent/vov2_v430_drain.flag"))
M.STAGE_DIR = "/tmp/vov_stage"
M.OUT_DIR = os.environ.get("DRIVER_OUT", "/tmp/vov_out")

if __name__ == "__main__":
    M.main()
