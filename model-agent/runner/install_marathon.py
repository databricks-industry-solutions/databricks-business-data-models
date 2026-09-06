#!/usr/bin/env python3
"""Install marathon v2/v3: parallel installs across catalog-capable workspaces.

- Preflights CREATE CATALOG (bare + managed-location fallback, like the installer).
- Excludes profiles that cannot create catalogs (e.g. my-aws).
- Default wave mode: ECM wave then MVM wave (per-profile multi-task jobs).
- Pool mode (--max-parallel N): global scheduler, ECM+MVM together, N concurrent max.
- Warning installs: fetch failures manifest, prune failed metric SQL, retry.
- Cleanup: DROP marathon_* catalogs before and after the run.

State: ~/claude/vibe-agent/install_marathon_v2_state.json
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

_STATE_LOCK = threading.Lock()
_SETUP_LOCK = threading.Lock()
_setup_active = 0
MAX_SETUP_PARALLEL = 10

INDUSTRIES = [
    "advertising", "agriculture", "airlines", "apparel_fashion", "automotive",
    "banking", "chemical_mfg", "clinical_trials", "construction", "consumer_goods",
    "ecommerce", "education", "energy_utilities", "food_beverage", "gaming",
    "genomics_biotech", "grocery", "health_insurance", "healthcare", "legal",
    "life_insurance", "manufacturing", "media_broadcasting", "mining", "ngo",
    "oil_gas", "payments_fintech", "pharmaceuticals", "real_estate", "restaurants",
    "retail", "semiconductors", "shipping_ports", "sports_entertainment",
    "staffing_hr", "telecommunication", "transport_shipping", "travel_hospitality",
    "waste_management", "water_utilities",
]

CANDIDATE_PROFILES = [
    "my-uae", "my-gcp", "my-adp", "my-aws",
    "fe-aws", "fe-gcp", "fe-adp",
]

WAREHOUSE = {
    "my-uae": "0ece1cdc84e98661",
    "my-gcp": "2023d0a3a188bd24",
    "my-adp": "2ad1b26db73a7c6f",
    "my-aws": "7c313dcbcd3119c1",
    "fe-aws": "862f1d757f0424f7",
    "fe-gcp": "d6d89fb9fd47b835",
    "fe-adp": "148ccb90800933a1",
}

INSTALLER_PATH = "/Users/user@example.com/data-model-installer"
MARATHON_TAG = "install_marathon_v2"
SOURCE_REPO = "databricks-industry-solutions/lakehouse-industry-data-models"
SOURCE_REF = "main"

ECM_TIMEOUT_S = 14400   # 4h
MVM_TIMEOUT_S = 10800   # 3h
JOB_TIMEOUT_S = 16200   # 4.5h
DEFAULT_MAX_PARALLEL = 40

STATE_FILE = os.path.expanduser(
    os.environ.get("MARATHON_STATE_FILE", "~/claude/vibe-agent/install_marathon_v2_state.json")
)
PULSE_FILE = os.path.expanduser(
    os.environ.get("MARATHON_PULSE_FILE", "~/claude/vibe-agent/install_marathon_v2_pulses.txt")
)
HEARTBEAT_FILE = os.path.expanduser(
    os.environ.get("MARATHON_HEARTBEAT_FILE", "~/claude/vibe-agent/install_marathon_heartbeat.log")
)
HEARTBEAT_STATE_FILE = os.path.expanduser(
    os.environ.get("MARATHON_HEARTBEAT_STATE_FILE", "~/claude/vibe-agent/install_marathon_heartbeat_state.json")
)
AUDIT_FILE = os.path.expanduser(
    os.environ.get("MARATHON_AUDIT_FILE", "~/claude/vibe-agent/install_marathon_verify_audit.log")
)
HEARTBEAT_INTERVAL_S = 900  # 15 minutes
MODEL_CACHE = Path("/tmp/install_marathon_models")

_AUTH_HINTS = (
    "oauth", "token has expired", "refresh token expired", "401",
    "unauthorized", "invalid_grant", "could not refresh",
)
_TRANSIENT_HINTS = (
    "no such host", "connection reset", "connection refused", "i/o timeout",
    "tls handshake timeout", "temporary failure", "network is unreachable",
    "eof", "broken pipe", "dial tcp",
)

_TERMINAL_LC = frozenset({"TERMINATED", "INTERNAL_ERROR", "SKIPPED", "CANCELED"})


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pulse(msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    Path(os.path.dirname(PULSE_FILE)).mkdir(parents=True, exist_ok=True)
    with open(PULSE_FILE, "a") as f:
        f.write(line + "\n")


def _run(cmd: list[str], timeout: int) -> tuple[int, str, str]:
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, stdin=subprocess.DEVNULL, start_new_session=True,
    )
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), 9)
        except OSError:
            p.kill()
        return 124, "", f"timeout after {timeout}s"


def _refresh(profile: str) -> None:
    _run(["databricks", "auth", "token", "--profile", profile], 60)


def db(args: list[str], profile: str, timeout: int = 300, retries: int = 5) -> str:
    cmd = ["databricks"] + args + ["--profile", profile]
    last_err = ""
    for attempt in range(retries):
        rc, out, err = _run(cmd, timeout)
        if rc == 0:
            return out
        last_err = (err or "")[:800]
        el = last_err.lower()
        if any(h in el for h in _AUTH_HINTS):
            _refresh(profile)
            rc, out, err = _run(cmd, timeout)
            if rc == 0:
                return out
            last_err = (err or "")[:800]
            el = last_err.lower()
        if attempt + 1 < retries and any(h in el for h in _TRANSIENT_HINTS):
            wait = min(30, 2 ** attempt * 2)
            pulse(f"[transient] databricks {' '.join(args[:3])} ... retry {attempt + 2}/{retries} in {wait}s")
            time.sleep(wait)
            continue
        break
    raise RuntimeError(f"databricks {' '.join(args)} -> {rc}: {last_err}")


def dbj(args: list[str], profile: str, timeout: int = 300) -> dict | list:
    out = db(args + ["-o", "json"], profile, timeout=timeout)
    return json.loads(out) if out.strip() else {}


def sql_exec(profile: str, stmt: str, timeout: int = 120) -> tuple[str, dict, list]:
    wh = WAREHOUSE[profile]
    payload = {"warehouse_id": wh, "statement": stmt, "wait_timeout": "50s"}
    pf = f"/tmp/sql_{profile}_{abs(hash(stmt)) % 100000}.json"
    Path(pf).write_text(json.dumps(payload))
    res = dbj(["api", "post", "/api/2.0/sql/statements", "--json", f"@{pf}"], profile, timeout=120)
    sid = res.get("statement_id")
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = (res.get("status", {}) or {}).get("state")
        if st not in ("PENDING", "RUNNING"):
            break
        time.sleep(3)
        res = dbj(["api", "get", f"/api/2.0/sql/statements/{sid}"], profile, timeout=120)
    st = (res.get("status", {}) or {}).get("state", "UNKNOWN")
    err = (res.get("status", {}) or {}).get("error") or {}
    rows = (res.get("result", {}) or {}).get("data_array") or []
    return st, err, rows


def preflight_profile(profile: str) -> tuple[bool, str]:
    """Return (capable, detail) using installer-equivalent catalog creation."""
    cat = f"__install_probe_{uuid.uuid4().hex[:8]}"
    sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=60)
    st, err, _ = sql_exec(profile, f"CREATE CATALOG `{cat}`", timeout=90)
    if st == "SUCCEEDED":
        sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=60)
        return True, "bare_create"
    msg = (err.get("message") if isinstance(err, dict) else str(err)).lower()
    if "permission_denied" in msg and "create catalog" in msg:
        return False, (err.get("message") if isinstance(err, dict) else str(err))[:300]
    if any(x in msg for x in ("storage root", "default storage", "managed location")):
        st2, err2, rows = sql_exec(profile, "SHOW EXTERNAL LOCATIONS", timeout=90)
        if st2 != "SUCCEEDED" or not rows:
            return False, f"no external locations ({msg[:120]})"
        last_err = msg
        for row in rows:
            name = row[0]
            url = (row[1] if len(row) > 1 else "").rstrip("/")
            if not url:
                continue
            loc = f"{url}/{cat}"
            st3, err3, _ = sql_exec(
                profile, f"CREATE CATALOG `{cat}` MANAGED LOCATION '{loc}'", timeout=90)
            if st3 == "SUCCEEDED":
                sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=60)
                return True, f"managed_location:{name}"
            last_err = (err3.get("message") if isinstance(err3, dict) else str(err3))[:200]
        return False, f"external_location_failed:{last_err}"
    return False, (err.get("message") if isinstance(err, dict) else str(err))[:300]


def discover_capable_profiles() -> dict[str, str]:
    capable: dict[str, str] = {}
    blocked: dict[str, str] = {}
    for p in CANDIDATE_PROFILES:
        if p not in WAREHOUSE:
            blocked[p] = "no warehouse mapped"
            continue
        ok, detail = preflight_profile(p)
        if ok:
            capable[p] = detail
            pulse(f"[preflight] {p} OK ({detail})")
        else:
            blocked[p] = detail
            pulse(f"[preflight] {p} BLOCKED — {detail[:120]}")
    return capable, blocked


def assign_industries(profiles: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {p: [] for p in profiles}
    for i, ind in enumerate(INDUSTRIES):
        out[profiles[i % len(profiles)]].append(ind)
    return out


def assign_split(ecm_profile: str, mvm_profile: str) -> dict[str, list[str]]:
    """All ECM on one profile, all MVM on another (verification layout)."""
    return {ecm_profile: list(INDUSTRIES), mvm_profile: list(INDUSTRIES)}


def build_work_items(assign: dict[str, list[str]], split: dict | None = None) -> list[tuple[str, str, str]]:
    if split:
        ecm_p, mvm_p = split["ecm"], split["mvm"]
        return (
            [(ecm_p, ind, "ecm") for ind in INDUSTRIES]
            + [(mvm_p, ind, "mvm") for ind in INDUSTRIES]
        )
    return work_items_from_assign(assign)


def drop_owned_catalogs(profile: str, owner: str = "user@example.com") -> int:
    """DROP every non-system catalog owned by `owner` on `profile`."""
    dropped = 0
    try:
        raw = dbj(["api", "get", "/api/2.1/unity-catalog/catalogs"], profile, timeout=120)
        cats = raw if isinstance(raw, list) else raw.get("catalogs", [])
    except Exception as e:
        pulse(f"[drop-owned] {profile} list failed: {str(e)[:120]}")
        return 0
    skip = frozenset({"hive_metastore", "samples", "system", "__databricks_internal"})
    targets = [
        c["name"] for c in cats
        if c.get("name") not in skip
        and c.get("catalog_type") not in ("SYSTEM_CATALOG",)
        and str(c.get("owner", "")).lower() == owner.lower()
    ]
    pulse(f"[drop-owned] {profile} dropping {len(targets)} catalog(s) owned by {owner}")
    for cat in sorted(targets):
        try:
            st, _, _ = sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=180)
            if st == "SUCCEEDED":
                dropped += 1
                pulse(f"[drop-owned] {profile} dropped `{cat}`")
        except Exception as e:
            pulse(f"[drop-owned] {profile} skip `{cat}`: {str(e)[:100]}")
    return dropped


def catalog_name(ind: str, size: str) -> str:
    return f"idx_{ind}_{size}"


def staging_catalog(profile: str, ind: str, size: str) -> str:
    """Parent catalog for pruned-model volume staging (fe-adp slot cap: reuse ECM)."""
    if profile == "fe-adp" and ind == "health_insurance" and size == "mvm":
        return "idx_health_insurance_ecm"
    target = catalog_name(ind, size)
    st, _, _ = sql_exec(profile, f"DESCRIBE CATALOG EXTENDED `{target}`", timeout=30)
    if st == "SUCCEEDED":
        return target
    return f"idx_staging_{profile.replace('-', '_')}"


def resolve_install_catalog(profile: str, ind: str, size: str) -> str:
    """Pick install catalog; use _b suffix when ghost/inaccessible name blocks CREATE."""
    cat = catalog_name(ind, size)
    st, err, _ = sql_exec(profile, f"DESCRIBE CATALOG EXTENDED `{cat}`", timeout=60)
    if st == "SUCCEEDED":
        return cat
    st2, err2, _ = sql_exec(profile, f"CREATE CATALOG IF NOT EXISTS `{cat}`", timeout=90)
    if st2 == "SUCCEEDED":
        st3, _, _ = sql_exec(profile, f"DESCRIBE CATALOG EXTENDED `{cat}`", timeout=60)
        if st3 == "SUCCEEDED":
            return cat
    def _msg(e) -> str:
        if isinstance(e, dict):
            return str(e.get("message") or "")
        return str(e or "")

    msg = f"{_msg(err)} {_msg(err2)}".lower()
    if "already exists" in msg or "not accessible" in msg:
        alt = f"{cat}_b"
        pulse(f"[catalog-ghost FIRED] {profile}:{ind}/{size} `{cat}` blocked — using `{alt}`")
        sql_exec(profile, f"DROP CATALOG IF EXISTS `{alt}` CASCADE", timeout=120)
        st4, err4, _ = sql_exec(profile, f"CREATE CATALOG `{alt}`", timeout=90)
        if st4 != "SUCCEEDED":
            st5, _, rows = sql_exec(profile, "SHOW EXTERNAL LOCATIONS", timeout=90)
            if st5 == "SUCCEEDED" and rows:
                for row in rows:
                    url = (row[1] if len(row) > 1 else "").rstrip("/")
                    if url:
                        loc = f"{url}/{alt}"
                        st6, _, _ = sql_exec(
                            profile, f"CREATE CATALOG `{alt}` MANAGED LOCATION '{loc}'", timeout=90)
                        if st6 == "SUCCEEDED":
                            return alt
            raise RuntimeError(f"CREATE `{alt}` failed: {(err4.get('message') if isinstance(err4,dict) else err4)}")
        return alt
    return cat


def task_key(ind: str, size: str, phase: str = "") -> str:
    base = f"{size}_{ind}"
    if phase:
        base = f"{phase}_{base}"
    return base[:100]


def installer_params(ind: str, size: str, local_install: str = "", catalog: str | None = None) -> dict[str, str]:
    return {
        "model": ind,
        "model_size": size,
        "catalog_name": catalog or catalog_name(ind, size),
        "cataloging_style": "One Catalog",
        "catalog_prefix": "",
        "catalog_suffix": "",
        "local_install": local_install,
        "session_id": "{{task.run_id}}",
        "threads": "32",
        "batch_size": "20",
        "include_metrics": "true",
        "source_repo": SOURCE_REPO,
        "source_ref": SOURCE_REF,
        "github_token": "",
    }


def build_wave_job_spec(profile: str, industries: list[str], size: str, phase: str) -> dict:
    tmo = ECM_TIMEOUT_S if size == "ecm" else MVM_TIMEOUT_S
    tasks = []
    for ind in industries:
        tasks.append({
            "task_key": task_key(ind, size, phase),
            "notebook_task": {
                "notebook_path": INSTALLER_PATH,
                "source": "WORKSPACE",
                "base_parameters": installer_params(ind, size),
            },
            "timeout_seconds": tmo,
        })
    return {
        "name": f"dbx_{MARATHON_TAG}_{profile.replace('-', '_')}_{size}_{phase}",
        "tags": {"marathon": MARATHON_TAG, "profile": profile, "wave": f"{size}_{phase}"},
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": tasks,
    }


def build_retry_job_spec(profile: str, ind: str, size: str, local_install: str, catalog: str | None = None) -> dict:
    tmo = ECM_TIMEOUT_S if size == "ecm" else MVM_TIMEOUT_S
    return {
        "name": f"dbx_{MARATHON_TAG}_retry_{profile.replace('-', '_')}_{size}_{ind}",
        "timeout_seconds": tmo + 600,
        "max_concurrent_runs": 4,
        "tasks": [{
            "task_key": f"retry_{size}_{ind}",
            "notebook_task": {
                "notebook_path": INSTALLER_PATH,
                "source": "WORKSPACE",
                "base_parameters": installer_params(ind, size, local_install=local_install, catalog=catalog),
            },
            "timeout_seconds": tmo,
        }],
    }


def find_or_reset_job(profile: str, spec: dict) -> int:
    name = spec["name"]
    jobs = dbj(["jobs", "list", "--limit", "100"], profile)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for j in items:
        if (j.get("settings", {}) or {}).get("name") == name:
            jid = j["job_id"]
            patch = {"job_id": jid, "new_settings": spec}
            pp = f"/tmp/install_marathon_patch_{hash(name) % 100000}.json"
            Path(pp).write_text(json.dumps(patch))
            db(["jobs", "reset", "--json", f"@{pp}"], profile, timeout=120)
            return jid
    sp = f"/tmp/install_marathon_spec_{hash(name) % 100000}.json"
    Path(sp).write_text(json.dumps(spec))
    res = dbj(["jobs", "create", "--json", f"@{sp}"], profile, timeout=120)
    return res["job_id"]


def run_now(profile: str, job_id: int) -> int:
    res = dbj(["jobs", "run-now", str(job_id), "--no-wait"], profile)
    return res["run_id"]


def get_run(profile: str, run_id: int) -> dict:
    info = dbj(["jobs", "get-run", str(run_id)], profile)
    st = info.get("state", {})
    tasks = []
    for t in info.get("tasks", []) or []:
        ts = t.get("state", {}) or {}
        tasks.append({
            "task_key": t.get("task_key"),
            "run_id": t.get("run_id"),
            "life_cycle": ts.get("life_cycle_state"),
            "result": ts.get("result_state"),
            "message": (ts.get("state_message") or "")[:500],
        })
    return {
        "life_cycle": st.get("life_cycle_state"),
        "result": st.get("result_state"),
        "url": info.get("run_page_url"),
        "tasks": tasks,
    }


def parse_task_meta(task_key_str: str) -> tuple[str, str]:
    m = re.match(r"^(?:retry_)?(?:wave\d+_)?(ecm|mvm)_(.+)$", task_key_str)
    if m:
        return m.group(2), m.group(1)
    return task_key_str, "unknown"


def parse_industry_from_output(output: dict) -> tuple[str, str] | None:
    nb = output.get("notebook_output") or ""
    m = re.search(r"INSTALLED[^:]*:\s*([^/]+)/(ecm|mvm)\s*->", nb, re.I)
    if m:
        return m.group(1).strip(), m.group(2).lower()
    m = re.search(r"`idx_([a-z0-9_]+)_(ecm|mvm)`", nb)
    if m:
        return m.group(1), m.group(2)
    return None


def fetch_task_output(profile: str, task_run_id: int) -> dict:
    try:
        ro = dbj(["jobs", "get-run-output", str(task_run_id)], profile, timeout=180)
    except Exception as e:
        return {"error": str(e)[:600], "notebook_output": ""}
    nb = ""
    if isinstance(ro, dict):
        nbo = ro.get("notebook_output") or {}
        if isinstance(nbo, dict):
            nb = (nbo.get("result") or "")[:12000]
        err = ro.get("error")
        if err:
            if isinstance(err, str):
                return {"error": err[:2000], "notebook_output": nb}
            return {
                "error": (err.get("message") or str(err))[:2000],
                "notebook_output": nb,
            }
    return {"notebook_output": nb, "error": None}


def classify_bucket(result: str | None, output: dict) -> str:
    nb = (output.get("notebook_output") or "")
    nbl = nb.lower()
    err = (output.get("error") or "").lower()
    text = nbl + " " + err
    if result == "SUCCESS":
        if "installed_with_warnings" in nbl or "metric-view source defects" in nbl:
            return "warning"
        if "success:" in nbl:
            return "clean"
        return "clean"
    if result == "TIMEDOUT":
        return "failed"
    if result in ("FAILED", "CANCELED"):
        if "unrecoverable" in text and "metric" in text:
            return "warning"
        if "structural" in text:
            return "failed"
        if "catalog" in text and ("could not be created" in text or "permission_denied" in text):
            return "failed"
        return "failed"
    return "failed" if result else "running"


def parse_metric_failures_from_output(output: dict) -> list[dict]:
    """Extract metric-phase failures from notebook output text."""
    nb = output.get("notebook_output") or ""
    failures = []
    phase = None
    for line in nb.splitlines():
        if "UNRECOVERABLE STATEMENTS" in line:
            phase = "header"
            continue
        m = re.match(r"\s*\[(metric)\]\s+(.+)", line)
        if m:
            failures.append({"phase": "metric", "sql_preview": m.group(2)[:200], "error": ""})
            continue
        m2 = re.match(r"\s*->\s+(.+)", line)
        if m2 and failures and not failures[-1].get("error"):
            failures[-1]["error"] = m2.group(1)[:400]
    return [f for f in failures if f.get("phase") == "metric"]


def _urlopen_with_retry(url: str, timeout: int = 60, retries: int = 6) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "install-marathon-v2"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429) and attempt + 1 < retries:
                time.sleep(min(60, 2 ** attempt * 5))
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt + 1 < retries:
                time.sleep(min(30, 2 ** attempt * 2))
                continue
            raise
    raise RuntimeError(f"urlopen failed for {url}: {last_err}")


def _gh_json(url: str) -> dict | list:
    return json.loads(_urlopen_with_retry(url).decode())


def latest_version_path(industry: str) -> str:
    items = _gh_json(f"https://api.github.com/repos/{SOURCE_REPO}/contents/data-models/{industry}?ref={SOURCE_REF}")
    versions = sorted(
        (it["name"] for it in items if it.get("type") == "dir" and re.match(r"^v\d+$", it["name"])),
        key=lambda v: int(v[1:]))
    if not versions:
        raise RuntimeError(f"No versions for {industry}")
    return f"data-models/{industry}/{versions[-1]}"


_CONSTRUCTION_SITE_STUB_RE = re.compile(
    r"\nCREATE OR REPLACE TABLE `[^`]+`\.`project`\.`site` \(\s*"
    r"`site_id` BIGINT COMMENT '',\s*"
    r"CONSTRAINT pk_site PRIMARY KEY\(`site_id`\)\s*"
    r"\) COMMENT '';\s*\n",
    re.IGNORECASE,
)


def _fix_schema_ddl_issues(base: Path, industry: str, size: str) -> None:
    """Patch known-bad schema DDL before install (alias=marathon-schema-ddl-fix)."""
    if industry != "construction" or size != "ecm":
        return
    schema_dir = base / "schemas"
    if not schema_dir.is_dir():
        return
    for sf in schema_dir.glob("*project*.sql"):
        text = sf.read_text(errors="ignore")
        new_text, n = _CONSTRUCTION_SITE_STUB_RE.subn("\n", text, count=1)
        if n:
            sf.write_text(new_text)
            pulse(
                f"[marathon-schema-ddl-fix FIRED] removed duplicate project.site stub "
                f"in {sf.name}"
            )


def _apply_metric_fixes(base: Path, industry: str, size: str) -> Path:
    _fix_schema_ddl_issues(base, industry, size)
    try:
        from fix_all_metrics import parse_schema_columns, fix_metric_file
        schema_cols = parse_schema_columns(base / "schemas")
        for mf in (base / "metrics").glob("*.sql"):
            fixed, _ = fix_metric_file(mf, schema_cols)
            mf.write_text(fixed)
    except Exception as e:
        pulse(f"[fix-metrics] {industry}/{size} local patch skipped: {e}")
    return base


def download_model_tree(industry: str, size: str) -> Path:
    base = MODEL_CACHE / industry / size
    base.mkdir(parents=True, exist_ok=True)
    marker = base / ".source.json"
    cached_ok = False
    if marker.exists() and (base / "metrics").is_dir() and list((base / "metrics").glob("*.sql")):
        try:
            meta = json.loads(marker.read_text())
            cached_ok = meta.get("repo") == SOURCE_REPO and meta.get("ref") == SOURCE_REF
        except Exception:
            cached_ok = False
    if cached_ok:
        return _apply_metric_fixes(base, industry, size)
    ver_base = latest_version_path(industry)
    for sub in ("schemas", "metrics"):
        items = _gh_json(f"https://api.github.com/repos/{SOURCE_REPO}/contents/{ver_base}/{size}/{sub}?ref={SOURCE_REF}")
        dest = base / sub
        if dest.exists():
            import shutil
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for it in items:
            if it.get("type") != "file" or not it["name"].endswith(".sql"):
                continue
            url = it.get("download_url")
            if not url:
                continue
            data = _urlopen_with_retry(url)
            (dest / it["name"]).write_bytes(data)
    marker.write_text(json.dumps({"repo": SOURCE_REPO, "ref": SOURCE_REF}))
    return _apply_metric_fixes(base, industry, size)


def metric_sql_fingerprint(sql: str) -> str:
    return hashlib.md5(re.sub(r"\s+", " ", sql.strip()).encode()).hexdigest()[:16]


METRIC_VIEW_NAME_RE = re.compile(
    r"MetricView\s+`[^`]+`\.`[^`]+`\.`([^`]+)`", re.IGNORECASE
)
CREATE_VIEW_NAME_RE = re.compile(
    r"CREATE\s+OR\s+REPLACE\s+VIEW\s+`[^`]+`\.`[^`]+`\.`([^`]+)`", re.IGNORECASE
)
MV_NAME_IN_FILE_RE = re.compile(
    r"CREATE\s+OR\s+REPLACE\s+VIEW\s+`[^`]+`\.`_metrics`\.`([^`]+)`", re.IGNORECASE
)


def _failure_view_names(metric_failures: list[dict]) -> set[str]:
    names: set[str] = set()
    for f in metric_failures:
        if f.get("phase") not in (None, "metric"):
            continue
        for blob in (f.get("sql") or "", f.get("sql_preview") or "", f.get("error") or ""):
            m = METRIC_VIEW_NAME_RE.search(blob) or CREATE_VIEW_NAME_RE.search(blob)
            if m:
                names.add(m.group(1).lower())
    return names


def prune_failed_metrics(model_dir: Path, metric_failures: list[dict]) -> tuple[Path, list[str]]:
    """Remove metric SQL files matching failed statements; return pruned dir + removed names."""
    metrics_dir = model_dir / "metrics"
    if not metrics_dir.is_dir():
        return model_dir, []
    fail_view_names = _failure_view_names(metric_failures)
    pruned = model_dir.parent / f"{model_dir.name}_pruned_{uuid.uuid4().hex[:8]}"
    import shutil
    shutil.copytree(model_dir, pruned)
    removed = []
    for sql_file in list((pruned / "metrics").glob("*.sql")):
        content = sql_file.read_text(errors="ignore")
        norm = re.sub(r"\s+", " ", content.strip()).lower()
        stem = sql_file.stem.lower()
        drop = False
        if fail_view_names:
            m = CREATE_VIEW_NAME_RE.search(content) or MV_NAME_IN_FILE_RE.search(content)
            view_name = (m.group(1) if m else stem).lower()
            if view_name in fail_view_names or stem in fail_view_names:
                drop = True
        if not drop:
            for f in metric_failures:
                sql_blob = (f.get("sql") or f.get("sql_preview") or "").lower()
                if sql_blob and sql_blob[:80] in norm:
                    drop = True
                    break
        if drop:
            removed.append(sql_file.name)
            sql_file.unlink()
    return pruned, removed


def ensure_catalog(profile: str, cat: str) -> None:
    """Create catalog if missing, with managed-location fallback (installer-equivalent)."""
    st, _, rows = sql_exec(profile, f"DESCRIBE CATALOG EXTENDED `{cat}`", timeout=60)
    if st == "SUCCEEDED":
        return
    st, err, _ = sql_exec(profile, f"CREATE CATALOG `{cat}`", timeout=90)
    if st == "SUCCEEDED":
        return
    msg = (err.get("message") if isinstance(err, dict) else str(err)).lower()
    if not any(x in msg for x in ("storage root", "default storage", "managed location", "already exists")):
        raise RuntimeError(f"CREATE CATALOG `{cat}` failed: {msg[:300]}")
    st2, _, rows = sql_exec(profile, "SHOW EXTERNAL LOCATIONS", timeout=90)
    if st2 != "SUCCEEDED" or not rows:
        raise RuntimeError(f"CREATE CATALOG `{cat}` needs managed location but none available")
    last_err = msg
    for row in rows:
        name = row[0]
        url = (row[1] if len(row) > 1 else "").rstrip("/")
        if not url:
            continue
        loc = f"{url}/{cat}"
        st3, err3, _ = sql_exec(
            profile, f"CREATE CATALOG `{cat}` MANAGED LOCATION '{loc}'", timeout=90)
        if st3 == "SUCCEEDED":
            return
        last_err = (err3.get("message") if isinstance(err3, dict) else str(err3))[:200]
    raise RuntimeError(f"CREATE CATALOG `{cat}` managed-location failed: {last_err}")


def upload_pruned_to_volume(profile: str, industry: str, size: str, pruned_dir: Path) -> str:
    """Stage pruned model on a scratch volume path for local_install."""
    staging_cat = staging_catalog(profile, industry, size)
    ensure_catalog(profile, staging_cat)
    sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{staging_cat}`.`_staging`", timeout=60)
    sql_exec(profile, f"CREATE VOLUME IF NOT EXISTS `{staging_cat}`.`_staging`.`models`", timeout=60)
    vol_path = f"/Volumes/{staging_cat}/_staging/models/{industry}_{size}_pruned"
    remote = f"dbfs:{vol_path}"
    try:
        db(["fs", "rm", "-r", remote], profile, timeout=120)
    except Exception:
        pass
    db(["fs", "mkdirs", remote], profile, timeout=60)
    for sub in ("schemas", "metrics"):
        sub_local = pruned_dir / sub
        if not sub_local.is_dir():
            continue
        if not any(sub_local.glob("*.sql")):
            pulse(f"[upload] {industry}/{size} skip empty {sub}/ (stale remote cleared)")
            continue
        db(
            ["fs", "cp", "--recursive", str(sub_local), f"{remote}/{sub}", "--overwrite"],
            profile, timeout=600,
        )
    return vol_path


def fetch_failures_manifest(profile: str, catalog: str) -> list[dict]:
    logs_base = f"dbfs:/Volumes/{catalog}/_install/logs"
    try:
        listing = db(["fs", "ls", logs_base], profile, timeout=60)
    except Exception:
        return []
    files = [ln.split()[-1] for ln in listing.splitlines() if "failures_" in ln]
    if not files:
        return []
    latest = sorted(files)[-1]
    local = f"/tmp/failures_{catalog}.json"
    db(["fs", "cp", f"{logs_base}/{latest}", local, "--overwrite"], profile, timeout=60)
    try:
        return json.loads(Path(local).read_text())
    except Exception:
        return []


def cleanup_marathon_catalogs(profile: str, industries: list[str] | None = None) -> int:
    """DROP marathon_* catalogs for assigned industries (or all marathon_* if industries None)."""
    dropped = 0
    targets = []
    if industries:
        for ind in industries:
            for size in ("ecm", "mvm"):
                targets.append(catalog_name(ind, size))
    else:
        try:
            cats = dbj(["catalogs", "list"], profile, timeout=120)
            items = cats if isinstance(cats, list) else cats.get("catalogs", [])
            targets = [c["name"] for c in items if c.get("name", "").startswith("idx_")]
        except Exception:
            return 0
    for cat in targets:
        try:
            st, _, _ = sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=120)
            if st == "SUCCEEDED":
                dropped += 1
                pulse(f"[cleanup] {profile} dropped `{cat}`")
        except Exception as e:
            pulse(f"[cleanup] {profile} skip `{cat}`: {str(e)[:100]}")
    return dropped


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            return json.loads(Path(STATE_FILE).read_text())
        except Exception:
            pass
    return {"started_at": now()}


def save_state(state: dict) -> None:
    with _STATE_LOCK:
        state["updated_at"] = now()
        Path(os.path.dirname(STATE_FILE)).mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        Path(tmp).write_text(json.dumps(state, indent=2, default=str))
        os.replace(tmp, STATE_FILE)


def pool_item_key(profile: str, ind: str, size: str) -> str:
    return f"{profile}:{ind}:{size}"


def work_items_from_assign(assign: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for profile, industries in assign.items():
        for ind in industries:
            for size in ("ecm", "mvm"):
                items.append((profile, ind, size))
    return items


def cleanup_single_catalog(profile: str, ind: str, size: str) -> None:
    cat = catalog_name(ind, size)
    try:
        st, _, _ = sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=120)
        if st == "SUCCEEDED":
            pulse(f"[cleanup] {profile} dropped `{cat}`")
    except Exception as e:
        pulse(f"[cleanup] {profile} skip `{cat}`: {str(e)[:100]}")


def _row_industry_size(row: dict, tk: str) -> tuple[str | None, str | None]:
    ind, size = row.get("industry"), row.get("size")
    if ind and size not in (None, "unknown"):
        return ind, size
    ind, size = parse_task_meta(tk)
    if size != "unknown":
        return ind, size
    parsed = parse_industry_from_output(row.get("output") or {})
    return parsed if parsed else (ind, size)


def import_legacy_waves_to_pool(state: dict) -> None:
    pool = state.setdefault("waves", {}).setdefault("pool", {"items": {}, "started_at": now()})
    items = pool.setdefault("items", {})
    for wave_key in ("ecm_wave1", "mvm_wave2"):
        wave = state.get("waves", {}).get(wave_key, {})
        for profile, pinfo in wave.get("profiles", {}).items():
            parent_run = pinfo.get("run_id")
            for tk, row in pinfo.get("tasks", {}).items():
                ind, size = _row_industry_size(row, tk)
                if not ind or size in (None, "unknown"):
                    continue
                key = pool_item_key(profile, ind, size)
                entry = {**row, "profile": profile, "industry": ind, "size": size,
                         "catalog": catalog_name(ind, size), "task_key": tk}
                if row.get("life_cycle") in ("RUNNING", "PENDING", "QUEUED"):
                    entry["legacy_mode"] = True
                    entry["legacy_parent_run_id"] = parent_run
                prev = items.get(key)
                if prev and prev.get("bucket") == "clean":
                    continue
                if not prev or row.get("life_cycle") == "TERMINATED" or row.get("bucket"):
                    items[key] = entry
    save_state(state)


def _finalize_pool_row(profile: str, ind: str, size: str, task: dict, out: dict) -> dict:
    row = {
        "profile": profile, "industry": ind, "size": size,
        "catalog": catalog_name(ind, size),
        "task_key": task.get("task_key"),
        "task_run_id": task.get("run_id"),
        "run_id": task.get("run_id"),
        "life_cycle": task.get("life_cycle"),
        "result": task.get("result"),
        "message": task.get("message"),
        "output": out,
    }
    bucket = classify_bucket(task.get("result"), out)
    row["bucket"] = bucket
    if bucket == "warning":
        mf = parse_metric_failures_from_output(out)
        if not mf:
            mf = [m for m in fetch_failures_manifest(profile, row["catalog"]) if m.get("phase") == "metric"]
        row["metric_failures"] = mf
        row["failures_manifest"] = fetch_failures_manifest(profile, row["catalog"])
    return row


def reconcile_pool(state: dict) -> dict:
    pool = state.setdefault("waves", {}).setdefault("pool", {"items": {}})
    items = pool.setdefault("items", {})
    summary = {"clean": 0, "warning": 0, "failed": 0, "running": 0, "pending": 0}
    for key, item in list(items.items()):
        profile = item.get("profile") or key.split(":")[0]
        ind = item.get("industry")
        size = item.get("size")
        b = item.get("bucket")
        lc = item.get("life_cycle")
        if b in ("clean", "warning", "failed") and lc == "TERMINATED":
            summary[b] += 1
            continue
        try:
            if item.get("legacy_mode") and item.get("legacy_parent_run_id"):
                run = get_run(profile, item["legacy_parent_run_id"])
                task = next((t for t in run["tasks"] if t["task_key"] == item.get("task_key")), None)
                if not task:
                    summary["running"] += 1
                    continue
                if task["life_cycle"] == "TERMINATED" and task.get("run_id"):
                    out = fetch_task_output(profile, task["run_id"])
                    items[key] = _finalize_pool_row(profile, ind, size, task, out)
                    item = items[key]
                    item.pop("legacy_mode", None)
                elif task["life_cycle"] in ("RUNNING", "PENDING", "QUEUED"):
                    summary["running"] += 1
                    continue
            elif item.get("run_id"):
                run = get_run(profile, item["run_id"])
                if run["life_cycle"] not in _TERMINAL_LC:
                    summary["running"] += 1
                    continue
                task = run["tasks"][0] if run["tasks"] else {}
                if task.get("life_cycle") == "TERMINATED" and task.get("run_id"):
                    out = fetch_task_output(profile, task["run_id"])
                    items[key] = _finalize_pool_row(profile, ind, size, task, out)
                    item = items[key]
        except Exception as e:
            pulse(f"[pool reconcile] {key} failed (will retry): {str(e)[:180]}")
            summary["running"] += 1
            continue
        b = item.get("bucket")
        lc = item.get("life_cycle")
        if lc in ("RUNNING", "PENDING", "QUEUED"):
            summary["running"] += 1
        elif b in summary:
            summary[b] += 1
        elif lc == "TERMINATED":
            summary["failed"] += 1
        else:
            summary["pending"] += 1
    pool["summary"] = summary
    save_state(state)
    return summary


def _pool_needs_submit(item: dict | None) -> bool:
    if not item:
        return True
    if item.get("bucket") == "clean":
        return False
    if item.get("bucket") == "warning":
        return False
    if item.get("life_cycle") in ("RUNNING", "PENDING", "QUEUED"):
        return False
    if item.get("legacy_mode"):
        return False
    if item.get("run_id") and item.get("life_cycle") not in _TERMINAL_LC and item.get("life_cycle"):
        return False
    if item.get("life_cycle") == "TERMINATED":
        return item.get("bucket") == "failed" or item.get("result") in ("FAILED", "TIMEDOUT", "CANCELED")
    return True


def submit_pool_install(state: dict, profile: str, ind: str, size: str) -> None:
    key = pool_item_key(profile, ind, size)
    cleanup_single_catalog(profile, ind, size)
    spec = build_retry_job_spec(profile, ind, size, local_install="")
    job_id = find_or_reset_job(profile, spec)
    run_id = run_now(profile, job_id)
    pool = state.setdefault("waves", {}).setdefault("pool", {"items": {}})
    pool["items"][key] = {
        "profile": profile, "industry": ind, "size": size,
        "catalog": catalog_name(ind, size), "job_id": job_id, "run_id": run_id,
        "started_at": now(), "life_cycle": "RUNNING",
    }
    pulse(f"[pool submit] {ind}/{size} @{profile} run={run_id}")
    save_state(state)


def _item_running(item: dict) -> bool:
    if item.get("life_cycle") in ("RUNNING", "PENDING", "QUEUED"):
        return True
    if item.get("legacy_mode"):
        return True
    if item.get("run_id") and item.get("life_cycle") not in _TERMINAL_LC and item.get("life_cycle"):
        return True
    return False


def _profile_active_count(items: dict, profile: str) -> int:
    return sum(1 for it in items.values() if it.get("profile") == profile and _item_running(it))


def monitor_pool(
    state: dict,
    assign: dict[str, list[str]],
    max_parallel: int,
    poll_s: int,
    work_items: list[tuple[str, str, str]] | None = None,
    profile_parallel: dict[str, int] | None = None,
) -> dict:
    state["max_parallel"] = max_parallel
    pool = state.setdefault("waves", {}).setdefault("pool", {"items": {}, "started_at": now()})
    import_legacy_waves_to_pool(state)
    pulse(f"monitor pool max_parallel={max_parallel} every {poll_s}s (ECM+MVM unified)")
    work = work_items or work_items_from_assign(assign)
    ppar = profile_parallel or {}
    last_heartbeat = time.time()
    while True:
        reconcile_pool(state)
        items = pool.get("items", {})
        active = sum(1 for it in items.values() if _item_running(it))
        pending = [(p, i, s) for p, i, s in work if _pool_needs_submit(items.get(pool_item_key(p, i, s)))]
        slots = max(0, max_parallel - active)
        submitted = 0
        for profile, ind, size in pending:
            if submitted >= slots:
                break
            blocked = state.get("blocked_profiles") or {}
            if profile in blocked:
                continue
            pmax = ppar.get(profile, max_parallel)
            if _profile_active_count(items, profile) >= pmax:
                continue
            submit_pool_install(state, profile, ind, size)
            submitted += 1
            active += 1
        s = reconcile_pool(state)
        pulse(
            f"[pool] clean={s['clean']} warn={s['warning']} fail={s['failed']} "
            f"run={s['running']} pending={len(pending) - min(slots, len(pending))}"
        )
        still_pending = sum(1 for p, i, sz in work if _pool_needs_submit(items.get(pool_item_key(p, i, sz))))
        if s["running"] == 0 and still_pending == 0:
            break
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL_S:
            try:
                emit_marathon_heartbeat(state)
            except Exception as e:
                pulse(f"[HEARTBEAT] emit failed: {e}")
            last_heartbeat = time.time()
        time.sleep(poll_s)
    return reconcile_pool(state)


def prepare_warning_retry_model(
    profile: str, ind: str, size: str, row: dict, aggressive: bool = False,
) -> tuple[Path, list[str]]:
    model_dir = download_model_tree(ind, size)
    cat = row.get("catalog") or catalog_name(ind, size)
    mf = fetch_failures_manifest(profile, cat)
    if not mf:
        mf = row.get("failures_manifest") or row.get("metric_failures") or []
    pruned, removed = prune_failed_metrics(model_dir, mf)
    if aggressive:
        fail_names = _failure_view_names(mf)
        metrics_dir = pruned / "metrics"
        for sql_file in list(metrics_dir.glob("*.sql")):
            if sql_file.name in removed:
                continue
            content = sql_file.read_text(errors="ignore")
            m = CREATE_VIEW_NAME_RE.search(content) or MV_NAME_IN_FILE_RE.search(content)
            view_name = (m.group(1) if m else sql_file.stem).lower()
            if fail_names and (view_name in fail_names or stem_in_failures(sql_file, mf)):
                removed.append(sql_file.name)
                sql_file.unlink()
        # attempt 2+: drop ALL remaining metric SQL so install is structurally clean
        for sql_file in list(metrics_dir.glob("*.sql")):
            if sql_file.name not in removed:
                removed.append(sql_file.name)
                sql_file.unlink()
        pulse(f"[retry prune] {ind}/{size} aggressive=True removed_all_metrics={len(removed)}")
    return pruned, removed


def stem_in_failures(sql_file: Path, metric_failures: list[dict]) -> bool:
    stem = sql_file.stem.lower()
    for f in metric_failures:
        blob = (f.get("sql") or f.get("sql_preview") or f.get("error") or "").lower()
        if stem in blob or sql_file.name.lower() in blob:
            return True
    return False


def _retry_in_flight(retries: dict, key: str) -> bool:
    info = retries.get(key, {})
    return bool(info.get("run_id") and not info.get("final_bucket"))


def submit_warning_retry(state: dict, key: str, row: dict) -> None:
    profile, ind, size = row["profile"], row["industry"], row["size"]
    prior = state.get("retries", {}).get(key, {})
    attempt = int(prior.get("attempt") or 0) + 1
    aggressive = (
        row.get("bucket") in ("warning", "failed")
        or prior.get("final_bucket") in ("warning", "failed")
        or attempt > 1
    )
    pulse(f"[retry] {key} fixing metric SQL + reinstall (attempt={attempt} aggressive={aggressive}) ...")
    try:
        pruned, removed = prepare_warning_retry_model(profile, ind, size, row, aggressive=aggressive)
        cleanup_single_catalog(profile, ind, size)
        vol_path = upload_pruned_to_volume(profile, ind, size, pruned)
        install_cat = resolve_install_catalog(profile, ind, size)
        spec = build_retry_job_spec(profile, ind, size, vol_path, catalog=install_cat)
        job_id = find_or_reset_job(profile, spec)
        run_id = run_now(profile, job_id)
        with _STATE_LOCK:
            state.setdefault("retries", {})[key] = {
                "removed_metrics": removed, "local_install": vol_path,
                "job_id": job_id, "run_id": run_id, "started_at": now(),
                "attempt": attempt, "aggressive": aggressive,
                "install_catalog": install_cat,
            }
        pulse(f"[retry] {key} submitted run={run_id} pruned_files={len(removed)}")
    except Exception as e:
        with _STATE_LOCK:
            state.setdefault("retries", {})[key] = {
                "error": str(e)[:500], "attempt": attempt, "aggressive": aggressive,
            }
        pulse(f"[retry] {key} FAILED setup: {e}")
    save_state(state)


def _pool_score(state: dict) -> dict[str, int]:
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    counts = {"clean": 0, "warning": 0, "failed": 0, "other": 0, "total": len(items)}
    for row in items.values():
        b = row.get("bucket")
        if b in counts:
            counts[b] += 1
        elif b:
            counts["other"] += 1
        else:
            counts["other"] += 1
    return counts


def _retry_targets(state: dict) -> list[str]:
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    return [
        k for k, v in items.items()
        if v.get("bucket") in ("warning", "failed") or not v.get("bucket")
    ]


def _pool_coming_queue(state: dict) -> list[str]:
    """Next installs not yet clean or in-flight (pool verification mode)."""
    split = state.get("split_mode")
    assign = state.get("assign", {})
    work = build_work_items(assign, split)
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    coming: list[str] = []
    for profile, ind, size in work:
        key = pool_item_key(profile, ind, size)
        it = items.get(key)
        if it and it.get("bucket") == "clean":
            continue
        if it and _item_running(it):
            continue
        if it and it.get("bucket") in ("warning", "failed"):
            coming.append(f"  {ind}/{size} @{profile}  RETRY ({it.get('bucket')})")
        else:
            coming.append(f"  {ind}/{size} @{profile}")
    return coming


_AUDIT_ERROR_PATTERNS = [
    (re.compile(r"\bERROR\b"), "ERROR"),
    (re.compile(r"Traceback \(most recent"), "Traceback"),
    (re.compile(r"UNRECOVERABLE STATEMENTS"), "UNRECOVERABLE"),
    (re.compile(r"Failed metric view"), "Failed metric view"),
    (re.compile(r"installed_with_warnings"), "installed_with_warnings"),
    (re.compile(r"Max retries \(3\) exhausted"), "soft-accept"),
]


def _audit_text_blob(item: dict) -> str:
    out = item.get("output") or {}
    nb = out.get("notebook_output") if isinstance(out, dict) else ""
    if isinstance(nb, dict):
        nb = str(nb.get("result") or nb.get("truncated") or "")
    err = ""
    if isinstance(out, dict):
        err = str(out.get("error") or "")
    return f"{nb}\n{err}"


def _audit_success_line(text: str) -> tuple[bool, str]:
    m = re.search(
        r"SUCCESS:\s*(\S+)\s*->\s*`([^`]+)`\s*\((\d+)\s*statements,\s*(\d+)\s*failures",
        text,
    )
    if not m:
        return False, "missing SUCCESS line"
    failures = int(m.group(4))
    if failures > 0:
        return False, f"SUCCESS reports {failures} failures"
    return True, f"catalog={m.group(2)} statements={m.group(3)}"


def audit_pool_item(key: str, item: dict, profile: str | None = None) -> dict:
    """Independent per-install audit — returns {key, pass, issues[], detail}."""
    prof = profile or item.get("profile") or key.split(":")[0]
    issues: list[str] = []
    text = _audit_text_blob(item)
    if not text.strip() and item.get("run_id"):
        try:
            run = get_run(prof, item["run_id"])
            task = run["tasks"][0] if run.get("tasks") else {}
            if task.get("run_id"):
                out = fetch_task_output(prof, task["run_id"])
                item = {**item, "output": out}
                text = _audit_text_blob(item)
        except Exception as e:
            issues.append(f"fetch_output: {str(e)[:120]}")
    ok_line, detail = _audit_success_line(text)
    if not ok_line:
        issues.append(detail)
    for pat, label in _AUDIT_ERROR_PATTERNS:
        hits = pat.findall(text)
        if hits:
            issues.append(f"{label} x{len(hits)}")
    cat = item.get("catalog") or catalog_name(item.get("industry", ""), item.get("size", ""))
    try:
        logs_base = f"dbfs:/Volumes/{cat}/_install/logs"
        listing = db(["fs", "ls", logs_base], prof, timeout=60)
        log_files = [ln.split()[-1] for ln in listing.splitlines() if "install_" in ln and ln.endswith(".log")]
        if log_files:
            latest = sorted(log_files)[-1]
            local = f"/tmp/audit_{cat}.log"
            db(["fs", "cp", f"{logs_base}/{latest}", local, "--overwrite"], prof, timeout=120)
            vol_text = Path(local).read_text(errors="ignore")
            for pat, label in _AUDIT_ERROR_PATTERNS:
                hits = pat.findall(vol_text)
                if hits:
                    issues.append(f"volume_log:{label} x{len(hits)}")
            if re.search(r"(\d+)\s*failures", vol_text):
                fm = re.search(r"(\d+)\s*failures", vol_text)
                if fm and int(fm.group(1)) > 0:
                    issues.append(f"volume_log:failures={fm.group(1)}")
    except Exception:
        pass
    return {"key": key, "pass": len(issues) == 0, "issues": issues, "detail": detail}


def run_independent_audit(state: dict, only_clean: bool = True) -> dict:
    """Audit all clean (or all terminal) pool installs; write AUDIT_FILE."""
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    results: list[dict] = []
    for key, item in sorted(items.items()):
        if only_clean and item.get("bucket") != "clean":
            continue
        if not only_clean and item.get("bucket") not in ("clean", "warning", "failed"):
            continue
        results.append(audit_pool_item(key, item))
    passed = sum(1 for r in results if r["pass"])
    failed = [r for r in results if not r["pass"]]
    report = {
        "audited_at": now(),
        "audited": len(results),
        "passed": passed,
        "failed": len(failed),
        "failures": failed,
    }
    lines = [
        f"========== INDEPENDENT AUDIT {now()} ==========",
        f"AUDITED: {len(results)}  PASSED: {passed}  FAILED: {len(failed)}",
    ]
    if failed:
        lines.append("VIOLATIONS (must be ZERO for 80/80 clean):")
        for r in failed:
            lines.append(f"  {r['key']}: {', '.join(r['issues'])}")
    else:
        lines.append("VIOLATIONS: none")
    lines.append("=" * 52)
    block = "\n".join(lines)
    Path(os.path.dirname(AUDIT_FILE)).mkdir(parents=True, exist_ok=True)
    with open(AUDIT_FILE, "a") as f:
        f.write(block + "\n")
    pulse(f"[AUDIT] audited={len(results)} pass={passed} fail={len(failed)}")
    return report


def emit_marathon_heartbeat(state: dict) -> str:
    """Write a 15m-style status block: installed / running / coming + independent audit."""
    reconcile_pool(state)
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    retries = state.get("retries", {})
    score = _pool_score(state)
    split = state.get("split_mode")

    clean_keys = sorted(k for k, v in items.items() if v.get("bucket") == "clean")
    clean_lines = [
        f"  {k}  catalog={items[k].get('catalog', '?')}"
        for k in clean_keys
    ]

    running: list[str] = []
    for k, v in sorted(items.items()):
        if not _item_running(v):
            ri = retries.get(k, {})
            if ri.get("run_id") and not ri.get("final_bucket"):
                running.append(f"  {k}  retry_run={ri['run_id']}  attempt={ri.get('attempt', 1)}")
            continue
        rid = v.get("run_id") or v.get("task_run_id") or "?"
        running.append(f"  {v.get('industry')}/{v.get('size')} @{v.get('profile')}  run={rid}")

    if split:
        coming = _pool_coming_queue(state)
    else:
        targets = _retry_targets(state)
        coming = []
        for k in sorted(targets):
            ri = retries.get(k, {})
            if ri.get("final_bucket") == "clean":
                continue
            if ri.get("run_id") and not ri.get("final_bucket"):
                continue
            if ri.get("error"):
                coming.append(f"  {k}  (setup retry after error)")
            else:
                coming.append(f"  {k}")

    prev_clean: set[str] = set()
    if os.path.exists(HEARTBEAT_STATE_FILE):
        try:
            prev_clean = set(json.loads(Path(HEARTBEAT_STATE_FILE).read_text()).get("clean_keys", []))
        except Exception:
            pass
    new_fixed = sorted(set(clean_keys) - prev_clean)
    Path(HEARTBEAT_STATE_FILE).write_text(json.dumps({
        "last_beat": now(), "clean_keys": clean_keys,
    }, indent=2))

    audit = run_independent_audit(state, only_clean=True)

    with _SETUP_LOCK:
        setup_busy = _setup_active
    monitor_pid = os.getpid()
    mode = "VERIFY" if split else "MARATHON"
    ecm_p = split.get("ecm", "?") if split else "?"
    mvm_p = split.get("mvm", "?") if split else "?"

    lines = [
        f"========== {mode} HEARTBEAT {now()} ==========",
        f"TARGET: 80/80 clean — ZERO errors (independent audit)",
        f"LAYOUT:  ECM@{ecm_p}  MVM@{mvm_p}" if split else "LAYOUT: multi-profile pool",
        f"SCORE:  clean={score['clean']}/80  warning={score['warning']}  failed={score['failed']}",
        f"MONITOR: pid={monitor_pid}  setup_in_flight={setup_busy}",
        "",
        f"INSTALLED CLEAN ({score['clean']}):",
    ]
    if clean_lines:
        lines.extend(clean_lines[-40:])
        if len(clean_lines) > 40:
            lines.append(f"  ... +{len(clean_lines) - 40} more (see state file)")
    else:
        lines.append("  (none yet)")
    lines.append("")
    lines.append(f"NEW CLEAN since last beat (+{len(new_fixed)}):")
    if new_fixed:
        lines.extend(f"  {k}" for k in new_fixed)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"RUNNING ({len(running)}):")
    lines.extend(running[:40] if running else ["  (none)"])
    if len(running) > 40:
        lines.append(f"  ... +{len(running) - 40} more")
    lines.append("")
    lines.append(f"COMING NEXT ({len(coming)}):")
    lines.extend(coming[:30] if coming else ["  (none — all submitted or done)"])
    if len(coming) > 30:
        lines.append(f"  ... +{len(coming) - 30} more")
    lines.append("")
    lines.append("INDEPENDENT AUDITOR (clean installs only):")
    lines.append(f"  audited={audit['audited']}  passed={audit['passed']}  violations={audit['failed']}")
    if audit["failed"]:
        for r in audit["failures"][:10]:
            lines.append(f"  FAIL {r['key']}: {', '.join(r['issues'])}")
    else:
        lines.append("  violations=ZERO")
    lines.append("=" * 52)

    block = "\n".join(lines)
    Path(os.path.dirname(HEARTBEAT_FILE)).mkdir(parents=True, exist_ok=True)
    with open(HEARTBEAT_FILE, "a") as f:
        f.write(block + "\n")
    pulse(
        f"[HEARTBEAT] clean={score['clean']}/80 warn={score['warning']} fail={score['failed']} "
        f"run={len(running)} queue={len(coming)} audit_violations={audit['failed']} new_clean=+{len(new_fixed)}"
    )
    return block


def _start_setup_async(state: dict, key: str, row: dict) -> bool:
    global _setup_active
    with _SETUP_LOCK:
        if _setup_active >= MAX_SETUP_PARALLEL:
            return False
        _setup_active += 1

    def _work() -> None:
        global _setup_active
        try:
            with _STATE_LOCK:
                ri = state.get("retries", {}).get(key, {})
                if ri.get("error"):
                    state["retries"].pop(key, None)
                if ri.get("final_bucket") == "warning":
                    state["retries"].pop(key, None)
            submit_warning_retry(state, key, row)
        finally:
            with _SETUP_LOCK:
                _setup_active -= 1

    threading.Thread(target=_work, daemon=True).start()
    return True


def sync_retries_to_pool(state: dict) -> None:
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    for key, info in state.get("retries", {}).items():
        fb = info.get("final_bucket")
        if not fb or key not in items:
            continue
        items[key]["bucket"] = fb
        items[key]["retry_result"] = info.get("result")
        items[key]["output"] = {"notebook_output": info.get("output_tail", "")}
        if info.get("install_catalog"):
            items[key]["catalog"] = info["install_catalog"]
    save_state(state)


def poll_retries_once(state: dict) -> dict:
    """Poll in-flight retry runs once and sync pool buckets."""
    retries = state.get("retries", {})
    targets = _retry_targets(state)
    for key in targets:
        if not _retry_in_flight(retries, key):
            continue
        info = retries[key]
        profile = key.split(":")[0]
        try:
            run = get_run(profile, info["run_id"])
        except Exception as e:
            pulse(f"[retry poll] {key} get-run failed: {str(e)[:120]}")
            continue
        if run["life_cycle"] not in _TERMINAL_LC:
            continue
        task = run["tasks"][0] if run["tasks"] else {}
        out = fetch_task_output(profile, task.get("run_id") or info["run_id"])
        bucket = classify_bucket(task.get("result"), out)
        info["final_bucket"] = bucket
        info["result"] = task.get("result")
        info["output_tail"] = (out.get("notebook_output") or "")[-800:]
        pulse(f"[retry done] {key} -> {bucket}")
    sync_retries_to_pool(state)
    return _pool_score(state)


def submit_next_retry(state: dict, max_parallel: int = 40) -> str | None:
    """Submit at most one aggressive retry if capacity allows. Returns key or None."""
    lock_path = STATE_FILE + ".submit.lock"
    key: str | None = None
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)
        state = load_state()
        targets = _retry_targets(state)
        retries = state.setdefault("retries", {})
        active_runs = sum(1 for k in targets if _retry_in_flight(retries, k))
        if active_runs >= max_parallel:
            return None
        items = state.get("waves", {}).get("pool", {}).get("items", {})
        now_ts = time.time()
        for k in targets:
            ri = retries.get(k, {})
            if ri.get("final_bucket") == "clean":
                continue
            if _retry_in_flight(retries, k):
                continue
            claimed = ri.get("submitting_at")
            if claimed:
                try:
                    age = now_ts - datetime.fromisoformat(
                        claimed.replace("Z", "+00:00")
                    ).timestamp()
                except Exception:
                    age = 0
                if age < 600:
                    continue
            key = k
            if ri.get("error"):
                retries.pop(k, None)
            if ri.get("final_bucket") in ("warning", "failed"):
                retries.pop(k, None)
            retries[k] = {"submitting_at": now()}
            save_state(state)
            break
    if not key:
        return None
    state = load_state()
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    try:
        submit_warning_retry(state, key, items[key])
    except Exception as e:
        pulse(f"[submit-next] {key} failed: {e}")
        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf, fcntl.LOCK_EX)
            state = load_state()
            ri = state.setdefault("retries", {}).get(key, {})
            if not ri.get("run_id"):
                state["retries"][key] = {"error": str(e)[:500], "attempt": ri.get("attempt", 0)}
            save_state(state)
    return key


def monitor_retries_parallel(state: dict, max_parallel: int, poll_s: int = 90, *, submit: bool = True) -> None:
    pulse(f"monitor retries max_parallel={max_parallel} every {poll_s}s — target 80/80 clean")
    last_heartbeat = 0.0
    emit_marathon_heartbeat(state)
    last_heartbeat = time.time()
    while True:
        try:
            reconcile_pool(state)
            retries = state.get("retries", {})
            items = state.get("waves", {}).get("pool", {}).get("items", {})
            score = _pool_score(state)
            targets = _retry_targets(state)

            for key in targets:
                if not _retry_in_flight(retries, key):
                    continue
                info = retries[key]
                profile = key.split(":")[0]
                try:
                    run = get_run(profile, info["run_id"])
                except Exception as e:
                    pulse(f"[retry poll] {key} get-run failed: {str(e)[:120]}")
                    continue
                if run["life_cycle"] not in _TERMINAL_LC:
                    continue
                task = run["tasks"][0] if run["tasks"] else {}
                out = fetch_task_output(profile, task.get("run_id") or info["run_id"])
                bucket = classify_bucket(task.get("result"), out)
                info["final_bucket"] = bucket
                info["result"] = task.get("result")
                info["output_tail"] = (out.get("notebook_output") or "")[-800:]
                pulse(f"[retry done] {key} -> {bucket}")
            sync_retries_to_pool(state)

            retries = state.get("retries", {})
            items = state.get("waves", {}).get("pool", {}).get("items", {})
            score = _pool_score(state)
            if score["clean"] >= 80 and score["warning"] == 0 and score["failed"] == 0 and score["other"] == 0:
                pulse(f"[DONE] 80/80 clean — zero warnings/failures")
                break

            active_runs = sum(1 for k in targets if _retry_in_flight(retries, k))
            with _SETUP_LOCK:
                setup_busy = _setup_active
            slots = max(0, max_parallel - active_runs - setup_busy)

            need: list[str] = []
            for k in targets:
                ri = retries.get(k, {})
                if ri.get("final_bucket") == "clean":
                    continue
                if _retry_in_flight(retries, k):
                    continue
                need.append(k)

            started = 0
            if submit:
                for key in need:
                    if slots <= 0:
                        break
                    try:
                        if _start_setup_async(state, key, items[key]):
                            started += 1
                            slots -= 1
                    except Exception as e:
                        pulse(f"[retry setup] {key} failed: {e}")

            still_running = sum(1 for k in targets if _retry_in_flight(state.get("retries", {}), k))
            pulse(
                f"[retries] pool clean={score['clean']}/80 warn={score['warning']} "
                f"fail={score['failed']} other={score['other']} run={still_running} "
                f"setup={setup_busy} queue={len(need)} started={started}"
            )
            if (
                score["clean"] >= 80
                and score["warning"] == 0
                and score["failed"] == 0
                and score["other"] == 0
                and still_running == 0
                and setup_busy == 0
                and not need
            ):
                pulse(f"[DONE] 80/80 clean — zero warnings/failures")
                break
        except Exception as e:
            pulse(f"[monitor] iteration error (will continue): {e}")
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL_S:
            try:
                emit_marathon_heartbeat(state)
            except Exception as e:
                pulse(f"[HEARTBEAT] emit failed: {e}")
            last_heartbeat = time.time()
        time.sleep(poll_s)
    reconcile_pool(state)


def retry_warnings_pool(state: dict) -> None:
    state.setdefault("retries", {})
    items = state.get("waves", {}).get("pool", {}).get("items", {})
    for key, row in items.items():
        if row.get("bucket") != "warning":
            continue
        profile, ind, size = row["profile"], row["industry"], row["size"]
        pulse(f"[retry] {key} pruning failed metric views ...")
        try:
            model_dir = download_model_tree(ind, size)
            mf = row.get("metric_failures") or []
            manifest = row.get("failures_manifest") or fetch_failures_manifest(profile, row["catalog"])
            if manifest:
                mf = manifest
            pruned, removed = prune_failed_metrics(model_dir, mf)
            if not removed and mf:
                removed = [f"manifest_{i}" for i in range(len(mf))]
            cleanup_single_catalog(profile, ind, size)
            vol_path = upload_pruned_to_volume(profile, ind, size, pruned)
            spec = build_retry_job_spec(profile, ind, size, vol_path)
            job_id = find_or_reset_job(profile, spec)
            run_id = run_now(profile, job_id)
            state["retries"][key] = {
                "removed_metrics": removed, "local_install": vol_path,
                "job_id": job_id, "run_id": run_id, "started_at": now(),
            }
            pulse(f"[retry] {key} submitted run={run_id} removed={len(removed)} files")
        except Exception as e:
            state["retries"][key] = {"error": str(e)[:500]}
            pulse(f"[retry] {key} FAILED setup: {e}")
    save_state(state)


def launch_wave(state: dict, assign: dict[str, list[str]], size: str, phase: str) -> None:
    state.setdefault("waves", {})[f"{size}_{phase}"] = {"started_at": now(), "profiles": {}}
    for profile, industries in assign.items():
        spec = build_wave_job_spec(profile, industries, size, phase)
        cleanup_marathon_catalogs(profile, industries)
        job_id = find_or_reset_job(profile, spec)
        run_id = run_now(profile, job_id)
        pulse(f"[wave {size}] {profile} job={job_id} run={run_id} tasks={len(industries)}")
        state["waves"][f"{size}_{phase}"]["profiles"][profile] = {
            "job_id": job_id, "run_id": run_id, "industries": industries,
            "url": None, "tasks": {},
        }
    save_state(state)


def wave_terminal(state: dict, wave_key: str) -> bool:
    wave = state.get("waves", {}).get(wave_key, {})
    for pinfo in wave.get("profiles", {}).values():
        lc = pinfo.get("life_cycle")
        if lc not in _TERMINAL_LC:
            return False
    return bool(wave.get("profiles"))


def reconcile_wave(state: dict, wave_key: str) -> dict:
    wave = state.setdefault("waves", {}).setdefault(wave_key, {"profiles": {}})
    summary = {"clean": 0, "warning": 0, "failed": 0, "running": 0}
    for profile, pinfo in wave.get("profiles", {}).items():
        run_id = pinfo.get("run_id")
        if not run_id:
            continue
        try:
            run = get_run(profile, run_id)
        except Exception as e:
            pulse(f"[reconcile] {profile} get-run failed (will retry): {str(e)[:200]}")
            summary["running"] += len(pinfo.get("tasks") or {}) or 1
            continue
        pinfo["life_cycle"] = run["life_cycle"]
        pinfo["result"] = run["result"]
        pinfo["url"] = run["url"]
        for t in run["tasks"]:
            ind, size = parse_task_meta(t["task_key"])
            row = {
                "industry": ind, "size": size, "catalog": catalog_name(ind, size),
                "task_key": t["task_key"], "task_run_id": t["run_id"],
                "life_cycle": t["life_cycle"], "result": t["result"],
                "message": t["message"],
            }
            if t["life_cycle"] == "TERMINATED" and t["run_id"]:
                out = fetch_task_output(profile, t["run_id"])
                row["output"] = out
                parsed = parse_industry_from_output(out)
                if parsed and (size == "unknown" or ind.startswith("wave")):
                    ind, size = parsed
                    row["industry"] = ind
                    row["size"] = size
                    row["catalog"] = catalog_name(ind, size)
                bucket = classify_bucket(t["result"], out)
                row["bucket"] = bucket
                if bucket == "warning":
                    mf = parse_metric_failures_from_output(out)
                    if not mf:
                        mf = [{"phase": "metric", "sql_preview": "", "error": ""}
                              for _ in fetch_failures_manifest(profile, row["catalog"])
                              if _.get("phase") == "metric"]
                    row["metric_failures"] = mf
                    manifest = fetch_failures_manifest(profile, row["catalog"])
                    row["failures_manifest"] = manifest
                summary[bucket if bucket in summary else "failed"] += 1
            elif t["life_cycle"] in ("RUNNING", "PENDING", "QUEUED"):
                summary["running"] += 1
            pinfo.setdefault("tasks", {})[t["task_key"]] = row
    wave["summary"] = summary
    save_state(state)
    return summary


def monitor_wave(state: dict, wave_key: str, poll_s: int = 120) -> dict:
    pulse(f"monitor wave {wave_key} every {poll_s}s")
    while not wave_terminal(state, wave_key):
        s = reconcile_wave(state, wave_key)
        pulse(f"[{wave_key}] clean={s['clean']} warn={s['warning']} fail={s['failed']} run={s['running']}")
        time.sleep(poll_s)
    return reconcile_wave(state, wave_key)


def retry_warnings(state: dict, wave_key: str) -> None:
    state.setdefault("retries", {})
    wave = state.get("waves", {}).get(wave_key, {})
    for profile, pinfo in wave.get("profiles", {}).items():
        for tk, row in pinfo.get("tasks", {}).items():
            if row.get("bucket") != "warning":
                continue
            ind, size = row["industry"], row["size"]
            key = f"{profile}:{ind}:{size}"
            pulse(f"[retry] {key} pruning failed metric views ...")
            try:
                model_dir = download_model_tree(ind, size)
                mf = row.get("metric_failures") or []
                manifest = row.get("failures_manifest") or fetch_failures_manifest(profile, row["catalog"])
                if manifest:
                    mf = manifest
                pruned, removed = prune_failed_metrics(model_dir, mf)
                if not removed and mf:
                    removed = [f"manifest_{i}" for i in range(len(mf))]
                cleanup_marathon_catalogs(profile, [ind])
                vol_path = upload_pruned_to_volume(profile, ind, size, pruned)
                spec = build_retry_job_spec(profile, ind, size, vol_path)
                job_id = find_or_reset_job(profile, spec)
                run_id = run_now(profile, job_id)
                state["retries"][key] = {
                    "removed_metrics": removed, "local_install": vol_path,
                    "job_id": job_id, "run_id": run_id, "started_at": now(),
                }
                pulse(f"[retry] {key} submitted run={run_id} removed={len(removed)} files")
            except Exception as e:
                state["retries"][key] = {"error": str(e)[:500]}
                pulse(f"[retry] {key} FAILED setup: {e}")
    save_state(state)


def monitor_retries(state: dict, poll_s: int = 90) -> None:
    retries = state.get("retries", {})
    pending = {k: v for k, v in retries.items() if v.get("run_id") and not v.get("final_bucket")}
    while pending:
        for key, info in list(pending.items()):
            profile = key.split(":")[0]
            run = get_run(profile, info["run_id"])
            if run["life_cycle"] not in _TERMINAL_LC:
                continue
            task = run["tasks"][0] if run["tasks"] else {}
            out = fetch_task_output(profile, task.get("run_id") or info["run_id"])
            bucket = classify_bucket(task.get("result"), out)
            info["final_bucket"] = bucket
            info["result"] = task.get("result")
            info["output_tail"] = (out.get("notebook_output") or "")[-800:]
            pending.pop(key, None)
            pulse(f"[retry done] {key} -> {bucket}")
        if pending:
            time.sleep(poll_s)
    save_state(state)


def final_cleanup(state: dict, assign: dict[str, list[str]]) -> int:
    total = 0
    for profile, industries in assign.items():
        total += cleanup_marathon_catalogs(profile, industries)
        staging = f"idx_staging_{profile.replace('-', '_')}"
        try:
            sql_exec(profile, f"DROP CATALOG IF EXISTS `{staging}` CASCADE", timeout=60)
        except Exception:
            pass
    state["cleanup_dropped"] = total
    save_state(state)
    return total


def build_final_report(state: dict) -> dict:
    buckets = {
        "ecm": {"clean": [], "warning": [], "failed": []},
        "mvm": {"clean": [], "warning": [], "failed": []},
    }
    retried_clean = []
    retried_still_warning = []
    retried_failed = []

    for wave_key in ("ecm_wave1", "mvm_wave2"):
        size = "ecm" if wave_key.startswith("ecm") else "mvm"
        wave = state.get("waves", {}).get(wave_key, {})
        for profile, pinfo in wave.get("profiles", {}).items():
            for row in pinfo.get("tasks", {}).values():
                entry = {
                    "profile": profile, "industry": row["industry"],
                    "catalog": row["catalog"], "result": row.get("result"),
                    "bucket": row.get("bucket"),
                    "metric_failures": row.get("metric_failures", []),
                    "failures_manifest": row.get("failures_manifest", []),
                }
                b = row.get("bucket", "failed")
                if b not in buckets[size]:
                    b = "failed"
                buckets[size][b].append(entry)

    pool_items = state.get("waves", {}).get("pool", {}).get("items", {})
    if pool_items:
        buckets = {"ecm": {"clean": [], "warning": [], "failed": []},
                   "mvm": {"clean": [], "warning": [], "failed": []}}
        for row in pool_items.values():
            size = row.get("size", "ecm")
            if size not in buckets:
                continue
            entry = {
                "profile": row.get("profile"), "industry": row.get("industry"),
                "catalog": row.get("catalog"), "result": row.get("result"),
                "bucket": row.get("bucket"),
                "metric_failures": row.get("metric_failures", []),
                "failures_manifest": row.get("failures_manifest", []),
            }
            b = row.get("bucket", "failed")
            if b not in buckets[size]:
                b = "failed"
            buckets[size][b].append(entry)

    for key, info in state.get("retries", {}).items():
        profile, ind, size = key.split(":")
        item = {"profile": profile, "industry": ind, "size": size,
                "removed": info.get("removed_metrics", []), "bucket": info.get("final_bucket")}
        fb = info.get("final_bucket")
        if fb == "clean":
            retried_clean.append(item)
        elif fb == "warning":
            retried_still_warning.append(item)
        else:
            retried_failed.append(item)

    return {
        "generated_at": now(),
        "capable_profiles": state.get("capable_profiles", {}),
        "blocked_profiles": state.get("blocked_profiles", {}),
        "assign": state.get("assign", {}),
        "ecm": buckets["ecm"],
        "mvm": buckets["mvm"],
        "retries": {
            "clean_after_prune": retried_clean,
            "still_warning": retried_still_warning,
            "failed": retried_failed,
        },
        "cleanup_dropped": state.get("cleanup_dropped", 0),
    }


def print_final_report(report: dict) -> None:
    print("\n" + "=" * 72)
    print("INSTALL MARATHON V2 REPORT")
    print("=" * 72)
    print(f"Generated: {report['generated_at']}")
    print("\n--- Catalog-capable profiles ---")
    for p, d in report.get("capable_profiles", {}).items():
        print(f"  {p}: {d}")
    print("\n--- Blocked profiles (excluded) ---")
    for p, d in report.get("blocked_profiles", {}).items():
        print(f"  {p}: {d[:120]}")
    for size in ("ecm", "mvm"):
        b = report[size]
        print(f"\n--- {size.upper()} installs ---")
        print(f"  CLEAN:   {len(b['clean'])}")
        print(f"  WARNING: {len(b['warning'])}")
        print(f"  FAILED:  {len(b['failed'])}")
        if b["clean"]:
            print("  Clean:", ", ".join(f"{x['industry']}@{x['profile']}" for x in b["clean"]))
        if b["warning"]:
            print("  Warning (metric defects):")
            for x in b["warning"]:
                mf = x.get("failures_manifest") or x.get("metric_failures") or []
                n_met = sum(1 for m in mf if m.get("phase") == "metric")
                print(f"    {x['industry']}@{x['profile']} ({n_met} metric failures in manifest)")
                for m in mf[:3]:
                    if m.get("phase") == "metric":
                        print(f"      - {(m.get('error') or m.get('sql_preview',''))[:100]}")
        if b["failed"]:
            print("  Failed:")
            for x in b["failed"]:
                print(f"    {x['industry']}@{x['profile']} result={x.get('result')} bucket={x.get('bucket')}")
    r = report.get("retries", {})
    print(f"\n--- Surgical metric-view retries ---")
    print(f"  Clean after prune:  {len(r.get('clean_after_prune', []))}")
    print(f"  Still warning:      {len(r.get('still_warning', []))}")
    print(f"  Retry failed:       {len(r.get('failed', []))}")
    for x in r.get("clean_after_prune", []):
        print(f"    FIXED {x['industry']}/{x['size']}@{x['profile']} removed={x.get('removed')}")
    print(f"\nCatalogs dropped in cleanup: {report.get('cleanup_dropped', 0)}")
    print(f"Full state: {STATE_FILE}")
    print("=" * 72)


def main() -> None:
    global SOURCE_REPO, SOURCE_REF
    ap = argparse.ArgumentParser(description="Install marathon v2")
    ap.add_argument("--preflight", action="store_true", help="Only test catalog creation")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true", help="Full pipeline")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--poll", type=int, default=120)
    ap.add_argument("--no-cleanup", action="store_true")
    ap.add_argument("--skip-retry", action="store_true")
    ap.add_argument("--source-repo", default=SOURCE_REPO, help="GitHub owner/repo for model SQL")
    ap.add_argument("--source-ref", default=SOURCE_REF, help="Git branch/tag for model SQL")
    ap.add_argument("--fresh", action="store_true", help="Ignore prior state file")
    ap.add_argument("--resume", action="store_true",
                    help="Resume monitoring in-flight waves from state file (no relaunch)")
    ap.add_argument("--max-parallel", type=int, default=0,
                    help=f"Pool mode: ECM+MVM unified scheduler with N global concurrent installs (default {DEFAULT_MAX_PARALLEL} when --pool)")
    ap.add_argument("--pool", action="store_true",
                    help=f"Use unified ECM+MVM pool scheduler (implies --max-parallel {DEFAULT_MAX_PARALLEL})")
    ap.add_argument("--fix-warnings", action="store_true",
                    help="Retry all warning-bucket installs with pruned/fixed metric SQL (pool state required)")
    ap.add_argument("--poll-retries-only", action="store_true",
                    help="Only poll in-flight retries + heartbeat (no new submits)")
    ap.add_argument("--submit-next-retry", action="store_true",
                    help="Submit one aggressive retry if capacity allows, then exit")
    ap.add_argument("--submit-retry-key", metavar="PROFILE:INDUSTRY:SIZE",
                    help="Submit aggressive retry for one pool key, then exit")
    ap.add_argument("--ecm-profile", metavar="PROFILE",
                    help="Verification mode: install all ECM industries on this profile")
    ap.add_argument("--mvm-profile", metavar="PROFILE",
                    help="Verification mode: install all MVM industries on this profile")
    ap.add_argument("--drop-owned-catalogs", metavar="PROFILE",
                    help="DROP all catalogs owned by --owner-email on PROFILE (repeatable)")
    ap.add_argument("--owner-email", default="user@example.com",
                    help="Owner filter for --drop-owned-catalogs")
    ap.add_argument("--state-file", metavar="PATH",
                    help="Override state JSON path (default install_marathon_v2_state.json)")
    args = ap.parse_args()
    global STATE_FILE
    if args.state_file:
        STATE_FILE = os.path.expanduser(args.state_file)
    if args.drop_owned_catalogs:
        for prof in args.drop_owned_catalogs.split(","):
            prof = prof.strip()
            if prof:
                drop_owned_catalogs(prof, owner=args.owner_email)
        if not (args.run or args.fix_warnings or args.poll_retries_only):
            return
    SOURCE_REPO = args.source_repo
    SOURCE_REF = args.source_ref

    if args.preflight:
        targets = CANDIDATE_PROFILES
        if args.ecm_profile and args.mvm_profile:
            targets = [args.ecm_profile, args.mvm_profile]
        capable, blocked = {}, {}
        for p in targets:
            if p not in WAREHOUSE:
                blocked[p] = "no warehouse mapped"
                continue
            ok, detail = preflight_profile(p)
            if ok:
                capable[p] = detail
                pulse(f"[preflight] {p} OK ({detail})")
            else:
                blocked[p] = detail
                pulse(f"[preflight] {p} BLOCKED — {detail[:120]}")
        print("CAPABLE:", capable)
        print("BLOCKED:", blocked)
        return

    state = load_state() if not args.fresh else {"started_at": now()}
    if args.ecm_profile and args.mvm_profile:
        capable, blocked = {}, {}
        for p in (args.ecm_profile, args.mvm_profile):
            if p not in WAREHOUSE:
                blocked[p] = "no warehouse mapped"
                continue
            ok, detail = preflight_profile(p)
            if ok:
                capable[p] = detail
            else:
                blocked[p] = detail
        state["capable_profiles"] = capable
        state["blocked_profiles"] = blocked
    elif not state.get("capable_profiles"):
        capable, blocked = discover_capable_profiles()
        state["capable_profiles"] = capable
        state["blocked_profiles"] = blocked
    else:
        capable = state["capable_profiles"]
        blocked = state.get("blocked_profiles", {})

    state["source_repo"] = SOURCE_REPO
    state["source_ref"] = SOURCE_REF
    split_mode = None
    if args.ecm_profile and args.mvm_profile:
        split_mode = {"ecm": args.ecm_profile, "mvm": args.mvm_profile}
        state["split_mode"] = split_mode
        profiles = [args.ecm_profile, args.mvm_profile]
        capable = {p: capable[p] for p in profiles if p in capable}
        blocked = {p: blocked[p] for p in profiles if p in blocked}
        assign = assign_split(args.ecm_profile, args.mvm_profile)
    else:
        profiles = list(capable.keys())
        assign = assign_industries(profiles)
    state["assign"] = assign
    work_items = build_work_items(assign, split_mode)
    profile_parallel: dict[str, int] = {}
    if split_mode:
        per = min(20, max(1, args.max_parallel // 2)) if args.max_parallel > 0 else 20
        profile_parallel = {split_mode["ecm"]: per, split_mode["mvm"]: per}
        state["profile_parallel"] = profile_parallel

    if args.dry_run:
        print("Capable:", capable)
        print("Blocked:", blocked)
        for p, inds in assign.items():
            print(f"{p} ({len(inds)}): {', '.join(inds)}")
        return

    if args.report:
        print_final_report(build_final_report(state))
        return

    if args.fix_warnings or args.poll_retries_only or args.submit_next_retry or args.submit_retry_key:
        max_parallel = args.max_parallel if args.max_parallel > 0 else DEFAULT_MAX_PARALLEL
        if args.submit_retry_key:
            key = args.submit_retry_key.strip()
            row = state.get("waves", {}).get("pool", {}).get("items", {}).get(key)
            if not row:
                pulse(f"[submit-key] unknown key {key}")
                return
            state.setdefault("retries", {}).pop(key, None)
            save_state(state)
            submit_warning_retry(load_state(), key, row)
            pulse(f"[submit-key] done {key}")
            return
        if args.submit_next_retry:
            key = submit_next_retry(state, max_parallel)
            pulse(f"[submit-next] {'started ' + key if key else 'nothing to submit (at capacity or queue empty)'}")
            save_state(state)
            return
        if args.poll_retries_only and not args.fix_warnings:
            pulse(f"--poll-retries-only every {args.poll}s — target 80/80 clean")
            last_heartbeat = 0.0
            emit_marathon_heartbeat(state)
            last_heartbeat = time.time()
            while True:
                try:
                    state = load_state()
                    score = poll_retries_once(state)
                    save_state(state)
                    if score["clean"] >= 80 and score["warning"] == 0 and score["failed"] == 0:
                        pulse("[DONE] 80/80 clean — zero warnings/failures")
                        break
                    still = sum(
                        1 for k in _retry_targets(state)
                        if _retry_in_flight(state.get("retries", {}), k)
                    )
                    pulse(
                        f"[poll] clean={score['clean']}/80 warn={score['warning']} "
                        f"fail={score['failed']} run={still}"
                    )
                except Exception as e:
                    pulse(f"[poll] iteration error: {e}")
                if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL_S:
                    try:
                        emit_marathon_heartbeat(state)
                    except Exception as e:
                        pulse(f"[HEARTBEAT] emit failed: {e}")
                    last_heartbeat = time.time()
                time.sleep(args.poll)
            reconcile_pool(state)
            return
        pulse(f"--fix-warnings parallel={max_parallel} resume from pool state")
        monitor_retries_parallel(state, max_parallel, poll_s=args.poll)
        report = build_final_report(state)
        state["final_report"] = report
        save_state(state)
        print_final_report(report)
        return

    if args.run:
        max_parallel = args.max_parallel
        if args.pool and max_parallel <= 0:
            max_parallel = DEFAULT_MAX_PARALLEL
        if max_parallel and max_parallel > 0:
            if not args.resume and not args.no_cleanup:
                pulse("pre-run cleanup of prior marathon catalogs ...")
                for p, inds in assign.items():
                    cleanup_marathon_catalogs(p, inds)
            else:
                pulse(f"--pool mode max_parallel={max_parallel} (resume={args.resume})")
            monitor_pool(
                state, assign, max_parallel, poll_s=args.poll,
                work_items=work_items, profile_parallel=profile_parallel or state.get("profile_parallel"),
            )
            if not args.skip_retry:
                monitor_retries_parallel(state, max_parallel, poll_s=90)
            if not args.no_cleanup:
                final_cleanup(state, assign)
            report = build_final_report(state)
            state["final_report"] = report
            save_state(state)
            print_final_report(report)
            return

        waves = state.setdefault("waves", {})
        if not args.resume:
            if not args.no_cleanup:
                pulse("pre-run cleanup of prior marathon catalogs ...")
                for p, inds in assign.items():
                    cleanup_marathon_catalogs(p, inds)
            launch_wave(state, assign, "ecm", "wave1")
        elif "ecm_wave1" not in waves:
            pulse("--resume: no ecm_wave1 in state; launching ECM wave")
            launch_wave(state, assign, "ecm", "wave1")
        else:
            pulse("--resume: continuing from saved state (ECM/MVM waves may be in-flight)")

        if not wave_terminal(state, "ecm_wave1"):
            monitor_wave(state, "ecm_wave1", poll_s=args.poll)

        if "mvm_wave2" not in waves or not waves["mvm_wave2"].get("profiles"):
            launch_wave(state, assign, "mvm", "wave2")
        if not wave_terminal(state, "mvm_wave2"):
            monitor_wave(state, "mvm_wave2", poll_s=args.poll)

        if not args.skip_retry:
            retry_warnings(state, "ecm_wave1")
            retry_warnings(state, "mvm_wave2")
            monitor_retries(state, poll_s=90)

        if not args.no_cleanup:
            final_cleanup(state, assign)

        report = build_final_report(state)
        state["final_report"] = report
        save_state(state)
        print_final_report(report)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
