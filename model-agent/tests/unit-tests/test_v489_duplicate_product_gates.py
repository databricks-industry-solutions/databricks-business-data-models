"""v4.8.9 alias=dup-product-gate-separator-blind.

Live evidence, coffee_roastery run 564741857926303: the published model.json and the
physical catalog both carried wholesale.invoice AND wholesale.wholesale_invoice, while
every one of the 11 static-analysis passes reported zero errors and the final pass logged
"4 warnings, 11 info". The architect reviewer saw the duplicate and prescribed the merge
("brings wholesale to 7"); nothing deterministic ever confirmed it landed, so the model
shipped 9 products in that domain against a user ceiling of 7.

Two causes, both reproduced here against the real notebook code:

  1. _validate_product_name_collisions Pass 2 buckets by product name ONLY, so a pair in
     the SAME domain enters the cross-domain branch and is renamed apart and reported as
     "duplicate of 'invoice' in another domain", which is false.
  2. The duplicate_product_pair gate compared f"{domain}_{pname}" against pname.lower().
     Pass 2 renames to PascalCase and a later pass canonicalises to snake, so in between
     the gate compares 'wholesale_invoice' against 'wholesaleinvoice' and sees nothing.
"""
import re

import pytest

from notebook_source_util import (assert_agent_version_at_least, cell_containing,
                                 slice_function_source)

I3_ANCHOR = '"duplicate_product_pair"'
COLLISION_ANCHOR = "P0.74-COLLISION-CROSSDOMAIN"


class _Log:
    def __init__(self):
        self.lines = []

    def _add(self, msg):
        self.lines.append(str(msg))

    info = warning = error = _add

    @property
    def text(self):
        return "\n".join(self.lines)


def _norm():
    src = cell_containing("def _v489_norm_entity")
    ns = {"re": re}
    exec(slice_function_source("_v489_norm_entity", src), ns)
    return ns["_v489_norm_entity"]


def _run_collisions(products, domains=None):
    src = cell_containing(COLLISION_ANCHOR)
    ns = {"re": re}
    exec("\n\n".join(slice_function_source(f, src) for f in
                     ("_p074_qualified_rename", "_validate_product_name_collisions")), ns)
    log = _Log()
    stats = ns["_validate_product_name_collisions"](
        domains or [{"domain": p["domain"]} for p in products], products, [], log)
    return stats, log


def _run_i3(products_by_domain):
    """Execute the real I3 gate region, nothing stubbed but its two inputs."""
    src = cell_containing(I3_ANCHOR)
    start = src.index("    # I3: Duplicate product pair detection")
    end = src.index("    # I4:")
    body = src[start:end]
    if "_v489_norm_entity" in body:
        ns = {"re": re}
        exec(slice_function_source("_v489_norm_entity",
                                   cell_containing("def _v489_norm_entity")), ns)
    else:
        ns = {"re": re}
    ns.update({"issues": [], "products_by_domain": products_by_domain, "logger": _Log()})
    exec("if True:\n" + body, ns)
    return ns["issues"]


# --- the normaliser ------------------------------------------------------------------

@pytest.mark.parametrize("a,b", [
    ("wholesale_invoice", "WholesaleInvoice"),
    ("wholesale_invoice", "Wholesale Invoice"),
    ("wholesale_invoice", "wholesale-invoice"),
    ("wholesale_invoice", "WHOLESALE__INVOICE"),
])
def test_the_same_entity_in_any_casing_normalises_together(a, b):
    norm = _norm()
    assert norm(a) == norm(b)


@pytest.mark.parametrize("a,b", [
    ("invoice", "invoices"),
    ("wholesale_invoice", "retail_invoice"),
    ("invoice", "invoice_line"),
])
def test_different_entities_stay_different(a, b):
    norm = _norm()
    assert norm(a) != norm(b)


@pytest.mark.parametrize("bad", [None, "", "___", "   "])
def test_the_normaliser_survives_empty_input(bad):
    assert _norm()(bad) == ""


# --- gate 1: the pair the live run shipped -------------------------------------------

def test_the_live_pair_is_caught_in_snake_case():
    """THE REGRESSION, in the casing the published model.json actually carried."""
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "wholesale_invoice"},
                                    {"product": "sales_order"}]})
    cats = [i["category"] for i in issues]
    assert "duplicate_product_pair" in cats, (
        "wholesale.invoice + wholesale.wholesale_invoice must be reported")
    pair = next(i for i in issues if i["category"] == "duplicate_product_pair")
    assert pair["severity"] == "error"
    assert pair["remediation_actions"] == ["merge"]


def test_the_live_pair_is_caught_mid_pipeline_in_pascal_case():
    """The window the gate was blind in: renamed but not yet canonicalised."""
    issues = _run_i3({"wholesale": [{"product": "invoice"},
                                    {"product": "WholesaleInvoice"}]})
    assert "duplicate_product_pair" in [i["category"] for i in issues]


def test_a_clean_domain_reports_nothing():
    """The negative control: without this the gate could report everything and 'pass'."""
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "sales_order"},
                                    {"product": "delivery"}]})
    assert issues == []


def test_a_product_merely_sharing_a_stem_is_not_a_pair():
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "invoice_line"}]})
    assert issues == []


# --- gate 2: same-domain X vs X, which no gate covered -------------------------------

def test_two_products_with_one_name_in_one_domain_are_reported():
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "invoice"}]})
    dup = [i for i in issues if i["category"] == "duplicate_product_name"]
    assert dup, "a same-domain X vs X duplicate must be an error, not silence"
    assert dup[0]["severity"] == "error"
    assert dup[0]["remediation_actions"] == ["merge"]
    assert dup[0]["details"]["products"] == ["invoice"]


def test_the_same_entity_declared_in_two_casings_is_one_duplicate():
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "Invoice"}]})
    dup = [i for i in issues if i["category"] == "duplicate_product_name"]
    assert len(dup) == 1
    assert dup[0]["details"]["products"] == ["Invoice", "invoice"]


def test_blank_product_names_are_not_counted_as_duplicates_of_each_other():
    issues = _run_i3({"wholesale": [{"product": ""}, {"product": None}, {"product": "  "}]})
    assert issues == []


def test_every_affected_domain_is_reported_not_just_the_first():
    issues = _run_i3({"wholesale": [{"product": "invoice"}, {"product": "invoice"}],
                      "retail": [{"product": "receipt"}, {"product": "receipt"}]})
    doms = {i["details"]["domain"] for i in issues
            if i["category"] == "duplicate_product_name"}
    assert doms == {"wholesale", "retail"}


# --- the mislabel in the collision autofix -------------------------------------------

def test_a_same_domain_duplicate_is_not_called_cross_domain():
    products = [{"domain": "wholesale", "product": "invoice"},
                {"domain": "wholesale", "product": "invoice"}]
    _stats, log = _run_collisions(products, domains=[{"domain": "wholesale"}])
    assert "in another domain" not in log.text, (
        "two products in ONE domain are not a cross-domain collision")


def test_a_genuine_cross_domain_collision_still_says_so():
    """The other half of the branch, so the fix is not a blanket relabel."""
    products = [{"domain": "wholesale", "product": "invoice"},
                {"domain": "retail", "product": "invoice"}]
    _stats, log = _run_collisions(products,
                                  domains=[{"domain": "wholesale"}, {"domain": "retail"}])
    assert "in another domain" in log.text
    assert "SAME-DOMAIN duplicate" not in log.text


def test_two_identical_names_in_one_domain_cannot_both_survive():
    """v4.8.9 renamed the duplicate apart; v4.9.1 merges it away.

    Either outcome satisfies the invariant this test actually guards, which is that a
    domain never ships two products under one name. Asserting the rename specifically
    is what made this test fail on v4.9.1, even though v4.9.1 is the better fix: the
    rename left an attribute-less husk table behind (live: wholesale.invoice, 3 cols).
    """
    products = [{"domain": "wholesale", "product": "invoice"},
                {"domain": "wholesale", "product": "invoice"}]
    _run_collisions(products, domains=[{"domain": "wholesale"}])
    names = [p["product"] for p in products]
    assert len(names) == len(set(names)), (
        "a domain must not end up with two products sharing one name")


def test_version_is_489_or_later():
    assert_agent_version_at_least("4.8.9")
