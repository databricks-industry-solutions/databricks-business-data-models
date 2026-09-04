import pandas as pd, sys
from . import config

def _load(schema, table):
    return pd.read_csv(config.OUTPUT_DIR / schema / f"{table}.csv", dtype=str, keep_default_na=False)

CHECKS = []
def check(fn): CHECKS.append(fn); return fn

@check
def fk_vbap_to_vbak():
    vbak=_load("sap_sd","vbak"); vbap=_load("sap_sd","vbap")
    orphans=set(vbap.vbeln)-set(vbak.vbeln)
    return f"vbap has {len(orphans)} orphan vbeln" if orphans else None

@check
def fk_vbep_to_vbap():
    vbap=_load("sap_sd","vbap"); vbep=_load("sap_sd","vbep")
    key=lambda d:set(d.vbeln+"|"+d.posnr)
    orphans=key(vbep)-key(vbap)
    return f"vbep has {len(orphans)} orphan line keys" if orphans else None

@check
def fk_vbpa_to_kna1():
    vbpa=_load("sap_sd","vbpa"); kna1=_load("sap_sd","kna1")
    orphans=set(vbpa.kunnr)-set(kna1.kunnr)
    return f"vbpa has {len(orphans)} orphan kunnr" if orphans else None

@check
def fk_account_to_kna1():
    acc=_load("salesforce_crm","account"); kna1=_load("sap_sd","kna1")
    orphans=set(acc.sap_kunnr)-set(kna1.kunnr)
    return f"account has {len(orphans)} unmatched sap_kunnr" if orphans else None

@check
def fk_edi_to_vbak():
    edi=_load("edi_gateway","edi_message_log"); vbak=_load("sap_sd","vbak")
    orphans=set(edi.order_number)-set(vbak.vbeln)
    return f"edi has {len(orphans)} orphan order_number" if orphans else None

@check
def fk_rma_to_vbak():
    rma=_load("returns_portal","rma_request"); vbak=_load("sap_sd","vbak")
    orphans=set(rma.original_order_number)-set(vbak.vbeln)
    return f"rma has {len(orphans)} orphan order_number" if orphans else None

@check
def fk_asset_to_vbak():
    a=_load("fieldlink","installed_asset"); vbak=_load("sap_sd","vbak")
    orphans=set(a.source_order_number)-set(vbak.vbeln)
    return f"installed_asset has {len(orphans)} orphan order_number" if orphans else None

@check
def fk_service_to_asset():
    so=_load("fieldlink","service_order"); a=_load("fieldlink","installed_asset")
    orphans=set(so.asset_id)-set(a.asset_id)
    return f"service_order has {len(orphans)} orphan asset_id" if orphans else None

@check
def converted_quote_customer_matches_order():
    # A converted quote must reference an order belonging to the SAME customer.
    # Cross-ref: quote.account_id -> account.sap_kunnr -> vbak.kunnr for that order.
    quote=_load("salesforce_crm","quote"); acc=_load("salesforce_crm","account"); vbak=_load("sap_sd","vbak")
    acct_to_kunnr=dict(zip(acc.account_id, acc.sap_kunnr))
    order_to_kunnr=dict(zip(vbak.vbeln, vbak.kunnr))
    conv=quote[quote.converted_order_number.str.len()>0]
    mism=sum(1 for _,q in conv.iterrows()
             if order_to_kunnr.get(q.converted_order_number)!=acct_to_kunnr.get(q.account_id))
    return f"{mism} converted quotes reference an order from a different customer" if mism else None

@check
def vbak_header_equals_line_sum():
    # VBAK.netwr must roll up its VBAP line net values.
    vbak=_load("sap_sd","vbak"); vbap=_load("sap_sd","vbap")
    lsum=vbap.assign(n=vbap.netwr.astype(float)).groupby("vbeln").n.sum().round(2)
    hdr=vbak.assign(n=vbak.netwr.astype(float)).set_index("vbeln").n.round(2)
    j=hdr.to_frame("h").join(lsum.to_frame("l"))
    bad=(j.h.sub(j.l).abs()>0.02).sum()
    return f"{bad} orders where vbak.netwr != sum(vbap line net)" if bad else None

@check
def quote_header_equals_line_sum():
    # quote.total_amount must roll up its quote_line net values.
    q=_load("salesforce_crm","quote"); ql=_load("salesforce_crm","quote_line")
    lsum=ql.assign(n=ql.net_value.astype(float)).groupby("quote_id").n.sum().round(2)
    hdr=q.assign(n=q.total_amount.astype(float)).set_index("quote_id").n.round(2)
    j=hdr.to_frame("h").join(lsum.to_frame("l"))
    bad=(j.h.sub(j.l).abs()>0.02).sum()
    return f"{bad} quotes where total_amount != sum(quote_line net)" if bad else None

@check
def fieldlink_dates_within_window():
    # service_order.opened_date must not exceed the data window end.
    import pandas as _pd
    so=_load("fieldlink","service_order")
    end=_pd.Timestamp(config.DATE_END)
    over=(_pd.to_datetime(so.opened_date, errors="coerce")>end).sum()
    return f"{over} service_order.opened_date values exceed {config.DATE_END}" if over else None

@check
def sap_dates_are_yyyymmdd():
    vbak=_load("sap_sd","vbak")
    bad=vbak[~vbak.erdat.str.match(r"^\d{8}$")]
    return f"vbak.erdat has {len(bad)} non-YYYYMMDD values" if len(bad) else None

@check
def sap_amounts_are_strings():
    vbak=_load("sap_sd","vbak")
    bad=vbak[~vbak.netwr.str.match(r"^\d+\.\d{2}$")]
    return f"vbak.netwr has {len(bad)} non-string-amount values" if len(bad) else None

@check
def row_count_floors():
    vbak=_load("sap_sd","vbak")
    return f"vbak has {len(vbak)} rows (<4500)" if len(vbak)<4500 else None

@check
def otd_has_late_deliveries():
    # sanity: some confirmed<actual lateness exists (crunch windows working)
    vbep=_load("sap_sd","vbep")
    late=(pd.to_datetime(vbep.wadat,format="%Y%m%d",errors="coerce") >
          pd.to_datetime(vbep.edatu,format="%Y%m%d",errors="coerce")).sum()
    return "no late schedule lines generated (OTD crunch not working)" if late==0 else None

def run():
    fails=[f() for f in CHECKS]
    return [f for f in fails if f]

# --- MVM-profile integrity gate (only run for --profile mvm) ---
MVM_CHECKS = []
def mvm_check(fn): MVM_CHECKS.append(fn); return fn

def _lk(d, a="vbeln", b="posnr"):
    return set(d[a] + "|" + d[b])

@mvm_check
def mvm_status_log_to_vbak():
    vbak=_load("sap_sd","vbak"); sl=_load("sap_sd","status_log")
    orphans=set(sl.vbeln)-set(vbak.vbeln)
    return f"status_log has {len(orphans)} orphan vbeln" if orphans else None

@mvm_check
def mvm_atp_log_to_vbap():
    vbap=_load("sap_sd","vbap"); atp=_load("sap_sd","atp_log")
    orphans=_lk(atp)-_lk(vbap)
    return f"atp_log has {len(orphans)} orphan line keys" if orphans else None

@mvm_check
def mvm_sched_to_vbak():
    vbak=_load("sap_sd","vbak"); s=_load("sap_sd","sched_agreement")
    orphans=set(s.vbeln)-set(vbak.vbeln)
    return f"sched_agreement has {len(orphans)} orphan vbeln" if orphans else None

@mvm_check
def mvm_cpq_to_vbap():
    vbap=_load("sap_sd","vbap"); c=_load("sap_sd","cpq_config")
    orphans=_lk(c)-_lk(vbap)
    return f"cpq_config has {len(orphans)} orphan line keys" if orphans else None

@mvm_check
def mvm_likp_to_vbak():
    vbak=_load("sap_sd","vbak"); likp=_load("sap_sd","likp")
    orphans=set(likp.vbeln_order)-set(vbak.vbeln)
    return f"likp has {len(orphans)} orphan vbeln_order" if orphans else None

@mvm_check
def mvm_lips_to_likp_and_vbap():
    likp=_load("sap_sd","likp"); lips=_load("sap_sd","lips"); vbap=_load("sap_sd","vbap")
    d_orphans=set(lips.vbeln_delivery)-set(likp.vbeln_delivery)
    l_orphans=_lk(lips,"vbeln_order","posnr_order")-_lk(vbap)
    problems=[]
    if d_orphans: problems.append(f"{len(d_orphans)} orphan delivery keys")
    if l_orphans: problems.append(f"{len(l_orphans)} orphan order-line keys")
    return "lips has "+" and ".join(problems) if problems else None

@mvm_check
def mvm_trim_columns_all_null():
    specs={"sched_agreement":["is_jis","is_jit","is_kanban_triggered","takt_time_seconds",
                              "cumulative_ordered_quantity","cumulative_delivered_quantity"],
           "atp_log":["is_ctp_capacity_checked","work_center_code","replenishment_lead_time_days",
                      "mrp_element_type","supply_source_reference"],
           "cpq_config":["cooling_type","hazardous_area_classification","communication_protocol",
                         "software_version","certification_marks"]}
    for tbl,cols in specs.items():
        d=_load("sap_sd",tbl)
        for c in cols:
            if c not in d.columns: return f"{tbl}.{c} missing (trim signal)"
            if not d[c].eq("").all(): return f"{tbl}.{c} not all-empty (trim signal broken)"
    return None

@mvm_check
def mvm_no_condition_source():
    p=config.OUTPUT_DIR/"sap_sd"
    bad=[f for f in ("prcd_elements","konv") if (p/f"{f}.csv").exists()]
    return f"pricing-condition source(s) present: {bad}" if bad else None

@mvm_check
def mvm_otd_in_range():
    likp=_load("sap_sd","likp")
    ot=(pd.to_datetime(likp.wadat_ist,format="%Y%m%d",errors="coerce")<=
        pd.to_datetime(likp.lfdat,format="%Y%m%d",errors="coerce")).mean()
    return f"delivery OTD {ot:.3f} outside 0.70-0.95" if not (0.70<=ot<=0.95) else None

def validate_mvm():
    return [r for r in (f() for f in MVM_CHECKS) if r]

if __name__=="__main__":
    fails=run()
    if fails:
        print("VALIDATION FAILED:"); [print(" -",f) for f in fails]; sys.exit(1)
    print(f"VALIDATION PASSED — {len(CHECKS)} checks")
