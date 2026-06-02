---
name: run-analysis
description: Use when the user asks to run video analysis for this ViBR project, especially with "/run-analysis" or "/run-analysis <video-path>". Codex should analyze an Android screen recording itself using approach/prompts/video_analysis.txt and write a valid *-video-analysis.json file, without delegating to a runner script.
---

# Run Video Analysis

Use this skill when the user asks for `/run-analysis`, `/run-analysis <video-path>`, or otherwise asks Codex to create a video analysis JSON for a ViBR app recording.

Do the analysis directly in Codex. Do not create or rely on a Python runner script for this workflow.

## Inputs

- Prompt template: `approach/prompts/video_analysis.txt`
- Default config: `approach/input/config.yml`
- Default video path, when no path is supplied:
  `apps/<run.app_name>-<model.gemini_model>/<run.quality>-video.mp4`
- Default output path, when no path is supplied:
  `apps/<run.app_name>-<model.gemini_model>/<run.quality>-video-analysis.json`
- Explicit video path, when supplied after `/run-analysis`:
  use that exact video path.

For an explicit path ending in `-video.mp4`, write beside it as `-video-analysis.json`.
For any other explicit video filename, write beside it as `<stem>-analysis.json`.

## Workflow

1. Read `approach/prompts/video_analysis.txt`.
2. Resolve the input video:
   - If the user supplied a path, use that path.
   - Otherwise read `approach/input/config.yml`, then build the default path from `run.app_name`, `model.gemini_model`, and `run.quality`.
3. Verify the video exists before analysis. If it does not exist, stop and report the missing path.
4. Inspect video metadata with `ffprobe` when available so timestamps stay within the actual duration.
5. Sample frames with `ffmpeg` when useful. Prefer a temporary directory under `/private/tmp` or `/tmp`; do not commit sampled frames.
6. Analyze only visible Android UI behavior using the template prompt rules.
7. Write the output JSON to the resolved output path.
8. Validate the JSON with `jq . <output-path>` or `python -m json.tool <output-path>`.

## Analysis Rules

- Return JSON only in the file.
- Match the schema requested in `approach/prompts/video_analysis.txt`.
- Include every required step field from the prompt.
- Include one matching `human_readable_step_summary` item for every detailed step.
- Use timestamps for every meaningful action or screen change.
- Do not invent app names, button names, exact text, entered data, or actions.
- If text or UI is unclear, write `"unclear"`.
- Group tiny repeated actions when they serve one task.
- Use only action names from the prompt's action vocabulary.
- Prefer video evidence over logs. If logs or summaries are inspected, use them only as supporting evidence.

## Helpful Commands

Read config and prompt:

```bash
sed -n '1,220p' approach/input/config.yml
sed -n '1,260p' approach/prompts/video_analysis.txt
```

Inspect metadata:

```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate -of json <video-path>
```

Sample frames:

```bash
mkdir -p /private/tmp/vibr_video_analysis_frames
ffmpeg -hide_banner -loglevel error -y -i <video-path> -vf fps=1/2,scale=360:-1 /private/tmp/vibr_video_analysis_frames/frame_%03d.jpg
```

Validate JSON:

```bash
jq . <output-path> >/dev/null
```

## Final Response

Report:

- Input video path.
- Output JSON path.
- Whether JSON validation passed.
- Any meaningful uncertainty, such as unreadable text or obscured gestures.
