# ViBR Run Issue Report: bakerspercentagecalculator2 (BAD)

**Generated:** 2026-06-20 18:16:42

## Log Summary

| Time | Module | Event |
| --- | --- | --- |
| 2026-06-01 19:20:38 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator2-gemini-2.5-pro/b... |
| 2026-06-01 19:20:38 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:20:46 | __main__ | Relevant regions: {'target_regions': [2], 'predicted_action': 'tap'} |
| 2026-06-01 19:20:46 | __main__ | GPT selected regions: [2] |
| 2026-06-01 19:20:46 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator2-gemini-2.5-pr... |
| 2026-06-01 19:20:46 | __main__ | Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screensh... |
| 2026-06-01 19:20:46 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:20:53 | __main__ | Attempting to align state (try 1/3)... |
| 2026-06-01 19:20:56 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:21:09 | __main__ | Recovery matched element: '' at (540, 147) |
| 2026-06-01 19:21:09 | execute_action | [1] Tap on the three dot menu icon. -> tap |
| 2026-06-01 19:21:12 | __main__ | Comparing state (recovery attempt 1): reference=step_0v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:21:12 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:21:17 | __main__ | Attempting to align state (try 2/3)... |
| 2026-06-01 19:21:20 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:21:31 | __main__ | Recovery matched element: '' at (540, 147) |
| 2026-06-01 19:21:31 | execute_action | [1] Tap on the three-dot menu icon in the top right corner. -> tap |
| 2026-06-01 19:21:34 | __main__ | Comparing state (recovery attempt 2): reference=step_0v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:21:34 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:21:43 | __main__ | Attempting to align state (try 3/3)... |
| 2026-06-01 19:21:46 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:21:59 | __main__ | Recovery using region index: 3 at (964, 1741) |
| 2026-06-01 19:21:59 | execute_action | [1] Press the + button to add your first recipe! -> tap |
| 2026-06-01 19:22:00 | __main__ | Comparing state (recovery attempt 3): reference=step_0v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:22:00 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:22:06 | __main__ | Skipping action: current GUI state does not match start state. Mismatch reason: ... |
| 2026-06-01 19:22:07 | __main__ | Processing segment 1/1... |
| 2026-06-01 19:22:12 | dino_detection | Annotated DINO output saved to apps/bakerspercentagecalculator2-gemini-2.5-pro/b... |
| 2026-06-01 19:22:12 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:22:20 | __main__ | Relevant regions: {'target_regions': [0], 'predicted_action': 'tap'} |
| 2026-06-01 19:22:20 | __main__ | GPT selected regions: [0] |
| 2026-06-01 19:22:20 | dino_detection | Relevant-only annotation saved to apps/bakerspercentagecalculator2-gemini-2.5-pr... |
| 2026-06-01 19:22:20 | __main__ | Comparing state: reference=step_1v_relevant_regions.png vs live=step_1e_screensh... |
| 2026-06-01 19:22:21 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:22:27 | __main__ | Attempting to align state (try 1/3)... |
| 2026-06-01 19:22:30 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:22:55 | __main__ | Recovery using region index: 9 at (539, 1468) |
| 2026-06-01 19:22:55 | execute_action | [1] Tap the Save Recipe button. -> tap |
| 2026-06-01 19:22:57 | __main__ | Comparing state (recovery attempt 1): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:22:57 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:23:03 | __main__ | Attempting to align state (try 2/3)... |
| 2026-06-01 19:23:06 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:23:20 | execute_action | [1] The application is already open, and on a different screen than the one that... |
| 2026-06-01 19:23:23 | __main__ | Comparing state (recovery attempt 2): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:23:23 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:23:31 | __main__ | Attempting to align state (try 3/3)... |
| 2026-06-01 19:23:33 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:23:48 | execute_action | [1] The current screen is already in the target application that was opened by t... |
| 2026-06-01 19:23:51 | __main__ | Comparing state (recovery attempt 3): reference=step_1v_tmp_stop.png vs live=ste... |
| 2026-06-01 19:23:51 | google_genai.models | AFC is enabled with max remote calls: 10. |
| 2026-06-01 19:23:58 | __main__ | Skipping action: current GUI state does not match start state. Mismatch reason: ... |
| 2026-06-01 19:23:58 | __main__ | Video processing completed. |
| 2026-06-01 19:23:58 | run_stats | ================================================================================ |
| 2026-06-01 19:23:58 | run_stats | RUN SUMMARY |
| 2026-06-01 19:23:58 | run_stats | ================================================================================ |
| 2026-06-01 19:23:58 | run_stats | App: bakerspercentagecalculator2 |
| 2026-06-01 19:23:58 | run_stats | Video: bad-video.mp4 |
| 2026-06-01 19:23:58 | run_stats | Provider + Model: gemini / gemini-2.5-pro |
| 2026-06-01 19:23:58 | run_stats | Algorithm: clip |
| 2026-06-01 19:23:58 | run_stats | Status: incomplete |
| 2026-06-01 19:23:58 | run_stats | Scenes: 2 |
| 2026-06-01 19:23:58 | run_stats | Actions executed: 0 |
| 2026-06-01 19:23:58 | run_stats | LLM calls: 17 |
| 2026-06-01 19:23:58 | run_stats | LLM total latency: 168.00s (2m 47s) |
| 2026-06-01 19:23:58 | run_stats | LLM avg latency: 9.88s (0m 9s) |
| 2026-06-01 19:23:58 | run_stats | Input tokens: 15777 |
| 2026-06-01 19:23:58 | run_stats | Output tokens: 928 |
| 2026-06-01 19:23:58 | run_stats | Tokens used: 16705 |
| 2026-06-01 19:23:58 | run_stats | Cost: $0.0290 (input: $0.0197 @ $1.25/M, output: $0.0093 @ $10.0/M) |
| 2026-06-01 19:23:58 | run_stats | Total duration: 234.49s (3m 54s) |
| 2026-06-01 19:23:58 | run_stats | ================================================================================ |
| 2026-06-01 19:23:58 | run_stats | Summary written to apps/bakerspercentagecalculator2-gemini-2.5-pro/bad-run-summa... |

### Interpretation

Execution log shows 72 events total (64 INFO, 8 WARNING, 0 ERROR). Vision model (GroundingDINO) was invoked for object detection. Warnings detected (8 events), suggesting fallback behaviors or partial failures. State mismatches detected between expected and actual UI. Segment replay operations were performed.

## Executive Summary

- **Expected steps (from truth):** 4
- **Executed actions:** 0
- **Coverage:** 0.0%
- **Gap:** 4 step(s)

The automation achieved **0.0% coverage**, with 4 step(s) uncompleted.

## Ground Truth vs Execution

| Step | Action | Status |
| --- | --- | --- |
| 1 | App initialization or recovery | ✗ NOT EXECUTED |
| 2 | Unknown - potential display or app issue | ✗ NOT EXECUTED |
| 3 | Unknown | ✗ NOT EXECUTED |
| 4 | Improve viewing angle or screen visibility | ✗ NOT EXECUTED |

## Detailed Failure Analysis


### Failure 1: State Mismatch

**Error:** Attempting to align state (try 1/3)...

### Failure 2: State Mismatch

**Error:** Attempting to align state (try 2/3)...

### Failure 3: State Mismatch

**Error:** Attempting to align state (try 3/3)...

### Failure 4: State Mismatch

**Error:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image displays the 'downloads' folder within a file manager application. the current image shows a form for creating a new recipe within a different application. the screens are completely different and do not offer the same functionality.

### Failure 5: State Mismatch

**Error:** Attempting to align state (try 1/3)...

### Failure 6: State Mismatch

**Error:** Attempting to align state (try 2/3)...

### Failure 7: State Mismatch

**Error:** Attempting to align state (try 3/3)...

### Failure 8: State Mismatch

**Error:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows the main screen of the app with a title 'baker's percentage calculator' and a floating action button to add a new item. the current image shows a form to create a new recipe, which is a different screen within the app.

## Root Cause Categorization

### Phase 1: Action Segmentation

No failures in this phase.

### Phase 2: GUI State Comparison

- **State Mismatch:** Attempting to align state (try 1/3)...
- **State Mismatch:** Attempting to align state (try 2/3)...
- **State Mismatch:** Attempting to align state (try 3/3)...
- **State Mismatch:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image displays the 'downloads' folder within a file manager application. the current image shows a form for creating a new recipe within a different application. the screens are completely different and do not offer the same functionality.
- **State Mismatch:** Attempting to align state (try 1/3)...
- **State Mismatch:** Attempting to align state (try 2/3)...
- **State Mismatch:** Attempting to align state (try 3/3)...
- **State Mismatch:** Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows the main screen of the app with a title 'baker's percentage calculator' and a floating action button to add a new item. the current image shows a form to create a new recipe, which is a different screen within the app.

### Phase 3: Bug Replay

No failures in this phase.

## Conclusions

This execution demonstrates **0.0% coverage** of expected steps. The dominant failure mode is **Phase 2: GUI State Comparison**, accounting for the majority of errors. GUI state comparison failures (8) suggest mismatches between expected and actual UI state. Overall, the system failed to complete 4 of 4 steps, limiting the ability to fully replicate the bad behavior.

## TL;DR

- ✗ 4/4 steps failed (coverage: 0.0%)
- Dominant issue: Phase 2: GUI State Comparison
- Critical events: 0 errors, 8 warnings
- **Verdict:** FAIL — Significant execution gaps prevent behavior replication
