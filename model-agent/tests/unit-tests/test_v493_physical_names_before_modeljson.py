"""v4.9.3 - model.json must carry the SAME column names the DDL creates.

Live defect (coffee_roastery, agent v4.9.1, catalog vibe_e2e_v491):

    14:14:30  model.json written
    14:14:37  [bare-name-fix-json-sync FIRED]  4 renamed attrs
    14:14:38  [DDL PRE-FIX] Fixed 8 FK column/reference mismatches

Both renames landed after serialization, so the shipped contract advertised 12
columns that no physical table had. Verified against the artifacts on the volume:

    model.json                              physical DDL
    wholesale.order_line.sales_order_id     order_id
    wholesale.shipment.wholesale_order_id   order_id
    roasting.roast_batch.operator_id        roast_operator_id
    retail.store.code / .name               store_code / store_name        (+ 6 more)

Anyone generating SQL from model.json got 12 UNRESOLVED_COLUMN failures.
"""
import re

import pytest

from notebook_source_util import (
    assert_agent_version_at_least,
    exec_function_namespace,
    notebook_concat_source,
    slice_function_source,
)

ALIGN = "_v493_align_fk_column_names_to_parent_pk"
RESOLVE = "_v493_resolve_physical_column_names"


def _align():
    """The FK-column aligner, executable in isolation."""
    from collections import defaultdict

    ns = exec_function_namespace(
        ALIGN,
        extra_globals={
            "defaultdict": defaultdict,
            "apply_convention": lambda name, conv: name,
        },
    )
    return ns[ALIGN]


def _attr(domain, product, name, fk="", **kw):
    a = {
        "domain": domain,
        "product": product,
        "attribute": name,
        "column_name": name,
        "foreign_key_to": fk,
        "type": "BIGINT",
    }
    a.update(kw)
    return a


def _product(domain, name, pk):
    return {"domain": domain, "product": name, "primary_key": pk, "table_name": name}


# --------------------------------------------------------------------------- live repro
def test_a_well_formed_labeled_fk_is_preserved_not_bare_renamed():
    """v4.9.4: sales_order_id already ends with the parent PK order_id, so it is a valid
    role-labeled FK and must be left alone. Bare-renaming it to order_id both destroys the
    label and (when two FKs share a parent) triggers the order-dependent collision relabel
    that drifted model.json vs the DDL."""
    products = [
        _product("wholesale", "order", "order_id"),
        _product("wholesale", "order_line", "order_line_id"),
    ]
    attributes = [
        _attr("wholesale", "order", "order_id"),
        _attr("wholesale", "order_line", "order_line_id"),
        _attr("wholesale", "order_line", "sales_order_id", "wholesale.order.order_id"),
    ]

    _align()(products, attributes, {}, None)

    fk = next(a for a in attributes if a["product"] == "order_line" and a.get("foreign_key_to"))
    assert fk["attribute"] == "sales_order_id", (
        "the well-formed labeled FK was renamed away: %r" % fk["attribute"]
    )
    assert fk["column_name"] == fk["attribute"], "column_name drifted from attribute"
    assert fk["foreign_key_to"] == "wholesale.order.order_id"


def test_column_name_moves_with_attribute():
    """A rename that updates `attribute` but not `column_name` re-creates the v4.8.7 bug."""
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
    assert fk["attribute"] == "roast_operator_id"
    assert fk["column_name"] == fk["attribute"], (
        "column_name drifted from attribute: %r vs %r" % (fk["column_name"], fk["attribute"])
    )


# --------------------------------------------------------------------------- idempotence
def test_running_it_twice_changes_nothing_the_second_time():
    """The DDL stage still calls this after the serialization boundary did. It must no-op."""
    products = [
        _product("wholesale", "order", "order_id"),
        _product("wholesale", "shipment", "shipment_id"),
    ]
    attributes = [
        _attr("wholesale", "order", "order_id"),
        _attr("wholesale", "shipment", "shipment_id"),
        # malformed: does NOT end with the parent PK order_id, so the first pass must align it
        # (a well-formed labeled FK like wholesale_order_id is preserved from v4.9.4 on).
        _attr("wholesale", "shipment", "ord_ref", "wholesale.order.order_id"),
    ]
    align = _align()

    first = align(products, attributes, {}, None)
    snapshot = [dict(a) for a in attributes]
    second = align(products, attributes, {}, None)

    assert first >= 1, "the first pass should have had work to do"
    assert second == 0, "second pass reported %d fixes - not idempotent" % second
    assert attributes == snapshot, "second pass mutated the model"


def test_an_already_aligned_column_is_left_alone():
    """Negative control: nothing to fix means zero fixes and zero mutation."""
    products = [
        _product("sourcing", "cooperative", "cooperative_id"),
        _product("sourcing", "purchase_order", "purchase_order_id"),
    ]
    attributes = [
        _attr("sourcing", "cooperative", "cooperative_id"),
        _attr("sourcing", "purchase_order", "purchase_order_id"),
        _attr("sourcing", "purchase_order", "cooperative_id", "sourcing.cooperative.cooperative_id"),
    ]
    before = [dict(a) for a in attributes]

    assert _align()(products, attributes, {}, None) == 0
    assert attributes == before


# --------------------------------------------------------------------------- collisions
def test_two_fks_to_the_same_parent_do_not_collapse_into_one_column():
    """Both FKs want `store_id`. Renaming both would emit a duplicate column in the DDL."""
    products = [
        _product("retail", "store", "store_id"),
        _product("retail", "transfer", "transfer_id"),
    ]
    attributes = [
        _attr("retail", "store", "store_id"),
        _attr("retail", "transfer", "transfer_id"),
        _attr("retail", "transfer", "origin_store_id", "retail.store.store_id"),
        _attr("retail", "transfer", "destination_store_id", "retail.store.store_id"),
    ]

    _align()(products, attributes, {}, None)

    cols = [a["column_name"] for a in attributes if a["product"] == "transfer"]
    assert len(cols) == len(set(cols)), "duplicate column names produced: %r" % (cols,)


def test_a_rename_onto_an_existing_column_is_refused():
    """The target name is already taken by a real column, so the FK keeps its own name."""
    products = [
        _product("retail", "store", "store_id"),
        _product("retail", "visit", "visit_id"),
    ]
    attributes = [
        _attr("retail", "store", "store_id"),
        _attr("retail", "visit", "visit_id"),
        _attr("retail", "visit", "store_id", type="STRING"),
        _attr("retail", "visit", "home_store_id", "retail.store.store_id"),
    ]

    _align()(products, attributes, {}, None)

    cols = [a["column_name"] for a in attributes if a["product"] == "visit"]
    assert len(cols) == len(set(cols)), "collided with the pre-existing column: %r" % (cols,)


# --------------------------------------------------------------------------- fk target repair
def test_a_stale_fk_target_pk_is_corrected():
    """foreign_key_to naming the wrong PK is repointed at the real one."""
    products = [
        _product("roasting", "post_roast_qc", "post_roast_qc_id"),
        _product("roasting", "finished_package", "finished_package_id"),
    ]
    attributes = [
        _attr("roasting", "post_roast_qc", "post_roast_qc_id"),
        _attr("roasting", "finished_package", "finished_package_id"),
        _attr("roasting", "finished_package", "releasing_post_roast_qc_id",
              "roasting.post_roast_qc.qc_id"),
    ]

    _align()(products, attributes, {}, None)

    fk = next(a for a in attributes if a["attribute"].endswith("post_roast_qc_id")
              and a["product"] == "finished_package")
    assert fk["foreign_key_to"] == "roasting.post_roast_qc.post_roast_qc_id"


def test_an_attribute_with_no_fk_is_never_renamed():
    products = [_product("retail", "store", "store_id")]
    attributes = [
        _attr("retail", "store", "store_id"),
        _attr("retail", "store", "city", type="STRING"),
    ]
    before = [dict(a) for a in attributes]

    assert _align()(products, attributes, {}, None) == 0
    assert attributes == before


# --------------------------------------------------------------------------- wiring
def test_the_resolver_runs_before_the_export_copies_are_taken():
    """If it runs after products_for_export is built, model.json ships the stale names."""
    src = slice_function_source("step_generate_data_model_json")
    call = src.index(RESOLVE)
    copy = src.index("products_for_export = [dict(p)")
    assert call < copy, (
        "%s is invoked at %d, after the export snapshot at %d - the shipped "
        "model.json would still carry pre-rename names" % (RESOLVE, call, copy)
    )


def test_the_resolver_covers_both_rename_passes():
    """Bare-name renames and FK-column renames both have to happen before serialization."""
    src = slice_function_source(RESOLVE)
    assert "_fix_bare_attribute_names" in src, "the 4 bare-name renames are still late"
    assert ALIGN in src, "the 8 FK-column renames are still late"


def test_the_resolver_writes_the_attributes_back_onto_widgets():
    src = slice_function_source(RESOLVE)
    assert re.search(r'widgets_values\[\s*["\']attributes["\']\s*\]\s*=', src), (
        "the mutated list is never published back, so downstream stages read the old one"
    )


def test_the_ddl_stage_no_longer_carries_its_own_copy_of_the_logic():
    """Two implementations of the same rename is how model.json and the DDL diverged."""
    ddl = slice_function_source("step_create_physical_schema_stage1")
    assert ALIGN in ddl, "the DDL stage must still run the backstop"
    assert "pk_lookup = {}" not in ddl, "the inline duplicate survived in the DDL stage"
    assert "_product_col_index = defaultdict(set)" not in ddl, (
        "the inline duplicate survived in the DDL stage"
    )


def test_the_helper_is_defined_once():
    src = notebook_concat_source()
    assert src.count("def %s(" % ALIGN) == 1
    assert src.count("def %s(" % RESOLVE) == 1


def test_the_fired_line_reports_both_counts():
    """A log line with no numbers cannot prove the pass did anything."""
    src = slice_function_source(RESOLVE)
    assert "v493-physical-names-before-modeljson FIRED" in src
    assert "bare_renames" in src and "fk_col_fixes" in src


def test_a_failing_pass_cannot_abort_serialization():
    """model.json must still be written even if a rename pass raises."""
    src = slice_function_source(RESOLVE)
    assert src.count("except Exception") >= 2, (
        "an unguarded rename pass would take the whole model.json write down with it"
    )


def test_version_is_493_or_later():
    assert_agent_version_at_least("4.9.3")
