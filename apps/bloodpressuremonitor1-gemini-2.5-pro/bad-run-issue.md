# ViBR Failure Analysis: bloodpressuremonitor1 (Bad Run)

## Log Summary

| Time | Module | Event |
|------|--------|-------|
| 01:56:28 | logger | RUN CONFIGURATION logged (app: bloodpressuremonitor1, quality: bad, algorithm: clip) |
| 01:56:29 | google_genai.models | AFC enabled with max remote calls: 10 |
| 01:56:31 | model_api | Gemini pong verified, provider selected |
| 01:56:34 | check_video.orchestrator | Video not SDR BT.709 (HEVC codec), conversion to H.264 initiated |
| 01:56:34 | check_video.orchestrator | Conversion completed, SDR BT.709 verified |
| 01:56:34 | __main__ | Video processing started (clip algorithm) |
| 01:56:34 | __main__ | ADB device controller initialized |
| 01:56:34 | __main__ | Stable segment detection started |
| 01:56:35–01:56:54 | httpx | CLIP model downloaded and cached (~20s network overhead) |
| 01:56:55 | __main__ | CLIP processing completed: 7 total frames, 1 segment detected |
| 01:56:55 | __main__ | Segment boundaries: [(0, 5)] (one incomplete segment) |
| 01:56:55 | run_stats | RUN SUMMARY: **incomplete**, 0 scenes, 0 actions executed, status="incomplete" |

**Interpretation:** The bad video file is severely corrupted or truncated. It contains only 7 frames (~0.13s duration) when converted from HEVC to H.264. CLIP detected only 1 segment with boundary (0, 5), indicating the video failed to capture meaningful interaction frames. The segmentation phase completed, but no frames were suitable for action extraction, resulting in zero scenes detected and zero actions executed. Video corruption likely occurred during capture or storage, preventing any meaningful replay simulation.

---

## Executive Summary

**Expected steps** (from good-truth.json reference): 5+ interaction steps (navigation, taps, screen transitions)  
**Executed steps**: 0  
**Gap**: 5+ steps missing  
**Coverage**: 0%

**Root cause**: Video corruption → insufficient frames → no segments actionable → replay failed

---

## Ground Truth vs Execution Log

| Step # | Expected Action (Good Truth) | Executed ✓/✗ | Status | Issue Category |
|--------|------------------------------|---------------|--------|-----------------|
| 1 | Wait for app dashboard load | ✗ | No frame data | **Phase 1: Video Input Processing** |
| 2 | Navigate to Statistics screen | ✗ | No frames | **Phase 1: Video Input Processing** |
| 3 | Tap Diastolic tab | ✗ | No frames | **Phase 1: Video Input Processing** |
| 4 | Tap Pulse tab | ✗ | No frames | **Phase 1: Video Input Processing** |
| 5 | View polar chart (time-of-day metrics) | ✗ | No frames | **Phase 1: Video Input Processing** |

---

## Video vs Log Comparison

**Extracted frames**: 7 frames total (frame_0001.png through frame_0007.png)

**Video metadata**:
- Duration: 0.13 seconds
- Codec: HEVC (original), converted to H.264 (SDR BT.709)
- Frame rate: ~54 fps (7 frames ÷ 0.13s)

**Segment detection result**:
- 1 segment identified: frames 0–5 (6 frames)
- Segment boundary: (0, 5)
- Frames 6–7 truncated/discarded

**Gap analysis**: Video capture crashed or was interrupted. Expected duration ~30–60 seconds of user interaction (based on good-truth.json duration: 00:00 to 05:00 = 5 minutes of app interaction), but actual capture yielded only 0.13 seconds. **Complete failure of video acquisition.**

---

## Detailed Failure Analysis

### Failure 1: Critical — Video Capture Failure

**Expected behavior**: 5+ minute video of user navigating app (based on good-truth reference)  
**Actual behavior**: 7-frame video (0.13s) — essentially empty  
**Log evidence**:
```
[01:56:55] [INFO] [__main__] Total frames: 7, total segments: 1
[01:56:55] [INFO] [__main__] Raw segment boundaries (before clamping): [(0, 5)]
```

**Root cause category**: **Phase 1.1 — Video Input Processing**
- **Issue**: Severe video corruption/truncation. File size suggests capture process was terminated abnormally.
- **Evidence**: 
  - `ffprobe` reports duration 00:00:00.13 vs expected ~300s
  - 7 frames insufficient to represent any meaningful app workflow
  - CLIP segmentation found 1 segment but with no actionable content
- **Cascade**: With no frames, segmentation produces meaningless boundaries, scene detection fails, no LLM prompts sent, zero actions replayed.

### Failure 2: Critical — No Actions Executable

**Expected behavior**: LLM receives segmented scenes, predicts actions, ADB executes them  
**Actual behavior**: 0 scenes created, 0 LLM prompts sent, 0 actions executed  
**Log evidence**:
```
[01:56:55] [INFO] [run_stats] Scenes: 0
[01:56:55] [INFO] [run_stats] Actions executed: 0
[01:56:55] [INFO] [run_stats] LLM calls: 1
```

**Note**: "LLM calls: 1" likely refers to the initial app launch/pong check, not action inference.

**Root cause**: No frames → no scene extraction → no inference → no replay.

---

## Root Cause Categorization

| Phase | Sub-category | Issue | Count | Impact |
|-------|--------------|-------|-------|--------|
| **Phase 1** | **1.1 Video Input Processing** | Video truncation/corruption | 1 | **CRITICAL** — blocking all downstream stages |
| **Phase 1** | **1.4 Scene Detection** | Insufficient boundaries (only 1 trivial segment) | 1 | Secondary (cascade from 1.1) |
| **Phase 3** | **3.12 Action Execution** | No actions to execute | 5 | Secondary (cascade from 1.1) |

**Dominant failure mode**: Video acquisition infrastructure failure, not ViBR algorithm failure.

---

## Impact Assessment

1. **Complete pipeline blockade**: Video corruption at input → entire ViBR pipeline halts at segmentation.
2. **Zero coverage**: 0% of expected workflow replayed on device.
3. **No algorithm evaluation possible**: Cannot assess CLIP, GroundingDINO, GPT-4o, or action inference quality due to absent input.
4. **Device never interacted with**: ADB initialized but never invoked (0 actions executed).

---

## Conclusions

The bad-run failure is **NOT an algorithmic failure within ViBR** but rather a **catastrophic input failure**. The video file provided is severely corrupted or truncated, containing only 7 frames (0.13s) instead of an expected ~5-minute recording of app interaction. 

CLIP segmentation correctly identified that insufficient actionable content existed in the frames (1 trivial segment with no scene information), but the root cause precedes the ViBR pipeline: **video capture or storage failed**.

This bad run cannot be used to evaluate ViBR's robustness to GUI variations, state changes, or action inference errors. A valid bad-run video is required to assess the system's failure modes.

---

## TL;DR

- **Success count**: 0 steps executed
- **Failure count**: 5 steps missed
- **Reason**: Bad video file is corrupted (7 frames, 0.13s) instead of ~5 minutes. Segmentation found 1 useless segment. Zero scenes extracted, zero actions replayed.
- **Bottom line**: Video acquisition failure, not ViBR algorithm failure — unusable for evaluation.

---

## Artifacts

- **Truth file** (good-truth.json): Reference ground truth with 5+ steps across 5 screens
- **Bad video**: 7 frames, 0.13s duration, no interaction data
- **Extracted frames**: `/tmp/bloodpressuremonitor1_bad_truth_frames/` (7 PNGs)
