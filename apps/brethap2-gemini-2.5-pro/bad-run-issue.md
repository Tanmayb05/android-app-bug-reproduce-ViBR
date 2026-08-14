# ViBR Run Issue Analysis: brethap2 (bad-quality)

## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 03:19:08 | logger | Configuration loaded |
| 03:19:12 | model_api | Selected provider: gemini |
| 03:19:24 | check_video.orchestrator | Video HDR conversion completed, SDR BT.709 verified |
| 03:19:24 | __main__ | Starting video processing from bad-video.mp4 (algorithm=clip) |
| 03:19:24 | __main__ | Initializing ADB device controller |
| 03:19:28 | __main__ | Detecting stable segments |
| 03:20:00 | __main__ | CLIP similarity calculated; 1336 total frames, 2 segments detected |
| 03:20:00 | __main__ | Segment boundaries: [(0, 1229), (1233, 1334)] |
| 03:20:01 | __main__ | Processing segment 0/0 |
| 03:20:05 | dino_detection | Loading GroundingDINO model |
| 03:20:08 | dino_detection | Annotated DINO output saved |
| 03:20:17 | __main__ | Relevant regions identified: target_regions=[0], predicted_action=tap |
| 03:20:17 | __main__ | Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_0.png |
| 03:20:22 | __main__ | **State mismatch detected — attempting state alignment (try 1/3)** |
| 03:20:40 | __main__ | Recovery attempt 1: Tapped "Press Start" |
| 03:20:43 | __main__ | Comparing recovery state: reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_1.png |
| 03:20:49 | __main__ | **State mismatch persisted — attempting state alignment (try 2/3)** |
| 03:20:57 | __main__ | Recovery attempt 2: No action taken (screen mismatch too large) |
| 03:21:05 | __main__ | **State mismatch persisted — attempting state alignment (try 3/3)** |
| 03:21:31 | __main__ | Recovery attempt 3: Tapped "Press Start" again |
| 03:21:40 | __main__ | **Final failure: Skipped action due to GUI state mismatch** |
| 03:21:40 | __main__ | Video processing completed; Actions executed: 0 |

**Interpretation:** ViBR attempted to replay the breathing exercise workflow but encountered a fundamental segmentation failure at frame 0. The CLIP algorithm split the 23-second video into 2 segments, but the reference frame (segment 0 start) captured the *Sessions* screen with a "clear all" dialog, while the device at replay time showed the *main* screen with "Press Start" button. This mismatch prevented ViBR from executing any actions across 3 recovery attempts. The core issue is that the segmentation algorithm failed to identify the correct start frame of the first interactive scene, causing the entire replay workflow to abort before any actions executed.

---

## Executive Summary

- **Expected steps (from ground truth video):** 5 major steps
  1. Tap "Press Start" button on main screen
  2. Observe "Inhale" phase with countdown timer (0:01:56–0:01:58)
  3. Transition to "PreExhale" phase with timer countdown
  4. Navigate back to Sessions screen via back arrow
  5. View list of 3 saved sessions with management options

- **Executed steps (from run log):** 0
  - ViBR attempted to tap "Press Start" 3 times (recovery attempts 1, 2, 3)
  - All 3 attempts failed due to GUI state mismatch
  - **Gap:** 5 expected steps, 0 executed → 100% failure coverage

- **Status:** INCOMPLETE (0% execution success)
- **Dominant failure mode:** Action Segmentation — incorrect initial scene boundary detection

---

## Ground Truth vs Execution Log

| Step | Expected Action | Executed | Status | Issue Category |
|------|-----------------|----------|--------|-----------------|
| 1 | Tap "Press Start" button (main screen) | ✗ | Skipped | 1.4 (Scene Detection) |
| 2 | Wait during "Inhale" phase (0:01:56–0:01:58) | ✗ | Not attempted | Cascading failure |
| 3 | Phase transition to "PreExhale" (auto) | ✗ | Not attempted | Cascading failure |
| 4 | Press back button to Sessions screen | ✗ | Not attempted | Cascading failure |
| 5 | Observe Sessions list with 3 items | ✗ | Not attempted | Cascading failure |

---

## Video vs Log Comparison

| Frame Range | Segment | Log Shows | Video Shows | Gap |
|-------------|---------|-----------|-------------|-----|
| 0–1229 | Seg 0 | Reference = Sessions screen with "clear all" dialog | Main screen with "Press Start" button | **Critical mismatch** |
| 1233–1334 | Seg 1 | (Not processed) | Breathing exercise phases + Sessions navigation | Unreached due to Seg 0 failure |

**Hidden Actions Identified:**
- User manually navigates from Sessions screen (logged in reference frame) to main screen (device state during replay). This suggests the reference frame captured a *prior* state, not the initial state of the video sequence.

---

## Detailed Failure Analysis

### Step 1: Tap "Press Start" Button

**Expected behavior:** User should tap "Press Start" button on main screen to initiate breathing exercise.

**Log entries:**
```
[03:20:17] Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_0.png
[03:20:22] WARNING: Attempting to align state (try 1/3)...
[03:20:40] Recovery matched element: '' at (540, 960)
[03:20:40] [execute_action] [1] Tap on "Press Start". -> tap
[03:20:43] Comparing state (recovery attempt 1): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_1.png
[03:20:49] WARNING: Attempting to align state (try 2/3)...
[03:20:57] [execute_action] [1] The current screen does not match the screen from the recording, so no action can be taken. -> no action
[03:21:31] [execute_action] [1] Tap on 'Press Start' to begin the breathing exercise. -> tap
[03:21:40] WARNING: Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows a confirmation dialog with the title 'clear all' on a 'sessions' screen. the current image shows the main screen of the app with the text 'press start' and a play button. the two screens represent completely different parts of the application and have different functionalities.
```

**Mismatch reason:** The reference frame extracted at segment 0 captured the Sessions screen (with "clear all" dialog), not the main screen where "Press Start" appears. This is a fundamental segmentation error: CLIP misidentified the frame boundaries, causing segment 0 to start at the wrong scene.

**Root cause category:** **Phase 1, Stage 1.4 (Scene Detection)** — Incorrect grouping of frames. CLIP similarity threshold (0.95) failed to detect the transition from Sessions screen back to main screen within the video sequence. The algorithm grouped dissimilar scenes together, placing the Sessions screen at the start of segment 0 instead of identifying the main screen as the initial state.

**Cascade impact:** All 5 steps aborted. ViBR's state alignment mechanism detected the mismatch after 3 recovery attempts, each taking ~17 seconds, then gave up. Total delay: ~72 seconds of failed recovery attempts.

---

## Root Cause Categorization

### Phase 1: Action Segmentation Failures

#### Category 1.4: Scene Detection (1 failure)
- **Issue:** Incorrect initial scene boundary detected by CLIP
- **Evidence:** Segment 0 starts with Sessions screen frame instead of main screen frame
- **Cause:** CLIP similarity threshold (0.95) insufficient to detect screen transitions in breathing app. The app's color scheme and layout are relatively stable across scenes (dark UI, centered text), causing CLIP embeddings to merge dissimilar screens into single segment.
- **Impact:** 100% of workflow blocked; no actions executed.

#### Category 1.3: Similarity Computation (contributing factor)
- **Issue:** Fixed threshold (0.95) did not generalize to brethap2 UI patterns
- **Evidence:** False grouping of Sessions and main screens as single stable segment
- **Cause:** Breathing exercise apps have minimal visual change between screens (dark theme, simple centered layout). CLIP embeddings may treat "Sessions list" and "main screen" as minor variations of same scene.

---

## Impact Assessment

**Execution Status:** 0/5 steps completed (0% coverage)

**What prevented full execution:**
1. Incorrect scene segmentation placed Sessions screen at segment 0 start instead of main screen
2. ViBR detected state mismatch and invoked recovery mechanism
3. Recovery attempts (3 total) failed to align reference screen with live device state
4. Algorithm aborted after max retries exhausted

**Cascading failures:**
- Step 1 (tap) blocked → Step 2 (wait) not attempted → Step 3 (transition) not attempted → Step 4 (back) not attempted → Step 5 (observe) not attempted
- Recovery mechanism consumed 72+ seconds of LLM calls (9 total LLM calls over 151.6s) to detect and fail gracefully

---

## Conclusions

The brethap2 "bad" video replay failed entirely due to a **Stage 1 Action Segmentation failure** (CLIP scene detection). The video contained a complex multi-screen workflow (main screen → breathing exercise → sessions list), but CLIP's similarity-based segmentation incorrectly grouped the Sessions screen with the main screen, placing them in the same segment and causing the wrong reference frame to be extracted. This fundamental segmentation error cascaded into total replay failure, with zero actions executed despite ViBR's recovery mechanism attempting state alignment 3 times.

**Root limitation:** CLIP embeddings are not specialized for mobile UI segmentation and may conflate scenes with similar color schemes and layout patterns. The fixed 0.95 threshold is too high for apps with stable, minimalist interfaces (like brethap2's dark-themed breathing exercise UI). ViBR's state alignment recovery is robust but cannot overcome segmentation-level errors where the initial reference frame is fundamentally from the wrong scene.

**Recommendation for improvement:**
- Reduce CLIP similarity threshold for apps with minimal visual change (e.g., 0.85–0.90) to trigger more frequent scene boundaries
- Augment CLIP embeddings with activity/DOM-aware segmentation (e.g., detect screen transitions via accessibility metadata or motion estimation)
- Validate segment 0 reference frame semantically (e.g., confirm main app screen exists) before proceeding to replay

---

## TL;DR

- ✗ **Complete failure:** 0/5 steps executed
- ✗ **Root cause:** CLIP incorrectly segmented video, placing Sessions screen at segment 0 start instead of main screen
- ✗ **Category:** Phase 1.4 (Scene Detection) — false negative on screen transition detection
- ✗ **Recovery:** State alignment mechanism detected mismatch but could not recover; aborted after 3 attempts
- **Bottom line:** CLIP's fixed threshold inadequate for minimal-UI apps; scene detection requires more sensitive edge detection or alternative segmentation approach.
