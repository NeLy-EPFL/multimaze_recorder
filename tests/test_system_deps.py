"""
System dependency checks.

These tests verify that the required non-Python dependencies are installed
correctly on the host.  They are intentionally designed to give actionable
error messages so they can serve as an installation checklist.
"""

import subprocess
import shutil
from pathlib import Path
import pytest


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def test_gstreamer_installed():
    """gst-inspect-1.0 must be reachable."""
    assert shutil.which("gst-inspect-1.0"), (
        "GStreamer tools not found. Install with:\n"
        "  sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base "
        "gstreamer1.0-plugins-good"
    )


def test_gstreamer_tcam_plugin():
    """The tcam GStreamer plugin must be loadable."""
    result = _run(["gst-inspect-1.0", "tcambin"])
    assert result.returncode == 0, (
        "tcambin GStreamer element not found.\n"
        "Install tiscamera from The Imaging Source – see INSTALL.md.\n"
        f"gst-inspect output: {result.stderr}"
    )


def test_tiscamera_typelib():
    """Tcam-1.0.typelib must be present for GObject-Introspection."""
    typelib = Path("/usr/lib/x86_64-linux-gnu/girepository-1.0/Tcam-1.0.typelib")
    assert typelib.exists(), (
        f"Tcam typelib not found at {typelib}.\n"
        "Install tiscamera from The Imaging Source – see INSTALL.md."
    )


def test_pygobject_importable():
    """PyGObject (gi) must be importable."""
    try:
        import gi  # noqa: F401
    except ImportError as exc:
        pytest.fail(
            f"Cannot import gi (PyGObject): {exc}\n"
            "Install system deps first:\n"
            "  sudo apt install libgirepository1.0-dev libglib2.0-dev\n"
            "Then:\n"
            "  uv sync"
        )


def test_tcam_gi_loadable():
    """The Tcam GI binding must load without errors."""
    try:
        import gi
        gi.require_version("Tcam", "1.0")
        from gi.repository import Tcam  # noqa: F401
    except Exception as exc:
        pytest.fail(
            f"Cannot load Tcam GI binding: {exc}\n"
            "This usually means tiscamera is not installed.\n"
            "See INSTALL.md for installation instructions."
        )


def test_gstreamer_gi_loadable():
    """GStreamer GI bindings must load without errors."""
    try:
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst  # noqa: F401
        Gst.init(None)
    except Exception as exc:
        pytest.fail(
            f"Cannot load GStreamer GI bindings: {exc}\n"
            "Install with:\n"
            "  sudo apt install python3-gst-1.0 gir1.2-gstreamer-1.0"
        )


def test_ffmpeg_available():
    """ffmpeg must be available for video processing scripts."""
    assert shutil.which("ffmpeg"), (
        "ffmpeg not found. Install with:\n  sudo apt install ffmpeg"
    )
