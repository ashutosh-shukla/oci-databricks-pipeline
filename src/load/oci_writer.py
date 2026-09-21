"""
src/load/oci_writer.py

Phase 1 — naive load. Step 1 of 2: just prove we can connect to the OCI
Autonomous Database from wherever this code runs (VS Code locally, or a
Databricks notebook/job). Write logic comes next, once connection is proven.
"""

import oracledb


def get_oracle_connection(config: dict):
    """
    Connects to the OCI Autonomous Database using python-oracledb in THIN
    mode (the default — no Oracle Instant Client install needed), pointed
    at the wallet folder for TLS.

    config["oracle_adb"] must contain: username, password, service_name
    (the TNS alias from tnsnames.ora), wallet_dir (resolved to the correct
    path already, by config_loader), and optionally wallet_password.
    """
    oracle_cfg = config["oracle_adb"]

    connection = oracledb.connect(
        user=oracle_cfg["username"],
        password=oracle_cfg["password"],
        dsn=oracle_cfg["service_name"],
        config_dir=oracle_cfg["wallet_dir"],
        wallet_location=oracle_cfg["wallet_dir"],
        wallet_password=oracle_cfg.get("wallet_password"),
    )
    return connection


if __name__ == "__main__":
    # Quick manual test — connect only, run a trivial query, confirm it
    # works before touching any DataFrame or write logic.
    # Run from PROJECT ROOT as: python -m src.load.oci_writer
    from src.utils.config_loader import load_config

    cfg = load_config()
    conn = get_oracle_connection(cfg)

    cursor = conn.cursor()
    cursor.execute("SELECT 'connected' FROM DUAL")
    result = cursor.fetchone()
    print(f"Connection test result: {result[0]}")

    cursor.close()
    conn.close()
    print("Connection closed cleanly.")
