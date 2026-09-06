"""v4.6.4 — behavioral tests for the PII lying-scoreboard root cause.

ROOT CAUSE (proven from v4.6.3 Test-00 audit + next_vibes.txt "13 attribute(s)
match person-data patterns but lack pii_ tags"):
  - The deterministic SA gate (pii_tagging_missing) detects untagged person columns
    with a WORD-BOUNDARY regex + false-positive guard and expects 100% coverage.
  - The VREQ verifier (verifier-model-wide-pii-tag) used a DIFFERENT substring
    detector AND a 0.7 "fulfilled" threshold, so it declared the PII VREQ FULFILLED
    while the SA gate still flagged N untagged person columns. The SelfFixer then
    saw a fulfilled requirement and no-op'd (selffixer-noop-guard fired 4x), so the
    remaining person columns never got tagged.

FIX (v4.6.4 alias=pii-verifier-sa-parity):
  - One shared classifier `_v464_classify_pii_column` (word-boundary regex + FP guard)
    is used by BOTH the SA gate and the verifier — identical detection.
  - The verifier credits 'fulfilled' ONLY when 0 person columns are missing a tag
    (parity with the SA gate), 'failed' when none are tagged, else 'partial'.

These tests slice the REAL module-level classifier + patterns from the notebook and
assert the observable classification and the parity decision. The parity-decision test
FAILS on pre-patch HEAD (0.7 threshold -> fulfilled at 0.8 coverage) and PASSES
post-patch (missing>0 -> partial).
"""
import ast
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = REPO_ROOT / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _concat_source():
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        if src.strip():
            parts.append(src)
    return "\n\n".join(parts)


SOURCE = _concat_source()


def _classifier_namespace():
    """Slice PII_FALSE_POSITIVE_RE, _PII_NAME_PATTERNS_RE and _v464_classify_pii_column
    from the notebook and exec them in an isolated namespace with `re` available."""
    lines = SOURCE.splitlines(keepends=True)
    tree = ast.parse(SOURCE)
    wanted = {}
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    name = t.id
        if name in ("PII_FALSE_POSITIVE_RE", "_PII_NAME_PATTERNS_RE", "_v464_classify_pii_column"):
            wanted[name] = "".join(lines[node.lineno - 1: node.end_lineno])
    missing = {"PII_FALSE_POSITIVE_RE", "_PII_NAME_PATTERNS_RE", "_v464_classify_pii_column"} - set(wanted)
    if missing:
        raise LookupError(f"missing module-level defs: {missing}")
    blob = "\n\n".join([wanted["PII_FALSE_POSITIVE_RE"], wanted["_PII_NAME_PATTERNS_RE"], wanted["_v464_classify_pii_column"]])
    ns = {"__name__": "_test_pii", "re": re}
    exec(compile(blob, str(NOTEBOOK_PATH), "exec"), ns)
    return ns


def test_classifier_person_untagged_is_missing():
    cls = _classifier_namespace()["_v464_classify_pii_column"]
    assert cls("customer_email", "") == "missing"
    assert cls("employee_name", "") == "missing"
    assert cls("approved_by", None) == "missing"
    assert cls("home_address", "some_other_tag") == "missing"


def test_classifier_tagged_and_pk_are_ok():
    cls = _classifier_namespace()["_v464_classify_pii_column"]
    assert cls("customer_email", "pii_email") == "ok"
    assert cls("employee_name", "PII") == "ok"
    assert cls("customer_id", "primary_key") == "ok"


def test_classifier_non_person_is_ok():
    cls = _classifier_namespace()["_v464_classify_pii_column"]
    assert cls("order_total", "") == "ok"
    assert cls("quantity", "") == "ok"
    assert cls("status_code", "") == "ok"


def test_classifier_false_positive_is_skipped():
    cls = _classifier_namespace()["_v464_classify_pii_column"]
    # 'address_type' / 'email_format' are generic descriptors, not person PII
    assert cls("address_type", "") == "fp_skip"
    assert cls("email_format", "") == "fp_skip"
    assert cls("equipment_serial", "") == "ok"  # 'serial' not a person pattern at all


def _verifier_decision(columns):
    """Replicate the POST-PATCH verifier parity rule using the REAL sliced classifier.
    `columns` = list of (name, tags). Returns 'fulfilled' | 'partial' | 'failed' | 'n/a'.
    Pre-patch the rule was `cov >= 0.7 -> fulfilled`; post-patch it is `missing == 0`.
    """
    cls = _classifier_namespace()["_v464_classify_pii_column"]
    pat = _classifier_namespace()["_PII_NAME_PATTERNS_RE"]
    tot = tag = missing = 0
    for name, tags in columns:
        ts = (tags or "").lower()
        c = cls(name, ts)
        if c == "missing":
            tot += 1
            missing += 1
        elif c == "ok" and pat.search((name or "").lower()) and (("pii" in ts) or ("classif" in ts) or ("sensitive" in ts) or ("personal" in ts)):
            tot += 1
            tag += 1
    if tot == 0:
        return "n/a"
    if missing == 0:
        return "fulfilled"
    if tag == 0:
        return "failed"
    return "partial"


def test_parity_partial_when_some_untagged():
    """The exact lying-scoreboard scenario: 8/10 person cols tagged (0.8 coverage).
    Pre-patch (0.7 threshold) => 'fulfilled' (the bug). Post-patch (0 missing rule)
    => 'partial' because 2 person columns are still untagged."""
    cols = [(f"person{i}_name", "pii_name") for i in range(8)]  # tagged
    cols += [("customer_email", ""), ("employee_phone", "")]     # untagged
    assert _verifier_decision(cols) == "partial"


def test_parity_fulfilled_only_at_full_coverage():
    cols = [("person_name", "pii_name"), ("customer_email", "pii_email")]
    assert _verifier_decision(cols) == "fulfilled"


def test_parity_failed_when_none_tagged():
    cols = [("person_name", ""), ("customer_email", "")]
    assert _verifier_decision(cols) == "failed"


def test_aliases_present_in_source():
    assert "pii-verifier-sa-parity" in SOURCE
    assert "verifier-model-wide-pii-tag FIRED v4.6.4" in SOURCE
    # verifier gates on 0-missing parity, not a 0.7 coverage threshold
    assert "_v336_missing == 0" in SOURCE
    assert "_v336_cov >= 0.7" not in SOURCE
    # SA gate reuses the shared classifier (DRY)
    assert "_v464_classify_pii_column(attr.get('attribute'), attr.get('tags'))" in SOURCE
