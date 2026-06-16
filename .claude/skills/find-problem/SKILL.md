---
name: find-problem
description: Compare truth value video with ViBR run log, analyze gaps and failures, report findings academically
---

# Find Problem Skill

Compare truth value video execution with ViBR run log execution. Identify missing steps, failures, and root causes. Report academically.

## Task

When invoked, Claude will perform ground-truth analysis:

1. **Read config** from `approach/input/config.yml` — extract `run.app_name`, `run.quality` (good|bad), `model.gemini_model`

2. **Locate or generate ground truth**:

   **2a. Check for existing truth JSON**:
   - Look for pre-existing truth value file:
     - `apps/{app_name}-{gemini_model}/{quality}-truth.json` (truth for the run video being analyzed)
   - If found → use it and skip to Step 3

   **2b. Generate truth value if missing (Claude vision analysis)**:
   - If no truth JSON exists, generate from the run video using Claude's vision
   - Locate run video: `apps/{app_name}-{gemini_model}/{quality}-video.mp4`
   - If missing: error out with "No {quality}-video.mp4 found for {app_name}. Cannot generate truth value."
   - Extract frames at 1fps using ffmpeg: `ffmpeg -i {quality}-video.mp4 -vf fps=1 /tmp/{app_name}_{quality}_truth_frames/frame_%04d.png`
   - Read extracted frames using Claude Code's image vision capability
   - Apply **Truth Value Generation Prompt** (see section below) to analyze the video frames
   - Claude generates structured JSON output matching the required schema
   - Save output as `apps/{app_name}-{gemini_model}/{quality}-truth.json`
   - Truth JSON must contain: video_summary, steps[], detected_action_types[], overall_flow[], human_readable_step_summary[]
   - Proceed to Step 3 using this generated truth file

3. **Locate ViBR run artifacts**:
   - `apps/{app_name}-{gemini_model}/{quality}-run-summary.json` — execution status, step counts
   - `apps/{app_name}-{gemini_model}/{quality}-run.log` — detailed execution log with warnings/failures
   - `apps/{app_name}-{gemini_model}/{quality}-video-analysis.json` — confidence scores per step
   - `apps/{app_name}-{gemini_model}/{quality}-video.mp4` — actual video of run execution (if available)

3b. **Extract video keyframes** (MANDATORY — always extract, even if artifacts present):
   - Parse `Clamped segment boundaries: [(start, end), ...]` from log to identify segment frame ranges
   - Extract 1fps timeline frames from video using ffmpeg or cv2 (Python utility available)
   - Extract keyframes at segment start/end boundaries PLUS full timeline across all segments
   - Compare each segment's log events (wait, skip, execute) to visual content in frames
   - Flag segments where log shows `wait`/`skip` but video shows active UI (keyboard, form, dialog, user interaction)
   - Identify hidden actions: steps the user took manually in the video but ViBR missed executing
   - **CRITICAL:** Do NOT skip extraction even if step_Nv_* PNG artifacts exist. Artifacts show only snapshots; timeline extraction reveals state transitions, timing, and *why* ViBR failed. Missing timeline analysis = incomplete root cause diagnosis.

4. **Compare execution**:
   - Extract truth value steps (steps visible in the run video)
   - Extract executed steps from run log (actions ViBR actually executed on device)
   - Calculate: steps_expected (from video), steps_executed (from log), steps_missing = steps_expected - steps_executed
   - Identify WHICH steps ViBR failed to execute and WHERE (step index, action type)

5. **Analyze each failure** — for each step in the video that ViBR did not execute:
   - Extract error/warning from log
   - Identify mismatch reason (GUI diff, timeout, state mismatch, etc.)
   - Classify using ViBR taxonomy:

     **Stage 1: Action Segmentation**
     - Over-segmentation: keywords "loading", "delay", "resource"
     - Dynamic element false boundary: keywords "ad", "video", "playback", "dynamic"

     **Stage 2: GUI State Comparison**
     - Resolution/layout mismatch: keywords "layout", "position", "align", "shift"
     - Cosmetic theme difference: keywords "color", "theme", "dark mode", "font"
     - Transient artifact overlay: keywords "toast", "banner", "notification"
     - Screen recording artifact: keywords "border", "artifact", "watermark"
     - Scroll-induced element shift: keywords "scroll", "shifted", "moved"
     - Dynamic/session-specific content: keywords "content", "dynamic", "different", "changed"

     **Stage 3: Bug Replay on Device**
     - Masked intermediate transition: keywords "input", "masked", "password", "pin"
     - Semantic gap (default): if no keywords match

6. **Write academic report** as `apps/{app_name}-{gemini_model}/{quality}-run-issue.md`:
   - Executive Summary: gap analysis (expected vs actual)
   - Ground Truth vs Execution: side-by-side step comparison
   - Video vs Log Comparison (if video processed): timeline of frames vs log events, highlight gaps
   - Step-by-Step Failure Analysis: for each missing/failed step, explain why
   - Root Cause Categorization: group failures by ViBR category + underlying issue
   - Impact Assessment: what prevented full execution, cascading failures
   - Conclusions: academic tone, grounded in ViBR paper

## Report Structure

```markdown
# ViBR Run Analysis: {app_name} ({quality} run)

## Executive Summary

**Ground Truth:** {steps_expected} expected steps
**Actually Executed:** {steps_executed} steps
**Gap:** {steps_missing} steps missing ({coverage}% execution rate)

The {quality} run fell short of ground truth by {steps_missing} step(s). Analysis identifies systematic failures in GUI state comparison and action segmentation.

---

## Ground Truth vs Execution Log

| Step # | Expected Action | Executed | Status | Issue Category |
|--------|-----------------|----------|--------|-----------------|
| 0 | {action} | ✓ | Success | — |
| 1 | {action} | ✗ | Failed | {Category Name} |
| ... | ... | ... | ... | ... |

---

## Video vs Log Comparison (if applicable)

Compares video timeline frames to log events:

| Frame Range | Segment | Log Shows | Video Shows | Gap? |
|-------------|---------|-----------|-------------|------|
| 0–100 | Seg 0 | Wait for data | Numeric keypad visible (user typing) | ⚠️ YES |
| 200–300 | Seg 1 | Action executed (tap) | Post-tap transition | ✓ Aligned |
| ... | ... | ... | ... | ... |

**Key Observations:**
- Hidden actions: steps user took manually but ViBR didn't detect
- Timing gaps: log shows `wait` while video shows user activity
- State mismatches: log says "state mismatch" but video shows what actually happened

---

## Detailed Failure Analysis

### Step {N}: {Expected Action} — FAILED

**Expected behavior (ground truth):**
> {action description from truth value}

**What the log shows:**
> {actual log entry}

**Mismatch reason:**
> {extracted from log warning}

**Root cause:** {Category} — {explanation}
- Evidence: {relevant log lines or artifact data}
- Why it matters: {impact on subsequent steps, if cascading}

...

---

## Root Cause Categorization

### Stage 1: Action Segmentation ({count} failures)
- Over-segmentation: {count}
- Dynamic element false boundary: {count}

### Stage 2: GUI State Comparison ({count} failures)
- Resolution/layout mismatch: {count}
- Cosmetic theme difference: {count}
- Transient artifact overlay: {count}
- Screen recording artifact: {count}
- Scroll-induced element shift: {count}
- Dynamic/session-specific content: {count}

### Stage 3: Bug Replay on Device ({count} failures)
- Semantic gap: {count}
- Masked intermediate transition: {count}

---

## Conclusions

The {quality} run achieved {coverage}% execution of ground truth. Primary failure mode: {dominant category}. This suggests {academic interpretation of underlying limitation}.

The gap of {steps_missing} steps represents {interpretation of severity and implications}.

---

## TL;DR — Why It Failed/Succeeded

**Success reasons (if applicable):**
- All segments detected and processed correctly
- UI state matching aligned between video and device
- ViBR action inference worked as expected
- No critical state mismatches

**Failure reasons (if applicable):**
- {dominant_category}: {one-line reason}
  - {specific evidence from log or video}
  - {impact: what prevented execution}
- {secondary_category}: {one-line reason}
  - {specific evidence}
  - {impact}

**Bottom line:** {executive summary in 1-2 sentences: what broke and why. e.g., "ViBR detected empty data state and correctly skipped action, but video shows user manually entered data—indicates missing UI element detection or form interaction logic."}
```

---

## Truth Value Generation Prompt

When generating a truth value from a good-quality video (Step 2b), use the following prompt and schema:

### Prompt

Analyze the uploaded Android app screen recording and generate a structured JSON output.
Break the video into meaningful interaction steps. Each step should describe what screen is visible,
what the user does, what changes on screen, and the likely user intent.

### Required JSON Format

```json
{
  "video_summary": {
    "app_name": "",
    "overall_goal": "",
    "device_type": "Android",
    "description": ""
  },
  "steps": [
    {
      "step_number": 1,
      "timestamp_start": "00:00",
      "timestamp_end": "00:00",
      "screen_name": "",
      "what_screen_is_visible": "",
      "visible_ui_elements": [],
      "user_gesture": "",
      "target_element": "",
      "system_response": "",
      "navigation_change": "",
      "data_entered": "",
      "visual_feedback": "",
      "intent_task": "",
      "confidence": "high | medium | low"
    }
  ],
  "detected_action_types": [],
  "overall_flow": [],
  "human_readable_step_summary": []
}
```

### Analysis Instructions

- Use timestamps for every meaningful user action or screen change.
- Do not invent app names, button names, text, or actions that are not visible.
- If any text or UI element is unclear, write "unclear" instead of guessing.
- Group very small repeated actions into one step when they serve the same purpose.
- Use simple action names from the action vocabulary (below).
- Focus only on visible Android app UI behavior.
- Do not assume background logic, user identity, account details, or hidden app behavior.
- For intent, infer only from the visible action and screen context.
- Return only valid JSON. Do not include markdown, comments, or explanation outside the JSON.

### Action Vocabulary

```
tap
double_tap
long_press
scroll_up
scroll_down
swipe_left
swipe_right
type_text
delete_text
open_keyboard
close_keyboard
press_back
press_home
open_dialog
close_dialog
submit
select_item
toggle
drag
wait
screen_transition
```

### Field Guidelines

- **app_name:** Name of the app if visible. If not visible, use "unclear".
- **overall_goal:** The likely purpose of the full user flow based on visible actions.
- **description:** A short summary of what happens in the recording.
- **screen_name:** Name of the current screen if visible or reasonably clear.
- **what_screen_is_visible:** Plain description of the screen shown.
- **visible_ui_elements:** List of visible buttons, menus, tabs, fields, cards, dialogs, icons, or labels.
- **user_gesture:** One action from the action vocabulary.
- **target_element:** The UI element the user interacted with.
- **system_response:** What the app did after the action.
- **navigation_change:** Describe screen change, dialog open/close, drawer open/close, or write "none".
- **data_entered:** Any typed or selected data. If none, use an empty string.
- **visual_feedback:** Any visible feedback such as highlight, loading, popup, animation, selected state, or error.
- **intent_task:** The likely reason the user performed the action.
- **confidence:** Use "high" when clearly visible, "medium" when partially inferred, and "low" when uncertain.

### Human-Readable Summary Requirement

At the end of the JSON, include a field called `human_readable_step_summary`.
This must be a list of simple plain-English step descriptions.
Each item should summarize the matching detailed step in a way a non-technical person can understand.

Example format:
```
"Step 1: The app opens on the main screen and shows the available options.",
"Step 2: The user taps a button to open the next screen.",
"Step 3: The user scrolls down to view more content."
```

Each summary item should have a matching detailed step in the steps[] array.

### Output Requirements

- The final response must be valid JSON only.
- Do not wrap the JSON in markdown.
- Do not add explanations before or after the JSON.
- Make sure every detailed step has a matching simple summary in `human_readable_step_summary`.
```