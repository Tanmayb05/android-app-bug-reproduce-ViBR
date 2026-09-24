#!/usr/bin/env bash
# Run ViBR variants a/b/c in parallel, one per emulator.
#
# Each variant uses its own config file (config.a.yml / config.b.yml / config.c.yml),
# which pins its own adb.device_id and adb.ui_dump_local_path so the three runs
# never touch the same emulator or the same host-side UI dump.
#
# Usage:
#   script/run_parallel.sh                # each config's own runs[0]
#   script/run_parallel.sh 07             # data/video07{a,b,c}-* override
#   script/run_parallel.sh 07 --only a,c  # subset of variants
#   script/run_parallel.sh --boot 07      # boot the emulators first
#
# Env:
#   STAGGER_SECONDS   delay between launches (default 30)
#
# Prerequisite: the app under test must already be installed and foregrounded on
# each emulator -- nothing in this repo installs an APK.

# NOT `set -e`: the first nonzero `wait` would abort and we would lose the
# other variants' exit codes.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

STAGGER_SECONDS="${STAGGER_SECONDS:-30}"
VARIANTS="a b c"
VIDEO_NUM=""
BOOT=0

while [ $# -gt 0 ]; do
    case "$1" in
        --only)
            VARIANTS="$(echo "$2" | tr ',' ' ')"
            shift 2
            ;;
        --boot)
            BOOT=1
            shift
            ;;
        -h|--help)
            sed -n '2,20p' "${BASH_SOURCE[0]}"
            exit 0
            ;;
        *)
            VIDEO_NUM="$1"
            shift
            ;;
    esac
done

if [ "$BOOT" -eq 1 ]; then
    scripts/start_emulators.sh || { echo "Emulator boot failed." >&2; exit 1; }
fi

LOG_DIR="logs/parallel"
mkdir -p "$LOG_DIR"

# Resolve data/video<NUM><letter>-* to exactly one bug dir.
resolve_bug_dir() {
    local letter="$1"
    local matches=(data/video"${VIDEO_NUM}${letter}"-*)
    if [ ! -d "${matches[0]}" ]; then
        echo "No bug dir matching data/video${VIDEO_NUM}${letter}-*" >&2
        return 1
    fi
    if [ "${#matches[@]}" -ne 1 ]; then
        echo "Ambiguous match for video${VIDEO_NUM}${letter}: ${matches[*]}" >&2
        return 1
    fi
    printf '%s' "${matches[0]}"
}

declare -a PIDS=()
declare -a LABELS=()
first=1

for v in $VARIANTS; do
    cfg="config.${v}.yml"
    if [ ! -f "$cfg" ]; then
        echo "Missing config file: $cfg" >&2
        exit 1
    fi

    if [ -n "$VIDEO_NUM" ]; then
        bug_dir="$(resolve_bug_dir "$v")" || exit 1
        label="video${VIDEO_NUM}${v}"
    else
        bug_dir=""
        label="config-${v}-default"
    fi

    # Stagger: all variants import CLIP and share XDG_CACHE_HOME, so a cold
    # HuggingFace cache can be corrupted by three simultaneous downloads.
    if [ "$first" -eq 0 ] && [ "$STAGGER_SECONDS" -gt 0 ]; then
        echo "Staggering ${STAGGER_SECONDS}s before ${label}..."
        sleep "$STAGGER_SECONDS"
    fi
    first=0

    out="${LOG_DIR}/${label}.out"
    echo "Launching ${label} (config=${cfg}) -> ${out}"
    if [ -n "$bug_dir" ]; then
        script/run_app.sh "$bug_dir" --config "$cfg" > "$out" 2>&1 &
    else
        script/run_app.sh --config "$cfg" > "$out" 2>&1 &
    fi
    PIDS+=("$!")
    LABELS+=("$label")
done

echo "Waiting for ${#PIDS[@]} run(s)..."
FAILED=0
for i in "${!PIDS[@]}"; do
    if wait "${PIDS[$i]}"; then
        echo "OK    ${LABELS[$i]}"
    else
        code=$?
        echo "FAIL  ${LABELS[$i]} (exit ${code}) -- see ${LOG_DIR}/${LABELS[$i]}.out" >&2
        FAILED=1
    fi
done

# Re-emit each run's BUG_DIR= line so the caller can chain into /report.
for i in "${!LABELS[@]}"; do
    grep -h '^BUG_DIR=' "${LOG_DIR}/${LABELS[$i]}.out" 2>/dev/null || true
done

exit "$FAILED"
