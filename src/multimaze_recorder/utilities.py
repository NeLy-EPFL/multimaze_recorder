import sys
import cv2
import time
try:
    from tqdm import tqdm
except Exception:
    tqdm = None
import json
from multimaze_recorder.camera import tis as TIS_module


def progress(count, total, status=""):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    sys.stdout.write("[%s] %s%s ...%s\r" % (bar, percents, "%", status))
    sys.stdout.flush()


def create_thumbnail(frame, dot_state, last_toggle_time):
    thumbnail = cv2.resize(frame, (640, 480))
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_GRAY2RGB)

    if dot_state:
        cv2.circle(thumbnail, (20, 20), 15, (0, 0, 255), -1)

    current_time = time.perf_counter()
    if current_time - last_toggle_time >= 0.5:
        dot_state = not dot_state
        last_toggle_time = current_time

    return thumbnail, dot_state, last_toggle_time


def update_progress_bar(pbar, start_time, total_time):
    elapsed_time = int(time.perf_counter() - start_time)
    if elapsed_time > pbar.n:
        pbar.update(elapsed_time - pbar.n)

    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    total_hours, total_remainder = divmod(total_time, 3600)
    total_minutes, total_seconds = divmod(total_remainder, 60)
    pbar.set_description(
        f"Recording time: {hours:02}:{minutes:02}:{seconds:02}/"
        f"{total_hours:02}:{total_minutes:02}:{total_seconds:02}"
    )


def configure_camera(presets, hardware_trigger=False):
    """Configure and return a TIS camera from a presets JSON file."""
    with open(presets) as jsonFile:
        cameraconfigs = json.load(jsonFile)

    fmt = cameraconfigs["format"]

    Tis = TIS_module.TIS(cameraconfigs["properties"])
    Tis.open_device(
        fmt["serial"],
        fmt["width"],
        fmt["height"],
        fmt["framerate"],
        TIS_module.SinkFormats.GRAY8,
        False,
    )

    Tis.start_pipeline()
    time.sleep(2)
    Tis.applyProperties()

    camera = Tis.get_source()

    if hardware_trigger:
        Tis.set_property("TriggerMode", "On")
        Tis.set_property("TriggerActivation", "Rising Edge")
    state = camera.get_property("tcam-properties-json")

    print(f"State of device is:\n{state}")

    return Tis
