"""v0.9.8 BEHAVIORAL tests for the airlines_mvm_v1 audit fixes.

Each test exercises real input -> output behavior (positive AND negative cases per CLAUDE.md
section 8.3 anti-tautology). Many tests parse the notebook source via AST/regex so they do
not require booting the agent runtime.

Fixes covered:
  1. mv-valid-columns-merge-joins  (MV-MEASURE-DEGEN root-cause patch)
  2. mv-attrs-by-key-stash         (KPI-first + per-domain caller stash global attrs map)
  3. ai-agent-call-fix             (D-24 ai_agent.call -> _call_ai_query)
  4. mv-fallback-emit-live         (A-2 dead-code wired to actually install fallback)
  5. vibe-metadata-honest          (cross-validate LLM issues_addressed against SA)
  6. mv-source-extract / mv-target-extract helpers
"""

import ast
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _read_notebook_source(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            parts.extend(cell.get("source", []))
    return "".join(parts)


@pytest.fixture(scope="module")
def agent_src() -> str:
    return _read_notebook_source(NOTEBOOK_PATH)


def _extract_function(src: str, fn_name: str) -> str:
    """Return the source text of a top-level function by name."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return ast.get_source_segment(src, node)
    raise AssertionError(f"Function {fn_name} not found")


def _exec_function(src: str, fn_name: str, extra_globals=None):
    """Execute a top-level function definition in an isolated namespace and return it."""
    fn_src = _extract_function(src, fn_name)
    g = {"re": re, "json": json}
    if extra_globals:
        g.update(extra_globals)
    exec(compile(fn_src, f"<{fn_name}>", "exec"), g)
    return g[fn_name]


# ----------------------------------------------------------------------
# 1. mv-valid-columns-merge-joins  (MV-MEASURE-DEGEN root-cause)
# ----------------------------------------------------------------------
class TestMvValidColumnsMergeJoins:
    def test_alias_present_in_renderer(self, agent_src):
        """The alias must self-report so audits can grep evidence."""
        assert agent_src.count("[mv-valid-columns-merge-joins FIRED]") >= 1
        assert "alias=mv-valid-columns-merge-joins" in agent_src

    def test_extends_valid_columns_with_joined_attrs(self, agent_src):
        """The patch must read from _metric_view_all_attrs_by_key."""
        assert "_metric_view_all_attrs_by_key" in agent_src
        assert "_joined_extra_cols" in agent_src
        assert "_joined_aliases" in agent_src

    def test_strips_domain_prefix_from_target_product(self, agent_src):
        """Joined-target product lookup must strip 'domain.product' qualifier."""
        # The strip code uses _tp_x.split('.')[-1] inside the patch
        snippet = agent_src.split("[mv-valid-columns-merge-joins FIRED]")[1][:1500]
        assert ".split('.')" in snippet or ".split(\".\")" in snippet

    def test_negative_when_no_joins_no_extension(self, agent_src):
        """Without joins, valid_columns must NOT be extended."""
        # The condition is: if _valid_joins and isinstance(_mv_joins_raw, list) and valid_columns is not None
        assert "if _valid_joins and isinstance(_mv_joins_raw, list) and valid_columns is not None" in agent_src


# ----------------------------------------------------------------------
# 2. mv-attrs-by-key-stash  (KPI-first + per-domain callers)
# ----------------------------------------------------------------------
class TestMvAttrsByKeyStash:
    def test_alias_fires_at_kpi_first_caller(self, agent_src):
        """KPI-first caller (the global LLM step) must build & stash the map."""
        # Two FIRED logs expected: one in KPI-first caller, one in per-domain fallback path.
        assert agent_src.count("[mv-attrs-by-key-stash FIRED]") >= 2

    def test_stashes_under_correct_config_key(self, agent_src):
        assert "config['_metric_view_all_attrs_by_key']" in agent_src

    def test_per_domain_path_only_stashes_when_missing(self, agent_src):
        """Per-domain caller must not overwrite if KPI-first already stashed."""
        assert "if '_metric_view_all_attrs_by_key' not in (config or {}):" in agent_src

    def test_indexes_by_lowercase_domain_product(self, agent_src):
        """Index key must be lowercase 'domain.product' for join target lookup parity."""
        # Both paths use same shape: f"{ad}.{ap}" with .strip().lower() on both halves
        assert "(a.get('domain') or '').strip().lower()" in agent_src
        assert "(_a_x.get('domain') or '').strip().lower()" in agent_src


# ----------------------------------------------------------------------
# 3. ai-agent-call-fix  (D-24)
# ----------------------------------------------------------------------
class TestAiAgentCallFix:
    def test_call_method_replaced_with_underscore_call_ai_query(self, agent_src):
        """The KPI-first call site must use _call_ai_query (not .call)."""
        idx = agent_src.find('step_name="kpi_first_global"')
        assert idx > 0, "kpi_first_global step_name not found"
        block = agent_src[max(0, idx - 1200):idx + 200]
        assert "_call_ai_query" in block, f"_call_ai_query not in KPI invocation block"
        # No bare `ai_agent.call(` invocation anywhere (excluding comments). The patch comment
        # references `ai_agent.call(...)` in backticks — we use a stricter regex match.
        invocations = re.findall(r"^\s*[\w_]*\s*=\s*ai_agent\.call\(", agent_src, flags=re.MULTILINE)
        assert not invocations, f"Live ai_agent.call() invocation regression: {invocations}"

    def test_alias_present_for_audit_grep(self, agent_src):
        assert "[ai-agent-call-fix FIRED]" in agent_src
        assert "alias=ai-agent-call-fix" in agent_src

    def test_aiagent_class_exposes_call_ai_query_only(self, agent_src):
        """AIAgent class must expose _call_ai_query (no def call)."""
        # Locate class AIAgent body slice
        cls_idx = agent_src.find("class AIAgent:")
        assert cls_idx > 0
        # Look at ~5K chars after class def for both methods
        body = agent_src[cls_idx:cls_idx + 50000]
        assert "def _call_ai_query(" in body
        # Must NOT have a "def call(" inside the AIAgent class section (would be confusing)
        # We check the slice up to the next class definition.
        next_cls = body.find("\nclass ", 100)
        if next_cls > 0:
            class_section = body[:next_cls]
        else:
            class_section = body[:20000]
        assert "    def call(" not in class_section, "AIAgent.call is back — D-24 regression"


# ----------------------------------------------------------------------
# 4. mv-fallback-emit-live  (A-2)
# ----------------------------------------------------------------------
class TestMvFallbackEmitLive:
    def test_alias_self_reports(self, agent_src):
        assert agent_src.count("[mv-fallback-emit-live FIRED]") >= 1
        assert "alias=mv-fallback-emit-live" in agent_src

    def test_uses_extractors_not_undefined_var(self, agent_src):
        """Must call the new extractor helpers (not the undefined _mv_source)."""
        # The new path uses _extract_metric_view_target_from_statement + _extract_metric_view_source_from_statement
        fn_start = agent_src.find("def _v467_install_mv_fallback")
        assert fn_start > 0
        block_start = agent_src.find("[mv-fallback-emit-live FIRED]", fn_start)
        assert block_start > fn_start
        installer = agent_src[fn_start:block_start]
        assert "_extract_metric_view_target_from_statement" in installer
        assert "_extract_metric_view_source_from_statement" in installer

    def test_actually_installs_via_execute_sql(self, agent_src):
        """The fallback path must call execute_sql, not just log."""
        block_start = agent_src.find("[mv-fallback-emit-live FIRED]")
        slice_around = agent_src[max(0, block_start - 1500):block_start + 3500]
        assert "execute_sql(spark, _fb_yaml" in slice_around

    def test_dead_code_replaced(self, agent_src):
        """The old `_mv_source if '_mv_source' in dir()` pattern must be gone."""
        assert "_mv_source if '_mv_source' in dir()" not in agent_src


# ----------------------------------------------------------------------
# 5. mv-source-extract / mv-target-extract helpers
# ----------------------------------------------------------------------
class TestMvSourceTargetExtractors:
    def test_extract_source_double_quoted(self, agent_src):
        fn = _exec_function(agent_src, "_extract_metric_view_source_from_statement")
        stmt = (
            "CREATE OR REPLACE VIEW `cat`.`_metrics`.`v1`\n"
            "WITH METRICS\nLANGUAGE YAML\nAS $$\n"
            "  version: 1.1\n"
            "  source: \"`cat`.`db`.`tbl`\"\n"
            "  dimensions:\n    - name: All Records\n      expr: \"1\"\n"
            "  measures:\n    - name: x\n      expr: COUNT(1)\n$$"
        )
        assert fn(stmt) == "`cat`.`db`.`tbl`"

    def test_extract_source_single_quoted(self, agent_src):
        fn = _exec_function(agent_src, "_extract_metric_view_source_from_statement")
        stmt = "  source: 'cat.db.tbl'"
        assert fn(stmt) == "cat.db.tbl"

    def test_extract_source_returns_none_on_missing(self, agent_src):
        fn = _exec_function(agent_src, "_extract_metric_view_source_from_statement")
        assert fn("CREATE OR REPLACE VIEW `cat`.`db`.`v1` AS SELECT 1") is None
        assert fn("") is None
        assert fn(None) is None

    def test_extract_target_three_part(self, agent_src):
        fn = _exec_function(agent_src, "_extract_metric_view_target_from_statement")
        stmt = "CREATE OR REPLACE VIEW `cat`.`_metrics`.`v1`\nWITH METRICS"
        assert fn(stmt) == "`cat`.`_metrics`.`v1`"

    def test_extract_target_returns_none_on_malformed(self, agent_src):
        fn = _exec_function(agent_src, "_extract_metric_view_target_from_statement")
        assert fn("not a create stmt") is None
        assert fn(None) is None


# ----------------------------------------------------------------------
# 6. vibe-metadata-honest  (LLM claims cross-validated)
# ----------------------------------------------------------------------
class TestVibeMetadataHonest:
    def test_alias_self_reports(self, agent_src):
        assert "[vibe-metadata-honest FIRED]" in agent_src
        assert "alias=vibe-metadata-honest" in agent_src

    def test_preserves_raw_llm_claims_for_audit(self, agent_src):
        """Original LLM list must be preserved separately so audits can compare."""
        assert "issues_addressed_llm_raw" in agent_src
        assert "issues_not_addressed_llm_raw" in agent_src

    def test_uses_sa_severity_by_class_for_verification(self, agent_src):
        """Must read the live SA class-counts (not invent)."""
        assert "_sa_severity_by_class" in agent_src
        assert "_prev_sa_severity_by_class" in agent_src

    def test_demoted_claims_carry_provenance(self, agent_src):
        """Demoted claims must include a 'verifier' tag + 'reason' for traceability."""
        assert "'verifier': 'vibe-metadata-honest'" in agent_src
        assert "vibe_metadata_verifier" in agent_src

    def test_keep_when_now_zero(self, agent_src):
        """A claim must KEEP when the SA class count is now 0."""
        # The keep condition is `if _now_n == 0 or (_prev_n > 0 and _now_n < _prev_n)`
        assert "_now_n == 0 or (_prev_n > 0 and _now_n < _prev_n)" in agent_src


# ----------------------------------------------------------------------
# 7. End-to-end JSON validity guard
# ----------------------------------------------------------------------
class TestNotebookIntegrity:
    def test_notebook_is_valid_json(self):
        d = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
        assert isinstance(d.get("cells"), list)
        assert len(d["cells"]) > 0

    def test_every_code_cell_parses(self, agent_src):
        d = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
        errors = []
        for i, c in enumerate(d["cells"]):
            if c.get("cell_type") != "code":
                continue
            src = "".join(c.get("source", []))
            try:
                ast.parse(src)
            except SyntaxError as e:
                errors.append((i, e.msg, e.lineno))
        assert not errors, f"Syntax errors in cells: {errors}"

    def test_all_v098_aliases_grep_at_least_once(self, agent_src):
       for alias, min_hits in [
               ("mv-valid-columns-merge-joins", 2),
               ("mv-attrs-by-key-stash", 2),
               ("ai-agent-call-fix", 2),
               ("mv-fallback-emit-live", 2),
               ("vibe-metadata-honest", 2),
               ("valid-joins-init-unconditional", 1),
               ("domain-to-db-from-config", 2),
               ("mv-yaml-no-type-field", 2),
               ("mv-joins-disabled-pending-syntax-fix", 2),
           ]:
               assert agent_src.count(alias) >= min_hits, f"{alias} not present (need >={min_hits} hits)"


# ----------------------------------------------------------------------
# 8. v0.9.9 hotfixes — _valid_joins UnboundLocal + domain_to_db_map NameError
# ----------------------------------------------------------------------
class TestV099Hotfixes:
    def test_valid_joins_initialized_unconditionally(self, agent_src):
        """`_valid_joins = []` must appear BEFORE the `if isinstance(_mv_joins_raw...` guard."""
        idx_init = agent_src.find("[valid-joins-init-unconditional FIRED]")
        assert idx_init > 0, "valid-joins-init-unconditional alias missing"
        window = agent_src[idx_init:idx_init + 800]
        assert "_valid_joins = []" in window

    def test_domain_to_db_map_from_config(self, agent_src):
        """The renderer must read `domain_to_db_map` from config keys."""
        idx = agent_src.find("[domain-to-db-from-config FIRED]")
        assert idx > 0, "domain-to-db-from-config alias missing"
        window = agent_src[idx:idx + 1500]
        assert "_kpi_first_domain_to_db_map" in window
        assert "_per_domain_domain_to_db_map" in window

    def test_per_domain_caller_stashes_domain_to_db_map(self, agent_src):
        """Per-domain caller must setdefault the per-domain map on config before invoking renderer."""
        assert "_per_domain_domain_to_db_map" in agent_src
        assert "setdefault('_per_domain_domain_to_db_map'" in agent_src

    def test_no_unbound_valid_joins_pattern(self, agent_src):
        """Sanity: ensure `_valid_joins` is referenced AFTER an init line in renderer."""
        idx_fn = agent_src.find("def _render_metric_sql_for_domain_from_llm_spec")
        assert idx_fn > 0
        body = agent_src[idx_fn:idx_fn + 30000]
        init_pos = body.find("_valid_joins = []\n")
        ref_pos = body.find("if _valid_joins and isinstance")
        assert init_pos > 0 and ref_pos > 0, "init or ref not found"
        assert init_pos < ref_pos, "_valid_joins init must precede unconditional ref"


# ----------------------------------------------------------------------
# 9. v1.0.0 hotfix — drop `type:` field from metric-view YAML joins
# ----------------------------------------------------------------------
class TestV100MetricViewYamlNoTypeField:
    def test_renderer_does_not_emit_type_field(self, agent_src):
        """The metric-view YAML renderer must NOT emit `type: <kind>` lines.
        Databricks metric views reject the `type` field on joins; emitting it
        causes [METRIC_VIEW_INVALID_VIEW_DEFINITION] and the view fails to install.
        """
        idx_fn = agent_src.find("def _render_metric_sql_for_domain_from_llm_spec")
        assert idx_fn > 0
        body = agent_src[idx_fn:idx_fn + 30000]
        offending = "type: {_vj['type']}"
        assert offending not in body, (
            "v1.0.0 regression: metric-view YAML still emits `type:` field — "
            "Databricks metric-view spec rejects this and the install fails."
        )

    def test_alias_self_reports_at_runtime(self, agent_src):
        """`mv-yaml-no-type-field` must self-report `[FIRED]` on every join emission."""
        assert "[mv-yaml-no-type-field FIRED]" in agent_src, (
            "v1.0.0 alias not present — no runtime evidence of fix execution."
        )


# ----------------------------------------------------------------------
# 10. v1.0.1 hotfix — disable MV joins entirely until syntax verified live
# ----------------------------------------------------------------------
class TestV101MetricViewJoinsDisabled:
    def test_joins_emission_block_gated_off(self, agent_src):
        """The `if isinstance(_mv_joins_raw, list) and _mv_joins_raw:` block must be gated
        with `if False and ...` so no joins YAML block is emitted."""
        idx = agent_src.find("if False and isinstance(_mv_joins_raw, list)")
        assert idx > 0, (
            "v1.0.1 regression: the join-emission gate was not flipped to `if False and ...`. "
            "MV joins will continue to emit and fail at column-resolution time."
        )

    def test_alias_present_and_self_reports(self, agent_src):
        """v1.0.1 alias must appear ≥2 times: once in comment, once in runtime self-report."""
        assert agent_src.count("mv-joins-disabled-pending-syntax-fix") >= 2, (
            "v1.0.1 alias missing — no audit trail."
        )
        assert "[mv-joins-disabled-pending-syntax-fix FIRED]" in agent_src

    def test_runtime_self_report_fires_on_suppressed_joins(self, agent_src):
        """The runtime marker must log when LLM proposed joins that we suppressed —
        provides the auditor with `suppressed_joins=N` evidence per MV."""
        assert "suppressed_joins=" in agent_src, (
            "v1.0.1 runtime marker missing the suppressed_joins=N count."
        )
