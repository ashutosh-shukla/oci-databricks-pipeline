"""config/credentials.py - loads SECRETS from .env. Never logs secret values."""

import os
from typing import Iterable

from dotenv import load_dotenv

from config.settings import PROJECT_ROOT


class Credentials:
    """Access point for secrets held in environment variables / .env."""

    def __init__(self, env_file=None):
        self._env_file = env_file or (PROJECT_ROOT / ".env")
        load_dotenv(dotenv_path=self._env_file)

    def get(self, key: str, required: bool = True, default: str = None) -> str:
        value = os.environ.get(key, default)
        if required and not value:
            raise EnvironmentError(
                f"Missing required secret '{key}'. Compare .env with .env.example."
            )
        return value

    def status(self, keys: Iterable[str]) -> dict:
        """Which keys are set? Returns booleans only - never the values."""
        return {k: bool(os.environ.get(k)) for k in keys}


if __name__ == "__main__":
    creds = Credentials()
    for key, ok in creds.status(["DATABRICKS_HOST", "DATABRICKS_TOKEN"]).items():
        print(f"{key}: {'set' if ok else 'MISSING'}")
