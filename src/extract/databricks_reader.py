"""
databricks_reader.py

Reads data from a Delta table or a CSV file in a Databricks volume.
"""


def read_delta_table(spark, catalog: str, schema: str, table: str):
    """Read a Delta table into a Spark DataFrame."""
    full_table_name = f"{catalog}.{schema}.{table}"
    return spark.table(full_table_name)


def read_csv_from_volume(spark, volume_path: str, header: bool = True):
    """Read a CSV file from a Databricks Unity Catalog volume."""
    return (
        spark.read
        .option("header", header)
        .option("inferSchema", True)
        .csv(volume_path)
    )
