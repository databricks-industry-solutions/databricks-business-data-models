"""v4.5.7 behavioral test -- domain-architect-response-coerce.

Fail-pre / pass-post for AttributeError when domain architect LLM returns
string (or list-of-strings) nested fields instead of dict / list-of-dicts.
"""
from __future__ import annotations

from notebook_source_util import agent_version_line

import ast
import json
import types
from pathlib import Path

import pytest

NB = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _cell_src(idx: int) -> str:
    nb = json.loads(NB.read_text())
    src = nb["cells"][idx]["source"]
    return "".join(src) if isinstance(src, list) else src


def _load_helpers():
    """Isolate _coerce_dict / _coerce_list_of_dicts + apply function via AST."""
    nb = json.loads(NB.read_text())
    # cell 25 has coerce helpers
    cell25 = "".join(nb["cells"][25]["source"])
    cell140 = "".join(nb["cells"][140]["source"])

    ns: dict = {
        "json": json,
        "re": __import__("re"),
        "sanitize_name": lambda s: str(s or "").strip().lower().replace(" ", "_"),
        "_GATE_ORDER": (
            "trust_in_production",
            "support_in_production",
            "recommend_to_industry_peers",
            "propose_for_global_standard",
        ),
        "_tier_aware_architect_gate_keys": lambda directives, logger=None, alias="": (
            (
                "trust_in_production",
                "support_in_production",
                "recommend_to_industry_peers",
                "propose_for_global_standard",
            ),
            (),
        ),
    }
    # exec coerce helpers
    tree25 = ast.parse(cell25)
    wanted25 = {"_coerce_dict", "_coerce_list_of_dicts"}
    body25 = [n for n in tree25.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted25]
    mod25 = ast.Module(body=body25, type_ignores=[])
    exec(compile(mod25, "<cell25>", "exec"), ns)

    tree140 = ast.parse(cell140)
    wanted140 = {
        "_apply_single_domain_review_to_model",
        "_normalize_gate_hierarchy",
        "_gate_is_pass",
    }
    body140 = [
        n for n in tree140.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted140
    ]
    assert any(getattr(n, "name", None) == "_apply_single_domain_review_to_model" for n in body140)
    mod140 = ast.Module(body=body140, type_ignores=[])
    exec(compile(mod140, "<cell140>", "exec"), ns)
    return ns


class _Log:
    def __init__(self):
        self.lines = []

    def info(self, m):
        self.lines.append(str(m))

    def warning(self, m):
        self.lines.append(str(m))


def test_agent_version_is_457():
    src = _cell_src(1)
    assert agent_version_line() in src
    # first non-comment code statement
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert s == agent_version_line()
        break


def test_alias_present_in_source():
    src = _cell_src(140)
    assert "domain-architect-response-coerce FIRED v4.5.7" in src
    assert '_coerce_list_of_dicts(_resp.get("products_to_rename"))' in src


def test_string_response_does_not_crash():
    ns = _load_helpers()
    fn = ns["_apply_single_domain_review_to_model"]
    products = [{"domain": "claim", "product": "claim_case", "primary_key": "claim_case_id"}]
    logger = _Log()
    stats = {
        "products_added": 0,
        "products_renamed": 0,
        "products_removed": 0,
        "products_merged": 0,
        "products_split": 0,
        "descriptions_updated": 0,
        "in_domain_links_queued": 0,
        "next_vibes_queued": 0,
        "domain_gate_failures": 0,
    }
    # whole response as narrative string (the crash shape)
    all_pass, record = fn(
        response_data="Domain looks incomplete; add more products.",
        domain_name="claim",
        products_data=products,
        must_have_set=set(),
        next_vibes_queue=[],
        in_domain_link_queue=[],
        applied_log=[],
        stats=stats,
        logger=logger,
    )
    assert isinstance(all_pass, bool)
    assert isinstance(record, dict)
    assert any("domain-architect-response-coerce FIRED v4.5.7" in x for x in logger.lines)


def test_list_of_strings_fields_do_not_crash():
    ns = _load_helpers()
    fn = ns["_apply_single_domain_review_to_model"]
    products = [{"domain": "claim", "product": "claim_case", "primary_key": "claim_case_id"}]
    logger = _Log()
    stats = {
        "products_added": 0,
        "products_renamed": 0,
        "products_removed": 0,
        "products_merged": 0,
        "products_split": 0,
        "descriptions_updated": 0,
        "in_domain_links_queued": 0,
        "next_vibes_queued": 0,
        "domain_gate_failures": 0,
    }
    resp = {
        "products_to_rename": ["rename claim_case to claim"],
        "products_to_remove": ["drop junk"],
        "products_to_add": ["add claim_note"],
        "description_improvements": ["improve desc"],
        "products_to_merge": ["merge a into b"],
        "products_to_split": ["split x"],
        "in_domain_links_needed": ["link a->b"],
        "next_vibes_items": ["later"],
        "assessment": "looks ok",
        "production_readiness_gates": "not a dict",
        "prior_iteration_self_review": "n/a",
    }
    all_pass, record = fn(
        response_data=resp,
        domain_name="claim",
        products_data=products,
        must_have_set=set(),
        next_vibes_queue=[],
        in_domain_link_queue=[],
        applied_log=[],
        stats=stats,
        logger=logger,
    )
    assert isinstance(all_pass, bool)
    assert products[0]["product"] == "claim_case"  # no bogus mutation from string items
