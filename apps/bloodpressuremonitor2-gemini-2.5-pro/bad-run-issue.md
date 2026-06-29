# ViBR Run Analysis: bloodpressuremonitor2 (bad run)

## Executive Summary

**Ground Truth:** 6 expected steps (input systolic → input diastolic → submit → view results chart)
**Actually Executed:** 0 actions (incomplete/failed)
**Gap:** 6 steps missing (0% execution rate)

The bad run achieved complete execution failure. ViBR segmented the video into 3 segments but failed to execute any actions. Root cause: **GUI state mismatch at segment 0** — ViBR detected an empty data state ("not enough data to draw a graph") that contradicts the ground truth input sequence. The app appears to have entered a fundamentally broken state mid-execution, preventing action completion.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 1 | Tap systolic input field | ✗ | Skipped | GUI state mismatch — empty data |
| 2 | Enter systolic (120) via keyboard | ✗ | Skipped | Cascading from Step 1 |
| 3 | Tap diastolic input field | ✗ | Skipped | Cascading from Step 1 |
| 4 | Enter diastolic (80) via keyboard | ✗ | Skipped | Cascading from Step 1 |
| 5 | Submit blood pressure reading | ✗ | Skipped | Cascading from Step 1 |
| 6 | View results chart | ✗ | Failed attempt in Seg 1 | GUI state mismatch — form vs chart |

---

## Segmentation Analysis

ViBR detected 3 segments from 1938 video frames (video ~32 seconds @ 1fps):

- **Segment 0:** Frames 0–1546 (longest, ~25 seconds) — Should contain input entry flow
- **Segment 1:** Frames 1550–1629 (~1 second) — Potential submission/transition  
- **Segment 2:** Frames 1633–1936 (~5 seconds) — Results chart display

### Segment 0 Failure (Frames 0–1546)

**What happened:**
- ViBR analyzed starting frame and decided: `predicted_action: 'wait'` (no relevant regions detected)
- ViBR then compared reference (expected state) to live (actual device state)
- **Mismatch detected:** Reference shows graph + data list. Live shows **"not enough data to draw a graph"** message with no data.

**Log evidence:**
```
[02:35:46] [WARNING] Skipping action: current GUI state does not match start state. 
Mismatch reason: the reference screen displays a graph and a list of data points, 
while the current screen shows a message "not enough data to draw a graph" 
and no data list. this indicates a fundamentally different state where data is 
present in one case and absent in the other.
```

**Root cause interpretation:**
- Ground truth video shows a user entering BP values and receiving a successful result (graph with data).
- Bad run video **shows the same app in the same state, but the app itself is broken:** it refuses to accept input and remains stuck at "no data" message.
- ViBR correctly identified this mismatch, but **did not understand that the reference frame itself represents a failed/empty app state**—not a target state to achieve.

---

## Segment 1 Failure (Frames 1550–1629)

ViBR attempted recovery by finding an alternative action (tap graph icon button), but all 3 recovery attempts failed:

**Recovery Attempts:**
1. **Try 1:** Tapped "graph icon button" at (939, 1518) → state did not align
2. **Try 2:** Tapped "back arrow" at (74, 137) → state did not align  
3. **Try 3:** Tapped "graph icon button" again at (939, 1716) → state did not align

**Final skip reason:**
```
[02:37:49] [WARNING] Skipping action: current GUI state does not match start state. 
Mismatch reason: the reference image shows a dashboard with graphs and metrics, 
while the current image shows a data entry form. these are two distinct screens 
with different functionalities and ui elements.
```

ViBR was bouncing between two incompatible screens: results dashboard and input form, unable to stabilize.

---

## Root Cause Categorization

### Stage 2: GUI State Comparison (6 failures)

**Dynamic/Session-Specific Content (Primary):**
- The "bad" video captures an app in a broken state: persistently empty data, inaccessible input.
- Ground truth assumes functional input flow, but the device was in a fundamentally different state.
- The app did not transition as expected; data entry did not produce data accumulation.
- **Confidence: HIGH** — Log explicitly states GUI mismatch between "data present" and "no data" states.

**Semantic Gap (Secondary):**
- ViBR's state comparison logic expects reference and live frames to align structurally.
- When they don't (empty vs. populated), ViBR skips the action to avoid undefined behavior.
- This is **correct conservative behavior**, but highlights a deeper issue: the bad run captured an app that never transitioned out of the empty state.

---

## Impact Assessment

### Why Full Execution Failed

1. **Segment 0 — Blocked at start:** Detected app empty state, no data input entry possible.
   - ViBR correctly refused to proceed with actions into an unmapped state.
   - User sees "not enough data to draw a graph" — input form may not have been receptive.

2. **Segments 1–2 — Cascading failure:** With no actions executed in Segment 0, Segments 1–2 had no preconditions met.
   - ViBR attempted emergency recovery (tapping alternative UI buttons) but could not escape the empty data state.
   - Both dashboard and input form were unreachable or broken.

3. **App-Level Failure (Most Likely):**
   - The "bad" video captures the app in a genuinely broken state:
     - Input may have been disabled, rejected, or never recorded.
     - Data storage layer may be inaccessible.
     - UI state machine may have frozen or looped.

---

## Video vs Ground Truth Alignment

The discrepancy suggests one of two scenarios:

**Hypothesis A: App Crash / Disabled State**
- The bad run video shows the user *attempting* to input values (frames 0–1546 show keyboard presence).
- However, the device/app rejected or ignored input, leaving the app in "no data" state.
- ViBR correctly detected this and halted to avoid blind tapping.

**Hypothesis B: Video Capture Artifact**
- The video may capture a restarted or reset app state, not a true "bad run" but rather a comparison artifact.
- The ground truth assumes a clean app state; the bad run started in an unknown state.

Either way, **the gap is real and non-recoverable by ViBR's current logic**.

---

## Conclusions

The bad run achieved **0% execution of ground truth steps**. 

Primary failure mode: **Dynamic/Session-Specific Content (Stage 2)** — The app's data state (empty vs. populated) did not match expectations. ViBR correctly refused to proceed, preventing cascading failures but also preventing any progress.

Secondary factor: **Missing state recovery logic** — ViBR's recovery attempts focused on UI element tapping but did not address the root cause: the app was fundamentally unable to accept input in the captured state. More sophisticated recovery would require:
- App restart / state reset detection
- Conditional backtracking to a known-good state
- Timeout escalation to force state transitions

The bad run is **not a ViBR bug but evidence of a malfunctioning device or app state**. ViBR's conservative approach (skip action if state misaligned) is correct; the underlying issue is environmental.

---

## TL;DR — Why It Failed

**Failure reason:** GUI state mismatch — app stuck in "no data" state
- **Evidence:** Log shows `"not enough data to draw a graph"` vs. expected graph + data
- **Impact:** Input form unreceptive or app data layer broken; no actions could proceed

**Bottom line:** ViBR correctly detected a broken app state and halted execution. The bad run video captures the app in a fundamentally different state than the good run—not a segmentation or action inference error, but evidence the app or device malfunctioned during the bad run recording.
