# ViBR Run Issue Report: jigsaw1 (bad quality, gemini-2.5-pro)

## 1. Log Summary

| Time | Module | Event |
|---|---|---|
| 16:20:04 | dino_detection | Annotated DINO output saved for segment 0 (`step_0v_dino.png`) |
| 16:20:34 | __main__ | Relevant regions for segment 0: `target_regions: []`, predicted action `tap` |
| 16:20:34 | __main__ | GPT selected regions: `[]` |
| 16:20:34 | dino_detection | WARNING: No relevant regions to annotate |
| 16:20:34 | __main__ | Comparing state: reference=`step_0v_relevant_regions.png` vs live=`step_0e_screenshot_0.png` |
| 16:20:41 | __main__ | WARNING: Attempting to align state (try 1/3) |
| 16:20:48 | execute_action | "The app is already open." -> no action |
| 16:20:51–16:21:25 | __main__ | Recovery attempts 2 and 3 repeat same "app already open" no-action outcome |
| 16:21:33 | __main__ | WARNING: Skipping action — mismatch reason: reference screenshot "heavily distorted," appears to show a list/menu; live screen shows the Jigsaw Puzzle creation screen. States judged entirely different |
| 16:21:33 | __main__ | Processing segment 1/2 |
| 16:21:45 | __main__ | Relevant regions for segment 1: `target_regions: [8]`, predicted action `tap` |
| 16:22:07–16:22:28 | execute_action | Three consecutive "no action" outcomes: "already on main menu," "already on target screen" |
| 16:22:29 | __main__ | "Action executed." (no actual tap logged — alignment loop exits without an ADB action) |
| 16:22:30 | __main__ | Processing segment 2/2 |
| 16:23:10 | __main__ | Relevant regions for segment 2: `target_regions: [1]`, predicted action `tap` |
| 16:23:38 | __main__ | Recovery matched element at (540, 1888); execute_action: "Tap the 'Generate Puzzle' button" -> **tap executed** |
| 16:23:40–16:24:18 | __main__ | Two further recovery attempts re-tap "Generate Puzzle" at same coordinates (redundant repeats) |
| 16:24:26 | __main__ | WARNING: Skipping action — reference shows main puzzle-solving screen; live shows settings/generation menu. Final state judged mismatched |
| 16:24:26 | __main__ | Video processing completed. Actions executed: 1 |

**Interpretation:** The run only ever emits **one real ADB action** (a tap on "Generate Puzzle" in segment 2) despite the ground-truth video containing two distinct slider-drag interactions (increasing puzzle width and height) before that final tap. Both preceding segments (0 and 1) end in "no action" outcomes because GroundingDINO/GPT-4o region selection returned no meaningful target region (segment 0: `target_regions: []`) or the state-alignment logic concluded the live screen already matched the goal state ("already open," "already on target screen") without ever issuing a tap/drag. The cascading effect: puzzle size stayed at the app's default (2×2) instead of the user's intended 4×3, so the final "Generate Puzzle" tap in segment 2 produced a puzzle inconsistent with the recorded video, causing the concluding state comparison to fail as a mismatch.

## 2. Executive Summary

- **Steps expected (ground truth):** 6 (open app, screen transition to config, increase width, increase height, tap Generate Puzzle, screen transition to puzzle board)
- **Interaction steps requiring device action:** 3 (open app / width slider / height slider) before the final Generate Puzzle tap
- **Steps executed by ViBR:** 1 (tap Generate Puzzle)
- **Steps missing:** 2 of 3 pre-generation interactions (width increase, height increase) — 0% coverage of slider interactions
- **Coverage:** 1/3 required interactive actions executed ≈ 33%

## 3. Ground Truth vs Execution Log

| Step# | Expected Action | Executed ✓/✗ | Status | Issue Category |
|---|---|---|---|---|
| 1 | Tap "Open" on Play Store listing (segment 0) | ✗ | Skipped — "app already open," no tap issued | Semantic gap / GUI State Comparison |
| 3 | Drag/tap Puzzle Size width 2→4 (segment 0/1) | ✗ | Skipped — empty target_regions in segment 0; "already on target screen" in segment 1 | Region Detection (GroundingDINO) / ROI Selection |
| 4 | Drag/tap Puzzle Size height 2→3 (segment 1) | ✗ | Skipped — no-action outcome, same segment as width | Region Detection (GroundingDINO) / ROI Selection |
| 5 | Tap "Generate Puzzle" (segment 2) | ✓ | Executed at (540, 1888) | — |
| 6 | Transition to puzzle board | Partial | Puzzle generated but at wrong size (2×2 default instead of 4×3) | Cascading — Bug Replay on Device |

## 4. Video vs Log Comparison

| Frame Range (approx.) | Segment | Log Shows | Video Shows | Gap? |
|---|---|---|---|---|
| Frames 0–118 (~0–8s) | Segment 0 | `target_regions: []`, three no-op alignment retries, final skip due to state mismatch | User taps "Open" on Play Store, then screen shows Jigsaw config screen at default 2×2 | **Yes** — ViBR never registers the app-open tap or initial screen; treats reference frame as unrecognizable ("heavily distorted... list or menu") |
| Frames 122–146 (~8–10s) | Segment 1 | `target_regions: [8]`, three no-op "already on target screen" outcomes, "Action executed" logged without a real tap | User drags width slider 2→4 and height slider 2→3 | **Yes** — both slider interactions are visually active in the video but ViBR's state-alignment loop repeatedly concludes the goal is already met, never issuing a drag/tap |
| Frames 150–447 (~10–30s) | Segment 2 | `target_regions: [1]`, tap on "Generate Puzzle" executed after 1 recovery attempt, then 2 redundant re-taps at same coordinates, final skip on end-state mismatch | User's finger presses "Generate Puzzle"; puzzle board renders with scattered pieces | **Partial** — the tap itself succeeds, but because puzzle size was never changed, the resulting board differs from the recorded (4×3, 12-piece) puzzle, so the end-of-segment comparison fails |

## 5. Detailed Failure Analysis

### Failure 1: Segment 0 — App-open tap and initial screen not registered
- **Expected behavior:** Recognize the Play Store "Open" tap and transition to the app's configuration screen.
- **Log entry:** `Relevant regions: {'target_regions': [], 'predicted_action': 'tap'}` followed by `WARNING: No relevant regions to annotate.`
- **Mismatch reason:** GroundingDINO/GPT-4o returned zero candidate regions for the reference frame, so no element could be selected for comparison or replay. Three retries defaulted to "app is already open," and the segment ultimately skipped with the mismatch description noting the reference image is "heavily distorted."
- **Root cause category:** **Phase 2, 2.5 Region Detection (GroundingDINO)** — missed interactive elements (Play Store "Open" button not detected as a candidate region), compounded by **1.1 Video Input Processing** (reference frame described as "heavily distorted," suggesting compression/HDR-conversion artifacts noted earlier in the log: "Video not SDR BT.709... Converting").
- **Cascade impact:** Without confirming app launch, the pipeline has no reliable anchor state, but conveniently the live device screen already matched the target (app was independently open), masking this failure from immediately halting the run.

### Failure 2: Segment 1 — Width and height slider drags never executed
- **Expected behavior:** Two drag/tap interactions on the Puzzle Size width and height controls, taking values from 2→4 and 2→3 respectively.
- **Log entry:** `Relevant regions: {'target_regions': [8], 'predicted_action': 'tap'}`, followed by three consecutive `execute_action` calls all resolving to "no action" ("already on the main menu," "already on the target screen"), then `Action executed.` with no corresponding tap/drag logged.
- **Mismatch reason:** The state-alignment/recovery logic judged the live screen sufficiently similar to the target state without requiring an action, even though the live puzzle-size values (2×2) had not been changed. This is a **false positive state-equivalence judgment**: superficially similar configuration screens (same layout, same labels) were treated as functionally equivalent despite differing slider values.
- **Root cause category:** **Phase 2, 2.7 State Consistency Check (GPT-4o)** — false positive "same state" determination; functional equivalence (slider value) not distinguishable from visual layout by the model. Secondary contributor: **Phase 3, 3.9 Action Space Definition** — the framework's action vocabulary/detection may not model incremental drag-based slider adjustments well, biasing the model toward "no action needed."
- **Cascade impact:** Puzzle size remained at the default (2×2) for the remainder of the run, directly causing the final segment's end-state mismatch (2×2 vs. expected 4×3/12-piece board).

### Failure 3: Segment 2 — Redundant repeated taps and final state mismatch
- **Expected behavior:** Single tap on "Generate Puzzle," followed by a matching puzzle board matching the video's 4×3 configuration.
- **Log entry:** Tap correctly executed at (540, 1888) on first recovery attempt, but two additional identical taps were issued during subsequent recovery/comparison cycles (16:23:57, 16:24:18) before the run concluded with: "the reference image shows the main puzzle-solving screen... the current image shows a settings or puzzle generation menu."
- **Mismatch reason:** Because size configuration diverged upstream (Failure 2), the generated puzzle board did not match the reference frame's expected appearance, and/or timing meant the live device had not yet finished transitioning when compared.
- **Root cause category:** **Phase 3, 3.11 Action Inference (GPT-4o)** — error recovery loop re-issues the same action multiple times without detecting that the action already succeeded (redundant tap repetition suggests the recovery loop doesn't track already-completed actions across retries). Secondary: **Misc — cascading state divergence** from Failure 2.
- **Cascade impact:** Terminal warning logged as a "Skipping action" state mismatch; run reports `status: successful` in the summary JSON despite only 1/3 meaningful interactions being executed, masking the functional failure behind a nominally "successful" run status.

## 6. Root Cause Categorization

| Category | Sub-category | Count | Notes |
|---|---|---|---|
| Phase 1: Action Segmentation | 1.1 Video Input Processing | 1 | HDR-to-SDR conversion and possible compression artifacts contributing to "heavily distorted" reference frame in segment 0 |
| Phase 2: GUI State Comparison | 2.5 Region Detection (GroundingDINO) | 1 | Zero candidate regions returned for segment 0's app-open tap |
| Phase 2: GUI State Comparison | 2.7 State Consistency Check (GPT-4o) | 1 | False positive "same state" judgments in segment 1 skip both slider interactions |
| Phase 3: Bug Replay on Device | 3.11 Action Inference (GPT-4o) | 1 | Redundant repeated taps on "Generate Puzzle" across recovery attempts in segment 2 |
| Phase 3: Bug Replay on Device | 3.9 Action Space Definition | 1 | Possible weak support for incremental/drag-based slider actions, biasing toward no-action outcomes |

## 7. Conclusions

The ViBR pipeline processed all three detected segments of the `jigsaw1` bad-quality video and terminated with a `successful` status, yet executed only one of the three meaningful device interactions present in the ground truth (33% functional coverage). The dominant failure mode is a **false-equivalence bias in the GPT-4o state-consistency check**: the model repeatedly concluded the live device state already matched the target state ("already open," "already on target screen") without verifying data-level differences such as slider values, leading it to skip both the width and height size adjustments entirely. This was compounded by a **region-detection failure** in the opening segment, where GroundingDINO returned no candidate regions for the Play Store "Open" tap. The consequence was a puzzle generated at the wrong size, which the pipeline itself flagged as a terminal state mismatch — yet the run's own summary statistics report success, indicating a broader limitation in how ViBR's end-to-end status is derived from per-segment outcomes.

## 8. TL;DR

- ViBR executed 1 of 3 required interactive steps (33% coverage); only the final "Generate Puzzle" tap succeeded.
- Both puzzle-size slider adjustments (width 2→4, height 2→3) were silently skipped because GPT-4o's state comparison falsely judged the live screen as already matching the target.
- Segment 0's app-open tap was also skipped due to GroundingDINO returning zero candidate regions on a possibly HDR/compression-distorted reference frame.
- The run's final "successful" status masks a functional failure: the generated puzzle board did not match the ground-truth video's 4×3 configuration.
- **Bottom line:** State-equivalence false positives, not action-execution failures, are the primary bottleneck — the model recognized the right screens but wrongly assumed the right values were already set.
