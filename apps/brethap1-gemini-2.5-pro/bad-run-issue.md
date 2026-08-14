# Brethap1 Bad-Run Failure Analysis

## Log Summary

Filtered event timeline (after GroundingDINO load):

| Time | Module | Event |
|------|--------|-------|
| 02:47:44 | dino_detection | Annotated DINO output saved |
| 02:48:09 | __main__ | Relevant regions detected; GPT selected regions [2]; action=tap |
| 02:48:09 | dino_detection | Relevant-only annotation saved |
| 02:48:16 | __main__ | **Attempting to align state (try 1/3)** |
| 02:48:32 | __main__ | Recovery matched element at (540, 960); Tap hamburger menu icon (top left) |
| 02:48:34 | __main__ | Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_1.png |
| 02:48:40 | __main__ | **Attempting to align state (try 2/3)** |
| 02:48:54 | __main__ | Recovery matched element at (540, 960); Tap hamburger menu icon (top left) |
| 02:48:56 | __main__ | Comparing state (recovery attempt 2): reference vs live |
| 02:49:02 | __main__ | **Attempting to align state (try 3/3)** |
| 02:49:16 | __main__ | Recovery matched element at (540, 960); Tap hamburger menu icon (top left) |
| 02:49:18 | __main__ | Comparing state (recovery attempt 3): reference vs live |
| 02:49:25 | __main__ | **SKIPPING ACTION**: GUI state does not match. Reference = sessions screen with past sessions list; current = main start screen with 'Press Start' prompt and timer |
| 02:49:25 | run_stats | Status: incomplete; Actions executed: 0; LLM calls: 9 |

**Interpretation:** ViBR detected one action in the bad video (tapping hamburger menu), but the reference screenshot showed Sessions screen, while device showed Start screen. Three alignment retry attempts all failed. ViBR conservatively skipped the action due to safety check: "current state ≠ expected state, cannot safely proceed." This is the correct behavior for a replay agent, but it reveals the root bug: **action segmentation error in Phase 1**.

---

## Executive Summary

- **Expected steps (from ground truth):** 8 steps (tap Start, breathing, pause, tap Start again, breathing, tap menu, navigate Sessions, idle)
- **Executed steps:** 0 actions on device
- **Coverage:** 0% (0/8 steps)
- **Gap count:** 8 steps missed
- **Status:** Incomplete replay; safety abort

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed ✓/✗ | Status | Issue Category |
|--------|-----------------|-------------|--------|-----------------|
| 1 | Tap 'Press Start' button to start breathing | ✗ | Not attempted | 1.4 Scene Detection |
| 2 | Wait for breathing exercise (Inhale/Exhale cycles) | ✗ | Not attempted | 1.4 Scene Detection |
| 3 | [Auto] Return to start screen | ✗ | Not attempted | 1.4 Scene Detection |
| 4 | Tap 'Press Start' again to restart | ✗ | Not attempted | 1.4 Scene Detection |
| 5 | Wait for second breathing session | ✗ | Not attempted | 1.4 Scene Detection |
| 6 | Tap hamburger menu icon (≡) | ✗ Attempted 3x | Skipped (state mismatch) | **2.7 State Consistency Check** |
| 7 | Navigate to Sessions screen | ✗ | Not attempted | 2.7 State Consistency Check |
| 8 | View sessions history | ✗ | Not attempted | 2.7 State Consistency Check |

---

## Video vs Log Comparison

**Video Timeline (Ground Truth):**

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 1-2 | Start screen → Press Start | (no log, pre-segmentation) | Start screen, timer 0:02:00 → Inhale instruction | **YES** — ViBR never segmented this action |
| 2-7 | Breathing exercise (Inhale/Exhale) | (no log, pre-segmentation) | Animated circle, timer countdown 0:01:59→0:01:54 | **YES** — breathing phase missed entirely |
| 8 | Screen returns to start | (no log) | Press Start button, timer reset to 0:02:00 | **YES** — transition missed |
| 8-11 | Second "Press Start" tap + breathing restart | (no log) | Start screen → Inhale/Exhale visible | **YES** — second action not segmented |
| 17-19 | Hamburger menu tap → drawer opens | ViBR attempted, skipped | Drawer with menu items (Preferences, Sessions, Calendar, About Brethap) visible | **PARTIAL** — ViBR detected action but rejected it |
| 20-23 | Sessions screen navigation + view | (no log) | Sessions header, past session list visible | **YES** — never reached |

**Hidden Actions (not executed by ViBR but present in video):**
- Frame 1→2: Tap "Press Start" (invisible to segmentation; likely merged into breathing animation)
- Frame 8→11: Return to start + second "Press Start" tap (missed as separate segment)
- Frame 17+: Tap menu + navigate Sessions (detected but rejected due to state mismatch)

---

## Detailed Failure Analysis

### Failure 1: Segmentation Missed First Action (Frames 1-2)

**Expected:** Tap "Press Start" button at start of video
**Video Shows:** Button visible, then immediately changes to Inhale instruction
**Log Shows:** No action segmentation for this step
**Root Cause (Category 1.3 or 1.4):** The "Press Start" tap may have been too brief or overlapped with animation transition:
- Phase 1 (CLIP) likely failed to detect stable boundary before/after tap
- High similarity between start screen and breathing instruction screen confused scene boundary detection
- **Cascading impact:** Without detecting first action, all downstream steps are orphaned

### Failure 2: Entire Breathing Phase Not Segmented (Frames 2-7)

**Expected:** Wait/play breathing animation cycle
**Video Shows:** 5+ seconds of Inhale, small circle expansion, Exhale, contraction, timer countdown
**Log Shows:** No step generated for this segment
**Root Cause (Category 1.2 or 1.4):** 
- Breathing animation creates **dynamic content** (animated circle) that may confuse CLIP embeddings
- CLIP not trained on mobile animations; may embed similar frames too closely
- Stable similarity threshold (0.95) may be too high/low for animation frames
- **Cascading impact:** Breathing segment lumped with Start screen or merged incorrectly

### Failure 3: Screen Return & Pause Not Detected (Frames 8-10)

**Expected:** Auto-transition back to start screen (app behavior)
**Video Shows:** Breathing screen → Start screen, timer reset
**Log Shows:** No transition logged
**Root Cause (Category 2.5 or 2.8):** 
- App internally paused exercise; no user action triggered
- ViBR segments based on user interactions; auto-transitions may be invisible to segmentation
- XML parsing may not capture intermediate states during rapid transitions

### Failure 4: Recovery Matched Wrong Region (State Mismatch)

**Expected:** Tap hamburger menu on Sessions screen
**Log Shows:** ViBR detected action (tap at 540, 960) but found Sessions screen reference, device showed Start screen
**Video Shows:** At Frame 17, menu opens; hamburger icon is in header of **breathing exercise screen** (frame ~17), not start screen
**Root Cause (Category 2.7 — State Consistency Check):**
- **Critical Bug:** ViBR's first detected segment expected the **Sessions screen** (end state), not the **Start screen** (initial state)
- This suggests Phase 2 (GUI state comparison) misidentified which screen was the "reference" for the first segment
- GroundingDINO + GPT-4o may have hallucinated or mis-anchored the reference region
- Device showed Start screen → ViBR's expected Sessions screen → **state mismatch → safety abort**
- **Why?** ViBR likely tried to replay the last (Sessions screen) action as the first step, due to incorrect frame-to-action mapping in Phase 1

---

## Root Cause Categorization

### Phase 1: Action Segmentation Failures (Primary)

| Sub-Category | Issue | Evidence | Count |
|--------------|-------|----------|-------|
| **1.2 CLIP Embedding** | Animated breathing circle confuses similarity computation | Breathing phase (Frames 2-7) produces continuous stream but no boundary detected | 1 |
| **1.4 Scene Detection** | Missed initial tap + subsequent transitions | Start→Inhale, Pause→Start, Start→Sessions not segmented as separate scenes | 3 |
| **Threshold sensitivity** | Fixed 0.95 threshold may not generalize to animation + app transitions | No frame clustering detected for dynamic content | 1 major |

### Phase 2: GUI State Comparison Failures (Secondary)

| Sub-Category | Issue | Evidence | Count |
|--------------|-------|----------|-------|
| **2.7 State Consistency Check** | Reference/current state mismatch; expected Sessions, got Start | ViBR attempted action 3 times, each time state diff was "Sessions screen vs Start screen" | 1 critical |
| **2.5 Region Detection** | GroundingDINO may have over-detected or hallucinated region in reference image | Recovery fallback matched element at (540, 960) which is incorrect for hamburger tap | 1 |

---

## Impact Assessment

**Why Full Replay Failed:**

1. **Segmentation broke early:** Frames 1-7 produced no actionable segments due to animation + transition confusion
2. **First detected segment corrupted:** ViBR's Phase 2 expected a Sessions screen as the start reference, but device showed Start screen
3. **Safety prevented blind execution:** Rather than tap blindly at wrong coordinates on wrong screen, ViBR correctly aborted after 3 retry attempts
4. **Cascading failures:** No action executed → entire workflow orphaned

**What Prevented Success:**

- CLIP model poor at detecting boundaries near animations
- Threshold (0.95) not adaptive across app domains
- State reference misidentification in first segment (may be GroundingDINO or frame-to-action mapping bug)
- No recovery strategy beyond coordinate-based fallback

---

## Conclusions

Brethap1 bad-run exhibits a **Phase 1 (Action Segmentation) failure with secondary Phase 2 (State Consistency) abort.** The breathing animation and rapid screen transitions confuse CLIP's similarity computation, leading to incorrect frame grouping. When ViBR attempted the one detected action (hamburger tap), the reference screen (Sessions) mismatched the device state (Start), triggering a conservative safety skip.

**Key finding:** The app's **dynamic animated content** (breathing circle) is a known limitation of CLIP-based segmentation (documented in ViBR paper Category 1.2). Additionally, **auto-state transitions** (app pausing exercise and returning to start) are not user-driven and fall outside ViBR's action-based segmentation model.

**Coverage:** 0% (0 of 8 steps executed)

**Dominant failure mode:** Segmentation boundaries lost during animation → reference state misidentification → safety abort

**Underlying limitation:** CLIP embeddings insufficient for apps with sustained animations and rapid, auto-triggered state changes.

---

## TL;DR

- ✗ **Breathing animation**: CLIP failed to segment animated circle frames (Category 1.2 — embeddings drift during animation)
- ✗ **Auto-transition**: App-initiated pause/return to start not captured (falls outside user-action-based model)
- ✗ **Reference state mismatch**: First detected segment expected Sessions screen but device showed Start screen; 3 retries failed
- ✗ **Result**: 0 actions executed; safety check prevented blind execution
- **Root:** Segmentation boundary collapse → state reference corruption → safety abort
- **Bottleneck:** CLIP model not robust to mobile animations + rapid self-driven state changes

