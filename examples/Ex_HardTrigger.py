"""Example: hardware-triggered image capture with a callback."""

import cv2
import numpy as np
import time

from multimaze_recorder.camera.tis import TIS, SinkFormats


class CustomData:
    def __init__(self):
        self.imagecounter = 0
        self.busy = False


def on_new_image(tis, userdata):
    if userdata.busy:
        return
    userdata.busy = True
    image = tis.get_image()
    kernel = np.ones((5, 5), np.uint8)
    image = cv2.erode(image, kernel, iterations=5)
    userdata.imagecounter += 1
    filename = f"./image{userdata.imagecounter:04}.jpg"
    cv2.imwrite(filename, image)
    userdata.busy = False


# Select a connected camera interactively
Tis = TIS(properties=[])
if not Tis.select_device():
    quit(0)

CD = CustomData()
Tis.set_image_callback(on_new_image, CD)
Tis.set_property("TriggerMode", "On")

try:
    Tis.set_property("BalanceWhiteAuto", "Off")
    Tis.set_property("GainAuto", "Off")
    Tis.set_property("Gain", 0)
    Tis.set_property("ExposureAuto", "Off")
    Tis.set_property("ExposureTime", 24000)
except Exception as error:
    print(error)

Tis.start_pipeline()
Tis.set_property("TriggerMode", "On")

while True:
    key = input("q : quit\nPlease enter: ")
    if key == "q":
        break

Tis.stop_pipeline()
print("Program end")
