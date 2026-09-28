"""config/settings.py - loads NON-secret config from config.<env>.yaml."""

import os
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    """Read-only view over one environment's YAML configuration."""

    def __init__(self, config_dict: dict, environment: str):
        self._config = config_dict
        self.environment = environment

    @classmethod
    def load(cls, environment: str = None) -> "Settings":
        """Order: explicit argument -> PIPELINE_ENV variable -> 'dev'."""
        environment = environment or os.environ.get("PIPELINE_ENV", "dev")
        path = PROJECT_ROOT / "config" / f"config.{environment}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No config file for '{environment}' at {path}")
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f), environment)

    def get(self, *keys, default=None):
        """settings.get('spark', 'master') - safe nested lookup."""
        node = self._config
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def as_dict(self) -> dict:
        return dict(self._config)


if __name__ == "__main__":
    s = Settings.load()
    print(s.environment, s.get("spark", "master"), s.get("nope", default="<default>"))
