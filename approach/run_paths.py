"""Resolve output/input file paths for a single run's bug directory."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunPaths:
    """All paths for a run, rooted at a single bug directory."""

    run_dir: Path
    video: Path
    apk: Path
    debug_log: Path
    issue_md: Path
    summary_json: Path
    run_log: Path
    truth_json: Path
    video_analysis_json: Path
    artifacts_dir: Path
    cache_dir: Path


def build_run_paths(bug_dir: str | Path) -> RunPaths:
    """Compose all run paths under bug_dir. Pure: no filesystem access."""
    run_dir = Path(bug_dir)
    return RunPaths(
        run_dir=run_dir,
        video=run_dir / "video.mp4",
        apk=run_dir / "app.apk",
        debug_log=run_dir / "debug.log",
        issue_md=run_dir / "issue.md",
        summary_json=run_dir / "summary.json",
        run_log=run_dir / "run.log",
        truth_json=run_dir / "truth.json",
        video_analysis_json=run_dir / "video_analysis.json",
        artifacts_dir=run_dir / "artifacts",
        cache_dir=run_dir / "cache",
    )


def ensure_run_dirs(paths: RunPaths) -> None:
    """Create run_dir, artifacts_dir, and cache_dir if missing."""
    paths.run_dir.mkdir(parents=True, exist_ok=True)
    paths.artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths.cache_dir.mkdir(parents=True, exist_ok=True)


def validate_run_inputs(paths: RunPaths) -> None:
    """Raise FileNotFoundError if required pre-populated inputs are missing."""
    if not paths.video.exists():
        raise FileNotFoundError(f"Video not found: {paths.video}")
    if not paths.apk.exists():
        raise FileNotFoundError(f"APK not found: {paths.apk}")
