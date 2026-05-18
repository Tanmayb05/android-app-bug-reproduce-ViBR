def build(predicted_action: str, relevant_indices: list[int] | None = None) -> str:
    return f"""
    Your goal is to reproduce the action {predicted_action} from the GUI recording on a real device.
    I show you the three GUI screenshots by order. In the recording, the interaction with the highlighted
    purple region in the first GUI leads to the second GUI. The current GUI on your device is shown as the
    third GUI. Relevant region indices, if any: {relevant_indices or []}.

    On which element should you perform the action to achieve the same transition?
    Please follow the primitive in action space.

    Possible actions:
    1. tap - Example: {{ "action": "tap", "region": 2, "description": "Tap center of screen to open app." }}
    2. swipe - Example: {{ "action": "swipe", "from": [540, 1600], "to": [540, 400], "duration": 500, "description": "Swipe up to scroll." }}
    3. input_text - Example: {{ "action": "input_text", "text": "hello world", "description": "Type search query." }}
    4. back - Example: {{ "action": "back", "description": "Go back to previous screen." }}
    5. home - Example: {{ "action": "home", "description": "Return to home." }}
    6. wait - Example: {{ "action": "wait", "duration": 1500, "description": "Wait for animation to finish." }}
    7. no action - Example: {{ "action": "no action", "description": "No action needed." }}

    Return a JSON object describing the required action. Do not include any other text or explanation.
    """
