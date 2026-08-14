# BinaryEye Bad Run Analysis: Complete Failure Due to State Mismatch

## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 15:31:29 | dino_detection | Loading GroundingDINO model with config and weights on MPS device |
| 15:31:32 | dino_detection | Annotated DINO output saved (detected UI elements) |
| 15:31:42 | __main__ | Identified relevant regions; predicted action: tap (region 2) |
| 15:31:51 | __main__ | **Attempting to align state (try 1/3)** — State mismatch detected |
| 15:32:18 | __main__ | Recovery attempt 1: Tap three-dot menu icon |
| 15:32:27 | __main__ | **Attempting to align state (try 2/3)** — Still mismatched |
| 15:32:50 | __main__ | Recovery attempt 2: Tap three dots icon to open menu |
| 15:32:57 | __main__ | **Attempting to align state (try 3/3)** — Final attempt |
| 15:33:14 | __main__ | Recovery attempt 3: Tap settings icon at (716, 252) |
| 15:33:21 | __main__ | **SKIPPED ACTION** — Reference (settings screen) vs Live (file browser "recent") — Complete state mismatch |
| 15:33:21 | run_stats | Video processing completed. Status: **incomplete**. Actions executed: 0/1 |

**Interpretation:** ViBR attempted to execute the first expected action (tap menu icon) after analyzing the initial screen. However, a fundamental state mismatch prevented execution: ViBR believed it should be on the app's settings screen (barcode formats, scan options), but the device was showing a system file browser (recent files). All three recovery attempts failed to resolve this state divergence, leading to complete action skip and job termination.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Expected steps (from truth video) | 8 |
| Executed steps (from run log) | 0 |
| Missing steps | 8 |
| Coverage | 0% |
| Status | **FAILED — Incomplete** |

**Root failure:** Catastrophic state mismatch at segment 0. ViBR predicted initial action on settings screen, but device was in file browser. Recovery logic (3 retries) all failed. No actions executed; automation halted.

---

## Ground Truth vs Execution Log

| Step# | Expected Action | Executed ✓/✗ | Status | Issue Category |
|-------|-----------------|--------------|--------|-----------------|
| 1 | Wait at scan screen (loading indicator visible) | ✗ | Skipped | Segmentation issue |
| 2 | Hand appears on screen (user preparing to interact) | ✗ | Skipped | Recording artifact |
| 3 | Tap menu icon → menu dropdown opens | ✗ | **Failed state check** | 2.7. State Consistency Check (GPT-4o) |
| 4 | Navigate to Settings screen | ✗ | Skipped | 3.11. Action Inference (GPT-4o) |
| 5 | Scroll through settings (cropping, crosshairs, zoom) | ✗ | Skipped | 3.12. Action Execution |
| 6 | Scroll settings (barcode, optimize reader, scan continuously) | ✗ | Skipped | 3.12. Action Execution |
| 7 | Scroll settings (notifications: vibrate, beep, audio) | ✗ | Skipped | 3.12. Action Execution |
| 8 | Scroll to bottom of settings (metadata, hex dump, language) | ✗ | Skipped | 3.12. Action Execution |

---

## Video vs Log Comparison

ViBR was provided with 15 extracted frames (1fps) from `bad-video.mp4`. The video clearly showed:

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 0001 | Scan screen | Initial screen detection | Scan screen with loading indicator, "Scan code" title visible | ✓ Aligned |
| 0002 | Hand interaction | Wait detected | User hand visible on right, appears to reach toward menu | ✓ Aligned |
| 0003 | Menu open | Expected transition | Menu dropdown open with 7 options visible (Switch camera, Scan continuously, Settings, etc.) | ✓ Aligned |
| 0004-0015 | Settings screen | **Expected final state** | Settings screen with toggles, barcode formats, profile, scan options — user scrolling through entire settings page | **✗ HUGE GAP** |

**Critical finding:** ViBR's internal reference state was set to "app settings screen" but at the critical moment (action execution), the device was displaying a completely different app — a system file browser titled "recent". This suggests either:
1. The app state diverged during processing (navigation to file browser occurred unexpectedly)
2. Initial screenshot/segmentation failed to capture the correct app state
3. Device recovery/state sync didn't work correctly

---

## Detailed Failure Analysis

### Failure #1: Initial State Mismatch (Critical)

**Expected behavior:** ViBR should have identified the opening state as "BinaryEye scan screen" and prepared to execute: tap menu icon → open settings → scroll through settings.

**What happened:** ViBR correctly identified the initial screen and DINO detected UI elements. However, when attempting to validate state before executing the first action, ViBR's internal model of the reference screen (settings page) did **not match** the live device screen (file browser).

**Log evidence:**
```
[15:33:21] Skipping action: current GUI state does not match start state. 
Mismatch reason: the reference screen is the app's settings page, 
allowing the user to configure options like 'barcode formats' and 'scan continuously'. 
The current screen is a system file browser titled 'recent', 
which is a completely different interface and functionality.
```

**Root cause:** State consistency check (GPT-4o) performed a pixel-level and semantic comparison between:
- **Reference:** `step_0v_relevant_regions.png` (predicted target: settings screen)
- **Live:** `step_0e_screenshot_0.png` (actual device: file browser)

The model correctly identified the mismatch but failed to recover because the states are fundamentally incompatible — not just a UI shift or animation, but a complete app switch.

**Cascade impact:** With zero recovery strategies remaining after 3 retries, ViBR aborted the entire automation sequence. No actions executed.

---

### Failure #2: State Alignment Retries (All 3 Failed)

**Retry 1 (15:31:51–15:32:18):**
- Action attempted: Tap three-dot menu icon at (911, 136)
- Result: State still mismatched
- Reason: Menu tap did not bring device into expected state

**Retry 2 (15:32:27–15:32:50):**
- Action attempted: Tap three-dot menu icon (retry) at (1016, 136)
- Result: State still mismatched
- Reason: Coordinate shift but state divergence persists

**Retry 3 (15:32:57–15:33:14):**
- Action attempted: Tap settings icon at (716, 252) using region-based recovery
- Result: State still mismatched → **ABORT**
- Reason: Device never recovered to expected settings screen state

**Evidence:** All 3 recovery attempts produced screenshots that remained fundamentally incompatible with the reference. The issue is not a timing problem or a simple coordinate error — the device is in a different app entirely.

---

## Root Cause Categorization

### Phase 2: GUI State Comparison — 2.7. State Consistency Check (GPT-4o)

**Issue:** False mismatch detection — GPT-4o correctly identified that reference and live states are different, but the automation system had no recovery path for "different app entirely."

**Evidence:**
- Reference screen: Settings screen (barcode formats, toggles, profile section visible)
- Live screen: File browser app titled "recent" (system UI, completely different)
- Verdict: This is a semantic/functional mismatch, not a visual alignment issue

**Why it failed:** 
1. No fallback strategy for "app switch" scenarios
2. State consistency check is based on visual/UI feature matching, not app identity verification
3. Recovery heuristics (retry menu tap, try settings icon) assume same app context — they don't account for the user navigating away from the target app

### Phase 3: Bug Replay on Device — 3.10. GUI Perception & 3.11. Action Inference

**Secondary issue:** ViBR's understanding of which screen the user should be on (settings page) did not match reality (file browser). This could indicate:
- **GUI Perception error:** Initial screenshot parsing failed to correctly identify the live app's state before actions began
- **Action Inference error:** ViBR inferred the action should be executed on settings screen, but that was never the actual state

---

## Impact Assessment

**Immediate impact:**
- 0 of 8 expected actions executed (0% coverage)
- Automation terminated without recovery
- Total time spent: ~160 seconds (LLM analysis + recovery attempts)
- LLM cost: 9 calls, 8336 tokens

**Cascading failures:**
- Since first action failed, all dependent actions were skipped
- Settings exploration (steps 5-8) never occurred
- User goal (navigate settings menu) never completed

**Why recovery failed:**
- The device's actual state (file browser) was semantically incompatible with the reference state (app settings screen)
- Recovery logic assumes the same app context and attempts to re-navigate; it does not detect or handle app switches
- After 3 retries, the system gave up rather than implement a recovery-from-app-switch strategy

---

## Conclusions

BinaryEye bad run failed completely due to a fundamental state mismatch: ViBR expected the device to be on the app's settings screen but found a system file browser instead. This is not a visual rendering issue, coordinate drift, or transient UI state — it is a semantic/functional divergence at the app level.

**Coverage:** 0% (0/8 steps executed)

**Dominant failure mode:** GUI state inconsistency (Phase 2.7 — GPT-4o state consistency check returned correct verdict of mismatch, but system had no recovery path)

**Underlying limitation:** ViBR's recovery system is designed for within-app state misalignment (e.g., button moved, text changed). It cannot handle scenarios where the user has navigated to a completely different application. This represents a gap in the action inference and device perception layers — the initial state may not have been correctly identified, or the app state diverged unexpectedly during early processing.

**Recommendation:** Investigate why the device showed a file browser when the expected state was BinaryEye settings. This could indicate:
1. App crash and fallback to file browser
2. Incorrect initial screenshot parsing
3. Unintended user action or system interaction captured in the video

---

## TL;DR

- ✗ **Failure:** All 8 steps skipped; 0 actions executed; automation terminated
- ✗ **Root cause:** State mismatch — reference screen (settings) vs live screen (file browser)
- ✗ **Recovery:** All 3 retry attempts failed; no path to recover from app-level divergence
- ✗ **Coverage:** 0% — BinaryEye bad run is a **complete failure**
- **Issue category:** Phase 2.7 (State Consistency Check) — system correctly detected mismatch but lacked recovery strategy for app switches
- **Bottom line:** ViBR's automation cannot proceed when the device is in a completely different app than expected; this represents a critical limitation in device state alignment and action recovery logic.
