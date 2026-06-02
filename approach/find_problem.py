#!/usr/bin/env python
"""
Find problem: Analyze a ViBR run and generate issue report with ViBR paper failure categories.
Usage: python approach/find_problem.py [--app_name APP] [--quality QUALITY]
  Defaults to config.yml values if not specified.
"""

import json
import re
from pathlib import Path
from typing import Optional
import yaml


FAILURE_CATEGORIES = {
    # Stage 1: Action Segmentation
    "over-segmentation": {
        "stage": "1: Action Segmentation",
        "keywords": ["loading", "delay", "resource"],
        "description": "Resource loading delays split one action into multiple segments.",
    },
    "dynamic-element-false-boundary": {
        "stage": "1: Action Segmentation",
        "keywords": ["ad", "advertisement", "video", "playback", "dynamic element"],
        "description": "Dynamic GUI elements (ads, video) create spurious scene cuts.",
    },
    # Stage 2: GUI State Comparison
    "resolution-layout-mismatch": {
        "stage": "2: GUI State Comparison",
        "keywords": ["layout", "position", "misalign", "shift"],
        "description": "Resolution or layout differences between recording and live device.",
    },
    "cosmetic-theme-difference": {
        "stage": "2: GUI State Comparison",
        "keywords": ["color", "theme", "dark mode", "font", "scale"],
        "description": "Cosmetic changes (dark mode, font scale) without interaction semantics change.",
    },
    "transient-artifact-overlay": {
        "stage": "2: GUI State Comparison",
        "keywords": ["toast", "banner", "notification", "overlay"],
        "description": "Transient artifacts (toast, status bar) that obscure the target region.",
    },
    "screen-recording-artifact": {
        "stage": "2: GUI State Comparison",
        "keywords": ["border", "artifact", "watermark", "container"],
        "description": "Screen recording artifacts (emulator border, watermark) degrade comparison.",
    },
    "scroll-induced-element-shift": {
        "stage": "2: GUI State Comparison",
        "keywords": ["scroll", "shifted", "moved", "position change"],
        "description": "Element positions shifted due to scrolling between recording and device.",
    },
    "dynamic-content-change": {
        "stage": "2: GUI State Comparison",
        "keywords": ["content", "dynamic", "different", "changed", "feed", "profile"],
        "description": "Dynamic/session-specific content changes (feed, ads, personalization).",
    },
    # Stage 3: Bug Replay on Device
    "masked-intermediate-transition": {
        "stage": "3: Bug Replay on Device",
        "keywords": ["input", "masked", "password", "pin"],
        "description": "Masked intermediate transitions (password input shown as dots).",
    },
    "semantic-gap": {
        "stage": "3: Bug Replay on Device",
        "keywords": [],  # default/catchall
        "description": "Semantic gap between GUI states; VLM cannot infer correct action.",
    },
}


def classify_mismatch(reason: str) -> str:
    """Classify a mismatch reason text to a failure category."""
    reason_lower = reason.lower()

    for category, info in FAILURE_CATEGORIES.items():
        if category == "semantic-gap":  # Skip default
            continue
        for keyword in info["keywords"]:
            if keyword.lower() in reason_lower:
                return category

    return "semantic-gap"  # default


def load_config(app_name: Optional[str] = None, quality: Optional[str] = None):
    """Load config.yml and return parsed values."""
    config_path = Path("approach/input/config.yml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    _app_name = app_name or config["run"]["app_name"]
    _quality = quality or config["run"]["quality"]
    _gemini_model = config["model"]["gemini_model"]

    return _app_name, _quality, _gemini_model


def read_artifact(path: Path) -> Optional[dict | str]:
    """Read JSON or text artifact."""
    if not path.exists():
        return None

    try:
        if path.suffix == ".json":
            with open(path) as f:
                return json.load(f)
        else:
            with open(path) as f:
                return f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def extract_skipped_actions(log_text: str) -> list[tuple[int, str]]:
    """
    Extract skipped actions and their mismatch reasons from log.
    Returns: list of (step_number, mismatch_reason)
    """
    skipped = []
    pattern = r"\[WARNING\].*?Skipping action: current GUI state does not match start state\. Mismatch reason: (.+?)(?:\n|$)"

    for i, match in enumerate(re.finditer(pattern, log_text)):
        reason = match.group(1).strip()
        skipped.append((i, reason))

    return skipped


def extract_alignment_attempts(log_text: str) -> int:
    """Count how many times 'Attempting to align state' appears in log."""
    return len(re.findall(r"\[WARNING\].*?Attempting to align state", log_text))


def find_low_confidence_steps(analysis: dict) -> list[dict]:
    """Extract steps with low confidence from video analysis JSON."""
    low_conf: list[dict] = []

    if "steps" not in analysis:
        return low_conf

    for step in analysis.get("steps", []):
        if step.get("confidence") == "low":
            low_conf.append(step)

    return low_conf


def build_issue_report(
    app_name: str,
    quality: str,
    gemini_model: str,
    status: str,
    scenes: int,
    actions_executed: int,
    skipped_actions: list[tuple[int, str]],
    alignment_attempts: int,
    low_conf_steps: list[dict],
) -> str:
    """Build markdown issue report."""
    skipped_count = scenes - actions_executed

    report = f"""# Run Issue Report: {app_name} ({quality} run)

**App:** {app_name}
**Model:** {gemini_model}
**Quality:** {quality}
**Pipeline status:** {status}
**Scenes detected:** {scenes}
**Actions executed:** {actions_executed}
**Skipped segments:** {skipped_count}

---

## Problems Found

"""

    if skipped_count == 0:
        report += "*No failures detected. All segments executed successfully.*\n"
    else:
        # Categorize and report each skipped action
        categories_found: dict[str, list[tuple[int, str]]] = {}
        for step_num, reason in skipped_actions:
            category = classify_mismatch(reason)
            if category not in categories_found:
                categories_found[category] = []
            categories_found[category].append((step_num, reason))

        for category in sorted(categories_found.keys()):
            cat_info = FAILURE_CATEGORIES.get(category, {})
            stage = cat_info.get("stage", "Unknown")

            report += f"### [{stage}] — {category.replace('-', ' ').title()}\n"

            for step_num, reason in categories_found[category]:
                report += f"\n*Step {step_num}: State mismatch*\n\n"
                report += f"**Mismatch reason (from log):**\n> {reason}\n\n"

            report += "\n"

    # Root cause analysis
    report += """---

## Limitations & Root Cause Analysis

"""

    if skipped_count > 0:
        category_counts: dict[str, int] = {}
        for _, reason in skipped_actions:
            category = classify_mismatch(reason)
            category_counts[category] = category_counts.get(category, 0) + 1

        for category in sorted(category_counts.keys()):
            cat_info = FAILURE_CATEGORIES.get(category, {})
            stage = cat_info.get("stage", "Unknown")
            description = cat_info.get("description", "Unknown failure mode")
            count = category_counts[category]

            report += f"### {category.replace('-', ' ').title()}\n"
            report += f"{description} This failure mode occurred {count} time(s) in this run.\n\n"

            if category == "resolution-layout-mismatch":
                report += "ViBR's GUI State Comparison (Section 2.2.3) uses visual similarity matching to determine if the current live screen matches the recorded reference frame. Resolution or layout differences between the recording device and the test device cause element misalignment, leading the LLM binary classifier [YES/NO] to incorrectly flag matching states as inconsistent. This maps to the 'Resolution/layout mismatch' failure mode documented in ViBR Section 3.2.4, Figure 7a. A possible mitigation would be to use layout-aware alignment (e.g., perspective correction) or scale-invariant feature matching before comparison.\n\n"

            elif category == "cosmetic-theme-difference":
                report += "Cosmetic settings (dark mode, font scaling, language localization) introduce significant visual differences without changing interaction semantics. ViBR's whole-GUI visual comparison cannot distinguish functional changes from cosmetic ones, causing false-negative state matches. This maps to the 'Cosmetic theme difference' failure mode (Section 3.2.4, Figure 7b). A possible mitigation would be to filter cosmetic variations or use semantic-level comparison (e.g., accessibility tree matching) instead of pixel-level.\n\n"

            elif category == "transient-artifact-overlay":
                report += "Transient overlays (toast messages, status banners) appear during replay and are captured in the screenshot, introducing visual differences that the LLM binary classifier misinterprets as state inconsistency. ViBR has no mechanism to distinguish transient artifacts from functional changes. This maps to the 'Transient artifact overlay' failure mode (Section 3.2.4, Figure 7c). A possible mitigation would be to pre-filter known transient UI patterns or apply temporal filtering to ignore short-lived overlays.\n\n"

            elif category == "screen-recording-artifact":
                report += "Screen recording artifacts (emulator container borders, watermarks from third-party tools) degrade image-based comparisons. ViBR's visual similarity matching is sensitive to these artifacts. This maps to the 'Screen recording artifact' failure mode (Section 3.2.4, Figure 7d). A possible mitigation would be to detect and crop known artifact regions before comparison.\n\n"

            elif category == "scroll-induced-element-shift":
                report += "Scrolling causes GUI elements to shift position between the recording and the live device. ViBR's Region-of-Interest (ROI) detection (Section 2.2.1-2.2.2) may misalign due to these shifts, causing the VLM to reason over the wrong image region. This maps to the 'Scroll-induced element shift' failure mode (Section 3.2.4, Figure 7e). A possible mitigation would be to use scroll-aware region detection or element-centric (rather than pixel-centric) comparison.\n\n"

            elif category == "dynamic-content-change":
                report += "Dynamic GUI content changes between sessions (personalized feeds, advertisements, user profiles). ViBR's holistic GUI comparison cannot match screens with dynamic content differences. This maps to the 'Dynamic/session-specific content' failure mode (Section 3.2.4, Figure 7f). A possible mitigation would be to focus comparison on the Region of Interest (target element) rather than the whole GUI, or to use content-agnostic structural matching.\n\n"

            elif category == "semantic-gap":
                report += "ViBR's action inference (Section 2.3.3) relies on the VLM to infer the next user action from consecutive GUI states. A semantic gap between pre- and post-action screens makes this inference impossible without intermediate frame context. This maps to the 'Semantic gap between GUI states' failure mode (Section 3.3.4, Figure 8a). A possible mitigation would be to include intermediate animation frames or to request the VLM to generate exploratory micro-actions (e.g., back, home, wait) when the gap is ambiguous.\n\n"

            elif category == "masked-intermediate-transition":
                report += "Inputting sensitive values (e.g., passwords, PINs) produces masked output (shown as `*` or dots). ViBR cannot identify the precise input value from masked screenshots alone. This maps to the 'Masked intermediate transition' failure mode (Section 3.3.4, Figure 8b). A possible mitigation would be to explicitly detect input masking and use metadata (e.g., input field type) to infer the intended input action.\n\n"

            elif category == "over-segmentation":
                report += "Delays in resource loading (e.g., images, data) can cause one user action to produce two or more scene boundaries in video segmentation. The system detects a scene cut for the GUI transition, then another for the delayed resource rendering. This maps to the 'Over-segmentation' failure mode (Section 3.1.4). A possible mitigation would be to use temporal windowing to merge nearby segments, or to include resource-loading indicators in the segmentation heuristic.\n\n"

            elif category == "dynamic-element-false-boundary":
                report += "Dynamic GUI elements such as advertisements or video playback produce continuous frame differences that are mistakenly interpreted as separate user actions. This maps to the 'Dynamic element false boundary' failure mode (Section 3.1.4). A possible mitigation would be to filter known dynamic regions before segmentation, or to use content-aware frame comparison that ignores high-entropy (dynamic) areas.\n\n"
    else:
        report += "*No limitations detected in this run. All segments executed successfully.*\n"

    # Summary table
    report += "\n---\n\n## Summary of Limitations\n\n"

    if skipped_count == 0:
        report += "| Stage | Failure Category | Occurrences | Impact |\n"
        report += "|---|---|---|---|\n"
        report += "| — | — | 0 | None |\n\n"
        report += f"**Overall impact:** All {scenes} replay steps completed successfully, meaning ViBR fully reproduced the recorded bug scenario.\n"
    else:
        report += "| Stage | Failure Category | Occurrences | Impact |\n"
        report += "|---|---|---|---|\n"

        categories_by_stage: dict[str, dict[str, int]] = {}
        for _, reason in skipped_actions:
            category = classify_mismatch(reason)
            cat_info = FAILURE_CATEGORIES.get(category, {})
            stage_name = str(cat_info.get("stage", "Unknown"))
            if stage_name not in categories_by_stage:
                categories_by_stage[stage_name] = {}
            stage_dict = categories_by_stage[stage_name]
            stage_dict[category] = stage_dict.get(category, 0) + 1

        for stage in sorted(categories_by_stage.keys()):
            stage_dict = categories_by_stage[stage]
            for category in sorted(stage_dict.keys()):
                count = stage_dict[category]
                report += f"| {stage} | {category.replace('-', ' ').title()} | {count} | Segment skipped |\n"

        report += f"\n**Overall impact:** {skipped_count} of {scenes} replay steps failed, meaning ViBR could not fully reproduce the recorded bug scenario. The agent achieved {int(100 * actions_executed / scenes)}% action coverage.\n"

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze ViBR run and generate issue report")
    parser.add_argument("--app_name", help="App name (default: from config.yml)")
    parser.add_argument("--quality", help="Quality (good|bad, default: from config.yml)")
    args = parser.parse_args()

    # Load config
    app_name, quality, gemini_model = load_config(args.app_name, args.quality)

    # Build paths
    app_dir = Path(f"apps/{app_name}-{gemini_model}")
    log_path = app_dir / f"{quality}-run.log"
    summary_path = app_dir / f"{quality}-run-summary.json"
    analysis_path = app_dir / f"{quality}-video-analysis.json"
    output_path = app_dir / f"{quality}-run-issue.md"

    print(f"Analyzing {app_name} ({quality}) in {app_dir}/")

    # Read artifacts
    summary = read_artifact(summary_path)
    log_text = read_artifact(log_path)
    analysis = read_artifact(analysis_path)

    if not summary or not log_text:
        print("Error: Missing required artifacts (log or summary JSON)")
        return

    # Extract problem signals
    status = summary.get("status", "unknown")
    scenes = summary.get("scenes", 0)
    actions_executed = summary.get("actions_executed", 0)

    skipped_actions = extract_skipped_actions(log_text)
    alignment_attempts = extract_alignment_attempts(log_text)
    low_conf_steps = find_low_confidence_steps(analysis) if analysis else []

    # Generate report
    report = build_issue_report(
        app_name=app_name,
        quality=quality,
        gemini_model=gemini_model,
        status=status,
        scenes=scenes,
        actions_executed=actions_executed,
        skipped_actions=skipped_actions,
        alignment_attempts=alignment_attempts,
        low_conf_steps=low_conf_steps,
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    print(f"✓ Report written to {output_path}")
    print(f"  Status: {status}")
    print(f"  Scenes: {scenes}, Actions: {actions_executed}, Skipped: {scenes - actions_executed}")
    if skipped_actions:
        print(f"  Failure categories: {', '.join(set(classify_mismatch(r) for _, r in skipped_actions))}")


if __name__ == "__main__":
    main()