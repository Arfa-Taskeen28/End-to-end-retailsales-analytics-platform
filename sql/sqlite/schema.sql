-- Star-schema DDL (SQLite dialect) for the retail sales warehouse.
-- One additive fact (fact_sales) surrounded by conformed dimensions.

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_customer;

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,   -- yyyymmdd
    date          TEXT NOT NULL,
    year          INTEGER,
    quarter       INTEGER,
    month         INTEGER,
    month_name    TEXT,
    month_name_it TEXT,
    week          INTEGER,
    day_of_week   INTEGER,               -- 1=Mon .. 7=Sun
    day_name      TEXT,
    is_weekend    INTEGER,
    is_holiday    INTEGER,
    season        TEXT
);

CREATE TABLE dim_product (
    product_key  INTEGER PRIMARY KEY,
    product_id   TEXT UNIQUE,
    product_name TEXT,
    category     TEXT,
    subcategory  TEXT,
    brand        TEXT,
    list_price   REAL,
    unit_cost    REAL
);

CREATE TABLE dim_store (
    store_key   INTEGER PRIMARY KEY,
    store_id    TEXT UNIQUE,
    store_name  TEXT,
    city        TEXT,
    region      TEXT,
    store_type  TEXT,
    open_date   TEXT
);

CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id  TEXT UNIQUE,
    gender       TEXT,
    age_band     TEXT,
    city         TEXT,
    loyalty_tier TEXT,
    signup_date  TEXT
);

CREATE TABLE fact_sales (
    sale_key        INTEGER PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
    store_key       INTEGER NOT NULL REFERENCES dim_store(store_key),
    customer_key    INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    quantity        INTEGER,
    unit_price      REAL,
    discount_pct    REAL,
    gross_sales     REAL,
    discount_amount REAL,
    net_sales       REAL,
    cost_amount     REAL,
    gross_margin    REAL,
    is_return       INTEGER
);

CREATE INDEX ix_fact_date    ON fact_sales(date_key);
CREATE INDEX ix_fact_product ON fact_sales(product_key);
CREATE INDEX ix_fact_store   ON fact_sales(store_key);
CREATE INDEX ix_fact_cust    ON fact_sales(customer_key);
