# Run Issue Report: bloodpressuremonitor1 (bad run)

**App:** bloodpressuremonitor1  
**Model:** gemini-2.5-pro  
**Quality:** bad  
**Pipeline status:** incomplete  
**Scenes detected:** 0  
**Actions executed:** 0  
**Segments detected:** 1  

---

## Executive Summary

The bad run for bloodpressuremonitor1 completed video segmentation but produced **0 scenes** for replay. Analysis reveals a fundamental limitation: the video contains only a single stable segment (no frame transitions), which is insufficient to trigger the scene-to-scene comparison loop. Scene replay requires **at least 2 distinct segments** (i.e., at least one transition between states). With only 1 segment detected, the replay loop `for i in range(len(segments) - 1)` executes zero iterations, yielding 0 action opportunities and 0 verification steps.

---

## Root Cause Analysis

### Segmentation Logic Constraint

The ViBR replay architecture operates on transitions between consecutive segments:
- Each "scene" is defined as the boundary between segment `i` and segment `i+1`
- With N segments, there are N-1 scenes to replay
- **Constraint:** minimum 2 segments required → 1 scene → ≥1 action execution opportunity

**Log evidence:**
```
Total frames: 7, total segments: 1
Raw segment boundaries: [(0, 5)]
Clamped segment boundaries: [(0, 5)]
Scenes: 0
Actions executed: 0
```

### Why Only 1 Segment Detected?

**Possible causes:**

1. **Video is too short or too uniform** — all frames are sufficiently similar (CLIP similarity above threshold) that no state boundary is detected
2. **CLIP segmentation threshold too high** — `stable_sim_threshold: 0.95` may be masking legitimate transitions in low-motion video
3. **Insufficient frame count** — 7 frames total; with `leading_segment_min_frame: 2`, the algorithm may collapse short sequences into a single stable region

---

## Limitations & Impact

### Stage 1: Action Segmentation — Insufficient Segment Boundaries

**Category:** Upstream segmentation failure (not a ViBR stage failure, but a prerequisite constraint)

The video does not contain sufficient UI state transitions to create multiple segments. This is **not a model hallucination, layout mismatch, or dynamic content issue** — it is a fundamental property of the input video itself.

**Impact:** 0% action coverage. The agent could not initiate replay because no state transitions were available to compare.

---

## Summary of Findings

| Aspect | Finding |
|---|---|
| **Segmentation phase** | Completed successfully; 1 stable segment detected |
| **Scene generation** | 0 scenes (requires ≥2 segments; only 1 available) |
| **Replay loop** | Did not execute (empty iteration range) |
| **Action coverage** | 0% (0 actions executed, infinite gap) |
| **Root cause** | Input video lacks sufficient state transitions |

---

## Recommendations for Future Analysis

1. **Generate longer videos** capturing at least 2 distinct UI states (e.g., app open → action performed → result shown)
2. **Verify segmentation threshold** — may need to lower `stable_sim_threshold` if legitimate transitions are being merged
3. **Compare with reference (good) run** — provide a good-run artifact to establish expected segment count and baseline behavior
4. **Consider alternative segmentation** — if CLIP merges transitions aggressively, compare against SSIM algorithm baseline

---

## Conclusion

The bloodpressuremonitor1 bad run failed **upstream of ViBR's core functionality**, not due to model limitations or GUI comparison failures. The video itself does not contain sufficient state transitions to trigger replay. This is a **data/input issue**, not a framework issue. To measure bug reproduction capability, provide video pairs (good/bad) with multiple distinct scenes and user actions.
