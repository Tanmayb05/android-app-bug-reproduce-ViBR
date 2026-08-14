# k91 (K-9 Mail) — Bad-Quality Run Issue Report

## 1. Log Summary

| Time | Module | Event |
|---|---|---|
| 16:38:53 | dino_detection | Loading GroundingDINO model (device=mps) |
| 16:39:00 | dino_detection | Annotated DINO output saved (`step_0v_dino.png`) |
| 16:39:08 | __main__ | Relevant regions: `{'target_regions': [4], 'predicted_action': 'tap'}` |
| 16:39:08 | __main__ | GPT selected regions: [4] |
| 16:39:08 | dino_detection | Relevant-only annotation saved (`step_0v_relevant_regions.png`) |
| 16:39:08 | __main__ | Comparing state: reference=`step_0v_relevant_regions.png` vs live=`step_0e_screenshot_0.png` |
| 16:39:14 | __main__ | WARNING: Attempting to align state (try 1/3) |
| 16:39:31 | __main__ | Recovery using region index: 3 at (786, 136) |
| 16:39:31 | execute_action | [1] Tap the search icon. → tap |
| 16:39:32 | __main__ | Comparing state (recovery attempt 1) |
| 16:39:40 | __main__ | WARNING: Attempting to align state (try 2/3) |
| 16:39:54 | __main__ | Recovery matched element: '' at (540, 1114) |
| 16:39:54 | execute_action | [1] Tap the Go button. → tap |
| 16:39:56 | __main__ | Comparing state (recovery attempt 2) |
| 16:40:02 | __main__ | WARNING: Attempting to align state (try 3/3) |
| 16:40:12 | __main__ | Recovery using region index: 3 at (786, 136) |
| 16:40:12 | execute_action | [1] Tap the search icon. → tap |
| 16:40:14 | __main__ | Comparing state (recovery attempt 3) |
| 16:40:21 | __main__ | WARNING: Skipping action: current GUI state does not match start state. Mismatch reason: "the reference screen displays search results, including an item titled 'hello world'. the current screen is an empty search interface..." |
| 16:40:21 | __main__ | Video processing completed. |

**Interpretation:** CLIP segmentation collapsed the entire 9-second interaction (tap search → type "Hi" → submit → view results) into a single segment (frames 0–308 of 567, i.e. ~9 of the video's ~17s). ViBR inferred only **one** action was needed to bridge the segment's start and stop frames — a tap on the search icon — when in truth three sequential actions (tap, type, submit) were required. The single tap predictably failed to reach the target state ("Hello World" search results), triggering three failed alignment/recovery retries (tapping the search icon again, tapping a "Go" button), each still landing short of the expected state. After exhausting retries, ViBR gave up and skipped the action entirely, ending the run with zero actions executed.

## 2. Executive Summary

- **Steps expected (ground truth):** 6 meaningful interaction steps (open search, type "Hi", submit, view results, tap "Hello World" result, email opens)
- **Steps executed by ViBR:** 0 (all 3 attempted taps were retries within one failed action, not distinct successful steps)
- **Steps missing:** 6/6
- **Coverage:** 0%
- **Root failure point:** Stage 1 (Action Segmentation) — CLIP under-segmented a multi-action sequence into one giant segment, making the derived single action fundamentally insufficient to reach the target state.

## 3. Ground Truth vs Execution Log

| Step # | Expected Action | Executed ✓/✗ | Status | Issue Category |
|---|---|---|---|---|
| 1 | Tap search icon (open Unified Inbox → search) | ✗ (attempted, but as sole action for whole segment) | Partial/misapplied | 1.4 Scene Detection |
| 2 | Type "Hi" into search field | ✗ | Missing entirely | 1.4 Scene Detection |
| 3 | Submit search (tap Go/enter) | ✗ (attempted blindly during recovery, not from truth) | Misapplied | 1.4 Scene Detection |
| 4 | View search results ("Hello World") | ✗ | Never reached | Cascading from above |
| 5 | Tap "Hello World" result | ✗ | Never reached | Cascading from above |
| 6 | Email detail begins loading | ✗ | Never reached | Cascading from above |

## 4. Video vs Log Comparison

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|---|---|---|---|---|
| 0–308 | Segment 0 (start) | Reference start frame = Unified Inbox with keyboard suggestions ("Hi/Ho/Ji") already visible (`step_0v_tmp_start.png`) | Truth: tap search icon → type "Hi" → submit | Yes — start frame already mid-interaction, meaning CLIP missed the search-icon-tap boundary too |
| 0–308 | Segment 0 (stop) | Reference stop frame = "Search results" screen with "Hello World" (`step_0v_tmp_stop.png`) | Truth: search results screen, single match | Matches truth step 5, but 3 intermediate actions omitted |
| 312–565 | Segment 1 (not processed — run stopped after Segment 0 failed) | N/A | Truth: tap "Hello World" → email opens | Entire second segment (tap result, open email) never attempted |

Live device state (`step_0e_screenshot_0.png`) never matched either reference: the emulator showed a **light-themed**, empty Unified Inbox — a completely different visual state (theme/content) from the recorded video's dark-themed inbox, compounding the state-alignment failure independent of the segmentation issue.

## 5. Detailed Failure Analysis

### Failure: Segment 0 action insufficient to reach target state

- **Expected behavior:** Three distinct actions (tap search icon, type "Hi", submit) transition Unified Inbox → Search results.
- **Log entry:** `Relevant regions: {'target_regions': [4], 'predicted_action': 'tap'}` — only one tap action was inferred for the entire segment.
- **Mismatch reason (from log):** "the reference screen displays search results ... the current screen is an empty search interface where the user can input a query."
- **Root cause category:** **Stage 1: Action Segmentation → 1.4 Scene Detection** — "Multiple actions merged together." CLIP's similarity threshold (0.95) treated the search-input and typing frames as part of one continuous "stable" segment relative to the inbox and results frames, merging tap+type+submit into a single scene transition instead of 3 separate ones.
- **Cascade impact:** Because the derived action set (1 tap) could never produce the derived target state (post-submit results), every recovery attempt was doomed — the device could reach at best a search-input state, never the results state. This exhausted all 3 `max_state_alignment_retries`, causing the action (and by extension the whole run) to be skipped, and Segment 1 (open email) was never attempted.
- **Secondary contributing factor:** Live emulator app state used a light theme with an empty inbox, unlike the recorded dark-themed populated inbox — a device/environment mismatch (Stage 2, 2.7 State Consistency Check) that also would have blocked correct state comparison even if segmentation had been correct.

## 6. Root Cause Categorization

| Category | Count | Notes |
|---|---|---|
| Stage 1.4 Scene Detection (multiple actions merged) | 1 | Primary/dominant cause — collapsed tap+type+submit into one segment |
| Stage 2.7 State Consistency Check (device/video state divergence — theme & content) | 1 | Secondary; emulator content differs from recorded video regardless of segmentation |
| Stage 3 (Bug Replay) | 0 | Never reached — run terminated in Stage 1/2 |

## 7. Conclusions

This run achieved **0% step coverage**, failing at the earliest replay stage. The dominant failure mode is over-aggressive scene merging in the CLIP-based segmentation stage (Section 4.1.4 / 1.4 of the ViBR taxonomy): a fixed similarity threshold of 0.95 failed to distinguish the search-input and typing sub-states from the surrounding stable screens, producing a segment boundary spanning tap, type, and submit as if they were one atomic transition. Because ViBR's action-inference step derives exactly one action per segment from the DINO/GPT region-selection pipeline, an under-segmented input structurally caps the number of recoverable actions below what the ground truth requires — no amount of state-alignment retrying can compensate for a segment boundary that omits necessary intermediate actions. A secondary, compounding limitation was observed in the device/video environment mismatch (light theme, empty inbox on device vs. dark theme, populated inbox in video), which independently would undermine GUI state comparison in Stage 2 of the pipeline.

## 8. TL;DR

- **Why it failed:** CLIP segmentation merged 3 user actions (tap search, type "Hi", submit) into 1 segment, so ViBR only inferred 1 action ("tap search icon") — insufficient to reach the recorded end state ("Hello World" search results).
- **Cascading effect:** All 3 state-alignment retries failed since the target state was structurally unreachable via the single inferred action; the action was skipped and the run terminated at 0 actions executed.
- **Secondary issue:** Emulator's live app state (light theme, empty inbox) diverged from the recorded video (dark theme, populated inbox), an environment mismatch that would separately break Stage 2 GUI comparison.
- **Bottom line:** This is a Stage 1 (Action Segmentation) failure — under-segmentation of a compound multi-step interaction — not a replay/execution defect.
