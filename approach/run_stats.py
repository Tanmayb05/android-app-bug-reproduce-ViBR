"""Track run statistics and output structured summary at end."""

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Literal
from pathlib import Path
import json


@dataclass
class RunStats:
    """Aggregates run metrics."""

    app_name: str
    video_quality: str
    provider: str
    model: str
    algorithm: str
    status: Literal[
        "complete", "incomplete", "successful", "failed", "partially_passed"
    ] = "incomplete"
    scenes: int = 0
    actions_executed: int = 0
    llm_calls: int = 0
    llm_total_latency_s: float = 0.0
    tokens_used: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    config_used: dict | None = None
    steps_taken: list[str] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def avg_llm_latency_s(self) -> float:
        if self.llm_calls == 0:
            return 0.0
        return self.llm_total_latency_s / self.llm_calls

    def add_step(self, description: str) -> None:
        """Log a step taken during run."""
        self.steps_taken.append(description)

    def record_llm_call(self, latency_s: float, tokens: int) -> None:
        """Record an LLM API call."""
        self.llm_calls += 1
        self.llm_total_latency_s += latency_s
        self.tokens_used += tokens

    def finalize(self) -> None:
        """Mark end time."""
        self.end_time = time.time()

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "app_name": self.app_name,
            "video_quality": self.video_quality,
            "provider": self.provider,
            "model": self.model,
            "algorithm": self.algorithm,
            "status": self.status,
            "scenes": self.scenes,
            "actions_executed": self.actions_executed,
            "llm_calls": self.llm_calls,
            "llm_total_latency_s": round(self.llm_total_latency_s, 2),
            "llm_avg_latency_s": round(self.avg_llm_latency_s, 2),
            "tokens_used": self.tokens_used,
            "duration_s": round(self.duration_s, 2),
            "steps_taken": self.steps_taken,
        }


# Global instance (per run)
_current_stats: RunStats | None = None


def init_run_stats(
    app_name: str,
    video_quality: str,
    provider: str,
    model: str,
    algorithm: str,
    config: dict | None = None,
) -> RunStats:
    """Initialize run stats tracker."""
    global _current_stats
    _current_stats = RunStats(
        app_name=app_name,
        video_quality=video_quality,
        provider=provider,
        model=model,
        algorithm=algorithm,
        config_used=config,
    )
    return _current_stats


def get_run_stats() -> RunStats:
    """Retrieve current run stats."""
    if _current_stats is None:
        raise RuntimeError("Run stats not initialized. Call init_run_stats() first.")
    return _current_stats


def _read_usage_value(usage: Any, key: str) -> int:
    """Read a token count from SDK objects or dict-like metadata."""
    if usage is None:
        return 0
    if isinstance(usage, dict):
        value = usage.get(key, 0)
    else:
        value = getattr(usage, key, 0)
    return value if isinstance(value, int) else 0


def response_token_count(response: Any) -> int:
    """Best-effort token extraction for supported LLM SDK response objects."""
    usage = getattr(response, "usage", None) or getattr(
        response, "usage_metadata", None
    )
    total = _read_usage_value(usage, "total_tokens") or _read_usage_value(
        usage, "total_token_count"
    )
    if total:
        return total

    return sum(
        _read_usage_value(usage, key)
        for key in (
            "prompt_tokens",
            "completion_tokens",
            "prompt_token_count",
            "candidates_token_count",
            "thoughts_token_count",
            "cached_content_token_count",
        )
    )


def record_llm_response(latency_s: float, response: Any) -> None:
    """Record an LLM response if a run stats tracker is active."""
    if _current_stats is None:
        return
    _current_stats.record_llm_call(latency_s, response_token_count(response))


def log_run_summary(app_dir: Path) -> None:
    """Log structured summary at end of run."""
    if _current_stats is None:
        logging.warning("No run stats to summarize")
        return

    logger = logging.getLogger(__name__)
    _current_stats.finalize()

    logger.info("=" * 80)
    logger.info("RUN SUMMARY")
    logger.info("=" * 80)
    logger.info(f"App: {_current_stats.app_name}")
    logger.info(f"Video: {_current_stats.video_quality}_video.mp4")
    logger.info(f"Provider + Model: {_current_stats.provider} / {_current_stats.model}")
    logger.info(f"Algorithm: {_current_stats.algorithm}")
    logger.info(f"Status: {_current_stats.status}")
    logger.info(f"Scenes: {_current_stats.scenes}")
    logger.info(f"Actions executed: {_current_stats.actions_executed}")
    logger.info(f"LLM calls: {_current_stats.llm_calls}")
    logger.info(f"LLM total latency: {_current_stats.llm_total_latency_s:.2f}s")
    logger.info(f"LLM avg latency: {_current_stats.avg_llm_latency_s:.2f}s")
    logger.info(f"Tokens used: {_current_stats.tokens_used}")
    logger.info(f"Total duration: {_current_stats.duration_s:.2f}s")
    logger.info("=" * 80)

    # Also write JSON summary to apps/<app_name>/<quality>_run_summary.json
    summary_path = app_dir / f"{_current_stats.video_quality}_run_summary.json"
    with open(summary_path, "w") as f:
        json.dump(_current_stats.to_dict(), f, indent=2)
    logger.info(f"Summary written to {summary_path}")
