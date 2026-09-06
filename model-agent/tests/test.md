# test.md — Test Protocol + Live Cycle State

> Version-agnostic test protocol for the vibe-modelling-agent.
> Part I (§§ A–F) is the protocol — applies to every cycle, every business, every version.
> Part II (Appendix A onward) is the current cycle's live state — gets rewritten each cycle.
> For the unit-test suite, see `readme.md` in this folder.

---

# PART I — TEST PROTOCOL (VERSION-AGNOSTIC)

## A. The 3-stage end-to-end audit (THE definition of "tested")

A pipeline run is NOT "tested" until ALL three stages below pass for ALL submitted businesses. Pipeline `TERMINATED=SUCCESS` is necessary but NOT sufficient (per CLAUDE.md §9.8 anti-rule — a model can be technically installed yet broken in terms of capturing user intent, structural integrity, or physical realisation).

| Stage | What it audits | Why it matters | Where to find evidence |
|---|---|---|---|
| **A — Vibe → Captured-Requirements** | Did the agent EXTRACT every concrete requirement from the user's vibe sources? | If a requirement is missed at the LLM input layer, no amount of downstream work can recover it. §3c USER-KING violation by omission. | `ai_logs/*.log` — search for `VIBE_PARSE` / `vibe_classification` / `user_directives` blocks |
| **B — Captured-Requirements → model.json** | Did the produced model HONOUR every captured requirement (domains, products, attributes, FKs, tags, MVs, counts)? | If captured but not honoured, this is the agent silently overriding the user (§3c violation by commission). | `model.json` for each sub-version (e.g. `/tmp/<run>_terminate/model.json`) + `next_vibes.txt` |
| **C — model.json → Physical Catalog** | Did the install render every model.json entity to a real Spark table / metric view / FK constraint / tag, with matching column lists and types? | Otherwise consumers querying the catalog see a different model than what model.json declares. R2/R6/N3 regressions. | `<catalog>.information_schema.{tables,columns,table_constraints,column_tags}` + `<catalog>._metrics.*` |

**Pass criteria — ALL must hold per business:**

```
Stage A adherence  >= 95%   (every must-have-X is captured; missing must be classifiable as "agent intentionally rejected" not "agent didn't see it")
Stage B adherence  = 100%   on widget-driven requirements (business_domains, must_have_data_products) — these are HARD (§3b)
                  >= 90%    on free-text-vibe requirements — soft, but every miss must have a documented reason (architect-reject, downstream-impossible, etc.)
Stage C adherence  = 100%   on tables + columns + FKs + tags declared in model.json
                  >= 95%    on metric views (R6 DATATYPE / UNRESOLVED drops are allowed only if the agent code can't fix them)
```

**Combined "100% adherence" is the user's bar** (CLAUDE.md §3c + "do not settle"). Anything below = v(NEXT) fix required (§1a NO VERSIONING ROADMAP).

## B. Stage A — Vibe → Captured-Requirements (deep recipe)

### B.1 Inventory ALL vibe sources for the business

A "vibe" can come from up to FOUR sources, all of which the agent reads. Stage A must enumerate requirements from every one of them:

| Source | Where it comes from | How to retrieve |
|---|---|---|
| `business_description` widget | Submit JSON `notebook_params.business_description` | `databricks jobs get-run <rid> -o json` → traverse to `task.notebook_task.base_parameters` |
| `model_vibes` widget | Submit JSON `notebook_params.model_vibes` (often pasted Google Doc text) | Same as above; size up to ~30KB |
| `next_vibes.txt` from the prior version | `dbfs:/Volumes/<cat>/_metamodel/vol_root/business/<biz>/<scope>_v<N-1>/vibes/next_vibes.txt` | `databricks fs cp ...` |
| Hard widgets that double as directives | `business_domains`, `must_have_data_products`, `naming_convention`, `data_model_scopes`, `cataloging_style` | Submit JSON |

### B.2 Extract concrete requirements from each source

This is a HUMAN+LLM hybrid pass — for every source, list every CONCRETE, TESTABLE requirement using these categories (extend as needed):

| Category | Examples | How to detect in vibe |
|---|---|---|
| Must-have DOMAINS | "must have a `claim` domain" | Look for "must have", "include", "required", named domain list |
| Must-have PRODUCTS | "every member must have a `mrn_history` product" | Same; also "should include" |
| Must-NOT-have | "do not split customer into separate `customer_profile` and `customer_account`" | "do not", "avoid", "no separate" |
| Count targets | "~80 products", "exactly 3 domains" | Numeric mentions with units (products/domains/attrs/MVs) |
| Naming conventions | "use snake_case", "no abbreviations except IATA codes" | "use", "follow", "convention" |
| Specific attributes | "every patient must have `mrn`", "include `iata_code` on every airport" | "must have", "include … on every" |
| PII / classification tags | "tag SSN as PII-HIPAA-IDENTIFIER", "all monetary fields tagged sensitivity:financial" | "tag", "classify", "sensitivity:", "PII", "HIPAA", "GDPR" |
| FK relationships | "every order line must link to a product item via item_id" | "link to", "FK", "references", "foreign key", "every X must reference Y" |
| Structural constraints | "no cycles", "shared domain max 5 products", "no bidirectional FKs" | "no cycles", "no shared", "max N" |
| Metric view requirements | "track `monthly_revenue_by_region`", "include `pmpm` MV per insurance plan" | "track", "report on", "monthly", "by-X", "KPI" |
| Industry-specific standards | "IATA codes for airports", "ICD-10 for diagnoses", "DOT FMCSA classes" | Industry acronyms; standards bodies |
| Architect rejections | next_vibes priorities to skip ("ignore PRIORITY 3 — premature") | next_vibes PRIORITY lines marked with `[user-override]` or carried-over |

Each extracted requirement gets a unique ID like `<BIZ>-REQ-001` so it can be tracked through B and C.

### B.3 Audit — was each requirement captured?

For each `<BIZ>-REQ-NNN`, the audit asks: did the agent's `VibeOrchestrator` / `VIBE_PARSE_PROMPT` / equivalent LLM call surface this requirement in its parsed output?

Evidence sources (in order of preference):
1. `ai_logs` log lines containing `VIBE_PARSE_PROMPT response` (or `vibe_classification`) — search for the requirement keyword.
2. `info.log` lines like `[VALIDATOR] User vibes detected (N chars) — count limits will be relaxed` (proves the agent saw the vibe AT ALL).
3. `info.log` lines like `[VIBE_EVENT] {"event": "...", "payload": ...}` — shows what the agent intends to act on.

Classify each requirement:
- **CAPTURED** — found in vibe-parse output verbatim or paraphrased
- **PARTIAL** — referenced but lost a constraint (e.g., "must-have" became "should-have")
- **MISSED** — no trace in any parser output
- **REJECTED-WITH-REASON** — explicitly noted by the agent as out-of-scope, with reason (acceptable for vibe-only — never for widget-driven)
- **DROPPED-SILENTLY** — agent saw it but said nothing (worst class — §3c silent override)

Stage A adherence = (CAPTURED + REJECTED-WITH-REASON) / total.

### B.4 Output format

A table per business:

```
<BIZ>-REQ-001  [CAPTURED]   "must have a claim domain"           evidence: ai_logs:09:01:23 vibe_parse → domains.must_have:["claim"]
<BIZ>-REQ-002  [MISSED]     "include iata_code on every airport" evidence: NONE in vibe_parse or downstream
<BIZ>-REQ-003  [REJECTED]   "exactly 5 domains"                  evidence: ai_logs vibe_parse → "deferred to architect; user count is soft target"
...
```

## C. Stage B — Captured-Requirements → model.json (deep recipe)

### C.1 Cross-check each CAPTURED requirement against model.json

For each `<BIZ>-REQ-NNN` classified as CAPTURED in Stage A, verify it landed in `model.json`. The script template:

```python
import json
m = json.load(open(f"/tmp/<run>_<biz>_terminate/model.json"))
mdl = m["model"]
domains = [d["name"] for d in mdl["domains"]]
products = {(d["name"], p["name"]) for d in mdl["domains"] for p in (d.get("products") or d.get("data_products", []))}
attrs    = {(d["name"], p["name"], a["name"]) for d in mdl["domains"] for p in (d.get("products") or d.get("data_products", [])) for a in p["attributes"]}
fks      = {(d["name"], p["name"], a["name"], a.get("foreign_key_to")) for ... if a.get("foreign_key_to")}
tags     = {(d["name"], p["name"], a["name"], t) for ... for t in (a.get("tags") or [])}
mvs      = [mv["view_name"] for mv in mdl.get("metric_views", [])]

# Per-requirement check
for req in captured_reqs:
    if req.category == "must_have_domain":     check req.value in domains
    if req.category == "must_have_product":    check req.product_key in products
    if req.category == "must_have_attribute":  check req.attr_key in attrs
    if req.category == "must_have_fk":         check req.fk_tuple in fks
    if req.category == "must_have_tag":        check req.tag_tuple in tags
    if req.category == "must_have_mv":         check req.mv_name in mvs
    if req.category == "count_target":         check tolerance(count, req.target)
    if req.category == "structural":           call structural checker (cycles/silos/bidirectional)
    if req.category == "must_not_have":        check the negative
```

### C.2 Classify each captured requirement

- **HONOURED** — in model.json correctly
- **PARTIAL** — present but degraded (e.g., domain in model but missing a must-have product within it)
- **OVERRIDDEN** — explicitly contradicted (e.g., user said "exactly 3 domains" and model has 5)
- **MISSING** — agent captured but did not render (worst class — §3c silent override)

Stage B adherence = HONOURED / (HONOURED + PARTIAL + OVERRIDDEN + MISSING).
Widget-driven requirements (B.1 row 4) must score 100% — anything else is a hard fail.

### C.3 Also count what's in model.json but NOT in any captured requirement

Call this **FABRICATED**. Not always bad — the agent's industry knowledge legitimately adds domains/products beyond what the user said. But fabricated items must be either:
- Justified by industry best-practice (e.g., adding a `payment` domain when user only said "order")
- OR flagged as scope-creep candidates for v(NEXT) removal

The full Stage B output is a 2-direction diff: `captured ∩ model.json`, `captured \ model.json` (missing), `model.json \ captured` (fabricated).

## D. Stage C — model.json → Physical Catalog (deep recipe)

### D.1 For each model.json entity, query the physical metastore

Run these queries against the deployment catalog (`<CATALOG>` = the catalog the run installed into, e.g. `retail_mvm_v1`):

```sql
-- Tables
SELECT table_schema, table_name
FROM   <CATALOG>.information_schema.tables
WHERE  table_schema NOT LIKE '_metamodel%' AND table_schema NOT LIKE '_metrics%';

-- Columns
SELECT table_schema, table_name, column_name, full_data_type
FROM   <CATALOG>.information_schema.columns
WHERE  table_schema NOT LIKE '_metamodel%' AND table_schema NOT LIKE '_metrics%';

-- Foreign-key constraints
SELECT tc.table_schema, tc.table_name, kcu.column_name,
       rc.unique_constraint_schema  AS ref_schema,
       rc.unique_constraint_table   AS ref_table,
       kcu_ref.column_name          AS ref_column
FROM   <CATALOG>.information_schema.table_constraints tc
JOIN   <CATALOG>.information_schema.key_column_usage  kcu      ON tc.constraint_name = kcu.constraint_name
JOIN   <CATALOG>.information_schema.referential_constraints rc  ON tc.constraint_name = rc.constraint_name
JOIN   <CATALOG>.information_schema.key_column_usage  kcu_ref  ON rc.unique_constraint_name = kcu_ref.constraint_name
WHERE  tc.constraint_type = 'FOREIGN KEY';

-- Column tags
SELECT catalog_name, schema_name, table_name, column_name, tag_name, tag_value
FROM   system.information_schema.column_tags
WHERE  catalog_name = '<CATALOG>';

-- Metric views (a separate schema named `_metrics`)
SHOW VIEWS IN <CATALOG>._metrics;
```

### D.2 Build the parity diff per dimension

For each of the 5 dimensions (tables, columns, FKs, tags, MVs), build two sets and diff:

```
model_set     = entities declared in model.json
physical_set  = entities present in information_schema / _metrics

declared_but_missing = model_set \ physical_set    (the bug surface)
physical_but_unmodelled = physical_set \ model_set (orphan installs — much rarer; usually system tables)
declared_and_present = model_set ∩ physical_set
```

### D.3 Classify each gap

- **R2-class** — model.json declares table/column but physical lacks it (DDL writer dropped or normalizer skipped)
- **R6-class** — declared MV failed to install (UNRESOLVED_COLUMN, DATATYPE_MISMATCH, etc.)
- **F10-class** — declared MV silently absent (no error but not in `_metrics` schema)
- **TAG-DROP** — model.json declares tag but `column_tags` missing it
- **FK-DROP** — model.json has `foreign_key_to` but `referential_constraints` lacks the FK

Stage C adherence = `len(declared_and_present) / len(model_set)` per dimension.
Combined Stage C adherence = unweighted average of the 5 dimensions.

### D.4 Type-fidelity sub-check

For each `declared_and_present` column, also verify `physical.full_data_type` matches `model.json.attributes[*].type` after applying the agent's type-map (e.g., model says `currency` → physical should be `DECIMAL(18,2)`; model says `id` → physical should be `BIGINT` or `STRING`). Type drift is a silent quality bug that doesn't show up at install time but breaks consumers.

## E. The combined Adherence Scorecard

For each business, produce a row:

```
| Business | Stage A | Stage B widget | Stage B free | Stage C tables | Stage C cols | Stage C FKs | Stage C tags | Stage C MVs | Verdict |
| RT       |  93%    |  100%          |  88%         |  100%          |  98%         |  93%        |  100%        |  82%        | PARTIAL — v207 retry |
| HC       |  ...    |  ...           |  ...         |  ...           |  ...         |  ...        |  ...         |  ...        |  ...                  |
```

Verdict rules:
- ALL columns 100% AND zero §10.6 hard signatures → **PASS — production-ready**
- Any widget-driven cell < 100% → **HARD FAIL — agent bug**
- Free-text cell < 90% OR any §10.6 hard signature → **PARTIAL — v(NEXT) retry required**
- Pipeline did not reach TERMINATED → **FAIL — investigate platform/runtime**

## F. Other protocol sections

The remaining sections (watcher behaviour, hard-signature list, self-healing loop, artifact layout, post-terminate recipe, decision tree at user ping, honesty rules) are protocol items that apply to every cycle. They follow below.

---

## G. v207 architectural plan — locked decisions (2026-05-26)

After v206 cycle (0/3 PASS, 2/3 PARTIAL, 1/3 INTERNAL_ERROR), the user locked four directional decisions. Recorded here so subsequent cycles inherit the constraints, not re-debate them.

### G.1 Root-cause classes (the 16 v206 candidates collapse to these 4)

| Class | Symptom-count | Examples from v206 | Structural cause |
|---|---|---|---|
| **C1 — LLM context-window topology** | 8 | tag-name double-prefix, MV-as-product confusion, FK-rename non-propagation, compliance domain dropped, 0 of 656 pii_phi tags applied, isolated facility.organization not flagged, soft-accept passing | LLM at stage N never sees what LLM at stage N-1 actually emitted; no queryable global state; each prompt rebuilds a partial view |
| **C2 — No adversarial self-audit role** | 4 | MV column hallucination, vibe directives silently dropped, EAV decomposition not enforced, soft-accept downstream silence | Every persona (Architect, DDL Writer, Verifier) is cooperative. Nobody's job is to FIND FLAWS and REJECT |
| **C3 — Spark Connect verifier as single point of failure** | 3 | HC INTERNAL_ERROR/timeout, RT N2=1, gov_transport N2=1 | Every verifier-LLM call (and the "deterministic rescue" path) goes through Spark Connect; transient REMOTE_FUNCTION_HTTP_FAILED_ERROR has no escape route |
| **C4 — No agent-side time awareness** | 1 | HC ran identical verifier loop with 5 min left as with 4 hours left | No `RuntimeBudget` instance tracking elapsed/remaining wall-clock |

### G.2 Path decisions (4 user-locked)

| Decision | Locked answer | Consequence for v207+ |
|---|---|---|
| Path | Option C: finish vov_2_0-style SelfAuditor + ship orthogonal monolith unblockers | All 4 phases ship in v207; no defer-to-future per §1a |
| v207 scope | Greedy — Phase 0 + 1 + 2 + 2.5 + 3 all in v207 | Includes auto-fix (SelfFixer), not just audit |
| Auditor LLM | `databricks-claude-opus-4-7` as **first-order thinker** | Inserted at order=5 ahead of claude-opus-4-6 (order=10); used for SelfAuditor + SelfFixer + Architect + Judge |
| Notebook strategy | **ONE notebook** | `agent/vov_2_0/*.py` becomes deprecated; all functionality folded into `dbx_vibe_modelling_agent.ipynb` cells. The standalone package is abandoned. |

### G.3 Phase plan for v207 (greedy = all phases ship together)

| Phase | Goal | New code lives in | §10.6 / §1a check |
|---|---|---|---|
| **0** | Monolith unblockers (Spark-free verifier path, Spark-transient-as-skip, RuntimeBudget) | New helper cells near existing LLM-call cells | Without these, HC cannot complete a run; nothing else can be tested |
| **1** | SelfAuditor cell — Stage A/B/C protocol from §A–E, codified as LLM prompt + audit_tools helpers + few-shot examples (the 16 v206 issues become labelled examples) | New cell after existing LLM-config cell | Behavioural test in tests/unit-tests/test_v207_self_auditor.py must show ≥80% issue-detection rate vs v206 manual audit |
| **2** | Wire SelfAuditor as Step 10.9 (post-artifact, pre-install) + Step 11.9 (post-install) | Edits to existing Step 10 / Step 11 cells | Findings written to `next_vibes.txt` as PRIORITY lines |
| **2.5** | SelfFixer — for each `auto_fixable=True` finding, LLM synthesises mutator+verifier in sandbox, runs invariant + scope checks, applies mutation to model.json | New cell using the AST allowlist pattern from existing `vov_2_0/sandbox.py` | The "fix on the fly" the user explicitly asked for |
| **3** | Migrate `vibe_modeling_of_version` step from current LLM-loop to sandbox-first VREQ-batch-handler architecture (port vov_2_0/pipeline.py logic into monolith cells) | Replaces existing `vibe_modeling_of_version` cells | Removes the soft-accept hatch entirely; non-applied VREQs become explicit `rejected_unsafe` / `invariant_violation` / `scope_mismatch` outcomes |

### G.4 Success gate for v207 (per §1b "no commit until success-verified")

ALL must hold on a SINGLE live deploy cycle, on ALL 3 businesses (RT + gov_transport + HC):

```
Stage A   >= 95%   (every business)
Stage B   = 100%   on widget-driven; >= 90% on free-text
Stage C   = 100%   on tables + columns + FKs + tags; >= 95% on MVs
§10.6 hard signatures  = 0   (F1, F2, F4, R6, R8, N2, NameErr, Traceback, INTERNAL_ERROR, timeout)
SelfAuditor findings   >= 80% caught vs manual baseline
SelfFixer auto-fix     >= 1 applied per business with positive verifier outcome (proves the loop works)
```

If ANY business misses ANY of the above on the v207 deploy, iterate (re-deploy without commit per §1b) until all green. Only then `git commit + push`.

### G.5 Anti-rules locked for v207

- **No new files under `agent/vov_2_0/`.** New code goes into the monolith notebook. Existing `vov_2_0/*.py` files are reference-only until removed.
- **No deferred fixes.** Every v206 root cause is addressed in v207 (§1a).
- **No commit until live success on all 3 businesses** (§1b).
- **No new deterministic guard that duplicates a SelfAuditor capability** (§3d DRY). If SelfAuditor can detect+fix it, don't also write a hard-coded rule for it.
- **No SelfAuditor LLM call through Spark Connect.** SelfAuditor uses the Phase 0 HTTP-direct path. Otherwise we re-introduce C3 in the audit layer.

---

# PART II — CURRENT CYCLE (v206 zero-shot v1→v2, started 2026-05-26)

> This part is **cycle-specific** and gets rewritten at the start of each cycle. The protocol in Part I is the contract; the sections below are the live state. When a new cycle starts, archive this whole Part II and rewrite for the new version.

## 1. What is currently being tested

A **zero-shot Value-Oriented-Vibe (VOV)** pass over three businesses, all reading the **v1 base model** and producing a **v2 model** in one shot. The agent runtime is the freshly deployed `dbx_vibe_modelling_agent_v206` notebook.

| Business | Catalog | Scope | Vibe source | Vibe length | Run ID |
|---|---|---|---|---|---|
| Healthcare | `healthcare_ecm_v1` | ECM | Google Doc (Muhammad Zahid review) | 16,755 chars | `616275845264216` (run #2 after scope-label fix; run #1 `980906059755192` FAILED at 06:55 — see §12) |
| Retail | `retail_mvm_v1` | MVM | Google Doc (Ruslan Dautkhanov critique) | 14,148 chars | `755132864379742` |
| gov_transport | `gov_transport_v1` | MVM | Original gov_transport base-model vibe doc | 21,781 chars | `700767918309955` |

The full vibe canvas the agent sees for each run =
1. `business_description` (1-paragraph industry overview from the submit JSON)
2. `model_vibes` (the Google Doc / gov_transport canonical content above)
3. `next_vibes.txt` (auto-generated by the v1 pipeline run, read from the volume by the VOV stage)

All three submits set `model_version="1"`, so the VOV reads `…/<biz>/<scope>_v1/model.json` from the volume and produces `…/<biz>/<scope>_v2/model.json`. **No serial iteration** (no v4→v5). **No additional user vibes** were typed into the submit — the user-curated input is the Google Doc plus the description paragraph.

---

## 2. What v206 fixes (and what it intentionally does NOT)

v206 closed two honest gaps from a self-audit of the deployed v205 archive:

| Gap | Fix | Verification grep |
|---|---|---|
| **GAP-1** — startup version print missing (user explicitly required it) | Added `print(...)` to stdout at `main()` entry **and** `logger.info(...)` to volume info.log right after `get_logger()` returns. Both emit `[v206-agent-version-startup-print FIRED] __AGENT_VERSION__=2.0.6 …`. | `grep "v206-agent-version-startup-print FIRED" tiny_info_v2_*.log` should return ≥1 hit per run |
| **GAP-3** — v205 constant falsely claimed "F5 mem/json canonicalize-on-write" but only shipped `_partial_credit=0.7` (symptom, not root cause) | Corrected the version-constant changelog to label F5 as **SYMPTOM (partial-credit)**, flagged canonicalize-on-write as defer-to-v207-only-if-F5-fires-live | `grep "_partial_credit" agent.ipynb` returns 2; `grep "SYMPTOM" agent.ipynb` ≥ 1 |

All v205 changes are retained verbatim in v206:

| v205 alias | Purpose | FIRED-emit sites in v206 deployed archive |
|---|---|---|
| `v204-verifier-stripped` | Sandbox auto-injects no-op verifier when LLM emits a stripped one | 1 |
| `v204-mv-preservation-invariant` | Reject mutator that drops MVs below the floor / <80% preservation | 2 |
| `v204-ast-class-retry-feedback` | Hint LLM with AST/violation classes on retry | 1 |
| `v204-pinned-domains-in-prompt` | Thread pinned domain set into synth prompt | 1 |
| `v205-schema-thread-through-tools-fallback` | F2 — forward `response_schema` to `complete_json` | 1 |
| `v205-final-cycle-purge` | F3 — deterministic post-pass removes any residual cycles | 1 |
| `v205-deterministic-overcount-trim` | F4 — trim ≤3 overage products instead of failing retry-3 | 1 |
| `v205-immutable-mutation-lock` | F6 — inject `ALL_MUTATIONS_FORBIDDEN` directive on architect IMMUTABLE-EARLY-EXIT fixation | 1 |

What v206 **does NOT** do (knowingly deferred):

- Real `canonicalize-on-write` root-cause fix for fidelity-gate precision drift. Deferred to v207 **iff** `Fidelity gates FAILED` appears in any v206 run's volume error log. If the partial-credit semi-fix proves sufficient, v207 leaves F5 as-is.

---

## 3. What to test (success criteria)

A run is **clean** only when **all** of the following hold at terminal state. This is the CLAUDE.md §10.6 zero-error contract.

### 3.1 Pipeline-level (per run)

- `state.life_cycle_state == "TERMINATED"`
- `state.result_state == "SUCCESS"`
- 0 lines matching `ERROR` in any volume error log
- 0 §10.6 hard-signature hits (see §4 below)
- All §9.5 positive signals firing where applicable

### 3.2 Model-level (per produced v2)

Apply CLAUDE.md §9 model-level validation methodology to each produced `model.json`:

- **§3b widget-domain compliance**: every name in `business_domains` widget appears verbatim in `[d['name'] for d in domains]`. gov_transport alone uses this widget here (`hr, project`), so HC + RT are §3b-vacuous.
- **§3c vibe-count compliance**: against any "exactly N" / "~N" / "intentionally tiny" phrase in `model_vibes`. None of the three current vibes hard-pin counts — checks are advisory only.
- **Structural integrity** (per §9.3.3):
  - `[CYCLE DETECTION]` = `✅ No cycles detected`
  - `[BIDIRECTIONAL DETECTION]` = `✅ No direct bidirectional links found`
  - 0 `SILOED TABLES DETECTED` lines (graph integrity)
  - 0 self-FKs on PKs (grep `model.json` for `"foreign_key_to": "<dom>.<prod>.<same_pk>"`)
  - 0 `[SA:denormalized_natural_key]` findings
  - `Fidelity gates FAILED` count = 0  *(v206 still uses partial-credit semi-fix — real test of GAP-3 deferral)*
- **Per-domain breakdown** (per §9.3.4): flag a domain with >2× the FK count of any other, isolated subgraphs, FK-out > attr count.
- **Quality score** parsed from `vibes/next_vibes.txt` should be ≥70/100 for an honest pass.

### 3.3 Vibe-adherence (the user-curated test of zero-shot)

For each business, count how much of the user's vibe content propagated into the v2 model:

1. Identify named entities in the Google Doc (tables, columns, domains, relationships, constraints, anti-patterns called out by the reviewer).
2. Cross-reference against `v2/model.json`. For each identified entity, mark **applied**, **partially applied**, **dropped silently**, or **explicitly skipped**.
3. Compute adherence percentage: `(applied + 0.5×partial) / total`. ≥80% is the bar.
4. Soft-accept lines (`Max retries (3) exhausted, proceeding with last response`) **never** count as applied — they're silent drops per §9.4 F2/R7.

### 3.4 v206-specific: agent-version proof

The PRIMARY purpose of the v206 bump was the user's request to **prove the right notebook is loaded**. Verification at pulse #2 (and every subsequent pulse) must show:

```
[v206-agent-version-startup-print FIRED] __AGENT_VERSION__=2.0.6 business=<Biz> catalog=<cat> operation=vibe modeling of version alias=v206-agent-version-startup-print
```

Count must be **≥1 per business** in `tiny_info_v2_*.log`. If any business shows 0, v206 was not loaded → root cause investigation kicks in immediately (likely workspace eventual-consistency or a cached notebook in the executor pool).

---

## 4. §10.6 hard-signature watchlist (the watcher counts these every 15 min)

These are the patterns that, if ANY non-zero, mean the run is broken even if it eventually reaches `result_state=SUCCESS`. The watcher emits a one-line summary per business per pulse.

| Code | grep pattern | Class |
|---|---|---|
| F1 | `Permission denied` or `[Errno 13]` on `/tmp/` | Serverless `/tmp` anti-pattern |
| F2 / R7 | `Max retries (3) exhausted` | Soft-accept silent drop |
| F4 | `SILOED TABLES DETECTED` | Graph integrity |
| F6 | `KeyError '0,62'` | Prompt template format-string bug |
| R6 | `Failed metric view.*UNRESOLVED` | Metric-view ↔ normalizer contract mismatch |
| R8 | `Found [1-9]\d*\s*cycle\(s\)` | FK cycle recurrence |
| N2 | `Fidelity gates FAILED` | Memory/JSON attribute-name drift (F5 partial-credit gates this) |
| — | `NameError\|AttributeError\|TypeError` | Generic Python crash |
| — | `Traceback (most recent` | Generic Python traceback |

The watcher's per-pulse output format:

```
[<BIZ> <RUN_ID>] life=<LIFE> result=<RESULT>
  v206 startup-print FIRED: <N>  (proves _v206 archive loaded)
  ALL FIRED markers      : <N>
  §10.6: F1=<n> F2=<n> F4=<n> R6=<n> R8=<n> N2=<n> NameErr=<n> TB=<n>
  [v206-agent-version-startup-print FIRED] __AGENT_VERSION__=...   ← actual log line
  ---last 5 info---
  <tail -5 of the info log>
```

---

## 5. The watcher — how it works, what it watches

### 5.1 Location and process

| Item | Value |
|---|---|
| Script | `/tmp/v200/v206_with_vibes_watcher.sh` |
| Output stream | Cursor-visible background shell (`block_until_ms: 0`); writes pulses to stdout, captured by Cursor for UI display |
| Process | `bash /tmp/v200/v206_with_vibes_watcher.sh`, pid recorded in the Cursor terminal file under `/Users/user/.cursor/projects/Users-user-Documents-projects-vibe-modelling-agent/terminals/` |
| Pulse interval | 900s (15 min) |
| Log mirror dir | `/tmp/v200/v206_with_vibes_logs/<BIZ>__<filename>` |
| Auto-exit | When all 3 runs reach `TERMINATED`, `INTERNAL_ERROR`, or `SKIPPED` |
| Bash compatibility | Plain bash 3 (macOS default); does **not** use `declare -A` (associative arrays) — was a real bug from a prior watcher version |

### 5.2 Per-pulse loop (what each pulse actually does)

For each of the 3 runs:

1. Calls `databricks jobs get-run <rid> -o json` and extracts `life_cycle_state` + `result_state` via inline python.
2. Mirrors every file in `dbfs:/Volumes/<cat>/_metamodel/vol_root/logs/<folder>/<scope>_v2/` to the local mirror dir, overwriting on every pulse.
3. Concatenates the info and error logs and counts the §10.6 hard signatures (see table in §4).
4. Greps explicitly for the v206 startup-print FIRED line and reports the count plus the literal line if present (proof of correct notebook version).
5. Appends the last 5 info-log lines as context.

If `ALL_DONE=1` (all 3 terminated), prints the closing banner and exits 0. Otherwise sleeps 900s and repeats.

### 5.3 Reading the pulses

- **Pulse #1 always has empty log fields** — runs just started; the volume log files don't exist yet. Look only at `life=RUNNING` to confirm submission worked.
- **Pulse #2 (~15 min in) should show**:
  - `v206 startup-print FIRED: ≥1` per business (otherwise → notebook version not loaded; halt and investigate)
  - First 100-200 lines of info log mirrored
  - Maybe a few early warnings — these are normal during step initialization
- **Pulses #3-N**: monitor §10.6 row. Any non-zero number triggers root-cause investigation (see §6 self-healing).
- **Final pulse**: prints `ALL 3 RUNS TERMINATED` and exits. This is when the §9 audit kicks in.

### 5.4 What the watcher does NOT do

- It does **not** kill runs early. If a run is on a failure trajectory, the human (or §6 self-healing decision logic) does the cancel.
- It does **not** modify code. It's read-only.
- It does **not** trigger the §9 model-quality audit automatically. That's a post-terminate step.
- It does **not** post to Slack / email / anywhere external. All output is local stdout.

---

## 6. Self-healing loop (the autonomous fix-and-redeploy cycle)

This is the canonical CLAUDE.md §10.2 loop in its current applied form for the v206 cycle. The loop fires when the watcher (or a post-terminate audit) surfaces an issue.

### 6.1 Trigger conditions

A self-heal cycle starts when **any** of the following is true:

1. Any §10.6 hard signature shows ≥1 hit in any business's logs.
2. `agent_version` mismatch — startup-print FIRED count = 0 in any business after ~5 min.
3. A run terminates with `result_state != SUCCESS`.
4. Post-terminate §9 audit finds a structural defect, vibe-adherence < 80%, or quality score < 70.
5. Self-audit of the deployed archive finds a gap (e.g., missing FIRED log for an alias, version-constant claim mismatch).

### 6.2 The 13-step loop (applied to v205 → v206 this morning)

For each surfaced issue:

1. **Root-cause classify** — class per §9.4 + §10.6 (F1, F2, R6, R8, N2, etc.) or as a meta-issue (audit-trail gap, version-print missing, plan-vs-shipped mismatch).
2. **Search-first, reuse-first per §3d** — grep the codebase for any existing helper / prompt / validator that solves it before writing new code.
3. **Apply fix on disk** in `agent/dbx_vibe_modelling_agent.ipynb` (single-cell mega-notebook). Every fix carries a `[<alias> FIRED]` log line at the fire site (§8.4 — no zero-caller helpers).
4. **Bump `__AGENT_VERSION__`** to next single-digit semver (e.g., 2.0.5 → 2.0.6). Update the comment on the constant to describe what changed.
5. **Write or extend a behavioral test** in `tests/unit-tests/test_v<NN>_behavioral.py`. Test must:
   - Fail on the previous version
   - Pass on the new version
   - Cover both code-shape (static grep) and runtime behavior where the bug was observable
6. **Run the full v<NN-1> + v<NN> regression** with `pytest tests/unit-tests/test_v<NN-1>_behavioral.py tests/unit-tests/test_v<NN>_behavioral.py`. If a prior test asserts version equality, relax it to `>=` so the bump doesn't break it.
7. **Deploy to versioned path** — `databricks workspace import "$WS/dbx_vibe_modelling_agent_v<NN>" --file <local> --format JUPYTER --overwrite`. NEVER deploy to canon path (executor pool caches it).
8. **Verify deployed archive** — `databricks workspace export "$WS/dbx_vibe_modelling_agent_v<NN>"` then grep for the new aliases. Each must return ≥1. If any returns 0, retry deploy after 10s (workspace eventual-consistency).
9. **Cancel in-flight runs** of the prior version (parallel: `databricks jobs cancel-run <rid>` for each).
10. **Build new submit JSONs** that point at the new `_v<NN>` path. Preserve all `base_parameters` from the prior submit, especially `model_vibes` (this morning's bug: stripping `model_vibes` to `""` thinking "zero-shot" — wrong).
11. **Submit with `--no-wait`** to avoid blocking the CLI. Capture each new `run_id` to `/tmp/v200/<BIZ>_v<NN>_with_vibes_run_id.txt`.
12. **Kill the prior watcher** and **start a new watcher** that knows the new run IDs.
13. **Pulse-monitor until terminate**, then run the §9 audit. If audit fails, loop back to step 1.

### 6.3 Hard rules (CLAUDE.md §1b)

- **NO commit until success-verified.** Every change made this morning is **uncommitted** in the working tree. The git history only gets a commit when the v206 runs terminate with `SUCCESS` + adherence audit passes.
- **NO push to remote** until commit is verified.
- **Local pytest passing is necessary but not sufficient** — live runs are the only proof.

### 6.4 Anti-shortcuts followed this morning

- Did NOT deploy to canon path `agent/dbx_vibe_modelling_agent`. Always `_v205` then `_v206`.
- Did NOT submit without `--no-wait` (an earlier mistake caused a stuck CLI; killed pid 83033).
- Did NOT submit before cancelling prior runs and verifying the JOB notebook_path.
- Did NOT skip the deployed-archive grep step.
- Did NOT defer GAP-1 (startup version print) — shipped in the same bump.
- DID honestly defer the F5 root-cause canonicalize-on-write fix, with explicit framing in the v206 version constant and an explicit trigger condition for v207.

---

## 7. Artifact layout (where to find everything)

### 7.1 Local artifacts (this laptop)

| Path | Purpose |
|---|---|
| `/tmp/v200/submit_<BIZ>_v206_with_vibes.json` | Submit JSON for each business |
| `/tmp/v200/<BIZ>_v206_with_vibes_run_id.txt` | One run_id per file |
| `/tmp/v200/v206_with_vibes_watcher.sh` | The watcher script |
| `/tmp/v200/v206_with_vibes_logs/<BIZ>__*.log` | Mirrored volume logs, updated every pulse |
| `/tmp/v200/v206_deployed_check.ipynb` | Exported copy of the deployed v206 archive (for offline grep verification) |
| `/tmp/v200/vibe_doc_HC_text.md` | Markdown extract of the HC Google Doc (Muhammad Zahid review) — used as `model_vibes` |
| `/tmp/v200/vibe_doc_RT_text.md` | Markdown extract of the RT Google Doc (Ruslan Dautkhanov critique) — used as `model_vibes` |
| `/tmp/v200/vibe_doc_HC_raw.json` / `_RT_raw.json` | Raw Google Docs API responses (in case extraction needs to be redone) |

### 7.2 Databricks workspace artifacts

| Path | Purpose |
|---|---|
| `/Users/user@example.com/dbx_vibe_modelling_agent_v206` | The notebook the JOB loads. Unique `object_id` proves the version. |
| `/Volumes/healthcare_ecm_v1/_metamodel/vol_root/business/Healthcare/ecm_v1/model.json` | HC v1 input (read by VOV) |
| `/Volumes/healthcare_ecm_v1/_metamodel/vol_root/business/Healthcare/ecm_v2/model.json` | HC v2 output (written by VOV) |
| `/Volumes/healthcare_ecm_v1/_metamodel/vol_root/logs/Healthcare/ecm_v2/tiny_info_v2_ecm.log` | HC info log (the watcher mirrors this) |
| `/Volumes/healthcare_ecm_v1/_metamodel/vol_root/logs/Healthcare/ecm_v2/tiny_error_v2_ecm.log` | HC error log |
| (same pattern for `retail_mvm_v1/Retail/mvm_v2/...` and `gov_transport_v1/gov_transport/mvm_v2/...`) | RT + gov_transport analogues |

### 7.3 Local test artifacts

| Path | Purpose |
|---|---|
| `tests/unit-tests/test_v205_behavioral.py` | v205 fix-set behavioral tests (9 tests, all pass; v205_version_bumped relaxed to `>=2.0.5`) |
| `tests/unit-tests/test_v206_behavioral.py` | v206 fix-set behavioral tests (8 tests, all pass) |
| `tests/readme.md` | The general test-suite reference (not run-specific) |
| `tests/test.md` | **This file** — current-cycle live state, watcher, self-healing |

---

## 8. Post-terminate audit recipe (kicks in when all 3 runs end)

Triggered automatically by the watcher when it prints `ALL 3 RUNS TERMINATED`. Steps for each business:

1. **Mirror the final logs and model artifacts** to a stable archive dir (`/tmp/v206_<BIZ>_logs/`), separate from the live-pulse mirror.
2. **Run the §10.6 zero-error Python regex audit** (see CLAUDE.md §10.11.2 step 13). All rows must be 0; any non-zero starts a v207 cycle.
3. **Pull `model.json` and `next_vibes.txt`** from the v2 volume for each business.
4. **Compute counts** per §9.3.1 (domains, products, attributes, FKs, MVs) — `model['model']['domains']` is the nested path.
5. **§3b / §3c compliance check** — only gov_transport has a widget-pinned domain list (`hr, project`).
6. **Structural integrity check** — cycles, bidirectionals, silos, self-FKs, SSOT, fidelity gates.
7. **Metric-view parity** — `len(model.metric_views)` vs `information_schema.tables WHERE table_schema = '_metrics'`.
8. **Vibe-adherence audit** — for each Google Doc, identify named entities, cross-reference v2 model, compute adherence %.
9. **Honest 0–100 quality score per sub-version**, with each deduction tied to a §8.1 invariant or §9.4 signature.
10. **Write two reports** to `/Users/user/claude/vibe-agent/v206-<run_tag>-{validation-report,model-quality-audit}.md` per §9.6.
11. **If audit passes** (all §10.6 zero, adherence ≥80%, score ≥70): commit v206 to git per §1b ("no commit until success-verified") with the commit message citing the live run IDs as proof.
12. **If audit fails**: identify root causes, group by class, prep v207 fix list, start the self-healing loop (§6) again.

---

## 9. Things to actively look for in the v206 pulse log

These are the leading indicators that decide whether v206 holds up or whether v207 is already needed.

### 9.1 Things that must show (positive signals)

- `v206 startup-print FIRED: 1` per business by pulse #2 (proves correct notebook is loaded).
- `FIRED` count growing each pulse — proves alias-tagged fixes are firing live, not dead code.
- `[VALIDATOR] User vibes detected (N chars) — count limits will be relaxed` — proves §3c authority firing.
- `USER-KING AUTHORITY` references in any LLM prompt log.
- `[CYCLE DETECTION] ✅ No cycles detected` at finalize stage.
- `Architect Self-Review iter N landed=K regressed=0 blocked=0` — clean corrective iteration.

### 9.2 Things that must NOT show (regression signals)

- `Max retries (3) exhausted, proceeding with last response despite validation errors` — any hit means F2 returned. Likely from a synth call that's still not properly schema-threaded. If recurrent, F2 fix is incomplete; v207 needs more call-site coverage.
- `Fidelity gates FAILED: precision < 0.85 — rollback recommended` — F5 partial-credit semi-fix was insufficient; v207 must ship the real `canonicalize-on-write` fix.
- `[CYCLE DETECTION] Found N cycle(s)` where N > 0 at finalize stage — F3 deterministic purge didn't run or didn't catch this case. Investigate the cycle path.
- `SILOED TABLES DETECTED` — F4 trim helped but didn't prevent the silo; investigate the dropped product.
- `[v205-immutable-mutation-lock FIRED]` appearing in a tight loop — F6 lock fired but architect still loops; v207 needs harder cutoff.
- Empty log file at terminate — log truncation R3 regression; rare but seen historically.

### 9.3 Things that are advisory only (not pulse blockers)

- `[v205-deterministic-overcount-trim FIRED]` — informational; F4 is working as designed.
- `[v205-final-cycle-purge FIRED]` — informational; F3 is working as designed (removing residual cycles deterministically).
- `[NORM-FIX] BLOCKED semantic mismatch` — defensive guard firing correctly; not a bug.

---

## 10. Decision tree at the next user ping

When the user pings next, the response strategy depends on the watcher state:

| Watcher state | Pulses since start | Recommended report |
|---|---|---|
| All RUNNING, no anomalies | 1-3 | "Pulse #N — all green, log lines visible, startup-print FIRED confirmed in HC=K RT=K NC=K." |
| All RUNNING, some §10.6 hits | any | "Pulse #N — `<signature>` detected in `<biz>` at line `<N>`. Root cause likely `<class>`. Decision: cancel + v207 OR let finish and v207 cycle. Recommend `<X>`." |
| 1-2 TERMINATED, others RUNNING | any | "Partial terminate. Quick §9 spot-check on terminated runs; full audit deferred until all 3 finish." |
| All TERMINATED | any | "Final pulse. Running §9 audit now. Reports will land at `/Users/user/claude/vibe-agent/v206-…-{validation,audit}.md`. Decision: commit v206 OR open v207 cycle." |
| Watcher exited unexpectedly | n/a | "Watcher pid gone; investigate. Live pulling logs manually." |

---

## 11. Brutal honesty about this document

- (-) The §9 audit logic in §8 above is described but not yet automated; the actual audit will be hand-run when the runs terminate. A truly self-healing pipeline would automate this — that's a v208+ scope.
- (-) The "agent_version mismatch → immediate halt" trigger in §6.1 #2 is descriptive only; the watcher currently REPORTS the count but does NOT auto-cancel runs when count=0. Human decision required.
- (-) The "post-terminate audit recipe" §8 doesn't write reports automatically yet — that's a manual step at next ping.
- (-) The vibe-adherence audit §3.3 / §8 step 8 is the hardest part and is currently un-automated. The Google Docs are >14K chars each; manual entity extraction is laborious. This is the single biggest hole in the test-cycle automation.
- (+) The watcher itself is solid and observable; pulse #1 already proved it runs cleanly.
- (+) Every fix in v206 has both a static-grep test AND a behavioral test (where applicable). No tautology fixes per CLAUDE.md §8.3.

Update this file at the next user ping with concrete pulse data and any v207 plans.

---

## 12. Live incident log (events between the doc being written and the next user ping)

### 12.1 (06:54 BST) Autonomous wake-up hook added

User asked "are you going to wake up every 15m and check progress and fix any issues?" — answer is now yes. Killed the old watcher (pid `90081`) and restarted it as a new background shell (pid `91268`, terminal id `261004`) **with `notify_on_output` attached**. The notify pattern matches:

- `PULSE #\d+ @` — every pulse header → I wake at every 15-min cadence
- `ALL 3 RUNS TERMINATED` — final terminate banner → I wake when audit is due
- `FIRED: 0  (proves _v206 archive loaded)` — startup-print absent → wrong notebook loaded
- `F[12468]=[1-9]` / `R[68]=[1-9]` / `N2=[1-9]` — any §10.6 hard signature crossing zero
- `NameErr=[1-9]` / `TB=[1-9]` / `Traceback` — generic Python crash
- `life=INTERNAL_ERROR` / `life=TERMINATED result=FAILED` — any run failed

`debounce_ms = 850000` (just under 15 min) — at most one notification per pulse, prevents spam.

When a notification fires, I enter the §6 self-healing loop: triage → root-cause → fix → bump → deploy → cancel → resubmit → restart watcher.

### 12.2 (06:55 BST) HC v206 run #1 failed at setup — submit-JSON bug, not agent bug

**Symptom:** HC run `980906059755192` reached `INTERNAL_ERROR/FAILED` ~62s after start with:
```
ValueError: Version '1' with model_scope 'mvm' does not exist for business 'Healthcare'.
```

**Root cause:** My v206 HC submit JSON had `data_model_scopes = "Enterprise Conceptual Model - ECM"`. The agent's normalizer at Cell-21 line 36553 only recognises `"expanded coverage model - ecm"`, `"expanded coverage model"`, and `"ecm"` for the ECM scope. The "Enterprise…" wording wasn't in the variant list, so the normalizer fell through to the default `"minimum viable model - mvm"`, logged a `print()` warning **to stdout only (no logger yet — pre-init)**, and then `_version_exists` looked for `mvm_v1` which doesn't exist for Healthcare → ValueError.

**Why I missed it:**
1. Visual confirmation bias — "Enterprise Conceptual Model" sounds plausible enough as an ECM label, so my eye glossed over the wrong word.
2. The agent's print-only warning never lands in the volume log, so a post-facto audit wouldn't find it without scanning the Databricks run output JSON.
3. The v204 HC submit (which I cloned conceptually but typed from memory) had the correct `"Expanded Coverage Model - ECM"` — I made a fresh typo, not a regression.

**Fix:** corrected `submit_HC_v206_with_vibes.json` to `"Expanded Coverage Model - ECM"` and resubmitted. New HC run_id = `616275845264216`, status RUNNING as of 06:58 BST.

**Why no agent code change:** the agent's behaviour (silent fallback + stdout warning) is debatable but not a regression — it's been there since at least v0.7. A proper v207 hardening would either (a) RAISE on unknown label rather than silent-fallback, or (b) duplicate the warning to volume info.log after `get_logger()` returns. Logged here for v207 consideration; not blocking this cycle.

**Verification:** the new submit JSON shows `data_model_scopes = 'Expanded Coverage Model - ECM'` (matches v204's working value verbatim), and Healthcare's `/Volumes/healthcare_ecm_v1/_metamodel/vol_root/business/healthcare/ecm_v1/model.json` exists (lowercase folder, agent handles case-folding internally).

### 12.3 Open v207 candidate findings (deferred unless triggered)

| Finding | Class | Trigger to ship in v207 |
|---|---|---|
| F5 mem/json canonicalize-on-write (real root-cause) | §3 root-cause-vs-symptom | Any `Fidelity gates FAILED` line in v206 run logs |
| Agent's silent MVM-fallback on unknown `data_model_scopes` label | §8.10 observability + §3 root-cause | If this bug ever resurfaces in any future submit |
| §9 audit recipe (§8 of this doc) → callable Python module | Automation gap | Independent of v206 outcome; quality-of-life |
| Vibe-adherence cross-reference (Google Doc entities → v2 model entities) | Automation gap | Independent of v206 outcome; biggest manual lift |

### 12.4 Watcher state at write-time (06:59 BST)

| Item | Value |
|---|---|
| Watcher pid | `91268` |
| Watcher uptime | ~30s |
| Pulse #1 status | All 3 RUNNING, no logs on volume yet (expected at run start) |
| Next pulse | ~07:13 BST |
| Notification target | Every pulse OR any §10.6 / terminate / FAILED event |
| Auto-exit | When all 3 reach TERMINATED/INTERNAL_ERROR/SKIPPED |

If you ping me before pulse #2, I'll do an inline live status pull. If pulse #2 fires first, the notify hook wakes me automatically and I'll triage anything that needs triaging before reporting back.

### 12.5 (07:13 BST) Pulse #2 of cycle-1 — watcher folder-case bug discovered

**Pulse #2 said "no logs on volume yet" for all 3 runs, which was a lie.** Direct ls of the volume showed HC was 1h+ into the pipeline and had been writing logs the entire time. Root cause: cycle-1 watcher had `FOLDERS=( Healthcare Retail gov_transport )` (capitalized) but the agent writes to `healthcare/`, `retail/`, `gov_transport/` (lowercase). gov_transport happened to match; HC and RT were silently missed.

**Direct check of HC's log at pulse #2 time confirmed:**
- `[v206-agent-version-startup-print FIRED] __AGENT_VERSION__=2.0.6` present (v206 fix works)
- §10.6 ALL ZERO (ERROR=0, F1-F6=0, R6-R8=0, N2=0, Traceback=0)
- HC was in ensemble-domain-generation stage (gpt-oss-120b 19 domains, claude-sonnet-4-5 18 domains)

Watcher script fixed: `FOLDERS=( healthcare retail gov_transport )`.

### 12.6 (07:48 BST) v5 numbering discovered → cycle-2 cleanup + resubmit

**Discovery:** RT + gov_transport `_metamodel.business` still had rows for v2/v3/v4/v5 from prior sessions (my earlier "cleanup" only deleted Databricks job runs and a subset of model.json folders, not the SQL registry). The agent's VOV correctly used v1 as the source (true zero-shot semantics) but wrote the output to v5 (next available integer in the registry sequence) instead of v2.

**HC was clean** — its registry had only v1 → wrote to v2 → matches user request literally.

**User decision:** kill RT + gov_transport, drop the leftover registry rows + folders, resubmit pure v1→v2.

**Cleanup performed:**
- SQL: `DELETE FROM {retail_mvm_v1,gov_transport_v1}._metamodel.{attribute,product,domain,business} WHERE version IN (2,3,4,5)` → 15655+418+30+4 rows from RT, 9104+233+6+4 from gov_transport. Post-cleanup: both catalogs have only `version=1` rows.
- Volume: `databricks fs rm --recursive` on `business/{retail,gov_transport}/mvm_v5` and `logs/{retail,gov_transport}/mvm_v5`. Post-cleanup: only `mvm_v1` folders remain in each.
- `_vibe_progress` table left alone (session_id-keyed, version-agnostic, harmless).

**Resubmit (07:55 BST):**
- HC: 616275845264216 (UNCHANGED — already clean v1→v2)
- RT new: 311271123062720 (clean v1→v2 zero-shot, 14148-char Google-Doc vibes)
- gov_transport new: 985321305623237 (clean v1→v2 zero-shot, 21781-char Google-Doc vibes)

### 12.7 (07:56 BST) Cycle-2 watcher restarted with corrected folder case + new run IDs

Old watcher (pid 91268) killed. New cycle-2 watcher started (terminal id `805038`) reading the corrected `FOLDERS=( healthcare retail gov_transport )`. Same notify hook for autonomous wake-up.

**Cycle-2 Pulse #1 (07:56 BST):**
- HC: `v206 startup-print FIRED: 1`, `ALL FIRED markers: 116`, `§10.6: F1=0 F2=0 F4=0 R6=0 R8=0 N2=0 NameErr=0 TB=0`. Deep in attribute generation (12-16 of 430 patient attributes done). ~2h into run.
- RT: RUNNING, no logs yet (~2 min in).
- gov_transport: RUNNING, no logs yet (~2 min in).

Next pulse ~08:11 BST. Notify hook armed for every pulse + any §10.6 / terminate / FAILED event.

### 12.8 (08:57 BST) Pulse #5 — RT verifier-LLM transient SparkExceptions degraded one metric view

**Watcher said RT clean. Direct grep showed it isn't.** RT error log grew +10KB between pulse #4 and pulse #5. Inspection found:

- 7 lines containing literal `ERROR` token (all inside WARNING-tagged retry telemetry like `[verifier-llm-fallback-call-fix ERROR] VREQ-002: _call_ai_query raised SparkException: Job aborted due to stage failure: org.apache.spark...`)
- 2 verifier checks (VREQ-002, VREQ-019) burned through 3 primary retries + 3 rescue retries, then downgraded to WARNING per design
- 7 measures (`total_supplier_item_relationships`, `distinct_suppliers`, `avg_list_price`, `avg_cost_vs_list_discount_pct`, `avg_gross_weight_kg`, `preferred_supplier_coverage_pct`, `multi_sourced_item_pct`) DROPPED from `metrics_supplier_item` MV via `mv-cross-table-measure-drop FIRED`
- 6 dimensions (`is_preferred_supplier`, `cost_currency_code`, `sourcing_type`, `supplier_item_type`, `effective_start_date`, `supplier_item_id`?) SKIPPED in the same MV
- 3 orphan attributes excluded from export

**Why the watcher missed it:**

Watcher script greps for §9.4 known signatures only (F1=Permission denied, F2=Max retries (3) exhausted, F4=SILOED, R6=`Failed metric view.*UNRESOLVED`, R8=cycles, N2=Fidelity gates FAILED, NameError/AttributeError/TypeError, Traceback). It does NOT grep for the bare `\bERROR\b` token in error files, which §10.6 explicitly says is a zero-tolerance criterion. **Watcher §10.6 contract gap — needs fixing in v207 watcher.**

**§10.6 contract verdict:**

- TECHNICALLY PASSED — no `Failed metric view.*UNRESOLVED` literal (R6 uses a different code path), no `Max retries (3) exhausted` literal (F2 is a different alias), no Traceback, no Python crash class.
- REAL-WORLD DEGRADED — `metrics_supplier_item` MV will ship missing 7 of N measures. This is a §9.4 R6-class symptom (metric view content degradation) even though the exact R6 regex doesn't fire.

**Root cause:** Spark serverless platform transient (`Job aborted due to stage failure: org.apache.spark...`). Agent's defensive retry worked as designed (3+3 attempts with exponential backoff 1s/3s/7s). Not an agent code bug. NOT fixable in v207 agent code — would need either a Databricks platform workaround or a re-architecture of the verifier to be Spark-free.

**v207 candidate added** to §12.3:

| Watcher §10.6 contract gap — add `\bERROR\b` literal grep on error file | §11 burning-scar / pulse-discipline | Trigger: every run from v207 onward |

**Other runs:**
- HC: 192/430 → 207/430 attrs complete, rate now ~44 attrs/15min (up from ~16 early in the run as the LLM warmed up). Revised terminate ETA ~10:30 BST.
- gov_transport: 41/78 → 57/78 products attribute-complete. Healthy throughout (attempt-1 validation passing). Terminate ETA ~09:40 BST.

### 12.9 (09:15 BST) Hardened watcher mid-stream — closing the §10.6 deep-pattern gap

After pulse #6 surfaced that the watcher was reporting "all zeros" while RT had 79+ literal ERROR tokens, 122 SparkExceptions, and 11 dropped metric-view measures, the right call was to fix the watcher live (deferring to v207 was wrong; the remaining ~5+ pulses would have stayed blind).

**Watcher patch (`/tmp/v200/v206_with_vibes_watcher.sh`):**
- Replaced fragile `grep -c | bash arithmetic` chain with a single Python block that reads info/error files once, counts all patterns, prints to stdout cleanly. Fixes the broken multi-line `F1=0\n0 F2=0\n0 ...` display.
- New `§10.6 (deep)` line: `ERROR=N WARNING=N VFAIL=N SPARK=N REJECTED=N MVDROP=N` covering counts the original 8-pattern grep missed.
- `ANNOTATIONS:` block translates raw deep counts into verdicts (`REJECTED=positive`, `SPARK=concern if growing`, `MVDROP=real model degradation`).
- `tail -5` now `grep -v VolumeLogFlush | tail -5` — strips watcher-emitted flush metadata so real stage-progress lines stay visible.

**Restart:** killed old watcher (pid 98212), restarted hardened version in new terminal (pid 7408).

**Smoke test:** ran one pulse manually before backgrounding — confirmed counts match a parallel python deep-scan (HC ERROR=1 WARN=72; RT ERROR=108 WARN=167 SPARK=168 MVDROP=11; gov_transport ERROR=1 WARN=73 REJECTED=25).

**Notify hook extended** to wake me on `MVDROP≥20`, `SPARK≥300`, `ERROR≥300` in addition to the original §10.6 patterns. Honest caveat: these are absolute-count thresholds, not growth-rate thresholds — if RT plateaus at SPARK=250 (still bad) the hook won't wake. Imperfect; will tune at terminate.

**Confirmed at watcher-restart time:**
- HC: ERROR=1 WARN=72 VFAIL=4 SPARK=0 REJECTED=5 MVDROP=0 — all REJECTED/VFAIL are §3b/§3c USER-KING-AUTHORITY guards firing (LLM tried to add `behavioral_health`, `clinical_ai`, `digital_health` domains; tried to rename/split protected products; tried product names >30 chars). All blocked correctly. **Clean.**
- RT: ERROR=108 WARN=167 VFAIL=3 SPARK=168 REJECTED=1 MVDROP=11. SparkException count growing steadily across last 3 deep scans (122 → 160 → 168). 11 measures + ~6 dimensions dropped from `metrics_supplier_item` MV. **Platform-induced degradation; not fixable in agent code.**
- gov_transport: ERROR=1 WARN=73 VFAIL=1 SPARK=0 REJECTED=25 MVDROP=0 — REJECTED=25 is the user-pinned-domain guard rejecting 25 LLM attempts to drop `hr` and `project`. **Healthy; nearly through attribute generation (75/78).**

### 12.10 (09:30 BST) RT TERMINATED — SUCCESS at the pipeline level, DEGRADED per §9 audit

**Run metadata:** `run_id=<run_id>`, life=TERMINATED, result=SUCCESS, duration=84.2 min.

**§10.6 hard signatures: 7/8 PASS, 1/8 FAIL.** `N2=1` — `Fidelity gates FAILED: precision 0.6667 < required 0.85 — rollback recommended`. This fired AFTER the VREQ-018 SparkException retry-rescue exhaustion at 08:16:29. The fidelity gate computes how many model.json attributes the verifier could confirm against the physical schema; 168 SparkExceptions in the verifier-LLM path prevented full verification → precision fell to 2/3 → gate triggered.

**model.json shape:**
- agent_version: 2.0.6 ✓ (proves the v206 fix and the canonical key are both honored)
- domains: 3 (customer, product, order) — matches v1 source verbatim ✓ (§3b PASS — user's source domains preserved)
- products: 26
- attributes: 962
- FKs: 63 — LOW, with 45+ unlinked-FK findings in next_vibes (`_id`-suffixed columns without `foreign_key_to`)
- metric_views: 22 declared / **18 effective** (4 prevalidate-dropped at 08:18:42 due to LLM emitting MV column refs the attribute generator never created)
- Model Quality Score (self-reported): **50/100**

**Real degradation analysis (4 root causes, separated):**

| # | Root cause | Class | Fixable in v207 agent code? |
|---|---|---|---|
| 1 | 168 SparkExceptions → fidelity gate verifier could only validate 2/3 attrs → precision 0.6667 → N2 fired | Platform transient (Databricks serverless) | **NO** — needs platform-side fix or Spark-free verifier rewrite (architectural, deferred) |
| 2 | 4 MVs dropped (`customer_merge_history`, `product_assortment`, `product_item_composition`, `order_discount`) reference columns LLM never emitted (`merge_surviving_profile_id`, `assortment_item_id`, `parent_item_id`, `applied_promotion_id`) | Agent code — MV generator + attribute generator are misaligned | **YES** — v207 candidate `mv-attribute-coherence-gate` |
| 3 | 45+ unlinked-FK findings — `_id`-suffixed columns (e.g. `order.discount.promotion_id`, `customer.account.tax_id`, `order.payment.processor_transaction_id`) lack `foreign_key_to` | Agent code — FK inference too conservative; doesn't propose targets for plausible `<entity>_id` patterns | **YES** — v207 candidate `fk-infer-from-suffix-pattern` |
| 4 | 2 attr groups with no matching product (`order.order_header`, `order.order_line`) — naming inconsistency between MV spec (`order.order_header`) and product spec (`order.header`) | Agent code — name canonicalisation gap | **YES** — v207 candidate `mv-name-canonicalize-against-product-registry` |

**Per §9.8 anti-rule: TERMINATED=SUCCESS does NOT mean PASS the audit.** RT is the textbook example. The pipeline self-reported success because no exception bubbled up; the model artefact is real-world degraded.

**Per §1a NO VERSIONING ROADMAP rule + user's "do not settle":** RT must be retried in v207 with the agent-side root causes fixed. The platform-transient (root cause #1) gets a mitigation (longer retry budget) but the real fixes are #2/#3/#4.

**Holding pattern for now:** HC and gov_transport are still RUNNING. Once both terminate, I'll do the same audit for each, then plan v207 scope and resubmit whichever runs need it. If HC/gov_transport also show §10.6 violations, v207 fixes the union of all three sets.

### 12.10.1 (09:32 BST) RT MV degradation budget (computed against model.json + error log)

Counted from `/tmp/v200/RT_terminate/model.json` (each MV row has `measures_count` + `dimensions_count`) cross-referenced with error-log drops:

| Phase | MVs lost | Measures lost | Dimensions lost | % of intent |
|---|---|---|---|---|
| MV-column prevalidate (post-DDL schema check) | 4 of 22 (`customer_merge_history`, `order_discount`, `product_assortment`, `product_item_composition`) | counts unknown — MV dropped entirely | counts unknown | **18.2%** of declared MVs gone |
| Cross-table verifier (SparkException-driven) on surviving MVs | 0 | 11 (across 2 MVs: `metrics_supplier_item` -7, `shipment_on_time_delivery` -4) | 7 (across same 2 MVs: -6, -1) | **7.1%** measures, **3.6%** dimensions, on the 18 surviving MVs |

**Worst-affected single MV:** `product_supplier_item` (named `metrics_supplier_item` in error logs) ended with **1 measure / 2 dimensions** in the final model.json — the cross-table-measure-drop wiped out 7 of 8 intended measures and 6 of 8 intended dimensions. **~88% of that single MV's content is gone.** This is the MV that consumers will hit first when querying supplier-item KPIs and they will see a near-empty result.

**Overall RT MV budget verdict:** Effective output is **18 MVs × 144 measures + 187 dimensions** (against intent of 22+ MVs and ~155 measures + ~194 dimensions). **Net usable retention ~82% of MV count, ~93% of measures on retained MVs, ~96% of dimensions on retained MVs.** Most of the damage is concentrated in 1 MV that has now lost its analytical value.

This data feeds the v207 candidate `mv-attribute-coherence-gate` (root cause #2 in §12.10) — the gate must REJECT MV drafts whose columns the attribute generator never emitted, instead of producing MVs that get prevalidate-dropped downstream.

### 12.10.2 (09:49 BST) RT root-cause #2 — CORRECTED: dropped MVs were NOT LLM hallucinations

Earlier in §12.10 I labeled root cause #2 as "MV generator + attribute generator misaligned — LLM emitted MV column refs the attribute generator never created." That diagnosis was WRONG. New evidence from `/tmp/v200/RT_dropped_mv_schema_diff.py` against `model.json`:

| Dropped MV | Expected column | Present in model.json `attributes`? | FK column? |
|---|---|---|---|
| `customer_merge_history` | `merge_surviving_profile_id` | YES (FK to customer.profile.profile_id) | YES |
| `order_discount` | `applied_promotion_id` | YES (alongside `promotion_id`) | NO (orphan `_id`) |
| `product_assortment` | `assortment_item_id` | YES (FK to product.item.item_id) | YES |
| `product_item_composition` | `parent_item_id` | YES (FK to product.item.item_id) | YES |

**All 4 columns DO exist in model.json `attributes`.** The MV synthesizer was correct. The drop reason is that the **physical Spark table** (queried by `[mv-column-prevalidate]` via `information_schema.columns` or `DESCRIBE TABLE`) is missing these columns — meaning the **DDL writer** (which renders model.json to `CREATE TABLE`) is dropping/renaming them at write time.

**Revised root-cause class (replaces §12.10 row 2):**

| # (revised) | Root cause | Class | Fixable in v207? |
|---|---|---|---|
| 2a | DDL writer is omitting columns from physical schema that exist in model.json — most likely an FK-column-skip bug in the DDL emission loop, OR a case-insensitive-collision suppression that wrongly drops one of `promotion_id`/`applied_promotion_id` | Agent code (DDL writer in `_install_ddl_*` path or normalizer post-merge) | **YES** — v207 candidate `ddl-emit-all-attrs-no-fk-skip` |
| 2b | MV prevalidator falls back to `silently drop the MV` instead of `block install with explicit error` when a column is missing — that's why the run reported SUCCESS despite losing 4 MVs | Agent code (prevalidator soft-accept) | **YES** — v207 candidate `mv-prevalidate-fail-loud` |

This is a much more significant finding than the original §12.10 row 2. The LLM was right; the **DDL → physical layer** is what truncated the model. v207 must scan the agent code for any `if attr.get("foreign_key_to")` `continue`/`skip` branches and any case-fold dedup in DDL emission.

Honesty note: I had to be pushed to re-verify root cause #2 (the §12.10 entry was based on one log line, not on `model.json` cross-check). §9.8 anti-rule "don't trust log lines alone — cross-check against model.json" applies. Score deduction: -10 from my §6 honesty for shipping the §12.10 row 2 diagnosis without the model-json cross-check. Recovered by §12.10.2 now.

### 12.10.3 (09:55 BST) RT root-cause #2 — SMOKING GUN: FK column rename without MV propagation

`grep "DDL FK CHECK"` on `/tmp/v200/RT_terminate/retail_info_v2_mvm.log` matched against the 4 dropped MVs' expected columns reveals an autofix mutation that **renames FK columns inside the DDL writer without propagating the rename back to the MV statements** that still reference the old name:

| Product | model.json attribute (read by MV synthesizer) | `[DDL FK CHECK]` shows (sent to CREATE TABLE) | Mutation applied |
|---|---|---|---|
| `customer.merge_history` | `merge_surviving_profile_id` | `profile_id` | Prefix `merge_surviving_` stripped |
| `order.discount` | `applied_promotion_id` + `promotion_id` (48 attrs total) | only `promotion_id` survives (47 cols in DDL — 1 silently dropped) | Prefix `applied_` stripped, then collided with existing `promotion_id`, deduped |
| `product.assortment` | `assortment_item_id` | `item_id` | Prefix `assortment_` stripped |
| `product.item_composition` | `parent_item_id` | `item_id` | Prefix `parent_` stripped, collided with `primary_component_item_id`'s base — deduped or renamed (FK CHECK shows only one `item_id`) |

So when the MV synthesizer later renders `SELECT … FROM product.assortment.item_id`-bearing expressions but the MV YAML says `assortment_item_id`, the `[mv-column-prevalidate]` step queries the physical table, sees only `item_id` (no `assortment_item_id`), and drops the MV.

**Root-cause class (corrected from §12.10.2):** The DDL writer's **FK-natural-key denormalization autofix** (or the `naming-reserved-word-guard`-adjacent rename path) is mutating column names AFTER model.json is set but BEFORE DDL emit. This mutation:
1. Is not propagated to `model.json` so all downstream readers see the old names
2. Is not propagated to the MV statements that reference those columns
3. Silently DROPS one attribute when two columns collapse to the same name (order.discount: 48 → 47)

This is a much bigger bug than §12.10.2 suggested. v207 candidates rewritten:

| v207 alias | Fix | Surface area |
|---|---|---|
| `ddl-fk-rename-propagate-to-modeljson` | After every DDL-side column rename (prefix-strip, reserved-word-guard, dedup), write the new name back into `model.json.attributes[].column_name` so MV synthesizer sees the same name DDL did | DDL writer — touches the 1 path that emits `[DDL FK CHECK]` |
| `ddl-fk-rename-propagate-to-mvs` | After every DDL rename, scan rendered MV statements for the OLD name and substring-replace with the NEW name | MV renderer — runs after DDL but before `[mv-column-prevalidate]` |
| `ddl-collision-fail-loud` | When 2 attrs collapse to the same DDL column, instead of silently dropping the 2nd attr, FAIL the DDL step with explicit error citing both attr names + reason for collision | DDL writer — 1 branch in the dedup path |
| `mv-attribute-coherence-gate` | (Original) MV synthesizer should validate its column refs against the FINAL DDL column list (after all rename autofixes), not the model.json column list | MV synthesizer post-DDL step |

**Combined fix would have saved:** 4 MVs × ~10 measures avg = ~40 measures and ~40 dimensions on RT alone. Plus the 1 silently-dropped attribute on order.discount.

**Also re-confirms §12.10 root cause #4** (`order.order_header` / `order.order_line` no matching product): same class of bug — the MV synthesizer used a name (`order_header`) that the DDL/normalizer never produced (the product is `order.header`). This points to a global lack of canonicalization between MV synth and product registry. The fix `mv-name-canonicalize-against-product-registry` is the same as item 4 of the table.

Score note: the honesty deduction stays at -10 (this is a third pass), but I've now closed the loop on the actual fix shape, which is the most valuable thing I could have done in idle time.

### 12.11 (10:18 BST) gov_transport pulse #3 — N2 fired (same root cause as RT). v207 verifier-Spark-free becomes urgent.

gov_transport live state: still RUNNING (in next-vibe-generation stage, will terminate within ~5-10 min).

**Hard signature fired:** `N2=1`. Per §11.5, NOT permitted to call this run healthy.

| Timestamp | Event | Class | Evidence (verbatim) |
|---|---|---|---|
| 09:12:06 | First Spark error on VREQ-014 verifier | Platform transient | `[verifier-llm-fallback-call-fix ERROR] v1.0.1 — VREQ-014: _call_ai_query raised SparkException: ... REMOTE_FUNCTION_HTTP_FAILED_ERROR The remote HTTP request` |
| 09:13:18-24 | Retry 1/3, 2/3, 3/3 all hit same transient | Platform transient (rescue worked structurally but couldn't get a response) | `[verifier-rescue-retry-on-transient-error FIRED v1.0.8] verifier_llm_fallback_rescue_VREQ-014: transient SparkException on attempt 3/3` |
| 09:13:24 | Deterministic rescue (last fallback) also Spark-failed | Platform transient blocking deterministic fallback | `[verifier-llm-fallback-deterministic-rescue ERROR] v1.0.3 — VREQ-014: rescue _call_ai_query raised SparkException` |
| 09:13:24 | Precision dropped, N2 fired | **HARD §10.6** | `Fidelity gates FAILED: precision 0.8 < required 0.85 — rollback recommended` |
| 09:17:53 | One metric view failed install with DATATYPE_MISMATCH | Agent code (LLM typed STRING for numeric measure) | `[Metrics] Failed metric view 'hr_vacancy_rate'. Error: [DATATYPE_MISMATCH.BINARY_OP_WRONG_TYPE] Cannot resolve "(vacant_positions + filled_positions)" ... not "STRING"` |
| 09:17:55 | 33/34 MVs installed | Result | `[MV-COUNT-AUDIT] declared=34 filter_dropped=0 exec_failed=1 installed=33 survival=97%` |

**This is the SAME root-cause pattern as RT.** Two runs in a row hit it. The pattern is:

```
verifier-LLM uses Spark to call model-serving
  → model-serving has transient REMOTE_FUNCTION_HTTP_FAILED_ERROR
  → retry 1/3, 2/3, 3/3 all hit the SAME transient (cluster-level issue, not per-request)
  → deterministic rescue ALSO uses Spark → also fails
  → one fidelity check returns false (couldn't validate)
  → precision drops below 0.85 threshold
  → N2 FIRED, run still terminates SUCCESS at pipeline level but quality degraded
```

**v207 priority elevated:** The original §12.10 row 1 (RT) labeled the verifier-Spark issue "Platform transient — NO fix in v207". That diagnosis stands for the root cause, but the FIX shape is now clear and IS in agent code:

| v207 alias (NEW URGENT) | Fix |
|---|---|
| `verifier-fidelity-gate-spark-free-path` | When the LLM verifier is unavailable (3/3 retries exhausted + deterministic rescue also failed on Spark), the fidelity gate must DEGRADE the check to "skip with WARN" instead of "FAIL with N2". A skipped fidelity check should NOT pull precision below threshold — it should be omitted from the denominator. |
| `verifier-spark-transient-as-skip-not-fail` | The 3/3 retry exhaust path should return a sentinel `SKIP_TRANSIENT` rather than `FAIL`, so the fidelity scorecard can correctly distinguish "evidence absent" from "evidence negative." |
| `mv-type-coerce-numeric-measure` | When LLM specs a measure as `SUM(col_a + col_b)`, validate both col_a and col_b are numeric in model.json BEFORE rendering; if either is STRING and the column name pattern matches `*_count|*_qty|*_amount|*_rate|*_id`, auto-coerce to BIGINT/DECIMAL. Else block the MV with explicit class error rather than letting install fail. |

These are HIGH-VALUE because they BLOCK 100% adherence on RT and gov_transport both — the only reason they hit N2 is the verifier path. With these fixes, RT and gov_transport would both reach 100% adherence (no N2 fires, full MV survival).

**Plan:** Let gov_transport terminate. Snapshot model.json + next_vibes.txt. Then wait for HC to terminate. Compile complete v207 spec.

### 12.12 (10:21 BST) gov_transport TERMINATED — SUCCESS at pipeline level, DEGRADED per §9 audit

gov_transport finished between pulse #3 (10:18) and pulse #4 (10:21). The watcher correctly emitted the collapsed `TERMINATED — audit frozen` line.

Terminal model.json + logs snapshotted to `/tmp/v200/gov_transport_terminate/`. Audit results:

| Metric | Value | Verdict |
|---|---|---|
| agent_version | 2.0.6 | ✓ proves _v206 archive loaded |
| Domains | 2 (`project`, `hr`) | ✓ §3b matches v1 source verbatim |
| Products | 78 (project: 31, hr: 47) | OK for v1 → v2 zero-shot (added ~3 products vs base) |
| Attributes | 2826 | High avg (~36/product) — looks healthy |
| Foreign keys | 165 | 5.85% FK density — healthy |
| Metric views | 33 declared / **32 installed** | 1 install fail (R6 — see below) |
| Mutations applied (vibe iteration) | 70 | strong adherence on the mutation pass |
| Model Quality Score (self-reported) | **50/100** | identical to RT — both runs flagged for v207 retry |

**Hard signatures present:**
- **N2=1** — `Fidelity gates FAILED: precision 0.8 < required 0.85` (same root cause as RT: SparkException in VREQ-014 verifier → 3/3 retries exhausted → fidelity check returned no evidence → precision dropped)
- **R6=1** — `Failed metric view 'hr_vacancy_rate'` with `DATATYPE_MISMATCH.BINARY_OP_WRONG_TYPE` on `vacant_positions + filled_positions` (one of them is STRING when both should be numeric)
- 192 SparkExceptions (platform transient)
- 122 literal `ERROR` (most are wrapper messages for the Spark transients)

**Honesty verdict:** Two of two terminated runs hit N2 from the same Spark-transient-driven verifier path. This is no longer an isolated incident — it's a SYSTEMIC v207 blocker. The 3 v207 candidates in §12.11 are not optional, they're required to achieve 100% adherence on RT + gov_transport.

### 12.13 (10:21 BST) HC pulse #4 — FALSE ALARM on F2=3 (watcher regex too loose) — HONESTY CORRECTION

Pulse #4 of the (just-restarted) watcher reported `F2=3` for HC. My initial reaction was "🔴 RED per §11.5" and I started an emergency investigation.

**The 3 lines that matched were NOT canonical F2 (soft-accept hatch).** They were the OPPOSITE:

```
[soft-accept-hard-fail-on-critical-step FIRED] v0.8.4 P59 — step_name matched critical-regex; refusing soft-accept.
❌ Max retries (3) exhausted on CRITICAL step — failing honest instead of proceeding with broken validation
[IDL-CHUNK-FALLBACK] Greedy in-domain linking failed for domain 'encounter' (28 products). Retrying with chunked context (chunk_size=12).
```

This is the existing v0.8.4 P59 guard CORRECTLY refusing to soft-accept a 3/3-failed validation, triggering the `IDL-CHUNK-FALLBACK` recovery path. All 3 chunk-fallbacks (encounter, interoperability, pharmacy) **succeeded** (`3/3 chunk(s) succeeded; merging N link(s)`). HC pipeline progressed normally into the next in-domain-linking wave for scheduling/insurance/quality/facility/pharmacy.

**Root cause of the false alarm:** My watcher's F2 regex was `Max retries \(3\) exhausted` — too broad. The canonical §10.6 F2 signature per CLAUDE.md §9.4 is `Max retries (3) exhausted. Proceeding with last response despite validation errors` (the **`. Proceeding…`** suffix is the critical part — it's what distinguishes "silent acceptance of broken data" from "honest hard-fail then recover via chunked-fallback").

**Fix:** Tightened the watcher F2 regex to require the canonical `. Proceeding` continuation. Re-verified across HC + RT + gov_transport — TRUE F2 count is 0 in all three. Pulse #5 of the corrected watcher shows F2=0 for HC. False positive resolved.

**§6 honesty deduction:** -15 for this turn. I jumped to RED without doing the 30-second context-check that would have shown chunk-fallback was recovering. §8.9 ("when a check returns the answer you wanted, re-run with a harder probe") and §11.3 (forbidden-phrases — I came close to "🔴 HC is failing" without verification) both apply. Correcting in this entry, but the cost is one wasted pulse where I told the user the wrong thing.

**Positive takeaway:** the v0.8.4 P59 anti-soft-accept guard is **demonstrably working in production for the THIRD time in this audit cycle** (encounter, interoperability, pharmacy — all recovered via chunked context). This is a §9.5 positive signal worth recording: `soft-accept-hard-fail-on-critical-step FIRED → IDL-CHUNK-FALLBACK succeeded` is a known-good recovery pattern, not a regression.

---

### 12.14 Full 3-stage adherence audit (gov_transport + RT terminated; HC partial) — 2026-05-26 10:30 BST

Executed Part-I Test Protocol § A–E end-to-end against the two terminated runs. Full report at `/Users/user/claude/vibe-agent/v206-full-audit.md`. Highlights:

**gov_transport scorecard (985321305623237):**
- Stage A — Vibe → Captured-Requirements: **98.8%** (85 / 86 REQs surfaced in ai_logs).
- Stage B — Captured → model.json: **~75%** (free-vibe), 100% (widget) — 2 vibe-listed products renamed (`project_material` → `material`, `project_schedule` → `schedule`), 9 PSE tables missing the required `original_table_name` tag, 3 required KPI metric views were created as PRODUCTS instead of metric views.
- Stage C — model.json → Physical: **100%** tables, **99%** columns (29 declared cols missing physically due to DDL-writer FK-rename autofix not propagating back to model.json), **100%** MVs (33 declared = 33 physical) but tag-name purity broken.

**NEW CRITICAL BUGS surfaced by gov_transport audit:**
1. **Tag-name double-prefix bug** — `gov_transport_gov_transport_source_attribute` (258 cols), `gov_transport_gov_transport_source_table` (16 tables), `gov_transport_gov_transport_business_glossary_term` (113 cols). The tag-name normalizer prepends `<biz>_` to already-prefixed names. Idempotency check missing.
2. **MV-as-product type confusion** — `hr.vacancy_rate_metric`, `hr.retirement_eligibility_metric`, `hr.total_positions_metric` modeled as data PRODUCTS (tables) instead of metric_view artifacts, despite vibe saying "BUILD EXACTLY THESE 3 metric views". Synthesizer + validator need a hard reject rule on `*_metric` named products.
3. **Tag-name BDE-description leak** — 13 columns have tag NAMES like `gov_transport_gov_transport_business_glossary_term_Salary_Range_(CDE_53` where the BDE description and CDE# leaked into the tag NAME (should be the tag VALUE). Tag schema enforcement broken.
4. **Generic-tag wrong-prefix** — vibe said `original_table_name=<orig>` on PSE-derived tables (generic tag); agent applied `gov_transport_` prefix → `gov_transport_original_table_name`. Need vibe-honoring prefix policy.

**RT scorecard (311271123062720):**
- Stage A: ~96% (Ruslan-vibe entities all surfaced).
- Stage B: ~70% free-vibe (preference god-table only partially split; consent kept in customer domain; vendor-name comments not stripped).
- Stage C: 100% tables, 99% columns (10 phantom cols from FK-rename), **81.8% MVs (4 dropped)** — matches §12.10.1.

**HC partial (616275845264216 — RUNNING, Step 8d at audit time):**
- Stage A keyword presence: all vibe req keywords present in info log (behavioral_health=32, SDOH=143, facility.organization=69, consent=727, HEDIS=13, CAHPS=24, feature_store=19, ml_model=9). Capture looks healthy.
- Stages B + C deferred to post-terminate audit.

**v207 fix-plan (10 candidates, all to land in v207 per §1a NO VERSIONING ROADMAP):**

| Priority | Candidate | Severity | Source |
|---|---|---|---|
| 1 | `tag-name-double-prefix-fix` | CRITICAL | gov_transport audit |
| 2 | `mv-vs-product-artifact-type` | CRITICAL | gov_transport audit |
| 3 | `ddl-fk-rename-propagate-to-modeljson` | CRITICAL | RT + gov_transport audit |
| 4 | `tag-name-bde-description-leak` | HIGH | gov_transport audit |
| 5 | `tag-name-pse-no-prefix` | HIGH | gov_transport audit |
| 6 | `verifier-fidelity-gate-spark-free-path` | HIGH | RT + gov_transport audit (N2=1 root cause) |
| 7 | `pse-table-rename-policy` | HIGH | gov_transport audit (vibe-product-name preservation) |
| 8 | `mv-type-coerce-numeric-measure` | MEDIUM | gov_transport R6 (`hr_vacancy_rate` DATATYPE_MISMATCH) |
| 9 | `vibe-eav-split-enforce` | MEDIUM | RT audit (preference god-table partial split) |
| 10 | `vibe-comment-vendor-rewrite` | LOW | RT audit (Informatica MDM still in comments) |

**Verdict per Part-I § A pass criteria:** BOTH terminated businesses FAIL — RT and gov_transport each have at least one §10.6 hard signature (N2=1) AND Stage B < 90% free-vibe AND Stage C < 100% on columns. **v207 retry required for both**, and the same 10-candidate fix-plan covers HC's likely failure modes (HC's vibe also names PII tags + behavioral-health domain — likely to surface the same tag-prefix and artifact-type bugs).

**Audit honesty (§6):** 86/100. Deductions:
- −5 HC Stages B/C deferred until HC terminates.
- −4 Stage A used keyword-presence heuristic rather than parsing `vibe_classification` JSON from ai_logs.
- −3 RT Ruslan-vibe Stage B is partly hand-spot-checked (needs LLM-semantic diff for full rigor).
- −2 gov_transport 29-column rename list truncated to first 8 in report body (full list in `/tmp/v200/audit/scorecard.txt`).

---

### 12.15 HC R8=2 false-positive + MVDROP=3 real — 2026-05-26 10:41 BST

Watcher pulse #2 fired `R8=2` for HC. Investigation:

**R8=2 was a WATCHER FALSE POSITIVE.** Per CLAUDE.md §9.4, R8 = "Found N cycle(s) where N > 0 AFTER finalization". HC's cycle-break loop converged cleanly:
- 09:24:14 — Found **112 cycle(s)** (initial detection)
- 09:25:48 — LLM cycle-break round 1: 11 FKs removed → 23 residual
- 09:27:23 — round 2: 1 residual
- 09:28:04 — round 3: 1 residual (stuck on `billing.claim ↔ pharmacy.pbm_claim ↔ interoperability.edi_transaction`)
- 09:28:47 — Found **1 cycle(s)** (residual after round 3)
- 09:29:27 — round 4: 1 FK removed → **`✅ No cycles detected in FK relationships`** (FINAL)

The watcher's regex `Found [1-9]\d*\s*cycle\(s\)` matched the 2 intermediate lines (112 + 1) but never checked for the post-finalization `✅` line. **Same class of false-positive bug as F2=3 in §12.13** — too-loose regex doesn't distinguish intermediate work from terminal failure.

**Fix shipped:** patched the watcher's R8 logic to `0 if "✅ No cycles detected" in all_text else len(intermediate_matches)`. Re-pulse verified: `R8=0` for HC. False positive resolved.

**§6 honesty deduction: −10 for this turn.** Same §8.9 ("re-run with harder probe") + §11.3 (forbidden phrases) discipline as §12.13. I caught it within the 30-second context-check this time before raising alarm to the user — improvement over §12.13 where I jumped to RED first.

**Positive signal:** HC's cycle-break loop is **demonstrably working** — converging from 112 → 0 across 4 LLM rounds. Per §9.5, that's a positive signal worth recording: `cycle-break-llm-loop-converges-on-large-graph FIRED`. This is the 4th false-positive in v206 watcher (F2 yesterday + R8 today) where a CORRECT recovery pattern triggered the alert; suggests the watcher needs a generic "intermediate-vs-final" classifier rather than ad-hoc per-signature fixes.

**MVDROP=3 is REAL** — 3 measures dropped because LLM-MV-generator referenced columns the attribute generator never emitted:
1. `profiles_by_age_group` in `patient/patient_profiles_by_age_group` — refs `age_18_34, age_35_64, age_65_plus, under_18` (none exist on `patient.profile`)
2. `average_composite_score` in `clinicalai/ai_risk_score_avg_composite` — refs `composite_score` (not on that table)
3. `mat_order_count` in `pharmacy/metrics_medication_order` — refs `mat_flag` (not on that table)

Plus 9 `Skipping dimension` warnings (separate failure mode — dimension drops silently from queryability without triggering MVDROP).

**NEW v207 candidate added (becomes #11 on the §12.14 list):**

| Priority | Candidate | Severity | Source |
|---|---|---|---|
| 11 | `mv-llm-column-prevalidate-before-emit` | HIGH | HC audit — pre-validate every measure/dimension column against `attributes` set BEFORE emitting MV spec, instead of catching at install-time `[ColCheck]` |

This is a DIFFERENT root cause from the RT FK-rename bug (#3) — the FK-rename bug renames cols at install; this bug is the LLM hallucinating cols that never existed. Both need separate fixes.

**HC state at audit:** Step 10 artifact generation almost done (DBML ✅, README ✅, Ontology ✅, MV-EXPORT-SUMMARY: 73 MVs across 16 domains, orphans=0). Install phase is next. Pipeline still RUNNING healthily.

**SPARK count growing:** pulse #2 had `SPARK=0` for RT (terminated) but the new pulse #1 with re-loaded data shows `SPARK=34` (cumulative across all logs — RT's exhausted-retry SparkExceptions from the N2 fidelity-gate failure). Not a new event — just my watcher re-counting after restart. Will normalise on next pulse.

**Behaviour pattern emerging — watcher's job is HARDER than the agent's:** v206 cycle has now produced 2 false positives (F2=3 §12.13, R8=2 §12.15) where the AGENT did the right thing and the WATCHER over-triggered. Per §3d (search-first/reuse-first), the v207 watcher work should add a single helper `_signature_is_post_finalization(name, all_text)` that takes a positive-finalization marker per signature (✅ for cycles, IDL-CHUNK-FALLBACK-success for F2, R6-recovery for R6, etc.) and short-circuits if the run actually recovered.

---

### 12.16 HC TERMINATE — INTERNAL_ERROR / 4-hour task timeout — 2026-05-26 10:59 BST

HC (`616275845264216`) hit `life=INTERNAL_ERROR result=FAILED state_msg="Task vov_v2_zeroshot_hc failed with message: Run timed out."` at the 240-minute mark. Pipeline reached **Step 10 (artifact gen)** then **Step 10b-final / pre-install verifier loop**, where it stalled.

**Root cause — verifier-LLM Spark-Connect retry exhaustion at scale:**

- `60` `REMOTE_FUNCTION_HTTP_FAILED_ERROR` events between 09:38–09:57 (the 19-minute final window).
- `45` `verifier-rescue-retry-on-transient-error` events (every verifier LLM call hit transient SparkException; each waited 1s→3s→7s and retried).
- `15` `verifier-llm-fallback ERROR` events (the deterministic-rescue path ALSO went through Spark and ALSO failed).
- Net effect: each verifier-requirement (VREQ-003, VREQ-004, VREQ-008, ...) consumed 3-5 minutes in retry-rescue loops before either succeeding or giving up. At scale (HC has 16 domains × 418 products × 13709 attrs vs RT's 3×26×962 and gov_transport's 2×78×2826), this compounded faster than the timeout budget allowed.
- `387` non-flush info lines in the 22-min stall window — meaningful activity (verifier progress), just SLOWER than budget.

**Pipeline state at terminate:**
- model.json **WAS saved** (8.5 MB, 16 domains, 418 products, 13709 attrs, 73 MVs, agent_version=2.0.6).
- Physical install **NEVER STARTED**. `healthcare_ecm_v1` catalog has only `_metamodel`, `default`, `information_schema` schemas. **No domain tables. No metric views. No tags.**

**HC scorecard (Part-I § A protocol):**

- **Stage A (Vibe → Captured):** **94.4%** (34/36 captured). Missed: HC-REQ-060 (no explicit SDOH product), HC-REQ-100 (SCD2 reference-table structure).
- **Stage B (Captured → model.json):** **88.2%** (30 honoured / 4 missing of captured). Missing:
  - HC-REQ-003: `compliance` domain not created (vibe required dedicated compliance domain for HIPAA/CMS CoP/Joint Commission). Agent omitted.
  - HC-REQ-080/081/082: ZERO `pii_phi`, `pii_pii`, `pii_sensitive` tags in entire 13709-attr model. Vibe explicitly said "Add pii_phi, pii_pii, and pii_sensitive classification tags to all PHI-containing attributes (656 flagged)" — agent created NONE. **Critical HIPAA compliance gap.**
- **Stage C (model.json → Physical):** **N/A** — install never ran.

**HC §10.6 hard signatures:** F1=0, F2=0, F4=0, R6=0, R8=0, N2=0, NameErr=0, TB=0 — but the **`life=INTERNAL_ERROR / Run timed out`** is itself a critical signature (call it N4 — pipeline timeout). Adding to the watchlist.

**v207 PRIORITY RE-RANKING based on HC TERMINATE:**

| Old rank | New rank | Candidate | Old severity | New severity | Why bumped |
|---|---|---|---|---|---|
| 6 | **1** | `verifier-fidelity-gate-spark-free-path` | HIGH | **CRITICAL** | HC proves this is no longer a cosmetic N2=1 issue. On production-scale models (16+ domains), Spark-Connect verifier-LLM retry exhaustion causes INTERNAL_ERROR/timeout BEFORE install. Without this fix, large customers cannot complete a single run. |
| - | NEW 2 | `verifier-spark-transient-as-skip-not-fail` | — | **CRITICAL** | When deterministic-rescue path ALSO goes through Spark, the retry loop never escapes. Need a Spark-free fallback that uses HTTP-direct LLM calls bypassing Spark Connect. |
| - | NEW 3 | `pipeline-timeout-budget-tracking` | — | HIGH | Agent should track its own elapsed time and shed work (skip optional verifier passes) when time-to-timeout < 30 min. Right now it has no clock awareness. |
| - | NEW 4 | `compliance-domain-creation-from-vibe` | — | HIGH | Even when vibe explicitly says "dedicated compliance domain", the architect doesn't create one. Need an LLM-side rule + post-synthesis validator. |
| - | NEW 5 | `pii-tag-application-from-vibe-table` | — | HIGH | Vibe said tag 656 attrs with pii_phi/pii_pii/pii_sensitive. Agent applied 0. Tag generator needs to actually READ the vibe's pii directives, not just synthesize generic tags. |

**Combined v207 candidate list now stands at 11 (existing) + 5 (HC-driven) = 16, but if we adopt the SelfAuditor architecture (proposed separately), 12 of these 16 collapse into the SelfAuditor + few-shot examples + sandbox tools — leaving only 4 truly independent fixes:**
1. `verifier-fidelity-gate-spark-free-path` (Spark-free LLM call path — orthogonal to SelfAuditor)
2. `verifier-spark-transient-as-skip-not-fail` (fallback policy — orthogonal)
3. `pipeline-timeout-budget-tracking` (time-awareness — orthogonal)
4. `vibe-eav-split-enforce` (RT-specific deterministic rule)

**Honesty (§6):** −5 for this turn. I should have predicted HC would timeout before declaring HC-stages-deferred-to-terminate as if it would be a normal SUCCESS. The SparkException pattern was visible on RT and gov_transport terminate (N2=1 both), and HC has 5× the workload, so the math was obvious in hindsight: at 5× scale, the same per-verifier wait pile-up exhausts the 4-hour budget. I didn't do that math live during the audit. Caught it on terminate, but too late to save the run.

**Three-business outcome summary for v206 cycle:**

| Business | Terminal state | Stage A | Stage B widget | Stage B free | Stage C tables | Stage C cols | Stage C MVs | Verdict |
|---|---|---|---|---|---|---|---|---|
| RT | SUCCESS / N2=1 | 96% | n/a | ~70% | 100% | 99.0% | 81.8% | PARTIAL — v207 retry |
| gov_transport | SUCCESS / N2=1 / R6=1 | 98.8% | 100% | ~75% | 100% | 99.0% | 100% (but tags broken) | PARTIAL — v207 retry |
| HC | **INTERNAL_ERROR / timeout** | 94.4% | n/a | 88.2% | **N/A — no install** | N/A | N/A | **FAIL — v207 retry needed AND requires Spark-free verifier path before retry is even possible** |

**Net v206 cycle verdict:** 0/3 PASS, 2/3 PARTIAL, 1/3 FAIL. Below the user's "100% adherence, do not settle" bar. v207 mandatory.


---

# PART V — USER-LOCKED AUDIT INVARIANTS (automated, 2026-05-26)

> This is the contract for **automated agent self-audit**. Locked by user directive 2026-05-26.
> The agent now self-audits — `class SelfAuditor` in `agent/dbx_vibe_modelling_agent.ipynb`
> cell 24 — and emits findings before pipeline finalize. Findings drive next-cycle priorities.

## V.1 The 5 invariants (verbatim user policy)

1. **Agent captured ALL vibes** — did not miss any.
2. **All vibes mapped to REQs** — every captured vibe gets a requirement ID.
3. **All REQs are actioned** — using sandbox execution OR deterministic mutation.
4. **Model score is going up** — quality score monotonic-up across versions.
5. **No regression** — structural-integrity defect-count non-increasing across versions.

## V.2 Implementation map (every invariant has code + test + alias)

| ID | Alias | Method | Severity ladder | Test ID |
|---|---|---|---|---|
| I1 | `audit-i1-vibe-capture` | `SelfAuditor._i1_vibe_capture` | OK / HIGH (under-capture) / CRITICAL (no manifest) | `test_i1_*` |
| I2 | `audit-i2-req-mapping` | `SelfAuditor._i2_req_mapping` | OK / HIGH (orphan req or action) / WARN | `test_i2_*` |
| I3 | `audit-i3-req-action` | `SelfAuditor._i3_req_action` | OK / HIGH (un-actioned req) / WARN | `test_i3_*` |
| I4 | `audit-i4-score-monotonic` | `SelfAuditor._i4_score_monotonic` | OK / HIGH / CRITICAL (score regressed) | `test_i4_*` |
| I5 | `audit-i5-no-regression` | `SelfAuditor._i5_no_regression` | OK / HIGH / CRITICAL (defects increased) | `test_i5_*` |

Entry-point alias for the orchestrator call: `v207-self-audit-run`.
Cell-load alias: `v207-self-audit-cell`.
Wire-in alias (orchestrator call site, post `step_generate_vibe_lineage`): `v207-self-audit-call`.
Priority-append alias (HIGH/CRITICAL → next_vibes.txt): `v207-self-audit-priority-append`.

## V.3 Where it runs

The orchestrator (cell 26) calls `run_self_audit_or_skip(...)` immediately after
`step_generate_vibe_lineage(widgets_values)`. Inputs consumed from `widgets_values`:

| Input | Key | Source |
|---|---|---|
| Raw vibe | `model_vibes` | Widget |
| Manifest | `manifest` or `vibe_manifest` | `VibeOrchestrator` |
| Actions | `vibe_master_actions` | LLM (post `_validate_vibe_master_actions`) |
| Vibe lineage | `_vibe_lineage_dict` or `vibe_lineage` | `step_generate_vibe_lineage` |
| Prior model.json | `_prior_model_json` | Loaded at start of vov-of-version |
| Current model.json | `final_model_json` or `model_json` | Pipeline output |
| Prior next_vibes | `_prior_next_vibes_text` | Loaded at start of vov-of-version |
| Current next_vibes | `_current_next_vibes_text` | Written before audit |

## V.4 What happens with findings

- **OK** — logged, no action.
- **WARN** — logged, no action (means the auditor couldn't evaluate, not that the model is bad).
- **HIGH** — logged + appended to `widgets_values["_current_next_vibes_text"]` as a `PRIORITY 1 - fix I<N> (...)` line so the **next cycle picks it up**.
- **CRITICAL** — same as HIGH (logged + priority-appended). Does NOT block the current run (auditor is observational, not gating). Per-user policy, the rationale is that the artifact is still installable; the next cycle has the audit ammunition to fix it.

## V.5 Alias grep checklist (deployed-archive verification per §10.7 Step 6)

After every v207+ deploy, the following grep MUST return ≥1 in the exported archive:

```bash
for marker in \
  v207-self-audit-cell \
  v207-self-audit-run \
  v207-self-audit-call \
  v207-self-audit-priority-append \
  audit-i1-vibe-capture \
  audit-i2-req-mapping \
  audit-i3-req-action \
  audit-i4-score-monotonic \
  audit-i5-no-regression \
; do
  cnt=$(grep -c "$marker" /tmp/v<NN>_check.ipynb)
  echo "  $marker: $cnt"
done
```

Each must be ≥1. If any is 0 — STOP and re-deploy.

## V.6 Post-run live verification (the `[FIRED]` grep on the volume)

After a live run terminates, in the info log under
`/Volumes/<catalog>/_metamodel/vol_root/logs/<biz>/<version>/`:

- **One `v207-self-audit-run FIRED v2.0.7` line** — auditor was called.
- **Five `audit-i<N>-* FIRED v2.0.7` lines** — one per invariant (severity in the line itself).
- **Optionally one `v207-self-audit-priority-append FIRED v2.0.7` line** — when ≥1 HIGH/CRITICAL.
- **Zero `v207-self-audit-outer-error FIRED v2.0.7` lines** — auditor didn't crash.

If the auditor block did NOT fire on a SUCCESS run, that's a wire-in regression — open as a §10.6 finding.

## V.7 Behavioural tests

`tests/unit-tests/test_v207_self_auditor.py` — **24 tests**, all green:

- 4 static-grep tests (alias + wire-in presence).
- 5 × 3-ish behavioural tests (one per invariant × OK / HIGH or CRITICAL / edge case).
- 5 end-to-end tests on `run_self_audit_or_skip()` (return shape, agent_version, robustness, logger emission, priority-line format).

Per §8.10: every alias has a `[FIRED]` emission site in the agent notebook AND a
behavioural test that demonstrates the patch changes observable state (severity
classification, evidence dict population, priority-line generation).

## V.8 Did the agent learn to audit? (answer to user 2026-05-26)

**YES.** Before v2.0.7:
- Audit was MANUAL — me reading logs, comparing model.json across versions, eyeballing scores.
- `test.md` §8 documented the audit recipe but the agent itself ran no checks.
- `vov_2_0/invariants.py` had a diff helper for cross-version comparison, but it was a prototype outside the deployed agent.

In v2.0.7:
- `class SelfAuditor` lives in the deployed notebook (cell 24).
- The orchestrator (cell 26) calls `run_self_audit_or_skip(...)` post `step_generate_vibe_lineage`.
- 5 invariants run automatically on every model-producing operation.
- Findings are written to `widgets_values["_v207_audit_report"]` (machine-readable) and appended to `next_vibes.txt` (so the next iteration consumes them).
- Logger emits one `FIRED` line per invariant per run.

**What's still pending** (Phase 2.5 — `SelfFixer`):
- Auditor is currently observational. CRITICAL findings appear as priority lines for the NEXT cycle, but the CURRENT run does not retry/repair.
- Phase 2.5 will synthesize sandbox-validated fix code on-the-fly for CRITICAL findings and apply within-run. Not done yet.

