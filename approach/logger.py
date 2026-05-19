import logging
import yaml
from pathlib import Path
from typing import Any


def setup_logger(
    app_name: str,
    quality: str,
    apps_root: Path,
    config: dict[str, Any] | None = None,
) -> logging.Logger:
    """Configure root logger for a run and log config.

    Args:
        app_name: Application name (e.g., "gmail")
        quality: Video quality ("good" or "bad")
        apps_root: Path to apps directory
        config: Optional config dict to log at start

    Returns:
        Configured root logger
    """
    # Create app directory if needed
    app_dir = apps_root / app_name
    app_dir.mkdir(parents=True, exist_ok=True)

    # Log file path (overwrites on each run)
    log_file = app_dir / f"{quality}_run.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler (write mode — overwrites)
    file_handler = logging.FileHandler(log_file, mode="w")
    logging_config = config.get("logging", {}) if config else {}
    file_level = logging_config.get("file_level", "DEBUG")
    console_level = logging_config.get("console_level", "INFO")
    file_handler.setLevel(getattr(logging, str(file_level).upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, str(console_level).upper()))

    # Format
    formatter = logging.Formatter(
        logging_config.get(
            "format", "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        ),
        datefmt=logging_config.get("date_format", "%Y-%m-%d %H:%M:%S"),
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log config at start if provided
    if config:
        logger = logging.getLogger(__name__)
        logger.info("=" * 80)
        logger.info("RUN CONFIGURATION")
        logger.info("=" * 80)
        config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)
        for line in config_yaml.strip().split("\n"):
            logger.info(line)
        logger.info("=" * 80)

    return root_logger
