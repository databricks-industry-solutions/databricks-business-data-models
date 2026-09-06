from dataclasses import dataclass
import pandas as pd, numpy as np
from faker import Faker
from . import config, utils

@dataclass
class Masters:
    customers: pd.DataFrame
    materials: pd.DataFrame
    plants: pd.DataFrame
    employees: pd.DataFrame
    calendar: pd.DataFrame
    channel_map: pd.DataFrame

def build() -> Masters:
    fake = Faker(); Faker.seed(config.SEED)
    g = utils.rng("masters")
    n_cust = config.ROWS["customers"]; n_mat = config.ROWS["materials"]

    countries = ["US","US","US","DE","FR","GB","JP","CN","IN"]  # US-weighted
    regions = {"US":"NA","DE":"EU","FR":"EU","GB":"EU","JP":"APAC","CN":"APAC","IN":"APAC"}
    ch_keys = list(config.CHANNELS.keys())
    cust = pd.DataFrame({
        "cust_seq": np.arange(1, n_cust+1),
        "kunnr": [f"CUST{i:06d}" for i in range(1, n_cust+1)],
        "sf_account_id": [f"001{i:015d}" for i in range(1, n_cust+1)],
        "name": [fake.company() for _ in range(n_cust)],
        "channel_code": g.choice(ch_keys, n_cust, p=[0.45,0.30,0.20,0.05]),
        "country_code": g.choice(countries, n_cust),
    })
    cust["region"] = cust["country_code"].map(regions)
    cust["city"] = [fake.city() for _ in range(n_cust)]
    cust["postal"] = [fake.postcode() for _ in range(n_cust)]
    cust["industry_code"] = g.choice(["OILGAS","WATER","CHEM","POWER","PHARMA","AUTO"], n_cust)
    cust["credit_limit"] = np.round(utils.lognormal_values(g, n_cust, 11.5, 0.8), 0)
    cust["is_jit"] = g.random(n_cust) < 0.08
    cust["is_edi"] = g.random(n_cust) < 0.15
    cust["order_weight"] = utils.pareto_weights(g, n_cust)

    pg = g.choice(["valve","actuator","positioner","instrument"], n_mat, p=[0.4,0.25,0.15,0.2])
    mat = pd.DataFrame({
        "mat_seq": np.arange(1, n_mat+1),
        "matnr": [f"MAT{i:06d}" for i in range(1, n_mat+1)],
        "sku_code": [f"MFC-{pg[i-1][:3].upper()}-{i:04d}" for i in range(1, n_mat+1)],
        "description": [f"{pg[i-1].title()} {fake.word()} {g.integers(1,24)}in" for i in range(1, n_mat+1)],
        "product_group": pg,
    })
    mat["product_hierarchy"] = ["H" + str(g.integers(10000,99999)) for _ in range(n_mat)]
    mat["base_uom"] = g.choice(config.UOM, n_mat, p=[0.7,0.2,0.1])
    mat["list_price"] = utils.lognormal_values(g, n_mat, 6.5, 0.9)
    mat["is_configurable"] = g.random(n_mat) < 0.15
    mat["is_serialized"] = g.random(n_mat) < 0.40

    plants = pd.DataFrame({
        "werks": ["P001","P002","P003","P004"],
        "plant_name": ["Houston TX","Ratingen DE","Nagoya JP","Pune IN"],
        "country_code": ["US","DE","JP","IN"], "region": ["NA","EU","APAC","APAC"],
    })
    n_emp = config.ROWS["employees"]
    emp = pd.DataFrame({
        "emp_seq": np.arange(1, n_emp+1),
        "emp_id": [f"E{i:05d}" for i in range(1, n_emp+1)],
        "name": [fake.name() for _ in range(n_emp)],
        "role": g.choice(["sales rep","credit analyst","service tech"], n_emp, p=[0.6,0.2,0.2]),
    })
    days = pd.date_range(config.DATE_START, config.DATE_END, freq="D")
    cal = pd.DataFrame({"d": days})
    cal["year"] = cal["d"].dt.year; cal["month"] = cal["d"].dt.month
    cal["is_otd_crunch"] = [ (y,m) in config.OTD_CRUNCH_MONTHS for y,m in zip(cal["year"],cal["month"]) ]
    ch = pd.DataFrame([{"channel_code":k,"channel_name":v} for k,v in config.CHANNELS.items()])
    return Masters(cust, mat, plants, emp, cal, ch)
