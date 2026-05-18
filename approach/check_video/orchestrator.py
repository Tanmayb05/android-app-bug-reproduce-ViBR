import logging
from pathlib import Path

from .checker import check_video_format
from .converter import convert_to_sdr_bt709

logger = logging.getLogger(__name__)


def ensure_sdr_bt709(video_path: Path) -> None:
    """
    Check if video is SDR BT.709. If not, convert and verify.
    Raises RuntimeError if post-conversion check fails.
    """
    is_valid, reason = check_video_format(video_path)

    if is_valid:
        logger.info(f"Video format OK: {video_path}")
        return

    logger.warning(f"Video not SDR BT.709: {reason}. Converting...")

    try:
        convert_to_sdr_bt709(video_path)
    except Exception as e:
        raise RuntimeError(f"Conversion failed: {e}") from e

    logger.info("Conversion done. Verifying...")

    is_valid2, reason2 = check_video_format(video_path)
    if not is_valid2:
        raise RuntimeError(f"Post-conversion check failed: {reason2}")

    logger.info("Video is now SDR BT.709.")
