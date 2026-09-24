import os
import logging
import time
from typing import Any

from approach.core.run_stats import record_llm_response

logger = logging.getLogger(__name__)

_client_instance: Any = None
_client_key: tuple[str, str] | None = None

DEFAULT_LOCATION = "us-central1"


def project() -> str | None:
    return (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
        or os.environ.get("GCLOUD_PROJECT")
    )


def location() -> str:
    return os.environ.get("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION)


def is_configured() -> bool:
    """Gemini is available when a Vertex AI project is set. Auth is ADC."""
    return project() is not None


def model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def client() -> Any:
    global _client_instance, _client_key

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini support requires the google-genai package.") from exc

    resolved_project = project()
    if not resolved_project:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is required for Gemini (Vertex AI via ADC). "
            "Run `gcloud auth application-default login` and set GOOGLE_CLOUD_PROJECT."
        )
    resolved_location = location()
    resolved_key = (resolved_project, resolved_location)

    if _client_instance is None or _client_key != resolved_key:
        _client_instance = genai.Client(
            vertexai=True,
            project=resolved_project,
            location=resolved_location,
        )
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
