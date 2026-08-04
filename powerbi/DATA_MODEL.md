# Data Model (star schema)

A single additive fact surrounded by conformed dimensions — the model Power BI is
happiest with (fast, simple DAX, clean filter propagation).

```mermaid
erDiagram
    dim_date     ||--o{ fact_sales : date_key
    dim_product  ||--o{ fact_sales : product_key
    dim_store    ||--o{ fact_sales : store_key
    dim_customer ||--o{ fact_sales : customer_key

    fact_sales {
        int   sale_key PK
        int   date_key FK
        int   product_key FK
        int   store_key FK
        int   customer_key FK
        int   quantity
        real  net_sales
        real  cost_amount
        real  gross_margin
        int   is_return
    }
    dim_date     { int date_key PK  date date  int year  int month  text month_name_it  int is_holiday }
    dim_product  { int product_key PK  text product_name  text category  real list_price  real unit_cost }
    dim_store    { int store_key PK  text store_name  text city  text region  text store_type }
    dim_customer { int customer_key PK  text loyalty_tier  text age_band  text city }
```

## Relationships (all single-direction, one-to-many dim → fact)

| From (dimension) | Key | To (fact) | Cardinality | Cross-filter |
|---|---|---|---|---|
| `dim_date[date_key]` | date_key | `fact_sales[date_key]` | 1 → * | single |
| `dim_product[product_key]` | product_key | `fact_sales[product_key]` | 1 → * | single |
| `dim_store[store_key]` | store_key | `fact_sales[store_key]` | 1 → * | single |
| `dim_customer[customer_key]` | customer_key | `fact_sales[customer_key]` | 1 → * | single |
| `dim_date[date]` | date | `forecast_daily[date]` | 1 → * | single |
| `dim_date[date]` | date | `anomalies[date]` | 1 → * | single |
| `dim_store[store_id]` | store_id | `anomalies[store_id]` | 1 → * | single |

**Notes**
- Mark **`dim_date`** as the date table (`dim_date[date]`) — required for time-intelligence DAX.
- `dim_date` extends past the sales data by the forecast horizon so **forecast dates still join**.
- Returns are stored as **negative** measures in `fact_sales`, so plain `SUM` nets them out.
- `forecast_daily` and `anomalies` are analytics outputs (the AI layer), joined on date/store.
