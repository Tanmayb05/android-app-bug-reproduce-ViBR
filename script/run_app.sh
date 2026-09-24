#!/usr/bin/env bash
# Run ViBR on active bug_dir (config.yml runs[0]), then print bug_dir
# so caller (Claude) can invoke the /report skill on it.
#
# Usage:
#   script/run_app.sh                # uses config.yml's active bug_dir
#   script/run_app.sh <bug_dir>      # override, e.g. data/video01b-amazefilemanager#2595
#   script/run_app.sh [<bug_dir>] [--config config.a.yml] [--device emulator-5554] [--algo ssim|clip]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${REPO_ROOT}/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python"
fi

BUG_DIR=""
CONFIG_PATH=""
EXTRA_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --config)
            CONFIG_PATH="$2"
            EXTRA_ARGS+=("$1" "$2")
            shift 2
            ;;
        --config=*)
            CONFIG_PATH="${1#--config=}"
            EXTRA_ARGS+=("$1")
            shift
            ;;
        --device|--algo)
            EXTRA_ARGS+=("$1" "$2")
            shift 2
            ;;
        --device=*|--algo=*)
            EXTRA_ARGS+=("$1")
            shift
            ;;
        *)
            BUG_DIR="$1"
            shift
            ;;
    esac
done

if [ -n "$BUG_DIR" ]; then
    "$PYTHON" -m approach.decision.segment_replay "$BUG_DIR" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
else
    "$PYTHON" -m approach.decision.segment_replay ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
    # Resolve the active bug_dir from the SAME config that was just run.
    BUG_DIR="$("$PYTHON" -c "
import sys
from approach.core.config_loader import get_config, get_active_run
path = sys.argv[1] if len(sys.argv) > 1 else None
print(get_active_run(get_config(path)))
" ${CONFIG_PATH:+"$CONFIG_PATH"})"
fi

echo "BUG_DIR=${BUG_DIR}"
