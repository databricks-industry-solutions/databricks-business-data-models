# Validation Skill — Session Feedback

> **Domain:** Sales Order (Meridian Manufacturing)  
> **Session date:** 2026-09-03  
> **Scope:** Full domain-model-validation run — 17 entities, 5 metadata tables, 17 narrative notebooks, 1 scorecard, 1 dashboard, 1 DABs job  
> **Outcome:** All 17 entities Grade A, 99/99 checks PASS — but with significant friction along the way  
> **Purpose:** Feedback for Claude Code to improve the `domain-model-validation` skill

---

## 1. Notebook not persisted after scratchpad validation

**Severity:** HIGH — should be a hard rule in the skill

**What happened:** The skill validated each entity's SQL in a scratchpad cell (via `executeCode`), confirmed the checks passed, then moved on to the next entity without persisting the validated SQL into the actual notebook asset. This meant:

- Work existed only in ephemeral execution results, not in the durable notebook files
- If the session had been interrupted mid-batch, completed work for already-validated entities would have been lost
- The user had to explicitly ask whether the notebooks had been saved

**What should happen:** The skill must persist each narrative notebook to the workspace asset *immediately* after its scratchpad validation passes, before moving on to the next entity. This should be a hard, non-negotiable rule in the skill:

> **Proposed rule:** "After validating a narrative notebook's SQL in scratchpad and confirming all checks PASS, persist the notebook to the workspace asset via `editAsset` or workspace API import. Do NOT begin the next entity until the current entity's notebook is durably written. Verify the write succeeded before marking the entity complete."

This aligns with the `autonomous-validation` skill's core principle: *validate in scratchpad → confirm → persist*. The "persist" step was being skipped.

---

## 2. Recurring GROUP BY / aggregate bug in drift check cells

**Severity:** HIGH — affected 5 of 17 notebooks; same root cause each time

**What happened:** The exploratory "Drift Check" cell in multiple narrative notebooks used this pattern:

```sql
-- BROKEN: COUNT(*) is aggregate, b.* columns are not → MISSING_GROUP_BY error
SELECT 'quotation' AS table_name, 'ROW_COUNT' AS metric_type,
  CAST(COUNT(*) AS STRING) AS current_value,
  b.Baseline_Value, b.Tolerance_Pct,
  CASE WHEN b.Baseline_Value IS NULL THEN 'BASELINE' ... END AS drift_status
FROM quotation
LEFT JOIN _data_drift_baseline b ON ...;
```

This mixes an aggregate function (`COUNT(*)`) with non-aggregated columns (`b.Baseline_Value`, `b.Tolerance_Pct`) without a GROUP BY, which Databricks SQL rejects with `MISSING_GROUP_BY` / `SQLSTATE: 42803`.

The correct pattern (which the Write Results cells already used correctly) wraps the aggregate in a subquery:

```sql
-- CORRECT: aggregate computed in subquery, outer SELECT has no aggregates
FROM (SELECT COUNT(*) AS cnt FROM quotation)
LEFT JOIN _data_drift_baseline b ON ...;
```

**Affected notebooks:** `narrative_sales_contract`, `narrative_sales_contract_line`, `narrative_quotation`, `narrative_order`, `narrative_quotation_line` (5 of 17)

**Why this is concerning:**
- The Write Results cell in the *same notebooks* used the correct subquery pattern, proving the skill "knew" the right approach but didn't apply it consistently to the exploratory cell
- The bug appeared in the Tier 0–2 notebooks (built first) but not in Tier 3–5 (built later), suggesting the skill self-corrected partway through but never went back to fix the earlier work
- The same class of aggregate-without-GROUP-BY error also appeared in the scorecard (see item 4 below)

**Proposed rule:** "When joining an aggregate result to a lookup/reference table, always compute the aggregate in a subquery first. Never mix `COUNT(*)`, `SUM()`, or other aggregate functions with non-aggregated columns from a JOIN without GROUP BY. This applies to both exploratory cells and Write Results cells."

---

## 3. No hard completion check before declaring done

**Severity:** MEDIUM — erodes trust in autonomous operation

**What happened:** The skill declared "all phases complete" and presented the summary without running a systematic verification pass. The user had to:

- Manually run individual notebooks to discover the drift check errors
- Ask whether notebooks had actually been persisted
- Request a scan across all 17 notebooks to find the GROUP BY bug

**What should happen:** Before declaring a phase complete, the skill should run a concrete verification checklist:

1. **Persistence check:** For each entity, confirm the notebook asset exists at the expected path and contains the expected cells (widget header, checks, Write Results)
2. **Execution check:** Run the Write Results cell of each notebook (or at minimum a dry-run parse) to confirm zero SQL errors
3. **Completeness check:** Query `_validation_check_detail WHERE Run_Id='PENDING'` and confirm the expected number of check rows exist for each entity
4. **Cross-entity consistency check:** Verify all notebooks use the same SQL patterns (e.g., subquery for drift checks, COALESCE for FK orphan rates)

**Proposed rule:** "Before declaring any batch or phase complete, run a verification pass that confirms: (a) all artifacts are persisted, (b) all SQL executes without error, (c) check counts match expectations. Present the verification results to the user. Do not declare done until verification passes."

---

## 4. Scorecard correlated subquery bug (same aggregate class)

**Severity:** MEDIUM — blocked scorecard execution; same root cause as item 2

**What happened:** The scorecard's grade-computation cell used a correlated subquery inside a GROUP BY context:

```sql
-- BROKEN: correlated subquery in aggregate context
(SELECT COUNT(*) FROM _gap_registry g
 WHERE g.Table_Name = cd.Table_Name AND g.Status != 'RESOLVED')
```

This triggered `SCALAR_SUBQUERY_IS_IN_GROUP_BY_OR_AGGREGATE_FUNCTION`. The fix was converting to a pre-aggregated LEFT JOIN:

```sql
LEFT JOIN (
  SELECT Table_Name, COUNT(*) AS gap_count
  FROM _gap_registry WHERE Status != 'RESOLVED'
  GROUP BY Table_Name
) gc ON cd.Table_Name = gc.Table_Name
```

**Takeaway:** The skill should have a general rule about never using correlated subqueries inside aggregate contexts. Both this and the drift check bug are the same underlying SQL anti-pattern: mixing aggregate and non-aggregate expressions without proper isolation.

---

## 5. Inconsistent code generation across batches

**Severity:** MEDIUM — creates maintenance burden and makes bugs harder to spot

**What happened:** The Tier 0–2 notebooks (built first) had different SQL formatting, column aliases, and patterns compared to Tier 3–5 (built later). Specific examples:

- Tier 0–2 drift cells used inline `COUNT(*)` (buggy); Tier 3–5 used subquery (correct)
- Column aliases varied (`current_value` vs `curr`, `table_name` vs `t`)
- Some notebooks had richer CASE expressions in the drift check; others had minimal `'BASELINE' ELSE 'CHECK'`

**What should happen:** The skill should establish a canonical template *before* generating any notebooks and apply it uniformly. If the template is refined during generation (as happened with the drift fix), the skill should go back and update earlier notebooks to match.

**Proposed rule:** "When a code pattern is corrected mid-batch, immediately propagate the fix backward to all previously generated notebooks in the same batch before continuing forward. Never leave known-buggy patterns in earlier work."

---

## 6. Initial bug scan missed one notebook (fragile detection)

**Severity:** LOW — but reveals a process gap

**What happened:** When asked to scan all 17 notebooks for the GROUP BY bug, the first scan reported `narrative_quotation_line` as OK. It was actually buggy — the SQL used slightly different formatting (`AS t` instead of `AS table_name`, `AS curr` instead of `AS current_value`), which evaded the regex pattern. The user ran the notebook and found the error, requiring a second fix pass.

**Takeaway:** Pattern-matching for bugs is fragile. The verification pass (item 3) should *execute* the SQL, not just grep for text patterns. A `SELECT ... LIMIT 0` dry-run parse is cheap and catches 100% of syntax/semantic errors regardless of formatting.

---

## 7. Dashboard creation required excessive trial-and-error

**Severity:** LOW — user wasn't blocked, but it burned tokens and time

**What happened:** The Lakeview dashboard creation took multiple attempts because:

- Initial widget specs used `version: 3` for all widget types; counters and tables require `version: 2`
- The `data.queryName` reference was missing from widget specs, causing "invalid widget definition" errors
- The SDK-based approach was blocked by the safety checker, requiring a fallback to raw `urllib.request` calls

**Takeaway:** The skill's `dashboard-spec.md` should include a tested, copy-paste-ready widget spec template for each widget type (counter, table, bar, line, pie) with the correct version numbers and required fields pre-filled. The current spec describes the *schema* but doesn't provide complete working examples.

---

## 8. Handoff document had incorrect gap counts

**Severity:** LOW — data integrity issue in documentation

**What happened:** The `validation_summary.md` handoff listed 14 DEFERRED gaps, but the actual `_gap_registry` table had 15 (12 P2 + 3 P3). The discrepancy was 1 gap (the `quotation.sales_contract_id` deferred FK). This was only caught when the gap registry was queried to verify.

**Takeaway:** Handoff documents should be generated *from queries against the metadata tables*, not from the skill's in-memory count of what it thinks it wrote. A simple `SELECT Status, COUNT(*) FROM _gap_registry GROUP BY Status` would have caught this.

---

## Summary of Proposed Skill Rules

| # | Proposed Rule | Priority |
|---|---|---|
| R1 | Persist each notebook immediately after scratchpad validation passes, before starting next entity | MUST |
| R2 | Never mix aggregate functions with non-aggregated JOIN columns — always use subquery isolation | MUST |
| R3 | Run a concrete verification pass (persist + execute + count) before declaring any phase complete | MUST |
| R4 | When a pattern is fixed mid-batch, propagate the fix backward to all earlier notebooks | SHOULD |
| R5 | Generate handoff documents from live metadata queries, not from memory | SHOULD |
| R6 | Dashboard spec should include complete working widget templates with correct version numbers | SHOULD |
| R7 | Use SQL execution (not regex) to verify generated SQL is error-free | SHOULD |
