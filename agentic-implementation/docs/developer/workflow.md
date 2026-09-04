# Workflow map — where to start, and what to decide

Two pictures for orienting a run of the suite: **when to start using the skills** (and where you
enter the loop), and **the decision tree after the assessment completes**. Both are maps, not the
spec — each links to the prose that is the source of truth. GitHub renders the diagrams inline.

---

## 1 · When to start using the skills

Getting started spans **two phases with a clean handoff between them**. First, upstream in the
**vibe-modeling app**: deploy the app, generate a baseline domain model, pick the domain you want
to bring alive, iterate on it a few times with human feedback *in the app*, then deploy the settled
model to a **catalog**. That deployed model — coherent and human-reviewed — is the **frozen input**
to this suite.

Then, in **Genie Code**, this suite picks up: settle `conventions.yml` (the assessment bootstraps
it interactively in Phase −1 if it's absent), load `autonomous-validation` alongside the loop
skills, and run the `domain-model-assessment` to see **how well your real data fits the modeled
domain**. Its output — grades + Gap Registry + `next_vibes.md` — is exactly what the
[decision tree in §2](#2--the-decision-tree-after-the-assessment) acts on. Clear that gate and the
four stations run **one domain at a time**; once a domain is built, `domain-sync` keeps its
artifacts current in steady state.

```mermaid
flowchart TD
    subgraph APP["In the vibe-modeling app"]
        A1["Deploy the app"] --> A2["Generate a baseline<br/>domain model"]
        A2 --> A3["Choose a domain"]
        A3 --> A4["Iterate with human<br/>feedback in the app"]
        A4 -.->|"refine a few times"| A4
        A4 --> A5["Deploy the model<br/>to a catalog"]
    end

    A5 ==>|"frozen model + bronze data"| E

    subgraph GC["In Genie Code — this suite, one domain at a time"]
        E["conventions.yml<br/>(Phase −1 bootstrap if absent)<br/>+ load autonomous-validation"] --> S1
        S1["1 · Assess<br/>domain-model-assessment"] --> DT{{"Decision tree — §2<br/>how well does your data fit?"}}
        DT --> S2["2 · Build<br/>etl-development-framework"]
        S2 --> S3["3 · Validate<br/>domain-model-validation"]
        S3 --> S4["4 · Document<br/>domain-documentation"]
        S4 --> G(["Domain built"])
        G --> H["Steady state:<br/>domain-sync on point updates"]
        G -.->|next domain| S1

        S1 -.->|handoff docs| S2
        S2 -.->|build manifest| S3
        S3 -.->|validation summary| S4
    end
```

**Handoff between stations is through documents, not chat** — the dotted links are the artifacts
(`etl_detailed_spec.md` → `build_manifest.md` → `validation_summary.md`) that carry discovery
forward so it runs once. New to the loop? Run it end-to-end on the Meridian domain via the
[tutorial](tutorial.md); the station catalog and handoff chain are in [reference.md](reference.md).

---

## 2 · The decision tree after the assessment

The `domain-model-assessment` ends with an S2T Mapping Report, a Gap & Enhancement Registry, and
`next_vibes.md` — plus a Full / Partial / Blocked grade per entity. Before the build, you close the
gap between the vibe model and your real data by giving **every open (Partial/Blocked) item a
recorded disposition**. The paths below are not mutually exclusive — defer some entities, take a
few vibes upstream, deviate on others, all in the same handoff. The build starts from that durable
record, never from the conversation.

```mermaid
flowchart TD
    A(["Assessment complete<br/>grades + Gap Registry + next_vibes.md"]) --> B{"For each open<br/>Partial / Blocked item:<br/>why is it open?"}

    B -->|"model is wrong about<br/>the business"| P1["Path 1 · Iterate upstream<br/>take next_vibes.md to the vibe agent → V+1"]
    B -->|"data not landed yet,<br/>model is right"| P2["Path 2 · Ingest & re-run<br/>action Gap Registry P0–P3"]
    B ==>|"anything not routed<br/>elsewhere"| P3["Path 3 · Defer<br/>the default catch-all — recorded DEFERRED,<br/>no silent descoping"]
    B -->|"ship a clean silver,<br/>prune to what you have"| P4["Path 4 · Deviate<br/>(opt-in model_deviation, human-gated)"]
    B -->|"pushing back on a<br/>specific item"| P6["Path 6 · Feedback router<br/>(can't-get / don't-do / you're-wrong)"]

    P1 -.->|"V+1 re-enters (Trigger E)"| A
    P2 -.->|"new bronze re-enters (Trigger A)"| A

    P3 --> N{"Always-null columns:<br/>keep or drop?<br/>(downstream, at handoff)"}
    P4 --> N
    P6 --> N

    N --> R(["Every open item now has a recorded<br/>disposition (Defer catches the rest)<br/>→ Start the build · etl-development-framework"])
```

Each path — when to pick it, how to invoke it, and its trade-off — is written out in
[how-to/decide-before-the-build.md](how-to/decide-before-the-build.md). The two feedback loops it
draws on (the Gap Registry for data-catches-up, `next_vibes.md` for model-refinement) and the
bright line between them are explained in [explanation.md](explanation.md#how-it-fits-with-the-vibe-model).
