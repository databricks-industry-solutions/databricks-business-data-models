# examples/ — the Meridian sample dataset

Everything here is **synthetic sample data** for trying the skill suite without any customer
access. It's built around **Meridian Fluid Controls** — a *fictional* manufacturer of industrial
valves, actuators, and flow instrumentation — so you can run the full assess → build → validate →
document loop end to end against realistic-but-invented data.

Nothing in this folder touches real systems, and the catalog names are **placeholders you swap for
your own**: `meridian_model` (where the vibe model is read), `meridian_bronze` (the source data),
and `meridian_silver` (where builds land).

## What's here

```
examples/
├── setup/                     # stand up the shared synthetic bronze ONCE
│   ├── data_generator/        #   seeded Python package → generates the CSVs (SEED=42, deterministic)
│   └── ingest/                #   CTAS-from-read_files SQL → loads the CSVs into meridian_bronze
│
├── field_service/             # ▶ START HERE — the fast 5-entity domain the tutorial runs on
│   ├── model_setup.sql        #   stands up the vibe model (self-contained DDL)
│   ├── conventions.*.yml      #   all six etl_type × output_model flow variants
│   └── EXAMPLE_OUTPUT.md       #   illustrative picture of a finished run
│
├── sales_order/               # the full 27-table counterpart — realistic scale (reference)
│
└── planted-divergences.md     # the "answer key": the intentional gaps a correct assessment
                               #   should find in the bronze (grading reference)
```

**Two tiers:** `setup/` is shared plumbing you run once to create the bronze; the domain folders
(`field_service/`, `sales_order/`) are the actual worked examples that read that bronze.

## Getting started

1. **Stand up the bronze once** — generate the CSVs and ingest them: see
   [`setup/data_generator/README.md`](setup/data_generator/README.md) and
   [`setup/ingest/ingest_bronze.sql`](setup/ingest/ingest_bronze.sql).
2. **Run the loop on `field_service`** — the fast path. Follow the
   [tutorial](../docs/developer/tutorial.md), which walks it end to end, or its
   [README](field_service/README.md) for the six flow variants.
3. **See it at scale** — [`sales_order/`](sales_order/README.md) is the full 27-table domain (a
   reference example; see its README for what it needs).

## The two domains

| Domain | Size | Runnable from this repo? | Role |
|---|---|---|---|
| **`field_service`** | 5 entities | **Yes** — ships `model_setup.sql` + uses the generated bronze | The fast tutorial loop; one planted gap (a missing technician master) |
| **`sales_order`** | 27 tables | **Reference** — needs a deployed `meridian_sales_model` (no `model_setup.sql` here) | Realistic scale: a gold layer, cross-domain divergences, SQL-reserved-word edge cases |

> The `field_service` domain is fully self-contained — its `model_setup.sql` stands up the vibe
> model, and the shared `setup/` generates the bronze — so a public reader can reproduce the whole
> tutorial with only their own empty workspace. `sales_order` is an illustrative reference at real
> scale; see its README for what it requires.
