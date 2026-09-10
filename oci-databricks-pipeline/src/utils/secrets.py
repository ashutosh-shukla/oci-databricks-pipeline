"""
secrets.py

Pulls secrets from environment variables or a Databricks secret scope.
"""

import os


def get_secret(key: str, scope: str = None, dbutils=None) -> str:
    """
    Retrieve a secret.

    If running inside Databricks and a dbutils instance + scope are provided,
    pull from the Databricks secret scope. Otherwise fall back to
    environment variables (populated from .env in local/dev use).
    """
    if dbutils is not None and scope is not None:
        return dbutils.secrets.get(scope=scope, key=key)

    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Secret \x27{key}\x27 not found in environment or secret scope.")
    return value
