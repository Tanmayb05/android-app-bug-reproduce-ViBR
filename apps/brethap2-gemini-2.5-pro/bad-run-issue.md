# ViBR Run Analysis: brethap2 (bad run)

## Executive Summary

**Ground Truth:** Unable to establish (no good-quality reference run available)
**Actually Executed:** 0 actions
**Status:** Complete failure — no actions executed; ViBR terminated after 1 segment

Bad run recorded video with severe quality degradation. ViBR detected a "tap" action but all 3 recovery attempts failed due to fundamental GUI state mismatch between video content and device state. Framework terminated workflow.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 0 | Initial screen state detection | ✗ | Failed | Screen Recording Artifact |

**Context:** No comparison point exists. Bad run is sole execution record for brethap2.

---

## Video vs Log Comparison

### Video Quality Issue (Primary Blocker)

**Video source:** Recorded via camera pointing at physical Android device (not clean screen capture)
- Frames 1–23 show hand, physical device edges, ambient lighting
- Screen content extremely dark; difficult to parse visually
- Timestamp overlay visible in frames (0:01:58 countdown visible at frame 12)
- Significant visual noise from camera recording environment

### Segment Detection

- Raw segment boundaries: `[(0, 1229), (1233, 1334)]`
- Clamped boundaries: `[(0, 1229), (1233, 1334)]` — 1229 frames in segment 0, 101 frames in segment 1
- CLIP algorithm detected 2 segments from ~1336 total frames
- However, extracted 1fps timeline = 23 seconds of usable video content
- **Discrepancy:** Log shows "total segments: 2" but only segment 0 processed

### Frame Timeline vs Log Events

| Frame Range (approx) | Segment | Log State | Video Shows | Alignment |
|---|---|---|---|---|
| 1–5 | Seg 0 start | Initial screenshot taken | Dark screen, hand visible | ⚠️ Mismatch |
| 6–12 | Seg 0 mid | DINO detection, action inference | Countdown timer visible (0:01:58) | ✓ Partial |
| 13–23 | Seg 0 end | Recovery attempts (3 retries) | Dark, unclear transitions | ⚠️ Corrupted |

---

## Detailed Failure Analysis

### Step 0: Initial Action Execution — FAILED

**Expected behavior (from video segmentation):**
ViBR detected "tap" action on region 0. Goal: replicate action seen in video onto live device.

**What the log shows:**
```
[2026-06-12 03:20:17] [__main__] Relevant regions: {'target_regions': [0], 'predicted_action': 'tap'}
[2026-06-12 03:20:17] [__main__] Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_0.png
[2026-06-12 03:20:22] [WARNING] [__main__] Attempting to align state (try 1/3)...
```

**Device state (screenshot_0):**
- Clean screen showing "Press Start" button (breathing timer app)
- Blue header bar with "Brethap" title
- Timer display: 0:02:00
- Blue play button (FAB) visible at bottom

**Video reference state (step_0v_tmp_stop.png):**
- Extremely dark, noisy frame
- Barely discernible UI elements
- Appears to show dialog or overlay, but text/buttons unclear
- Visual quality too poor for reliable element matching

**Critical mismatch:**
After execution attempt, device state remained at "Press Start" screen (screenshot_1, screenshot_2, screenshot_3 identical to screenshot_0). This indicates:
1. ViBR's tap target did not match actual device button location
2. OR the tap executed but the device was in different state than video showed
3. OR the video and device were showing different parts of the app entirely

**Log evidence of mismatch (recovery attempt 2):**
```
[2026-06-12 03:21:40] [WARNING] [__main__] Skipping action: current GUI state does not match start state. Mismatch reason: the reference image shows a confirmation dialog with the title 'clear all' on a 'sessions' screen. the current image shows the main screen of the app with the text 'press start' and a play button. the two screens represent completely different parts of the application and have different functionalities.
```

**Interpretation:** LLM analysis reveals catastrophic semantic gap—video reference shows "Sessions" screen (admin/clear-all dialog), but device is stuck on main "Press Start" (breathing exercise) screen. These are fundamentally different app features.

---

## Root Cause Analysis

### Primary Issue: Screen Recording Artifact (Stage 2 — GUI State Comparison)

**Category:** Screen recording artifact + resolution/quality mismatch

**Evidence:**
- Bad video recorded via camera → severe compression, noise, dark frames
- Device screenshots clear and readable (proper ADB screencap)
- Video frames difficult to parse visually; UI elements obscured
- DINO detection and Gemini vision models struggled with dark/noisy input

**Why it matters:**
ViBR depends on visual similarity matching to align video frames with device state. When video quality degrades:
1. Segmentation becomes unreliable (still detected 2 segments but quality poor)
2. Action region detection loses precision (DINO detections less reliable on dark input)
3. State matching fails (LLM cannot confidently map video regions to device UI)
4. Recovery cascades fail (3 retries all failed due to fundamental mismatch)

### Secondary Issue: Potential App State Divergence

**Category:** Semantic gap (Stage 3 — Bug Replay)

**Evidence from log:**
- LLM inferred reference shows "Sessions screen / clear all dialog"
- Device shows "Press Start screen / main UI"
- These are distinct screens within the brethap app

**Interpretation:**
Two possibilities:
1. **Video capture error:** Bad video was recorded from wrong screen or wrong point in app lifecycle
2. **State initialization mismatch:** Device launched app in main screen; video shows prior session state from different screen (Sessions history view)

Either way, semantic content mismatch is unrecoverable—device and video show incompatible states.

### Tertiary Issue: Single Segment Processing

**Log shows:** "Processing segment 0/0" but boundaries indicate 2 segments
- Segment 0: frames 0–1229
- Segment 1: frames 1233–1334 (not processed)

**Why:** ViBR exited after segment 0 failed (no action executed). Segment 1 never reached.

---

## Impact Assessment

**Execution rate:** 0/1 actions executed (0%)
**Workflow termination:** Early exit due to failed state alignment
**Cascading failures:** None (single step failure prevented cascade)

**What prevented execution:**
1. Video recording quality too poor to extract reliable UI signals
2. Video content showed incompatible app state vs device state
3. LLM recovery logic exhausted all 3 retries; no alignment achieved
4. Framework correctly terminated to avoid blind/incorrect actions

---

## Classification by ViBR Taxonomy

### Stage 2: GUI State Comparison (1 failure)

**Screen Recording Artifact** (primary)
- Dark/noisy video frames from camera-based recording
- Poor visual quality degraded DINO detection and Gemini vision analysis
- Prevented state alignment despite device state being correct

**Resolution/Layout Mismatch** (secondary)
- Video (22fps, 1080x1920 camera angle) vs Device (1080x1920 ADB screencap)
- Camera angle + ambient lighting distorted on-screen layout

### Stage 3: Bug Replay (1 failure)

**Semantic Gap** (default category)
- Video showed "Sessions / Clear All dialog" state
- Device showed "Press Start / Main UI" state
- Incompatible semantic content across app feature boundaries

---

## Conclusions

**brethap2 bad run failed completely** due to poor video recording quality combined with semantic state mismatch. The video was recorded via camera pointed at a physical device, resulting in:
- Severe visual degradation (dark, noisy frames)
- Difficult-to-parse UI elements
- Potential recording of wrong app state or app lifecycle point

ViBR correctly identified the mismatch and terminated safely rather than executing blind actions. **The failure is not a ViBR limitation but a data quality issue**—video input insufficient for reliable automation replay.

### Failure Mode

**Primary:** Screen recording artifact (camera-based video, poor quality)
**Secondary:** Semantic state divergence (video ≠ device lifecycle)

### Recommendation

To rerun brethap2 successfully:
1. Use clean screen capture method (Android screenrecorder or adb logcat + screenshare) instead of camera
2. Ensure good and bad runs start from same app state (both from Press Start screen, not Sessions dialog)
3. Verify video quality before passing to ViBR (minimum contrast, clarity requirements)

---

## TL;DR — Why It Failed

Bad video recorded via camera = dark, noisy frames ViBR cannot reliably parse. Even when device had correct "Press Start" state, video reference was too degraded for state matching. LLM detected semantic incompatibility (video showed different app screen), causing safe termination. **Not a ViBR bug; data quality insufficient for automation.**
