"""Load and cache YAML configuration."""

from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).parent / "input" / "config.yml"

_config: dict | None = None


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load YAML config from file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_config() -> dict:
    """Get cached config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
