import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
import json
import TIS
from Utilities import *
import sys
import threading


# os.environ['GST_DEBUG'] = '3' # Uncomment this line to see detailed debug information for the Gstreamer pipeline

# Parse command-line arguments
if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} FOLDERNAME FPS DURATION")
    sys.exit(1)

FolderName = sys.argv[1]
fps = int(sys.argv[2])
duration = int(sys.argv[3])

# Record images
timeout = 1 / fps

total = duration * fps

LocalPath = Path("/home/matthias/Videos/")
RemotePath = Path("/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/")

presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"
folder = LocalPath.joinpath(FolderName)
folder.mkdir(parents=True, exist_ok=True)

# Create arena and corridor folders
#print('Creating remote folders...')
#arenas_folder = RemotePath.joinpath(folder.name)
#arenas_folder.mkdir(parents=True, exist_ok=True)
#for arena in range(1, 10):
#    arena_folder = arenas_folder.joinpath(f"arena{arena}")
#    arena_folder.mkdir(parents=True, exist_ok=True)
#    for corridor in range(1, 7):
#        corridor_folder = arena_folder.joinpath(f"corridor{corridor}")
#        corridor_folder.mkdir(parents=True, exist_ok=True)

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

# Initialize the dot_state variable
dot_state = False
last_toggle_time = time.perf_counter()

start = time.perf_counter()
while count < duration * fps:
    if Tis.snap_image(timeout):
        
        frame = Tis.get_image()

        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = Image.fromarray(np.squeeze(frame), mode="L")

        image = image.crop((Left, Top, Right, Bottom))
        threading.Thread(target=image.save, args=(filename,), daemon=True).start()

        # thumbnail = cv2.resize(frame, (640, 480))
        # # Draw a blinking red dot on the top left corner of the thumbnail image
        # if dot_state:
        #     cv2.circle(thumbnail, (10, 10), 5, (0, 0, 255), -1)

        # # Check if enough time has elapsed since the last toggle
        # current_time = time.perf_counter()
        # if current_time - last_toggle_time >= 0.5:
        #     # Toggle the dot_state variable
        #     dot_state = not dot_state
        #     # Update the last_toggle_time variable
        #     last_toggle_time = current_time

        # cv2.imshow("Maze Recorder", thumbnail)
        # cv2.waitKey(1)
        
        thumbnail = thumbnail(frame, last_toggle_time, dot_state)
        
        cv2.imshow("Maze Recorder", thumbnail)
        cv2.waitKey(1)

        count += 1
        progress(count, total, status='Recording')

stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()

# Rename the folder with '_Recorded' suffix to tag it as a recorded folder
folder.rename(folder.parent.joinpath(folder.name + "_Recorded"))

print("Program ends")

# TODO: Make the dot red
# TODO: prooftest the code speed and all