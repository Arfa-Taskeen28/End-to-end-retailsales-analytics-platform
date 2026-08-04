"""
ETL: raw source files -> star-schema warehouse (SQLite) + Power BI marts (CSV).

Builds conformed dimensions with surrogate keys, a full calendar dim_date (with
Italian month names + public holidays), and the additive fact_sales with
row-level measures (returns reverse the sale). Executes the real DDL in
sql/sqlite/schema.sql, then loads and also exports each table as CSV for Power BI.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from ..config import REPO_ROOT, Config, config as default_cfg

MONTH_IT = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
# fixed-date Italian public holidays (month, day)
IT_HOLIDAYS = {(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15),
               (11, 1), (12, 8), (12, 25), (12, 26)}
SCHEMA_SQL = REPO_ROOT / "sql" / "sqlite" / "schema.sql"


def _season(m: int) -> str:
    return ("Inverno" if m in (12, 1, 2) else "Primavera" if m in (3, 4, 5)
            else "Estate" if m in (6, 7, 8) else "Autunno")


def _build_dim_date(dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame({
        "date_key": dates.strftime("%Y%m%d").astype(int),
        "date": dates.strftime("%Y-%m-%d"),
        "year": dates.year, "quarter": dates.quarter, "month": dates.month,
        "month_name": dates.strftime("%B"),
        "month_name_it": [MONTH_IT[m - 1] for m in dates.month],
        "week": dates.isocalendar().week.astype(int).to_numpy(),
        "day_of_week": dates.dayofweek + 1,
        "day_name": dates.strftime("%A"),
        "is_weekend": (dates.dayofweek >= 5).astype(int),
        "is_holiday": [int((d.month, d.day) in IT_HOLIDAYS) for d in dates],
        "season": [_season(m) for m in dates.month],
    })


def run_etl(cfg: Config | None = None) -> dict:
    cfg = cfg or default_cfg
    cfg.ensure_dirs()

    products = pd.read_excel(cfg.raw_dir / "products.xlsx")
    stores = pd.read_csv(cfg.raw_dir / "stores.csv")
    customers = pd.read_csv(cfg.raw_dir / "customers.csv")
    tx = pd.read_csv(cfg.raw_dir / "transactions.csv", parse_dates=["date"])

    # --- dimensions (surrogate keys) ----------------------------------------
    dim_product = products.copy(); dim_product.insert(0, "product_key",
                                                      np.arange(1, len(products) + 1))
    dim_store = stores.copy(); dim_store.insert(0, "store_key",
                                                np.arange(1, len(stores) + 1))
    dim_customer = customers.copy(); dim_customer.insert(0, "customer_key",
                                                         np.arange(1, len(customers) + 1))
    # extend the calendar past the data by the forecast horizon so forecast
    # (future) dates still join to dim_date in Power BI
    cal_end = tx["date"].max() + pd.Timedelta(days=cfg.forecast_horizon_days)
    dim_date = _build_dim_date(pd.date_range(tx["date"].min(), cal_end, freq="D"))

    # --- fact (join to keys + costs, compute measures) ----------------------
    pk = dim_product.set_index("product_id")[["product_key", "unit_cost"]]
    sk = dim_store.set_index("store_id")["store_key"]
    ck = dim_customer.set_index("customer_id")["customer_key"]

    f = tx.join(pk, on="product_id").assign(
        store_key=tx["store_id"].map(sk),
        customer_key=tx["customer_id"].map(ck),
        date_key=tx["date"].dt.strftime("%Y%m%d").astype(int),
    )
    sign = np.where(f["is_return"] == 1, -1.0, 1.0)
    gross = f["quantity"] * f["unit_price"]
    disc = gross * f["discount_pct"]
    net = gross - disc
    cost = f["quantity"] * f["unit_cost"]
    fact = pd.DataFrame({
        "sale_key": np.arange(1, len(f) + 1),
        "date_key": f["date_key"], "product_key": f["product_key"],
        "store_key": f["store_key"], "customer_key": f["customer_key"],
        "quantity": (f["quantity"] * sign).astype(int),
        "unit_price": f["unit_price"], "discount_pct": f["discount_pct"],
        "gross_sales": (gross * sign).round(2),
        "discount_amount": (disc * sign).round(2),
        "net_sales": (net * sign).round(2),
        "cost_amount": (cost * sign).round(2),
        "gross_margin": ((net - cost) * sign).round(2),
        "is_return": f["is_return"].astype(int),
    })

    # --- load into SQLite via the real DDL ----------------------------------
    conn = sqlite3.connect(cfg.warehouse_db)
    conn.executescript(SCHEMA_SQL.read_text())
    tables = {"dim_date": dim_date, "dim_product": dim_product,
              "dim_store": dim_store, "dim_customer": dim_customer,
              "fact_sales": fact}
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="append", index=False)
    conn.commit(); conn.close()

    # --- export marts for Power BI ------------------------------------------
    for name, df in tables.items():
        df.to_csv(cfg.marts_dir / f"{name}.csv", index=False)

    return {k: len(v) for k, v in tables.items()}
