# Power BI Build Guide

Build the `.pbix` in ~1–2 hours by following these steps. Everything upstream
(data, warehouse, forecast, anomalies) is produced by `python -m retail_analytics.cli all`,
which writes the marts to `data/marts/`.

---

## 1 · Get data
**Option A — CSV marts (easiest):** Home → **Get data → Folder** → point at
`data/marts/` → load `dim_date`, `dim_product`, `dim_store`, `dim_customer`,
`fact_sales`, `forecast_daily`, `anomalies`. (Or **Text/CSV** each file.)

**Option B — SQL (shows the SQL story):** connect to the **PostgreSQL** database
built from `sql/postgres/schema.sql` (or the bundled `data/warehouse.db` via an
ODBC/SQLite connector). Use **Import** mode.

In **Power Query**: set data types (keys = whole number, dates = date, amounts =
decimal), verify no errors, then **Close & Apply**.

## 2 · Model
- Create the relationships in [`DATA_MODEL.md`](DATA_MODEL.md) (drag key → key;
  all one-to-many, single cross-filter).
- **Modeling → Mark as date table** → `dim_date[date]`.
- Hide key columns (`*_key`) and raw numeric columns you won't use directly.

## 3 · Measures
Add the measures from [`DAX_MEASURES.md`](DAX_MEASURES.md) (create a blank
`_Measures` table via **Enter data**, then paste). Start with §1 base + §3 time
intelligence — the rest build on those.

## 4 · Report pages

**① Executive Overview**
- KPI cards: `Total Net Sales`, `Gross Margin %`, `Sales YoY %` (with arrow),
  `Avg Order Value`, `Return Rate %`.
- Line chart: `Total Net Sales` by `dim_date[date]` (month) with `Sales PY`.
- Donut: net sales by `category`. Map: net sales by `region` (filled map of Italy).
- Slicers: Year, Region, Category.

**② Sales & Forecast**
- Line chart overlaying `Total Net Sales` (actual) and `Forecast Sales` by date;
  add `Forecast Lower`/`Forecast Upper` as a shaded band (area). Annotate MAPE ≈ 7%.
- Cards: `Rolling 3M Sales`, `Sales MoM %`.

**③ Product & Category**
- Matrix: category → subcategory → product with `Total Net Sales`, `Gross Margin`,
  `Gross Margin %`, `Total Quantity`.
- Bar: top 10 products by `Gross Margin`. Scatter: margin % vs. net sales by product.

**④ Store & Geography**
- Filled map by `region`; bar chart of stores ranked by `Total Net Sales`.
- Table: store, region, type, sales, `Sales YoY %`.

**⑤ Customers (RFM)**
- Cards: `Customer Count`, `New Customers`, `Sales per Customer`.
- Bar: net sales by `loyalty_tier` and `age_band`. (Optional: import the RFM query
  from `sql/analytics.sql` as a table for an R/F/M segment matrix.)

**⑥ Anomaly Monitor**
- Line: `net_sales` vs. `expected` (from `anomalies`) by date, sliced by store.
- Table of flagged anomalies (`is_anomaly = 1`): date, store, net sales, expected,
  `robust_z`, direction. Highlights the planted store-closure & demand dip.

## 5 · Row-Level Security
Add the **Regional Manager** role from [`DAX_MEASURES.md`](DAX_MEASURES.md) (§RLS),
then **View as → Role** to verify a manager sees only their region.

## 6 · Polish & publish
- Consistent theme, number formats (€, %, thousands), tooltips, a title bar.
- **Publish** to the Power BI Service; set scheduled refresh; for large data enable
  **incremental refresh** on `fact_sales` (range parameters on `dim_date[date]`).
- Export a couple of screenshots / a short GIF for your CV & LinkedIn.

---

### What this demonstrates to an employer
End-to-end BI: **SQL star-schema modelling → DAX measure library + time-intelligence
→ RLS → an AI layer (forecasting + anomaly detection) surfaced in the dashboard →
published, refreshable report.** Exactly the Excel + SQL + Power BI + forecasting
stack Italian analyst/BI postings ask for.
