import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import run_stats


def test_response_token_count_reads_openai_usage():
    response = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8, total_tokens=20)
    )

    assert run_stats.response_token_count(response) == (12, 8)


def test_response_token_count_reads_gemini_usage_metadata():
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=8,
            total_token_count=20,
        )
    )

    assert run_stats.response_token_count(response) == (12, 8)


def test_response_token_count_sums_when_total_missing():
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=8,
            thoughts_token_count=3,
        )
    )

    assert run_stats.response_token_count(response) == (12, 8)


def test_record_llm_response_is_noop_without_active_stats():
    previous_stats = run_stats._current_stats
    run_stats._current_stats = None
    try:
        run_stats.record_llm_response(1.5, SimpleNamespace(usage={"total_tokens": 9}))
    finally:
        run_stats._current_stats = previous_stats


def test_record_llm_response_updates_active_stats():
    stats = run_stats.init_run_stats(
        app_name="demo",
        video_quality="bad",
        provider="gemini",
        model="gemini-2.5-flash",
        algorithm="clip",
    )

    run_stats.record_llm_response(
        1.5,
        SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=7,
                candidates_token_count=2,
            )
        ),
    )

    assert stats.llm_calls == 1
    assert stats.llm_total_latency_s == 1.5
    assert stats.input_tokens == 7
    assert stats.output_tokens == 2
    assert stats.tokens_used == 9


def test_log_run_summary_writes_quality_prefixed_summary(tmp_path):
    previous_stats = run_stats._current_stats
    stats = run_stats.init_run_stats(
        app_name="demo",
        video_quality="bad",
        provider="gemini",
        model="gemini-2.5-flash",
        algorithm="clip",
    )
    stats.status = "complete"

    try:
        run_stats.log_run_summary(tmp_path)
    finally:
        run_stats._current_stats = previous_stats

    assert (tmp_path / "bad-run-summary.json").exists()
    assert not (tmp_path / "run_bad_summary.json").exists()
    assert not (tmp_path / "bad_run_summary.json").exists()
