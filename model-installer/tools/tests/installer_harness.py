"""Test doubles for exercising the installer's sample path without a Spark cluster.

`FakeSpark` answers the three information_schema reads the engine issues, serves the
`SELECT * FROM t LIMIT 0` schema probe from the same fixture, and records every write,
so a test can assert on the rows that WOULD land in Unity Catalog.
"""
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTALLER = HERE.parent.parent / "data-model-installer.ipynb"
ENGINE = HERE.parent / "sample_engine.py"


# ---------------------------------------------------------------- notebook access

def notebook_cells():
    return json.loads(INSTALLER.read_text())["cells"]


def cell_source(cell):
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def find_cell(needle):
    for cell in notebook_cells():
        if cell.get("cell_type") == "code" and needle in cell_source(cell):
            return cell_source(cell)
    raise LookupError("no code cell contains %r" % needle)


def load_engine():
    """Exec the notebook's sample cell, so tests bind to what actually ships."""
    namespace = {"__name__": "installer_sample_cell"}
    exec(compile(find_cell("def generate_sample_data"), "<sample-cell>", "exec"), namespace)
    return namespace


# ---------------------------------------------------------------- fake spark

class FakeField(object):
    def __init__(self, name):
        self.name = name


class FakeSchema(object):
    def __init__(self, names):
        self.fields = [FakeField(n) for n in names]


class FakeResult(object):
    def __init__(self, rows, schema=None):
        self._rows = rows
        self.schema = schema

    def collect(self):
        return list(self._rows)


class FakeWriter(object):
    def __init__(self, frame):
        self._frame = frame

    def mode(self, _mode):
        return self

    def saveAsTable(self, name):
        self._frame.spark.written.setdefault(name, []).extend(self._frame.rows)


class FakeFrame(object):
    def __init__(self, spark, rows, schema):
        self.spark = spark
        self.rows = rows
        self.schema = schema

    @property
    def write(self):
        return FakeWriter(self)


class FakeSpark(object):
    """Serves information_schema from a fixture dict and records writes.

    fixture = {"catalog": str,
               "tables": {(schema, table): {"columns": [(name, type, nullable)],
                                            "pk": [...],
                                            "fks": [{"columns": [...],
                                                     "parent": (schema, table),
                                                     "parent_columns": [...]}]}}}
    """

    def __init__(self, fixture, ai_response=None, ai_error=False, write_error=(),
                 ai_delay=0.0):
        self.fixture = fixture
        self.ai_response = ai_response
        self.ai_error = ai_error
        self.ai_delay = ai_delay
        self.write_error = set(write_error)
        self.written = {}
        self.queries = []

    # -- helpers ---------------------------------------------------------------
    def _columns_rows(self):
        rows = []
        for (schema, table), spec in self.fixture["tables"].items():
            for position, (name, dtype, nullable) in enumerate(spec["columns"], start=1):
                rows.append((schema, table, name, dtype,
                             "YES" if nullable else "NO", position))
        return rows

    def _pk_rows(self):
        rows = []
        for (schema, table), spec in self.fixture["tables"].items():
            for position, column in enumerate(spec.get("pk", []), start=1):
                rows.append((schema, table, column, position))
        return rows

    def _fk_rows(self):
        """One row per (foreign key column, referenced column) pair, ordinals aligned.

        This mirrors referential_constraints joined to key_column_usage on both sides,
        which is what the engine reads. constraint_column_usage is not modelled because
        the engine must not use it: in Unity Catalog its constraint_schema is the
        REFERENCED table's schema, so correlating on it drops cross-schema keys.
        """
        rows, seq = [], 0
        catalog = self.fixture["catalog"]
        for (schema, table), spec in self.fixture["tables"].items():
            for fk in spec.get("fks", []):
                seq += 1
                name = "%s_%s_fk%d" % (table, schema, seq)
                parent_schema, parent_table = fk["parent"]
                pairs = list(zip(fk["columns"], fk["parent_columns"]))
                for position, (column, parent_column) in enumerate(pairs, start=1):
                    rows.append((schema, name, schema, table, column, position,
                                 catalog, parent_schema, parent_table, parent_column))
        return rows

    # -- api -------------------------------------------------------------------
    def sql(self, query):
        self.queries.append(query)
        flat = " ".join(query.split())
        if "ai_query" in flat:
            if self.ai_delay:
                time.sleep(self.ai_delay)
            if self.ai_error:
                raise RuntimeError("endpoint unavailable")
            return FakeResult([(self.ai_response or "",)])
        if "information_schema.columns" in flat:
            return FakeResult(self._columns_rows())
        if "referential_constraints" in flat:
            return FakeResult(self._fk_rows())
        if "constraint_column_usage" in flat:
            raise RuntimeError(
                "constraint_column_usage.constraint_schema is the referenced table's "
                "schema in Unity Catalog; read foreign keys via referential_constraints")
        if "key_column_usage" in flat:
            return FakeResult(self._pk_rows())
        probe = re.match(r"SELECT \* FROM `([^`]+)`\.`([^`]+)`\.`([^`]+)` LIMIT 0", flat)
        if probe:
            _catalog, schema, table = probe.groups()
            if (schema, table) in self.write_error:
                raise RuntimeError("table is not writable")
            spec = self.fixture["tables"][(schema, table)]
            return FakeResult([], FakeSchema([c[0] for c in spec["columns"]]))
        return FakeResult([])

    def createDataFrame(self, rows, schema):
        return FakeFrame(self, list(rows), schema)


# ---------------------------------------------------------------- fixtures

def shop_fixture():
    """A model with every shape the engine has to survive.

    single-column key, string key, composite key, cross-schema FK, composite FK,
    self FK, a two-table FK cycle, a narrow decimal and an ordered date pair.
    """
    return {
        "catalog": "demo",
        "tables": {
            ("sales", "customer"): {
                "columns": [("customer_id", "BIGINT", False),
                            ("customer_name", "STRING", False),
                            ("country_code", "STRING", True),
                            ("email", "STRING", True),
                            ("loyalty_score", "DECIMAL(5,4)", True),
                            ("status", "STRING", False),
                            ("created_date", "DATE", True),
                            ("updated_date", "DATE", True),
                            ("primary_order_id", "BIGINT", True)],
                "pk": ["customer_id"],
                # cycle: customer -> order -> customer
                "fks": [{"columns": ["primary_order_id"], "parent": ("sales", "order"),
                         "parent_columns": ["order_id"]}],
            },
            ("sales", "order"): {
                "columns": [("order_id", "BIGINT", False),
                            ("customer_id", "BIGINT", False),
                            ("order_date", "DATE", True),
                            ("ship_date", "DATE", True),
                            ("total_amount", "DECIMAL(18,2)", True),
                            ("quantity", "INT", True),
                            ("order_status", "STRING", True)],
                "pk": ["order_id"],
                "fks": [{"columns": ["customer_id"], "parent": ("sales", "customer"),
                         "parent_columns": ["customer_id"]}],
            },
            ("sales", "order_line"): {
                "columns": [("order_id", "BIGINT", False),
                            ("line_no", "INT", False),
                            ("unit_price", "DECIMAL(10,2)", True),
                            ("quantity", "INT", True)],
                "pk": ["order_id", "line_no"],
                "fks": [{"columns": ["order_id"], "parent": ("sales", "order"),
                         "parent_columns": ["order_id"]}],
            },
            ("hr", "employee"): {
                "columns": [("employee_id", "BIGINT", False),
                            ("full_name", "STRING", False),
                            ("manager_id", "BIGINT", True),
                            ("hire_date", "DATE", True),
                            ("termination_date", "DATE", True)],
                "pk": ["employee_id"],
                "fks": [{"columns": ["manager_id"], "parent": ("hr", "employee"),
                         "parent_columns": ["employee_id"]}],
            },
            ("ops", "shipment"): {
                "columns": [("shipment_id", "STRING", False),
                            ("order_id", "BIGINT", True),
                            ("carrier_name", "STRING", True),
                            ("dispatch_timestamp", "TIMESTAMP", True)],
                "pk": ["shipment_id"],
                "fks": [{"columns": ["order_id"], "parent": ("sales", "order"),
                         "parent_columns": ["order_id"]}],
            },
            ("ops", "line_event"): {
                "columns": [("event_id", "BIGINT", False),
                            ("order_id", "BIGINT", True),
                            ("line_no", "INT", True),
                            ("event_type", "STRING", True)],
                "pk": ["event_id"],
                "fks": [{"columns": ["order_id", "line_no"],
                         "parent": ("sales", "order_line"),
                         "parent_columns": ["order_id", "line_no"]}],
            },
            ("ops", "reference_country"): {
                "columns": [("country_code", "STRING", False),
                            ("country_name", "STRING", False)],
                "pk": ["country_code"],
                "fks": [],
            },
        },
    }


def sample_config(**overrides):
    cfg = {"enabled": True, "rows": 10, "seed": 20260801, "threads": 2,
           "llm": False, "llm_endpoints": []}
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------- uninstall doubles

class FakeMetastore(object):
    """A metastore that remembers its catalogs and schemas and answers the DDL the
    uninstall path issues, so a test can assert on what survived.

    `schemas` maps catalog -> set of schema names. Every catalog implicitly carries
    `information_schema`, which the uninstall must never count as leftover content.
    """

    def __init__(self, schemas, fail_on=()):
        self.schemas = {cat: set(names) for cat, names in schemas.items()}
        self.fail_on = set(fail_on)
        self.statements = []

    def sql(self, query):
        flat = " ".join(query.split())
        self.statements.append(flat)
        for token in self.fail_on:
            if token in flat:
                raise RuntimeError("simulated failure on %s" % token)

        m = re.match(r"SELECT schema_name FROM `([^`]+)`\.information_schema\.schemata",
                     flat, re.I)
        if m:
            catalog = m.group(1)
            if catalog not in self.schemas:
                raise RuntimeError("catalog %s does not exist" % catalog)
            return FakeResult([(n,) for n in
                               sorted(self.schemas[catalog] | {"information_schema"})])

        m = re.match(r"DROP SCHEMA IF EXISTS `([^`]+)`\.`([^`]+)` CASCADE", flat, re.I)
        if m:
            catalog, schema = m.groups()
            self.schemas.get(catalog, set()).discard(schema)
            return FakeResult([])

        m = re.match(r"DROP CATALOG IF EXISTS `([^`]+)`(?: CASCADE)?", flat, re.I)
        if m:
            self.schemas.pop(m.group(1), None)
            return FakeResult([])

        return FakeResult([])


def load_uninstall(spark, manifest=None, plan=None, log_lines=None):
    """Exec the notebook's uninstall cell against stubs, so the test binds to shipped code.

    `manifest` is the dict a prior install would have written (None = no manifest, which
    exercises the plan fallback). `plan` is what build_plan returns in that fallback.
    """
    import datetime as _datetime
    import json as _json
    import os as _os
    import time as _time

    lines = log_lines if log_lines is not None else []
    written = {}

    def _log(msg):
        lines.append(str(msg))

    def _run_phase(_name, statements, _threads, _batch, group=False, serial=False):
        failures = []
        for stmt in statements:
            try:
                spark.sql(stmt)
            except Exception as exc:
                failures.append((stmt, str(exc)))
        return failures

    class _FakeFile(object):
        def __init__(self, path):
            self.path, self.buf = path, []

        def write(self, text):
            self.buf.append(text)

        def flush(self):
            pass

        def fileno(self):
            return 0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            written[self.path] = "".join(self.buf)
            return False

    def _open(path, mode="r"):
        if "w" in mode:
            return _FakeFile(path)
        if manifest is None:
            raise IOError("no such file: %s" % path)
        return _FakeFile2(_json.dumps(manifest))

    class _FakeFile2(object):
        def __init__(self, text):
            self.text = text

        def read(self):
            return self.text

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    namespace = {
        "__name__": "installer_uninstall_cell",
        "spark": spark, "log": _log, "json": _json, "os": _os, "time": _time,
        "datetime": _datetime, "_re": re, "open": _open,
        "run_phase": _run_phase,
        "retry_failed": lambda failures, passes=3: failures,
        "build_plan": lambda cfg: plan or {"schema": []},
        "_flush_log_durable": lambda: None,
        "_SINK": {"path": None},
    }
    exec(compile(find_cell("def uninstall(cfg)"), "<uninstall-cell>", "exec"), namespace)
    namespace["_log_lines"] = lines
    namespace["_written_files"] = written
    return namespace


def run_main_cell(sample_cfg, failures=(), calls=None, catalog_exists=None,
                  on_manifest=None):
    """Exec the installer's main cell against stubs and run main() once.

    `catalog_exists` is the stub behind the pre-install catalog probe; pass a callable
    with side effects to observe WHEN main() probes. `on_manifest` receives
    (cfg, plan, pre_existing, samples) so a test can assert what the install recorded.
    """
    import datetime as _datetime
    import json as _json
    import os as _os
    import time as _time

    calls = {} if calls is None else calls
    failures = list(failures)
    source = find_cell("def main()")
    assert source.rstrip().endswith("main()")
    body = source.rstrip()[:-len("main()")]

    class _Exit(Exception):
        pass

    def notebook_exit(value):
        calls["exit"] = value
        raise _Exit()

    def _sink_setup(cfg):
        calls.setdefault("order", []).append("setup_log_sink")

    namespace = {
        "__name__": "installer_main_cell",
        "time": _time, "datetime": _datetime, "os": _os, "json": _json,
        "log": lambda m: calls.setdefault("log", []).append(m),
        "INDUSTRIES": ["airlines"],
        "INSTALLER_TAG_PREFIX": "t_",
        "_wget": lambda k, d="": {"model": "airlines"}.get(k, d),
        "_running_as_job": lambda: True,
        "resolve_config": lambda: {
            "operation": "install",
            "industry": "airlines", "model_size": "mvm", "catalog": "demo",
            "cataloging_style": "One Catalog", "catalog_prefix": "", "catalog_suffix": "",
            "threads": 8, "batch_size": 20, "include_metrics": False, "mode": "REPO",
            "session_id": "1", "local_install": "", "resolved_version": "v1",
            "target_catalogs": ["demo"], "sample": sample_cfg},
        "_catalog_exists": catalog_exists or (lambda catalog: True),
        "write_install_manifest": (
            on_manifest or (lambda cfg, plan, pre_existing, samples=None: None)),
        "uninstall": lambda cfg: ([], 1.0),
        "build_plan": lambda cfg: {"table": ["CREATE TABLE t"]},
        "install": lambda cfg, plan: (failures, 12.0, {"table": 12.0}),
        "generate_sample_data": lambda spark, cfg, catalogs, log: (
            calls.setdefault("samples", []).append((cfg, catalogs))
            or {"written": 42, "tables": 7, "failed": []}),
        "setup_log_sink": _sink_setup,
        "teardown_log_sink": lambda: None,
        "_flush_log_durable": lambda: None,
        "write_failures_manifest": lambda cfg, final: None,
        "_SINK": {"path": "/tmp/log"},
        "spark": None,
        "dbutils": type("D", (), {
            "notebook": type("N", (), {"exit": staticmethod(notebook_exit)})})(),
    }
    exec(compile(body, "<main-cell>", "exec"), namespace)
    # install / setup_log_sink / write_failures_manifest are defined by the cell itself,
    # so they can only be stubbed once it has been executed.
    namespace.update(
        install=lambda cfg, plan: (failures, 12.0, {"table": 12.0}),
        setup_log_sink=_sink_setup,
        teardown_log_sink=lambda: None,
        write_failures_manifest=lambda cfg, final: None,
        JobLauncher=type("J", (), {
            "update_job_tags": staticmethod(lambda tags: {"success": True})}))
    try:
        namespace["main"]()
    except _Exit:
        pass
    return calls


def uninstall_config(**overrides):
    cfg = {"industry": "banking", "model_size": "mvm", "catalog": "bank_cat",
           "cataloging_style": "One Catalog", "include_metrics": True,
           "target_catalogs": ["bank_cat"], "ddl_threads": 4, "batch_size": 20,
           "resolved_version": "v1", "operation": "uninstall"}
    cfg.update(overrides)
    return cfg
