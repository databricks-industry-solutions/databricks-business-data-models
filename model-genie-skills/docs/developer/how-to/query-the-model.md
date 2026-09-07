# How to query the model through the Genie space

**Goal:** ask business questions of a built domain in natural language — and read the answers **honestly
against the model's documented gaps**, so an empty column or a surprising number sends you to the right
explanation instead of a wrong conclusion.

**Roughly:** minutes — this is the consumer's entry point, not a build task.

> **Audience note.** This is the one **consumer-facing** guide in this folder. The others assume you're
> building or operating the model; this one assumes you just want to *use* it. If you built it, point your
> analysts here.

## Step 1 — Find the space and start from the sample queries

The documentation skill auto-generates a Genie space named **`{Domain} Analytics`** (e.g. "Sales Order
Analytics"). Two things to know:

- The **space UUID is the stable reference** — `createAsset` may append a timestamp to the display name,
  so don't rely on the exact name matching the doc.
- The space ships with **curated sample queries** — these *are* the how-to layer. Start from one that's
  close to your question and adapt it, rather than asking cold; every sample query was validated against
  the live schema, so it's a known-good starting shape.

Genie writes the SQL for you using the model's UC metadata (column comments, FKs) plus curated
instructions. You don't need to know the schema — but you do need to know the three caveats below.

## Step 2 — The three things that keep answers honest

The Genie space's instruction text encodes these, but knowing them yourself is what separates a trustworthy
answer from a plausible-looking wrong one.

1. **`-1` means "Unknown", not zero.** When a fact row had no match for a dimension, its FK is set to `-1`
   (the explicit Unknown member). **Aggregations should filter `WHERE {Key} != -1`** — otherwise an
   "Unknown" bucket silently inflates or skews your totals. If a breakdown shows a large "Unknown" slice,
   that's this, and it's usually a documented gap (next point), not bad data.

2. **An empty or NULL column may be a *documented gap*, not a data error.** A modeled attribute with no
   bronze source is never silently dropped — it's built as an unpopulated column and recorded in the gap
   registry (status `OPEN` / `IN_PROGRESS` / `DEFERRED` / `ACCEPTED`). So before concluding "the data is
   broken", check whether the column is a **known gap** — e.g. in the Meridian gold example, *Gross Margin*
   and *Rep Quota Attainment* are empty **by design** because silver has no cost/quota source yet (see
   [extend-to-gold.md](extend-to-gold.md)). The Genie caveats and the Model Guide list these; a documented
   gap is a *finding*, not a failure.

3. **In a `hybrid` model, prefer the gold star for analytics.** A hybrid space exposes two layers: the
   **gold dimensional star** (`dim_`/`fact_`, conformed dims — the **preferred analytics surface**, clean
   joins) and the **normalized silver** (3NF — for operational detail, lineage, or entities gold doesn't
   model). Don't mix silver natural keys with gold surrogate keys in one question — ask against the star
   for KPIs, drop to silver only for detail the star doesn't carry.

## Step 3 — When an answer looks wrong

Work down this list before trusting or discarding a surprising result:

- **Is it a documented gap?** Empty column / big "Unknown" bucket → check the gap registry or the Model
  Guide's caveats. Likely expected.
- **Is the space stale?** The instruction text carries a `synced-against` stamp. If the model changed
  after that stamp, the space may be describing an older shape — ask the maintainer to re-sync (see
  [re-sync-after-a-change.md](re-sync-after-a-change.md)).
- **Wrong joins / surrogate-vs-natural-key mixups?** Usually means UC FKs aren't registered or the
  two-layer routing wasn't taught — a maintainer fix, again via re-sync.
- **Genie SQL just looks off?** Fall back to the nearest **sample query** (validated) and adapt it.

## Step 4 — Go deeper than a single question

- **Model Guide notebook** (project root) — the entry point. Live `INFORMATION_SCHEMA` reference queries
  (always current), the glossary, and the caveat list. Read this to understand *what's in the model*.
- **Domain narrative** (`docs/explanation/domain_narrative.md`) — the *why*: what the domain represents,
  how the entities relate, what the model can and can't answer.

## Done when

You can get a business question answered in natural language, and — crucially — you can tell the difference
between a real number, a documented-gap emptiness, and a stale-space artifact, routing each to the right
place instead of trusting a wrong answer.
