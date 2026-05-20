"""Unit tests for multimaze_recorder.utilities (no hardware required)."""

import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def patch_gi_and_camera(monkeypatch):
    # Pre-load cv2 so it stays in sys.modules across patch.dict contexts
    import cv2  # noqa: F401

    gi_mod = MagicMock()
    gst = MagicMock()
    gst.is_initialized.return_value = True
    gst.State.PLAYING = 4
    gst.FlowReturn.OK = 0
    gst.SECOND = 1_000_000_000
    pipeline = MagicMock()
    pipeline.get_state.return_value = (None, gst.State.PLAYING, None)
    gst.parse_launch.return_value = pipeline

    modules = {
        "gi": gi_mod,
        "gi.repository": MagicMock(),
        "gi.repository.GLib": MagicMock(),
        "gi.repository.Gst": gst,
        "gi.repository.Tcam": MagicMock(),
    }
    # Only delete multimaze_recorder modules so gi mocks take effect on re-import
    for k in list(sys.modules.keys()):
        if "multimaze_recorder" in k:
            del sys.modules[k]

    with patch.dict("sys.modules", modules):
        yield


def test_create_thumbnail_shape():
    from multimaze_recorder.utilities import create_thumbnail
    frame = np.zeros((3000, 4096, 1), dtype=np.uint8)
    thumb, dot_state, last_time = create_thumbnail(frame, False, 0.0)
    assert thumb.shape == (480, 640, 3)
    assert thumb.dtype == np.uint8


def test_create_thumbnail_toggles_dot():
    import time
    from multimaze_recorder.utilities import create_thumbnail
    frame = np.zeros((100, 100, 1), dtype=np.uint8)
    # Start with dot off and a very old last_toggle_time to force a toggle
    _, dot_after, _ = create_thumbnail(frame, False, 0.0)
    assert dot_after is True  # should have toggled


def test_create_thumbnail_no_toggle_if_recent():
    import time
    from multimaze_recorder.utilities import create_thumbnail
    frame = np.zeros((100, 100, 1), dtype=np.uint8)
    # Recent toggle: last_toggle_time is "now"
    now = time.perf_counter()
    _, dot_after, _ = create_thumbnail(frame, False, now)
    assert dot_after is False  # should NOT have toggled


def test_update_progress_bar():
    import time
    from multimaze_recorder.utilities import update_progress_bar
    from unittest.mock import MagicMock
    pbar = MagicMock()
    pbar.n = 0
    update_progress_bar(pbar, time.perf_counter() - 5, 60)
    # Should have called update and set_description
    pbar.update.assert_called_once()
    pbar.set_description.assert_called_once()


def test_configure_camera_calls_tis(tmp_path):
    """configure_camera should open a device and start the pipeline."""
    import json
    from multimaze_recorder.utilities import configure_camera

    preset = {
        "format": {"serial": "99999", "width": 1920, "height": 1200, "framerate": "30/1"},
        "cropping": {"Left": 0, "Top": 0, "Right": 1920, "Bottom": 1200},
        "properties": [],
    }
    preset_file = tmp_path / "preset.json"
    preset_file.write_text(json.dumps(preset))

    # Patch TIS class so no real camera is opened
    with patch("multimaze_recorder.utilities.TIS_module") as mock_tis_mod:
        mock_tis = MagicMock()
        mock_tis_mod.TIS.return_value = mock_tis
        mock_tis_mod.SinkFormats.GRAY8 = "GRAY8"
        mock_tis.start_pipeline.return_value = True
        mock_source = MagicMock()
        mock_source.get_property.return_value = "{}"
        mock_tis.get_source.return_value = mock_source

        result = configure_camera(str(preset_file))

        mock_tis_mod.TIS.assert_called_once()
        mock_tis.open_device.assert_called_once()
        mock_tis.start_pipeline.assert_called_once()
        assert result is mock_tis
