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
    
folder = Path("/home/matthias/Videos/Test/")
    
Tis.set_property("location", folder.joinpath("video.mp4").as_posix())

Tis._create_pipeline(conversion= "mp4mux -e !", showvideo=True)

Tis.start_pipeline()

time.sleep(5)

Tis.stop_pipeline()


