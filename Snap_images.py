import cv2
import numpy as np
import time
from pathlib import Path
from PIL import Image
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from Utilities import *

# Better commenting and function documentation

class Recorder:
    def __init__(self, presets):
        self.presets = presets
        self.camera_configs = self.load_camera_configs()
        self.cropping = self.camera_configs["cropping"]
        self.left, self.top, self.right, self.bottom = self.cropping.values()
        self.tis = configure_camera(self.presets)
        self.dot_state = False
        self.last_toggle_time = time.perf_counter()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def load_camera_configs(self):
        with open(self.presets) as jsonFile:
            camera_configs = json.load(jsonFile)
        return camera_configs
    
    def save_image(self, image, filename):
        image.save(filename)

    def record(self, folder_name, fps, duration):
        folder = Path("/home/matthias/Videos/").joinpath(folder_name)
        folder.mkdir(parents=True, exist_ok=True)
        count = 0
        timeout = 1 / fps
        
        time.sleep(2)

        with tqdm(total=duration, desc="Progress", bar_format="{l_bar}{bar}") as pbar:
            start = time.perf_counter()
            last_update = start
            while count < duration * fps:
                if self.tis.snap_image(timeout):
                    if time.perf_counter() - last_update >= 1:
                        update_progress_bar(pbar, start, duration)
                        last_update = time.perf_counter()

                    frame = self.tis.get_image()
                    filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
                    image = Image.fromarray(np.squeeze(frame), mode="L")
                    image = image.crop((self.left, self.top, self.right, self.bottom))
                    future = self.executor.submit(self.save_image, image, filename)

                    thumbnail, self.dot_state, self.last_toggle_time = create_thumbnail(frame, self.dot_state, self.last_toggle_time)
                    cv2.imshow("Maze Recorder", thumbnail)
                    cv2.waitKey(1)

                    count += 1
                    
        recorder.executor.shutdown(wait=True)
        
        print(f"Captured {count} frames in {time.perf_counter() - start:0.4f} seconds")
        folder.rename(folder.parent.joinpath(folder.name + "_Recorded"))
        print("Program ends")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} FOLDERNAME FPS DURATION")
        sys.exit(1)

    folder_name = sys.argv[1]
    fps = int(sys.argv[2])
    duration = int(sys.argv[3])
    presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"

    recorder = Recorder(presets)
    recorder.record(folder_name, fps, duration)