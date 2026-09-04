"""B4 — net-new likp/lips: FK closure + a realistic OTD spread for the headline metric."""
import pandas as pd, pathlib
OUT = pathlib.Path(__file__).parents[1] / "output" / "sap_sd"


def test_delivery_lines_close_to_orders():
    lips = pd.read_csv(OUT / "lips.csv", dtype=str)
    likp = pd.read_csv(OUT / "likp.csv", dtype=str)
    assert len(lips) > 0 and len(likp) > 0
    assert set(lips["vbeln_delivery"]).issubset(set(likp["vbeln_delivery"]))
    vbap = pd.read_csv(OUT / "vbap.csv", dtype=str)
    lk = set(vbap["vbeln"] + "|" + vbap["posnr"])
    assert set(lips["vbeln_order"] + "|" + lips["posnr_order"]).issubset(lk)


def test_delivery_header_orders_exist():
    likp = pd.read_csv(OUT / "likp.csv", dtype=str)
    vbak = set(pd.read_csv(OUT / "vbak.csv", dtype=str)["vbeln"])
    assert set(likp["vbeln_order"]).issubset(vbak)


def test_otd_distribution_realistic():
    likp = pd.read_csv(OUT / "likp.csv")
    on_time = (pd.to_datetime(likp["wadat_ist"], format="%Y%m%d")
               <= pd.to_datetime(likp["lfdat"], format="%Y%m%d")).mean()
    assert 0.70 <= on_time <= 0.95, f"on-time share {on_time:.3f} outside 0.70-0.95"
