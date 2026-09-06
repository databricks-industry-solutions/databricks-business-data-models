"""v3.9.5 behavioral guard (§8.10 fail-pre/pass-post) for Fix B1
(alias=verifier-description-coverage).

ROOT CAUSE (ngo + manufacturing v3.9.2 independent VReq audits): description/comment VReqs were
APPLIED to the model dict (SelfFixer update_description landed, proven by _selffixer_state_signature
delta) but the LLM verifier snapshot _v260_summarize_model_for_llm OMITS descriptions/comments, so
every such VReq false-negatived (verifier-skipped-budget / partial) -- the mission's #1
lying-scoreboard lever.

VibeOrchestrator._v395_verify_description_coverage decides the description class from the after-state
dict with NO budget, ALL-PRESENT (every extracted target term must appear, never a 50% threshold),
FULFILLED-ONLY: it can RESCUE a genuine false-negative, and can NEVER inflate (a missing term, an
old-term-left-behind 'replace', or an out-of-scope term all return None so the caller keeps its
existing verdict).

fail-pre proof:
    VOV_NB=/tmp/agent_v394_backup.ipynb pytest tests/unit-tests/test_v395_description_verifier.py
    -> the method is ABSENT pre-patch => the fixture pytest.fail's.
"""
import ast
import json
import logging
import os
import textwrap
from collections import defaultdict

import pytest

NB = os.environ.get(
    "VOV_NB",
    "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb",
)

LG = logging.getLogger("t395")
LG.addHandler(logging.NullHandler())


def _src():
    nb = json.load(open(NB))
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


def _extract_method(class_name, method_name):
    src = _src()
    tree = ast.parse(src)
    lines = src.split("\n")
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name == method_name:
                    return textwrap.dedent("\n".join(lines[sub.lineno - 1:sub.end_lineno]))
    return None


@pytest.fixture(scope="module")
def desc_fn():
    method_src = _extract_method("VibeOrchestrator", "_v395_verify_description_coverage")
    if method_src is None:
        pytest.fail("FAIL-PRE: VibeOrchestrator._v395_verify_description_coverage ABSENT (expected pre-patch)")
    ns = {"defaultdict": defaultdict}
    exec(compile(method_src, "<v395-method>", "exec"), ns)
    return ns["_v395_verify_description_coverage"]


class _Req:
    def __init__(self, text, scope_targets=None, rid="VREQ-T"):
        self.original_text = text
        self.scope_targets = scope_targets or []
        self.id = rid


class _FakeSelf:
    """The hoisted method calls self.logger.info on the fulfilled path."""
    logger = LG


SELF = _FakeSelf()


def _model(prod_desc=None, attr_desc=None, domain="finance", product="ledger"):
    products = [{"domain": domain, "product": product, "description": prod_desc or ""}]
    attrs = [{"domain": domain, "product": product, "attribute": "framework_code",
              "type": "STRING", "description": attr_desc or ""}]
    return products, attrs


# ---------------------------------------------------------------------------
# PASS-POST: rescue genuine false-negative (all required terms now present)
# ---------------------------------------------------------------------------
def test_all_terms_present_fulfilled(desc_fn):
    products, attrs = _model(
        prod_desc="General ledger. Financial statements are now prepared under IPSAS accrual basis.",
    )
    req = _Req("Reframe the accounting-framework references in finance descriptions to IPSAS.")
    res = desc_fn(SELF, req, products, attrs)
    assert res and res["status"] == "fulfilled"
    assert "verifier-description-coverage FIRED v3.9.5" in res["evidence"]


def test_multi_system_list_all_present_fulfilled(desc_fn):
    products, attrs = _model(
        domain="operations", product="programme",
        prod_desc="Programme delivery sourced from SAP and DHIS2 and ICON and RAM systems.",
    )
    req = _Req("Reference SAP, DHIS2, ICON and RAM in the operations table descriptions.")
    res = desc_fn(SELF, req, products, attrs)
    assert res and res["status"] == "fulfilled"


def test_backticked_term_present_fulfilled(desc_fn):
    products, attrs = _model(prod_desc="Records reconciled against the etools platform feed.")
    req = _Req("Mention `eTools` in the finance.ledger description.")
    res = desc_fn(SELF, req, products, attrs)
    assert res and res["status"] == "fulfilled"


# ---------------------------------------------------------------------------
# ANTI-INFLATION: a missing / unapplied term must NEVER be credited (-> None)
# ---------------------------------------------------------------------------
def test_missing_term_not_credited(desc_fn):
    products, attrs = _model(prod_desc="General ledger. Prepared under the local statutory basis.")
    req = _Req("Reframe the accounting-framework references in finance descriptions to IPSAS.")
    assert desc_fn(SELF, req, products, attrs) is None


def test_replace_left_old_term_behind_not_inflated(desc_fn):
    # VReq names BOTH the old (ASC958) and new (IPSAS) framework; only the OLD is still present.
    # ALL-PRESENT rule => IPSAS absent => NOT credited (the §8.3 inflation guard).
    products, attrs = _model(
        prod_desc="Statements prepared under ASC958 not-for-profit guidance.",
    )
    req = _Req("Reframe descriptions: replace ASC958 with IPSAS.")
    assert desc_fn(SELF, req, products, attrs) is None


def test_one_of_many_systems_missing_not_credited(desc_fn):
    products, attrs = _model(
        domain="operations", product="programme",
        prod_desc="Programme delivery sourced from SAP and DHIS2 and ICON systems.",  # RAM missing
    )
    req = _Req("Reference SAP, DHIS2, ICON and RAM in the operations table descriptions.")
    assert desc_fn(SELF, req, products, attrs) is None


def test_term_substring_does_not_falsely_match(desc_fn):
    # 'RAM' must not match inside 'program'/'parameter' (word-boundary guard).
    products, attrs = _model(
        domain="operations", product="programme",
        prod_desc="Programme parameters and diagrams only; no source-system reference.",
    )
    req = _Req("Reference RAM in the operations descriptions.")
    assert desc_fn(SELF, req, products, attrs) is None


# ---------------------------------------------------------------------------
# SCOPE + GATING
# ---------------------------------------------------------------------------
def test_scope_restricts_to_named_domain(desc_fn):
    # Required term present ONLY in another domain; VReq names 'finance' -> not credited.
    products = [
        {"domain": "finance", "product": "ledger", "description": "Local statutory basis only."},
        {"domain": "operations", "product": "log", "description": "Prepared under IPSAS basis."},
    ]
    attrs = [
        {"domain": "finance", "product": "ledger", "attribute": "x", "type": "STRING", "description": ""},
        {"domain": "operations", "product": "log", "attribute": "y", "type": "STRING", "description": ""},
    ]
    req = _Req("Reframe the finance descriptions to reference IPSAS.")
    assert desc_fn(SELF, req, products, attrs) is None


def test_non_description_vreq_returns_none(desc_fn):
    products, attrs = _model(prod_desc="Anything with IPSAS in it.")
    req = _Req("Move product ledger from finance to operations domain.")
    assert desc_fn(SELF, req, products, attrs) is None


def test_no_extractable_terms_returns_none(desc_fn):
    products, attrs = _model(prod_desc="lots of lowercase prose with no acronyms at all here")
    req = _Req("Improve the wording of the finance.ledger description for clarity.")
    assert desc_fn(SELF, req, products, attrs) is None
