# ViBR Failure Analysis: bakerspercentagecalculator1 (bad-quality video)

## Log Summary

Extracted timeline from `/bad-run.log` (starting after GroundingDINO load, filtered for relevance):

| Time | Module | Event |
|------|--------|-------|
| 19:52:03 | __main__ | CLIP segmentation complete: 3 segments detected |
| 19:52:08 | __main__ | Processing segment 0 (frames 0–137) |
| 19:52:12 | dino_detection | DINO model loaded; annotated output saved |
| 19:52:18 | __main__ | Region selection: target region [4] (+ button), action=tap |
| 19:52:44 | execute_action | [Segment 0] Executed: Tap the '+' button to add your first recipe |
| 19:52:49 | __main__ | Processing segment 1 (frames 142–1398) |
| 19:53:06 | __main__ | Region selection: target region [1], action=tap |
| 19:53:14 | **WARNING** | State alignment failed (try 1/3) |
| 19:53:33 | __main__ | Recovery attempt 1: Tap region [3] at (964, 1741) (Save Recipe button) |
| 19:53:41 | **WARNING** | State alignment still failed (try 2/3) |
| 19:53:49 | __main__ | Recovery attempt 2: Tap region [9] at (539, 1468) (Save Recipe button) |
| 19:53:58 | **WARNING** | State alignment still failed (try 3/3) |
| 19:54:06 | **WARNING** | **SKIP ACTION:** GUI mismatch — reference shows main list, current shows recipe form |
| 19:54:16 | run_stats | **Status: successful** | Actions executed: 1, LLM calls: 12, Cost: $0.0191 |

**Interpretation:**
ViBR executed only the first action (tapping the + button) successfully. Processing segment 1 (the main form-filling interaction) failed immediately due to state mismatch. The model attempted three recovery actions, all targeting wrong UI elements (Save Recipe button instead of form input fields). After three failed retry attempts, the entire segment 1 was skipped, causing the sequence to halt. Segment 2 was unreachable because segment 1 never completed, so the expected "save success" state never materialized. The run reports "successful" status despite executing only 1 of ~9 expected steps (11% coverage).

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Expected steps (from video)** | 9 |
| **Executed steps (from log)** | 1 |
| **Missing steps** | 8 |
| **Coverage** | 11% |
| **Execution failures** | 1 (segment 1 state mismatch + 3 failed retries) |
| **Root cause category** | Phase 2: GUI State Comparison (state consistency mismatch) |

**Key finding:** ViBR's perception of the device GUI state diverged catastrophically after the first action. The model detected the form opening but could not reconcile the expected post-tap state with the actual screenshot, leading to repeated failed recovery attempts and eventual skip of the entire interaction segment.

---

## Ground Truth vs Execution Log

| Step# | Expected Action | Executed | Status | Issue |
|-------|-----------------|----------|--------|-------|
| 1 | Tap + button to open form | ✓ | OK | Successful |
| 2 | Tap Recipe Name field | ✗ | SKIP | State mismatch detected; recovery failed |
| 3 | Type "cake" | ✗ | SKIP | Cascading: step 2 failed |
| 4 | Type ingredient amount "50.0" | ✗ | SKIP | Cascading: step 2 failed |
| 5 | Tap Notes field | ✗ | SKIP | Cascading: step 2 failed |
| 6 | Type notes | ✗ | SKIP | Cascading: step 2 failed |
| 7 | Tap Oven Temp & Time field | ✗ | SKIP | Cascading: step 2 failed |
| 8 | Type oven info | ✗ | SKIP | Cascading: step 2 failed |
| 9 | Tap Save Recipe button | ✗ | SKIP | Cascading: step 2 failed |

---

## Video vs Log Comparison

**Segment 0 (frames 0–137, log expects ~2 sec):**
- Log shows: App startup, DINO detection, + button tap → action executed ✓
- Video shows: Initial state, form opens after tap
- **Gap:** None (well-aligned)

**Segment 1 (frames 142–1398, log expects form filling + multiple taps):**
- Log shows: Detected region [1] as target but state comparison **FAILED**
  - Recovery 1: Tried region [3] (Save Recipe button) — no state change
  - Recovery 2: Tried region [9] (Save Recipe button again) — no state change
  - Recovery 3: Tried region [9] again — no state change
  - **Result: SKIPPED entire segment**
- Video shows: Form visible with Recipe Name, Ingredients, and keyboard; user taps on fields, types text, interacts for ~13 seconds
- **Gap:** Critical — ViBR never attempted to interact with form input fields. Recovery logic targeted Save button repeatedly instead of identifying and filling form inputs.

**Segment 2 (frames 1402–1503, log expects return to list):**
- Log shows: Unreachable (segment 1 was skipped)
- Video shows: Recipe saved, returned to list
- **Gap:** Not executed due to cascading failure from segment 1

---

## Detailed Failure Analysis

### Failure Event: Segment 1 State Alignment Mismatch

**What ViBR expected (from good-run reference):**
After tapping + button, the form should open cleanly and remain stable. Region selection should identify form input fields (Recipe Name, ingredient inputs, etc.) and execute sequential taps.

**What ViBR detected (from bad-run log):**
- Reference image: Main list + button (from segment 0 end state, stored as `step_1v_relevant_regions.png`)
- Live screenshot: Form with Recipe Name, ingredients, Save button, etc. (`step_1e_screenshot_0.png`)
- **GPT-4o assessment:** "The reference image shows a main screen with a list and a floating action button, likely for adding a new item. The current image shows a detailed form for creating a new recipe. These are different screens representing different steps in a user workflow."
- **Decision:** States are not consistent → cannot proceed → SKIP

**Why the mismatch occurred:**

The critical insight from the log line 177:
> "Comparing state: reference=step_1v_relevant_regions.png vs live=step_1e_screenshot_0.png"

The reference image being compared is the **output of the previous segment's region extraction**, not the expected post-action state. This is a logical error in the comparison flow:

1. Segment 0 executed: Tap + button
2. Segment 1 starts: Compares "what should segment 1's START state be?" against "what is it NOW?"
3. **Problem:** The reference stored is segment 0's region-annotated image (the pre-tap list screen), not the expected post-tap form state
4. **Result:** State comparison sees "list → form" and flags it as mismatch

**Root cause category:**
- **Phase 2.7: State Consistency Check (GPT-4o)** — False negative due to incorrect reference state selection
- The model is comparing against the wrong baseline (previous segment's state snapshot rather than expected next state)

**Cascade impact:**
- Unable to identify which input field to interact with next
- Recovery logic falls back to searching for recognized buttons (Save Recipe)
- Attempts to tap Save button 3 times, hoping state will resolve
- All three recovery attempts fail because tapping Save button in an incomplete form achieves nothing
- Segment 1 is abandoned entirely

---

## Root Cause Categorization

| Phase | Category | Issue | Count | Evidence |
|-------|----------|-------|-------|----------|
| **2.7** | State Consistency Check | False negative: valid state transition flagged as mismatch | 1 | Log lines 152, 161, 169 (3 retry attempts, all failed due to same comparison error) |
| **3.10** | Action Space Definition / Recovery Logic | Recovery algorithm targets wrong UI elements (Save button instead of form inputs) | 3 | Log lines 157, 164, 172 (recovery attempts tap Save instead of form fields) |
| **3.11** | Action Inference (GPT-4o) | Model cannot infer form-filling sequence from mismatched state context | 1 | No form input regions were ever selected; focus remained on Save button |

**Dominant failure mode:** Phase 2.7 (state consistency) + Phase 3.10 (wrong recovery target)

---

## Impact Assessment

**Execution halted at:** Segment 1 out of 3
**Steps completed:** 1 out of 9 (11% coverage)
**Full workflow prevented:** Yes — recipe was never saved

**Why ViBR cannot recover from this failure:**
1. State comparison doesn't recognize form-open as valid continuation
2. Recovery mechanism doesn't re-examine region detection; instead re-taps last known button
3. No fallback to re-run DINO object detection or re-analyze current screenshot for new regions
4. Retry limit (3 attempts) is exhausted with wrong strategy

**If segment 1 had completed:**
- Segment 2 (recipe saved + return to list) would likely execute successfully
- Full workflow coverage: 100%
- Cost impact: No additional cost (same model calls budgeted)

---

## Conclusions

The failure in `bakerspercentagecalculator1` bad-quality run is a **state consistency check failure** compounded by a **recovery logic defect**. 

ViBR's segmentation correctly identified three scene boundaries. The first action (open form) executed successfully. However, when transitioning to segment 1 (form-filling), the state comparison baseline was incorrectly set to the previous segment's reference image rather than the expected post-action form state. This caused a false negative: the model flagged a valid screen transition (list → form) as a mismatched state.

The recovery mechanism then attempted to correct the mismatch by repeatedly tapping the Save Recipe button—a region it could recognize but which was semantically wrong for the current context. This suggests that the region classifier (DINO) successfully detected UI elements, but the action inference layer (GPT-4o) could not determine appropriate next steps from the inconsistent state context.

**Coverage:** 11% (1 of 9 steps)
**Failure type:** State consistency check error (Phase 2.7) + misguided recovery (Phase 3.10)
**Mitigation path:** Improve state baseline selection in segment-to-segment transitions; augment recovery logic to re-analyze regions from live screenshot rather than re-tapping previous targets.

---

## TL;DR

✗ **Form-filling sequence never started** — Only initial "+ button" tap executed (1/9 steps = 11% coverage)

✗ **Root cause:** ViBR compared segment 1 start state against wrong reference baseline (segment 0 end state instead of expected post-tap form state), triggering false state mismatch

✗ **Recovery failed:** Recovery logic repeatedly tapped Save button (wrong element) instead of re-detecting form input fields

✗ **Cascade:** All form input steps (8 total) were skipped; recipe never saved

**Bottom line:** State consistency check false negative prevented form-filling workflow from starting; recovery mechanism lacked intelligence to re-analyze live screen and select appropriate form input targets.
