"""B3 — new MVM SAP SD sources: every intra-domain FK closes against the base frames."""
import pandas as pd, pathlib
OUT = pathlib.Path(__file__).parents[1] / "output" / "sap_sd"


def _csv(n):
    return pd.read_csv(OUT / f"{n}.csv", dtype=str)


def test_status_log_fks_close():
    vbak = set(_csv("vbak")["vbeln"])
    sl = _csv("status_log")
    assert len(sl) > 0
    assert set(sl["vbeln"]).issubset(vbak)


def test_atp_log_fks_close():
    vbap = _csv("vbap")
    linekeys = set(vbap["vbeln"] + "|" + vbap["posnr"])
    atp = _csv("atp_log")
    assert len(atp) > 0
    assert set(atp["vbeln"] + "|" + atp["posnr"]).issubset(linekeys)


def test_sched_agreement_fks_close():
    vbak = set(_csv("vbak")["vbeln"])
    sched = _csv("sched_agreement")
    assert len(sched) > 0
    assert set(sched["vbeln"]).issubset(vbak)


def test_cpq_config_fks_close():
    vbap = _csv("vbap")
    linekeys = set(vbap["vbeln"] + "|" + vbap["posnr"])
    cpq = _csv("cpq_config")
    assert len(cpq) > 0
    assert set(cpq["vbeln"] + "|" + cpq["posnr"]).issubset(linekeys)
