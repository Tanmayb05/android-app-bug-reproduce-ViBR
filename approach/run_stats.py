"""Track run statistics and output structured summary at end."""

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Literal
import json

from run_paths import RunPaths


def _format_duration(seconds: float) -> str:
    """Format duration in seconds as 'XXs (Xm Ys)' format."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{seconds:.2f}s ({mins}m {secs}s)"


# Gemini API pricing per 1M tokens (standard tier, May 2026)
PRICING = {
    "gemini-2.5-pro": {
        "input": 1.25,  # $1.25 per 1M tokens (prompts <= 200k)
        "output": 10.00,  # $10.00 per 1M tokens (prompts <= 200k)
    },
    "gemini-2.5-flash": {
        "input": 0.30,  # $0.30 per 1M tokens
        "output": 2.50,  # $2.50 per 1M tokens
    },
}


@dataclass
class RunStats:
    """Aggregates run metrics."""

    app_name: str
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
    input_tokens: int = 0
    output_tokens: int = 0
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

    @property
    def tokens_used(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        """Calculate total cost in USD based on model pricing."""
        if self.model not in PRICING:
            return 0.0
        pricing = PRICING[self.model]
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    @property
    def input_cost_usd(self) -> float:
        """Calculate input token cost in USD."""
        if self.model not in PRICING:
            return 0.0
        pricing = PRICING[self.model]
        return (self.input_tokens / 1_000_000) * pricing["input"]

    @property
    def output_cost_usd(self) -> float:
        """Calculate output token cost in USD."""
        if self.model not in PRICING:
            return 0.0
        pricing = PRICING[self.model]
        return (self.output_tokens / 1_000_000) * pricing["output"]

    def add_step(self, description: str) -> None:
        """Log a step taken during run."""
        self.steps_taken.append(description)

    def record_llm_call(
        self, latency_s: float, input_tokens: int, output_tokens: int
    ) -> None:
        """Record an LLM API call with token breakdown."""
        self.llm_calls += 1
        self.llm_total_latency_s += latency_s
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def finalize(self) -> None:
        """Mark end time."""
        self.end_time = time.time()

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "app_name": self.app_name,
            "provider": self.provider,
            "model": self.model,
            "algorithm": self.algorithm,
            "status": self.status,
            "scenes": self.scenes,
            "actions_executed": self.actions_executed,
            "llm_calls": self.llm_calls,
            "llm_total_latency_s": round(self.llm_total_latency_s, 2),
            "llm_avg_latency_s": round(self.avg_llm_latency_s, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tokens_used": self.tokens_used,
            "input_cost_usd": round(self.input_cost_usd, 4),
            "output_cost_usd": round(self.output_cost_usd, 4),
            "cost_usd": round(self.cost_usd, 4),
            "duration_s": round(self.duration_s, 2),
            "steps_taken": self.steps_taken,
        }


# Global instance (per run)
_current_stats: RunStats | None = None


def init_run_stats(
    app_name: str,
    provider: str,
    model: str,
    algorithm: str,
    config: dict | None = None,
) -> RunStats:
    """Initialize run stats tracker."""
    global _current_stats
    _current_stats = RunStats(
        app_name=app_name,
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


def response_token_count(response: Any) -> tuple[int, int]:
    """Extract input and output tokens from LLM response (input, output)."""
    usage = getattr(response, "usage", None) or getattr(
        response, "usage_metadata", None
    )

    # Try input tokens
    input_tokens = (
        _read_usage_value(usage, "prompt_tokens")
        or _read_usage_value(usage, "prompt_token_count")
    )

    # Try output tokens
    output_tokens = (
        _read_usage_value(usage, "completion_tokens")
        or _read_usage_value(usage, "candidates_token_count")
    )

    # Fallback: if only total available, assume 80% input, 20% output (rough estimate)
    total = _read_usage_value(usage, "total_tokens") or _read_usage_value(
        usage, "total_token_count"
    )
    if total and not (input_tokens or output_tokens):
        input_tokens = int(total * 0.8)
        output_tokens = int(total * 0.2)

    return input_tokens, output_tokens


def record_llm_response(latency_s: float, response: Any) -> None:
    """Record an LLM response if a run stats tracker is active."""
    if _current_stats is None:
        return
    input_tokens, output_tokens = response_token_count(response)
    _current_stats.record_llm_call(latency_s, input_tokens, output_tokens)


def log_run_summary(paths: RunPaths) -> None:
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
    logger.info(f"Video: {paths.video}")
    logger.info(f"Provider + Model: {_current_stats.provider} / {_current_stats.model}")
    logger.info(f"Algorithm: {_current_stats.algorithm}")
    logger.info(f"Status: {_current_stats.status}")
    logger.info(f"Scenes: {_current_stats.scenes}")
    logger.info(f"Actions executed: {_current_stats.actions_executed}")
    logger.info(f"LLM calls: {_current_stats.llm_calls}")
    logger.info(f"LLM total latency: {_format_duration(_current_stats.llm_total_latency_s)}")
    logger.info(f"LLM avg latency: {_format_duration(_current_stats.avg_llm_latency_s)}")
    logger.info(f"Input tokens: {_current_stats.input_tokens}")
    logger.info(f"Output tokens: {_current_stats.output_tokens}")
    logger.info(f"Tokens used: {_current_stats.tokens_used}")
    cost_breakdown = ""
    if _current_stats.model in PRICING:
        pricing = PRICING[_current_stats.model]
        cost_breakdown = f" (input: ${_current_stats.input_cost_usd:.4f} @ ${pricing['input']}/M, output: ${_current_stats.output_cost_usd:.4f} @ ${pricing['output']}/M)"
    logger.info(f"Cost: ${_current_stats.cost_usd:.4f}{cost_breakdown}")
    logger.info(f"Total duration: {_format_duration(_current_stats.duration_s)}")
    logger.info("=" * 80)

    with open(paths.summary_json, "w") as f:
        json.dump(_current_stats.to_dict(), f, indent=2)
    logger.info(f"Summary written to {paths.summary_json}")
