import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_paths import build_run_paths, ensure_run_dirs, validate_run_inputs


def test_build_run_paths_field_values():
    paths = build_run_paths("data/video03-k92#9005")

    run_dir = Path("data/video03-k92#9005")
    assert paths.run_dir == run_dir
    assert paths.video == run_dir / "video.mp4"
    assert paths.apk == run_dir / "app.apk"
    assert paths.debug_log == run_dir / "debug.log"
    assert paths.issue_md == run_dir / "issue.md"
    assert paths.summary_json == run_dir / "summary.json"
    assert paths.run_log == run_dir / "run.log"
    assert paths.truth_json == run_dir / "truth.json"
    assert paths.video_analysis_json == run_dir / "video_analysis.json"
    assert paths.artifacts_dir == run_dir / "artifacts"
    assert paths.cache_dir == run_dir / "cache"


def test_build_run_paths_accepts_path_and_str(tmp_path):
    from_str = build_run_paths(str(tmp_path))
    from_path = build_run_paths(tmp_path)

    assert from_str == from_path


def test_build_run_paths_creates_no_filesystem_entries(tmp_path):
    bug_dir = tmp_path / "video01-app#1"
    build_run_paths(bug_dir)

    assert not bug_dir.exists()


def test_ensure_run_dirs_creates_directories(tmp_path):
    bug_dir = tmp_path / "video01-app#1"
    paths = build_run_paths(bug_dir)

    ensure_run_dirs(paths)

    assert paths.run_dir.is_dir()
    assert paths.artifacts_dir.is_dir()
    assert paths.cache_dir.is_dir()
    assert not paths.video.exists()
    assert not paths.apk.exists()


def test_validate_run_inputs_raises_on_missing_video(tmp_path):
    paths = build_run_paths(tmp_path)
    paths.apk.touch()

    try:
        validate_run_inputs(paths)
    except FileNotFoundError as exc:
        assert "video" in str(exc).lower()
    else:
        raise AssertionError("Expected FileNotFoundError for missing video")


def test_validate_run_inputs_raises_on_missing_apk(tmp_path):
    paths = build_run_paths(tmp_path)
    paths.video.touch()

    try:
        validate_run_inputs(paths)
    except FileNotFoundError as exc:
        assert "apk" in str(exc).lower()
    else:
        raise AssertionError("Expected FileNotFoundError for missing apk")


def test_validate_run_inputs_passes_when_present(tmp_path):
    paths = build_run_paths(tmp_path)
    paths.video.touch()
    paths.apk.touch()

    validate_run_inputs(paths)
