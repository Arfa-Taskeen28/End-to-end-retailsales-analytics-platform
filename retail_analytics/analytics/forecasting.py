"""
Sales forecasting (the "AI" layer, part 1).

Holt-Winters exponential smoothing (additive trend + weekly seasonality) forecasts
daily net sales for the next N days with confidence bands, and back-tests the last
30 days to report accuracy (MAPE). Output feeds a Power BI "actual vs forecast"
visual.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from ..config import Config, config as default_cfg


def _daily_series(cfg: Config) -> pd.Series:
    con = sqlite3.connect(cfg.warehouse_db)
    df = pd.read_sql(
        "SELECT d.date AS date, SUM(f.net_sales) AS net_sales "
        "FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key "
        "GROUP BY d.date ORDER BY d.date", con, parse_dates=["date"])
    con.close()
    s = df.set_index("date")["net_sales"].asfreq("D").fillna(0.0)
    return s


def _fit_forecast(series: pd.Series, horizon: int):
    model = ExponentialSmoothing(series, trend="add", damped_trend=True,
                                 seasonal="add", seasonal_periods=7).fit()
    fc = model.forecast(horizon)
    resid_std = float(np.std(model.resid))
    band = 1.96 * resid_std
    return model, fc, band


def _mape_backtest(series: pd.Series, horizon: int = 30) -> float:
    train, test = series.iloc[:-horizon], series.iloc[-horizon:]
    _, fc, _ = _fit_forecast(train, horizon)
    mask = test.to_numpy() > 0
    return float(np.mean(np.abs((test.to_numpy()[mask] - fc.to_numpy()[mask])
                                / test.to_numpy()[mask])) * 100)


def run_forecast(cfg: Config | None = None) -> dict:
    cfg = cfg or default_cfg
    series = _daily_series(cfg)
    h = cfg.forecast_horizon_days

    model, fc, band = _fit_forecast(series, h)
    mape = _mape_backtest(series, 30)

    hist = pd.DataFrame({
        "date": series.index.strftime("%Y-%m-%d"),
        "actual": series.to_numpy().round(2),
        "forecast": model.fittedvalues.to_numpy().round(2),
        "lower_bound": np.nan, "upper_bound": np.nan, "segment": "actual",
    })
    fut = pd.DataFrame({
        "date": fc.index.strftime("%Y-%m-%d"),
        "actual": np.nan,
        "forecast": fc.to_numpy().round(2),
        "lower_bound": (fc.to_numpy() - band).round(2),
        "upper_bound": (fc.to_numpy() + band).round(2),
        "segment": "forecast",
    })
    out = pd.concat([hist, fut], ignore_index=True)
    out.to_csv(cfg.marts_dir / "forecast_daily.csv", index=False)

    return {"horizon_days": h, "forecast_total": float(fc.sum().round(0)),
            "backtest_mape_30d": round(mape, 2)}
