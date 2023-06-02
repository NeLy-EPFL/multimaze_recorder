import sys
import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
import json
from collections import namedtuple
import TIS
import threading
import os
import math
import gi
gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")

from gi.repository import GLib, Gst, Tcam
#os.environ['GST_DEBUG'] = '3'


presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"

# Video parameters

duration = 20

fps = 30

timeout = 1 / fps

#timeout = math.floor(timeout * 1000) / 1000

folder = Path("/home/matthias/Videos/Test_Htrigger/")

# Cropping parameters

Left = 250
Top = 0
Right = 3850
Bottom = 3000


class CustomData:
    """Example class for user data passed to the on new image callback function
    It is used for an image counter only. Also for a busy flag, so the callback
    is not called, while a previons callback call is still active.
    """

    def __init__(self, image):
        self.imagecounter = 0
        self.image = image
        self.busy = False


def on_new_image(tis, userdata, folder=folder):
    """
    Callback function, which will be called by the TIS class
    :param tis: the camera TIS class, that calls this callback
    :param userdata: This is a class with user data, filled by this call.
    :return:
    """
    # Avoid being called, while the callback is busy
    if userdata.busy is True:
        return

    userdata.busy = True
    framestart = time.perf_counter()
    userdata.image = tis.get_image()
    frame = tis.get_image()

    # Doing a sample image processing
    userdata.imagecounter += 1
    filename = folder.joinpath("image" + str(userdata.imagecounter) + ".jpg").as_posix()
    image = Image.fromarray(np.squeeze(frame), mode="L")

    image = image.crop((Left, Top, Right, Bottom))

    # Save image in a separate thread
    threading.Thread(target=image.save, args=(filename,), daemon=True).start()

    framestop = time.perf_counter()
    print(
        f"Image {userdata.imagecounter} saved. Time: {framestop - framestart:0.4f} seconds"
    )
    small_image = cv2.resize(frame, (640, 480))
    cv2.imshow("Window", small_image)
    cv2.waitKey(1)
    
    displaystop = time.perf_counter()
    
    print(f"Display time: {displaystop - framestop:0.4f} seconds")

    userdata.busy = False


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

# Create an instance of the CustomData class
CD = CustomData(None)

# Set the callback function
Tis.set_image_callback(on_new_image, CD)

Tis.set_property("TriggerMode", "On")

# Main loop triggering images at 1/fps Hz
count = 0

programstart = time.perf_counter()
while count < duration * fps:
    triggerstart = time.perf_counter()
    Tis.execute_command("TriggerSoftware")  # Send a software trigger
    time.sleep(timeout)
    count += 1
    triggerstop = time.perf_counter()
    print(f"Trigger time: {triggerstop - triggerstart:0.4f} seconds")
programstop = time.perf_counter()
print(f"Programm duration: {programstop - programstart:0.4f} seconds")

Tis.stop_pipeline()
print("Program end")
