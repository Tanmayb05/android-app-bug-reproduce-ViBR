import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest

from config_loader import get_active_run


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
