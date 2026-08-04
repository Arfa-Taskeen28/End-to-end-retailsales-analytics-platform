-- Star-schema DDL (PostgreSQL dialect) — enterprise-portable version.
-- Load the marts CSVs with \copy, or point Power BI directly at these tables.

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date, dim_product, dim_store, dim_customer CASCADE;

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,     -- yyyymmdd
    date          DATE NOT NULL,
    year          SMALLINT,
    quarter       SMALLINT,
    month         SMALLINT,
    month_name    VARCHAR(12),
    month_name_it VARCHAR(12),
    week          SMALLINT,
    day_of_week   SMALLINT,
    day_name      VARCHAR(12),
    is_weekend    BOOLEAN,
    is_holiday    BOOLEAN,
    season        VARCHAR(10)
);

CREATE TABLE dim_product (
    product_key  INTEGER PRIMARY KEY,
    product_id   VARCHAR(12) UNIQUE,
    product_name VARCHAR(120),
    category     VARCHAR(40),
    subcategory  VARCHAR(40),
    brand        VARCHAR(40),
    list_price   NUMERIC(10,2),
    unit_cost    NUMERIC(10,2)
);

CREATE TABLE dim_store (
    store_key  INTEGER PRIMARY KEY,
    store_id   VARCHAR(8) UNIQUE,
    store_name VARCHAR(80),
    city       VARCHAR(40),
    region     VARCHAR(40),
    store_type VARCHAR(20),
    open_date  DATE
);

CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id  VARCHAR(12) UNIQUE,
    gender       VARCHAR(4),
    age_band     VARCHAR(8),
    city         VARCHAR(40),
    loyalty_tier VARCHAR(12),
    signup_date  DATE
);

CREATE TABLE fact_sales (
    sale_key        BIGINT PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
    store_key       INTEGER NOT NULL REFERENCES dim_store(store_key),
    customer_key    INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    quantity        INTEGER,
    unit_price      NUMERIC(10,2),
    discount_pct    NUMERIC(5,2),
    gross_sales     NUMERIC(12,2),
    discount_amount NUMERIC(12,2),
    net_sales       NUMERIC(12,2),
    cost_amount     NUMERIC(12,2),
    gross_margin    NUMERIC(12,2),
    is_return       BOOLEAN
);

CREATE INDEX ix_fact_date    ON fact_sales(date_key);
CREATE INDEX ix_fact_product ON fact_sales(product_key);
CREATE INDEX ix_fact_store   ON fact_sales(store_key);
CREATE INDEX ix_fact_cust    ON fact_sales(customer_key);
