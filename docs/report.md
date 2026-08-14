# ViBR Run Review

> [!summary] Current Objective
> Find what is going wrong in ViBR runs.

## Run Notes

- MPS issue: CLIP was working on CPU instead of GPU, so the run took a lot of time.
- Scan the other videos.
- Try one by one.
- Next to next week: solution to resolve one of the problems.

## App Reviews

### Adaway

**Good-quality video (6/8 steps)**
- Attempt to Align State (3 times)
- Not able to do input text properly

**Bad-quality video (2/8)**
- DINO was not able to identify the Allowed Card Section, because of the finger blocking. ViBR takes keyframes into consideration and the keyframe had finger in between the screen which blocked the DINO labelling for the Allowed Card.
- apps/adaway-gemini-2.5-pro/bad-artifacts/step_0v_dino.png
- #Phase2-GUI-State-Comparison - Region Detection Grounding DINO
- Because of this when labelling

### Antennapod

**Bad-quality video**
- The video had fdroid screen at the start. Took one extra step to open the app.
- The finger clicked the Queue Tab in Navigation bar, but the DINO recognised the bottom gesture bar to be a relevant region.

### Bakers Percentage Calculator

**Good-quality video**
- `srv-001`: Not able to find relevant regions. Trying to align with the current state.
- `srv-002`: Short video. Not able to do 3 actions. Did not recognize the actions.

**Bad-quality video**
- `hhv-001`: Did not recognize the frames properly.

**Good-quality video (additional notes)**
- Root cause: `segment_replay.py` crashes on index out of bounds when accessing frame indices for segment 2+. This happens when video has fewer frames than expected.
- Segment found = 2, which is more than expected. Basically found fewer frames.

**Bad-quality video (additional notes - bad-video1) (2/9)**
- Not able to enter text in Recipe Name, Ingredient Name, Notes and then Save recipe.
- That's the reason why not able to save recipe.

**Bad-quality video (bad-video2)**
- CLIP segmentation threshold (0.95) too high—treats menu/dialog/screen overlays as same scene, lumps 3 steps into one segment. Frame extraction then grabs wrong boundary frame, skipping segment 0 entirely.
- Fix: Lower threshold to 0.85-0.90 or require 3+ consecutive stable frames instead of 1, so overlays trigger new segment.
- Lowering to 0.85 + raising interval to 3 collapsed entire video into **single segment**. CLIP now treats all 4 steps as one continuous scene (threshold too permissive after lowering).

**Good-quality video (good-video2)**
- DINO correct, recognised by LLM to click on three dots at the top right, but cannot see in execution.
- LLM returned tap action with hardcoded coordinates `[540, 147]` instead of element text/description. Code fell back to position-based matching, found wrong/stale element, tap missed or hit unintended button → app state collapsed (recipe list → empty).

**Bad-quality video (bad-video3)**
- Step-0-v end frame skipped the text input fields screens.
- Step-0-v relevant regions not able to identify the correct click.
- Step-0-e all three screenshots have the same screen.
- DINO detected no UI elements in graph area in the main screen. Actual action: click the FAB, but DINO did not detect it. Hence LLM did not click FAB.
- Reasons maybe: DINO detection threshold missed it. LLM prompt didn't instruct "if no actionable elements, look at FABs".
- The video changes did not detect the input screens.

### Bily

**Good-quality video**
- `srv-001`: DINO is done correctly. The labeled regions are not correct.

**Bad-quality video**
- `hhv-001`: Labeling the regions in the emulator incorrectly. Not able to find the correct region.

### Brethap

**Good-quality video (6/10)**
- Start stop, start stop executed successfully for the breathing sessions.
- Step6-v-relevant regions not able to detect click on the hamburger to show the left navigation pane.
- Diverged after step 6.

**Bad-quality video (0/10)**
- The video extracted using CLIP starts from step 6. First DINO pic has the navigation menu opened directly.
- Therefore there is a state mismatch and the VIBR is not able to go forward from the start.
- **Key findings:**
  - **Segment 0 (frames 0-1002) is extremely stable:**
  - Avg: **0.9979** (near perfect consistency)
  - Min: 0.9556 (just above 0.95 threshold)
  - Frames below threshold: **0** (none)
  - Confirms design: frames 0-1002 are one long stable scene. Only the 1004-1006 transition dips below 0.95. So skipping 0-1002 makes sense — nothing changes there, just hand/phone positioning noise.

### Breathap

**Good-quality video**
- Labeling is not done properly.
- There are a lot of states with the same screens.
- No valid region or element match. Proceeding without position.

**Bad-quality video**
- _Add bad-quality run notes here._

### Homemedkit

**Good-quality video (1/10)**
- VIBR recognised correctly to click the add button in the main screen, but the tool clicked on Settings instead and went on a loop to recover to the aligned state.
- The video has moved on to the next frames, even though the state has not been aligned.

**Bad-quality video (0/10)**
- The start screen of the video doesn't match with the emulator start. So try to get to the aligned state.
- The recovery state is compared with the wrong state here. As it is recovering, it should be compared with the state it failed to align with in the first place and then it should start to go ahead.
- The recovery is gone correctly but after the state is recovered, it is compared with the next state and that's where cascading state mismatches occurred.
- **Key findings:**
  - **0% execution rate** — no actions executed vs 10 expected steps
  - **Root cause:** Cascading state mismatches from initial boundary error (segment 0 references Play Store, device already has app open) + coordinate drift in segment 1 (add button tap fails)
  - **Category:** Stage 2 GUI State Comparison failure (dynamic content + coordinate drift)
  - **Impact:** Segments 0–3 all failed or skipped; recovery exhausted after 3 retries per segment

**Bad-quality video (bad-video2)**
- _TBD_

### Homeraudioplayer

**Bad-quality video (0/10)**
- **Root cause:** Stage 2 GUI state mismatch (expanded UI divergence) + cascading segment failures
- **Coverage:** 60% execution (3/5 actions)
- **Why segmentation failed to detect menu:**
  - CLIP similarity is high across menu frames (low visual variance)
  - Menu = stable region, not a transition
  - Segmentation algorithm finds _boundaries_ (sharp changes), not content types
  - Menu frames blend into broader segment without creating distinct boundary

### Jigsaw

**Bad-quality video (bad-video1)**

- 



### Wifi Analyzer

**Bad-quality video (3/9)**
- Was not able to proceed to next steps because failed in between to find relevant regions to click and the LLM returned a relevant region which did not exist in the discovered regions.

**Detailed failure analysis:**
- **Segment 1:** LLM selects `[11]` but annotation says "No relevant regions" → DINO only detected 0-10 (11 boxes total, indices 0-10)
- **Segment 2:** LLM selects `[1]` but annotation says "No relevant regions" → **DINO detected 0 boxes OR detected boxes have NO index 1**

**Real issue:** Line 197 filter `if r["index"] in relevant_indices` — when LLM returns index 11 but DINO only has 11 detections [0-10], key 11 doesn't exist. **Annotation image is blank**, LLM gets blank image, doesn't know what region is valid, guesses wrong.

**Two-liner for run example:**
- **Segment 1:** DINO found 11 boxes [0-10]. LLM asked "which is relevant?" → incorrectly returns index 11 (doesn't exist). Annotation filter fails silent.
- **Segment 2:** DINO found multiple boxes. LLM asked "which is relevant?" → returns index 1, but index 1 not in DINO results (filtered during detection). Annotation blank. LLM guesses region 1, but lookup fails at execution.

**Good-quality video (1/10)**
- DINO images are not annotated correctly.
- Every step takes 3 steps to align with the target (produces a lot of intermediary steps).
- Got stuck after step one because of wrong state. Not able to recover to base state.
