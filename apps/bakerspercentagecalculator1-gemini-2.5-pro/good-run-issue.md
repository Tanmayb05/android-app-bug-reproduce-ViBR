# ViBR Run Issue Report: bakerspercentagecalculator1 (GOOD)

**Generated:** 2026-06-20 18:16:42

## Log Summary

| Time | Module | Event |
| --- | --- | --- |
| 2026-06-01 19:00:50 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator1-gemini-2.5-pro/g... |
| 2026-06-01 19:00:50 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:00:57 | __main__ | Relevant regions: {'target_regions': [4], 'predicted_action': 'tap'} |
| 2026-06-01 19:00:57 | __main__ | GPT selected regions: [4] |
| 2026-06-01 19:00:57 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator1-gemini-2.5-pr... |
| 2026-06-01 19:00:57 | __main__ | Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screensh... |
| 2026-06-01 19:00:57 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:01:05 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:01:12 | __main__ | Replay using region index: 4 at (940, 1754) |
| 2026-06-01 19:01:12 | execute_action | [1] Tap the plus button to add a new recipe. -> tap |
| 2026-06-01 19:01:13 | __main__ | Action executed. |
| 2026-06-01 19:01:13 | __main__ | Processing segment 1/1... |
| 2026-06-01 19:01:17 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator1-gemini-2.5-pro/g... |
| 2026-06-01 19:01:17 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:01:22 | __main__ | Relevant regions: {'target_regions': [5], 'predicted_action': 'tap'} |
| 2026-06-01 19:01:22 | __main__ | GPT selected regions: [5] |
| 2026-06-01 19:01:22 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator1-gemini-2.5-pr... |
| 2026-06-01 19:01:22 | __main__ | Comparing state: reference=step_1v_relevant_regions.png vs live=step_1e_screensh... |
| 2026-06-01 19:01:22 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:01:31 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:01:42 | __main__ | Replay using region index: 5 at (539, 1467) |
| 2026-06-01 19:01:42 | execute_action | [1] Tap the Save Recipe button. -> tap |
| 2026-06-01 19:01:42 | __main__ | Action executed. |
| 2026-06-01 19:01:42 | __main__ | Video processing completed. |
| 2026-06-01 19:01:42 | run_stats | ================================================================================ |
| 2026-06-01 19:01:42 | run_stats | RUN SUMMARY |
| 2026-06-01 19:01:42 | run_stats | ================================================================================ |
| 2026-06-01 19:01:42 | run_stats | App: bakerspercentagecalculator1 |
| 2026-06-01 19:01:42 | run_stats | Video: good-video.mp4 |
| 2026-06-01 19:01:42 | run_stats | Provider + Model: gemini / gemini-2.5-pro |
| 2026-06-01 19:01:42 | run_stats | Algorithm: clip |
| 2026-06-01 19:01:42 | run_stats | Status: successful |
| 2026-06-01 19:01:42 | run_stats | Scenes: 2 |
| 2026-06-01 19:01:42 | run_stats | Actions executed: 2 |
| 2026-06-01 19:01:42 | run_stats | LLM calls: 7 |
| 2026-06-01 19:01:42 | run_stats | LLM total latency: 44.07s (0m 44s) |
| 2026-06-01 19:01:42 | run_stats | LLM avg latency: 6.30s (0m 6s) |
| 2026-06-01 19:01:42 | run_stats | Input tokens: 5811 |
| 2026-06-01 19:01:42 | run_stats | Output tokens: 177 |
| 2026-06-01 19:01:42 | run_stats | Tokens used: 5988 |
| 2026-06-01 19:01:42 | run_stats | Cost: $0.0090 (input: $0.0073 @ $1.25/M, output: $0.0018 @ $10.0/M) |
| 2026-06-01 19:01:42 | run_stats | Total duration: 77.31s (1m 17s) |
| 2026-06-01 19:01:42 | run_stats | ================================================================================ |
| 2026-06-01 19:01:42 | run_stats | Summary written to apps/bakerspercentagecalculator1-gemini-2.5-pro/good-run-summ... |

### Interpretation

Execution log shows 44 events total (44 INFO, 0 WARNING, 0 ERROR). Vision model (GroundingDINO) was invoked for object detection. State mismatches detected between expected and actual UI. Segment replay operations were performed.

## Executive Summary

- **Expected steps (from truth):** 9
- **Executed actions:** 2
- **Coverage:** 22.2%
- **Gap:** 7 step(s)

The automation achieved **22.2% coverage**, with 7 step(s) uncompleted.

## Ground Truth vs Execution

| Step | Action | Status |
| --- | --- | --- |
| 1 | Create new recipe | ✓ EXECUTED |
| 2 | Enter recipe name | ✓ EXECUTED |
| 3 | View form with auto-filled ingredient | ✗ NOT EXECUTED |
| 4 | Focus on Notes field to enter additional information | ✗ NOT EXECUTED |
| 5 | Add notes about recipe | ✗ NOT EXECUTED |
| 6 | Focus on Oven Temp field | ✗ NOT EXECUTED |
| 7 | Enter oven temperature/time | ✗ NOT EXECUTED |
| 8 | Save the recipe and return to home | ✗ NOT EXECUTED |
| 9 | Confirm recipe was saved successfully | ✗ NOT EXECUTED |

## Detailed Failure Analysis


No failures detected in log.

## Root Cause Categorization

### Phase 1: Action Segmentation

No failures in this phase.

### Phase 2: GUI State Comparison

No failures in this phase.

### Phase 3: Bug Replay

No failures in this phase.

## Conclusions

This execution demonstrates **22.2% coverage** of expected steps. The automation completed successfully with no detected failures. All 9 expected steps were executed and verified.

## TL;DR

- ✗ 7/9 steps failed (coverage: 22.2%)
- Dominant issue: N/A (No Failures)
- Critical events: 0 errors, 0 warnings
- **Verdict:** FAIL — Significant execution gaps prevent behavior replication
