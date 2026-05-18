from pathlib import Path
from unittest.mock import MagicMock, patch

from .checker import check_video_format


def test_check_video_format_no_file():
    """Test missing file."""
    video_path = Path("/tmp/nonexistent_12345.mp4")
    is_valid, reason = check_video_format(video_path)

    assert is_valid is False
    assert "does not exist" in reason


def test_check_video_format_ffprobe_missing():
    """Test ffprobe not found."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run", side_effect=FileNotFoundError("ffprobe not found")
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "ffprobe not found" in reason


def test_check_video_format_ffprobe_error():
    """Test ffprobe returns error."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(returncode=1, stderr="ffprobe error"),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "ffprobe failed" in reason


def test_check_video_format_no_streams():
    """Test file with no video streams."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout='{"streams": []}',
            ),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "No video streams found" in reason


def test_check_video_format_hdr_pq():
    """Test HDR video (PQ transfer) fails check."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "smpte2084",
                        "color_primaries": "bt709"
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/hdr_test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "smpte2084" in reason


def test_check_video_format_bt2020():
    """Test wide-gamut video (bt2020) fails check."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "bt709",
                        "color_primaries": "bt2020"
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/hdr_test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "bt2020" in reason


def test_check_video_format_wrong_codec():
    """Test non-H.264 codec fails check."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "hevc",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "bt709",
                        "color_primaries": "bt709"
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/hevc_test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "hevc" in reason


def test_check_video_format_valid():
    """Test valid SDR BT.709 H.264 video passes check."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "bt709",
                        "color_primaries": "bt709",
                        "color_space": "bt709",
                        "bits_per_raw_sample": 8
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is True
            assert reason is None


def test_check_video_format_valid_string_bit_depth():
    """Test ffprobe string bit depth values are handled."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "bt709",
                        "color_primaries": "bt709",
                        "color_space": "bt709",
                        "bits_per_raw_sample": "8"
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is True
            assert reason is None


def test_check_video_format_rejects_string_high_bit_depth():
    """Test ffprobe string bit depth values over 8 fail."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "color_transfer": "bt709",
                        "color_primaries": "bt709",
                        "color_space": "bt709",
                        "bits_per_raw_sample": "10"
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is False
            assert "Bit depth 10" in reason


def test_check_video_format_valid_no_color_space():
    """Test valid video with unspecified color space (default to OK)."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout="""{
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "bits_per_raw_sample": 8
                    }]
                }""",
            ),
        ):
            video_path = Path("/tmp/test.mp4")
            is_valid, reason = check_video_format(video_path)
            assert is_valid is True
            assert reason is None
