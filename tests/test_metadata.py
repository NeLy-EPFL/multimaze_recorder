"""Tests for Metadata change detection and arena-ordering integrity."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock


# ── helpers ──────────────────────────────────────────────────────────────────

def _template(tmp_path, variables):
    p = tmp_path / "template.json"
    p.write_text(json.dumps({"Variable": variables}))
    return p


def _metadata(variables, arena_values=None):
    from multimaze_recorder.gui.widgets import Metadata
    m = Metadata.__new__(Metadata)
    dict.__init__(m)
    m["Variable"] = list(variables)
    if arena_values:
        m.update(arena_values)
    return m


def _parent(tmp_path, template_path, metadata_dict):
    """Minimal stand-in for ExperimentWindow."""
    from multimaze_recorder.gui.widgets import Metadata
    m = Metadata.__new__(Metadata)
    dict.__init__(m)
    m.update(metadata_dict)
    parent = MagicMock()
    parent.metadata = m
    parent.main_window.settings.metadata_template = template_path
    parent.folder_path = tmp_path / "exp"
    parent.folder_path.mkdir(exist_ok=True)
    return parent


# ── check_diff ────────────────────────────────────────────────────────────────

class TestCheckDiff:
    def test_no_change_returns_false(self, tmp_path):
        tpl = _template(tmp_path, ["Date", "Genotype"])
        m = _metadata(["Date", "Genotype"], {"Arena1": ["2024-01-01", "WT"]})
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is False

    def test_value_change_does_not_trigger(self, tmp_path):
        """Filling in arena values must never trigger the template-changed dialog."""
        tpl = _template(tmp_path, ["Date", "Genotype"])
        m = _metadata(["Date", "Genotype"], {"Arena1": ["completely_different_value"]})
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is False

    def test_trailing_empty_strings_ignored(self, tmp_path):
        """Template with trailing '' entries (from empty table rows) must not
        flag a difference when the saved metadata has them stripped."""
        tpl = _template(tmp_path, ["Date", "Genotype", "", "", ""])
        m = _metadata(["Date", "Genotype"])          # stripped, as save_metadata does it
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is False

    def test_new_variable_triggers(self, tmp_path):
        tpl = _template(tmp_path, ["Date", "Genotype"])
        m = _metadata(["Date", "Genotype", "NewVar"])
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is True

    def test_removed_variable_triggers(self, tmp_path):
        tpl = _template(tmp_path, ["Date", "Genotype", "Period"])
        m = _metadata(["Date", "Genotype"])
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is True

    def test_missing_template_returns_false(self, tmp_path):
        parent = MagicMock()
        parent.main_window.settings.metadata_template = tmp_path / "nonexistent.json"
        m = _metadata(["Date"])
        assert m.check_diff(parent) is False


# ── create_template ───────────────────────────────────────────────────────────

class TestCreateTemplate:
    def test_empty_strings_stripped_from_saved_template(self, tmp_path):
        """create_template must not write trailing '' entries into the file."""
        from multimaze_recorder.gui.widgets import Metadata
        m = Metadata.__new__(Metadata)
        dict.__init__(m)
        m["Variable"] = ["Date", "Genotype", "", "", ""]
        out = tmp_path / "new_template.json"
        m.create_template(MagicMock(), out)
        saved = json.loads(out.read_text())
        assert "" not in saved["Variable"]
        assert saved["Variable"] == ["Date", "Genotype"]

    def test_round_trip_template_produces_no_diff(self, tmp_path):
        """After create_template, check_diff on the same variables returns False."""
        from multimaze_recorder.gui.widgets import Metadata
        m = Metadata.__new__(Metadata)
        dict.__init__(m)
        m["Variable"] = ["Date", "Genotype", "Period"]
        tpl = tmp_path / "tpl.json"
        m.create_template(MagicMock(), tpl)

        parent = MagicMock()
        parent.main_window.settings.metadata_template = tpl
        assert m.check_diff(parent) is False


# ── arena ordering (require a display) ───────────────────────────────────────

@pytest.mark.usefixtures("qtbot")
class TestArenaOrdering:
    """Verify that arena values stay bound to the correct column through the
    full save / load cycle.  These are the regression guards for the
    arena-swapping bug."""

    def _make_widget(self, qtbot, metadata_dict, tmp_path):
        from multimaze_recorder.gui.widgets import CustomTableWidget
        parent = _parent(tmp_path, tmp_path / "tpl.json", metadata_dict)
        widget = CustomTableWidget(parent)
        qtbot.addWidget(widget)
        parent.table = widget
        return widget, parent

    # ── table structure ──────────────────────────────────────────────────────

    def test_column_headers_in_numeric_order(self, qtbot, tmp_path):
        widget, _ = self._make_widget(qtbot, {"Variable": []}, tmp_path)
        headers = [widget.horizontalHeaderItem(c).text() for c in range(1, 10)]
        assert headers == [f"Arena{i}" for i in range(1, 10)]

    # ── load correctness ─────────────────────────────────────────────────────

    def test_values_load_into_correct_columns(self, qtbot, tmp_path):
        """Arena1 values must appear in the Arena1 column, not Arena3 or Arena9."""
        metadata = {
            "Variable": ["Date", "Genotype"],
            "Arena1": ["2024-01-01", "WildType"],
            "Arena3": ["2024-03-03", "Mutant"],
            "Arena9": ["2024-09-09", "Hybrid"],
        }
        widget, _ = self._make_widget(qtbot, metadata, tmp_path)
        col_for = {
            widget.horizontalHeaderItem(c).text(): c
            for c in range(widget.columnCount())
        }
        for arena, expected in [
            ("Arena1", ["2024-01-01", "WildType"]),
            ("Arena3", ["2024-03-03", "Mutant"]),
            ("Arena9", ["2024-09-09", "Hybrid"]),
        ]:
            col = col_for[arena]
            for row, exp_val in enumerate(expected):
                item = widget.item(row, col)
                actual = item.text() if item else ""
                assert actual == exp_val, (
                    f"{arena} row {row}: expected {exp_val!r}, got {actual!r}"
                )

    # ── save correctness ─────────────────────────────────────────────────────

    def test_save_preserves_arena_column_binding(self, qtbot, tmp_path):
        """After save_metadata the JSON must have each arena's values under
        the correct key."""
        metadata = {
            "Variable": ["Date", "Genotype"],
            "Arena1": ["2024-01-01", "WT"],
            "Arena2": ["2024-02-02", "Mutant"],
            "Arena9": ["2024-09-09", "Hybrid"],
        }
        _, parent = self._make_widget(qtbot, metadata, tmp_path)
        parent.metadata.save_metadata(parent)

        saved = json.loads((tmp_path / "exp" / "metadata.json").read_text())
        assert saved["Arena1"] == ["2024-01-01", "WT"]
        assert saved["Arena2"] == ["2024-02-02", "Mutant"]
        assert saved["Arena9"] == ["2024-09-09", "Hybrid"]

    def test_arena_keys_in_numeric_order_in_json(self, qtbot, tmp_path):
        """Saved JSON must have Arena keys in order 1–9 regardless of dict
        insertion order in the source metadata."""
        metadata = {
            "Variable": ["Date"],
            "Arena9": ["last"],
            "Arena1": ["first"],    # intentionally out of order
            "Arena5": ["middle"],
        }
        _, parent = self._make_widget(qtbot, metadata, tmp_path)
        parent.metadata.save_metadata(parent)

        saved = json.loads((tmp_path / "exp" / "metadata.json").read_text())
        arena_keys = [k for k in saved if k.startswith("Arena") and "_" not in k]
        nums = [int(k[5:]) for k in arena_keys]
        assert nums == sorted(nums), f"Arena keys not in numeric order: {arena_keys}"

    # ── round-trip ───────────────────────────────────────────────────────────

    def test_round_trip_preserves_all_arena_values(self, qtbot, tmp_path):
        """Full save→reload cycle: every arena must have exactly its original values."""
        original = {
            "Variable": ["Date", "Genotype", "Period"],
            **{f"Arena{i}": [f"date{i}", f"geno{i}", f"period{i}"] for i in range(1, 10)},
        }
        _, parent = self._make_widget(qtbot, original, tmp_path)
        parent.metadata.save_metadata(parent)

        reloaded = json.loads((tmp_path / "exp" / "metadata.json").read_text())
        for i in range(1, 10):
            key = f"Arena{i}"
            assert reloaded[key] == [f"date{i}", f"geno{i}", f"period{i}"], (
                f"{key} corrupted after round-trip: {reloaded[key]}"
            )

    # ── swapping canary ──────────────────────────────────────────────────────

    def test_distinct_markers_not_swapped_across_arenas(self, qtbot, tmp_path):
        """Each arena carries a unique marker string.  After save, the marker
        for ArenaN must still be under ArenaN – not under any other arena."""
        metadata = {
            "Variable": ["Marker"],
            **{f"Arena{i}": [f"ARENA{i}_UNIQUE"] for i in range(1, 10)},
        }
        _, parent = self._make_widget(qtbot, metadata, tmp_path)
        parent.metadata.save_metadata(parent)

        saved = json.loads((tmp_path / "exp" / "metadata.json").read_text())
        for i in range(1, 10):
            key = f"Arena{i}"
            assert saved[key] == [f"ARENA{i}_UNIQUE"], (
                f"Arena values swapped! {key} contains {saved[key]}"
            )
