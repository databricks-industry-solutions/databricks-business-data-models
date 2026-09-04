# How to investigate a data-drift alert

**Goal:** understand and act on a drift alert raised by the validation suite (a metric or
distribution moved beyond its baseline tolerance).

## Step 1 — Read the drift detail

Load `domain-model-validation` and open the affected entity's narrative:

> "Show me the drift detail for `{entity}`."

Read the `narrative_{entity}` notebook and the `_data_drift_baseline` comparison. The narrative
explains what shifted, by how much, and against which baseline.

## Step 2 — Classify the drift

Decide which of two situations you're in:

- **Legitimate change** — the business genuinely changed (new plant online, seasonality, a real
  volume shift). The data is correct; the baseline is stale.
- **Defect** — the drift signals a broken load (a source schema change, a bad join, dropped
  rows). The data is wrong.

## Step 3a — If legitimate: accept the new baseline

> "Accept the new baseline for `{entity}`."

The skill updates `_data_drift_baseline` to the new normal. Document *why* in the acceptance so
the next reviewer understands the shift.

## Step 3b — If a defect: escalate to a fix

Treat it like a degraded table — generate a remediation brief and hand it to the build skill.
See [fix-a-degraded-table.md](fix-a-degraded-table.md).

## Done when

Either the baseline is updated with a documented reason, or a fix is in flight with a
remediation brief and a POST_FIX plan.
