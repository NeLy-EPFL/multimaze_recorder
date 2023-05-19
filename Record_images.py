import sys
import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image

#sys.path.append("../python-common")

import TIS

# This sample shows, how to get an image and convert it to OpenCV
# needed packages:
# pyhton-opencv
# pyhton-gst-1.0
# tiscamera


Tis = TIS.TIS()

Tis.open_device("39220254",4096, 3000, "30/1", TIS.SinkFormats.GRAY8, True)

# the camera with serial number 39220254 uses a 4096x3000 video format at 30 fps and the image is converted to
# GRAY8.
# True means whether the live view is shown or not.

# The next line is for selecting a device, video format and frame rate.
#if not Tis.select_device():
#    quit(0)

# Just in case trigger mode is enabled, disable it.
try:
    Tis.set_property("TriggerMode", "Off")
except Exception as error:
    print(error)


Tis.start_pipeline()  # Start the pipeline so the camera streams

duration = 15

fps = 30

count = 0
timeout = 1/fps

folder = Path("/home/matthias/Videos/Test/")


start = time.perf_counter()
while count < duration * fps:
    if Tis.snap_image(timeout):  # Snap an image with one second timeout    
        image = Tis.get_image()  # Get the image. It is a numpy array
        print("Image ", image.shape, image.dtype)
        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = np.reshape(image, (3000, 4096))
        im = Image.fromarray(image, mode="L")
        im.save(filename) 
        #cv2.imwrite(filename, image)
        #time.sleep(timeout) 
        count += 1

stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()
print("Program ends")
