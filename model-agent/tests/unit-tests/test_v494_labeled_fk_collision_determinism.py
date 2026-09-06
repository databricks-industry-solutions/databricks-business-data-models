"""v4.9.4 - two FKs to the same parent must name deterministically across call-sites.

Live residual (coffee_roastery v4.9.3, catalog vibe_e2e_v493):
  retail.pos_transaction had two FKs to retail.shopper.shopper_id. The SelfFixer
  multi_fk_missing_label pass relabeled one of them BETWEEN the model.json serialization
  boundary and the DDL stage. Because the aligner tried to bare-rename a well-formed
  labeled column and fell into an order-dependent collision relabel, the two call-sites
  resolved the names differently:
      model.json : {cashier_shopper_id, shopper_id}
      DDL        : {shopper_id, customer_shopper_id}
  -> 1 broken column reference of 930.

The v4.9.4 guard preserves any column already ending with '_<parent_pk>', so labeled FKs
are never touched and the result is identical no matter what ran in between.
"""
from collections import defaultdict

from notebook_source_util import (
    assert_agent_version_at_least,
    exec_function_namespace,
    slice_function_source,
)

ALIGN = "_v493_align_fk_column_names_to_parent_pk"


def _align():
    ns = exec_function_namespace(
        ALIGN,
        extra_globals={"defaultdict": defaultdict, "apply_convention": lambda n, c: n},
    )
    return ns[ALIGN]


def _attr(domain, product, name, fk="", **kw):
    a = {"domain": domain, "product": product, "attribute": name,
         "column_name": name, "foreign_key_to": fk, "type": "BIGINT"}
    a.update(kw)
    return a


def _product(domain, name, pk):
    return {"domain": domain, "product": name, "primary_key": pk, "table_name": name}


def _shopper_model():
    products = [
        _product("retail", "shopper", "shopper_id"),
        _product("retail", "pos_transaction", "pos_transaction_id"),
    ]
    attributes = [
        _attr("retail", "shopper", "shopper_id"),
        _attr("retail", "pos_transaction", "pos_transaction_id"),
        _attr("retail", "pos_transaction", "cashier_shopper_id", "retail.shopper.shopper_id"),
        _attr("retail", "pos_transaction", "customer_shopper_id", "retail.shopper.shopper_id"),
    ]
    return products, attributes


def test_both_labeled_shopper_fks_are_preserved():
    products, attributes = _shopper_model()

    _align()(products, attributes, {}, None)

    pt = [a for a in attributes if a["product"] == "pos_transaction" and a.get("foreign_key_to")]
    names = sorted(a["attribute"] for a in pt)
    assert names == ["cashier_shopper_id", "customer_shopper_id"], (
        "labeled FKs were mangled: %r" % names
    )
    for a in pt:
        assert a["column_name"] == a["attribute"]
        assert a["foreign_key_to"] == "retail.shopper.shopper_id"


def test_no_two_columns_collapse_to_the_same_name():
    products, attributes = _shopper_model()
    _align()(products, attributes, {}, None)
    cols = [a["column_name"] for a in attributes if a["product"] == "pos_transaction"]
    assert len(cols) == len(set(cols)), "collision produced duplicate columns: %r" % cols


def test_each_labeled_fk_keeps_its_own_name_regardless_of_order():
    """The live drift was a per-column disagreement, not a set disagreement: model.json kept
    cashier_shopper_id while the DDL produced customer_shopper_id for the same FK. A sorted-set
    check hides that (the aligner is symmetric on the set), so we assert that a labeled FK's
    (foreign_key_to -> column_name) mapping is identical no matter what order the attributes are
    processed in. Pre-patch the aligner mangles one label to shopper_shopper_id / bare shopper_id
    depending on order, so the two mappings disagree."""
    align = _align()

    def mapping(order):
        products = [
            _product("retail", "shopper", "shopper_id"),
            _product("retail", "pos_transaction", "pos_transaction_id"),
        ]
        base = {
            "cashier": _attr("retail", "pos_transaction", "cashier_shopper_id", "retail.shopper.shopper_id"),
            "customer": _attr("retail", "pos_transaction", "customer_shopper_id", "retail.shopper.shopper_id"),
        }
        attrs = [
            _attr("retail", "shopper", "shopper_id"),
            _attr("retail", "pos_transaction", "pos_transaction_id"),
        ] + [base[k] for k in order]
        align(products, attrs, {}, None)
        # map the original role (via its description-free identity) to the final column name
        return {order[0]: attrs[2]["column_name"], order[1]: attrs[3]["column_name"]}

    forward = mapping(("cashier", "customer"))
    reverse = mapping(("customer", "cashier"))
    assert forward == reverse, (
        "the same FK gets different physical names depending on processing order "
        "-> model.json/DDL drift: %r vs %r" % (forward, reverse)
    )
    assert forward["cashier"] == "cashier_shopper_id"
    assert forward["customer"] == "customer_shopper_id"


def test_a_genuinely_malformed_fk_is_still_aligned():
    """The guard must not stop legitimate fixes: operator_id does NOT end with the parent
    PK roast_operator_id, so it is malformed and must be aligned."""
    products = [
        _product("roasting", "roast_operator", "roast_operator_id"),
        _product("roasting", "roast_batch", "roast_batch_id"),
    ]
    attributes = [
        _attr("roasting", "roast_operator", "roast_operator_id"),
        _attr("roasting", "roast_batch", "operator_id", "roasting.roast_operator.roast_operator_id"),
    ]
    _align()(products, attributes, {}, None)
    fk = next(a for a in attributes if a["product"] == "roast_batch" and a.get("foreign_key_to"))
    assert fk["attribute"] == "roast_operator_id", (
        "a malformed FK was left unaligned: %r" % fk["attribute"]
    )


def test_running_it_twice_is_a_no_op():
    products, attributes = _shopper_model()
    align = _align()
    align(products, attributes, {}, None)
    snap = [dict(a) for a in attributes]
    second = align(products, attributes, {}, None)
    assert second == 0
    assert attributes == snap


def test_the_guard_is_in_the_helper_source():
    src = slice_function_source(ALIGN)
    assert "endswith('_' + actual_pk)" in src, "the preservation guard is missing"
    assert "v494-preserve-labeled-fk FIRED" in src, "no observable FIRED line for the fix"


def test_version_is_494_or_later():
    assert_agent_version_at_least("4.9.4")
