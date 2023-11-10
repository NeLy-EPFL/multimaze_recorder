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

# Cropping parameters

with open(presets) as jsonFile:
    cameraconfigs = json.load(jsonFile)
    jsonFile.close()

# Extract cropping parameters
cropping = cameraconfigs["cropping"]
Left, Top, Right, Bottom = cropping.values()

# Configure the camera
Tis = configure_camera(presets)

count = 0

time.sleep(2)

# Initialize the dot_state variable
dot_state = False
last_toggle_time = time.perf_counter()


with tqdm(total=duration, desc="Progress", bar_format="{l_bar}{bar}") as pbar:
    start = time.perf_counter()
    last_update = start
    while count < duration * fps:
        if Tis.snap_image(timeout):
            if time.perf_counter() - last_update >= 1:
                update_progress_bar(pbar, start, duration)
                last_update = time.perf_counter()
                
            frame = Tis.get_image()

            filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
            image = Image.fromarray(np.squeeze(frame), mode="L")

            image = image.crop((Left, Top, Right, Bottom))
            threading.Thread(target=image.save, args=(filename,), daemon=True).start()
            
            thumbnail, dot_state, last_toggle_time = create_thumbnail(frame, dot_state, last_toggle_time)
            cv2.imshow("Maze Recorder", thumbnail)
            cv2.waitKey(1)

            count += 1
            

    stop = time.perf_counter()

print(f"Captured {count} frames in {stop - start:0.4f} seconds")


# Stop the pipeline and clean up
Tis.stop_pipeline()

# Rename the folder with '_Recorded' suffix to tag it as a recorded folder
folder.rename(folder.parent.joinpath(folder.name + "_Recorded"))

print("Program ends")