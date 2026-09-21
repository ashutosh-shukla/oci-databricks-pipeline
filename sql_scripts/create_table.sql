-- ============================================================================
-- create_tables.sql
-- Run this in the OCI SQL Worksheet, connected as user ASHU (or as ADMIN,
-- then GRANT the needed privileges to ASHU afterward).
-- Order matters: parents (CUSTOMERS) before children (ACCOUNTS, TRANSACTIONS,
-- CUSTOMER_ACTIVITY_METRICS) because of the foreign keys.
-- ============================================================================

-- 1. CUSTOMERS_DIM — who the customer is
CREATE TABLE CUSTOMERS_DIM (
    customer_id             VARCHAR2(50)    NOT NULL,
    customer_name           VARCHAR2(200),
    email                   VARCHAR2(200),
    phone                   VARCHAR2(50),
    customer_dob            DATE,
    address_city            VARCHAR2(100),
    marital_status          VARCHAR2(30),
    employment_status       VARCHAR2(30),
    preferred_language      VARCHAR2(30),
    customer_segment        VARCHAR2(30),
    monthly_income          NUMBER(15,2),
    credit_score            NUMBER(5),
    debt_to_income_ratio    NUMBER(6,4),
    kyc_status               VARCHAR2(30),
    risk_rating              VARCHAR2(30),
    tenure_months             NUMBER(6),
    product_holding_count    NUMBER(4),
    nps_score                 NUMBER(5,2),
    churn_probability          NUMBER(6,4),
    lifetime_value_score        NUMBER(15,2),
    marketing_opt_in            CHAR(1),
    paperless_consent           CHAR(1),
    complaint_count_12m          NUMBER(6),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

-- 2. ACCOUNTS_DIM — account-level info
CREATE TABLE ACCOUNTS_DIM (
    account_id                  VARCHAR2(50)   NOT NULL,
    customer_id                 VARCHAR2(50)   NOT NULL,
    branch_code                 VARCHAR2(20),
    relationship_manager_id     VARCHAR2(50),
    account_open_date           DATE,
    credit_limit                NUMBER(15,2),
    has_overdraft                CHAR(1),
    total_relationship_value     NUMBER(15,2),
    avg_balance_30d               NUMBER(15,2),
    min_balance_30d                NUMBER(15,2),
    overdraft_days_12m              NUMBER(6),
    salary_credit_flag               CHAR(1),
    direct_debit_count                NUMBER(6),
    standing_order_count               NUMBER(6),
    utilisation_pct                      NUMBER(6,2),
    CONSTRAINT pk_accounts PRIMARY KEY (account_id),
    CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMERS_DIM (customer_id)
);

-- 3. TRANSACTIONS_FACT — one row per transaction (the core table)
CREATE TABLE TRANSACTIONS_FACT (
    transaction_id           VARCHAR2(50)    NOT NULL,
    account_id               VARCHAR2(50)    NOT NULL,
    customer_id               VARCHAR2(50)    NOT NULL,
    transaction_ts             TIMESTAMP,
    transaction_date            DATE,
    value_date                   DATE,
    transaction_amount            NUMBER(18,2),
    fee_amount                     NUMBER(12,2),
    fx_rate                         NUMBER(12,6),
    transaction_amount_usd           NUMBER(18,2),
    balance_before                    NUMBER(18,2),
    balance_after                      NUMBER(18,2),
    transaction_type                    VARCHAR2(30),
    channel                              VARCHAR2(30),
    merchant_category                     VARCHAR2(50),
    merchant_name                          VARCHAR2(200),
    narrative                               VARCHAR2(500),
    currency                                 VARCHAR2(10),
    country_code                              VARCHAR2(5),
    is_international                           CHAR(1),
    is_flagged_fraud                            CHAR(1),
    is_reversed                                  CHAR(1),
    is_recurring                                  CHAR(1),
    CONSTRAINT pk_transactions PRIMARY KEY (transaction_id),
    CONSTRAINT fk_txn_account FOREIGN KEY (account_id)
        REFERENCES ACCOUNTS_DIM (account_id),
    CONSTRAINT fk_txn_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMERS_DIM (customer_id)
);

-- 4. CUSTOMER_ACTIVITY_METRICS — pre-aggregated 30d/90d behavioral stats
-- NOTE (Phase 1 decision): source CSV has no snapshot date, so this table
-- holds only the LATEST metrics per customer (overwritten each load).
-- We'll upgrade this to real history-tracking in Phase 7 (SCD concepts) —
-- flagged here on purpose so you can see exactly why that phase matters later.
CREATE TABLE CUSTOMER_ACTIVITY_METRICS (
    customer_id                  VARCHAR2(50)   NOT NULL,
    txn_count_30d                 NUMBER(8),
    txn_count_90d                  NUMBER(8),
    txn_amount_30d                  NUMBER(18,2),
    txn_amount_90d                   NUMBER(18,2),
    avg_txn_amount_30d                NUMBER(18,2),
    max_txn_amount_30d                 NUMBER(18,2),
    distinct_merchants_30d              NUMBER(8),
    distinct_countries_30d               NUMBER(8),
    days_since_last_txn                   NUMBER(8),
    days_since_account_open                NUMBER(8),
    login_count_30d                         NUMBER(8),
    failed_login_count_30d                   NUMBER(8),
    last_login_ts                             TIMESTAMP,
    weekend_txn_ratio_90d                      NUMBER(6,4),
    night_txn_ratio_90d                         NUMBER(6,4),
    atm_withdrawal_count_30d                     NUMBER(8),
    pos_txn_count_30d                             NUMBER(8),
    online_txn_count_30d                           NUMBER(8),
    cross_border_count_90d                          NUMBER(8),
    declined_txn_count_30d                           NUMBER(8),
    chargeback_count_12m                              NUMBER(8),
    device_type                                        VARCHAR2(30),
    mobile_app_version                                  VARCHAR2(20),
    campaign_code                                        VARCHAR2(30),
    CONSTRAINT pk_customer_metrics PRIMARY KEY (customer_id),
    CONSTRAINT fk_metrics_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMERS_DIM (customer_id)
);