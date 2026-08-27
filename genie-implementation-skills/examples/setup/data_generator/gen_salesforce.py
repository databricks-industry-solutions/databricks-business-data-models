import pandas as pd, numpy as np
from datetime import timedelta
from . import config, utils
from .masters import Masters

def generate(m: Masters, backbone: pd.DataFrame) -> dict:
    g = utils.rng("sf")
    # account: mirror of customer master with clean names + sap cross-ref
    account = pd.DataFrame({
        "account_id": m.customers.sf_account_id, "account_name": m.customers.name,
        "sap_kunnr": m.customers.kunnr, "billing_country": m.customers.country_code,
        "region": m.customers.region, "industry": m.customers.industry_code,
        "channel": m.customers.channel_code.map(config.CHANNELS),
        "annual_revenue": np.round(m.customers.credit_limit*g.uniform(3,8,len(m.customers)),0),
    })
    utils.write_csv(account, "salesforce_crm", "account")

    n_opp = config.ROWS["opportunities"]
    acc = m.customers.sample(n=n_opp, replace=True, weights=m.customers.order_weight, random_state=config.SEED).reset_index(drop=True)
    opp_dates = utils.rand_dates(g, n_opp)
    stages = g.choice(["Prospecting","Proposal","Negotiation","Closed Won","Closed Lost"], n_opp, p=[0.15,0.25,0.2,0.25,0.15])
    opportunity = pd.DataFrame({
        "opportunity_id":[f"006{i:015d}" for i in range(1,n_opp+1)],
        "opportunity_name":[f"OPP-{g.integers(10000,99999)}" for _ in range(n_opp)],
        "account_id":acc.sf_account_id.values, "created_date":[utils.iso_date(d) for d in opp_dates],
        "stage":stages, "amount":np.round(utils.lognormal_values(g,n_opp,9.0,1.0),2),
        "probability":np.where(stages=="Closed Won",100,np.where(stages=="Closed Lost",0,g.integers(10,90,n_opp))),
        "loss_reason_code": np.where(stages=="Closed Lost", g.choice(["900","901","902"],n_opp), ""),
    })
    utils.write_csv(opportunity, "salesforce_crm", "opportunity")

    # quotes: parented by opportunities that reached Proposal+; a subset link to real converted orders
    n_q = config.ROWS["quotes"]
    parent = opportunity[opportunity.stage.isin(["Proposal","Negotiation","Closed Won","Closed Lost"])].sample(n=n_q, replace=True, random_state=config.SEED).reset_index(drop=True)
    q_status = np.where(parent.stage=="Closed Won","accepted",np.where(parent.stage=="Closed Lost","rejected",g.choice(["open","expired"],n_q)))
    # Converted orders must belong to the SAME customer as the quote: map account_id -> kunnr
    # -> that customer's real orders in the backbone. Only accepted (Closed Won) quotes convert,
    # and only if the customer actually has an order; otherwise blank.
    kunnr_by_acct = m.customers.set_index("sf_account_id")["kunnr"].to_dict()
    orders_by_kunnr = backbone.groupby("kunnr")["vbeln"].apply(list).to_dict()
    conv_col = []
    for acct, status in zip(parent.account_id.values, q_status):
        cust_orders = orders_by_kunnr.get(kunnr_by_acct.get(acct), [])
        if status == "accepted" and cust_orders:
            conv_col.append(cust_orders[int(g.integers(0, len(cust_orders)))])
        else:
            conv_col.append("")
    quote = pd.DataFrame({
        "quote_id":[f"0Q0{i:015d}" for i in range(1,n_q+1)],
        "quote_number":[f"Q{2024000+i}" for i in range(1,n_q+1)],
        "opportunity_id":parent.opportunity_id.values, "account_id":parent.account_id.values,
        "quote_date":parent.created_date.values, "status":q_status,
        "valid_until":[utils.iso_date(pd.Timestamp(d)+timedelta(days=30)) for d in parent.created_date],
        "currency":g.choice(config.CURRENCIES,n_q,p=[0.6,0.25,0.1,0.05]),
        "conversion_probability":np.round(g.uniform(0,1,n_q),2),
        "converted_order_number": conv_col,
        "sales_rep": g.choice(m.employees[m.employees.role=="sales rep"].name.tolist(), n_q),
    })

    qrows=[]
    for _, qq in quote.iterrows():
        for ln in range(1,int(g.integers(1,6))+1):
            mat=m.materials.sample(1,random_state=int(g.integers(0,1_000_000))).iloc[0]
            qty=int(g.integers(1,40)); disc=round(g.uniform(0,0.2),3)
            qrows.append({"quote_line_id":f"0QL{len(qrows)+1:012d}","quote_id":qq.quote_id,
                          "line_number":ln*10,"sku_code":mat.sku_code,"material_description":mat.description,
                          "quantity":qty,"uom":mat.base_uom,"list_price":round(float(mat.list_price),2),
                          "discount_pct":disc,"net_price":round(float(mat.list_price)*(1-disc),2),
                          "net_value":round(float(mat.list_price)*(1-disc)*qty,2),"product_group":mat.product_group})
    quote_line = pd.DataFrame(qrows)
    # Reconcile quote header total to the sum of its line net values (header rolls up its lines).
    line_totals = quote_line.groupby("quote_id")["net_value"].sum()
    quote["total_amount"] = quote.quote_id.map(line_totals).fillna(0.0).round(2)
    utils.write_csv(quote, "salesforce_crm", "quote")
    utils.write_csv(quote_line, "salesforce_crm", "quote_line")

    loss = pd.DataFrame([{"loss_reason_code":c,"reason_name":n,"category":"win_loss"} for c,n in
        [("900","Price too high"),("901","Lost to competitor"),("902","Lead time too long"),("903","No budget")]])
    utils.write_csv(loss, "salesforce_crm", "loss_reason_ref")
    return dict(account=account, opportunity=opportunity, quote=quote, loss_reason_ref=loss)
