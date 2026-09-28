"""src/bronze/bronze_schema.py - the bronze contract: 100 raw columns, all strings."""

from typing import Iterable

from pyspark.sql.types import StringType, StructField, StructType

from src.common.exceptions import SchemaMismatchError


class BronzeSchema:
    """
    Bronze keeps the source exactly as received: every column is a string, so
    dirty values ("156,38", "03-Aug-2017", "N") survive untouched. Typing and
    cleaning happen in silver, never here.
    """

    RAW_COLUMNS = (
        "customer_id",
        "account_id",
        "transaction_id",
        "branch_code",
        "relationship_manager_id",
        "transaction_ts",
        "transaction_date",
        "value_date",
        "account_open_date",
        "customer_dob",
        "last_login_ts",
        "transaction_amount",
        "transaction_amount_str",
        "amount_eur_comma",
        "fee_amount",
        "fx_rate",
        "balance_before",
        "balance_after",
        "credit_limit",
        "monthly_income",
        "total_relationship_value",
        "transaction_type",
        "channel",
        "merchant_category",
        "currency",
        "country_code",
        "customer_segment",
        "product_type",
        "risk_rating",
        "kyc_status",
        "employment_status",
        "marital_status",
        "preferred_language",
        "is_international",
        "is_flagged_fraud",
        "is_reversed",
        "is_recurring",
        "has_overdraft",
        "paperless_consent",
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
        "complaint_count_12m",
        "product_holding_count",
        "credit_score",
        "debt_to_income_ratio",
        "utilisation_pct",
        "tenure_months",
        "customer_name",
        "email",
        "phone",
        "merchant_name",
        "narrative",
        "address_city",
        "etl_batch_id",
        "source_system",
        "record_status",
        "reserved_field_1",
        "reserved_field_2",
        "legacy_flag",
        "internal_notes",
        "unused_code",
        "row_hash",
        "import_filename",
        "schema_version",
        "dq_score_placeholder",
        "txn_amount_copy",
        "cust_segment",
        "transaction_amount_usd",
        "txn_amount_30d_eur",
        "weekend_txn_ratio_90d",
        "night_txn_ratio_90d",
        "atm_withdrawal_count_30d",
        "pos_txn_count_30d",
        "online_txn_count_30d",
        "cross_border_count_90d",
        "declined_txn_count_30d",
        "chargeback_count_12m",
        "avg_balance_30d",
        "min_balance_30d",
        "overdraft_days_12m",
        "salary_credit_flag",
        "direct_debit_count",
        "standing_order_count",
        "mobile_app_version",
        "device_type",
        "marketing_opt_in",
        "nps_score",
        "campaign_code",
        "churn_probability",
        "lifetime_value_score",
    )

    # Added by OUR pipeline at load time (underscore prefix avoids clashing with
    # the source's own etl_batch_id / import_filename columns).
    METADATA_COLUMNS = ("_ingested_at", "_source_file", "_load_id")

    KEY_COLUMN = "transaction_id"

    @classmethod
    def raw_struct(cls) -> StructType:
        """Schema used when reading the CSV (source columns only)."""
        return StructType([StructField(c, StringType(), True) for c in cls.RAW_COLUMNS])

    @classmethod
    def full_columns(cls) -> tuple:
        return cls.RAW_COLUMNS + cls.METADATA_COLUMNS

    @classmethod
    def validate_header(cls, actual_columns: Iterable[str]) -> None:
        """Compare a file's header with the contract; raise with details if it differs."""
        actual = list(actual_columns)
        missing = [c for c in cls.RAW_COLUMNS if c not in actual]
        extra = [c for c in actual if c not in cls.RAW_COLUMNS]
        if missing or extra:
            raise SchemaMismatchError(
                "Source header does not match bronze contract",
                missing=missing,
                extra=extra,
                expected=len(cls.RAW_COLUMNS),
                actual=len(actual),
            )


if __name__ == "__main__":
    print("raw columns:", len(BronzeSchema.RAW_COLUMNS))
    print("unique names:", len(set(BronzeSchema.RAW_COLUMNS)))
    print("struct fields:", len(BronzeSchema.raw_struct().fields))
    BronzeSchema.validate_header(BronzeSchema.RAW_COLUMNS)
    print("valid header accepted")
    try:
        BronzeSchema.validate_header(BronzeSchema.RAW_COLUMNS[:-1] + ("brand_new_col",))
    except SchemaMismatchError as err:
        print("drift detected:", err)
