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
duration = 20

fps = 30

count = 0
timeout = 1 / fps

folder = Path("/home/matthias/Videos/TestShort/")

# Cropping parameters

Left = 250
Top = 0
Right = 3850
Bottom = 3000

time.sleep(2)

start = time.perf_counter()
while count < duration * fps:
    if Tis.snap_image(timeout):  # Snap an image with one second timeout
        image = Tis.get_image()  # Get the image. It is a numpy array
        
        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = Image.fromarray(np.squeeze(image), mode='L')
        
        image = image.crop((Left, Top, Right, Bottom))
        # image = image.resize((Width, Height), 
        #                      #Image.BICUBIC,
        #                      )
        image.save(filename,)

        count += 1

stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()
print("Program ends")
