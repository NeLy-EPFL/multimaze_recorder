"""Example: software-triggered image capture using a preset config."""

import cv2
import numpy as np
import time
import sys
from pathlib import Path

from multimaze_recorder.utilities import configure_camera
from multimaze_recorder.camera.tis import SinkFormats

# Default to the package's standard preset; override via command-line arg
_DEFAULT_PRESETS = (
    Path(__file__).parent.parent
    / "src" / "multimaze_recorder" / "gui" / "config" / "Presets" / "standard_set.json"
)
presets = sys.argv[1] if len(sys.argv) > 1 else str(_DEFAULT_PRESETS)


class CustomData:
    def __init__(self):
        self.newImageReceived = False
        self.image = None
        self.busy = False


def on_new_image(tis, userdata):
    if userdata.busy:
        return
    userdata.busy = True
    userdata.newImageReceived = True
    userdata.image = tis.get_image()
    userdata.busy = False


CD = CustomData()
Tis = configure_camera(presets)
Tis.set_image_callback(on_new_image, CD)
Tis.set_property("TriggerMode", "On")
Tis.start_pipeline()

duration = 5
fps = 30
timeout = 1 / fps
folder = Path("./trigger_output")
folder.mkdir(exist_ok=True)

cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
start = time.perf_counter()
count = 0

while count < duration * fps:
    Tis.execute_command("TriggerSoftware")
    tries = 10
    while not CD.newImageReceived and tries > 0:
        time.sleep(timeout)
        tries -= 1

    if CD.newImageReceived:
        CD.newImageReceived = False
        filename = str(folder / f"image{count:04}.jpg")
        cv2.imshow("Window", CD.image)
        cv2.imwrite(filename, CD.image)
        count += 1
    else:
        print("No image received")

stop = time.perf_counter()
print(f"Captured {count} frames in {stop - start:0.4f} seconds")

Tis.stop_pipeline()
cv2.destroyAllWindows()
print("Program ends")
