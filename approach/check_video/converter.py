import subprocess
import tempfile
from pathlib import Path


def _get_stream_info(video_path: Path) -> dict:
    """Helper: get video stream info from ffprobe."""
    import json

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)
    video_stream: dict = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    return video_stream


def _is_hdr(video_path: Path) -> bool:
    """Check if video has HDR markers."""
    try:
        stream = _get_stream_info(video_path)
        color_transfer = stream.get("color_transfer", "unknown")
        color_primaries = stream.get("color_primaries", "unknown")
        return (
            color_transfer in ("smpte2084", "arib-std-b67", "smpte-st-2084")
            or color_primaries == "bt2020"
        )
    except Exception:
        return False


def convert_to_sdr_bt709(video_path: Path) -> None:
    """
    Convert video to SDR BT.709 H.264 yuv420p in-place.
    Uses tone-mapping for HDR, simple normalize for SDR.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    is_hdr = _is_hdr(video_path)

    # Choose filter based on HDR detection
    if is_hdr:
        vf = (
            "zscale=t=linear:npl=100,format=gbrpf32le,"
            "zscale=p=bt709:t=bt709:m=bt709:r=tv,"
            "tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
        )
    else:
        vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"

    # Write to temp file first
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-colorspace",
            "bt709",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-movflags",
            "+faststart",
            "-y",
            tmp_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed:\n{result.stderr}")

        # Atomic replace
        Path(tmp_path).replace(video_path)

    except Exception:
        # Clean up temp file on error
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass
        raise
