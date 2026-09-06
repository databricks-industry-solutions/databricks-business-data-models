"""v4.9.0 alias=shrink-guard-user-king.

Live evidence, coffee_roastery run 564741857926303: the user asked for "roughly five to
seven tables per domain". The SelfFixer proposed the mutation that delivers it exactly,
32 products -> 28 across 4 domains, and selffixer-invariants-guard rejected it TWELVE
times with "REJECTED mutation due to regression pre={'product_count': 32} post={28}".
The rejection reason was the unconditional rule `post_count < pre_count`, so a generic
never-shrink invariant outranked an explicit user directive and the model shipped 9
products in two of the four domains.

These tests execute the real helper and the real guard expression out of the notebook.
"""
import pytest

from notebook_source_util import (assert_agent_version_at_least, cell_containing,
                                 slice_function_source)

HOLDER_ANCHOR = "def set_user_sizing_bounds_runtime("
GUARD_ANCHOR = "selffixer-invariants-guard"


def _bounds_ns():
    src = cell_containing(HOLDER_ANCHOR)
    ns = {"_USER_SIZING_BOUNDS_RUNTIME": {}}
    exec("\n\n".join(slice_function_source(f, src) for f in
                     ("set_user_sizing_bounds_runtime", "_v490_user_product_bounds",
                      "shrink_is_user_requested")), ns)
    return ns


def _shrink(directives, pre, post, domains=4):
    ns = _bounds_ns()
    ns["set_user_sizing_bounds_runtime"](directives, domain_count=domains)
    return ns["shrink_is_user_requested"](pre, post, domains)


# --- the exact live mutation ---------------------------------------------------------

def test_the_mutation_the_guard_rejected_twelve_times_is_now_allowed():
    """THE REGRESSION: 32 -> 28 under "five to seven per domain" over 4 domains."""
    assert _shrink({"min_products_per_domain": 5, "max_products_per_domain": 7},
                   32, 28) is True


def test_a_partial_step_toward_the_ceiling_also_counts():
    """28 is the ceiling; 32 -> 30 is still progress and must not be blocked."""
    assert _shrink({"min_products_per_domain": 5, "max_products_per_domain": 7},
                   32, 30) is True


# --- it must not become a licence to delete ------------------------------------------

def test_it_will_not_cut_below_the_users_own_floor():
    """Floor is 5*4 = 20. Cutting to 19 is not what the user asked for."""
    assert _shrink({"min_products_per_domain": 5, "max_products_per_domain": 7},
                   32, 19) is False


def test_a_model_already_within_the_ceiling_may_not_shrink():
    """At 28 the user is satisfied; further deletion is a regression again."""
    assert _shrink({"min_products_per_domain": 5, "max_products_per_domain": 7},
                   28, 24) is False


def test_without_a_sizing_vibe_nothing_changes():
    """THE NEGATIVE CONTROL. No user directive means the old rule governs untouched."""
    assert _shrink({}, 32, 28) is False


def test_growth_is_never_a_shrink():
    assert _shrink({"max_products_per_domain": 7}, 28, 32) is False


def test_an_unchanged_count_is_not_a_shrink():
    assert _shrink({"max_products_per_domain": 7}, 32, 32) is False


# --- bound resolution ----------------------------------------------------------------

def test_an_explicit_total_outranks_the_per_domain_product():
    """max_total_products=20 must win over 7*4=28, so 32 -> 22 is still progress."""
    assert _shrink({"max_total_products": 20, "max_products_per_domain": 7},
                   32, 22) is True
    assert _shrink({"max_total_products": 20, "min_total_products": 18},
                   32, 17) is False


def test_a_per_domain_ceiling_needs_a_domain_count_to_become_a_total():
    ns = _bounds_ns()
    ns["set_user_sizing_bounds_runtime"]({"max_products_per_domain": 7}, domain_count=None)
    assert ns["shrink_is_user_requested"](32, 28, None) is False
    assert ns["shrink_is_user_requested"](32, 28, 4) is True


@pytest.mark.parametrize("bad", [None, "", [], "max_products_per_domain=7", 7])
def test_a_non_dict_publishes_nothing(bad):
    ns = _bounds_ns()
    assert ns["set_user_sizing_bounds_runtime"](bad, domain_count=4) == {}
    assert ns["shrink_is_user_requested"](32, 28, 4) is False


@pytest.mark.parametrize("bad", [None, "many", float("nan")])
def test_non_numeric_counts_are_refused_rather_than_crashing(bad):
    assert _shrink({"max_products_per_domain": 7}, bad, 28) is False


def test_a_bool_is_not_read_as_a_bound():
    """True == 1 would silently become "the user asked for one product per domain"."""
    ns = _bounds_ns()
    assert ns["set_user_sizing_bounds_runtime"]({"max_products_per_domain": True},
                                                domain_count=4) == {"domain_count": 4}


def test_publishing_twice_does_not_accumulate_stale_bounds():
    ns = _bounds_ns()
    ns["set_user_sizing_bounds_runtime"]({"max_total_products": 20}, domain_count=4)
    second = ns["set_user_sizing_bounds_runtime"]({"max_products_per_domain": 7},
                                                  domain_count=4)
    assert "max_total_products" not in second


# --- the guard actually consults it --------------------------------------------------

def test_the_guard_consults_the_helper_rather_than_shrinking_unconditionally():
    src = cell_containing(GUARD_ANCHOR)
    assert "shrink_is_user_requested(" in src, "the guard must call the helper"
    assert 'post_inv["product_count"] < pre_inv["product_count"] and not _shrink_ok' in src


def test_the_other_invariants_are_left_alone():
    """Only the product-count clause is conditional; FK/silo/domain rules must not move."""
    src = cell_containing(GUARD_ANCHOR)
    for clause in ('post_inv["fk_target_misses"] > pre_inv["fk_target_misses"]',
                   'post_inv["silo_count"] > pre_inv["silo_count"]',
                   'post_inv["domain_count"] < pre_inv["domain_count"]'):
        assert clause in src


def test_the_bounds_are_published_from_the_parsed_vibe():
    src = cell_containing("_v488_sizing_override_from_directives(")
    assert "set_user_sizing_bounds_runtime(" in src, (
        "nothing publishes the bounds, so the guard would never see them")


def test_version_is_490_or_later():
    assert_agent_version_at_least("4.9.0")
