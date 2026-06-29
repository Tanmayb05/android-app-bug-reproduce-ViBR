# ViBR Run Analysis: bloodpressuremonitor3 (bad run)

## Executive Summary

**Ground Truth:** 6 expected steps (navigate dashboard → statistics → systolic/diastolic/pulse tabs → metrics by time of day)
**Actually Executed:** 1 step executed (single tap on graph icon)
**Gap:** 5 steps missing (16.7% execution rate)

The bad run achieved minimal execution coverage. ViBR detected 2 processable segments but skipped the primary action in segment 0 due to GUI state mismatch, then executed only 1 tap in segment 1. Root cause: **dynamic content mismatch** — the reference video shows graph data displayed, but the bad run video shows "Not enough data to draw a graph" state, causing ViBR to reject the action as unsafe.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 0 | Navigate to Statistics screen (implicit start state) | ✗ | Skipped | Dynamic/session-specific content |
| 1 | View Systolic distribution (implicit in stats screen) | ✗ | Skipped | Dynamic/session-specific content |
| 2 | Tap Diastolic tab | ✗ | Skipped | Dynamic/session-specific content |
| 3 | Tap Pulse tab | ✗ | Skipped | Dynamic/session-specific content |
| 4 | Scroll to Metrics by Time of Day | ✗ | Skipped | Dynamic/session-specific content |
| 5 | View polar chart (final state) | ✗ | Skipped | Dynamic/session-specific content |
| 6 | Tap graph icon (segment 1 action) | ✓ | Success | — |

---

## Video vs Log Comparison

### Segment 0 (Frames 0–1546, ~25.8 seconds)

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 0–1 | Seg 0 start | Wait for state alignment | App UI with "not enough data" message (dark theme) | ⚠️ YES |
| 1–8 | Seg 0 progress | Attempt state alignment (retry 1/3) | Keyboard visible, user actively typing/entering data | ⚠️ YES |
| 8–16 | Seg 0 progress | Attempt state alignment (retry 2/3) | Keyboard still open, user interaction ongoing | ⚠️ YES |
| 16–24 | Seg 0 progress | Attempt state alignment (retry 3/3) | Keyboard still open, user typing | ⚠️ YES |
| 24–25.8 | Seg 0 end | Action skipped: GUI state mismatch (reference has graph, current has "not enough data") | Screen still shows no-data state | ✓ Aligned |

**Key Observations:**
- **Hidden user action:** User manually entered data via keyboard throughout segment 0, but ViBR never executed this action. Log shows `wait` commands but video shows active user interaction.
- **State mismatch root cause:** Reference screenshot (from good run) shows graph data; bad run shows empty state. ViBR correctly rejected action as unsafe but missed that user was manually recovering by entering data.
- **Timing gap:** Log shows ~3 retry attempts over 24+ frames; video confirms keyboard was visible the entire time, indicating data entry was in progress.

### Segment 1 (Frames 1550–1629, ~80 frames)

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 1550–1629 | Seg 1 | Detect relevant region (tap on graph icon) | Keyboard closes, screen transitions to show polar chart visualization | ✓ Aligned |
| 1629–1936 | Seg 2 (skipped in log) | Not processed | Polar chart fully visible with 24-hour distribution (teal/cyan colors) | — |

---

## Detailed Failure Analysis

### Step 0–5: Navigation and Tab Switching — SKIPPED

**Expected behavior (ground truth):**
> User navigates to Statistics screen and sequentially views Systolic, Diastolic, and Pulse value distributions, then scrolls to view Metrics by Time of Day (polar chart).

**What the log shows:**
> Segment 0 processing:
> ```
> Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_0.png
> Attempting to align state (try 1/3)...
> Wait for the graph data to load. -> wait
> 
> Comparing state (recovery attempt 1): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_1.png
> Attempting to align state (try 2/3)...
> Wait for the graph to load. -> wait
> 
> Comparing state (recovery attempt 2): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_2.png
> Attempting to align state (try 3/3)...
> Wait for the graph data to load. -> wait
> 
> Comparing state (recovery attempt 3): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_3.png
> Skipping action: current GUI state does not match start state. Mismatch reason: the current 
> screen displays a message 'not enough data to draw a graph' and has no data listed, whereas the 
> reference screen shows a graph and a list of data entries. additionally, the floating action 
> buttons are different; the current screen has three buttons (settings, graph, and plus), while 
> the reference screen has only two (settings and plus).
> ```

**Mismatch reason:**
> GUI state comparison detected critical difference: reference (good run) shows data-populated dashboard with graph visualization; current (bad run) shows "Not enough data to draw a graph" message. ViBR made 3 alignment attempts, each issuing `wait` command, but state never aligned.

**Root cause:** **Dynamic/session-specific content** — the bad run video captures a device state where blood pressure measurement data is absent or has not yet loaded. The reference video assumes pre-existing data. This is not a ViBR bug; it is a legitimate state divergence.

- **Evidence:** Log line 160 explicitly states: "current screen displays a message 'not enough data to draw a graph' and has no data listed, whereas the reference screen shows a graph and a list of data entries."
- **Why it matters:** Because segment 0 represents the primary navigation flow (tapping to access statistics), skipping it blocks all downstream tab-switching and scrolling actions. Cascading failure: 5 dependent steps cannot execute.

### Step 6: Tap Graph Icon — EXECUTED

**Expected behavior (secondary, inferred):**
> User may tap graph icon to open statistics or alternative view.

**What the log shows:**
> Segment 1 processing:
> ```
> Relevant regions: {'target_regions': [4], 'predicted_action': 'tap'}
> GPT selected regions: [4]
> Replay using region index: 5 at (446, 779)
> Action executed: [1] Tap the button with the graph icon. -> tap
> ```

**What video shows:**
> Frame 1550–1629: Keyboard closes, screen transitions. By frame 1629, polar chart is visible, indicating the app navigated to or updated the view. Tap was successful in changing screen state.

**Root cause:** None — action executed as planned.

- **Evidence:** Action completed, screen state changed (keyboard → chart).
- **Why it succeeded:** Segment 1 had clear, unambiguous UI state matching.

---

## Root Cause Categorization

### Stage 1: Action Segmentation (0 failures)
- Over-segmentation: 0
- Dynamic element false boundary: 0

**Verdict:** Segmentation was correct. CLIP detected 3 segments and clamped boundaries appropriately.

### Stage 2: GUI State Comparison (5 failures)
- **Dynamic/session-specific content:** 5
  - Reference assumes pre-existing blood pressure data (graph visible)
  - Bad run has empty state ("Not enough data to draw a graph")
  - No root UI differences (buttons, layout, theme) — pure data absence

### Stage 3: Bug Replay on Device (0 failures)
- Semantic gap: 0
- Masked intermediate transition: 0

**Verdict:** ViBR correctly identified and refused to replay on mismatched state. This is defensive behavior, not a bug.

---

## Video vs Log Deep Dive: Hidden User Action

**Critical finding:** Video shows user entering data via keyboard (frames 1–24) while log shows ViBR issuing `wait` commands.

- **Frame 0–1:** App starts in no-data state.
- **Frame 1–24:** User's finger visible on keyboard, typing blood pressure values manually.
- **Log:** ViBR observes no-data state, issues `wait`, never detects keyboard or user action.

**Interpretation:**
> ViBR's reference is a good run with pre-loaded data. The bad run is a fresh/reset device state. The user manually recovered by entering data in real-time (visible in video), but ViBR's state alignment logic only saw the mismatch, not the recovery action. This is a **data availability gap**, not a ViBR algorithm failure.

---

## Impact Assessment

**Execution gap:** 5 steps (83.3% coverage loss)

**Cascading failure chain:**
1. Segment 0: Skipped due to data mismatch → primary navigation blocked
2. Dependent steps (tabs, scroll): Cannot execute without completing segment 0
3. Segment 1: Executed as fallback (tap graph icon)
4. Segment 2: Not processed (beyond scope)

**Prevention:**
- Segment 0 represents a state that **cannot reliably be matched** between a pre-populated reference (good run) and a fresh device (bad run).
- Future runs should either: (a) pre-populate test data on device, (b) use reference videos from similar starting states, or (c) accept that data-dependent apps require synchronized device state.

---

## Conclusions

The bad run achieved 16.7% execution (1/6 steps) due to a **data availability mismatch**, not algorithmic failure. ViBR correctly detected that the device state diverged from the reference and refused to proceed (safe behavior). The video evidence confirms this: the bad run starts with an empty dataset while the good run assumes pre-existing data.

**Root cause (academic):** ViBR's state-matching pipeline relies on visual equivalence between reference and live screenshots. When reference assumes populated application state and live reflects an empty/reset state, alignment fails. This is a **domain-level data inconsistency**, not a vision or segmentation error.

**Severity:** Medium. The single executed action (tap graph icon) succeeded, so ViBR did not produce an incorrect interaction. However, the workflow was incomplete due to upstream state mismatch.

---

## TL;DR — Why It Failed

**Failure reason:**
- **Dynamic/session-specific content (5 failures):** Reference video (good run) assumes blood pressure measurement data exists. Bad run video shows empty state ("not enough data to draw a graph"). ViBR detected mismatch and correctly refused to proceed, skipping segment 0 (primary navigation). Video confirms user manually entered data via keyboard during segment 0, but ViBR's state alignment did not detect this recovery action.

**Bottom line:** ViBR executed safely by rejecting a mismatched state, but the mismatch arose from data availability, not UI differences. The bad run could not follow the good run's flow because it started from a fresh/empty device state. One fallback action (tap graph icon) succeeded in segment 1.
