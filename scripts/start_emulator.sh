#!/usr/bin/env bash
# Start Android emulator (first AVD found, or $AVD_NAME if set) and wait for boot.
set -euo pipefail

AVD_NAME="${AVD_NAME:-$(emulator -list-avds | head -n1)}"

if [ -z "$AVD_NAME" ]; then
  echo "No AVDs found. Create one with Android Studio or avdmanager." >&2
  exit 1
fi

if adb devices | grep -q "device$"; then
  echo "Device already running."
else
  echo "Starting emulator: $AVD_NAME"
  nohup emulator -avd "$AVD_NAME" > /tmp/emulator.log 2>&1 &
  disown
fi

adb wait-for-device

echo "Waiting for boot to complete..."
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r\n')" = "1" ]; do
  sleep 2
done

echo "Emulator booted."
adb devices
