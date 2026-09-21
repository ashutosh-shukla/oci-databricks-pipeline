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


def load_config(config_path: str = "config/config.dev.yaml") -> dict:
    """
    Reads config.dev.yaml, then layers in secrets from environment variables
    (which came from .env locally, or a Databricks secret scope in the cluster).

    Returns a plain dict, e.g.:
        config["databricks"]["source_path"]
        config["oracle_adb"]["target_tables"]["customers"]
        config["oracle_adb"]["password"]        <- injected here, not in YAML
        config["oracle_adb"]["wallet_dir"]      <- resolved to the right path
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # --- Inject secrets (never stored in the YAML file) -------------------
    oci_password = os.environ.get("ORACLE_ADB_PASSWORD")
    if not oci_password:
        raise ValueError(
            "ORACLE_ADB_PASSWORD not found. Make sure .env exists (copied "
            "from .env.example) and has a real value set, or that it's set "
            "as an environment variable / Databricks secret."
        )
    config["oracle_adb"]["password"] = oci_password
    config["oracle_adb"]["wallet_password"] = os.environ.get(
        "ORACLE_ADB_WALLET_PASSWORD"
    )  # may be None, that's fine

    # username and DSN also come from .env in this project's convention —
    # override whatever (if anything) is in the YAML file
    env_username = os.environ.get("ORACLE_ADB_USER")
    if env_username:
        config["oracle_adb"]["username"] = env_username

    env_dsn = os.environ.get("ORACLE_ADB_DSN")
    if env_dsn:
        config["oracle_adb"]["service_name"] = env_dsn

    # --- Resolve the correct wallet path for this environment -------------
    wallet_dirs = config["oracle_adb"]["wallet_dir"]
    if is_running_in_databricks():
        config["oracle_adb"]["wallet_dir"] = wallet_dirs["databricks"]
    else:
        config["oracle_adb"]["wallet_dir"] = wallet_dirs["local"]

    return config
