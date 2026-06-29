## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 2026-05-30 20:34:11 | dino_detection | Annotated DINO output saved to apps/batteryte |
| 2026-05-30 20:34:33 | __main__ | Relevant regions: {'target_regions': [3], 'pr |
| 2026-05-30 20:34:33 | __main__ | GPT selected regions: [3] |
| 2026-05-30 20:34:34 | dino_detection | Relevant-only annotation saved to apps/batter |
| 2026-05-30 20:34:34 | __main__ | Comparing state: reference=step_0v_relevant_r |
| 2026-05-30 20:34:42 | __main__ | Attempting to align state (try 1/3)... |
| 2026-05-30 20:34:56 | execute_action | [1] Swipe down from top of screen. -> swipe |
| 2026-05-30 20:34:58 | __main__ | Comparing state (recovery attempt 1): referen |
| 2026-05-30 20:35:20 | execute_action | [1] Swipe up to unlock the phone. -> swipe |
| 2026-05-30 20:35:21 | __main__ | Action executed. |
| 2026-05-30 20:35:21 | __main__ | Processing segment 1... |
| 2026-05-30 20:35:26 | dino_detection | Annotated DINO output saved to apps/batteryte |

**Interpretation:** Execution completed successfully with 2 action(s) executed.

## Executive Summary

- Expected steps (from truth video): **7**
- Executed actions (from run log): **2**
- Gap: **5**
- Coverage: **28%**
- Status: **successful**

## Ground Truth vs Execution Log

| Step | Expected | Executed | Status |
|------|----------|----------|--------|
| 1 | wait | ✓ | OK |
| 2 | tap | ✓ | OK |
| 3 | tap | ✗ | MISSING |
| 4 | tap | ✗ | MISSING |
| 5 | tap | ✗ | MISSING |
| 6 | screen_transition | ✗ | MISSING |
| 7 | tap | ✗ | MISSING |

## Root Cause Analysis

**Failures detected:**
- [__main__] Attempting to align state (try 1/3)...

## Conclusions

✗ Partial execution: 2/7 steps (28%).
Unexecuted steps (5): likely due to action segmentation, GUI state comparison mismatch, or device timing.

## TL;DR

- Status: successful
- Coverage: 28% (2/7)
- Remaining gap: 5 step(s)