"""
src/utils/config_loader.py

Loads config.dev.yaml (non-secret settings) and .env (secrets), and merges
them into one config object the rest of the pipeline can use.

Why this file exists: every other file (extract, load, pipeline) needs the
same settings. Instead of each file reading YAML/env on its own, they all
import load_config() from here — one source of truth, loaded once.
"""

import os
import yaml
from dotenv import load_dotenv

# Load .env into environment variables. Safe to call even if .env is missing
# (e.g. in CI) — it just won't set anything.
load_dotenv()


def is_running_in_databricks() -> bool:
    """
    Databricks sets this env var automatically inside every cluster.
    It does NOT exist on a local machine (VS Code) — that's how we tell
    the two environments apart without hardcoding anything.
    """
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def get_secret(key: str, databricks_scope: str = "pipeline-secrets"):
    """
    Reads a secret from the right place depending on where we're running:
        - Local (VS Code): from .env, via a plain environment variable
        - Databricks: from a Secret Scope (since .env doesn't exist there —
        it's gitignored, so it never made it into the Databricks Repo)

        databricks_scope must already exist and hold a matching key name
        (see the setup steps for creating it via the Databricks CLI).
    """
    if is_running_in_databricks():
        from pyspark.sql import SparkSession
        from pyspark.dbutils import DBUtils

        spark = SparkSession.builder.getOrCreate()
        dbutils = DBUtils(spark)
        # Secret scope keys are conventionally lowercase-with-dashes
        secret_key = key.lower().replace("_", "-")
        try:
            return dbutils.secrets.get(scope=databricks_scope, key=secret_key)
        except Exception:
            return None

    return os.environ.get(key)


def load_config(config_path: str = "config/config.dev.yaml") -> dict:
    """
    Reads config.dev.yaml, then layers in secrets — from .env locally, or a
    Databricks Secret Scope when running inside a cluster/notebook.

    Returns a plain dict, e.g.:
        config["databricks"]["source_path"]
        config["oracle_adb"]["target_tables"]["customers"]
        config["oracle_adb"]["password"]        <- injected here, not in YAML
        config["oracle_adb"]["wallet_dir"]      <- resolved to the right path
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # --- Inject secrets (never stored in the YAML file) -------------------
    oci_password = get_secret("ORACLE_ADB_PASSWORD")
    if not oci_password:
        raise ValueError(
            "ORACLE_ADB_PASSWORD not found. Locally: make sure .env exists "
            "(copied from .env.example) with a real value. In Databricks: "
            "make sure the 'pipeline-secrets' secret scope exists and has "
            "an 'oracle-adb-password' key set."
        )
    config["oracle_adb"]["password"] = oci_password
    config["oracle_adb"]["wallet_password"] = get_secret(
        "ORACLE_ADB_WALLET_PASSWORD"
    )  # may be None, that's fine

    # username and DSN also come from secrets in this project's convention —
    # override whatever (if anything) is in the YAML file
    env_username = get_secret("ORACLE_ADB_USER")
    if env_username:
        config["oracle_adb"]["username"] = env_username

    env_dsn = get_secret("ORACLE_ADB_DSN")
    if env_dsn:
        config["oracle_adb"]["service_name"] = env_dsn

    # --- Resolve the correct wallet path for this environment -------------
    wallet_dirs = config["oracle_adb"]["wallet_dir"]
    if is_running_in_databricks():
        config["oracle_adb"]["wallet_dir"] = wallet_dirs["databricks"]
    else:
        config["oracle_adb"]["wallet_dir"] = wallet_dirs["local"]

    return config
