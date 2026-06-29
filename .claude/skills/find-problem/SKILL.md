---
name: find-problem
description: Compare truth value video with ViBR run log, analyze gaps and failures, report findings academically
---

# Find Problem Skill

Compare truth value video execution with ViBR run log execution. Identify missing steps, failures, and root causes. Report academically.

## Task

When invoked, Claude will perform ground-truth analysis:

0. **Parse invocation args** — if the skill was invoked with positional args (e.g. `/find-problem homemedkit1 batterytemperaturedisplay1`):
   - Treat each arg as an `app_name` to process
   - Use `quality` from `approach/input/config.yml` for all apps (shared setting)
   - If no args provided → fall back to reading `app_name` from config (existing behavior, run single app)

**LOOP:** If multiple app_names were parsed in Step 0, repeat Steps 1–6 for each app sequentially.
Write one report per app: `apps/{app_name}-{gemini_model}/{quality}-run-issue.md`

1. **Read config** from `approach/input/config.yml` — extract `run.quality` (good|bad), `model.gemini_model`. Use `app_name` from Step 0 arg (or fallback to config if no args).

2. **Locate or generate ground truth** — MANDATORY ARTIFACT:

   **2a. Check for existing truth JSON**:
   - Look for pre-existing truth value file: `apps/{app_name}-{gemini_model}/{quality}-truth.json`
   - If found → verify it contains all required fields (video_summary, steps[], detected_action_types[], overall_flow[], human_readable_step_summary[])
   - If valid → proceed to Step 3

   **2b. Generate truth value if missing (Claude vision analysis) — REQUIRED IF 2a FAILS**:
   - If no valid truth JSON exists, generate from video using Claude's vision (non-negotiable)
   - Locate video: `apps/{app_name}-{gemini_model}/{quality}-video.mp4`
   - If missing: ERROR — "No {quality}-video.mp4 found for {app_name}. Cannot generate truth value."
   - Extract frames at 1fps: `ffmpeg -i {quality}-video.mp4 -vf fps=1 /tmp/{app_name}_{quality}_truth_frames/frame_%04d.png`
   - Read extracted frames using Claude Code's image vision capability
   - Analyze frames sequentially to identify: user actions, screen transitions, timing, UI elements
   - Apply **Truth Value Generation Prompt** (section below) to analyze the video frames
   - Generate structured JSON output matching required schema
   - **CHECKPOINT: Verify JSON contains all required fields before saving**
   - Save output as `apps/{app_name}-{gemini_model}/{quality}-truth.json`
   - Required fields (mandatory): video_summary, steps[], detected_action_types[], overall_flow[], human_readable_step_summary[]
   - **VALIDATION: Do NOT proceed to Step 3 until truth JSON exists and is valid**
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

---

## Problem Category Taxonomy

When classifying failures in Step 5, use this taxonomy to assign:
- `category_phase` — the phase label
- `category_name` — numbered sub-category (e.g. "1.1. Video Input Processing")
- `category_issue` — the specific issue string from the list below

### Phase 1: Action Segmentation

#### 1.1. Video Input Processing
- Compression artifacts alter GUI appearance
- Frame drops or variable frame rates
- Motion blur during scrolling
- Screen recording quality differences
- Y-channel loses color information that may be semantically important

#### 1.2. CLIP Embedding
- Embeddings miss subtle UI changes
- CLIP not trained specifically on mobile GUIs
- Similar screens mapped too closely
- Different themes/devices produce embedding drift
- Small interactive changes may be ignored

#### 1.3. Similarity Computation
- Fixed threshold (0.95) may not generalize
- False transitions from animations
- Missed transitions during subtle state changes
- Different apps require different thresholds
- Noise accumulates over long recordings

#### 1.4. Scene Detection
- Incorrect grouping of frames
- One action split into multiple segments
- Multiple actions merged together
- Scroll actions produce unstable boundaries
- Timing sensitivity (±3 frames may be insufficient)

### Phase 2: GUI State Comparison

#### 2.5. Region Detection (GroundingDINO)
- Missed interactive elements
- Incorrect bounding boxes
- Prompt sensitivity
- Over-detection of non-interactive elements
- Poor performance on custom UI components

#### 2.6. ROI Selection (GPT-4o)
- Wrong clicked element identified
- Ambiguous causal attribution
- Nearby elements confused
- Multiple simultaneous UI changes
- Model reasoning inconsistencies

#### 2.7. State Consistency Check (GPT-4o)
- False positives ("same state" when not)
- False negatives ("different state" when equivalent)
- Functional equivalence difficult to judge
- Hidden state differences undetectable visually
- Hallucinated UI relationships

#### 2.8. UI Hierarchy Parsing
- Incomplete XML extraction
- Dynamic elements missing from hierarchy
- Accessibility metadata unavailable
- Coordinates inconsistent across devices
- Custom-rendered widgets poorly represented

### Phase 3: Bug Replay on Device

#### 3.9. Action Space Definition
- Action vocabulary too limited
- Missing gestures (pinch, swipe, long press, drag)
- Complex actions poorly represented
- Context-dependent actions ignored

#### 3.10. GUI Perception
- Incorrect screen understanding
- Occluded elements
- Visual grounding errors
- Annotation ambiguity
- Screen clutter overwhelms model

#### 3.11. Action Inference (GPT-4o)
- Wrong next action predicted
- Exploration strategy inefficient
- Error recovery loops
- Ambiguous replay decisions
- Model drift during long replay sequences

#### 3.12. Action Execution
- ADB timing issues
- Device latency differences
- Tap coordinates become invalid
- Keyboard/input synchronization failures
- OS permission dialogs interrupt execution

### Misc

For failures that don't map to any phase above:

- `category_phase`: Misc
- `category_name`: Misc — {short descriptive name}
- `category_issue`: {description of the specific issue observed}

---

6. **Write academic report** as `apps/{app_name}-{gemini_model}/{quality}-run-issue.md`:
   
   **Log Summary step (do first):**
   - Read the full `{quality}-run.log`
   - Find the line containing `Loading GroundingDINO model` — start from the NEXT non-httpx, non-google_genai.models line after it
   - Filter out all lines with `[httpx]` or `[google_genai.models]` in the module field
   - Build a timeline table from remaining lines: extract timestamp, module, and event summary
   - Write a 2–4 sentence Interpretation paragraph: what happened, where the first failure was, what cascaded from that
   - Place this as the **first section** of the report (before Executive Summary)
   
   **Report sections:**
   - Log Summary: extracted timeline of events from log, with interpretation
   - Executive Summary: gap analysis (expected vs actual)
   - Ground Truth vs Execution: side-by-side step comparison
   - Video vs Log Comparison (if video processed): timeline of frames vs log events, highlight gaps
   - Step-by-Step Failure Analysis: for each missing/failed step, explain why
   - Root Cause Categorization: group failures by ViBR category + underlying issue
   - Impact Assessment: what prevented full execution, cascading failures
   - Conclusions: academic tone, grounded in ViBR paper

## Report Structure

File: `apps/{app_name}-{gemini_model}/{quality}-run-issue.md`

Sections (in order):

1. **Log Summary** — timeline table (Time | Module | Event) filtered to exclude `[httpx]` and `[google_genai.models]` lines, starting after `Loading GroundingDINO model`. End with 2–4 sentence Interpretation paragraph.
2. **Executive Summary** — steps_expected vs steps_executed, gap count, coverage %.
3. **Ground Truth vs Execution Log** — table: Step# | Expected Action | Executed ✓/✗ | Status | Issue Category
4. **Video vs Log Comparison** *(if video processed)* — table: Frame Range | Segment | Log Shows | Video Shows | Gap?. Note hidden actions, timing gaps, state mismatches.
5. **Detailed Failure Analysis** — per failed step: expected behavior, log entry, mismatch reason, root cause category + evidence + cascade impact.
6. **Root Cause Categorization** — group failures by Stage 1/2/3 sub-categories with counts.
7. **Conclusions** — academic tone: coverage %, dominant failure mode, underlying limitation.
8. **TL;DR** — bullet success/failure reasons + one-sentence bottom line.

---

## Truth Value Generation Prompt

When generating a truth value from video (Step 2b), use the following prompt and schema:

### Prompt

Analyze the uploaded Android app screen recording and generate a structured JSON output.
Break the video into meaningful interaction steps. Each step should describe what screen is visible,
what the user does, what changes on screen, and the likely user intent.

### Required JSON Schema

Top-level fields (all mandatory):
- `video_summary`: `{app_name, overall_goal, device_type: "Android", description}`
- `steps[]`: one object per interaction step (see fields below)
- `detected_action_types[]`: list of action vocab terms used
- `overall_flow[]`: high-level flow summary list
- `human_readable_step_summary[]`: plain-English summary per step, 1:1 with steps[]

Step fields: `step_number`, `timestamp_start`, `timestamp_end`, `screen_name`, `what_screen_is_visible`, `visible_ui_elements[]`, `user_gesture` (from vocab), `target_element`, `system_response`, `navigation_change` ("none" if absent), `data_entered` ("" if none), `visual_feedback`, `intent_task`, `confidence` (high|medium|low)

### Action Vocabulary

`tap`, `double_tap`, `long_press`, `scroll_up`, `scroll_down`, `swipe_left`, `swipe_right`, `type_text`, `delete_text`, `open_keyboard`, `close_keyboard`, `press_back`, `press_home`, `open_dialog`, `close_dialog`, `submit`, `select_item`, `toggle`, `drag`, `wait`, `screen_transition`

### Analysis Rules

- Timestamps for every meaningful action or screen change.
- Never invent names/text/actions not visible — write "unclear" if unsure.
- Group tiny repeated actions serving same purpose into one step.
- Focus only on visible Android UI; do not assume hidden logic or identity.
- Output: valid JSON only. No markdown wrapper, no explanation outside JSON.