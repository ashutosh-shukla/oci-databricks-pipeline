"""
oci_writer.py

Writes a DataFrame to Oracle Autonomous Database (ADB) tables using the
OCI wallet for connectivity.
"""


def write_to_oracle_adb(df, jdbc_url: str, table: str, connection_properties: dict):
    """Write a Spark DataFrame to an Oracle ADB table via JDBC."""
    (
        df.write
        .jdbc(
            url=jdbc_url,
            table=table,
            mode="append",
            properties=connection_properties,
        )
    )
