import sys
import cv2
import numpy as np
from tqdm import tqdm
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
from Utilities import *


gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")

from gi.repository import GLib, Gst, Tcam

# os.environ['GST_DEBUG'] = '3'

import serial

# Open the serial port
ser = serial.Serial("/dev/ttyACM0", 9600)

# Close and reopen the serial port to reset the Arduino
ser.close()
time.sleep(2)  # Wait for the Arduino to reset
ser.open()

# Wait for acknowledgment from Arduino
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode("utf-8").rstrip()
        if line == "Arduino Ready":
            print("Arduino connection established")
            break

presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"

# Load camera configs
with open(presets) as jsonFile:
    cameraconfigs = json.load(jsonFile)

LocalPath = Path("/home/matthias/Videos/")
RemotePath = Path(
    "/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/"
)

# Parse command-line arguments
if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} FOLDERNAME")
    sys.exit(1)

FolderName = sys.argv[1]
fps = int(sys.argv[2])
duration = int(sys.argv[3])

folder = LocalPath.joinpath(FolderName)
folder.mkdir(parents=True, exist_ok=True)

# Extract cropping parameters
cropping = cameraconfigs["cropping"]
Left, Top, Right, Bottom = cropping.values()


class CustomData:
    """Example class for user data passed to the on new image callback function
    It is used for an image counter only. Also for a busy flag, so the callback
    is not called, while a previons callback call is still active.
    """

    def __init__(self, image):
        self.imagecounter = 0
        self.image = image
        self.busy = False
        self.dot_state = False
        self.last_toggle_time = time.perf_counter()


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
    # framestart = time.perf_counter()
    userdata.image = tis.get_image()
    frame = tis.get_image()

    # Doing a sample image processing
    userdata.imagecounter += 1
    filename = folder.joinpath("image" + str(userdata.imagecounter) + ".jpg").as_posix()
    image = Image.fromarray(np.squeeze(frame), mode="L")

    image = image.crop((Left, Top, Right, Bottom))

    # Save image in a separate thread
    threading.Thread(target=image.save, args=(filename,), daemon=True).start()

    thumbnail, userdata.dot_state, userdata.last_toggle_time = create_thumbnail(
        frame, userdata.dot_state, userdata.last_toggle_time
    )

    cv2.imshow("Maze Recorder", thumbnail)
    cv2.waitKey(1)

    userdata.busy = False


# Configure the camera
Tis = configure_camera(presets, hardware_trigger=True)

# Create an instance of the CustomData class
CD = CustomData(None)

# Set the callback function
Tis.set_image_callback(on_new_image, CD)

# Send start command and fps and duration values together
ser.write(f"start\n".encode("utf-8"))
time.sleep(0.2)
ser.write(f"{fps}*".encode("utf-8"))
time.sleep(0.2)
ser.write(f"{duration}*".encode("utf-8"))
print("Commands sent to Arduino, waiting for acknowledgment...")
time.sleep(0.2)

ack_received = False
start_time = time.time()
arduino_output = []
while not ack_received:
    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8")
        arduino_output.append(line)
        ack_received = True
    if time.time() - start_time > 10:  # Timeout after 10 seconds
        raise Exception("No acknowledgment received from Arduino")
    else:
        time.sleep(0.1)  # Sleep for a short time to avoid busy waiting

print(
    f"Acknowledgment received from Arduino: {''.join(arduino_output)}\n starting recording."
)


# Create a loop to display progress and wait for the program to finish
with tqdm(total=duration, desc="Progress", bar_format="{l_bar}{bar}") as pbar:
    start = time.perf_counter()
    last_update = start
    while True:
        # Wait for Arduino to send "done" message
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").rstrip()
            if line == "done":
                break

        current_time = time.perf_counter()
        # Update the progress bar every second
        if current_time - last_update >= 1:
            update_progress_bar(pbar, start, duration)
            last_update = current_time

programstop = time.perf_counter()
print(f"Program duration: {programstop - start:0.4f} seconds")
print(f"Saved {CD.imagecounter} images")

Tis.stop_pipeline()

# Rename the folder with '_Recorded' suffix to tag it as a recorded folder
folder.rename(folder.parent.joinpath(folder.name + "_Recorded"))

ser.close()
print("Program end")