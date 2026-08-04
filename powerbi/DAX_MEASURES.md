# DAX Measure Library

Copy these into Power BI (create a dedicated `_Measures` table, or put them on
`fact_sales`). They assume the star schema in [`DATA_MODEL.md`](DATA_MODEL.md)
and that **`dim_date` is marked as the date table** (Modeling → Mark as date table
→ `dim_date[date]`).

---

## 1 · Base measures
```DAX
Total Net Sales   = SUM ( fact_sales[net_sales] )
Total Gross Sales = SUM ( fact_sales[gross_sales] )
Total Cost        = SUM ( fact_sales[cost_amount] )
Gross Margin      = SUM ( fact_sales[gross_margin] )
Gross Margin %    = DIVIDE ( [Gross Margin], [Total Net Sales] )
Total Quantity    = SUM ( fact_sales[quantity] )
Total Discount    = SUM ( fact_sales[discount_amount] )
Discount Rate %   = DIVIDE ( [Total Discount], [Total Gross Sales] )
Sales Line Count  = COUNTROWS ( fact_sales )
Customer Count    = DISTINCTCOUNT ( fact_sales[customer_key] )
Avg Order Value   = DIVIDE ( [Total Net Sales], [Sales Line Count] )
Sales per Customer = DIVIDE ( [Total Net Sales], [Customer Count] )
```

## 2 · Returns
```DAX
Return Lines = CALCULATE ( [Sales Line Count], fact_sales[is_return] = 1 )
Return Rate % =
DIVIDE (
    CALCULATE ( [Sales Line Count], fact_sales[is_return] = 1 ),
    [Sales Line Count]
)
```

## 3 · Time intelligence  *(requires dim_date marked as date table)*
```DAX
Sales YTD = TOTALYTD ( [Total Net Sales], dim_date[date] )
Sales QTD = TOTALQTD ( [Total Net Sales], dim_date[date] )
Sales MTD = TOTALMTD ( [Total Net Sales], dim_date[date] )

Sales PY  = CALCULATE ( [Total Net Sales], SAMEPERIODLASTYEAR ( dim_date[date] ) )
Sales YoY = [Total Net Sales] - [Sales PY]
Sales YoY % = DIVIDE ( [Sales YoY], [Sales PY] )

Sales PM  = CALCULATE ( [Total Net Sales], DATEADD ( dim_date[date], -1, MONTH ) )
Sales MoM % = DIVIDE ( [Total Net Sales] - [Sales PM], [Sales PM] )

Rolling 3M Sales =
CALCULATE ( [Total Net Sales],
    DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )

Rolling 12M Sales =
CALCULATE ( [Total Net Sales],
    DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -12, MONTH ) )
```

## 4 · Customers — new vs. returning
```DAX
New Customers =
VAR CurUsers = VALUES ( fact_sales[customer_key] )
VAR MaxDate  = MAX ( dim_date[date] )
RETURN
COUNTROWS (
    FILTER ( CurUsers,
        CALCULATE (
            MIN ( dim_date[date] ),
            ALLEXCEPT ( fact_sales, fact_sales[customer_key] ),
            dim_date[date] <= MaxDate
        ) >= MIN ( dim_date[date] )
    )
)

Returning Customers = [Customer Count] - [New Customers]
```

## 5 · Forecast  *(from the `forecast_daily` table, related to dim_date[date])*
```DAX
Forecast Sales = SUM ( forecast_daily[forecast] )
Forecast Lower = SUM ( forecast_daily[lower_bound] )
Forecast Upper = SUM ( forecast_daily[upper_bound] )

-- overlay actual vs forecast on one line chart using [Total Net Sales] and
-- [Forecast Sales] by dim_date[date]; the model's back-test MAPE is ~7%.
```

## 6 · Anomalies  *(from the `anomalies` table)*
```DAX
Anomaly Count = CALCULATE ( COUNTROWS ( anomalies ), anomalies[is_anomaly] = 1 )
Dip Anomalies = CALCULATE ( [Anomaly Count], anomalies[direction] = "dip" )
```

## 7 · KPI helpers (for cards / conditional formatting)
```DAX
Sales YoY Arrow =
VAR v = [Sales YoY %]
RETURN IF ( ISBLANK ( v ), "", IF ( v >= 0, "▲ ", "▼ " ) ) & FORMAT ( v, "0.0%" )

Margin Status =                       -- traffic-light for a card
SWITCH ( TRUE (),
    [Gross Margin %] >= 0.40, "🟢 Healthy",
    [Gross Margin %] >= 0.30, "🟡 Watch",
    "🔴 Low" )
```

---

## Row-Level Security (RLS) — regional managers see only their region
Create roles under **Modeling → Manage roles**.

**Static role** (one per region):
```DAX
[region] = "Lombardia"      -- table filter on dim_store
```

**Dynamic role** (one role for everyone, driven by a `user_region` mapping table):
```DAX
-- filter on dim_store:
dim_store[region] IN
    SELECTVALUES (
        FILTER ( user_region, user_region[email] = USERPRINCIPALNAME() ),
        user_region[region]
    )
```
Test with **Modeling → View as → Role**.
