# multimaze_recorder

Tools to operate a high-throughput behavioural recording setup using an Imaging Source camera, with a PyQt6 GUI for experiment management and data processing.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)
- tiscamera 1.1.0 (system package — see [INSTALL.md](INSTALL.md))
- GStreamer 1.x (system package)

See [INSTALL.md](INSTALL.md) for the full installation walkthrough.

## Quick start

```bash
# 1. Install system dependencies (once per machine — see INSTALL.md)

# 2. Clone the repo and install the Python package
git clone <repo-url> multimaze_recorder
cd multimaze_recorder
uv sync

# 3. Launch the GUI
./RunGUI.sh
# or: uv run mmrecorder
```

## Repository layout

```
multimaze_recorder/
├── src/multimaze_recorder/     # Python package (src layout)
│   ├── camera/
│   │   └── tis.py              # TIS camera wrapper (GStreamer/tcambin)
│   ├── gui/
│   │   ├── main.py             # Entry point → MainWindow
│   │   ├── experiment_window.py
│   │   ├── processing_window.py
│   │   ├── settings.py
│   │   ├── widgets.py
│   │   └── config/             # Presets, metadata templates, experiments list
│   ├── processing/             # Post-processing pipeline modules
│   │   ├── array_to_*.py       # Image cropping (arenas, corridors, F1 tracks)
│   │   ├── images_to_videos.py
│   │   ├── recombine_videos.py
│   │   ├── check_videos.py
│   │   ├── tracker_f1.py       # SLEAP-based tracking (requires --extra tracking)
│   │   └── ...
│   ├── scripts/
│   │   ├── snap.py             # Software-triggered capture
│   │   ├── trigger.py          # Hardware (Arduino) triggered capture
│   │   └── livestream.py       # Live preview
│   └── utilities.py
├── arduino/
│   └── ImageCapture_Trigger.ino   # Arduino sketch for hardware triggering
├── examples/                   # Standalone usage examples
├── notebooks/                  # Exploratory / diagnostic notebooks
├── tests/                      # pytest suite (unit + system-dep checks)
├── processing_commands/        # Shell script wrappers + YAML workflow configs
├── motor_control/              # Motor control (student code; canonical + old/ backups)
├── pyproject.toml
├── INSTALL.md
└── RunGUI.sh
```

## CLI entry points

After `uv sync`, the following commands are available:

**Recording**

| Command | Description |
|---|---|
| `mmrecorder` | Launch the full GUI |
| `mmrecorder-snap` | Software-triggered image capture |
| `mmrecorder-trigger` | Hardware-triggered image capture (Arduino) |
| `mmrecorder-livestream` | Live camera preview |

**Processing** (`uv sync` is enough; tracking commands also need `uv sync --extra tracking`)

| Command | Description |
|---|---|
| `mmrecorder-crop-arenas` | Crop standard multi-maze arenas |
| `mmrecorder-crop-corridors` | Crop corridor arenas |
| `mmrecorder-crop-f1` | Crop F1-track arenas |
| `mmrecorder-crop-h-corridors` | Crop horizontal corridor arenas |
| `mmrecorder-images-to-videos` | Convert cropped images to videos |
| `mmrecorder-check-videos` | Validate video integrity and duration |
| `mmrecorder-check-process` | Verify cropped folders, rename → *_Checked |
| `mmrecorder-recombine` | Recombine Left/Right video pairs |
| `mmrecorder-batch-recombine` | Batch recombine from YAML list |
| `mmrecorder-verify-processed` | Visual verification of processed experiments |
| `mmrecorder-verify-cropping` | Check that F1-track cropping completed |
| `mmrecorder-batch-verify` | Batch verify from YAML list |
| `mmrecorder-track-f1` | SLEAP-based tracking for F1 experiments |
| `mmrecorder-assign-ball-id` | Reassign consistent ball IDs from SLEAP files |
| `mmrecorder-check-tracks` | Rename *_Checked → *_Tracked when all files present |
| `mmrecorder-test-arenas` | Visual test of arena recombination |
| `mmrecorder-test-recombine` | Interactive test of video recombination |
| `mmrecorder-boundaries` | Detect arena boundaries from tracked videos |

The `processing_commands/` directory also contains shell script wrappers (`MakeVideos.sh`, `ProcessImages.sh`, etc.) for common pipeline steps, plus YAML files listing experiments for batch operations.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MMRECORDER_LOCAL_PATH` | `~/Videos` | Where recordings are saved; also the default input for processing |
| `MMRECORDER_DATA_PATH` | `~/Videos` | Root for the data browser in the GUI |
| `MMRECORDER_SERIAL_PORT` | `/dev/ttyACM0` | Arduino serial port |
| `MMRECORDER_PRESETS` | package default | Path to camera preset JSON |
| `MMRECORDER_REMOTE_HOST` | — | SSH host for remote data sync |
| `MMRECORDER_F1_DATA_PATH` | `/mnt/upramdya_data/MD/F1_Tracks/Videos` | Root for F1-track video data |
| `MMRECORDER_SLEAP_MODEL_BALL_CENTROID` | hardcoded default | SLEAP centroid model for ball tracking |
| `MMRECORDER_SLEAP_MODEL_BALL_CENTERED` | hardcoded default | SLEAP centered-instance model for ball tracking |
| `MMRECORDER_SLEAP_MODEL_FLY` | hardcoded default | SLEAP model for fly tracking |

## Running tests

```bash
# System dependency checks (run first on a new install)
uv run pytest tests/test_system_deps.py -v

# Full unit test suite (no hardware required)
uv run pytest
```

## GUI — metadata registry

Known variables are always pre-populated in the metadata table. They can be deleted before saving and won't appear in the final `metadata.json`. This is intentional:

1. Reduces syntax errors (e.g. "Date" vs "date") by surfacing the canonical key.
2. When an older folder is opened after a new variable is added, it appears in the table as a reminder that the field may need backfilling.

## Arduino hardware trigger

The sketch in `arduino/ImageCapture_Trigger.ino` receives fps and duration over serial, then pulses the camera's optocoupler input accordingly. Connect the Arduino before launching `mmrecorder-trigger`.
