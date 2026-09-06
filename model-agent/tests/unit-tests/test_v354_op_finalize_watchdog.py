import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

NB = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _nb():
    return json.loads(NB.read_text())


def _code_cells():
    return ["".join(c["source"]) for c in _nb()["cells"] if c["cell_type"] == "code"]


def _cell_with(anchor):
    for src in _code_cells():
        if anchor in src:
            return src
    raise AssertionError(f"no code cell contains {anchor!r}")


def test_v354_version_floor():
    import re
    for src in _code_cells():
        m = re.search(r'__AGENT_VERSION__\s*=\s*"([^"]+)"', src)
        if m:
            parts = tuple(int(x) for x in m.group(1).split("."))
            assert parts >= (3, 5, 4), m.group(1)
            return
    raise AssertionError("no __AGENT_VERSION__ found")


def test_v354_helper_defined_once_before_safe_exit():
    # Helper must be defined in the same cell as (and before) _safe_notebook_exit so every
    # operation path can reference it.
    src = _cell_with("def _arm_finalization_watchdog")
    assert src.count("def _arm_finalization_watchdog") == 1
    assert "def _safe_notebook_exit" in src
    assert src.index("def _arm_finalization_watchdog") < src.index("def _safe_notebook_exit")


def test_v354_three_distinct_call_sites():
    calls = []
    for src in _code_cells():
        for l in src.split("\n"):
            if "_arm_finalization_watchdog(widgets_values" in l and "def " not in l:
                calls.append(l)
    sources = {s for s in ("install model", "uninstall model version",
                           "pipeline-finally")
               if any(f'source="{s}"' in c for c in calls)}
    assert sources == {"install model", "uninstall model version",
                       "pipeline-finally"}, sources
    assert len(calls) == 3


def test_v354_install_arms_before_volume_copy_and_before_safe_exit():
    # ROOT CAUSE guard: install finalizes via a UC Volume log copy (Step 6) that can hang
    # BEFORE control returns to _safe_notebook_exit. The watchdog must be armed before that
    # copy, and obviously before the install branch's _safe_notebook_exit.
    src = _cell_with('source="install model"')
    arm = src.index('_arm_finalization_watchdog(widgets_values, grace_seconds=300, source="install model")')
    step6 = src.index("Step 6: Copying Model Files to Deployment Volume")
    assert arm < step6


def test_v354_helper_reads_exit_result_lazily_and_force_exits():
    src = _cell_with("def _arm_finalization_watchdog")
    assert '_notebook_exit_result' in src
    assert "_ow_os._exit(0)" in src
    assert "op-finalize-watchdog FIRED v3.5.4" in src
    assert "daemon=True" in src
    # os._exit skips buffer flush; the lazily-read exit result must reach the driver log.
    assert "_ow_sys.stdout.flush()" in src
    assert src.index("_ow_sys.stdout.flush()") < src.index("_ow_os._exit(0)")


def test_v354_helper_force_exits_on_stall_behavioral():
    # Behavioral proof: a process that arms the watchdog with a tiny grace and then "hangs"
    # in finalization must be force-killed by the daemon watchdog (exit 0), printing the
    # lazily-read exit result. Pre-patch (no watchdog) this child would hang forever.
    prog = textwrap.dedent('''
        import threading, os, time, sys

        def _arm_finalization_watchdog(widgets_values, grace_seconds=300, source="operation"):
            try:
                import threading as _ow_t, os as _ow_os, time as _ow_time
                def _wd():
                    _ow_time.sleep(grace_seconds)
                    try:
                        _er = widgets_values.get("_notebook_exit_result") if widgets_values else None
                        if _er:
                            print("[VIBE_EXIT_RESULT]" + str(_er) + "[/VIBE_EXIT_RESULT]")
                        print("[op-finalize-watchdog FIRED v3.5.4] source=" + source)
                    except Exception:
                        pass
                    try:
                        import sys as _ow_sys
                        _ow_sys.stdout.flush(); _ow_sys.stderr.flush()
                    except Exception:
                        pass
                    _ow_os._exit(0)
                _ow_t.Thread(target=_wd, name="op_finalize_watchdog", daemon=True).start()
            except Exception:
                pass

        wv = {}
        _arm_finalization_watchdog(wv, grace_seconds=1, source="install model")
        # exit result is set lazily, AFTER arming (mirrors real ordering)
        wv["_notebook_exit_result"] = "INSTALL_DONE"
        # simulate a hung finalization (UC Volume FUSE copy)
        time.sleep(60)
        sys.stdout.write("REACHED_END_SHOULD_NOT_HAPPEN")
    ''')
    r = subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert "REACHED_END_SHOULD_NOT_HAPPEN" not in r.stdout
    assert "op-finalize-watchdog FIRED v3.5.4" in r.stdout
    assert "INSTALL_DONE" in r.stdout


def test_v354_all_code_cells_parse():
    import ast
    for ci, c in enumerate(_nb()["cells"]):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]))
