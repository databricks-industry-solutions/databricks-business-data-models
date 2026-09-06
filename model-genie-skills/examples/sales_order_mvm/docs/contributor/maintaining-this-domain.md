# Maintaining This Domain — Sales Order

> **Per-domain maintenance guide.** This covers the Sales Order domain specifically.
> For the full skill suite decision tree, cross-domain recipes, and how to use the six loop skills,
> see **[`docs/developer/`](../developer/)** (repo-level developer documentation).

---

## This Domain at a Glance

| Item | Value |
|---|---|
| Schema | `manufacturing_silver_vibe.sales_order` |
| Pipeline | `sales_order_silver_pipeline` (`resources/sales_order_silver.pipeline.yml`) |
| ETL type | SDP (Lakeflow Spark Declarative Pipeline, 17 Materialized Views) |
| Source files | `src/silver/pipeline/*.sql` (17 files, one per entity) |
| Validation notebooks | `src/silver/validation/narrative_*` (17) + `scorecard` |
| Build handoff | `docs/.pipeline/handoffs/silver/build_manifest.md` |
| Validation handoff | `docs/.pipeline/handoffs/silver/validation_summary.md` |
| Model Guide | `Sales Order Model Guide` notebook (project root) |
| Genie space | UUID `01f1a7a4c7a513e8ba12be272cde5a82` — Sales Order Analytics |
| Tutorials | `docs/tutorials/01–03 Sales Order *` |
| Entities | 17 (5 reference, 12 transactional) — all Grade A |
| Key gap | Cross-domain FKs null: `account_id`, `plant_id`, `sku_id`, `price_list_id` |

---

## How to Add a Table to This Domain

Invoke the `etl-development-framework` skill:

> "Add a new entity `{entity_name}` to the Sales Order domain. Source: `{bronze_table}`. Key: `{natural_key}`."

The skill will:
1. Author `src/silver/pipeline/{entity_name}.sql` (MV definition with inline COMMENTs)
2. Register it in `resources/sales_order_silver.pipeline.yml`
3. Update `docs/.pipeline/handoffs/silver/build_manifest.md`

For the general procedure (conventions, FK patterns, EXPECT constraints), see
**[docs/developer/how-to/add-a-table.md](../developer/how-to/add-a-table.md)**.

---

## How to Fix a Degraded Table

If a validation run shows Grade B–F on an entity:

1. Check `src/silver/validation/narrative_{entity}` — the failing check details are there.
2. Invoke `etl-development-framework` with the remediation brief from the validation output.

For the general remediation workflow, see
**[docs/developer/how-to/fix-a-degraded-table.md](../developer/how-to/fix-a-degraded-table.md)**.

---

## How to Re-Sync After a Point Change

For a closed gap, FK fix, added column, or source repoint, invoke `domain-sync`:

> "Close the gap for `quotation.sales_contract_id` — the FK is now populated. Re-sync
> the narrative, Model Guide, Genie caveats, and validation summary."

`domain-sync` reads each artifact's `synced-against` stamp and scopes regeneration to
the changed entity only.

For the general staleness-linting and sync procedure, see
**[docs/developer/how-to/domain-sync.md](../developer/how-to/domain-sync.md)**.

---

## Pending Manual Steps (from this documentation run)

- [ ] Rename the Genie space from "Sales Order Analytics 2026-09-03 14:35:59" to
  "Sales Order Analytics" via the Genie UI.
- [ ] Paste instruction text from `docs/.pipeline/handoffs/genie_space_instructions.md`
  into the Genie space's instruction field.
- [ ] Add the 20 validated sample queries from the same file into the Genie space.
- [ ] Run `docs/.pipeline/handoffs/silver/enrich_uc_metadata.sql` to apply UC tags
  (after verifying governed-tag vocabulary allows the `domain`/`entity_type`/`tier`/`source_system` keys).
- [ ] Create `ARCHITECTURE.md` at the project root via the first `domain-sync` run.
