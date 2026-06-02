# Run Issue Report: adaway (bad run)

**App:** adaway
**Model:** gemini-2.5-pro
**Quality:** bad
**Pipeline status:** successful
**Scenes detected:** 3
**Actions executed:** 1
**Skipped segments:** 2

---

## Problems Found

### [2: GUI State Comparison] — Dynamic Content Change

*Step 0: State mismatch*

**Mismatch reason (from log):**
> the reference image shows a search screen with a search bar and a keyboard. the current image shows a list of 'hosts sources' with a title and list items. these are two completely different screens with different functionalities.


### [1: Action Segmentation] — Dynamic Element False Boundary

*Step 1: State mismatch*

**Mismatch reason (from log):**
> the current screen shows a list of 'hosts sources', while the reference screen displays a dialog to 'add host to whitelist'. these are fundamentally different screens with different ui elements and purposes.


---

## Limitations & Root Cause Analysis

### Dynamic Content Change
Dynamic/session-specific content changes (feed, ads, personalization). This failure mode occurred 1 time(s) in this run.

Dynamic GUI content changes between sessions (personalized feeds, advertisements, user profiles). ViBR's holistic GUI comparison cannot match screens with dynamic content differences. This maps to the 'Dynamic/session-specific content' failure mode (Section 3.2.4, Figure 7f). A possible mitigation would be to focus comparison on the Region of Interest (target element) rather than the whole GUI, or to use content-agnostic structural matching.

### Dynamic Element False Boundary
Dynamic GUI elements (ads, video) create spurious scene cuts. This failure mode occurred 1 time(s) in this run.

Dynamic GUI elements such as advertisements or video playback produce continuous frame differences that are mistakenly interpreted as separate user actions. This maps to the 'Dynamic element false boundary' failure mode (Section 3.1.4). A possible mitigation would be to filter known dynamic regions before segmentation, or to use content-aware frame comparison that ignores high-entropy (dynamic) areas.


---

## Summary of Limitations

| Stage | Failure Category | Occurrences | Impact |
|---|---|---|---|
| 1: Action Segmentation | Dynamic Element False Boundary | 1 | Segment skipped |
| 2: GUI State Comparison | Dynamic Content Change | 1 | Segment skipped |

**Overall impact:** 2 of 3 replay steps failed, meaning ViBR could not fully reproduce the recorded bug scenario. The agent achieved 33% action coverage.
