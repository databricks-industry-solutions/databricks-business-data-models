# V2 VIBE-MODELING MARATHON — AGENT HANDOFF PROMPT

You are taking over an autonomous marathon. Your single job: generate **v2** of 13 industry
data models with the `vibe-modelling-agent`, driving each to terminal SUCCESS at the highest
possible **verified** vibe adherence, then publish each v2 into the fork repo. Run all 13 in
parallel across 5 Databricks workspaces, watch them, score them honestly, and push results.
Do NOT stop until all 13 are green or genuinely unrecoverable. Operate under the repo
guardrails in `CLAUDE.md` (root-cause fixes, single-digit semver, brutal honesty score,
§10.6 zero-error gate, §11 pulse discipline, §9 model-level audit).

---

## 0. TL;DR — what to run

```bash
cd /Users/user/Documents/projects/vibe-modelling-agent/runner

# 0a. Deploy the current agent to ALL 5 workspaces (versioned path) — see §3.
# 0b. Set AGENT_VER in vov_v2_marathon.py to match (§3.3).
# 0c. Stage v1 model.json + curated next_vibes from the fork into /tmp/vov_stage (§4).
# 0d. Dry-run to confirm job specs:
python3 vov_v2_marathon.py --dry-run
# 0e. Launch the marathon (backgrounded, survives your turn):
nohup python3 vov_v2_marathon.py > ~/claude/vibe-agent/vov2_console.log 2>&1 &
# 0f. Watch (§6) and pulse every 30 min (§9). On each industry terminal: audit (§7-8), run the
#     structural-quality + improvement gate (§8.3), and ONLY publish v2 if it passes (§10, §12).
```

> Read **§1A PRIME DIRECTIVES** first. The five rules (VOV must improve the model; adherence is
> against the WHOLE vibe so 45 applied of 100 = 45% not 90%; every fix is generic; any hang/critical
> → generic fix → relaunch; run in background + 30-min pulse) outrank everything else here.

---

## 1. Mission & scope

- **Industries (13):** automotive, construction, consumer_goods, health_insurance, healthcare,
  manufacturing, media_broadcasting, ngo, restaurants, retail, semiconductors,
  travel_hospitality, water_utilities.
- **Operation per industry:** a 3-task Databricks job (already coded in `vov_v2_marathon.py`):
  1. `install model` — installs the **v1 ECM** `model.json` into a fresh catalog (gives VOV a real
     v1 to diff against).
  2. `vibe modeling of version` (VOV) — reads the **curated `next_vibes.txt`** and produces **v2 ECM**.
  3. `shrink ecm` — derives **v2 MVM** from v2 ECM.
- **Input authority:** the curated `next_vibes.txt` (Section 2 = reviewer comments verbatim) is the
  **supreme authority** (CLAUDE.md §3c). Every VReq in it must be applied and **verified** against
  the v2 model.json + physical schema. A "Max retries exhausted, proceeding" soft-accept does NOT
  count as applied.
- **Deliverable per industry:** v2 ECM + v2 MVM published into the fork at
  `data-models/<industry>/v2/{ecm,mvm}/`, plus a stored VReq audit JSON.

---

## 1A. PRIME DIRECTIVES — read before every action (NON-NEGOTIABLE)

These five rules outrank everything else in this prompt. If any other section seems to
contradict them, these win.

### PD-1 — VOV MUST IMPROVE THE MODEL. Always.
v2 is a FAILURE if it is not strictly better than v1. Terminal SUCCESS is necessary but NOT
sufficient. Before publishing any v2 you MUST prove improvement with the structural gate:
```bash
python3 runner/vov_structural_audit.py \
  --v1 /tmp/vov_stage/<ind>/model/model.json \
  --v2 /tmp/vov_out/<ind>/v2/ecm/model.json
# exit 0 = PASS (no structural regression). exit 1 = v2 regressed -> DO NOT PUBLISH; RCA + fix + relaunch.
```
v2 must NOT add empty/thin/skeleton products or domains vs v1, must NOT lose attributes on net,
and must NOT drop structural integrity (cycles/silos/FK density). A v2 that "ran clean" but is
flatter, thinner, or more stubbed than v1 is a regression — treat it as a FAILED run (PD-4).

### PD-2 — ADHERENCE IS MEASURED AGAINST THE *WHOLE* VIBE, NOT WHAT THE AGENT EXTRACTED.
The denominator is EVERY VReq present in `next_vibes.txt` — including the ones the agent never
extracted. Worked example the agent MUST internalize:
> A vibe contains **100** VReqs. The agent extracts **50** and applies **45**.
> Adherence = 45 / 100 = **45%**.  NOT 45/50 = 90%.

Extraction completeness is HALF the score. A VReq the agent never noticed is a MISS, identical to
one it noticed and dropped. The agent self-scoreboard (§8.1) divides by what it extracted and so
LIES; always gate on the ground-truth audit (§8.2) whose denominator is the full parsed VReq set.
**Target = 100% verified adherence; HARD FLOOR = 90%.** A "Max retries exhausted, proceeding"
soft-accept is NOT applied and scores 0 for that VReq.

### PD-3 — EVERY FIX IS GENERIC. NEVER INDUSTRY-SPECIFIC.
No fix, patch, prompt tweak, threshold, blacklist, or workaround may reference or special-case any
industry (automotive, healthcare, gov_transport, banking, …). Every root cause is solved from the vibe /
runtime / catalog / model structure so the SAME fix improves all 41 industries. If a fix only helps
one industry it is wrong — find the generic root cause (CLAUDE.md §3, §8.5). Grep your diff for
industry names before committing; a hit is a defect.

### PD-4 — ANY HANG OR CRITICAL ISSUE -> GENERIC FIX -> RELAUNCH FROM SCRATCH.
If an industry hangs (teardown hang past cap with no artifact), trips any §10.6 hard signature,
fails the PD-1 improvement gate, or scores < 90% ground-truth: do NOT accept it. RCA the root cause,
apply a GENERIC fix (PD-3), bump the single-digit semver, redeploy to all 5 workspaces, DROP that
industry's catalog, and re-run it FROM SCRATCH (no chaining). Loop until green (§12). Never publish
a hung / critical / regressed industry.

### PD-5 — RUN IN BACKGROUND. PULSE EVERY 30 MINUTES. NEVER GO SILENT.
The marathon runs as a backgrounded process (§5) plus a background reconcile tick (§6.3). Post a §9
pulse every 30 minutes covering all industries until every one is green or genuinely unrecoverable.
Use background shells, never Cursor `Monitor` (needs approvals, stalls the loop). Follow CLAUDE.md
§11 pulse discipline — no "looking good" without evidence; soft-accepts are RED.

---

## 2. Repos, branches, and key paths

| Thing | Location |
|---|---|
| Agent repo (this repo) | `/Users/user/Documents/projects/vibe-modelling-agent` (branch `scratch/vibe-compiler-breakthrough`) |
| Fork (publish target) | `amralieg/lakehouse-business-data-models` — local clone: `/Users/user/Documents/projects/_marathon_prep/fork` (branch `main`) |
| Curated vibes source | `amralieg/vibe-business-data-models-v2` — local clone: `/Users/user/Documents/projects/_marathon_prep/repo2` |
| Agent notebook | `agent/dbx_vibe_modelling_agent.ipynb` (`__AGENT_VERSION__` in Cell 1) |
| Orchestrator | `runner/vov_v2_marathon.py` (THE driver — reuse it, do not reinvent) |
| Self-scoreboard audit | `runner/vov_audit_extract.py` |
| Ground-truth (honest) audit | `runner/vov_groundtruth_audit.py` |
| Structural-quality auditor + improvement gate | `runner/vov_structural_audit.py` (empty/thin domains & products, wrong types, untagged PII, v1→v2 improvement gate — §8.3) |
| Repo-sync helper | `runner/sync_to_repo.py` (retarget to the fork — see §10) |
| Pulse log | `~/claude/vibe-agent/vov2_pulses.txt` |
| State file | `~/claude/vibe-agent/vov2_state.json` |
| Kill switch | `touch ~/claude/vibe-agent/vov2_KILL` (stops new submissions; leaves running jobs alone) |
| Per-industry export | `/tmp/vov_out/<industry>/v2/{ecm,mvm}/model.json` |

The fork already has, for all 13 industries:
- `data-models/<industry>/v1/ecm/model.json` (5–14 MB) — the **install input**.
- `data-models/<industry>/v1/ecm/vibes/next_vibes.txt` — the **curated VOV input** (already replaced
  with repo2's reviewer-authored instructions; committed as `d8802fe`).

GitHub auth: `gh auth switch --user amralieg` before any push to the fork.

---

## 3. Pre-flight — deploy the agent to ALL 5 workspaces

The marathon spreads 13 industries across 5 workspaces. The agent notebook must be deployed
(versioned, never canon path) to **every** workspace the marathon uses, and `vov_v2_marathon.py`
must point at that exact version.

### 3.1 Environments (all valid as of handoff)

| Profile | Cloud | Warehouse ID | Industries (from `ASSIGN`) |
|---|---|---|---|
| `<profile>` | GCP field-eng | `d6d89fb9fd47b835` | travel_hospitality, consumer_goods, automotive |
| `<profile>` | AWS field-eng | `862f1d757f0424f7` | ngo, retail, healthcare |
| `<profile>` | GCP personal | `2023d0a3a188bd24` | restaurants, semiconductors, media_broadcasting |
| `<profile>` | Azure personal | `2ad1b26db73a7c6f` | water_utilities, manufacturing |
| `my-uae` | Azure personal | `6b2c33b3b2aae3ac` | construction, health_insurance |

(`logfood` is internal Databricks telemetry — do NOT run the agent there.)

### 3.2 Deploy (versioned path, per CLAUDE.md §10.7 Step 5–6)

Let `NN` = `__AGENT_VERSION__` minus dots (e.g. `3.8.5` → `385`). For each profile:

```bash
WS="/Users/user@example.com"
for P in <profile> <profile> <profile> <profile> my-uae; do
  databricks workspace import "$WS/dbx_vibe_modelling_agent_v${NN}" \
    --file agent/dbx_vibe_modelling_agent.ipynb \
    --format JUPYTER --language PYTHON --overwrite --profile $P
done
# Verify each deployed archive carries this version's aliases (Step 6):
for P in <profile> <profile> <profile> <profile> my-uae; do
  databricks workspace export "$WS/dbx_vibe_modelling_agent_v${NN}" --format JUPYTER \
    --profile $P --file /tmp/v${NN}_check_$P.ipynb
  grep -c "verifier-after-state-inventory\|self-cancel-vol-log\|canonical-key-attr-flag" /tmp/v${NN}_check_$P.ipynb
done   # each must be >= 1
```

### 3.3 Point the orchestrator at the deployed version

Edit `runner/vov_v2_marathon.py`:

```python
AGENT_VER = "385"   # MUST equal __AGENT_VERSION__ minus dots; never run a stale agent
```

`AGENT_PATH` is derived from it (`.../dbx_vibe_modelling_agent_v{AGENT_VER}`). If `AGENT_VER` does
not match the deployed archive, you are running a stale agent — STOP and fix.

### 3.4 Version note

The current code is `__AGENT_VERSION__ = "3.8.5"` (verifier-blindness + hang-observability +
canonical-PK fixes, committed to `scratch/vibe-compiler-breakthrough` but **not yet live-proven**).
This marathon IS the live proof. If any §10.6 hard signature appears, RCA → root-cause fix → bump
to the next single-digit semver → redeploy to all 5 → re-run that industry from scratch (§11).

---

## 4. Stage inputs from the fork

`vov_v2_marathon.py` stages from `/tmp/vov_stage/<ind>/{model/model.json, next_vibes.txt}`. Populate
it from the fork (so the install gets v1 ECM and VOV gets the curated next_vibes):

```bash
FORK=/Users/user/Documents/projects/_marathon_prep/fork
for I in automotive construction consumer_goods health_insurance healthcare manufacturing \
         media_broadcasting ngo restaurants retail semiconductors travel_hospitality water_utilities; do
  mkdir -p /tmp/vov_stage/$I/model
  cp "$FORK/data-models/$I/v1/ecm/model.json"            /tmp/vov_stage/$I/model/model.json
  cp "$FORK/data-models/$I/v1/ecm/vibes/next_vibes.txt"  /tmp/vov_stage/$I/next_vibes.txt
done
```

Optional `description.txt` per industry improves `business_description`; if absent the orchestrator
derives a sensible default.

> Staging goes INSIDE each catalog's own `_metamodel/vol_root/_input` folder (NOT a separate
> `_staging` database — that was a regression the user rejected). `vov_v2_marathon.py:vol_base()`
> already does this correctly.

---

## 5. Launch

```bash
cd /Users/user/Documents/projects/vibe-modelling-agent/runner
python3 vov_v2_marathon.py --dry-run        # confirms cat names + task graph per industry
nohup python3 vov_v2_marathon.py > ~/claude/vibe-agent/vov2_console.log 2>&1 &
echo $! > ~/claude/vibe-agent/vov2.pid
```

The orchestrator spawns one worker thread per profile; each worker runs its industries
sequentially, submitting each 3-task job with `jobs run-now --no-wait`, then polling to terminal,
exporting, and auto-running the self-scoreboard audit. State is checkpointed to
`vov2_state.json` after every transition, so the marathon is **resumable**: re-running
`vov_v2_marathon.py` re-attaches to in-flight runs and skips industries already `green`.

Run a single profile or industry subset with `--profiles <profile>,<profile>`. Use `--once` for a single
reconcile tick (useful from a cron/background watcher).

---

## 6. How to WATCH the runs

### 6.1 Pulse + state (fastest signal)
```bash
tail -n 40 ~/claude/vibe-agent/vov2_pulses.txt
python3 -c "import json;d=json.load(open('$HOME/claude/vibe-agent/vov2_state.json'));
[print(f\"{k:<20} {v.get('status'):<12} run={v.get('run_id')} term={v.get('terminal')}\")
 for k,v in sorted(d.get('industries',{}).items())]"
```

### 6.2 Live job state (per industry)
Get `run_id` from the state file, then:
```bash
databricks jobs get-run <run_id> --profile <profile> -o json | python3 -c "
import json,sys;i=json.load(sys.stdin);s=i.get('state',{})
print(s.get('life_cycle_state'),s.get('result_state'))
[print(' ',t['task_key'],(t.get('state') or {}).get('life_cycle_state'),(t.get('state') or {}).get('result_state')) for t in i.get('tasks',[])]
print('URL',i.get('run_page_url'))"
```
The `run_page_url` is the platform URL to verify in the browser.

### 6.3 Background watcher (so progress advances without you)
`runner/vov_daemon.py` / `runner/sync_watchdog.py` / `runner/auto_bounce_watcher.py` exist for
unattended reconcile loops. Simplest robust option — a `--once` tick every few minutes:
```bash
nohup bash -c 'while [ ! -f ~/claude/vibe-agent/vov2_KILL ]; do \
  python3 /Users/user/Documents/projects/vibe-modelling-agent/runner/vov_v2_marathon.py --once \
    >> ~/claude/vibe-agent/vov2_tick.log 2>&1; sleep 300; done' >/dev/null 2>&1 &
```
Do NOT use Cursor's `Monitor` (needs approvals and stalls the loop). Use background shells.

---

## 7. Where the LOGS are

All on the deployment volume `vibe_<ind>_v1`:

| Log | Path (`dbfs:` prefix for `databricks fs cp`) |
|---|---|
| VOV info (the one that matters) | `/Volumes/vibe_<ind>_v1/_metamodel/vol_root/logs/<ind>/v2/ecm/<ind>_info_v2_ecm.log` |
| VOV error | `/Volumes/vibe_<ind>_v1/_metamodel/vol_root/logs/<ind>/v2/ecm/<ind>_error_v2_ecm.log` |
| Shrink (v2 MVM) info/error | `.../logs/<ind>/v2/mvm/<ind>_{info,error}_v2_mvm.log` |
| Install (v1 ECM) info/error | `.../logs/<ind>/v1/ecm/<ind>_{info,error}_v1_ecm.log` |
| AI logs (LLM call trace) | `.../logs/<ind>/v2/ecm/<ind>_ai_logs_v2_ecm.log` |

Pull a log:
```bash
databricks fs cp "dbfs:/Volumes/vibe_<ind>_v1/_metamodel/vol_root/logs/<ind>/v2/ecm/<ind>_info_v2_ecm.log" \
  /tmp/<ind>_info.log --overwrite --profile <profile>
```
Model + next_vibes artifacts (written BEFORE teardown, so present even if the task is cap-killed in
a teardown hang):
```
/Volumes/vibe_<ind>_v1/_metamodel/vol_root/business/<ind>/v2/ecm/model.json
/Volumes/vibe_<ind>_v1/_metamodel/vol_root/business/<ind>/v2/ecm/vibes/next_vibes.txt
/Volumes/vibe_<ind>_v1/_metamodel/vol_root/business/<ind>/v2/mvm/model.json
```

---

## 8. How to SCORE / audit the next_vibes (TWO scoreboards — trust the honest one)

There are two audits. They disagree on purpose; report BOTH but gate on the ground-truth one.

### 8.1 Agent self-scoreboard (what the agent THINKS it did)
```bash
python3 runner/vov_audit_extract.py            # writes ~/claude/vibe-agent/v2_audit/<ind>.json
```
Reads the final `vibe_orchestrator_scored` payload from the VOV info log: extracted / fulfilled /
partial / failed + per-VReq evidence + SelfFixer events + model.json counts. **Caveat:** its
denominator = what the agent *extracted*, so it flatters itself (the "lying scoreboard").

### 8.2 Ground-truth / honest score (what the model ACTUALLY satisfies)
```bash
python3 runner/vov_groundtruth_audit.py        # writes ~/claude/vibe-agent/v2_groundtruth/<ind>.json
```
This parses VReqs from `next_vibes.txt` **independently** and verifies each against the v2 ECM
`model.json`, so **adherence = fulfilled / ALL parsed VReqs**. If a vibe has 100 VReqs, the agent
extracts 50 and applies 45, this reports **45%**, not 90%. VReq classes parsed:
- SEC1 preserve — every v1 domain+product must exist in v2 ECM.
- SEC3C P1..P20 — connect_table / rename_attribute / move_product / remove_fk / rename_product.
- SEC3A stubs — listed products must gain real (non-PK/FK) attributes.
- SEC3B thin — listed products should be expanded vs v1.
- SEC2 entities — reviewer-flagged required entities must exist.

> The mission metric (CLAUDE.md) is **VERIFIED vibe adherence**, measured against the WHOLE vibe
> (PD-2): adherence = fulfilled / ALL VReqs in next_vibes.txt, NOT / extracted. Target 100%,
> HARD FLOOR 90%. A soft-accept is NOT applied (scores 0).

### 8.3 Structural-quality pass + VOV-improvement gate (empty / thin domains & products)
Run on EVERY v2 ECM the moment it exports — this is the "empty or thin domains and products pass":
```bash
# single-model findings (empty/thin/skeleton domains+products, wrong types, untagged PII):
python3 runner/vov_structural_audit.py --model /tmp/vov_out/<ind>/v2/ecm/model.json
# improvement gate — v2 MUST NOT regress vs v1 (PD-1):
python3 runner/vov_structural_audit.py \
  --v1 /tmp/vov_stage/<ind>/model/model.json \
  --v2 /tmp/vov_out/<ind>/v2/ecm/model.json   # exit 0 = PASS, exit 1 = REGRESSION -> relaunch
```
Definitions (industry-agnostic, read from model.json structure):
- **empty domain** = 0 products · **thin/stub domain** = <5 products
- **empty product** = 0 attributes · **thin/stub product** = <5 attributes
- **skeleton product** = only PK/FK columns (0-1 data attributes) — the most critical stub class
- **wrong type** = high-precision token rule (e.g. `*_flag` STRING→BOOLEAN, money/rate STRING→DECIMAL,
  `*_date/_at` STRING→TIMESTAMP) · **untagged PII** = person/sensitive column with no sensitivity tag

The gate is a publish blocker: if `--v1/--v2` exits 1, or the v2 still has empty/skeleton products,
the run FAILED PD-1 → RCA → GENERIC fix (PD-3) → relaunch from scratch (PD-4). The same auditor
runs on the whole fork (`--fork <data-models>`) for a portfolio snapshot.

---

## 9. The 30-MINUTE PULSE (what to report)

Every 30 min, post a pulse covering ALL 13 industries. Follow CLAUDE.md §11 (no "looking good"
without evidence; soft-accepts are RED). Each pulse must include, per industry:

1. **Run state** — `lc` + per-task (`install/vov/shrink`) state. Flag retries / `EXPECTED RECURRENCE`.
2. **Ground-truth adherence %** (§8.2) once an ECM exists — headline number. State it as
   `fulfilled / TOTAL_vibe_vreqs` (PD-2 denominator), e.g. `45/100 = 45%`, never `45/50`.
   Floor 90%; below floor → on the relaunch list (PD-4).
3. **Structural pass + improvement** (§8.3) — empty/thin/skeleton domain+product counts for v2,
   and the v1→v2 improvement gate verdict (PASS/REGRESSION). A regression or any new empty/skeleton
   product is RED and forces a relaunch.
4. **§10.6 hard-signature scan** on the pulled logs (must be 0):
   ```python
   import re,glob
   t="".join(open(f,errors='ignore').read() for f in glob.glob('/tmp/<ind>_*.log'))
   for lbl,pat in [("ERROR",r"\bERROR\b"),("F1 perm",r"Permission denied"),
     ("F2/R7 soft-accept",r"Max retries \(3\) exhausted"),("F4 silo",r"SILOED TABLES DETECTED"),
     ("R6 MV fail",r"Failed metric view.*UNRESOLVED"),("R8 cycles",r"Found [1-9]\d* cycle\(s\)"),
     ("N2 fidelity",r"Fidelity gates FAILED"),("NameError",r"NameError|AttributeError|TypeError"),
     ("Traceback",r"Traceback \(most recent")]:
       print(lbl,len(re.findall(pat,t)))
   ```
5. **Soft-accept inventory** — list every `Max retries (3) exhausted` site (RED, not yellow).
6. **Self-cancel proof** (v3.8.5) — grep the VOV info log for `self-cancel` ARMED + the watchdog
   diag (confirms the teardown-hang terminator fired with the correct run_id).
7. **Tag counts** — physical vs model.json (§11.2) once installed.
8. **Predictive verdict** — probability this industry terminates SUCCESS, with the math.

Aggregate footer: `green=N/13, running=…, failed=…, on-relaunch(PD-4)=…`.

---

## 10. PUBLISH v2 to the fork (after each industry goes green)

`runner/sync_to_repo.py` mirrors completed artifacts and commits one commit per industry, but its
DEFAULT target is the OLD `vibe-business-data-models` repo. **Retarget it to the fork** (set
`DEFAULT_REPO_PATH` / `DEFAULT_REPO_REMOTE` to `_marathon_prep/fork` /
`amralieg/lakehouse-business-data-models`), OR do the equivalent copy+commit directly:

```bash
FORK=/Users/user/Documents/projects/_marathon_prep/fork
I=<industry>
mkdir -p "$FORK/data-models/$I/v2/ecm" "$FORK/data-models/$I/v2/mvm"
cp -r /tmp/vov_out/$I/v2/ecm/* "$FORK/data-models/$I/v2/ecm/"
cp -r /tmp/vov_out/$I/v2/mvm/* "$FORK/data-models/$I/v2/mvm/"
cd "$FORK"
gh auth switch --user amralieg
git add data-models/$I/v2
git commit -m "marathon: publish $I v2 (ECM+MVM) — gt-adherence <PCT>%, run <run_id>"
git push origin main
```
Match the existing v1 folder layout (`model.json`, `readme.md`, `diagram/`, `docs/`, `metrics/`,
`ontology/`, `schemas/`, `vibes/`) — `vov_export_full.py` pulls the full artifact set if you want
parity beyond model.json. Reference the live `run_id` and the **ground-truth** adherence % in the
commit message (CLAUDE.md §1b: a published commit must cite the run that proved it).

---

## 11. Verify against model.json AND physical schema (R2 / install parity)

Do NOT trust terminal SUCCESS alone (§8.7 runner's test). For each completed industry:

### 11.1 model.json structural verify
`vov_groundtruth_audit.py` (§8.2) already does this. Additionally sanity-check counts:
```python
import json
m=json.load(open('/tmp/vov_out/<ind>/v2/ecm/model.json'))['model']
D=m['domains']; P=sum(len(d.get('products',d.get('data_products',[]))) for d in D)
A=sum(len(p['attributes']) for d in D for p in d.get('products',d.get('data_products',[])))
FK=sum(1 for d in D for p in d.get('products',d.get('data_products',[])) for a in p['attributes'] if a.get('foreign_key_to'))
print('domains',len(D),'products',P,'attrs',A,'fks',FK,'metric_views',len(m.get('metric_views',[])))
```

### 11.2 Physical schema vs model.json (run on the deployment warehouse)
```sql
-- table parity
SELECT table_schema, COUNT(*) FROM vibe_<ind>_v1.information_schema.tables
WHERE table_schema NOT LIKE '\_%' GROUP BY 1 ORDER BY 1;
-- column tag parity (glossary / sensitivity / source_attribute / primary_key)
SELECT COUNT(*) FROM vibe_<ind>_v1.information_schema.column_tags;
-- table tag parity (subdomain / source_table / original_table_name / division)
SELECT COUNT(*) FROM vibe_<ind>_v1.information_schema.table_tags;
```
Compare physical tag counts to the model.json tag inventory. A physical count materially below the
model.json count is an **R2 / SET TAGS regression** — RCA it (see the tags answer in §13; v3.6.6
fixed the Spark-Connect concurrency loss, v3.8.5 fixed the verifier blindness that masked it).

Note: the marathon job (install → VOV → shrink) builds the catalog at **v2** as it goes; the
VOV/shrink steps write physical tables + tags into `vibe_<ind>_v1`. If you instead want to validate
a clean install from the published model.json, run the agent `install model` operation against the
exported `v2/ecm/model.json` into a throwaway catalog and re-run §11.2.

---

## 12. Success criteria & the zero-error gate (CLAUDE.md §10.6)

An industry is **green** only when ALL hold:
- Job `result_state=SUCCESS` (install + vov + shrink all `done`; `run_if=ALL_DONE` tolerates a
  teardown-hang cap-kill on a functionally-complete task, but the artifacts must exist).
- `v2/ecm/model.json` AND `v2/mvm/model.json` exported (non-empty, parse-valid).
- §10.6 hard signatures all **0** in the logs (ERROR / F1 / F2 soft-accept / F4 silo / R6 MV fail /
  R8 cycles / N2 fidelity / NameError / Traceback).
- **PD-2 ground-truth adherence (§8.2) ≥ 90%** (target 100%), denominator = ALL vibe VReqs.
  Measured from the v4.2.2 CORRECTED physical reground (informational-exclude + blind-partial-unknown
  + gt-rescue-typecorrect); a "Max retries exhausted, proceeding" soft-accept does NOT count as applied.
- **PD-1 improvement gate (§8.3) PASS** — `vov_structural_audit.py --v1 --v2` exits 0; v2 has
  **zero empty/skeleton products**, no new thin/stub domains or products vs v1, and no net attribute loss.
- **native_quality (structural) ≥ v1** — the v2 native/structural quality must not regress vs v1
  (the vov_quality 50/50 blend embeds adherence, so gate its native half against v1, not an absolute bar).
- v2 published to the fork with a commit citing the run_id + ground-truth adherence %.

**Gate 4A (v4.2.2, superseding the original vov_quality≥85 hard gate):** publish iff
adherence≥90 (corrected) AND §10.6 zero-error AND PD-1 strictly-improves AND native_quality≥v1.
`vov_quality` is REPORT-ONLY (recorded in the audit, not a blocking gate) — the original 85% vov_quality
bar was infeasible against the published "strong 6" baseline and conflated adherence with native quality.

The whole marathon is done when all 13 are green. "Mostly clean" is not done. Any industry that
hangs, trips a §10.6 signature, fails PD-1, or scores <90% goes on the relaunch list (PD-4): fix
generically (PD-3), redeploy all 5, drop catalog, re-run from scratch — never publish it as-is.

---

## 13. ANSWER: does `model.json` contain the tags? will install apply them?

**Yes, `model.json` contains the tags — at all three scopes.** Verified against a real exported
model.json:
- **Domain:** `division` + `tags` (flat string) + `tag_set` (structured `[{key,value,kind,source}]`).
- **Product/table:** `subdomain`, `steward`, `tags` (e.g. `gov_transport_subdomain=...`), `tag_set`.
- **Attribute/column:** `tags` (e.g. `primary_key,glossary_term=Applicant Id`), `tag_set`.
- **Metric views:** carried under `model.metric_views`.

Two parallel representations exist (additive, backward-compatible): the legacy flat **`tags`**
string and the structured **`tag_set`** (v3.4.6 `model-json-authoritative-tags`). The physical
tag-apply pass (`step_apply_tags`) reads the **flat `tags` string** and issues Unity Catalog
`SET TAGS`. So:

**When you install from `model.json`, you DO get the tags** — the install path reconstructs the
physical schema from `model.json` and runs the same `step_apply_tags` pass, re-emitting the
domain/table/column tags via `SET TAGS`.

**Honest caveats (so you verify, not assume):**
1. **It depends on the installer.** The **agent's `install model` operation** applies tags. The
   `model-installer` in the upstream `lakehouse-industry-data-models` repo is a *different* tool —
   confirm it issues `SET TAGS` before claiming parity; if it only `CREATE TABLE`s, you get the
   schema but not the tags from that path.
2. **SET TAGS reliability.** Tag application historically lost up to ~97% of tags under
   Spark-Connect session saturation (healthcare); fixed in **v3.6.6** with a concurrency cap +
   backoff. Always do the §11.2 physical-vs-model.json tag-count check after install.
3. **Tag governance.** UC column/table tags must be permitted by the workspace tag policy; the
   agent creates the keys it needs, but a restrictive metastore tag allowlist can silently drop
   them — check `information_schema.{column_tags,table_tags}` to confirm.

Bottom line: model.json is self-contained for tags; a faithful installer (the agent's own
`install model`) reproduces them; always verify physically because `SET TAGS` is the lossy step.

---

## 14. Known hazards & how to handle them

| Hazard | Symptom | Handling |
|---|---|---|
| Serverless teardown hang | task `RUNNING` for hours after `pipeline-finally`; artifacts already on volume | v3.8.5 control-plane self-cancel should fire (grep `self-cancel` ARMED). `run_if=ALL_DONE` lets downstream proceed. If a task hangs past its cap with NO artifact, cancel-run and re-run that industry. |
| Auth token expiry | `databricks` CLI 401 / `token has expired` mid-marathon | orchestrator auto-refreshes (`_refresh`); if persistent, `databricks auth token --profile <p>` and re-run `--once`. |
| Catalog storage-root | `CREATE CATALOG` fails with managed-location error | `prepare_catalog` auto-discovers a managed base and retries; if all fail, the industry logs `prep_failed` — fix the workspace default storage and re-run. |
| Stale agent | running an old `_v<NN>` | §3.3: `AGENT_VER` MUST equal `__AGENT_VERSION__`; re-verify the deployed archive grep (§3.2). |
| Phantom QUEUED run | run stuck `QUEUED` > 3 min | `databricks jobs list-runs --job-id <id> --active-only`; cancel residual `run-now`-without-`--no-wait` leftovers. |
| Lying scoreboard | agent reports high adherence, model is worse | ALWAYS gate on §8.2 ground-truth, never §8.1. v3.8.5 verifier-blindness fix narrows the gap but the independent audit is the source of truth. |
| v2 regression (PD-1) | v2 has new empty/skeleton products, fewer attrs, or thinner than v1 | `vov_structural_audit.py --v1 --v2` exits 1. Do NOT publish. RCA the generic root cause (e.g. generator received only a count and free-invented stubs; preserve-pass dropped v1 products), fix generically (PD-3), bump semver, redeploy all 5, drop catalog, re-run from scratch (PD-4). |
| Low adherence (<90%) | §8.2 ground-truth below floor | Usually an extraction miss (PD-2 denominator) or soft-accept drop. Trace the missed VReq classes generically, fix, relaunch. Never publish below floor. |
| Industry-specific fix creep | a patch special-cases one industry | PD-3 violation. Grep the diff for industry names; rewrite the fix to read from vibe/runtime/catalog so it helps all 41. |

---

## 15. Kill switch / pause

```bash
touch ~/claude/vibe-agent/vov2_KILL     # stops NEW submissions; running jobs keep going
rm    ~/claude/vibe-agent/vov2_KILL     # resume; re-run vov_v2_marathon.py to re-attach
```
To stop a specific run: `databricks jobs cancel-run <run_id> --profile <profile>`.

---

## 16. End-of-marathon deliverables

1. All 13 industries green (§12) and published to the fork `data-models/<ind>/v2/{ecm,mvm}/`.
2. Per-industry ground-truth audit JSONs in `~/claude/vibe-agent/v2_groundtruth/`.
3. The two §9.6 reports (validation-report + model-quality-audit) per industry under
   `~/claude/vibe-agent/`.
4. A final summary table: industry × ground-truth adherence % × counts (D/P/A/FK/MV) × §10.6 clean.
5. Brutal honesty score (§6) for the marathon as a whole, with per-deduction evidence.
