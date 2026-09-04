# Explanation — the motion, the vibe-model fit, and why it's phase-gated

This is the *understanding-oriented* doc. It doesn't tell you what buttons to press (see
[tutorial.md](tutorial.md) and [how-to/](how-to/)) or catalog the parts (see
[reference.md](reference.md)). It explains **why the suite is shaped the way it is** so the
rest of the docs make sense.

## The problem this motion solves

A generated **vibe data model** is a *coherent, documented business model* — a star schema
with dimensions, facts, hierarchies, grain declarations, and comments, produced by the
vibe-modeling agent. It is a genuinely good starting point. But it is **empty**: it describes
what the business *means*, not what the customer's *real data* contains. Between "here is a
clean model of a sales-order domain" and "here is a validated, documented, queryable silver
layer built from the customer's actual bronze tables" sits a large amount of careful,
error-prone work: finding the right sources, mapping cryptic columns, resolving foreign keys,
choosing load strategies, proving the load landed correctly, and explaining the result to the
people who will use it.

The naive way to close that gap is to point a roaming agent at the model and the data and say
"build it." That fails in predictable ways — the agent invents sources, silently drops rows,
ships joins that return zero results, and produces documentation that contradicts the data.

This suite is the disciplined alternative.

## How it fits with the vibe model

The vibe model is the **input**, not something these skills produce or regenerate.

- **The vibe model is a one-shot, pre-iterated frozen input.** The customer has (often)
  already iterated on it upstream, with the vibe-modeling agent, *before* entering this loop.
  This motion deliberately diverges from the vibe-modeling blog's "regenerate via the
  model-agent" story: **there is no model-agent regeneration here.**
- **The model is revisable, not sacred.** When assessment discovers the model genuinely
  misses — a missing entity, a wrong grain, an unsupported FK cardinality — it doesn't
  silently paper over it. It surfaces the miss and offers two disposition paths:
  1. **Iterate upstream** — emit *vibe-model prompts* (natural-language instructions the
     user takes back to the vibe-modeling agent to refine the model before the build). This
     is the recommended path for structural misses.
  2. **Edit in place via Genie Code** — a scoped SQL edit against the `vibe_metamodel_*`
     tables, for small additive/corrective changes.
- **The skills form the model to real data.** Everything downstream — the S2T mapping, the
  DDL, the MERGE logic, the validation baselines, the domain narrative — is the model
  *brought alive* against the customer's bronze, inside the customer's Databricks workspace.

So the mental model is: **vibe model = coherent hypothesis about the business; the skill
suite = the disciplined process that tests and realizes that hypothesis against real data.**

## Why a phase-gated loop (and not a roaming agent)

Three design commitments make the motion trustworthy with production work:

### 1. Handoff is through documents, not chat

Each station's output *documents* are the next station's input:

```
assessment → etl_detailed_spec.md / business_requirements.md → build
build       → build_manifest.md                              → validate
validate    → validation_summary.md                          → document
```

Discovery runs **once**, in assessment; everything downstream inherits it. Nothing critical
lives only in the conversation. This is what lets the loop survive context resets, be picked
up by a different agent, and be audited after the fact. If a decision matters, it's written
down in a typed handoff artifact — see [reference.md](reference.md#the-handoff-artifact-chain).

### 2. Human at the decisions, agent between them

The skills run **autonomously between gates**. Most "Gate:" lines in the skills are
*auto-checks* — the agent verifies a condition (rows landed, PK unique, FK resolves), reports
a scorecard, and proceeds without asking. You are pulled in only at a small number of **true
human gates**, where the decision is genuinely yours: approving model changes, signing off a
proposed DDL, accepting a known exception, approving prod promotion. Expect roughly **4–6 true
human gates per full lifecycle run** — not a prompt at every table. The
`autonomous-validation` skill codifies this contract (scratchpad-validate → confirm → persist;
run until a gate; self-grade and report, don't prod). See
[reference.md](reference.md#human-gates-vs-auto-checks).

### 3. Validate before you persist

Borrowed from `autonomous-validation`: the agent validates SQL in an ephemeral scratchpad,
confirms the result, and only *then* writes it to a notebook cell. A tutorial or sample query
that compiles but returns zero rows has **failed** — the suite treats non-empty, verified
results as the bar, not syntactic validity. This is why the generated documentation can be
trusted to match the data.

### 4. Quality is persisted and tracked, not asserted once

Validation doesn't run a batch of checks, print a grade, and forget. It writes results to a set of
`_validation_*` metadata tables in the model schema, surfaces them on a **quality dashboard** (grades,
gaps, drift, integration health), and ships a **re-runnable DAB job** so the same checks run on a
schedule or after any change. Because every run is a new row with computed grade/row-count deltas,
quality becomes something you *watch move* — a gap closing shows as a table climbing C → B → A on the
trend tab, and a regression trips a remediation handoff the moment a grade drops. The point is that
data-quality debt lives in a shared, queryable place (the gap registry and the dashboard) instead of
in someone's memory of a one-off run. See
[reference.md](reference.md#the-validation-quality-tracking-system-tables--dashboard--job).

## Scope reality: the fast path is silver

Be honest about what the loop delivers autonomously versus what still needs a human:

- **The fast path delivers a coherent, documented, validated *silver* layer** — conformed
  dimensions and facts, Type-1 by default, with FK integrity and DQ gates.
- **Deep, business-unit-specific logic and metrics (gold) still need human definition.** The
  same skills *accelerate* the gold/metrics layer — especially when there are existing
  dashboards/KPIs to grade generated metrics against (the validation skill's PARITY checks
  compare a generated metric to the number the business already trusts) — but gold is not a
  push-button output. Treat gold as "assisted," silver as "fast-path."

## Two layers of docs

It's worth being explicit, because it's the crux of how this repo is organized:

- **These developer docs** (`docs/developer/`) are about the **suite** — how a developer
  drives the four skills to build *any* domain. Audience: developers/implementers. Mostly
  stable; they change only as the suite changes.
- **The `domain-documentation` skill's output** is about **one built domain** — a Model
  Guide, a Genie space, insight tutorials, and a narrative, all aimed at that domain's data
  **consumers** (analysts, stakeholders). The skill also emits a *lightweight* co-located
  "maintaining this domain" guide for developers who later tend that specific model — and
  that guide links back here for the full suite explanation.

Keeping these two layers separate is deliberate: the suite-level "how to use the skills"
content lives **once**, here; the per-domain output never re-derives it.

## Pre-build decision paths

After the assessment, you close the gap between the vibe model and your real data before the build
starts. Two feedback loops govern that gap:

- **Gap & Enhancement Registry** — the *ingestion* loop. "You modeled X; no bronze exists —
  go get source {Y}." This is the only place that asks for more data.
- **`next_vibes.md`** — the *model-refinement* loop. "Here is how to make the model itself more
  coherent." It is emitted every run, in model-agent format, and never removes a modeled element
  for absence of data — only for business-coherence reasons.

These loops are complementary and must never overlap. Acting on one when you meant the other
leads to either a narrowed model (wrong) or an ingestion ask that won't land (wasted effort).

The full menu of pre-build decisions — iterate upstream, ingest more, defer and keep, deviate to
ship now, keep/drop null columns, and the three-way feedback router — is in
[how-to/decide-before-the-build.md](how-to/decide-before-the-build.md).

## Where to go next

- Ready to try it: [tutorial.md](tutorial.md)
- Need to do one specific thing: [how-to/](how-to/)
- Need the facts: [reference.md](reference.md)
