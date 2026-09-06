"""v4.9.5 - the model.json boundary must resync column_name to the logical name.

Live residual (coffee_roastery v4.9.4, catalog vibe_e2e_v494):
  the SelfFixer multi_fk_missing_label pass renamed wholesale.order_line's generic FK,
  setting name='line_finished_package_id' but leaving column_name='finished_package_id'.
  model.json serializes column_name (stale) while the DDL runs the v487 colname resync
  and emits the logical name -> 1 broken column reference of 1059.

v4.9.5 runs the identical resync inside _v493_resolve_physical_column_names, ahead of
serialization, so model.json carries the DDL's physical name.
"""
from collections import defaultdict

from notebook_source_util import (
    assert_agent_version_at_least,
    exec_function_namespace,
    slice_function_source,
)

RESOLVE = "_v493_resolve_physical_column_names"


class _Log:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def debug(self, *a, **k):
        pass


def _resolver():
    """Execute the resolver with the two OTHER passes stubbed to no-ops, so the test
    isolates the v4.9.5 colname-resync."""
    ns = exec_function_namespace(
        RESOLVE,
        extra_globals={
            "defaultdict": defaultdict,
            "_fix_bare_attribute_names": lambda attrs, logger: 0,
            "_v493_align_fk_column_names_to_parent_pk": lambda p, a, c, l: 0,
        },
    )
    return ns[RESOLVE]


def _attr(name, column_name, fk=""):
    return {"domain": "wholesale", "product": "order_line", "attribute": name,
            "name": name, "column_name": column_name, "foreign_key_to": fk, "type": "BIGINT"}


def test_a_stale_column_name_is_resynced_to_the_logical_name():
    wv = {
        "config": {},
        "products": [{"domain": "wholesale", "product": "order_line", "primary_key": "order_line_id"}],
        "attributes": [
            _attr("line_finished_package_id", "finished_package_id",
                  "roasting.finished_package.finished_package_id"),
        ],
    }
    _resolver()(wv, _Log(), "test")
    a = wv["attributes"][0]
    assert a["column_name"] == "line_finished_package_id", (
        "column_name still stale after the resolver: %r" % a["column_name"]
    )
    assert a["column_name"] == (a.get("attribute") or a.get("name"))


def test_an_already_synced_column_is_untouched():
    wv = {
        "config": {},
        "products": [{"domain": "wholesale", "product": "order_line", "primary_key": "order_line_id"}],
        "attributes": [_attr("sku_finished_package_id", "sku_finished_package_id")],
    }
    _resolver()(wv, _Log(), "test")
    assert wv["attributes"][0]["column_name"] == "sku_finished_package_id"


def test_a_column_name_only_falls_back_to_name_when_attribute_missing():
    wv = {
        "config": {},
        "products": [{"domain": "wholesale", "product": "order_line", "primary_key": "order_line_id"}],
        "attributes": [{"domain": "wholesale", "product": "order_line",
                        "name": "line_finished_package_id", "column_name": "finished_package_id",
                        "type": "BIGINT"}],
    }
    _resolver()(wv, _Log(), "test")
    assert wv["attributes"][0]["column_name"] == "line_finished_package_id"


def test_the_resync_is_in_the_resolver_source():
    src = slice_function_source(RESOLVE)
    assert "_colname_synced" in src, "the colname-resync pass is missing from the resolver"
    assert "v495-colname-sync-before-modeljson FIRED" in src, "no observable FIRED line"


def test_version_is_495_or_later():
    assert_agent_version_at_least("4.9.5")
