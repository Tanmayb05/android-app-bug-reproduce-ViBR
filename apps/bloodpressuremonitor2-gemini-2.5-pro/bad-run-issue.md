# Blood Pressure Monitor 2 (Bad Run) — ViBR Execution Analysis

## Log Summary

**Timeline** (filtered logs, starting after GroundingDINO load at 02:34:08):

| Timestamp | Module | Event |
|-----------|--------|-------|
| 02:34:13 | dino_detection | DINO output annotated for segment 0 |
| 02:34:22 | __main__ | Relevant regions empty; predicted action: wait |
| 02:34:31 | __main__ | State alignment attempt 1/3 initiated |
| 02:34:42 | execute_action | [1] Wait for graph and data to load → wait |
| 02:34:55 | __main__ | State alignment attempt 2/3 initiated |
| 02:35:08 | execute_action | [1] Wait for graph and data to finish loading → wait |
| 02:35:21 | __main__ | State alignment attempt 3/3 initiated |
| 02:35:34 | execute_action | [1] Wait for data to load → wait |
| 02:35:46 | __main__ | **SKIP ACTION 0**: Reference shows graph + data; current shows "not enough data" + different UI (tabs vs table) |
| 02:35:51 | dino_detection | DINO output annotated for segment 1 |
| 02:36:00 | __main__ | Relevant regions: [6]; predicted action: tap |
| 02:36:08 | __main__ | State alignment attempt 1/3 initiated |
| 02:36:16 | execute_action | [1] Tap graph icon button → tap (recovery attempt 1) |
| 02:36:27 | __main__ | State alignment attempt 2/3 initiated |
| 02:37:19 | __main__ | Tap back arrow (recovery attempt 2); then tap graph icon (recovery attempt 3) |
| 02:37:49 | __main__ | **SKIP ACTION 1**: Reference shows dashboard + graphs; current shows data entry form (two distinct screens) |

**Interpretation:**
ViBR segmented the video into 2 scenes correctly. Segment 0 depicts initial empty graph state and predicts a wait action, but fails alignment 3 times due to fundamental state mismatch: the reference video frame shows data/graphs present, but device initially shows "not enough data" screen. Segment 1 correctly identifies a tap action (add button), but after 3 recovery attempts, ViBR gives up because the target screen (statistics/graphs) conflicts with current execution state (data entry form). Root cause: **ViBR's segmentation extracted video frames showing the final statistics screen as the action target, but did not detect the intermediate form-filling steps**, creating an impossible alignment scenario.

---

## Executive Summary

- **Expected steps (from video truth):** 5 major interactions: wait → tap FAB → fill form (3 fields + note) → submit → view stats
- **Executed steps (from ViBR log):** 0 actions completed
- **Coverage:** 0/5 steps (0%)
- **Root issue:** Segmentation missed intermediate steps; ViBR detected only 2 scene boundaries instead of 5+, conflating form-entry activity into one segment with contradictory start/stop states

---

## Ground Truth vs Execution Log

| Step# | Expected Action | Video Shows | ViBR Segment | ViBR Status | Issue |
|-------|-----------------|-------------|--------------|-------------|-------|
| 1 | Wait for graph screen | Empty graph, "Not enough data" message | Seg 0 start | Predicted wait | No action because state doesn't match end frame |
| 2 | Tap add button (FAB) | User taps blue FAB | Seg 0→1 transition | Detected tap, region [6] | Attempted recovery 3x, then skipped |
| 3 | Fill systolic/diastolic/pulse | User types 122, 78, 72 | Seg 1 middle (missed) | Not detected | Hidden in segment 1 without action |
| 4 | Add note "polu" | User types text | Seg 1 middle (missed) | Not detected | Hidden in segment 1 without action |
| 5 | Submit form & navigate | Save pressed, stats shown | Seg 1 end | Not executed | Form never filled, so no submit possible |

---

## Video vs Log Comparison

**Frame Timeline vs Log Events:**

| Frame Range | Content Observed | Log Shows | Gap |
|-------------|-----------------|-----------|-----|
| 0–2 (0–2s) | Graph screen, "not enough data" | Segment 0 start, predict wait | ✓ Aligned |
| 2–5 (2–5s) | FAB tap, form opens | Segment 1 detected, predict tap | ✓ Aligned |
| 5–15 (5–15s) | User fills form (Sys, Dia, Pulse, Note) | Segment 1 body (treated as single wait/hold) | **✗ Gap:** ViBR logs no fill actions; video shows active typing |
| 15–32 (15–32s) | Submit & statistics screen | Segment 1 end (skipped) | **✗ Gap:** ViBR never reached save/transition |

**Hidden Actions Detected:**
- Form-filling steps (3 separate inputs + note entry) were not recognized as distinct actions; they appeared to ViBR as one continuous segment without state transitions
- Keyboard interactions masked intermediate screen state changes
- No keyboard dismiss/state-change detection between field entries

---

## Detailed Failure Analysis

### Failure 1: Segment 0 — State Alignment Impossible

**Expected:** Wait action completes; next action is tap FAB to open form.

**What ViBR saw:**
- Reference image: `step_0v_tmp_stop.png` (from video frame marking segment 0 end)
- Live screenshots: `step_0e_screenshot_[0-3].png` (device screenshots after 3 wait + retry attempts)
- Log: *"reference screen displays a graph and a list of data points, while the current screen shows a message 'not enough data to draw a graph'"* (line 160)

**Root cause:** The video segment boundary was placed at a frame where data/graphs ARE present (showing successful data load). But the device starts with empty state. ViBR correctly predicted "wait," but the reference frame chosen represents the **end state after all actions**, not the intermediate state during the wait. This is a **segmentation boundary error**: the segment marked "segment 0 stop" should align with a device screenshot, but instead aligns with a video frame from deep in the sequence.

**Category:** **Phase 1.4 — Scene Detection**: Incorrect grouping/boundary placement. Fixed threshold or CLIP similarity caused ViBR to mark a frame deep into the form-filling sequence as segment 0 end, when it should have ended immediately after the graph appears empty.

### Failure 2: Segment 1 — Recovery Loop Exhausted

**Expected:** Tap FAB → form opens → (user fills form) → submit → statistics screen.

**What ViBR saw:**
- Segment 1 start: Form entry screen (after FAB tap)
- Predicted action: Tap to navigate to graph/statistics
- Region detected: [6] (likely the add/FAB button or a chart icon)
- Recovery attempts 1–3: Tried different coordinates (939, 1518), back arrow (74, 137), alternate coordinate (939, 1716)
- Result: All attempts failed to match reference state (dashboard with graphs)

**Why it failed:**
1. ViBR segmented the entire form-filling sequence (5–15s) as one scene boundary
2. No intermediate actions detected between "tap FAB" (segment boundary) and "form filled" (next segment boundary)
3. Recovery logic attempted to navigate **away** from the form (tap back, tap graph icon) to reach the expected next state (statistics), but this is the wrong recovery strategy: the form must be filled first
4. After 3 exhausted attempts, ViBR gave up and skipped the action (line 195)

**Why recovery failed:** Log line 182 shows ViBR tried to identify recovery regions, but the device remained on the form screen. Recovery attempted navigation (back, graph icon taps) instead of recognizing the form must be completed first.

**Category:** **Phase 1.4 — Scene Detection** (primary): Video shows 5 distinct interactive steps, but CLIP + fixed threshold (0.95) grouped form-filling into one segment. **Phase 3.10 — GUI Perception** (secondary): ViBR misunderstood the device state during recovery—it saw a form but expected a statistics screen, leading to navigation attempts that were semantically wrong.

---

## Root Cause Categorization

### Primary: Phase 1.4 — Scene Detection (Over-Grouping)

**Issue:** CLIP embeddings did not detect sufficient visual difference between:
- Frame showing FAB tap / form opening
- Frames showing form fields being filled (text entry with keyboard)
- Frame showing form submitted / statistics screen

**Evidence:**
- Video duration: 32s
- CLIP-detected segments: 2 (instead of 5+)
- Segment 0: ~0–5s (graph → form open)
- Segment 1: ~5–32s (entire form-fill + submit + stats, all merged into one)

**Why CLIP failed:** The blood pressure monitor's UI has subtle changes:
1. **Keyboard appearance/disappearance** does not trigger a strong visual boundary (same form still visible, just with keyboard overlay)
2. **Field focus changes** (blue outline on different input) are color-only modifications, potentially below CLIP's threshold
3. **Form field values** (text content) are text-level, not image-level changes; CLIP does not weight text changes heavily
4. **Statistics screen** has similar color scheme/layout structure to form (dark theme, scrollable content), reducing embedding distance

**Impact:** Impossible for ViBR to execute form-filling steps because it never recognized them as separate actions.

### Secondary: Phase 2.7 — State Consistency Check (False Negative)

**Issue:** ViBR's state comparisons used GPT-4o to evaluate whether reference and live screenshots matched. Both comparisons correctly identified mismatches, but the recovery logic was semantically wrong.

**Evidence (log lines 160, 195):**
- Segment 0: Correctly flagged mismatch (graph vs no-graph)
- Segment 1: Correctly flagged mismatch (form vs statistics), but recovery strategy was wrong—tried navigation instead of form completion

**Category:** **Phase 3.11 — Action Inference**: Given the mismatch, ViBR inferred "navigate to the statistics screen" via back/graph-icon taps, rather than "complete the form that is currently visible."

### Tertiary: Phase 3.9 — Action Space Definition

**Issue:** ViBR's action vocabulary does not include intermediate user gestures during form entry:
- Tap to focus field (recognized)
- Type numeric/text content (not in execution loop)
- Close keyboard (not triggered)
- Tap next/submit button (conflated with final navigation)

ViBR's vocabulary is structured around navigation actions (tap, swipe, back, wait), not data-entry actions (type, fill field, scroll form).

---

## Impact Assessment

**Why full execution failed:**

1. **Segmentation error locked out form-filling:** ViBR never detected the form-filling steps as separate actions. Instead, it conflated 10 seconds of typing into the segment's "wait" state.

2. **State alignment cascaded to recovery failure:** Once ViBR reached segment 1's end state (statistics) in the reference video but saw a form on the device, all 3 recovery attempts failed because the recovery logic tried navigation (semantically wrong) instead of form completion.

3. **Action vocabulary mismatch:** ViBR predicted "wait" for segment 0 (correct conceptually) but had no way to execute "wait for graph to fully load after form submission." The expected next action (form-fill) was never detected.

4. **Zero actions executed:** Because no segment action was ever fully validated, ViBR skipped both segments and exited with 0/2 actions completed.

**Cascade effect:**
- Segmentation error → boundary misalignment
- Boundary misalignment → impossible state consistency
- Impossible state consistency → recovery exhausted
- Recovery exhausted → skip action, move to next segment
- Next segment inherits device state inconsistency from previous skip → repeat failure

---

## Conclusions

**Coverage:** 0% (0/5 steps executed)

**Dominant failure mode:** Over-grouping in segmentation phase. CLIP embedding similarity threshold (0.95) was insufficient to distinguish intermediate form-filling steps from the continuous form-entry scene.

**Underlying limitation:** 
1. **CLIP's visual grounding is layout-centric, not content-centric.** Text input changes (field focus, keyboard overlay, text content) do not produce large embedding shifts because the overall spatial layout (form structure) remains constant.
2. **Action vocabulary assumes navigation-based workflows.** Form-filling, data-entry, and text-input workflows require a different detection strategy (e.g., frame-to-frame keyboard state tracking, OCR-based field-value change detection).
3. **Segmentation algorithm static threshold (0.95) does not adapt to app-specific UI patterns.** Blood pressure monitor uses persistent forms with subtle state changes; a more sensitive threshold (0.85–0.90) or dynamic per-app threshold tuning would likely help.

**Remedies for future runs:**
- Reduce CLIP similarity threshold to 0.85–0.90 for form-heavy apps
- Add keyboard state tracking (appears/disappears) as a boundary signal
- Extend action vocabulary to include form interactions (type, submit)
- Implement OCR-based detection of field value changes
- Train a task-specific model for healthcare/data-entry app workflows

---

## TL;DR

| Aspect | Finding |
|--------|---------|
| **Status** | Failed completely (0/5 steps) |
| **Why** | CLIP over-grouped form-filling into single segment; segmentation boundary mismatch caused impossible state alignment; recovery logic exhausted after 3 attempts |
| **Stage** | Phase 1.4 (Scene Detection) — insufficient threshold sensitivity for data-entry workflows |
| **Bottom line** | Form-filling workflows with subtle keyboard/focus changes fall below CLIP's detection threshold; a more sensitive algorithm or task-specific thresholding is required |

