import ast
import json
import re

from notebook_source_util import (
    agent_version_line,
    exec_function_namespace as _exec_function_namespace,
    exec_functions_namespace as _exec_functions_namespace,
    notebook_concat_source,
    slice_function_source as _slice_function_source,
)

SOURCE = notebook_concat_source()


def slice_function_source(function_name):
    return _slice_function_source(function_name, source=SOURCE)


def exec_function_namespace(function_name, extra_globals=None):
    return _exec_function_namespace(
        function_name,
        extra_globals=extra_globals,
        source=SOURCE,
    )


def exec_functions_namespace(function_names, extra_globals=None):
    return _exec_functions_namespace(
        function_names,
        extra_globals=extra_globals,
        source=SOURCE,
    )


class Logger:
    def __init__(self):
        self.records = []

    def debug(self, message):
        self.records.append(("DEBUG", str(message)))

    def info(self, message):
        self.records.append(("INFO", str(message)))

    def warning(self, message):
        self.records.append(("WARNING", str(message)))

    def error(self, message):
        self.records.append(("ERROR", str(message)))


def _cycle_namespace():
    return exec_functions_namespace(
        [
            "_build_fk_adjacency",
            "_would_create_cycle",
            "_v458_assign_fk_if_acyclic",
        ],
        {
            "_disk_cached_call": lambda name, key, compute: compute(),
            "_would_create_bidirectional_fk": lambda *args, **kwargs: (False, ""),
        },
    )


def _four_hop_attributes():
    return [
        {
            "domain": "inventory",
            "product": "stock_item",
            "attribute": "menu_item_id",
            "foreign_key_to": "product.menu_item.menu_item_id",
        },
        {
            "domain": "product",
            "product": "menu_item",
            "attribute": "price_tier_id",
            "foreign_key_to": "product.price_tier.price_tier_id",
        },
        {
            "domain": "product",
            "product": "price_tier",
            "attribute": "reward_campaign_id",
            "foreign_key_to": "loyalty.reward_campaign.reward_campaign_id",
        },
    ]


def test_cycle_guard_blocks_live_four_hop_closer_and_admits_negative_control():
    ns = _cycle_namespace()
    attrs = _four_hop_attributes()
    logger = Logger()
    closer = {
        "domain": "loyalty",
        "product": "reward_campaign",
        "attribute": "stock_item_id",
    }
    cache = ns["_build_fk_adjacency"](attrs)
    assert not ns["_v458_assign_fk_if_acyclic"](
        closer,
        "inventory.stock_item.stock_item_id",
        attrs,
        logger,
        "pairwise-cycle-skip",
        _adj_cache=cache,
        alias_version="4.6.3",
    )
    assert "foreign_key_to" not in closer
    assert any(
        "[pairwise-cycle-skip FIRED v4.6.3]" in message
        for _, message in logger.records
    )

    acyclic = {
        "domain": "loyalty",
        "product": "reward_campaign",
        "attribute": "region_id",
    }
    assert ns["_v458_assign_fk_if_acyclic"](
        acyclic,
        "shared.region.region_id",
        attrs,
        logger,
        "pairwise-cycle-skip",
        _adj_cache=cache,
        alias_version="4.6.3",
    )
    assert acyclic["foreign_key_to"] == "shared.region.region_id"


def test_all_primary_llm_fk_writers_route_admissions_through_shared_guard():
    expectations = {
        "_run_in_domain_linking_smart_worker": "in-domain-cycle-skip",
        "_run_cross_domain_linking_smart_worker": "cross-domain-cycle-skip",
        "run_pairwise_cross_domain_linking": "pairwise-cycle-skip",
    }
    for function_name, alias in expectations.items():
        source = slice_function_source(function_name)
        assert alias in source
        assert "_v458_assign_fk_if_acyclic(" in source
        assert "_create_new_fk_attribute(" in source
        assert "['foreign_key_to'] = fk_target" not in source

    create_source = slice_function_source("_create_new_fk_attribute")
    assert create_source.count("_v458_assign_fk_if_acyclic(") == 2
    assert "['foreign_key_to'] = fk_target" not in create_source


def _nested_function(outer_name, nested_name, globals_map):
    tree = ast.parse(slice_function_source(outer_name))
    target = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == nested_name
    )
    module = ast.fix_missing_locations(ast.Module(body=[target], type_ignores=[]))
    namespace = dict(globals_map)
    exec(compile(module, "<nested-function>", "exec"), namespace)
    return namespace[nested_name]


def test_fmfl_postprocessor_unwraps_tuple_pk_and_sanitizes_only_invalid_links():
    logger = Logger()
    postprocess = _nested_function(
        "_run_find_missing_fk_links",
        "_fmfl_postprocessor",
        {
            "pk_map": {
                "catalog.item": ("catalog", "item", "item_id"),
                "item": ("catalog", "item", "item_id"),
            },
            "pk_suffix": "_id",
            "config": {},
            "_is_person_role_column": lambda column: False,
            "_is_non_person_table": lambda target: False,
            "_find_best_person_table": lambda: None,
            "_fmfl_normalise_target": lambda target: ".".join(
                str(target).split(".")[:2]
            ),
            "_fmfl_canonical_entities": {"catalog.item"},
        },
    )
    response = {
        "decisions": [
            {
                "table": "catalog.item",
                "column": "item_id",
                "decision": "LINK",
                "target_table": "missing.entity.entity_id",
                "reasoning": "",
            },
            {
                "table": "catalog.item",
                "column": "supplier_id",
                "decision": "LINK",
                "target_table": "missing.entity.entity_id",
                "reasoning": "",
            },
            {
                "table": "catalog.item",
                "column": "category_id",
                "decision": "LINK",
                "target_table": "catalog.item.item_id",
                "reasoning": "",
            },
        ],
        "summary": {},
    }
    result = postprocess(response, logger)
    assert result["decisions"][0]["decision"] == "KEEP_AS_IS"
    assert result["decisions"][1]["decision"] == "DROP"
    assert result["decisions"][2]["decision"] == "LINK"
    assert any(
        "[fmfl-pk-map-tuple-unwrapped FIRED v4.6.3]" in message
        for _, message in logger.records
    )


class Agent:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def run_worker(self, **kwargs):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def _smart_worker():
    return exec_function_namespace(
        "smart_worker_loop",
        {
            "json": json,
            "re": re,
            "normalize_llm_response_names": lambda value: value,
            "_strip_tags_from_prompt_vars": lambda values, logger: (values, 0),
        },
    )["smart_worker_loop"]


def _smart_call(agent, validator, postprocessor=None, max_retries=2):
    return _smart_worker()(
        ai_agent=agent,
        logger=Logger(),
        step_name="mutation-test",
        prompt_key="unused",
        prompt_vars={},
        response_schema={},
        validator_func=validator,
        config={"MAX_RETRIES": max_retries},
        max_retries=max_retries,
        response_postprocess_func=postprocessor,
    )


def test_smart_worker_preserves_validator_mutation_for_postprocessor_and_return():
    observed = {}

    def validator(value):
        value["decision"] = "KEEP_AS_IS"
        return True, []

    def postprocessor(value, logger):
        observed["decision"] = value["decision"]
        value["postprocessed"] = True
        return value

    agent = Agent(['{"decision":"LINK"}'])
    success, result, errors = _smart_call(agent, validator, postprocessor)
    assert success
    assert errors == []
    assert observed["decision"] == "KEEP_AS_IS"
    assert result == {"decision": "KEEP_AS_IS", "postprocessed": True}


def test_smart_worker_non_mutating_validator_is_unchanged_and_invalid_retries():
    success, result, errors = _smart_call(
        Agent(['{"decision":"LINK"}']),
        lambda value: (True, []),
    )
    assert success
    assert result == {"decision": "LINK"}
    assert errors == []

    invalid_agent = Agent(['{"decision":"LINK"}', '{"decision":"LINK"}'])
    success, result, errors = _smart_call(
        invalid_agent,
        lambda value: (False, ["invalid decision"]),
        max_retries=2,
    )
    assert not success
    assert invalid_agent.calls == 2
    assert errors == ["invalid decision"]


def test_post_create_sweep_skips_own_pk_without_blocking_external_or_labeled_self_refs():
    predicate = exec_function_namespace(
        "_v463_is_own_pk_for_created_table"
    )["_v463_is_own_pk_for_created_table"]
    supplier_pk = {
        "domain": "supplier",
        "product": "supplier",
        "attribute": "supplier_id",
        "is_primary_key": True,
    }
    grn_supplier = {
        "domain": "inventory",
        "product": "goods_receipt",
        "attribute": "supplier_id",
    }
    parent_category = {
        "domain": "product",
        "product": "category",
        "attribute": "parent_category_id",
    }
    assert predicate(supplier_pk, "supplier", "supplier", "supplier_id")
    assert not predicate(grn_supplier, "supplier", "supplier", "supplier_id")
    assert not predicate(parent_category, "product", "category", "category_id")
    source = slice_function_source("_run_find_missing_fk_links")
    assert "[create-sweep-own-pk-skip FIRED v4.6.3]" in source
    assert "_v463_is_own_pk_for_created_table(" in source


def _verification_function():
    return exec_function_namespace(
        "_post_normalization_verification",
        {
            "get_pk_suffix": lambda config: "_id",
            "build_pk_map": lambda products, config: {
                f"{p['domain']}.{p['product']}": p["primary_key"]
                for p in products
            },
            "_is_pk_pattern": lambda *args, **kwargs: False,
            "extract_fk_base_name": lambda name, config: name[:-3],
            "_is_system_identifier_column": lambda *args, **kwargs: False,
        },
    )["_post_normalization_verification"]


def test_unlinked_ids_are_info_before_fmfl_and_warning_after_fmfl():
    verify = _verification_function()
    products = [
        {
            "domain": "inventory",
            "product": "receipt",
            "primary_key": "receipt_id",
        }
    ]
    attrs = [
        {
            "domain": "inventory",
            "product": "receipt",
            "attribute": "supplier_id",
            "tags": "",
        }
    ]
    pre_logger = Logger()
    assert verify(attrs, products, {}, pre_logger) == 1
    assert not any(level == "WARNING" for level, _ in pre_logger.records)
    assert any(
        "[pre-fmfl-unlinked-progress FIRED v4.6.3]" in message
        for _, message in pre_logger.records
    )

    post_logger = Logger()
    assert verify(attrs, products, {}, post_logger, post_fmfl=True) == 1
    assert any(
        level == "WARNING"
        and "[post-fmfl-unlinked-residual FIRED v4.6.3]" in message
        for level, message in post_logger.records
    )


def _domain_apply_namespace():
    return exec_functions_namespace(
        [
            "_coerce_dict",
            "_coerce_list_of_dicts",
            "_gate_is_pass",
            "_normalize_gate_hierarchy",
            "_tier_aware_architect_gate_keys",
            "_apply_single_domain_review_to_model",
        ],
        {
            "json": json,
            "re": re,
            "sanitize_name": lambda value: str(value or "").strip().lower(),
            "_GATE_ORDER": (
                "trust_in_production",
                "support_in_production",
                "recommend_to_industry_peers",
                "propose_for_global_standard",
            ),
        },
    )


def _gate_response(trust="yes", support="yes", recommend="no", propose="no"):
    return {
        "production_readiness_gates": {
            "trust_in_production": {
                "answer": trust,
                "blockers": ["trust blocker"],
                "required_actions": ["fix trust"],
            },
            "support_in_production": {
                "answer": support,
                "blockers": ["support blocker"],
                "required_actions": ["fix support"],
            },
            "recommend_to_industry_peers": {
                "answer": recommend,
                "blockers": ["recommend blocker"],
                "required_actions": ["fix recommend"],
            },
            "propose_for_global_standard": {
                "answer": propose,
                "blockers": ["propose blocker"],
                "required_actions": ["fix propose"],
            },
        }
    }


def _apply_gates(response, sizing_directives):
    namespace = _domain_apply_namespace()
    queue = []
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
    logger = Logger()
    passed, record = namespace["_apply_single_domain_review_to_model"](
        response_data=response,
        domain_name="inventory",
        products_data=[],
        must_have_set=set(),
        next_vibes_queue=queue,
        in_domain_link_queue=[],
        applied_log=[],
        stats=stats,
        logger=logger,
        sizing_directives=sizing_directives,
    )
    return passed, record, queue, stats, logger


def test_domain_architect_tiny_skips_all_production_readiness_gates():
    # v4.6.4 (alias=tiny-trust-support-converge) SUPERSEDES the v4.6.3 behavior: on tiny scope
    # the tier-aware policy now skips ALL FOUR production-readiness gates (trust + support +
    # the two aspirational), not just the aspirational pair. trust/support auto-"No" on
    # "weak coverage / incomplete domain", which is by-design at smoke scope, so keeping them
    # active spun the review to the ceiling and queued scale-growth actions that violate the
    # user's tiny vibe (§3c). Structural correctness stays enforced by the deterministic SA gates.
    passed, record, queue, stats, logger = _apply_gates(
        _gate_response(),
        {"max_total_products": 15, "max_domains": 3},
    )
    assert passed
    assert stats["domain_gate_failures"] == 0
    assert queue == []
    assert record["skipped_gates"] == [
        "trust_in_production",
        "support_in_production",
        "recommend_to_industry_peers",
        "propose_for_global_standard",
    ]
    assert any(
        "[tiny-trust-support-converge FIRED v4.6.4]" in message
        for _, message in logger.records
    )

    # The exact v4.6.3 non-convergence bug that v4.6.4 fixes: even when the LLM answers
    # trust=No/support=No on a tiny model, the review CONVERGES (gates skipped) — no gate
    # failures recorded, and no trust/support actions queued into next_vibes.
    passed, record, queue, stats, logger = _apply_gates(
        _gate_response(trust="no", support="no"),
        {"max_total_products": 15},
    )
    assert passed
    assert stats["domain_gate_failures"] == 0
    assert not any("trust_in_production" in item["gate"] for item in queue)


def test_domain_architect_full_tier_keeps_aspirational_failures_and_logs_honestly():
    passed, record, queue, stats, logger = _apply_gates(
        _gate_response(),
        {"max_total_products": 100, "max_domains": 12},
    )
    assert passed
    assert stats["domain_gate_failures"] == 2
    assert any("recommend_to_industry_peers" in item["gate"] for item in queue)
    assert any("propose_for_global_standard" in item["gate"] for item in queue)
    domain_source = slice_function_source("step_domain_architect_review")
    assert "passed ALL 4 gates" not in domain_source
    assert "passed required trust/support gates" in domain_source


def test_architect_gate_bag_merge_preserves_domain_queue_when_global_bag_empty():
    merge = exec_function_namespace(
        "_v463_merge_architect_gate_bags"
    )["_v463_merge_architect_gate_bags"]
    domain_item = {"gate": "domain", "action": "fix domain"}
    assert merge([domain_item], []) == [domain_item]
    assert merge([domain_item], [domain_item]) == [domain_item]
    global_source = slice_function_source("step_architect_review")
    assert "[architect-gate-bag-merge FIRED v4.6.3]" in global_source
    assert "ALL 4 GATES PASSED" not in global_source


def test_v463_version_aliases_and_terminal_residual_wiring():
    source = SOURCE
    assert source.lstrip().splitlines()[0] == agent_version_line()
    for alias in (
        "in-domain-cycle-skip",
        "cross-domain-cycle-skip",
        "pairwise-cycle-skip",
        "fmfl-pk-map-tuple-unwrapped",
        "smart-worker-validator-mutations-preserved",
        "create-sweep-own-pk-skip",
        "pre-fmfl-unlinked-progress",
        "post-fmfl-unlinked-residual",
        "domain-arch-gate-tier-aware",
        "architect-gate-bag-merge",
    ):
        assert f"{alias} FIRED v4.6.3" in source
    final_source = slice_function_source("step_finalize_model_before_physical_schema")
    assert "_post_normalization_verification(" in final_source
    assert "config, logger, post_fmfl=True" in final_source
