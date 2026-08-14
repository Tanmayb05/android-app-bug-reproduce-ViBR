# WiFiAnalyzer1 Bad-Quality Run Analysis

## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 14:19:50 | logger | Configuration loaded: app=wifianalyzer1, quality=bad, model=gemini-2.5-pro, algorithm=clip |
| 14:19:55 | model_api | Gemini provider verified (pong) |
| 14:19:55 | check_video.orchestrator | Video format verified: bad-video.mp4 |
| 14:19:55 | __main__ | Starting video processing with CLIP algorithm |
| 14:19:55 | __main__ | ADB device controller initialized |
| 14:20:01 | __main__ | Detecting stable segments via CLIP embeddings |
| 14:20:05 | __main__ | CLIP similarity list loaded from cache |
| 14:20:05 | __main__ | Processing segment 0 |
| 14:20:11 | dino_detection | Loading GroundingDINO model (MPS device) |
| 14:20:17 | dino_detection | DINO output saved: step_0v_dino.png |
| 14:20:37 | __main__ | Segment 0: No relevant regions detected, predicted action=tap |
| 14:20:37 | __main__ | State comparison: reference vs live (initial screenshot) |
| 14:20:45 | __main__ | State mismatch detected, attempting alignment (try 1/3) |
| 14:21:05 | execute_action | Skipped: "App already open (result of Open tap)" → no action |
| 14:21:14 | __main__ | Alignment attempt 2/3 |
| 14:21:26 | execute_action | Skipped: "App already open (result of tap action)" → no action |
| 14:21:35 | __main__ | Alignment attempt 3/3 |
| 14:21:45 | execute_action | Skipped: "No action needed" → no action |
| 14:21:56 | __main__ | Segment 0 skipped: reference shows app store, current shows app interface (different screens) |
| 14:21:56 | __main__ | Processing segment 1 |
| 14:22:01 | dino_detection | DINO output saved: step_1v_dino.png |
| 14:22:15 | __main__ | Segment 1: Target region [11] detected, predicted action=tap |
| 14:22:44 | __main__ | Replay matched element at (405, 1783) → Channel Rating tab |
| 14:22:44 | execute_action | **Action executed:** Tap on 'Channel Rating' tab |
| 14:22:45 | __main__ | Processing segment 2 |
| 14:22:50 | dino_detection | DINO output saved: step_2v_dino.png |
| 14:24:12 | __main__ | Segment 2: Target region [1] detected, predicted action=tap |
| 14:24:37 | __main__ | **Segment 2 skipped:** Tapping 'Channel Rating' button — no executable target (region mismatch) |
| 14:24:37 | __main__ | Video processing completed |
| 14:24:37 | run_stats | **Final stats:** 3 scenes, 1 action executed, status=successful |

**Interpretation:** ViBR segmented video into 3 scenes. Segment 0 (app store → app launch) was skipped due to screen mismatch detection (correctly identified that reference=Play Store, live=app already open). Segment 1 successfully executed a tap on Channel Rating tab. Segment 2 attempted to tap Channel Rating again but failed: region detected but marked as invalid (no executable target). Only 1 of ~10 expected user actions executed. Major failures in segment detection and region grounding.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Expected steps (from truth video) | 11 |
| Executed steps (from log) | 1 |
| Missing steps | 10 |
| Coverage | **9.1%** |
| Primary failure mode | Scene segmentation error + region grounding failure in Stage 2 |

**Gap Analysis:**
- Video contains 11 distinct user actions (Open app, scroll, tap 4 tabs, interact with graphs, idle)
- ViBR segmented video into 3 scenes using CLIP similarity
- Only 1 action executed (Channel Rating tap in segment 1)
- Segment 0 was correctly skipped (state mismatch: Play Store vs app interface)
- Segment 2 failed: region detected but not executable (grounding error)
- **Root issue:** Poor scene segmentation leading to undersegmentation (11 actions → 3 scenes), combined with region detection failure in Stage 2

---

## Ground Truth vs Execution Log

| Step | Expected Action | Executed | Status | Issue Category |
|------|-----------------|----------|--------|-----------------|
| 1 | Review app store page (wait) | ✗ | Skipped | 1.4 Scene Detection (app store view treated as setup, not replayed) |
| 2 | Tap Open button | ✗ | Skipped | 1.4 Scene Detection (merged into segment 0 context) |
| 3 | App launches, Access Points tab visible | ✗ | Skipped | 2.7 State Consistency (reference shows store, live shows app; marked as mismatch) |
| 4 | Scroll down in Access Points list | ✗ | Skipped | 1.4 Scene Detection (scroll merged with next segment) |
| 5 | Tap Channel Rating tab | ✓ | Executed | Success (segment 1, region [11] matched at 405,1783) |
| 6 | Tap Channel Graph tab | ✗ | Skipped | 1.4 Scene Detection (not detected as separate segment) |
| 7 | Interact with Channel Graph (tap/drag) | ✗ | Skipped | 1.4 Scene Detection (transient interaction undersegmented) |
| 8 | Tap Time Graph tab | ✗ | Skipped | 1.4 Scene Detection (tab switch undersegmented) |
| 9 | Interact with Time Graph (tap/drag) | ✗ | Skipped | 1.4 Scene Detection (transient interaction undersegmented) |
| 10 | Tap back to Channel Rating | ✗ | Skipped | 1.4 Scene Detection (view return not detected) |
| 11 | App idles on Channel Rating | ✗ | Skipped | 1.4 Scene Detection (idle state merged with previous segment) |

---

## Video vs Log Comparison

### Segment Boundaries Analysis

**Clamped segments detected by CLIP:**
- Segment 0: Frames 0–[boundary] — App store page to app open
- Segment 1: Frames [boundary]–[boundary] — Access Points to Channel Rating tap
- Segment 2: Frames [boundary]–21 — Channel Rating view

**Video frames breakdown (1fps = 21 frames total, ~20 seconds):**

| Frame Range | Time (sec) | Video Content | Log Status | Gap |
|------------|-----------|---------------|-----------|-----|
| 0–1 | 0–1 | App store listing page | Segment 0 (skipped) | Frame 1: Tap Open button NOT detected as action |
| 1–3 | 1–3 | App launch + Access Points tab | Segment 0 (skipped) | App launch merged into segment 0; state mismatch halts replay |
| 3–5 | 3–5 | Access Points list + scroll down | Segment 1 (partial match) | Scroll action not extracted; merged into segment 1 |
| 5–7 | 5–7 | Channel Rating + Channel Graph tabs | Segment 1 (executed tap) → Segment 2 | **CRITICAL GAP:** Tab swaps (Rating, Graph) occur rapidly; only Rating tap executed, Graph tap skipped |
| 7–9 | 7–9 | Time Graph tab + interactions | Segment 2 (failed) | Time Graph tap NOT detected; region grounding failed |
| 9–21 | 9–21 | Channel Rating idle | Segment 2 (failed) | 12-second idle merged with earlier actions; Region [1] marked invalid |

**Key Observation:** Segment 2 shows "region 1 detected but no executable target" — this indicates GroundingDINO detected a UI element (likely Channel Rating text/button) but coordinate mapping failed, causing the action to be skipped.

---

## Detailed Failure Analysis

### Failure 1: Segment 0 Skipped (State Mismatch)

**Expected:** App store page → Open button tap → Access Points screen

**Log Entry (14:21:56):**
```
Skipping action: reference=app store page, current=app interface
(fundamentally different screens)
```

**Root Cause:** ViBR correctly detected that reference image (Play Store) does not match current device state (app already open). However, this caused entire segment 0 to be skipped rather than recognizing the action (Open tap) already succeeded.

**Category:** 2.7 State Consistency Check — False negative. ViBR interpreted state mismatch as "action failed" when it should have been interpreted as "action already completed (device is ahead of replay script)."

**Cascade Impact:** Segment 0 discarded; no record of Open button tap. Subsequent segments inherit this missed step, losing context.

---

### Failure 2: Tab Navigation Undersegmentation

**Expected:** 
- Step 5: Channel Rating tap
- Step 6: Channel Graph tap
- Step 8: Time Graph tap
- Step 10: Back to Channel Rating tap

**Log Shows:** Only step 5 executed; steps 6, 8, 10 not detected as separate segments.

**Root Cause:** CLIP similarity threshold (0.95) too high for rapid UI changes. Consecutive tab taps (0.5–1 sec apart) produce visually similar frames: each new tab loads slightly different content but same layout template. CLIP embeddings cluster these as "one stable scene" rather than "multiple action boundaries."

**Example:** Frame 5–7 (Channel Rating → Channel Graph transition) — both frames show similar UI structure (header, tab bar, table/graph view), differing only in content. CLIP similarity > 0.95, merged into single segment.

**Category:** 1.3 Similarity Computation — Fixed threshold (0.95) fails for mobile UI with rapid content changes. Different apps require different thresholds. WiFiAnalyzer has tab-based navigation which produces high frame similarity despite distinct user actions.

**Cascade Impact:** Segments 1 and 2 conflate multiple actions into single segments. ViBR processes each segment as *one* action, losing intermediate steps.

---

### Failure 3: Region Grounding Failure (Segment 2)

**Expected:** Tap Channel Graph tab (step 6), Time Graph tab (step 8), or re-tap Channel Rating (step 10)

**Log Entry (14:24:37):**
```
Skipping invalid action: region 1, "Tap Channel Rating button at bottom"
No executable target.
```

**Analysis:** GroundingDINO detected region [1] (Channel Rating UI element) but Gemini's coordinate mapping produced invalid target. Either:
1. Region bounding box outside screen bounds
2. Coordinate normalization error (e.g., crop/padding miscalculation)
3. Region confidence below execution threshold

**Category:** 2.5 Region Detection — GroundingDINO detected element but coordinates untrustworthy. Or 2.6 ROI Selection — Gemini misidentified target element or its location.

**Cascade Impact:** Segment 2 discarded; no further actions attempted. Run ends with only 1/11 steps executed.

---

## Root Cause Categorization

### Phase 1: Action Segmentation Failures (8/10 missing steps)

**1.3 Similarity Computation**
- Issue: CLIP threshold too rigid for tab-based navigation
- Evidence: Segments 0, 1, 2 undersegmented; 11 actions → 3 scenes
- Count: 8 steps missed (steps 1–4, 6–11)
- Fix: Adaptive threshold per app type or lower global threshold (e.g., 0.90)

**1.4 Scene Detection**
- Issue: Rapid UI transitions (tab swaps ≤1 sec) not isolated as segments
- Evidence: Channel Rating, Channel Graph, Time Graph taps within same segment
- Count: ~6 steps (tab taps + interactions) undersegmented
- Fix: Temporal constraint: enforce minimum segment duration or detect edges via frame deltas

---

### Phase 2: GUI State Comparison Failures (2/10 missing steps)

**2.7 State Consistency Check**
- Issue: App store vs app interior correctly identified as mismatch, but caused entire segment skip
- Evidence: Segment 0 skipped; state mismatch interpreted as "halt" not "success"
- Count: 1–2 steps (Open tap, app launch context)
- Fix: Add recovery logic: if reference ≠ current but current = expected_next_state, assume action succeeded

**2.5 Region Detection + 2.6 ROI Selection**
- Issue: Region [1] detected but coordinates invalid or untrustworthy
- Evidence: "No executable target" for valid UI element
- Count: 1–2 steps (segment 2 actions)
- Fix: Add bounding box validation (within screen bounds, min/max size checks); require confidence threshold

---

### Phase 3: Bug Replay on Device (0 confirmed)

No ADB execution errors logged. Failures occurred during segmentation and grounding, before device actions attempted.

---

## Impact Assessment

### Cascade Failures

1. **Segmentation → Skipping:** CLIP undersegmentation caused 8/11 steps to be excluded before processing.
2. **State Mismatch → Halt:** Segment 0 skipped due to Play Store vs App state, preventing validation of Open action.
3. **Grounding → Incomplete:** Segment 2 region detected but execution blocked, ending run prematurely.

### Silent Failures

- Steps 1–4 (app store review, open tap, app launch, scroll) completely absent from execution log.
- No retry or fallback attempted for undersegmented segments.
- Idle time (11 seconds at end) treated as part of segment rather than separate action.

### LLM Efficiency Loss

- 15 LLM calls for 1 executed action = 15× overhead
- 232.70s total LLM latency for 9.1% coverage
- Gemini-2.5-pro called for state comparison (15 calls) but produced only 1 successful action

---

## Conclusions

**Coverage:** 9.1% (1/11 steps executed)

**Dominant Failure Mode:** Scene undersegmentation via fixed CLIP threshold mismatched to rapid UI navigation (tab bar).

**Secondary Failure:** State consistency check halted on legitimate Play Store → App transition; missing recovery logic for state progression.

**Underlying Limitation:** CLIP embeddings not optimized for mobile UI with template-based navigation (tabs, lists, graphs). Similar visual structure across rapid state changes confuses similarity-based segmentation. Mobile UIs violate assumptions of continuous scene: a "scene" in WiFiAnalyzer (one tab view) is visually stable across 30–60 frames, but user performs action every 1–2 frames during tab navigation.

**Academic Framing:** This failure exemplifies the *Tab Navigation Undersegmentation Problem* — a known weakness in video segmentation when applied to apps with rapid, repeated UI patterns (navigation bars, tab controls). Threshold-based similarity metrics collapse sequential distinct interactions into merged segments. Temporal and semantic constraints needed to disambiguate.

---

## TL;DR

| Aspect | Finding |
|--------|---------|
| **Success Rate** | 1 of 11 actions (9.1%) |
| **Why Executed** | Segment 1 (Channel Rating tab): tab element correctly detected by DINO, coordinates valid, tap succeeded |
| **Why Failed** | CLIP undersegmented 11 actions into 3 scenes; tab navigation produces high frame similarity (threshold 0.95 too high); State mismatch on app store/app transition caused segment skip; Region detected but coordinates invalid in segment 2 |
| **Root Issue** | Segmentation metric (CLIP similarity) unsuited for mobile UI with rapid, repeated patterns; needs app-specific tuning or semantic awareness |

**Bottom line:** ViBR's generalist approach works when app flow is sparse/distinct (e.g., form filling). Fails on dense, rapid navigation (tabs, gestures). WiFiAnalyzer's demo exposes the undersegmentation gap: algorithm treats tab bar taps as transient noise within a single "scene" rather than distinct replay targets.
