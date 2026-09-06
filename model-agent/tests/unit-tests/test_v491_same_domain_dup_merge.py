"""v4.9.1 alias=dup-product-same-domain-merge.

Live evidence, coffee_roastery run 564741857926303 (v4.8.8). The shipped model.json carried
BOTH of these in the wholesale domain:

    wholesale_invoice    39 attributes, 4 FKs
    invoice               3 attributes, 2 FKs   <- husk, reported as a global silo

One entity, two tables, one of them empty. Three defects produced it and all three are
exercised here against the real notebook code:

  P1  _validate_product_name_collisions Pass 2 buckets duplicates by product NAME, so a pair
      in ONE domain takes the cross-domain branch and gets RENAMED apart. Attribute rows key
      by (domain, product), so the rename hauls every attribute onto the renamed product and
      leaves the original a PK-plus-FK husk. Same name + same domain is one entity: merge it.

  P2  The v4.8.9 gates detect the pair, but neither `duplicate_product_pair` nor
      `duplicate_product_name` was in the SelfFixer `_fixable` whitelist, so no repair
      channel existed (CLAUDE.md 12.4 step 2).

  P3  The architect proposed exactly the right merge and the immutable guard rejected it,
      because the LLM core-product pass had marked `invoice` protected. Two consecutive
      rejections tripped IMMUTABLE-EARLY-EXIT and the WHOLE review was discarded. Merging an
      entity into itself preserves it, so protection must not veto it.
"""
import re

import pytest

from notebook_source_util import (assert_agent_version_at_least, cell_containing,
                                  slice_function_source)

COLLISION_ANCHOR = "P0.74-COLLISION-CROSSDOMAIN"
IMMUT_ANCHOR = "IMMUTABLE VIOLATION: Cannot merge protected product"
FIXABLE_ANCHOR = "_fixable = {"


class _Log:
    def __init__(self):
        self.lines = []

    def _add(self, msg):
        self.lines.append(str(msg))

    info = warning = error = _add

    @property
    def text(self):
        return "\n".join(self.lines)


def _run_collisions(products, attributes=None, domains=None):
    """Run the real collision autofix over flat pipeline lists, nothing stubbed."""
    src = cell_containing(COLLISION_ANCHOR)
    ns = {"re": re}
    fns = ["_p074_qualified_rename", "_validate_product_name_collisions"]
    exec("\n\n".join(slice_function_source(f, src) for f in fns), ns)
    # deduplicate_attributes_in_place lives in an earlier cell; the merge path calls it.
    dedup_src = cell_containing("def deduplicate_attributes_in_place")
    exec(slice_function_source("deduplicate_attributes_in_place", dedup_src), ns)
    norm_src = cell_containing("def _v489_norm_entity")
    exec(slice_function_source("_v489_norm_entity", norm_src), ns)
    attributes = attributes if attributes is not None else []
    log = _Log()
    domains = domains or [{"domain": d} for d in
                          dict.fromkeys(p["domain"] for p in products)]
    stats = ns["_validate_product_name_collisions"](domains, products, attributes, log)
    return stats, log


def _duplicate_invoice_model():
    """The exact shape run 564741857926303 held when the collision pass ran: two products
    both named `invoice` in `wholesale`, with the attribute rows in one flat pool keyed by
    (domain, product) so they are indistinguishable between the two product dicts."""
    products = [
        {"domain": "wholesale", "product": "invoice", "table_name": "invoice",
         "primary_key": "invoice_id", "description": "Billing document issued to a cafe."},
        {"domain": "wholesale", "product": "invoice", "table_name": "invoice",
         "primary_key": "invoice_id", "description": ""},
        {"domain": "wholesale", "product": "cafe_account", "table_name": "cafe_account",
         "primary_key": "cafe_account_id", "description": "A wholesale customer."},
    ]
    attributes = [
        {"domain": "wholesale", "product": "invoice", "attribute": "invoice_id",
         "data_type": "BIGINT", "is_primary_key": True},
        {"domain": "wholesale", "product": "invoice", "attribute": "cafe_account_id",
         "data_type": "BIGINT", "foreign_key_to": "wholesale.cafe_account.cafe_account_id"},
        {"domain": "wholesale", "product": "invoice", "attribute": "invoice_total",
         "data_type": "DECIMAL(18,2)"},
        {"domain": "wholesale", "product": "cafe_account", "attribute": "cafe_account_id",
         "data_type": "BIGINT", "is_primary_key": True},
    ]
    return products, attributes


def _wholesale(products):
    return [p["product"] for p in products if p["domain"] == "wholesale"]


# --- P1: the merge itself -------------------------------------------------------------

def test_a_same_domain_duplicate_is_merged_not_renamed_apart():
    products, attributes = _duplicate_invoice_model()
    _run_collisions(products, attributes)
    assert sorted(_wholesale(products)) == ["cafe_account", "invoice"], (
        "the duplicate must collapse into one `invoice`; pre-v4.9.1 it was renamed to "
        "`wholesale_invoice` and BOTH products survived"
    )


def test_the_merge_is_counted_and_reported():
    products, attributes = _duplicate_invoice_model()
    stats, log = _run_collisions(products, attributes)
    assert stats.get("same_domain_merges") == 1
    assert "dup-product-same-domain-merge FIRED" in log.text


def test_the_merge_does_not_inflate_the_cross_domain_counter():
    """Counting a same-domain merge as a cross-domain rename is how the defect hid: the
    stats said 'qualified a duplicate' and nobody looked at which domain it landed in."""
    products, attributes = _duplicate_invoice_model()
    stats, _ = _run_collisions(products, attributes)
    assert stats["cross_domain_duplicates"] == 0


def test_no_attribute_row_is_stranded_by_the_merge():
    products, attributes = _duplicate_invoice_model()
    _run_collisions(products, attributes)
    live = {(p["domain"], p["product"]) for p in products}
    for a in attributes:
        assert (a["domain"], a["product"]) in live, (
            f"attribute {a['attribute']} points at a product that no longer exists"
        )


def test_the_surviving_product_keeps_every_attribute():
    products, attributes = _duplicate_invoice_model()
    _run_collisions(products, attributes)
    kept = sorted(a["attribute"] for a in attributes
                  if (a["domain"], a["product"]) == ("wholesale", "invoice"))
    assert kept == ["cafe_account_id", "invoice_id", "invoice_total"], (
        "the husk in production had only PK + FKs because the rename moved the rest away"
    )


def test_the_keeper_inherits_a_field_only_the_duplicate_had():
    products, attributes = _duplicate_invoice_model()
    products[0]["description"] = ""
    products[1]["description"] = "Billing document issued to a cafe."
    _run_collisions(products, attributes)
    survivor = next(p for p in products if p["product"] == "invoice")
    assert survivor["description"] == "Billing document issued to a cafe.", (
        "merging must not throw away the only populated copy of a field"
    )


def test_a_populated_keeper_field_is_not_overwritten_by_the_duplicate():
    products, attributes = _duplicate_invoice_model()
    products[1]["description"] = "A worse, later description."
    _run_collisions(products, attributes)
    survivor = next(p for p in products if p["product"] == "invoice")
    assert survivor["description"] == "Billing document issued to a cafe."


def test_nested_attributes_on_the_duplicate_are_unioned_onto_the_keeper():
    """Some stages carry attributes nested on the product dict as well as flat."""
    products, attributes = _duplicate_invoice_model()
    products[0]["attributes"] = [{"attribute": "invoice_id"}]
    products[1]["attributes"] = [{"attribute": "invoice_id"}, {"attribute": "due_date"}]
    _run_collisions(products, attributes)
    survivor = next(p for p in products if p["product"] == "invoice")
    names = sorted(a["attribute"] for a in survivor["attributes"])
    assert names == ["due_date", "invoice_id"], "union by name, no duplicate carried over"


def test_three_copies_of_one_entity_collapse_to_one():
    products, attributes = _duplicate_invoice_model()
    products.insert(2, {"domain": "wholesale", "product": "invoice",
                        "table_name": "invoice", "primary_key": "invoice_id",
                        "description": ""})
    stats, _ = _run_collisions(products, attributes)
    assert _wholesale(products).count("invoice") == 1
    assert stats["same_domain_merges"] == 2


def test_duplicate_attribute_rows_are_collapsed_after_the_merge():
    products, attributes = _duplicate_invoice_model()
    attributes.append({"domain": "wholesale", "product": "invoice",
                       "attribute": "invoice_total", "data_type": "DECIMAL(18,2)"})
    _run_collisions(products, attributes)
    totals = [a for a in attributes if a["attribute"] == "invoice_total"]
    assert len(totals) == 1, "the flat pool must not keep two rows for one column"


def test_an_fk_pointing_at_the_merged_entity_still_resolves():
    products, attributes = _duplicate_invoice_model()
    attributes.append({"domain": "wholesale", "product": "cafe_account",
                       "attribute": "latest_invoice_id", "data_type": "BIGINT",
                       "foreign_key_to": "wholesale.invoice.invoice_id"})
    _run_collisions(products, attributes)
    fk = next(a for a in attributes if a["attribute"] == "latest_invoice_id")
    live = {f"{p['domain']}.{p['product']}" for p in products}
    assert fk["foreign_key_to"].rsplit(".", 1)[0] in live


# --- P1 negative controls: cross-domain behaviour must not change ---------------------

def test_a_cross_domain_duplicate_is_still_renamed_not_merged():
    products = [
        {"domain": "wholesale", "product": "invoice", "primary_key": "invoice_id"},
        {"domain": "retail", "product": "invoice", "primary_key": "invoice_id"},
    ]
    stats, _ = _run_collisions(products)
    assert len(products) == 2, "two domains own two distinct entities; never merge them"
    assert stats["cross_domain_duplicates"] == 1
    assert stats.get("same_domain_merges", 0) == 0


def test_a_product_colliding_with_a_domain_name_is_still_renamed():
    products = [
        {"domain": "wholesale", "product": "retail", "primary_key": "retail_id"},
        {"domain": "retail", "product": "store", "primary_key": "store_id"},
    ]
    stats, _ = _run_collisions(products)
    assert stats["renamed_domain_collisions"] == 1
    assert len(products) == 2


def test_a_model_with_no_duplicates_is_untouched():
    products = [
        {"domain": "wholesale", "product": "invoice", "primary_key": "invoice_id"},
        {"domain": "wholesale", "product": "delivery", "primary_key": "delivery_id"},
    ]
    before = [dict(p) for p in products]
    stats, _ = _run_collisions(products)
    assert products == before
    assert stats.get("same_domain_merges", 0) == 0


def test_the_merge_is_idempotent():
    products, attributes = _duplicate_invoice_model()
    _run_collisions(products, attributes)
    snapshot = [dict(p) for p in products]
    stats, _ = _run_collisions(products, attributes)
    assert products == snapshot
    assert stats.get("same_domain_merges", 0) == 0


# --- P2: the gate finding reaches the SelfFixer ---------------------------------------

@pytest.mark.parametrize("category", ["duplicate_product_pair", "duplicate_product_name"])
def test_the_duplicate_categories_are_repairable_by_the_selffixer(category):
    src = cell_containing(FIXABLE_ANCHOR)
    block = src[src.index(FIXABLE_ANCHOR):]
    block = block[:block.index("}") + 1]
    assert f"'{category}'" in block, (
        f"{category} is detected but not requeued, so nothing ever repairs it"
    )


# --- P3: protection stops vetoing a dedup ---------------------------------------------

def _run_merge_guard(sources, target, protected, domain="wholesale"):
    """Execute the real products_to_merge validation loop from the architect validator."""
    src = cell_containing(IMMUT_ANCHOR)
    start = src.index('        for pm in _coerce_list_of_dicts(data.get("products_to_merge"')
    end = src.index('        for ps in _coerce_list_of_dicts(data.get("products_to_split"')
    body = src[start:end]
    ns = {"re": re, "errors": [], "logger": _Log(),
          "_all_protected_products_lower": {p.lower() for p in protected},
          "_coerce_list_of_dicts": lambda v: [x for x in (v or []) if isinstance(x, dict)],
          "data": {"products_to_merge": [{"source_products": sources,
                                          "target_product": target,
                                          "domain": domain}]}}
    exec(slice_function_source("_v489_norm_entity",
                               cell_containing("def _v489_norm_entity")), ns)
    exec("if True:\n" + body, ns)
    return ns["errors"], ns["logger"]


def test_merging_an_entity_into_itself_is_allowed_even_when_protected():
    errors, log = _run_merge_guard(["invoice", "invoice"], "invoice",
                                   {"wholesale.invoice"})
    assert not [e for e in errors if "IMMUTABLE" in e], (
        "this is the live proposal that was rejected twice and cost the whole review"
    )
    assert "immutable-merge-same-entity-allowed FIRED" in log.text


def test_the_carve_out_is_separator_blind():
    errors, _ = _run_merge_guard(["wholesale_invoice"], "WholesaleInvoice",
                                 {"wholesale.wholesale_invoice"})
    assert not [e for e in errors if "IMMUTABLE" in e]


def test_merging_a_protected_entity_into_a_DIFFERENT_one_is_still_blocked():
    """The carve-out must not become a hole: folding `invoice` into `payment` really does
    delete the protected entity, and that stays forbidden."""
    errors, _ = _run_merge_guard(["invoice", "payment"], "payment", {"wholesale.invoice"})
    assert any("Cannot merge protected product 'wholesale.invoice'" in e for e in errors)


def test_an_unprotected_source_is_unaffected_by_the_carve_out():
    errors, _ = _run_merge_guard(["credit_memo", "payment"], "payment",
                                 {"wholesale.invoice"})
    assert not [e for e in errors if "IMMUTABLE" in e]


def test_a_merge_with_an_empty_target_still_blocks_a_protected_source():
    errors, _ = _run_merge_guard(["invoice", "payment"], "", {"wholesale.invoice"})
    assert any("Cannot merge protected product" in e for e in errors)


# --- version ---------------------------------------------------------------------------

def test_the_running_version_is_491_or_later():
    assert_agent_version_at_least("4.9.1")
