"""MVM-profile SAP SD extension sources.

Six extra bronze tables that make the Meridian bronze *nearly fully fit* the
16-table sales_order (MVM) vibe model, plus the model_deviation demo signals:

  status_log       -> silver.order_status_event   (KEEP + new source)
  atp_log          -> silver.atp_check             (KEEP + new source; TRIM cols null)
  sched_agreement  -> silver.delivery_schedule     (KEEP + new source; TRIM cols null)
  cpq_config       -> silver.order_configuration   (KEEP + new source; TRIM cols null)
  likp             -> silver.outbound_delivery      (net-new ADD; OTD actuals)
  lips             -> silver.outbound_delivery_line (net-new ADD)

Every FK draws its parent key from the base SAP frames (backbone / vbap_full),
so intra-domain FKs close ~100%. TRIM columns are emitted present-but-empty so
the assessment's drop_null_columns deviation fires on them. No pricing-condition
source (prcd_elements/konv) is emitted -> the two condition tables have no source.

Deterministic: one utils.rng sub-stream per table (SEED=42 -> byte-identical).
"""
import numpy as np, pandas as pd
from datetime import timedelta
from . import config, utils

# TRIM columns emitted always-empty (feed silver cols the deviation drops).
_ATP_TRIM = ["is_ctp_capacity_checked", "work_center_code", "replenishment_lead_time_days",
             "mrp_element_type", "supply_source_reference"]
_SCHED_TRIM = ["is_jis", "is_jit", "is_kanban_triggered", "takt_time_seconds",
               "cumulative_ordered_quantity", "cumulative_delivered_quantity"]
_CPQ_TRIM = ["cooling_type", "hazardous_area_classification", "communication_protocol",
             "software_version", "certification_marks"]

_LIFECYCLE = ["order_created", "order_confirmed", "delivery_created", "goods_issued", "invoiced"]
# how far each order status progressed along the lifecycle
_REACHED = {"open": 1, "in-process": 2, "cancelled": 2, "shipped": 4, "invoiced": 5, "closed": 5}


def _status_log(backbone):
    g = utils.rng("mvm_status")
    rows = []
    for o in backbone.itertuples(index=False):
        reached = _REACHED.get(o.status, 2)
        base, actual, conf = pd.Timestamp(o.order_date), pd.Timestamp(o.actual), pd.Timestamp(o.conf)
        span = max((actual - base).days, 1)
        prev = ""
        for i, ev in enumerate(_LIFECYCLE[:reached]):
            ts = base + timedelta(days=int(span * (i + 1) / len(_LIFECYCLE)))
            otd = ""
            gi = ""
            if ev == "goods_issued":
                otd = "true" if actual <= conf else "false"
                gi = utils.sap_date(actual)
            rows.append({
                "vbeln": o.vbeln, "event_seq": i + 1, "event_type": ev,
                "event_timestamp": utils.iso_date(ts), "previous_status": prev, "new_status": ev,
                "otd_flag": otd, "confirmed_delivery_date": utils.sap_date(conf),
                "actual_goods_issue_date": gi,
                "triggered_by_type": g.choice(["user", "system", "batch_job", "workflow"]),
                "source_system": "SAP_SD",
            })
            prev = ev
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "status_log")
    return df


def _atp_log(vbap_full):
    g = utils.rng("mvm_atp")
    n = min(config.MVM_ROWS["atp_log"], len(vbap_full))
    lines = vbap_full.sample(n=n, random_state=config.SEED).reset_index(drop=True)
    statuses = g.choice(["CONFIRMED", "PARTIALLY_CONFIRMED", "NOT_CONFIRMED", "BACKORDER"],
                        n, p=[0.7, 0.15, 0.1, 0.05])
    rows = []
    for i, l in enumerate(lines.itertuples(index=False)):
        req_qty = float(l.kwmeng)
        # NOT_CONFIRMED / BACKORDER = nothing available yet → 0 confirmed;
        # PARTIALLY_CONFIRMED = a random fraction; CONFIRMED = full request.
        if statuses[i] == "CONFIRMED":
            conf_qty = req_qty
        elif statuses[i] == "PARTIALLY_CONFIRMED":
            conf_qty = round(req_qty * float(g.random()), 2)
        else:
            conf_qty = 0.0
        rows.append({
            "vbeln": l.vbeln, "posnr": l.posnr, "check_number": f"ATP{i + 1:08d}",
            "check_status": statuses[i], "requested_quantity": utils.sap_amount(req_qty),
            "confirmed_quantity": utils.sap_amount(conf_qty),
            "earliest_confirmation_date": utils.sap_date(l.conf),
            "check_timestamp": utils.iso_date(pd.Timestamp(l.conf)),
            "check_type": g.choice(["ATP", "CTP", "RULE_BASED_ATP"]),
            "source_system": "SAP_S4HANA",
            **{c: "" for c in _ATP_TRIM},   # TRIM: present but always empty
        })
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "atp_log")
    return df


def _sched_agreement(backbone, veda):
    g = utils.rng("mvm_sched")
    n = min(config.MVM_ROWS["sched_agreement"], len(backbone))
    orders = backbone.sample(n=n, random_state=config.SEED).reset_index(drop=True)
    # tie each agreement to a contract where available (round-robin), else blank
    contract_ids = list(veda["vbeln"]) if veda is not None and len(veda) else [""]
    rows = []
    for i, o in enumerate(orders.itertuples(index=False)):
        start = pd.Timestamp(o.order_date)
        rows.append({
            "vbeln": o.vbeln, "schedule_number": f"LPA{i + 1:07d}",
            "contract_number": contract_ids[i % len(contract_ids)],
            "schedule_type": g.choice(["forecast", "jit", "blanket", "consignment"]),
            "schedule_status": g.choice(["active", "closed", "draft"], p=[0.7, 0.2, 0.1]),
            "horizon_start_date": utils.sap_date(start),
            "horizon_end_date": utils.sap_date(start + timedelta(days=180)),
            "open_quantity": utils.sap_amount(g.integers(10, 500)),
            "quantity_unit": "EA", "source_system": "SAP_SD",
            **{c: "" for c in _SCHED_TRIM},   # TRIM: present but always empty
        })
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "sched_agreement")
    return df


def _cpq_config(vbap_full):
    g = utils.rng("mvm_cpq")
    cfg = vbap_full[vbap_full["is_config"]].copy()
    if len(cfg) > config.MVM_ROWS["cpq_config"]:
        cfg = cfg.sample(n=config.MVM_ROWS["cpq_config"], random_state=config.SEED)
    cfg = cfg.reset_index(drop=True)
    rows = []
    for i, l in enumerate(cfg.itertuples(index=False)):
        rows.append({
            "vbeln": l.vbeln, "posnr": l.posnr, "configuration_key": f"CFG{i + 1:08d}",
            "configuration_status": g.choice(["valid", "incomplete", "superseded"], p=[0.8, 0.15, 0.05]),
            "bom_explosion_status": g.choice(["exploded", "not_exploded", "partial"], p=[0.75, 0.15, 0.1]),
            "configuration_source": g.choice(["cpq", "manual", "edi"]),
            "configuration_date": utils.sap_date(l.conf),
            "source_system": "sap_sd",
            **{c: "" for c in _CPQ_TRIM},   # TRIM: present but always empty
        })
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "cpq_config")
    return df


def _likp(backbone):
    g = utils.rng("mvm_likp")
    # deliveries exist for orders that reached shipping (shipped/invoiced/closed)
    shipped = backbone[backbone["status"].isin(["shipped", "invoiced", "closed"])]
    n = min(config.MVM_ROWS["delivery"], len(shipped))
    dlv = shipped.sample(n=n, random_state=config.SEED).reset_index(drop=True)
    # Delivery-level OTD: ~15% late, rest on-time/early. Derived independently of the
    # order-level `actual` (which carries the ECM crunch story) so the headline
    # otd_performance metric lands at a realistic ~85% on-time.
    late_mask = g.random(n) < 0.15
    offsets = np.where(late_mask, g.integers(1, 11, n), g.integers(-3, 1, n))
    rows = []
    for i, o in enumerate(dlv.itertuples(index=False)):
        lfdat = pd.Timestamp(o.conf)                          # planned delivery date
        wadat = lfdat + timedelta(days=int(offsets[i]))       # actual goods-issue date
        rows.append({
            "vbeln_delivery": f"80{i + 1:08d}", "vbeln_order": o.vbeln,
            "lfdat": utils.sap_date(lfdat), "wadat_ist": utils.sap_date(wadat),
            "vstel": g.choice(["1000", "2000", "3000"]),           # shipping point
            "traty": g.choice(["truck", "rail", "parcel", "sea"]),  # carrier / transport
            "route": f"R{g.integers(100, 999)}", "source_system": "SAP_SD",
        })
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "likp")
    return df


def _lips(likp, vbap_full):
    g = utils.rng("mvm_lips")
    # map order -> its lines; a delivery ships 1..k of the order's lines
    lines_by_order = {v: grp for v, grp in vbap_full.groupby("vbeln", sort=False)}
    rows = []
    dln = 0
    cap = config.MVM_ROWS["delivery_line"] * 3   # generous total-row cap
    for d in likp.itertuples(index=False):
        if dln >= cap:                            # bound TOTAL rows, not just per-delivery
            break
        grp = lines_by_order.get(d.vbeln_order)
        if grp is None:
            continue
        for l in grp.itertuples(index=False):
            dln += 1
            rows.append({
                "vbeln_delivery": d.vbeln_delivery, "posnr": l.posnr,
                "vbeln_order": d.vbeln_order, "posnr_order": l.posnr,
                "lfimg": utils.sap_amount(l.kwmeng),   # delivered quantity
                "matnr": l.matnr, "charg": "" if not l.is_serial else f"LOT{g.integers(10000, 99999)}",
                "serial": "" if not l.is_serial else f"SN{g.integers(1000000, 9999999)}",
                "source_system": "SAP_SD",
            })
            if dln >= cap:
                break
    df = pd.DataFrame(rows)
    utils.write_csv(df, "sap_sd", "lips")
    return df


def generate(m, sap: dict) -> dict:
    """Emit the 6 MVM-profile sources. `sap` is gen_sap_sd.generate(m)'s return."""
    backbone, vbap_full, veda = sap["_backbone"], sap["_vbap_full"], sap.get("veda")
    out = {}
    out["status_log"] = _status_log(backbone)
    out["atp_log"] = _atp_log(vbap_full)
    out["sched_agreement"] = _sched_agreement(backbone, veda)
    out["cpq_config"] = _cpq_config(vbap_full)
    likp = _likp(backbone)
    out["likp"] = likp
    out["lips"] = _lips(likp, vbap_full)
    return out
