---
name: Find Problem Implementation
description: Internal Claude implementation for /find-problem analysis
hidden: true
---

# Implementation Instructions for /find-problem

When invoked, execute these steps:

## Step 1: Read Config
Read `approach/input/config.yml` using Read tool. Extract:
- `run.app_name`
- `run.quality` (good or bad)
- `model.gemini_model`

## Step 2: Build Paths
Construct file paths:
- app_dir = `apps/{app_name}-{gemini_model}/`
- log_path = `{app_dir}/{quality}-run.log`
- summary_path = `{app_dir}/{quality}-run-summary.json`
- analysis_path = `{app_dir}/{quality}-video-analysis.json`
- output_path = `{app_dir}/{quality}-run-issue.md`

## Step 3: Read Artifacts (parallel)
Read all three in parallel using Read tool:
1. summary JSON
2. run log (first 200 lines to identify key patterns)
3. video-analysis JSON (if exists)

Parse JSON files. Grep/search log for patterns:
- `[WARNING] Skipping action:` — extract mismatch reason text after "Mismatch reason:"
- `[WARNING] Attempting to align state` — count occurrences

## Step 4: Extract Key Metrics
From summary JSON:
- `status` (usually "successful")
- `scenes` (int)
- `actions_executed` (int)
- `steps_taken` (array of strings)

Compute:
- `skipped = scenes - actions_executed`

From log:
- List of (step_index, mismatch_reason) tuples for each skipped action

From analysis JSON:
- List of steps with `"confidence": "low"`

## Step 5: Classify Each Failure
For each skipped action's mismatch_reason text, classify using keyword matching:

**Stage 1: Action Segmentation**
- If reason contains "loading" or "delay" → **over-segmentation**
- If reason contains "ad", "advertisement", "video", "playback", "dynamic" → **dynamic-element-false-boundary**

**Stage 2: GUI State Comparison**
- If reason contains "layout", "position", "align", "shift" → **resolution-layout-mismatch**
- If reason contains "color", "theme", "dark mode", "font", "scale" → **cosmetic-theme-difference**
- If reason contains "toast", "banner", "notification", "overlay" → **transient-artifact-overlay**
- If reason contains "border", "artifact", "watermark", "container" → **screen-recording-artifact**
- If reason contains "scroll", "scrolled", "shifted", "moved" → **scroll-induced-element-shift**
- If reason contains "content", "dynamic", "different", "changed", "feed", "profile" → **dynamic-content-change**

**Stage 3: Bug Replay on Device**
- If reason contains "input", "masked", "password", "pin", "*" → **masked-intermediate-transition**
- Otherwise (default) → **semantic-gap**

Store classification as: `category → (stage, description, section_ref)`

## Step 6: Build Report Markdown

Output structure:

```markdown
# Run Issue Report: {app_name} ({quality} run)

**App:** {app_name}
**Model:** {gemini_model}
**Quality:** {quality}
**Pipeline status:** {status}
**Scenes detected:** {scenes}
**Actions executed:** {actions_executed}
**Skipped segments:** {skipped}

---

## Problems Found

[For each skipped step, add section:]

### [Stage N: {Stage Name}] — {Category Name}
*Step {index}: State mismatch*

**Mismatch reason (from log):**
> {exact reason text from log}

**Evidence:** {context: e.g., "1 action skipped; recovery exhausted after 3 tries"}

[... repeat for each skipped step ...]

[If no skipped steps:]
*No failures detected. All segments executed successfully.*

---

## Limitations & Root Cause Analysis

[For each unique category found, add section with academic explanation:]

### {Category Name}
{Brief description from ViBR paper}

[ViBR's {stage} relies on {mechanism}. In this run, {specific observation}. This maps to the "{paper category name}" failure mode (ViBR Section {N.N.N}, Figure {N}): {paper explanation}. The root cause is {deeper reason}. A possible mitigation would be {suggestion}.]

[If no failures:]
*No limitations detected in this run. All segments executed successfully.*

---

## Summary of Limitations

| Stage | Failure Category | Occurrences | Impact |
|---|---|---|---|
[Add row per unique stage/category pair]

**Overall impact:** {X} of {Y} replay steps failed, meaning ViBR could not fully reproduce the recorded bug scenario. The agent achieved {coverage}% action coverage.

[If no failures:]
| — | — | 0 | None |

**Overall impact:** All {scenes} replay steps completed successfully, meaning ViBR fully reproduced the recorded bug scenario.
```

## Step 7: Write Report
Use Write tool to create `{output_path}` with final markdown.

## Step 8: Summarize for User
Print summary:
- Status: {status}
- Scenes: {scenes}, Actions: {actions_executed}, Skipped: {skipped}
- Failure categories found (if any)
- Path to written report

---

## Category Explanations (for Step 6 output)

### Over-segmentation
ViBR's Action Segmentation (Section 2.1) uses CLIP embeddings to detect scene boundaries. Resource loading delays (images, data) can cause one user action to produce two segments: one for the GUI transition, another for delayed content rendering. This maps to the "over-segmentation" failure mode (Section 3.1.4).

### Dynamic Element False Boundary
Dynamic GUI elements (ads, video playback) produce continuous frame differences mistakenly interpreted as separate actions. This maps to "dynamic element false boundary" (Section 3.1.4).

### Resolution / Layout Mismatch
ViBR's GUI State Comparison (Section 2.2.3) uses visual similarity matching. Resolution or layout differences between recording and live device cause element misalignment, leading the LLM [YES/NO] classifier to flag matching states as inconsistent. This maps to "resolution/layout mismatch" (Section 3.2.4, Figure 7a).

### Cosmetic Theme Difference
Cosmetic changes (dark mode, font scaling, language) introduce visual differences without changing interaction semantics. ViBR's whole-GUI comparison cannot distinguish functional changes from cosmetic ones. This maps to "cosmetic theme difference" (Section 3.2.4, Figure 7b).

### Transient Artifact Overlay
Toast messages, status banners appear during replay, introducing visual differences the LLM classifier misinterprets as state inconsistency. ViBR has no mechanism to distinguish transient artifacts from functional changes. This maps to "transient artifact overlay" (Section 3.2.4, Figure 7c).

### Screen Recording Artifact
Emulator borders, watermarks degrade image-based comparisons. ViBR's visual similarity matching is sensitive to these artifacts. This maps to "screen recording artifact" (Section 3.2.4, Figure 7d).

### Scroll-Induced Element Shift
Scrolling causes GUI elements to shift position. ViBR's Region-of-Interest detection (Sections 2.2.1-2.2.2) may misalign due to shifts, causing the VLM to reason over the wrong region. This maps to "scroll-induced element shift" (Section 3.2.4, Figure 7e).

### Dynamic / Session-Specific Content
Dynamic content changes between sessions (personalized feeds, ads, user profiles). ViBR's holistic GUI comparison cannot match screens with dynamic content differences. This maps to "dynamic/session-specific content" (Section 3.2.4, Figure 7f).

### Masked Intermediate Transition
Inputting sensitive values (passwords, PINs) produces masked output (shown as dots). ViBR cannot identify the precise input value from masked screenshots alone. This maps to "masked intermediate transition" (Section 3.3.4, Figure 8b).

### Semantic Gap
ViBR's action inference (Section 2.3.3) relies on LLM to infer next action from consecutive GUI states. Semantic gap between pre- and post-action screens makes inference impossible without intermediate context. This maps to "semantic gap between GUI states" (Section 3.3.4, Figure 8a).