from pathlib import Path

import pytest
import yaml

from approach.core.config_loader import get_active_run

REPO_ROOT = Path(__file__).parent.parent.parent
VARIANTS = ("a", "b", "c")


def test_get_active_run_returns_first_entry():
    config = {
        "runs": [
            {"bug_dir": "data/video01-app#1"},
            {"bug_dir": "data/video02-app#2"},
        ]
    }

    assert get_active_run(config) == "data/video01-app#1"


def test_get_active_run_raises_on_empty_runs():
    with pytest.raises(ValueError):
        get_active_run({"runs": []})


def test_get_active_run_raises_on_missing_runs():
    with pytest.raises(ValueError):
        get_active_run({})


def test_get_active_run_raises_on_missing_bug_dir():
    with pytest.raises(ValueError):
        get_active_run({"runs": [{}]})


def _load_variant(letter: str) -> dict:
    path = REPO_ROOT / f"config.{letter}.yml"
    assert path.exists(), f"missing {path.name}"
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize("letter", VARIANTS)
def test_variant_config_has_single_matching_run(letter):
    config = _load_variant(letter)

    runs = config["runs"]
    assert len(runs) == 1, f"config.{letter}.yml must have exactly one run entry"

    bug_dir = get_active_run(config)
    video_id = Path(bug_dir).name.split("-")[0]
    assert video_id.endswith(letter), (
        f"config.{letter}.yml points at {bug_dir}, expected a video{{NN}}{letter} dir"
    )


@pytest.mark.parametrize("letter", VARIANTS)
def test_variant_config_declares_device_id(letter):
    assert _load_variant(letter)["adb"]["device_id"]


def test_variant_configs_are_mutually_isolated():
    """Each variant must target its own emulator and its own host-side UI dump.

    A copy-paste slip here would make two parallel runs fight over one emulator
    (or one ui_dump.xml) and silently produce garbage results.
    """
    device_ids = []
    dump_paths = []
    for letter in VARIANTS:
        adb_config = _load_variant(letter)["adb"]
        device_ids.append(adb_config["device_id"])
        dump_paths.append(adb_config["ui_dump_local_path"])

    assert len(set(device_ids)) == len(VARIANTS), f"duplicate device_id: {device_ids}"
    assert len(set(dump_paths)) == len(VARIANTS), f"duplicate ui_dump path: {dump_paths}"
