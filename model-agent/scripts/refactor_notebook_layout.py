#!/usr/bin/env python3
"""Refactor dbx_vibe_modelling_agent.ipynb for readability."""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_NB = ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb.bak-layout"
DST_NB = ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"

AGENT_VERSION = "4.2.8"
RELEASE_VERSION = "0.8.0"
MIN_CHUNK = 500
MAX_CHUNK = 700

WIDGET_DOCS_MD = textwrap.dedent(
    """
    # Vibe Modelling Agent

    **Production notebook for [Vibe Data Modeling](https://www.databricks.com/blog/reimagining-data-modeling-lakehouse-introducing-vibe-data-modeling)** on Databricks.

    Describe your business in plain English (or point at a `vibes.txt` file), run the pipeline, and get a versioned, rule-validated Silver-layer data model deployed to Unity Catalog. Iterate with natural-language **vibes** until the model fits. No version is overwritten.

    This is the same agent that produced the **[40 Lakehouse Industry Data Models](https://www.databricks.com/blog/jumpstart-your-data-modeling-databricks-industry-data-models)** published by Databricks: pre-built MVM and ECM scopes for the world's biggest industries, each validated against 200+ structural rules before release. Use this notebook to build new models, customize an industry baseline, or evolve an existing version.

    | Read first | What you learn |
    |------------|----------------|
    | [Reimagining Data Modeling on the Lakehouse: Introducing Vibe Data Modeling](https://www.databricks.com/blog/reimagining-data-modeling-lakehouse-introducing-vibe-data-modeling) | What Vibe Data Modeling is, how a vibe becomes a model, iteration, and physical catalog layouts |
    | [Jumpstart your Data Modeling with Databricks Industry Data Models](https://www.databricks.com/blog/jumpstart-your-data-modeling-databricks-industry-data-models) | The 40 industry models this agent generated, tier sizing, governance, and the public repo |

    **Industry models repo:** [databricks-industry-data-models](https://github.com/databricks-industry-solutions/databricks-industry-data-models)

    ---

    ## How to run

    1. Execute cells **top to bottom** on **Databricks Serverless**.
    2. **Cell 1 (code)** prints the agent banner and sets `__AGENT_VERSION__`.
    3. Scroll to **Widget registration** (near the end), set widgets, then run **`main()`**.

    ---

    ## What this notebook does

    | Phase | Operation widget | Outcome |
    |-------|------------------|---------|
    | Build | `new base model` | Generate MVM or ECM from business name, description, and vibes |
    | Iterate | `vibe modeling of version` | Apply `next_vibes.txt` priorities to produce vN+1 |
    | Resize | `shrink ecm` / `enlarge mvm` | Move between ECM and MVM scope |
    | Deploy | `install model` | DDL, FKs, tags, metric views into Unity Catalog |
    | Remove | `uninstall model version` | Drop a installed version from catalog |
    | Demo | `generate sample data` | Synthetic rows for demos and QA |

    Every generation pass runs architect review, static analysis, FK/cycle guards, and optional agentic repair before writeback.

    ---

    ## Widget reference

    | # | Widget | Required? | When | Notes |
    |---|--------|-----------|------|-------|
    | 01 | `business_name` | **Yes** | Almost all ops | Short key, e.g. `airlines`, `healthcare`, `telecom` |
    | 02 | `business_description` | No | `new base model` | Industry narrative; complements vibes |
    | 03 | `operation` | **Yes** | Always | See table above |
    | 04 | `model_version` | Conditional | Non-base ops | Required for VOV, shrink, enlarge, install, uninstall, samples; blank for first base model only |
    | 05 | `data_model_scopes` | **Yes** | `new base model` | `Minimum Viable Model - MVM` or `Expanded Coverage Model - ECM` |
    | 06 | `business_domains` | No | Base model | Comma-separated; when set, names are **immutable** in output |
    | 07 | `org_divisions` | No | Base model | `Operations`, `Operations and Business`, or full three-division set |
    | 08 | `model_vibes` | No | Build / VOV | Inline text or `/path/to/vibes.txt`; **supreme authority** over heuristics |
    | 09 | `deployment_catalog` | Conditional | `install model` | **Required** for install; target Unity Catalog |
    | 09a | `cataloging_style` | No | Install | One catalog · per division · per domain |
    | 09b | `catalog_prefix` | No | Install | Prefix when multi-catalog |
    | 09c | `catalog_suffix` | No | Install | Suffix when multi-catalog |
    | 10 | `generate_samples` | No | Base / samples | `0` = off; `5`–`100` rows per table |
    | 11 | `context_file` | No | Bootstrap | External `model.json` path |
    | 12 | `naming_convention` | No | Base | Default `snake_case` |
    | 13 | `primary_key_suffix` | No | Base | Default `_id` |
    | 15–15a | `schema_prefix` / `schema_suffix` | No | Install | Physical schema naming |
    | 16–16a | `tag_prefix` / `tag_suffix` | No | Install | UC tag naming (default prefix `dbx_`) |
    | 17 | `table_id_type` | No | Base | `BIGINT` default |
    | 18–20 | boolean / date / timestamp format | No | Samples | Display formats for generated data |
    | 21 | `classification_levels` | No | Governance | `key=label` pairs for sensitivity tags |
    | 22–23 | housekeeping / history columns | No | Base | Audit and SCD-style columns |
    | 24 | `vibe_session_id` | No | Tracing | Correlate logs across runs |

    **Tips**
    - Leave `business_domains` empty to let the agent infer domains from industry context and vibes.
    - For `vibe modeling of version`, leave `model_vibes` blank to consume auto-generated `next_vibes.txt` from the prior version.
    - `runtime_budget_seconds` is a job base parameter (not a widget); the entrypoint reads it when present.
    """
).strip()

VOV_SYMBOL_BLURBS: dict[str, str] = {
    "VibeSection": "One parsed section of a vibe document with offsets and constraints.",
    "VibeChunk": "Token-bounded slice of a vibe document passed to the extractor.",
    "CannedResponse": "Fixed LLM response used by MockLLM in tests.",
    "UnsafeCodeError": "Raised when synthesized handler code fails AST allowlist checks.",
    "InvariantSnapshot": "Frozen structural hash of PKs, FKs, tags, and counts at a point in time.",
    "VibeOutline": "Structured outline across all vibe sections for extraction.",
    "RawVREQ": "Single extracted vibe requirement before dedupe and batching.",
    "Batch": "Group of VREQs executed together in one sandbox handler.",
    "Handler": "Synthesized Python function that mutates the model for a batch.",
    "PipelineResult": "Terminal VOV outcome: applied/skipped VREQs, model diff, logs.",
    "LLMClient": "Protocol for LLM calls used by extractor, synthesizer, and verifier.",
    "MockLLM": "Deterministic LLM stub for unit tests and offline runs.",
    "DatabricksLLM": "Production LLM client using Databricks model serving / ai_query.",
    "validate_ast": "Allowlist AST walk; rejects unsafe constructs before sandbox run.",
    "execute_in_sandbox": "Run handler in isolated subprocess with timeout and rlimits.",
    "capture_invariants": "Snapshot structural invariants (PK, FK, tags) before/after change.",
    "verify_invariants": "Score whether a VREQ actually changed the model as intended.",
    "chunk_vibe": "Split long vibe text into section-aligned chunks.",
    "build_outline": "Turn chunks into a navigable outline for the extractor.",
    "extract_all": "LLM pass that emits raw VREQs from outline + vibe text.",
    "dedupe_vreqs": "Merge overlapping VREQs so each user intent is applied once.",
    "batch_vreqs": "Pack VREQs into batches that can share one handler.",
    "synthesize_batch_handlers": "LLM codegen for batch handlers; output is AST-validated.",
    "plan_waves": "Order batches into parallel waves without scope collisions.",
    "run_vov_pipeline": "Main VOV loop from vibes file to updated model.json.",
    "run_vov_2_against_widgets": "Widget-driven entry shim into the VOV pipeline.",
    "AIAgentLLMBridge": "Adapts notebook AIAgent to the VOV LLMClient protocol.",
}

VOV_MODULE_DOCS = {
    "types.py": (
        "VOV 2.0 — Core types",
        "Shared dataclasses exchanged across every VOV stage. Keeps extraction, synthesis, and verification aligned on one schema.",
        ("VibeSection", "VibeOutline", "RawVREQ", "Batch", "Handler", "PipelineResult"),
    ),
    "llm.py": (
        "VOV 2.0 — LLM clients",
        "Abstraction over LLM providers so VOV stages can run in production (Databricks) or in tests (mock).",
        ("LLMClient", "MockLLM", "DatabricksLLM"),
    ),
    "sandbox.py": (
        "VOV 2.0 — Subprocess sandbox",
        "Security boundary for synthesized handlers: only approved AST nodes run, in a fresh subprocess.",
        ("validate_ast", "execute_in_sandbox", "UnsafeCodeError"),
    ),
    "invariants.py": (
        "VOV 2.0 — Model invariants",
        "Deterministic proof layer: compare model dict before/after each handler so the scoreboard cannot lie.",
        ("capture_invariants", "verify_invariants", "diff_models_summary"),
    ),
    "chunker.py": (
        "VOV 2.0 — Vibe chunker",
        "Prepares large `next_vibes.txt` / vibe files for token-bounded LLM extraction.",
        ("chunk_vibe", "find_section_offsets"),
    ),
    "outline.py": (
        "VOV 2.0 — Outline builder",
        "Builds a structured index of priorities and SA findings for the extractor prompt.",
        ("build_outline",),
    ),
    "extractor.py": (
        "VOV 2.0 — VREQ extractor",
        "Turns natural-language vibe instructions into typed, scoped VREQ records.",
        ("extract_all",),
    ),
    "deduper.py": (
        "VOV 2.0 — VREQ deduper",
        "Prevents duplicate LLM extractions from executing twice and fighting each other.",
        ("dedupe_vreqs",),
    ),
    "batcher.py": (
        "VOV 2.0 — VREQ batcher",
        "Groups compatible VREQs so one handler can satisfy multiple related intents.",
        ("batch_vreqs",),
    ),
    "synthesizer.py": (
        "VOV 2.0 — Handler synthesizer",
        "Writes Python mutation functions per batch; failures retry with validator feedback.",
        ("synthesize_batch_handlers",),
    ),
    "planner.py": (
        "VOV 2.0 — Wave planner",
        "Schedules batches in dependency-safe waves for parallel execution.",
        ("plan_waves",),
    ),
    "pipeline.py": (
        "VOV 2.0 — Pipeline orchestrator",
        "Wires every VOV stage, merges partial model updates, and returns adherence metrics.",
        ("run_vov_pipeline", "run_vov_2_against_widgets", "AIAgentLLMBridge"),
    ),
}

SECTION_DOCS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "Imports, Constants & JobLauncher": (
        "Foundation — constants, sizing, JobLauncher",
        "Bootstraps the agent runtime: tier sizing matrices, forbidden-domain policy, PII detectors, "
        "division taxonomy, and `JobLauncher` for firing follow-on Databricks jobs. User-pinned domains "
        "from widgets or vibes are cached here so later stages cannot drop them.",
        ("JobLauncher", "get_division_taxonomy", "classify_pii_subtype", "TECHNICAL_CONTEXT"),
    ),
    "Helpers, Schemas & PROMPT_TEMPLATES (1)": (
        "LLM schemas & prompts (1/2)",
        "Defines JSON response schemas for every LLM stage and registers the first half of prompt templates. "
        "Schemas run in strict mode where supported so hallucinated fields are rejected early.",
        ("PROMPT_TEMPLATES", "wrap_schema_with_honesty"),
    ),
    "PROMPT_TEMPLATES (2) & Auxiliary Helpers": (
        "LLM prompts (2/2) & helpers",
        "Completes the prompt registry (domain/product/attribute/metric prompts) plus small parsers "
        "that clean LLM JSON, normalize names, and bridge widget values into prompt variables.",
        ("PROMPT_TEMPLATES",),
    ),
    "Utility Functions & Validators": (
        "Utilities & validators",
        "Stateless helpers used everywhere: FK parsing, naming enforcement, retry/backoff, sample-data pools, "
        "and `run_metamodel_static_analysis` quality gates that feed autofix and next_vibes.",
        ("run_metamodel_static_analysis", "_pre_static_analysis_autofix"),
    ),
    "AIAgent, VibeWriter & Core Classes": (
        "Core classes — AIAgent & VibeWriter",
        "`AIAgent` routes prompts to configured foundation models with health tracking. "
        "`VibeWriter` persists domains/products/attributes to `_metamodel` tables and volumes. "
        "Catalog resolver picks physical catalog names from widget cataloging style.",
        ("AIAgent", "VibeWriter", "CatalogResolver"),
    ),
    "Pipeline Steps: Setup, Business Context & Domain Generation": (
        "Pipeline — setup & domains (steps 0–2)",
        "Clears prior run artifacts, classifies industry tier, generates business context, then runs "
        "ensemble + judge to pick domains. User widget domains are injected verbatim when provided.",
        ("step_setup", "step_business_context", "step_domain_generation"),
    ),
    "Pipeline Steps: Product Generation & Architect Reviews": (
        "Pipeline — products & architect review (step 3)",
        "Generates data products per domain in parallel, then runs domain-level and principal-architect "
        "self-review loops that add/remove products while protecting user must-haves.",
        ("step_product_generation", "step_domain_architect_review"),
    ),
    "Pipeline Steps: Attribute Generation": (
        "Pipeline — attributes (step 4)",
        "Adds columns to every product: types, descriptions, PKs, and candidate FKs. "
        "Validates attribute counts per tier and trims runaway width.",
        ("step_attribute_generation",),
    ),
    "Pipeline Steps: Normalization, Linking & SSOT": (
        "Pipeline — FK linking & SSOT (steps 4.x)",
        "Resolves `foreign_key_to` targets, breaks cycles, removes silos, and enforces single-source-of-truth "
        "so the same entity is not owned by two domains.",
        ("step_normalization", "step_linking"),
    ),
    "Pipeline Steps: Finalize, Naming, Subdomain, Metric Views": (
        "Pipeline — finalize & metrics (steps 5–7)",
        "Locks the logical model: uniform naming, subdomain/division tags, glossary tags, and "
        "declarative metric view definitions aligned to physical columns.",
        ("step_finalize", "step_metric_views"),
    ),
    "Pipeline Steps: Physical Schema, FK, Tags & Samples": (
        "Pipeline — physical install prep",
        "Builds Unity Catalog DDL, applies FK metadata, sets column/table tags, and optionally "
        "generates Faker-based sample rows for demos.",
        ("step_physical_schema", "step_tags"),
    ),
    "VIBE LINEAGE ARTIFACT (v0.9.3)": (
        "Vibe lineage artifact writer",
        "Writes lineage sidecar files so the model viewer can show how each version evolved from vibes.",
        (),
    ),
    "v207 SelfAuditor — automated audit invariants (5 user-locked rules)": (
        "SelfAuditor — automated invariants",
        "Five deterministic checks that must pass before a model is considered ship-ready; "
        "user-locked so the agent cannot relax them silently.",
        ("SelfAuditor",),
    ),
    "v208 SelfFixer — Opus 4.7 + sandbox closed-loop REQ fixer": (
        "SelfFixer — closed-loop repair",
        "When VREQs or SA findings remain, spins an agentic codegen loop (sandboxed) to patch the model dict "
        "before the next install attempt.",
        ("SelfFixer",),
    ),
    "Pipeline Orchestration & Track 1/2/3": (
        "Orchestration — tracks & progress",
        "`VibeOrchestrator` sequences ECM/MVM tracks, vibe-of-version, shrink/enlarge, and writes "
        "progress rows consumed by the monitoring UI.",
        ("VibeOrchestrator", "run_pipeline"),
    ),
    "Main Entry & Sanity Checks": (
        "Entrypoint — main()",
        "Reads widgets into `config`, validates combinations (operation vs version, catalog on install), "
        "runs pre-flight sanity checks, then dispatches the pipeline branch for the selected operation.",
        ("main",),
    ),
    "Run Entry": (
        "Notebook run guard",
        "Ensures `main()` runs once when Databricks executes the notebook as a job task.",
        ("__main__",),
    ),
}

IMPORTS_MD = """## Imports

Shared **PySpark**, **threading**, and stdlib imports for the entrypoint, physical install, and progress logging.

Loads `SparkSession`, SQL types/functions, and concurrency primitives used when writing Delta tables, running parallel DDL, and streaming logs to the volume."""

WIDGET_REG_MD = """## Widget registration

Creates **Databricks notebook widgets** for every user-facing parameter (business, operation, version, vibes, catalog, naming).

Set widget values in the UI **before** running `main()`. The entrypoint reads them via `dbutils.widgets.get` and builds the `config` dict consumed by the whole pipeline."""

VOV_OVERVIEW_MD = """## VOV 2.0 Sandbox Pipeline

**Vibe modeling of version** engine, inlined as a single notebook (no external `vov_2_0` package).

| Stage | Purpose |
|-------|---------|
| Chunk + outline | Break large vibe files into LLM-safe sections |
| Extract + dedupe | Turn prose into scoped VREQ records |
| Batch + plan | Group VREQs into parallel-safe waves |
| Synthesize + sandbox | Codegen handlers; run in AST-guarded subprocess |
| Verify + merge | Prove invariants; merge dict patches into `model.json` |

Sub-cells mirror `agent/vov_2_0/*.py` modules in execution order."""

VOV_BOOTSTRAP_MD = """### VOV bootstrap

Pins `__VOV_VERSION__`, imports inlined module aliases, and shared constants before any VOV class definitions.

Run this cell (and those below it in order) before invoking vibe modeling of version."""

CELL_HEADER_RE = re.compile(r"^#\s*===\s*(.+?)\s*===")
END_BLOCK_RE = re.compile(r"^#\s*===\s*END\s+.+===\s*$")
VOV_MODULE_RE = re.compile(r"^#\s*-----\s*inlined from agent/vov_2_0/(\w+\.py)\s*-----")
VERSION_COMMENT_RE = re.compile(
    r"^#\s*(v\d+\.\d+(\.\d+)?\b|alias=agent-version|legacy header preserved|VOV 2\.0 SANDBOX|END VOV)",
    re.I,
)
BANNER_VAR_RE = re.compile(r"^VIBE_MODELING_ASCII_ART\s*=")
WIDGET_RE = re.compile(r'^dbutils\.widgets\.(text|dropdown)\(')
IMPORT_RE = re.compile(r"^(import |from )")
TOP_LEVEL_SYM_RE = re.compile(r"^(?:@\w+\s+)*(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)")


def _md_cell(text: str) -> dict:
    src = text.strip() + "\n"
    return {"cell_type": "markdown", "metadata": {}, "source": [src]}


def _code_cell(lines: list[str]) -> dict:
    body = "\n".join(lines).rstrip() + "\n"
    return {"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": [body]}


def _parse_section_name(raw: str) -> str | None:
    name = raw.strip()
    if not re.search(r"[A-Za-z]", name):
        return None
    if re.fullmatch(r"=+", name):
        return None
    if re.match(r"^STEP\s+\d+", name, re.I):
        return None
    if not (name.upper().startswith("CELL ") or name.startswith("VOV 2.0")):
        return None
    if name.upper().startswith("CELL "):
        name = name.split(":", 1)[-1].strip()
    if name.startswith("VOV 2.0 SANDBOX"):
        return "VOV 2.0 Sandbox Pipeline"
    return name


def _should_drop_comment(line: str) -> bool:
    s = line.strip()
    if not s.startswith("#"):
        return False
    if CELL_HEADER_RE.match(s) or END_BLOCK_RE.match(s):
        return True
    if VERSION_COMMENT_RE.search(s):
        return True
    if "legacy header preserved" in s:
        return True
    if s.startswith("# This block is the inlined"):
        return True
    if s.startswith("# Public symbols exported"):
        return True
    if s.startswith("# Bug-fixes applied during inline"):
        return True
    if s.startswith("# Sandbox sentinels emitted"):
        return True
    if re.match(r"^#\s*===\s*VIBE LINEAGE", s):
        return True
    if VOV_MODULE_RE.match(s):
        return False
    if s.startswith("# ----- inlined from"):
        return False
    return False


def _clean_lines(lines: list[str]) -> list[str]:
    out = [ln for ln in lines if not _should_drop_comment(ln)]
    cleaned: list[str] = []
    blanks = 0
    for ln in out:
        if not ln.strip():
            blanks += 1
            if blanks <= 1:
                cleaned.append(ln)
        else:
            blanks = 0
            cleaned.append(ln)
    return cleaned


def _extract_banner_block(lines: list[str]) -> tuple[list[str], list[str]]:
    banner: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(lines):
        if BANNER_VAR_RE.match(lines[i].strip()):
            banner.append(lines[i])
            i += 1
            while i < len(lines):
                banner.append(lines[i])
                if lines[i].rstrip().endswith('"""') and len(banner) > 1:
                    i += 1
                    break
                i += 1
            continue
        if lines[i].strip() == "print(VIBE_MODELING_ASCII_ART)":
            i += 1
            continue
        rest.append(lines[i])
        i += 1
    return banner, rest


def _strip_version_banner(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("__AGENT_VERSION__") or s.startswith("__RELEASE_VERSION__"):
            continue
        if BANNER_VAR_RE.match(s) or s == "print(VIBE_MODELING_ASCII_ART)":
            continue
        out.append(ln)
    return out


def _extract_widgets(lines: list[str]) -> tuple[list[str], list[str]]:
    w, r = [], []
    for ln in lines:
        (w if WIDGET_RE.match(ln.strip()) else r).append(ln)
    return w, r


def _extract_import_block(lines: list[str]) -> tuple[list[str], list[str]]:
    start = None
    for i, ln in enumerate(lines):
        if IMPORT_RE.match(ln) and "pyspark.sql import SparkSession" in "".join(lines[i : i + 25]):
            start = i
            break
    if start is None:
        return [], lines
    end = start + 1
    while end < len(lines):
        ln = lines[end]
        if IMPORT_RE.match(ln) or not ln.strip() or ln.strip().endswith("(") or ln.strip().endswith("\\"):
            end += 1
            continue
        if ln.startswith(" ") and end > start:
            end += 1
            continue
        break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end], lines[:start] + lines[end:]


def _all_top_level_symbols(lines: list[str]) -> list[str]:
    return [m.group(2) for ln in lines if (m := TOP_LEVEL_SYM_RE.match(ln))]


def _clean_doc_line(text: str) -> str:
    s = text.strip().strip('"').strip("'")
    s = re.sub(r"^v\d+\.\d+(\.\d+)?\s*(P\d+\s*)?(alias=\S+\s*)?[-—:]?\s*", "", s, flags=re.I)
    s = re.sub(r"\s*alias=\S+.*$", "", s)
    s = re.sub(r"\[[A-Z0-9_-]+\]", "", s)
    s = re.sub(r"\(like\s+`[^`]+`[^)]*\)", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    if len(s) > 200:
        s = s[:197].rstrip() + "..."
    return s


def _docstring_first_line(lines: list[str], start: int) -> str:
    """Return first meaningful line of docstring starting at or after start index."""
    i = start
    while i < len(lines) and i < start + 3:
        ln = lines[i]
        stripped = ln.strip()
        if '"""' in ln or "'''" in ln:
            quote = '"""' if '"""' in ln else "'''"
            if ln.count(quote) >= 2:
                inner = ln.split(quote, 2)
                if len(inner) >= 2 and inner[1].strip():
                    return _clean_doc_line(inner[1])
            j = i + 1
            while j < len(lines) and j < i + 12:
                if quote in lines[j]:
                    block = "\n".join(lines[i + 1 : j]).strip()
                    if block:
                        first = next((x.strip() for x in block.splitlines() if x.strip()), "")
                        return _clean_doc_line(first)
                    break
                j += 1
            break
        i += 1
    return ""


def _humanize_symbol(name: str) -> str:
    if name in VOV_SYMBOL_BLURBS:
        return VOV_SYMBOL_BLURBS[name]
    if name == "PROMPT_TEMPLATES":
        return "Registry of LLM prompt templates keyed by pipeline stage."
    if name == "TECHNICAL_CONTEXT":
        return "Tier sizing tables and scope constants that drive domain/product counts."
    if name == "RuntimeBudget":
        return "Tracks elapsed wall-clock time vs job budget for graceful shutdown."
    if name.startswith("step_"):
        label = name[5:].replace("_", " ")
        return f"Pipeline step implementing {label}."
    if name.startswith("_"):
        label = re.sub(r"_+", " ", name).strip().lower()
        return f"Internal helper: {label}."
    label = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ")
    return f"Defines {label.lower()}."


def _extract_symbol_entries(lines: list[str], limit: int = 10) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for i, ln in enumerate(lines):
        m = TOP_LEVEL_SYM_RE.match(ln)
        if not m:
            continue
        name = m.group(2)
        kind = m.group(1)
        desc = _docstring_first_line(lines, i + 1)
        if not desc:
            desc = _humanize_symbol(name)
        elif kind == "class" and not desc.lower().startswith(("class", "dataclass", "defines")):
            desc = f"Class — {desc[0].lower() + desc[1:]}" if desc else _humanize_symbol(name)
        entries.append((name, desc))
        if len(entries) >= limit:
            break
    return entries


def _first_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    m = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    return m[0]


def _resolve_section_doc(title: str) -> tuple[str, str, tuple[str, ...]] | None:
    base = title.split(" — ")[0].split(" (body)")[0].strip()
    if base in SECTION_DOCS:
        return SECTION_DOCS[base]
    for key, doc in SECTION_DOCS.items():
        if base.startswith(key) or key.startswith(base):
            return doc
    for _mod, doc in VOV_MODULE_DOCS.items():
        short, body, symbols = doc
        if title == short or title.startswith(short):
            return doc
    return None


def _format_symbol_bullets(entries: list[tuple[str, str]]) -> list[str]:
    if not entries:
        return []
    lines = ["", "**What this cell defines:**"]
    for name, desc in entries:
        lines.append(f"- `{name}` — {desc}")
    return lines


def _rich_md(title: str, lines: list[str] | None = None) -> str:
    lines = lines or []
    entries = _extract_symbol_entries(lines, limit=12)
    doc = _resolve_section_doc(title)
    is_subchunk = "—" in title or "(body)" in title

    if doc:
        short, body, symbols = doc
        display = title if is_subchunk else short
        parts = [f"## {display}", "", _first_sentence(body) if is_subchunk else body]
        if entries:
            parts.extend(_format_symbol_bullets(entries))
        elif symbols:
            parts.append("")
            parts.append("**What this cell defines:**")
            for sym in symbols[:10]:
                parts.append(f"- `{sym}` — {_humanize_symbol(sym)}")
        if is_subchunk and not entries and not symbols and "(body)" in title:
            sym = title.split("`")[1] if "`" in title else ""
            if sym:
                parts.extend(["", f"Continues the implementation of `{sym}` (helpers, branches, and nested logic)."])
        return "\n".join(parts)

    parts = [f"## {title}"]
    if entries:
        parts.extend(_format_symbol_bullets(entries))
    else:
        parts.extend(["", "Supporting logic for the surrounding pipeline section."])
    return "\n".join(parts)


def _chunk_title(parent: str, lines: list[str], active_sym: str | None) -> tuple[str, str | None]:
    syms = _all_top_level_symbols(lines)
    new_active = syms[-1] if syms else active_sym
    if syms:
        if len(syms) == 1:
            return f"{parent} — `{syms[0]}`", new_active
        return f"{parent} — `{syms[0]}` … `{syms[-1]}`", new_active
    if active_sym:
        return f"{parent} — `{active_sym}` (body)", active_sym
    return parent, new_active


def _cell_compiles(lines: list[str]) -> bool:
    try:
        compile("\n".join(lines), "<cell>", "exec")
        return True
    except SyntaxError:
        return False


def _split_trailing_decorators(buf: list[str]) -> tuple[list[str], list[str]]:
    """If buf ends with @decorator lines, peel them for the next cell."""
    if not buf:
        return buf, []
    i = len(buf)
    while i > 0:
        s = buf[i - 1].strip()
        if not s:
            i -= 1
            continue
        if s.startswith("@"):
            i -= 1
            continue
        break
    if i < len(buf) and any(buf[j].strip().startswith("@") for j in range(i, len(buf))):
        return buf[:i], buf[i:]
    return buf, []


def _split_by_size(parent: str, lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split only at top-level def/class (or VOV module) boundaries.

    Databricks compiles each notebook cell independently, so we must never
    cut mid-block. MAX_CHUNK is a soft target: we flush at the next top-level
    symbol once the buffer reaches MIN_CHUNK, and may exceed MAX_CHUNK when a
    single function/class is large.
    """
    if len(lines) <= MAX_CHUNK:
        return [(parent, lines)]

    chunks: list[tuple[str, list[str]]] = []
    buf: list[str] = []
    pending_decorators: list[str] = []
    active_sym: str | None = None

    def flush():
        nonlocal buf, active_sym, pending_decorators
        if not buf:
            return
        title, active_sym = _chunk_title(parent, buf, active_sym)
        chunks.append((title, buf))
        buf = []

    for ln in lines:
        is_boundary = bool(TOP_LEVEL_SYM_RE.match(ln) or VOV_MODULE_RE.match(ln.strip()))
        if is_boundary and buf and len(buf) >= MIN_CHUNK:
            main, decorators = _split_trailing_decorators(buf)
            if decorators:
                buf = main
                pending_decorators.extend(decorators)
            if buf:
                flush()
        if is_boundary and TOP_LEVEL_SYM_RE.match(ln) and pending_decorators:
            buf.extend(pending_decorators)
            pending_decorators = []
        m = TOP_LEVEL_SYM_RE.match(ln)
        if m:
            active_sym = m.group(2)
        buf.append(ln)
    if pending_decorators:
        buf = pending_decorators + buf
        pending_decorators = []
    flush()
    return chunks or [(parent, lines)]


def _split_vov_section(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split VOV on inlined module markers, then by size."""
    modules: list[tuple[str, list[str]]] = []
    current_mod = "bootstrap"
    buf: list[str] = []

    for ln in lines:
        m = VOV_MODULE_RE.match(ln.strip())
        if m:
            if buf:
                modules.append((current_mod, buf))
            current_mod = m.group(1)
            buf = []
            continue
        buf.append(ln)
    if buf:
        modules.append((current_mod, buf))

    out: list[tuple[str, list[str]]] = []
    for mod, mod_lines in modules:
        if mod == "bootstrap":
            parent = "VOV 2.0 Sandbox Pipeline — bootstrap"
            out.extend(_split_by_size(parent, mod_lines))
            continue
        doc = VOV_MODULE_DOCS.get(mod)
        parent = doc[0] if doc else f"VOV 2.0 — {mod}"
        out.extend(_split_by_size(parent, mod_lines))
    return out


def _split_section(name: str, lines: list[str]) -> list[tuple[str, list[str]]]:
    if "VOV" in name and "Sandbox" in name:
        return _split_vov_section(lines)
    return _split_by_size(name, lines)


def _parse_sections(all_lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    cur_name = "Preamble"
    cur: list[str] = []

    for ln in all_lines:
        # Only treat CELL/VOV banner comments at column 0 as section boundaries.
        # Indented copies like `        # === STEP 1: ... ===` live inside main() and
        # must not split the notebook into orphan continuation cells.
        if ln and not ln[0].isspace():
            m = CELL_HEADER_RE.match(ln.strip())
            if m:
                parsed = _parse_section_name(m.group(1))
                if parsed:
                    if cur:
                        sections.append((cur_name, cur))
                    cur_name = parsed
                    cur = []
                    continue
            if END_BLOCK_RE.match(ln.strip()):
                if cur:
                    sections.append((cur_name, cur))
                cur, cur_name = [], "Preamble"
                continue
        cur.append(ln)
    if cur:
        sections.append((cur_name, cur))
    return sections


def refactor(nb: dict) -> dict:
    raw: list[str] = []
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            raw.extend("".join(cell.get("source", [])).splitlines())

    agent_ver, release_ver = AGENT_VERSION, RELEASE_VERSION

    banner, raw = _extract_banner_block(raw)
    raw = _strip_version_banner(raw)
    sections = [(n, _clean_lines(ls)) for n, ls in _parse_sections(raw)]

    widgets: list[str] = []
    imports: list[str] = []
    fixed_sections: list[tuple[str, list[str]]] = []
    for name, lines in sections:
        if "Main Entry" in name:
            w, lines = _extract_widgets(lines)
            widgets.extend(w)
            imp, lines = _extract_import_block(lines)
            imports.extend(imp)
        fixed_sections.append((name, lines))
    sections = fixed_sections

    cells: list[dict] = [_md_cell(WIDGET_DOCS_MD)]
    cells.append(
        _code_cell(
            [
                f'__AGENT_VERSION__ = "{agent_ver}"  # alias=agent-version-global',
                f'__RELEASE_VERSION__ = "{release_ver}"  # alias=release-version-public',
                "",
                *banner,
                "",
                "print(VIBE_MODELING_ASCII_ART)",
                "",
            ]
        )
    )

    if imports:
        cells.append(_md_cell(IMPORTS_MD))
        cells.append(_code_cell(_clean_lines(imports)))

    widgets_added = False
    for name, lines in sections:
        if name == "Preamble" or not any(ln.strip() for ln in lines):
            continue

        if widgets and not widgets_added and "Main Entry" in name:
            cells.append(_md_cell(WIDGET_REG_MD))
            cells.append(_code_cell(_clean_lines(widgets)))
            widgets_added = True

        if name == "VOV 2.0 Sandbox Pipeline":
            cells.append(_md_cell(VOV_OVERVIEW_MD))

        for sub_title, chunk in _split_section(name, lines):
            if name == "VOV 2.0 Sandbox Pipeline" and sub_title.startswith("VOV 2.0 Sandbox Pipeline — bootstrap"):
                cells.append(_md_cell(VOV_BOOTSTRAP_MD))
            else:
                cells.append(_md_cell(_rich_md(sub_title, chunk)))
            cells.append(_code_cell(chunk))

    if widgets and not widgets_added:
        cells.append(_md_cell(WIDGET_REG_MD))
        cells.append(_code_cell(_clean_lines(widgets)))

    return {
        "nbformat": nb.get("nbformat", 4),
        "nbformat_minor": nb.get("nbformat_minor", 5),
        "metadata": nb.get("metadata", {}),
        "cells": cells,
    }


def main() -> None:
    nb = json.loads(SRC_NB.read_text())
    out = refactor(nb)
    DST_NB.write_text(json.dumps(out, ensure_ascii=True, indent=1))
    code = [c for c in out["cells"] if c["cell_type"] == "code"]
    md = [c for c in out["cells"] if c["cell_type"] == "markdown"]
    sizes = [len("".join(c["source"]).splitlines()) for c in code]
    bad = [s for s in sizes if s > MAX_CHUNK]
    parts = sum(1 for c in md if "(continued)" in "".join(c["source"]) or "(part " in "".join(c["source"]))
    vov_md = sum(1 for c in md if "INLINED" in "".join(c["source"]))
    print(f"cells: {len(out['cells'])} ({len(md)} md, {len(code)} code)")
    print(f"code lines: min={min(sizes)} max={max(sizes)} avg={sum(sizes)//len(sizes)}")
    print(f"cells > {MAX_CHUNK} lines: {len(bad)}")
    print(f"part/continued titles: {parts}")
    print(f"VOV INLINED md cells: {vov_md}")
    broken = []
    for i, c in enumerate(code):
        src = "".join(c.get("source", []))
        try:
            compile(src, f"<code_cell_{i}>", "exec")
        except SyntaxError as e:
            broken.append((i, len(src.splitlines()), str(e)))
    if broken:
        print(f"SYNTAX BROKEN cells: {len(broken)}")
        for i, n, err in broken[:10]:
            print(f"  cell {i} lines={n}: {err}")
        raise SystemExit(1)
    print("all code cells compile OK")


if __name__ == "__main__":
    main()
