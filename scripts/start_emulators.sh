#!/usr/bin/env bash
# Boot the three Pixel 6 AVDs on fixed ports and wait for each to finish booting.
# AVDs must already exist (see `emulator -list-avds`) -- this script does not create them.
#
# Usage:
#   scripts/start_emulators.sh                       # Pixel_6_a / Pixel_6_b / Pixel_6_c
#   scripts/start_emulators.sh AVD_A AVD_B AVD_C     # custom AVD names
#
# Env:
#   BOOT_TIMEOUT   seconds to wait per emulator for sys.boot_completed (default 300)
#
# Ports must be even and 2 apart: each emulator consumes N (console) and N+1 (adb),
# which yields the serials emulator-5554 / emulator-5556 / emulator-5558 that
# config.a.yml / config.b.yml / config.c.yml target via adb.device_id.
set -uo pipefail

AVDS=("${1:-Pixel_6_a}" "${2:-Pixel_6_b}" "${3:-Pixel_6_c}")
PORTS=(5554 5556 5558)
BOOT_TIMEOUT="${BOOT_TIMEOUT:-300}"

adb start-server >/dev/null 2>&1 || true
AVAILABLE="$(emulator -list-avds)"

for i in "${!AVDS[@]}"; do
    avd="${AVDS[$i]}"
    port="${PORTS[$i]}"
    serial="emulator-${port}"

    if ! grep -qx "$avd" <<< "$AVAILABLE"; then
        echo "AVD not found: $avd" >&2
        echo "Available AVDs:" >&2
        echo "$AVAILABLE" >&2
        exit 1
    fi

    if adb devices | grep -q "^${serial}[[:space:]]*device$"; then
        echo "Already running: ${serial} (${avd}) -- skipping"
        continue
    fi

    echo "Starting ${avd} on ${serial}..."
    nohup emulator -avd "$avd" -port "$port" > "/tmp/emulator-${port}.log" 2>&1 &
    disown
done

for port in "${PORTS[@]}"; do
    serial="emulator-${port}"
    echo "Waiting for ${serial} to boot (timeout ${BOOT_TIMEOUT}s)..."
    # Per-serial wait: a bare `adb wait-for-device` returns as soon as ANY device appears.
    adb -s "$serial" wait-for-device
    elapsed=0
    until [ "$(adb -s "$serial" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r\n')" = "1" ]; do
        sleep 2
        elapsed=$((elapsed + 2))
        if [ "$elapsed" -ge "$BOOT_TIMEOUT" ]; then
            echo "Timed out waiting for ${serial}; see /tmp/emulator-${port}.log" >&2
            echo "(If the port was already taken, the emulator silently picks another one.)" >&2
            exit 1
        fi
    done
    echo "${serial} booted."
done

adb devices
