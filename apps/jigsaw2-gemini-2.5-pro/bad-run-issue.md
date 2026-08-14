# ViBR Run Issue Report: jigsaw2 (bad quality)

## Log Summary

**Execution Timeline (filtered, post-GroundingDINO init):**

| Time | Module | Event |
|------|--------|-------|
| 16:25:33 | __main__ | CLIP similarity complete. 435 total frames, 2 segments. Raw boundaries: [(0, 358), (362, 433)] |
| 16:25:33 | __main__ | Clamped boundaries: [(0, 358), (362, 433)] |
| 16:25:33 | __main__ | Processing segment 0/0 |
| 16:25:36 | dino_detection | Loading GroundingDINO model device=mps |
| 16:25:39 | dino_detection | DINO annotation saved |
| 16:25:48 | __main__ | Relevant regions: target_regions=[8], predicted_action='tap' |
| 16:25:48 | __main__ | Comparing state: reference vs live |
| 16:26:10 | execute_action | [1] Tap 'Generate Puzzle' button → tap |
| 16:26:10 | __main__ | Action executed. Video processing completed. |

**Interpretation:** ViBR segmented 435-frame video (7 seconds) into 2 scenes using CLIP embedding similarity. Segment 0 spans frames 0–358 (~85% of video), covering entire scroll + tap sequence. DINO detected objects, selected region #8 as target for tap action. State comparison confirmed tap action feasibility. One action executed: tap "Generate Puzzle" button. No actions detected for scroll interactions or initial menu state.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Expected Steps** | 5 (menu→scroll×3→tap) |
| **Executed Actions** | 1 (tap only) |
| **Missing Actions** | 4 (menu state, 3 scroll events) |
| **Coverage** | 20% (1/5 steps) |
| **Execution Status** | Partial success (wrong puzzle size applied) |

ViBR successfully identified and executed a tap action but failed to recognize and execute preceding scroll interactions. The executed tap targeted the correct "Generate Puzzle" button but on an unmodified device state (puzzle size = 4 instead of intended 9), causing the replay to diverge from the ground truth workflow.

---

## Ground Truth vs Execution Log

| Step | Expected Action | Log Shows | Executed? | Status |
|------|-----------------|-----------|-----------|--------|
| 1 | Observe initial menu state | Menu visible, no action | No (implicit) | ✗ Missing |
| 2 | Scroll puzzle size selector 4→2 | No scroll detected | ✗ | ✗ Missing |
| 3 | Continue scroll 2→4→6 | No scroll detected | ✗ | ✗ Missing |
| 4 | Scroll to final size 9 | No scroll detected | ✗ | ✗ Missing |
| 5 | Tap "Generate Puzzle" | Region #8 selected, tap executed | ✓ | ✓ Executed |

---

## Video vs Log Comparison

**Video Timeline (1fps extraction, 7 frames):**

| Frame | Time | Visual Content | Log Shows | Gap? |
|-------|------|-----------------|-----------|------|
| 1 | 0.0s | Menu + size=4, hand near selector | Menu state (implicit) | No action logged |
| 2–3 | 1.0–3.0s | Size scrolling 4→2→4→6, hand on selector | No scroll events | ✗ MISSING |
| 4–5 | 3.0–5.0s | Size 6→9, hand still on selector | No scroll events | ✗ MISSING |
| 6 | 5.0–6.0s | Size=9, hand points at "Generate Puzzle" | Tap action inferred | ✓ Detected |
| 7 | 6.0–7.0s | Puzzle gameplay screen | Should follow tap | No follow-up |

**Gap Analysis:** Frames 1–5 (0–6s) show continuous user interaction (scroll events). Log contains **zero scroll actions** — all 3 scroll interactions invisible to ViBR. Frame 6 tap is logged correctly. Video shows smooth progression; log shows single action in vacuum.

---

## Detailed Failure Analysis

### **Failure 1: Missing Scroll #1 (size 4→2→4)**
- **Expected:** Scroll puzzle size selector downward, value cycles 4→2
- **Log Entry:** None. No scroll action detected or logged
- **Mismatch Reason:** CLIP segmentation did not partition video to isolate scroll as distinct action segment
- **Root Cause Category:** Phase 1.4 (Scene Detection) — "One action split into multiple segments / Incorrect grouping of frames"
- **Evidence:** Segment 0 spans frames 0–358 (85% of video), merging all scroll frames with final tap frame into single scene. No segment boundary between scroll start (frame ~60) and tap (frame ~360)
- **Cascade:** Skipping scroll #1 → device state at wrong position (size=4 vs target=9) → subsequent actions inherit wrong precondition

### **Failure 2: Missing Scroll #2 (size 2→4→6)**
- **Expected:** Scroll puzzle size selector, values progress 2→4→6
- **Log Entry:** None
- **Mismatch Reason:** Same root cause as Failure 1 — unified segment prevents independent scroll detection
- **Root Cause Category:** Phase 1.4 (Scene Detection)
- **Evidence:** Frames 2–3 show clear scroll motion; CLIP embeddings did not detect state transition
- **Cascade:** Device remains at size=2; user must re-scroll to reach size=9

### **Failure 3: Missing Scroll #3 (size 6→9)**
- **Expected:** Final scroll to reach puzzle size = 9
- **Log Entry:** None
- **Mismatch Reason:** Segment boundary at frame 362 occurs **after** all scroll interactions end (~frame 360). This boundary is too late; it separates the scroll sequence from the tap action instead of isolating scrolls
- **Root Cause Category:** Phase 1.4 (Scene Detection) — "Timing sensitivity (±3 frames may be insufficient)"
- **Evidence:** Raw boundaries before clamping were [(0, 358), (362, 433)]. Segment 1 (frames 362–433) should contain post-tap state, but instead likely captures menu screen or early puzzle load. Gap of 4 frames (358→362) is artifact of discretization, not real scene boundary
- **Cascade:** All three scroll events absorbed into segment 0; treated as single "scrolling state" rather than sequence of distinct actions

### **Failure 4: Tap Without Precondition**
- **Expected:** Tap "Generate Puzzle" after puzzle size = 9
- **Log Entry:** `[16:26:10] [INFO] [execute_action] [1] Tap the 'Generate Puzzle' button. -> tap`
- **Mismatch Reason:** Tap correctly identified and executed, but on unmodified device state (size=4, not 9). Device screenshot confirms size=4 post-action
- **Root Cause Category:** Phase 2.7 (State Consistency Check) — "False positives ('same state' when not equivalent)" / Phase 3.11 (Action Inference) — "Ambiguous replay decisions"
- **Evidence:** Reference frame (segment start, frame ~360 from video) shows size=9; device screenshot post-action shows size=4. State mismatch not flagged by ViBR's state consistency check. Model inferred tap action based on visual context but did not validate that device preconditions match video preconditions
- **Cascade:** Puzzle generated at wrong size; user flow broken; subsequent puzzle gameplay uses size=4 instead of size=9

---

## Root Cause Categorization

| Phase | Category | Issue | Count | Impact |
|-------|----------|-------|-------|--------|
| **1** | 1.4 Scene Detection | Incorrect frame grouping; scroll merged with tap into single segment | 3 failures | All scroll actions invisible |
| **2** | 2.7 State Consistency | No validation that device state matches video state before action | 1 failure | Tap executed on wrong device state |
| **3** | 3.11 Action Inference | Model did not infer scroll actions; only detected final tap | 3 failures | Sequence broken; missing intermediate states |

**Dominant Failure Mode:** CLIP embedding similarity threshold (0.95) too aggressive; treated smooth interactive scroll as "stable state," failing to detect state transitions during user finger-drag motion. This collapsed 3 separate scroll actions into noise/single segment, leaving only the final distinct state (finger near button) as actionable.

---

## Impact Assessment

### Execution Flow Broken
- **Intended:** Size 4 → (scroll to 9) → Tap → Gameplay with 9 pieces
- **Actual:** Size 4 → (no scroll) → Tap → Gameplay with 4 pieces
- **Divergence Point:** Step 2 (first scroll not executed)
- **Cascade:** All downstream steps operate on wrong state

### Replay Authenticity
- Tap action is correct for video context (frame 6 shows hand over button)
- But tap applied to wrong device state (puzzle size = 4 vs 9)
- ViBR appears to "succeed" (action executed) but result is semantically incorrect
- User workflow goal (play 9-piece puzzle) not achieved

### Hidden Complexity in Video
- Video contains continuous smooth interaction (scroll animation)
- Scroll is implicit state change, not discrete tap/release gesture
- CLIP embeddings from scroll frames very similar to each other → "stable region"
- Threshold-based segmentation cannot distinguish "stable idle" from "smooth scroll"

---

## Conclusions

ViBR achieved **20% step coverage** on jigsaw2 bad-quality video due to a fundamental limitation in action segmentation. The CLIP-based scene detection algorithm failed to recognize scroll interactions as state-changing actions, collapsing them into a single "stable" region merged with the subsequent tap action.

**Root Cause Summary:**
- **Primary:** Phase 1.4 (Scene Detection) — CLIP similarity threshold treats smooth scroll as static state; no intermediate keyframe boundaries inserted
- **Secondary:** Phase 2.7 (State Consistency) — State validation did not flag device ↔ video state mismatch (size=4 vs size=9)
- **Tertiary:** Phase 3.11 (Action Inference) — LLM did not infer scroll sequence; recognized only final tap

**Underlying Limitation:** Embedding-based scene detection optimized for discrete screen transitions (menu ↔ gameplay) performs poorly on animated continuous gestures (scrolls, drags, swipes). CLIP does not encode kinetic intent; it measures pixel-space similarity, which is high during smooth interactive motion.

**Practical Impact:** Puzzle generated with wrong size (4 instead of 9), breaking user's intended workflow. Replay marked "successful" despite semantic failure.

---

## TL;DR

| Item | Finding |
|------|---------|
| **Coverage** | 20% (1 of 5 steps executed) |
| **Primary Failure** | CLIP scene detection merged scroll+tap into one segment; all 3 scrolls invisible |
| **Secondary Failure** | State consistency check did not flag device size mismatch (4 vs 9) |
| **Success Reason** | Final tap action correctly identified & executed (but on wrong device state) |
| **Bottom Line** | Continuous scroll gestures bypass CLIP's threshold-based segmentation; intermediate state changes lost |

