"""Snap-based (software-triggered) image recorder."""

import cv2
import numpy as np
import time
import os
import sys
from pathlib import Path
from PIL import Image
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from multimaze_recorder.utilities import configure_camera, create_thumbnail, update_progress_bar

LOCAL_PATH = Path(os.environ.get("MMRECORDER_LOCAL_PATH", Path.home() / "Videos"))


class Recorder:
    def __init__(self, presets):
        self.presets = presets
        self.camera_configs = self._load_camera_configs()
        self.cropping = self.camera_configs["cropping"]
        self.left, self.top, self.right, self.bottom = self.cropping.values()
        self.tis = configure_camera(self.presets)
        self.dot_state = False
        self.last_toggle_time = time.perf_counter()
        self.executor = ThreadPoolExecutor(max_workers=5)

    def _load_camera_configs(self):
        with open(self.presets) as f:
            return json.load(f)

    def _save_image(self, image, filename):
        image.save(filename)

    def record(self, folder_name, fps, duration):
        folder = LOCAL_PATH / folder_name
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
                    filename = folder / f"image{count}.jpg"
                    image = Image.fromarray(np.squeeze(frame), mode="L")
                    image = image.crop((self.left, self.top, self.right, self.bottom))
                    self.executor.submit(self._save_image, image, str(filename))

                    thumbnail, self.dot_state, self.last_toggle_time = create_thumbnail(
                        frame, self.dot_state, self.last_toggle_time
                    )
                    cv2.imshow("Maze Recorder", thumbnail)
                    cv2.waitKey(1)

                    count += 1

        self.executor.shutdown(wait=True)
        print(f"Captured {count} frames in {time.perf_counter() - start:0.4f} seconds")
        folder.rename(folder.parent / (folder.name + "_Recorded"))
        print("Program ends")


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} FOLDERNAME FPS DURATION PRESETS")
        sys.exit(1)

    folder_name = sys.argv[1]
    fps = int(sys.argv[2])
    duration = int(sys.argv[3])
    presets = sys.argv[4]

    recorder = Recorder(presets)
    recorder.record(folder_name, fps, duration)


if __name__ == "__main__":
    main()
