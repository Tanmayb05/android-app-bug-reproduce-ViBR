import subprocess
import time
import os
from config_loader import get_config

class ADBDeviceController:
    def __init__(self, device_id=None):
        """Initialize with optional device ID for ADB."""
        config = get_config().get("adb", {})
        self.device_id = device_id
        self.pre_action_sleep = config.get("pre_action_sleep", 0.2)
        self.default_swipe_duration_ms = config.get("default_swipe_duration_ms", 500)
        self.default_long_click_duration_ms = config.get(
            "default_long_click_duration_ms", 1000
        )
        self.screenshot_remote_path = config.get(
            "screenshot_remote_path", "/sdcard/screenshot-{index}.png"
        )
        self.ui_dump_remote_path = config.get("ui_dump_remote_path", "/sdcard/ui_dump.xml")
        self.ui_dump_local_path = config.get("ui_dump_local_path", "temp/ui_dump.xml")

    def _adb(self, cmd):
        """Run an adb command with optional device targeting."""
        base = ["adb"]
        if self.device_id:
            base += ["-s", self.device_id]
        return subprocess.run(base + cmd, capture_output=True, text=True)

    def click(self, x, y):
        """Simulate a tap at (x, y) on the device screen."""
        time.sleep(self.pre_action_sleep)
        self._adb(["shell", "input", "tap", str(int(x)), str(int(y))])

    def input_text(self, text):
        """Send text input to the device (escapes spaces)."""
        time.sleep(self.pre_action_sleep)
        text = text.replace(" ", "\\ ")  # Escape spaces
        self._adb(["shell", "input", "text", text])

    def swipe(self, x1, y1, x2, y2, duration_ms=None):
        """Simulate swipe from (x1, y1) to (x2, y2) with optional duration."""
        time.sleep(self.pre_action_sleep)
        duration_ms = duration_ms or self.default_swipe_duration_ms
        self._adb([
            "shell", "input", "swipe",
            str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(duration_ms)
        ])

    def long_click(self, x, y, duration_ms=None):
        """Simulate a long click by swiping a short distance for a duration."""
        time.sleep(self.pre_action_sleep)
        duration_ms = duration_ms or self.default_long_click_duration_ms
        self.swipe(x, y, x+1, y+1, duration_ms)

    def back(self):
        """Send back key event."""
        time.sleep(self.pre_action_sleep)
        self._adb(["shell", "input", "keyevent", "4"])

    def screenshot(self, index, save_path):
        """Take a screenshot and pull it from device to local path."""
        remote_path = self.screenshot_remote_path.format(index=index)
        local_path = os.path.join(save_path, f"screenshot-{index}.png")
        print(f"Taking screenshot: {remote_path} -> {local_path}")
        self._adb(["shell", "/system/bin/screencap", "-p", remote_path])
        self._adb(["pull", remote_path, local_path])
        return local_path

    def shell(self, command):
        """Run a custom shell command on the device."""
        return self._adb(["shell"] + command.split())

    def get_ui_xml(self, local_path=None):
        """
        Dump UI hierarchy to XML and pull it locally.
        Returns XML string, or raises error if failed.
        """
        remote_path = self.ui_dump_remote_path
        local_path = local_path or self.ui_dump_local_path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        self._adb(["shell", "uiautomator", "dump", remote_path])
        result = self._adb(["pull", remote_path, local_path])
        if result.returncode == 0 and os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise RuntimeError("Failed to dump or pull UI XML")
