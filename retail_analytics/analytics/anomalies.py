"""
Anomaly detection (the "AI" layer, part 2).

Flags abnormal store-day sales with a robust rolling baseline: expected = trailing
median, deviation scored by rolling MAD (median absolute deviation, outlier-proof).
Catches the planted incidents — a store closure, a demand dip — that a simple
threshold would miss. Output feeds a Power BI "anomaly monitor" page.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from ..config import Config, config as default_cfg

WINDOW = 28          # trailing days for the baseline
Z_THRESHOLD = 3.5    # robust z beyond which a day is anomalous


def _store_daily(cfg: Config) -> pd.DataFrame:
    con = sqlite3.connect(cfg.warehouse_db)
    df = pd.read_sql(
        "SELECT d.date AS date, s.store_id, s.store_name, s.region, "
        "       SUM(f.net_sales) AS net_sales "
        "FROM fact_sales f "
        "JOIN dim_date d  ON f.date_key=d.date_key "
        "JOIN dim_store s ON f.store_key=s.store_key "
        "GROUP BY d.date, s.store_id ORDER BY s.store_id, d.date",
        con, parse_dates=["date"])
    con.close()
    return df


def run_anomaly_detection(cfg: Config | None = None) -> dict:
    cfg = cfg or default_cfg
    df = _store_daily(cfg)

    # Reindex each store to the full calendar filling 0 — otherwise a closed
    # store's missing days would be a gap the detector can't see (rather than a
    # visible collapse to zero sales).
    full_dates = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    meta = df.groupby("store_id")[["store_name", "region"]].first()

    out = []
    for sid, g in df.groupby("store_id"):
        s = g.set_index("date")["net_sales"].reindex(full_dates, fill_value=0.0)
        med = s.rolling(WINDOW, min_periods=10).median()
        mad = (s - med).abs().rolling(WINDOW, min_periods=10).median()
        z = (s - med) / (1.4826 * mad.replace(0, np.nan))
        out.append(pd.DataFrame({
            "date": full_dates, "store_id": sid,
            "store_name": meta.loc[sid, "store_name"], "region": meta.loc[sid, "region"],
            "net_sales": s.to_numpy().round(2), "expected": med.to_numpy().round(2),
            "robust_z": z.to_numpy().round(2),
            "is_anomaly": (z.abs() >= Z_THRESHOLD).astype(int).to_numpy(),
            "direction": np.where(z < 0, "dip", "spike"),
        }))

    res = pd.concat(out, ignore_index=True)
    res["date"] = res["date"].dt.strftime("%Y-%m-%d")
    res.to_csv(cfg.marts_dir / "anomalies.csv", index=False)

    flagged = res[res["is_anomaly"] == 1]
    return {"store_days": len(res), "anomalies": int(res["is_anomaly"].sum()),
            "top_anomaly_stores": flagged["store_name"].value_counts()
                                  .head(3).to_dict()}
