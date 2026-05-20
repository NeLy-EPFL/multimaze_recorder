"""Unit tests for the TIS camera module (no hardware required)."""

import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers to inject mocked GI modules before importing the camera module
# ---------------------------------------------------------------------------

def _make_gi_mocks():
    gst = MagicMock()
    gst.is_initialized.return_value = True
    gst.State.PLAYING = 4
    gst.State.READY = 2
    gst.State.PAUSED = 3
    gst.State.NULL = 1
    gst.FlowReturn.OK = 0
    gst.SECOND = 1_000_000_000

    pipeline = MagicMock()
    pipeline.get_state.return_value = (None, gst.State.PLAYING, None)
    gst.parse_launch.return_value = pipeline

    gi_mod = MagicMock()
    gi_mod.require_version = MagicMock()

    gi_repo = MagicMock()
    gi_repo.GLib = MagicMock()
    gi_repo.Gst = gst
    gi_repo.Tcam = MagicMock()
    gi_mod.repository = gi_repo

    return gi_mod, gst


@pytest.fixture(autouse=True)
def patch_gi():
    gi_mod, gst = _make_gi_mocks()
    modules = {
        "gi": gi_mod,
        "gi.repository": gi_mod.repository,
        "gi.repository.GLib": gi_mod.repository.GLib,
        "gi.repository.Gst": gst,
        "gi.repository.Tcam": gi_mod.repository.Tcam,
    }
    with patch.dict("sys.modules", modules):
        # Force re-import so our mocks are used
        for mod_name in list(sys.modules.keys()):
            if "multimaze_recorder.camera" in mod_name:
                del sys.modules[mod_name]
        yield gst


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sink_formats_values():
    from multimaze_recorder.camera.tis import SinkFormats
    assert SinkFormats.GRAY8.value == "GRAY8"
    assert SinkFormats.GRAY16_LE.value == "GRAY16_LE"


def test_tis_instantiation():
    from multimaze_recorder.camera.tis import TIS
    tis = TIS(properties=[])
    assert tis.serialnumber == ""
    assert tis.height == 0
    assert tis.width == 0
    assert tis.ImageCallback is None
    assert tis.pipeline is None


def test_tis_set_image_callback():
    from multimaze_recorder.camera.tis import TIS

    def dummy_callback(tis, data):
        pass

    tis = TIS(properties=[])
    tis.set_image_callback(dummy_callback, "extra_arg")
    assert tis.ImageCallback is dummy_callback
    assert tis.ImageCallbackData == ("extra_arg",)


def test_tis_apply_properties(patch_gi):
    """applyProperties should call set_property for each config entry."""
    from multimaze_recorder.camera.tis import TIS

    props = [
        {"property": "ExposureAuto", "value": "Off"},
        {"property": "ExposureTime", "value": 800.0},
    ]
    tis = TIS(properties=props)

    # Inject a mock source so set_property doesn't crash
    mock_source = MagicMock()
    tis.source = mock_source
    mock_prop = MagicMock()
    mock_source.get_tcam_property.return_value = mock_prop

    tis.applyProperties()

    assert mock_source.get_tcam_property.call_count == 2
    calls = [c[0][0] for c in mock_source.get_tcam_property.call_args_list]
    assert "ExposureAuto" in calls
    assert "ExposureTime" in calls


def test_tis_get_property(patch_gi):
    from multimaze_recorder.camera.tis import TIS

    tis = TIS(properties=[])
    mock_source = MagicMock()
    tis.source = mock_source
    mock_prop = MagicMock()
    mock_prop.get_value.return_value = 42
    mock_source.get_tcam_property.return_value = mock_prop

    val = tis.get_property("Gain")
    assert val == 42
    mock_source.get_tcam_property.assert_called_once_with("Gain")


def test_tis_set_property_error(patch_gi):
    from multimaze_recorder.camera.tis import TIS

    tis = TIS(properties=[])
    mock_source = MagicMock()
    tis.source = mock_source
    mock_source.get_tcam_property.side_effect = RuntimeError("not found")

    with pytest.raises(RuntimeError, match="Failed to set property"):
        tis.set_property("NonExistent", 0)


def test_tis_stop_pipeline(patch_gi):
    from multimaze_recorder.camera.tis import TIS

    tis = TIS(properties=[])
    mock_pipeline = MagicMock()
    tis.pipeline = mock_pipeline

    tis.stop_pipeline()
    assert mock_pipeline.set_state.call_count == 2


def test_res_desc():
    from multimaze_recorder.camera.tis import ResDesc
    r = ResDesc(1920, 1200, ["30/1", "25/1"])
    assert r.width == 1920
    assert r.height == 1200
    assert "30/1" in r.fps


def test_fmt_desc_name():
    from multimaze_recorder.camera.tis import FmtDesc
    f = FmtDesc("image/jpeg", "JPEG")
    assert f.get_name() == "jpeg"
    f2 = FmtDesc("video/x-raw", "GRAY8")
    assert f2.get_name() == "GRAY8"
