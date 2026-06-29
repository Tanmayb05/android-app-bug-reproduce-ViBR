## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 2026-06-01 15:20:37 | dino_detection | Annotated DINO output saved to apps/bily-gemi |
| 2026-06-01 15:20:44 | __main__ | Relevant regions: {'target_regions': [1], 'pr |
| 2026-06-01 15:20:44 | __main__ | GPT selected regions: [1] |
| 2026-06-01 15:20:44 | dino_detection | Relevant-only annotation saved to apps/bily-g |
| 2026-06-01 15:20:44 | __main__ | Comparing state: reference=step_0v_relevant_r |
| 2026-06-01 15:20:55 | __main__ | Attempting to align state (try 1/3)... |
| 2026-06-01 15:21:15 | __main__ | Recovery matched element: 'Global Bill' at (5 |
| 2026-06-01 15:21:15 | execute_action | [1] Tap the three dots icon to open the menu. |
| 2026-06-01 15:21:17 | __main__ | Comparing state (recovery attempt 1): referen |
| 2026-06-01 15:21:24 | __main__ | Attempting to align state (try 2/3)... |
| 2026-06-01 15:21:43 | __main__ | Recovery matched element: 'Global Bill' at (5 |
| 2026-06-01 15:21:43 | execute_action | [1] Tap the three dots menu icon. -> tap |

**Interpretation:** Execution completed with status: incomplete. Gap of 5 step(s) from expected 5.

## Executive Summary

- Expected steps (from truth video): **5**
- Executed actions (from run log): **0**
- Gap: **5**
- Coverage: **0%**
- Status: **incomplete**

## Ground Truth vs Execution Log

| Step | Expected | Executed | Status |
|------|----------|----------|--------|
| 1 | wait | ✗ | MISSING |
| 2 | tap | ✗ | MISSING |
| 3 | tap | ✗ | MISSING |
| 4 | wait | ✗ | MISSING |
| 5 | screen_transition | ✗ | MISSING |

## Root Cause Analysis

**Failures detected:**
- [__main__] Attempting to align state (try 1/3)...
- [__main__] Attempting to align state (try 2/3)...
- [__main__] Attempting to align state (try 3/3)...
- [__main__] Skipping action: current GUI state does not match start stat
- [__main__] Attempting to align state (try 1/3)...

## Conclusions

✗ Partial execution: 0/5 steps (0%).
Unexecuted steps (5): likely due to action segmentation, GUI state comparison mismatch, or device timing.

## TL;DR

- Status: incomplete
- Coverage: 0% (0/5)
- Remaining gap: 5 step(s)