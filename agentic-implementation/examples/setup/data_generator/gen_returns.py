import pandas as pd, numpy as np
from datetime import timedelta
from . import config, utils
from .masters import Masters

def generate(m: Masters, backbone: pd.DataFrame, vbap_full: pd.DataFrame) -> dict:
    g = utils.rng("returns")
    reason = pd.DataFrame([{"reason_code":c,"reason_text":t,"is_warranty":w} for c,t,w in
        [("QUAL","Quality defect",False),("WRONG","Wrong item shipped",False),
         ("DMG","Damaged in transit",False),("WARR","Warranty failure",True),
         ("OVER","Over-delivery",False),("COMM","Commercial return",False)]])
    utils.write_csv(reason, "returns_portal", "rma_reason_code")

    shipped = backbone[backbone.status.isin(["shipped","invoiced","closed"])]
    n = min(config.ROWS["rmas"], int(len(shipped)*0.07))
    src = shipped.sample(n=n, random_state=config.SEED).reset_index(drop=True)
    status = g.choice(["requested","approved","in-transit","received","credited"], n, p=[0.1,0.2,0.15,0.2,0.35])
    req = pd.DataFrame({
        "rma_number":[f"RMA{2024000+i}" for i in range(1,n+1)],
        "original_order_number":src.vbeln.values, "customer_kunnr":src.kunnr.values,
        "rma_date":[utils.iso_date(pd.Timestamp(d)+timedelta(days=int(g.integers(10,120)))) for d in src.actual],
        "reason_code": g.choice(reason.reason_code, n),
        "status":status, "return_plant": g.choice(m.plants.werks, n),
        "credit_memo_required": g.random(n)<0.8, "inspection_required": g.random(n)<0.6,
        "total_return_value": np.round(utils.lognormal_values(g,n,7.0,0.8),2),
    })
    utils.write_csv(req, "returns_portal", "rma_request")

    rrows=[]
    for _, r in req.iterrows():
        # pull real lines from the original order
        olines = vbap_full[vbap_full.vbeln==r.original_order_number]
        if len(olines)==0: continue
        pick = olines.sample(n=min(len(olines),int(g.integers(1,3))), random_state=int(g.integers(0,1_000_000)))
        for ln,(_,l) in enumerate(pick.iterrows(), start=1):
            qty=int(g.integers(1,int(l.kwmeng)+1))
            insp = g.choice(["accepted","rejected","scrap"]) if r.status in ("received","credited") else ""
            rrows.append({"rma_line_id":f"RL{len(rrows)+1:010d}","rma_number":r.rma_number,
                          "line_number":ln*10,"sku_code":m.materials.set_index('matnr').loc[l.matnr,'sku_code'],
                          "returned_quantity":qty,"uom":l.vrkme,
                          "reason_code":r.reason_code,"inspection_result":insp,
                          "credit_value":round(float(l.netpr)*qty,2),
                          "restocking_fee":round(float(l.netpr)*qty*g.choice([0,0.1,0.15]),2),
                          "is_warranty": bool(reason.set_index('reason_code').loc[r.reason_code,'is_warranty'])})
    utils.write_csv(pd.DataFrame(rrows), "returns_portal", "rma_line")
    return dict(rma_request=req, rma_reason_code=reason)
