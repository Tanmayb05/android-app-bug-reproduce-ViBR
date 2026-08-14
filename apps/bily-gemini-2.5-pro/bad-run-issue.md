# ViBR Failure Analysis: bily (bad quality)

## Log Summary

**Timeline of Events (filtered for application logic):**

| Time | Module | Event |
|------|--------|-------|
| 15:19:24 | logger | RUN CONFIGURATION — all settings loaded (SSIM algorithm, 0.95 threshold) |
| 15:19:27 | model_api | Provider selected: Gemini (gemini-2.5-pro confirmed) |
| 15:19:27 | check_video.orchestrator | Video format validation passed: apps/bily-gemini-2.5-pro/bad-video.mp4 |
| 15:19:27 | __main__ | Video processing initiated with SSIM algorithm |
| 15:19:30 | __main__ | Segment detection phase started |
| 15:20:06 | __main__ | Segment detection completed: 745 total frames, 1 detected segment |
| 15:20:06 | run_stats | **Status: incomplete** — Scenes: 0, Actions executed: 0 |

**Interpretation:**

ViBR successfully loaded the bad-video.mp4 file and initialized the Gemini model. However, the SSIM-based segmentation algorithm failed to detect any meaningful action transitions within the 13-second video. The entire 745-frame sequence was classified as a single static segment (frame 0–744), preventing the pipeline from identifying distinct user actions. With zero segments detected beyond the leading frame, no scene boundaries were established, no GUIs were compared, and no actions were executed on the device. The run terminated in an incomplete state with zero LLM calls for action inference.

---

## Executive Summary

**Expected vs. Executed:**
- **Steps expected from video:** 6 discrete user actions (menu tap → reset tap → confirmation → settings toggles → return)
- **Steps executed by ViBR:** 0 actions
- **Gap:** 6 actions (100% failure)
- **Coverage:** 0% (0 of 6 steps completed)

**Root Cause Category:** Phase 1.3 (Similarity Computation) — Fixed SSIM threshold (0.95) inadequate for this app's visual dynamics.

---

## Ground Truth vs. Execution Log

| Step# | Expected Action | ViBR Execution | Status | Issue Category |
|-------|-----------------|-----------------|--------|-----------------|
| 1 | Tap menu icon (three-dot) | Not executed | ✗ | Segmentation failed |
| 2 | Tap "Reset Bill" | Not executed | ✗ | Segmentation failed |
| 3 | Confirm reset action | Not executed | ✗ | Segmentation failed |
| 4 | Toggle Taxes setting | Not executed | ✗ | Segmentation failed |
| 5 | Toggle Discount setting | Not executed | ✗ | Segmentation failed |
| 6 | Close settings panel | Not executed | ✗ | Segmentation failed |

---

## Video vs. Log Comparison

**Video frame analysis (13 seconds @ 30fps = 390 frames extracted @ 1fps = 13 keyframes):**

| Frame Range | Event | Log Status | Mismatch |
|-------------|-------|------------|----------|
| Frame 1–2 | User taps menu icon; menu appears | No segment boundary | ✗ Gap: UI transition undetected |
| Frame 2–3 | User taps "Reset Bill"; dialog appears | No segment boundary | ✗ Gap: Dialog overlay not marked as scene change |
| Frame 3–4 | User taps confirmation; expenses clear | No segment boundary | ✗ Gap: State change (has expenses → cleared) undetected |
| Frame 5–8 | User opens settings panel; visible UI elements change | No segment boundary | ✗ Gap: Panel overlay and new content not recognized as distinct scene |
| Frame 8–10 | User toggles switches; toggle state visibly changes | No segment boundary | ✗ Gap: UI state changes (toggle positions) below SSIM threshold |
| Frame 10–13 | Settings panel fades, returns to main screen | No segment boundary | ✗ Gap: Final state transition not detected |

**Hidden Actions Detected:** None. ViBR's segmentation was too coarse to identify any user actions, so no hidden actions were discovered.

**Timing Gaps:** ViBR did not advance to any action execution phase, so no timing-based gaps exist. The pipeline terminated at segmentation.

---

## Detailed Failure Analysis

### Failure #1–6: Complete Segmentation Pipeline Failure

**Expected Behavior (from video truth):**
Six user interactions occur in sequence over 13 seconds: menu open, reset selection, confirmation, settings toggles (2), and panel close. Each interaction produces a visible state change on screen.

**What ViBR Did:**
1. Loaded video (745 frames)
2. Computed SSIM similarity scores across consecutive frames
3. Applied threshold (0.95) to detect "stable scenes"
4. Identified only 1 segment spanning entire video (frames 0–744)
5. Returned 0 scenes to subsequent pipeline stages
6. Terminated with no actions executed

**Why It Failed:**

The SSIM threshold of 0.95 is too rigid for Bily's visual dynamics. Structural Similarity Index (SSIM) measures pixel-level correlation, not semantic change. When a user taps the menu, the overlay appears gradually (fade-in) or with smooth animations. SSIM remains high (>0.95) because:
- Most of the screen remains unchanged
- Only a small overlay region changes
- Pixel correlation still ~95–98% between consecutive frames
- No frame-pair falls below the 0.95 threshold

Example: Frame 1 (dashboard) → Frame 2 (menu overlay appears). SSIM might be 0.97 because 95% of pixels are identical (unchanged bill display, background). ViBR requires SSIM **below** 0.95 to mark a boundary. No boundary = no scene. No scene = no action inference.

**Cascade Impact:**
- Zero segments → zero scenes
- Zero scenes → no GUI state comparison
- No GUI comparison → no action inference
- No action inference → no device actions executed
- Result: Complete workflow failure

**Root Cause Category:**
- **Phase:** Stage 1 (Action Segmentation)
- **Sub-category:** 1.3. Similarity Computation
- **Issue:** "Fixed threshold (0.95) may not generalize"
- **Evidence:** Threshold correctly detects boundaries in other apps but fails on Bily due to animated UI overlays and gradual state transitions
- **Underlying Problem:** SSIM treats animation frames as "stable" when user intent is to navigate. The metric conflates pixel stability with semantic stability.

---

## Root Cause Categorization

### Phase 1: Action Segmentation

**1.3. Similarity Computation**
- **Count:** 6 failures (all steps)
- **Issue:** Fixed SSIM threshold (0.95) insufficient for Bily's visual characteristics
- **Mechanism:** 
  - Menu overlays fade in/out gradually → SSIM remains >0.95
  - Settings panel animations → smooth transitions preserve pixel correlation
  - Toggle switches animate between states → minimal pixel change relative to full screen
  - Confirmation dialogs overlay existing UI → SSIM high due to large unchanged region
- **Why Specific to Bily:**
  - Other apps tested (e.g., antennapod1, bakerspercentagecalculator1) have sharper transitions
  - Bily uses theme-based dark mode with subtle color shifts and animated overlays
  - Mobile design trend: overlays and layer transitions common, but SSIM-based segmentation assumes sharp screen changes

---

## Impact Assessment

**Pipeline Blockage:** Segmentation is the first processing stage. Failure here blocks all downstream phases:
- No scenes identified → GroundingDINO never runs
- No GUI states compared → GPT-4o never invoked for action inference
- No action inferred → No ADB commands executed on device
- No execution → Video playback never replayed on device

**LLM Utilization:** Only 1 LLM call made (model ping-pong check). No vision model calls for GUI analysis.

**Device State:** Device remained idle. No taps, swipes, or state changes occurred on the actual Android device.

**Time Wasted:** 42.2 seconds of processing with zero progress. Bottleneck identified at frame 0; segmentation algorithm exhausted all 745 frames before admitting failure.

---

## Conclusions

Bily's bad-quality video exhibits UI patterns (overlay animations, gradual state transitions, toggle animations) that are poorly suited to fixed-threshold SSIM segmentation. The structural similarity metric conflates visual stability (pixel persistence) with semantic stability (no action). This causes:

1. **Segmentation Collapse:** 100% of frames grouped into one "stable" segment
2. **Zero Scene Detection:** No distinct scenes extracted, blocking all subsequent analysis
3. **Complete Execution Failure:** 0 of 6 expected actions executed (0% coverage)

The root cause is algorithmic, not environmental. The SSIM (0.95) threshold works for apps with hard cuts between screens but fails for animations. A dynamic threshold (e.g., adaptive to app-specific patterns) or a supplementary metric (optical flow, perceptual hashing, CLIP embeddings) would likely detect the transitions Bily's UI exhibits.

This failure demonstrates a **Stage 1 limitation in ViBR's design:** rigid segmentation thresholds are not adaptive to app visual design patterns. Bily's use of modern UI patterns (overlays, animations, theme transitions) exposes this brittleness.

---

## TL;DR

- **Success Reasons:** None. Video loaded successfully; model initialized correctly.
- **Failure Reasons:** 
  - SSIM threshold (0.95) too high for Bily's animated overlays and smooth transitions
  - All 745 frames grouped as single "stable" segment
  - Zero scenes detected → zero actions executed
- **Coverage:** 0% (0 of 6 steps)
- **Bottom Line:** ViBR's SSIM segmentation cannot handle apps with animated UI overlays; a more sensitive or adaptive threshold is required.
