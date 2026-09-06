"""v3.3.2 — verifier metadata-blindness fix.

ROOT CAUSE (live gov_transport mvm_v8 run <run_id>): the per-VREQ verifier snapshot
exposed ONLY products + attributes. It omitted TAGS, METRIC VIEWS and the CATALOG name,
so the LLM verifier (and its deterministic-blind fallback) reported "No tags present",
"Metric view absent" and "no catalog reference" for a model that actually carried 785
tagged attributes / 6 metric views / a real catalog. Separately, remove_fk was verified
at TABLE level: removing one column's FK while the table kept other legitimate FKs always
scored FAILED. Together these produced 16 confirmed false-FAILs that dragged measured
precision to 39.7% on an otherwise healthy 92/100 model.

Fixes (this file proves each against the EXACT deployed block, failing on pre-patch HEAD):
  A. verifier-snapshot-metadata: untruncatable TAG / METRIC-VIEW / CATALOG inventories.
  B. verifier-relation-remove-column: column-scoped remove_fk verification.
"""
import json
import logging
import os
import textwrap
import types

NB = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dbx_vibe_modelling_agent.ipynb")


def _load_src():
    nb = json.load(open(NB))
    return "".join("".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code")


def _slice(src, start, end):
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j]


# ---------------- FIX A: snapshot metadata inventories ----------------

def _run_metadata_block(attributes_data, metric_views, catalog):
    src = _load_src()
    block = _slice(src, "            _v332_tag_counts = {}\n",
                   "            _v100_attrs_by_pk = {}\n")
    block = textwrap.dedent(block)
    _self = types.SimpleNamespace(
        logger=logging.getLogger("v332test"),
        widgets_values={"metric_views": metric_views, "catalog": catalog},
    )
    ns = {"attributes_data": attributes_data,
          "_v100_summary_lines": ["# Model snapshot (post-mutation)"],
          "self": _self}
    exec(block, ns, ns)
    return "\n".join(ns["_v100_summary_lines"])


def test_tag_inventory_surfaced():
    attrs = [
        {"domain": "hr", "product": "employee", "attribute": "employee_id",
         "tags": "primary_key,confidential,pii,gov_transport_cde=CDE-26"},
        {"domain": "hr", "product": "employee", "attribute": "division_id", "tags": "foreign_key"},
        {"domain": "hr", "product": "employee", "attribute": "name", "tags": ""},
    ]
    snap = _run_metadata_block(attrs, [], "")
    assert "TAG INVENTORY" in snap, snap
    # 2 of 3 attrs carry tags; distinct keys include pii + confidential
    assert "2 attribute(s) carry tags" in snap, snap
    assert "pii" in snap and "confidential" in snap, snap


def test_metric_view_inventory_surfaced():
    mvs = [{"name": "Vacancy Rate"}, {"name": "Retirement Eligibility"}, {"name": "Total Positions"}]
    snap = _run_metadata_block([], mvs, "")
    assert "METRIC-VIEW INVENTORY" in snap, snap
    assert "3 metric view(s)" in snap, snap
    assert "Vacancy Rate" in snap and "Total Positions" in snap, snap


def test_catalog_surfaced():
    snap = _run_metadata_block([], [], "gov_transport_v1")
    assert "CATALOG (authoritative): gov_transport_v1" in snap, snap


def test_metadata_absent_when_model_has_none():
    # No tags / no MVs / no catalog -> none of the inventory headers appear (no false claims).
    snap = _run_metadata_block([{"domain": "d", "product": "p", "attribute": "a", "tags": ""}], [], "")
    assert "TAG INVENTORY" not in snap
    assert "METRIC-VIEW INVENTORY" not in snap
    assert "CATALOG (authoritative)" not in snap


# ---------------- FIX B: column-level remove_fk verification ----------------

def _run_remove_branch(ll, fk_attrs, tl, target):
    """Run the EXACT deployed remove-verb branch as a function body.

    The slice starts at _rel_needles (v4.8.2) rather than _rel_linked, because the
    needle set is what _rel_linked reads. _rtl and _rel_canon are passed in as the
    identity case (target already canonical, no extra resolution), which is the
    pre-v4.8.2 matching behaviour these cases were written against.
    """
    src = _load_src()
    block = _slice(src,
                   '                _rel_needles = {tl, _rtl} | _rel_canon',
                   '                if any(kw in ll for kw in ("link", "connect", "fk", "foreign key")):\n')
    body = textwrap.indent(textwrap.dedent(block), "    ")
    fn = ("import re\ndef _f(self, ll, fk_attrs, tl, target, req, _rtl, _rel_canon):\n"
          + body + "    return {'status': 'no-branch'}\n")
    _self = types.SimpleNamespace(logger=logging.getLogger("v332test"))
    ns = {}
    exec(fn, ns, ns)
    return ns["_f"](_self, ll, fk_attrs, tl, target,
                    types.SimpleNamespace(id="VREQ-009"), tl, set())


def test_remove_fk_column_level_fulfilled_when_named_column_removed():
    # Table keeps 7 legitimate FKs but the NAMED column (pse_user_id) FK is gone.
    fk_attrs = [{"domain": "project", "product": "dsctr_category_group",
                 "attribute": f"other_{i}_id", "foreign_key_to": f"project.x{i}.id"} for i in range(7)]
    res = _run_remove_branch(
        "remove the foreign key on column pse_user_id from project.dsctr_category_group",
        fk_attrs, "project.dsctr_category_group", "project.dsctr_category_group")
    assert res["status"] == "fulfilled", res
    assert "pse_user_id" in res["evidence"]


def test_remove_fk_column_level_failed_when_named_column_still_linked():
    # The named column STILL has its FK -> genuine miss must still be failed (no tautology).
    fk_attrs = [{"domain": "project", "product": "dsctr_category_group",
                 "attribute": "pse_user_id", "foreign_key_to": "hr.pse_user.id"}]
    res = _run_remove_branch(
        "remove the foreign key on column pse_user_id from project.dsctr_category_group",
        fk_attrs, "project.dsctr_category_group", "project.dsctr_category_group")
    assert res["status"] == "failed", res


def test_remove_fk_table_level_fallback_when_no_column_named():
    # No column parseable -> fall back to table-level check (legacy behavior preserved).
    fk_attrs = [{"domain": "project", "product": "x", "attribute": "y_id",
                 "foreign_key_to": "project.dsctr_group_control.id"}]
    res = _run_remove_branch(
        "remove all foreign keys touching project.dsctr_group_control",
        fk_attrs, "project.dsctr_group_control", "project.dsctr_group_control")
    assert res["status"] == "failed", res  # link still present, no column named


# ---------------- static contracts ----------------

def test_version_is_332():
    import re as _re
    m = _re.search(r'__AGENT_VERSION__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', _load_src())
    assert m, "version constant not found"
    assert tuple(int(x) for x in m.groups()) >= (3, 3, 2), m.groups()


def test_aliases_present():
    src = _load_src()
    for a in ("verifier-snapshot-metadata", "verifier-snapshot-tags", "verifier-snapshot-mv",
              "verifier-snapshot-catalog", "verifier-relation-remove-column"):
        assert a in src, a
    assert "AUTHORITATIVE TAGS/METRIC-VIEWS/CATALOG" in src
