## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 2026-05-30 20:38:06 | dino_detection | Annotated DINO output saved to apps/batteryte |
| 2026-05-30 20:38:15 | __main__ | Relevant regions: {'target_regions': [8], 'pr |
| 2026-05-30 20:38:15 | __main__ | GPT selected regions: [8] |
| 2026-05-30 20:38:15 | dino_detection | No relevant regions to annotate. |
| 2026-05-30 20:38:15 | __main__ | Comparing state: reference=step_0v_relevant_r |
| 2026-05-30 20:38:34 | execute_action | [1] Return to home. -> home |
| 2026-05-30 20:38:34 | __main__ | Action executed. |
| 2026-05-30 20:38:34 | __main__ | Video processing completed. |
| 2026-05-30 20:38:34 | run_stats | ============================================= |
| 2026-05-30 20:38:34 | run_stats | RUN SUMMARY |
| 2026-05-30 20:38:34 | run_stats | ============================================= |
| 2026-05-30 20:38:34 | run_stats | App: batterytemperaturedisplay |

**Interpretation:** Execution completed successfully with 1 action(s) executed.

## Executive Summary

- Expected steps (from truth video): **5**
- Executed actions (from run log): **1**
- Gap: **4**
- Coverage: **20%**
- Status: **successful**

## Ground Truth vs Execution Log

| Step | Expected | Executed | Status |
|------|----------|----------|--------|
| 1 | wait | ✓ | OK |
| 2 | tap | ✗ | MISSING |
| 3 | tap | ✗ | MISSING |
| 4 | wait | ✗ | MISSING |
| 5 | screen_transition | ✗ | MISSING |

## Root Cause Analysis

**Failures detected:**
- [dino_detection] No relevant regions to annotate.

## Conclusions

✗ Partial execution: 1/5 steps (20%).
Unexecuted steps (4): likely due to action segmentation, GUI state comparison mismatch, or device timing.

## TL;DR

- Status: successful
- Coverage: 20% (1/5)
- Remaining gap: 4 step(s)