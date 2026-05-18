import os
import logging
from pathlib import Path
from typing import Any

from providers import openai_provider, gemini_provider
from prompts import state_consistency, action_region, relevant_regions

logger = logging.getLogger(__name__)

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


def active_provider() -> str:
    _load_dotenv()
    requested_provider = os.environ.get("MODEL_PROVIDER", "").strip().lower()
    if requested_provider:
        if requested_provider not in {"openai", "gemini"}:
            raise RuntimeError("MODEL_PROVIDER must be either 'openai' or 'gemini'.")
        if requested_provider == "openai" and not openai_provider.api_key():
            raise RuntimeError("MODEL_PROVIDER=openai requires OPENAI_API_KEY or OPEN_AI_KEY.")
        if requested_provider == "gemini" and not gemini_provider.api_key():
            raise RuntimeError("MODEL_PROVIDER=gemini requires GEMINI_API_KEY.")
        return requested_provider

    if openai_provider.api_key():
        return "openai"
    if gemini_provider.api_key():
        return "gemini"
    raise RuntimeError(
        "No model API key found. Add OPENAI_API_KEY, OPEN_AI_KEY, or GEMINI_API_KEY to .env.local."
    )


def ping_model_connections() -> str:
    _load_dotenv()
    statuses: list[str] = []

    openai_key = openai_provider.api_key()
    gemini_key = gemini_provider.api_key()

    if openai_key:
        try:
            c = openai_provider.client(openai_key)
            response = c.chat.completions.create(
                model=openai_provider.model(),
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
            c = gemini_provider.client(gemini_key)
            response = c.models.generate_content(
                model=gemini_provider.model(),
                contents="Reply with pong.",
            )
            statuses.append(f"Gemini -> pong ({response.text.strip() or 'ok'})")
        except Exception as exc:
            statuses.append(f"Gemini -> failed ({exc})")
    else:
        statuses.append("Gemini -> no key")

    provider = active_provider()
    logger.info("LLM ping-pong connection link:")
    for status in statuses:
        logger.info(f"  {status}")
    logger.info(f"Selected provider: {provider}")
    return provider


def _ask_provider(prompt: str, image_paths: list[str], details: list[str] | None = None) -> str:
    provider = active_provider()
    if provider == "openai":
        return openai_provider.ask(prompt, image_paths, details)
    return gemini_provider.ask(prompt, image_paths)


def ask_gpt_state_consistency(start_img: str, live_img: str, action: str = "", target_region: Any = "") -> str:
    prompt = state_consistency.build(action, target_region)
    reply = _ask_provider(prompt, [start_img, live_img])
    logger.debug(f"Consistency Response from {active_provider()}: {reply}")
    return reply.lower()


def ask_gpt_for_action_region(
    start_img: str,
    stop_img: str,
    live_img: str,
    predicted_action: str,
    relevant_indices: list[int] | None = None,
) -> str:
    prompt = action_region.build(predicted_action, relevant_indices)
    reply = _ask_provider(prompt, [start_img, stop_img, live_img], ["low", "low", "high"])
    logger.debug(f"Region Action Response from {active_provider()}: {reply}")
    return reply


def ask_gpt_for_relevant_regions(start_img_path: str, stop_img_path: str) -> str:
    reply = _ask_provider(relevant_regions.PROMPT, [start_img_path, stop_img_path])
    logger.debug(f"Relevant Region Response from {active_provider()}: {reply}")
    return reply
