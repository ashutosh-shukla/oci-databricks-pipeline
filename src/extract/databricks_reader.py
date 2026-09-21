"""
src/extract/databricks_reader.py

Phase 1 — naive extract. Reads data from a Delta table or a CSV file in a
Databricks Volume. Functions take explicit parameters (not a config dict) so
they're easy to test in isolation and reusable outside this specific project.

No cleaning, no validation, no error handling yet — that comes in later
phases. Goal right now: prove we can read real data.
"""

from pyspark.sql import SparkSession, DataFrame


def get_spark() -> SparkSession:
    """
    Inside a Databricks notebook/job, a SparkSession already exists globally
    — getOrCreate() picks that up automatically.

    Outside Databricks (VS Code), we connect to the real remote cluster via
    Databricks Connect, using DATABRICKS_HOST / DATABRICKS_TOKEN /
    DATABRICKS_CLUSTER_ID from .env. This gives local code real access to
    Unity Catalog Volumes and Delta tables, not a fake empty local session.
    """
    from src.utils.config_loader import is_running_in_databricks

    if is_running_in_databricks():
        return SparkSession.builder.getOrCreate()

    # Running locally (VS Code) — use Databricks Connect against Serverless
    # compute (no cluster_id needed, since this workspace uses General
    # compute -> Serverless rather than a named cluster).
    from databricks.connect import DatabricksSession
    import os

    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")

    if not (host and token):
        raise ValueError(
            "Running locally requires DATABRICKS_HOST and DATABRICKS_TOKEN "
            "to be set in .env for Databricks Connect to reach serverless "
            "compute."
        )

    return (
        DatabricksSession.builder.remote(host=host, token=token)
        .serverless(True)
        .getOrCreate()
    )


def read_delta_table(
    spark: SparkSession, catalog: str, schema: str, table: str
) -> DataFrame:
    """Read a Delta table into a Spark DataFrame. Not used yet — no Delta
    table exists in this project — but kept here since we'll likely add one
    later, and the pattern should exist alongside the CSV reader."""
    full_table_name = f"{catalog}.{schema}.{table}"
    return spark.table(full_table_name)


def read_csv_from_volume(
    spark: SparkSession, volume_path: str, header: bool = True
) -> DataFrame:
    """Read a CSV file from a Databricks Unity Catalog volume."""
    return (
        spark.read.option("header", header).option("inferSchema", True).csv(volume_path)
    )


if __name__ == "__main__":
    # Quick manual test: run this file directly to confirm the CSV actually
    # reads correctly before wiring it into the full pipeline.
    # Run this from the PROJECT ROOT as: python -m src.extract.databricks_reader
    from src.utils.config_loader import load_config

    cfg = load_config()
    spark = get_spark()

    df = read_csv_from_volume(spark, cfg["databricks"]["source_path"])

    print(f"Row count: {df.count()}")
    print(f"Column count: {len(df.columns)}")
    df.printSchema()
    df.show(5, truncate=False)
