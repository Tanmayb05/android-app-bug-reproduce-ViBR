# ViBR-main → approach: Implementation Changes

## Overview

Migration from **OpenAI-only + hardcoded API keys** to **multi-provider LLM abstraction + config-driven setup**. Adds observability (logging, stats tracking), structured data validation, safer error handling, and batch app support.

---

## 1. Dependency Injection & Provider Abstraction

### ViBR-main (OpenAI-only)

```python
# openai_api.py
from openai import OpenAI
client = OpenAI(api_key="put-your-api-key-here")  # ❌ Hardcoded secret

def ask_gpt_state_consistency(...):
    response = client.chat.completions.create(model="gpt-4o", ...)
```

- Hardcoded OpenAI client
- Secret exposed in code
- No abstraction for alternative providers

### approach (Multi-provider)

```python
# model_api.py — provider facade
def active_provider() -> str:
    if os.environ.get("MODEL_PROVIDER") == "openai":
        return "openai"
    return "gemini"

def _ask_provider(prompt, images, details=None) -> str:
    provider = active_provider()
    if provider == "openai":
        return openai_provider.ask(prompt, images, details)
    return gemini_provider.ask(prompt, images)

# providers/openai_provider.py
def client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

def ask(prompt: str, image_paths, details=None) -> str:
    # Delegate to OpenAI

# providers/gemini_provider.py
def client(api_key: str):
    return genai.GenerativeModel(model)

def ask(prompt: str, image_paths) -> str:
    # Delegate to Gemini
```

**Changes:**
- ✅ Provider auto-detection: OpenAI → Gemini fallback
- ✅ Secrets loaded from `.env.local` (never in code)
- ✅ Pluggable: `MODEL_PROVIDER=openai|gemini` env var
- ✅ Structured provider modules: `providers/openai_provider.py`, `providers/gemini_provider.py`
- ✅ Unified interface: both providers implement `ask(prompt, image_paths)`

---

## 2. Configuration & Path Management

### ViBR-main

```python
# Hard-coded paths
video_out_dir = os.path.join("temp", video_stem)
live_path = device.screenshot(index=0, save_path=video_out_dir)
```

- No config file
- Paths scattered in code
- Single app support

### approach

```python
# input/config.yml (or custom --config path)
model:
  provider: "openai|gemini"
  openai_model: "gpt-4o"
  gemini_model: "gemini-2.0-flash"

paths:
  apps_root: "apps"
  video_filename_template: "{quality}-video.mp4"

run:
  app_name: "gmail"
  quality: "good|bad"

replay:
  header_crop_px: 33
  inter_segment_sleep: 0.5
  max_state_alignment_retries: 3

segmentation:
  algorithm: "clip"
  cache_dir: "./cache"
  ssim:
    stable_sim_threshold: 0.95
    stable_interval_threshold: 3
  clip:
    model: "openai/clip-vit-base-patch32"

runtime:
  matplotlib_config_dir: "..."
  xdg_cache_home: "..."
```

**Changes:**
- ✅ Config loader: `config_loader.py` (YAML-based)
- ✅ Batch apps: `apps/<app_name>-<provider_model>/<quality>-video.mp4`
- ✅ Video I/O templates: standardized naming
- ✅ Configurable thresholds: segmentation, replay, runtime

---

## 3. Structured Data & Validation

### ViBR-main

```python
# Loose dicts
if "text" in action:
    # action is untyped dict
action["position"] = matched_element.center  # May not exist
```

### approach

```python
def normalize_indices(value: Any) -> list[int]:
    """Coerce various index formats to list[int]."""
    if isinstance(value, int):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int)]
    return []

def normalize_relevant_response(response: dict[str, Any]) -> dict[str, Any]:
    """Validate & normalize LLM response."""
    target_regions = normalize_indices(response.get("target_regions"))
    predicted_action = str(response.get("predicted_action", "no action")).strip().lower()
    if predicted_action not in ACTION_TYPES:
        logger.warning("Unknown action %r; using no action.", predicted_action)
        predicted_action = "no action"
    return {
        **response,
        "target_regions": target_regions,
        "predicted_action": predicted_action,
    }

def normalize_action_response(action: dict[str, Any]) -> dict[str, Any]:
    """Validate action type & handle multi-region responses."""
    action_type = str(action.get("action", "no action")).strip().lower()
    if action_type not in ACTION_TYPES:
        logger.warning("Unknown action %r; using no action.", action_type)
        action_type = "no action"
    return {..., "action": action_type}

def action_is_executable(action: dict[str, Any]) -> bool:
    """Validate action has required fields before execution."""
    action_type = action.get("action")
    if action_type in {"tap", "double_tap", "long_press"}:
        return "position" in action
    return action_type in {"back", "home", "wait", "no action"}
```

**Changes:**
- ✅ Type coercion: handle LLM JSON variances (int vs list, string vs int)
- ✅ Action validation: ensure required fields before execution
- ✅ Logging: warn on invalid responses instead of crashing
- ✅ Safe defaults: "no action" for unknown types

---

## 4. Artifact Organization & Naming

### ViBR-main

```python
step_out_dir = os.path.join(video_out_dir, f"step_{i}")
tmp_start_path = os.path.join(step_out_dir, "tmp_start.png")
labeled_path = label_screenshot(screenshot_path, screenshot_dir, name="labeled", ...)
```

- Nested per-step directories
- No source tagging (emulator vs video)
- Naming collision risk

### approach

```python
def artifact_path(artifacts_dir: Path, step: int, source: str, name: str) -> Path:
    """Build flat artifact path with source tags: e=emulator, v=video."""
    return artifacts_dir / f"step_{step}{source}_{name}.png"
    # e.g. step_0e_screenshot_0.png, step_0v_tmp_start.png

artifacts_dir = app_dir / f"{quality}-artifacts"
tmp_start = artifact_path(artifacts_dir, i, "v", "tmp_start")
tmp_stop = artifact_path(artifacts_dir, i, "v", "tmp_stop")
live_path = device.screenshot(
    index=0,
    save_path=str(artifacts_dir),
    filename=artifact_path(artifacts_dir, i, "e", "screenshot_0").name,
)
```

**Changes:**
- ✅ Flat directory structure (easier to browse, grep, archive)
- ✅ Source tags: `e` = emulator, `v` = video
- ✅ Standardized naming: `step_{i}{source}_{name}.png`
- ✅ No nested step dirs, no naming collisions

---

## 5. Logging & Observability

### ViBR-main

```python
# print() everywhere
print("❌ JSON decoding failed:", e)
print(f"🔍 Relevant regions: {relevant}")
print("▶ Press ENTER to continue...")
```

- No structured logging
- No debug context
- No log files

### approach

```python
# logger.py — centralized setup
import logging
from pathlib import Path

def setup_logger(app_dir: Path, quality: str, config: dict):
    """Initialize structured logger with file + console handlers."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    log_file = app_dir / f"{quality}-run.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
    ))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# In segment_replay.py
logger = logging.getLogger(__name__)

logger.info(f"Starting video processing from {video_path} (algorithm={algorithm})...")
logger.error(f"Video not found: {video_path}")
logger.warning(f"Attempting to align state (try {attempts + 1}/{max_attempts})...")
logger.debug(f"Consistency Response from {active_provider()}: {reply}")
```

**Changes:**
- ✅ Structured logger with DEBUG/INFO/WARNING/ERROR levels
- ✅ File logging: `apps/<app>-<model>/<quality>-run.log`
- ✅ Console + file dual output
- ✅ Module-aware logging (logger names from `__name__`)

---

## 6. Run Statistics & Telemetry

### ViBR-main

None. No tracking of LLM usage, execution counts, etc.

### approach

```python
# run_stats.py
from dataclasses import dataclass, field

@dataclass
class RunStats:
    app_name: str
    video_quality: str
    provider: str
    model: str
    algorithm: str
    status: str = "pending"
    scenes: int = 0
    actions_executed: int = 0
    llm_calls: int = 0
    llm_total_cost: float = 0.0
    
    steps: list[str] = field(default_factory=list)
    llm_responses: list[dict] = field(default_factory=list)

def init_run_stats(...):
    """Initialize global stats tracker."""
    ...

def log_run_summary(app_dir: Path):
    """Write summary JSON to apps/<app>-<model>/<quality>-run.json"""
    stats = get_run_stats()
    summary = {
        "app_name": stats.app_name,
        "status": stats.status,
        "scenes": stats.scenes,
        "actions_executed": stats.actions_executed,
        "llm_calls": stats.llm_calls,
        "llm_total_cost": stats.llm_total_cost,
        "steps": stats.steps,
    }
    (app_dir / f"{stats.video_quality}-run.json").write_text(json.dumps(summary, indent=2))

# In segment_replay.py
stats = get_run_stats()
stats.scenes = len(stable_segments) - 1
stats.add_step(f"Processing segment {i}")
stats.actions_executed += 1
log_run_summary(app_dir)
```

**Changes:**
- ✅ Stats tracking: scenes, actions, LLM calls, cost, status
- ✅ Per-step logging: add_step() records workflow
- ✅ Summary JSON: `<quality>-run.json` for post-run analysis
- ✅ Cost tracking: integrated into response recording

---

## 7. Prompt Management

### ViBR-main

```python
# Prompts embedded in openai_api.py
prompt = (
    "You are given two screenshots of an Android interface:\n"
    "..."
)
```

- Prompts hardcoded in function bodies
- Hard to version, test, or reuse

### approach

```python
# prompts/state_consistency.py
def build(action: str = "", target_region: Any = "") -> str:
    """Build state consistency prompt."""
    return f"""You are given two screenshots of an Android interface:
1. The first image is the REFERENCE state from a stable app video.
2. The second image is the CURRENT real-time app state.

Action: {action}
Target Region: {target_region}

Your task is to determine if the current screen is functionally consistent with the reference...
Respond strictly in the following JSON format:
{{ "same_state": "yes" }} or {{ "same_state": "no", "description": "..." }}
"""

# prompts/action_region.py, prompts/relevant_regions.py — similar

# model_api.py
from prompts import state_consistency, action_region, relevant_regions

prompt = state_consistency.build(action, target_region)
reply = _ask_provider(prompt, [start_img, live_img])
```

**Changes:**
- ✅ Prompts in separate files: `prompts/state_consistency.py`, etc.
- ✅ Parameterized: `build()` functions for reusability
- ✅ Easier to version and test
- ✅ Separates prompt logic from API calls

---

## 8. Video Format Validation

### ViBR-main

```python
# No validation; assumes video is ready
frames, y_frames = yyh_utils.read_frames_from_video(video_path, header_pixel_size=33)
```

### approach

```python
# check_video.py
def ensure_sdr_bt709(video_path: Path) -> None:
    """Validate/convert video to SDR BT.709 color space if needed.
    
    Tools like DINO + CLIP expect standard color space.
    """
    # ffprobe: check color_space, color_transfer, color_primaries
    # ffmpeg: convert if needed
    ...

# segment_replay.py
try:
    ensure_sdr_bt709(video_path)
except RuntimeError as e:
    logger.error(f"Video format check/conversion failed: {e}")
    stats.status = "failed"
    log_run_summary(app_dir)
    sys.exit(1)
```

**Changes:**
- ✅ Validates video color space (SDR BT.709) before processing
- ✅ Auto-converts if needed (prevents DINO/CLIP artifacts)
- ✅ Graceful error handling with cleanup (log summary before exit)

---

## 9. Safer JSON Extraction

### ViBR-main

```python
try:
    return json.loads(reply_text.strip())
except json.JSONDecodeError as e:
    print("❌ JSON decoding failed:", e)
    raise
```

- No fallback
- Crashes on malformed JSON

### approach

```python
def extract_json(reply_text):
    if not reply_text or not reply_text.strip():
        raise ValueError("LLM returned empty response")
    
    reply_text = reply_text.strip()
    if reply_text.startswith("```json"):
        reply_text = reply_text[7:]
    elif reply_text.startswith("```"):
        reply_text = reply_text[3:]
    if reply_text.endswith("```"):
        reply_text = reply_text[:-3]
    
    try:
        return json.loads(reply_text.strip())
    except json.JSONDecodeError:
        # Fallback: extract first {...} block if top-level parse fails
        m = re.search(r'\{.*\}', reply_text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        logger.error(f"JSON decoding failed; raw response: {reply_text!r}")
        raise ValueError(f"Could not extract valid JSON from LLM response: {reply_text!r}")
```

**Changes:**
- ✅ Regex fallback: extract `{...}` block if top-level parse fails
- ✅ Handles markdown-wrapped responses: ` ```json ... ``` `
- ✅ Better error messages: raw response in log
- ✅ Empty response check upfront

---

## 10. Action Resolution & Validation

### ViBR-main

```python
if "region" in action and action["region"] in region_index_to_center:
    action["position"] = region_index_to_center[action["region"]]
    print(f"🎯 Using region index: {action['region']} at {action['position']}")
elif matched_element:
    action["position"] = matched_element.center
    print(f"🎯 Matched element: '{matched_element.text}' at {matched_element.center}")
else:
    print("⚠️ No valid region or element match. Using original position if available.")

execute_actions(device, [action])
```

- No validation before execution
- May execute with missing fields
- No structured logging

### approach

```python
def resolve_action_position(
    action: dict[str, Any],
    region_index_to_center: dict[int, tuple[int, int]],
    elements: List[AndroidElement],
    *,
    context: str,
) -> dict[str, Any]:
    """Resolve action position from region index or matched element."""
    if "region" in action and action["region"] in region_index_to_center:
        action["position"] = region_index_to_center[action["region"]]
        logger.info("%s using region index: %s at %s", context, action["region"], action["position"])
        return action
    
    matched_element = match_action_to_element(action, elements)
    if matched_element:
        action["position"] = matched_element.center
        logger.info("%s matched element: %r at %s", context, matched_element.text, matched_element.center)
    return action

def action_is_executable(action: dict[str, Any]) -> bool:
    """Validate action has required fields before execution."""
    action_type = action.get("action")
    if action_type in {"tap", "double_tap", "long_press"}:
        return "position" in action
    if action_type == "swipe":
        return "from" in action and "to" in action
    if action_type == "input_text":
        return "text" in action
    return action_type in {"back", "home", "wait", "no action"}

# segment_replay.py
action = normalize_action_response(extract_json(reply))
action = resolve_action_position(action, region_index_to_center, elements, context="Replay")

if not action_is_executable(action):
    logger.warning("Skipping invalid action with no executable target: %s", action)
    continue

execute_actions(device, [action])
```

**Changes:**
- ✅ Validator: `action_is_executable()` checks required fields
- ✅ Resolver: `resolve_action_position()` with context logging
- ✅ Skip invalid actions: logged warning + continue (no crash)
- ✅ Action normalization: coerce unknown types to "no action"

---

## 11. State Alignment & Recovery Loop

### ViBR-main

```python
while match["same_state"] != "yes" and attempts < max_attempts:
    print(f"🔄 Attempting to align state (try {attempts + 1}/{max_attempts})...")
    # Retry logic is implicit; success/failure not validated until max_attempts
```

- Retries blindly
- No state validation between attempts
- Uses same region index map

### approach

```python
attempts = 0
max_attempts = replay_config.get("max_state_alignment_retries", 3)
while match["same_state"] != "yes" and attempts < max_attempts:
    logger.warning(f"Attempting to align state (try {attempts + 1}/{max_attempts})...")
    
    elements = parse_live_elements(device, replay_config)
    live_region_index_to_center = {
        idx: element.center for idx, element in enumerate(elements)
    }
    
    recovery_reply = ask_gpt_for_action_region(...)
    recovery_action = normalize_action_response(extract_json(recovery_reply))
    recovery_action = resolve_action_position(
        recovery_action,
        live_region_index_to_center,  # ✅ Fresh mapping per attempt
        elements,
        context="Recovery",
    )
    
    if not action_is_executable(recovery_action):
        logger.warning("Skipping invalid recovery action: %s", recovery_action)
        break
    
    execute_actions(device, [recovery_action])
    time.sleep(replay_config.get("post_recovery_sleep", 1.0))
    screenshot_attempt_index += 1
    live_path = device.screenshot(
        index=0,
        save_path=str(artifacts_dir),
        filename=artifact_path(artifacts_dir, i, "e", f"screenshot_{screenshot_attempt_index}").name,
    )
    logger.info(f"Comparing state (recovery attempt {attempts + 1}): ...")
    match = extract_json(ask_gpt_state_consistency(str(tmp_stop_path), live_path))
    attempts += 1
```

**Changes:**
- ✅ Fresh element parsing per attempt (layout changes)
- ✅ Fresh region mapping per attempt (coordinates shift)
- ✅ Validation before execution: `action_is_executable()`
- ✅ Numbered screenshots: `screenshot_0`, `screenshot_1`, etc.
- ✅ Configurable sleep: `post_recovery_sleep`
- ✅ Break on invalid action (don't waste retries)

---

## 12. Argument Parsing & CLI Interface

### ViBR-main

```python
parser = argparse.ArgumentParser(description="...")
parser.add_argument("video_path", type=str, help="Path to the input video")
parser.add_argument("algorithm", type=str, default="clip", choices=SUPPORTED_ALGORITHMS, ...)
args = parser.parse_args()
main(args.video_path, args.algorithm)
```

- Positional: `python segment_replay.py demo.mp4 clip`
- No config support

### approach

```python
parser = argparse.ArgumentParser(description="...")
parser.add_argument(
    "app_name",
    type=str,
    nargs="?",
    help="Application name override (default: run.app_name from config)",
)
parser.add_argument(
    "quality",
    type=str,
    nargs="?",
    choices=["good", "bad"],
    help="Video quality override: good or bad (default: run.quality from config)",
)
parser.add_argument(
    "--algo",
    type=str,
    default=None,
    choices=SUPPORTED_ALGORITHMS,
    help="Boundary detection algorithm override (default: config value)",
)
parser.add_argument(
    "--config",
    type=Path,
    default=Path(__file__).parent / "input" / "config.yml",
    help="Path to YAML config file (default: approach/input/config.yml)",
)
args = parser.parse_args()
main(args.app_name, args.quality, args.algo, args.config)
```

**Usage:**
```bash
python segment_replay.py                                      # Use all from config
python segment_replay.py gmail good                          # Override app_name, quality
python segment_replay.py gmail bad --config custom.yml       # Override config file
python segment_replay.py gmail bad --algo ssim               # Override algorithm
```

**Changes:**
- ✅ Optional positional args: `app_name`, `quality`
- ✅ Config-first: defaults to `input/config.yml`
- ✅ CLI overrides config for convenience
- ✅ Better help text

---

## 13. Error Handling & Graceful Shutdown

### ViBR-main

```python
if algorithm not in SUPPORTED_ALGORITHMS:
    print(f"❌ Unknown algorithm '{algorithm}'...")
    sys.exit(1)

# No cleanup on exit
```

### approach

```python
if algorithm not in SUPPORTED_ALGORITHMS:
    logger.error(f"Unknown algorithm '{algorithm}'...")
    stats.status = "failed"
    log_run_summary(app_dir)  # ✅ Write stats before exit
    sys.exit(1)

if not video_path.exists():
    logger.error(f"Video not found: {video_path}")
    stats.status = "failed"
    log_run_summary(app_dir)
    sys.exit(1)

try:
    ensure_sdr_bt709(video_path)
except RuntimeError as e:
    logger.error(f"Video format check/conversion failed: {e}")
    stats.status = "failed"
    log_run_summary(app_dir)
    sys.exit(1)

# At end
logger.info("Video processing completed.")
stats.status = "successful" if stats.actions_executed > 0 else "incomplete"
log_run_summary(app_dir)
```

**Changes:**
- ✅ All exits write stats summary (for post-run analysis)
- ✅ Status tracking: pending → successful | incomplete | failed
- ✅ Explicit error logging before shutdown
- ✅ No silent failures

---

## Summary Table

| Feature | ViBR-main | approach |
|---------|-----------|----------|
| **LLM Provider** | OpenAI only (hardcoded) | OpenAI + Gemini (env/config) |
| **API Key** | Embedded in code ❌ | `.env.local` ✅ |
| **Configuration** | None | YAML (`input/config.yml`) |
| **App Support** | Single | Batch (`apps/<app>-<model>`) |
| **Video I/O** | Hard-coded | Template-based |
| **Logging** | print() only | Structured logger + file |
| **Stats Tracking** | None | `RunStats` + JSON summary |
| **Prompts** | Embedded | Separate modules |
| **Video Validation** | None | `check_video.py` (SDR BT.709) |
| **JSON Extraction** | Crash on error | Regex fallback |
| **Action Validation** | None | `action_is_executable()` |
| **Region Resolution** | Static mapping | Fresh per attempt |
| **CLI Interface** | video_path + algorithm | app_name + quality + config |
| **Error Handling** | Basic | Graceful + summary logging |

---

## Migration Checklist

- [x] Extract provider logic → `providers/` folder
- [x] Separate prompts → `prompts/` folder
- [x] Config file → `input/config.yml`
- [x] Logger setup → `logger.py`
- [x] Stats tracking → `run_stats.py`
- [x] Video validation → `check_video.py`
- [x] Batch app support → `apps/<app>-<model>/<quality>-*`
- [x] Config-first CLI → app_name + quality + --config
- [x] Action validation & normalization
- [x] Structured error handling & logging
- [x] Remove hardcoded secrets
- [x] Add type hints throughout
