"""Apply the v4.8.1 root-cause fixes to agent/dbx_vibe_modelling_agent.ipynb.

FIX 1 alias=v481-response-format-envelope
  Live coffee_roastery run 984308838662601 emitted, twice:
    [verifier-llm-fallback-call-fix ERROR] _call_ai_query raised SparkException:
    The responseFormat is invalid or unsupported by the model.
  _call_ai_query_impl's Spark ai_query path assumed every response_schema is already
  in the OpenAI {name, schema} envelope. 57/57 registered schema constants are; the two
  verifier-fallback schemas are authored inline as RAW JSON Schemas, so the emitted
  responseFormat carried no 'name' and Databricks rejected it. VREQ-001 then went
  unverified and the fidelity gate reported precision 0.5 < 0.85.
  The wrap is applied ONLY when the envelope is absent, so the 57 working schemas
  (three of which carry their own 'strict') emit byte-identical SQL.

FIX 2 alias=v481-no-samples-folder
  v4.8.0 moved sample generation to the model installer but left 'samples' in three
  folder lists, so every run still minted an empty samples/ directory and the
  carry-over map would resurrect a pre-4.8.0 model's stale sample files into a
  4.8.0+ model folder.

FIX 3 __AGENT_VERSION__ 4.8.0 -> 4.8.1.
"""
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

HELPER = '''
def _v481_response_format_envelope(response_schema, prompt_name=None, step_name=None):
    """Return response_schema in the OpenAI json_schema envelope ai_query requires.

    Databricks rejects a responseFormat whose json_schema has no 'name' with
    "The responseFormat is invalid or unsupported by the model". Schemas already
    authored as {"name": ..., "schema": {...}} are returned UNCHANGED so callers
    that also set "strict" keep it.
    """
    if not isinstance(response_schema, dict):
        return response_schema
    if isinstance(response_schema.get("schema"), dict) and str(response_schema.get("name") or "").strip():
        return response_schema
    import re as _v481_re
    _name = str(prompt_name or step_name or "response_schema")
    try:
        _name = _v481_re.sub(r"[^A-Za-z0-9_-]", "_", _name)[:60] or "response_schema"
    except Exception:
        _name = "response_schema"
    return {"name": _name, "schema": response_schema}

'''

OLD_SPARK = """                if response_schema is not None:
                    response_format_str = json.dumps({"type": "json_schema", "json_schema": response_schema}, separators=(',', ':')).replace("'", "''")"""

NEW_SPARK = """                if response_schema is not None:
                    _v481_rf = _v481_response_format_envelope(response_schema, prompt_name, step_name)
                    if _v481_rf is not response_schema:
                        try:
                            self.logger.info(f"  [v481-response-format-envelope FIRED v4.8.1] prompt={prompt_name!r} raw JSON Schema wrapped in {{name, schema}} envelope for ai_query responseFormat alias=v481-response-format-envelope")
                        except Exception:
                            pass
                    response_format_str = json.dumps({"type": "json_schema", "json_schema": _v481_rf}, separators=(',', ':')).replace("'", "''")"""

SAMPLES_SITES = [
    (120, '    for _subfolder in ["schemas", "samples", "docs", "vibes", "ontology", "sandbox", "diagram", "metrics"]:',
          '    for _subfolder in ["schemas", "docs", "vibes", "ontology", "sandbox", "diagram", "metrics"]:'),
    (204, '                _deploy_subfolders = ["schemas", "samples", "docs", "vibes", "ontology", "diagram", "metrics", "snapshots"]',
          '                _deploy_subfolders = ["schemas", "docs", "vibes", "ontology", "diagram", "metrics", "snapshots"]'),
    (202, '        "metrics": "metrics",\n        "samples": "samples",\n    }',
          '        "metrics": "metrics",\n    }'),
]


def cell_text(cell):
    src = cell.get("source", [])
    return "".join(src) if isinstance(src, list) else src


def set_cell(cell, text):
    cell["source"] = text


def main():
    nb = json.load(open(NB))
    cells = nb["cells"]
    applied = []

    # FIX 1a: helper
    t86 = cell_text(cells[86])
    if "_v481_response_format_envelope" not in t86:
        anchor = "def _v446_coerce_ai_response(response_rows):"
        assert anchor in t86, "helper anchor not found"
        t86 = t86.replace(anchor, HELPER.lstrip("\n") + anchor, 1)
        applied.append("helper _v481_response_format_envelope")

    # FIX 1b: spark call site
    if "_v481_rf = _v481_response_format_envelope" not in t86:
        assert OLD_SPARK in t86, "spark responseFormat anchor not found"
        t86 = t86.replace(OLD_SPARK, NEW_SPARK, 1)
        applied.append("spark ai_query responseFormat envelope")
    set_cell(cells[86], t86)

    # FIX 2: samples folder sites
    for idx, old, new in SAMPLES_SITES:
        t = cell_text(cells[idx])
        if old in t:
            set_cell(cells[idx], t.replace(old, new, 1))
            applied.append(f"samples folder removed from cell {idx}")
        elif new not in t:
            raise AssertionError(f"cell {idx}: neither old nor new samples list found")

    # FIX 3: version bump
    t1 = cell_text(cells[1])
    if '__AGENT_VERSION__ = "4.8.0"' in t1:
        set_cell(cells[1], t1.replace('__AGENT_VERSION__ = "4.8.0"', '__AGENT_VERSION__ = "4.8.1"', 1))
        applied.append("__AGENT_VERSION__ -> 4.8.1")

    if not applied:
        print("already applied, nothing to do")
        return 0

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    for a in applied:
        print("applied:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
