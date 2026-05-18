import json
import subprocess
from pathlib import Path


def check_video_format(video_path: Path) -> tuple[bool, str | None]:
    """
    Probe video with ffprobe. Return (is_valid, reason).
    Valid = H.264 + yuv420p + BT.709 (or no HDR tags) + 8-bit or less.
    """
    if not video_path.exists():
        return False, f"File does not exist: {video_path}"

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return False, "ffprobe not found. Install ffmpeg."
    except subprocess.TimeoutExpired:
        return False, "ffprobe timeout"
    except Exception as e:
        return False, f"ffprobe error: {e}"

    if result.returncode != 0:
        return False, f"ffprobe failed: {result.stderr}"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "ffprobe output not valid JSON"

    streams = data.get("streams", [])
    if not streams:
        return False, "No video streams found"

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        return False, "No video stream in file"

    # Check codec
    codec = video_stream.get("codec_name")
    if codec != "h264":
        return False, f"Codec is {codec}, need h264"

    # Check pixel format
    pix_fmt = video_stream.get("pix_fmt")
    if pix_fmt != "yuv420p":
        return False, f"Pixel format is {pix_fmt}, need yuv420p"

    # Check bit depth
    bits_per_raw = video_stream.get("bits_per_raw_sample")
    if bits_per_raw and bits_per_raw > 8:
        return False, f"Bit depth {bits_per_raw}, need 8-bit or less"

    # Check for HDR markers
    color_transfer = video_stream.get("color_transfer", "unknown")
    if color_transfer in ("smpte2084", "arib-std-b67", "smpte-st-2084"):
        return False, f"HDR transfer curve detected: {color_transfer}"

    color_primaries = video_stream.get("color_primaries", "unknown")
    if color_primaries == "bt2020":
        return False, "Wide-gamut primaries (bt2020) detected"

    # If color_space is explicitly set and not bt709, flag it
    color_space = video_stream.get("color_space")
    if color_space and color_space not in ("bt709", "unknown", "unspecified"):
        return False, f"Color space is {color_space}, need bt709"

    return True, None
