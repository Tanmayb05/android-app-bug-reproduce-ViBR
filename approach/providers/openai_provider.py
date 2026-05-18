import os
import base64
import logging
from typing import Any

logger = logging.getLogger(__name__)


def api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_KEY")


def model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o")


def client(api_key_override: str | None = None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI support requires the openai package.") from exc

    resolved_key = api_key_override or api_key()
    if not resolved_key:
        raise RuntimeError("OPENAI_API_KEY or OPEN_AI_KEY is required for OpenAI.")
    return OpenAI(api_key=resolved_key)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ask(prompt: str, image_paths: list[str], details: list[str] | None = None) -> str:
    resolved_details = details or ["high"] * len(image_paths)
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for image_path, detail in zip(image_paths, resolved_details):
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encode_image(image_path)}",
                    "detail": detail,
                },
            }
        )

    response = client().chat.completions.create(
        model=model(),
        messages=[{"role": "user", "content": content}],
    )
    return (response.choices[0].message.content or "").strip()
