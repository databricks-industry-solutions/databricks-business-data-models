#!/usr/bin/env python3
"""Add the Uninstall operation (and the install manifest it reads) to the installer.

Edits data-model-installer.ipynb in place. Idempotent: re-running is a no-op once the
notebook already carries the patch.
"""
import json
from pathlib import Path

NB = Path(__file__).resolve().parent.parent / "data-model-installer.ipynb"


def cell_source(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def find(cells, needle, kind="code"):
    for i, cell in enumerate(cells):
        if cell.get("cell_type") == kind and needle in cell_source(cell):
            return i
    raise LookupError("no %s cell contains %r" % (kind, needle))


def sub(text, old, new, count=1):
    """Apply an edit, or leave the text alone when it is already applied, so this
    script can be re-run against a notebook that carries an earlier version of it."""
    if new in text:
        return text
    assert old in text, "anchor not found: %r" % old[:120]
    assert text.count(old) >= count, "anchor appears %d times" % text.count(old)
    return text.replace(old, new, count)


# ------------------------------------------------------------------ widgets cell

WIDGETS_OLD = '''dbutils.widgets.removeAll()
dbutils.widgets.dropdown("model", SELECT_PROMPT, [SELECT_PROMPT] + INDUSTRIES, "1. industry")
dbutils.widgets.dropdown("model_size", "mvm", ["mvm", "ecm"], "2. size")
dbutils.widgets.text("catalog_name", "", "3. catalog (blank = industry name)")
dbutils.widgets.dropdown("cataloging_style", "One Catalog", ["One Catalog", "Catalog per Division", "Catalog per Domain"], "4. cataloging style")
dbutils.widgets.text("catalog_prefix", "", "5. catalog prefix (optional)")
dbutils.widgets.text("catalog_suffix", "", "6. catalog suffix (optional)")
dbutils.widgets.text("local_install", "", "7. local install (blank = pull from repo)")
dbutils.widgets.dropdown("generate_samples", "No", ["No", "Yes"], "8. generate samples")
dbutils.widgets.dropdown("sample_rows", "10", ["5", "10", "20", "50", "100"], "9. sample rows")'''

WIDGETS_NEW = '''dbutils.widgets.removeAll()
dbutils.widgets.dropdown("operation", "Install", ["Install", "Uninstall"], "1. operation")
dbutils.widgets.dropdown("model", SELECT_PROMPT, [SELECT_PROMPT] + INDUSTRIES, "2. industry")
dbutils.widgets.dropdown("model_size", "mvm", ["mvm", "ecm"], "3. size")
dbutils.widgets.text("catalog_name", "", "4. catalog (blank = industry name)")
dbutils.widgets.dropdown("cataloging_style", "One Catalog", ["One Catalog", "Catalog per Division", "Catalog per Domain"], "5. cataloging style")
dbutils.widgets.text("catalog_prefix", "", "6. catalog prefix (optional)")
dbutils.widgets.text("catalog_suffix", "", "7. catalog suffix (optional)")
dbutils.widgets.text("local_install", "", "8. local install (blank = pull from repo)")
dbutils.widgets.dropdown("generate_samples", "No", ["No", "Yes"], "9. generate samples")
dbutils.widgets.dropdown("sample_rows", "10", ["5", "10", "20", "50", "100"], "10. sample rows")'''

WIDGET_COMMENT_OLD = '''# Nine widgets are shown, in order.'''
WIDGET_COMMENT_NEW = '''# Ten widgets are shown, in order.'''


# ------------------------------------------------------------------ config cell

CONFIG_OLD = '''    cfg = {
        "industry": industry,'''
CONFIG_NEW = '''    cfg = {
        "operation": _wget("operation", "Install").strip().lower() or "install",
        "industry": industry,'''

ASSERT_OLD = '''    assert industry in INDUSTRIES, "Unknown industry: %s" % industry
    assert model_size in ("mvm", "ecm"), "model_size must be mvm or ecm"'''
ASSERT_NEW = '''    # A local install points at its own model folder, so the industry is only a label
    # and need not be one of the 40 shipped here - that is how a freshly generated
    # model (which no repo folder describes yet) gets installed. Default the label to
    # the folder name so the dropdown does not have to be touched at all.
    if cfg["local_install"]:
        if industry in ("", SELECT_PROMPT):
            industry = os.path.basename(cfg["local_install"].rstrip("/")) or "local_model"
            cfg["industry"] = industry
            if not dbutils.widgets.get("catalog_name").strip():
                cfg["catalog"] = industry
        assert industry, "an industry label is required"
    else:
        assert industry in INDUSTRIES, "Unknown industry: %s" % industry
    assert cfg["operation"] in ("install", "uninstall"), \\
        "operation must be Install or Uninstall, got %r" % cfg["operation"]
    assert model_size in ("mvm", "ecm"), "model_size must be mvm or ecm"'''


# ------------------------------------------------------------------ uninstall cell

UNINSTALL_CELL = '''# === Install manifest + the Uninstall operation ===
# An uninstall must remove exactly what the matching install created and nothing else.
# Guessing from the catalog contents is unsafe: a user may install into a catalog that
# already holds their own schemas. So the install records what it created, and the
# uninstall reads that record back.

INSTALL_SCHEMA = "_install"   # holds the log volume and the manifest


def _manifest_path(cfg):
    return "/Volumes/%s/%s/logs/manifest_%s_%s.json" % (
        cfg["catalog"], INSTALL_SCHEMA, cfg["industry"], cfg["model_size"])


_SCHEMA_STMT_RE = _re.compile(
    r"CREATE\\s+(?:SCHEMA|DATABASE)\\s+(?:IF\\s+NOT\\s+EXISTS\\s+)?"
    r"`?([^`.\\s(]+)`?(?:\\s*\\.\\s*`?([^`.\\s(]+)`?)?", _re.I)


def plan_schemas(plan, default_catalog=None):
    """The (catalog, schema) pairs the plan's schema statements would create.

    The shipped models say CREATE DATABASE, not CREATE SCHEMA, and a statement may name
    the schema alone when the session already holds a catalog - so both spellings and
    both shapes are read here. Missing one is how an uninstall silently leaves the whole
    model behind, so a schema phase that parses to nothing raises rather than no-ops."""
    pairs = []
    for stmt in plan.get("schema", []):
        m = _SCHEMA_STMT_RE.search(stmt)
        if not m:
            continue
        catalog, schema = (m.group(1), m.group(2)) if m.group(2) else (default_catalog,
                                                                       m.group(1))
        if catalog and (catalog, schema) not in pairs:
            pairs.append((catalog, schema))
    if plan.get("schema") and not pairs:
        raise Exception(
            "Could not read a schema name out of any of the %d schema statement(s); "
            "refusing to continue, because that would drop or record nothing. First "
            "statement: %s" % (len(plan["schema"]), plan["schema"][0][:200]))
    return pairs


def installed_schemas(cfg, plan):
    """Every schema the install creates: the model's own, plus `_metrics` when metric
    views are on. `_install` is excluded - it holds the log sink, so uninstall drops it
    last, by hand, after the log has been flushed."""
    schemas = plan_schemas(plan, cfg.get("catalog"))
    if cfg["include_metrics"]:
        for cat in (cfg.get("target_catalogs") or [cfg["catalog"]]):
            if (cat, "_metrics") not in schemas:
                schemas.append((cat, "_metrics"))
    return schemas


def write_install_manifest(cfg, plan, pre_existing, samples=None):
    """Record what this install created so a later uninstall can undo exactly that.

    `pre_existing` is the set of catalogs that already existed before the install ran;
    any target catalog outside it was created here and may therefore be dropped."""
    body = {
        "industry": cfg["industry"],
        "model_size": cfg["model_size"],
        "version": cfg.get("resolved_version", "unknown"),
        "catalog": cfg["catalog"],
        "cataloging_style": cfg.get("cataloging_style", "One Catalog"),
        "include_metrics": bool(cfg["include_metrics"]),
        "installed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "catalogs": [{"name": c, "created_by_installer": c not in pre_existing}
                     for c in (cfg.get("target_catalogs") or [cfg["catalog"]])],
        "schemas": [[c, s] for c, s in installed_schemas(cfg, plan)],
        "samples": samples or {"enabled": False},
    }
    path = _manifest_path(cfg)
    try:
        with open(path, "w") as f:
            f.write(json.dumps(body, indent=2))
            f.flush()
            os.fsync(f.fileno())
        log("Install manifest: %s (%d schemas, %d catalog(s), %d created here)"
            % (path, len(body["schemas"]), len(body["catalogs"]),
               sum(1 for c in body["catalogs"] if c["created_by_installer"])))
    except Exception as e:
        log("Could not write the install manifest (%s) - an uninstall will fall back "
            "to the model plan and will not drop any catalog." % str(e)[:160])
    return body


def read_install_manifest(cfg):
    try:
        with open(_manifest_path(cfg), "r") as f:
            return json.loads(f.read())
    except Exception:
        return None


def _existing_schemas(catalog):
    """Schema names present in a catalog right now, excluding UC's own."""
    try:
        rows = spark.sql(
            "SELECT schema_name FROM `%s`.information_schema.schemata" % catalog).collect()
    except Exception:
        return set()
    return set(r[0] for r in rows) - {"information_schema"}


def uninstall(cfg):
    """Drop exactly what the matching install created.

    Order matters: model schemas first, then `_install` (which holds the log sink), then
    any catalog the installer itself created. A catalog the installer did NOT create is
    always left in place, as is anything inside it that the install did not put there.
    Returns (failures, elapsed_seconds)."""
    run_start = time.time()
    manifest = read_install_manifest(cfg)
    if manifest:
        schemas = [(c, s) for c, s in manifest.get("schemas", [])]
        catalogs = manifest.get("catalogs", [])
        log("Manifest: %s (installed %s, version %s)"
            % (_manifest_path(cfg), manifest.get("installed_at"), manifest.get("version")))
    else:
        # No manifest: either the install predates them, or the volume is gone. The model
        # source still names the same schemas the install created, so drop those - but
        # leave every catalog alone, because nothing here proves the installer made it.
        log("No install manifest at %s - falling back to the model plan. No catalog "
            "will be dropped." % _manifest_path(cfg))
        plan = build_plan(cfg)
        schemas = installed_schemas(cfg, plan)
        catalogs = [{"name": c, "created_by_installer": False}
                    for c in (cfg.get("target_catalogs") or [cfg["catalog"]])]

    log("-" * 60)
    log("UNINSTALL %s/%s from `%s`: %d schema(s) across %d catalog(s)"
        % (cfg["industry"], cfg["model_size"], cfg["catalog"], len(schemas), len(catalogs)))
    for cat, schema in schemas:
        log("    drop `%s`.`%s`" % (cat, schema))

    failures = []
    stmts = ["DROP SCHEMA IF EXISTS `%s`.`%s` CASCADE" % (c, s) for c, s in schemas]
    for stmt, msg in run_phase("drop-schema", stmts, cfg["ddl_threads"], cfg["batch_size"]):
        failures.append(("drop-schema", stmt, msg))
    failures = [(ph, st, er) for ph, st, er in retry_failed(failures)]

    # The log sink lives in `_install`, so flush it before that schema disappears; the
    # rest of the uninstall is reported to the driver log and the job result.
    _flush_log_durable()
    _SINK["path"] = None
    for cat in sorted(set(c for c, _ in schemas) | set(c["name"] for c in catalogs)):
        try:
            spark.sql("DROP SCHEMA IF EXISTS `%s`.`%s` CASCADE" % (cat, INSTALL_SCHEMA))
        except Exception as e:
            failures.append(("drop-schema", "DROP SCHEMA `%s`.`%s`" % (cat, INSTALL_SCHEMA),
                             str(e)))

    dropped_catalogs = []
    for entry in catalogs:
        cat = entry["name"]
        if not entry.get("created_by_installer"):
            log("Keeping catalog `%s` - it existed before the install." % cat)
            continue
        left = _existing_schemas(cat) - {"default"}
        if left:
            # Something the install did not create is still in there. Dropping the
            # catalog would take it with us, so stop and say so.
            failures.append(("drop-catalog", "DROP CATALOG `%s`" % cat,
                             "catalog still holds schemas the install did not create: %s"
                             % ", ".join(sorted(left))))
            continue
        try:
            spark.sql("DROP CATALOG IF EXISTS `%s` CASCADE" % cat)
            dropped_catalogs.append(cat)
            log("Dropped catalog `%s` - the install created it." % cat)
        except Exception as e:
            failures.append(("drop-catalog", "DROP CATALOG `%s`" % cat, str(e)))

    # Prove it: re-read the catalogs that survive and confirm none of the schemas remain.
    residue = []
    for cat, schema in schemas:
        if cat in dropped_catalogs:
            continue
        if schema in _existing_schemas(cat):
            residue.append("`%s`.`%s`" % (cat, schema))
    if residue:
        failures.append(("verify", "post-uninstall check",
                         "still present: %s" % ", ".join(residue)))

    elapsed = time.time() - run_start
    log("=" * 64)
    log("UNINSTALL SUMMARY  %s/%s  from  `%s`"
        % (cfg["industry"], cfg["model_size"], cfg["catalog"]))
    log("  schemas dropped : %d" % (len(schemas) - len([f for f in failures
                                                        if f[0] == "drop-schema"])))
    log("  catalogs dropped: %d (%s)" % (len(dropped_catalogs),
                                         ", ".join(dropped_catalogs) or "none"))
    log("  failures        : %d" % len(failures))
    log("  total time      : %.1fs" % elapsed)
    return failures, elapsed
'''


# ------------------------------------------------------------------ main cell

MAIN_GUARD_OLD = '''    if _wget("model", "").strip() not in INDUSTRIES:
        log("Please select an industry in the '1. industry' widget, then click Run All again.")
        return'''
MAIN_GUARD_NEW = '''    if (_wget("model", "").strip() not in INDUSTRIES
            and not _wget("local_install", "").strip()):
        log("Please select an industry in the 'industry' widget (or point 'local install' "
            "at a model folder), then click Run All again.")
        return'''

MAIN_LOG_OLD = '''    cfg = resolve_config()
    log("Mode          : %s" % cfg["mode"])'''
MAIN_LOG_NEW = '''    cfg = resolve_config()
    log("Operation     : %s" % cfg["operation"])
    log("Mode          : %s" % cfg["mode"])'''

MAIN_DISPATCH_OLD = '''    setup_log_sink(cfg)
    result = None
    try:
        plan = build_plan(cfg)
        final, elapsed, timings = install(cfg, plan)'''
MAIN_DISPATCH_NEW = '''    if cfg["operation"] == "uninstall":
        # No volume log sink here: it lives in `_install`, inside the catalog being
        # removed, so it would be deleted by the very operation it is recording.
        failures, elapsed = uninstall(cfg)
        if failures:
            for phase, stmt, err in failures:
                log("  [%s] %s" % (phase, " ".join(stmt.split())[:110]))
                log("        -> %s" % (" ".join((err or "").split())[:200]))
            raise Exception("Uninstall FAILED: %d statement(s) unrecoverable in `%s`"
                            % (len(failures), cfg["catalog"]))
        result = ("UNINSTALLED: %s/%s from `%s` (%.1f min)"
                  % (cfg["industry"], cfg["model_size"], cfg["catalog"], elapsed / 60.0))
        log(result)
        dbutils.notebook.exit(result)
        return

    # Probed BEFORE the log sink is set up: the sink lives in the target catalog and
    # creates it when missing, so a later probe would see a catalog this install made
    # and record it as pre-existing - and the uninstall would then refuse to drop it.
    probed = set(cfg.get("target_catalogs") or [cfg["catalog"]])
    pre_existing = set(c for c in probed if _catalog_exists(c))

    setup_log_sink(cfg)
    result = None
    try:
        plan = build_plan(cfg)
        # A per-division / per-domain layout only names its catalogs once the plan is
        # built. None of them has been created yet, so this is still a true "before".
        for _c in (cfg.get("target_catalogs") or []):
            if _c not in probed:
                probed.add(_c)
                if _catalog_exists(_c):
                    pre_existing.add(_c)
        final, elapsed, timings = install(cfg, plan)'''

MAIN_MANIFEST_OLD = '''        sample_note = ""
        if cfg["sample"]["enabled"]:'''
MAIN_MANIFEST_NEW = '''        sample_note = ""
        sample_summary = {"enabled": bool(cfg["sample"]["enabled"])}
        if cfg["sample"]["enabled"]:'''

MAIN_SUMMARY_OLD = '''                sample_note = (" | samples: %d rows in %d tables"
                               % (summary["written"], summary["tables"]))
                if summary.get("failed"):
                    sample_note += " (%d failed)" % len(summary["failed"])'''
MAIN_SUMMARY_NEW = '''                sample_note = (" | samples: %d rows in %d tables"
                               % (summary["written"], summary["tables"]))
                if summary.get("failed"):
                    sample_note += " (%d failed)" % len(summary["failed"])
                sample_summary.update(rows=cfg["sample"]["rows"], tables=summary["tables"],
                                      written=summary["written"],
                                      failed=len(summary.get("failed") or []))

        # Written after the samples so the manifest reflects the finished install.
        write_install_manifest(cfg, plan, pre_existing, sample_summary)'''

# Migration for a notebook that already carries an earlier version of this patch: the
# catalog pre-existence probe used to run after setup_log_sink, which creates the
# catalog - so a catalog the install had just made was recorded as pre-existing and the
# uninstall then left it behind.
PRE_EXISTING_OLD = '''    setup_log_sink(cfg)
    result = None
    try:
        pre_existing = set(c for c in (cfg.get("target_catalogs") or [cfg["catalog"]])
                           if _catalog_exists(c))
        plan = build_plan(cfg)
        pre_existing |= set(c for c in (cfg.get("target_catalogs") or [cfg["catalog"]])
                            if _catalog_exists(c))
        final, elapsed, timings = install(cfg, plan)'''

PRE_EXISTING_NEW = MAIN_DISPATCH_NEW[MAIN_DISPATCH_NEW.index("    # Probed BEFORE"):]

LAUNCH_OLD = '''    widgets = {
        "model": cfg["industry"],'''
LAUNCH_NEW = '''    widgets = {
        "operation": "Uninstall" if cfg["operation"] == "uninstall" else "Install",
        "model": cfg["industry"],'''

JOBNAME_OLD = '''    job_name = "dbx_vibe_installer_%s_%s_%s" % (cfg["industry"], cfg["model_size"], version)'''
JOBNAME_NEW = '''    job_name = "dbx_vibe_%s_%s_%s_%s" % (
        "uninstaller" if cfg["operation"] == "uninstall" else "installer",
        cfg["industry"], cfg["model_size"], version)'''


def main():
    nb = json.loads(NB.read_text())
    cells = nb["cells"]

    # Re-runnable: when the notebook already carries the cell, refresh it from the
    # constant above so this script stays the single source of truth for the uninstall,
    # then fall through so the surrounding edits are brought up to date too.
    already = None
    for j, cell in enumerate(cells):
        if "def uninstall(cfg)" in cell_source(cell):
            already = j
            cells[j]["source"] = UNINSTALL_CELL
            break

    if already is not None:
        i = find(cells, "def main()")
        text = cell_source(cells[i])
        text = sub(text, PRE_EXISTING_OLD, PRE_EXISTING_NEW)
        cells[i]["source"] = text
        NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
        print("refreshed: uninstall cell %d and the main cell brought up to date" % already)
        return 0

    # widgets
    i = find(cells, 'dbutils.widgets.dropdown("model", SELECT_PROMPT')
    text = cell_source(cells[i])
    text = sub(text, WIDGETS_OLD, WIDGETS_NEW)
    text = sub(text, WIDGET_COMMENT_OLD, WIDGET_COMMENT_NEW)
    cells[i]["source"] = text

    # config
    i = find(cells, "def resolve_config")
    text = cell_source(cells[i])
    text = sub(text, CONFIG_OLD, CONFIG_NEW)
    text = sub(text, ASSERT_OLD, ASSERT_NEW)
    cells[i]["source"] = text

    # main cell edits
    i = find(cells, "def main()")
    text = cell_source(cells[i])
    for old, new in ((MAIN_GUARD_OLD, MAIN_GUARD_NEW), (MAIN_LOG_OLD, MAIN_LOG_NEW),
                     (MAIN_DISPATCH_OLD, MAIN_DISPATCH_NEW),
                     (MAIN_MANIFEST_OLD, MAIN_MANIFEST_NEW),
                     (MAIN_SUMMARY_OLD, MAIN_SUMMARY_NEW),
                     (LAUNCH_OLD, LAUNCH_NEW), (JOBNAME_OLD, JOBNAME_NEW)):
        text = sub(text, old, new)
    cells[i]["source"] = text

    # the uninstall cell goes immediately before the main cell so its defs exist first
    cells.insert(i, {"cell_type": "code", "execution_count": None, "metadata": {},
                     "outputs": [], "source": UNINSTALL_CELL})

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    print("patched: uninstall cell inserted at %d, %d cells total" % (i, len(cells)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
