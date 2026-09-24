"""
src/load/oci_writer.py

Phase 1 — naive load. Connects to the OCI Autonomous Database and writes a
Spark DataFrame into a target Oracle table via batched INSERTs.
"""

import oracledb
import pandas as pd


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


def _prepare_rows(pdf: pd.DataFrame):
    """
    Converts a pandas DataFrame into a list of plain Python tuples that
    oracledb can safely bind:
        - NaN / NaT -> None (Oracle NULL)
        - pandas.Timestamp -> python datetime (oracledb doesn't accept pandas
        Timestamp objects directly)
    Phase 1 keeps this minimal on purpose — real type/format validation
    (e.g. the comma-decimal amount_eur_comma column, the string
    account_open_date) is deliberately deferred to Phase 5.
    """
    pdf = pdf.astype(object).where(pd.notnull(pdf), None)

    rows = []
    for row in pdf.itertuples(index=False, name=None):
        clean_row = tuple(
            value.to_pydatetime() if isinstance(value, pd.Timestamp) else value
            for value in row
        )
        rows.append(clean_row)
    return rows


def write_dataframe_to_oracle(spark_df, table_name: str, connection) -> int:
    """
    Writes a Spark DataFrame into an Oracle table via a batched INSERT
    (executemany — one round trip for the whole batch, not one per row).

    Phase 1 note: converts to pandas via toPandas() first. That's fine while
    each table's data is small (thousands of rows, fits easily in memory).
    This becomes the exact bottleneck Phase 6 (scaling/batching) addresses
    once data volume grows — flagged here on purpose.

    Returns the number of rows written.
    """
    pdf = spark_df.toPandas()
    if pdf.empty:
        print(f"  {table_name}: 0 rows to write, skipping.")
        return 0

    columns = list(pdf.columns)
    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{i+1}" for i in range(len(columns)))
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    rows = _prepare_rows(pdf)

    cursor = connection.cursor()
    try:
        cursor.executemany(insert_sql, rows)
        connection.commit()
    finally:
        cursor.close()

    print(f"  {table_name}: {len(rows)} rows written.")
    return len(rows)


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
