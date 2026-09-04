# Iteration Loop — Phase 5

After the initial S2T Mapping Report is delivered, the discovery process is iterative.
The user will return with one or more of these triggers, each requiring a different response.

---

## Trigger Types & Response Protocol

### Trigger A — New Ingestion Landed
User says: "I've added `wip_discrete_jobs` to `orcy_wip_curated`" or "the Windchill export is in bronze now."

Response protocol:
1. Profile the new table (row count, columns, date range) — one `executeCode` call
2. Re-open the S2T report for all entities that listed this table as an ingestion ask
3. For each affected entity:
   - Re-run the column mapping for previously-gapped columns
   - Update the grade (Blocked → Partial or Full, Partial → Full)
   - Update the key derivation if the natural key changed
4. Update the ingestion ask table (remove the resolved P-item)
5. Produce amended scorecard section and append to the existing report file
6. State the new summary: "X Full · Y Partial · Z Blocked (was A/B/C)"

### Trigger B — Existing Model Found
User says: "There's a model at schema X that's already in production for this domain."

Response protocol:
1. Run the full existing-model-assessment.md protocol (Steps 3.1–3.7)
2. Identify which V2 entities get grade uplifts from the existing model's tables
3. Document the integration option (A/B/C) with rationale
4. Produce grade amendment table
5. Append the full Integration Assessment section as a separate file in **`docs/design/`** within the
   domain project folder (create `docs/design/` if absent; NOT the project root or a bare `docs/`) —
   use the `templates/integration_assessment.md` shell
6. Update the S2T report with the revised grades

### Trigger C — Business Correction
User says: "That source is wrong — we don't use that table anymore" or "the grain on X is actually Y."

Response protocol:
1. Ask one clarifying question if the correction is ambiguous
2. Re-run only the affected mapping section (not the full report)
3. If the correction demotes a grade (Full → Partial, Partial → Blocked), add a new ingestion ask
4. Update the report file with a dated "Amendment — {date}" section at the bottom

### Trigger D — Gap Accepted / Deferred
User says: "We don't need serial_unit for V1 of this build" or "skip ECN for now."

> **Gap-status vocabulary:** use the standardized enum — `OPEN` / `IN_PROGRESS` / `DEFERRED`
> / `ACCEPTED` / `RESOLVED` (defined in `domain-sync/next-steps-generation.md`). Do NOT use
> legacy `Descoped` / `Backlog` — map "skip for now / out of scope" → `DEFERRED`, and "known
> limitation, won't fix" → `ACCEPTED`. Consistent status is what keeps deferred gaps visible in
> the dashboard, Genie caveats, and `NEXT_STEPS.md` instead of silently vanishing.

Response protocol:
1. Mark the entity as **Out of Scope for Phase 1** (status `DEFERRED`) in the scorecard (not Blocked)
2. Remove associated P0/P1 ingestion asks; retain P2/P3 for future reference
3. Update the load order (remove the entity from the tier sequence)
4. Note the descope decision with date in the report under "Scope Decisions"

### Trigger E — Revised Model Re-Enters (the return leg of "iterate upstream")
User says: "We have a new version of the domain model. Re-run discovery." — **or** the user has
taken the **vibe-model prompts** this skill emitted (at the Phase 2C / Step 2.7 human gate) to
the vibe-modeling agent, iterated the model upstream, and returned with a **V+1** model.

This is the **return leg of the iterate-upstream disposition** (`model-completeness-protocol.md` Step
2C.4, path 1): Phase 2C/2.7 found a gap → the skill emitted vibe-model prompts → the user
refined the model in the vibe agent → V+1 lands here. **There is no model-agent regeneration in
this skill** — the user did the iteration in the vibe agent; Trigger E only re-runs discovery
against the *changed metamodel*.

Response protocol:
1. Diff the new model against the old model: find added tables, removed tables, changed columns.
   If the V+1 was produced from emitted vibe-model prompts, this diff should match those prompts —
   confirm each prompt's intended change landed.
2. For unchanged tables: carry forward existing grade + source mapping (no re-profiling needed)
3. For changed tables: re-run column mapping for changed columns only, and re-run the relevant
   **Step 2.7 assertion probes** (grain / type / PK / FK) for any entity whose grain, type, key,
   or FK changed
4. For new tables: run full Phase 1–4 protocol (including Step 2.7 assertion validation)
5. Open a new report file with the new version number; reference the prior report for baseline

> **Model-edit disposition (how a finding gets here).** When Phase 2C (additive) or Step 2.7
> (surgical) surfaces a miss, the user chooses at the single human gate between:
> **(1) iterate upstream** — take the emitted **vibe-model prompt** to the vibe agent, refine the
> model, re-enter via *this* Trigger E with V+1 (recommended for structural misses); or
> **(2) edit in place via Genie Code** — a scoped `vibe_metamodel_*` SQL edit for small
> additive/corrective changes (no re-entry needed; the metamodel is revised directly, then
> re-map the affected entity). Path 1's loopback is exactly this trigger; path 2 stays inside the
> current pass. Neither path uses model-agent regeneration.

### Trigger F — User feedback on the Gap Registry or next_vibes (the three-way router)

The Gap Registry and `next_vibes.md` are surfaces the user talks back to. When the user pushes back
on an item, ask which of three things they mean, and route — every outcome is a recorded disposition,
never lost in chat:

1. **"We can't get that data — but the concept is real."** Build-scope decision, not a model
   correction. Flip the registry item `DEFERRED → ACCEPTED` — annotate `Gap_Type = DROPPED (deviation)` when the `model_deviation` gate actively dropped the element, or `(no source — out of scope)` otherwise. **`DROPPED (deviation)` is a `Gap_Type` annotation, not a `gap_status` value** — the status field always holds one of the `gap_status_enum` values (`OPEN`, `IN_PROGRESS`, `DEFERRED`, `ACCEPTED`, `RESOLVED`). Model + next_vibes UNCHANGED; the concept stays a recoverable breadcrumb. *Absence of data never shrinks the model.*
2. **"We don't do that / that concept doesn't apply to us."** A business-*coherence* correction →
   emit a user-confirmed `remove_product` / `remove_attribute` in next_vibes; close the registry item
   as "removed from model scope." **This is the only path by which "we don't have that" removes a
   modeled element — driven by a business assertion, not a data gap.**
3. **"You're wrong about our data — that bronze table doesn't exist / is empty / isn't what you
   think."** Corrects the assessment's *evidence* → re-grade affected entities (usually down),
   withdraw any next_vibes item or S2T mapping that leaned on that table, add the now-real gap to the
   registry.

### Trigger G — Architecture Decision
User says: "Go with Option A" or "Make V2 upstream of the existing model."

Response protocol:
1. Identify which entities have source dependencies on the existing model (from integration assessment)
2. For each affected entity: trace the existing model's tables back to their bronze origins
3. Re-route source mappings to bronze (eliminate circular dependency)
4. Re-grade affected entities against bronze-only sources
5. Update the Domain Readiness Summary with the new architecture and source map
6. Append the architecture decision and revised data flow to the integration assessment doc

---

## Load Order Maintenance

The load order is derived from the FK graph (the resolved `referential_constraints` +
`key_column_usage` join from discovery-protocol §1.5 — or the `foreign_key_to` fallback when the
model declares FKs only in the metamodel, not as physical UC constraints). When tables are added or
removed during iteration, recalculate the tier sequence:

```
Tier 0: tables with no FK columns to other tables in this schema
Tier 1: tables whose FKs all point to Tier 0
...
Tier N: tables whose FKs include at least one to Tier N-1

Skip/Defer: Blocked tables and Out-of-Scope tables
```

Always state: "Build first: {Tier 0 list} → then {Tier 1} → … → {facts/transactions}"

---

## Gap & Enhancement Registry

At the end of every iteration, maintain a **Gap & Enhancement Registry** with these columns. It
captures **both reconciliation directions** — model-wants-data-bronze-lacks (Gap) and
bronze-has-meaning-the-model-missed (Enhancement) — and is the **primary review artifact** for
the per-domain human gate. This registry is **knob-blind**: a Blocked/DEFERRED entity is deferred
regardless of `output_model` (the knob shapes only the built *target*, not whether the data
supports the entity).

| Priority | Type | Entity | Column(s) affected | Missing source / found source | Unblock or add action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Blocked entity | `wip_job` | ordered_qty, status, dates | `wip_discrete_jobs` missing from `orcy_wip_curated` | Request EBS WIP team to add | DEFERRED |
| P0 | Blocked entity | `serial_unit` | All columns | `mtl_serial_numbers` not ingested | Request INV team to add | DEFERRED |
| P1 | Significant column group | `plant` | address, ISO cert, DFF flag | No bronze source | Manual reference data load | OPEN |
| P2 | Single column | `manufacturing_bom_line` | pfas_flag, rohs_flag | Compliance domain not in lake | Await compliance domain V2 | DEFERRED |
| P3 | Enrichment | `routing_operation` | operation_code text | `bom_standard_operations` not in bronze | Nice-to-have; add if available | DEFERRED |
| P2 | **Model addition** (bronze→model) | *(new)* `lot_genealogy` | parent/child lot links | `mtl_lot_relationships` present, no model entity | Propose new entity; surface in `next_vibes.md` | OPEN |

**Rules:**
- **Every `NULL_SOURCE` column gets a registry row** (a mapped source column that is 100% null),
  Type `NULL_SOURCE`, carrying its keep/drop disposition — regardless of disposition, so the
  per-domain review sees every all-null column. A **dropped** null column is omitted from the built
  DDL ONLY with this row present (`etl-development-framework/ddl-and-modeling.md`); a **kept** one
  is a documented all-null column. A NULL_SOURCE finding feeds the "Other known issues from static
  analysis" section of `next_vibes.md` (always emitted — see "Generating `next_vibes.md`" above);
  the registry remains the primary per-domain review artifact.
- **Never delete a gap or silently descope.** A modeled entity with no bronze source is recorded
  **DEFERRED** with a future-enhancement callout (the ingestion ask that unblocks it) — the build
  may skip building it, but the registry must report it. "The data isn't here yet" is a finding,
  not a decision. A P0 item the user accepts as out-of-scope moves to `ACCEPTED`/`DEFERRED`, never
  deleted.
- **Bronze-reveals-more surfaces as a `Model addition` row** (proposed new entity / attribute /
  grain / hierarchy level) for the DE team's review — and as a `connect_table`/new-entity PRIORITY
  in `next_vibes.md` (always emitted every run).
- **`DROPPED (deviation)`** — an element the user chose to drop at the deviation gate (via
  `model_deviation` toggles); carries a reason and a next_vibes recovery breadcrumb; never a silent
  removal. This is a registry-row annotation; it does not replace `DEFERRED`/`ACCEPTED` in the
  base `gap_status_enum` (see `conventions.yml`) — downstream readers treat `DROPPED (deviation)`
  as a terminal disposition distinct from a build-scope deferral.
- Carry the registry forward across all iterations.

---

## Generating `next_vibes.md` (always-on default output)

Emit `docs/design/next_vibes.md` on EVERY run, in the model-agent format (Model Quality Score →
PRIORITY lines → static-analysis findings → deterministic score), paste-ready into the vibe-modeling
agent's Model Vibes widget. Use `templates/next_vibes.md` as the fillable shell. Governed by the
bright line (SKILL.md "Two loops & the bright line").

**Sources → actions:**
- Step 2.7 contradictions (grain/type/PK-uniqueness/FK-cardinality the data disproves) → `rename_*` /
  fix-grain / `remove_fk` PRIORITYs (coherence, data-volume-independent).
- Phase 2C additions where bronze reveals a real *business* concept the model missed → `connect_table`
  / new-entity PRIORITYs (the one legitimate "add to model" direction).
- Deviation drops → recovery breadcrumbs only ("build dropped X to ship; get bronze {Y} to reinstate")
  — NEVER `remove_product`.
- Router case-2 ("concept doesn't apply") → user-confirmed `remove_product` / `remove_attribute`.
- NULL_SOURCE / naming / boilerplate → "Other known issues from static analysis" bullets.
- Ingestion "go get data" asks stay in the Gap Registry — NEVER here.

**Deterministic score (documented rubric):** start at 100; subtract weighted points per finding —
e.g. −5 per Step 2.7 contradiction, −3 per orphan/missing-FK, −4 per missing business process, −1 per
redundant/ambiguous name; floor at 0. Stable and monotonic (fewer findings → higher score) so runs
are comparable.

**Perfect-model case:** still emit — high score, zero/low PRIORITYs, and the explicit line
"No structural refinements recommended; the model is coherent against the profiled data."

---

## Scope Decisions Live in a Committed Artifact — NEVER in Chat or Memory

Every human-gate decision (the `HG-*` scope decisions, deferrals, accepted gaps, type-tension
acceptances) MUST be recorded in a **committed artifact** the next pass reads — not in assistant
memory and not left implicit in the conversation. If a decision only exists in chat/memory, the
next session (or a different agent) has no durable record, silently re-derives it, and the two
passes can disagree. That is the exact "context that lived only in chat" failure this loop exists
to prevent — handoff is through documents.

**Where:** a `docs/design/scope_decisions.md` file in the project folder, OR the "Scope Decisions" section
of the S2T report (pick one and keep it authoritative). Format:

| ID | Date | Entity / Gap | Decision | Rationale |
| --- | --- | --- | --- | --- |
| HG-1 | 2026-07-19 | `opportunity` | DEFERRED — out of Phase 1 scope | CRM pipeline analytics not required yet |
| HG-4 | 2026-07-19 | `order` type tension | ACCEPTED | `Transactional` convention covers lifecycle records |

**Rules:**
- Each new pass **reads** this artifact first and **appends** to it — never starts from a blank
  slate or from memory.
- When a re-profile changes the scorecard vs a prior pass (e.g. "15 Full now vs 13 Full before"),
  record BOTH numbers **in the artifact** with the reason for the change. Do NOT resolve the
  discrepancy by silently editing assistant memory to match the new run.
- Do not use the `assistant`/session memory as the store of record for any scope decision. Memory
  may *summarise* the current state, but the artifact is authoritative.

---

## Iteration Exit Criteria

The discovery phase is complete when one of these is true:
1. **Zero Blocked entities** (all entities are Full or Partial)
2. **All remaining Blocked entities are accepted as out-of-scope** by the user
3. **User explicitly says "start the build"** — hand off to `etl-development-framework` skill

At exit, produce a final **Domain Readiness Summary** with:
- Final scorecard: X Full · Y Partial · Z Blocked / Deferred
- Load order for the build phase
- Sources confirmed per entity
- Open ingestion asks (P0/P1) to monitor during build
- Recommendation: which entities to build in Phase 1 vs defer

> **Before you treat any of the three criteria above as met — including "user says start the
> build" — run the Phase 5 → 6 Completion Self-Audit (SKILL.md, Critical Rule 15) and report the
> "Remaining before handoff" list unprompted.** "User says start the build" is a *request* to exit,
> not proof the work is closed: an ungraded entity, an undisposed Blocked entity, or an open
> 2C/2.7 finding still blocks handoff. Only an empty Remaining list unlocks the handoff-doc
> generation below.

---

## Handoff to ETL Development Framework — Document Generation

When exit criteria are satisfied and the user confirms "start the build," **do not just tell
them to load the other skill**. Instead, produce two pre-filled handoff documents that satisfy
the ETL framework's requirements gate (Phase 0) and skip its discovery phase (Phase 1):

> **The handoff docs are KNOB-AWARE — carry `output_model` through.** The rows below describe the
> `dimensional` shape (the default is now `normalized` — see below). In **`normalized`** mode, entity names stay the metamodel product names
> verbatim (no `dim_/fact_` prefix), and keys follow the model's `{product}_id` (no `{Entity}_Key`
> surrogate). In **`hybrid`**, silver entities are product-named and the `dim_/fact_` star goes in
> the gold tier. Set `output_model` + `scd_strategy` in `business_requirements.md` §1 and
> `etl_detailed_spec.md` §1 "Target shape" so the build knows which templates to use. The
> *reconciliation* behind these docs (what's Full/Partial/Blocked) is knob-blind.

### Document 1: `business_requirements.md`

Fill the ETL framework template (`etl-development-framework/templates/business_requirements.md`)
using discovery context:

| Template section | Source from discovery |
| --- | --- |
| 1. Project Context | Domain name, metamodel `vibe_metamodel_business.description`, layer = Silver (+ Gold if re-platform) |
| 2. Source Systems | All confirmed bronze schemas from S2T report + any gold sources (with row counts) |
| 3. Business Entities | All buildable entities from scorecard (entity name, DIM/FACT type from FK graph tiers, natural key from S2T key derivation, source table) |
| 4. Key Metrics & KPIs | Derived from Gold re-platform plan (if exists): e.g. Schedule_Compliance, OEE%, production_actuals monthly qty |
| 5. Consumers | Known downstream consumers: DFF dashboards, Genie spaces, gold MVs, other models |
| 6. Refresh & SLA | Default: daily batch; infer from source freshness patterns |
| 7. Non-Functional | Volume estimates from row counts; PII = none for manufacturing; retention = current state (Type 1) |
| 8. Out of Scope / Deferred | DEFERRED entities from the Gap & Enhancement Registry — listed as future enhancements with their unblock action, **NOT silently dropped**. Also set `output_model` + `scd_strategy` in §1. |
| 9. Open Questions | Outstanding P0 ingestion asks that may land during build |

### Document 2: `etl_detailed_spec.md`

Fill the ETL framework template (`etl-development-framework/templates/etl_detailed_spec.md`)
using S2T mapping report outputs:

| Template section | Source from discovery |
| --- | --- |
| Section 0 — Locations | **Silver land target (WRITE)** = `conventions.yml` `catalogs.silver` + `schemas.silver_pattern`. **Vibe model source (READ-ONLY)** = `vibe_model.catalog`/`vibe_model.schema` — the location you READ the model from during assessment. These MUST be different. **NEVER stamp `vibe_model.*` as the target catalog/schema** — that would make the build MERGE into the graded model. If the resolved land `catalog.schema` (`catalogs.silver` + `schemas.silver_pattern`) equals the resolved `vibe_model.catalog`/`vibe_model.schema`, STOP and ask the user for the land target before writing the spec. |
| Section 0 — Naming (from `conventions.yml` `naming:`) | Copy the FULL `naming:` block verbatim into the spec (Section 7). **The metamodel supplies the BASE name; `conventions.yml` `naming:` supplies the FORM.** Every entity and column name you write into the spec MUST already be transformed through it — do NOT pass through raw `vibe_metamodel_product.table_name` / `attribute` names. When the metamodel's own naming fields (`data_asset_naming_convention`, `primary_key_suffix`) conflict with `conventions.yml`, **`conventions.yml` wins** (flag the conflict for the user, don't silently keep the metamodel form). |
| Section 1 — Target shape | Stamp `output_model` (normalized / dimensional / hybrid) + `scd_strategy` from `conventions.yml` into the spec §1 "Target shape" so the build picks the right templates. |
| Section 1 — Target Model: Entities | Scorecard table: entity, type, layer, source table(s), load order tier. **Apply naming per `output_model`:** `dimensional` → prefix by Type (`dim_prefix` DIM, `fact_prefix` FACT, `bridge_prefix` bridges; gold uses `gold_prefix`) + `table_case` + `entity_form` (e.g. `sales_area`→`dim_sales_area`, `order`→`fact_order`). `normalized` (+ hybrid-silver) → **keep the metamodel product name verbatim** (`sales_area`, `order`), no prefix. `hybrid` → product names for silver rows, `dim_/fact_` for gold-tier rows. Never emit a bare name in `dimensional` mode; never add a prefix in `normalized` mode. |
| Section 1 — Grain | From metamodel `vibe_metamodel_product.description` — extract "one row per..." |
| Section 1 — Conformed Dimensions | From FK graph: dimensions referenced by 2+ fact entities |
| Section 2 — Column Mappings | From S2T column mapping tables — one subsection per entity, **complete for every buildable (Full/Partial) entity**: every target column with its **`Type`** (from S2T `Target Type`), verified `Source column`, `Transform / cast`, and **`FK Lookup`**. Keys-only fill is NOT acceptable in a handoff — a complete typed map is what makes the build's reconciliation confirmation-only. Carry each `NULL_SOURCE` column with its **`Null Disposition`** (keep/drop, blank = global default) — mark each in the §2 `Notes` cell as `NULL_SOURCE`. Target column names use `naming.business_column_case` (e.g. `Pascal_Snake` → `Net_Amt`); metadata/audit columns use `naming.metadata_column_case` (e.g. `_source_system`). |
| Section 3 — Keys & Constraints | From S2T key derivation: natural key, PK, FK references, value_regex → CHECK, **plus the complete per-FK resolution table for EVERY FK** (`FK Column \| Parent Entity \| Domain (intra/cross) \| Resolution (LEFT JOIN / NULL) \| Join Condition`) — normalized product FKs and fact FKs alike; the `Join Condition` MUST spell out composite joins in full. **PK generation AND FK resolution both reference `conventions.yml surrogate_key_formula`** — do not restate a hash in the spec. **Keys per `output_model`:** `dimensional` (+ hybrid-gold) → surrogate `{Entity}_Key` (`naming.surrogate_key_suffix`), the `surrogate_key_formula`, FK per `naming.fk_naming`. `normalized` (+ hybrid-silver) → **follow the model's PK** (`{product}_id`), no `{Entity}_Key` surrogate; add one only where the model PK is composite/mutable or cross-source integration needs it. Set per-entity `SCD` (type_2 dims — dimensional/hybrid-gold only) in §5. |
| Section 4 — Load Order | From tier sequence (already calculated) |
| Section 5 — Strategy Overrides | Default: MERGE for silver, INSERT_OVERWRITE for gold. Keys/SCD per `output_model` + `scd_strategy` (SHA2 surrogates in dimensional/hybrid-gold; follow-model keys in normalized). Set per-entity `type_2` here for dims that need history. |
| Section 6 — DQ Thresholds | Standard: PK uniqueness (0 dups, fail), FK orphans (0, fail), population (≥95%, warn), row count delta (≤10%, warn) |

#### Keep/drop the partial (always-null) columns — interactive gate

Before generating the handoff, enumerate every `NULL_SOURCE` (always-null / partial) column and
present them to the user: **keep** (build as a documented all-null column) or **drop**. The answer:
1. Sets `null_columns.disposition` (existing knob) as the **domain-wide default**, and
2. Is recorded **per-column** in `etl_detailed_spec.md` (the §2 `Null Disposition` field on the null-column row)
   so the ETL build drops exactly those columns and keeps the rest.
A dropped column is still a logged registry row (`NULL_SOURCE`, disposition `drop`) — never a silent
removal. Default remains `keep` if the user declines to decide.

### Handoff Protocol

1. Create the project folder: `{domain}_etl/` (or use existing project folder)
2. Write `docs/design/business_requirements.md` (filled)
3. Write `docs/design/etl_detailed_spec.md` (filled)
4. Tell the user:
   > "Handoff documents generated. These satisfy the ETL framework requirements gate.
   > To build: load the `etl-development-framework` skill and point it at `{project_folder}/docs/design/`.
   > The detailed spec is fully pre-filled — discovery will be skipped for all specified entities.
   > Only entities marked as gaps in Section 2 will trigger discovery questions."

### Quality Gate for Handoff Docs

Before writing, verify:
- **Section 0 land target ≠ vibe model source.** The spec's target catalog/schema resolves from
  `catalogs.silver` + `schemas.silver_pattern`, NOT from `vibe_model.*`. If they are equal, STOP —
  do not write the spec; ask the user for the silver land target first.
- **Naming conventions applied per `output_model`.** In `dimensional` mode: every entity name in
  Section 1 carries its `dim_`/`fact_`/`bridge_` prefix per Type + `table_case`/`entity_form`,
  every surrogate key uses `surrogate_key_suffix`, business columns use `business_column_case`; NO
  bare un-prefixed names pass through. In `normalized` mode: every entity keeps the metamodel
  product name verbatim (NO `dim_/fact_` prefix), keys are the model's `{product}_id`; NO invented
  prefixes or `{Entity}_Key` surrogates pass through. `hybrid` = **layered (not both-at-once)** —
  normalized silver first, THEN a dimensional gold star built downstream from it. `output_model` +
  `scd_strategy` are stamped in §1. The full `conventions.yml` `naming:`
  block is copied into Section 7.
- Every entity in the detailed spec Section 1 has at least one source table confirmed
- Every entity in Section 3 has a natural key defined (+ SHA2 surrogate formula in
  dimensional/hybrid-gold; model `{product}_id` in normalized)
- Load order in Section 4 matches the FK graph (no forward references)
- Grade=Full entities have complete column mappings in Section 2 — **every column typed** (`Type`
  filled from S2T `Target Type`) with a verified `Source column` and `FK Lookup`
- Grade=Partial entities have column mappings with explicit `GAP` / `NULL_SOURCE` markers for
  unmapped or all-null columns; each `NULL_SOURCE` column carries a `Null Disposition` and a Gap &
  Enhancement Registry row
- Every FK (normalized product FKs and fact FKs) has a Section 3 resolution row with an explicit
  `Join Condition` (composite joins spelled out in full)
- Section 3 / Section 5 reference `conventions.yml surrogate_key_formula` for PK generation and FK
  resolution — no restated hash
- Blocked entities are **not built in the Phase 1 DAG**, but they DO appear as **DEFERRED
  future-enhancement rows** in `business_requirements.md` §8 + the Gap & Enhancement Registry —
  never silently omitted. (Do not confuse "not built yet" with "descoped and forgotten.")

---

## Legacy Handoff (Fallback)

If the user prefers to fill the ETL framework templates manually, the discovery outputs
feed directly into the ETL framework as reference:

| Discovery output | ETL framework input |
| --- | --- |
| Load order (tier sequence) | Task DAG `depends_on` in the DAB job YAML |
| Candidate sources per entity | Source SELECT in each MERGE notebook |
| Key derivation formula | SHA2 surrogate key in DDL + MERGE |
| Column mapping + transformation | MERGE `WHEN MATCHED THEN UPDATE SET` + `WHEN NOT MATCHED THEN INSERT` |
| value_regex from metamodel | CHECK constraints in DDL |
| V2 column comments from metamodel | COMMENT clauses in DDL |
| Grade = Full → build now | Include in Phase 1 DAG |
| Grade = Partial → build with gaps | Include with NULL placeholders for gapped columns |
| Grade = Blocked → defer | Do not include in Phase 1 DAG |
