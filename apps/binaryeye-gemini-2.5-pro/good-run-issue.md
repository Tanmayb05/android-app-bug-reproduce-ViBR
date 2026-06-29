## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 2026-06-01 15:40:55 | dino_detection | Annotated DINO output saved to apps/binaryeye |
| 2026-06-01 15:41:06 | __main__ | Relevant regions: {'target_regions': [], 'pre |
| 2026-06-01 15:41:06 | __main__ | GPT selected regions: [] |
| 2026-06-01 15:41:06 | dino_detection | No relevant regions to annotate. |
| 2026-06-01 15:41:06 | __main__ | Comparing state: reference=step_0v_relevant_r |
| 2026-06-01 15:41:24 | execute_action | [1] No action needed. -> no action |
| 2026-06-01 15:41:25 | __main__ | Action executed. |
| 2026-06-01 15:41:25 | __main__ | Processing segment 1... |
| 2026-06-01 15:41:35 | dino_detection | Annotated DINO output saved to apps/binaryeye |
| 2026-06-01 15:41:55 | __main__ | Relevant regions: {'target_regions': [5], 'pr |
| 2026-06-01 15:41:55 | __main__ | GPT selected regions: [5] |
| 2026-06-01 15:41:55 | dino_detection | Relevant-only annotation saved to apps/binary |

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
| 3 | screen_transition | ✗ | MISSING |
| 4 | wait | ✗ | MISSING |
| 5 | screen_transition | ✗ | MISSING |

## Root Cause Analysis

**Failures detected:**
- [dino_detection] No relevant regions to annotate.
- [__main__] Attempting to align state (try 1/3)...
- [__main__] Attempting to align state (try 2/3)...
- [__main__] Attempting to align state (try 3/3)...
- [__main__] Skipping action: current GUI state does not match start stat

## Conclusions

✗ Partial execution: 1/5 steps (20%).
Unexecuted steps (4): likely due to action segmentation, GUI state comparison mismatch, or device timing.

## TL;DR

- Status: successful
- Coverage: 20% (1/5)
- Remaining gap: 4 step(s)