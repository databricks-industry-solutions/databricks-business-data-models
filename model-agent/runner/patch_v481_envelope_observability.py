"""v4.8.1 FIX 1b alias=v481-response-format-envelope (observability).

The v4.8.1 live run 186683145042109 proved the envelope fix by its effect: the
verifier LLM fallback returned 11 real verdicts with 0 'responseFormat is invalid'
errors, where v4.8.0 raised that SparkException 4 times from the same function with
the same raw schema. But the FIRED marker itself never reached any persisted sink,
because AIAgent's own logger is driver-stdout only: not one AIAgent-origin marker
(v207-model-params, model-batch-route, FALLBACK, v446-aiquery-none-guard) appears in
either run's volume logs.

CLAUDE.md 8.10 requires an auditor to be able to grep the alias on the live run, so
count the wraps on the class and emit one line from the MODEL RUNTIME PROFILES block,
which demonstrably does reach the volume info log.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD_COUNTER = """    return {"name": _name, "schema": response_schema}
"""

NEW_COUNTER = """    try:
        _v481_envelope_wraps.append(str(_name))
    except Exception:
        pass
    return {"name": _name, "schema": response_schema}
"""

OLD_DECL = "def _v481_response_format_envelope(response_schema, prompt_name=None, step_name=None):"
NEW_DECL = """_v481_envelope_wraps = []


def _v481_response_format_envelope(response_schema, prompt_name=None, step_name=None):"""

# AIAgent's logger never reaches the volume sink, so the per-call info line is dead
# observability; the summary line below replaces it.
OLD_LOG = """                    _v481_rf = _v481_response_format_envelope(response_schema, prompt_name, step_name)
                    if _v481_rf is not response_schema:
                        try:
                            self.logger.info(f"  [v481-response-format-envelope FIRED v4.8.1] prompt={prompt_name!r} raw JSON Schema wrapped in {{name, schema}} envelope for ai_query responseFormat alias=v481-response-format-envelope")
                        except Exception:
                            pass
"""
NEW_LOG = """                    _v481_rf = _v481_response_format_envelope(response_schema, prompt_name, step_name)
"""

OLD_SUMMARY = """        if AIAgent._demoted_models:
            lines.append("")
            lines.append("--- Model Demotions ---")"""

NEW_SUMMARY = """        if _v481_envelope_wraps:
            _v481_uniq = sorted(set(_v481_envelope_wraps))
            lines.append("")
            lines.append(
                f"  [v481-response-format-envelope FIRED v4.8.1] wrapped {len(_v481_envelope_wraps)} raw JSON Schema(s) "
                f"in the {{name, schema}} envelope ai_query requires, across {len(_v481_uniq)} prompt(s): "
                f"{', '.join(_v481_uniq[:8])} — without this the endpoint rejects the call with "
                f"'The responseFormat is invalid or unsupported by the model'. alias=v481-response-format-envelope"
            )

        if AIAgent._demoted_models:
            lines.append("")
            lines.append("--- Model Demotions ---")"""


def main():
    nb = json.load(open(NB))
    cell = nb["cells"][86]
    src = cell.get("source", [])
    text = "".join(src) if isinstance(src, list) else src

    if "_v481_envelope_wraps" in text:
        print("already applied")
        return 0

    for old, new, label in (
        (OLD_DECL, NEW_DECL, "module counter"),
        (OLD_COUNTER, NEW_COUNTER, "counter append"),
        (OLD_LOG, NEW_LOG, "drop unreachable per-call log"),
        (OLD_SUMMARY, NEW_SUMMARY, "runtime-profile summary line"),
    ):
        assert text.count(old) == 1, f"{label}: anchor count = {text.count(old)}"
        text = text.replace(old, new, 1)
        print("applied:", label)

    cell["source"] = text
    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
