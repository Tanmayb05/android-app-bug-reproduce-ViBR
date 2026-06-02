---
name: Find Problem
description: Analyze a ViBR run, identify failure categories, write issue report
---

## Find Problem

Analyze a completed ViBR run (good or bad quality) to identify failures and write structured issue report (`<quality>-run-issue.md`) categorizing them using ViBR paper taxonomy across three pipeline stages: Action Segmentation, GUI State Comparison, Bug Replay on Device.

### How to Use

Just invoke `/find-problem` — Claude will:

1. **Read** `approach/input/config.yml` to get app_name, quality, gemini_model
2. **Parse** run artifacts:
   - `apps/<app>-<model>/<quality>-run-summary.json` — status, scenes, actions_executed
   - `apps/<app>-<model>/<quality>-run.log` — grep for `[WARNING] Skipping action:` and mismatch reasons
   - `apps/<app>-<model>/<quality>-video-analysis.json` — low-confidence steps
3. **Classify** each failure by mismatch reason text using ViBR paper taxonomy (9 categories across 3 stages)
4. **Write** `<quality>-run-issue.md` with:
   - Metadata (app, model, quality, scenes, executed, skipped)
   - Problems Found (one section per skipped step with category and mismatch reason)
   - Limitations & Root Cause Analysis (academic explanation per category, grounded in paper sections)
   - Summary Table (Stage | Category | Count | Impact)
   - Overall Impact (X of Y steps failed, action coverage %)

### Failure Categories (from ViBR Paper)

**Stage 1: Action Segmentation**
- Over-segmentation (resource loading delay) — keyword: "loading", "delay"
- Dynamic element false boundary (ads, video) — keyword: "ad", "video", "dynamic"

**Stage 2: GUI State Comparison** (most common)
- Resolution / layout mismatch — keyword: "layout", "position"
- Cosmetic theme difference — keyword: "color", "theme", "dark", "font"
- Transient artifact overlay (toast, banner) — keyword: "toast", "banner", "notification"
- Screen recording artifact — keyword: "border", "artifact", "watermark"
- Scroll-induced element shift — keyword: "scroll", "shifted", "moved"
- Dynamic/session-specific content — keyword: "content", "dynamic", "different", "changed"

**Stage 3: Bug Replay on Device**
- Semantic gap between GUI states — default if no keywords match
- Masked intermediate transition (PIN/password) — keyword: "input", "masked", "password", "pin"

### Example Output

```
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

...

## Limitations & Root Cause Analysis

### Dynamic Content Change
Dynamic GUI content changes between sessions (personalized feeds, advertisements, user profiles). ViBR's holistic GUI comparison cannot match screens with dynamic content differences. This maps to the 'Dynamic/session-specific content' failure mode (Section 3.2.4, Figure 7f).

...

## Summary of Limitations

| Stage | Failure Category | Occurrences | Impact |
|---|---|---|---|
| 2: GUI State Comparison | Dynamic Content Change | 1 | Segment skipped |

**Overall impact:** 2 of 3 replay steps failed, meaning ViBR could not fully reproduce the recorded bug scenario. The agent achieved 33% action coverage.
```