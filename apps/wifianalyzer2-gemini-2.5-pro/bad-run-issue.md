# WiFi Analyzer 2 (wifianalyzer2) — Bad Video Run Analysis

## Log Summary

ViBR execution timeline (15:09:31–15:13:14, ~4min):

| Time | Module | Event Summary |
|------|--------|---------------|
| 15:09:31 | [dino_detection] | Loading GroundingDINO model (MPS device) |
| 15:09:37 | [dino_detection] | DINO detection on segment 0, saved annotated output |
| 15:09:48 | [__main__] | Regions detected for segment 0: target_regions=[3], action=tap |
| 15:09:48 | [__main__] | Comparing state: reference vs live screenshot |
| 15:09:54 | [__main__] | State mismatch detected, attempting alignment (try 1/3) |
| 15:10:17 | [__main__] | Recovery matched element at (405, 1783) |
| 15:10:17 | [execute_action] | Action 1: Tap 'Channel Rating' button in bottom navigation |
| 15:10:50 | [__main__] | Replay using region index 3 at (512, 1609), action executed |
| 15:10:51 | [__main__] | Processing segment 1 |
| 15:10:56 | [dino_detection] | DINO detection on segment 1 |
| 15:11:08 | [__main__] | Regions detected for segment 1: target_regions=[4], action=tap |
| 15:11:15 | [__main__] | State mismatch for segment 1, attempting alignment (try 1/3) |
| 15:11:34 | [__main__] | Recovery action: Tap 'Channel Graph' button |
| 15:11:42 | [__main__] | Second alignment attempt (try 2/3) |
| 15:12:00 | [__main__] | Recovery action: Tap on graph for AndroidWifi 8 |
| 15:12:09 | [__main__] | Third alignment attempt (try 3/3) |
| 15:12:24 | [__main__] | Final recovery action: Tap Channel Graph tab |
| 15:12:33 | [__main__] | **SKIP SEGMENT**: GUI state mismatch reason logged: reference shows pop-up dialog, current shows only graph |
| 15:12:34 | [__main__] | Processing segment 2 |
| 15:12:39 | [dino_detection] | DINO detection on segment 2 |
| 15:12:46 | [__main__] | Regions detected for segment 2: target_regions=[3], action=tap |
| 15:13:14 | [__main__] | Action 2: Tap 'Channel Graph' button, action executed |
| 15:13:14 | [__main__] | Video processing completed |

**Interpretation**: ViBR started normally but failed at segment 1 (expected state: dialog showing network metadata; actual state: channel graph without dialog). After three failed recovery attempts, segment 1 was skipped due to unresolvable GUI mismatch. Segment 2 executed a tab switch that matched state, completing the run with only 2 of 10 expected actions executed.

---

## Executive Summary

**Expected vs Actual Execution**:
- **Steps Expected (from ground truth)**: 10 user interactions (access points view → channel rating tab → channel graph tab → long-press on graph → metadata dialog → hamburger menu → menu selection → share bottom sheet → app selection → return to graph)
- **Steps Executed (from ViBR log)**: 2 actions (tap Channel Rating button, tap Channel Graph button)
- **Steps Missing**: 8 (metadata dialog interaction, menu navigation, share workflow, detailed graph interaction)
- **Coverage**: 20% (2/10 steps executed)

**Root Cause**: ViBR segmentation detected a scene boundary between the channel graph and the metadata dialog. The ground truth video shows a long-press interaction that opens a dialog (step 4), but ViBR's scene detection broke this into separate segments. When attempting to replay segment 1 (which expected the dialog to appear), the device state did not match the reference frame, causing ViBR to skip the entire segment and lose the interaction flow.

---

## Ground Truth vs Execution Log

| Step# | Expected Action | Executed? | Status | Issue Category |
|-------|-----------------|-----------|--------|-----------------|
| 1 | Screen transition to Access Points list | ✓ | Initial state | None |
| 2 | Tap Channel Rating tab | ✓ | Executed | None |
| 3 | Tap Channel Graph tab | ✓ | Executed (segment 2) | Timing mismatch |
| 4 | Long-press on graph to show details | ✗ | Skipped | **Segment boundary issue** |
| 5 | Modal dialog appears with metadata | ✗ | Skipped | Cascading failure |
| 6 | Tap hamburger menu | ✗ | Never reached | Cascading failure |
| 7 | Menu navigation/selection | ✗ | Never reached | Cascading failure |
| 8 | Share action (Android bottom sheet) | ✗ | Never reached | Cascading failure |
| 9 | Tap share destination app | ✗ | Never reached | Cascading failure |
| 10 | Return to graph view | ✗ | Never reached | Cascading failure |

---

## Video vs Log Comparison

**Frame-by-frame Analysis** (17 frames at 1fps from ~17sec video):

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 0001–0002 | Seg 0 | Initial DINO detection, state comparison | Access Points list view | None |
| 0002 | Seg 0→1 | Attempting alignment try 1/3 | Channel Rating tab (stars visible) | **BOUNDARY** |
| 0003–0005 | Seg 1 | State mismatch, recovery attempts 1–2 | Channel Graph view with hand touching graph | Mismatch: log expects dialog, video shows graph interaction |
| 0005–0006 | Seg 1 | Recovery attempt 3, skip segment | Information dialog with "Copy" and "Quick Share" buttons | **DIALOG NOT REPLAYED** |
| 0006 | Seg 1→2 | Skipped (mismatch reason: "reference shows pop-up dialog, current shows graph") | Hamburger menu opening (left drawer) | User continued interaction despite ViBR skip |
| 0007–0010 | Seg 2 | Processing segment 2 | Menu visible with options (Settings, About, Export, etc.) | **ENTIRE MENU FLOW INVISIBLE TO ViBR** |
| 0011–0015 | Seg 2 | Detecting regions for channel graph action | Share bottom sheet with app icons (My Delays, Seem, Best Deals, etc.) and finger tapping | **SHARE WORKFLOW NOT SEGMENTED** |
| 0016–0017 | Seg 2 | Final action: tap Channel Graph button | Back to Channel Graph view with "Copied" indicator | Graph view matches expected recovery state |

**Critical Observations**:
1. **Hidden Actions**: The metadata dialog (frame 0005–0006) and hamburger menu (frames 0007–0010) appear in video but ViBR has no segments for them after skipping segment 1.
2. **Timing Mismatch**: Frames 0003–0005 show the user long-pressing the graph, but ViBR's segment 1 expected only a tap. Long-press is harder to detect via CLIP similarity than tap.
3. **Cascading Skip**: Once segment 1 was skipped, ViBR never attempted to replay the subsequent menu and share interactions—they remained unexecuted.

---

## Detailed Failure Analysis

### Failure 1: Segment 0→1 State Mismatch (15:11:15–15:12:33)

**Expected Behavior (from ground truth)**: After tapping Channel Rating tab, the device shows a list of channels with star ratings. Then user taps Channel Graph tab and the view switches to a frequency spectrum graph. The user long-presses on the graph, and a modal dialog appears showing metadata about the selected network.

**What ViBR Detected**: 
- Segment 0: Access Points list
- Segment 1: Expected start state is the channel rating view, but ViBR's reference frame (step_1v_relevant_regions.png) contains the dialog, not the graph.

**What Happened on Device**:
- Frame 0003–0004: Channel graph is visible (after tab switch)
- Frame 0005: Dialog appears with metadata
- But ViBR's segmentation break-point placed segment 1 as "dialog should appear on screen"

**Recovery Attempts**:
1. **Try 1** (15:11:34): Tap "Channel Graph" button → didn't help, still had graph, not dialog
2. **Try 2** (15:12:00): Tap on graph for "AndroidWifi 8" → didn't trigger dialog
3. **Try 3** (15:12:24): Tap Channel Graph tab again → toggled back to different state

**Mismatch Reason (logged at 15:12:33)**:
> "Reference image shows a pop-up dialog with details about a specific wi-fi network, which is not present in the current image. The current image only shows the main channel graph."

**Root Cause Category**: **Phase 1.4 — Scene Detection**. The CLIP-based segmentation detected frame-to-frame similarity changes (graph view → dialog overlay), but the recovery mechanism in Phase 3 (Action Execution) could not programmatically trigger the dialog state. The long-press gesture that opens the dialog was missed during segmentation.

**Evidence**: 
- Frames 0003–0005 show continuous user interaction (graph visible, hand gesture, then dialog), but ViBR only segmented this as two states (graph state → dialog state), losing the intermediate gesture.
- CLIP embeddings for "graph + hand" and "graph alone" may be similar enough to not trigger a new segment boundary until the dialog actually appears, creating a state mismatch.

---

### Failure 2: Cascading Skip (Segment 1 → Segment 2+)

**What Happened**:
1. Segment 1 failed to reach expected dialog state (three recovery attempts exhausted).
2. ViBR marked segment 1 as "SKIP" at line [15:12:33].
3. Segment 2 was processed immediately, but it only captured the final graph tap (action executed at 15:13:14).

**Missing Interactions** (never attempted):
- Hamburger menu tap (frame 0006, visible in video)
- Menu item selection (frames 0007–0010)
- Share action / bottom sheet interaction (frames 0011–0015)
- App selection from share menu (frame 0016)

**Why They Weren't Segmented**:
ViBR's segmentation found only 3 scene boundaries in the video (see log: "Scenes: 3"). The hamburger menu and share sheet were not detected as separate segments—they were either:
- Part of segment 2 but overshadowed by the graph state, or
- Too brief or visually similar to adjacent frames to trigger a new boundary at similarity threshold 0.95.

**Root Cause Category**: **Phase 1.3 — Similarity Computation** + **Phase 1.4 — Scene Detection**. Fixed threshold (0.95) failed to detect subtle UI changes (menu drawer opening, bottom sheet appearing) as scene transitions. The menu and share interactions are overlays on the main graph view, so frame-to-frame CLIP similarity remained high despite different interactive content.

---

## Root Cause Categorization

| ViBR Phase | Sub-Category | Count | Issue | Evidence |
|-----------|--------------|-------|-------|----------|
| Phase 1: Action Segmentation | 1.4 Scene Detection | 1 | Incorrect grouping: long-press gesture + dialog not isolated | Frames 0003–0006 show continuous interaction but ViBR segmented as disconnected states |
| Phase 1: Action Segmentation | 1.3 Similarity Computation | 1 | Fixed threshold (0.95) misses menu/share UI overlays | Menu drawer (frame 0006) and share sheet (frames 0011–0015) not detected as scene boundaries |
| Phase 2: GUI State Comparison | 2.7 State Consistency Check | 1 | False negative: dialog expected but not present after recovery attempts | ViBR compared graph-only screenshot to dialog reference; mismatch unresolvable |
| Phase 3: Bug Replay on Device | 3.11 Action Inference | 1 | Long-press gesture not inferred; only tap actions attempted | Recovery attempts tried tap (Channel Graph, on graph area) but never long-press |
| Misc | Cascading Failure | 1 | Skip of segment 1 prevented all downstream interactions | Menu, share, final interactions never reached |

**Dominant Failure Mode**: **Scene Detection Inadequacy**. ViBR's CLIP-based segmentation failed to isolate the long-press → dialog transition as a distinct segment, causing the reference frame to be inconsistent with the device state during replay.

---

## Impact Assessment

**What Prevented Full Execution**:
1. **Segmentation Broke at Gesture-State Boundary** (Phase 1.4): The long-press interaction that opens the metadata dialog was not captured as a separate step. Instead, ViBR placed the dialog as the "expected start state" of segment 1, but the device still showed the graph after the tap recovery attempts.

2. **Recovery Exhaustion** (Phase 3.12): ViBR tried three recovery actions (tap Channel Graph, tap on graph, tap Channel Graph again) but none triggered the dialog. The action inference (Phase 3.11) only considered tap, never inferring the long-press needed to open the dialog.

3. **Threshold Sensitivity** (Phase 1.3): Similarity threshold 0.95 was too high to detect menu/share overlays as scene breaks. These interactions remained invisible in ViBR's action sequence, so only the final "tap Channel Graph" action was recorded.

**Cascading Failures**:
- Segment 1 skip → no metadata dialog interaction
- No menu segmentation → no hamburger menu tap
- No share segmentation → no share workflow execution
- Final execution: only 2 tap actions instead of 10 interaction steps

**Coverage Impact**: 20% (2/10 steps). ViBR successfully replayed only the tab navigation (Access Points → Channel Rating → Channel Graph), but failed on gesture-based interaction (long-press), UI overlays (menu, share sheet), and the dialog-driven workflow.

---

## Conclusions

ViBR's failure on the wifianalyzer2 bad video exemplifies a limitation in **gesture detection and scene boundary refinement**. The ground truth video contains a long-press interaction (frame 0005) that opens a modal dialog, but ViBR's CLIP-based segmentation did not isolate this gesture as a distinct segment. Instead, the dialog appeared as part of the expected state for segment 1, causing a state mismatch when the device showed only the graph (without dialog) during recovery attempts.

Furthermore, subsequent UI interactions (menu drawer, Android share sheet) were too subtle for the fixed similarity threshold (0.95) to detect as scene boundaries. They remained embedded in segment 2, which was only partially replayed (final tap action executed, but menu/share workflow skipped).

**Key Limitations Identified**:
1. **Gesture Vocabulary Mismatch** (Phase 3.9): Long-press is an interactive gesture, but recovery only attempted taps.
2. **Scene Detection Sensitivity** (Phase 1.4): CLIP threshold tuned for large state changes; UI overlays (menu, dialogs) not reliably detected.
3. **State Consistency Assumptions** (Phase 2.7): Recovery expects the device to reach a stable state matching the reference; modal dialogs break this assumption.

**Recommended Improvements**:
- Detect modal dialogs / overlay states explicitly (e.g., via accessibility tree changes, not just visual similarity).
- Expand action vocabulary to include long-press, swipe, and other gestures; infer them from touch event patterns in video frames.
- Adapt similarity thresholds per app (e.g., lower threshold for apps with frequent overlays).
- Segment on changes in the accessibility tree (XML hierarchy), not just visual frames.

**Coverage: 20% (2/10 steps executed)**. **Dominant limitation: Gesture detection and scene segmentation sensitivity**.

---

## TL;DR

- ✓ Tab navigation works (2/3 tab taps executed)
- ✗ Gesture interaction fails (long-press on graph not detected)
- ✗ Dialog state mismatch halts recovery (expected dialog, got graph)
- ✗ UI overlays invisible (menu drawer, share sheet not segmented)
- **Bottom line**: CLIP segmentation too coarse for gesture-driven workflows; modal dialogs and overlays require explicit detection.
