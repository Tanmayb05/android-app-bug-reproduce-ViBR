import base64
import os
from pathlib import Path
from typing import Any

"""
Provider facade for visual app state comparison, action region prediction,
and relevant region identification for Android GUI screenshots.

Provider selection:
- MODEL_PROVIDER=openai or MODEL_PROVIDER=gemini forces a provider.
- OpenAI is used when OPENAI_API_KEY or OPEN_AI_KEY is present.
- Gemini is used when no OpenAI key is present and GEMINI_API_KEY is present.
"""

ENV_PATH = Path(__file__).resolve().parents[1] / ".env.local"


def _load_dotenv(path: Path = ENV_PATH) -> None:
    """Load simple KEY=VALUE pairs without requiring python-dotenv."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _openai_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_KEY")


def _gemini_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY")


def _openai_model() -> str:
    _load_dotenv()
    return os.environ.get("OPENAI_MODEL", "gpt-4o")


def _gemini_model() -> str:
    _load_dotenv()
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def active_provider() -> str:
    _load_dotenv()
    requested_provider = os.environ.get("MODEL_PROVIDER", "").strip().lower()
    if requested_provider:
        if requested_provider not in {"openai", "gemini"}:
            raise RuntimeError("MODEL_PROVIDER must be either 'openai' or 'gemini'.")
        if requested_provider == "openai" and not _openai_api_key():
            raise RuntimeError("MODEL_PROVIDER=openai requires OPENAI_API_KEY or OPEN_AI_KEY.")
        if requested_provider == "gemini" and not _gemini_api_key():
            raise RuntimeError("MODEL_PROVIDER=gemini requires GEMINI_API_KEY.")
        return requested_provider

    if _openai_api_key():
        return "openai"
    if _gemini_api_key():
        return "gemini"
    raise RuntimeError(
        "No model API key found. Add OPENAI_API_KEY, OPEN_AI_KEY, or GEMINI_API_KEY to .env.local."
    )


def ping_model_connections() -> str:
    """
    Ping configured providers at startup and return the selected provider.

    MODEL_PROVIDER overrides auto-selection. Otherwise, OpenAI has priority when both
    OpenAI and Gemini keys are present.
    """
    _load_dotenv()
    statuses: list[str] = []

    openai_key = _openai_api_key()
    gemini_key = _gemini_api_key()

    if openai_key:
        try:
            client = _openai_client(openai_key)
            response = client.chat.completions.create(
                model=_openai_model(),
                messages=[{"role": "user", "content": "Reply with pong."}],
                max_tokens=8,
            )
            text = response.choices[0].message.content or ""
            statuses.append(f"OpenAI -> pong ({text.strip() or 'ok'})")
        except Exception as exc:
            statuses.append(f"OpenAI -> failed ({exc})")
    else:
        statuses.append("OpenAI -> no key")

    if gemini_key:
        try:
            client = _gemini_client(gemini_key)
            response = client.models.generate_content(
                model=_gemini_model(),
                contents="Reply with pong.",
            )
            statuses.append(f"Gemini -> pong ({response.text.strip() or 'ok'})")
        except Exception as exc:
            statuses.append(f"Gemini -> failed ({exc})")
    else:
        statuses.append("Gemini -> no key")

    provider = active_provider()
    print("LLM ping-pong connection link:")
    for status in statuses:
        print(f"  {status}")
    print(f"Selected provider: {provider}")
    return provider


def encode_image(image_path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _openai_client(api_key: str | None = None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI support requires the openai package.") from exc

    api_key = api_key or _openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY or OPEN_AI_KEY is required for OpenAI.")
    return OpenAI(api_key=api_key)


def _gemini_client(api_key: str | None = None) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini support requires the google-genai package.") from exc

    resolved_key = api_key or _gemini_api_key()
    if not resolved_key:
        raise RuntimeError("GEMINI_API_KEY is required for Gemini.")
    return genai.Client(api_key=resolved_key)


def _gemini_image(path: str) -> Any:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Gemini image support requires Pillow.") from exc

    return Image.open(path)


def _ask_openai(prompt: str, image_paths: list[str], details: list[str] | None = None) -> str:
    details = details or ["high"] * len(image_paths)
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for image_path, detail in zip(image_paths, details):
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encode_image(image_path)}",
                    "detail": detail,
                },
            }
        )

    response = _openai_client().chat.completions.create(
        model=_openai_model(),
        messages=[{"role": "user", "content": content}],
    )
    return (response.choices[0].message.content or "").strip()


def _ask_gemini(prompt: str, image_paths: list[str]) -> str:
    contents: list[Any] = [prompt]
    contents.extend(_gemini_image(image_path) for image_path in image_paths)
    response = _gemini_client().models.generate_content(
        model=_gemini_model(),
        contents=contents,
    )
    return response.text.strip()


def _ask_provider(prompt: str, image_paths: list[str], details: list[str] | None = None) -> str:
    provider = active_provider()
    if provider == "openai":
        return _ask_openai(prompt, image_paths, details)
    return _ask_gemini(prompt, image_paths)


def ask_gpt_state_consistency(start_img: str, live_img: str, action: str = "", target_region: Any = "") -> str:
    """
    Compares two Android screenshots to determine if their UI state is functionally equivalent.

    Returns a JSON string: {"same_state": "yes"} or {"same_state": "no", ...}
    """
    prompt = (
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

    reply = _ask_provider(prompt, [start_img, live_img])
    print(f"Consistency Response from {active_provider()}:", reply)
    return reply.lower()


def ask_gpt_for_action_region(
    start_img: str,
    stop_img: str,
    live_img: str,
    predicted_action: str,
    relevant_indices: list[int] | None = None,
) -> str:
    """
    Infers which action and UI region should be executed on the current screen
    to reproduce a state transition observed in start/stop images.
    """
    prompt = f"""
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

    reply = _ask_provider(prompt, [start_img, stop_img, live_img], ["low", "low", "high"])
    print(f"Region Action Response from {active_provider()}:", reply)
    return reply


def ask_gpt_for_relevant_regions(start_img_path: str, stop_img_path: str) -> str:
    """
    Asks which UI regions are most relevant for the transition and predicts the action type.
    """
    prompt = """
      You are given two screenshots of an Android interface:

      1. The first image is the REFERENCE state before an interaction.
      2. The second image is the FOLLOW-UP state after the interaction.

      You are also given a list of interactive UI regions detected in the reference image. Each region includes:
      - A numeric index
      - A bounding box
      - A phrase describing the region, e.g. button or text field

      Your task is to determine which of these regions are most likely involved in the transition between the two states.

      - Focus on regions that, if interacted with, could explain the visual change between the first and second image.
      - Minor layout shifts or content changes are not enough. Identify only regions that are plausible interaction targets.
      - Use the phrases and bounding boxes to reason about the intent of the user.
      - When pointers or animations on a button or similar can be seen, prioritize the region around it.

      You must also predict the type of user action that caused the change. Choose only from:
      ["tap", "double_tap", "long_press", "swipe", "input_text", "back", "home", "wait", "no action"]

      Respond strictly in this JSON format. If no regions are relevant, return an empty list:
      { "target_regions": [int, int, ...], "predicted_action": "<action>" }
      """

    reply = _ask_provider(prompt, [start_img_path, stop_img_path])
    print(f"Relevant Region Response from {active_provider()}:", reply)
    return reply
