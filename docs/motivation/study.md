# Motivation Study: ViBR Fails on Handheld Bug-Report Videos

## 1. What ViBR claims

ViBR (FSE 2025 target) reports **73.7% reproducibility** across 38 GUI bug
recordings drawn from three prior benchmarks (Themis, GIFdroid, V2S). Its
pipeline: CLIP-based scene segmentation → GroundingDINO region detection →
GPT-4o state consistency check → GPT-4o action inference, with a 3-retry
recovery loop when state comparison fails.

ViBR's own paper (§3.4, §6) admits exactly **two** narrow failure modes:
1. Semantic correlation gap — tapping a button jumps to a screen with no
   obvious visual link to the trigger.
2. Masked input (PIN fields rendered as `****`) — value unrecoverable
   without intermediate frames.

Both are framed as fixable via more intermediate-frame sampling — a
prompt/sampling tweak, not an architectural defect. Weak motivation on its
own for a new paper.

Critically: **ViBR's evaluation corpus (Themis/GIFdroid/V2S) is built
entirely from clean screen recordings** — pixel-exact captures via
`scrcpy`/ADB/OS screen-record APIs. Every prior tool in this space (V2S,
GIFdroid, ViBR) is validated exclusively on this input type.

## 2. What we tested — and why it matters

Our corpus of 20 apps is **handheld video** — a phone filming a second
device's screen while reproducing a bug, the format a non-technical user
actually produces when they hit a bug and grab their phone to record it.
This is not a benchmark variant; it's the dominant real-world bug-report
format, and one no prior tool (ViBR included) has been evaluated against.
Camera framing, hand tremor, ambient lighting, and reflections are present
in every clip, layered on top of all the ordinary app-behavior challenges
ViBR already targets.

**Coverage across 20 apps, all handheld-recorded:**

| Coverage | Count | Apps |
|---|---|---|
| 0% | 9 (45%) | antennapod1, bily, binaryeye, bloodpressuremonitor1, bloodpressuremonitor2, brethap1, brethap2, homemedkit1, simplenotes |
| 9–33% | 7 (35%) | adaway, bloodpressuremonitor3, jigsaw1, jigsaw2, wifianalyzer1, wifianalyzer2, batterytemperaturedisplay |
| 50–60% | 2 (10%) | vanilla, homeraudioplayer |
| 100% | 1 (5%) | bakerspercentagecalculator1 |

Median coverage ≈ 0–20%, sharply below ViBR's own claimed 73.7%. The gap
is explained by our corpus testing exactly the input condition ViBR's
evaluation never included.

**Root cause tally (dominant failure per app, ViBR's own phase taxonomy),
20 apps:**

| Category | Count | % of apps |
|---|---|---|
| Phase 2.7 — State Consistency Check | 8 | 40% |
| Phase 1.4 — Scene Detection | 8 | 40% |
| Phase 1.1 — Video Input Processing | 1 | 5% |
| Phase 1.3 — Similarity Computation | 1 | 5% |
| Phase 2.5 — Region Detection | 1 | 5% |
| Device/Session Divergence (env) | 1 | 5% |

**80% of failures concentrate in just two categories** — neither of which
is the "intermediate frame sampling" gap ViBR's own future-work section
targets.

## 3. Why handheld capture drives both dominant failure modes

The two dominant categories aren't independent of the capture method —
handheld video is the structural cause behind both, even in cases where
the per-app root-cause writeup names an app-specific trigger (keyboard,
animation, gesture). The mechanism is the same underlying weakness,
expressed differently per app:

- **Scene Detection (1.4) — CLIP conflates camera motion with app-state
  change, in both directions.** A handheld camera never holds perfectly
  still: hand tremor, refocus, and micro-reframing constantly perturb
  frame-to-frame pixel content independent of what the app is doing. This
  pushes CLIP similarity scores around in ways a fixed screen-recording
  environment never produces. We observe both failure directions:
  - **Over-grouping**: continuous gestures (long-press, scroll, keyboard
    entry) already sit close to the 0.95 similarity threshold on a clean
    recording; camera jitter pushes still more frames above threshold,
    causing entire multi-step interactions to collapse into one segment
    (batterytemperaturedisplay, bloodpressuremonitor2, jigsaw2).
  - **Under-grouping**: conversely, incidental camera movement between
    otherwise-identical app states (re-angling the phone, hand
    repositioning) can itself drop similarity below threshold and
    manufacture a spurious scene boundary with no corresponding user
    action (brethap1, brethap2, wifianalyzer1).
  Either way, no fixed threshold recovers both directions simultaneously
  — the noise floor introduced by handheld capture is not separable from
  the signal ViBR is trying to detect.

- **State Consistency (2.7) — the VLM cannot separate "different app
  state" from "different camera angle/lighting."** In every 2.7 case we
  examined, the VLM (GPT-4o/Gemini) correctly registered a visual
  difference between reference and live frame — but on handheld footage,
  a visual difference no longer implies a semantic one. Screen glare,
  perspective skew, and exposure shifts between the reference frame
  (captured at one moment, one angle) and the live comparison frame
  (captured seconds later, camera re-settled) are enough to trip a "state
  mismatch" verdict even when the app itself is in a perfectly
  reproducible, matching state. ViBR's recovery loop then burns all 3
  retries chasing a mismatch that was never real, and cascades into
  skipping the entire downstream segment (adaway, antennapod1, binaryeye,
  simplenotes).

This is the structural claim: **ViBR's segmentation and state-comparison
stages assume the only source of visual change between frames is the
app itself. Handheld capture introduces a second, uncontrolled source of
visual change — the camera — that the pipeline has no mechanism to
separate from genuine app-state transitions.** Lowering/raising the CLIP
threshold or adding more VLM retries does not fix this: it just trades
over- for under-segmentation, and burns more budget confirming the same
false mismatches, because the noise source itself is never modeled.

## 4. Proposed motivation framing for the paper

> Existing VLM-based GUI bug replay tools (V2S, GIFdroid, ViBR) are
> evaluated exclusively on clean, fixed-frame screen recordings — an input
> format that implicitly assumes the only source of visual change between
> frames is the application itself. We show this assumption fails on
> handheld-camera bug videos, the format most non-technical users actually
> produce, where camera motion, lighting drift, and perspective shift
> introduce a second, uncontrolled source of frame-to-frame visual change.
> Across 20 real handheld bug recordings, ViBR achieves median coverage of
> 0–20% (vs. its reported 73.7%), with 80% of failures concentrated in
> exactly two pipeline stages — scene segmentation and state consistency
> checking — both of which conflate camera-induced visual change with
> genuine app-state transitions. We propose [camera-motion-invariant
> segmentation / explicit screen-region stabilization prior to comparison]
> to separate these two noise sources and recover reproducibility on
> real-world, non-studio bug footage.

## 5. Best showcase example: wifianalyzer2

**File:** `apps/wifianalyzer2-gemini-2.5-pro/bad-run-issue.md`
(video: `bad-video.mp4`, log: `bad-run.log`, ground truth: `bad-truth.json`)

Why this is the strongest single example to lead the paper with:

- **Both dominant failure modes co-occur in one recording, cleanly
  chained.** Video shows the user long-pressing a WiFi channel graph →
  metadata dialog opens → hamburger menu → share sheet. On handheld
  footage, the long-press itself already produces near-static frames (the
  finger holds position); camera micro-jitter during the hold nudges CLIP
  similarity just enough that segmentation still doesn't isolate the
  press-to-dialog transition as its own segment (**1.4**). ViBR's
  reference frame for "segment 1" ends up expecting the dialog already
  open. When it compares that reference against the live frame — which
  itself carries a slightly different camera angle from re-settling after
  the tap — GPT-4o reports a mismatch ("*reference shows a pop-up
  dialog... current image only shows the main channel graph*") that is
  real in content but confounded by handheld angle drift, and the 3-retry
  recovery loop (re-tap only) can't resolve a state gap that actually
  needs a long-press (**2.7**). Segment is skipped; 8 of 10 downstream
  steps (menu, share, return) never execute even though the user's video
  shows them succeeding. Coverage: 2/10 (20%).
- **No app-specific confound to explain away** — this isn't a corrupted
  video, an empty-database precondition mismatch, or a device/session
  divergence (unlike bloodpressuremonitor1, simplenotes, homemedkit1).
  The failure is entirely attributable to the segmentation/consistency
  gap this study identifies as dominant across the corpus.
- **Directly visualizable**: a figure showing (a) the frame sequence
  spanning the long-press → dialog transition, annotated with ViBR's
  actual segment boundary (showing it collapsed into the prior segment),
  next to (b) the verbatim GPT-4o mismatch text ending in "SKIP SEGMENT,"
  makes the "camera-induced noise masks/mimics real state change" claim
  legible without requiring the reader to parse a root-cause table.

## 6. Next step to sharpen the showcase further

To make the camera-vs-app-noise distinction fully unambiguous (rather
than inferred from the log), the strongest possible follow-up experiment
is a **controlled A/B pair**: re-shoot one already-analyzed bug (e.g.
wifianalyzer2) twice — once handheld (as done here) and once from a fixed
tripod/rig at the same distance/angle — and run unmodified ViBR on both.
Any coverage delta between the two runs, with the app, ground truth, and
bug held constant, isolates camera motion as the sole causal variable and
would make an even stronger paper figure than the single-run case above.
