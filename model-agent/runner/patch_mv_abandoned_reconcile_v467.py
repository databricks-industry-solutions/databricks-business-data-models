#!/usr/bin/env python3
"""v4.6.7 patch: close the metric-view silent-abandonment hole in
execute_metric_views_in_parallel_no_halt.

Root cause (evidenced): _safe_as_completed catches TimeoutError, cancels unfinished
futures, and stops yielding. Futures unfinished at pool_timeout were therefore never
installed, never fallback-repaired, never appended to `failures`, yet `succeeded =
total - len(failures)` counted them as succeeded — only to surface as `missing` at the
physical-parity gate and hard-fail the whole run (WCB Alberta v4.6.6 run 908193301348249,
missing=['claim_cost_summary','claim_eligibility_determination']).

Fix (DRY, surgical):
 1. Extract the inline per-future fallback body into a shared nested helper
    `_v467_install_mv_fallback(stmt, metric_view_name, prior_error) -> (ok, err)`.
 2. Track resolved futures in `_resolved_futures`.
 3. After the loop, reconcile every submitted-but-unresolved future: keep a late-landed
    real view (DESCRIBE probe, no clobber), else install the minimal fallback, else record
    an explicit `AbandonedByPoolTimeout` failure. No declared MV can silently vanish.

Self-verifying: asserts each anchor is unique, applies, re-parses the cell with ast.
"""
import ast
import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

HELPER = '''    fallback_statements = {}
    def _v467_install_mv_fallback(stmt, metric_view_name, prior_error):
        # v4.6.7 alias=mv-abandoned-reconcile — DRY fallback installer shared by the per-future
        # FAILED path AND the post-loop abandoned-future reconcile. Installs the minimal
        # row-count metric view so a declared MV can never be silently missing at the parity
        # gate. Serverless-safe (execute_sql only; no cache/persist/sparkContext).
        _fb_ok = False
        _fb_error = ""
        try:
            _fb_target = _extract_metric_view_target_from_statement(stmt)
            _fb_source = _extract_metric_view_source_from_statement(stmt)
            if _fb_target and _fb_source:
                _fb_yaml = (
                    f"CREATE OR REPLACE VIEW {_fb_target}\\n"
                    f"WITH METRICS\\nLANGUAGE YAML\\nAS $$\\n"
                    f"  version: 1.1\\n"
                    f"  comment: \\"FALLBACK: original MV failed install, replaced with minimal row-count view\\"\\n"
                    f"  source: \\"{_fb_source}\\"\\n"
                    f"  dimensions:\\n"
                    f"    - name: All Records\\n"
                    f"      expr: \\"1\\"\\n"
                    f"  measures:\\n"
                    f"    - name: Row Count\\n"
                    f"      expr: COUNT(1)\\n"
                    f"$$"
                )
                try:
                    execute_sql(spark, _fb_yaml, logger)
                    _fb_ok = True
                    fallback_repaired.append(metric_view_name)
                    fallback_statements[metric_view_name] = _fb_yaml
                    logger.info(f"  [mv-fallback-emit-live FIRED] installed minimal row-count fallback for '{metric_view_name}' source='{_fb_source}' alias=mv-fallback-emit-live")
                    logger.info(f"  [mv-strict-parity-repair FIRED v4.5.8] view='{metric_view_name}' repaired=1 final_failure=0 alias=mv-strict-parity-repair")
                except Exception as _fb_install_err:
                    _fb_error = _v458_metric_exception_detail(_fb_install_err, [prior_error])
            else:
                _fb_error = f"fallback source/target extraction failed target={bool(_fb_target)} source={bool(_fb_source)}"
        except Exception as _fb_err:
            _fb_error = _v458_metric_exception_detail(_fb_err, [prior_error])
        return _fb_ok, _fb_error
    completed_count = 0'''

HELPER_ANCHOR = '''    fallback_statements = {}
    completed_count = 0'''

# 2. inline fallback body -> helper call
OLD_INLINE = '''                    _fallback_ok = False
                    _fallback_error = ""
                    try:
                        _fb_target = _extract_metric_view_target_from_statement(stmt)
                        _fb_source = _extract_metric_view_source_from_statement(stmt)
                        if _fb_target and _fb_source:
                            _fb_yaml = (
                                f"CREATE OR REPLACE VIEW {_fb_target}\\n"
                                f"WITH METRICS\\nLANGUAGE YAML\\nAS $$\\n"
                                f"  version: 1.1\\n"
                                f"  comment: \\"FALLBACK: original MV failed install, replaced with minimal row-count view\\"\\n"
                                f"  source: \\"{_fb_source}\\"\\n"
                                f"  dimensions:\\n"
                                f"    - name: All Records\\n"
                                f"      expr: \\"1\\"\\n"
                                f"  measures:\\n"
                                f"    - name: Row Count\\n"
                                f"      expr: COUNT(1)\\n"
                                f"$$"
                            )
                            try:
                                execute_sql(spark, _fb_yaml, logger)
                                _fallback_ok = True
                                fallback_repaired.append(metric_view_name)
                                fallback_statements[metric_view_name] = _fb_yaml
                                logger.info(f"  [mv-fallback-emit-live FIRED] installed minimal row-count fallback for '{metric_view_name}' source='{_fb_source}' alias=mv-fallback-emit-live")
                                logger.info(f"  [mv-strict-parity-repair FIRED v4.5.8] view='{metric_view_name}' repaired=1 final_failure=0 alias=mv-strict-parity-repair")
                            except Exception as _fb_install_err:
                                _fallback_error = _v458_metric_exception_detail(_fb_install_err, [actionable_error])
                        else:
                            _fallback_error = f"fallback source/target extraction failed target={bool(_fb_target)} source={bool(_fb_source)}"
                    except Exception as _fb_err:
                        _fallback_error = _v458_metric_exception_detail(_fb_err, [actionable_error])'''

NEW_INLINE = '''                    _fallback_ok, _fallback_error = _v467_install_mv_fallback(stmt, metric_view_name, actionable_error)'''

# 3. track resolved futures
OLD_LOOP = '''        for future in _safe_as_completed(futures, timeout=pool_timeout, logger=logger, label="metric_view_no_halt"):
            stmt = futures[future]
            metric_view_name = _extract_metric_view_name_from_statement(stmt)'''
NEW_LOOP = '''        _resolved_futures = set()
        for future in _safe_as_completed(futures, timeout=pool_timeout, logger=logger, label="metric_view_no_halt"):
            stmt = futures[future]
            _resolved_futures.add(future)
            metric_view_name = _extract_metric_view_name_from_statement(stmt)'''

# 4. reconcile block before elapsed summary
OLD_ELAPSED = '''    _mv_total_elapsed = time.time() - _mv_op_start
    if failures:'''
NEW_ELAPSED = '''    # v4.6.7 alias=mv-abandoned-reconcile — _safe_as_completed cancels + stops yielding on
    # pool_timeout, so unfinished MV futures previously vanished silently (never installed,
    # never fallback-repaired, never in `failures`) yet were counted as succeeded, only to
    # surface as `missing` at the physical-parity gate and hard-fail the whole run. Reconcile
    # every submitted-but-unresolved future: keep a late-landed real view (no clobber), else
    # install the minimal fallback, else record an explicit failure.
    _abandoned = [(_f, _s) for _f, _s in futures.items() if _f not in _resolved_futures]
    if _abandoned:
        logger.error(f"{_ts()} - [mv-abandoned-reconcile FIRED v4.6.7] {len(_abandoned)} metric-view future(s) unresolved after pool_timeout={pool_timeout}s -- reconciling alias=mv-abandoned-reconcile")
        for _f, _s in _abandoned:
            try:
                _f.cancel()
            except Exception:
                pass
            _abn_name = _extract_metric_view_name_from_statement(_s)
            _abn_target = _extract_metric_view_target_from_statement(_s)
            _abn_exists = False
            if _abn_target:
                try:
                    spark.sql(f"DESCRIBE {_abn_target}")
                    _abn_exists = True
                except Exception:
                    _abn_exists = False
            if _abn_exists:
                logger.info(f"  [mv-abandoned-reconcile FIRED v4.6.7] '{_abn_name}' real view landed late -- kept, no fallback alias=mv-abandoned-reconcile")
                completed_count += 1
                continue
            _abn_err = f"AbandonedByPoolTimeout: future did not complete within pool_timeout={pool_timeout}s"
            _abn_ok, _abn_fb_err = _v467_install_mv_fallback(_s, _abn_name, _abn_err)
            if concurrency_manager:
                concurrency_manager.record_task(_abn_ok)
            if not _abn_ok:
                failures.append((_abn_name, _abn_err + " | fallback=" + (_abn_fb_err or "unknown fallback failure")))
                logger.error(f"[Metrics] Failed metric view '{_abn_name}'. Error: {_abn_err} | fallback={_abn_fb_err}")
            completed_count += 1
    _mv_total_elapsed = time.time() - _mv_op_start
    if failures:'''


def main():
    nb = json.load(open(NB))
    target = None
    for c in nb["cells"]:
        if c.get("cell_type") != "code":
            continue
        src = c["source"]
        s = "".join(src) if isinstance(src, list) else src
        if "def execute_metric_views_in_parallel_no_halt" in s:
            target = c
            src_str = s
            break
    assert target is not None, "cell with execute_metric_views_in_parallel_no_halt not found"

    for label, old in [("helper", HELPER_ANCHOR), ("inline", OLD_INLINE),
                       ("loop", OLD_LOOP), ("elapsed", OLD_ELAPSED)]:
        n = src_str.count(old)
        assert n == 1, f"anchor '{label}' count={n} (expected 1)"

    src_str = src_str.replace(HELPER_ANCHOR, HELPER)
    src_str = src_str.replace(OLD_INLINE, NEW_INLINE)
    src_str = src_str.replace(OLD_LOOP, NEW_LOOP)
    src_str = src_str.replace(OLD_ELAPSED, NEW_ELAPSED)

    # post-conditions
    assert src_str.count("_v467_install_mv_fallback") == 3, "expected 3 refs (def + 2 calls)"
    assert "_resolved_futures.add(future)" in src_str
    assert "mv-abandoned-reconcile FIRED v4.6.7" in src_str
    # cell must still parse
    ast.parse(src_str)

    target["source"] = src_str
    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("MV-ABANDONED-RECONCILE v4.6.7 APPLIED — cell parses, 3 helper refs, reconcile present.")


if __name__ == "__main__":
    main()
