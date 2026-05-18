"""Load and cache YAML configuration."""

from pathlib import Path
from typing import Any
import yaml

CONFIG_PATH = Path(__file__).parent / "input" / "config.yml"

_config: dict[str, Any] | None = None
_config_path: Path = CONFIG_PATH


def load_config(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    """Load YAML config from file."""
    with open(Path(path)) as f:
        return yaml.safe_load(f)


def get_config(path: Path | str | None = None) -> dict[str, Any]:
    """Get cached config singleton."""
    global _config, _config_path
    if path is not None:
        requested_path = Path(path)
        if _config is None or requested_path != _config_path:
            _config_path = requested_path
            _config = load_config(_config_path)
        return _config

    if _config is None:
        _config = load_config(_config_path)
    return _config
