"""
pipeline.py

Orchestrates the extract -> transform -> load flow.
"""

from src.extract.databricks_reader import read_delta_table
from src.transform.transformations import clean_dataframe, map_schema
from src.load.oci_writer import write_to_oracle_adb
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline(spark, config: dict, jdbc_url: str, connection_properties: dict):
    logger.info("Starting pipeline run")

    df = read_delta_table(
        spark,
        catalog=config["databricks"]["catalog"],
        schema=config["databricks"]["schema"],
        table=config["databricks"]["table"],
    )
    logger.info("Extracted %d rows", df.count())

    df = clean_dataframe(df)
    df = map_schema(df, column_mapping={})

    write_to_oracle_adb(
        df,
        jdbc_url=jdbc_url,
        table=config["oracle_adb"]["target_table"],
        connection_properties=connection_properties,
    )
    logger.info("Pipeline run complete")


if __name__ == "__main__":
    raise SystemExit(
        "Run this pipeline from a Databricks notebook/job with a Spark session, "
        "or adapt this entry point for your orchestration tool."
    )
