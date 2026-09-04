# How to decide what to do before the build

**Goal:** after the `domain-model-assessment` has produced a complete S2T Mapping Report, Gap &
Enhancement Registry, and `next_vibes.md`, choose how to close the gap between the vibe model and
your real data before you start the build.

These paths are not mutually exclusive. You can defer some entities, take a few vibes upstream,
and enable deviation on others — all in the same handoff. The assessment ends when you've made a
recorded disposition for every open item; the build starts from that durable record.

> **Prefer a picture?** These paths are drawn as a decision tree in the
> [workflow map](../workflow.md#2--the-decision-tree-after-the-assessment) — the routing paths
> converging on "every open item dispositioned → start the build," with Defer as the default
> catch-all and the null-column keep/drop as a downstream decision.

> **Background:** the assessment runs two complementary feedback loops that must never overlap:
> the **Gap & Enhancement Registry** (data catches up to the model — P0–P3 ingestion asks) and
> **`next_vibes.md`** (model refines toward the business truth). Keep them separate when you act.
> The full rationale is in [explanation.md](../explanation.md#how-it-fits-with-the-vibe-model) and
> the "Two loops & the bright line" section of
> `domain-model-assessment/SKILL.md`.

---

## Path 1 — Iterate the model upstream

**When to pick it:** a structural miss — the model is *wrong or incomplete about the business*.
Examples: a bad grain declaration the data disproves, a nonsensical FK cardinality, a business
entity the bronze data proved real that the model doesn't know about. This is a business-coherence
problem, not a data-coverage problem.

**What it does:** `domain-model-assessment` always emits `docs/design/next_vibes.md` every run, in
the vibe-modeling agent's exact format (Model Quality Score → PRIORITY lines → static-analysis
findings → deterministic score). It is paste-ready into the vibe-modeling agent's Model Vibes
widget. You take it — or a hand-edited version — to the vibe agent, produce a **V+1** model, then
re-enter the assessment via **Trigger E** (revised model re-enters) in `iteration-loop.md`. The
assessment diffs V+1 against V0, carries forward unchanged grades, and re-runs only the affected
mappings.

There is **no model-agent regeneration inside this skill** — the skill emits vibe-model prompts
you act on in the vibe agent; Trigger E is the return leg.

**How to invoke it:**
1. Open `docs/design/next_vibes.md` — review the PRIORITY lines; edit out anything that doesn't
   apply or add clarifying context.
2. Paste into the vibe-modeling agent's Model Vibes widget. Produce V+1.
3. In your next assessment session, tell the skill: "We have a new version of the domain model.
   Re-run discovery." — that is **Trigger E**.

**Trade-off:** highest-fidelity fix. The V+1 model will be more coherent and better aligned to the
business. Costs a round-trip through the vibe agent and a partial re-assessment (only changed
entities get re-profiled).

---

## Path 2 — Ingest more source data, then re-run

**When to pick it:** the model is right about the business, but the data isn't landed yet. A
Partial or Blocked grade because the source table is missing from bronze.

**What it does:** the Gap & Enhancement Registry is the primary instrument here. Its P0–P3 rows
name exactly which bronze table or schema is missing and who to ask for it. Land the named source,
then re-enter the assessment via **Trigger A** (new ingestion landed) in `iteration-loop.md`. The
skill runs an abbreviated re-assessment: profile the new table, re-grade only the entities that
listed it as an ingestion ask, and update the registry.

The "get more data" pressure lives **entirely in the Gap Registry** — never in `next_vibes.md`
(the bright line: `next_vibes.md` never removes a modeled element for absence of data — only for
business-coherence reasons).

**How to invoke it:**
1. Open `docs/design/` → review the Gap & Enhancement Registry. Action the P0/P1 rows first —
   those block entities entirely.
2. Land the named bronze table(s) in the right schema.
3. Tell the skill: "I've added `{table}` to `{schema}`." — that is **Trigger A**.

**Trade-off:** fills the model as designed — the built silver will match the vibe model's intent.
Costs an ingestion cycle (and sometimes a data-engineering ask to a source team).

---

## Path 3 — Defer and keep the model complete (the safe default)

**When to pick it:** you want to build now, but you accept that some entities or columns aren't
sourced yet and will be populated later when their bronze arrives.

**What it does:** this is the assessment's default behavior — the "no silent descoping" rule. An
unsourced modeled element is recorded **DEFERRED** in the Gap Registry (with a "needs bronze {X}"
callout). The entity is carried into the handoff docs as a DEFERRED future-enhancement row
(`business_requirements.md` §8) and recorded in the Gap Registry with its unblock action — it is
not built in the Phase 1 pipeline; the build creates it once its source arrives. Nothing is
dropped. Nothing is forgotten.

No action is required to choose this path — it is what the handoff produces if you don't override
anything. A Blocked entity with no explicit disposition moves to `DEFERRED` automatically.

**Trade-off:** the model stays complete and aspirational. Unsourced entities wait as DEFERRED rows
until their source arrives — they are not built empty, they are simply not built yet. The Gap
Registry items remain OPEN/DEFERRED in the quality dashboard, making the gap visible and
trackable.

---

## Path 4 — Deviate: change what actually gets built (opt-in)

**When to pick it:** "perfect is the enemy of good" — you've landed all the bronze you're going
to get, it still won't fill the domain, and you want to ship a clean silver layer now rather than a
schema that's half-populated by design.

**What it does:** enable `model_deviation` in `conventions.yml` (default OFF). Granular toggles
control what the deviation covers:

| Toggle | What it drops/adds |
| --- | --- |
| `drop_null_columns` | Columns whose only mapped source is 100% NULL — drop from the built DDL |
| `drop_unbuilt_domain_fks` | FKs pointing at domains not yet built — drop the FK constraint |
| `drop_no_process_tables` | Modeled tables with no identified business process and no source |
| `allow_new_entities` | Let the assessment propose net-new tables/columns the bronze reveals — **propose→build** |

`preset: pragmatic` turns on all four at once — the most common shipping configuration.

Every drop and every net-new is **human-confirmed at the Phase 2C / Step 2.7 gate**. Nothing is
dropped silently. Each drop lands in the registry as `DROPPED (deviation)` with a reason and a
`next_vibes.md` recovery breadcrumb — so reinstating a dropped element later is as simple as
presenting the breadcrumb back to the vibe agent.

Net-new (`allow_new_entities`) follows a **propose→build** path: the assessment records the
proposed element in `etl_detailed_spec.md` and the ETL build creates it. There is no write to the
vibe metamodel — the vibe model is never modified by this skill.

**You don't have to decide this upfront.** The Completion Self-Audit surfaces the option at the
end, unprompted, when Partial/Blocked entities remain and `model_deviation` is off:
> "N entities are Partial/Blocked. The default is accept-and-defer (recorded as ingestion asks). If
> you'd rather ship silver now, you can enable `model_deviation` (drop these / add net-new). Here
> is what each toggle would drop: …"

**A lighter in-place alternative:** for small additive or corrective changes — not a broad pruning
— you can **edit the model directly via Genie Code** (a scoped SQL edit against the
`vibe_metamodel_*` tables). That is the other disposition at the same Phase 2C / Step 2.7 gate,
and it doesn't require enabling `model_deviation`.

**Trade-off:** fastest path to a coherent, shippable silver layer. The built model diverges from
the vibe model — intentionally. All divergences are logged and recoverable. The deviation is
knob-blind: it works the same way regardless of `output_model`.

---

## Path 5 — Keep vs. drop the always-null columns (decided at handoff)

**When:** always, at the Phase 5 → 6 transition. The assessment lists every 100%-null
(`NULL_SOURCE`) column and asks you: keep or drop?

**What it does:** the answer sets `null_columns.disposition` as the domain-wide default (default
`keep` if you don't decide), AND is recorded **per-column** in `etl_detailed_spec.md` so the ETL
build drops exactly those columns and keeps the rest. A dropped null column is still a logged
registry row — never a silent removal.

- **Keep:** the column is built as a documented all-null column. The DDL includes it; the MERGE
  populates it with NULLs. Future source coverage will fill it without schema migration.
- **Drop:** the column is omitted from the DDL. The registry row carries the `NULL_SOURCE`
  disposition and a note. The `etl_detailed_spec.md` marks it as dropped.

This decision is separate from the broader `model_deviation` toggle — it applies to columns
with a confirmed source mapping that happens to be all-null, not to unmapped entities.

**Trade-off:** keep = a complete schema with some empty columns, forward-compatible with future
data; drop = leaner tables, cleaner initial build. You can re-add a dropped column later (it's
logged), but it requires a schema migration.

---

## Path 6 — Talk back to the outputs: the three-way feedback router (Trigger F)

The Gap Registry and `next_vibes.md` are surfaces you respond to. When you push back on an item —
"we can't get that data," "we don't do that," "you're wrong about our data" — the skill routes by
what you actually mean (**Trigger F** in `iteration-loop.md`):

| You say | What it means | What happens |
| --- | --- | --- |
| "We can't get that data, but the concept is real." | Build-scope decision, not a model correction | Registry item flips to `DEFERRED → ACCEPTED (no source)` or `DROPPED (deviation)`. Model and `next_vibes.md` UNCHANGED. The concept stays as a recoverable breadcrumb. |
| "We don't do that / that concept doesn't apply to us." | Business-coherence correction | A user-confirmed `remove_product` or `remove_attribute` is emitted in `next_vibes.md`; the registry item closes as "removed from model scope." **This is the only path by which "we don't have that" removes a modeled element — driven by a business assertion, not a data gap.** |
| "You're wrong about our data — that table doesn't exist / is empty / isn't what you think." | Evidence correction | Affected entities are re-graded (usually down); any `next_vibes.md` item or S2T mapping that leaned on that table is withdrawn; the now-real gap is added to the registry. |

Every outcome is a recorded disposition in a committed artifact — none of it lives only in chat.

---

## Decision heuristic

| If… | Pick |
| --- | --- |
| The model is wrong about the business (bad grain, missing entity, nonsensical FK) | **Path 1** — iterate upstream |
| The data isn't landed yet, but the model is right | **Path 2** — ingest, then re-assess |
| Build now, keep unsourced elements for later | **Path 3** — defer (the safe default) |
| Ship a clean silver layer, prune to what you actually have | **Path 4** — deviate |
| Per-column null cleanup at handoff | **Path 5** — keep/drop |
| Pushing back on a specific registry item or next_vibes line | **Path 6** — feedback router |

You can combine them. The only constraint is that every path produces a **committed artifact** —
the handoff document is the record, not the conversation.
