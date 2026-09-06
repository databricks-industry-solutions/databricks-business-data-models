#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

AGENT_VER = "424"  # matches __AGENT_VERSION__ 4.2.4 (semver minus dots, §3a); never run stale
AGENT_PATH = f"/Users/user@example.com/dbx_vibe_modelling_agent_v{AGENT_VER}"
STAGE_DIR = "/tmp/vov_stage"
OUT_DIR = "/tmp/vov_out"
PULSE_FILE = os.path.expanduser("~/claude/vibe-agent/vov2_pulses.txt")
STATE_FILE = os.path.expanduser("~/claude/vibe-agent/vov2_state.json")
KILL_FILE = os.path.expanduser("~/claude/vibe-agent/vov2_KILL")
# DRAIN_FILE (v390 baseline-preserve): when present, workers RE-ATTACH + monitor + audit any
# already-in-flight run to terminal, but DO NOT START new (queued/prep_failed) industries. This
# honors the "let the 5 in-flight v385 VOVs finish as the honest baseline, pause the queued"
# directive without the KILL_FILE bluntness (KILL abandons in-flight monitoring). Remove the file
# and restart to resume normal fan-out. alias=marathon-drain-baseline-preserve
DRAIN_FILE = os.path.expanduser("~/claude/vibe-agent/vov2_drain.flag")

POLL_S = 120
PULSE_S = 900
# Per-task caps reflect the user directive "timeout for any agent run is 15h" applied to the
# QUALITY-CRITICAL agent run (vov), tempered by the proven teardown-hang reality of install/shrink:
#   - vov SELF-COMPLETES (writes ECM model.json + finalizes) and is the run whose truncation costs
#     quality, so it gets the full 15h ceiling => NEVER truncated mid-finalization. (Was 4h, which
#     sat dangerously close to observed 3.3h vov runtimes on tier-1-size models.)
#   - install + shrink PROVABLY hang in a GIL-held teardown AFTER writing their artifacts (installs
#     observed TERMINATED/TIMEDOUT; canary shrinks hit their cap then exported a written mvm). In the
#     3-task job, run_if=ALL_DONE means the NEXT task waits for the current to be 'done', so a 15h cap
#     on install/shrink would block the pipeline for up to 15h of pure teardown hang — slower, not
#     faster. They therefore get generous-but-bounded caps well above measured functional times
#     (install functional <=40m on the slow my-uae workspace; shrink functional 66-106m), so real work
#     never truncates while teardown waste stays bounded. Artifacts (model.json, next_vibes) are on the
#     volume BEFORE teardown, so a cap-killed-but-functionally-complete task still exports + advances.
JOB_TIMEOUT_S = 82800        # 23h job ceiling (>= 1h install + 15h vov + 2.5h shrink, with margin)
# v385 marathon EVIDENCE (2026-06-19): all 13 installs finished functional work (physical schema +
# tags + MVs + model.json deploy) in 14-17m, then hung in a GIL-held serverless teardown for ~90m
# with NO new log lines and NO self-cancel marker (the in-driver self-cancel/faulthandler _exit kills
# the DRIVER but does NOT flip the serverless RUN to TERMINATED -- only a control-plane cancel does).
# The control-plane JOB TIMEOUT is that reliable external terminator. Install/shrink have short,
# predictable functional times, so a tight cap bounds the teardown-hang waste WITHOUT truncating real
# work. vov is quality-critical (variable multi-hour real work) so it keeps the full 15h ceiling and
# relies on artifacts-before-teardown + the in-driver self-cancel (live-watched this run).
INSTALL_TIMEOUT_S = 3600     # 60m: functional install <=40m even on slow my-uae; bounds the PROVEN
                             #      teardown hang to ~20-45m (was 120m -> ~100m wasted) and unblocks
                             #      vov (run_if=ALL_DONE) ~60m sooner. Never truncates <=40m functional.
VOV_TIMEOUT_S = 54000        # 15h: user directive — the quality-critical agent run is never truncated
SHRINK_TIMEOUT_S = 9000      # 2.5h: functional shrink 66-106m; same serverless teardown-hang mechanism
                             #       as install -> bound via control-plane timeout (was 5h)

# v4.2.1 marathon (2026-07-01 user directive): regenerate v2 for the 7 REMAINING weak industries
# ONLY. The strong 6 (travel_hospitality, consumer_goods, health_insurance, construction,
# media_broadcasting, semiconductors) are already published and must NOT be touched, so they are
# removed from ASSIGN entirely (the marathon only processes ASSIGN industries). The 7 keep their
# original droppable per-industry catalogs (none is a FIXED_CATALOG profile), so a clean fresh
# DROP+install v1 -> VOV -> shrink is possible with VOV_FORCE_REINSTALL=1 (set at launch). Special
# cases (restaurants dropped catalog / water_utilities non-standard layout / manufacturing no
# baseline) all self-heal via the standard prepare_catalog fresh-install path.
# 2026-07-03 clean-v1->v2 relaunch: healthcare + restaurants already PUBLISHED (removed). automotive
# DEFERRED to a separate v4.2.4 track (needs junk-domain + name-prefix fixes, not just a relaunch).
# manufacturing (was accumulated v6) + ngo (was accumulating to v5) + water_utilities (rebuild) are
# relaunched CLEAN v1->v2, one-per-profile for true parallelism (user "no queue, run in parallel").
# retail is a clean v1->v2 already RUNNING on <profile> -> re-attach and let it finish.
# 2026-07-03 v4.2.4 relaunch: healthcare, restaurants, ngo, manufacturing already PUBLISHED
# (clean v1->v2, gate-passed) and are NOT in the active list. The v4.2.4 track relaunches the
# three that missed the gate on v4.2.3, one-per-droppable-profile for true parallelism:
#   automotive (<profile>)     — RC-A junk/empty-domain guard + RC-C move-FQN verifier
#   retail     (<profile>)     — VOV holistic/refactor VREQ grounding (live-iterative)
#   water_utilities (<profile>)— verifier-pipeline-meta-informational (VREQ-029) + create-entity grounding
# All three sit on CREATE/DROP-CATALOG-capable profiles so prepare_catalog can do a clean
# DROP+install v1 -> VOV -> shrink. None is a FIXED_CATALOG (<profile>) or flaky-Azure profile.
ASSIGN = {
    "<profile>": ["automotive"],
    "<profile>": ["retail"],
    "<profile>": ["water_utilities"],
}

WAREHOUSE = {
    "<profile>": "d6d89fb9fd47b835",
    "<profile>": "862f1d757f0424f7",
    "<profile>": "2023d0a3a188bd24",
    "<profile>": "2ad1b26db73a7c6f",
    "my-uae": "6b2c33b3b2aae3ac",
    "<profile>": "7c313dcbcd3119c1",
}

# FIXED_CATALOG (user directive 2026-06-19): on environments where the principal lacks
# CREATE CATALOG on the metastore, the marathon CANNOT mint a per-industry `vibe_<ind>_v1`
# catalog. Instead every industry assigned to such a profile shares one pre-existing catalog
# the user granted. cat_name() resolves an industry to this fixed catalog via the profile it is
# assigned to, and prepare_catalog() skips the DROP/CREATE CATALOG dance for these profiles
# (the agent's _ensure_catalog_exists SHOW-CATALOGS check then skips creation too).
FIXED_CATALOG = {
    "<profile>": "serverless_stable_8nstmo_catalog",
}
# reverse index ind -> profile, built from the static ASSIGN map, so cat_name(ind) (which only
# receives the industry) can tell whether that industry lives on a fixed-catalog profile.
_IND_PROFILE = {ind: prof for prof, inds in ASSIGN.items() for ind in inds}

ECM_SCOPE = "Expanded Coverage Model - ECM"
MVM_SCOPE = "Minimum Viable Model - MVM"

_AUTH_HINTS = ("oauth", "token has expired", "refresh token expired", "401",
               "unauthorized", "invalid_grant", "could not refresh",
               "token was revoked", "access_token")

_state_lock = threading.Lock()
_pulse_lock = threading.Lock()


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pulse(msg):
    line = f"[{now()}] {msg}"
    with _pulse_lock:
        print(line, flush=True)
        Path(os.path.dirname(PULSE_FILE)).mkdir(parents=True, exist_ok=True)
        with open(PULSE_FILE, "a") as f:
            f.write(line + "\n")


def _run(cmd, timeout):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), 9)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        try:
            p.communicate(timeout=10)
        except Exception:
            pass
        return 124, "", f"timeout after {timeout}s"


def _refresh(profile):
    _run(["databricks", "auth", "token", "--profile", profile], 60)


def db(args, profile, timeout=300):
    cmd = ["databricks"] + args + ["--profile", profile]
    rc, out, err = _run(cmd, timeout)
    if rc == 0:
        return out
    el = (err or "").lower()
    if any(h in el for h in _AUTH_HINTS):
        _refresh(profile)
        rc, out, err = _run(cmd, timeout)
        if rc == 0:
            return out
    raise RuntimeError(f"databricks {' '.join(args)} -> {rc}: {(err or '')[:600]}")


def dbj(args, profile, timeout=300):
    out = db(args + ["-o", "json"], profile, timeout=timeout)
    return json.loads(out) if out.strip() else {}


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"started_at": now(), "industries": {}}
    try:
        return json.loads(Path(STATE_FILE).read_text())
    except Exception:
        return {"started_at": now(), "industries": {}}


def save_state(state):
    with _state_lock:
        state["updated_at"] = now()
        Path(os.path.dirname(STATE_FILE)).mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        Path(tmp).write_text(json.dumps(state, indent=2, default=str))
        os.replace(tmp, STATE_FILE)


def set_ind(state, ind, **kv):
    with _state_lock:
        state.setdefault("industries", {}).setdefault(ind, {}).update(kv)
        state["industries"][ind]["ts"] = now()
    save_state(state)


def cat_name(ind):
    # fixed-catalog profiles (no CREATE CATALOG on the metastore) share one pre-existing catalog;
    # everyone else gets an isolated per-industry catalog the marathon creates/drops at will.
    prof = _IND_PROFILE.get(ind)
    if prof in FIXED_CATALOG:
        return FIXED_CATALOG[prof]
    return f"vibe_{ind}_v1"


def _parse_mtime_ms(v):
    # v4.0.7 marathon-harvest-latest-version: normalize a `databricks fs ls -o json` mtime to epoch ms.
    # The CLI reports `last_modified` as ISO-8601 (e.g. '2026-06-21T10:48:03Z') OR epoch ms int on older
    # builds; return epoch ms (int) or None so the freshness gate can compare against run start_ms.
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if s.isdigit():
        return int(s)
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def latest_version(profile, ind):
    # v4.0.7 alias=marathon-harvest-latest-version -- ROOT CAUSE (lying-scoreboard #1 lever): both
    # export_industry and the audit hardcoded the 'v2' artifact path, but install-once-reuse vov's a
    # reused catalog repeatedly so the LATEST model lands at v3/v4/... (live: construction v3=agent
    # 4.0.6 / 20 domains while the harvested v2=agent 3.9.2). The marathon then HARVESTED + AUDITED the
    # STALE v2, under-reporting every multi-generation industry and making the scoreboard lie. Discover
    # the highest v<N> business dir; default 'v2' on empty/auth-fail (honest, never crashes the run).
    #
    # v4.1.1 alias=marathon-harvest-complete-pair -- ROOT CAUSE (live manufacturing partial, 2026-06-23):
    # install-once-reuse vov'd the same catalog repeatedly to v8, but the v8 shrink no-op'd MVM creation
    # (only the older v2/v3 ever wrote mvm/model.json). max(vers)=v8 has ecm/model.json but NO
    # mvm/model.json, so export_industry copied a complete ecm + an EMPTY mvm and harvested 'partial'.
    # This marathon always runs MVM scope (data_model_scopes=MVM_SCOPE), so a COMPLETE version must
    # carry BOTH ecm/model.json AND mvm/model.json. Pick the highest version that has the complete pair;
    # only if none is complete do we fall back to max(vers) (then ecm-only, then 'v2') so the run still
    # harvests something and never crashes -- but a half-baked latest version no longer shadows the last
    # good complete pair. Fail SAFE: any ls/auth error on a candidate just skips it.
    import re as _re
    cat = cat_name(ind)
    base = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/business/{ind}"

    def _has_model_json(ver_dir, scope):
        try:
            o = db(["fs", "ls", f"{base}/{ver_dir}/{scope}"], profile, timeout=90)
            return any(ln.strip().rstrip("/").split("/")[-1].split()[0] == "model.json"
                       for ln in (o or "").splitlines() if ln.strip())
        except Exception:
            return False

    try:
        out = db(["fs", "ls", base], profile, timeout=90)
        vers = []
        for line in (out or "").splitlines():
            nm = line.strip().rstrip("/").split("/")[-1].split()[0] if line.strip() else ""
            m = _re.fullmatch(r"v(\d+)", nm)
            if m:
                vers.append(int(m.group(1)))
        if vers:
            vers_desc = sorted(set(vers), reverse=True)
            for n in vers_desc:
                vd = f"v{n}"
                if _has_model_json(vd, "ecm") and _has_model_json(vd, "mvm"):
                    return vd
            # no complete ecm+mvm pair anywhere: prefer the highest version with at least an ecm,
            # else the bare highest version. Pulse so a partial harvest is never silent.
            for n in vers_desc:
                if _has_model_json(f"v{n}", "ecm"):
                    pulse(f"[{ind}] no complete ecm+mvm version found; harvesting ecm-only v{n} "
                          f"(latest complete pair absent). alias=marathon-harvest-complete-pair")
                    return f"v{n}"
            return f"v{max(vers)}"
    except Exception:
        pass
    return "v2"


def vol_base(ind):
    # stage inputs INSIDE the agent's own _metamodel/vol_root volume (a folder),
    # never a separate _staging database (user directive 2026-06-18). The agent
    # creates _metamodel/vol_root with CREATE ... IF NOT EXISTS, so pre-creating
    # them here and reusing is safe; the staged file survives the agent run.
    return f"/Volumes/{cat_name(ind)}/_metamodel/vol_root/_input"


def _try(args, profile, ok_substrings=(), timeout=180):
    try:
        db(args, profile, timeout=timeout)
        return True
    except Exception as e:
        s = str(e).lower()
        if any(o in s for o in ok_substrings):
            return True
        raise


def sql_exec(profile, stmt, timeout=180):
    wh = WAREHOUSE[profile]
    payload = {"warehouse_id": wh, "statement": stmt, "wait_timeout": "50s"}
    pf = f"/tmp/vov_sql_{profile}_{abs(hash(stmt)) % 100000}.json"
    Path(pf).write_text(json.dumps(payload))
    res = dbj(["api", "post", "/api/2.0/sql/statements", "--json", f"@{pf}"], profile, timeout=120)
    sid = res.get("statement_id")
    status = (res.get("status", {}) or {}).get("state")
    deadline = time.time() + timeout
    while status in ("PENDING", "RUNNING") and time.time() < deadline:
        time.sleep(4)
        res = dbj(["api", "get", f"/api/2.0/sql/statements/{sid}"], profile, timeout=120)
        status = (res.get("status", {}) or {}).get("state")
    if status != "SUCCEEDED":
        err = (res.get("status", {}) or {}).get("error", {})
        raise RuntimeError(f"SQL '{stmt[:60]}' -> {status}: {str(err)[:300]}")
    return res


def _rows(res):
    return (res.get("result", {}) or {}).get("data_array", []) or []


def v1_installed(profile, ind):
    # install-once-reuse (user directive 2026-06-19): the install phase deterministically
    # materializes the staged v1 model.json and is NOT under test — VOV (v1->v2) is. The vov task
    # runs with context_file="" and reads the prior version straight from `<cat>._metamodel.business`,
    # so a v1 row there is necessary AND sufficient for VOV to attach. When present we reuse it and
    # skip both the DROP CATALOG and the install task instead of rebuilding v1 every relaunch.
    # VOV_FORCE_REINSTALL=1 forces a clean rebuild (use when the install path / v1 model changes).
    if os.environ.get("VOV_FORCE_REINSTALL") == "1":
        return False
    cat = cat_name(ind)
    bn = ind.replace("'", "''")
    try:
        # require BOTH a v1 business row AND v1 domain rows: the agent writes the logical model
        # (business -> domain -> product -> attribute) early in install, so a complete logical v1
        # is what vov reads. A business row alone could be a partial/aborted install; demanding
        # domains too guards reuse against feeding vov a truncated v1.
        # ROOT CAUSE (live consumer_goods/semiconductors/retail INTERNAL_ERROR, 2026-06-23):
        # a bare existence check reused a v1 whose 'new base model' run never finished (the agent
        # records completed_percent<100 for a truncated install). VOV then fail-closes with
        # "Version '1' ... INCOMPLETE (progress: 99.0%)". The agent's OWN completeness contract is
        # completed_percent==100.0 (see _version_is_incomplete / _get_latest_completed_version), so
        # mirror it here: only reuse a v1 the agent would accept as a base; otherwise force a fresh
        # install. MAX(COALESCE(...)) returns NULL when no v1 row exists (-> fresh install) and a
        # missing completed_percent column raises (-> except -> fresh install): both fail SAFE.
        biz = sql_exec(
            profile,
            f"SELECT MAX(COALESCE(completed_percent, 0.0)) FROM `{cat}`.`_metamodel`.`business` "
            f"WHERE LOWER(business)=LOWER('{bn}') AND CAST(version AS INT)=1",
            timeout=120,
        )
        brows = _rows(biz)
        if not brows or brows[0][0] is None:
            return False
        _pct = float(brows[0][0] or 0.0)
        if _pct < 100.0:
            pulse(f"[{ind}] v1 present on {profile} but INCOMPLETE (completed_percent={_pct}) — forcing fresh install, not reuse. alias=marathon-reuse-incomplete-v1")
            return False
        # v4.2.4 marathon-reset-accumulated-v2plus (2026-07-03 user directive "launch v2 on v1->v2 vov"):
        # install-once-reuse on a catalog that ALREADY carries v2+ completed generations makes the VOV
        # read the LATEST completed version (e.g. v5) and write v6 -- an ACCUMULATION, never a clean
        # v1->v2 (empirically: manufacturing v2=4.1.0 .. v6=4.2.2; ngo v2=4.1.4 .. v4=4.2.2). A published
        # "v2" MUST be a single VOV step from v1. If any completed version > 1 exists, the catalog has
        # drifted through prior generations; force a fresh install (drop+reinstall v1) so the VOV attaches
        # to v1 and writes a CLEAN v2. Generic/industry-agnostic: reads the live business version table.
        try:
            accr = sql_exec(
                profile,
                f"SELECT MAX(CAST(version AS INT)) FROM `{cat}`.`_metamodel`.`business` "
                f"WHERE LOWER(business)=LOWER('{bn}') AND COALESCE(completed_percent, 0.0) >= 100.0",
                timeout=120,
            )
            arows = _rows(accr)
            maxv = int(arows[0][0]) if (arows and arows[0][0] is not None) else 1
        except Exception:
            maxv = 1
        if maxv > 1:
            pulse(f"[{ind}] catalog carries accumulated completed v{maxv} (>v1) — forcing FRESH install so VOV yields a CLEAN v1->v2, not an accumulation. alias=marathon-reset-accumulated-v2plus")
            return False
        dom = sql_exec(
            profile,
            f"SELECT COUNT(*) FROM `{cat}`.`_metamodel`.`domain` WHERE CAST(version AS INT)=1",
            timeout=120,
        )
        rows = _rows(dom)
        return bool(rows) and int(rows[0][0]) > 0
    except Exception:
        return False


def _external_location_bases(profile):
    # When the metastore has NO default storage, a plain CREATE CATALOG fails and we must
    # supply an explicit MANAGED LOCATION. The metastore's own WRITABLE external locations are
    # the most reliable candidates (the principal is, by definition, permitted to use them),
    # unlike sibling-catalog storage_roots which are frequently owned by other principals.
    # Generic/industry-agnostic: reads live UC config, never special-cases any workspace.
    try:
        d = dbj(["external-locations", "list"], profile, timeout=120)
    except Exception:
        return []
    locs = d if isinstance(d, list) else d.get("external_locations", [])
    bases = []
    for l in locs:
        url = (l.get("url") or "").rstrip("/")
        if url and not l.get("read_only") and url.startswith(("abfss://", "s3://", "gs://")):
            bases.append(url)
    return bases


def _managed_bases(profile):
    res = sql_exec(profile, "SHOW CATALOGS")
    cats = [str(r[0]) for r in _rows(res)
            if r and not str(r[0]).lower().startswith(("_", "system", "samples", "main", "hive_metastore", "__"))]
    cats.sort(key=lambda c: (0 if any(c.endswith(s) for s in ("_ecm_v1", "_mvm_v1", "_v1", "_v2")) else 1))
    bases, seen = [], set()
    for cn in cats:
        try:
            d = sql_exec(profile, f"DESCRIBE CATALOG EXTENDED `{cn}`")
            for row in _rows(d):
                if len(row) >= 2 and str(row[0]).lower() in ("storage_root", "storage root") \
                        and str(row[1]).startswith(("abfss://", "s3://", "gs://")):
                    b = str(row[1]).rsplit("/__unitystorage/", 1)[0]
                    if b not in seen:
                        seen.add(b)
                        bases.append(b)
        except Exception:
            continue
    return bases


def prepare_catalog(profile, ind):
    cat = cat_name(ind)
    if v1_installed(profile, ind):
        pulse(f"[{ind}] v1 already installed on {profile} — REUSING catalog, skip drop+install. alias=marathon-install-once-reuse")
        sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{cat}`.`_metamodel`")
        sql_exec(profile, f"CREATE VOLUME IF NOT EXISTS `{cat}`.`_metamodel`.`vol_root`")
        return True
    if profile in FIXED_CATALOG:
        # fixed-catalog profile: the metastore denies CREATE CATALOG, and the shared catalog
        # already exists, so we MUST NOT DROP/CREATE it. Just ensure the agent's meta schema +
        # volume exist (CREATE SCHEMA/VOLUME IF NOT EXISTS are permitted on the granted catalog).
        # v1 is not yet installed here -> return False so the install task runs; the agent's
        # _ensure_catalog_exists then skips catalog creation because SHOW CATALOGS lists it.
        pulse(f"[{ind}] fixed catalog `{cat}` on {profile} — no DROP/CREATE (metastore denies CREATE CATALOG); ensure schema+volume. alias=marathon-fixed-catalog-no-create")
        sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{cat}`.`_metamodel`")
        sql_exec(profile, f"CREATE VOLUME IF NOT EXISTS `{cat}`.`_metamodel`.`vol_root`")
        return False
    sql_exec(profile, f"DROP CATALOG IF EXISTS `{cat}` CASCADE", timeout=600)
    try:
        sql_exec(profile, f"CREATE CATALOG `{cat}`")
    except Exception as e:
        el = str(e).lower()
        if not ("storage root" in el or "default storage" in el or "managed location" in el):
            raise
        created, last = False, str(e)[:200]
        cand_bases, seen_b = [], set()
        for b in _external_location_bases(profile) + _managed_bases(profile):
            if b not in seen_b:
                seen_b.add(b)
                cand_bases.append(b)
        for base in cand_bases:
            for loc in (f"{base}/{cat}", base):
                try:
                    sql_exec(profile, f"CREATE CATALOG `{cat}` MANAGED LOCATION '{loc}'")
                    created = True
                    break
                except Exception as e2:
                    last = str(e2)[:200]
                    le = last.lower()
                    if "overlap" in le:
                        continue
                    if "permission_denied" in le or "not accessible" in le or "forbidden" in le:
                        break
                    break
            if created:
                break
        if not created:
            raise RuntimeError(f"[{ind}] could not create catalog on {profile}: {last}")
    # reuse the agent's own meta schema/volume; do NOT create a separate _staging
    # database (user directive 2026-06-18). The agent re-uses these via IF NOT EXISTS.
    sql_exec(profile, f"CREATE SCHEMA IF NOT EXISTS `{cat}`.`_metamodel`")
    sql_exec(profile, f"CREATE VOLUME IF NOT EXISTS `{cat}`.`_metamodel`.`vol_root`")
    return False


def stage_files(profile, ind, reused=False):
    base = vol_base(ind)
    _try(["fs", "mkdir", f"dbfs:{base}/model"], profile, ("already exists",))
    # model.json is only the install task's context_file; when reusing an installed v1 the install
    # task is dropped, so staging it is pointless. next_vibes.txt is the VOV vibe input — always stage.
    if not reused:
        db(["fs", "cp", f"{STAGE_DIR}/{ind}/model/model.json",
            f"dbfs:{base}/model/model.json", "--overwrite"], profile, timeout=600)
    db(["fs", "cp", f"{STAGE_DIR}/{ind}/next_vibes.txt",
        f"dbfs:{base}/next_vibes.txt", "--overwrite"], profile, timeout=300)


def industry_desc(ind):
    p = f"{STAGE_DIR}/{ind}/description.txt"
    d = Path(p).read_text().strip() if os.path.exists(p) else ""
    return d or f"{ind.replace('_', ' ')} industry enterprise data model."


def build_job_spec(ind, installed=False):
    cat = cat_name(ind)
    base = vol_base(ind)
    desc = industry_desc(ind)
    # v4.0.8 alias=self-cancel-reuse-vibe-session-id: vibe_session_id carries the Databricks-native
    # {{job.run_id}} (substituted at runtime). ONE identifier now drives both the progress-tracking
    # session AND the control-plane self-cancel (which arms even when the serverless context exposes
    # no run_id tags, e.g. <profile> tag_keys=[]). Replaces the retired separate self_run_id base-param.
    common = {"business_name": ind, "business_description": desc,
              "deployment_catalog": cat, "generate_samples": "0",
              "vibe_session_id": "{{job.run_id}}",
              "databricks_task_run_id": "{{task.run_id}}"}
    install = dict(common, operation="install model", model_version="1",
                   data_model_scopes=ECM_SCOPE,
                   context_file=f"{base}/model/model.json", model_vibes="")
    vov = dict(common, operation="vibe modeling of version", model_version="1",
               data_model_scopes=ECM_SCOPE,
               model_vibes=f"{base}/next_vibes.txt", context_file="")
    shrink = dict(common, operation="shrink ecm", model_version="2",
                  data_model_scopes=MVM_SCOPE, model_vibes="", context_file="")
    def task(key, params, tmo, dep=None):
        # v4.0.8 alias=runtime-budget-config-base-param: inject runtime_budget_seconds = this task's
        # REAL timeout so the agent's per-VREQ verifier RuntimeBudget honours the full allocation
        # (vov=15h) instead of the 14400s/4h default. Databricks does not expose the timeout as an
        # env var, so this base-param is the only correct source for marathon runs. DRY: tmo is the
        # single source of truth for both the platform timeout AND the agent budget.
        params = dict(params)
        params["runtime_budget_seconds"] = str(int(tmo))
        t = {"task_key": key,
             "notebook_task": {"notebook_path": AGENT_PATH, "source": "WORKSPACE",
                               "base_parameters": params},
             "timeout_seconds": tmo}
        if dep:
            # run_if=ALL_DONE: upstream task may be killed by the platform timeout while in a
            # GIL-held teardown hang AFTER its functional work + volume artifacts completed.
            # ALL_DONE lets the downstream operation proceed (it reads the installed catalog /
            # volume model.json, both populated before teardown) instead of being skipped.
            t["depends_on"] = [{"task_key": dep}]
            t["run_if"] = "ALL_DONE"
        return t
    # install-once-reuse: when v1 is already installed, drop the install task and point vov at the
    # existing catalog v1 directly (it reads _metamodel.business, not the staged context_file).
    if installed:
        tasks = [task("vov", vov, VOV_TIMEOUT_S),
                 task("shrink", shrink, SHRINK_TIMEOUT_S, dep="vov")]
    else:
        tasks = [task("install", install, INSTALL_TIMEOUT_S),
                 task("vov", vov, VOV_TIMEOUT_S, dep="install"),
                 task("shrink", shrink, SHRINK_TIMEOUT_S, dep="vov")]
    return {
        "name": f"dbx_vibe_vov2_{ind}_v{AGENT_VER}",
        "timeout_seconds": JOB_TIMEOUT_S,
        "max_concurrent_runs": 1,
        "tasks": tasks,
    }


def find_or_create_job(profile, ind, installed=False):
    name = f"dbx_vibe_vov2_{ind}_v{AGENT_VER}"
    jobs = dbj(["jobs", "list", "--limit", "100"], profile)
    items = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    for j in items:
        if (j.get("settings", {}) or {}).get("name") == name:
            spec = build_job_spec(ind, installed=installed)
            patch = {"job_id": j["job_id"], "new_settings": spec}
            pp = f"/tmp/vov_jobpatch_{ind}.json"
            Path(pp).write_text(json.dumps(patch))
            db(["jobs", "reset", "--json", f"@{pp}"], profile)
            return j["job_id"]
    spec = build_job_spec(ind, installed=installed)
    sp = f"/tmp/vov_jobspec_{ind}.json"
    Path(sp).write_text(json.dumps(spec))
    res = dbj(["jobs", "create", "--json", f"@{sp}"], profile)
    return res["job_id"]


def run_now(profile, job_id):
    res = dbj(["jobs", "run-now", str(job_id), "--no-wait"], profile)
    return res["run_id"]


def get_run(profile, run_id):
    info = dbj(["jobs", "get-run", str(run_id)], profile)
    st = info.get("state", {})
    return {
        "lc": st.get("life_cycle_state"),
        "result": st.get("result_state"),
        "msg": (st.get("state_message", "") or "")[:200],
        "url": info.get("run_page_url"),
        # v4.0.7 marathon-harvest-latest-version: start_ms gates the teardown-hang freshness check so a
        # stale prior-generation model.json/log (older than this run) cannot trigger a false hang.
        "start_ms": info.get("start_time") or info.get("start_time_ms"),
        "tasks": [{"k": t.get("task_key"),
                   "lc": (t.get("state", {}) or {}).get("life_cycle_state"),
                   "r": (t.get("state", {}) or {}).get("result_state")}
                  for t in info.get("tasks", [])],
    }


HANG_CHECK_S = 300    # re-evaluate the teardown-hang signal at most every 5 min
HANG_STALL_S = 1200   # 20 min of ecm-log flatline AFTER the teardown marker => in-driver kill failed

# Finalization-class markers (gate d). ANY one, together with model.json-on-volume (gate b) +
# HANG_STALL_S info-log flatline (gate c), proves the vov body finished and only teardown remains,
# so a control-plane cancel is loss-free. All are emitted ONLY at/after finalization -> no mid-run
# false positive. FINAL-FLUSH + JobTags were added 2026-06-19 after the restaurants hang
# (run <run_id>) ended at exactly these two lines and NEVER reached the pkw watchdog ARM-LOG.
_TEARDOWN_DONE_MARKERS = (
    "[VolumeLogFlush][FINAL-FLUSH]",   # volume log flusher's final flush -- only at pipeline shutdown
    "[JobTags] Updated job tags",      # terminal ECM tagging step -- last functional action
)


def _ls_json(profile, dir_path, timeout=120):
    out = dbj(["fs", "ls", dir_path], profile, timeout=timeout)
    return out if isinstance(out, list) else out.get("files", []) or []


def _vov_teardown_hang_cancel(profile, ind, run_id, info, hang_state):
    """v3.9.3 alias=marathon-vov-teardown-hang-cancel.

    PROVEN (probe run <run_id>, <profile> serverless, 2026-06-19): the agent's in-driver
    self-cancel CANNOT resolve its own run_id in serverless -- env DATABRICKS_RUN_ID/TASK_RUN_ID
    are null, spark.conf.get('spark.databricks.job.runId') raises AnalysisException, and
    dbutils...getContext().toJson() raises Py4JSecurityException. So a vov task that FINISHED its
    functional work (wrote v2/ecm/model.json + JobTags) but then hung in a GIL-held teardown stays
    RUNNING until the 15h vov cap -- wasting hours of compute (live: restaurants run <run_id>
    hung from 21:16, model.json already on the volume). The marathon DOES hold the run_id, so it is
    the ONLY actor that can flip the run to TERMINATED.

    Fires ONLY when ALL hold (low false-positive quad gate): (a) the vov task is RUNNING, (b)
    v2/ecm/model.json is on the volume (functional work done -- it is written only at finalization,
    never mid-vov), (c) the ecm info.log mtime has not advanced for HANG_STALL_S (in-driver kill
    failed), and (d) the log tail carries ANY genuine finalization marker in _TEARDOWN_DONE_MARKERS.

    On gate (d): the original build required ONLY the 'process-kill-watchdog ARM-LOG FIRED ...
    source=pipeline-finally' pair, but the LIVE restaurants hang (run <run_id>, 2026-06-19)
    does NOT emit it -- its 8665-line info.log ends cleanly at the final '[JobTags] Updated job tags'
    + '[VolumeLogFlush][FINAL-FLUSH]' and then the driver freezes BEFORE the pkw watchdog arms (or
    its ARM-LOG is never flushed). A gate that only accepts the pkw pair is therefore a false-negative
    no-op against the exact hang it was built to catch. The fix accepts ANY finalization-class marker:
    the pkw pair, OR the volume-log FINAL-FLUSH (emitted only at pipeline shutdown), OR the terminal
    JobTags update (the last functional ECM step). All three are emitted only at/after finalization,
    so combined with gates (b)+(c) the cancel stays loss-free and cannot false-fire mid-run. Artifacts
    are on the volume before teardown and the downstream shrink is run_if=ALL_DONE, so the cancel is
    loss-free and unblocks shrink immediately. Scoped to the vov task only -- install/shrink already
    have tight control-plane caps."""
    vt = next((t for t in info.get("tasks", [])
               if t.get("k") == "vov" and t.get("lc") == "RUNNING"), None)
    if not vt:
        return False
    now_t = time.time()
    hs = hang_state.setdefault(ind, {"last_check": 0.0, "mtime": None, "since": None})
    if now_t - hs["last_check"] < HANG_CHECK_S:
        return False
    hs["last_check"] = now_t
    cat = cat_name(ind)
    # v4.0.7 alias=marathon-harvest-latest-version -- watch the CURRENT run's log, not a hardcoded
    # stale v2. ROOT CAUSE (live retail false-positive): on an install-once-reuse catalog the new vov
    # writes v4 while the old v2 log already carries a FINAL-FLUSH + a 24m-flatline mtime, so the
    # detector false-flagged a teardown hang on a run only 33m in (still in early vov, no v4 log yet)
    # AND could never see a REAL v4 teardown hang (wrong log). Resolve the latest version per-run.
    ver = latest_version(profile, ind)
    biz_dir = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/business/{ind}/{ver}/ecm"
    log_dir = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/logs/{ind}/{ver}/ecm"
    log_name = f"{ind}_info_{ver}_ecm.log"
    try:
        _entries = _ls_json(profile, biz_dir)
        names = {e.get("name") for e in _entries}
        if "model.json" not in names:
            hs["mtime"] = None
            hs["since"] = None
            return False
        # v4.0.7 marathon-harvest-latest-version FRESHNESS GATE -- ROOT CAUSE of the live retail
        # false-positive: on a reused catalog the latest EXISTING version (e.g. v3) is a COMPLETED
        # prior generation whose model.json + log already carry FINAL-FLUSH and a long-flatlined
        # mtime, so the detector flagged a teardown hang on a run still in early vov. Only treat the
        # model.json as THIS run's output when it was written AFTER the run started. If it predates
        # the run (stale gen) OR the run start is unknown but the model.json is clearly old, bail.
        _start_ms = info.get("start_ms")
        if _start_ms:
            _mj = next((e for e in _entries if e.get("name") == "model.json"), {})
            _mjmt = _parse_mtime_ms(_mj.get("last_modified") or _mj.get("modification_time")
                                    or _mj.get("mtime"))
            if _mjmt is not None and _mjmt < (_start_ms - 60000):
                # model.json belongs to a prior generation -> not this run's teardown.
                hs["mtime"] = None
                hs["since"] = None
                return False
        mt = None
        for e in _ls_json(profile, log_dir):
            if e.get("name") == log_name:
                # `databricks fs ls -o json` reports the mtime as `last_modified` (ISO-8601 string,
                # verified live 2026-06-19); older CLIs used `modification_time`/`mtime` (epoch ms).
                # Either way string/int EQUALITY is all the flatline check needs: an unchanged value
                # across HANG_STALL_S means the log file was not written, i.e. the driver is hung.
                mt = e.get("last_modified") or e.get("modification_time") or e.get("mtime")
                break
        if mt is None:
            return False
    except Exception as e:
        pulse(f"[{ind}] hang-check err: {str(e)[:120]}")
        return False
    if hs["mtime"] == mt:
        if hs["since"] is None:
            hs["since"] = now_t
        elif now_t - hs["since"] >= HANG_STALL_S:
            try:
                tmpf = f"/tmp/vov_hangchk_{ind}.log"
                db(["fs", "cp", f"{log_dir}/{log_name}", tmpf, "--overwrite"], profile, timeout=300)
                tail = open(tmpf, errors="ignore").read()[-20000:]
            except Exception:
                tail = ""
            _pkw = ("process-kill-watchdog ARM-LOG FIRED" in tail
                    and "source=pipeline-finally" in tail)
            _final = next((m for m in _TEARDOWN_DONE_MARKERS if m in tail), None)
            if _pkw or _final:
                mins = int((now_t - hs["since"]) / 60)
                _why = "pkw pipeline-finally" if _pkw else f"finalization marker '{_final}'"
                # v3.9.3 alias=marathon-vov-teardown-observe-only -- OBSERVABILITY ONLY, never cancel.
                # ROOT CAUSE of the user's "I did not cancel any run" concern: a run-level
                # `jobs cancel-run` cancels the WHOLE run, so the downstream shrink task goes
                # UPSTREAM_CANCELED and the MVM stage is LOST. The job is built (build_job_spec) with
                # the vov task on a 15h VOV_TIMEOUT_S and shrink depends_on=vov run_if=ALL_DONE: when a
                # hung vov hits its TASK timeout the platform marks only that task TIMEDOUT and shrink
                # STILL runs via ALL_DONE -> the run ends on its own with full ECM+MVM. Early
                # run-cancel DEFEATS that design. So we only LOG the teardown-hang (so the operator
                # knows ECM functional work is done and the run is waiting out its task timeout); the
                # 15h task-timeout -> ALL_DONE -> shrink path is what terminates it. The real fix for
                # the wasted teardown wall-time is a clean in-driver vov exit (agent-side), tracked
                # separately; the marathon must NOT cancel.
                pulse(f"[{ind}] VOV TEARDOWN-HANG DETECTED (observe-only): model.json written + "
                      f"ecm-log flatline ~{mins}m + {_why}. NOT cancelling -- vov rides its 15h task "
                      f"timeout, then shrink/MVM runs via ALL_DONE (run ends on its own with full "
                      f"ECM+MVM). alias=marathon-vov-teardown-observe-only")
    else:
        hs["mtime"] = mt
        hs["since"] = None
    return False


def wait_terminal(profile, ind, run_id):
    started = time.time()
    last = 0
    hang_state = {}
    while True:
        if os.path.exists(KILL_FILE):
            pulse(f"[{ind}] KILL file present — leaving run {run_id} as-is and exiting watcher")
            return {"lc": "ABORTED", "result": "KILLED"}
        try:
            info = get_run(profile, run_id)
        except Exception as e:
            pulse(f"[{ind}] poll err (retry): {str(e)[:160]}")
            time.sleep(POLL_S)
            continue
        if info["lc"] in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
            return info
        try:
            _vov_teardown_hang_cancel(profile, ind, run_id, info, hang_state)
        except Exception as e:
            pulse(f"[{ind}] hang-detector err: {str(e)[:120]}")
        if time.time() - last >= PULSE_S:
            ts = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}" for t in info["tasks"])
            pulse(f"[{ind}] {profile} elapsed={int((time.time()-started)/60)}m lc={info['lc']} [{ts}]")
            last = time.time()
        time.sleep(POLL_S)


def export_industry(profile, ind):
    cat = cat_name(ind)
    root = f"/Volumes/{cat}/_metamodel/vol_root/business/{ind}"
    ver = latest_version(profile, ind)  # v4.0.7 marathon-harvest-latest-version (never stale v2)
    dest = f"{OUT_DIR}/{ind}"
    Path(dest).mkdir(parents=True, exist_ok=True)
    got = {"_version": ver}
    for scope in ("ecm", "mvm"):
        src = f"dbfs:{root}/{ver}/{scope}"
        d = f"{dest}/{ver}/{scope}"
        Path(os.path.dirname(d)).mkdir(parents=True, exist_ok=True)
        try:
            db(["fs", "cp", "-r", src, d, "--overwrite"], profile, timeout=1200)
            got[scope] = os.path.exists(f"{d}/model.json")
        except Exception as e:
            pulse(f"[{ind}] export {scope} failed: {str(e)[:160]}")
            got[scope] = False
    for fn in ("readme.md",):
        try:
            db(["fs", "cp", f"dbfs:{root}/{ver}/{fn}", f"{dest}/{ver}/{fn}", "--overwrite"],
               profile, timeout=120)
        except Exception:
            pass
    pulse(f"[{ind}] export harvested {ver} ecm={got.get('ecm')} mvm={got.get('mvm')} "
          f"alias=marathon-harvest-latest-version")
    return got


def process_industry(profile, ind, state):
    if os.path.exists(KILL_FILE):
        return
    cur = state.get("industries", {}).get(ind, {})
    if cur.get("status", "").startswith("green"):
        pulse(f"[{ind}] already green — skip")
        return
    rid = cur.get("run_id")
    if cur.get("status") in ("running", "submitted", "exporting") and rid:
        try:
            info = get_run(profile, rid)
            if info["lc"] in ("PENDING", "RUNNING", "TERMINATED", "INTERNAL_ERROR", "SKIPPED", "BLOCKED"):
                pulse(f"[{ind}] RE-ATTACH run={rid} lc={info['lc']}")
                if info["lc"] not in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
                    info = wait_terminal(profile, ind, rid)
                if info.get("result") == "KILLED":
                    return
                _finish(profile, ind, state, info)
                return
        except Exception as e:
            pulse(f"[{ind}] re-attach failed ({str(e)[:120]}) — restarting")
    if os.path.exists(DRAIN_FILE):
        pulse(f"[{ind}] DRAIN active — not starting new run (baseline-preserve). alias=marathon-drain-baseline-preserve")
        if not cur.get("status", "").startswith(("green", "partial", "red")):
            set_ind(state, ind, status="queued_paused")
        return
    pulse(f"=== START {ind} on {profile} ===")
    set_ind(state, ind, status="preparing", profile=profile)
    try:
        reused = prepare_catalog(profile, ind)
        stage_files(profile, ind, reused=reused)
    except Exception as e:
        pulse(f"[{ind}] PREP FAILED: {str(e)[:300]}")
        set_ind(state, ind, status="prep_failed", error=str(e)[:300])
        return
    try:
        job_id = find_or_create_job(profile, ind, installed=reused)
        set_ind(state, ind, job_id=job_id, status="submitted", install_reused=reused)
        run_id = run_now(profile, job_id)
        set_ind(state, ind, run_id=run_id, status="running")
        pulse(f"[{ind}] submitted job={job_id} run={run_id}")
    except Exception as e:
        pulse(f"[{ind}] SUBMIT FAILED: {str(e)[:300]}")
        set_ind(state, ind, status="submit_failed", error=str(e)[:300])
        return
    info = wait_terminal(profile, ind, run_id)
    if info.get("result") == "KILLED":
        return
    _finish(profile, ind, state, info)


def _finish(profile, ind, state, info):
    ts = ", ".join(f"{t['k']}={t['r'] or t['lc']}" for t in info.get("tasks", []))
    pulse(f"[{ind}] TERMINAL lc={info['lc']} result={info.get('result')} tasks=[{ts}] url={info.get('url')}")
    set_ind(state, ind, status="exporting", terminal=info.get("result"),
            tasks=info.get("tasks"), run_url=info.get("url"))
    got = export_industry(profile, ind)
    status = "green" if (got.get("ecm") and got.get("mvm")) else \
             ("partial" if got.get("ecm") else "red")
    set_ind(state, ind, status=status, exported=got)
    pulse(f"[{ind}] {status.upper()} exported ecm={got.get('ecm')} mvm={got.get('mvm')}")
    # User directive: full VReq audit on EVERY industry as it completes (stored for later v3 use).
    # Runs whenever an ECM exists (green or partial) — audit reads the ECM vov log + exported model.json.
    if got.get("ecm"):
        try:
            import vov_audit_extract as _audit  # lazy: avoids circular import at module load
            audit = _audit.extract(ind, profile)
            sb = (audit or {}).get("scoreboard", {})
            pulse(f"[{ind}] AUDIT stored total={sb.get('total_requirements')} "
                  f"fulfilled={sb.get('fulfilled')} partial={sb.get('partial')} "
                  f"failed={sb.get('failed')} precision={sb.get('precision')} recall={sb.get('recall')}")
        except Exception as e:
            pulse(f"[{ind}] AUDIT FAILED: {str(e)[:200]}")


def tick_profile(profile, state):
    for ind in ASSIGN[profile]:
        if os.path.exists(KILL_FILE):
            return
        cur = state.get("industries", {}).get(ind, {})
        st = cur.get("status", "")
        if st.startswith("green"):
            continue
        rid = cur.get("run_id")
        if rid and st in ("running", "submitted", "exporting"):
            try:
                info = get_run(profile, rid)
            except Exception as e:
                pulse(f"[{ind}] {profile} poll err: {str(e)[:140]}")
                return
            if info["lc"] in ("TERMINATED", "INTERNAL_ERROR", "SKIPPED"):
                _finish(profile, ind, state, info)
                continue
            ts = ", ".join(f"{t['k']}={t['lc'] or '?'}/{t['r'] or '-'}" for t in info["tasks"])
            pulse(f"[{ind}] {profile} lc={info['lc']} [{ts}]")
            return
        if os.path.exists(DRAIN_FILE):
            pulse(f"[{ind}] DRAIN active — not starting new run (baseline-preserve). alias=marathon-drain-baseline-preserve")
            if not st.startswith(("green", "partial", "red")):
                set_ind(state, ind, status="queued_paused")
            continue
        pulse(f"=== START {ind} on {profile} ===")
        set_ind(state, ind, status="preparing", profile=profile)
        try:
            reused = prepare_catalog(profile, ind)
            stage_files(profile, ind, reused=reused)
            job_id = find_or_create_job(profile, ind, installed=reused)
            set_ind(state, ind, job_id=job_id, install_reused=reused)
            run_id = run_now(profile, job_id)
            set_ind(state, ind, run_id=run_id, status="running")
            pulse(f"[{ind}] submitted job={job_id} run={run_id}")
        except Exception as e:
            pulse(f"[{ind}] START FAILED: {str(e)[:280]}")
            set_ind(state, ind, status="prep_failed", error=str(e)[:280])
        return
    pulse(f"[{profile}] all industries done")


def tick(profiles, state):
    pulse(f"--- TICK {now()} profiles={profiles} ---")
    threads = []
    for p in profiles:
        t = threading.Thread(target=tick_profile, args=(p, state), name=p)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    inds = state.get("industries", {})
    done = [i for i, v in inds.items() if v.get("status", "").startswith(("green", "partial", "red"))]
    green = [i for i, v in inds.items() if v.get("status", "").startswith("green")]
    total = sum(len(v) for v in ASSIGN.values())
    pulse(f"--- TICK DONE green={len(green)} done={len(done)}/{total} ---")
    return len(done) >= total


def worker(profile, state):
    for ind in ASSIGN[profile]:
        if os.path.exists(KILL_FILE):
            pulse(f"[{profile}] KILL — stopping worker")
            return
        try:
            process_industry(profile, ind, state)
        except Exception as e:
            pulse(f"[{profile}] UNCAUGHT {ind}: {str(e)[:300]}")
            set_ind(state, ind, status="uncaught", error=str(e)[:300])
    pulse(f"[{profile}] worker done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", default=",".join(ASSIGN.keys()))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    state = load_state()
    save_state(state)
    if args.once:
        tick(profiles, state)
        return
    pulse(f"=== VOV2 MARATHON START profiles={profiles} ===")
    if args.dry_run:
        for p in profiles:
            for ind in ASSIGN[p]:
                spec = build_job_spec(ind)
                pulse(f"[dry] {p}/{ind} cat={cat_name(ind)} tasks={[t['task_key'] for t in spec['tasks']]}")
        pulse("=== DRY RUN DONE ===")
        return
    threads = []
    for p in profiles:
        t = threading.Thread(target=worker, args=(p, state), name=p, daemon=False)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    inds = state.get("industries", {})
    green = [i for i, v in inds.items() if v.get("status", "").startswith("green")]
    pulse(f"=== VOV2 MARATHON DONE green={len(green)}/{sum(len(v) for v in ASSIGN.values())} :: {sorted(green)} ===")


if __name__ == "__main__":
    main()
