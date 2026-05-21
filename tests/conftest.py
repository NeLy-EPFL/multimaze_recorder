"""Shared pytest fixtures."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_gst(monkeypatch):
    """Patch GStreamer so camera tests run without hardware."""
    gst_mock = MagicMock()
    gst_mock.is_initialized.return_value = True
    gst_mock.State.PLAYING = 4
    gst_mock.State.READY = 2
    gst_mock.State.PAUSED = 3
    gst_mock.State.NULL = 1
    gst_mock.FlowReturn.OK = 0
    gst_mock.SECOND = 1_000_000_000

    gi_mock = MagicMock()
    gi_mock.require_version = MagicMock()

    glib_mock = MagicMock()
    tcam_mock = MagicMock()

    modules = {
        "gi": gi_mock,
        "gi.repository": MagicMock(),
        "gi.repository.GLib": glib_mock,
        "gi.repository.Gst": gst_mock,
        "gi.repository.Tcam": tcam_mock,
    }

    with patch.dict("sys.modules", modules):
        yield gst_mock


@pytest.fixture
def sample_preset_file(tmp_path):
    """Create a minimal camera preset JSON for tests."""
    import json
    preset = {
        "format": {
            "serial": "12345678",
            "width": 1920,
            "height": 1200,
            "framerate": "30/1",
        },
        "cropping": {"Left": 0, "Top": 0, "Right": 1920, "Bottom": 1200},
        "properties": [
            {"property": "ExposureAuto", "value": "Off"},
            {"property": "ExposureTime", "value": 800.0},
        ],
    }
    p = tmp_path / "test_preset.json"
    p.write_text(json.dumps(preset))
    return p


@pytest.fixture
def config_dir():
    """Return the package config directory."""
    return Path(__file__).parent.parent / "src" / "multimaze_recorder" / "gui" / "config"
