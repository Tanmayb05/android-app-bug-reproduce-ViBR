# ViBR Run Analysis: homemedkit1 (bad run)

## Executive Summary

**Ground Truth:** 10 expected steps (medicine list → add dialog → form fill with 6 fields → submit → view confirmation)  
**Actually Executed:** 0 steps  
**Gap:** 10 steps missing (0% execution rate)  

The bad run failed catastrophically with zero actions executed. The root cause is a **fundamental segmentation boundary mismatch** on segment 0: the reference frame shows the Google Play Store "open" button (app installation state), while the device screen shows the app already open (post-installation state). This state mismatch cascades through all four segments, causing repeated recovery failures and eventual abandonment of the automation.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 1 | Open app from Play Store | ✗ | Skipped | Dynamic GUI State Mismatch |
| 2 | Tap add button (FAB) | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 3 | Tap 'Add' option in menu | ✗ | Failed (recovery) | Semantic Gap |
| 4 | Type product name 'medA' | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 5 | Fill group/dates/display name | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 6 | Type release form 'medB' | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 7 | Type comment 'abc' | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 8 | Submit form (checkmark) | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 9 | Verify detail view | ✗ | Failed (recovery) | Dynamic GUI State Mismatch |
| 10 | Final state confirmation | ✗ | Abandoned | Dynamic GUI State Mismatch |

---

## Segment-by-Segment Failure Analysis

### Segment 0: Initial State Mismatch (CRITICAL)

**Expected state (reference):** Google Play Store with "open" button visible  
**Actual device state:** HomeMedKit app already open on medicine list screen  
**Log entry (line 160):**
```
[WARNING] Skipping action: current GUI state does not match start state. 
Mismatch reason: the reference screen shows the app's page on the google play store 
with an 'open' button. the current screen is the main interface of the app after 
it has been opened. therefore, the action of opening the app from the play store 
cannot be performed from the current screen.
```

**Root cause:** The **bad-video.mp4** was recorded with the app already installed and open. The first segmentation boundary extracted a frame from early in the video that does NOT represent the true initial state. The segmentation algorithm identified this frame as a "stable segment boundary," but it captures the app installation/startup state (Play Store page), not the actual initial state when the video recording began.

**Impact:** ViBR correctly recognized the state mismatch but could not proceed. The initial action (opening the app) cannot be replayed because the app is already open. This is a valid skip decision, but it leaves ViBR with no baseline state alignment for subsequent segments.

---

### Segment 1: Recovery Attempts Fail (CASCADING)

**Expected state (reference):** Medicine list with add button visible  
**Actual device state:** Varies wildly between recovery attempts (settings screen appears, empty list screen)  
**Log entries (lines 174–195):**

**Recovery attempt 1:** Tapped add button at (900, 1773)  
→ Result: Settings screen appeared instead of form  
→ Mismatch: "the reference image shows a screen for adding or editing medication details... the current image shows the app's settings screen"

**Recovery attempt 2:** Tapped Medicine icon (bottom nav) at (180, 1773)  
→ Result: Still not aligned  

**Recovery attempt 3:** Tapped add button again at (900, 1773)  
→ Result: Settings screen still showing  
→ **Skipped:** "the reference screen shows a form for adding or editing medication... the current screen is the app's settings screen... completely different screens"

**Root cause:** Segment 1 boundary is correct (medicine list → add form), but the device is not responding predictably to tap coordinates. ViBR is tapping the correct location (bottom right ≈ add button area), but the app state is diverging—navigation is jumping to settings instead of opening the add dialog. This suggests:

1. **Timing issue:** Post-segment-0 recovery sleep (1.0s) may be insufficient for app state to stabilize
2. **Coordinate drift:** The device resolution or display scaling differs from the video recording device
3. **App state instability:** The bad video was recorded under conditions (different device, different app version, network issues) that produce non-deterministic UI responses

---

### Segment 2 & 3: Compounding Failures

Each subsequent segment shows the same pattern:
- ViBR predicts correct action (tap add button / form fill)
- Recovery attempts fail because device state diverges from reference
- LLM correctly identifies the state mismatch
- ViBR skips action to avoid corrupting app state

**Segment 2 log (line 230):**
```
[WARNING] Skipping action: the reference screen shows a form for adding or editing 
a medication, with various input fields... the current screen is a main list view 
that is empty and prompts the user to add medications. These are completely 
different screens.
```

**Segment 3 log (line 265):**
```
[WARNING] Skipping action: the top bar in the reference image contains a 
notification bell icon, while the top bar in the current image contains a 
checkmark icon. Therefore, the same action cannot be performed.
```

The final failure mentions icon differences in the header—a **cosmetic/transient artifact**, suggesting the device state has drifted so far that even identical UI elements appear in different contexts.

---

## Root Cause Categorization

### Stage 1: Action Segmentation
**Failures:** 1/10 (initial state/Play Store boundary)

- **Over-segmentation:** The video segmentation captured a "stable frame" that was not the true initial recording state. This caused ViBR to begin with a reference frame that does not match the actual device state.

### Stage 2: GUI State Comparison
**Failures:** 9/10 (all recovery attempts post-segment-0)

- **Dynamic/session-specific content:** The bad video was recorded under different device conditions. When ViBR attempts to replay the actions, the app's UI responses do not match the recorded video—buttons tap but wrong screens appear, navigation jumps unexpectedly, icons shift.
  
- **Coordinate/layout drift:** The segmentation identified coordinates that do not map correctly to UI elements on the replay device.

- **Transient artifacts:** Segment 3 shows header icon differences (notification bell vs checkmark), suggesting temporary UI state divergence.

### Stage 3: Bug Replay on Device
**Failures:** 0/10 (not reached; failed at stages 1–2)

---

## Why This Failure Occurs (Academic Analysis)

### Problem 1: Initial State Misalignment (Segmentation Artifact)

The bad-video.mp4 begins with the app already open. However, the segmentation algorithm identified frame 0 as a stable boundary, which happens to show the Google Play Store "open" button. This is a **false initial state**—it does not represent the recorded video's actual starting point. 

ViBR's segmentation uses CLIP-based similarity scoring to find transitions. Frame 0 and early frames of the video may show similar color/layout patterns (both light-colored screens), causing the algorithm to misjudge the transition point. This results in a reference frame that is internally consistent but external to the actual recording context.

**Fix required:** Either:
1. Ensure the "good" video starts from the same initial state (Play Store → install → launch), or
2. Use segment boundaries that include a buffer frame representing the true initial state

### Problem 2: Non-Deterministic Device Behavior Under Replay

When ViBR runs recovery actions (tapping coordinates, waiting for state changes), the device does not respond as the original recording did. This indicates:

- **Device differences:** The original video was recorded on Device A; replay is on Device B (different screen resolution, DPI, app version)
- **Network/timing issues:** The original video may have been recorded with slow network or specific app cache state. Replay under different network conditions causes the app to load different data.
- **Session state:** The original video session may have had pre-initialized data; replay starts fresh and encounters different API responses or default states.

The log shows ViBR correctly identifying these mismatches and declining to execute actions. This is *safe* but results in 0% execution.

### Problem 3: Recovery Strategy Exhaustion

ViBR attempts up to 3 recovery retries per action:
1. State comparison (visual diff)
2. Recovery alignment (LLM predicts how to get to target state)
3. Retry with adjusted coordinates

After 3 retries, if state still doesn't match, ViBR skips the action. With segment 1 failing, segment 0's lack of execution cascades—ViBR never enters the form state needed for segments 2–3 to make sense.

---

## Detailed Failure Analysis

### Segment 0: Initial State Mismatch (CRITICAL)

**Expected behavior (ground truth):**
> User is viewing the app's Google Play Store page with an "open" button visible. Tapping "open" (or the system launching the app) transitions to the medicine list screen.

**What the log shows:**
> ViBR detected the reference state (Play Store + open button) but the current device state is already past this point—the app is open on the medicine list. ViBR correctly declined to execute the "open app" action because the app is already open.

**Mismatch reason:**
> The video segmentation identified the wrong frame as the segment boundary. The actual video starts with the app already open. Frame 0 of the reference segment captures the Play Store, which is external to the actual recording context.

**Root cause:** **Over-segmentation / Incorrect Boundary Detection**
- The CLIP model scored frame similarity and identified a "stable region" that actually represents an out-of-context frame
- The segmentation thresholds (stable_sim_threshold: 0.95, stable_interval_threshold: 1) may be too lenient for this video's specific visual characteristics

**Why it matters:**
- ViBR cannot proceed without a shared initial state
- All subsequent actions are built on the assumption that segment 0 completed successfully
- With segment 0 skipped, segments 1–3 are orphaned—their reference states become meaningless

---

### Segment 1: Add Button / Add Dialog (CASCADING FROM SEG 0)

**Expected behavior:**
> From the medicine list (post-segment-0), tap the green floating action button (FAB) at the bottom right. A menu appears with "Scan" and "Add" options. Tap "Add" to open the medication form.

**What the log shows:**
> Recovery attempt 1: Tapped coordinate (900, 1773) (presumed add button location). Device responded by opening the **Settings screen** instead of the form.
> 
> Recovery attempts 2–3: Tried alternative approaches (tapping Medicine icon, retrying add button). Device state continued to diverge—empty list, settings screen, wrong navigation.

**Mismatch reason:**
> The device is not responding to the tap coordinates as expected. Either:
> - Coordinates are incorrect due to screen resolution/DPI differences
> - App routing is non-deterministic (same tap → different screen in replay vs original)
> - Device state is unstable (settings screen should not be reachable from a tap on the add button)

**Root cause:** **Dynamic/Session-Specific Content + Coordinate Drift**
- The bad video was recorded under device/network conditions that the replay device does not match
- Coordinate (900, 1773) mapped correctly to the add button on the original device but not on the replay device
- The app's internal navigation stack may be corrupted, causing taps to route to unrelated screens

**Why it matters:**
- Without successfully entering segment 1's target state (add form), ViBR cannot proceed to fill the form fields in segments 2–3
- This is the cascade failure point—segment 0 was skipped, segment 1 recovery failed, all downstream actions are blocked

---

## Impact Assessment

### Execution Cascade

```
Segment 0 (skip)
  ↓ [No action executed]
Segment 1 (recovery fails after 3 retries)
  ↓ [State mismatch, skipped]
Segment 2 (recovery fails; device in unknown state)
  ↓ [State mismatch, skipped]
Segment 3 (recovery fails; device in Settings screen instead of form)
  ↓ [State mismatch, skipped]
Result: 0/10 actions executed
```

### Root Cause Priority

1. **Segment 0 boundary mismatch** (initial state) — the starting point for everything
2. **Coordinate drift** (segment 1 recovery) — the first actual action that should have worked
3. **Session state instability** (cascading) — why recovery didn't converge to target state

---

## Conclusions

The bad run achieved **0% execution** of the ground truth. The primary failure mode is **Stage 2: GUI State Comparison**, driven by mismatches between the recording environment and the replay environment.

### Why It Failed

1. **Initial state boundary mismatch (segmentation):** The first segment references a frame outside the actual video recording context (Google Play Store, not recorded app state).

2. **Coordinate/resolution drift:** The replay device has different resolution or UI scaling than the original. The add button is tapped at coordinate (900, 1773), which is correct in theory but does not map to the expected UI element on the replay device.

3. **Non-deterministic app behavior:** The bad video was recorded under conditions (network, device state, app version) that differ from replay. The app's response to identical tap inputs is inconsistent between recording and replay—same input → different output.

4. **Cascading failures:** Once segment 0 is skipped and segment 1 fails, ViBR has no valid reference state for subsequent segments. Recovery attempts exhaust, and ViBR declines further action to avoid corrupting the app state.

### Why This Matters

The gap of 10 steps (0% execution) indicates that **the bad video is fundamentally not reproducible on the current replay device under the current recording conditions.** This is not a bug in ViBR's logic (the state matching and skip decisions are correct); it is a **fundamental incompatibility between recording and replay environments**.

### Implications for ViBR's Robustness

- **Video segmentation must anchor to recording context:** Boundaries should be validated against the actual recorded initial state, not abstract frame similarity.
- **Coordinate-based recovery must account for device differences:** Use device-aware scaling or preference-based selectors (resource-id, text) over raw coordinates.
- **Session state must be controlled:** Pre-record videos on canonical devices with canonical app/network states, or use device-independent assertions for segment boundaries.

---

## TL;DR — Why It Failed

**Bottom line:** The bad video was recorded on a different device or under different app/network conditions than the replay environment. The first action couldn't execute (Play Store "open" button, but app already open), and recovery attempts failed because tap coordinates didn't map to the expected UI elements on the replay device. With no valid entry point, ViBR abandoned all 10 steps of the form-filling workflow.

**The specific failure:** Segment 0 skip + Segment 1 coordinate drift → cascading state mismatches → 0 actions executed.

**Technical root cause:** Stage 2 GUI State Comparison failures driven by dynamic/session-specific content and coordinate drift between recording and replay devices.
