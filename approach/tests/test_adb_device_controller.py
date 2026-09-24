import logging
import subprocess

import pytest

from approach.device import adb_device_controller as adb_mod
from approach.device.adb_device_controller import ADBDeviceController


@pytest.fixture
def captured_argv(monkeypatch):
    """Capture argv passed to subprocess.run, returning a successful result."""
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(adb_mod.subprocess, "run", fake_run)
    return calls


def _stub_config(monkeypatch, adb_config: dict) -> None:
    monkeypatch.setattr(adb_mod, "get_config", lambda: {"adb": adb_config})


def test_explicit_device_id_wins_over_config_and_env(monkeypatch, captured_argv):
    _stub_config(monkeypatch, {"device_id": "emulator-5556"})
    monkeypatch.setenv("ANDROID_SERIAL", "emulator-5558")

    device = ADBDeviceController(device_id="emulator-5554")
    device.click(10, 20)

    assert device.device_id == "emulator-5554"
    assert captured_argv[0][:3] == ["adb", "-s", "emulator-5554"]


def test_config_device_id_wins_over_env(monkeypatch, captured_argv):
    _stub_config(monkeypatch, {"device_id": "emulator-5556"})
    monkeypatch.setenv("ANDROID_SERIAL", "emulator-5558")

    device = ADBDeviceController()
    device.click(10, 20)

    assert device.device_id == "emulator-5556"
    assert captured_argv[0][:3] == ["adb", "-s", "emulator-5556"]


def test_env_used_when_config_has_no_device_id(monkeypatch, captured_argv):
    _stub_config(monkeypatch, {})
    monkeypatch.setenv("ANDROID_SERIAL", "emulator-5558")

    device = ADBDeviceController()
    device.click(10, 20)

    assert device.device_id == "emulator-5558"
    assert captured_argv[0][:3] == ["adb", "-s", "emulator-5558"]


def test_no_device_id_yields_bare_adb(monkeypatch, captured_argv):
    _stub_config(monkeypatch, {})
    monkeypatch.delenv("ANDROID_SERIAL", raising=False)

    device = ADBDeviceController()
    device.click(10, 20)

    assert device.device_id is None
    assert captured_argv[0] == ["adb", "shell", "input", "tap", "10", "20"]
    assert "-s" not in captured_argv[0]


def test_empty_env_serial_normalized_to_none(monkeypatch, captured_argv):
    _stub_config(monkeypatch, {})
    monkeypatch.setenv("ANDROID_SERIAL", "")

    device = ADBDeviceController()

    assert device.device_id is None


def test_adb_failure_logs_warning_and_does_not_raise(monkeypatch, caplog):
    _stub_config(monkeypatch, {"device_id": "emulator-5554"})

    def failing_run(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv, 1, stdout="", stderr="adb: more than one device/emulator"
        )

    monkeypatch.setattr(adb_mod.subprocess, "run", failing_run)
    device = ADBDeviceController()

    with caplog.at_level(logging.WARNING, logger=adb_mod.__name__):
        result = device._adb(["shell", "input", "tap", "1", "2"])

    assert result.returncode == 1
    assert "adb command failed (exit 1)" in caplog.text
    assert "more than one device/emulator" in caplog.text
