import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import exec_function_namespace


class _L:
    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


def _load():
    ns = exec_function_namespace("_finalize_fk_namespace_desc_autofix")
    return ns["_finalize_fk_namespace_desc_autofix"]


def _old_autofix(attributes_data, domains_data):
    """Pre-v4.3.1 behaviour: only rewrite a 'linking to X.Y' description when the
    desc-mentioned domain X is STILL a surviving/known domain. Reproduced so the
    test proves the fix changes observable state for DROPPED-domain references
    (the exact water_utilities MVM failure). Returns count rewritten."""
    known = {(d.get("domain") or "").lower() for d in domains_data if d.get("domain")}
    pat = re.compile(r"linking to (\w+)\.(\w+)", re.IGNORECASE)
    rewritten = 0
    for a in attributes_data:
        fk = (a.get("foreign_key_to") or "").strip()
        desc = a.get("description") or ""
        if not fk or "." not in fk or not desc:
            continue
        fk_dom = fk.split(".")[0].lower()
        if fk_dom not in known:
            continue
        new = desc
        for m in pat.finditer(desc):
            d = m.group(1).lower()
            # OLD guard: skip unless the mentioned domain still survives.
            if d in known and d != fk_dom:
                new = new.replace(m.group(0), "linking to {}.{}".format(fk_dom, m.group(2)))
        if new != desc:
            a["description"] = new
            rewritten += 1
    return rewritten


def test_dropped_domain_reference_is_rewritten_postfix_but_not_prefix():
    """After an MVM shrink drops domain 'project', an FK that was re-pointed to the
    surviving 'distribution' still carries a stale 'linking to project.X' description.
    FAIL-PRE: the old guard skips it (project no longer known). PASS-POST: the fix
    rewrites it to the true FK-target domain."""
    fn = _load()
    doms = [{"domain": "treatment"}, {"domain": "distribution"}]  # 'project' dropped

    pre = [{
        "domain": "treatment", "product": "chemical_dose_event", "attribute": "storage_tank_id",
        "foreign_key_to": "distribution.storage_tank.storage_tank_id",
        "description": "Chemical dosing event FK linking to project.storage_tank for the tank.",
    }]
    assert _old_autofix(pre, doms) == 0
    assert "project.storage_tank" in pre[0]["description"]  # unchanged by old code

    post = [{
        "domain": "treatment", "product": "chemical_dose_event", "attribute": "storage_tank_id",
        "foreign_key_to": "distribution.storage_tank.storage_tank_id",
        "description": "Chemical dosing event FK linking to project.storage_tank for the tank.",
    }]
    assert fn(post, doms, _L()) == 1
    assert "linking to distribution.storage_tank" in post[0]["description"]
    assert "project.storage_tank" not in post[0]["description"]


def test_surviving_domain_mismatch_still_rewritten():
    """Regression guard: the historical surviving-domain mismatch (both old and new
    code handle it) is still rewritten by the new helper."""
    fn = _load()
    doms = [{"domain": "asset"}, {"domain": "distribution"}]
    attrs = [{
        "domain": "distribution", "product": "pipe_main", "attribute": "asset_id",
        "foreign_key_to": "asset.equipment.equipment_id",
        "description": "Pipe main FK linking to distribution.equipment record.",
    }]
    assert fn(attrs, doms, _L()) == 1
    assert "linking to asset.equipment" in attrs[0]["description"]


def test_correct_description_left_untouched():
    """When the description domain already matches the FK target, nothing changes."""
    fn = _load()
    doms = [{"domain": "asset"}, {"domain": "distribution"}]
    attrs = [{
        "domain": "distribution", "product": "pipe_main", "attribute": "asset_id",
        "foreign_key_to": "asset.equipment.equipment_id",
        "description": "Pipe main FK linking to asset.equipment record.",
    }]
    assert fn(attrs, doms, _L()) == 0
    assert attrs[0]["description"] == "Pipe main FK linking to asset.equipment record."


def test_generic_the_token_not_rewritten():
    """'linking to the.X' style filler must not be rewritten (matches the gate's
    desc_domain != 'the' carveout)."""
    fn = _load()
    doms = [{"domain": "asset"}]
    attrs = [{
        "domain": "asset", "product": "equipment", "attribute": "parent_id",
        "foreign_key_to": "asset.equipment.equipment_id",
        "description": "Self FK linking to the.parent equipment row.",
    }]
    assert fn(attrs, doms, _L()) == 0


def test_no_fk_or_unresolved_target_untouched():
    """No FK, or FK whose domain did not survive, is left alone (never fabricate)."""
    fn = _load()
    doms = [{"domain": "asset"}]
    attrs = [
        {"domain": "asset", "product": "equipment", "attribute": "name",
         "foreign_key_to": "", "description": "linking to project.x mention with no FK."},
        {"domain": "asset", "product": "equipment", "attribute": "ghost_id",
         "foreign_key_to": "gonedomain.g.g_id", "description": "linking to project.g stale."},
    ]
    assert fn(attrs, doms, _L()) == 0
    assert attrs[0]["description"] == "linking to project.x mention with no FK."
    assert attrs[1]["description"] == "linking to project.g stale."
