import sys
import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
import json

# sys.path.append("../python-common")
import TIS

presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"

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
    True,
)

Tis.start_pipeline()
Tis.applyProperties()

camera = Tis.get_source()
state = camera.get_property("tcam-properties-json")
print(f"State of device is:\n{state}")

# Record images
duration = 15

fps = 30

count = 0
timeout = 1 / fps

folder = Path("/home/matthias/Videos/Test/")

time.sleep(2)

start = time.perf_counter()
while count < duration * fps:
    if Tis.snap_image(timeout):  # Snap an image with one second timeout
        image = Tis.get_image()  # Get the image. It is a numpy array
        # print("Image ", image.shape, image.dtype)
        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = np.reshape(image, (3000, 4096))
        # crop image to only keep the center part of the width
        image = image[100:2900, 300:3700]
        im = Image.fromarray(image, mode="L")
        im.save(filename)
        # cv2.imwrite(filename, image)
        # time.sleep(timeout)
        count += 1

stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()
print("Program ends")
