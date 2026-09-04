---
project: {project}
customer: {customer}
use_case: {Domain} Vibe V{version} — Integration Assessment
type: architecture_decision
created: {YYYY-MM-DD}
author: Genie Code
---

# {Domain} Vibe V{version} — Integration Assessment
## Can the Production {model_name} Be Folded into Vibe V{version}?

> **Short answer:** {one-sentence verdict and recommended option}

---

## Inventory of the Current Production Model

### Silver: `{catalog}.{schema}`

| Table | Rows | Source system(s) | Grain |
|---|---|---|---|
| `{table}` | {N} | {source} | {one-row-is} |

### Gold: `{gold_catalog}`

| Table | Schema | Rows | Purpose |
|---|---|---|---|
| `{table}` | `{schema}` | {N} | {purpose} |

---

## Why It Is / Is Not a Natural Fold-In

### 1. Grain Analysis

{Describe grain of existing model vs V2 grain. State: Full Overlap / Scope Mismatch /
Level Mismatch / Entity Mismatch. Give numerical evidence (row count comparison).}

### 2. Naming & Structural Conventions

| Dimension | Existing Model | Vibe V2 Standard | Pass? |
|---|---|---|---|
| Column case | {actual} | Pascal_Snake_Case | {Y/N} |
| Metadata prefix | {actual} | _lower_snake_case | {Y/N} |
| Column comments | {yes/no} | Required | {Y/N} |
| UC tags | {yes/no} | Required | {Y/N} |

### 3. Purpose Classification

{Semantic Contract or Gold-pattern? Evidence: does it have computed KPIs? Single-use-case joins?
Window functions in base tables?}

---

## Where They Align: Source Inputs for V2

| Existing table | V2 target entity | How it maps | Source quality uplift |
|---|---|---|---|
| `{table}` | `{entity}` | {column mapping summary} | {benefit vs re-reading bronze} |

### Gold / Other Tier Tables That Unblock V2 Entities

| Table | Unblocked V2 entity | What it provides |
|---|---|---|
| `{gold_table}` | `{entity}` | {specific columns / rows} |

---

## The Architecture Options

### Option {A/B/C} — {Name} (RECOMMENDED)

```
{ASCII diagram of data flow}
```

Outcome: {what changes}
Risk: {what could go wrong}

### Option {A/B/C} — {Name}

{Same structure}

---

## Recommendation

**Adopt Option {X} now, targeting Option {Y} within {timeline}.**

### Phase 1 — Immediate

| V2 entity | Read from | Instead of re-reading bronze |
|---|---|---|

### Phase 2 — Medium term

{Steps to re-platform gold layer}

### Phase 3 — Long term

{Steps to decommission existing silver}

---

## Updated Discovery Report Amendments

| Table | Previous grade | Revised grade | Reason |
|---|---|---|---|

**Revised summary: {X} Full · {Y} Partial · {Z} Blocked** (was {A}/{B}/{C})

---

*Analysis by Genie Code — {date}. All data profiled read-only.*
