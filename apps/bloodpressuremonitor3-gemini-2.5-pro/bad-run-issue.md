# BloodPressureMonitor3 Bad-Run Issue Analysis

## Log Summary

Timeline of key events from execution log (filtered for signal, excluding infrastructure logs):

| Time | Module | Event |
|------|--------|-------|
| 02:38:27 | model_api | Selected provider: gemini |
| 02:38:27 | check_video.orchestrator | ⚠️ Video not SDR BT.709; converting from yuv420p10le |
| 02:38:51 | check_video.orchestrator | Conversion done; video is now SDR BT.709 |
| 02:38:51 | __main__ | Starting video processing (algorithm=clip) |
| 02:38:51 | __main__ | Initializing ADB device controller |
| 02:39:01 | __main__ | Detecting stable segments via CLIP |
| 02:41:28 | __main__ | CLIP analysis complete: 3 segments detected |
| 02:41:28 | __main__ | Segment boundaries: [(0, 1546), (1550, 1629), (1633, 1936)] |
| 02:41:35 | dino_detection | Loading GroundingDINO model |
| 02:41:47 | __main__ | **Segment 0: No relevant regions detected** → predict action: wait |
| 02:41:54 | __main__ | ⚠️ State alignment attempt 1/3 failed |
| 02:42:06 | execute_action | Execute: [1] Wait for graph data to load |
| 02:42:21 | __main__ | ⚠️ State alignment attempt 2/3 failed |
| 02:42:32 | execute_action | Execute: [1] Wait for graph to load |
| 02:42:44 | __main__ | ⚠️ State alignment attempt 3/3 failed |
| 02:42:54 | execute_action | Execute: [1] Wait for graph data to load |
| 02:43:07 | __main__ | **SKIP: GUI state mismatch** — reference shows graph+data, current shows "insufficient data" message |
| 02:43:12 | __main__ | Segment 1: Region 4 detected → predict action: tap |
| 02:43:21 | dino_detection | GroundingDINO identified region 4 (graph button) |
| 02:43:44 | __main__ | Execute: [1] Tap button with graph icon @ (446, 779) |
| 02:43:44 | __main__ | Action executed; video processing completed |

**Interpretation:** ViBR detected 3 segments but processed only 2 (segment 0 and 1). In segment 0, DINO found no interactive regions; ViBR predicted "wait" and retried state alignment 3 times. All 3 alignment attempts failed with the same mismatch: reference frame expected a graph with data entries, but device showed "insufficient data" message and different button layout (3 buttons instead of 2). After exhausting retries, ViBR skipped segment 0 and moved to segment 1, where it successfully identified and tapped the graph icon. Overall: 1 action executed out of ~5 expected from video analysis.

---

## Executive Summary

**Expected vs. Actual Execution:**
- **Truth value steps (from video):** 5 major steps
  1. Initial chart view (waiting/observation)
  2. Tap add button → open data entry form
  3. Enter measurement data (date, time, systolic, diastolic, pulse)
  4. Type note in optional field
  5. Navigate to statistics view
- **Steps executed by ViBR:** 1 (tap graph icon in statistics view)
- **Steps missing:** 4 (add button tap, data entry, note typing, form submission)
- **Coverage:** 20% (1 of 5 expected actions)

**Root cause:** ViBR's segment 0 (covering the add record dialog and form entry flow) failed state alignment 3 times due to GUI mismatch. Reference frame expected a populated chart view, but the device showed an empty chart with "insufficient data" message. This mismatch prevented ViBR from detecting and executing the add button tap and subsequent form interactions. Segment 1 executed successfully (tap graph button), but this was out of sequence and did not replay the intended user workflow.

---

## Ground Truth vs. Execution Log

| Step# | Expected Action (Truth) | ViBR Executed | Status | Category |
|-------|-------------------------|---------------|--------|----------|
| 1 | Wait/observe initial chart view | — | SKIP | State Mismatch |
| 2 | Tap add button (plus icon) | — | SKIP | State Mismatch |
| 3 | Enter systolic/diastolic/pulse | — | SKIP | State Mismatch |
| 4 | Type note in optional field | — | SKIP | State Mismatch |
| 5 | Navigate to statistics view | Tap graph button | ✓ | Executed (partial) |

**Key finding:** ViBR detected segment 1 (statistics view) but skipped segment 0 (data entry form) entirely. Segment 0 accounted for ~75% of the video (frames 0–1546) and contained the core user workflow. Skipped due to persistent GUI state mismatch on device vs. reference.

---

## Video vs. Log Comparison

**Frame segments extracted from video:**
- Frames 0–32 (1 fps): complete user interaction from initial chart → form entry → statistics view
- **Segment 0 frames (approx. 0–15 based on CLIP segmentation):** Chart view + add dialog + form entry
- **Segment 1 frames (approx. 16–20):** Form completion (note typing, possible systolic clear)
- **Segment 2 frames (approx. 21–32):** Statistics view

**Log shows:**
- Segment 0 (frames 0–1546): DINO detected no regions. Model predicted `wait`. Three state alignment retries, all failed.
- Segment 1 (frames 1550–1629): DINO detected region 4 (graph button). Model predicted `tap`. Executed successfully.
- Segment 2 (frames 1633–1936): Not processed in log (only 2 of 3 segments marked in steps_taken).

**Mismatch interpretation:**
- Log: "current screen displays 'not enough data to draw a graph' and has no data listed, whereas reference screen shows a graph and a list of data entries"
- Video shows: User successfully tapped add button, entered data, and navigated to statistics view
- Hypothesis: Reference frame for segment 0 was likely extracted from the **start** of segment 0 (initial chart view), but as user interacted, screen transitioned to add dialog (not present in reference). State alignment failed because the expected chart+data was never visible during the form entry portion of segment 0.

---

## Detailed Failure Analysis

### Failure 1: Segment 0 State Alignment (3x retry exhausted)

**Expected behavior (from video):**
- Frame 0: Chart view with "insufficient data" message (matches ViBR's perceived device state)
- User taps + button
- Dialog opens with data entry form
- User enters data, form changes state
- Dialog may close or transition occurs

**Actual ViBR behavior:**
- DINO found no interactive regions in segment 0 reference frame
- Model predicted action: `wait`
- Attempted state alignment 3 times:
  - Try 1: Compare reference (step_0v_relevant_regions.png) vs live (step_0e_screenshot_0.png)
  - Try 2: Compare step_0v_tmp_stop.png vs step_0e_screenshot_1.png
  - Try 3: Compare step_0v_tmp_stop.png vs step_0e_screenshot_2.png
- All 3 failed with: "current screen shows 'insufficient data' message with no data, reference shows graph with data entries"
- Decision: SKIP action (state never aligned)

**Root cause category:**
- **Phase 2: GUI State Comparison** — specifically **2.7. State Consistency Check**
  - False negative: ViBR's reference frame expected post-data state (chart with populated data), but device never transitioned to that state during segmentation
  - **Underlying issue:** Video input artifact or CLIP segmentation boundary incorrectly placed reference frame at an intermediate state (add dialog open) instead of the stable start state (chart view with data)

**Evidence:**
- DINO output: "No relevant regions to annotate" — indicates reference frame had no clickable elements
- GPT mismatch reason: explicit state difference (missing data in current vs. present in reference)
- Expected interaction (tapping add button) was never attempted because reference frame assumed a different starting state

### Failure 2: Segment 1 Executed Out of Order

**What happened:**
- Segment 1 (frames 1550–1629) successfully detected region 4 (graph button)
- ViBR executed tap at (446, 779)
- This transitioned device to statistics view

**Why this is a problem:**
- Segment 0 (the add record dialog and data entry) was supposed to run first
- Segment 1 and 2 depend on segment 0 completing successfully
- Executing segment 1 bypassed the entire form submission workflow
- Result: Device shows statistics view without new data being added

---

## Root Cause Categorization

### Phase 2: GUI State Comparison (Primary)

**2.7. State Consistency Check — False Negative**
- **Count:** 3 occurrences (3 retry attempts)
- **Issue:** Reference frame expected a chart view with data, but device screen showed "insufficient data" message
- **Reason:** CLIP segmentation boundary (frame split at 1546→1550) may have placed reference frame snapshot at an intermediate state or the reference was compared against a different device state than the video's ground truth
- **Impact:** ViBR abandoned segment 0 after 3 failed retries, preventing all form interactions

**2.5. Region Detection (GroundingDINO) — Missed Elements**
- **Count:** 1 occurrence (segment 0)
- **Issue:** DINO found "No relevant regions to annotate" in segment 0
- **Reason:** Add button likely became invisible or non-interactive in the reference frame (possibly due to timing artifact or video frame extraction)
- **Impact:** No regions detected → action space empty → model defaulted to `wait` (safe but unproductive)

### Phase 1: Action Segmentation (Secondary)

**1.3. Similarity Computation — Incorrect Grouping**
- **Count:** 1 (possible)
- **Issue:** 3 segments detected, but boundary placement at frames 1546/1550/1633 may reflect false transitions
- **Evidence:** Segment 0 (0–1546) is 80% of total video, yet represents only initial view + form interaction
- **Possible cause:** CLIP similarity threshold (0.95) may have been too strict; consecutive frames in form entry (data → clear field → statistics) show GUI changes that triggered false boundaries

---

## Impact Assessment

**Cascade failure:**
1. Segment 0 state alignment failed 3x → skipped entirely
2. Segment 1 executed in isolation (graph button tap) → navigated to statistics view
3. Segment 2 never processed (log shows only 2 of 3 segments in steps_taken)
4. Intended workflow (add record) incomplete; device shows statistics without new entry

**Prevention required:**
- Robust reference frame selection (ensure stable start state, not intermediate transitions)
- Fallback heuristics for "no regions" scenarios (e.g., scan full frame for tap-able elements, not just DINO regions)
- Segment boundary validation (detect false transitions caused by fast UI changes, form field updates, keyboard visibility)

---

## Conclusions

**Coverage:** 20% of expected actions executed (1 of 5 steps).

**Dominant failure mode:** GUI state mismatch in Phase 2 (State Consistency Check). The model's reference frame expected a populated chart view, but the device screen showed an empty chart with insufficient data message. This mismatch persisted across 3 retry attempts, exhausting the recovery strategy and forcing ViBR to skip the entire data entry segment.

**Underlying limitation:** ViBR's state alignment logic assumes reference and live frames should match within the same segment. However, in this video:
- Segment 0 spans multiple distinct UI states (initial chart → add dialog → form with data)
- CLIP segmentation placed the boundary such that the reference frame expected post-data state, not the pre-action state
- DINO's region detection failed to identify the add button in the context of the reference frame

**Academic insight:** The failure demonstrates a fundamental challenge in video-based UI automation: **temporal alignment mismatch**. CLIP detects scene changes (major transitions), but does not account for **intra-scene state transitions** (e.g., form field changes, dialog overlays, keyboard appearance). When such transitions occur within a segment, the model's reference frame (typically at segment start) may not match the ground truth of what that segment "should" accomplish.

**Recommendation:** Future work should incorporate multi-frame references per segment or use dynamic state tracking (e.g., observe consecutive frames to detect intermediate transitions and adapt action space accordingly).

---

## TL;DR

- **Success:** 1 action (tap graph button) executed
- **Failures:** 4 actions skipped (add button, form entry, note typing, form submission)
- **Coverage:** 20%
- **Root cause:** Segment 0 state alignment failed 3x due to GUI mismatch (reference expected chart+data, device showed "insufficient data" message)
- **Category:** Phase 2.7 (State Consistency Check) — false negative; reference frame and live state assumed different app state
- **Bottom line:** ViBR skipped the entire data entry workflow due to reference-frame mismatch during state alignment, demonstrating the brittleness of fixed reference frames in fast-transitioning UIs.
