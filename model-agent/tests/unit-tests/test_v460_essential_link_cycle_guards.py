import re
from collections import defaultdict

from notebook_source_util import (
    agent_version_line,
    exec_function_namespace,
    exec_functions_namespace,
    notebook_concat_source,
    slice_function_source,
)


class Logger:
    def __init__(self):
        self.lines = []

    def info(self, message):
        self.lines.append(message)

    def warning(self, message):
        self.lines.append(message)


def _bidirectional(source_domain, source_product, target_domain, target_product, attrs):
    target_key = f"{target_domain}.{target_product}".lower()
    source_key = f"{source_domain}.{source_product}".lower()
    for attr in attrs:
        attr_key = f"{attr.get('domain', '')}.{attr.get('product', '')}".lower()
        target = str(attr.get("foreign_key_to") or "").lower()
        if attr_key == target_key and target.startswith(f"{source_key}."):
            return True, attr.get("attribute", "")
    return False, ""


def _load_essential(cycle=False):
    return exec_functions_namespace(
        ["_v458_assign_fk_if_acyclic", "_apply_architect_essential_links"],
        {
            "re": re,
            "_would_create_cycle": lambda *args, **kwargs: cycle,
            "_would_create_bidirectional_fk": _bidirectional,
            "sanitize_attribute_type": lambda attr: attr,
        },
    )["_apply_architect_essential_links"]


def _link(source_domain, source_product, source_attribute, target_domain, target_product):
    return {
        "source_domain": source_domain,
        "source_product": source_product,
        "source_attribute": source_attribute,
        "target_domain": target_domain,
        "target_product": target_product,
        "target_attribute": f"{target_product}_id",
    }


def test_reverse_edge_blocks_essential_new_column_without_stub():
    reverse = {
        "domain": "inventory",
        "product": "stock_level",
        "attribute": "menu_item_id",
        "foreign_key_to": "sales.menu_item.menu_item_id",
    }
    widgets = {
        "attributes": [reverse],
        "products": [],
        "_architect_essential_links": [
            _link(
                "sales",
                "menu_item",
                "stock_level_id",
                "inventory",
                "stock_level",
            )
        ],
    }
    logger = Logger()

    _load_essential()(widgets, logger)

    assert widgets["attributes"] == [reverse]
    assert widgets["_architect_essential_links_applied"] == 0
    assert any(
        "[essential-link-cycle-skip FIRED v4.6.0]" in line
        and "blocked=bidirectional" in line
        for line in logger.lines
    )


def test_acyclic_essential_new_and_existing_columns_are_retained():
    existing = {
        "domain": "sales",
        "product": "order",
        "attribute": "customer_id",
    }
    widgets = {
        "attributes": [existing],
        "products": [],
        "_architect_essential_links": [
            _link("sales", "order", "customer_id", "customer", "customer"),
            _link("sales", "order", "channel_id", "reference", "channel"),
        ],
    }

    _load_essential()(widgets, Logger())

    assert existing["foreign_key_to"] == "customer.customer.customer_id"
    created = next(
        attr for attr in widgets["attributes"] if attr["attribute"] == "channel_id"
    )
    assert created["foreign_key_to"] == "reference.channel.channel_id"
    assert widgets["_architect_essential_links_applied"] == 2


def test_dynamic_only_fk_is_not_explicit_user_vibed():
    check = exec_function_namespace("_v460_is_explicit_user_vibed_fk")[
        "_v460_is_explicit_user_vibed_fk"
    ]
    attr = {
        "domain": "sales",
        "product": "menu_item",
        "attribute": "stock_level_id",
        "foreign_key_to": "inventory.stock_level.stock_level_id",
        "_dynamically_created": True,
    }
    logger = Logger()

    assert check(
        attr,
        "sales.menu_item.stock_level_id->inventory.stock_level.stock_level_id",
        "sales.menu_item.stock_level_id",
        set(),
        set(),
        logger,
    ) is False
    assert any(
        "[dynamic-fk-protection-rejected FIRED v4.6.0]" in line
        for line in logger.lines
    )
    assert check(
        attr,
        "sales.menu_item.stock_level_id->inventory.stock_level.stock_level_id",
        "sales.menu_item.stock_level_id",
        set(),
        {"sales.menu_item.stock_level_id"},
        Logger(),
    ) is True


def test_post_normalization_writer_blocks_cycle_through_shared_guard():
    namespace = exec_functions_namespace(
        [
            "_v458_assign_fk_if_acyclic",
            "_post_normalization_deterministic_fk_linker",
        ],
        {
            "get_pk_suffix": lambda config: "_id",
            "build_pk_map": lambda products, config: {
                "alpha.child": "child_id",
                "beta.parent": "parent_id",
            },
            "_build_fk_adjacency": lambda attrs: {},
            "_is_pk_pattern": lambda *args, **kwargs: False,
            "extract_fk_base_name": lambda name, config: name.removesuffix("_id"),
            "_is_system_identifier_column": lambda *args, **kwargs: False,
            "_is_hierarchical_self_ref": lambda *args, **kwargs: False,
            "_would_create_cycle": lambda *args, **kwargs: True,
            "_would_create_bidirectional_fk": lambda *args, **kwargs: (False, ""),
            "_sync_fk_type_with_pk": lambda *args, **kwargs: None,
        },
    )
    attr = {
        "domain": "alpha",
        "product": "child",
        "attribute": "parent_id",
        "tags": "",
    }
    logger = Logger()

    linked = namespace["_post_normalization_deterministic_fk_linker"](
        [], [], [attr], {}, logger
    )

    assert linked == 0
    assert "foreign_key_to" not in attr
    assert any(
        "[post-normalization-cycle-skip FIRED v4.6.0]" in line
        for line in logger.lines
    )


def test_post_qa_isolation_and_missing_column_writers_block_cycles_without_stubs():
    class Validator:
        def __init__(self, logger, config):
            self.calls = 0

        def validate_domain_isolation(self, domains, products, attributes):
            self.calls += 1
            if self.calls == 1:
                return False, ["Domain 'isolated' is completely isolated"]
            return True, []

    namespace = exec_functions_namespace(
        ["_v458_assign_fk_if_acyclic", "_run_post_linking_fk_validations"],
        {
            "re": re,
            "defaultdict": defaultdict,
            "validate_and_fix_all_fk_references": lambda *args: (True, [], []),
            "SmartWorkerValidator": Validator,
            "build_pk_map": lambda *args, **kwargs: {
                "target": ("connected", "target", "target_id")
            },
            "is_potential_fk_column": lambda *args: True,
            "extract_fk_base_name": lambda name, config: "target",
            "build_product_keys_set": lambda products: {
                "isolated.source",
                "connected.target",
            },
            "parse_fk_reference": lambda value: tuple(value.split(".", 2)),
            "make_attribute_dict": lambda business, domain, product, attribute, **kw: {
                "domain": domain,
                "product": product,
                "attribute": attribute,
                "column_name": kw.get("column_name", attribute),
                "foreign_key_to": kw.get("fk_to", ""),
            },
            "apply_convention": lambda value, convention: value,
            "_would_create_cycle": lambda *args, **kwargs: True,
            "_would_create_bidirectional_fk": lambda *args, **kwargs: (False, ""),
        },
    )
    attributes = [
        {
            "domain": "isolated",
            "product": "source",
            "attribute": "target_id",
            "column_name": "target_id",
        }
    ]
    products = [
        {
            "domain": "isolated",
            "product": "source",
            "foreign_keys": [
                {
                    "attribute": "missing_target_id",
                    "foreign_key_to": "connected.target.target_id",
                }
            ],
        },
        {"domain": "connected", "product": "target"},
    ]
    logger = Logger()

    namespace["_run_post_linking_fk_validations"](
        [{"domain": "isolated"}, {"domain": "connected"}],
        products,
        attributes,
        "business",
        {},
        logger,
    )

    assert attributes == [
        {
            "domain": "isolated",
            "product": "source",
            "attribute": "target_id",
            "column_name": "target_id",
        }
    ]
    assert any(
        "[post-qa-isolation-cycle-skip FIRED v4.6.0]" in line
        for line in logger.lines
    )
    assert any(
        "[post-qa-missing-column-cycle-skip FIRED v4.6.0]" in line
        for line in logger.lines
    )


def test_post_clean_new_edge_writers_use_shared_guard():
    essential = slice_function_source("_apply_architect_essential_links")
    post_normalization = slice_function_source(
        "_post_normalization_deterministic_fk_linker"
    )
    post_linking = slice_function_source("_run_post_linking_fk_validations")
    autofix = slice_function_source("_pre_static_analysis_autofix")

    assert essential.count("_v458_assign_fk_if_acyclic(") == 2
    assert "essential-link-cycle-skip" in essential
    assert "['foreign_key_to'] =" not in essential
    assert "'foreign_key_to': _fk_target_str" not in essential

    assert "post-normalization-cycle-skip" in post_normalization
    assert "attr['foreign_key_to'] =" not in post_normalization

    assert "post-qa-isolation-cycle-skip" in post_linking
    assert "post-qa-missing-column-cycle-skip" in post_linking
    assert post_linking.count("_v458_assign_fk_if_acyclic(") == 2
    assert "attr['foreign_key_to'] =" not in post_linking
    assert "fk_to=fk_to" not in post_linking

    assert "post-qa-autofix-cycle-skip" in autofix
    assert "_a['foreign_key_to'] = f\"{_chosen[0]}" not in autofix


def test_version_is_v460_and_first_code_statement():
    source = notebook_concat_source()
    assert agent_version_line() in source
    first_code_cell = source.lstrip().splitlines()[0]
    assert first_code_cell == agent_version_line()
