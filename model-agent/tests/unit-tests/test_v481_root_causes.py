import json
import re

import pytest

from notebook_source_util import NOTEBOOK_PATH, agent_version_line


def _cells():
    return json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))["cells"]


def _text(cell):
    src = cell.get("source", [])
    return "".join(src) if isinstance(src, list) else src


def _cell_with(needle):
    for cell in _cells():
        if cell.get("cell_type") != "code":
            continue
        text = _text(cell)
        if needle in text:
            return text
    raise AssertionError(f"no code cell contains {needle!r}")


def _envelope_ns():
    text = _cell_with("def _v481_response_format_envelope")
    start = text.index("_v481_envelope_wraps = []")
    end = text.index("def _v446_coerce_ai_response")
    namespace = {}
    exec(compile(text[start:end], "<envelope>", "exec"), namespace)
    return namespace


def _envelope_fn():
    return _envelope_ns()["_v481_response_format_envelope"]


class TestResponseFormatEnvelope:
    """The live coffee_roastery run rejected two verifier calls with
    'The responseFormat is invalid or unsupported by the model' because the
    inline verifier schemas carry no json_schema name."""

    def test_a_raw_json_schema_is_given_the_name_databricks_requires(self):
        envelope = _envelope_fn()
        raw = {
            "type": "object",
            "required": ["status", "evidence"],
            "properties": {
                "status": {"type": "string", "enum": ["fulfilled", "partial", "failed"]},
                "evidence": {"type": "string"},
            },
        }
        out = envelope(raw, "VERIFIER_LLM_FALLBACK", "verifier_llm_fallback_VREQ-001")
        assert out is not raw
        assert out["name"] == "VERIFIER_LLM_FALLBACK"
        assert out["schema"] is raw

    def test_an_already_enveloped_schema_is_returned_untouched(self):
        envelope = _envelope_fn()
        wrapped = {"name": "estimates", "schema": {"type": "object", "properties": {}}}
        assert envelope(wrapped, "QA_ESTIMATE_ROWS_PROMPT", "step") is wrapped

    def test_a_schema_that_declares_strict_keeps_it(self):
        envelope = _envelope_fn()
        wrapped = {"name": "fix", "schema": {"type": "object"}, "strict": True}
        assert envelope(wrapped, "p", "s")["strict"] is True

    def test_a_name_is_sanitised_to_what_the_api_accepts(self):
        envelope = _envelope_fn()
        out = envelope({"type": "object"}, "verifier fallback/VREQ 001!", None)
        assert re.fullmatch(r"[A-Za-z0-9_-]+", out["name"])
        assert len(out["name"]) <= 60

    def test_a_nameless_schema_falls_back_to_the_step_name(self):
        envelope = _envelope_fn()
        out = envelope({"type": "object"}, None, "verifier_llm_fallback_VREQ-001")
        assert out["name"] == "verifier_llm_fallback_VREQ-001"

    def test_a_non_dict_schema_is_passed_through(self):
        envelope = _envelope_fn()
        assert envelope(None, "p", "s") is None

    def test_the_spark_ai_query_path_routes_through_the_envelope(self):
        text = _cell_with("responseFormat => ")
        call = text[text.index("if response_schema is not None:"):]
        call = call[: call.index("ai_query_sql = f\"SELECT ai_query('{model}', '{replace_single_quote(prompt)}', responseFormat")]
        assert "_v481_response_format_envelope(response_schema, prompt_name, step_name)" in call
        assert '"json_schema": response_schema' not in text

    def test_a_wrap_is_recorded_so_the_run_can_be_audited(self):
        """AIAgent's own logger never reaches the volume sink, so the alias is only
        greppable on a live run if the wrap is counted and reported in the runtime
        profile block, which does reach the info log."""
        ns = _envelope_ns()
        envelope = ns["_v481_response_format_envelope"]
        envelope({"type": "object"}, "VERIFIER_LLM_FALLBACK", None)
        envelope({"type": "object"}, "VERIFIER_EXTRACT", None)
        assert ns["_v481_envelope_wraps"] == ["VERIFIER_LLM_FALLBACK", "VERIFIER_EXTRACT"]

    def test_a_schema_that_needs_no_wrap_is_not_counted(self):
        ns = _envelope_ns()
        envelope = ns["_v481_response_format_envelope"]
        envelope({"name": "already", "schema": {"type": "object"}}, "SOME_PROMPT", None)
        envelope("not a dict", "SOME_PROMPT", None)
        assert ns["_v481_envelope_wraps"] == []

    def test_the_runtime_profile_reports_the_wraps(self):
        text = _cell_with("MODEL RUNTIME PROFILES")
        block = text[text.index("MODEL RUNTIME PROFILES") : text.index("--- Model Demotions ---")]
        assert "if _v481_envelope_wraps:" in block
        assert "alias=v481-response-format-envelope" in block

    def test_the_dead_per_call_log_is_gone(self):
        """It logged through AIAgent.logger, which no live run persists."""
        text = _cell_with("def _v481_response_format_envelope")
        assert "self.logger.info(f\"  [v481-response-format-envelope FIRED" not in text

    def test_the_two_verifier_schemas_are_still_authored_raw(self):
        """If these ever gain their own envelope the fix above stops being load-bearing."""
        text = _cell_with("_v103_extract_schema = {")
        for name in ("_v100_schema = {", "_v103_extract_schema = {"):
            body = text[text.index(name) : text.index(name) + 400]
            assert '"name"' not in body.split("properties")[0]


class TestSampleFolderResidue:
    """v4.8.0 moved sample generation to the model installer; the agent must stop
    minting a samples/ folder and must not carry stale sample files forward."""

    @pytest.mark.parametrize(
        "needle",
        [
            "for _subfolder in [",
            "_deploy_subfolders = [",
        ],
    )
    def test_no_samples_folder_is_created(self, needle):
        text = _cell_with(needle)
        line = next(l for l in text.split("\n") if needle in l)
        assert '"samples"' not in line, line

    def test_the_carry_over_map_does_not_resurrect_old_samples(self):
        text = _cell_with("subfolder_map = {")
        block = text[text.index("subfolder_map = {") :]
        block = block[: block.index("}") + 1]
        assert "samples" not in block, block


class TestExportMirrorResync:
    """The live run exported 1227 attrs / 78 FKs from memory while the on-disk mirror
    the next step's merge and recovery readers consume still held 1226 / 77."""

    def _resync(self, tmp_path, products_path, attributes_path, products, attributes, logger):
        text = _cell_with("v481-export-mirror-resync")
        start = text.index("    # The export lists above are authoritative")
        end = text.index("    products = products_for_export", start)
        body = "\n".join(line[4:] if line.startswith("    ") else line
                         for line in text[start:end].split("\n"))
        ns = {
            "json": json,
            "os": __import__("os"),
            "config": {"PRODUCTS_FILE_PATH": products_path, "ATTRIBUTES_FILE_PATH": attributes_path},
            "products_for_export": products,
            "attributes_for_export": attributes,
            "logger": logger,
        }
        exec(compile(body, "<resync>", "exec"), ns)
        return ns

    @staticmethod
    def _logger():
        class L:
            def __init__(self):
                self.info_lines = []
                self.warn_lines = []

            def info(self, msg):
                self.info_lines.append(str(msg))

            def warning(self, msg):
                self.warn_lines.append(str(msg))

        return L()

    def test_a_mirror_one_attribute_behind_is_rewritten_from_the_export(self, tmp_path):
        attrs = [{"domain": "d", "product": "p", "attribute": f"a{i}"} for i in range(3)]
        attrs[0]["foreign_key_to"] = "d.q.id"
        apath = tmp_path / "attributes.json"
        apath.write_text(json.dumps(attrs[:2]))
        ppath = tmp_path / "products.json"
        ppath.write_text(json.dumps([{"domain": "d", "product": "p"}]))
        log = self._logger()
        self._resync(tmp_path, str(ppath), str(apath), [{"domain": "d", "product": "p"}], attrs, log)
        assert json.loads(apath.read_text()) == attrs
        assert any("v481-export-mirror-resync FIRED" in m for m in log.info_lines)

    def test_a_mirror_that_lost_only_a_foreign_key_is_still_rewritten(self, tmp_path):
        attrs = [{"domain": "d", "product": "p", "attribute": "a", "foreign_key_to": "d.q.id"}]
        stale = [{"domain": "d", "product": "p", "attribute": "a"}]
        apath = tmp_path / "attributes.json"
        apath.write_text(json.dumps(stale))
        log = self._logger()
        self._resync(tmp_path, None, str(apath), [], attrs, log)
        assert json.loads(apath.read_text())[0]["foreign_key_to"] == "d.q.id"

    def test_a_mirror_already_in_sync_is_left_alone(self, tmp_path):
        attrs = [{"domain": "d", "product": "p", "attribute": "a"}]
        apath = tmp_path / "attributes.json"
        apath.write_text(json.dumps(attrs))
        before = apath.stat().st_mtime_ns
        log = self._logger()
        self._resync(tmp_path, None, str(apath), [], attrs, log)
        assert apath.stat().st_mtime_ns == before
        assert not log.info_lines

    def test_a_missing_mirror_file_is_not_created(self, tmp_path):
        apath = tmp_path / "attributes.json"
        log = self._logger()
        self._resync(tmp_path, None, str(apath), [], [{"a": 1}], log)
        assert not apath.exists()

    def test_an_unreadable_mirror_is_repaired_rather_than_raising(self, tmp_path):
        apath = tmp_path / "attributes.json"
        apath.write_text("{ this is not json")
        attrs = [{"domain": "d", "product": "p", "attribute": "a"}]
        log = self._logger()
        self._resync(tmp_path, None, str(apath), [], attrs, log)
        assert json.loads(apath.read_text()) == attrs
        assert not log.warn_lines

    def test_the_resync_runs_after_the_phantom_product_exclusion(self, tmp_path):
        """Rewriting before the exclusion filters would persist rows the export drops."""
        text = _cell_with("v481-export-mirror-resync")
        assert text.index("PHANTOM PRODUCTS IN EXPORT") < text.index("v481-export-mirror-resync")
        assert text.index("v481-export-mirror-resync") < text.index("    products = products_for_export")


def test_the_agent_version_is_at_least_the_one_that_shipped_these_fixes():
    # pinned to a floor, not a literal: a later bump must not fail a test about v4.8.1's
    # fixes, but a rollback below 4.8.1 must.
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', agent_version_line())
    assert m, agent_version_line()
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 1), agent_version_line()
