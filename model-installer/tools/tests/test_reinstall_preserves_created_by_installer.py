"""A repeat install on an installer-owned catalog must not demote the manifest flag.

Live repro (advertising/mvm, runs 976731135363658 install → 980762276263286 re-install
→ 3380090647409 uninstall on scratch e2e branch, 2026-08-04):

    Install A ran on a FRESH catalog `e2e_20260804_0742_adv`. The manifest recorded
    `created_by_installer=True` for that catalog. Install B was a widget-only
    Install re-run on the same catalog to regenerate samples; it recomputed
    pre_existing from `_catalog_exists` (now True), so the new manifest overwrote
    the flag with `created_by_installer=False`. Uninstall C read that manifest,
    dropped every schema, and left the empty catalog behind, breaking the widget
    round-trip. Fix: write_install_manifest inherits `True` from any prior manifest
    at the same catalog (alias `manifest-preserve-created-by-installer`).

Both tests bind to the shipped notebook cell, not to a copy of the logic. Both fail
on the pre-patch notebook (proven by first stashing the fix and re-running).
"""
import json
import os
import tempfile

import pytest

from installer_harness import find_cell


def _load_manifest_cell(tmp_logs_dir):
    """Exec the notebook's manifest cell against a real tmp filesystem. Widgets are
    unused; `open` and `glob.glob` are the real modules pointing at tmp_logs_dir so
    the helper's manifest scan sees whatever the test placed there."""
    import datetime as _datetime
    import glob as _glob
    import re as _re
    import time as _time

    logs = []

    ns = {
        "__name__": "manifest_cell_probe",
        "json": json, "os": os, "time": _time, "datetime": _datetime, "_re": _re,
        "glob": _glob, "open": open,
        "log": lambda m: logs.append(str(m)),
        "spark": None,
        "run_phase": lambda *a, **k: [],
        "retry_failed": lambda failures, passes=3: failures,
        "build_plan": lambda cfg: {"schema": []},
        "_flush_log_durable": lambda: None,
        "_SINK": {"path": None},
    }
    exec(compile(find_cell("def write_install_manifest"), "<manifest-cell>", "exec"), ns)
    ns["_log_lines"] = logs
    return ns


def _write_prior_manifest(logs_dir, catalog, created_by_installer):
    os.makedirs(logs_dir, exist_ok=True)
    body = {
        "industry": "coffee_roastery",
        "model_size": "mvm",
        "catalog": catalog,
        "catalogs": [{"name": catalog, "created_by_installer": bool(created_by_installer)}],
        "schemas": [[catalog, "wholesale"]],
    }
    path = os.path.join(logs_dir, "manifest_coffee_roastery_mvm.json")
    with open(path, "w") as f:
        f.write(json.dumps(body))
    return path


@pytest.fixture
def tmp_volume(monkeypatch, tmp_path):
    """Redirect `/Volumes/{catalog}/_install/logs` to a real tmp dir the tests populate."""
    catalog = "reinstall_probe"
    base = tmp_path / "Volumes" / catalog / "_install" / "logs"
    # Point the helper's glob at this real dir by monkeypatching os.path such that
    # /Volumes/... resolves under tmp_path. Simpler: monkeypatch the module-level
    # constant INSTALL_SCHEMA is unnecessary; instead, monkeypatch glob.glob to
    # rewrite the '/Volumes/...' prefix to our tmp dir.
    import glob as _glob
    real_glob = _glob.glob

    def _glob_shim(pattern):
        if pattern.startswith("/Volumes/"):
            rewritten = str(tmp_path) + pattern
            return real_glob(rewritten)
        return real_glob(pattern)

    monkeypatch.setattr(_glob, "glob", _glob_shim)
    return {"catalog": catalog, "logs_dir": str(base)}


def test_prior_installer_created_returns_true_when_prior_manifest_recorded_ownership(tmp_volume):
    _write_prior_manifest(tmp_volume["logs_dir"], tmp_volume["catalog"], created_by_installer=True)
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    assert ns["_prior_installer_created"](tmp_volume["catalog"]) is True


def test_prior_installer_created_returns_false_when_prior_manifest_recorded_no_ownership(tmp_volume):
    _write_prior_manifest(tmp_volume["logs_dir"], tmp_volume["catalog"], created_by_installer=False)
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    assert ns["_prior_installer_created"](tmp_volume["catalog"]) is False


def test_prior_installer_created_returns_false_when_no_prior_manifest_at_all(tmp_volume):
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    assert ns["_prior_installer_created"](tmp_volume["catalog"]) is False


def _write_manifest_via_notebook(ns, catalog, pre_existing, tmp_logs_dir):
    """Invoke write_install_manifest via the shipped cell and return the manifest body it
    wrote to disk (the notebook's writer uses `open(path,'w')` and json.dumps)."""
    cfg = {
        "industry": "advertising",
        "model_size": "mvm",
        "catalog": catalog,
        "cataloging_style": "One Catalog",
        "catalog_prefix": "", "catalog_suffix": "",
        "include_metrics": False,
        "resolved_version": "v1",
        "target_catalogs": [catalog],
    }
    # Force _manifest_path to point at the tmp dir so we don't need /Volumes access.
    real_mp = ns["_manifest_path"]
    ns["_manifest_path"] = lambda _cfg: os.path.join(
        tmp_logs_dir, "manifest_%s_%s.json" % (_cfg["industry"], _cfg["model_size"]))
    # installed_schemas returns whatever build_plan-derived pairs; keep small.
    ns["installed_schemas"] = lambda _cfg, _plan: [(catalog, "audience")]
    os.makedirs(tmp_logs_dir, exist_ok=True)
    ns["write_install_manifest"](cfg, {"schema": []}, pre_existing, samples={"enabled": False})
    ns["_manifest_path"] = real_mp
    with open(os.path.join(tmp_logs_dir,
                           "manifest_%s_%s.json" % (cfg["industry"], cfg["model_size"]))) as f:
        return json.loads(f.read())


def test_reinstall_on_catalog_we_created_preserves_created_by_installer_true(tmp_volume):
    """Live-repro root cause: install B rewrites the manifest and demotes the flag."""
    # Simulate the state AFTER install A: a prior manifest exists at this catalog
    # with created_by_installer=True.
    _write_prior_manifest(tmp_volume["logs_dir"], tmp_volume["catalog"], created_by_installer=True)

    # Install B calls write_install_manifest with pre_existing={catalog} because
    # _catalog_exists is True at re-install time.
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    body = _write_manifest_via_notebook(
        ns, tmp_volume["catalog"], pre_existing={tmp_volume["catalog"]},
        tmp_logs_dir=tmp_volume["logs_dir"])

    entry = next(c for c in body["catalogs"] if c["name"] == tmp_volume["catalog"])
    assert entry["created_by_installer"] is True, (
        "re-install must inherit created_by_installer=True from the prior manifest; "
        "manifest was: %s" % body)
    fired = [l for l in ns["_log_lines"]
             if "manifest-preserve-created-by-installer FIRED" in l]
    assert fired, "the fix must self-report [manifest-preserve-created-by-installer FIRED]"


def test_first_install_on_a_pre_existing_catalog_still_records_false(tmp_volume):
    """A first install on a user-provided catalog that already existed must still record
    `created_by_installer=False` - the fix must not over-fire when no prior manifest
    exists, otherwise Uninstall would drop a catalog the user created."""
    # No prior manifest at all.
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    body = _write_manifest_via_notebook(
        ns, tmp_volume["catalog"], pre_existing={tmp_volume["catalog"]},
        tmp_logs_dir=tmp_volume["logs_dir"])
    entry = next(c for c in body["catalogs"] if c["name"] == tmp_volume["catalog"])
    assert entry["created_by_installer"] is False


def test_fresh_install_on_a_new_catalog_records_true(tmp_volume):
    """A first install on a genuinely new catalog records True unchanged."""
    ns = _load_manifest_cell(tmp_volume["logs_dir"])
    body = _write_manifest_via_notebook(
        ns, tmp_volume["catalog"], pre_existing=set(),
        tmp_logs_dir=tmp_volume["logs_dir"])
    entry = next(c for c in body["catalogs"] if c["name"] == tmp_volume["catalog"])
    assert entry["created_by_installer"] is True
