# Video Analysis Using Codex

This is the repeatable workflow for producing a structured video analysis JSON from an Android screen recording using Codex.

The goal is to turn a video like:

```text
apps/<app-run>/<quality>-video.mp4
```

into:

```text
apps/<app-run>/<quality>-video-analysis.json
```

using the schema and instructions from:

```text
approach/prompts/video_analysis.txt
```

## Inputs

Required:

- A screen recording, usually `apps/<app-run>/<quality>-video.mp4`
- The analysis prompt, usually `approach/prompts/video_analysis.txt`

Useful when available:

- `apps/<app-run>/<quality>-run-summary.json`
- `apps/<app-run>/<quality>-run.log`
- Any generated artifacts under `apps/<app-run>/<quality>-artifacts/`

## Workflow

### 1. Read the Prompt

Start by reading the analysis prompt so the output matches the expected schema exactly.

```bash
sed -n '1,220p' approach/prompts/video_analysis.txt
```

The current prompt expects JSON with:

- `video_summary`
- `steps`
- `detected_action_types`
- `overall_flow`

Follow the prompt rules strictly:

- Use timestamps for meaningful actions.
- Do not invent details that are not visible.
- If text is unclear, write `"unclear"`.
- Group small repeated actions when appropriate.
- Use the prompt's action vocabulary.
- Return machine-readable JSON only in the final output file.

### 2. Verify Paths

Confirm the video exists and resolve any path typos before writing output.

```bash
rg --files apps approach | rg 'video_analysis\.txt|video\.mp4|video-analysis\.json|run-summary\.json|run\.log'
ls -la apps
ls -la apps/<app-run>
```

If the requested output path differs from the real app directory by an obvious typo, prefer the directory that actually contains the video. Note that decision in the final response.

### 3. Inspect Video Metadata

Use `ffprobe` to get duration, resolution, and frame rate.

```bash
ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,r_frame_rate \
  -of json \
  apps/<app-run>/<quality>-video.mp4
```

Use the duration to bound timestamps. For example, a `44.373` second video should have step timestamps between `00:00` and about `00:44`.

### 4. Sample Frames

Extract still frames at a regular interval. One frame every two seconds is a good starting point for short mobile recordings.

```bash
mkdir -p /private/tmp/<app-run>_<quality>_frames

ffmpeg -hide_banner -loglevel error -y \
  -i apps/<app-run>/<quality>-video.mp4 \
  -vf fps=1/2,scale=360:-1 \
  /private/tmp/<app-run>_<quality>_frames/frame_%03d.jpg
```

Adjust the sampling rate when needed:

- Use `fps=1` for fast interactions.
- Use `fps=1/2` or `fps=1/3` for slower flows.
- Keep a scaled copy for overview, but inspect original or higher-detail frames when text is hard to read.

### 5. Create a Contact Sheet

Make a tiled overview image so the whole flow can be scanned quickly.

```bash
ffmpeg -hide_banner -loglevel error -y \
  -pattern_type glob \
  -i '/private/tmp/<app-run>_<quality>_frames/frame_*.jpg' \
  -vf 'scale=180:-1,tile=4x6:padding=8:margin=8' \
  -frames:v 1 \
  /private/tmp/<app-run>_<quality>_contact.jpg
```

Inspect the contact sheet first. Identify:

- Major screen transitions
- Dialogs opening or closing
- Keyboard appearance
- Text entry
- Back navigation
- Toasts, snackbars, or validation messages

### 6. Inspect Key Frames Individually

Open individual frames around each meaningful transition. For each possible step, answer:

- What screen is visible?
- What UI elements are visible?
- What gesture likely happened?
- What element was targeted?
- What changed after the gesture?
- Was any data entered?
- How confident is the interpretation?

Use conservative language when fingers obscure the UI or text is blurry.

Good examples:

```json
"data_entered": "unclear"
```

```json
"confidence": "low"
```

Avoid guessing exact text from blurry frames. Mention possible readings only in descriptive fields if useful, and mark the actual entered data as `"unclear"`.

### 7. Cross-Check Logs When Available

If a run summary or run log exists, use it as supporting evidence, not as the sole source of truth.

```bash
sed -n '1,220p' apps/<app-run>/<quality>-run-summary.json

rg -n "Action|tap|type|search|dialog|hostname|screen|segment|gesture|input|submit" \
  apps/<app-run>/<quality>-run.log
```

Logs can help confirm:

- App name
- Detected scenes or segments
- Predicted actions
- Dialog names
- Automation failures or mismatches

Still prefer visible video evidence when the log disagrees with the recording.

### 8. Segment the Video Into Steps

Create one step for each meaningful user interaction or state change.

Typical Android video-analysis steps include:

- Initial screen visible
- Tap opens a new screen
- Search mode opens
- Keyboard opens
- Text is typed
- Dialog opens
- Text field validation appears
- Submit button is tapped
- Toast/snackbar appears
- Back navigation returns to the previous screen

Group repeated small actions into one step when they form one task. For example, several keystrokes in the same field should usually be one `type_text` step.

### 9. Choose Action Names

Use the action vocabulary from the prompt.

Common mappings:

- Finger taps a button: `tap`
- Text appears through keyboard input: `type_text`
- User clears text: `delete_text`
- Keyboard appears: often part of `tap` or `type_text`
- Dialog appears: `open_dialog` if the gesture itself is opening a dialog, or `tap` with dialog in `system_response`
- User taps ADD, OK, Save, or similar: `submit`
- User exits with Android or toolbar back: `press_back`
- Screen changes after an action: include `screen_transition` in `detected_action_types`

### 10. Write the JSON

Create the output file beside the input video.

```text
apps/<app-run>/<quality>-video-analysis.json
```

The JSON should follow this shape:

```json
{
  "video_summary": {
    "app_name": "",
    "overall_goal": "",
    "device_type": "Android",
    "description": ""
  },
  "steps": [],
  "detected_action_types": [],
  "overall_flow": []
}
```

Each step should include all fields required by `video_analysis.txt`, even when a value is empty or unclear.

### 11. Validate JSON

Always validate the file before considering the task done.

```bash
jq . apps/<app-run>/<quality>-video-analysis.json >/dev/null
```

If `jq` reports an error, fix the JSON before returning.

## Quality Rules

Use high confidence only when the screen, gesture, and result are visible.

Use medium confidence when the result is clear but the exact target is partly obscured.

Use low confidence when text or target details are blurry, hidden by a finger, or inferred from nearby frames.

Do not invent:

- Exact typed text
- User intent beyond visible UI context
- Hidden app state
- Error messages that cannot be read
- Backend/network behavior

Prefer descriptions like:

```text
The text is blurry, but a validation message appears.
```

over:

```text
The app rejects the hostname because it is invalid.
```

unless the rejection message is actually readable.

## Example Command Sequence

Replace `<app-run>` and `<quality>` with the target app directory and video quality.

```bash
sed -n '1,220p' approach/prompts/video_analysis.txt

ls -la apps/<app-run>

ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,r_frame_rate \
  -of json \
  apps/<app-run>/<quality>-video.mp4

mkdir -p /private/tmp/<app-run>_<quality>_frames

ffmpeg -hide_banner -loglevel error -y \
  -i apps/<app-run>/<quality>-video.mp4 \
  -vf fps=1/2,scale=360:-1 \
  /private/tmp/<app-run>_<quality>_frames/frame_%03d.jpg

ffmpeg -hide_banner -loglevel error -y \
  -pattern_type glob \
  -i '/private/tmp/<app-run>_<quality>_frames/frame_*.jpg' \
  -vf 'scale=180:-1,tile=4x6:padding=8:margin=8' \
  -frames:v 1 \
  /private/tmp/<app-run>_<quality>_contact.jpg

rg -n "Action|tap|type|search|dialog|screen|segment|gesture|input|submit" \
  apps/<app-run>/<quality>-run.log

jq . apps/<app-run>/<quality>-video-analysis.json >/dev/null
```

## Final Response Checklist

When reporting back, include:

- The output file path.
- Whether path typos were corrected.
- Whether JSON validation passed.
- Any uncertainty that remains, such as unreadable text or obscured gestures.
