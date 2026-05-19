import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from segment_replay import (
    action_is_executable,
    artifact_path,
    normalize_action_response,
    normalize_relevant_response,
)


def test_normalize_action_response_accepts_scalar_region():
    action = normalize_action_response({"action": "tap", "region": "7"})

    assert action["action"] == "tap"
    assert action["region"] == 7


def test_normalize_action_response_collapses_region_list():
    action = normalize_action_response({"action": "tap", "region": [3, 4]})

    assert action["region"] == 3
    assert action["regions"] == [3, 4]


def test_normalize_relevant_response_defaults_bad_action():
    relevant = normalize_relevant_response(
        {"target_regions": ["1", 2, "bad"], "predicted_action": "drag"}
    )

    assert relevant["target_regions"] == [1, 2]
    assert relevant["predicted_action"] == "no action"


def test_tap_without_position_is_not_executable():
    assert not action_is_executable({"action": "tap"})


def test_input_text_is_executable_with_text():
    assert action_is_executable({"action": "input_text", "text": "hello"})


def test_artifact_path_uses_flat_source_tagged_name(tmp_path):
    assert artifact_path(tmp_path, 3, "v", "dino") == tmp_path / "step_3v_dino.png"
    assert artifact_path(tmp_path, 3, "e", "labeled") == tmp_path / "step_3e_labeled.png"


def test_artifact_path_rejects_unknown_source(tmp_path):
    try:
        artifact_path(tmp_path, 0, "x", "dino")
    except ValueError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError("Expected artifact_path to reject unknown source")
