"""src/bronze/databricks_delta_writer.py - CSV in a Databricks Volume -> bronze Delta table."""

import hashlib

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from config.settings import Settings
from src.bronze.bronze_schema import BronzeSchema
from src.common.exceptions import BronzeIngestionError
from src.common.oci_logger import PipelineLogger
from src.common.spark_session import SparkSessionProvider


class BronzeDeltaWriter:
    """
    Loads the raw CSV into the bronze Delta table, untouched.

    - every source column stays a string (inferSchema=false in the config)
    - three audit columns are added: _ingested_at, _source_file, _load_id
    - no cleaning, no deduplication, no MERGE (that is silver's job)
    - re-runs are safe: rows are replaced by _load_id, never doubled
    """

    def __init__(
        self,
        spark: SparkSession = None,
        settings: Settings = None,
        logger: PipelineLogger = None,
    ):
        self._settings = settings or Settings.load()
        self._spark = spark or SparkSessionProvider(self._settings).get()
        self._log = logger or PipelineLogger(__name__, self._settings)

        self._source_path = self._settings.get("databricks", "source_path")
        self._table = self._settings.get("databricks", "bronze_table")
        self._read_options = (
            self._settings.get("databricks", "csv_read_options", default={}) or {}
        )
        if not self._source_path or not self._table:
            raise BronzeIngestionError(
                "databricks.source_path and databricks.bronze_table must be set in the config"
            )

    # ---------- steps ----------

    def read_raw(self) -> DataFrame:
        """Read the CSV as-is and check its header against the bronze contract."""
        df = self._spark.read.options(**self._read_options).csv(self._source_path)
        BronzeSchema.validate_header(df.columns)  # raises SchemaMismatchError on drift
        return df

    def compute_load_id(self, df: DataFrame) -> str:
        """
        Deterministic ID: same file (path + size + modified time) -> same ID.
        Hidden `_metadata` is provided by Spark for file sources.
        """
        meta = df.select(
            F.col("_metadata.file_path").alias("path"),
            F.col("_metadata.file_size").alias("size"),
            F.col("_metadata.file_modification_time").alias("mtime"),
        ).first()
        if meta is None:
            raise BronzeIngestionError("Source file is empty", path=self._source_path)
        digest = hashlib.sha256(
            f"{meta['path']}|{meta['size']}|{meta['mtime']}".encode()
        ).hexdigest()[:16]
        return f"LOAD_{digest}"

    def add_audit_columns(self, df: DataFrame, load_id: str) -> DataFrame:
        return (
            df.withColumn("_ingested_at", F.current_timestamp())
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_load_id", F.lit(load_id))
        )

    def write(self, df: DataFrame, load_id: str) -> None:
        """
        First run creates the table. Later runs use replaceWhere on _load_id:
            a new load_id is appended, a repeated load_id replaces its own rows.
        """
        if not self._spark.catalog.tableExists(self._table):
            df.write.format("delta").mode("append").saveAsTable(self._table)
            return
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", f"_load_id = '{load_id}'")
            .saveAsTable(self._table)
        )

    def verify(self, load_id: str, source_rows: int) -> dict:
        table_df = self._spark.table(self._table)
        loaded_rows = table_df.filter(F.col("_load_id") == load_id).count()
        if loaded_rows != source_rows:
            raise BronzeIngestionError(
                "Row count mismatch after bronze load",
                load_id=load_id,
                source_rows=source_rows,
                loaded_rows=loaded_rows,
            )
        return {"loaded_rows": loaded_rows, "table_total": table_df.count()}

    # ---------- orchestration ----------

    def run(self) -> dict:
        self._log.info("Bronze load starting: %s -> %s", self._source_path, self._table)
        df = self.read_raw()
        load_id = self.compute_load_id(df)
        source_rows = df.count()
        if source_rows == 0:
            raise BronzeIngestionError(
                "Source file has no data rows", path=self._source_path
            )
        self._log.info("load_id=%s source_rows=%d", load_id, source_rows)

        self.write(self.add_audit_columns(df, load_id), load_id)
        result = self.verify(load_id, source_rows)

        summary = {"load_id": load_id, "source_rows": source_rows, **result}
        self._log.info("Bronze load finished: %s", summary)
        return summary
