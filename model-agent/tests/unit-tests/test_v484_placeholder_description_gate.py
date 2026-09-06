"""v4.8.4 - a description that promises its own replacement must be scored, at every scope.

Live failure this pins (coffee_roastery mvm_v1, run 1060088887830650, agent 4.8.3): the
published model.json described two of its four domains as "... injected by v0.7.3 P0.52
because the judge omitted it. Replace this description when the architect review runs."
The gate that exists to catch placeholder text read attributes only and measured length,
so 130 characters of internal engineering note reached the customer artifact unscored, and
the SelfFixer - which already lists low_quality_description as fixable - never saw a
finding to repair.
"""
import json
import re

from notebook_source_util import agent_version_line, notebook_concat_source
# the deployed static-analysis function, built from the real notebook, not a re-implementation
from test_v368_qgate_suite import _run_sa

SRC = notebook_concat_source()


def _run_gate(domains, products, attributes):
    """Run the deployed gate and return only its description-quality findings."""
    _, issues = _run_sa(domains, products, attributes)
    return [i for i in issues if i.get("category") == "low_quality_description"]


PROVISIONAL = ("Provisional description for user-specified domain 'wholesale'. "
               "Awaiting a generated description of what this domain owns.")
LEGACY = ("User-specified domain 'wholesale' injected by v0.7.3 P0.52 because the judge "
          "omitted it. Replace this description when the architect review runs.")
GOOD_DOM = ("Owns wholesale account, order and invoice data for the business, including "
            "pricing tiers and fulfilment commitments to trade customers.")
GOOD_PRD = "One row per wholesale customer order, keyed by order id."
GOOD_ATTR = "Monetary total of the order before tax and discounts."


def _model(dom_desc=GOOD_DOM, prd_desc=GOOD_PRD, attr_desc=GOOD_ATTR):
    domains = [{"domain": "wholesale", "description": dom_desc, "division": "business"}]
    products = [{"domain": "wholesale", "product": "order", "description": prd_desc,
                 "primary_key": "order_id", "table_name": "order"}]
    attributes = [{"domain": "wholesale", "product": "order", "attribute": "order_total",
                   "description": attr_desc, "data_type": "DECIMAL(18,2)"}]
    return domains, products, attributes


def test_the_exact_text_that_shipped_to_a_customer_is_now_scored():
    found = _run_gate(*_model(dom_desc=LEGACY))
    assert found, "the v4.8.3 published domain description was not scored by any gate"
    assert "wholesale" in json.dumps(found)


def test_the_new_provisional_wording_is_also_scored():
    # the injected description is deliberately publishable, so only a content rule catches
    # it; if this regresses the domain silently ships a stub description.
    found = _run_gate(*_model(dom_desc=PROVISIONAL))
    assert found, "provisional domain description was not scored"


def test_a_real_domain_description_is_not_scored():
    # the guard against a gate that fires on everything and so means nothing
    assert _run_gate(*_model()) == []


def test_a_placeholder_on_a_table_is_scored_too():
    found = _run_gate(*_model(prd_desc="Replace this description later."))
    assert found
    assert found[0]["details"]["by_scope"]["table"] == 1


def test_the_attribute_scope_that_already_worked_still_works():
    found = _run_gate(*_model(attr_desc="TBD"))
    assert found
    assert found[0]["details"]["by_scope"]["attribute"] == 1


def test_each_scope_is_counted_separately_so_the_report_is_actionable():
    found = _run_gate(*_model(dom_desc=LEGACY, prd_desc="TODO", attr_desc="n/a"))
    assert found
    scopes = found[0]["details"]["by_scope"]
    assert scopes == {"domain": 1, "table": 1, "attribute": 1}, scopes


def test_an_empty_description_is_left_to_the_missing_description_gates():
    # emptiness is a different category; double-reporting it would inflate the scoreboard
    found = _run_gate(*_model(dom_desc=""))
    assert found == []


def test_the_finding_stays_in_the_category_the_selffixer_already_repairs():
    # low_quality_description is in the _fixable whitelist; a new category name would
    # emit a finding that nothing is wired to repair
    found = _run_gate(*_model(dom_desc=LEGACY))
    assert found[0]["category"] == "low_quality_description"
    assert "modify" in found[0]["remediation_actions"]


def test_the_injection_site_no_longer_writes_an_engineering_note():
    assert "injected by v0.7.3 P0.52" not in SRC
    assert "Replace this description when the" not in SRC
    assert "Provisional description for user-specified domain" in SRC


def test_the_gate_reports_itself_so_a_live_run_can_be_audited():
    assert SRC.count("qgate-placeholder-description FIRED v4.8.4") == 1


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', agent_version_line())
    assert m, agent_version_line()
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 4), agent_version_line()
