import os
import json
import pickle
import time
import cv2
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional
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

Video input: apps/<app_name>/<quality>-quality.mp4
Log output: apps/<app_name>/run_<quality>.log (overwrites each run)

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
    """
    reply_text = reply_text.strip()
    if reply_text.startswith("```json"):
        reply_text = reply_text[7:]
    elif reply_text.startswith("```"):
        reply_text = reply_text[3:]
    if reply_text.endswith("```"):
        reply_text = reply_text[:-3]

    try:
        return json.loads(reply_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise


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
    app_dir = apps_root / app_name
    app_dir.mkdir(parents=True, exist_ok=True)

    algorithm = (algorithm or config.get("segmentation", {}).get("algorithm", "clip")).lower()

    # Initialize logger with config dump
    setup_logger(app_name, quality, apps_root, config)

    # Initialize run stats tracker
    provider = config["model"]["provider"]
    model_key = f"{provider}_model"
    model = config["model"].get(model_key, "unknown")
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
    video_template = path_config.get("video_filename_template", "{quality}-quality.mp4")
    video_path = apps_root / app_name / video_template.format(quality=quality)

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
    temp_dir = Path(path_config.get("temp_root", "temp")) / video_stem
    temp_dir.mkdir(parents=True, exist_ok=True)

    live_path = device.screenshot(index=0, save_path=str(temp_dir))

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

    # ---- Per-segment replay loop (unchanged) ----
    stats.scenes = len(stable_segments) - 1
    for i in range(len(stable_segments) - 1):
        time.sleep(replay_config.get("inter_segment_sleep", 0.5))
        logger.info(f"Processing segment {i}...")
        stats.add_step(f"Processing segment {i}")

        step_out_dir = temp_dir / f"step_{i}"
        step_out_dir.mkdir(parents=True, exist_ok=True)

        start = stable_segments[i][1]
        stop = stable_segments[i + 1][0]

        start_img = frames[start]
        stop_img = frames[stop]
        live_path = device.screenshot(index=0, save_path=str(step_out_dir))

        tmp_start_path = step_out_dir / "tmp_start.png"
        tmp_stop_path = step_out_dir / "tmp_stop.png"
        cv2.imwrite(str(tmp_start_path), start_img)
        cv2.imwrite(str(tmp_stop_path), stop_img)

        # XML UI parse and clickable element detection
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

        labeled_path = label_screenshot(
            screenshot_path=live_path,
            screenshot_dir=str(step_out_dir),
            name="labeled",
            elements=elements,
        )
        current_img_labeled_xml_region = cv2.imread(labeled_path)

        # DINO detection for grounding region proposals
        dino_out_path = step_out_dir / "dino.png"
        dino_regions = run_grounding_dino(str(tmp_start_path), str(dino_out_path))

        regions = []
        for idx, e in enumerate(elements):
            region = {
                "index": idx,
                "center": e.center,
                "box": list(e.bounds),
                "phrase": e.text if e.text else "unknown element",
            }
            regions.append(region)

        relevant = ask_gpt_for_relevant_regions(str(dino_out_path), str(tmp_stop_path))
        relevant = extract_json(relevant)
        logger.info(f"Relevant regions: {relevant}")
        target_indices = relevant["target_regions"]
        logger.info(f"GPT selected regions: {target_indices}")

        relevant_annotated_path = step_out_dir / "relevant_regions.png"
        annotate_relevant_regions(
            str(tmp_start_path),
            str(relevant_annotated_path),
            dino_regions,
            target_indices,
        )

        region_index_to_center = {r["index"]: r["center"] for r in regions}

        show_images(
            cv2.imread(str(relevant_annotated_path)),
            stop_img,
            current_img_labeled_xml_region,
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

            labeled_path = label_screenshot(
                screenshot_path=live_path,
                screenshot_dir=str(step_out_dir),
                name="labeled",
                elements=elements,
            )

            recovery_reply = ask_gpt_for_action_region(
                str(tmp_start_path),
                str(tmp_stop_path),
                labeled_path,
                relevant["predicted_action"],
            )
            recovery_action = extract_json(recovery_reply)

            if (
                "region" in recovery_action
                and recovery_action["region"] in region_index_to_center
            ):
                recovery_action["position"] = region_index_to_center[
                    recovery_action["region"]
                ]
                logger.info(
                    f"Recovery using region index: {recovery_action['region']} at {recovery_action['position']}"
                )
            else:
                matched_element = match_action_to_element(recovery_action, elements)
                if matched_element:
                    recovery_action["position"] = matched_element.center
                    logger.info(
                        f"Recovery matched element: '{matched_element.text}' at {matched_element.center}"
                    )

            execute_actions(device, [recovery_action])
            time.sleep(replay_config.get("post_recovery_sleep", 1.0))
            live_path = device.screenshot(index=0, save_path=str(step_out_dir))
            match = extract_json(
                ask_gpt_state_consistency(str(tmp_start_path), live_path)
            )
            attempts += 1

        if match["same_state"] == "yes":
            reply = ask_gpt_for_action_region(
                str(relevant_annotated_path),
                str(tmp_stop_path),
                labeled_path,
                relevant["predicted_action"],
                target_indices,
            )
            action = extract_json(reply)

            matched_element = match_action_to_element(action, elements)
            if "region" in action and action["region"] in region_index_to_center:
                action["position"] = region_index_to_center[action["region"]]
                logger.info(
                    f"Using region index: {action['region']} at {action['position']}"
                )
            elif matched_element:
                action["position"] = matched_element.center
                logger.info(
                    f"Matched element: '{matched_element.text}' at {matched_element.center}"
                )
            else:
                logger.warning(
                    "No valid region or element match. Using original position if available."
                )

            execute_actions(device, [action])
            logger.info("Action executed.")
            stats.actions_executed += 1
        else:
            logger.warning(
                f"Skipping action: current GUI state does not match start state. "
                f"Mismatch reason: {match['description']}"
            )

        input("Press Enter to continue...")

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
