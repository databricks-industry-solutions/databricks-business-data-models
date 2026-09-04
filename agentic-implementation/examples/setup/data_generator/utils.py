import numpy as np, pandas as pd, hashlib
from datetime import timedelta
from . import config

def rng(name: str) -> np.random.Generator:
    """Deterministic per-module sub-stream: seed derived from global SEED + name."""
    h = int(hashlib.sha256(f"{config.SEED}:{name}".encode()).hexdigest()[:8], 16)
    return np.random.default_rng(h)

def sap_date(d) -> str:
    return "" if d is None or (isinstance(d, float) and np.isnan(d)) else pd.Timestamp(d).strftime("%Y%m%d")

def sap_amount(x) -> str:
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{float(x):.2f}"

def iso_date(d) -> str:
    return "" if d is None else pd.Timestamp(d).strftime("%Y-%m-%d")

def rand_dates(gen, n, start=None, end=None):
    start = start or config.DATE_START; end = end or config.DATE_END
    span = (end - start).days
    return [start + timedelta(days=int(x)) for x in gen.integers(0, span + 1, n)]

def lognormal_values(gen, n, mean_log=8.5, sigma=1.1):
    return np.round(gen.lognormal(mean_log, sigma, n), 2)

def pareto_weights(gen, n, top_frac=0.2, top_share=0.6):
    """Return a probability vector of length n where top_frac of items hold ~top_share of mass."""
    w = gen.random(n)
    cut = int(n * top_frac)
    idx = np.argsort(w)[::-1]
    weights = np.ones(n)
    weights[idx[:cut]] = (top_share / max(cut, 1)) * n
    weights[idx[cut:]] = ((1 - top_share) / max(n - cut, 1)) * n
    return weights / weights.sum()

def write_csv(df: pd.DataFrame, schema: str, table: str):
    out = config.OUTPUT_DIR / schema
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"{table}.csv", index=False)
    return len(df)
