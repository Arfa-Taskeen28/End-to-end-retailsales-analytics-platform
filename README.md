# End-to-End Retail Sales Analytics Platform

A complete **Excel → SQL → Power BI** analytics platform for a multi-store Italian
retailer, with an **AI layer** (sales forecasting + anomaly detection) surfaced in
the dashboard. Built to mirror exactly what Italian *Analista Dati / BI Analyst*
roles ask for: **advanced Excel, SQL, a star-schema data model, DAX, and forecasting**.

```
raw source files            SQL star-schema warehouse         AI layer                 Power BI
(Excel + CSV extracts) ─▶  ETL → dim_* + fact_sales  ─▶  forecasting + anomalies  ─▶  dashboard
 products / stores /        (SQLite runnable +              (Holt-Winters,            (DAX model,
 customers / 700k tx)        PostgreSQL scripts)             robust anomaly z)          RLS, forecast)
```

---

## What's in the box

| Layer | What it does | Tech |
|---|---|---|
| **Data generation** | A realistic Italian retailer ("BellaCasa Retail"): 18 stores across Italian regions, 60 products in 6 categories, 8,000 customers, **~700k transactions** over 3 years with trend, seasonality, promotions, returns, and *planted anomalies*. | Python, pandas, NumPy, openpyxl |
| **SQL warehouse** | A proper **star schema** (`fact_sales` + `dim_date/product/store/customer`) with surrogate keys, an Italian calendar (holidays), and returns as negative measures. Runnable in **SQLite**, portable to **PostgreSQL**. | SQL (DDL + window-function analytics), SQLite |
| **AI layer** | **Holt-Winters** forecast of daily sales (90-day horizon, confidence bands, ~**7% back-test MAPE**) + **robust anomaly detection** (rolling median/MAD z-score) that catches a planted store closure & demand dip. | statsmodels |
| **Power BI** | A full build: data model, a **copy-paste DAX measure library** (KPIs, time-intelligence, RFM, forecast, RLS), and a 6-page report guide. | Power BI, DAX |

## Results (from `python -m retail_analytics.cli all`)
- **701,330** transactions → star-schema warehouse (0 orphan keys) in ~30 s —
  **€77.6 M** net sales, **€24.8 M** gross margin over 3 years.
- Daily sales **forecast** with **~7% MAPE** (30-day back-test).
- **Anomaly detection** flags the planted incidents (e.g. a 2-week store closure).
- Power BI-ready **marts** exported to `data/marts/`.

---

## Quickstart

```bash
python -m venv .venv        # activate it
pip install -r requirements.txt

python -m retail_analytics.cli all     # generate -> SQL warehouse -> forecast + anomalies (~30s)
```
Outputs:
- `data/warehouse.db` — the SQLite star-schema warehouse
- `data/marts/*.csv` — Power BI-ready tables (`fact_sales`, `dim_*`, `forecast_daily`, `anomalies`)
- `data/raw/*` — the operational-style source files (products as **Excel**)

Then build the report by following **[`powerbi/BUILD_GUIDE.md`](powerbi/BUILD_GUIDE.md)**
(with **[`powerbi/DATA_MODEL.md`](powerbi/DATA_MODEL.md)** and the copy-paste
**[`powerbi/DAX_MEASURES.md`](powerbi/DAX_MEASURES.md)**).

### SQL
- `sql/sqlite/schema.sql`, `sql/postgres/schema.sql` — the star-schema DDL.
- `sql/analytics.sql` — analytical queries (YoY via `LAG`, store ranking via `RANK`,
  category share, 7-day moving average, **RFM segmentation** via `NTILE`).

### Tests
```bash
pytest -q                   # generation, star-schema integrity, forecast, anomalies
```

---

## Project layout
```
retail_analytics/
  config.py                 the simulated retailer + paths
  generate/generator.py     synthetic Italian retail source data
  warehouse/etl.py          raw -> star schema (SQLite) + marts (CSV)
  analytics/
    forecasting.py          Holt-Winters daily forecast + back-test MAPE
    anomalies.py            robust rolling-MAD anomaly detection
  cli.py                    generate -> ETL -> analytics
sql/                        DDL (SQLite + PostgreSQL) + analytical queries
powerbi/                    DATA_MODEL.md · DAX_MEASURES.md · BUILD_GUIDE.md
tests/                      pipeline + warehouse integrity tests
```

## Why this project
It is the exact stack Italian analyst/BI job posts list — **Excel + SQL +
Power BI/Tableau + forecasting** — done *end-to-end and properly*: real dimensional
modelling, a DAX measure library with time-intelligence and RLS, and an AI layer
that turns the dashboard from "reporting" into "decision support".

## Roadmap / extensions
- Per-category and per-store forecasts; promo-uplift modelling.
- A natural-language-to-SQL assistant over the warehouse ("chat with your data").
- dbt for the transformations; Microsoft Fabric (Lakehouse + Copilot) variant.
- Publish to the Power BI Service with scheduled + incremental refresh.
