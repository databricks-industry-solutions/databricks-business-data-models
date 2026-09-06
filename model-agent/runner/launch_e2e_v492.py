#!/usr/bin/env python3
"""End-to-end gate for v4.9.2: prove the agent still builds a model with the sample
subsystem removed, so the model can then be installed, sampled and uninstalled by the
model-installer.

Deliberately small (4 user-specified domains, MVM scope) because the point is the full
agent -> install -> sample -> uninstall loop, not model size.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-uae"
AGENT_PATH = "/Users/user@example.com/dbx_vibe_modelling_agent_v492"
CATALOG = "vibe_e2e_v492"
BUSINESS = "coffee_roastery"
BUDGET_S = 10800
JOB_TIMEOUT_S = 12600
STALL_EMPTY_INFO_S = 1500

DESC = (
    "A specialty coffee roastery that buys green coffee from origin cooperatives, roasts "
    "it in batches against roast profiles, packages it, and sells it both wholesale to "
    "cafes and direct to consumers through its own retail stores and online shop."
)
VIBES = (
    "Keep this model intentionally small and production-clean: roughly five to seven "
    "tables per domain. Every table must carry a primary key. Green coffee lots must be "
    "traceable from the origin purchase through the roast batch into the finished "
    "package, so the lineage chain has to be modelled with real foreign keys."
)

M.AGENT_PATH = AGENT_PATH
M.PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/e2e492_pulses.txt")
M.STATE_FILE = os.path.expanduser("~/claude/vibe-agent/e2e492_state.json")
M.KILL_FILE = os.path.expanduser("~/claude/vibe-agent/e2e492_KILL")
M.PULSE_S = 300
M._IND_PROFILE = {BUSINESS: PROFILE}
M.cat_name = lambda ind: CATALOG  # noqa: E731


def _catalog_exists():
    cats = M.dbj(["catalogs", "list"], PROFILE)
    items = cats if isinstance(cats, list) else cats.get("catalogs", [])
    return any(c.get("name") == CATALOG for c in items)


def prepare_fresh_catalog():
    """This metastore runs on Default Storage with no storage root, so a bare
    CREATE CATALOG is rejected and the catalog needs an explicit managed location
    under an existing external location. Discovered at runtime, never hardcoded."""
    if _catalog_exists():
        M.pulse("reusing existing catalog `%s`" % CATALOG)
    else:
        locs = M.dbj(["external-locations", "list"], PROFILE)
        items = locs if isinstance(locs, list) else locs.get("external_locations", [])
        bases = [e["url"].rstrip("/") for e in items
                 if not e.get("name", "").startswith("__databricks")]
        if not bases:
            raise RuntimeError("no external location to host the catalog on %s" % PROFILE)
        M.pulse("CREATE catalog `%s` at %s" % (CATALOG, bases[0]))
        M.db(["catalogs", "create", CATALOG, "--storage-root",
              "%s/%s" % (bases[0], CATALOG)], PROFILE)
    # Through the UC API, not SQL: this workspace's SQL warehouse cold-starts for
    # minutes and a warehouse is not needed to declare a schema and a volume.
    M._try(["schemas", "create", "_metamodel", CATALOG], PROFILE, ("already exists",))
    M._try(["volumes", "create", CATALOG, "_metamodel", "vol_root", "MANAGED"],
           PROFILE, ("already exists",))
    M.pulse("catalog `%s` ready (_metamodel.vol_root)" % CATALOG)


def build_spec():
    # generate_samples is deliberately absent: v4.8.0 removed that widget, and a run that
    # succeeds without it is the proof the removal left no required parameter behind.
    params = {
        "operation": "new base model",
        "business_name": BUSINESS,
        "business_description": DESC,
        "business_domains": "sourcing, roasting, wholesale, retail",
        "model_vibes": VIBES,
        "data_model_scopes": "Minimum Viable Model - MVM",
        "deployment_catalog": CATALOG,
        "model_version": "1",
        "runtime_budget_seconds": str(BUDGET_S),
        "cataloging_style": "One Catalog",
        "vibe_session_id": "{{job.run_id}}",
        "databricks_task_run_id": "{{task.run_id}}",
    }
    return {
        "name": "dbx_vibe_e2e_v492_coffee_roastery",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "max_retries": 0,
        "tasks": [{
            "task_key": "mvm",
            "notebook_task": {"notebook_path": AGENT_PATH, "source": "WORKSPACE",
                              "base_parameters": params},
            "timeout_seconds": BUDGET_S,
            "max_retries": 0,
        }],
    }


def find_or_create_job(spec):
    jobs = M.dbj(["jobs", "list", "--limit", "100"], PROFILE)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for job in items:
        if (job.get("settings", {}) or {}).get("name") == spec["name"]:
            Path("/tmp/e2e492_jobpatch.json").write_text(
                json.dumps({"job_id": job["job_id"], "new_settings": spec}))
            M.db(["jobs", "reset", "--json", "@/tmp/e2e492_jobpatch.json"], PROFILE)
            return job["job_id"]
    Path("/tmp/e2e492_jobspec.json").write_text(json.dumps(spec))
    return M.dbj(["jobs", "create", "--json", "@/tmp/e2e492_jobspec.json"], PROFILE)["job_id"]


def info_log_bytes():
    base = "dbfs:/Volumes/%s/_metamodel/vol_root/logs/%s/v1/mvm" % (CATALOG, BUSINESS)
    try:
        out = M.dbj(["fs", "ls", base], PROFILE, timeout=90)
        files = out if isinstance(out, list) else out.get("files", []) or []
        for entry in files:
            if "info" in (entry.get("name") or ""):
                return int(entry.get("file_size") or entry.get("size") or 0)
    except Exception:
        pass
    return None


def wait_terminal(run_id):
    started, last_pulse, empty_since = time.time(), 0, None
    while True:
        if os.path.exists(M.KILL_FILE):
            M.pulse("KILL file present — leaving run %s" % run_id)
            return {"lc": "ABORTED", "result": "KILLED"}
        try:
            info = M.get_run(PROFILE, run_id)
        except Exception as exc:
            M.pulse("poll err: %s" % str(exc)[:160])
            time.sleep(M.POLL_S)
            continue
        if info["lc"] in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return info
        task = next((t for t in info.get("tasks", []) if t.get("k") == "mvm"), None)
        if task and task.get("lc") == "RUNNING":
            size = info_log_bytes()
            if not size:
                empty_since = empty_since or time.time()
                if time.time() - empty_since >= STALL_EMPTY_INFO_S:
                    M.pulse("STALL: info.log empty >%dm — canceling run %s"
                            % (STALL_EMPTY_INFO_S // 60, run_id))
                    M.db(["jobs", "cancel-run", str(run_id)], PROFILE)
                    return {"lc": "TERMINATED", "result": "CANCELED", "url": info.get("url"),
                            "tasks": info.get("tasks", [])}
            else:
                empty_since = None
        if time.time() - last_pulse >= M.PULSE_S:
            states = ", ".join("%s=%s/%s" % (t["k"], t["lc"] or "?", t["r"] or "-")
                               for t in info["tasks"])
            M.pulse("[%s] elapsed=%dm lc=%s [%s] info_bytes=%s"
                    % (BUSINESS, int((time.time() - started) / 60), info["lc"], states,
                       info_log_bytes()))
            last_pulse = time.time()
        time.sleep(M.POLL_S)


def main():
    Path(os.path.dirname(M.PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    M.pulse("=== E2E v4.9.2 START catalog=%s agent=%s ===" % (CATALOG, AGENT_PATH))
    prepare_fresh_catalog()
    job_id = find_or_create_job(build_spec())
    try:
        active = M.dbj(["jobs", "list-runs", "--job-id", str(job_id), "--active-only"], PROFILE)
        for run in (active if isinstance(active, list) else active.get("runs", [])):
            if run.get("run_id"):
                M.db(["jobs", "cancel-run", str(run["run_id"])], PROFILE)
    except Exception as exc:
        M.pulse("active-run cleanup skipped: %s" % exc)
    run_id = M.run_now(PROFILE, job_id)
    M.pulse("submitted job=%s run=%s" % (job_id, run_id))
    state = {"job_id": job_id, "run_id": run_id, "profile": PROFILE, "catalog": CATALOG}
    Path("/tmp/e2e492_run.json").write_text(json.dumps(state, indent=2))
    info = wait_terminal(run_id)
    M.pulse("TERMINAL lc=%s result=%s url=%s"
            % (info["lc"], info.get("result"), info.get("url")))
    state.update(terminal=info)
    Path("/tmp/e2e492_run.json").write_text(json.dumps(state, indent=2, default=str))


if __name__ == "__main__":
    main()
