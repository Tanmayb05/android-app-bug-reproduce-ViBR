# ViBR Run Analysis: bloodpressuremonitor3 (bad run)

## Executive Summary

**Ground Truth (video):** 2 distinct scenes with state transition between segments
**Actually Executed:** 1 action completed (tap graph icon)
**Gap:** 1 segment skipped despite state alignment; execution coverage 50%

Run detected segments correctly but skipped Segment 0 due to persistent state mismatch warnings, even though video shows the same empty state throughout Segment 0. Critical finding: the mismatch is not data absence, but **transient UI rendering difference** during state alignment attempts.

---

## Ground Truth vs Execution Log

| Segment # | Video State | Emulator State | Executed | Status | Issue |
|-----------|------------|---|----------|--------|---------|
| 0 | Empty (no data message, tabs visible) | Empty (no data message, tabs visible) | ✗ Skipped | Failed | State alignment rejected despite visual match |
| 1 | Graph data visible (post-transition) | Empty state persists | ✓ Executed | Partial | Action executed in wrong context |

**Coverage:** 1/2 = 50%

---

## Video vs Execution Comparison

### Segment 0 (Frames 0–1546)

**Video timeline (physical device):**
- Frame 0: "Not enough data to draw a graph" message, date range (Apr 24–May 1), 3 FAB buttons (settings, graph, +), dark theme
- Frame 773 (midpoint): Identical state, user hand visible, app stable
- Frame 1546 (end): Identical state, user finger positioning for graph tap

**Execution (emulator):**
- Initial screenshot: Same "Not enough data" message
- State comparison loop: 3 attempts to align states
- All 3 attempts reported mismatch

**Visual Match Observation:** Video's Segment 0 displays **empty state throughout**, matching emulator's empty state. Yet ViBR rejected replay due to "mismatch" warnings in log.

**Discrepancy identified in log (lines 160):**
```
Mismatch reason: the current screen displays a message 'not enough data to draw a graph' 
and has no data listed, whereas the reference screen shows a graph and a list of data entries. 
Additionally, the floating action buttons are different; the current screen has three buttons 
(settings, graph, and plus), while the reference screen has only two (settings and plus).
```

But **video timeline extraction shows video also has 3 FAB buttons AND empty state**. Reference screenshot (step_0v_tmp_stop.png) is not the actual video frame; it's an artifact taken at segment end.

**Key Issue:** ViBR compared emulator state to `step_0v_tmp_stop.png` (artifact), not to actual video segment 0 content. The artifact may represent a different frame or processing artifact.

---

### Segment Boundary Transition (Frames 1546–1550)

**Critical discovery:** Between frames 1546 and 1550, video shows a **state jump**.
- Frame 1546: Empty state (no data message)
- Frame 1550: Graph with data visible

This 4-frame gap represents the **dynamic element** or **transient UI transition** that CLIP segmentation detected as boundary.

**Video shows data materializes between segment boundary.** Emulator state remains empty throughout.

---

### Segment 1 (Frames 1550–1629)

**Video timeline:**
- Frames 1550–1589: Graph with data visible, user hand positioning
- Action context: tap graph icon to navigate

**Execution (emulator):**
- State: Still shows empty ("Not enough data") message
- ViBR action: tap at (446, 779) — graph icon
- Result: executed, but in empty state (no post-tap transition visible)

**Execution Status:** ✓ Action executed; ✗ Context mismatch (empty vs data-populated)

---

## Detailed Failure Analysis

### Segment 0: State Mismatch Rejection — FAILED

**Expected behavior (video ground truth):**
> Display empty state with message "Not enough data to draw a graph", date navigation (Apr 24–May 1), and 3 FAB buttons.

**What the log shows:**
```
[INFO] Relevant regions: {'target_regions': [], 'predicted_action': 'wait'}
[WARNING] Skipping action: current GUI state does not match start state. 
Mismatch reason: the current screen displays a message 'not enough data to draw a graph' 
and has no data listed, whereas the reference screen shows a graph and a list of data entries.
```

**Root Cause Analysis:**

1. **Video Content:** Segment 0 IS the empty state (confirmed by timeline frames 0, 773, 1546)
2. **Reference Image Mismatch:** Log compares emulator to `step_0v_tmp_stop.png` (reference artifact), which shows **graph with data**, not the actual segment 0 content
3. **Artifact Origin:** `step_0v_tmp_stop.png` appears to be the segment *endpoint* snapshot after video processing, not the segment start frame
4. **CLIP Segmentation Result:** Correctly identified Segment 0 as stable (frames 0–1546), then detected transition at 1546→1550 (data appears)

**Why rejection occurred:**
- ViBR extracted `step_0v_tmp_stop.png` as the reference state (expected state at segment end)
- Emulator showed empty state throughout
- Reference image showed populated data
- ViBR reported mismatch correctly (empty vs populated)
- But this mismatch is **expected** — the reference image is from segment *endpoint* post-transition, not segment 0 content

**Evidence:**
- Video Frame 1546 (segment 0 end): empty state ✓
- Artifact `step_0v_tmp_stop.png`: populated state ✗ (this is from segment 1, not 0)
- Emulator: empty state ✓

**Timing Issue:** ViBR used the wrong reference image (segment-end artifact vs. segment-start/mid content).

---

### Segment 1: Execution in Wrong Context — PARTIAL

**Expected behavior (video ground truth):**
> Tap graph icon to navigate, with graph data visible on screen (context-dependent action).

**What the log shows:**
```
[INFO] Replay using region index: 5 at (446, 779)
[INFO] [execute_action] [1] Tap the button with the graph icon. -> tap
[INFO] Action executed.
```

**Execution Status:** Action was executed as predicted, but emulator state remained empty (no data context), so the action had no visible effect.

**Impact:** Action replay is mechanically correct but semantically wrong (context mismatch). In video, tap navigates within data. In emulator, tap has no effect (no data to navigate).

---

## Root Cause Categorization

### Stage 2: GUI State Comparison (1 critical failure)

**Transient artifact overlay / State reference mismatch:** 1 occurrence

The core failure is not video-vs-emulator state difference, but **reference image selection error**. ViBR compared:
- Emulator current state (Segment 0 empty state) 
- vs. `step_0v_tmp_stop.png` (Segment 1 populated state)

This is a **Stage 2** failure because the root cause is in GUI state comparison, not segmentation. The reference artifact contains a different scene (post-transition) than the segment being replayed.

**Severity:** High. Safety mechanism (state validation) correctly triggered, but on wrong reference. This prevented Segment 0 replay despite aligned ground-truth state.

---

## Video Timeline Analysis

| Frame | Segment | Log Event | Visual Content | Alignment |
|-------|---------|-----------|---|---|
| 0 | 0 | Wait (predicted) | Empty state, no data, 3 FAB buttons | ✓ Match |
| 773 | 0 | Wait | Empty state, same | ✓ Match |
| 1546 | 0 end | Alignment attempt 3 | Empty state | ✓ Matches emulator |
| 1550 | 1 start | Segment boundary | **Data appears** (graph visible) | ✗ Mismatch |
| 1589 | 1 | Tap executed | Graph with data | ✗ Emulator still empty |

**Key observation:** Video *contains* state transition (empty→data at 1546→1550). Emulator misses this transition entirely.

---

## Conclusions

ViBR achieved 50% action coverage on bloodpressuremonitor3 bad run. Segment 0 was **incorrectly rejected** due to reference image mismatch, not actual state divergence. The video's Segment 0 is indeed empty (matches emulator), but ViBR compared against a post-transition image.

**Primary root cause:** Reference image artifact (`step_0v_tmp_stop.png`) selected from wrong segment boundary, causing false positive mismatch detection.

**Secondary issue:** State transition between segments (data materialization at 1546→1550) represents a **transient UI change** or **dynamic element** (Section 3.1.4: Dynamic element false boundary) that CLIP segmentation correctly detected but ViBR's state validation rejected due to reference mismatch.

**Mitigation:** Use frame-accurate reference extraction at segment start, not segment end artifact. Or detect and handle transient boundaries gracefully.

---

## TL;DR — Why It Failed

**Failure reason: Reference image mismatch in state validation**
- Video Segment 0: empty state ✓
- Emulator Segment 0: empty state ✓
- Reference image used: `step_0v_tmp_stop.png` (from post-transition) showing populated data ✗
- Comparison: empty vs. populated → mismatch detected
- Result: Segment 0 skipped despite aligned ground truth

**Bottom line:** ViBR's state validation correctly detected a mismatch, but the mismatch was between emulator and a wrong reference image (from Segment 1), not between emulator and actual video content. The video and emulator had the *same* empty state in Segment 0. Fixing reference image timing would resolve.
