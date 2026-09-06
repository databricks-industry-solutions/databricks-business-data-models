"""v0.9.0 hotfix bundle tests.

After v0.8.9 was deployed, the live tester surfaced four MORE root causes
that v0.8.9 had not fully closed:

  - schema-strict-preserve     — wrap_schema_with_honesty was forcing
                                  strict=False, defeating R7-SCHEMA's
                                  required[] enforcement
  - pool-spec-decimal-coerce-pre-spark — _build_df_from_pool_spec called
                                  spark.createDataFrame on rows containing
                                  Decimal values, raising "Could not convert
                                  Decimal(...) tried to convert to double"
                                  before the existing v0.8.2 P3 coerce ran
  - jobtags-deleted-job-info-not-warn — tag-update on deleted tester jobs
                                  was logging WARNING despite being expected
  - ddl-skip-duplicate-column-names — when redundant-prefix autofix
                                  collapsed two attribute column_names to
                                  the same value, Spark CREATE TABLE
                                  failed with [COLUMN_ALREADY_EXISTS]

These are static (read-only) sentinel checks against the notebook source.
Live verification runs in the tester next iteration.
"""

import json
import re
from pathlib import Path

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


# ---------------------------------------------------------------------------
# R7-STRICT-PRESERVE — wrap_schema_with_honesty preserves strict
# ---------------------------------------------------------------------------
class TestR7StrictPreserve:
    def test_alias_present(self, agent_src):
        assert "schema-strict-preserve" in agent_src

    def test_strict_false_override_removed(self, agent_src):
        # The two old `wrapped["strict"] = False` / `wrapped["schema"]["strict"] = False`
        # lines must be GONE so that strict=True flows through.
        assert 'wrapped["strict"] = False' not in agent_src
        assert 'wrapped["schema"]["strict"] = False' not in agent_src

    def test_honesty_score_still_required(self, agent_src):
        # The honesty fields must still be added to the required[] array so
        # they remain mandatory under strict mode.
        assert (
            'wrapped["schema"]["required"] = list(wrapped["schema"]["required"]) '
            '+ ["honesty_score", "honesty_justification"]' in agent_src
        )


# ---------------------------------------------------------------------------
# P0.83-DECIMAL-FIX — pre-spark coerce in _build_df_from_pool_spec
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# JOBTAGS-DOWNGRADE — job-deleted is INFO not WARNING
# ---------------------------------------------------------------------------
class TestJobTagsDeletedDowngrade:
    def test_alias_present(self, agent_src):
        assert "jobtags-deleted-job-info-not-warn" in agent_src

    def test_branch_on_job_deleted_substring(self, agent_src):
        assert '"job-deleted" in _tag_err.lower()' in agent_src
        assert '"does not exist" in _tag_err.lower()' in agent_src

    def test_info_level_used_for_deleted_path(self, agent_src):
        # Ensure the deleted-job path uses logger.info, not logger.warning.
        # We verify by locating the alias and confirming logger.info appears
        # in its emission line.
        idx = agent_src.find("jobtags-deleted-job-info-not-warn")
        assert idx > 0
        # Look forward for the emission line.
        snippet = agent_src[idx:idx + 4000]
        assert 'logger.info(f"[JobTags] Tag update skipped' in snippet


# ---------------------------------------------------------------------------
# NEW-6 — DDL skip duplicate column names
# ---------------------------------------------------------------------------
class TestDdlSkipDuplicateColumnNames:
    def test_alias_present(self, agent_src):
        assert "ddl-skip-duplicate-column-names" in agent_src

    def test_check_uses_generated_columns_set(self, agent_src):
        assert "if col_name in generated_columns:" in agent_src

    def test_warning_emitted(self, agent_src):
        assert "Duplicate column name" in agent_src

    def test_continue_after_warning(self, agent_src):
        # The continue must follow the warning, otherwise duplicate cols still
        # emit into cols_defs.
        idx = agent_src.find("ddl-skip-duplicate-column-names")
        assert idx > 0
        snippet = agent_src[idx:idx + 1500]
        assert 'logger.warning(f"[DDL] Duplicate column name' in snippet
        assert "continue" in snippet[snippet.find("Duplicate"):]
