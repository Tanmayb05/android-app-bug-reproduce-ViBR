from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GROUNDING_DINO_ROOT = PROJECT_ROOT / "GroundingDINO"
for path in (PROJECT_ROOT, GROUNDING_DINO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from config_loader import get_config


def _apply_runtime_config() -> None:
    runtime_config = get_config().get("runtime", {})
    matplotlib_config_dir = runtime_config.get("matplotlib_config_dir")
    if matplotlib_config_dir:
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config_dir))
        Path(matplotlib_config_dir).mkdir(parents=True, exist_ok=True)

    xdg_cache_home = runtime_config.get("xdg_cache_home")
    if xdg_cache_home:
        os.environ.setdefault("XDG_CACHE_HOME", str(xdg_cache_home))
        Path(xdg_cache_home).mkdir(parents=True, exist_ok=True)


_apply_runtime_config()

from GroundingDINO.groundingdino.util.inference import load_model, load_image, predict
import cv2
import numpy as np
import torch
import supervision as sv
import logging
from PIL import Image
from typing import cast
from torchvision.ops import box_convert

logger = logging.getLogger(__name__)

"""
GroundingDINO region detection and annotation utilities.

- Uses a loaded GroundingDINO model to detect semantically-relevant UI regions in a screenshot.
- Provides annotation functions for highlighting both all detected regions and a subset of relevant regions.
"""

def _select_dino_device() -> str:
    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is not None and mps_backend.is_available():
        return "mps"
    return "cpu"


DINO_DEVICE = _select_dino_device()

MODEL = None
MODEL_CONFIG_PATH = None
MODEL_WEIGHTS_PATH = None


def _dino_config() -> dict:
    return get_config().get("dino", {})


def _model():
    """Load the configured DINO model once per config/weights pair."""
    global MODEL, MODEL_CONFIG_PATH, MODEL_WEIGHTS_PATH
    config = _dino_config()
    config_path = config.get(
        "config_path", "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
    )
    weights_path = config.get(
        "weights_path", "GroundingDINO/weights/groundingdino_swint_ogc.pth"
    )

    if (
        MODEL is None
        or MODEL_CONFIG_PATH != config_path
        or MODEL_WEIGHTS_PATH != weights_path
    ):
        logger.info(
            "Loading GroundingDINO model with config=%s weights=%s device=%s",
            config_path,
            weights_path,
            DINO_DEVICE,
        )
        MODEL = load_model(config_path, weights_path, device=DINO_DEVICE)
        MODEL_CONFIG_PATH = config_path
        MODEL_WEIGHTS_PATH = weights_path

    return MODEL

def _as_cv2_image(image: np.ndarray | Image.Image) -> np.ndarray:
    """Convert supervision/PIL output to an OpenCV-compatible BGR array."""
    if isinstance(image, Image.Image):
        return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    return image

def run_grounding_dino(image_path: str, output_path: str):
    """
    Runs GroundingDINO model to detect regions in an image and save an annotated version.

    Args:
        image_path (str): Path to input screenshot image (RGB).
        output_path (str): Where to save the annotated image.

    Returns:
        regions (list): List of dicts for each detected region, each with keys:
            - "index": int (detection index)
            - "phrase": str (predicted phrase)
            - "confidence": float (logit)
            - "center": (cx, cy) int tuple
            - "box": [x1, y1, x2, y2] bounding box in image coords
    """
    image_source, image_tensor = load_image(image_path)
    config = _dino_config()
    text_prompt = config.get(
        "text_prompt",
        "header bar. navigation bar. toolbar. button. icon. checkbox. toggle. text input. search bar. text field. image. card. list item. bottom navigation. tab bar",
    )
    box_threshold = config.get("box_threshold", 0.25)
    text_threshold = config.get("text_threshold", 0.2)

    # Run GroundingDINO on the image tensor
    boxes, logits, phrases = predict(
        model=_model(),
        image=image_tensor,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold,
        device=DINO_DEVICE,
    )

    if len(boxes) == 0:
        logger.warning("No regions detected by GroundingDINO.")
        cv2.imwrite(output_path, cv2.cvtColor(image_source, cv2.COLOR_RGB2BGR))
        logger.info(f"Annotated DINO output saved to {output_path}")
        return []

    # Scale predicted boxes to image size and convert from (cx, cy, w, h) to (x1, y1, x2, y2)
    h, w, _ = image_source.shape
    boxes_scaled = boxes * torch.Tensor([w, h, w, h])
    xyxy = box_convert(boxes=boxes_scaled, in_fmt="cxcywh", out_fmt="xyxy").numpy()

    # Build detections for supervision annotation
    detections = sv.Detections(xyxy=xyxy)
    labels = [
        f"{i}: {phrase} ({logit:.2f})"
        for i, (phrase, logit) in enumerate(zip(phrases, logits))
    ]

    # Annotate and save image using Supervision
    annotated_frame = cv2.cvtColor(image_source, cv2.COLOR_RGB2BGR)
    bbox_annotator = sv.BoxAnnotator(color_lookup=sv.ColorLookup.INDEX)
    label_annotator = sv.LabelAnnotator(color_lookup=sv.ColorLookup.INDEX)
    annotated_frame = bbox_annotator.annotate(scene=annotated_frame, detections=detections)
    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

    cv2.imwrite(output_path, _as_cv2_image(annotated_frame))
    logger.info(f"Annotated DINO output saved to {output_path}")

    # Return region metadata for downstream reasoning or annotation
    regions = []
    for i, (box, phrase, logit) in enumerate(zip(xyxy, phrases, logits)):
        x1, y1, x2, y2 = map(int, box)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        regions.append({
            "index": i,
            "phrase": phrase,
            "confidence": float(logit),
            "center": (cx, cy),
            "box": [x1, y1, x2, y2]
        })

    return regions

def annotate_relevant_regions(image_path, output_path, regions, relevant_indices):
    """
    Annotate only a subset of detected regions (by index) on an image.

    Args:
        image_path (str): Path to original screenshot.
        output_path (str): Path to save annotated image.
        regions (list): List of region dicts from run_grounding_dino.
        relevant_indices (list): List of indices for regions to highlight.
    """
    import supervision as sv
    import numpy as np
    import cv2

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    image = cast(np.ndarray, image)

    filtered_regions = [r for r in regions if r["index"] in relevant_indices]

    if not filtered_regions:
        logger.warning("No relevant regions to annotate.")
        cv2.imwrite(output_path, image)
        return

    boxes = np.array([r["box"] for r in filtered_regions])
    labels = [f"{r['index']}: {r['phrase']}" for r in filtered_regions]

    detections = sv.Detections(xyxy=boxes)
    annotated = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    bbox_annotator = sv.BoxAnnotator(color_lookup=sv.ColorLookup.INDEX)
    label_annotator = sv.LabelAnnotator(color_lookup=sv.ColorLookup.INDEX)

    annotated = cast(Image.Image, bbox_annotator.annotate(scene=annotated, detections=detections))
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

    cv2.imwrite(output_path, _as_cv2_image(annotated))
    logger.info(f"Relevant-only annotation saved to {output_path}")
