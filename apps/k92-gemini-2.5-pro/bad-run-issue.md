# k92 (K-9 Mail) — Bad-Quality Run Issue Report

## 1. Log Summary

| Time | Module | Event |
|---|---|---|
| 16:42:34 | check_video.orchestrator | Video not SDR BT.709: Codec is hevc, need h264. Converting... |
| 16:42:58 | check_video.orchestrator | Conversion done. Video is now SDR BT.709. |
| 16:42:58 | __main__ | Starting video processing from apps/k92-gemini-2.5-pro/bad-video.mp4 (algorithm=clip)... |
| 16:42:58 | __main__ | Initializing ADB device controller... |
| — | (stdout) | Reading frames from video... Loaded 1730 total frames |
| 16:43:04 | __main__ | Detecting stable segments... |
| — | (stdout) | Encoding frames with CLIP... Encoded 1730/1730 |
| 16:44:46 | __main__ | CLIP similarity list calculated and saved. |
| 16:44:48 | __main__ | Total frames: 1730, total segments: 1 |
| 16:44:48 | __main__ | Raw segment boundaries (before clamping): [(0, 1728)] |
| 16:44:48 | __main__ | Clamped segment boundaries: [(0, 1728)] |
| 16:44:48 | __main__ | Video processing completed. |
| 16:44:48 | run_stats | Status: incomplete; Scenes: 0; Actions executed: 0 |

**Interpretation:** No GroundingDINO/action-inference stage was ever reached in this run — the log jumps directly from CLIP segmentation to "Video processing completed" with zero scenes. CLIP found only **one** stable segment spanning nearly the entire 1730-frame (~29s) video: `(0, 1728)`. Because ViBR derives replayable "scenes" from the gaps *between* consecutive stable segments (`stats.scenes = len(stable_segments) - 1`), a single segment yields `scenes = 1 - 1 = 0` — the per-segment replay loop (`for i in range(len(stable_segments) - 1)`) never executes its body even once. The entire video was judged to contain zero transitions worth replaying, despite the ground-truth video containing at least 10 distinct user interactions (drawer opens, screen navigations, an app switch, and a home-screen/app-relaunch cycle) and a visible theme-color bug at the end.

## 2. Executive Summary

- **Steps expected (ground truth):** 12 meaningful interaction steps (open drawer, navigate Settings → Accounts → bruce → General settings, inspect/toggle default account and account color, back out to inbox, press Home, brief FTP Server app view, tap K-9 Mail to relaunch, reopen drawer and observe pink-tint bug)
- **Steps executed by ViBR:** 0
- **Steps missing:** 12/12
- **Coverage:** 0%
- **Root failure point:** Stage 1 (Action Segmentation) — CLIP judged the entire video as one continuous stable segment, producing zero derivable scenes; the replay loop never ran.

## 3. Ground Truth vs Execution Log

| Step # | Expected Action | Executed ✓/✗ | Status | Issue Category |
|---|---|---|---|---|
| 1 | Open nav drawer (tap hamburger) | ✗ | Never attempted | 1.3 Similarity Computation |
| 2 | Tap Settings | ✗ | Never attempted | 1.3 Similarity Computation |
| 3 | Tap "bruce" account under Accounts | ✗ | Never attempted | 1.3 Similarity Computation |
| 4 | Tap General settings (bruce) | ✗ | Never attempted | 1.3 Similarity Computation |
| 5 | Inspect/toggle Default account & Account color | ✗ | Never attempted | 1.3 Similarity Computation |
| 6 | Back out to Unified Inbox (multiple back presses) | ✗ | Never attempted | 1.3 Similarity Computation |
| 7 | Press Home | ✗ | Never attempted | 1.3 Similarity Computation |
| 8 | Brief FTP Server app / recents view | ✗ | Never attempted | 1.3 Similarity Computation |
| 9 | Tap K-9 Mail icon on home screen to relaunch | ✗ | Never attempted | 1.3 Similarity Computation |
| 10 | Unified Inbox reopens | ✗ | Never attempted | 1.3 Similarity Computation |
| 11 | Reopen nav drawer | ✗ | Never attempted | 1.3 Similarity Computation |
| 12 | Observe pink/magenta theme-bug in drawer header | ✗ | Never attempted | Cascading — target bug never reached |

## 4. Video vs Log Comparison

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|---|---|---|---|---|
| 0–1728 (of 1730) | Segment 0 (only segment) | Entire video treated as one "stable" block; `total segments: 1` | Unified Inbox → drawer → Settings → Accounts → bruce → General settings (toggle + pink color swatch) → back-chain to inbox → Home → FTP Server app flash → home screen → relaunch K-9 Mail → drawer reopened showing pink-tinted header (the bug) | **Yes — total.** At least 9 distinct screen types (Unified Inbox blue, drawer blue, Settings list, Account settings, General settings x2, Home screen wallpaper, FTP Server app, drawer pink) are visually very different, yet CLIP's frame-to-frame similarity never dropped below the 0.95 stability threshold long enough to register a boundary. |
| 1728–1730 (2 trailing frames) | Discarded (below `leading_segment_min_frame`) | Not processed | End of video, likely still showing pink-tinted inbox | No independent segment created; folded into the single segment |

No live-device screenshots exist in `bad-artifacts/` for this run (directory has no `step_*` files) because the replay loop never started — there was nothing to compare against a device state.

## 5. Detailed Failure Analysis

### Failure: Entire video collapsed into a single CLIP segment, yielding zero scenes

- **Expected behavior:** CLIP should detect roughly 8–11 stability breaks corresponding to each screen transition (drawer open, Settings, Account settings, General settings, back-navigation, Home, app switch, relaunch, drawer-with-bug).
- **Log entry:** `Total frames: 1730, total segments: 1` / `Raw segment boundaries (before clamping): [(0, 1728)]`
- **Mismatch reason:** No explicit mismatch warning was logged — the failure is silent. `stats.scenes = len(stable_segments) - 1` evaluated to `0`, so `for i in range(len(stable_segments) - 1)` never iterated. No action-inference, DINO detection, or device interaction occurred at all (LLM calls = 1, using only 6 tokens — just the initial provider ping-pong check).
- **Root cause category:** **Stage 1: Action Segmentation → 1.3 Similarity Computation** — "Fixed threshold (0.95) may not generalize" / "Missed transitions during subtle state changes" / "Noise accumulates over long recordings." At 1730 frames (≈29s, 60fps), this is roughly 3x longer than the k91 companion video (567 frames, ~9s) that itself already showed segmentation problems (see `k91-gemini-2.5-pro/bad-run-issue.md`). The longer duration combined with `stable_interval_threshold: 1` (very short run-length requirement) appears to have caused CLIP's frame-embedding similarity to stay above 0.95 across screen changes — plausibly because consecutive frames during each transition (menu slide animations, tap-triggered activity transitions) are visually close to their neighbors even when the two endpoints of a transition differ greatly, and the algorithm's segment-merging logic treated the whole sequence as one long "stable-ish" run without ever accumulating a large enough embedding delta to trigger a split.
- **Cascade impact:** With `scenes = 0`, absolutely no part of the ViBR pipeline downstream of segmentation executed: no GroundingDINO region detection, no GPT/Gemini action inference, no ADB device interaction, no state-alignment retries. This is a total pipeline short-circuit, more severe than k91's partial failure (which at least attempted one action). The user-visible bug being reproduced in the source video — the pink/magenta theme corruption in the nav drawer after visiting the "bruce" account's General settings — was never even approached.

## 6. Root Cause Categorization

| Category | Count | Notes |
|---|---|---|
| Stage 1.3 Similarity Computation (fixed threshold fails to generalize to long/complex videos) | 1 | Sole and total cause — zero segment boundaries detected across a 29s, multi-screen video |
| Stage 1.4 Scene Detection (scenes derived as `segments - 1`) | 1 | Structural consequence — a single segment mathematically guarantees zero scenes regardless of content |
| Stage 2/3 | 0 | Never reached |

## 7. Conclusions

This run represents a complete pipeline failure at the earliest possible stage, achieving **0% step coverage** with **zero LLM-driven action attempts** (excluding the initial provider handshake). Unlike the companion k91 run, which at least produced one segment and one (insufficient) action before failing, k92's CLIP-based segmentation collapsed an entire 1730-frame, ~29-second recording — containing at least nine visually distinct screens and a clear intentional theme-color bug — into a single undifferentiated block. Because ViBR's scene count is defined as `len(stable_segments) - 1`, a single detected segment structurally guarantees zero actionable scenes, independent of how much true interaction content the video contains. This suggests the fixed CLIP similarity threshold (0.95) and short stability-interval requirement (1 frame) do not generalize to longer, multi-screen recordings, where cumulative embedding drift across many small transitions apparently never exceeds the threshold in a way the segmentation algorithm registers as a hard boundary. The practical consequence is severe: no matter how significant the underlying bug (here, a UI theme/color leak), if the reproduction video is long or its transitions are gradual relative to frame sampling, ViBR may never generate a single replayable action.

## 8. TL;DR

- **Why it failed:** CLIP segmentation found only 1 stable segment across the entire ~29s video, and since scene count is `segments - 1`, this yields exactly 0 scenes — the replay loop body never executes.
- **Cascading effect:** Zero GroundingDINO calls, zero action-inference LLM calls, zero ADB actions. The run reports `actions_executed: 0` and completes almost silently (no WARNING/ERROR lines), making this failure mode harder to notice than k91's retry-loop failure.
- **What was missed:** A 10+ step interaction culminating in a nav-drawer theme-color bug (pink/magenta gradient replacing blue) — the actual target bug — was never approached.
- **Bottom line:** This is a Stage 1 (Action Segmentation) failure — total under-segmentation on a long, multi-screen video — distinct from and more severe than k91's partial under-segmentation; both point to the fixed CLIP similarity threshold not generalizing across video lengths/content complexity.
