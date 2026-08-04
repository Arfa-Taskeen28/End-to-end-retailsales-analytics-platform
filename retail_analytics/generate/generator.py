"""
Synthetic Italian retailer — source data generator.

Produces operational-style source files (a big transactions extract + product /
store / customer masters) for "BellaCasa Retail". Sales carry a growth trend,
yearly + weekly seasonality, category-specific seasonality, promotions, returns,
and a few *planted* anomalies (a store closure, a viral product, a regional dip)
so the forecasting + anomaly-detection layer has real signal to find.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import CATEGORIES, STORE_LOCATIONS, Config, config as default_cfg

BRANDS = ["Aurora", "Moretti", "Vela", "Nord", "Prisma", "Fiore", "Kappe", "Rialto"]
LOYALTY = ["Bronze", "Silver", "Gold", "Platinum"]
AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

# monthly seasonality per category (index 0=Jan .. 11=Dec)
CAT_SEASON = {
    "Abbigliamento": [.8, .8, 1.1, 1.2, 1.0, .9, .8, .7, 1.2, 1.2, 1.1, 1.5],
    "Elettronica":   [.9, .8, .9, .9, .9, .9, .9, .9, 1.1, 1.0, 1.6, 1.8],
    "Casa & Arredo": [1.0, .9, 1.0, 1.0, 1.1, 1.0, .9, .8, 1.0, 1.1, 1.1, 1.4],
    "Alimentari":    [1.0, .95, 1.0, 1.0, 1.0, 1.0, 1.05, 1.0, 1.0, 1.0, 1.05, 1.3],
    "Bellezza":      [.9, 1.1, 1.0, 1.0, 1.1, 1.0, .9, .8, 1.0, 1.0, 1.2, 1.5],
    "Sport":         [1.3, 1.0, 1.1, 1.1, 1.2, 1.3, 1.2, .9, 1.0, 1.0, .9, 1.0],
}


def _make_products(cfg: Config, rng) -> pd.DataFrame:
    cats = list(CATEGORIES)
    rows = []
    for i in range(cfg.n_products):
        cat = cats[i % len(cats)] if i < len(cats) else rng.choice(cats)
        subs, (pmin, pmax), margin = CATEGORIES[cat]
        price = round(float(np.exp(rng.uniform(np.log(pmin), np.log(pmax)))), 2)
        cost = round(price * (1 - margin) * rng.uniform(0.9, 1.1), 2)
        sub = rng.choice(subs)
        brand = rng.choice(BRANDS)
        rows.append({
            "product_id": f"P{i+1:04d}",
            "product_name": f"{sub} {brand} {rng.integers(100, 999)}",
            "category": cat, "subcategory": sub, "brand": brand,
            "list_price": price, "unit_cost": min(cost, price - 0.5),
            "popularity": float(rng.uniform(0.3, 1.0)),
        })
    return pd.DataFrame(rows)


def _make_stores(cfg: Config, rng) -> pd.DataFrame:
    rows = []
    for i, (city, region, stype) in enumerate(STORE_LOCATIONS[: cfg.n_stores]):
        size = {"Flagship": 1.8, "Standard": 1.0, "Outlet": 0.7}[stype]
        rows.append({
            "store_id": f"S{i+1:02d}",
            "store_name": f"{cfg.retailer_name} {city}",
            "city": city, "region": region, "store_type": stype,
            "open_date": (pd.Timestamp("2015-01-01") +
                          pd.Timedelta(days=int(rng.integers(0, 2500)))).date().isoformat(),
            "size_weight": size * rng.uniform(0.85, 1.15),
        })
    return pd.DataFrame(rows)


def _make_customers(cfg: Config, rng, cities) -> pd.DataFrame:
    n = cfg.n_customers
    tier = rng.choice(LOYALTY, n, p=[0.5, 0.3, 0.15, 0.05])
    propensity = {"Bronze": 0.6, "Silver": 1.0, "Gold": 1.8, "Platinum": 3.0}
    start = pd.Timestamp(cfg.start_date)
    return pd.DataFrame({
        "customer_id": [f"C{i+1:06d}" for i in range(n)],
        "gender": rng.choice(["F", "M", "N/D"], n, p=[0.52, 0.46, 0.02]),
        "age_band": rng.choice(AGE_BANDS, n, p=[.15, .28, .22, .17, .11, .07]),
        "city": rng.choice(cities, n),
        "loyalty_tier": tier,
        "signup_date": [(start - pd.Timedelta(days=int(d))).date().isoformat()
                        for d in rng.integers(0, 2000, n)],
        "propensity": np.array([propensity[t] for t in tier]) * rng.uniform(0.6, 1.4, n),
    })


def _transactions(cfg: Config, rng, products, stores, customers) -> pd.DataFrame:
    dates = pd.date_range(cfg.start_date, cfg.end_date, freq="D")
    months = pd.PeriodIndex(dates, freq="M").unique()
    # trend: +30% growth across the horizon, applied per month
    trend = np.linspace(1.0, 1.30, len(months))
    glob_season = np.array([np.mean([CAT_SEASON[c][m.month - 1] for c in CATEGORIES])
                            for m in months])
    month_weight = trend * glob_season
    n_per_month = (cfg.n_transactions * month_weight / month_weight.sum()).astype(int)

    prod = products.reset_index(drop=True)
    prod_cat = prod["category"].to_numpy()
    prod_pop = prod["popularity"].to_numpy()
    store_w = stores["size_weight"].to_numpy() / stores["size_weight"].sum()
    cust_w = customers["propensity"].to_numpy() / customers["propensity"].sum()
    dow_w = np.array([0.9, 0.9, 0.95, 1.0, 1.25, 1.5, 1.2])  # Mon..Sun

    parts = []
    for mi, per in enumerate(months):
        nm = n_per_month[mi]
        if nm <= 0:
            continue
        mdays = dates[(dates.year == per.year) & (dates.month == per.month)]
        dw = dow_w[mdays.dayofweek.to_numpy()]
        d_idx = rng.choice(len(mdays), nm, p=dw / dw.sum())
        tx_date = mdays[d_idx]

        # product weights this month = popularity x category seasonality
        pw = prod_pop * np.array([CAT_SEASON[c][per.month - 1] for c in prod_cat])
        p_idx = rng.choice(len(prod), nm, p=pw / pw.sum())
        s_idx = rng.choice(len(stores), nm, p=store_w)
        c_idx = rng.choice(len(customers), nm, p=cust_w)
        qty = 1 + rng.poisson(0.5, nm)

        parts.append(pd.DataFrame({
            "date": tx_date,
            "product_id": prod["product_id"].to_numpy()[p_idx],
            "store_id": stores["store_id"].to_numpy()[s_idx],
            "customer_id": customers["customer_id"].to_numpy()[c_idx],
            "quantity": qty,
            "_cat": prod_cat[p_idx],
            "_list_price": prod["list_price"].to_numpy()[p_idx],
        }))
    tx = pd.concat(parts, ignore_index=True)

    # promotions: seasonal sales windows + random product promos
    month = tx["date"].dt.month
    promo = np.zeros(len(tx))
    promo[np.isin(month, [7])] = 0.20                     # saldi estivi (summer)
    promo[np.isin(month, [1])] = 0.25                     # saldi invernali (winter)
    black_friday = (month == 11) & (tx["date"].dt.day >= 20)
    promo[black_friday.to_numpy()] = 0.30
    rand_promo = rng.random(len(tx)) < 0.10               # sporadic product promos
    promo = np.where(rand_promo, np.maximum(promo, rng.uniform(0.1, 0.35, len(tx))), promo)
    tx["discount_pct"] = np.round(promo, 2)
    # promos lift volume
    tx.loc[tx["discount_pct"] > 0, "quantity"] += rng.poisson(0.4, int((tx["discount_pct"] > 0).sum()))

    # returns ~3%
    tx["is_return"] = (rng.random(len(tx)) < 0.03).astype(int)

    tx["unit_price"] = tx["_list_price"]
    tx = tx.drop(columns=["_cat", "_list_price"])
    tx = _plant_anomalies(cfg, rng, tx, stores)
    tx = tx.sort_values("date").reset_index(drop=True)
    tx.insert(0, "transaction_id", np.arange(1, len(tx) + 1))
    tx["date"] = tx["date"].dt.date.astype(str)
    return tx


def _plant_anomalies(cfg, rng, tx, stores):
    d = pd.to_datetime(tx["date"])
    # 1) store closure (2 weeks, sales -> 0 for one store)
    closed_store = stores["store_id"].iloc[3]
    win = (d >= "2025-03-10") & (d <= "2025-03-24") & (tx["store_id"] == closed_store)
    tx = tx.loc[~win.to_numpy()].copy()
    d = pd.to_datetime(tx["date"])
    # 2) viral product spike (x5 volume for one product for a month)
    hot = tx["product_id"].mode().iloc[0]
    spike = (d >= "2024-11-15") & (d <= "2024-12-15") & (tx["product_id"] == hot)
    extra = pd.concat([tx.loc[spike.to_numpy()]] * 4, ignore_index=True)
    tx = pd.concat([tx, extra], ignore_index=True)
    d = pd.to_datetime(tx["date"])
    # 3) regional supply dip (drop 70% of a region's sales for 10 days)
    region_stores = stores.loc[stores["region"] == "Campania", "store_id"]
    dip = (d >= "2025-09-01") & (d <= "2025-09-10") & tx["store_id"].isin(region_stores)
    drop_idx = tx.loc[dip.to_numpy()].sample(frac=0.7, random_state=cfg.seed).index
    tx = tx.drop(index=drop_idx).reset_index(drop=True)
    return tx


def generate_all(cfg: Config | None = None) -> dict:
    cfg = cfg or default_cfg
    cfg.ensure_dirs()
    rng = np.random.default_rng(cfg.seed)

    products = _make_products(cfg, rng)
    stores = _make_stores(cfg, rng)
    customers = _make_customers(cfg, rng, stores["city"].tolist())
    tx = _transactions(cfg, rng, products, stores, customers)

    # write operational-style source files (product master as Excel)
    products.drop(columns=["popularity"]).to_excel(
        cfg.raw_dir / "products.xlsx", index=False)
    stores.drop(columns=["size_weight"]).to_csv(cfg.raw_dir / "stores.csv", index=False)
    customers.drop(columns=["propensity"]).to_csv(cfg.raw_dir / "customers.csv", index=False)
    tx.to_csv(cfg.raw_dir / "transactions.csv", index=False)

    return {"products": len(products), "stores": len(stores),
            "customers": len(customers), "transactions": len(tx)}
