"""
config/settings.py

Single source of truth for reading configuration. Every other module in the
pipeline calls `get_settings()` instead of touching YAML files directly.

Why this matters:
    - If we hardcode paths/bucket names inside bronze_loader.py, silver, gold, etc,
    then switching from local -> dev -> prod means hunting through every file.
    - By centralizing it here, switching environments is just one environment
    variable change (PIPELINE_ENV=dev vs PIPELINE_ENV=prod).
"""

import os
import yaml
from pathlib import Path

# The project root is two levels up from this file (config/settings.py -> project/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    """
    Thin wrapper around the loaded YAML dict.
    Using a class (instead of just returning a raw dict) means:
        - we can add validation later (e.g. "fail loudly if 'spark' section missing")
        - callers get a single, controlled way to read config
    """

    def __init__(self, config_dict: dict, environment: str):
        self._config = config_dict
        self.environment = environment

    def get(self, *keys, default=None):
        """
        Safely walk a nested path in the config.
        Example: settings.get("spark", "master") reads config["spark"]["master"]
        without raising a KeyError if a section is missing — returns `default` instead.
        """
        node = self._config
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def as_dict(self) -> dict:
        return self._config


def get_settings(environment: str = None) -> Settings:
    """
    Loads config.<environment>.yaml and returns a Settings object.

    environment resolution order:
        1. explicit argument passed by caller
        2. PIPELINE_ENV environment variable
        3. defaults to "dev"
    """
    if environment is None:
        environment = os.environ.get("PIPELINE_ENV", "dev")

    config_path = PROJECT_ROOT / "config" / f"config.{environment}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"No config file found for environment '{environment}' at {config_path}. "
            f"Expected something like config/config.{environment}.yaml"
        )

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    return Settings(config_dict, environment)

    # Quick manual test when this file is run directly (not imported).
    # This is NOT a formal unit test (that goes in tests/), just a fast sanity check
    # so we can prove settings.py works before anything else depends on it.


if __name__ == "__main__":
    settings = get_settings()
    print(f"Environment loaded: {settings.environment}")
    print(f"Log level:          {settings.get('logging', 'level')}")
    print(f"Spark master:       {settings.get('spark', 'master')}")
    print(f"Local data dir:     {settings.get('paths', 'local_data_dir')}")
    print(
        f"Missing key test:   {settings.get('does', 'not', 'exist', default='<default used>')}"
    )
