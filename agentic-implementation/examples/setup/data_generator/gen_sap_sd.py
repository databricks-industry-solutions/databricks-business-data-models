import pandas as pd, numpy as np
from datetime import timedelta
from . import config, utils
from .masters import Masters


def _masters_tables(m: Masters):
    kna1 = pd.DataFrame({
        "kunnr": m.customers.kunnr, "name1": m.customers.name,
        "land1": m.customers.country_code, "regio": m.customers.region,
        "ort01": m.customers.city, "pstlz": m.customers.postal,
        "brsch": m.customers.industry_code,  # industry key (code)
        "ktokd": m.customers.channel_code,   # account group ~ channel
    })
    knvv = pd.DataFrame({
        "kunnr": m.customers.kunnr, "vkorg": "1000", "vtweg": m.customers.channel_code,
        "spart": "00", "klimk": m.customers.credit_limit.map(utils.sap_amount),
        "zterm": np.random.default_rng(1).choice(list(config.PAYMENT_TERMS), len(m.customers)),
        "inco1": np.random.default_rng(2).choice(list(config.INCOTERMS), len(m.customers)),
    })
    mara = pd.DataFrame({
        "matnr": m.materials.matnr, "matkl": m.materials.product_group,
        "prdha": m.materials.product_hierarchy, "meins": m.materials.base_uom,
        "kzkfg": m.materials.is_configurable.map({True:"X",False:""}),
    })
    makt = pd.DataFrame({"matnr": m.materials.matnr, "spras":"E", "maktx": m.materials.description})
    t001w = pd.DataFrame({"werks": m.plants.werks, "name1": m.plants.plant_name, "land1": m.plants.country_code})
    tvakt = pd.DataFrame([{"auart":k,"vtext":v} for k,v in config.ORDER_TYPES.items()])
    tinct = pd.DataFrame([{"inco1":k,"bezei":v} for k,v in config.INCOTERMS.items()])
    t052u = pd.DataFrame([{"zterm":k,"text1":v} for k,v in config.PAYMENT_TERMS.items()])
    for name, df in [("kna1",kna1),("knvv",knvv),("mara",mara),("makt",makt),
                     ("t001w",t001w),("tvakt",tvakt),("tinct",tinct),("t052u",t052u)]:
        utils.write_csv(df, "sap_sd", name)
    return dict(kna1=kna1,knvv=knvv,mara=mara,makt=makt,t001w=t001w,tvakt=tvakt,tinct=tinct,t052u=t052u)


def _config_tables(m: Masters):
    # sales areas = vkorg x vtweg x spart combos actually used
    areas = []
    for vtweg in config.CHANNELS:
        areas.append({"vkorg":"1000","vtweg":vtweg,"spart":"00",
                      "waers":"USD","kalks":"1","bezei":f"US {config.CHANNELS[vtweg]}"})
    tvta = pd.DataFrame(areas)
    zsd = pd.DataFrame([{
        "vtweg":k,"chan_name":v,
        "credit_check_req":"X" if k in ("20","30") else "",
        "edi_capable":"X" if k in ("20","40") else "",
        "min_order_val": utils.sap_amount(500 if k=="10" else 1000),
        "pricing_proc":"ZVAA01","pay_terms":"NT30","inco":"FCA",
    } for k,v in config.CHANNELS.items()])
    reasons = [("100","order","New project"),("101","order","Repeat business"),
               ("900","rejection","Price too high"),("901","rejection","Lost to competitor"),
               ("902","rejection","Lead time"),("950","cancellation","Customer cancelled"),
               ("960","return","Quality defect"),("961","return","Wrong item shipped")]
    tvaut = pd.DataFrame([{"augru":c,"category":cat,"bezei":t} for c,cat,t in reasons])
    for name, df in [("tvta",tvta),("zsd_channel_config",zsd),("tvaut",tvaut)]:
        utils.write_csv(df, "sap_sd", name)
    return dict(tvta=tvta, zsd_channel_config=zsd, tvaut=tvaut)


def _orders(m: Masters):
    g = utils.rng("sap_orders")
    n = config.ROWS["orders"]
    cust = m.customers.sample(n=n, replace=True, weights=m.customers.order_weight,
                              random_state=config.SEED).reset_index(drop=True)
    order_dates = utils.rand_dates(g, n)
    vbeln = [f"00{i:08d}" for i in range(1, n+1)]
    auart = g.choice(list(config.ORDER_TYPES), n, p=[0.7,0.05,0.05,0.15,0.05])
    # lead time 7-60 days; requested = order + lead; confirmed jitter; actual w/ OTD crunch lateness
    lead = g.integers(7, 61, n)
    req = [d + timedelta(days=int(l)) for d,l in zip(order_dates, lead)]
    conf = [r + timedelta(days=int(g.integers(-2,6))) for r in req]
    crunch = [ (pd.Timestamp(c).year, pd.Timestamp(c).month) in config.OTD_CRUNCH_MONTHS for c in conf ]
    late_bonus = [int(g.integers(3,15)) if cr and g.random()<0.6 else int(g.integers(-2,4)) for cr in crunch]
    actual = [pd.Timestamp(c)+timedelta(days=lb) for c,lb in zip(conf, late_bonus)]
    status = g.choice(config.ORDER_STATUSES, n, p=[0.1,0.15,0.15,0.2,0.3,0.1])
    backbone = pd.DataFrame({
        "vbeln":vbeln, "kunnr":cust.kunnr.values, "werks": g.choice(m.plants.werks, n),
        "order_date":order_dates, "req":req, "conf":conf, "actual":actual,
        "channel_code":cust.channel_code.values, "auart":auart, "status":status,
        "is_jit":cust.is_jit.values, "is_edi":cust.is_edi.values,
        "netwr": utils.lognormal_values(g, n),
    })
    vbak = pd.DataFrame({
        "vbeln":backbone.vbeln, "auart":backbone.auart, "vtweg":backbone.channel_code,
        "vkorg":"1000","spart":"00","kunnr":backbone.kunnr, "werks":backbone.werks,
        "erdat":[utils.sap_date(d) for d in backbone.order_date],
        "vdatu":[utils.sap_date(d) for d in backbone.req],   # requested delivery
        "audat":[utils.sap_date(d) for d in backbone.conf],  # confirmed
        "netwr":backbone.netwr.map(utils.sap_amount),
        "waerk": g.choice(config.CURRENCIES, n, p=[0.6,0.25,0.1,0.05]),
        "inco1": g.choice(list(config.INCOTERMS), n),
        "zterm": g.choice(list(config.PAYMENT_TERMS), n),
        "gbstk":backbone.status,  # overall processing status
        "augru": g.choice(["100","101"], n),
        "bstnk":[f"PO{g.integers(100000,999999)}" for _ in range(n)],  # customer PO
        "vsbed": g.choice(["01","02","03"], n),  # shipping condition
    })
    utils.write_csv(vbak, "sap_sd", "vbak")
    return backbone, vbak


def _lines(m: Masters, backbone):
    g = utils.rng("sap_lines")
    rows = []
    for _, o in backbone.iterrows():
        nlines = int(g.integers(1, 6))
        for ln in range(1, nlines+1):
            mat = m.materials.sample(1, random_state=int(g.integers(0,1_000_000))).iloc[0]
            qty = int(g.integers(1, 50))
            rows.append({"vbeln":o.vbeln, "posnr":f"{ln*10:06d}", "matnr":mat.matnr,
                         "werks":o.werks, "kwmeng":qty, "vrkme":mat.base_uom,
                         "netpr":mat.list_price, "list_price":mat.list_price,
                         "req":o.req, "conf":o.conf, "actual":o.actual, "status":o.status,
                         "is_config":mat.is_configurable, "is_serial":mat.is_serialized})
    vbap_full = pd.DataFrame(rows)
    vbap_full["posnr_int"] = range(1, len(vbap_full)+1)
    vbap_full["line_net"] = vbap_full.kwmeng * vbap_full.netpr
    vbap = pd.DataFrame({
        "vbeln":vbap_full.vbeln, "posnr":vbap_full.posnr, "matnr":vbap_full.matnr,
        "werks":vbap_full.werks, "kwmeng":vbap_full.kwmeng.map(utils.sap_amount),
        "vrkme":vbap_full.vrkme, "netpr":vbap_full.netpr.map(utils.sap_amount),
        "netwr":vbap_full.line_net.map(utils.sap_amount),
        "abgru":"",  # rejection reason (mostly blank)
        "pstyv": np.where(vbap_full.is_config, "TAC", "TAN"),  # item category
        "uepos":"", "charg":"", "serail": np.where(vbap_full.is_serial,"0001",""),
    })
    utils.write_csv(vbap, "sap_sd", "vbap")
    # schedule lines: 1-2 per line
    srows = []
    for _, l in vbap_full.iterrows():
        for e in range(1, int(g.integers(1,3))+1):
            srows.append({"vbeln":l.vbeln,"posnr":l.posnr,"etenr":f"{e:04d}",
                          "edatu":utils.sap_date(l.conf), "wadat":utils.sap_date(l.actual),
                          "bmeng":utils.sap_amount(l.kwmeng), "wmeng":utils.sap_amount(l.kwmeng),
                          "lifsp":"" })
    vbep = pd.DataFrame(srows)
    utils.write_csv(vbep, "sap_sd", "vbep")
    order_net = vbap_full.groupby("vbeln", sort=False)["line_net"].sum()
    return vbap_full, vbap, vbep, order_net


def _partners(m: Masters, backbone):
    g = utils.rng("sap_partners")
    cust_by_kunnr = m.customers.set_index("kunnr")
    rows = []
    for _, o in backbone.iterrows():
        c = cust_by_kunnr.loc[o.kunnr]
        for parvw, nm in [("AG","Sold-To"),("WE","Ship-To"),("RE","Bill-To")]:
            rows.append({"vbeln":o.vbeln,"parvw":parvw,"kunnr":o.kunnr,"name1":c["name"],
                         "land1":c.country_code,"ort01":c.city,"pstlz":c.postal,
                         "adrnr":f"AD{g.integers(100000,999999)}","func_desc":nm})
    vbpa = pd.DataFrame(rows)
    utils.write_csv(vbpa, "sap_sd", "vbpa")
    return vbpa


def _credit(m: Masters, backbone):
    g = utils.rng("sap_credit"); cust_by = m.customers.set_index("kunnr")
    # credit checks only on distributor/dealer channels + a sample of others
    subset = backbone[(backbone.channel_code.isin(["20","30"])) | (g.random(len(backbone))<0.2)]
    subset = subset.head(config.ROWS["credit_checks"])
    rows=[]
    for _, o in subset.iterrows():
        lim = float(cust_by.loc[o.kunnr].credit_limit)
        exp_before = round(g.random()*lim*0.8,2); val=float(o.netwr)
        result = "blocked" if exp_before+val>lim else ("warning" if exp_before+val>lim*0.9 else "approved")
        rows.append({"vbeln":o.vbeln,"kunnr":o.kunnr,"check_ts":utils.sap_date(o.order_date),
                     "check_type":g.choice(["static","dynamic","maxdoc"]),"klimk":utils.sap_amount(lim),
                     "exp_before":utils.sap_amount(exp_before),"order_val":utils.sap_amount(val),
                     "exp_after":utils.sap_amount(exp_before+val),"result":result,
                     "kkber":"1000","ctlpc":g.choice(["001","002","003"])})
    z = pd.DataFrame(rows); utils.write_csv(z,"sap_sd","zcredit_log"); return z


def _contracts(m: Masters):
    g = utils.rng("sap_contracts"); n=config.ROWS["contracts"]
    cust = m.customers[m.customers.channel_code.isin(["10","20"])].sample(n=n, replace=True, random_state=config.SEED)
    start = utils.rand_dates(g, n, end=config.DATE_END)
    veda = pd.DataFrame({
        "vbeln":[f"40{i:08d}" for i in range(1,n+1)], "kunnr":cust.kunnr.values,
        "vtweg":cust.channel_code.values, "kbtyp":g.choice(["QC","VC","ZS"],n),  # qty/value/sched-agmt
        "vbegdat":[utils.sap_date(d) for d in start],
        "venddat":[utils.sap_date(pd.Timestamp(d)+timedelta(days=365)) for d in start],
        "zmeng":[utils.sap_amount(x) for x in g.integers(100,5000,n)],
        "target_val":[utils.sap_amount(x) for x in utils.lognormal_values(g,n,10.5,0.7)],
        "vstat":g.choice(["active","expired","cancelled"],n,p=[0.7,0.2,0.1])})
    utils.write_csv(veda,"sap_sd","veda")
    irows=[]
    for _, c in veda.iterrows():
        for ln in range(1,int(g.integers(1,6))+1):
            mat=m.materials.sample(1,random_state=int(g.integers(0,1_000_000))).iloc[0]
            irows.append({"vbeln":c.vbeln,"posnr":f"{ln*10:06d}","matnr":mat.matnr,
                          "zmeng":utils.sap_amount(g.integers(50,1000)),
                          "target_val":utils.sap_amount(mat.list_price*g.integers(50,1000)),
                          "netpr":utils.sap_amount(mat.list_price)})
    veda_item=pd.DataFrame(irows); utils.write_csv(veda_item,"sap_sd","veda_item"); return veda, veda_item


def generate(m: Masters) -> dict:
    out = {}
    out.update(_masters_tables(m))
    out.update(_config_tables(m))
    backbone, vbak = _orders(m)
    vbap_full, vbap, vbep, order_net = _lines(m, backbone)
    # Reconcile header total to the sum of its line net values (real SAP VBAK.NETWR behavior).
    # Patch the backbone first so _credit sees the reconciled value, then rewrite vbak.netwr.
    backbone["netwr"] = backbone.vbeln.map(order_net).astype(float)
    vbak["netwr"] = backbone["netwr"].map(utils.sap_amount).values
    utils.write_csv(vbak, "sap_sd", "vbak")
    out["vbak"]=vbak; out["_backbone"]=backbone
    out["vbap"]=vbap; out["vbep"]=vbep; out["_vbap_full"]=vbap_full
    out["vbpa"]=_partners(m, backbone)
    out["zcredit_log"]=_credit(m, backbone)
    veda, veda_item=_contracts(m); out["veda"]=veda; out["veda_item"]=veda_item
    return out
