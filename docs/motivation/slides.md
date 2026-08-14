# Motivation Presentation — Slide-by-Slide Content

> Presentation content for my professor, motivating a **new paper**. Angle: I ran
> ViBR (Video-Based bug Reproduction) on **handheld videos** — a phone filming
> another phone's screen — an input distribution ViBR was never designed or
> evaluated for (its datasets are 100% screen recordings). 19 apps, true root
> causes traced, one genuine unaddressed research gap surfaced.
>
> Each slide below gives **text to show** + **exact image/diagram to use**.
> Numbers sourced from `docs/report-root-causes.md`. Image paths verified on disk.

---

## Image asset map (verified present)

| Slide use | Path |
|---|---|
| ViBR overview figure | `images/vibr_architecture.png` |
| **Finger occlusion (headline)** | `images/adaway-finger-occlusion-dino.png` |
| Adaway detected regions (target missing) | `images/adaway-relevant-regions-target-missing.png` |
| Adaway execution result | `images/adaway-execution-labeled.png` |
| Zero-region / FAB missed | `images/homeraudioplayer-zero-regions-dino.png`, `images/bloodpressuremonitor3-zero-regions-dino.png` |
| Distorted reference frame (HDR→SDR) | `images/jigsaw1-distorted-frame-dino.png` |
| Wrong segment-0 reference (Sessions screen) | `images/brethap2-wrong-segment0-reference-dino.png` |
| Rapid taps merged (calculator) | `images/vanilla-rapid-taps-frame0-dino.png`, `images/vanilla-rapid-taps-frame1-dino.png`, `images/vanilla-rapid-taps-frame2-dino.png` |
| Form-filling merged (5 steps → 2 segments) | `images/bloodpressuremonitor2-form-merged-frame0-dino.png`, `images/bloodpressuremonitor2-form-merged-frame1-dino.png` |
| Proposed method diagram | `images/src-llm-architecture.svg` |

**Diagrams to author** (mermaid or slide tool): pipeline flow, poisoned-input
propagation, similarity curve, root-cause bar chart.

---

# SLIDES

## Slide 1 — Title
- **Title:** Reproducing Bugs from *Handheld* Videos: Where ViBR Breaks
- **Subtitle:** A root-cause study of automated GUI bug reproduction on camera-captured video
- Name / affiliation / date.
- **Image:** split image — left: clean screen recording; right: handheld photo of a phone screen (glare/finger visible). States the whole thesis at a glance.

## Slide 2 — What is ViBR
- ViBR = automated pipeline. **Input:** a video of a bug being reproduced. **Output:** the bug replayed on a real device via ADB.
- Three phases: **segment** the video into actions → **compare** recorded GUI state vs live device → **replay** actions on device.
- **Image:** `images/vibr_architecture.png` — ViBR **Figure 2 Overview**. Anchor figure — referenced again later.

## Slide 3 — The pipeline, phase by phase
Use these exact stage IDs (they map to the root-cause taxonomy and recur through the deck):

- **Phase 1 — Action Segmentation**
  - **1.1** Video Input Processing (decode / frame extraction)
  - **1.3** Similarity Computation (CLIP/SSIM cosine similarity between frames)
  - **1.4** Scene Detection (dip below `stable_sim_threshold=0.95` → boundary; classify tap/scroll/input)
- **Phase 2 — GUI State Comparison**
  - **2.5** Region Detection (GroundingDINO finds candidate interactive regions)
  - **2.6** ROI Selection (VLM picks the Region of Interest from candidates)
  - **2.7** State Consistency (VLM YES/NO: recorded state matches live state?)
- **Phase 3 — Bug Replay on Device**
  - **3.10** GUI Perception (ADB screenshot + UIAutomator XML) → VLM action inference → tap/scroll/input/end

- **Diagram:** horizontal 3-box pipeline, each box exploded into sub-stages. Author as mermaid (see Design notes). Color-code the stages I later flag as failure origins.

## Slide 4 — What I tested (the data)
- **Input = handheld video capture:** a phone filming *another* phone's screen while a human reproduces a bug. **Not** screen recording.
- Why it matters up front: ViBR's paper datasets (**Themis, GIFdroid, V2S**) are **100% screen recordings** — no camera ever between viewer and screen.
- **19 apps**, Gemini-2.5-pro as VLM, real emulator replay.
- Each run self-labeled a failure category; I re-traced every one to its **true** origin.
- **Image:** side-by-side — clean screen-recording frame vs a handheld frame (e.g. `images/adaway-finger-occlusion-dino.png`, which shows glare/angle). Caption: *"Same UI content. Fundamentally different pixel distribution."*

## Slide 5 — Method: finding the *true* root cause
- Problem: a failure becomes *visible* at a late stage (e.g. "state mismatch" in **2.7**) but was *caused* earlier (bad segment reference from **1.4**).
- Method: I traced each run's log **backward** from the final failure to the **earliest stage whose output was already wrong** — everything downstream is a healthy stage inheriting a *poisoned input*.
- Result: **8 of 19 apps (42%) diverge** from their self-labeled category once traced to true origin. Most common misattribution: blaming **2.7 State Consistency** when the check was working correctly.
- **Diagram:** poisoned-input propagation — green chain of stages, one **red** upstream stage, red arrow flowing downstream and turning the label red at the *wrong* (later) place.

## Slide 6 — All root causes at a glance
| Rank | Root cause | Apps |
|---|---|---|
| 1 | 1.4 Scene Detection | 9 |
| 2 | 2.5 Region Detection | 5 |
| 3 | 1.3 Similarity Computation | 2 |
| 4 | 2.6 ROI / stale recovery region | 1 |
| 5 | 2.7 State Consistency (genuine + false-positive) | 2 |
| 6 | 3.10 GUI Perception (capture-time divergence) | 1 |
| 6 | 1.1 Video Input (corrupted capture) | 1 |

- **Chart:** horizontal bar chart of counts, plain bars (no special highlight color) — let the numbers speak.

## Slide 7 — Each cause in one line, with a real example
Rapid-fire, one line + one app each:
- **1.4 Scene Detection** — rapid taps below CLIP's sensitivity get merged into one segment. *vanilla: 6 calculator taps in 6 frames → 3 segments.*
- **2.5 Region Detection** — DINO returns zero or wrong regions. *adaway: finger over the "Allowed" card blocks detection.*
- **1.3 Similarity Computation** — fade-in animations keep SSIM >0.95, no boundary fires. *bily: 745 frames → 1 segment.*
- **2.6 ROI / stale recovery** — recovery re-taps the old region instead of re-detecting. *bakerspercentagecalculator1.*
- **2.7 State Consistency (genuine)** — device data reset vs video had pre-existing notes. *simplenotes: reference 2 notes, device empty.*
- **2.7 (false positive)** — "same screen" judged true while slider *value* differs (2 vs 4). *jigsaw1 seg 1.*
- **3.10 GUI Perception** — live screenshot already on the wrong screen before any compare. *binaryeye: file browser vs settings.*
- **1.1 Video Input** — corrupted/truncated capture (0.13s, 7 frames). *bloodpressuremonitor1.*
- **Image:** none (or tiny thumbnail per row). Keep dense and fast.

---

# MAIN CAUSE #1 — Scene Detection (biggest count, not the paper)

## Slide 8 — Scene Detection: what breaks (3 examples)
Dominant true cause: **9 of 19 apps.** Two failure directions — under-segmentation (rapid actions merge) and wrong boundary (a mid-video frame gets picked as "segment 0"). Three concrete examples:

1. **brethap2 — wrong segment-0 reference.** The reference frame extracted for segment 0 is the *Sessions* screen, not the video's true start (main screen). CLIP found *a* stable region — the wrong one.
   - **Image:** `images/brethap2-wrong-segment0-reference-dino.png`
   - **Caption:** *"CLIP picked a stable frame — the wrong one."*
   - **Why:** CLIP's stability check only asks "is this frame similar to the last," not "is this the video's actual start." A long static hold (frames 0–1002, avg similarity 0.9979) anywhere in the video looks exactly like a valid segment-0 candidate, so the algorithm locks onto whichever stable span it meets first — here, the Sessions screen — with no mechanism to check it against the true recording start.

2. **vanilla — rapid taps merged.** 6 calculator button taps in 6 consecutive frames collapse into 3 segments; each segment's single inferred action can't represent the 2 taps it actually contains.
   - **Image:** `images/vanilla-rapid-taps-frame0-dino.png` next to `images/vanilla-rapid-taps-frame1-dino.png` (or add `images/vanilla-rapid-taps-frame2-dino.png` for a 3-frame strip)
   - **Caption:** *"6 taps, 6 frames — CLIP sees one continuous scene."*
   - **Why:** each calculator tap changes only a few dozen pixels (one digit/operator glyph); CLIP's embedding is dominated by the mostly-unchanged background and layout, so consecutive tap-frames stay above the 0.95 threshold and never register as a boundary. Six taps in six frames is exactly the rapid, low-pixel-delta regime the fixed threshold cannot see.

3. **bloodpressuremonitor2 — form-filling merged.** A 32-second, 5-step recipe-entry flow collapses into 2 segments; keyboard/field-focus changes fall below CLIP's sensitivity.
   - **Image:** `images/bloodpressuremonitor2-form-merged-frame0-dino.png` next to `images/bloodpressuremonitor2-form-merged-frame1-dino.png`
   - **Caption:** *"5 form-filling steps, 2 detected segments."*
   - **Why:** form-filling changes are localized to a small keyboard/field-focus region per keystroke; the surrounding form layout dominates the frame-to-frame similarity score, so five distinct field-entry steps never individually cross the dissimilarity threshold and collapse into 2 broad segments instead of 5.

**General cause:** in all three cases, CLIP is answering "how visually similar is this frame to the last" — a holistic, whole-frame similarity score — when the real question is "did a discrete user action occur." Small, spatially localized changes (a digit, a keyboard, a field highlight) get diluted by the much larger unchanged background, so they never cross a single fixed similarity threshold (0.95) regardless of how many real actions occurred. The failure is a mismatch between what CLIP measures (scene similarity) and what the segmentation needs to measure (action occurrence), not a bug in any individual video.

## Slide 9 — Scene Detection: does handheld make it worse? + verdict
- **Mostly no.** Sub-second tap sequences produce the same CLIP curve whether screen-recorded or handheld. A screen recording of rapid "3","+","6" looks the same to CLIP.
- Minor compounding only: 1fps frame extraction loses fast taps regardless of source; handheld adds slight irregular frame rate from autofocus/blur. Not the driver.
- **Verdict: engineering fix, not new research.** Lower/adaptive threshold, motion-vector signals, higher sampling in suspected rapid-interaction windows. ViBR already uses a supplementary signal (OCR keyboard detection) — same family.
- **Image:** similarity-curve diagram — a flat line hovering ~0.99 across a span that actually contains 3 taps; the 0.95 threshold line never crossed. Real numbers from brethap: seg 0 (frames 0–1002), **avg 0.9979**, **min 0.9556**, **0 frames below threshold.**

---

# MAIN CAUSE #2 — Region Detection, the research gap

## Slide 10 — Region Detection: what breaks (3 examples)
**5 apps.** GroundingDINO is prompted with generic terms ("button", "icon", "text field") to find candidate regions. Downstream is healthy but starved: no region → ROI selection has nothing → VLM guesses `swipe`/`wait` → recovery loops → run dies at 0%. Three concrete examples:

1. **adaway — finger occlusion.** A finger physically covers the target UI element in the keyframe; DINO boxes 12 other elements but never the occluded one.
   - **Image:** `images/adaway-finger-occlusion-dino.png`
   - **Caption:** *"DINO detected nothing under the finger — the target was never a candidate."*
   - **Why:** GroundingDINO detects regions from the pixels actually visible in the keyframe; a finger physically between the camera and the screen replaces the target element's pixels with skin/shadow, so there is no "button" or "card" signal left for the open-vocabulary detector to match against — it isn't misclassifying, it's operating on a keyframe where the target genuinely no longer exists.

2. **homeraudioplayer — zero regions returned.** A small FAB icon spanning a 900-frame span falls below DINO's confidence threshold entirely.
   - **Image:** `images/homeraudioplayer-zero-regions-dino.png` (or `images/bloodpressuremonitor3-zero-regions-dino.png` as an alternate/second case)
   - **Caption:** *"The correct target — the FAB — was never a candidate."*
   - **Why:** the FAB is a small icon relative to the frame, and DINO's open-vocabulary detection assigns confidence scores partly based on visual salience/size; a small, low-contrast target sitting below the confidence threshold gets filtered out entirely, even though it is fully visible and unoccluded.

3. **jigsaw1 — distorted reference frame.** An HDR-to-SDR phone-codec conversion leaves the reference frame "heavily distorted," starving DINO of a clean input to detect against.
   - **Image:** `images/jigsaw1-distorted-frame-dino.png`
   - **Caption:** *"A camera-codec artifact, not a detector failure — DINO had nothing usable to work with."*
   - **Why:** the phone-camera capture pipeline's HDR-to-SDR tone mapping alters color/contrast in ways screen-recorded frames never experience; the resulting reference frame is visually distorted enough that DINO's detector — trained on natural, undistorted imagery — has no clean edges or color contrast to anchor a region proposal on.

**General cause:** in all three cases, GroundingDINO is being asked to find a region in a keyframe that no longer faithfully represents the UI — either because part of it is physically covered (adaway), the target's visual footprint is too small to clear the detector's confidence floor (homeraudioplayer), or the frame itself has been altered by the capture pipeline before detection ever runs (jigsaw1). The detector is not malfunctioning; it is working correctly on a keyframe that handheld capture has already corrupted, degraded, or reduced in salience — a failure mode that cannot occur when the keyframe is guaranteed to be a lossless screen capture.

## Slide 11 — Region Detection: why it happens + handheld is the cause
Two mechanisms, both amplified or **created** by handheld capture:
1. **Occlusion / visual corruption of the keyframe** — a finger physically covering the target (adaway); a distorted reference frame from HDR→SDR phone-codec conversion (jigsaw1).
2. **Low-salience / ambiguous targets** — a small FAB below DINO's confidence; near-identical buttons DINO can't disambiguate by function.

- **The key claim:** finger occlusion is **structurally impossible in a screen recording** — there is no finger between camera and screen when the screen *is* the recording source. It exists **only** because capture = a second camera filming a touched physical device.
- Handheld also injects **glare, off-axis perspective, hand-tremor motion blur, variable lighting, autofocus artifacts** — none of which a screen recording can produce, and none of which DINO (or CLIP) was trained/evaluated against.
- **Image (the money shot):** `images/adaway-finger-occlusion-dino.png` (finger over "Allowed" card) **next to** `images/adaway-relevant-regions-target-missing.png` (DINO's boxes, target missing). Full-bleed. A human can *see* the finger and *see* the missing box.

## Slide 12 — Region Detection: verdict → the new paper
- **This is the genuine research gap.** ViBR's entire Phase 2 (DINO region detection + VLM ROI + attention state comparison) was designed and evaluated **exclusively on clean, occlusion-free, artifact-free screen recordings.** Its dataset (Themis, GIFdroid, V2S) excludes camera-captured video *by construction*. Its threats-to-validity section never considers imaging artifacts layered on UI content.
- **Proposed contribution:** occlusion- and artifact-robust region detection / GUI state comparison for **camera-captured** bug videos. Directions:
  - a pre-processing dehaze / de-occlusion step,
  - a region-detection model fine-tuned on camera-captured UI imagery,
  - **multi-frame aggregation** to vote out transient occlusions (finger blocks frame N but not N+1).
- **Punchline:** *"ViBR can't surface this problem — its dataset excludes it. That's exactly why it's a paper."*
- **Image:** the screen-recording-vs-handheld comparison (callback to Slide 4), now annotated with the three artifact types (occlusion / glare / blur) via arrows. Alternative: a diagram of the multi-frame voting fix.

---

# CLOSE

## Slide 13 — Why not the other causes? (pre-empt the question)
One line each on why the runner-ups are not the paper:
- **1.3 Similarity** — same family as 1.4, capture-independent, engineering.
- **2.6 ROI recovery** — control-flow gap: recovery should re-run DINO on the *live* frame. Small fix.
- **2.7 State Consistency** — simplenotes is a test-harness / data-parity issue; jigsaw1 is a narrow VLM prompt fix (check *values*, not just layout).

Reinforces that Region Detection is the one cause where handheld capture is the structural root.

## Slide 14 — Summary / takeaway
- 19 apps, handheld video, ViBR pipeline.
- **Scene Detection (1.4)** dominant by count — but a known engineering problem, capture-independent.
- **Region Detection (2.5) is the one cause where handheld capture is the structural root** — occlusion, glare, blur, codec artifacts that screen recordings cannot contain.
- **The new paper:** robust GUI region detection & state comparison for **camera-captured bug-reproduction videos** — a problem ViBR's own design and dataset cannot address.
- **Image:** root-cause bar chart + the finger-occlusion thumbnail. One glance = the whole talk.

---

# PROPOSED METHOD — src_llm

## Slide 14.5 — From root cause to design decision
The bridge: why src_llm's architecture is a direct answer to Cause #2's mechanism, and why Cause #1 stays out of scope.

- **Cause #2's mechanism, restated:** ViBR's Region Detection runs **per step, on one live frame, with no fallback.** A finger, glare, or a distorted frame in that single frame is fatal — there's no other frame to check against (adaway, homeraudioplayer, jigsaw1, Slide 10).
- **The direct counter:** src_llm's Stage 1 builds memory from **multiple keyframes sampled across the whole video**, not one frame per step. If one keyframe is occluded, adjacent keyframes of the same UI state are still candidates — an aggregation point ViBR's single-shot detection never has.
- **What this buys, precisely:** Stage 2 acts from **memory**, not from re-detecting the target in a fresh device screenshot each time — so a bad live frame at automation time doesn't kill the step the way it kills ViBR's DINO call.
- **Scoped honestly:** this is a structural opening, not a finished fix. A bad frame can still enter the keyframe set today. The actual contribution is the mechanism that goes *in* that opening — multi-frame voting / robust keyframe selection before memory is committed (detailed Slide 17).
- **Why Cause #1 doesn't drive this design:** Scene Detection's failure (CLIP blind to small localized changes) is orthogonal — it lives in *which* frames get selected as keyframes, not in *whether* a single bad frame is fatal. src_llm's keyframe selector (SSIM-based) could still under-segment the same way; that's an acknowledged, separate engineering fix, not what this architecture targets.
- **One line:** *"Cause #2 is fatal because ViBR has one frame and no memory. src_llm's whole design is built around having many frames and a memory — that's the direct line from problem to method."*
- No image — this is the connective-tissue slide; the diagram appears next.

## Slide 15 — From gap to proposal
- ViBR's Region Detection fails on handheld video because it re-detects, per step, against a live frame that may carry occlusion, glare, or codec artifacts — with no memory of what it already understood about the task.
- I propose **src_llm**: a two-stage architecture that analyzes the video **once** to build a reusable "memory" of the task, then uses that memory — not repeated raw-frame re-detection — to drive on-device automation.
- **Image:** `images/src-llm-architecture.svg`

## Slide 16 — Architecture: two stages
- **Stage 1 (offline, once per video):** extract frames → select keyframes (SSIM-filtered, near-duplicates dropped) → VLM analyzes the keyframe set → structured `memory.md` (task summary, ordered steps, UI elements, completion criteria).
- **Stage 2 (online, per automation step):** load memory → screenshot device → VLM decides the next action from memory + current screen → execute (tap / type / scroll / wait) → log → repeat until done.
- **Image:** `images/src-llm-architecture.svg` (same diagram — the full pipeline)

## Slide 17 — Why this addresses the handheld-video gap
- Memory is built **once** from the whole video: keyframes are selected for stability and diversity across the recording, not derived fresh per step from whatever single live frame happens to be in front of the detector.
- A single bad frame (finger occlusion, glare, one distorted keyframe) still has to survive keyframe filtering to poison the memory — the same failure *mode* remains possible, but the two-stage split creates a natural aggregation point (multi-frame keyframe voting, robust selection before memory is committed) that ViBR's per-step live DINO detection has no equivalent of.
- Scoped honestly: this is the architectural motivation for *why* a memory-based design is a better substrate for the occlusion/artifact fix proposed earlier — not yet a claim that src_llm already solves occlusion. That robustness mechanism is the follow-on contribution this architecture enables.

## Slide 18 — Efficiency as a secondary benefit
- The two-stage split also cuts cost: one full video analysis instead of re-analyzing per step — roughly a single ~2000-token pass versus ~2000 tokens repeated at every step.
- Secondary, practical benefit — the paper's main contribution is robustness to capture artifacts, not efficiency.

---

# DESIGN NOTES (for whoever builds the deck)

**Diagrams to author** (recommend mermaid → render to PNG):
1. **Pipeline flow (Slide 3):** 3 phases → sub-stages, color-code failure origins.
2. **Poisoned-input propagation (Slide 5):** green chain, one upstream red node, red arrow mislabeling a downstream node.
3. **Similarity curve (Slide 9):** flat ~0.99 line, 0.95 threshold, 3 hidden taps.

**Charts (Slides 6 & 14):** horizontal bar chart of root-cause counts — plain, no single bar singled out in color; let the count differences carry the message.

**Photo evidence (Slides 4, 8, 10, 11):** pull the real PNGs from the asset map. The **adaway finger-occlusion pair (Slide 11) is the emotional core** — make it full-bleed. Slides 8 and 10 each carry 3 distinct app examples with images, per the Scene Detection and Region Detection sections above.

**Consistency:** keep the stage IDs (1.1 / 1.3 / 1.4 / 2.5 / 2.6 / 2.7 / 3.10) as a recurring visual key so the audience tracks which box each failure lives in — tie every example back to the Slide 3 pipeline diagram. Present all stage IDs with equal visual weight; don't single one out typographically outside its own dedicated slides.

**Proposed method (Slides 15–18):** use the existing `images/src-llm-architecture.svg` diagram for Slides 15 and 16 — no new diagram authoring needed for this section.
