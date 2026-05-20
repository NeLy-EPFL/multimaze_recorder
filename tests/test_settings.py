"""Tests for the Settings class (no display required)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# Mock PyQt6 so tests run headlessly
@pytest.fixture(autouse=True)
def patch_pyqt(monkeypatch):
    qt_mock = MagicMock()
    modules = {
        "PyQt6": qt_mock,
        "PyQt6.QtGui": qt_mock,
        "PyQt6.QtWidgets": qt_mock,
        "PyQt6.QtCore": qt_mock,
    }
    with patch.dict("sys.modules", modules):
        import sys
        for k in list(sys.modules.keys()):
            if "multimaze_recorder.gui" in k:
                del sys.modules[k]
        yield


def _make_settings(tmp_path, experiments=None):
    """Build a Settings instance pointing at a temporary config dir."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "Presets").mkdir()
    (config_dir / "Metadata_Templates").mkdir()

    if experiments is None:
        experiments = [
            {
                "name": "TestExperiment",
                "path": "TestData/Videos",
                "metadata_template": "Metadata_Templates/variables_registry_Standard.json",
                "camera_settings": "Presets/standard_set.json",
            }
        ]

    (config_dir / "experiments.json").write_text(json.dumps(experiments))
    (config_dir / "Metadata_Templates" / "variables_registry_Standard.json").write_text(
        json.dumps({"Variable": ["Date", "Genotype"]})
    )
    (config_dir / "Presets" / "standard_set.json").write_text(
        json.dumps({"format": {}, "properties": []})
    )

    import importlib
    import multimaze_recorder.gui.settings as settings_mod
    importlib.reload(settings_mod)

    # Patch _CONFIG_DIR to point to our temp dir
    with patch.object(settings_mod, "_CONFIG_DIR", config_dir):
        s = settings_mod.Settings.__new__(settings_mod.Settings)
        settings_mod.Settings.__init__(s)
    return s


def test_settings_loads_experiments(tmp_path):
    s = _make_settings(tmp_path)
    assert len(s.experiments) == 1
    assert s.experiments[0]["name"] == "TestExperiment"


def test_settings_experiment_type(tmp_path):
    s = _make_settings(tmp_path)
    assert s.experiment_type == "TestExperiment"


def test_settings_metadata_template_is_absolute(tmp_path):
    s = _make_settings(tmp_path)
    assert s.metadata_template.is_absolute()
    assert s.metadata_template.name == "variables_registry_Standard.json"


def test_settings_camera_settings_is_absolute(tmp_path):
    s = _make_settings(tmp_path)
    assert s.camera_settings.is_absolute()
    assert s.camera_settings.name == "standard_set.json"


def test_settings_empty_experiments(tmp_path):
    s = _make_settings(tmp_path, experiments=[])
    assert s.experiment_type is None
    assert s.experiments == []


def test_settings_local_path_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MMRECORDER_LOCAL_PATH", str(tmp_path / "MyVideos"))
    s = _make_settings(tmp_path)
    assert s.local_path == tmp_path / "MyVideos"


def test_settings_update_settings(tmp_path):
    experiments = [
        {"name": "Exp1", "path": "Exp1/Videos", "camera_settings": "Presets/standard_set.json"},
        {"name": "Exp2", "path": "Exp2/Videos", "camera_settings": "Presets/standard_set.json"},
    ]
    s = _make_settings(tmp_path, experiments=experiments)
    s.update_settings("Exp2")
    assert s.experiment_type == "Exp2"


def test_config_dir_exists():
    """The package config directory must exist and contain expected files."""
    config_dir = (
        Path(__file__).parent.parent
        / "src"
        / "multimaze_recorder"
        / "gui"
        / "config"
    )
    assert config_dir.is_dir(), f"Config directory not found: {config_dir}"
    assert (config_dir / "experiments.json").is_file(), "experiments.json missing"
    assert (config_dir / "Presets").is_dir(), "Presets/ directory missing"
    assert (config_dir / "Metadata_Templates").is_dir(), "Metadata_Templates/ directory missing"
