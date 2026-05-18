from typing import Any


def build(action: str = "", target_region: Any = "") -> str:
    return (
        "You are given two screenshots of an Android interface:\n"
        "1. The first image is the REFERENCE state from a stable app video.\n"
        "2. The second image is the CURRENT real-time app state.\n"
        "\n"
        "You also get a possible action and region that has to be executed to reach the target state. "
        "Take this into account but also keep in mind that something else could be the action.\n"
        f"Action: {action}\n"
        f"Region: {target_region}\n"
        "Your task is to determine if the current screen is functionally consistent with the reference.\n"
        "That means: Can the user perform the same action from the current screen as in the reference?\n"
        "\n"
        "- Minor differences in layout, text alignment, icon position or additional items that do not influence the action DO NOT matter.\n"
        "- For home screens or app drawers, the presence of extra app icons, widgets, or a different order of icons DOES NOT matter, as long as the same action can be performed from both screens.\n"
        "- Focus on whether the same buttons, inputs, or menus are present and usable. Sometimes the keyboard or something can block some parts, this still means the state is consistent.\n"
        "- Ignore small stylistic or timing variations (e.g., animation state, different time shown, small icon differences).\n"
        "- Cases like the home screen or similar, where icons can be ordered differently do not matter if the same action can be performed.\n"
        "\n"
        "Respond strictly in the following JSON format:\n"
        '{ "same_state": "yes" } or { "same_state": "no", "description": "<reason>" }'
    )
