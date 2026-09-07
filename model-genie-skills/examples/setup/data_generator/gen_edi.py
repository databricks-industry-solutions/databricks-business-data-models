import pandas as pd, numpy as np
from . import config, utils
from .masters import Masters

def generate(m: Masters, backbone: pd.DataFrame) -> dict:
    g = utils.rng("edi")
    edi_custs = m.customers[m.customers.is_edi]
    tp = pd.DataFrame({
        "partner_id":[f"TP{i:04d}" for i in range(1,len(edi_custs)+1)],
        "partner_kunnr":edi_custs.kunnr.values, "partner_name":edi_custs.name.values,
        "qualifier": g.choice(["ZZ","01","14"], len(edi_custs)),
        "standard": g.choice(["X12","EDIFACT"], len(edi_custs)),
        "van": g.choice(["OpenText","SPS","Cleo"], len(edi_custs)),
    })
    utils.write_csv(tp, "edi_gateway", "trading_partner")

    edi_orders = backbone[backbone.is_edi]
    n = min(config.ROWS["edi_messages"], len(edi_orders)*2)
    src = edi_orders.sample(n=n, replace=True, random_state=config.SEED).reset_index(drop=True)
    tp_by = tp.set_index("partner_kunnr")
    msg_type = g.choice(["ORDERS","ORDRSP","ORDCHG"], n, p=[0.6,0.3,0.1])
    status = g.choice(["received","validated","mapped","posted","error"], n, p=[0.05,0.1,0.1,0.7,0.05])
    log = pd.DataFrame({
        "message_id":[f"MSG{i:010d}" for i in range(1,n+1)],
        "order_number":src.vbeln.values,
        "partner_id":[tp_by.loc[k,"partner_id"] if k in tp_by.index else "" for k in src.kunnr],
        "direction": np.where(msg_type=="ORDRSP","outbound","inbound"),
        "message_type":msg_type, "standard": g.choice(["X12","EDIFACT"],n),
        "transmission_ts":[utils.iso_date(d) for d in src.order_date],
        "processing_status":status,
        "error_code": np.where(status=="error", g.choice(["E01","E02","E03"],n), ""),
        "ack_status": np.where(status=="posted","997-accepted","pending"),
        "interchange_control": [f"{g.integers(100000000,999999999)}" for _ in range(n)],
    })
    utils.write_csv(log, "edi_gateway", "edi_message_log")
    return dict(trading_partner=tp, edi_message_log=log)
