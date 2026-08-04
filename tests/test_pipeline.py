"""End-to-end pipeline tests: generation, warehouse integrity, analytics."""
from __future__ import annotations

import sqlite3

import pandas as pd


def test_raw_files_generated(cfg):
    assert (cfg.raw_dir / "products.xlsx").exists()
    assert (cfg.raw_dir / "transactions.csv").exists()
    tx = pd.read_csv(cfg.raw_dir / "transactions.csv")
    assert len(tx) > 1000
    assert {"date", "product_id", "store_id", "customer_id", "quantity"} <= set(tx.columns)


def test_star_schema_integrity(cfg):
    con = sqlite3.connect(cfg.warehouse_db)
    # every fact key resolves to a dimension (no orphans)
    for dim, key in [("dim_product", "product_key"), ("dim_store", "store_key"),
                     ("dim_customer", "customer_key"), ("dim_date", "date_key")]:
        orphans = pd.read_sql(
            f"SELECT COUNT(*) c FROM fact_sales f "
            f"LEFT JOIN {dim} d ON f.{key}=d.{key} WHERE d.{key} IS NULL", con).iloc[0, 0]
        assert orphans == 0, f"orphan {key}"
    # returns are stored negative -> they reduce totals
    neg = pd.read_sql("SELECT COUNT(*) c FROM fact_sales WHERE is_return=1 AND net_sales>0",
                      con).iloc[0, 0]
    assert neg == 0
    con.close()


def test_dim_date_covers_forecast_horizon(cfg):
    con = sqlite3.connect(cfg.warehouse_db)
    d = pd.read_sql("SELECT MAX(date) md FROM dim_date", con).iloc[0, 0]
    f = pd.read_sql("SELECT MAX(d.date) md FROM fact_sales f "
                    "JOIN dim_date d ON f.date_key=d.date_key", con).iloc[0, 0]
    con.close()
    # calendar extends past the sales data (so forecast dates join)
    assert pd.Timestamp(d) > pd.Timestamp(f)


def test_forecast_output(cfg):
    fc = pd.read_csv(cfg.marts_dir / "forecast_daily.csv")
    assert (fc["segment"] == "forecast").sum() == cfg.forecast_horizon_days
    fut = fc[fc["segment"] == "forecast"]
    assert (fut["upper_bound"] >= fut["forecast"]).all()
    assert (fut["forecast"] >= fut["lower_bound"]).all()


def test_anomalies_output(cfg):
    a = pd.read_csv(cfg.marts_dir / "anomalies.csv")
    assert set(a["is_anomaly"].unique()) <= {0, 1}
    assert a["is_anomaly"].sum() >= 1
    assert set(a["direction"].unique()) <= {"dip", "spike"}
