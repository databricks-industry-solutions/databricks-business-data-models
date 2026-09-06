# CLAUDE.md — Project Guardrails for the vibe-modelling-agent

These instructions apply to every session in this repository. Follow them verbatim.

---

## MISSION (read this first, every session — never forget it)

The single purpose of this agent is to PRODUCE A DATA MODEL THAT 100% ADHERES TO THE USER'S VIBES (hard floor 90% VERIFIED adherence), is production-ready, and is good enough to recommend to peers or propose as a global standard. This will run for HUNDREDS of industries.

The mission is judged by VERIFIED VIBE ADHERENCE = (VREQs verified-applied) / (VREQs extracted), with two mandatory halves: (a) EXTRACTION COMPLETENESS — every requirement in the vibe becomes a VREQ; (b) APPLICATION + VERIFICATION — every VREQ is actually applied AND deterministically provable against the real catalog. A "Max retries exhausted, proceeding" soft-accept is NOT applied.

NON-NEGOTIABLE OPERATING RULES FOR THIS MISSION:
- NEVER OVERFIT or HARDCODE any industry (gov_transport, airlines, automotive, healthcare, etc.). Every fix must be generic and read from the vibe / runtime / catalog, never from a baked-in name.
- For EVERY failed VREQ, examine its FULL LIFECYCLE: extracted? → applied to model dict? → physically built? → verified? Find the exact stage where it dropped and fix THAT stage's root cause.
- Three systemic failure classes drive non-adherence (diagnosed from the gov_transport v3.4.0 24-VREQ trace + live HEALTH sandbox, 2026-06-08):
  1. VERIFIER FALSE-NEGATIVES (the "lying scoreboard") — the model DID follow the vibe but the verifier scores it failed because its snapshot is lossy (missing `_metrics` schema MVs, missing column tags) and its matching is too literal (user display name "Vacancy Rate" vs physical `hr_vacancy_rate`). This is the LARGEST lever. Fix = ground every VREQ class against the REAL catalog with NAME NORMALIZATION (display→snake, domain-prefix-tolerant, substring/contains).
  2. GENUINE NAME/SHAPE SUBSTITUTION — generators that receive only a COUNT free-invent names. Fix = forward the user's EXACT named artifacts as a USER-KING mandate into the generator prompt.
  3. DEAD AGENTIC REPAIR — the SelfFixer (sandbox code-gen residual repair) ran inert because it was built with ai_agent=None. Fix = resolve a live AIAgent at the single shared entry point; the sandbox mechanism itself is proven working (HEALTH made 397 VOV_2_SANDBOX code-gen calls).
- Run AUTONOMOUSLY: monitor → RCA every miss → generic root-cause fix → behavioral test (fail pre-patch, pass post-patch) → bump version → redeploy → re-run FROM V1 (no chaining) → loop until ALL targets ≥90% with zero §10.6 signatures. Do not stop until the goal is met.

---

## 0. Release-note detail standard (when tagging to main)

REFERENCE: https://example.com/releases/v0/

When the user asks to tag a release to main, the release notes MUST match the depth and structure of that reference tag. That means, at minimum:

1. **Opening summary** — one paragraph describing the release theme and what problem the release solves.
2. **Highlights / Headline features** — bulleted list of the most visible user-facing changes with 1–2 sentence descriptions each.
3. **Detailed change sections** grouped by theme (e.g. "Core pipeline", "Prompts & validators", "Autofix", "Sample generation", "Viewer", "Observability"). Each section:
   - Lists each change with its P-number (e.g. P0.81).
   - Describes WHAT changed in 1–2 sentences.
   - Describes WHY (the underlying bug or gap) in 1–2 sentences.
   - Describes the behavioural impact (what users/consumers now see vs before).
4. **Regression report** — explicit "Known risks / regressions" subsection listing anything that might behave differently and how it was mitigated.
5. **Validation evidence** — which runs (smoke / vov / Airlines) tested the release, what was measured (e.g. "78.6% vibe adherence", "15/15 MVs 0 orphans"), and pass/fail per gate.
6. **Metrics** — table of objective before/after numbers where available (naming uniformity %, MV failure count, sample-gen tier rate, adherence %, model-quality score, etc.).
7. **Upgrade / migration notes** — any changes to widget schemas, model.json shape, catalog conventions, volume paths, or Databricks SDK versioning that consumers must adapt to.
8. **Commit / PR links** — inline links to the individual merged commits or PRs that make up the release.
9. **Contributors / co-authors** — Isaac credit plus any other contributors.

Short, emoji-filled, or pure-feature-list changelogs are NOT acceptable for tag-to-main operations. If the change is tiny (single-commit patch), say so explicitly and match the same structure with brief entries, rather than abbreviating the format away.

---

## 1. Regression report after every delivery

AFTER FINISHING YOUR JOB, FIND EVERY SINGLE REGRESSION ERROR AND RACTIFY THE ROOT CAUSE BEFORE YOU DELIVER, AND THEN SHOW ME REGRESSION RESPORT WITH HOW CRITICAL THE ISSUE IS.

## 1a-bis. SUCCESS-GATE APPLIES TO `main` ONLY — SCRATCH BRANCHES KEEP FULL HISTORY (clarified 2026-06-08)

**The success-verification gate is a `main`-branch rule, NOT a global ban on committing.** (updated 2026-06-08)

There are two distinct branch classes, with opposite rules:

### Scratch / work branches (e.g. `scratch/*`, `agent-vov-fix`, any non-`main` working branch) — COMMIT FREELY

- **You MUST checkpoint every fix here as you go.** Commit + push in-flight attempts, partial fixes, RCA snapshots, redeploys — the whole iteration trail. The point is to preserve the history of WHAT WAS TRIED so nothing is lost between sessions and the user can audit the path.
- No success-verification is required before committing or pushing to a scratch branch. "Let me commit this WIP" is correct behaviour here.
- Use descriptive commit messages that say what the attempt was and its live result so far (e.g. "v3.4.4 vibe-conventions-override — deployed, gov_transport run 1089… RUNNING, not yet audited").
- A long-lived scratch branch per task is preferred so the fix history is contiguous. Push it to `origin` so it survives.

### `main` (and any protected/release branch the user designates) — SUCCESS-GATED

The `main` branch is the record of WHAT SHIPPED AND WORKED. A commit reaches `main` ONLY via a merge/PR after the change has been verified end-to-end on live runs to satisfy the user's success criteria (typically: ≥90% / 100% adherence to user vibes + ZERO §10.6 hard signatures).

**Promotion-to-`main` workflow (HARD):**

1. Iterate on a scratch branch: edit working tree, commit checkpoints freely.
2. Bump `__AGENT_VERSION__` to the next single-digit semver (per §3a).
3. **Deploy directly from the working-tree file to the workspace** as `dbx_vibe_modelling_agent_v<NN>` via `databricks workspace import` (CLI reads from disk).
4. Patch the JOB notebook_path → `_v<NN>`.
5. Drop catalogs, prior runs, submit fresh runs.
6. Monitor per §11. KILL early on RED trajectory, iterate on the scratch branch (re-deploy from working tree).
7. **ONLY AFTER** the run terminates with `result_state=SUCCESS` AND the adherence audit passes success criteria, merge the scratch branch into `main` (`git merge` / PR) and push `main`.
8. The merge/commit on `main` references the live run_id that proved the fix worked.

**Hard prohibitions (apply to `main` ONLY):**
- ❌ Merging/pushing to `main` before the live run terminates with SUCCESS + target adherence.
- ❌ Fast-forwarding an unverified scratch commit onto `main` to "save a step".
- ❌ Bypassing with "the test passes locally, that's good enough" — local tests cover ~20% of production behavior; `main` needs live proof.

**These prohibitions do NOT apply to scratch branches** — on scratch branches, committing/pushing in-flight work is REQUIRED, not prohibited.

## 2. Databricks Serverless compatibility (hard constraint)

ALL THE CODE YOU GENERATE MUST ALWAYS WORKS WITH DATABRIKC SERVERLESS ENVIRONMENT, No Cache, persist, uncache, sparkcontext etc.

## 3. Root-cause fixes, not symptom fixes

WHEN I ASK YOU TO FIX A PROBLEM, ALWAY FIND THE ROOT CAUSE OF THE PROBLEM AND FIX IT, DO NOT JUST FIX THE SYMPTOM, YOU MUST FIX THE ROOT CAUSE.

## 3d. SEARCH-FIRST, REUSE-FIRST — NEVER INVENT WHAT ALREADY EXISTS

BEFORE PROPOSING OR WRITING ANY NEW CODE, YOU MUST:

1. **Search the existing codebase** for any function, class, prompt, schema, widget, or utility that already solves the problem or something close to it. Use `Grep` and `Glob` aggressively. Don't guess — verify.

2. **Extend or reuse first**. If existing code covers 70%+ of the need, refactor or extend it rather than duplicating. If it covers less, compose it with thin new code. Only when the existing code is genuinely unrelated or structurally wrong do you write something new.

3. **Honour DRY**. Two implementations of the same concept is a bug in this codebase. If you add a second parser, a second validator, a second log helper, a second cap calculator — you have failed this rule.

Real examples of violations to never repeat:
- Proposing regex extraction of user directives from `business_description` when `VibeOrchestrator` + `VIBE_PARSE_PROMPT` + `_VIBE_PARSE_RESPONSE_SCHEMA` already LLM-parse the same concepts into a structured `vibe_classification` dict consumed by every downstream stage.
- Writing a second "sample data" engine alongside the pool engine without first checking whether `_sample_numeric` / `_sample_temporal` / `_assemble_rows_from_pools` could be extended.
- Adding a new autofix pass that duplicates logic already present in `_pre_static_analysis_autofix`.

The search-first loop before every new solution is:
```
Grep for: the concept name, the likely function prefix, the widget name, the schema tag
→ read the top 3 matches
→ ask: can I extend this to cover my case?
→ if yes, extend
→ if no, compose with a thin wrapper
→ only if no existing code is usable, write net-new — and justify why
```

Failing this rule wastes cycles and creates parallel sub-systems that drift apart over time.

## 3c. USER VIBES ARE THE SUPREME AUTHORITY — NON-NEGOTIABLE

EVERYTHING THE USER TELLS YOU — IN WIDGETS, IN `model_vibes`, IN `business_description`, IN ANY EXPLICIT DIRECTIVE — OUTRANKS EVERY HEURISTIC, SCORING FORMULA, BEST-PRACTICE GUIDELINE, OR LLM OPINION IN THE ENTIRE PIPELINE.

The priority pyramid is:
1. **User vibes** (widgets, model_vibes, business_description, any explicit user instruction) — ALWAYS WINS
2. Deterministic invariants (Databricks Serverless compat, single-digit semver, industry-agnostic code)
3. Architect review scores, gates, and LLM recommendations
4. Best-practice heuristics (tier classification, sizing formulas, blacklists)

If a user vibe says "target 3 domains, ~18 products," the tier-classifier prompt MAY NOT override it based on SaaS-landscape count or regulatory density. If user says "exactly 25 products per domain," no architect gate can propose to exceed. If user says "keep domain `support` in the model," no judge/architect may remove it.

**Enforcement rules for every prompt, autofix, and validator:**
- Every prompt template MUST carry a preamble declaring user vibes as the supreme authority.
- Every LLM instruction set must instruct the model: "If this guidance conflicts with an explicit user directive in `{user_vibes}` or `{business_description}`, the user directive WINS without exception."
- Every mutation validator must detect and REJECT any LLM proposal that violates a user vibe.
- Every autofix, rule, blacklist, cap, or scoring heuristic must check user vibes before firing and SKIP ITSELF if the user has explicitly directed otherwise.
- Every log line that shows a heuristic overrode a user directive is a critical bug and must be fixed at root cause.

Violations seen in prior runs (all must never happen again):
- Tier-classifier ignored "intentionally tiny — target 3 domains" → built 13 domains / 181 products.
- Judge substituted user's `business_domains="customer, order, product"` with `fulfillment, inventory` based on its own preferences.
- Architect review proposed removing user-specified domains because "SSOT violation" outweighed user intent.

## 3a-bis. Count-fixation guidance (added 2026-04-25 from user feedback)

**Real users don't fixate on exact domain or product counts in the FREE-TEXT VIBE.** §3c (`model_vibes` natural-language count clamp) was originally added so a TEST RUN with `model_vibes="exactly 3 domains and ~15 products"` could finish in ~30 min instead of producing a 200-product behemoth. The vibe-derived count clamping is TEST INSTRUMENTATION, not a product requirement for vibe-based usage.

**HARD CARVEOUT — `business_domains` WIDGET is NOT relaxed.** §3b stays absolute:
- If the user POPULATES the `business_domains` widget, the agent MUST produce EXACTLY those domains, verbatim. No additions, no removals, no renames. This is contractual, not a soft target.
- This applies regardless of what the free-text vibe says. The widget OUTRANKS the vibe.

**The PRIMARY goals are:**
1. **Quality models** — correct domain boundaries, healthy FK density, attribute completeness, accurate types, working metric views, no orphan tables, structural integrity (no cycles, no bidirectional FKs, no SSOT violations).
2. **Zero errors** — no NameError / NoneType / ValueError, no fidelity-gate failure, no install crash, no DDL [COLUMN_ALREADY_EXISTS], no unhandled exception path.

**De-prioritize (vibe-only):**
- VIBE COUNT VIOLATION enforcement when the count comes from FREE-TEXT vibes (not the widget). Already de-tautologized in v0.8.9 NEW-2.
- Vibe-derived product-count clamps that fight the LLM.
- Anything that adds code complexity to enforce "exactly N" from natural-language vibes.

**Relax (vibe-only):**
- Architect-gate failures for "tier-inappropriate" tiny vibes (v0.8.9 NEW-4 covers global; v0.9.4+ should NOT also patch per-domain — let those gates emit a warning, that's fine).
- §3c product-count over/undershoot when source is vibe — log INFO, do not error or trim aggressively.

**Keep absolute (widget-driven):**
- §3b `business_domains` widget — verbatim preservation (HARD).
- `must_have_data_products` widget — verbatim preservation (HARD).
- Structural-integrity invariants (no cycles, no orphans, no broken FKs) — these are quality, not count.

When triaging logs, PASS the count-related warnings ONLY if they originated from a FREE-TEXT vibe directive. Widget-driven count violations are still HARD failures. Burn cycles on NameErrors, install failures, fidelity drift, and unlinked _id columns first.

---

## 3b. User-specified business_domains is HARD, NON-NEGOTIABLE

IF THE USER SETS THE `business_domains` WIDGET (OR ANY EQUIVALENT INPUT SPECIFYING DOMAIN NAMES), THOSE DOMAINS MUST APPEAR IN THE FINAL MODEL VERBATIM. THE AGENT MAY ADD MORE DOMAINS IF THE MODEL SCOPE REQUIRES IT, BUT MAY NEVER REMOVE, RENAME, OR SUBSTITUTE A USER-SPECIFIED DOMAIN.

Violations to prevent:
- Ensemble + judge synthesising a DIFFERENT list (e.g. user says "customer, order, product" → pipeline builds "fulfillment, inventory")
- Architect review removing a user-specified domain because of SSOT/scope
- Architect review renaming a user-specified domain for "consistency"

The user's `business_domains` list is the SINGLE SOURCE OF TRUTH for minimum required domains. Treat every name in it as IMMUTABLE across the whole pipeline (like `must_have_data_products` today). The ensemble + judge MUST preserve them; if they don't appear in any ensemble variant, the judge MUST inject them; Step 3.7 Principal Architect and Step 3.6 Domain Architect MUST treat them as protected.

## 3a-bis. Global `__AGENT_VERSION__` constant — HARD RULE (added 2026-04-27)

EVERY VERSION OF THE AGENT MUST EXPOSE THE RUNNING VERSION AT TWO PLACES, OR THE FIX IS NOT DONE:

1. **First non-comment line of code in `agent/dbx_vibe_modelling_agent.ipynb` Cell 1:**
   ```python
   __AGENT_VERSION__ = "<single-digit-semver>"  # alias=agent-version-global
   ```
   - The literal MUST be the FIRST statement after the cell-header comment, BEFORE any other constant, import, or class definition.
   - The string value MUST follow §3a single-digit semver (e.g. `"0.6.9"`, `"0.7.0"`, `"1.0.0"` — never `"0.6.10"`, `"0.10.0"`).

2. **First top-level property of every generated `model.json`:**
   ```json
   {
     "agent_version": "<same-value-as-__AGENT_VERSION__>",
     "model_requirements": { ... },
     "_vibe_session_metadata": { ... },
     "model": { ... }
   }
   ```
   - The key is `agent_version` (snake_case, no leading underscore).
   - The value MUST equal `__AGENT_VERSION__` verbatim — no derivation, no prefix, no suffix.
   - Every model.json rewrite path (metric-view writeback, install metric-view cleanup, install location update) MUST refresh `agent_version` to the running agent's value so an older model.json gets re-stamped on rewrite. NEVER leave stale `agent_version`.

**Pre-deploy mutation rule:**
- BEFORE EVERY TEST CYCLE: bump `__AGENT_VERSION__` to the new single-digit semver, commit, deploy. The deployed notebook archive name MUST match (`dbx_vibe_modelling_agent_v<NN>` where `NN` is `__AGENT_VERSION__` minus dots — e.g. `0.6.9` → `_v69`, `1.0.0` → `_v100`).
- BEFORE EVERY TAG-TO-MAIN: decide the next semver, write it into `__AGENT_VERSION__` in the SAME commit that updates `readme.md`, then push. The tag and the constant must agree.
- The audit grep `grep -E '__AGENT_VERSION__\s*=\s*"<expected>"' agent/dbx_vibe_modelling_agent.ipynb` is part of §10.7 Step 6 deployed-archive verification.
- Behavioural test in `tests/unit-tests/test_v<NN>_behavioral.py` MUST assert: (a) constant equals expected, (b) it is the first non-comment code statement in Cell 1, (c) generated `model.json` has `agent_version` as the first key with the same value, (d) every rewrite path refreshes/prepends the key.

**Why this rule exists:**
- Audit cannot tell which agent version produced a given `model.json` from filename alone (versioned volume paths can be re-overwritten by a `vibe modeling of version` operation).
- Every regression report must cite the agent version that produced the artifact; a missing `agent_version` field is a §8.1 invariant violation that blocks honest scoring.
- The constant being the FIRST line of code makes a stale-deploy detectable by visual inspection without grep.

Violations that are §8.1 hard fails:
- Bumping `__AGENT_VERSION__` AFTER the deploy and forgetting to re-deploy → live notebook reports the OLD version while local says the NEW one.
- Forgetting to update `agent_version` in `model.json` rewrite paths → stale value persists across surgical/install passes.
- Two-digit semver segment (`"0.6.10"`) → §3a violation that propagates into model.json.
- Using `version` or `__version__` instead of the canonical `__AGENT_VERSION__` constant → audit grep fails.

## 3a. Single-digit semver — HARD RULE

EVERY SEGMENT OF THE VERSION NUMBER IS A SINGLE DIGIT 0-9. NEVER TWO OR MORE DIGITS IN ANY SEGMENT. WHEN A SEGMENT REACHES 9, THE NEXT BUMP ROLLS IT TO 0 AND CARRIES +1 TO THE SEGMENT TO ITS LEFT.

Examples:
- v0.7.8 → next patch → v0.7.9
- v0.7.9 → next patch → v0.8.0 (not v0.7.10)
- v0.9.9 → next patch → v1.0.0 (not v0.9.10, not v0.10.0)
- v1.0.0 → next patch → v1.0.1

The workspace notebook name MUST match the semver minus dots:
- v0.7.9 → dbx_vibe_modelling_agent_v79
- v0.8.0 → dbx_vibe_modelling_agent_v80
- v1.0.0 → dbx_vibe_modelling_agent_v100 (first 3-char notebook name)

NEVER emit v0.7.10, v0.10.0, v0.7.12 — these are INVALID under this scheme.

## 4. No lazy route, ever

WHENEVER I GIVE YOU TASK TO DO, NEVER EVER CHOOSE THE LAZY ROUTE, TO MINIMISE YOUR WORK, NEVER. ALWAYS USE THE MOST RIGHT APPRACH AND DO THE MOST RIGHT THING. NO CONSTRAINTS WHAT SO EVER.

## 5. Critique my approach

WHENEVER I GIVE YOU A TASK AND DESCRIBE WHAT TO DO, ASSUME I KNOW NOTHING AND ALWAYS CRITISIZE MY APPROACH, AND OFFER BETTER APPROACH IF THERE IS ONE, IF MY APPROACH IS THE BEST ONE, FOLLOW IT.

## 6. Brutal self-honesty score — MUST DO, EVERY ACTION

THIS IS CRITICAL YOU CANNOT SKIP --> FOR EVERY ACTION THAT YOU PERFORM I WANT YOU TO ASSASE YOUR WORK AND PROVIDE BRUTAL HONESTY SCORE (0%-100%) OF HOW DID YOU DO THE ASK WITH DETAILED JUSTIFICATIONS FOR YOUR SCORE, FOCUSE HEAVILY ON WHAT DID YOU MISSED OR WHAT COULD YOU HAVE DONE BETTER. MUST DO THIS. YOUR OUTPUT AND THE SCORE WILL GIVEN TO ANOTHER MORE POWERFUL LLM TO JUDGE IT AND SCORE AGAIN, SO BE VERY CAREFUL AND 100% HONEST ABOUT YOUR SCORE OR YOU WILL BE EXPOSED.

---

## 7. Review methodology (apply before any code change)

Review this plan thoroughly before making any code changes. For every issue or recommendation, explain the concrete tradeoffs.

### Engineering preferences (use these to guide your recommendations)

- DRY is important — flag repetition aggressively.
- Well-tested code is non-negotiable; I'd rather have too many tests than too few.
- I want code that's "engineered enough" — not under-engineered (fragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity).
- I err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
- Bias toward explicit over clever.

### 7.1 Architecture review

Evaluate:
- Overall system design and component boundaries.
- Dependency graph and coupling concerns.
- Data flow patterns and potential bottlenecks.
- Scaling characteristics and single points of failure.
- Security architecture (auth, data access, API boundaries).

### 7.2 Code quality review

Evaluate:
- Code organization and module structure.
- DRY violations — be aggressive here.
- Error handling patterns and missing edge cases (call these out explicitly).
- Technical debt hotspots.
- Areas that are over-engineered or under-engineered relative to my preferences.

### 7.3 Performance review

Evaluate:
- N+1 queries and database access patterns.
- Memory-usage concerns.
- Caching opportunities.
- Slow or high-complexity code paths.

### 7.4 For each issue you find

For every specific issue (bug, smell, design concern, or risk):
- Describe the problem concretely, with file and line references.
- Present 2–3 options, including "do nothing" where that's reasonable.
- For each option, specify: implementation effort, risk, impact on other code, and maintenance burden.
- Give me your recommended option and why, mapped to my preferences above.
- Then explicitly ask whether I agree or want to choose a different direction before proceeding.

### 7.5 Workflow and interaction

- Do not assume my priorities on timeline or scale.

### 7.6 Review output format — MUST follow

FOR EACH STAGE OF REVIEW: output the explanation and pros and cons of each stage's questions AND your opinionated recommendation and why, and then use AskUserQuestion. Also NUMBER issues and then give LETTERS for options, and when using AskUserQuestion make sure each option clearly labels the issue NUMBER and option LETTER so the user doesn't get confused. Make the recommended option always the 1st option.

### 7.7 2-minute timeout on AskUserQuestion

If I present an AskUserQuestion and the user does not answer within 2 minutes, I proceed with the **recommended option** (the first option labeled "(Recommended)") without re-asking or stalling. This keeps the autonomous loop moving when the user is away, asleep, or in a meeting. If the user answers late and contradicts the auto-choice, I revert and redo that piece. If the user is actively chatting (answering recent messages), this timeout does NOT apply — it's only for away/sleep mode.

---

## 8. Honesty invariants — DO / DON'T

Added 2026-04-23 after an audit exposed a "v0.8.0 shipped, 66/100 implemented" claim while every sub-fix was in an orphan commit unreachable from `dev`. These rules are permanent.

### 8.1 Defining "done"

**DO** verify ALL before claiming a fix is done:
- Code on disk in target file
- Syntax-checked
- Unit test exists AND exercises the failure mode AND passes
- At least one call site exists (for helpers)
- `git branch --contains <sha>` returns target branch
- `git push` succeeded → `git ls-remote origin <branch>` includes the SHA
- Deployed notebook re-exported + grep confirms the change

**DON'T**:
- Call a helper with 0 callers a "fix"
- Call a local commit "on dev" before verifying reachability + push
- Say "should work" / "mostly done" / "partial" — it's done per §8.1 or it's 0

### 8.2 Self-scoring

**DO** score against the live target (remote branch / deployed notebook / running system).
**DO** list the specific §8.1 invariant violated for every score deduction.

**DON'T** score against local workspace state when remote differs.
**DON'T** use vague adjectives in score justifications.

### 8.3 No tautologies

**DO** include a test case where the filter MUST exclude and prove it does.

**DON'T** ship filters with `return True  # conservative keep-on-ambiguity` or equivalent.
**DON'T** ship code whose two branches are semantically identical.

### 8.4 No dead code framed as fixes

**DO** ship new helpers + first call site in the same commit.

**DON'T** claim a helper is a fix without a call site.
**DON'T** include zero-caller infrastructure in "implemented" counts.

### 8.5 Industry-agnostic

**DO** read from the live metastore / runtime env for environment-specific values.
**DO** grep the diff for customer strings before every commit.

**DON'T** hardcode customer catalog names, business names, or workspace identifiers in helpers.

### 8.6 Git discipline

**DO** after every `git commit` that claims delivered work:
- `git branch --contains <sha>` (must list target branch)
- `git push origin <branch>` (must succeed)

**DO** sync with origin via `git fetch && git rebase origin/<branch>` or `git fetch && git merge --ff-only origin/<branch>`.

**DON'T** run `git reset --hard <remote>` when local has unpushed commits.
**DON'T** trust `git log --oneline` alone as proof of "committed to dev."

### 8.7 Runner's test

**DO** before saying "shipped," ask: *"If the auditor runs `git log --oneline -3 origin/<branch>` and greps the live target right now, do they see my SHA and my change?"* If no → not shipped.

### 8.8 Audit response

**DO** on audit finding:
1. Verify auditor's evidence mechanically (`git rev-parse`, `git branch --contains`, grep).
2. Recover via cherry-pick if orphan; re-patch if lost.
3. Publish new SHA + sentinel grep + test result.
4. State the root cause in one line.

**DON'T** argue with evidence.
**DON'T** restate the original claim.
**DON'T** hide behind "a hook did it" without proof — and even with proof, own the missing post-commit check.

### 8.9 Check-bias override

**DO** when a check returns the answer you wanted, re-run with a harder probe.

**DON'T** accept "looks green" as proof.
**DON'T** skip §6 self-score because "session complete."

### 8.10 No-op patches are §8.4 violations (added 2026-05-19 from v0.7.6 P26 audit)

A patch that LOGS a `FIRED` line but does NOT mutate the system state is a **no-op observability patch**, not a fix. It satisfies the static-grep test ("alias is in the file") but does not change downstream behavior. v0.7.6 P26 (`vreq-target-revalidate-on-execute`) was the canonical violation: it computed `_revalidate_resolved` via last-component fuzzy match, logged FIRED, then still appended the mutation to `skipped` without retrying — so the v0.7.5 healthcare `unlinked_fk REMEDIATE` adherence ceiling (84.2%) persisted into v0.7.6 despite the "fix".

**DO** for every patch claiming to fix a failure mode:
1. Identify the OBSERVABLE downstream state change the patch must produce (e.g. "FK column gets `foreign_key_to` set", "domain gets removed from output model", "config flag becomes True").
2. Write a BEHAVIORAL test that:
   - Sets up minimal model state where the failure mode would fire pre-patch.
   - Calls the production code path (NOT a stub) end-to-end.
   - Asserts the OBSERVABLE state change.
   - **Proves it fails on pre-patch HEAD** (run `git stash push` → `pytest` → expect failure) before claiming the patch fixes anything.
3. Static-grep contracts (`assert "string" in src`) are SMOKE checks only — they prove code shape, not behavior. Every patch needs ≥1 behavioral test alongside.

**DON'T**:
- Ship a patch whose ONLY effect is a log line (FIRED / MISS / SKIP).
- Ship a patch where the FIRED log fires but the downstream code path takes the same branch it would have taken without the patch.
- Count a static-grep `assert "alias=foo" in src` test as proof the patch fixes the failure mode — that's §8.3 tautology dressed up as testing.
- Accept "the test passes" without first verifying the test FAILS on the pre-patch HEAD (otherwise it's tautological).

**Sentinel: at audit time, every alias in `__AGENT_VERSION__` history must have BOTH:**
- A `[<alias> FIRED]` log emission site in the agent notebook.
- A behavioral test (not just a static-grep assertion) that demonstrates the patch changes observable state.

**Why this rule exists:** The v0.7.6 P26 no-op was caught only because v0.7.7 review re-read the actual code. A weaker reviewer would have seen "23/23 tests pass" + "FIRED log present in code" and shipped the run, then watched the same v0.7.5 84.2% adherence ceiling re-appear and called it "stubborn LLM behavior". The honest cost of skipping behavioral testing is one wasted ~$200 tier-1 industry pipeline run. The rule pays for itself per shipped patch.

## 9. Model-level validation methodology — what to check, how to check it, what to report

This section captures the **model-level validation protocol** used to audit every pipeline run (new base model, vibe-modeling-of-version, shrink, enlarge, install). It is distinct from §7 (code review). Apply §9 after every pipeline terminal state before claiming "run looks good."

### 9.1 Intent — validate the *output* of the agent, not the code

The agent produces data models (model.json) + physical schemas + metric views + tags. §9 audits THESE ARTIFACTS. Code quality matters (§7) but only insofar as it produced a correct model.

### 9.2 Inputs to collect BEFORE running any check

1. **User vibe string** — verbatim from `model_vibes` widget / `business_description`. Save the exact text so §3c comparisons are evidence-based, not paraphrased.
2. **Widget params** — business_name, business_domains, data_model_scopes, operation, model_version, naming_convention, generate_samples, cataloging_style.
3. **JobTags snapshot at terminal** — `{'dbx_vibe_modelling_domains': N, '_products': N, '_attributes': N, '_foreign_keys': N, '_tags': N, '_metrics': N}`.
4. **model.json snapshot** for EVERY sub-version produced (ecm_v1, mvm_v1, mvm_v2, mvm_v3, ecm_v2, ...). Save to `/tmp/<run>_models/<version>/model.json` with its sibling `vibes/next_vibes.txt`.
5. **All info + error logs** from `/Volumes/<catalog>/_metamodel/vol_root/logs/<business>/<version>/<business>_{info,error}_v{N}_{ecm|mvm}.log` and the merged tester logs `logs/vibe_tester/<ts>/{test_summary,merged_info,merged_error,quality_report}.log`.
6. **Physical catalog state** via `databricks schemas list` and `databricks tables list` on the deployment catalog to verify R2 install parity.

### 9.3 Per-model checks (run for EVERY sub-version produced)

#### 9.3.1 Counts table
Counts to extract from model.json + cross-check with JobTags:

| Metric | How to compute from model.json | Expected behaviour |
|---|---|---|
| Domains | `len(model['domains'])` | Matches user `business_domains` widget (§3b) |
| Products | `sum(len(d['products']) for d in domains)` | Close to user vibe "~N products" target (§3c). Tolerance ±20% for soft targets, 0% for "exactly N" |
| Attributes | `sum(len(p['attributes']) for d,p in iter_all_products)` | Typical range 30–50 per product. Trim if >60, augment if <12 |
| Foreign keys | `sum(1 for a in all_attrs if a.get('foreign_key_to'))` | Healthy density: 30–70 FKs for 15-product tiny; 500–900 for 160-product airlines. Overlinked >25% FKs-per-product is red flag |
| Tags | `len(model.get('metric_views', []))` cross with JobTags `_tags` | Cross-check — if physical `_tags` count diverges from model.json, R2-class drop |
| Metric views | `len(model.get('metric_views', []))` vs physical `SHOW TABLES IN <cat>._metrics` | MATCHES — if physical < declared, R2 regression |
| Quality score | Parse from `vibes/next_vibes.txt` `**Model Quality Score: N/100**` | Trend matters: should monotonically improve v1→v2→...; dropping is a signal |

#### 9.3.2 §3b / §3c user-vibe authority compliance

For EVERY model:
- **§3b domain check:** Every name in user's `business_domains` widget MUST appear verbatim in `[d['name'] for d in domains]`. No renames, no merges. Additional domains allowed ONLY if user vibe explicitly permits.
- **§3c product-count check:** Against user vibe phrase pattern (`~N products`, `exactly N products`, `intentionally tiny`, `do not expand`, etc.). "Exactly N" → ±0. "~N" → ±20%. "Do not expand" → no growth vs baseline.
- **§3c domain-count check:** If user said "exactly 3 domains", the model MUST have exactly 3 — no judge-added domains (like `reference`, `shared`, `analytics`) unless user permits.
- **Enlarge tests are the hardest §3c probe** — agent's default instinct is to scale; user vibe must override. If enlarge produces 10× products ignoring "intentionally tiny", that's a critical §3c violation (seen in v0.8.1, fixed in v0.8.3).

#### 9.3.3 Structural integrity checks (grep the info + error logs)

| Check | Log pattern | Pass | Fail |
|---|---|---|---|
| FK cycles | `[CYCLE DETECTION]` | `✅ No cycles detected in FK relationships` | `Found N cycle(s)` — list each cycle path; any >0 = R8 present |
| Bidirectional FKs | `[BIDIRECTIONAL DETECTION]` | `✅ No direct bidirectional links found` | `🚨 Found N DIRECT BIDIRECTIONAL LINK(S)` — identify the A↔B pair |
| Siloed products | `SILOED TABLES DETECTED` / `silo` | 0 warnings | product has zero FK in and zero FK out — F4 present |
| SSOT violations | `cross_domain_duplicate` | 0 | Two domains own same entity name |
| Self-FKs on PKs | grep model.json where `foreign_key_to == "{same_domain}.{same_product}.{same_pk}"` | 0 | Each self-FK = 1 anti-pattern violation (F2-era pattern) |
| Denormalized natural keys | `[SA:denormalized_natural_key]` | 0 | FK + natural key for same entity coexist |
| Fidelity gates | `Fidelity gates FAILED` | precision ≥ 0.85 | `precision < 0.85 — rollback recommended` = Memory/JSON drift (N2) |
| Post-normalization unlinked `_id` | `Step 4.8: N unlinked _id columns remain` | 0-5 | >10 = IDL or CDL dropped too many candidates |

#### 9.3.4 Per-domain breakdown

Build a per-domain table with products, attrs, FKs-out. Red flags:
- One domain has >2× the FKs of any other (over-hubby)
- Domain with zero FKs-out AND zero FKs-in (isolated subgraph)
- FK-out count > attribute count (nonsensical)
- "shared" / "reference" domain with >5 products (should be lookup-only, see `feedback_shared_domain_strict`)

#### 9.3.5 Metric view parity (R2 probe)

After install tests:
- `databricks tables list <catalog> _metrics --profile <profile>` → count N_physical
- Compare to `len(model.metric_views)` = N_declared
- If N_physical < N_declared → R2 regression. Identify which metric views dropped and why (usually UNRESOLVED_COLUMN class R6 — grep error log for `Failed metric view '<name>'`).

#### 9.3.6 Vibe adherence (for any `vibe modeling of version` output)

If v→v+1 operation produced a new model from `next_vibes.txt` input:
1. Parse v1 `next_vibes.txt` — enumerate every PRIORITY (`PRIORITY N — <action>: <target>`) and every SA finding (`[SA:<class>] <detail>`).
2. For each PRIORITY, search v2 logs for `[MUTATION-BATCH]`, `[MUTATION-SUMMARY]`, and `action '{action}'` outputs. Map: applied (count in mutation summary), skipped (by_reason), or absent (no mention).
3. For each SA finding, check whether v2's static analysis still shows the same finding (run post-v2 static analysis or compare static-analysis output logs).
4. Adherence % = (applied SA findings + applied PRIORITIES) / total. Soft-accept bias: don't count "Max retries exhausted, proceeding with errors" as applied — those are silent drops.

#### 9.3.7 Cross-version delta (v1 vs v2, or ECM vs MVM from shrink/enlarge)

Compute and report:
- ΔD, ΔP, ΔA, ΔFK, ΔMV
- Products added / removed (set diff of `(domain, product)` tuples)
- FKs added / removed (set diff of `(domain, product, attribute, foreign_key_to)` tuples)
- Renames (products with same position but different name — heuristic: positional index in domain's products list)
- Domain-description semantic shift (if Memory/JSON descriptions diverge)

### 9.4 Pattern-based failure signatures to watch for

Keep this watchlist in the monitor prompt on every run. If a signature is detected, report as PRESENT / ABSENT / NEW-SITE and cite the verbatim log line.

| ID | Signature (grep pattern) | Class |
|---|---|---|
| F1 | `/tmp/.*_model_data.*PermissionError` or `[Errno 13] Permission denied` on `/tmp/` | Serverless /tmp anti-pattern |
| F2 | `Max retries (3) exhausted. Proceeding with last response despite validation errors` | Soft-accept hatch |
| F4 | `SILOED TABLES DETECTED` | Graph-integrity |
| F6 | `KeyError '0,62'` or similar format-string KeyError | Prompt template bug |
| F7 | Parent run exits SUCCESS while child FAILED; 30–60s parent durations | Launch-gate fake-success |
| F10 / R2 | Physical `_metrics` count < declared `metric_views` | Install-time metric-view drop |
| R1 | `SELECT version FROM _metamodel.business` returns only v=1 after "vibe modeling of version" | In-place overwrite |
| R3 | `wc -l info.log` returns 0 after SUCCESS | Log truncation on final merge |
| R6 | `[Metrics] Failed metric view '<name>'.*UNRESOLVED_COLUMN` | Metric-view ↔ normalizer contract mismatch |
| R7 | `[MODEL-PARAMS] <field> missing from LLM output — using midpoint N` | LLM JSON-schema non-compliance |
| R8 | `[CYCLE DETECTION] Found N cycle(s)` where N > 0 after finalization | FK cycle recurrence |
| R8b | finalization `[CYCLE DETECTION] ✅ No cycles` BUT the output `model.json` still has FK cycles (SCC on the nested dict > 0) | Lying-scoreboard: the flat-list finalization breaker (`_v394` on `products_data/attributes_data`) ran clean, but cycles persisted in the NESTED `data_model` serialized to model.json (VOV sandbox-authoritative FK adds / SSOT resolver / flat↔nested desync). Live: mfg vov_v3 <profile> run <run_id> = 11 SCC cycles, finalization said 0. FIXED v4.0.3 `v403-serialize-cycle-guard` (deterministic detect+break on the nested dict at the model.json serialization boundary). PRESENT if `[v403-serialize-cycle-guard FIRED]` reports `remaining>0`, or model.json SCC > 0 on any run. |
| N1 | install test failure at ~50-60s with `Workload failed, see run output for details` + no info log on volume | Install early-exit, no diagnostics |
| N2 | `Fidelity gates FAILED: precision < 0.85 — rollback recommended` | Memory/JSON attribute-name drift |
| N3 | `⚠️ DBML FK SCRUB: Skipping dangling ref` (cosmetic) | DBML exporter naming drift |
| N4 | `mutator raised: AttributeError: '<scalar>' object has no attribute '<append/get/extend>'` recurring across all 3 retries → `rejected_unsafe` (VREQ lost) | Mis-directed retry hint: the generic `_v204_ast_class_hints` needle assumed the bad value was a DICT and gave dict-only advice, so the LLM kept crashing on a STRING scalar field. FIXED v4.0.2 `vov-scalar-attr-typed-hint` (type-accurate advice + suppress contradictory dict hint). PRESENT if a `'str'/'int'/'float' object has no attribute` crash survives all retries with NO `STRING-NOT-LIST`/`TYPE-MISMATCH` hint in the trace. |
| N5 | `[UC-DDL] ■ Finished SET TAGS in NN:NN` where NN > ~20min at 8 workers (e.g. mfg 14585 stmts = 28min, 0 failures) | Tag-DDL wall-clock is the post-VOV bottleneck (~6% of tier-1 runtime). NOT a defect — the 8-worker cap (`TAG_DDL_MAX_WORKERS`, `settags-sparkconnect-concurrency-cap`) is CORRECT (prevents the 97.7% Spark-Connect-saturation failure cascade). The ONLY proven safe speedup is routing tag DDL through a SQL-Warehouse REST endpoint (v3.6.6 repro: 1800 tags @ 60 workers = 0% fail, 12/s). Do NOT naively raise the worker cap — that reintroduces the cascade. |
| N6 | A `[VOV-2.0 LLM BRIDGE FIRED]` line with large `output_chars` (>150K) is the LAST non-flush content line, then ONLY `[VolumeLogFlush]` lines for >25min while the run stays RUNNING (the "looks-alive-but-stalled" hang). Live: ngo shrink-ecm v397 run <run_id> sat 82min with one 158K-char bridge output as the last content line, zero progress, then was killed. | Silent main-thread hang AFTER a successful LLM bridge return. Sandbox subprocess (240s) and `ai_query` (240s/360s) BOTH have enforced timeouts, so the hang is NOT those — it is pure-Python post-processing of the huge payload OR a bounded-pool nested-submission deadlock (`_SharedPoolHandle.__exit__` does `_cf2.wait(self._futs)` with NO timeout; `run_parallel_with_rate_limit_backoff` uses `mark_guard=False`, so a `run_parallel` call from inside a saturated global-pool worker can block its worker forever). DIAGNOSE: v4.0.4 `heartbeat-stalldump` dumps ALL thread stacks once per stall episode when `app_silent>=600s` — the next occurrence will show exactly which frame each thread is blocked in (`_cf2.wait`, an HTTP read, or a DDL). DETECT: external poller flags STALL when the last non-flush content line is >25min old while RUNNING; kill + relaunch on the latest version. |
| N7 | The `physical_ground_truth` scoreboard pass (`gt-headline-reground`) scores a model-wide STRUCTURAL invariant VREQ (e.g. "every table has a primary key") `failed` while the SAME VREQ scored `fulfilled` on the earlier logical pass, and the physical `failed` verdict becomes authoritative → reported adherence drops below the honest value with the model actually correct. Live: coffee_roastery basemvm run <run_id> = VREQ-005 PK fulfilled 13/13 logical, failed 13/13 physical → 88.9% instead of 100%. | Lying-scoreboard from a LOSSY PHYSICAL SNAPSHOT: `_run_ground_truth_audit` rebuilds the verification snapshot from `information_schema` and enriched `foreign_key_to` from physical FK constraints, but Delta/UC stores NO enforced PK constraint, so the physical snapshot carried ZERO PK signal and the deterministic PK invariant false-failed every table. Same class as the §12.1 tag/MV enrichment. FIXED v4.2.7 `gt-pk-from-model-declared` (enrich the physical snapshot with the model's declared `primary_key` WHEN every declared PK column physically exists in `information_schema.columns` — cannot false-positive nor false-negative; composite-PK-aware). PRESENT if a structural invariant flips fulfilled→failed between the logical and physical passes with no corresponding physical schema change. |

### 9.5 Positive signals to look for (don't regress what works)

Equally important — affirmatively detect and record these, because absence over time signals regression:

- `[VALIDATOR] User vibes detected (N chars) — count limits will be relaxed` → §3c authority firing at validator
- `USER-KING AUTHORITY` in LLM judge/architect prompts and AI logs → §3c authority at LLM level
- `✅ Step N: <name> - PASSED validation` → each step self-verified
- `Architect Self-Review iter N landed=K regressed=0 blocked=0` → corrective actions landing cleanly
- `🛡️ BLOCKED product move: '<name>' is protected` → defense-in-depth guard working even when LLM pushes against it
- `[vov-scalar-attr-typed-hint FIRED v4.0.2]` → type-accurate scalar-attribute retry hint firing (str/int/float `.append`/`.get` crash steered with the RIGHT advice instead of the contradictory dict hint; prevents adherence loss from un-recoverable retries)
- `[vov-deterministic-preskip FIRED v4.0.1]` → a VREQ already satisfied per the deterministic dict probe was credited `applied` WITHOUT spending an LLM synth+verify+sandbox cycle (speed + anti-false-negative; reduces the `noop_failed` empty-diff class)
- `[v403-serialize-cycle-guard FIRED]` with `remaining=0` → the model.json serialization boundary verified the NESTED `data_model` has 0 FK cycles before writing; `cleared=0` on a clean model is the expected idempotent no-op, `cleared>0` means residual cycles that escaped the flat finalization breaker were deterministically broken in place (R8b backstop; user-vibed edges protected per §3c)
- `[HEARTBEAT-STACKDUMP v4.0.4 FIRED]` (only on a genuine stall, `app_silent>=600s`) → the heartbeat localized a silent hang (N6) by dumping every thread's stack ONCE per stall episode; this is a DIAGNOSTIC, so its presence means a real stall occurred AND is now diagnosable (read the dumped frames to see if it is `_cf2.wait`/HTTP/DDL). ABSENCE on a healthy run is the normal state (the helper returns immediately when `app_silent<threshold`)
- `[NORM-FIX] BLOCKED semantic mismatch` → normalizer correctly rejecting a bad join
- `[verifier-domain-create-name-normalize FIRED]` → a vibe domain display name (spaces/punctuation) was matched to its space-collapsed physical name before scoring, so a domain-create VREQ is no longer false-failed on a pure name-shape mismatch (v4.2.6 anti lying-scoreboard)
- `[verifier-structural-invariant-deterministic FIRED v4.2.6]` → a model-wide PK/FK-resolve/silo/cycle VREQ (`scope_target '*'`) was scored deterministically from the model dict BEFORE any LLM route, so a transient `SparkException` can no longer false-fail it (largest anti lying-scoreboard lever; verdict reads the real after-state so it can neither false-negative nor false-positive)
- `[gt-pk-from-model-declared FIRED v4.2.7]` reporting `N/N physical tables carry a model-declared PK whose column(s) physically exist` → the physical ground-truth snapshot was enriched with the model's declared primary key (grounded on physical column presence), so the deterministic PK invariant scores the true after-state on the PHYSICAL pass instead of false-failing on Delta/UC's absent PK constraint (N7 backstop)
- LLM health: all models `0 timeouts, 0 errors, ✅ healthy` in the runtime-profile summary

### 9.6 Reporting structure (what to write after every pipeline run)

Two documents, saved to `/Users/user/claude/vibe-agent/`:

**A. Validation report (`<run-id>-validation-report.md`):**
1. Summary (commit, run_id, duration, PASSED/FAILED/SKIPPED if via vibe_tester)
2. Per-test or per-phase timeline table with concrete timestamps
3. Complete error inventory — EVERY ERROR verbatim + WARNINGs grouped by tag with counts
4. F1-F10 + R1-R8 + N1-N3 regression table (PRESENT / ABSENT / NEW-SITE + evidence log line)
5. NEW regressions not in the catalogue
6. Positive signals (fixes confirmed, §3a/b/c compliance, honest_score highlights)
7. Recommendations for next version
8. Brutal honesty score for the tested version (§6)

**B. Model quality audit (`<run-id>-model-quality-audit.md`):**
1. Counts table across all sub-versions
2. §3b / §3c compliance verdict per model
3. Per-domain breakdown per model
4. Structural integrity (cycles / silos / self-FKs / SSOT / fidelity gates) per model
5. Metric-view parity per model
6. Vibe adherence (for any "vibe modeling of version" output)
7. Cross-version delta
8. Honest model-quality score (0-100) per sub-version with justification
9. Best model of the N produced — production-usability ranking
10. Comparison vs previous-version baseline (e.g. v0.8.4 audit cites v0.8.3's ecm_v2 = 80/100)
11. Archival paths table
12. Brutal honesty score for the audit itself

### 9.7 What to save for posterity (per run)

| Artifact | Path |
|---|---|
| model.json (per sub-version) | `/tmp/<run_tag>_models/<version>/model.json` |
| next_vibes.txt (per sub-version) | `/tmp/<run_tag>_models/<version>/next_vibes.txt` |
| info + error logs (per sub-version) | `/tmp/<run_tag>_logs/<version>/{info,error}.log` |
| merged tester logs + test_summary | `/tmp/<run_tag>_logs/{merged_info,merged_error,test_summary,quality_report}.log` |
| Physical catalog state dump | `/tmp/<run_tag>_logs/_metamodel_dump.json` (via a small extractor notebook) |
| Validation + audit reports | `/Users/user/claude/vibe-agent/<run-tag>-{validation-report,model-quality-audit}.md` |

### 9.8 Anti-rules — never do this during model-level audit

- **DON'T** trust JobTags alone — always cross-check against `_metamodel.business/domain/product/attribute` tables when possible.
- **DON'T** trust terminal SUCCESS as proof the model is usable — §8.7 runner's test: grep the deployed catalog for real tables before claiming "install worked."
- **DON'T** skip the vibe-adherence analysis because it "seems fine" — compute PRIORITY-level mapping. Soft adherence claims get exposed on the next audit.
- **DON'T** treat `Max retries exhausted → proceeding` as applied — it's a silent drop.
- **DON'T** accept structural warnings as "cosmetic" without tracing their downstream effects. (R8 cycles looked cosmetic until a customer hit JOIN divergence.)
- **DON'T** claim "§3c compliance" based on the domain list alone — product count, attribute count, and scope-creep-on-enlarge all matter.

### 9.9 Update cadence

Append a new regression signature or positive signal to §9.4/§9.5 whenever a novel pattern appears in a production run. The catalogue is the memory — keep it fresh.

---

## 10. HOW TO TEST — autonomous fix-and-verify loop (MUST follow on every task)

This is the canonical loop the user expects every coding task to follow. Do NOT ask the user to repeat any of these steps — execute them yourself and report progress.

### 10.1 Inputs the user provides
1. A previous run's log/error file (e.g. `/Users/user/claude/vibe-agent/error_NN.txt`).
2. Optionally, a Databricks job-run URL whose terminal logs you must collect.
3. A target business and vibe (or "no vibe" for default behaviour).

### 10.2 The loop — repeat until ZERO errors / warnings

For EACH iteration:

1. **Wait for run terminal state** before triaging — `databricks jobs get-run <run_id> --profile <profile>` until `life_cycle_state == TERMINATED`. Use `Bash run_in_background` (NOT Monitor — it requires approvals) to poll.
2. **Collect ALL logs verbatim** — every file under `/Volumes/<catalog>/_metamodel/vol_root/logs/<business>/<version>/` AND `/Volumes/<catalog>/_metamodel/vol_root/logs/vibe_tester/<ts>/` AND any `_install_audit/` mirror. Save to `/tmp/<run_tag>_logs/`.
3. **Read EVERY line** — do not skim. `info`, `error`, AND any `ailogs/*` outputs. Watch for §9.4 signatures (F1–F10, R1–R8, N1–N3) AND §9.5 positive signals.
4. **Watch the progress table** — `_metamodel.progress` (or whatever the live progress sink is) — confirm each step transitions through `stage_started → stage_succeeded`. Any `stage_warning` or `stage_failed` must be triaged.
5. **Triage every emitted warning + error** — root-cause each one. NEVER mark anything as "cosmetic" without tracing its downstream effect (per §9.8). Group by class.
6. **Apply root-cause fixes** in the agent / runner / tester source — NOT symptom patches. Follow §3 (root cause), §3c (user-vibe authority), §3d (search-first/reuse-first/DRY), §3a (single-digit semver). For each fix, place a sentinel comment with the version + alias so future audits can grep for it.
7. **Bump the version** per §3a (single-digit semver) — update readme.md, version-history table, and any embedded version markers in the agent notebook header.
8. **Add unit tests** — every fix gets at least one test in `tests/unit-tests/test_v<version>_<topic>.py` exercising the failure mode. No fix without a test.
9. **Commit + push to `dev`** — one commit per version bump. Commit message MUST list:
   - Each issue (ID, severity, file:line, root cause one-liner)
   - The fix (what changed, with sentinel/alias for grep)
   - How to verify (the exact grep pattern that proves the fix is live)
   - Co-authored-by: Isaac
10. **Verify push reachability** — `git ls-remote origin dev | grep <sha>` and `git branch --contains <sha>` per §8.6/§8.7. NEVER claim "shipped" without this verification.
11. **Re-deploy + re-submit — VERSIONED PATHS ONLY**:
    a. Upload agent to `/Users/user@example.com/dbx_vibe_modelling_agent_v<NN>` (NOT canon path — canon-cache renders post-deploy fixes invisible).
    b. Upload tester to `/Users/user@example.com/vibe_tester_v<NN>` (versioned).
    c. Upload runner to `/Users/user@example.com/vibe_runner_v<NN>` (versioned).
    d. **Patch the JOB definition** so every task's `notebook_task.notebook_path` points at the versioned agent: `databricks jobs reset --json @<patch>` after editing `notebook_path` to `/Users/user@example.com/dbx_vibe_modelling_agent_v<NN>`.
    e. Verify the JOB now points at the versioned path: `databricks jobs get <job_id> | python3 -c "..."` shows all tasks → `dbx_vibe_modelling_agent_v<NN>`.
    f. Then submit a fresh run via `databricks jobs run-now <job_id>`. Each unique versioned path has a UNIQUE workspace `object_id`, so the executor pool's notebook cache CANNOT serve a stale version.
    g. NEVER trust the canon path for deploy verification — always export the versioned archive and grep for the new aliases.
12. **Tail logs aggressively** — start a background poll-and-tail loop (Bash run_in_background, NOT Monitor) that pulls `/Volumes/<catalog>/_metamodel/vol_root/logs/...` every 60s and appends new lines to a sliding `error_NN.txt`. Do NOT stay silent: every PULSE INGEST must surface counts by category.
13. **Repeat from step 2** — until the tester run produces ZERO errors AND ZERO non-positive warnings. "Mostly clean" is NOT acceptable.

### 10.3 After the tiny tester is clean — airline MVM no-vibe judge

Once tiny is 100% clean:
1. Submit an airline MVM run with `model_vibes=""` (no vibe) and the standard widget defaults.
2. Apply §9 model-level validation methodology to the artifacts.
3. Produce the two reports per §9.6 (validation-report + model-quality-audit) under `/Users/user/claude/vibe-agent/<run-tag>-{validation-report,model-quality-audit}.md`.
4. Honest 0–100 score per sub-version (§9.6 B.8) — back every deduction with a §8.1 invariant or §9.4 signature. The user expects 100% honesty; cover-ups will be caught and called out.

### 10.4 Autonomous-mode invariants (when the user is asleep / away)

- Never use `Monitor` — it requires approval and stalls the loop. Use `Bash run_in_background` for every long-running poll/tail.
- Never `git reset --hard` or `--force-push`.
- If a decision is needed via `AskUserQuestion`, wait 2 minutes and pick the **first / Recommended** option (per §7.7).
- Never fabricate a "fixed" claim — every fix must satisfy §8.1 (code on disk + syntax-checked + unit test + first call site + reachability + push verified + deployed grep).
- Never skip §6 brutal honesty score on any iteration. If you skipped it on iteration N, ship it on N+1 with the missed score retroactively recorded.

### 10.5 Commit-message template (HARD requirement)

```
v<version>: <N> root-cause fixes from <previous>-<run_id> tester audit (<class-list>)

ISSUE 1 — <ID> <one-line title> [<severity>]
  ROOT CAUSE: <one-line>
  FILE: <path>:<line>
  FIX: <what changed> (alias=<sentinel-grep-anchor>)
  VERIFY: <grep pattern> — must return >=1 hit on origin/dev

ISSUE 2 — ...
...

TESTS: <N> new unit tests in tests/unit-tests/test_v<version>_*.py
README: version-history row added; alias-table updated.
DEPLOY: workspace archive renamed dbx_vibe_modelling_agent_v<NN>.

Co-authored-by: Isaac
```

### 10.6 What "no errors at all" means (NON-NEGOTIABLE)

The tester is "clean" only when ALL of these are true at run terminal:
- 0 lines matching `ERROR` in any error log.
- 0 lines matching §9.4 F1–F10/R1–R8/N1–N3 signatures.
- 0 `Max retries (3) exhausted` lines (R7/F2 silent-drop hatch).
- 0 `[CYCLE DETECTION] Found N cycle(s)` where N>0.
- 0 `Fidelity gates FAILED` lines.
- 0 `name '<X>' is not defined` `NameError` lines.
- 0 `[Metrics] Failed metric view` lines.
- 0 `Workload failed, see run output for details` parent-task lines (with no info log).
- All §9.5 positive signals firing where applicable.

If even one of these is non-zero, you have NOT completed the iteration — go back to step 6 in §10.2.

---

### 10.7 TESTING PROTOCOL — STEP-BY-STEP RECIPE (NEVER SKIP)

This is the canonical cookbook. NEVER skip a step. NEVER take shortcuts. NEVER assume any state from a prior run carries over correctly.

**Inputs you need:**
- A version number `NN` (single-digit semver per §3a; never 2-digit segments).
- The Databricks workspace profile (e.g., `<profile>`).
- The canonical tester JOB id (e.g., `191701398472200`).
- The target run scope (tiny tester / airline MVM no-vibe / etc.).

**Step 1 — Code change + commit + push.**
- Apply the fix in `agent/dbx_vibe_modelling_agent.ipynb` and any related notebook.
- Run `python3 -m pytest tests/unit-tests/` and verify all NEW tests pass; pre-existing failures unchanged.
- Each fix MUST self-report a `[<alias> FIRED]` log line at runtime (no silent fixes).
- Commit with the §10.5 commit-message template. Push to `origin/dev`.
- `git ls-remote origin dev | grep <sha>` — if not present, you didn't ship.

**Step 2 — DROP all non-system catalogs (no exceptions).**
```bash
databricks catalogs list --profile <profile> -o json \
  | python3 -c "import json,sys;d=json.load(sys.stdin);
[print(c['name']) for c in (d.get('catalogs',d) if isinstance(d,dict) else d)
 if c.get('catalog_type','')!='SYSTEM_CATALOG'
 and c.get('name') not in ('hive_metastore','samples','system','__databricks_internal')]" \
  | while read CAT; do
      databricks catalogs delete "$CAT" --force --profile <profile>
    done
```
Verify: `databricks catalogs list` shows ONLY system catalogs.

**Step 3 — DELETE all prior runs of the canonical JOB.**
```bash
databricks jobs list-runs --job-id <JOB_ID> --limit 25 --profile <profile> \
  | tail -n +2 | awk '{print $2}' \
  | while read RID; do
      [[ "$RID" =~ ^[0-9]+$ ]] || continue
      databricks jobs delete-run "$RID" --profile <profile>
    done
```
Verify: `databricks jobs list-runs --job-id <JOB_ID>` shows empty.

**Step 4 — DELETE all OTHER jobs (keep ONLY the canonical JOB).**
```bash
databricks jobs list --profile <profile> | grep -E "^[0-9]+\s" | awk '{print $1}' \
  | while read JID; do
      [ "$JID" = "<JOB_ID>" ] && continue
      databricks jobs delete "$JID" --profile <profile>
    done
```
Verify: `databricks jobs list` shows ONLY the canonical JOB.

**Step 5 — Upload agent + tester + runner to VERSIONED paths at user-root.**
```bash
WS="/Users/<user>@example.com"
databricks workspace import "$WS/dbx_vibe_modelling_agent_v<NN>" --file agent/dbx_vibe_modelling_agent.ipynb --format JUPYTER --language PYTHON --overwrite --profile <profile>
databricks workspace import "$WS/vibe_tester_v<NN>" --file tests/vibe_tester.ipynb --format JUPYTER --language PYTHON --overwrite --profile <profile>
databricks workspace import "$WS/vibe_runner_v<NN>" --file runner/vibe_runner.ipynb --format JUPYTER --language PYTHON --overwrite --profile <profile>
```
NEVER deploy to canon path `agent/dbx_vibe_modelling_agent`. NEVER skip the version suffix. Each version archive has a unique workspace `object_id` so the executor cache cannot serve a stale version.

**Step 6 — Verify versioned archive content.**
```bash
databricks workspace export "$WS/dbx_vibe_modelling_agent_v<NN>" --format JUPYTER --profile <profile> --file /tmp/v<NN>_check.ipynb
for marker in <list-of-aliases>; do
  count=$(grep -c "$marker" /tmp/v<NN>_check.ipynb)
  echo "  $marker: $count"
done
```
Every alias from this version's commit MUST appear ≥1 in the deployed archive. If any is 0 — STOP and re-deploy.

**Step 7 — Patch the JOB definition to point at the versioned agent.**
```bash
databricks jobs get <JOB_ID> --profile <profile> > /tmp/job.json
python3 -c "
import json
d=json.load(open('/tmp/job.json'))
js=d['settings']
NEW='${WS}/dbx_vibe_modelling_agent_v<NN>'
for t in js.get('tasks',[]):
    nbk=t.get('notebook_task',{})
    if 'dbx_vibe_modelling_agent' in nbk.get('notebook_path',''):
        nbk['notebook_path']=NEW
json.dump({'job_id':d['job_id'],'new_settings':js}, open('/tmp/job_patch.json','w'))
"
databricks jobs reset --json @/tmp/job_patch.json --profile <profile>
```
Verify: `databricks jobs get <JOB_ID>` shows every task `notebook_path` = `dbx_vibe_modelling_agent_v<NN>`.

**Step 8 — Submit the run.**
- For the canonical tiny tester pipeline: `databricks jobs run-now <JOB_ID> --profile <profile>`.
- For a custom one-off run (different business / no-vibe): `databricks jobs submit --json @/tmp/<run_spec>.json --profile <profile>` where the JSON specifies a single task with `notebook_task.notebook_path = "$WS/dbx_vibe_modelling_agent_v<NN>"`.
- Capture the new `run_id`. Add it to your tracking task (`TaskUpdate`).

**Step 9 — Start the autonomous poller.**
- Background bash (NOT `Monitor` — needs approvals): every ~120s, `databricks fs cp` every log file under `/Volumes/<catalog>/_metamodel/vol_root/logs/...` to a local mirror; categorize new lines; append a PULSE block to `/Users/user/claude/vibe-agent/error_NN.txt`.
- Start a 5-minute pulse loop that prints `state + per-task progress + last 10 log lines + commentary` to stdout.

**Step 10 — Wait for terminate.**
- `until [ "$(databricks jobs get-run <run_id> ...)" = "TERMINATED" ]; do sleep 600; done` — background bash.
- Do NOT prematurely poll. Do NOT use `Monitor`. Do NOT spawn redundant until-loops.

**Step 11 — On terminate: full audit per §9 + §10.6.**
- `databricks fs cp` ALL log files (info, error, ai_logs, install) to `/tmp/v<NN>_logs/`.
- Run `wc -l /tmp/v<NN>_logs/*.log` — record total lines.
- Categorize warnings + errors. Group by signature. Cross-reference against §9.4 / §10.6.
- For each `[<alias> FIRED]` from this version: `grep -c` to confirm the fix actually fired.
- Inspect `model.json` for each sub-version: counts (domains/products/attrs/FKs/MV).
- Per §9.6: write `<run-tag>-validation-report.md` + `<run-tag>-model-quality-audit.md`.
- Honest 0-100 score per sub-version; back EVERY deduction with a §8.1 invariant violation OR §9.4 signature OR §10.6 criterion.

**Step 12 — If terminal != SUCCESS or any §10.6 criterion non-zero → iterate.**
- Identify root cause. NEVER ship a workaround for a real bug.
- Bump version to `NN+1` per §3a (single-digit segments).
- Go back to Step 1.

**Step 13 — If terminal == SUCCESS AND all §10.6 criteria zero → next scope.**
- Tiny tester clean → submit airline MVM no-vibe (§10.3).
- Airline MVM clean → submit airline ECM, then vibe iterations.
- Each new scope STARTS at Step 2 (full cleanup).

### 10.9 POST-MVM VIBE-ITERATION + EXTENSIVE QUALITY AUDIT (NEW MANDATORY PHASE)

After every successful MVM run (Step 13 reports `SUCCESS`), the work is NOT done. The MVM is the FIRST artifact; the agent's value is in the iteration. Run this 8-step audit + iteration phase EVERY TIME without skipping.

**Phase A — Line-by-line log audit of the MVM run** (right after terminate)

A.1 Download every log file from the volume:
```bash
mkdir -p /tmp/<run_tag>_logs
for F in tiny_info_v1_mvm.log tiny_error_v1_mvm.log tiny_ai_logs_v1_mvm.log install_v1_mvm.log ; do
  databricks fs cp "dbfs:/Volumes/<catalog>/_metamodel/vol_root/logs/<biz>/mvm_v1/$F" "/tmp/<run_tag>_logs/$F" --overwrite --profile <profile>
done
```

A.2 Read EVERY line. Not skim. Not grep-only. **Every line.**
- Group warnings + errors by category.
- Cross-reference each category against §9.4 F1–F10/R1–R8/N1–N3.
- For each `[<alias> FIRED]` marker from this version, confirm it actually fired. If not, root-cause why.
- Look at LLM `ai_logs` honesty scores per stage. Score < 80 = quality concern, log it.

A.3 Decide: are there fixes required BEFORE proceeding to next vibes?
- If YES → bump version, repeat §10.7 (full clean reset + re-run MVM).
- If NO → proceed to Phase B.

**Phase B — Run "vibe modeling of version" (next-vibes iteration)**

B.1 Read the v1 model's `next_vibes.txt` artifact:
```bash
databricks fs cp "dbfs:/Volumes/<catalog>/_metamodel/vol_root/business/<biz>/mvm_v1/vibes/next_vibes.txt" /tmp/<run_tag>_next_vibes_v1.txt --overwrite --profile <profile>
```
Enumerate every PRIORITY (`PRIORITY N — <action>: <target>`) and every SA finding (`[SA:<class>] <detail>`).

B.2 Submit a `vibe modeling of version` run with:
- `operation = "vibe modeling of version"`
- `model_version = "1"`
- `model_vibes = ""` (no NEW user-vibes — just consume the auto-generated next_vibes from v1)
- Same business + catalog as v1.

B.3 Use the §10.7 protocol: cleanup the prior runs (but NOT the catalog — vibe-of-version reads v1 from it), upload versioned, patch JOB notebook_path, submit.

B.4 Wait for v2 terminate.

**Phase C — Adherence verification (v1.next_vibes → v2)**

C.1 For each PRIORITY from v1.next_vibes:
- Search v2 logs for `[MUTATION-BATCH]` and `[MUTATION-SUMMARY]` blocks.
- Map: applied (count in mutation summary), skipped (by reason), or absent (no mention).
- A "soft accept" (`Max retries (3) exhausted, proceeding`) does NOT count as applied.

C.2 For each `[SA:<class>]` finding from v1:
- Run static-analysis post-v2 against v2's model.json.
- Compare: did the finding still appear? If yes, the iteration failed to fix it.

C.3 Compute: **adherence % = (applied PRIORITIES + applied SA findings) / total**.
- ≥ 80% → high adherence (good)
- 50–79% → medium
- < 50% → low (vibe-iteration failure)

C.4 Did v2 IMPROVE vs v1?
- Counts (D, P, A, FK, MV) — should change in the direction priorities asked.
- Quality score in v2's next_vibes header — should be > v1's score.
- Structural integrity (cycles / silos / bidirectional) — should not regress.

**Phase D — EXTENSIVE QUALITY AUDIT for BOTH models (v1 + v2)**

This is a deep audit, not a skim. The auditor is a Principal Data Architect with 20+ years of production experience. They WILL NOT run a model in production unless every concern is satisfied. Bias toward FINDING flaws, not justifying them.

For EACH sub-version (v1 and v2 separately):

D.1 **Counts table** (§9.3.1) — exact numbers from `model.json`. Match against tier expectations + user vibes.

D.2 **§3b / §3c compliance** (§9.3.2) — verbatim widget-driven domain names preserved? Vibe-driven counts within tolerance?

D.3 **Per-domain breakdown** (§9.3.4) — products, attrs, FKs-in/FKs-out per domain. Flag:
   - One domain >2× the FK count of any other (over-hubby)
   - Domain with zero FKs in or out (subgraph isolated)
   - FK-out > attribute count (nonsensical)
   - "shared"/"reference" domain with >5 products

D.4 **Structural integrity** (§9.3.3):
   - Cycles? Bidirectional FKs? Self-FKs on PKs? Siloed products?
   - SSOT violations (same entity name in two domains)?
   - Denormalized natural keys (FK + business-key pair on same product)?
   - Fidelity gates precision >= 0.85?
   - Post-norm unlinked _id columns ≤ 5?

D.5 **Metric view parity** (§9.3.5):
   - `len(model.metric_views)` vs physical `SHOW TABLES IN <cat>._metrics`?
   - If physical < declared → R2 regression. Identify which views dropped + why.

D.6 **Real-world architect review (the 20-year-veteran filter)**:
   For each domain, ask:
   - Could a real airline operations engineer use this domain end-to-end?
   - Are the FKs RIGHT — not just structurally valid, but business-correct (passenger.booking → flight.leg, NOT flight.leg → passenger.booking)?
   - Is the cardinality correct (1:N vs N:1 vs M:N)?
   - Is each product worth being a separate entity, OR is it a denormalization that should be inlined?
   - Are key attributes missing (e.g. flight.aircraft_id but no flight.aircraft_tail_number)?
   - Are the attribute types reasonable (BIGINT for monetary? SHOULD be DECIMAL with precision)?
   - PII / classification correctness?
   - Reference data (lookup tables) properly modeled?

   For each issue, classify severity:
   - **CRITICAL** → would break a production query / cause corruption / violate a constraint
   - **HIGH** → would break a downstream consumer / mislead an analyst
   - **MEDIUM** → would require a workaround in production
   - **LOW** → cosmetic / style preference

D.7 **Industry-specific checks** (per business):
   - Airlines: aircraft → maintenance lineage, crew rest periods (FDP), revenue allocation, IATA codes, codeshare
   - Healthcare: encounter → diagnosis → procedure → claim, ICD/CPT lookup, HIPAA tagging
   - Banking: trade → settlement → custody → reconciliation, regulatory reporting
   - Manufacturing: BOM hierarchy, work order → operation → resource, quality lots
   - Retail: SKU → inventory → reservation → fulfillment, channel attribution

   List every industry-canonical pattern the model FAILS to capture.

D.8 **Honest model-quality score** per sub-version (0-100):
   - Document each deduction with the §8.1 invariant violated, the §9.4 signature, the architect-veteran finding, or the structural defect.
   - No vague adjectives. Each deduction = N points + 1-line evidence.

**Phase E — Compile fix plan**

E.1 Group flaws by FILE + ROOT-CAUSE-CLASS.
- "Symptom in 12 metric views" → likely 1 root cause in MV prompt or LLM-spec parser.
- "Multiple bidirectional FKs" → likely a missing reverse-direction guard.

E.2 For each root cause, propose:
- File + line of the fix site
- The fix (one-liner)
- Verification grep pattern for the next run

E.3 Order by impact / risk / effort:
- HIGH IMPACT + LOW EFFORT → ship FIRST
- HIGH IMPACT + HIGH EFFORT → schedule, isolate, behavioral-test
- LOW IMPACT → defer

E.4 Each fix gets its own version bump + behavioral test + `[FIRED]` self-report.

**Phase F — Honesty report of everything done in this audit cycle**

The honesty report MUST cover:

F.1 What was DONE (commits, deploys, runs, audits) with concrete artifact paths.

F.2 What was FIXED (root causes located + patched) — separate from "covered up" / "deferred" / "observability-only".

F.3 What was COVERED UP or rationalized away. Be brutal:
- Did you skip any line of any log? (Phase A.2 violation)
- Did you accept any honesty-score adjective without evidence?
- Did you let a `Max retries (3) exhausted` count as "applied"?
- Did you mark a fix "shipped" without a `[FIRED]` grep on the live run?

F.4 What was NOT FIXED (the unhonest deferred items) — name each one, the file:line, the root-cause hypothesis, and the reason for deferral.

F.5 Brutal honest score for THE AUDIT WORK ITSELF (separate from the model-quality scores). 0–100.

F.6 Final verdict: would a 20-year-veteran architect deploy v1 or v2 to production? If neither, why?

This phase is non-negotiable. Skipping it is a §8.4 / §8.7 violation.

---

### 10.8 Anti-shortcuts (HARD invariants)

- ❌ NEVER deploy to canon path `agent/dbx_vibe_modelling_agent` directly. ALWAYS use `_v<NN>` suffix.
- ❌ NEVER reuse a catalog from a prior version's run. ALWAYS drop catalogs first.
- ❌ NEVER skip Step 6 (deployed-archive grep). Even if you "just deployed" — workspace eventual-consistency means the archive may not have the new content for several seconds.
- ❌ NEVER submit a run before ALL prior runs of this JOB are deleted (Step 3). Stale runs pollute audit triage.
- ❌ NEVER claim a fix is "verified" without a `[<alias> FIRED]` grep hit on the LIVE run's volume info.log.
- ❌ NEVER inflate honesty scores. If a fix didn't fire live, score it 0 for that iteration.
- ❌ NEVER skip writing the validation-report + model-quality-audit (§9.6) for a SUCCESS run. The audit IS the verification.

---

## 10.11 BATTLE-TESTED RECIPE — what "follow test protocol" means (v0.6.1 addendum)

This is the exact recipe that produced the clean v0.6.1 tiny run (5/5 tasks SUCCESS, §10.6 zero-error contract met, deterministic quality score 94/100). When the user says **"follow test protocol"**, **"follow claude.md test protocol"**, or **"test it like you always do"**, execute this section literally, end-to-end, without shortcuts.

### 10.11.1 Pre-flight inputs to collect

Before touching anything:
- Current version `NN` you are about to ship (single-digit semver per §3a; e.g. v0.6.1 → `_v61`).
- Databricks profile (`databricks auth profiles`) — pick the one labelled `<profile>` unless user says otherwise.
- Canonical JOB id (read from `databricks jobs list --profile $PROFILE`).
- Target business + vibe + operation. If not specified: tiny ECM+MVM with the canonical JOB's existing widgets.

### 10.11.2 Step-by-step (gotchas annotated)

1. **Code + commit + push** — fix on disk, run `python3 -m pytest tests/unit-tests/test_v<version>_*.py` and the full regression suite (all prior `test_v*_behavioral.py`). Every fix has a `[<alias> FIRED]` self-report log line. Commit with §10.5 template. Push.

   **GOTCHA A — ensure_ascii matters.** When re-serializing the agent notebook via `json.dump`, pass `ensure_ascii=True`. Using `ensure_ascii=False` converts every `\uXXXX` escape in the original file to its literal unicode character, which blows up the diff to 5000+ lines of pure noise and makes code review useless. Post-edit sanity:
   ```bash
   git diff --stat agent/dbx_vibe_modelling_agent.ipynb
   # Should show tens to hundreds of line changes, NOT thousands.
   ```

2. **Verify reachability** — `git ls-remote origin dev | grep <sha>` must return a hit; `git branch --contains <sha>` must list `dev`. This is §8.6/§8.7 — no exceptions.

3. **Drop non-system catalogs** — `databricks catalogs list -o json` → Python list comprehension skipping `SYSTEM_CATALOG` types and known protected names (`hive_metastore`, `samples`, `system`, `__databricks_internal`). Loop `databricks catalogs delete <name> --force`.

4. **Delete all prior runs of the canonical JOB** — `databricks jobs list-runs --job-id <JOB_ID> --limit 25 -o json`.

   **GOTCHA B — list-runs JSON shape varies.** Newer CLI returns a bare list `[...]`; older returns `{"runs": [...]}`. Handle both:
   ```python
   runs = d if isinstance(d, list) else d.get('runs', [])
   ```
   Then `databricks jobs delete-run <run_id>` for each.

5. **Verify only canonical JOB exists** — `databricks jobs list | grep -E "^[0-9]+\s" | awk '{print $1}'` → delete any id ≠ canonical.

6. **Deploy versioned archives to user-root** — `databricks workspace import "$WS/dbx_vibe_modelling_agent_v<NN>" --file agent/dbx_vibe_modelling_agent.ipynb --format JUPYTER --language PYTHON --overwrite --profile $PROFILE`. Repeat for tester + runner. NEVER deploy to canon path.

7. **Verify deployed archive aliases** — `databricks workspace export "$WS/dbx_vibe_modelling_agent_v<NN>" --format JUPYTER --profile $PROFILE --file /tmp/v<NN>_check.ipynb`. Grep every `[<alias> FIRED]` marker from this version's commit. Each must return ≥1. If any returns 0 — STOP and re-deploy. Workspace import has brief eventual-consistency; retry after 10s.

8. **Patch the JOB** — `databricks jobs get <JOB_ID>` → mutate each `notebook_task.notebook_path` that contains `dbx_vibe_modelling_agent` → `databricks jobs reset --json @<patch>.json`. Verify every task now points at the new versioned path. The new `object_id` means the executor pool CANNOT serve a stale version.

9. **Submit the run** — ALWAYS `databricks jobs run-now <JOB_ID> --no-wait --profile <profile> -o json`.

   **GOTCHA C — `run-now` WITHOUT `--no-wait` blocks the CLI for the full run duration.** If the user (or you) cancels the CLI via Ctrl-C, the submitted run keeps RUNNING in the background and becomes a phantom residual that blocks the next submit due to job-concurrency. If you ever see `QUEUED` for >3 minutes, immediately check `databricks jobs list-runs --job-id <id> --active-only -o json` and `cancel-run` any residuals.

10. **Start background poller** — do NOT use `Monitor` (requires approvals and will stall). Use a bash script in `run_in_background` mode that polls `databricks jobs get-run` + mirrors logs via `databricks fs cp` to a local dir, writing a timestamped pulse block to `/tmp/<ver>_pulses.txt` every ~120s.

    **GOTCHA D — modern Databricks CLI `fs ls` has NO header row.** Do NOT use `awk 'NR>1'` — that skips the first (and often only) entry. Use `awk '{print $1}'`. The canonical poller shape:
    ```bash
    for CAT in $(databricks catalogs list -o json | python3 -c "…skip SYSTEM…"); do
      BASE="dbfs:/Volumes/$CAT/_metamodel/vol_root/logs/tiny"
      for VER in $(databricks fs ls "$BASE" --profile $PROFILE 2>/dev/null | awk '{print $1}'); do
        for F in $(databricks fs ls "$BASE/$VER" --profile $PROFILE 2>/dev/null | awk '{print $1}'); do
          databricks fs cp "$BASE/$VER/$F" "/tmp/<ver>_logs/${CAT}__${VER}__${F}" --overwrite --profile $PROFILE 2>/dev/null
        done
      done
    done
    ```
    Break out of the poller when the top-level state matches `TERMINATED|INTERNAL_ERROR`.

    **GOTCHA E — MVM logs live under the ECM catalog's volume** when the pipeline runs ECM+MVM in one shot. Don't look for a `tiny_mvm_v1` catalog; MVM logs appear as `…/tiny_ecm/…/logs/tiny/mvm_v1/*.log`. The poller loops all non-system catalogs automatically, so this is handled.

11. **5-minute commentary cadence** — every ~300s, read the last 2–3 pulse blocks from `/tmp/<ver>_pulses.txt`, summarize to the user with: per-task state, log-line count, error count, top `FIRED` markers, and the last 3 lines of each info log. NEVER stay silent for >6 minutes during a run — the user wants continuous feedback.

12. **On each pulse**, check for new §10.6 signatures. If an ERROR line appears, immediately tail the info log around that timestamp, classify the error (F/R/N signature per §9.4), and — if root-cause is code — QUEUE a fix for the next version. Do NOT cancel the run; let it finish so you see the downstream cascade.

13. **On terminate: §10.6 zero-error audit via Python regex** — bash's `grep -c | awk '{s+=$NF}'` pattern is fragile (single-file output has no colon, empty output gives "0", arithmetic breaks). Use Python instead:
    ```python
    import re, glob
    all_text = "".join(open(f, errors="ignore").read() for f in sorted(glob.glob("/tmp/<ver>_logs/*.log")))
    err_text  = "".join(open(f, errors="ignore").read() for f in sorted(glob.glob("/tmp/<ver>_logs/*error*.log")))
    for label, pat, src in [
        ("ERROR lines",               r"\bERROR\b",                                err_text),
        ("F1 Permission denied",      r"Permission denied",                        all_text),
        ("F2/R7 Max retries exhausted",r"Max retries \(3\) exhausted",             all_text),
        ("F4 SILOED TABLES",          r"SILOED TABLES DETECTED",                   all_text),
        ("F6 KeyError format-string", r"KeyError '[0-9],[0-9]'",                   all_text),
        ("R6 Failed metric view",     r"Failed metric view.*UNRESOLVED",           all_text),
        ("R8 N>0 cycles",             r"Found [1-9]\d*\s*cycle\(s\)",              all_text),
        ("N2 Fidelity gates FAILED",  r"Fidelity gates FAILED",                    all_text),
        ("NameError/AttributeError",  r"NameError|AttributeError|TypeError",       all_text),
        ("Traceback",                 r"Traceback \(most recent",                  all_text),
    ]:
        print(f"  {label:<35} {len(re.findall(pat, src))}")
    ```
    All rows must be 0. If any row is non-zero, iterate (§10.2 step 6 onward).

14. **Pull model.json + next_vibes.txt for every sub-version** — `databricks fs cp "dbfs:/Volumes/<cat>/_metamodel/vol_root/business/<biz>/<ver>/model.json" /tmp/<run>_logs/final/<ver>__model.json`. Same for `vibes/next_vibes.txt`.

    **GOTCHA F — model.json shape is nested.** Counts are under `m["model"]["domains"]`, NOT `m["domains"]`. Attributes are under `product["attributes"]`. FKs are attributes with `foreign_key_to` set. The full count extractor:
    ```python
    m = json.load(open(f"/tmp/<run>_logs/final/<ver>__model.json"))
    model = m.get('model', {})
    domains = model.get('domains', [])
    n_p = sum(len(d.get('products') or d.get('data_products', [])) for d in domains)
    n_a = sum(len(p.get('attributes', [])) for d in domains for p in (d.get('products') or d.get('data_products', [])))
    n_fk = sum(1 for d in domains for p in (d.get('products') or d.get('data_products', [])) for a in p.get('attributes', []) if a.get('foreign_key_to'))
    n_mv = len(model.get('metric_views', []))
    quality_score = re.search(r'Model Quality Score:\s*\**\s*([\d.]+)\s*/\s*100', open(f"/tmp/<run>_logs/final/<ver>__next_vibes.txt").read()).group(1)
    ```

15. **Physical-vs-model.json parity** — do NOT trust JobTags. Query `information_schema`:
    ```sql
    SELECT table_schema, COUNT(*) AS n_tables FROM <catalog>.information_schema.tables
     WHERE table_schema NOT LIKE '_metamodel%' AND table_schema NOT LIKE '_metrics%'
     GROUP BY table_schema ORDER BY 1;
    ```
    Diff each schema's table list vs `domain['products']`. Same for `information_schema.columns` vs attributes, and `_metrics` schema vs `metric_views`. Any drift is an R2-class regression — report PRESENT.

16. **Two reports per §9.6** — save to `/Users/user/claude/vibe-agent/<run-tag>-{validation-report,model-quality-audit}.md`. The user rule "never generate .md" is subordinate to the §9.6 requirement which the user has historically demanded. If in doubt ask.

17. **§6 brutal honesty score** — end every delivery message with a 0-100 score, per-deduction evidence, explicit "what I missed". Score against the deployed run, not the local commit.

### 10.11.3 Residual-run recovery checklist

If the run stays `QUEUED` for >3 minutes after submission:

1. `databricks jobs list-runs --job-id <JOB_ID> --active-only --profile <profile> -o json` — look for runs other than yours.
2. For each active run whose `state.life_cycle_state == RUNNING` that you did NOT just submit, cancel it: `databricks jobs cancel-run <rid> --profile <profile>`.
3. Wait 5s, re-query. Your run should transition `QUEUED → RUNNING`.
4. Add a retrospective entry in the session log explaining what the residual was (nearly always a previous `run-now` without `--no-wait`).

### 10.11.4 When "no errors" is not enough — deep-audit phase (§10.9 link)

`TERMINATED / SUCCESS` + §10.6 all-zero is NECESSARY but NOT SUFFICIENT. After that, execute §10.9 Phase A (line-by-line log read) through Phase F (honesty report). The user has been burned by "looks green at the top level but latent regressions in the model" before — NEVER skip §10.9.

---

## 11. PULSE-MONITOR DISCIPLINE — NEVER SAY "RUN IS GOING WELL" WITHOUT THESE CHECKS (HARD RULE — NON-NEGOTIABLE)

Added 2026-04-28 after a critical session failure: while monitoring run `453386975947787`, I told the user "all 13 hard signatures still 0" and implied the run was healthy, while the runner had ALREADY restarted from a prior FAILED attempt (`76240803654456` → child shrink failed with `AttributeError 'str' has no get'` then `SHRINK-NEW-SILO`). The user had to kill 9+ hours of compute and tell me **"YOU TOLD ME EVERYTHING IS OK AND READY FOR FULL ECM RUN YET TO FAIL ON SHRINK"**. NEVER AGAIN.

These rules are now PERMANENT and apply to EVERY pulse the agent emits.

### 11.1 Mandatory pre-pulse-1 checks (before saying ANYTHING about a run's health)

BEFORE the first pulse on any new monitoring session, you MUST gather and report ALL of the following:

1. **Parent task graph** — `databricks jobs get-run <run_id> --profile <prof>` and report:
   - Is this a TOP-LEVEL run, or a CHILD run launched by a runner? (Look for `job_clusters`, `run_type`, `parent_run_id`, `original_attempt_run_id`.)
   - Has THIS task ever failed before in the run history? (Look at `original_attempt_run_id` ≠ `run_id` → this is a retry.)
   - Does the JOB definition have `min_retry_interval_millis` or `max_retries` > 0? Quote it explicitly in the pulse.

2. **Prior-attempt audit** — for every task in the run with `attempt_number > 1`:
   - `databricks jobs get-run-output <prior_attempt_run_id>` to retrieve the failure trace.
   - Identify the root-cause class (NameError / AttributeError / ValueError / soft-accept / silo / cycle / etc.)
   - **Predict whether the same bug will reoccur** in the current attempt. If the underlying code wasn't fixed since the prior failure, the answer is YES — and you MUST flag this loudly with `🚨 EXPECTED RECURRENCE` in the pulse, not bury it.

3. **Active-run sanity** — `databricks jobs list-runs --active-only` to detect zombie peers. If multiple runs of the same JOB are RUNNING simultaneously, surface that as `🟡 ZOMBIE PEER DETECTED` and explain whether it's a retry or a leak.

If you can't complete §11.1 inside 60 seconds of starting a monitor session, that's a HARD STOP — tell the user "I cannot pulse-monitor honestly until I have the parent task graph + prior-attempt failures." Do NOT proceed with optimistic pulses to fill silence.

### 11.2 Pulse-content rules (every single pulse, no exceptions)

Each 10-minute pulse MUST include:

1. **Per-attempt status** — not just "RUNNING", but:
   - `attempt N/M` (e.g. `attempt 1/2` if the job has 1 retry configured)
   - Time spent in current stage
   - Whether the stage was reached in any prior attempt (and if so, whether prior attempt failed AT this stage)

2. **Categorised line-by-line read** — never `grep -c | report count`. Always:
   - Read EVERY error log line from the previous-pulse mark to NOW
   - Group by category (CYCLE, SILO, SOFT-ACCEPT, BIDIRECTIONAL, FK-CONSISTENCY, SCHEMA-FAIL, FIDELITY-FAIL, NAMEERROR/ATTR-ERROR/TYPEERROR, INSTALL-FAIL, etc.)
   - Quote 1 representative literal log line per category
   - Track DELTA from prior pulse (`new since pulse N: 12 SOFT-ACCEPT, 0 cycles, 1 silo`)

3. **Soft-accept inventory** (THIS IS THE BURNING-SCAR RULE) — every `Max retries (3) exhausted. Proceeding with last response despite validation errors` line is `🔴 RED`, NEVER `🟡` or `🟢`. List EVERY soft-accept by site:
   - `[domain.product.column → target] SOFT-ACCEPT - alias=<...>`
   - For each, predict downstream impact (broken FK → R2 metric view fail, broken silo → install crash, etc.)
   - If aggregated count > 0, the pulse cannot end with "looking good" — it must end with "K SOFT-ACCEPTS PRESENT — root cause is X, fix is Y, NOT addressed in this run."

4. **Per-domain silo + cycle delta** — list every silo and cycle by literal table name. Count cycles converging round-by-round; if not converging, that's `🔴 RED`.

5. **Bidirectional FK list** — every `[BIDIRECTIONAL DETECTION]` line, with the literal `A.col_a ↔ B.col_b` pair. If detected and not yet resolved, `🟡 YELLOW`. If still detected after the resolution step, `🔴 RED`.

6. **Stage progression vs runtime budget** — for tier_1 (airlines / banking / healthcare), the ECM pipeline takes 60–120 minutes through linking + cycle-break + finalize. If a stage has been "in progress" for >2× expected duration, flag `🟡 STAGE STUCK`.

7. **Predictive failure check** — explicitly answer: **"If this run TERMINATES right now, what's the probability of SUCCESS?"** Cite evidence — every red signature you've seen reduces the probability. Show the math:
   - Base: 100%
   - Each soft-accept: −5%
   - Each persistent silo: −10%
   - Each unresolved bidirectional: −15%
   - Each unresolved cycle after round 3: −5% per cycle
   - Each known prior-attempt bug not fixed: −50%
   - Final probability — if < 80%, the pulse MUST say "this run is on track to FAIL" and explain why.

### 11.3 The forbidden-phrases list (NEVER use these without §11.2 evidence)

The following phrases are RED-LIST and FORBIDDEN unless every check in §11.2 passed cleanly:

- ❌ "all signatures clean" / "all hard signatures still 0"
- ❌ "everything looks good" / "pipeline is healthy" / "run is on track"
- ❌ "no red flags" / "no issues" / "looking solid"
- ❌ "ready for production" / "ready for full ECM" (the EXACT phrase that burned the user)
- ❌ "we're in good shape" / "minor warnings only" (warnings can ABSOLUTELY block production)

Acceptable replacements REQUIRE explicit qualifications:
- ✅ "0 of 13 §10.6 hard signatures fired YET, but K soft-accepts present at sites X, Y, Z which downstream WILL [break the install / leave silos / drop metric views / fail fidelity gates]"
- ✅ "stage 4/8 reached, mirroring the prior attempt's failure point at 4/8 — bug 'AttributeError str has no get' in `_run_resize_model` line 79586 was NOT fixed since the prior attempt, so I expect the same crash in ~N minutes"
- ✅ "no NEW errors since pulse N, but the run is still on the failure trajectory established in pulse 1"

### 11.4 Auto-trigger investigation rules

If ANY of the following appear in any pulse, you MUST immediately switch from passive monitoring to active investigation (not silent waiting):

1. `Max retries (3) exhausted` — pull the validator-feedback chain, identify the LLM-vs-validator deadlock, decide if the deployed agent has the fix.
2. `Workload failed, see run output for details` — `databricks jobs get-run-output <rid>` and surface the trace immediately.
3. `Found N cycle(s)` where N is non-decreasing across rounds — cycle-break is failing to converge; identify the LLM batch causing the persistence.
4. `Permission denied` or `[Errno 13]` — F1 surface, regression in serverless `/tmp` use; should not happen if v0.6.x+ is deployed.
5. `[CONSISTENCY] FK ... target not found` recurring — the consistency cleaner is hiding a model-drift bug; surface the LLM call producing the bad target.
6. `KeyError '0,62'` or any `KeyError '[0-9],[0-9]'` — F6, prompt template format-string bug. Stop the run if it's safe to.

### 11.5 Soft-accepts are RED, not yellow (the rule that has been violated 3 times now)

The §10.6 contract lists `Max retries exhausted` as a hard-zero criterion. If the current run has even ONE such line, the pulse cannot say "0 hard signatures." It must say `🔴 1+ HARD SOFT-ACCEPT SIGNATURES PRESENT`.

**Justification for this rule** (do not relax):
- Every soft-accept means a known-bad LLM response was accepted into the model
- Downstream stages assume responses are valid → bad LLM response → bad model artifact → user-facing failure
- Historical examples:
  - v0.6.5 telecom vov_v2: `find_missing_fk_links_order` soft-accept → R2 metric view drop downstream
  - v0.6.6 airlines (run <run_id>): `architect_self_review` soft-accept → silo product survived to MVM
  - v0.7.0 airlines (run <run_id> — KILLED): `find_missing_fk_links_workforce` soft-accept on `timesheet.schedule_id` → would have produced unlinked FK → install would have failed

### 11.6 Re-attempt detection (the rule that would have prevented the burning failure)

When monitoring a run, ALWAYS check `original_attempt_run_id` and `attempt_number`. If `attempt_number > 1`:

1. The PRIOR attempt FAILED. Pull its `get-run-output` immediately — do not wait for the current attempt to fail too.
2. Identify the prior failure's root cause class.
3. Check whether the deployed agent has the fix. If NOT, the current attempt is on the same crash trajectory. State this explicitly in pulse 1: `🚨 EXPECTED RECURRENCE — prior attempt (run_id X) failed with bug Y at stage Z; deployed code unchanged; current attempt will hit same bug in ~N minutes. RECOMMEND KILL NOW.`
4. NEVER passively monitor an inevitable-failure attempt to "see what happens." That wastes the user's compute and time.

### 11.7 Post-run honesty (mandatory, not optional)

After every pulse-monitored run terminates:

1. Re-read every pulse you emitted during the run.
2. For each pulse, ask: **"Was anything I said inconsistent with what I knew at the time?"**
3. If YES, surface this in the post-run report under `[PULSE-DISCIPLINE FAILURE]` with the specific pulse number + the misleading claim + the truth I should have said.
4. Honesty score (§6) MUST be deducted by 25 points for each pulse that violated §11.3 or §11.5, regardless of run outcome.

---

## 12. STRUCTURED QUALITY-GATE CATALOG (QGATE) — the honest scoreboard (added 2026-06-17)

Added after the gov_transport base-MVM "lying scoreboard" incident: the agent reported high adherence while the model degraded, because the VREQ verifier scored governance/tagging VREQs off a LOSSY snapshot (attribute tags/subdomain/division/descriptions omitted). It false-FAILED glossary/subdomain VREQs that were PHYSICALLY present (vibe_gov_transport_basemvm: 3031 glossary + 7 subdomain tags). This section is the permanent contract for structured quality.

### 12.1 The four-layer anti-lying architecture

1. **Deterministic gates** (`run_metamodel_static_analysis`) read the REAL model dict, so a gate verdict cannot false-negative or false-positive. 66 categories today.
2. **Agentic-loop wiring** (`_v366_sa_findings_requeue` `_fixable` whitelist) — every gate category is requeued to the SelfFixer closed loop so a discovered gap is REPAIRED, not merely reported. Curated completeness categories (descriptions/tags/types) requeue even at info severity.
3. **Authoritative verifier override** (`VibeOrchestrator._verify_bulk_coverage`, alias `verifier-bulk-coverage-authoritative`) — for glossary/subdomain/division coverage VREQs, the deterministic dict verdict runs FIRST in `_verify_deterministic` and OVERRIDES the LLM verdict. Conservative thresholds: coverage >=0.9 fulfilled, ==0 failed, else partial. rename/drop and non-coverage VREQs are deferred (no hijack).
4. **Physical ground-truth parity** (existing `gt-tag-enrich`/`gt-mv-enrich`/`gt-tag-verify`/`gt-mv-verify`) — post-build, query `information_schema.column_tags`, `information_schema.columns`, and the `_metrics` schema; verify tag/type/MV VREQs against the live catalog. This is the ultimate anti-lying check. DO NOT build a second physical-parity system — extend these.

The deterministic quality score (`_compute_deterministic_confidence_and_status`) is computed from ALL severity issues and is AUTHORITATIVE over the LLM self-score. Every new gate feeds it automatically.

### 12.2 The gate catalog (enforce ALL; add more whenever a new failure class appears)

**Keys & relationships**
- Every table has a PK (`missing_pk`, `pk_attribute_missing`).
- Every FK resolves to an existing target PK (`broken_fk`, `pk_mismatch`, `fk_target_missing`, `unlinked_fk`, `invalid_fk_domain_refs`).
- FK column type == target PK type (`fk_pk_type_mismatch`) — MEDIUM weight (join hazard).
- No FK cycles (`fk_cycle`), no self-FK on a PK (`self_fk_on_pk`, `self_referencing_fk`), no direct bidirectional links. Enforced at THREE layers: base-model Step 7D cycle-break, VOV-finalize flat backstop (`_v394_break_post_vov_cycles`), and the v4.0.3 serialization-boundary guard (`_v403_break_cycles_in_serialized_model`) that re-checks the NESTED `data_model` immediately before `model.json` is written — the last line of defense against R8b (flat finalization clean while the serialized nested dict still cycles).
- No siloed tables (`siloed_table`, `silo_product`); FK density / over-hubby cap (`fk_density_over_hubby`).
- Multi-FK label completeness; FK namespace/format/naming (`multi_fk_missing_label`, `fk_namespace_mismatch`, `fk_format_invalid`, `fk_column_naming`, `fk_name_target_mismatch`).

**Governance / tagging**
- Glossary-term tag on every business attribute when a glossary is in use (`missing_glossary_tag`).
- PII/sensitivity tag on every person-pattern attribute (`pii_tagging_missing`).
- Division tag on every domain (`missing_division_tag`).
- Division within the canonical set + balance (`invalid_division`, `division_imbalance`).
- Subdomain tag on every table (`missing_subdomain_tag`); subdomain SSOT collisions (`subdomain_ssot_collision`).
- Generic tag presence (`missing_tags`).

**Descriptions**
- Domain/table/attribute descriptions present (`missing_domain_description`, `missing_product_description`, `missing_attribute_description`).
- Non-placeholder, non-echo, >=10 chars (`low_quality_description`); no banned boilerplate (`banned_boilerplate_in_output`).

**Types**
- Type present & valid (`missing_data_type`, `invalid_data_type`); PK datatype consistency (`pk_datatype_inconsistency`, `datatype_mismatch`); well-known-column type sanity.

**Structure / naming / dedup**
- snake_case for domain/table/attribute; PK naming convention; no product-prefix on attribute.
- Duplicate names/attributes/product-pairs; cross-domain SSOT duplicate (`cross_domain_duplicate`); denormalized natural keys (`denormalized_natural_key`).
- Domain bloat caps; empty/orphaned domains; too-few-attributes; missing table/db names.

### 12.3 Canonical division taxonomy — EXACTLY 3 (HARD)

Every domain MUST be classified into EXACTLY ONE of three canonical divisions: **`operations`, `business`, `corporate`**. No other value is allowed. Legacy synonyms (`supporting`, `support`, `back_office`, `backoffice`) fold to `corporate`. Balance rule (DOM-RUL-001): Operations + Business >= 80% of domains; Corporate <= 20%. No early corporate (DOM-RUL-003): no corporate domains until Operations >= 2 and Business >= 2. The taxonomy lives in `get_division_taxonomy`; prompts, normalizer, and gates all read it (never hardcode the set elsewhere).

### 12.4 Adding new gates (the standing instruction)

Whenever a production run surfaces a new structural/governance defect class: (1) add a deterministic gate in `run_metamodel_static_analysis` reading the real dict; (2) add its category to the `_fixable` whitelist so it self-repairs; (3) if it is a coverage VREQ class, extend `_verify_bulk_coverage` so the scoreboard is authoritative; (4) add the rule to `rules/vibe-data-modelling-rules.csv` under the `Quality Gate` group; (5) add a fail-pre/pass-post behavioral test (§8.10). "Add AS MANY static structure checks AS POSSIBLE" is a standing directive, not a one-time task.
