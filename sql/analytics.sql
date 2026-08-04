-- ============================================================================
-- Analytical queries over the star schema (SQLite dialect; window functions,
-- CTEs, date logic). These are the kind of questions the Power BI model answers
-- — kept here to show the SQL directly. Postgres notes inline where they differ.
-- ============================================================================

-- 1) Monthly net sales with Year-over-Year growth (LAG over 12 months) ---------
WITH monthly AS (
    SELECT d.year, d.month,
           printf('%d-%02d', d.year, d.month) AS ym,
           SUM(f.net_sales) AS net_sales
    FROM fact_sales f JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year, d.month
)
SELECT ym, net_sales,
       LAG(net_sales, 12) OVER (ORDER BY year, month) AS net_sales_py,
       ROUND(100.0 * (net_sales - LAG(net_sales, 12) OVER (ORDER BY year, month))
             / LAG(net_sales, 12) OVER (ORDER BY year, month), 1) AS yoy_pct
FROM monthly
ORDER BY year, month;

-- 2) Top 10 products by gross margin, with margin % ---------------------------
SELECT p.product_name, p.category,
       ROUND(SUM(f.net_sales), 0)   AS net_sales,
       ROUND(SUM(f.gross_margin), 0) AS gross_margin,
       ROUND(100.0 * SUM(f.gross_margin) / SUM(f.net_sales), 1) AS margin_pct
FROM fact_sales f JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_key
ORDER BY gross_margin DESC
LIMIT 10;

-- 3) Store performance ranking (RANK window over net sales) -------------------
SELECT s.store_name, s.region, s.store_type,
       ROUND(SUM(f.net_sales), 0) AS net_sales,
       RANK() OVER (ORDER BY SUM(f.net_sales) DESC) AS sales_rank
FROM fact_sales f JOIN dim_store s ON f.store_key = s.store_key
GROUP BY s.store_key
ORDER BY sales_rank;

-- 4) Category contribution to total (share of net sales) ----------------------
SELECT p.category,
       ROUND(SUM(f.net_sales), 0) AS net_sales,
       ROUND(100.0 * SUM(f.net_sales) / SUM(SUM(f.net_sales)) OVER (), 1) AS pct_of_total
FROM fact_sales f JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY net_sales DESC;

-- 5) 7-day moving average of daily net sales (smoothing) ----------------------
WITH daily AS (
    SELECT d.date, SUM(f.net_sales) AS net_sales
    FROM fact_sales f JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.date
)
SELECT date, net_sales,
       ROUND(AVG(net_sales) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING
                                  AND CURRENT ROW), 0) AS ma_7d
FROM daily
ORDER BY date;

-- 6) RFM customer segmentation (Recency / Frequency / Monetary via NTILE) ------
--    Postgres: replace julianday(...) with (max_date - MAX(d.date)).
WITH cust AS (
    SELECT f.customer_key,
           julianday((SELECT MAX(date) FROM dim_date)) - julianday(MAX(d.date)) AS recency_days,
           COUNT(*)          AS frequency,
           SUM(f.net_sales)  AS monetary
    FROM fact_sales f JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.is_return = 0
    GROUP BY f.customer_key
)
SELECT customer_key, recency_days, frequency, ROUND(monetary, 0) AS monetary,
       NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- recent = high
       NTILE(5) OVER (ORDER BY frequency)          AS f_score,
       NTILE(5) OVER (ORDER BY monetary)           AS m_score
FROM cust
ORDER BY monetary DESC
LIMIT 25;
