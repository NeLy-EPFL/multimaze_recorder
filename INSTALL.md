# Installation Guide

This guide covers everything needed to get `multimaze_recorder` running on a fresh Ubuntu 22.04/24.04 machine.

---

## Overview

The project has two categories of dependencies:

| Category | How to install |
|---|---|
| Python packages | `uv sync` (after system deps below) |
| System libraries (GStreamer, tiscamera) | `apt` + manual `.deb` from The Imaging Source |

---

## 1  Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart shell or source the profile to add uv to PATH
```

---

## 2  Install system dependencies

### 2.1  GStreamer

```bash
sudo apt update
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev
```

### 2.2  PyGObject build dependencies

PyGObject is installed by `uv sync` but it needs these system headers first:

```bash
sudo apt install -y \
    libgirepository1.0-dev \
    libglib2.0-dev \
    pkg-config \
    python3-dev
```

> **Ubuntu version note:**
> `pyproject.toml` pins `PyGObject>=3.44,<3.50` for Ubuntu 22.04 compatibility
> (PyGObject 3.50+ requires `libgirepository-2.0-dev`, only available on Ubuntu 24.04+).
> If you are on Ubuntu 24.04 or later, change the pin to `PyGObject>=3.50`
> and install `libgirepository-2.0-dev` instead of `libgirepository1.0-dev`.

### 2.3  Additional tools

```bash
sudo apt install -y ffmpeg
```

---

## 3  Install tiscamera (The Imaging Source camera driver)

> **This is the step most likely to differ between users.**  
> The tiscamera libraries must be installed **system-wide** (they land in `/lib/`
> and `/usr/lib/`).  They are **not** a Python package and cannot be installed
> via `pip` or `uv`.

### 3.1  Download the correct version

The project uses **tiscamera 1.1.0** (confirmed by `/lib/libtcam.so.1.1.0`).

Download the matching `.deb` package from the releases page:

```
https://github.com/TheImagingSource/tiscamera/releases
```

Look for a file named like:
```
tiscamera_1.1.0_amd64_ubuntu_2204.deb
```
(exact filename varies; match your Ubuntu version and architecture).

### 3.2  Install the package

```bash
sudo dpkg -i tiscamera_1.1.0_amd64_ubuntu_2204.deb
sudo apt-get install -f   # fix any missing dependencies
```

### 3.3  Verify the installation

```bash
# GStreamer plugin should be found
gst-inspect-1.0 tcambin

# GI typelib should exist
ls /usr/lib/x86_64-linux-gnu/girepository-1.0/Tcam-1.0.typelib
```

Both commands must succeed before proceeding.

### 3.4  Troubleshooting tiscamera

**`gst-inspect-1.0 tcambin` fails after install**

The tiscamera GStreamer plugins might be installed in a non-standard path.
Check:

```bash
find /usr /opt /lib -name "libgst*tcam*" 2>/dev/null
```

If plugins are found in a path not in `GST_PLUGIN_PATH`, add it:

```bash
# Add to ~/.bashrc or /etc/environment
export GST_PLUGIN_PATH=/path/to/tcam/plugins:$GST_PLUGIN_PATH
```

**`import gi; gi.require_version("Tcam","1.0")` raises `ValueError`**

The typelib was installed but the GI repository path is wrong.  Check:

```bash
find / -name "Tcam-1.0.typelib" 2>/dev/null
```

If it is not in `/usr/lib/x86_64-linux-gnu/girepository-1.0/`, add its
directory to `GI_TYPELIB_PATH`:

```bash
export GI_TYPELIB_PATH=/path/to/typelib/dir:$GI_TYPELIB_PATH
```

**Camera not detected**

Ensure the camera is plugged in via USB 3 and:

```bash
python3 -c "
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst
Gst.init(None)
m = Gst.DeviceMonitor.new()
m.add_filter('Video/Source/tcam')
for d in m.get_devices():
    print(d.get_properties().get_string('serial'))
"
```

At least one serial number should be printed.

---

## 4  Clone and set up the project

```bash
git clone <repo-url> multimaze_recorder
cd multimaze_recorder

# Create the virtual environment and install all Python dependencies
uv sync

# Verify the installation
uv run pytest tests/test_system_deps.py -v
```

A fully passing `test_system_deps.py` means all dependencies are correctly installed.

---

## 5  Configure for your setup

Edit `src/multimaze_recorder/gui/config/experiments.json` to match your
server paths and experiment types.

Key environment variables (set in `~/.bashrc` or `/etc/environment`):

| Variable | Default | Description |
|---|---|---|
| `MMRECORDER_LOCAL_PATH` | `~/Videos` | Where raw images are saved locally |
| `MMRECORDER_DATA_PATH` | `/mnt/upramdya_data/MD/` | Lab server data root |
| `MMRECORDER_USER` | `MD` | User identifier for paths |
| `MMRECORDER_REMOTE_HOST` | `mmrecorder` | Hostname of the recording workstation |
| `MMRECORDER_SERIAL_PORT` | `/dev/ttyACM0` | Arduino serial port |

---

## 6  Run the GUI

```bash
./RunGUI.sh
# or equivalently:
uv run mmrecorder
```

---

## 7  Run the tests

```bash
# System dependency checks (run on any new installation)
uv run pytest tests/test_system_deps.py -v

# Unit tests (no hardware required)
uv run pytest tests/test_camera.py tests/test_utilities.py tests/test_settings.py -v

# All tests
uv run pytest -v
```

---

## Notes on multi-user setups

The tiscamera `.deb` installs libraries to `/lib/` and `/usr/lib/` — both
accessible to all system users.  The Python package installed via `uv sync` is
per-checkout.  A second user only needs to:

1. Clone the repo (or access the shared clone).
2. Run `uv sync` in their checkout.
3. Ensure environment variables point to their own paths if different.

No admin rights are needed after the initial tiscamera `.deb` install.

### GStreamer plugin not found for a second user on the same machine

If the typelib exists (`ls /usr/lib/x86_64-linux-gnu/girepository-1.0/Tcam-1.0.typelib`
succeeds) but `gst-inspect-1.0 tcambin` still fails with "No such element or
plugin", the tiscamera GStreamer plugin `.so` is installed outside GStreamer's
default scan path.  Each user needs `GST_PLUGIN_PATH` pointing to it.

**Step 1 — find the plugin:**

```bash
find /usr /opt /lib -name "libgst*tcam*" 2>/dev/null
```

A typical result is something like:
```
/usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgsttcam.so
```

**Step 2 — add the directory to the new user's environment:**

```bash
# Replace the path below with the directory from Step 1
echo 'export GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0:$GST_PLUGIN_PATH' >> ~/.bashrc
source ~/.bashrc
```

**Step 3 — verify:**

```bash
gst-inspect-1.0 tcambin
```
