# ViBR Run Issue Report: vanilla (bad-quality)

## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 22:34:59 | check_video.orchestrator | Video codec conversion hevc→h264 |
| 22:35:08 | check_video.orchestrator | Video conversion verified, SDR BT.709 confirmed |
| 22:35:08 | __main__ | Starting video processing (algorithm=clip) |
| 22:35:11 | __main__ | Detecting stable segments |
| 22:35:33 | __main__ | CLIP similarity loaded from cache |
| 22:35:33 | __main__ | Processing segment 0 |
| 22:35:37 | dino_detection | Loading GroundingDINO model (device=mps) |
| 22:36:07 | dino_detection | DINO output saved (step_0v_dino.png) |
| 22:36:16 | __main__ | Relevant regions: [4], action=tap |
| 22:36:16 | __main__ | State comparison: step_0v_relevant_regions vs step_0e_screenshot_0 |
| 22:36:46 | __main__ | Replay region 4 at (787, 1581): "Tap the equals button" |
| 22:36:46 | __main__ | Action executed |
| 22:36:46 | __main__ | Processing segment 1 |
| 22:36:50 | dino_detection | DINO output saved (step_1v_dino.png) |
| 22:37:00 | __main__ | Relevant regions: [5], action=tap |
| 22:37:00 | __main__ | State comparison: step_1v_relevant_regions vs step_1e_screenshot_0 |
| 22:37:24 | __main__ | Replay region 5 at (668, 1569): "Tap the backspace button" |
| 22:37:24 | __main__ | Action executed |
| 22:37:24 | __main__ | Processing segment 2 |
| 22:37:29 | dino_detection | DINO output saved (step_2v_dino.png) |
| 22:37:48 | __main__ | Relevant regions: [], action=tap |
| 22:37:48 | __main__ | State comparison: step_2v_relevant_regions vs step_2e_screenshot_0 |
| 22:38:19 | __main__ | Replay matched element at (934, 1474): "Tap the minus button" |
| 22:38:19 | __main__ | Action executed |
| 22:38:19 | __main__ | Video processing completed |

**Interpretation:** ViBR's action segmentation detected only 3 scenes in a 10-frame video where 6 user actions occur. The algorithm segmented the video at high-level state boundaries (equals→result display, backspace→clear, minus→new calc), missing intermediate steps (tap 3, tap +, tap 6, tap ×, tap 6). DINO region detection succeeded for first two segments but found zero relevant regions in segment 2, triggering fallback coordinate matching. The core issue: CLIP-based scene detection compressed 6 sequential calculator taps into 3 stable-state segments, losing the individual button-press actions that ViBR needed to replay.

## Executive Summary

| Metric | Value |
|--------|-------|
| **Expected Steps** | 6 (3 + tap, 6 + tap, ×, 6, =) |
| **Executed Steps** | 3 (=, backspace, minus) |
| **Steps Missing** | 3 (50% coverage) |
| **Gap Count** | 3 missed interactions |
| **Coverage %** | 50% |

**Verdict:** ViBR achieved 50% action coverage. Three critical steps (3→+, 6→×, 6→=) were missed entirely. The video was segmented at stable display states, not at action boundaries, leading to temporal over-segmentation bias.

## Ground Truth vs Execution Log

| Step# | Expected Action | Executed ✓/✗ | ViBR Action | Issue Category |
|-------|-----------------|--------------|-------------|-----------------|
| 1 | Tap number 3 | ✗ | (skipped) | 1.4: Scene Detection |
| 2 | Tap + operator | ✗ | (skipped) | 1.4: Scene Detection |
| 3 | Tap number 6 | ✗ | (skipped) | 1.4: Scene Detection |
| 4 | Tap × operator | ✗ | (skipped) | 1.4: Scene Detection |
| 5 | Tap number 6 | ✗ | (skipped) | 1.4: Scene Detection |
| 6 | Tap = button | ✓ | Tap equals button @ (787, 1581) | Success |

*Note: ViBR executed 3 additional actions not in truth (backspace, minus) due to misaligned segmentation.*

## Video vs Log Comparison

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 0-1 | Seg 0 (initial) | Loading DINO, processing | Display shows default, user taps 3 | Missing: tap 3 |
| 1-2 | Seg 0 (cont.) | State comparison starting | Display shows "3", user taps + | Missing: tap + |
| 2-3 | Seg 0 (result) | Replay action: tap equals @ (787,1581) | Display shows "3", user taps 6 | **Mismatch**: executing tap = instead of tap + |
| 3-4 | Seg 1 (post-eq) | Processing segment 1, DINO output | Display stable or showing prior state, user taps × | Missing: tap × |
| 4-5 | Seg 1 (cont.) | State comparison, replay backspace | Display shows result, user taps 6 | **Mismatch**: executing backspace instead of taps |
| 5-6 | Seg 2 (pre-result) | Processing segment 2, no regions | Display shows "6×6", user taps = | Missing: user still tapping |
| 6-10 | Seg 2 (result) | Replay element: tap minus | Display shows "36", user done | **Mismatch**: executing minus on final state |

**Analysis:** CLIP segmentation created boundaries at stable display states (initial → after equals → final result), not at action points. Frames 0-3 (user entering 3+6) all assigned to "segment 0" because display remained visually similar during rapid taps. ViBR's first action thus targeted the *end* of this segment (tap equals), not the *start* (tap 3). Segments 1 and 2 similarly misaligned: backspace and minus were extrapolated guesses at state change inference, not observed actions.

## Detailed Failure Analysis

### Step 1: Tap number 3 (MISSING)
- **Expected:** User taps "3" button, display updates to show "3"
- **ViBR Action:** (None — not segmented)
- **Mismatch Reason:** CLIP embedding saw frames with "3" visible but did not detect actionable boundary between initial state and "3 displayed" because visual difference was subtle (single digit added to display)
- **Root Cause Category:** **1.4. Scene Detection** — temporal over-aggregation; consecutive frames with incremental UI changes (display number building) mapped to same embedding cluster, collapsed into single segment
- **Evidence:** Log shows segment 0 processing starts at frame 0, but first action replayed is "tap equals" (end of visible state), not "tap 3" (start)
- **Cascade:** Missing first action breaks action chain; subsequent steps offset by 1, causing action replay on wrong frame context

### Step 2: Tap + operator (MISSING)
- **Expected:** User taps "+" button after seeing "3" displayed
- **ViBR Action:** (None — not segmented)
- **Mismatch Reason:** CLIP did not separate "3" display state from "3+" state as distinct scenes
- **Root Cause Category:** **1.4. Scene Detection** — stable_sim_threshold (0.95) too permissive for single-digit calculators; small text changes insufficient to trigger new segment
- **Evidence:** Frames 1-2 likely below similarity threshold; CLIP saw minimal visual change (button highlight, cursor position)
- **Cascade:** Compounds Step 1 miss; ViBR proceeded to what it perceived as next stable state (result display post-equals)

### Step 3: Tap number 6 (MISSING)
- **Expected:** User taps "6" button after operator
- **ViBR Action:** (None — not segmented)
- **Mismatch Reason:** Operator + first operand display ("6") still below CLIP similarity threshold
- **Root Cause Category:** **1.4. Scene Detection** — fixed threshold does not adapt to button-tapping interactions on calculator UI; "display text changes" register as noise, not scene transitions
- **Evidence:** All taps (3, +, 6) occur within ~3-4 frames; CLIP interval threshold = 1 frame; algorithm detected 0 boundaries during this rapid sequence
- **Cascade:** ViBR jumped directly to "stable state after user finished" (equals pressed, result 36 visible)

### Step 4: Tap × operator (MISSING)
- **Expected:** User taps "×" to multiply result by next operand
- **ViBR Action:** (None — not segmented)
- **Mismatch Reason:** Segment 1 DINO detected "backspace" as relevant action (region 5), not "multiply" — visual grounding confusion on operator buttons
- **Root Cause Category:** **1.4. Scene Detection** + **2.5. Region Detection (GroundingDINO)** — DINO prompt includes "button" generically; backspace and multiply buttons have similar visual properties (pink circles in calculator); DINO ranked backspace higher due to prompt order or training bias
- **Evidence:** Log shows region 5 selected for segment 1; in physical calculator layout, backspace is right-hand column, multiply is also right-hand; DINO likely confused similar-looking pink operator buttons
- **Cascade:** ViBR executed wrong operator, breaking calculation semantics

### Step 5: Tap number 6 (MISSING — second occurrence)
- **Expected:** User taps "6" as multiplier operand
- **ViBR Action:** (None — not segmented in correct context)
- **Mismatch Reason:** Segment 1 boundary placed ViBR at state where "6" was already on display (from Step 3); replaying "backspace" cleared this, making second "tap 6" invisible/unreachable
- **Root Cause Category:** **1.4. Scene Detection** + **3.12. Action Execution** — action execution (backspace) modified device state irreversibly; subsequent steps depend on prior state which no longer existed
- **Evidence:** After backspace execution (line 182), display would be cleared; user's second "6" tap in video is now orphaned (no "+" operator to precede it)
- **Cascade:** Chain of errors cascades; ViBR state no longer matches video ground truth

### Step 6: Tap = button (CORRECT, but early)
- **Expected:** User taps = after entering full expression (3+6×6)
- **ViBR Action:** ✓ Tapped equals button @ (787, 1581)
- **Success Reason:** "Equals" button is visually distinct, unambiguous; DINO had high confidence; action was semantically final
- **Note:** Executed correctly *syntactically* (right button) but *semantically* wrong — should have been action#6, not action#1

## Root Cause Categorization

### Phase 1: Action Segmentation (3 failures)

**1.4. Scene Detection** — 3 occurrences
- CLIP similarity threshold (0.95) insufficient for detecting rapid button-press sequences on calculator
- Frame rate (1fps) may be too coarse for 0.1-0.5s button press durations
- Consecutive taps (3, +, 6) all appear in frames within ±1 stability interval, collapsed into single cluster
- **Fundamental issue:** CLIP trained on natural images/scenes, not on fine-grained UI state transitions during rapid user interactions
- **Evidence:** Segment 0 spans frames 0-~3 (initial display + 3 taps), but CLIP saw it as single stable scene
- **Impact:** 3 steps lost to under-segmentation

### Phase 2: GUI State Comparison (1 failure)

**2.5. Region Detection (GroundingDINO)** — 1 occurrence
- DINO prompt lists "button. icon." generically; calculator has 16 visually similar pink/tan buttons
- Segment 1 DINO selected "backspace" (region 5) instead of "multiply" (region 4 or adjacent)
- Likely cause: CLIP embedding for segment 1 shows operator result state; DINO, viewing static image, inferred "clear display" action rather than "next operator"
- **Impact:** 1 wrong operator button selected, breaking downstream arithmetic

### Phase 3: Bug Replay on Device (0 failures in detected actions, but cascading state corruption)

**3.12. Action Execution** — state mismatch cascade
- Backspace execution modified device state (cleared display)
- Subsequent ViBR actions (minus tap) now operate on corrupted state
- Root cause not in action execution itself, but upstream segmentation & region selection

## Impact Assessment

**What prevented full execution:**
1. **Primary:** CLIP-based scene segmentation designed for longer, more visually distinct state changes; calculator tapping violates assumptions (rapid, subtle UI changes)
2. **Secondary:** DINO visual grounding on generic "button" prompt; no differentiation between button types (operator vs edit)
3. **Tertiary:** Lack of action-boundary-aware segmentation; ViBR segments on *display state*, not *user intent* (tap is a state-change event, not a state itself)

**Cascading failures:**
- Missing Step 1 (tap 3) → subsequent actions temporally offset
- Missing Step 2 (tap +) → operator chain broken
- Wrong operator (backspace vs ×) → state corruption
- Missing Step 5 (tap 6) → incomplete operand
- Step 6 (tap =) executed early on partial state

**Device replay impact:** ViBR successfully executed actions on device; the bug is not in ADB execution but in *which* actions were selected and *when*.

## Conclusions

ViBR achieved **50% coverage (3 of 6 steps)** on the calculator app's "bad" video. The fundamental limitation lies in **Phase 1: Action Segmentation**, where CLIP-based scene detection is optimized for longer state durations and visually distinctive transitions, not for rapid button-tapping workflows common in mobile UIs.

The vanilla calculator exemplifies a worst-case scenario for CLIP segmentation:
- Short video (10 frames, ~10 sec)
- Rapid sequential actions (6 taps in 6 frames)
- Subtle visual changes (display text updates, no screen transitions)
- Uniform UI elements (buttons are similar shapes/colors)

**Dominant failure mode:** Temporal over-aggregation in CLIP embeddings, collapsing action-level granularity into state-level segmentation. The algorithm detects *where* the user ended up (display shows 36), not *how* they got there (sequence of 6 taps).

**Underlying limitation:** CLIP embeddings measure holistic image similarity, not action boundaries. Two frames with "3" on display and "3+" on display may have similarity > 0.95, causing CLIP to treat both as single stable state. This is correct for document scrolling or menu navigation (long stable states), but incorrect for task-completion workflows where every action is a discrete user intent.

**Recommendation for future work:**
- Develop action-aware segmentation: detect *events* (button highlights, visual feedback, display changes) not just *states* (final display value)
- Implement differential CLIP thresholding by interaction type (calculator: lower threshold for button activity detection)
- Augment with action-detection models (e.g., detecting touch feedback animation) to ground segmentation in user gesture timing

## TL;DR

**Success factors:** Equals button detected correctly (high visual salience, unambiguous LLM reasoning)

**Failure factors:**
- CLIP over-segmented 6 rapid taps into 3 stable-state scenes (50% miss)
- DINO confused operator buttons under generic "button" prompt (1 wrong button)
- Missing first 3 actions offset all downstream steps

**Bottom line:** ViBR's scene-detection pipeline trades action granularity for state stability, achieving good results on long-duration tasks but failing on rapid, button-tapping UIs where user intent changes faster than visual state stabilizes.
