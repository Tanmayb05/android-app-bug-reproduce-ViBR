import time
import logging
from config_loader import get_config

logger = logging.getLogger(__name__)

# Human-readable action parser and execution script for Android ADB automation

def execute_actions(device, actions):
    """
    Execute a list of UI actions on an Android device via ADB.

    Args:
        device: An instance of ADBDeviceController
        actions: List of action dicts, each with:
            - 'action': str (e.g. 'tap', 'swipe', 'input_text', ...)
            - plus relevant keys (e.g. 'position', 'text', 'from', 'to', 'duration').

    Unknown actions are ignored with a warning.
    """
    action_config = get_config().get("actions", {})
    for i, action in enumerate(actions):
        logger.info(f"[{i+1}] {action.get('description', 'Executing action')} -> {action['action']}")

        if action["action"] == "tap":
            x, y = action["position"]
            device.click(x, y)

        elif action["action"] == "double_tap":
            x, y = action["position"]
            device.click(x, y)
            time.sleep(action_config.get("double_tap_inter_click_sleep", 0.1))
            device.click(x, y)

        elif action["action"] == "long_press":
            x, y = action["position"]
            duration = action.get(
                "duration", action_config.get("default_long_press_duration_ms", 1000)
            )
            device.long_click(x, y, duration)

        elif action["action"] == "swipe":
            x1, y1 = action["from"]
            x2, y2 = action["to"]
            duration = action.get(
                "duration", action_config.get("default_swipe_duration_ms", 500)
            )
            device.swipe(x1, y1, x2, y2, duration)

        elif action["action"] == "input_text":
            if "position" in action:
                x, y = action["position"]
                device.click(x, y)
            text = action["text"]
            device.input_text(text)

        elif action["action"] == "back":
            device.back()

        elif action["action"] == "home":
            # 'input keyevent 3' is the Android HOME key
            device.shell("input keyevent 3")

        elif action["action"] == "wait" or action["action"] == "no action":
            # 'wait' and 'no action' both just pause for the given duration (ms)
            duration = action.get(
                "duration", action_config.get("default_wait_duration_ms", 1000)
            )
            time.sleep(duration / 1000.0)

        else:
            logger.warning(f"Unknown action type: {action['action']}")
