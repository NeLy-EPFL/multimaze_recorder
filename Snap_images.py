import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
import json
import TIS
from Utilities import *

# os.environ['GST_DEBUG'] = '3' # Uncomment this line to see detailed debug information for the Gstreamer pipeline


# Record images
duration = 20
fps = 30
timeout = 1 / fps

total = duration * fps

presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"
folder = Path("/home/matthias/Videos/TestShort/")

# Cropping parameters

Left = 250
Top = 0
Right = 3850
Bottom = 3000

# Camera config

with open(presets) as jsonFile:
    cameraconfigs = json.load(jsonFile)
    jsonFile.close()

format = cameraconfigs["format"]

Tis = TIS.TIS(cameraconfigs["properties"])

Tis.open_device(
    format["serial"],
    format["width"],
    format["height"],
    format["framerate"],
    TIS.SinkFormats.GRAY8,
    False,
)

Tis.start_pipeline()
Tis.applyProperties()

camera = Tis.get_source()
state = camera.get_property("tcam-properties-json")
print(f"State of device is:\n{state}")

count = 0

time.sleep(2)

start = time.perf_counter()
while count < duration * fps:
    if Tis.snap_image(timeout):
        frame = Tis.get_image()

        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = Image.fromarray(np.squeeze(frame), mode="L")

        image = image.crop((Left, Top, Right, Bottom))
        image.save(
            filename,
        )

        thumbnail = cv2.resize(frame, (640, 480))
        cv2.imshow("Maze Recorder", thumbnail)
        cv2.waitKey(1)

        count += 1
        progress(count, total, status='Recording')

stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()
print("Program ends")
