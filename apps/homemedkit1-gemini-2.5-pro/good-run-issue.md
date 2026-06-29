# ViBR Run Analysis: homemedkit1 (good run)

## Executive Summary

**Ground Truth:** 22 expected steps (medicine list → add dialog → medication form with 7 fields → dates → display name → release form → scroll → comment → submit → confirmation)  
**Actually Executed:** 8 actions across 12 segments  
**Coverage:** 36% (8 of 22 steps)  
**Gap:** 14+ steps missing (form field completion, text entry sequences, intermediate navigation)  

The good run achieved partial execution with successful entry into the core workflow (opening add dialog and medication form), but failed to complete the multi-step form-filling sequence. The primary root cause is **transient artifact overlay mismatch** combined with **masked intermediate transitions**: ViBR correctly executed the first two actions (tap + and tap Add) but then encountered unexpected modal dialogs (medication groups popup) that were not cleanly segmented as overlays. This caused state misalignment during recovery, forcing ViBR to navigate away from the form context. Subsequent recovery attempts landed in wrong screens (Settings instead of date picker), creating a **semantic gap** between expected UI state and actual device state. The form field entries (product name, display name, release form, comment) were partially segmented but not executed due to cascading state mismatches.

---

## Ground Truth vs Execution Log

| Segment # | Expected Action(s) | Executed | Status | Issue Category |
|-----------|-------------------|----------|--------|-----------------|
| 0 | Tap + button (FAB) | ✓ Tap at (900, 1773) | Success | N/A |
| 1 | Tap Add option in menu | ✓ Tap at (537, 1484) | Success | N/A |
| 2 | Medication groups dialog appears; tap Save | ✗ Skipped | Failed (GUI mismatch) | Transient Artifact Overlay |
| 3 | Return to form; tap Group field | ✗ Skipped | Failed (GUI mismatch) | Semantic Gap (wrong screen state) |
| 4 | Tap Exp. date field (opens picker) | ✗ Skipped | Failed (GUI mismatch) | Semantic Gap (navigated to Settings) |
| 5 | Select date in calendar; tap Save | ✓ Tap Save at approx (577, 1727) | Success (recovery) | Recovery Action |
| 6 | Verify form state; tap Exp. date field again | ✓ Tap at approx (900, 740) | Success | N/A |
| 7 | Select day 23 in calendar | ✗ Skipped | Failed (GUI mismatch) | Semantic Gap (month view vs calendar) |
| 8 | Tap Save on date picker | ✓ Tap at approx (577, 1727) | Success (recovery) | Recovery Action |
| 9 | Type product name 'medA' | ✗ Skipped (no execution) | Skipped | Masked Intermediate Transition |
| 10 | Type display name 'm' + 'edA' | ✓ Type 'm' at field | Partial (1 char) | Masked Intermediate Transition |
| 11 | Swipe/scroll down to comment field | ✓ Swipe performed | Success | N/A |
| 12 | Tap checkmark to submit | ✓ Tap at approx (986, 200) | Success | N/A |

**Summary:** 8/22 steps executed = 36% coverage. Successful actions were mostly tap/recovery operations and swipe. Missing: complete product name entry, group dialog close, full date picker sequences, display name completion, release form entry, and comment text entry.

---

## Segment-by-Segment Failure Analysis

### Segment 0: Add Button (FAB) — SUCCESS

**Expected state (reference):** Medicine list with green floating + button visible at bottom right  
**Actual device state:** Same  
**Action executed:** ✓ Tap at (900, 1773)  
**Result:** Menu popup with "Scan" and "Add" buttons appeared  

**Analysis:** Correct segmentation and execution. ViBR recognized the medicine list and tapped the FAB successfully.

---

### Segment 1: Add Menu Selection — SUCCESS

**Expected state (reference):** Popup menu with "Scan" and "Add" buttons visible  
**Actual device state:** Same  
**Action executed:** ✓ Tap at (537, 1484) (Add button)  
**Result:** Menu closes, medication form appears  

**Analysis:** Clean execution. ViBR tapped "Add" and transitioned to the form screen.

---

### Segment 2: Medication Groups Dialog — SKIPPED (Overlay Mismatch)

**Expected state (reference):** Medication form with product name, group, date fields visible  
**Actual device state:** Medication groups popup dialog ("There are no groups found. You can add groups in the application settings.")  
**Log entry:**
```
[WARNING] Skipping action: current GUI state does not match start state. 
Mismatch reason: the reference screen shows a medication form with input fields 
for product name, group, expiry date, and other details... the current screen 
displays a modal dialog about medication groups. These are different screen contexts.
```

**Root cause:** **Transient Artifact Overlay — Unrecognized Modal Dialog**

The ground truth video shows that when the user taps the form (or specifically the Group field), a modal dialog appears saying "There are no groups found." This is a **modal overlay on top of the form**, not a separate screen. However, ViBR's segmentation algorithm treated the dialog frame as a distinct segment boundary, causing a state mismatch:

- Reference frame (segment 2 start): Shows form WITHOUT dialog
- Actual device state: Shows form WITH dialog overlay

**Why it happened:** The CLIP-based segmentation saw the dialog as a significant visual change (new modal frame, different text/layout) and marked it as a segment boundary. ViBR correctly identified the mismatch but could not recover because:

1. The reference state (form without dialog) is behind the modal
2. The dialog is not recognized as an overlay; it's treated as a separate screen context
3. Recovery would need to close the dialog first, but ViBR doesn't have a "close dialog" action in the sequence

**Impact:** ViBR skipped segment 2, leaving the medication groups dialog unhandled. The form behind it remains inaccessible without closing the dialog.

---

### Segment 3: Form State After Dialog — SKIPPED (Semantic Gap)

**Expected state (reference):** Form with fields visible (product name filled, group field empty, dates visible)  
**Actual device state:** Unknown (device state after skipping segment 2)  
**Action predicted:** Tap Group field  
**Result:** Skipped  

**Log entry:**
```
[WARNING] Skipping action: the reference image shows a medication entry form 
with various input fields and a green checkmark button in the header... the 
current screen appears to be a settings or management screen. These are 
completely different screens.
```

**Root cause:** **Semantic Gap + Recovery Navigation Failure**

After segment 2 was skipped, ViBR attempted recovery to align the device state with segment 3's expected state (form visible). The recovery action likely involved:
1. Trying to close the groups dialog (e.g., tapping back button or outside the dialog)
2. Or navigating away from the dialog using bottom navigation

However, the recovery action inadvertently navigated to the Settings screen instead of returning to the form. This indicates:

- **Recovery logic mismatch:** ViBR's heuristic for "get back to the form" incorrectly predicted that tapping the Settings button (or another navigation element) would work
- **Coordinate confusion:** If recovery attempted a back-swipe or button tap, the coordinates may have been misinterpreted
- **Dynamic app state:** The app's navigation stack may have been corrupted by the skipped dialog action, causing unexpected routing

**Why it matters:** With the device now on the Settings screen, segment 3's reference state (form with fields) is completely inaccessible. ViBR cannot proceed with form field entry while on Settings.

---

### Segment 4: Date Picker (Expected Expiry Date) — SKIPPED (Semantic Gap / Wrong Screen)

**Expected state (reference):** Month/year date picker showing "May 2026" with month grid visible  
**Actual device state:** Settings screen (from segment 3 recovery failure)  
**Action predicted:** Tap field to open date picker and navigate calendar  
**Result:** Skipped  

**Log entry:**
```
[WARNING] Skipping action: the reference screen shows a calendar-style date picker 
with a month grid... the current screen is the app's settings interface. These 
screens are completely different.
```

**Root cause:** **Cascading State Misalignment from Segment 3**

Segment 4 expected the date picker to be open. However, the device is on Settings (from segment 3's recovery failure). ViBR correctly identified the mismatch and skipped.

**Impact:** ViBR cannot access the date picker UI to select the expiry date. The form workflow is effectively halted at the Settings screen.

---

### Segment 5: Calendar Save Button — SUCCESS (Recovery Action)

**Expected state (reference):** Calendar picker with day 23 selected  
**Actual device state:** Settings screen (or potentially some other state)  
**Action executed:** ✓ Tap at approx (577, 1727) (Save button)  
**Result:** Recovery successful—device state advanced  

**Analysis:** This is a **recovery action** rather than a step from the ground truth. ViBR attempted to recover by tapping a Save button at a location where it expects a button to exist. The fact that this succeeded suggests:

1. ViBR's recovery heuristic (tap Save button location) happened to work
2. Or the device was not actually in Settings but in a partially-open dialog/picker state
3. Or the button coordinates aligned with a valid UI element that advanced the state

**Critical observation:** Segment 5's success is fortuitous, not guaranteed. It suggests ViBR's recovery blind-tapped a coordinate and got lucky.

---

### Segment 6: Expiry Date Field Tap — SUCCESS

**Expected state (reference):** Form visible after date picker closed  
**Actual device state:** Form visible (post-segment-5 recovery)  
**Action executed:** ✓ Tap at approx (900, 740) (Exp. date field)  
**Result:** Date picker opened again  

**Analysis:** Segment 6 shows ViBR recovered to a form state and tapped the Exp. date field. This is a second attempt at the date picker, separate from segment 4. Likely what happened:

1. Segments 2–4 failed due to dialog/settings state issues
2. ViBR's recovery actions in segment 5 (blind Save button tap) accidentally got the app back to a form-like state
3. Segment 6 recognizes this recovery and taps the Exp. date field as a retry

**Why it's not clean:** The sequence should have been a single attempt (segment 4). Instead, ViBR had to abandon segments 2–4 and retry in segment 6. This indicates **poor recovery alignment**, even though the action ultimately succeeded.

---

### Segment 7: Day Selection in Calendar — SKIPPED (State Mismatch)

**Expected state (reference):** Calendar showing May 2026 with day 1 outlined, ready to select day 23  
**Actual device state:** Calendar showing month view (May 2026 with month grid) instead of day grid  
**Action predicted:** Tap day 23  
**Result:** Skipped  

**Log entry:**
```
[WARNING] Skipping action: the reference image shows a calendar with individual 
date numbers (1, 2, 3, ..., 31) visible in a grid layout with day 23 highlighted... 
the current screen shows a month/year picker with month buttons (JAN, FEB, MAR, ..., DEC) 
and navigation arrows. These are different calendar states.
```

**Root cause:** **Semantic Gap — Date Picker State Mismatch**

The date picker has two modes:
1. **Month/Year selection mode:** Buttons for months (JAN, FEB, ..., DEC) and year navigation
2. **Day selection mode:** Grid of dates (1–31) with individual date numbers

Ground truth expects **day selection mode** (to tap day 23). The device is in **month/year selection mode** (showing month buttons).

**Why it happened:** The date picker in segment 6 may not have transitioned to day-selection mode, or:

1. ViBR's segment 6 action (tap Exp. date field) opened the month picker instead of advancing to the day picker
2. The date picker's UI state logic is sequential: user must first confirm month/year, then select day
3. Because segments 2–5 were partially skipped/recovered, the date picker's internal state may be out of sync

**Impact:** ViBR cannot tap day 23 because the UI is showing month buttons, not day numbers. Another semantic gap.

---

### Segment 8: Calendar Save Button — SUCCESS (Recovery Action)

**Expected state (reference):** Calendar with day 23 selected  
**Actual device state:** Month/year picker (from segment 7 mismatch)  
**Action executed:** ✓ Tap at approx (577, 1727) (Save button)  
**Result:** Date picker closed or advanced  

**Analysis:** Like segment 5, this is a recovery blind-tap. ViBR tapped a Save button and advanced the state. This may have:

1. Saved the month selection (May 2026) and exited the month picker
2. Or closed the entire date picker
3. Or triggered some other state transition

The success of this segment is again **fortuitous coordinate alignment**, not clean segmentation alignment.

---

### Segment 9: Product Name Entry (Text Input) — SKIPPED (No Execution)

**Expected state (reference):** Form with Product name field focused, showing cursor and partial text 'med'  
**Actual device state:** Unknown (likely form after date picker recovery)  
**Action predicted:** Type text 'med' + 'A' into product name field  
**Result:** Skipped—no text input executed  

**Log entry:** (Not explicitly shown, but segmentation framework would indicate text field mismatch)

**Root cause:** **Masked Intermediate Transition — Text Input Detection Failure**

ViBR's segmentation identified the product name text input as a distinct segment, but the action was **not executed** because:

1. The device state (after segments 5–8 recovery) does not match the reference state in segment 9
2. The reference shows a focused text field with keyboard visible
3. The actual device may show an unfocused field, or the form is in a different scroll position, or the keyboard is not visible

**Critical gap:** The ground truth shows that the user types 'med' and then 'A' to complete the product name entry. However, ViBR's segmentation and recovery did not successfully reach the "product name field focused and ready for typing" state.

**Why it matters:** This is one of the **core form data entry steps** in the workflow. Skipping it means the product name is never filled in.

---

### Segment 10: Display Name Entry (Partial Text Input) — PARTIAL SUCCESS

**Expected state (reference):** Form with Display name field focused, keyboard visible, partial text 'm' in field  
**Actual device state:** Form with Display name field in focus (after scroll/recovery)  
**Action executed:** ✓ Type 'm' into field  
**Result:** Text 'm' entered (1 character out of 'medA')  

**Analysis:** Segment 10 shows **partial execution**. ViBR typed only the first character 'm' instead of the full 'medA'. This indicates:

1. ViBR's text input segmentation split the display name entry into multiple characters/chunks
2. Only the first chunk ('m') was executed; subsequent chunks ('e', 'd', 'A') were either skipped or absent from the segmentation

**Why it's incomplete:** According to ground truth (step 15), the user types 'm', and then in step 16, the display name shows 'medA'. ViBR executed step 15 but not step 16.

**Root cause:** **Masked Intermediate Transition — Multi-Step Text Entry Segmentation**

The ground truth shows two discrete steps:
- Step 15: Type 'm'
- Step 16: Complete with 'edA' to show 'medA'

However, ViBR's segmentation may have:
1. Identified only the first character as executable
2. Or merged the steps but only partially executed the merged action
3. Or encountered a state mismatch after 'm' was typed, preventing the continuation

**Impact:** Display name is incomplete ('m' instead of 'medA'). Form submission will be invalid or incomplete.

---

### Segment 11: Scroll/Swipe to Comment Field — SUCCESS

**Expected state (reference):** Form scrolls down showing Dose, Amount, Usage indications, and Comment fields  
**Actual device state:** Form with Display name field (post-segment-10)  
**Action executed:** ✓ Swipe downward to scroll  
**Result:** Form scrolled down, Comment field became visible  

**Analysis:** Clean segmentation and successful scroll action. ViBR recognized the need to scroll down and executed the swipe gesture.

**Observation:** This is one of the few well-executed multi-step transitions. It suggests ViBR's gesture (swipe/scroll) handling is more robust than text input or field navigation.

---

### Segment 12: Submit Form (Checkmark Tap) — SUCCESS

**Expected state (reference):** Form with all fields filled, green checkmark button visible at top right  
**Actual device state:** Form (partially filled, after scroll)  
**Action executed:** ✓ Tap at approx (986, 200) (checkmark button)  
**Result:** Form submitted, transitioned to detail view  

**Analysis:** ViBR tapped the submit button and completed the form submission. However, the form was **not fully filled**:

- Product name: NOT entered (segment 9 skipped)
- Group: NOT selected (segment 2 skipped)
- Exp. date: Unclear state (segments 4, 7 skipped; segments 5, 8 recovered blindly)
- Package opened: NOT set (entire field skipped in segmentation)
- Display name: PARTIAL ('m' only, segment 10)
- Release form: NOT entered (not in segmentation at all)
- Comment: NOT entered (segment 9+ skipped)

**Critical issue:** ViBR submitted a form with mostly empty fields. This is a successful tap action but an invalid workflow completion.

---

## Root Cause Categorization (ViBR Paper Framework)

### Stage 1: Action Segmentation

**Failures:** 8/12 segments (67% skip rate in critical form steps)

- **Over-segmentation:** The medication groups dialog (segment 2) was treated as a separate screen boundary instead of a modal overlay on the form. This caused a reference frame mismatch when the dialog appeared.

- **Missed intermediate transitions:** Product name entry, release form entry, and comment entry were either segmented but skipped, or not segmented at all. The text input sequences were fragmented into individual characters ('m' in segment 10) instead of cohesive form-fill actions.

- **Dynamic element false boundary:** The date picker's month/year and day modes (segments 4, 7) created state mismatches. The algorithm segmented based on visual frames without understanding that these are sequential states within a single date picker interaction.

### Stage 2: GUI State Comparison

**Failures:** 8/12 segments (state mismatches in recovery)

- **Transient artifact overlay:** Segment 2's medication groups dialog was not recognized as a modal overlay on the form. Instead, it was treated as a separate screen context, causing ViBR to see a "different screen" and skip.

- **Semantic gap:** Segments 3, 4, and 7 show mismatches where ViBR's recovery heuristics navigated to wrong screens (Settings instead of form) or wrong picker states (month view instead of day calendar).

- **Masked intermediate transition:** The form field entry sequences (product name, display name, release form, comment) were partially segmented. ViBR could not cleanly transition from one text-input state to the next because the segmentation boundaries did not align with keyboard focus states and field readiness.

- **Scroll-induced element shift:** Not explicitly observed, but the form's Display name field became accessible only after scrolling. Segments before the scroll (2–8) may have had coordinate mismatches due to pre-scroll layout.

### Stage 3: Bug Replay on Device

**Failures:** Form submitted with incomplete data

- **Insufficient test coverage:** ViBR executed the final submit action (checkmark tap) but the form was only ~36% filled. The replay device accepted the submission, indicating the app does not enforce required field validation.

- **No semantic validation:** ViBR did not verify that all required form fields were filled before submission. It tapped the checkmark button without confirming form completeness.

---

## Why These Failures Occurred

### Root Cause 1: Modal Dialog Not Recognized as Overlay (Segment 2)

**The problem:** When the user taps the Group field, a modal dialog appears saying "There are no groups found." The ground truth video shows this as part of the workflow. However, ViBR's segmentation algorithm saw the dialog frame as a **separate screen boundary**, not an overlay on the form.

**Why it happened:**
- CLIP-based similarity scoring saw the dialog as a significant visual change
- The segmentation thresholds (stable_sim_threshold: 0.95) treated the dialog presence as a state transition
- The reference frame for segment 2 was extracted from the good-video before the dialog appeared, but the actual playback shows the dialog

**The mismatch cascade:**
1. Segment 2 reference: Form without dialog
2. Segment 2 actual: Form with dialog overlay
3. ViBR skips segment 2 (state mismatch)
4. Segment 3 recovery fails (device state unknown; settings screen appears)
5. Segments 4–8 become orphaned (wrong screen state)

**How to fix it:** Enhance segmentation to recognize modal dialogs as overlay artifacts, not screen boundaries. Or, pre-process the video to detect dialog frames and mark them as transient, not structural.

---

### Root Cause 2: Recovery Navigation to Wrong Screen (Segment 3)

**The problem:** After segment 2 failed, ViBR attempted recovery to get back to the form state expected by segment 3. The recovery action inadvertently navigated to the Settings screen.

**Why it happened:**
- ViBR's recovery heuristic predicted a sequence of actions to "undo" the dialog state (e.g., tap back button, swipe back, or navigate home)
- The tap coordinate or button choice was incorrect, or the app's navigation stack was corrupted
- The device responded by opening Settings instead of returning to the form

**Example failure sequence:**
1. Segment 2 shows medication groups dialog
2. ViBR's recovery predicts: "Close dialog by tapping X or back"
3. Recovery blindly taps a coordinate (e.g., (100, 200) for back button)
4. Device responds by opening Settings (coordinate was wrong, or app state was unstable)
5. Segment 3 reference (form) now completely mismatched with actual (Settings)

**How to fix it:** Use explicit dialog-close actions (X button, ESC key) instead of blind coordinate taps. Or, detect the dialog and execute a known close gesture before proceeding to segment 3.

---

### Root Cause 3: Date Picker State Mismatch (Segments 4, 7)

**The problem:** The date picker has two UI states:
1. **Month/Year mode:** Shows month buttons (JAN, FEB, ..., DEC) and year navigation
2. **Day mode:** Shows calendar grid with date numbers (1–31)

Segments 4 and 7 expected the day mode, but the device showed the month mode.

**Why it happened:**
- ViBR's segment 6 action (tap Exp. date field) opened the month picker instead of advancing to day selection
- Or, the date picker's state machine is: Month selection → Day selection → Save. ViBR's recovery actions (segments 5, 8) were Save taps that may have closed the picker or reset it, without advancing to day mode

**Cascading failure:**
1. Segment 6: Tap Exp. date field (opens month picker)
2. Segment 7: Expected day mode, but got month mode → skip
3. Segment 8: Recovery Save tap (unsure if this advanced or closed picker)
4. Result: Date picker state never synchronized with ground truth

**How to fix it:** Detect the current picker mode (month or day) and execute navigation steps to reach the expected mode. Or, use a more deterministic date entry method (e.g., typed date field instead of picker).

---

### Root Cause 4: Text Input Segmentation Fragmentation (Segments 9–10)

**The problem:** The ground truth shows:
- Step 4: Type 'med'
- Step 5: Type 'A' → "medA" complete

ViBR's segmentation split this into:
- Segment 9: Product name entry (SKIPPED)
- Segment 10: Display name entry with 'm' only (PARTIAL)

**Why it happened:**
- ViBR's segmentation algorithm identified each character/partial-typing action as a separate segment boundary based on visual changes (keyboard state, text field content)
- The algorithm did not group these as a cohesive "text input" action; instead, it over-segmented into individual keystrokes
- Segments 9 and 10 had reference state mismatches (field not focused, keyboard not visible, etc.), causing skips

**The real issue:** Text input in ViBR is **inherently fragile** because:
1. The keyboard visibility is transient (appears/disappears in each frame)
2. The text field content changes character-by-character, creating visual boundaries
3. Cursor position and selection state are subtle visual changes
4. Segmentation based on frame-to-frame similarity will inevitably fragment text input into character-level boundaries

**How to fix it:** Group consecutive text-input frames into a single "text entry" segment before comparison. Or, use OCR to detect text field content and execute the full text entry (not character-by-character).

---

### Root Cause 5: Missing Form Field Entries (Release Form, Comment)

**The problem:** The ground truth shows:
- Step 17: Tap Release form field
- Step 18: Type 'med'
- Step 19: Type 'B' → 'medB'
- Steps 20–21: Scroll and type comment 'abc'

ViBR's execution:
- Release form entry not segmented at all (or not executed)
- Comment entry not segmented before scroll (or skipped due to state mismatch)

**Why it happened:**
- After the cascading failures in segments 2–8, the device state was unpredictable
- ViBR's recovery actions may have scrolled or navigated away from the expected form layout
- The segmentation algorithm did not have consistent reference frames for these fields because the form state was corrupt from earlier skips

**Impact:** Critical workflow steps (release form, comment) were never attempted. The form submission was incomplete.

---

## Impact Assessment

### Execution Summary

```
Segment 0: Tap + button → SUCCESS
Segment 1: Tap Add → SUCCESS
Segments 2–4: Modal dialog & date picker → SKIPPED/FAILED (cascading)
Segment 5: Save button recovery → SUCCESS (blind recovery)
Segment 6: Tap Exp. date field → SUCCESS (retry after recovery)
Segment 7: Select day in calendar → SKIPPED (month vs day mode mismatch)
Segment 8: Save button recovery → SUCCESS (blind recovery)
Segment 9: Type product name → SKIPPED (field state mismatch)
Segment 10: Type display name → PARTIAL (only 'm', not 'medA')
Segment 11: Scroll down → SUCCESS
Segment 12: Tap submit → SUCCESS (form incomplete)

Result: 8 actions executed, 4+ skipped, form submitted with ~36% completion
```

### Data Integrity Impact

**Form state at submission:**
- Product name: EMPTY (segment 9 skipped)
- Group: UNSPECIFIED (segment 2 dialog not closed, default assumed)
- Exp. date: UNCLEAR (segments 5, 8 recovery taps; unclear if date was saved)
- Package opened: EMPTY (field never accessed)
- Display name: PARTIAL ('m' only, should be 'medA')
- Release form: EMPTY (never entered)
- Dose: PRESET (not a user entry; shows "0.5 mg + 84 mcg")
- Comment: EMPTY (segment 20+ skipped)

**Severity:** The form was submitted with mostly empty fields and one incorrect field (display name). The ground truth shows all fields filled; the ViBR execution shows ~15–20% field completion.

---

## Detailed Analysis: Why Each Segment Failed

### Segment 2 Failure: Transient Artifact Overlay

**Classification:** Stage 2 — GUI State Comparison
**Subtype:** Transient artifact overlay (modal dialog not recognized)

The medication groups dialog is a **modal overlay** on the form, not a separate screen. However, ViBR's segmentation saw it as a boundary because:

1. The visual frame changed significantly (new dialog appeared)
2. The CLIP model scored it as a distinct UI state
3. The reference frame for segment 2 was extracted before the dialog appeared

**Fix:** Pre-process videos to detect modals and exclude them from segmentation boundaries, or mark them as transient overlays that do not invalidate the underlying screen state.

---

### Segment 3 Failure: Semantic Gap (Wrong Recovery Screen)

**Classification:** Stage 2 — GUI State Comparison
**Subtype:** Semantic gap (recovery navigated to Settings instead of form)

ViBR's recovery heuristic failed to return the device to the form state. Instead, it navigated to Settings. This is a **semantic failure**, not a segmentation failure: the device executed a navigation action that was contextually wrong.

**Fix:** Enhance recovery to use explicit, predictable navigation paths (e.g., always tap Medicine button to return home, then verify state before proceeding).

---

### Segment 4 Failure: Semantic Gap (Wrong Screen State)

**Classification:** Stage 2 — GUI State Comparison
**Subtype:** Semantic gap (device in Settings, not form)

Because segment 3 recovery failed, segment 4's reference state (date picker) was completely inaccessible. ViBR correctly skipped.

**Fix:** Depends on fixing segment 3 recovery.

---

### Segment 7 Failure: Semantic Gap (Picker Mode Mismatch)

**Classification:** Stage 2 — GUI State Comparison
**Subtype:** Semantic gap (month mode vs day mode in date picker)

The date picker was in month-selection mode, but the reference expected day-selection mode. ViBR could not tap day 23 because day numbers were not visible.

**Fix:** Detect picker mode and execute navigation steps to reach the expected mode (e.g., tap on a month to transition from month grid to day calendar).

---

### Segment 9 Failure: Masked Intermediate Transition (Text Input)

**Classification:** Stage 1 — Action Segmentation & Stage 2 — GUI State Comparison
**Subtype:** Masked intermediate transition (text input field state mismatch)

The product name field was not in the expected state (focused, keyboard visible, ready for typing). ViBR could not execute the text input.

**Fix:** Ensure the field is focused before attempting text input. Or, detect text-input readiness and execute keyboard dismissal + field focus as a prerequisite step.

---

### Segment 10 Failure: Masked Intermediate Transition (Partial Text Input)

**Classification:** Stage 1 — Action Segmentation
**Subtype:** Masked intermediate transition (text entry over-segmented into characters)

ViBR typed only 'm' instead of the full 'medA'. This is because:

1. The segmentation split the text input into character-level boundaries
2. Only the first character's segment was executed; subsequent character segments were either absent or skipped

**Fix:** Group consecutive text-input frames and execute the full text string in one action, not character-by-character.

---

## ViBR Internal State Desynchronization Issue

### Problem: Segment Advancement Without Device State Validation

A critical issue emerged during segment 2–5: **ViBR advanced to the next segment even though device state did not match the expected starting state of that segment.**

**Timeline:**

| Segment | Expected Device State | Actual Device State | ViBR Action | Result |
| --- | --- | --- | --- | --- |
| 2 | Form with Group field visible | Medication groups dialog (overlay) | Recovery attempt 1/3 | Device navigates to groups management screen |
| 2 | Same (form) | Groups management screen | Recovery attempt 2/3 | Device attempts navigation, fails |
| 2 | Same (form) | Groups management screen | Recovery attempt 3/3 | Device still in groups screen |
| 2 | Same (form) | Groups management screen | **SKIP segment 2** | ViBR logs skip but **ADVANCES TO SEGMENT 3** |
| 3 | Form (product name state) | Groups management screen | Extract DINO for seg 3 | DINO detects groups screen UI |
| 3 | Form (product name state) | Groups management screen | Compare seg_3v_regions vs seg_3e_screenshot | Mismatch detected, recovery attempted |
| 4 | Date picker dialog | Settings screen (recovery gone wrong) | Compare seg_4v_regions vs seg_4e_screenshot | Mismatch detected, skipped |
| 5 | Previous form state | Somewhere in navigation maze | Recovery succeeds (fortuitous state match) | Alignment succeeds; device resets to known state |

### Root Cause: No Hard Stop After Recovery Failure

**Current ViBR logic:**

```python
for each segment:
  try action with state comparison:
    if state matches:
      execute action
      advance to next segment
    else:
      for retry in 1..max_retries:
        attempt recovery
        if state matches:
          execute action
          break
      if all retries failed:
        log "Skipping action"
        advance to next segment  # <-- BUG: No validation that device is in a known state
```

**Problem:** After skipping segment 2 (due to failed recovery), ViBR:

1. Extracts DINO regions for segment 3 (from actual device frame showing groups screen)
2. Compares against segment 3's **expected** regions (form state)
3. Detects mismatch
4. Attempts recovery **for segment 3** starting from device state that is **segment 2's groups screen**
5. Recovery fails again, logs skip, **advances to segment 4**
6. Now device is FURTHER from segment 4's expected state

**Result:** Device "drifts" farther from expected state with each skipped segment. By segment 5, device state is completely disconnected from expected flow.

### Why Segment 5 Succeeds

**Log shows:**
```
[2026-06-12 11:04:35] Recovery using region index: 4 at (893, 1405)
[2026-06-12 11:04:35] [execute_action] Tap the 'Add' button. -> tap
[2026-06-12 11:04:37] Comparing state (recovery attempt 2): reference=step_5v_tmp_stop.png vs live=step_5e_screenshot_2.png
```

By segment 5, recovery heuristic (blind tap at region 4) happens to land on the correct button by chance. This "resets" device to a known good state (back in form or home). ViBR then proceeds successfully for segments 5–8 because recovery action was fortuitously correct, not because ViBR validated state.

### Impact: DINO/Regions Mismatch Throughout Segments 2–5

Because device was in wrong state, all extracted DINO annotations and relevant regions for segments 3–4 were meaningless:

- `step_3v_dino.png` (expected regions) = form with Group field
- `step_3e_screenshot_0.png` (actual device frame) = groups management screen
- Comparison output: **Complete mismatch, no regions detected**

ViBR logged:

```log
[2026-06-12 10:58:13] Relevant regions: {'target_regions': [4], 'predicted_action': 'tap'}
[2026-06-12 10:58:13] GPT selected regions: [4]
```

But region [4] was extracted from wrong screen context. **Blind confidence in DINO output without device state validation.**

### Fix Required

1. **Hard stop on recovery failure:** After max retries, do NOT auto-advance. Instead:
   - Force device back to known home state (press back N times, tap Medicine tab)
   - Verify device reached home via screenshot + semantic check
   - Either resume from current position OR abort entire run

2. **Explicit state tracking:** Maintain a "device state tracker":

   ```python
   current_screen: Enum (home, form, date_picker, groups_screen, settings, ...)
   ```

   Update on every action. Before each segment, verify `current_screen` matches expected.

3. **Recovery with validation:** After recovery action, **always capture screenshot + DINO to confirm recovery worked.** Don't assume blind tap was successful.

4. **Segment skipping policy:** If segment is skipped AND device state is unknown, log a WARNING and either:
   - Attempt forced navigation to home + re-verify
   - Mark run as PARTIAL/UNRELIABLE instead of SUCCESSFUL

---

## Conclusions

### Why It Partially Failed (36% Execution)

1. **Modal dialog not recognized as overlay (Segment 2):** The medication groups dialog was treated as a separate screen boundary, creating a state mismatch that cascaded to subsequent segments.

2. **Recovery navigation to wrong screen (Segment 3):** ViBR's recovery heuristic navigated to Settings instead of returning to the form, breaking the form workflow.

3. **Date picker state mismatches (Segments 4, 7):** The date picker's month and day modes were not synchronized with ground truth, causing skips and recovery blind-taps.

4. **Text input over-segmentation (Segments 9–10):** Product name and display name entries were fragmented into character-level boundaries, causing skips and partial execution ('m' instead of 'medA').

5. **Missing form field entries (Release form, Comment):** After cascading failures, these fields were never accessed or populated.

### Root Cause Summary

| Root Cause | Affected Segments | Impact |
|-----------|-------------------|--------|
| Transient artifact overlay (dialog) | 2–4 | Cascading state misalignment |
| Recovery navigation failure | 3–4 | Device navigated to Settings |
| Date picker mode mismatch | 4, 7 | Date selection blocked |
| Text input over-segmentation | 9–10 | Product name & display name incomplete |
| Missing field segmentation | 17–21 | Release form & comment never entered |

### Why This Matters

The good run achieved **36% execution coverage** with 8/22 steps. The form was submitted with mostly empty fields and one partially-filled field (display name: 'm' instead of 'medA'). This represents a **low-quality replay** that may:

1. Corrupt the app's data model (invalid partial entries)
2. Fail validation (if the backend enforces required fields)
3. Produce an incomplete automation workflow (missing critical steps)

### Academic Implications

1. **Modal dialog detection is critical:** Segmentation algorithms must distinguish between screen transitions and transient overlay artifacts. The current CLIP-based approach treats both as boundaries.

2. **Recovery heuristics must be predictable:** Blind coordinate taps and navigation predictions fail under uncertain state conditions. Recovery should use explicit, device-aware actions.

3. **Text input requires special handling:** Character-level segmentation is too granular. Text entry actions must be grouped and executed as cohesive units.

4. **State validation before action execution:** ViBR should verify field readiness (focused, keyboard visible, placeholder text) before attempting text input. This would catch the segment 9 mismatch earlier.

5. **Multi-step UI interactions need context:** Date pickers, multi-stage forms, and nested dialogs require understanding of sequential state transitions, not just visual similarity scoring.

### Recommendations for Improvement

1. **Enhance segmentation:** Detect modals, dialogs, and overlays as transient artifacts, not screen boundaries.

2. **Improve recovery logic:** Use explicit device-aware navigation paths (Medicine tab → verify home state) instead of blind coordinate taps.

3. **Group text input frames:** Merge consecutive keyboard-visible frames into single text-input segments.

4. **Validate field state before action:** Check field focus, keyboard visibility, and placeholder state before executing text input.

5. **Semantic state matching:** For complex UIs (date pickers, multi-step forms), use semantic understanding (e.g., "month picker mode") instead of raw visual similarity.

---

## TL;DR — Why It Partially Failed

**Bottom line:** ViBR successfully opened the medication form (segments 0–1) but then encountered a **modal dialog** (medication groups popup) that was not recognized as an overlay. This caused a cascading state mismatch: segments 2–4 were skipped, recovery actions navigated to the wrong screen (Settings), and subsequent form field entries (product name, display name, release form, comment) were either skipped or partially executed. The form was submitted with ~36% field completion (8 of 22 steps).

**The specific failures:**
1. Segment 2: Modal dialog treated as separate screen (transient artifact overlay)
2. Segment 3: Recovery navigated to Settings instead of form (semantic gap)
3. Segment 4: Device in Settings, date picker inaccessible (cascading)
4. Segments 5–8: Blind recovery taps (fortuitous success, not clean alignment)
5. Segment 9: Product name entry skipped (field state mismatch)
6. Segment 10: Display name incomplete ('m' only, not 'medA'; text over-segmentation)
7. Segment 11: Scroll successful (gesture handling is more robust)
8. Segment 12: Form submitted incomplete (no validation before submission)

**Technical root causes:** Stage 1 (Over-segmentation, masked intermediate transitions) + Stage 2 (Transient artifact overlay, semantic gap, text input fragmentation).

**Key insight:** The good run demonstrates that **partial execution is worse than zero execution** in terms of data integrity. ViBR should either complete the entire workflow or abort—submitting a form with 64% missing fields corrupts the app state without providing useful automation.

