# ADR 0002: Separate native benchmark inputs and outputs

## Status

Accepted, 2026-10-05.

## Context

The canonical benchmark stores immutable videos/APKs under `benchmark/inputs`
and run artifacts under `benchmark/outputs/vibr/<run-id>`. ViBR historically
assumed both lived in one `bug_dir`, and its video-normalization step may replace
`video.mp4` in place. Applying that behavior to a canonical hardlink could alter
benchmark data or historical sources.

## Decision

`RunPaths` accepts explicit external video and APK paths while all other paths
remain rooted in the writable run directory. Native benchmark selection is
resolved by `tools/benchmark_paths.py`. New artifacts use
`benchmark/outputs/vibr/<run-id>/` directly. A nonempty migrated historical
run directory is protected from overwrite. When normalization is required,
ViBR copies the video beneath that run directory and converts the private copy.

Every completed or failed native run writes `run-manifest.json` with its
command, timestamps, tool version, and input/output checksums.

## Consequences

- Canonical benchmark inputs remain read-only.
- Legacy one-directory runs continue to use the default `RunPaths` behavior.
- A prior run directory must be moved or archived before rerunning the ID.
- Video normalization may add an `_input/video.mp4` working artifact to the run
  output directory.
