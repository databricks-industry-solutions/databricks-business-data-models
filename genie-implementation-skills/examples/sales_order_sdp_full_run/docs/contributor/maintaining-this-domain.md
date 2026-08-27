<!-- synced-against: progress.md @ 2026-08-09 (rev: VAL-SDP-GOLD-20260809) -->

# Maintaining the Sales Order Domain (SDP Hybrid)

This domain models B2B sales order processing across silver (3NF normalized, 17 entities) and gold (dimensional star, 13 entities) layers, deployed as a single Lakeflow SDP pipeline.

## This Domain at a Glance

| Entity | Layer | Type | Tier | Grade |
|---|---|---|---|---|
| sales_area | Silver | REF | 0 | A |
| order_reason | Silver | REF | 0 | A |
| channel_config | Silver | REF | 1 | A |
| sales_contract | Silver | MASTER | 1 | A |
| sales_contract_line | Silver | MASTER | 2 | A |
| quotation | Silver | TXN | 2 | A |
| order | Silver | TXN | 3 | A |
| quotation_line | Silver | TXN | 3 | A |
| order_line | Silver | TXN | 4 | A |
| order_partner | Silver | TXN | 4 | A |
| order_schedule_line | Silver | TXN | 5 | A |
| delivery_schedule | Silver | MASTER | 6 | A |
| edi_order_message | Silver | TXN | 6 | A |
| order_credit_check | Silver | TXN | 6 | A |
| return_order | Silver | TXN | 6 | A |
| otd_record | Silver | TXN | 6 | A |
| return_order_line | Silver | TXN | 7 | A |
| dim_date | Gold | DIM | G0 | A |
| dim_sales_area | Gold | DIM | G0 | A |
| dim_channel | Gold | DIM | G0 | A |
| dim_order_reason | Gold | DIM | G0 | A |
| dim_customer | Gold | DIM | G1 | A |
| dim_material | Gold | DIM | G1 | A |
| dim_sales_contract | Gold | DIM | G1 | A |
| bridge_order_partner | Gold | BRIDGE | G1 | A |
| fact_sales_order_line | Gold | FACT | G2 | A |
| fact_otd | Gold | FACT | G2 | A |
| fact_quotation_line | Gold | FACT | G2 | A |
| fact_return_line | Gold | FACT | G2 | A |
| fact_credit_check | Gold | FACT | G2 | A |

**Key paths:**

* Silver pipeline SQL: `src/silver/pipeline/`
* Gold pipeline SQL: `src/gold/pipeline/`
* Silver validation: `src/silver/validation/`
* Gold validation: `src/gold/validation/`
* Pipeline resource: `resources/meridian_sales_order_silver_sdp.pipeline.yml`
* Validation jobs: `resources/meridian_sales_order_*_validation.job.yml`
* Model Guide: `Sales Order Model Guide` (project root)
* Genie space: Sales Order Analytics (`01f193a8e28b18eb91b85edac9274d28`)

**Schemas:**

* Silver: `manufacturing_silver_vibe.sales_order_silver_sdp`
* Gold: `manufacturing_silver_vibe.sales_order_gold_sdp`
* Bronze sources: `manufacturing_bronze_vibe.{sap_sd, salesforce_crm, edi_gateway, returns_portal}`

## Maintenance Recipes

### Add a table to this model

Bronze sources already mapped: sap_sd, salesforce_crm, edi_gateway, returns_portal. To add a new entity, create a `.sql` file in `src/silver/pipeline/` (MV or ST) and optionally a gold counterpart in `src/gold/pipeline/`. Add the table to the pipeline glob path if needed, then re-deploy.

→ See [docs/developer/how-to/add-a-table.md](../../docs/developer/how-to/add-a-table.md) for the full procedure.

### Fix a degraded table

Silver validation job: deployed via `resources/meridian_sales_order_validation.job.yml`  
Gold validation job: job ID `74728959503728`  
Dashboard: check the validation narrative notebook for the affected entity in `src/{silver|gold}/validation/`.

→ See [docs/developer/how-to/fix-a-degraded-table.md](../../docs/developer/how-to/fix-a-degraded-table.md) for the full procedure.

### Re-sync after a point change

Point fixes (closed gap, FK fix, added column) route through `domain-sync`, never a manual full re-run. The sync skill reads `synced-against` stamps on each artifact and scopes regeneration to the changed entity.

→ See [docs/developer/how-to/re-sync-after-a-change.md](../../docs/developer/how-to/re-sync-after-a-change.md) for the full procedure.

## See Also

Full skill-suite documentation: `docs/developer/` (decision tree, cross-domain recipes, skill catalog).
