"""v4.8.4 - stop publishing internal placeholder text as a domain description.

Live evidence (coffee_roastery mvm_v1, run 1060088887830650, agent 4.8.3): two of four
published domains carried

    "User-specified domain 'wholesale' injected by v0.7.3 P0.52 because the judge omitted
     it. Replace this description when the architect review runs."

as their model.json description. Nothing ever replaced it, and the architect then failed
trust_in_production / support_in_production / recommend_to_industry_peers /
propose_for_global_standard for exactly those two domains on every iteration.

Two root causes, both fixed here:

  1. The P0.52 domain-injection site writes an internal engineering note into a
     customer-facing field. It names an internal patch id and "the judge", and it promises
     a replacement that no mechanism guarantees.

  2. The low_quality_description gate that should have caught it iterates attributes_data
     ONLY, so domain and product descriptions are never scored; and its placeholder rule is
     an exact-match token set plus a <10 char floor, which 130 characters of prose passes.
     Because the gate never fired, the SelfFixer never saw it - the category is already in
     the _fixable whitelist, so emitting the finding is all that was missing.
"""
import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "agent" / "dbx_vibe_modelling_agent.ipynb"

OLD_DESC = '''                    "description": (
                        f"User-specified domain '{_usd_name}' injected by v0.7.3 P0.52 "
                        f"because the judge omitted it. Replace this description when the "
                        f"architect review runs."
                    ),'''

NEW_DESC = '''                    "description": (
                        f"Provisional description for user-specified domain '{_usd_name}'. "
                        f"Awaiting a generated description of what this domain owns."
                    ),'''

OLD_GATE = '''    _qg_placeholder = {"tbd", "n/a", "na", "todo", "description", "none", "null", "-", "."}
    _qg_lowq = 0
    _qg_lowq_sample = []
    for attr in attributes_data:
        _d = str(attr.get("description", "") or "").strip()
        an = attr.get("attribute", "")
        if not _d:
            continue
        if _d.lower() in _qg_placeholder or len(_d) < 10 or _d.lower() == str(an or "").lower():
            _qg_lowq += 1
            if len(_qg_lowq_sample) < 25:
                _qg_lowq_sample.append(attr.get("domain", "") + "." + attr.get("product", "") + "." + an)
    if _qg_lowq > 0:
        issues.append({
            "category": "low_quality_description",
            "severity": "info",
            "message": str(_qg_lowq) + " attribute description(s) are placeholders, echoes of the name, or <10 chars. e.g., " + ", ".join(_qg_lowq_sample[:5]),
            "details": {"count": _qg_lowq, "attributes": _qg_lowq_sample},
            "remediation_actions": ["modify"]
        })'''

NEW_GATE = '''    _qg_placeholder = {"tbd", "n/a", "na", "todo", "description", "none", "null", "-", "."}
    # A description that announces its own replacement, or that leaks the internal patch
    # that wrote it, is a placeholder however long it runs. alias=qgate-placeholder-description
    _qg_provisional_marks = (
        "replace this description", "provisional description", "injected by v",
        "placeholder description", "description pending", "to be written",
        "to be provided", "fill this in",
    )

    def _qg_desc_low_quality(_desc, _name):
        _d = str(_desc or "").strip()
        if not _d:
            return False  # emptiness is scored by the missing_*_description gates
        _dl = _d.lower()
        return bool(_dl in _qg_placeholder
                    or len(_d) < 10
                    or _dl == str(_name or "").lower()
                    or any(_mark in _dl for _mark in _qg_provisional_marks))

    _qg_lowq = 0
    _qg_lowq_sample = []
    _qg_lowq_scopes = {"domain": 0, "table": 0, "attribute": 0}
    for _dom in domains_data:
        if _qg_desc_low_quality(_dom.get("description", ""), _dom.get("domain", "")):
            _qg_lowq += 1
            _qg_lowq_scopes["domain"] += 1
            if len(_qg_lowq_sample) < 25:
                _qg_lowq_sample.append(str(_dom.get("domain", "")))
    for _prd in products_data:
        if _qg_desc_low_quality(_prd.get("description", ""), _prd.get("product", "")):
            _qg_lowq += 1
            _qg_lowq_scopes["table"] += 1
            if len(_qg_lowq_sample) < 25:
                _qg_lowq_sample.append(str(_prd.get("domain", "")) + "." + str(_prd.get("product", "")))
    for attr in attributes_data:
        an = attr.get("attribute", "")
        if _qg_desc_low_quality(attr.get("description", ""), an):
            _qg_lowq += 1
            _qg_lowq_scopes["attribute"] += 1
            if len(_qg_lowq_sample) < 25:
                _qg_lowq_sample.append(attr.get("domain", "") + "." + attr.get("product", "") + "." + an)
    if _qg_lowq > 0:
        logger.info("  [qgate-placeholder-description FIRED v4.8.4] "
                    + str(_qg_lowq_scopes["domain"]) + " domain / "
                    + str(_qg_lowq_scopes["table"]) + " table / "
                    + str(_qg_lowq_scopes["attribute"]) + " attribute description(s) are "
                    "placeholders, echoes of the name, or <10 chars alias=qgate-placeholder-description")
        issues.append({
            "category": "low_quality_description",
            "severity": "info",
            "message": str(_qg_lowq) + " description(s) are placeholders, echoes of the name, or <10 chars ("
                       + str(_qg_lowq_scopes["domain"]) + " domain, " + str(_qg_lowq_scopes["table"])
                       + " table, " + str(_qg_lowq_scopes["attribute"]) + " attribute). e.g., "
                       + ", ".join(_qg_lowq_sample[:5]),
            "details": {"count": _qg_lowq, "by_scope": _qg_lowq_scopes, "attributes": _qg_lowq_sample},
            "remediation_actions": ["modify"]
        })'''


def cell_text(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def put(cell, text):
    """Write back in the cell's own representation so the diff stays the size of the edit."""
    cell["source"] = text.splitlines(keepends=True) if isinstance(cell.get("source"), list) else text


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    edits = {"description": 0, "gate": 0, "version": 0}

    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = cell_text(cell)
        out = src

        if OLD_DESC in out:
            out = out.replace(OLD_DESC, NEW_DESC)
            edits["description"] += 1
        if OLD_GATE in out:
            out = out.replace(OLD_GATE, NEW_GATE)
            edits["gate"] += 1
        if '__AGENT_VERSION__ = "4.8.3"' in out:
            out = out.replace('__AGENT_VERSION__ = "4.8.3"', '__AGENT_VERSION__ = "4.8.4"')
            edits["version"] += 1

        if out != src:
            put(cell, out)

    for key, want in (("description", 1), ("gate", 1), ("version", 1)):
        if edits[key] != want:
            print("FAIL %s: expected %d anchor(s), matched %d" % (key, want, edits[key]))
            return 1

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print("patched: %s" % edits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
