# Documentation Skill Session Feedback

> **Domain:** Sales Order (`manufacturing_silver_vibe.sales_order`)  
> **Skill:** `domain-documentation` (all six phase files)  
> **Session date:** 2026-09-03  
> **Purpose:** Feedback for Claude Code to improve the `domain-documentation` skill.
> This file captures every issue — from UX annoyances to data-correctness bugs — encountered
> during a full 6-phase documentation run on a 17-entity silver-only domain.

---

## Issue 1: Genie Space Name Gets a Timestamp Appended

**Severity:** UX / cosmetic  
**Phase:** 5 (Genie Space)

**What happened:** `createAsset(assetType='genie', name='Sales Order Analytics')` created a
space named **"Sales Order Analytics 2026-09-03 14:35:59"**. The platform appends a timestamp
to the requested name. The skill's `genie-space-config.md` documents this behavior but offers
no workaround.

**Impact:** The space name is ugly and unprofessional in the Genie UI. Every downstream
reference (Model Guide, maintenance guide, genie_space_instructions.md) had to note the
mismatch and add a "rename this manually" pending step.

**Recommended fix for the skill:**
1. After `createAsset`, immediately attempt to rename the space via whatever API is available
   (the `renameTitle` tool works for notebooks/queries — investigate whether it works for
   Genie spaces, or if the Databricks CLI has an equivalent).
2. If no rename API exists, the skill should:
   - Always reference the space by UUID, never by display name.
   - Add a prominent `## Pending Manual Step` block to the maintenance guide and
     `genie_space_instructions.md` with the exact rename instruction.
   - Consider prefixing the name with the domain name only (no "Analytics" suffix) to
     minimize the visual damage of the appended timestamp.

---

## Issue 2: Model Guide Links Don't Work in Databricks Browser

**Severity:** High — breaks the primary navigation experience  
**Phase:** 4 (Model Guide Notebook)

**What happened:** The Model Guide's Quick Navigation table used relative markdown links:
```markdown
| Understand the model | [Domain Narrative](docs/explanation/domain_narrative.md) |
| Contribute           | [Contributor Guide](docs/contributor/maintaining-this-domain.md) |
```
These paths work in a Git file browser (GitHub, VS Code) but **do not resolve** when clicking
from a Databricks notebook rendered in the browser. The user had to manually add browser links.

**What the user fixed (manually):**
```markdown
| Understand the model | [Domain Narrative](docs/explanation/domain_narrative.md).... [in browser link](https://host/editor/files/2237626864845442?o=...) |
| Contribute           | [Contributor Guide](docs/contributor/maintaining-this-domain.md) ... [in browser link](https://host/editor/files/2237626864845452?o=...) |
```

**Recommended fix for the skill:**
The `model-guide.md` template should instruct the agent to emit **dual links** for every
cross-file reference in the Model Guide:

```markdown
[Domain Narrative](docs/explanation/domain_narrative.md) · [open in browser](/editor/files/{assetId})
```

The agent already has the `assetId` from the `createAsset` call that produced each file.
The skill should:
1. Collect a `{filename → assetId}` registry during Phases 2–3 as files are created.
2. In Phase 4, emit both the relative path (for Git portability) and the `/editor/files/{id}`
   path (for Databricks browser) for every link in the Welcome & Orientation cell and the
   Documentation Map cell.
3. Document this dual-link pattern in the model-guide.md template so it's not forgotten.

---

## Issue 3: `createAsset` Path Doubling Bug

**Severity:** Medium — causes file creation at wrong location  
**Phase:** 2 (Domain Narrative)

**What happened:** On the first attempt to create `docs/explanation/domain_narrative.md`,
the agent passed a full workspace-absolute path to `createAsset`. The tool interpreted this
as relative to the user's home directory, producing a doubled path:
```
/Users/stuart.swartz/.../vibe-model-skills-testing/meridian/sales-order-mvm/
  vibe-modeling-skills-testing/vibe-model-skills-testing/meridian/sales-order-mvm/
    docs/explanation/domain_narrative.md
```
A blank file was created at the wrong nested location (assetId `2237626864845440`).
The agent caught this on read-back and re-created the file using only the project-relative
path (`docs/explanation/domain_narrative.md`), which worked correctly.

**Recommended fix for the skill:**
Add an explicit rule to `phase-protocol.md`:
> When creating files with `createAsset`, always use the **project-relative path** (e.g.,
> `docs/explanation/domain_narrative.md`), never the full workspace path. The CWD is the
> project root; the tool resolves relative to CWD.

---

## Issue 4: Generated Queries Referenced Non-Existent Columns

**Severity:** High — queries would fail at runtime  
**Phase:** 5 (Genie Space sample queries)

**What happened:** The agent initially wrote ATP-related sample queries referencing
`atp_check.requested_date` and `atp_check.confirmed_date`. These columns **do not exist**.
The actual columns are:
- `requested_quantity` (DECIMAL)
- `confirmed_quantity` (DECIMAL)
- `earliest_confirmation_date` (DATE)
- `check_timestamp` (TIMESTAMP)

The agent caught this via scratchpad validation (the `autonomous-validation` pattern),
fixed the queries, and re-validated. But the initial generation was wrong.

**Root cause:** The agent inferred column names from business semantics ("ATP checks dates")
instead of reading the actual pipeline SQL or UC metadata first.

**Recommended fix for the skill:**
Add a mandatory pre-step to Phase 5 in `genie-space-config.md`:
> Before writing ANY sample query, the agent MUST read the column dictionary for every
> table referenced in the query — either from the `information_schema.columns` result
> (if the Model Guide has been run) or from the pipeline SQL files. Column names must
> be copy-pasted from the schema, never inferred from business semantics.

---

## Issue 5: Return Order FK Column Name Wrong

**Severity:** High — query errors at runtime  
**Phase:** 5 (Genie Space sample queries)

**What happened:** The agent wrote a return-rate query joining on `return_order.order_id`,
but the actual FK column is `return_order.original_order_id` (as defined in the pipeline SQL
and `conventions.yml` entity spec). The query failed on execution, and the agent corrected it.

**Root cause:** Same as Issue 4 — the agent assumed a standard FK naming convention instead
of reading the actual schema. The column name `original_order_id` is non-obvious and specific
to the RMA return-to-original-order relationship.

**Recommended fix:** Same as Issue 4. Additionally, the `genie-space-config.md` should note:
> FK column names are NOT always `{parent_entity}_id`. Read the actual column COMMENTs
> (which document FK targets) before writing JOIN conditions.

---

## Issue 6: Hybrid Gate Triggered Without Checking Gold Existence

**Severity:** High — caused the previous run to document a non-existent gold layer  
**Phase:** 1 (Context Gathering)

**What happened:** `conventions.yml` declares `output_model: hybrid`, which means the domain
is designed to have both a normalized silver layer and a dimensional gold star layer. However,
the gold layer was **explicitly deferred** — it was never built. The previous documentation
run (before this session) "accidentally picked up a gold layer" — it generated gold-referencing
artifacts, a gold column dictionary, and gold sample queries for tables that don't exist.

This session correctly identified the gap by checking for the gold validation summary
(which was absent) and treated the run as silver-only.

**Recommended fix for the skill:**
The Layer & ETL-type Gate in `phase-protocol.md` should add an explicit existence check:

```
IF conventions.yml says output_model: hybrid THEN
  CHECK: Does docs/.pipeline/handoffs/gold/validation_summary.md exist?
  CHECK: Does a gold schema actually contain tables?
  IF NEITHER exists → treat as silver-only; log warning:
    "conventions.yml declares hybrid but no gold artifacts found. 
     Proceeding as silver-only. Gold documentation deferred."
```

The current gate trusts `conventions.yml` at face value without confirming the gold layer
was actually built and validated.

---

## Issue 7: Gold Layer Claimed Without Verifying Project Ownership

**Severity:** High — caused the previous run to document tables this project doesn't own  
**Phase:** 1 (Context Gathering)

**What happened:** In the previous documentation run, the skill discovered gold-layer tables
in the catalog (e.g., a dimensional star schema in `manufacturing_gold_vibe` or similar) and
assumed they belonged to this domain. It generated gold documentation artifacts — column
dictionaries, sample queries, narrative sections — for tables that were **built by a different
project** (likely a sibling domain or an earlier experiment).

The tables existed in the catalog, and the schema name was plausible, so the skill treated
them as part of the sales order domain. But they were never referenced in this project's
`databricks.yml`, pipeline YAML, `build_manifest.md`, or any pipeline SQL file.

**Root cause:** The skill's gold detection logic checked whether gold tables *exist in the
catalog* but did not verify whether those tables *belong to this project*. Catalog-level
existence is necessary but not sufficient — multiple projects can write to the same catalog.

**Recommended fix for the skill:**
Add a **project-ownership gate** to the Layer & ETL-type Gate in `phase-protocol.md`:

```
IF gold tables are found in the catalog THEN
  CHECK: Are any of these tables declared in this project's:
    - databricks.yml (pipeline targets)?
    - resources/*.pipeline.yml (pipeline table list)?
    - src/gold/pipeline/*.sql (pipeline SQL files)?
    - docs/.pipeline/handoffs/gold/build_manifest.md?
  IF NONE match → do NOT claim them as part of this domain.
    Log warning: "Gold tables found in catalog but not owned by this project.
    Treating as silver-only. If these tables belong to this domain, add them
    to the pipeline configuration."
```

The principle: **catalog existence ≠ project ownership**. Only tables traceable to this
project's build artifacts should be documented.

---

## Issue 8: Sandbox Data Gaps Caused Query Validation Surprises

**Severity:** Low — not a skill bug, but worth documenting  
**Phase:** 5 (Genie Space sample query validation)

**What happened:** Several queries returned unexpected results due to sandbox data gaps:
- **Contract coverage:** 100% of orders have `sales_contract_id = NULL`. The JOIN from
  `order` to `sales_contract` matches on `contract_number = order vbeln`, which finds
  no matches in sandbox data. Not a schema bug — the test data simply lacks contract
  relationships.
- **Schedule line forward commitments:** 0 rows when filtering `>= current_date()` because
  all sandbox data is historical (through 2026-06-30) and the session ran on 2026-09-03.

**Impact:** Sample queries that work against production data return empty results in the
sandbox. The agent correctly handled this by:
1. Documenting the gap in the Genie instruction caveats.
2. Removing the future-date filter from the schedule line query.
3. Adding a note about the contract coverage gap.

**Recommendation for the skill:**
Add a note to `genie-space-config.md`:
> When validating sample queries against sandbox/dev data, expect NULL FK columns and
> date-range gaps. Document these as caveats in the instruction text rather than treating
> them as query bugs. Remove date filters that assume production-scale data ranges.

---

## Issue 9: Model Guide `%sql` / Rule 13 Compliance Requires Extra Vigilance

**Severity:** Medium — could produce broken notebooks if missed  
**Phase:** 4 (Model Guide Notebook)

**What happened:** The Model Guide notebook is SQL-shape (default language = Python, but all
cells are `language: sql` or `language: markdown`). The skill's Rule 13 requires a read-back
verification that no `# MAGIC` prefixes appear in cell content. The agent performed this
check correctly, but it required an extra tool call purely for verification.

**Recommendation for the skill:**
Consider having `model-guide.md` specify that the Model Guide should be created as a
**SQL notebook** (not a Python notebook with SQL cells). This would eliminate the
SQL-shape compliance concern entirely. The Model Guide contains zero Python code —
there's no reason for the default language to be Python.

Alternatively, if the Python default is required for widget compatibility, document why
in the template.

---

## Summary of Recommended Skill Changes

| # | File to Change | Change |
|---|---|---|
| 1 | `genie-space-config.md` | Add post-create rename attempt; document UUID-only referencing |
| 2 | `model-guide.md` | Dual-link pattern: relative path + `/editor/files/{id}` for all cross-file refs |
| 3 | `phase-protocol.md` | Add rule: use project-relative paths only in `createAsset` |
| 4 | `genie-space-config.md` | Mandatory column-dictionary read before writing any sample query |
| 5 | `genie-space-config.md` | Note that FK columns are not always `{parent}_id`; read COMMENTs |
| 6 | `phase-protocol.md` | Hybrid gate must confirm gold artifacts exist before treating as hybrid |
| 7 | `phase-protocol.md` | Gold ownership gate: catalog existence ≠ project ownership; verify via build artifacts |
| 8 | `genie-space-config.md` | Sandbox data gap handling guidance |
| 9 | `model-guide.md` | Consider SQL notebook default language, or document why Python is required |

---

*Generated by the documentation session agent on 2026-09-03. Review and apply selectively.*
