import os
import logging
import time
from typing import Any

from run_stats import record_llm_response

logger = logging.getLogger(__name__)

_client_instance: Any = None
_client_key: str | None = None


def api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY")


def model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def client(api_key_override: str | None = None) -> Any:
    global _client_instance, _client_key

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini support requires the google-genai package.") from exc

    resolved_key = api_key_override or api_key()
    if not resolved_key:
        raise RuntimeError("GEMINI_API_KEY is required for Gemini.")

    if _client_instance is None or _client_key != resolved_key:
        _client_instance = genai.Client(api_key=resolved_key)
        _client_key = resolved_key

    return _client_instance


def load_image(path: str) -> Any:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Gemini image support requires Pillow.") from exc

    return Image.open(path)


def ask(prompt: str, image_paths: list[str]) -> str:
    contents: list[Any] = [prompt]
    contents.extend(load_image(p) for p in image_paths)
    start = time.perf_counter()
    response = client().models.generate_content(
        model=model(),
        contents=contents,
    )
    record_llm_response(time.perf_counter() - start, response)
    return response.text.strip()
