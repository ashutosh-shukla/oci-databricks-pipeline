"""
src/pipeline.py

Phase 1 — naive end-to-end pipeline. Reads the CSV, splits it into the 4
target tables' worth of columns, deduplicates by each table's primary key
(required — the raw CSV has repeated customer_id/account_id across multiple
transaction rows), and writes each piece to its Oracle table.

Run from PROJECT ROOT as: python -m src.pipeline
"""

from src.utils.config_loader import load_config
from src.legacy.databricks_reader import get_spark, read_csv_from_volume
from src.legacy.oci_writer import get_oracle_connection, write_dataframe_to_oracle

# Column groupings match sql/create_tables.sql exactly.
CUSTOMERS_COLS = [
    "customer_id",
    "customer_name",
    "email",
    "phone",
    "customer_dob",
    "address_city",
    "marital_status",
    "employment_status",
    "preferred_language",
    "customer_segment",
    "monthly_income",
    "credit_score",
    "debt_to_income_ratio",
    "kyc_status",
    "risk_rating",
    "tenure_months",
    "product_holding_count",
    "nps_score",
    "churn_probability",
    "lifetime_value_score",
    "marketing_opt_in",
    "paperless_consent",
    "complaint_count_12m",
]

ACCOUNTS_COLS = [
    "account_id",
    "customer_id",
    "branch_code",
    "relationship_manager_id",
    "account_open_date",
    "credit_limit",
    "has_overdraft",
    "total_relationship_value",
    "avg_balance_30d",
    "min_balance_30d",
    "overdraft_days_12m",
    "salary_credit_flag",
    "direct_debit_count",
    "standing_order_count",
    "utilisation_pct",
]

TRANSACTIONS_COLS = [
    "transaction_id",
    "account_id",
    "customer_id",
    "transaction_ts",
    "transaction_date",
    "value_date",
    "transaction_amount",
    "fee_amount",
    "fx_rate",
    "transaction_amount_usd",
    "balance_before",
    "balance_after",
    "transaction_type",
    "channel",
    "merchant_category",
    "merchant_name",
    "narrative",
    "currency",
    "country_code",
    "is_international",
    "is_flagged_fraud",
    "is_reversed",
    "is_recurring",
]

CUSTOMER_METRICS_COLS = [
    "customer_id",
    "txn_count_30d",
    "txn_count_90d",
    "txn_amount_30d",
    "txn_amount_90d",
    "avg_txn_amount_30d",
    "max_txn_amount_30d",
    "distinct_merchants_30d",
    "distinct_countries_30d",
    "days_since_last_txn",
    "days_since_account_open",
    "login_count_30d",
    "failed_login_count_30d",
    "last_login_ts",
    "weekend_txn_ratio_90d",
    "night_txn_ratio_90d",
    "atm_withdrawal_count_30d",
    "pos_txn_count_30d",
    "online_txn_count_30d",
    "cross_border_count_90d",
    "declined_txn_count_30d",
    "chargeback_count_12m",
    "device_type",
    "mobile_app_version",
    "campaign_code",
]


def run_pipeline():
    config = load_config()
    spark = get_spark()

    print("Step 1/3: Extracting source CSV...")
    raw_df = read_csv_from_volume(spark, config["databricks"]["source_path"])
    print(f"  Read {raw_df.count()} rows, {len(raw_df.columns)} columns.")

    print("Step 2/3: Splitting into per-table DataFrames (with dedup on PK)...")
    customers_df = raw_df.select(*CUSTOMERS_COLS).dropDuplicates(["customer_id"])
    accounts_df = raw_df.select(*ACCOUNTS_COLS).dropDuplicates(["account_id"])
    transactions_df = raw_df.select(
        *TRANSACTIONS_COLS
    )  # transaction_id is already unique per row
    metrics_df = raw_df.select(*CUSTOMER_METRICS_COLS).dropDuplicates(["customer_id"])

    print(f"  customers: {customers_df.count()} rows")
    print(f"  accounts: {accounts_df.count()} rows")
    print(f"  transactions: {transactions_df.count()} rows")
    print(f"  customer_metrics: {metrics_df.count()} rows")

    print("Step 3/3: Writing to Oracle...")
    target_tables = config["oracle_adb"]["target_tables"]
    conn = get_oracle_connection(config)
    try:
        write_dataframe_to_oracle(customers_df, target_tables["customers"], conn)
        write_dataframe_to_oracle(accounts_df, target_tables["accounts"], conn)
        write_dataframe_to_oracle(transactions_df, target_tables["transactions"], conn)
        write_dataframe_to_oracle(metrics_df, target_tables["customer_metrics"], conn)
    finally:
        conn.close()

    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
