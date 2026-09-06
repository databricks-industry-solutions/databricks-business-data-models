"""v4.8.2 alias=verifier-relation-target-resolvable.

Live: coffee_roastery run 186683145042109 scored VREQ-003 failed on the physical pass
while its three lineage FKs physically existed, because the first scope_target was the
vibe's own wording ("origin purchase") rather than a product name, and the relation
branch returned failed on that name miss before reaching the targets that do resolve.

The model below is the shape of that run: an origin -> middle -> end FK chain where the
VREQ names the first hop in prose and the later hops by their real product names.
"""

import re

import agent_helpers as ah
from notebook_source_util import agent_version_line, notebook_concat_source


class _Logger:
    def __init__(self):
        self.lines = []

    def info(self, msg):
        self.lines.append(str(msg))

    def warning(self, msg):
        self.lines.append(str(msg))


class _Req:
    def __init__(self, text, scope, targets, rid="VREQ-003"):
        self.original_text = text
        self.scope = scope
        self.scope_targets = targets
        self.id = rid
        self.status = ""
        self.evidence = ""


LINEAGE_TEXT = (
    "Green coffee lots must be traceable from the origin purchase through the roast batch "
    "into the finished package, so the lineage chain has to be modelled with real foreign "
    "keys connecting origin purchase, roast batch and finished package."
)

REMOVE_TEXT = "Remove the foreign key from roast batch to the origin purchase."


def _model():
    domains = [{"domain": "sourcing"}, {"domain": "roasting"}]
    products = [
        {"domain": "sourcing", "product": "purchase_contract"},
        {"domain": "sourcing", "product": "gc_lot"},
        {"domain": "roasting", "product": "roast_batch"},
        {"domain": "roasting", "product": "finished_package"},
    ]
    attrs = [
        {"domain": "sourcing", "product": "purchase_contract", "attribute": "purchase_contract_id",
         "foreign_key_to": ""},
        {"domain": "sourcing", "product": "gc_lot", "attribute": "gc_lot_id", "foreign_key_to": ""},
        {"domain": "sourcing", "product": "gc_lot", "attribute": "purchase_contract_id",
         "foreign_key_to": "sourcing.purchase_contract.purchase_contract_id"},
        {"domain": "roasting", "product": "roast_batch", "attribute": "roast_batch_id", "foreign_key_to": ""},
        {"domain": "roasting", "product": "roast_batch", "attribute": "gc_lot_id",
         "foreign_key_to": "sourcing.gc_lot.gc_lot_id"},
        {"domain": "roasting", "product": "finished_package", "attribute": "finished_package_id",
         "foreign_key_to": ""},
        {"domain": "roasting", "product": "finished_package", "attribute": "roast_batch_id",
         "foreign_key_to": "roasting.roast_batch.roast_batch_id"},
    ]
    return domains, products, attrs


def _orch(logger=None):
    o = object.__new__(ah.VibeOrchestrator)
    o.logger = logger or _Logger()
    o._step_snapshots = {}
    o.config = {"MODEL_CONVENTIONS": {"data_asset_naming_convention": "snake_case"}}
    return o


def _verify(req, logger=None):
    domains, products, attrs = _model()
    return _orch(logger)._verify_deterministic(req, domains, products, attrs)


def test_a_prose_first_target_no_longer_false_fails_a_lineage_that_exists():
    # pre-patch this returned {"status": "failed", "evidence": "No FK relationship found
    # for 'origin purchase'"} and the physical pass took that as authoritative.
    res = _verify(_Req(LINEAGE_TEXT, "relation",
                       ["origin purchase", "roasting.roast_batch", "roasting.finished_package"]))
    assert res is not None
    assert res["status"] != "failed", res


def test_the_later_resolvable_target_is_what_decides_the_verdict():
    res = _verify(_Req(LINEAGE_TEXT, "relation",
                       ["origin purchase", "roasting.roast_batch", "roasting.finished_package"]))
    assert res["status"] == "fulfilled", res
    assert "roast_batch" in res["evidence"], res


def test_the_skip_is_reported_so_the_run_can_be_audited():
    log = _Logger()
    _verify(_Req(LINEAGE_TEXT, "relation", ["origin purchase", "roasting.roast_batch"]), log)
    fired = [l for l in log.lines if "verifier-relation-target-resolvable FIRED" in l]
    assert len(fired) == 1, log.lines
    assert "origin purchase" in fired[0]


def test_a_target_that_resolves_but_has_no_foreign_key_still_fails():
    # the guard must not turn every miss into a pass: a real product with no FK is a
    # genuine failure and has to keep failing.
    domains, products, attrs = _model()
    attrs = [a for a in attrs if not a["foreign_key_to"]]
    res = _orch()._verify_deterministic(
        _Req(LINEAGE_TEXT, "relation", ["roasting.finished_package"]), domains, products, attrs
    )
    assert res["status"] == "failed", res


def test_a_remove_verb_on_an_unresolvable_target_is_not_reported_as_removed():
    # opposite polarity of the same bug: "not _rel_linked -> removed" false-fulfilled a
    # remove VREQ whose target named nothing.
    res = _verify(_Req(REMOVE_TEXT, "relation", ["origin purchase"]))
    assert res is None or res["status"] != "fulfilled", res


def test_a_remove_verb_on_a_resolvable_target_still_reports_the_surviving_link():
    res = _verify(_Req("Remove the foreign key to sourcing.gc_lot.", "relation", ["sourcing.gc_lot"]))
    assert res["status"] == "failed", res


def test_a_target_naming_a_product_with_different_punctuation_resolves():
    res = _verify(_Req(LINEAGE_TEXT, "relation", ["finished package"]))
    assert res["status"] == "fulfilled", res


def test_the_guard_is_wired_into_the_notebook_source():
    src = notebook_concat_source()
    assert src.count("verifier-relation-target-resolvable FIRED") == 1
    assert re.search(r"if not _rel_known:\s*\n\s+try:", src)


def test_the_agent_version_is_at_least_the_one_that_shipped_this_fix():
    # a floor, not a literal: a later bump must not fail a test about v4.8.2's fix,
    # but a rollback below 4.8.2 must.
    m = re.search(r'__AGENT_VERSION__ = "(\d)\.(\d)\.(\d)"', agent_version_line())
    assert m, agent_version_line()
    assert tuple(int(g) for g in m.groups()) >= (4, 8, 2), agent_version_line()
