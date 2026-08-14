# ViBR Bad-Run Root Cause Analysis

Context: ViBR (`docs/research-paper/ViBR.pdf`) was designed and evaluated on **screen recordings** (native iOS/Android screen capture — GUIRecorder-style, GIFdroid/V2S/Themis datasets). Our data is **handheld video capture**: a phone filming another phone's screen while a bug is reproduced. This is a materially different input distribution than anything in the paper's evaluation, and it matters for several of the causes below.

The pipeline has three phases (paper §2):

- **Phase 1 — Action Segmentation**: CLIP embeds Y-luminance of consecutive frames, computes cosine similarity, groups frames into scenes at similarity dips (fixed `stable_sim_threshold: 0.95`, `stable_interval_threshold: 1`), and classifies each scene as tap/scroll/input via similarity-curve shape + OCR keyboard detection.
- **Phase 2 — GUI State Comparison**: GroundingDINO detects candidate interactive regions in a frame → VLM (GPT-4o) selects the Region of Interest (ROI) from candidates → VLM does an attention-guided YES/NO comparison between recorded and live GUI state.
- **Phase 3 — Bug Replay on Device**: fixed action space (tap/scroll/input/end) + ADB screenshot/UIAutomator XML perception + VLM action inference, branching on whether Phase 2 said "consistent" (replay directly) or "inconsistent" (guided exploration).

## 1. Method: how "true root cause" was determined

Each `bad-run-issue.md` self-labels a root cause category, but many labels point at the pipeline stage where the failure **became observable** — a state-mismatch warning, a "no relevant regions" log line, an LLM's wrong action guess — rather than the stage that **produced the bad input** those later stages merely reacted to correctly. To find the true root cause, each app's log timeline was traced backward from the final failure to the earliest stage whose *output* (not error) was already wrong or missing, and everything downstream is treated as a correctly-functioning stage inheriting a poisoned input. Where a report's label matches this origin, it's marked unchanged; where the label was anchored to visible symptom instead, it's reclassified with the evidence line that shows why.

Two failure modes the paper itself acknowledges (§3.3.4, Fig. 8) — (a) no clear semantic correlation between GUI states across a tap (e.g., tapping "Dropbox" leads to a screen with no visible link back), and (b) masked/obscured input fields (PIN entry shows `****`) — do **not** appear as the true cause in any of the 19 apps below. All 19 failures trace to different, more upstream causes than what the paper's own limitations section anticipates.

## 2. App-by-app true root cause

| App | Report's labeled category | **True root cause** | Evidence | Diverges from label? |
|---|---|---|---|---|
| adaway | 2.5 Region Detection | **2.5 Region Detection** — finger occlusion in keyframe blocks DINO | keyframe has finger over "Allowed Card" section | No |
| antennapod1 | 2.7 State Consistency (×6) | **1.4 Scene Detection** — segment boundaries reference screens device never reaches | segs 2–7 all skip: "reference is X screen; current is Y screen" for screens with no navigation path from prior segment | **Yes** |
| bakerspercentagecalculator1 | 2.7 State Consistency | **2.6 ROI Selection / recovery** — recovery re-taps stale region set instead of re-detecting | report itself: "region classifier (DINO) successfully detected UI elements, but... recovery mechanism doesn't re-examine region detection" | **Yes** |
| bakerspercentagecalculator2 | 2.7 State Consistency (×2) | **1.4 Scene Detection** — reference frame extracted from wrong point in video (menu/file-browser vs recipe-form flows never reconcile) | "device is NOT showing the expected app state... video and device execution are capturing different user flows entirely" | **Yes** |
| batterytemperaturedisplay | 1.4 Scene Detection + 2.5 | **1.4 Scene Detection** (confirmed primary) + 2.5 Region Detection (confirmed secondary) | `target_regions=[0]` single region for 900-frame span; segment 2 never processed | No |
| bily | 1.3 Similarity Computation | **1.3 Similarity Computation** — SSIM 0.95 threshold too high for animated overlays | "745 frames grouped into 1 segment"; fade-in menu overlay keeps SSIM >0.95 | No |
| binaryeye | 2.7 State Consistency | **3.10 GUI Perception** — initial screenshot capture itself diverged before any comparison ran | live screen showed file browser "recent" when settings screen was expected — a capture-time state divergence, not a comparison defect | **Yes** |
| bloodpressuremonitor1 | 1.1 Video Input Processing | **1.1 Video Input Processing** — corrupted/truncated capture (0.13s, 7 frames) | non-algorithmic; explicitly called out as "not a ViBR algorithm failure" | No |
| bloodpressuremonitor2 | 1.4 Scene Detection | **1.4 Scene Detection** — CLIP over-grouped form-filling into one segment | 2 segments for a 32s / 5-step video; keyboard/field-focus changes below CLIP's sensitivity | No |
| bloodpressuremonitor3 | 2.7 State Consistency | **2.5 Region Detection** — DINO returned zero regions for segment 0, forcing `wait` fallback that then loops | "No relevant regions to annotate" precedes and causes the 3 failed wait/retry cycles | **Yes** |
| brethap1 | 1.4 Scene Detection + 2.7/2.5 | **1.4 Scene Detection** (primary, breathing animation confuses CLIP) + 2.5 Region Detection (contributing, hallucinated region) | "breathing animation... CLIP not trained on mobile animations"; first detected segment references wrong (Sessions) screen | No |
| brethap2 | 1.4 Scene Detection | **1.4 Scene Detection** — CLIP merged Sessions screen and main screen into one segment | segment 0 reference frame is Sessions screen, not the actual video-start main screen | No |
| homemedkit1 | 2.7 State Consistency ("coordinate drift, dynamic content") | **1.4 Scene Detection** — segment 0 boundary anchored to Play Store frame, not true video start | report's own evidence: "the first segmentation boundary extracted a frame... that does NOT represent the true initial state" | **Yes** |
| homeraudioplayer | 1: Action Segmentation / 3.9 Action Space | **2.5 Region Detection** — `target_regions: []` in segment 0 is the actual origin | `[15:17:51] Relevant regions: {'target_regions': [], 'predicted_action': 'swipe'}` — LLM's swipe guess is downstream of empty regions | **Yes** |
| jigsaw1 | 2.7 State Consistency (false positive) | **Dual: 2.5 Region Detection** (seg 0, zero candidate regions) **+ 2.7 false-positive equivalence** (seg 1, "already on target screen" masks unset slider values) | two genuinely separate origins in one run — report actually splits these correctly | No |
| jigsaw2 | 1.4 Scene Detection | **1.4 Scene Detection** — scroll/drag gesture invisible to CLIP, merged with tap into one segment | segment 0 spans 85% of video; 3 scroll events produce zero boundaries | No |
| simplenotes | 2.7 State Consistency | **2.7 State Consistency (genuine)** — device data reset vs video recorded with pre-existing notes | reference shows 2 notes; device shows "no notes yet" — a real precondition mismatch, not a pipeline defect | No |
| vanilla | 1.4 Scene Detection + 2.5 | **1.4 Scene Detection** (primary) + 2.5 Region Detection (secondary, DINO confuses backspace/multiply) | 6 taps in 6 frames collapse to 3 segments; region 5 picked instead of region 4 for visually similar buttons | No |
| wifianalyzer1 | 1.3/1.4 + 2.7 + 2.5/2.6 | **1.3/1.4 Scene Detection** (primary, tab-navigation undersegmentation) — 2.7 label on segment 0 is a **missing-recovery-heuristic gap**, not a bad state check | check correctly detects Play Store→app transition; the defect is no "state progressed further than expected" recovery path | **Yes** (partial) |
| wifianalyzer2 | 1.4 Scene Detection | **1.4 Scene Detection** — long-press gesture type not modeled by segmentation, only tap | "long-press is harder to detect via CLIP similarity than tap" | No |

**8 of 19 apps (42%) diverge** from their self-labeled category once traced to true origin.

## 3. Counter — true root causes, sorted by frequency

| Rank | Root cause | Count | Apps |
|---|---|---|---|
| 1 | **1.4 Scene Detection** | 9 | antennapod1, bakerspercentagecalculator2, batterytemperaturedisplay, bloodpressuremonitor2, brethap1, brethap2, homemedkit1, jigsaw2, vanilla, wifianalyzer1, wifianalyzer2 *(11 apps have 1.4 as a listed cause; 9 have it as sole/primary true root; 2 more list it as contributing)* |
| 2 | **2.5 Region Detection** | 5 | adaway, bloodpressuremonitor3, homeraudioplayer, jigsaw1 (seg 0), vanilla (secondary) |
| 3 | **1.3 Similarity Computation** | 2 | bily (primary), wifianalyzer1 (contributing to 1.4) |
| 4 | **2.6 ROI Selection / stale recovery region** | 1 | bakerspercentagecalculator1 |
| 5 | **2.7 State Consistency — genuine environmental mismatch** | 1 | simplenotes |
| 5 | **2.7 State Consistency — false-positive equivalence** | 1 | jigsaw1 (seg 1) |
| 6 | **3.10 GUI Perception — capture-time state divergence** | 1 | binaryeye |
| 6 | **1.1 Video Input Processing — corrupted capture** | 1 | bloodpressuremonitor1 |

*(Counts don't sum to 19 because 3 apps — batterytemperaturedisplay, brethap1, vanilla — have two independent true causes; jigsaw1 has two causes in different segments of the same run.)*

**Headline: Scene Detection (Phase 1.4) is the dominant true root cause, responsible for roughly half of all bad runs — nearly double the next most common cause (Region Detection).** Several reports self-labeled 2.7 State Consistency as "root cause" when the state-mismatch check was doing its job correctly and simply inherited a bad reference frame from segmentation.

## 4. Deep dive: top causes

### #1 — Scene Detection (Phase 1.4 / CLIP segmentation), 9 apps

**What exactly breaks.** The paper's segmentation algorithm (§2.1.1–2.1.2) computes cosine similarity between consecutive frames' CLIP embeddings of the Y-luminance channel, and marks a scene boundary wherever similarity dips below a fixed `stable_sim_threshold` of 0.95. Two failure directions show up across the 9 apps:
- **Under-segmentation (collapse)**: rapid, low-visual-delta interactions — calculator button taps (vanilla), slider drags (jigsaw1/jigsaw2), form-field typing (bloodpressuremonitor2), tab switches (wifianalyzer1) — never push similarity below 0.95 between consecutive 1fps-sampled frames, so 3-6 real user actions get merged into a single segment with a single inferred action.
- **Over-/mis-segmentation (wrong boundary)**: transient states not present in the true recording (batterytemperaturedisplay's phantom lock-screen segment) or a mid-sequence frame incorrectly chosen as the segment-0 reference (bakerspercentagecalculator2, homemedkit1, brethap2, antennapod1) — CLIP finds *a* stable region, but it's the wrong one for "segment start."

**Why it happens.** CLIP embeddings capture holistic scene similarity, not fine-grained interaction state. A calculator display changing "3" → "3+" or a slider moving 2 clicks changes only a small fraction of pixels; CLIP correctly reports this as "highly similar," but similarity ≠ "no action occurred." The fixed 0.95 threshold is a single global constant applied to visually static apps (breathing exercise dark UI, calculator) and visually dynamic apps (podcast browsers) alike — the paper acknowledges this class of limitation in passing ("over-segmentation... dynamic GUI elements... future improvement," §3.1.4) but only in the direction of over-segmentation from ads/video, not under-segmentation from rapid taps, which is the dominant failure here.

**Is handheld capture making this worse? No — mostly independent.** Sub-second tap/slider/scroll sequences produce the same low-frame-delta CLIP similarity pattern whether the video is a clean screen recording or a handheld capture of the same interaction. A screen recording of a user rapidly tapping "3", "+", "6" would show near-identical CLIP similarity curves to what's in our handheld videos — this is a threshold/sampling-rate problem intrinsic to the algorithm, not a capture-artifact problem. The one partial exception: 1fps frame extraction (used across all these logs) is itself a choice that would lose fast taps regardless of source, and handheld video sometimes has irregular/lower effective frame rates from camera autofocus hunting or motion blur — but this is a minor compounding factor, not the driver.

**Verdict: engineering fix, not new research.** This is a known, already-partially-addressed class of problem (the paper's own OCR-triggered keyboard-frame detection, §2.1.2, is exactly this kind of supplementary signal). Fixes are incremental: lower/adaptive threshold per app-visual-density, add motion-vector or touch-event-adjacent signals, increase frame sampling rate during suspected rapid-interaction windows. Not worth a new paper on its own.

### #2 — Region Detection (Phase 2.5 / GroundingDINO), 5 apps

**What exactly breaks.** GroundingDINO (paper §2.2.1) is an open-vocabulary object detector prompted with generic terms ("button," "icon," "text field") to find candidate interactive regions in a frame. In these 5 apps it returns **zero** candidate regions (adaway, bloodpressuremonitor3, homeraudioplayer, jigsaw1 seg 0) or a **wrong** region among several correct candidates (vanilla — picks visually-similar "backspace" instead of "multiply").

**Why it happens.** Two distinct mechanisms:
1. **Occlusion / visual corruption of the keyframe** — adaway's keyframe has a finger physically covering the target UI element; jigsaw1's reference frame is "heavily distorted" (compression/HDR-conversion artifact) leaving DINO with an unreadable region.
2. **Low-salience or visually-ambiguous targets** — a small FAB icon on a 900-frame span (homeraudioplayer, bloodpressuremonitor3) falls below DINO's confidence threshold; visually near-identical buttons (backspace vs. multiply, both pink circles) get confused because the prompt vocabulary ("button") gives DINO no way to disambiguate function from appearance.

**Is handheld capture making this worse? Yes — this is the standout case.** Finger occlusion (adaway) is *structurally impossible* in a screen recording — there is no finger between the camera and the screen when the screen itself is the recording source. It only exists because the capture method is a second camera filming a physical device being touched. Likewise, handheld capture introduces glare, off-axis viewing angle, motion blur from hand tremor, variable ambient lighting, and camera autofocus artifacts — none of which a screen recording can ever produce, and none of which GroundingDINO (or CLIP upstream) was trained or evaluated against, since the paper's evaluation datasets (Themis, GIFdroid, V2S) are exclusively screen recordings (§3.1.1). The "heavily distorted" reference frame in jigsaw1, attributed in the report to HDR-to-SDR conversion, is also a symptom specific to phone-camera video codecs, not screen-capture output.

**Verdict: this is the genuine research gap.** The paper's entire Phase 2 pipeline — GroundingDINO region detection, VLM-based ROI selection, attention-driven state comparison — was designed and evaluated exclusively on clean, occlusion-free, camera-artifact-free screen recordings. Nothing in the paper's threats-to-validity section (§4) or conclusion (§6) considers input video that itself contains a physical camera's imaging artifacts (occlusion, glare, motion blur, focus hunting, perspective distortion) layered on top of the UI content being recorded. A follow-on paper on **occlusion- and artifact-robust region detection for camera-captured (as opposed to screen-captured) bug videos** would be addressing a problem this paper structurally cannot surface, since its own dataset excludes it by construction. This is not a threshold tweak — it likely requires either a pre-processing dehazing/deocclusion step, a region-detection model fine-tuned on camera-captured UI imagery, or multi-frame aggregation to vote out transient occlusions (a finger blocking one frame but not the next).

### #3 — Similarity Computation (Phase 1.3), 2 apps

**What exactly breaks.** This is the threshold-choice root of Scene Detection failures, isolated separately in bily where SSIM (not CLIP — bily's run used the SSIM algorithm variant) at 0.95 never triggers a boundary across 745 frames because menu/settings overlay animations fade in gradually, keeping pixel correlation high throughout.

**Why it happens.** SSIM measures pixel-level structural correlation; a fade-in overlay changes a small screen region gradually, so frame-to-frame SSIM stays >0.95 throughout the entire animation even though the user's intent (open menu → reset → toggle settings) involves 6 distinct semantic actions.

**Is handheld capture making this worse? No.** Identical failure mode regardless of capture source — animation smoothness is a property of the app's UI design, not the recording method.

**Verdict: engineering fix**, same family as #1 (adaptive thresholding / supplementary signals), not separable as its own research contribution from the Scene Detection fix above.

### #4 — ROI Selection / stale recovery region (Phase 2.6), 1 app

**What exactly breaks.** In bakerspercentagecalculator1, DINO correctly detects regions initially, but when the state-consistency check fails and recovery kicks in, the recovery logic re-taps the *previous* segment's already-selected region instead of re-running region detection against the new (post-tap) screen. The report's own text: "recovery mechanism doesn't re-examine region detection... no fallback to re-run DINO object detection or re-analyze current screenshot for new regions."

**Why it happens.** This is a control-flow gap, not a model-quality gap — Phase 2's region/ROI pipeline is only invoked once per segment on the *reference* frame, and the recovery loop (Phase 3's guided exploration) has no mechanism to invoke it again against the *live* frame when the live frame has changed screens entirely (list → form).

**Is handheld capture making this worse? No.** Purely a pipeline architecture gap, orthogonal to capture method.

**Verdict: small, clearly-scoped engineering fix** — recovery should re-run Phase 2's region detection against the current live screenshot rather than replaying a stale region, each retry.

### #5 — State Consistency (Phase 2.7), 2 apps (2 distinct sub-failures)

**simplenotes — genuinely environmental.** Device app data was reset/empty while the reference video was recorded against an app with 2 pre-existing notes. Phase 2.7's YES/NO check correctly identifies these as different states; there is no recovery possible because the precondition (existing notes) simply doesn't exist on the replay device. Not a pipeline defect at all — a test-setup/dataset-parity issue.

**jigsaw1 (segment 1) — false-positive equivalence.** The state check judges "already on target screen" as true because layout and labels match, without checking that the underlying slider *value* (2 vs. 4) differs. This is a genuine model-reasoning limitation: VLM-based visual comparison isn't grounded in the app's actual data state, only its visual layout.

**Is handheld capture making this worse?** No for either — both are reasoning/data-parity issues independent of capture source.

**Verdict:** simplenotes needs dataset/device-state parity control (test harness fix, not ViBR fix). jigsaw1's false-positive equivalence is a real but narrow VLM-reasoning limitation — worth a prompt-engineering fix (explicitly ask the VLM to check for value/data differences, not just layout), not a new research direction on its own.

## 5. Summary takeaway

Of the causes examined, **Scene Detection (Phase 1.4) and Similarity Computation (Phase 1.3) are known, already-partially-addressed engineering problems** — fixable with adaptive thresholds, motion-aware signals, or higher sampling rates, and largely independent of whether the source video is screen-recorded or camera-captured. **ROI Selection and State Consistency gaps (#4, #5) are narrow, well-scoped pipeline fixes** — re-run region detection on recovery, add data-state awareness to the VLM comparison prompt.

**Region Detection (Phase 2.5) stands apart.** It is the only top-5 cause where handheld capture is not just a minor compounding factor but the structural reason the failure exists at all — finger occlusion, glare, motion blur, and camera-codec artifacts cannot occur in a screen recording by definition, and the ViBR paper's evaluation, dataset, and threats-to-validity discussion never touch camera-captured input because its entire dataset (Themis, GIFdroid, V2S recordings) is screen-recording-only. This is a legitimate, currently-unaddressed research gap: **region detection and GUI state comparison robust to physical-camera capture artifacts**, distinct from (and outside the scope of) what ViBR itself set out to solve. It is the strongest candidate among these findings for a follow-on research contribution rather than an incremental fix to the existing pipeline.
