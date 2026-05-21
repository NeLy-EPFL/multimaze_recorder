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

**Start here: check which GStreamer is active**

Many failures below share the same symptom (`undefined symbol` warnings or
`No such element or plugin 'tcambin'`) but have different root causes.
Run this first to orient yourself:

```bash
which gst-inspect-1.0      # should be /usr/bin/gst-inspect-1.0
gst-inspect-1.0 --version  # should match: apt-cache policy libgstreamer1.0-0
```

---

**conda or miniconda is shadowing system GStreamer**

This is the most common cause on a shared workstation where conda is installed.
Conda ships its own older GStreamer (typically 1.22.x) which takes priority over
the system version (1.24.x on Ubuntu 24.04).  The tiscamera plugin is compiled
against the system GStreamer and will fail under the conda one — either with
`undefined symbol` errors or silently as `No such element or plugin`.

If `which gst-inspect-1.0` points to a conda path (e.g. `~/miniconda3/...`),
confirm with the system binary:

```bash
/usr/bin/gst-inspect-1.0 tcambin
```

If that succeeds, conda is the culprit.  To fix it permanently, remove the
`conda initialize` block from your `~/.bashrc`:

```bash
# Find and delete the block between these two lines:
# >>> conda initialize >>>
# <<< conda initialize <<<
```

Then open a fresh terminal and verify `which gst-inspect-1.0` now returns
`/usr/bin/gst-inspect-1.0`.

---

**`undefined symbol` warnings — Ubuntu version mismatch in the .deb**

If conda is not involved but you still see `undefined symbol` errors, the `.deb`
was compiled against a different Ubuntu version than the one installed.

Check:

```bash
lsb_release -a
dpkg -l | grep tiscamera
```

If the `.deb` variant does not match (e.g. `ubuntu_2404` build on a 22.04 machine),
reinstall the correct one:

```bash
sudo dpkg -r tiscamera
# Download the matching .deb from https://github.com/TheImagingSource/tiscamera/releases
sudo dpkg -i tiscamera_1.1.0_amd64_ubuntu_XXXX.deb
sudo apt-get install -f
```

---

**`gst-inspect-1.0 tcambin` fails — plugin installed in a non-standard path**

If there are no symbol errors but `tcambin` is still not found, the plugin `.so`
may not be in GStreamer's default scan path.  Check where it landed:

```bash
find /usr /opt /lib -name "libgst*tcam*" 2>/dev/null
```

If it is not in `/usr/lib/x86_64-linux-gnu/gstreamer-1.0/`, add the directory to
your `~/.bashrc`:

```bash
export GST_PLUGIN_PATH=/path/to/tcam/plugins:$GST_PLUGIN_PATH
source ~/.bashrc
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
# --extra dev adds pytest and related test tools
uv sync --extra dev

# Verify the installation
uv run pytest tests/test_system_deps.py -v
```

A fully passing `test_system_deps.py` means all dependencies are correctly installed.

---

## 5  Configure for your setup

The easiest way to configure the application is through the **Settings tab** in the
GUI itself.  Settings are saved to `~/.config/mmrecorder/settings.json` and persist
across sessions.  The fields are described below.

### 5.1  User initials

Your user identifier — 2 to 4 capital letters (e.g. `MD`, `VLR`, `TKL`).  The GUI
scans the lab server for existing user directories and lists them in a dropdown.  If
you are setting up for the first time, type your initials directly.

### 5.2  Data path (lab server)

The full path to your data folder on the lab server, **including your user directory**.

The lab server is mounted at one of two locations depending on the workstation:

| Mount point | Notes |
|---|---|
| `/mnt/upramdya_data` | Most workstations |
| `/mnt/upramdya/data` | Some older setups |

So the data path is typically `/mnt/upramdya_data/MD/` (replace `MD` with your
initials).  If you are not in the lab, point this to any local folder.

The GUI will warn you at startup if the path looks like a lab server path but the
server is not mounted — useful if you forgot to mount it before launching.

### 5.3  Local path

Where raw images are saved on this machine during recording.  Default: `~/Videos`.
This folder is on the recording workstation's local disk and gets synced to the
server after recording.

### 5.4  Remote host

The SSH hostname of the recording workstation — the machine physically connected
to the cameras.  This is used to detect whether the GUI is running locally (on that
machine) or remotely (on another computer accessing it over the network).

- If you are running from the recording workstation itself, this must match the
  machine's hostname (`hostname` in a terminal tells you what it is).
- If you are running remotely, this must be a name that resolves over SSH — either
  the workstation's network hostname, or an alias defined in `/etc/hosts` or
  `~/.ssh/config`.

Example: if the workstation is called `mmrecorder`, set this to `mmrecorder`.  You
can verify SSH connectivity with `ssh mmrecorder echo ok`.

### 5.5  Serial port

The port the Arduino is connected to for hardware-triggered recording.  Usually
`/dev/ttyACM0` on Linux.  Click **Refresh** in the Settings tab to list all
currently connected ports.

If no ports appear:
- Make sure the Arduino is plugged in, then click Refresh.
- If it still doesn't appear, your user may not be in the `dialout` group:

```bash
sudo usermod -aG dialout $USER   # then log out and back in
```

### 5.6  Environment variable overrides

Settings saved in the GUI can be overridden by environment variables if needed
(useful for scripting or CI).  Variables take priority over the saved config file.

| Variable | Default | Description |
|---|---|---|
| `MMRECORDER_USER` | `MD` | User initials |
| `MMRECORDER_LOCAL_PATH` | `~/Videos` | Local recording path |
| `MMRECORDER_DATA_PATH` | `/mnt/upramdya_data/<user>/` | Lab server data path |
| `MMRECORDER_REMOTE_HOST` | `mmrecorder` | SSH hostname of recording workstation |
| `MMRECORDER_SERIAL_PORT` | `/dev/ttyACM0` | Arduino serial port |

---

## 6  Run the GUI

```bash
./RunGUI.sh
# or equivalently:
uv run mmrecorder
```

---

## 6.1  Create a desktop shortcut (optional)

Run once after `uv sync` to install a launcher icon:

```bash
./install_desktop.sh
```

This places a `.desktop` entry in `~/.local/share/applications/` (visible in the
app menu) and, if a `~/Desktop` folder exists, also puts a clickable icon there.
Each user on the workstation runs this once from their own checkout.

> **GNOME note:** if the Desktop icon shows a plain file instead of launching,
> right-click it and choose **Allow Launching**.

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
