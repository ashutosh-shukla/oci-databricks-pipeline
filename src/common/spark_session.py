"""src/common/spark_session.py - hands out the Spark session (Databricks provides it)."""

from pyspark.sql import SparkSession

from config.settings import Settings


class SparkSessionProvider:
    """
    On Databricks a session already exists, so getOrCreate() simply returns it
    (no master, no Delta jars to configure). Keeping this behind a class means
    the rest of the code never calls SparkSession directly, and Data Flow can
    get its own tuning later without touching the layers.
    """

    def __init__(self, settings: Settings = None):
        self._settings = settings or Settings.load()

    def get(self) -> SparkSession:
        return SparkSession.builder.appName(
            self._settings.get("spark", "app_name", default="banking_pipeline")
        ).getOrCreate()
