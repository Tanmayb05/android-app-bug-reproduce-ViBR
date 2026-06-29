# ViBR Run Issue Report: bakerspercentagecalculator1 (BAD)

**Generated:** 2026-06-20 18:16:42

## Log Summary

| Time | Module | Event |
| --- | --- | --- |
| 2026-05-30 19:52:12 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator1-gemini-2.5-pro/b... |
| 2026-05-30 19:52:12 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:52:18 | __main__ | Relevant regions: {'target_regions': [4], 'predicted_action': 'tap'} |
| 2026-05-30 19:52:18 | __main__ | GPT selected regions: [4] |
| 2026-05-30 19:52:18 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator1-gemini-2.5-pr... |
| 2026-05-30 19:52:18 | __main__ | Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screensh... |
| 2026-05-30 19:52:18 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:52:26 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:52:44 | __main__ | Replay using region index: 4 at (560, 1588) |
| 2026-05-30 19:52:44 | execute_action | [1] Tap the '+' button to add your first recipe. -> tap |
| 2026-05-30 19:52:45 | __main__ | Action executed. |
| 2026-05-30 19:52:45 | __main__ | Processing segment 1... |
| 2026-05-30 19:52:49 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator1-gemini-2.5-pro/b... |
| 2026-05-30 19:52:49 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:06 | __main__ | Relevant regions: {'target_regions': [1], 'predicted_action': 'tap'} |
| 2026-05-30 19:53:06 | __main__ | GPT selected regions: [1] |
| 2026-05-30 19:53:06 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator1-gemini-2.5-pr... |
| 2026-05-30 19:53:06 | __main__ | Comparing state: reference=step_1v_relevant_regions.png vs live=step_1e_screensh... |
| 2026-05-30 19:53:06 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:14 | __main__ | Attempting to align state (try 1/3)... |
| 2026-05-30 19:53:16 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:33 | __main__ | Recovery using region index: 3 at (964, 1741) |
| 2026-05-30 19:53:33 | execute_action | [1] Tap the plus button to add a new recipe. -> tap |
| 2026-05-30 19:53:35 | __main__ | Comparing state (recovery attempt 1): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-05-30 19:53:35 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:41 | __main__ | Attempting to align state (try 2/3)... |
| 2026-05-30 19:53:43 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:49 | __main__ | Recovery using region index: 9 at (539, 1468) |
| 2026-05-30 19:53:49 | execute_action | [1] Tap the Save Recipe button. -> tap |
| 2026-05-30 19:53:51 | __main__ | Comparing state (recovery attempt 2): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-05-30 19:53:51 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:53:58 | __main__ | Attempting to align state (try 3/3)... |
| 2026-05-30 19:54:00 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:54:06 | __main__ | Recovery using region index: 9 at (539, 1468) |
| 2026-05-30 19:54:06 | execute_action | [1] Tap the Save Recipe button. -> tap |
| 2026-05-30 19:54:07 | __main__ | Comparing state (recovery attempt 3): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-05-30 19:54:07 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-05-30 19:54:16 | __main__ | Skipping action: current GUI state does not match start state. Mismatch reason: ... |
| 2026-05-30 19:54:16 | __main__ | Video processing completed. |
| 2026-05-30 19:54:16 | run_stats | ================================================================================ |
| 2026-05-30 19:54:16 | run_stats | RUN SUMMARY |
| 2026-05-30 19:54:16 | run_stats | ================================================================================ |
| 2026-05-30 19:54:16 | run_stats | App: bakerspercentagecalculator1 |
| 2026-05-30 19:54:16 | run_stats | Video: bad-video.mp4 |
| 2026-05-30 19:54:16 | run_stats | Provider + Model: gemini / gemini-2.5-pro |
| 2026-05-30 19:54:16 | run_stats | Algorithm: clip |
| 2026-05-30 19:54:16 | run_stats | Status: successful |
| 2026-05-30 19:54:16 | run_stats | Scenes: 2 |
| 2026-05-30 19:54:16 | run_stats | Actions executed: 1 |
| 2026-05-30 19:54:16 | run_stats | LLM calls: 12 |
| 2026-05-30 19:54:16 | run_stats | LLM total latency: 107.22s (1m 47s) |
| 2026-05-30 19:54:16 | run_stats | LLM avg latency: 8.94s (0m 8s) |
| 2026-05-30 19:54:16 | run_stats | Input tokens: 10794 |
| 2026-05-30 19:54:16 | run_stats | Output tokens: 559 |
| 2026-05-30 19:54:16 | run_stats | Tokens used: 11353 |
| 2026-05-30 19:54:16 | run_stats | Cost: $0.0191 (input: $0.0135 @ $1.25/M, output: $0.0056 @ $10.0/M) |
| 2026-05-30 19:54:16 | run_stats | Total duration: 259.37s (4m 19s) |
| 2026-05-30 19:54:16 | run_stats | ================================================================================ |
| 2026-05-30 19:54:16 | run_stats | Summary written to apps/bakerspercentagecalculator1-gemini-2.5-pro/bad-run-summa... |

### Interpretation

Execution log shows 59 events total (55 INFO, 4 WARNING, 0 ERROR). Vision model (GroundingDINO) was invoked for object detection. Warnings detected (4 events), suggesting fallback behaviors or partial failures. State mismatches detected between expected and actual UI. Segment replay operations were performed.

## Executive Summary

- **Expected steps (from truth):** 6
- **Executed actions:** 1
- **Coverage:** 16.7%
- **Gap:** 5 step(s)

The automation achieved **16.7% coverage**, with 5 step(s) uncompleted.

## Ground Truth vs Execution

| Step | Action | Status |
| --- | --- | --- |
| 1 | App launch/initialization | ✓ EXECUTED |
| 2 | Display home state | ✗ NOT EXECUTED |
| 3 | Prepare for or trigger text input | ✗ NOT EXECUTED |
| 4 | Unknown - possible display issue | ✗ NOT EXECUTED |
| 5 | Unknown - potential display or app state issue | ✗ NOT EXECUTED |
| 6 | Stabilize device viewing angle | ✗ NOT EXECUTED |

## Detailed Failure Analysis


### Failure 1: State Mismatch

**Error:** Attempting to align state (try 1/3)...

### Failure 2: State Mismatch

**Error:** Attempting to align state (try 2/3)...

### Failure 3: State Mismatch

**Error:** Attempting to align state (try 3/3)...

### Failure 4: State Mismatch

**Error:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows a main screen with a list and a floating action button, likely for adding a new item. the current image shows a detailed form for creating a new recipe. these are different screens representing different steps in a user workflow.

## Root Cause Categorization

### Phase 1: Action Segmentation

No failures in this phase.

### Phase 2: GUI State Comparison

- **State Mismatch:** Attempting to align state (try 1/3)...
- **State Mismatch:** Attempting to align state (try 2/3)...
- **State Mismatch:** Attempting to align state (try 3/3)...
- **State Mismatch:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows a main screen with a list and a floating action button, likely for adding a new item. the current image shows a detailed form for creating a new recipe. these are different screens representing different steps in a user workflow.

### Phase 3: Bug Replay

No failures in this phase.

## Conclusions

This execution demonstrates **16.7% coverage** of expected steps. The dominant failure mode is **Phase 2: GUI State Comparison**, accounting for the majority of errors. GUI state comparison failures (4) suggest mismatches between expected and actual UI state. Overall, the system failed to complete 5 of 6 steps, limiting the ability to fully replicate the bad behavior.

## TL;DR

- ✗ 5/6 steps failed (coverage: 16.7%)
- Dominant issue: Phase 2: GUI State Comparison
- Critical events: 0 errors, 4 warnings
- **Verdict:** FAIL — Significant execution gaps prevent behavior replication
