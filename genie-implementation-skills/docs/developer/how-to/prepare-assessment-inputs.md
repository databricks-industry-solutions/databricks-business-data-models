# How to prepare your own inputs for the assessment

**Goal:** seed the **Assess** station with prior knowledge you already have — a hand-written
requirements doc, a domain narrative, an existing ERD or data dictionary, known KPIs — so the
assessment builds on what you know instead of inferring everything from the vibe model alone.

**Roughly:** as long as it takes to drop in the docs you already have; 20–40 minutes if you write a
brief from scratch.

> **This is optional but high-leverage.** The loop runs fine with just the vibe model + `conventions.yml`.
> But `domain-model-assessment` explicitly supports users who **author requirements themselves** (silver
> *or* gold) — and the single best input you can give discovery is *which source systems feed this domain
> and where they live*. A little prose here sharpens every downstream artifact.

## When you'd do this

- You **wrote the requirements yourself** (a BRD, a spec) instead of — or alongside — the vibe model.
- You have **prior artifacts**: an ERD, a data dictionary, a glossary, an existing design doc.
- You know **domain facts the model can't encode**: which bronze systems are in play, the universal
  identifiers most facts hang off, cross-domain references, load order.
- You have **existing dashboards / KPIs** with trusted numbers (these seed gold + metric-parity — see
  [extend-to-gold.md](extend-to-gold.md)).

## The two kinds of input

### 1. Loose requirement docs → `docs/inputs/` (the intake mechanism)

Drop **any `.md` file** at the project root or in `docs/` before running the assessment. In its
**Phase 0 intake**, the skill detects files that aren't its own generated artifacts and `git mv`s them
verbatim into **`docs/inputs/`**, then treats that folder as **read-only source material**. It synthesizes
an authoritative `business_requirements.md` (and, for gold, the requirements brief) into **`docs/design/`**
*from* your inputs — it never rewrites your originals back. So:

- **Freeform is fine.** A BRD, meeting notes, a pasted email, an exported data dictionary — any `.md`.
  You don't need a specific structure; the skill reads and synthesizes.
- **Your originals are preserved.** Enriched/synthesized versions land in `docs/design/`, your inputs stay
  untouched in `docs/inputs/`.
- **No file, no folder.** If you drop nothing, `docs/inputs/` isn't created — the assessment infers from
  the model + `conventions.yml` and says so.

### 2. The discovery brief (structured Genie context)

For a sharper discovery pass, fill in
[`skills/domain-model-assessment/templates/discovery_brief.md`](../../../skills/domain-model-assessment/templates/discovery_brief.md).
It's the structured shell for the domain knowledge that most helps discovery find sources:

- the **domain narrative** (what process, which sites/geographies),
- **source systems expected** and their bronze neighborhoods (table prefixes/schemas),
- the **universal identifiers** most facts hang off,
- **entity groups** and **load order**, and **cross-domain references** not ported to the schema.

## What actually helps (ranked)

The content that moves the needle, roughly in order of leverage:

| Input | Why it helps | Relationship to `conventions.yml` |
| --- | --- | --- |
| **Source systems + where they live** | Gives discovery its search targets. "Orders come from SAP SD (`vbak`/`vbap`); quotes from Salesforce" tells the skill exactly where to look. | The **prose** companion to the structured `bronze_sources` map (see [fill-out-conventions.md](fill-out-conventions.md)) — the map says *where*, the narrative says *what's in there and why*. |
| **Universal identifiers** | The keys most facts hang off; anchors FK resolution. | — |
| **Existing requirements / BRD** | Becomes the seed for the synthesized `business_requirements.md`. | — |
| **Existing dashboards / KPIs with values** | Seeds gold requirements and gives metric-parity reference numbers. | Feeds the gold brief in [extend-to-gold.md](extend-to-gold.md). |
| **ERD / data dictionary / glossary** | Relationships and column meanings the model's comments may not fully capture. | — |
| **Domain narrative** | Process, sites, entity groups, cross-domain refs — context for grading fit. | — |

## Worked example — a minimal hand-authored requirements input

You don't need the full template. Even a short `docs/sales_order_requirements.md` like this, dropped at
the project root before running assess, gets folded into `docs/inputs/` and synthesized:

```markdown
# Sales Order — requirements (author-provided)

## Scope
Quote-to-cash for Meridian's B2B channels (OE, distributor, dealer, e-comm, interco).

## Source systems (and where they live)
- SAP S/4HANA SD — orders, scheduling, credit. Bronze: `meridian_bronze.sap_sd`
  (vbak = order header, vbap = order line, vbep = schedule line).
- Salesforce CRM — quotes/opportunities. Bronze: `meridian_bronze.salesforce_crm` (quote, quote_line).
- EDI gateway — electronic order messages. Bronze: `meridian_bronze.edi_gateway`.
- Returns portal — RMAs. Bronze: `meridian_bronze.returns_portal`.

## Universal identifiers
- Order: `order_number` (SAP vbeln). Customer: `customer_id` (SAP kunnr). Material: `material_id`.

## Known KPIs (for gold / parity)
- On-Time Delivery % (Ops dashboard shows 94.2% for Jun-26).
- Net Bookings ($48.3M Q2-26). Quote Conversion Rate.

## Notes / known gaps
- No cost/COGS source yet → margin KPIs can't be built (expected gap).
- No rep-quota feed → attainment can't be built (expected gap).
```

The skill lifts this into `docs/inputs/`, and Phase 1+ reads it as authoritative context alongside the
metamodel. The **no-silent-descope rule still applies** — anything you request that bronze can't support
becomes a recorded gap, exactly like the two "expected gap" notes above.

## Done when

Your input docs sit at the project root (or `docs/`) before you run `domain-model-assessment`, the skill
moves them into `docs/inputs/` in Phase 0, and the synthesized `docs/design/business_requirements.md`
reflects your source-system knowledge and requirements — so discovery searches the right places and the
gap registry reflects *real* missing data, not context you had but didn't hand over.
