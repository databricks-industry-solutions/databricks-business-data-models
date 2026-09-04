import pandas as pd, numpy as np
from datetime import timedelta
from . import config, utils
from .masters import Masters

def generate(m: Masters, backbone: pd.DataFrame, vbap_full: pd.DataFrame) -> dict:
    g = utils.rng("fieldlink")
    END = pd.Timestamp(config.DATE_END)  # event dates must not exceed the data window
    mat_by = m.materials.set_index("matnr")
    # installed assets: serialized lines from shipped orders
    serial_lines = vbap_full[(vbap_full.is_serial) & (vbap_full.status.isin(["shipped","invoiced","closed"]))]
    n = min(config.ROWS["installed_assets"], len(serial_lines))
    src = serial_lines.sample(n=n, random_state=config.SEED).reset_index(drop=True)
    ord_by = backbone.set_index("vbeln")
    assets = pd.DataFrame({
        "asset_id":[f"AST{i:08d}" for i in range(1,n+1)],
        "serial_number":[f"SN{g.integers(10_000_000,99_999_999)}" for _ in range(n)],
        "sku_code":[mat_by.loc[mt,"sku_code"] for mt in src.matnr],
        "product_group":[mat_by.loc[mt,"product_group"] for mt in src.matnr],
        "source_order_number":src.vbeln.values,
        "customer_kunnr":[ord_by.loc[v,"kunnr"] for v in src.vbeln],
        "install_date":[utils.iso_date(min(pd.Timestamp(d)+timedelta(days=int(g.integers(5,60))), END)) for d in src.actual],
        "commissioning_status": g.choice(["commissioned","pending","failed"],n,p=[0.85,0.1,0.05]),
        "warranty_end_date":[utils.iso_date(pd.Timestamp(d)+timedelta(days=730)) for d in src.actual],
        "site_country": [m.customers.set_index('kunnr').loc[ord_by.loc[v,'kunnr'],'country_code'] for v in src.vbeln],
    })
    utils.write_csv(assets, "fieldlink", "installed_asset")

    # service orders on ~35% of assets
    so_src = assets.sample(n=min(config.ROWS["service_orders"], int(n*0.4)), random_state=config.SEED).reset_index(drop=True)
    m_so = len(so_src)
    so = pd.DataFrame({
        "service_order_id":[f"SO{i:08d}" for i in range(1,m_so+1)],
        "asset_id":so_src.asset_id.values, "serial_number":so_src.serial_number.values,
        "order_type": g.choice(["preventive","corrective","inspection","calibration"],m_so),
        "opened_date":[utils.iso_date(min(pd.Timestamp(d)+timedelta(days=int(g.integers(30,600))), END)) for d in so_src.install_date],
        "status": g.choice(["open","dispatched","completed","closed"],m_so,p=[0.1,0.1,0.4,0.4]),
        "technician": g.choice(m.employees[m.employees.role=="service tech"].name.tolist(), m_so),
        "priority": g.choice(["low","medium","high","critical"],m_so,p=[0.3,0.4,0.2,0.1]),
    })
    utils.write_csv(so, "fieldlink", "service_order")

    # visits: 1-2 per completed/closed service order
    vrows=[]
    for _, s in so[so.status.isin(["completed","closed"])].iterrows():
        for v in range(1,int(g.integers(1,3))+1):
            vrows.append({"visit_id":f"SV{len(vrows)+1:09d}","service_order_id":s.service_order_id,
                          "visit_date":utils.iso_date(min(pd.Timestamp(s.opened_date)+timedelta(days=int(g.integers(1,30))), END)),
                          "duration_hours":round(float(g.uniform(0.5,8)),1),
                          "labor_cost":round(float(g.uniform(75,900)),2),
                          "parts_cost":round(float(g.uniform(0,2500)),2),
                          "outcome":g.choice(["resolved","follow-up needed","escalated"],p=[0.7,0.2,0.1])})
    utils.write_csv(pd.DataFrame(vrows), "fieldlink", "service_visit")

    # warranty claims off corrective service orders within warranty
    wc_src = so[so.order_type=="corrective"].sample(n=min(config.ROWS["warranty_claims"], (so.order_type=="corrective").sum()), random_state=config.SEED).reset_index(drop=True)
    mwc=len(wc_src)
    wc = pd.DataFrame({
        "claim_id":[f"WC{i:07d}" for i in range(1,mwc+1)],
        "asset_id":wc_src.asset_id.values, "service_order_id":wc_src.service_order_id.values,
        "claim_date":wc_src.opened_date.values,
        "failure_mode": g.choice(["seal leak","actuator fault","sensor drift","body crack","electronics"],mwc),
        "claim_status": g.choice(["submitted","under review","approved","rejected","paid"],mwc,p=[0.1,0.2,0.3,0.15,0.25]),
        "claim_amount": np.round(utils.lognormal_values(g,mwc,6.0,0.7),2),
        "root_cause": g.choice(["manufacturing","material","misuse","wear","unknown"],mwc),
    })
    utils.write_csv(wc, "fieldlink", "warranty_claim")
    return dict(installed_asset=assets, service_order=so, warranty_claim=wc)
