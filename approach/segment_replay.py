import os
import json
import pickle
import time
import cv2
import sys
import argparse
import logging
import re
from pathlib import Path
from typing import Any, List, Optional
from math import hypot

from logger import setup_logger
from config_loader import get_config
from run_stats import init_run_stats, get_run_stats, log_run_summary
from model_api import (
    ask_gpt_for_action_region,
    ask_gpt_state_consistency,
    ask_gpt_for_relevant_regions,
    ping_model_connections,
)
from adb_device_controller import ADBDeviceController
from execute_action import execute_actions
import yyh_utils  # Your video/frame utils (SSIM-based segmentation)
from input_formatter import parse_xml_string, label_screenshot, AndroidElement
from check_video import ensure_sdr_bt709

logger = logging.getLogger(__name__)

"""
Main script for segmenting a video of Android UI interaction and replaying those actions on a device.

Supports two boundary-detection algorithms:
  - ssim : pixel-level structural similarity (via yyh_utils) — default
  - clip : CLIP embedding cosine similarity (via clip_seg)

Video input: apps/<app_name>-<provider_model>/<quality>-video.mp4
Log output: apps/<app_name>-<provider_model>/<quality>-run.log (overwrites each run)

Usage:
    python segment_replay.py [app_name] [good|bad] [--config input/config.yml] [--algo ssim|clip]
    python segment_replay.py
    python segment_replay.py gmail good
    python segment_replay.py gmail bad --config input/config.yml
    python segment_replay.py gmail bad --config input/config.yml --algo clip
"""

SUPPORTED_ALGORITHMS = ("ssim", "clip")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_json(reply_text):
    """
    Extracts JSON object from GPT reply (removes any markdown formatting).
    Falls back to regex extraction if top-level parse fails.
    """
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
        raise ValueError(
            f"Could not extract valid JSON from LLM response: {reply_text!r}"
        )


ACTION_TYPES = {
    "tap",
    "double_tap",
    "long_press",
    "swipe",
    "input_text",
    "back",
    "home",
    "wait",
    "no action",
}


def normalize_indices(value: Any) -> list[int]:
    """Normalize an LLM region/index field into a list of integer indices."""
    if value is None:
        return []
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        try:
            return [int(value)]
        except ValueError:
            return []
    if isinstance(value, list):
        indices: list[int] = []
        for item in value:
            indices.extend(normalize_indices(item))
        return indices
    return []


def artifact_path(artifacts_dir: Path, step: int, source: str, name: str) -> Path:
    """Build a flat artifact path using e=emulator and v=video source tags."""
    if source not in {"e", "v"}:
        raise ValueError("Artifact source must be 'e' or 'v'.")
    return artifacts_dir / f"step_{step}{source}_{name}.png"


def provider_model_name(config: dict[str, Any]) -> str:
    """Return the model selected by model.provider in config."""
    model_config = config.get("model", {})
    provider = str(model_config.get("provider", "")).strip()
    model_key = f"{provider}_model"
    return str(model_config.get(model_key, "unknown")).strip() or "unknown"


def safe_app_run_dir_name(app_name: str, model: str) -> str:
    """Build apps/<app_name>-<model> without allowing path separators."""
    safe_app_name = re.sub(r"[^A-Za-z0-9._-]+", "_", app_name.strip())
    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "_", model.strip())
    return f"{safe_app_name}-{safe_model}"


def normalize_relevant_response(response: dict[str, Any]) -> dict[str, Any]:
    target_regions = normalize_indices(response.get("target_regions"))
    predicted_action = str(response.get("predicted_action", "no action")).strip().lower()
    if predicted_action not in ACTION_TYPES:
        logger.warning("Unknown predicted action %r; using no action.", predicted_action)
        predicted_action = "no action"
    return {
        **response,
        "target_regions": target_regions,
        "predicted_action": predicted_action,
    }


def normalize_action_response(action: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(action)
    action_type = str(normalized.get("action", "no action")).strip().lower()
    if action_type not in ACTION_TYPES:
        logger.warning("Unknown action %r; using no action.", action_type)
        action_type = "no action"
    normalized["action"] = action_type

    region_indices = normalize_indices(normalized.get("region"))
    if region_indices:
        normalized["region"] = region_indices[0]
        if len(region_indices) > 1:
            normalized["regions"] = region_indices
            logger.warning(
                "LLM returned multiple regions %s; using first region %s.",
                region_indices,
                region_indices[0],
            )
    elif "region" in normalized:
        normalized.pop("region", None)
    return normalized


def resolve_action_position(
    action: dict[str, Any],
    region_index_to_center: dict[int, tuple[int, int]],
    elements: List[AndroidElement],
    *,
    context: str,
) -> dict[str, Any]:
    if "region" in action and action["region"] in region_index_to_center:
        action["position"] = region_index_to_center[action["region"]]
        logger.info(
            "%s using region index: %s at %s",
            context,
            action["region"],
            action["position"],
        )
        return action

    matched_element = match_action_to_element(action, elements)
    if matched_element:
        action["position"] = matched_element.center
        logger.info(
            "%s matched element: %r at %s",
            context,
            matched_element.text,
            matched_element.center,
        )
    return action


def action_is_executable(action: dict[str, Any]) -> bool:
    action_type = action.get("action")
    if action_type in {"tap", "double_tap", "long_press"}:
        return "position" in action
    if action_type == "swipe":
        return "from" in action and "to" in action
    if action_type == "input_text":
        return "text" in action
    return action_type in {"back", "home", "wait", "no action"}


def parse_live_elements(
    device: ADBDeviceController, replay_config: dict[str, Any]
) -> List[AndroidElement]:
    xml_str = device.get_ui_xml()
    elements = parse_xml_string(
        xml_str,
        bound_margin=replay_config.get("xml_parse_bound_margin", 10),
        min_cent_dist=replay_config.get("xml_parse_min_center_distance", 20),
        clickable_only=True,
    )
    if len(elements) <= replay_config.get("min_elements_threshold", 5):
        elements = parse_xml_string(
            xml_str,
            bound_margin=replay_config.get("xml_parse_bound_margin", 10),
            min_cent_dist=replay_config.get("xml_parse_min_center_distance", 20),
        )
    return elements


def show_images(start_img, stop_img, current_img):
    """
    Displays three images side by side for human inspection (waits for keypress).
    """

    def resize(img, max_height=600):
        h, w = img.shape[:2]
        if h > max_height:
            scale = max_height / h
            return cv2.resize(img, (int(w * scale), max_height))
        return img

    cv2.imshow("Start Frame", resize(start_img))
    cv2.imshow("Stop Frame", resize(stop_img))
    cv2.imshow("Current Frame", resize(current_img))
    logger.info("Press ENTER to continue to the next action, or ESC to exit.")
    key = cv2.waitKey(0)
    cv2.destroyAllWindows()
    if key == 27:
        logger.info("Exiting.")
        sys.exit(0)


def match_action_to_element(
    action: dict, elements: List[AndroidElement]
) -> Optional[AndroidElement]:
    """
    Attempts to map an action to the best matching AndroidElement.
    Tries by text, then by proximity to a position if given.
    """
    if "text" in action:
        target_text = action["text"].strip().lower()
        for e in elements:
            if e.text and e.text.strip().lower() == target_text:
                return e
        for e in elements:
            if e.text and target_text in e.text.strip().lower():
                return e

    if "position" in action:
        px, py = action["position"]
        closest_element = min(
            elements,
            key=lambda e: hypot(px - e.center[0], py - e.center[1]),
            default=None,
        )
        return closest_element

    return None


# ---------------------------------------------------------------------------
# Segmentation helpers
# ---------------------------------------------------------------------------


def segment_with_ssim(
    frames,
    y_frames,
    video_stem,
    cache_folder="./cache",
    stable_sim_threshold=0.95,
    stable_interval_threshold=3,
):
    """Run SSIM-based stable-segment detection (original yyh_utils path)."""
    os.makedirs(cache_folder, exist_ok=True)
    sim_file = os.path.join(cache_folder, f"sim_list_ssim_{video_stem}.pkl")

    if os.path.exists(sim_file):
        with open(sim_file, "rb") as f:
            sim_list = pickle.load(f)
        logger.info("SSIM similarity list loaded from cache.")
    else:
        sim_list = yyh_utils.calculate_sim_seq(y_frames)
        with open(sim_file, "wb") as f:
            pickle.dump(sim_list, f)
        logger.info("SSIM similarity list calculated and saved.")

    segmenter = yyh_utils.VideoStableSegment(
        stable_sim_threshold=stable_sim_threshold,
        stable_interval_threshold=stable_interval_threshold,
    )
    stable_segments = segmenter.detect_keyframes(sim_list)
    return stable_segments


def segment_with_clip(
    frames,
    video_stem,
    cache_folder="./cache",
    stable_sim_threshold=0.95,
    stable_interval_threshold=3,
    model_name="openai/clip-vit-base-patch32",
):
    """Run CLIP-based stable-segment detection."""
    from clip_seg import VideoStableSegmentCLIP

    os.makedirs(cache_folder, exist_ok=True)
    sim_file = os.path.join(cache_folder, f"sim_list_clip_{video_stem}.pkl")

    clip_segmenter = VideoStableSegmentCLIP(
        stable_sim_threshold=stable_sim_threshold,
        stable_interval_threshold=stable_interval_threshold,
        model_name=model_name,
    )

    if os.path.exists(sim_file):
        with open(sim_file, "rb") as f:
            sim_list = pickle.load(f)
        logger.info("CLIP similarity list loaded from cache.")
    else:
        # Convert BGR numpy frames → PIL for CLIP
        from PIL import Image

        pil_frames = [
            Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames
        ]
        sim_list = clip_segmenter.calculate_clip_sim_seq(pil_frames)
        with open(sim_file, "wb") as f:
            pickle.dump(sim_list, f)
        logger.info("CLIP similarity list calculated and saved.")

    stable_segments = clip_segmenter.detect_keyframes(sim_list)
    return stable_segments


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _apply_model_config(config: dict) -> None:
    """Expose model config to provider modules through their existing env API."""
    model_config = config.get("model", {})
    provider = model_config.get("provider")
    if provider:
        os.environ["MODEL_PROVIDER"] = str(provider)
    if model_config.get("openai_model"):
        os.environ["OPENAI_MODEL"] = str(model_config["openai_model"])
    if model_config.get("gemini_model"):
        os.environ["GEMINI_MODEL"] = str(model_config["gemini_model"])


def _apply_runtime_config(config: dict) -> None:
    """Apply process-level runtime settings before heavy imports."""
    runtime_config = config.get("runtime", {})
    matplotlib_config_dir = runtime_config.get("matplotlib_config_dir")
    if matplotlib_config_dir:
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config_dir))
        Path(matplotlib_config_dir).mkdir(parents=True, exist_ok=True)

    xdg_cache_home = runtime_config.get("xdg_cache_home")
    if xdg_cache_home:
        os.environ.setdefault("XDG_CACHE_HOME", str(xdg_cache_home))
        Path(xdg_cache_home).mkdir(parents=True, exist_ok=True)


def main(
    app_name: str | None = None,
    quality: str | None = None,
    algorithm: str | None = None,
    config_path: Path | None = None,
):
    """
    Main entry point: processes video and replays UI actions segment by segment.
    """
    # Load config and initialize stats
    config = get_config(config_path)
    _apply_runtime_config(config)
    _apply_model_config(config)
    from model_api import _load_dotenv
    _load_dotenv()

    from dino_detection import run_grounding_dino, annotate_relevant_regions

    run_config = config.get("run", {})
    app_name = app_name or run_config.get("app_name")
    quality = quality or run_config.get("quality")
    if not app_name:
        raise ValueError("Missing app_name. Pass it on the CLI or set run.app_name in config.")
    if quality not in {"good", "bad"}:
        raise ValueError("Missing/invalid quality. Pass good|bad on the CLI or set run.quality in config.")

    path_config = config.get("paths", {})
    apps_root = Path(path_config.get("apps_root", "apps"))
    provider = config["model"]["provider"]
    model = provider_model_name(config)
    app_dir_name = safe_app_run_dir_name(app_name, model)
    app_dir = apps_root / app_dir_name
    app_dir.mkdir(parents=True, exist_ok=True)

    algorithm = (algorithm or config.get("segmentation", {}).get("algorithm", "clip")).lower()

    # Initialize logger with config dump
    setup_logger(app_dir, quality, config)

    # Initialize run stats tracker
    init_run_stats(
        app_name=app_name,
        video_quality=quality,
        provider=provider,
        model=model,
        algorithm=algorithm,
        config=config,
    )
    stats = get_run_stats()

    ping_model_connections()

    if algorithm not in SUPPORTED_ALGORITHMS:
        logger.error(
            f"Unknown algorithm '{algorithm}'. Choose from: {SUPPORTED_ALGORITHMS}"
        )
        stats.status = "failed"
        log_run_summary(app_dir)
        sys.exit(1)

    # Resolve paths
    video_template = path_config.get("video_filename_template", "{quality}-video.mp4")
    video_path = app_dir / video_template.format(quality=quality)

    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        stats.status = "failed"
        log_run_summary(app_dir)
        sys.exit(1)

    # Check and convert video format if needed
    try:
        ensure_sdr_bt709(video_path)
    except RuntimeError as e:
        logger.error(f"Video format check/conversion failed: {e}")
        stats.status = "failed"
        log_run_summary(app_dir)
        sys.exit(1)

    logger.info(
        f"Starting video processing from {video_path} (algorithm={algorithm})..."
    )
    stats.add_step("Initialized configuration and device controller")
    logger.info("Initializing ADB device controller...")
    device = ADBDeviceController()

    video_stem = video_path.stem
    replay_config = config.get("replay", {})
    segmentation_config = config.get("segmentation", {})
    # Output dir: apps/<app_name>-<provider_model>/<quality>-artifacts/
    artifacts_dir = app_dir / f"{quality}-artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    frames, y_frames = yyh_utils.read_frames_from_video(
        video_path, header_pixel_size=replay_config.get("header_crop_px", 33)
    )

    # ---- Segment detection (switchable) ----
    logger.info("Detecting stable segments...")
    if algorithm == "ssim":
        ssim_config = segmentation_config.get("ssim", {})
        stable_segments = segment_with_ssim(
            frames,
            y_frames,
            video_stem,
            cache_folder=segmentation_config.get("cache_dir", "./cache"),
            stable_sim_threshold=ssim_config.get("stable_sim_threshold", 0.95),
            stable_interval_threshold=ssim_config.get("stable_interval_threshold", 3),
        )
    else:
        clip_config = segmentation_config.get("clip", {})
        stable_segments = segment_with_clip(
            frames,
            video_stem,
            cache_folder=segmentation_config.get("cache_dir", "./cache"),
            stable_sim_threshold=clip_config.get("stable_sim_threshold", 0.95),
            stable_interval_threshold=clip_config.get("stable_interval_threshold", 3),
            model_name=clip_config.get("model", "openai/clip-vit-base-patch32"),
        )

    if stable_segments[0][0] > segmentation_config.get("leading_segment_min_frame", 2):
        stable_segments = [(0, 1)] + stable_segments

    frame_count = len(frames)
    logger.info(f"Total frames: {frame_count}, total segments: {len(stable_segments)}")
    logger.info(f"Segment boundaries: {stable_segments}")

    # ---- Per-segment replay loop (unchanged) ----
    stats.scenes = len(stable_segments) - 1
    for i in range(len(stable_segments) - 1):
        time.sleep(replay_config.get("inter_segment_sleep", 0.5))
        logger.info(f"Processing segment {i}...")
        stats.add_step(f"Processing segment {i}")

        start = stable_segments[i][1]
        stop = stable_segments[i + 1][0]

        if start >= frame_count or stop >= frame_count:
            logger.error(f"Segment {i}: invalid indices start={start} stop={stop} (frame_count={frame_count}). Skipping.")
            continue

        start_img = frames[start]
        stop_img = frames[stop]
        live_path = device.screenshot(
            index=0,
            save_path=str(artifacts_dir),
            filename=artifact_path(artifacts_dir, i, "e", "screenshot_0").name,
        )

        tmp_start_path = artifact_path(artifacts_dir, i, "v", "tmp_start")
        tmp_stop_path = artifact_path(artifacts_dir, i, "v", "tmp_stop")
        cv2.imwrite(str(tmp_start_path), start_img)
        cv2.imwrite(str(tmp_stop_path), stop_img)

        screenshot_attempt_index = 0

        # XML UI parse and clickable element detection
        elements = parse_live_elements(device, replay_config)

        labeled_path = label_screenshot(
            screenshot_path=live_path,
            screenshot_dir=str(artifacts_dir),
            name=f"step_{i}e_labeled",
            elements=elements,
        )

        # DINO detection for grounding region proposals
        dino_out_path = artifact_path(artifacts_dir, i, "v", "dino")
        dino_regions = run_grounding_dino(str(tmp_start_path), str(dino_out_path))

        relevant = ask_gpt_for_relevant_regions(str(dino_out_path), str(tmp_stop_path))
        relevant = normalize_relevant_response(extract_json(relevant))
        logger.info(f"Relevant regions: {relevant}")
        target_indices = relevant["target_regions"]
        logger.info(f"GPT selected regions: {target_indices}")

        relevant_annotated_path = artifact_path(
            artifacts_dir, i, "v", "relevant_regions"
        )
        annotate_relevant_regions(
            str(tmp_start_path),
            str(relevant_annotated_path),
            dino_regions,
            target_indices,
        )

        dino_region_index_to_center = {r["index"]: r["center"] for r in dino_regions}

        logger.info(
            f"Comparing state: reference={relevant_annotated_path.name} vs live={Path(live_path).name}"
        )
        match = extract_json(
            ask_gpt_state_consistency(
                str(relevant_annotated_path),
                live_path,
                relevant["predicted_action"],
                relevant["target_regions"],
            )
        )

        attempts = 0
        max_attempts = replay_config.get("max_state_alignment_retries", 3)
        while match["same_state"] != "yes" and attempts < max_attempts:
            logger.warning(
                f"Attempting to align state (try {attempts + 1}/{max_attempts})..."
            )
            elements = parse_live_elements(device, replay_config)
            live_region_index_to_center = {
                idx: element.center for idx, element in enumerate(elements)
            }

            labeled_path = label_screenshot(
                screenshot_path=live_path,
                screenshot_dir=str(artifacts_dir),
                name=f"step_{i}e_labeled",
                elements=elements,
            )

            recovery_reply = ask_gpt_for_action_region(
                str(tmp_start_path),
                str(tmp_stop_path),
                str(labeled_path),
                relevant["predicted_action"],
            )
            recovery_action = normalize_action_response(extract_json(recovery_reply))
            recovery_action = resolve_action_position(
                recovery_action,
                live_region_index_to_center,
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
            logger.info(
                f"Comparing state (recovery attempt {attempts + 1}): reference={tmp_stop_path.name} vs live={Path(live_path).name}"
            )
            match = extract_json(
                ask_gpt_state_consistency(str(tmp_stop_path), live_path)
            )
            attempts += 1

        if match["same_state"] == "yes":
            elements = parse_live_elements(device, replay_config)
            labeled_path = label_screenshot(
                screenshot_path=live_path,
                screenshot_dir=str(artifacts_dir),
                name=f"step_{i}e_labeled",
                elements=elements,
            )

            reply = ask_gpt_for_action_region(
                str(relevant_annotated_path),
                str(tmp_stop_path),
                str(labeled_path),
                relevant["predicted_action"],
                target_indices,
            )
            action = normalize_action_response(extract_json(reply))
            action = resolve_action_position(
                action,
                dino_region_index_to_center,
                elements,
                context="Replay",
            )

            if not action_is_executable(action):
                logger.warning(
                    "Skipping invalid action with no executable target: %s",
                    action,
                )
                continue

            execute_actions(device, [action])
            logger.info("Action executed.")
            stats.actions_executed += 1
        else:
            logger.warning(
                f"Skipping action: current GUI state does not match start state. "
                f"Mismatch reason: {match['description']}"
            )

    logger.info("Video processing completed.")
    stats.status = "successful" if stats.actions_executed > 0 else "incomplete"
    log_run_summary(app_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Segment and replay actions from video."
    )
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
        help="Boundary detection algorithm override: ssim or clip (default: config value)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "input" / "config.yml",
        help="Path to YAML config file (default: approach/input/config.yml)",
    )
    args = parser.parse_args()
    main(args.app_name, args.quality, args.algo, args.config)
