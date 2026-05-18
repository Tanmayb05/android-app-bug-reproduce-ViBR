import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


def api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY")


def model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def client(api_key_override: str | None = None) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini support requires the google-genai package.") from exc

    resolved_key = api_key_override or api_key()
    if not resolved_key:
        raise RuntimeError("GEMINI_API_KEY is required for Gemini.")
    return genai.Client(api_key=resolved_key)


def load_image(path: str) -> Any:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Gemini image support requires Pillow.") from exc

    return Image.open(path)


def ask(prompt: str, image_paths: list[str]) -> str:
    contents: list[Any] = [prompt]
    contents.extend(load_image(p) for p in image_paths)
    response = client().models.generate_content(
        model=model(),
        contents=contents,
    )
    return response.text.strip()
