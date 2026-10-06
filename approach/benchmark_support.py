"""Shared-benchmark adapter for ViBR native runs."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


WORKSPACE = Path(__file__).resolve().parents[3]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from tools.benchmark_paths import (  # type: ignore[import-not-found]  # noqa: E402
    BenchmarkPathError,
    BenchmarkRun,
    resolve_run,
    tool_version,
    write_run_manifest,
)


def resolve_benchmark_run(args) -> BenchmarkRun:
    return resolve_run(
        "vibr",
        benchmark_root=args.benchmark_root,
        run_id=args.run_id,
        video_id=args.video_id,
        variant=args.variant,
        app_slug=args.app_slug,
        bug_id=args.bug_id,
    )


def ensure_fresh_output(run: BenchmarkRun) -> None:
    """Never overwrite a prior benchmark run or migrated historical output."""
    if run.output_dir.exists() and any(run.output_dir.iterdir()):
        raise BenchmarkPathError(
            f"Benchmark output directory is not empty: {run.output_dir}. "
            "Prior benchmark runs and migrated historical outputs are never "
            "overwritten; move/archive the run directory contents first."
        )


def started_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record_run(
    run: BenchmarkRun,
    *,
    command: Sequence[str],
    start: str,
    status: str,
    base_config: Path,
) -> Path:
    return write_run_manifest(
        run,
        tool="vibr",
        command=command,
        started_at=start,
        status=status,
        version=tool_version(Path(__file__).resolve().parents[1]),
        extra_inputs=[base_config],
    )
