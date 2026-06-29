# ViBR Run Analysis: brethap1 (bad run)

## Executive Summary

**Ground Truth:** 5 expected steps
**Actually Executed:** 0 steps
**Gap:** 5 steps missing (0% execution rate)

Bad run failed immediately at segment 0, never executing any action. ViBR attempted to tap a hamburger menu icon 3 times with recovery attempts, but was blocked by a fundamental state mismatch: the bad video starts on the **main screen** ("Press Start"), while the reference state extracted from the good video was the **sessions menu screen** with a hamburger icon. ViBR's GUI state comparison correctly identified this incompatibility and aborted execution after exhausting recovery attempts.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 0 | Tap play button on main screen | ✗ | Failed | Semantic gap (state mismatch) |
| 1 | Wait for breathing session to progress | ✗ | Skipped | Cascading failure |
| 2 | Wait during inhale/exhale cycles | ✗ | Skipped | Cascading failure |
| 3 | Wait until session timer completes | ✗ | Skipped | Cascading failure |
| 4 | Automatic transition to sessions list | ✗ | Skipped | Cascading failure |

---

## Video vs Log Comparison

Extracted frames from bad video at 1 fps (32 total frames, ~32 seconds duration):

| Frame | Time | Log Event | Video Shows | Gap? |
|-------|------|-----------|-------------|------|
| 0001 | 00:00 | Segment 0 start | Main screen, finger about to tap play button | ✓ Match |
| 0010 | 00:10 | Action inference phase | Breathing session in progress ("Inhale", blue circle, timer 0:01:56) | ✓ Match |
| 0023 | 00:23 | Late in segment | Session ending, screen mostly blank | ✓ Match |
| 0024 | 00:24 | Segment 0 end | Keyboard visible (input field active), different context | — |

**Key Observations:**

1. **Correct video playback progression**: Video shows natural breathing session flow: main screen → tap play → session progresses → timer runs down → end state.
2. **Reference state corruption**: ViBR extracted segment 0 from bad video but used a **reference screenshot from good video's post-session state** (hamburger menu visible on sessions screen).
3. **State mismatch detection**: ViBR correctly identified the mismatch at line 163 of log: "reference image displays a 'sessions' screen... current image shows the main start screen."
4. **Recovery attempts exhausted**: ViBR attempted 3 state alignment retries (lines 139–162), each time re-tapping coordinates (540, 960), which consistently failed to transition state.

---

## Detailed Failure Analysis

### Step 0: Tap Play Button to Start Breathing Session — FAILED

**Expected behavior (ground truth):**
> User taps the blue play button on the main screen. App transitions to a breathing session screen showing a large blue circle, timer (0:02:00), and "Session, 0 Breaths" label.

**What the log shows:**
```
[2026-06-12 02:48:09] Comparing state: reference=step_0v_relevant_regions.png vs live=step_0e_screenshot_0.png
[2026-06-12 02:48:16] WARNING Attempting to align state (try 1/3)...
[2026-06-12 02:48:32] Recovery matched element: '' at (540, 960)
[2026-06-12 02:48:34] Comparing state (recovery attempt 1): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_1.png
[2026-06-12 02:48:40] WARNING Attempting to align state (try 2/3)...
[2026-06-12 02:48:54] Recovery matched element: '' at (540, 960)
[2026-06-12 02:48:56] Comparing state (recovery attempt 2): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_2.png
[2026-06-12 02:49:02] WARNING Attempting to align state (try 3/3)...
[2026-06-12 02:49:16] Recovery matched element: '' at (540, 960)
[2026-06-12 02:49:18] Comparing state (recovery attempt 3): reference=step_0v_tmp_stop.png vs live=step_0e_screenshot_3.png
[2026-06-12 02:49:25] WARNING Skipping action: current GUI state does not match start state. Mismatch reason: the reference image displays a 'sessions' screen with a list of past sessions. the current image shows the main start screen of the app with a 'press start' prompt and a timer. these are two different screens with completely different functionalities.
```

**Mismatch reason:**
ViBR's action planning inferred "tap the hamburger menu icon" as the next action (because segment 0 reference from good video showed that menu state). But the bad video's segment 0 started on the main screen, not the menu. The reference screenshot (`step_0v_relevant_regions.png`) was extracted from the good video's post-hamburger-tap state (sessions menu with drawer open), **not** the actual starting state of segment 0 in the bad video.

**Root cause:** Stage 3 (Bug Replay on Device) — Semantic Gap
- Evidence: Log line 163 explicitly states mismatch between reference (sessions screen) and live (main screen).
- Evidence: Recovery attempts targeted coordinates (540, 960), which is not a valid button on the main screen.
- Why it matters: This blocks execution of all subsequent steps. The planner inferred an action based on a reference state that was incompatible with the actual starting context of the bad run.

---

## Root Cause Categorization

### Stage 1: Action Segmentation (0 failures)
- Over-segmentation: 0
- Dynamic element false boundary: 0

### Stage 2: GUI State Comparison (0 failures)
- Resolution/layout mismatch: 0
- Cosmetic theme difference: 0
- Transient artifact overlay: 0
- Screen recording artifact: 0
- Scroll-induced element shift: 0
- Dynamic/session-specific content: 0

### Stage 3: Bug Replay on Device (1 failure)
- Semantic gap: 1
  - **Root issue**: ViBR extracted segment 0 reference from **good video's state** but applied it as the expected starting state for **bad video's segment 0**. The two videos have fundamentally different entry points (main screen vs. sessions menu), causing a cascading state mismatch.
- Masked intermediate transition: 0

---

## Conclusions

The bad run achieved **0% execution** of ground truth. The single failure is a **semantic state mismatch** at the segment level. ViBR's segmentation algorithm (CLIP) correctly identified segment boundaries in the bad video, but the reference state used for initial action planning was extracted from the good video at an incompatible screen context.

This indicates a fundamental limitation in how ViBR handles **heterogeneous video contexts**. When two recordings of the same app start in different UI states, the frame-by-frame segmentation (CLIP similarity) may align temporal structure but not semantic state. ViBR's recovery mechanism (state alignment retries) was appropriate but insufficient, as the mismatch was not a transient UI difference but a structurally different starting condition.

The gap of **5 missing steps** is not due to action inference failures, UI detection issues, or timing problems—it stems from **incompatible reference context** between good and bad videos at the segment initialization level.

---

## TL;DR — Why It Failed

**Failure reason:**
- **Semantic state mismatch**: Bad video starts on main screen ("Press Start" button). ViBR's reference state for segment 0 was extracted from good video's sessions menu screen. These are different apps states with different UI elements and interaction points.
  - Evidence: Log explicitly identifies mismatch—reference shows "sessions screen with list," live shows "main start screen with press start prompt."
  - Impact: Action planning (hamburger menu tap at 540,960) was invalid for the actual starting state. Recovery attempts failed because the target coordinate doesn't exist on the main screen. Execution aborted.

**Bottom line:** ViBR detected a valid state incompatibility and correctly aborted execution rather than executing wrong actions blindly. The root cause is incompatible entry states between reference (good) and target (bad) videos, not a failure of ViBR's state detection or recovery logic. This suggests a video capture or setup issue where the bad run recorded a different app initialization flow than the good run, violating the assumption that both recordings start in the same UI context.
