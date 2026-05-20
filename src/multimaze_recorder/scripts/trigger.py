"""Hardware-triggered (Arduino) image recorder."""

import sys
import cv2
import numpy as np
from tqdm import tqdm
import time
import os
from pathlib import Path
from PIL import Image
import json
from concurrent.futures import ThreadPoolExecutor
import gi
import serial
from multimaze_recorder.utilities import configure_camera, create_thumbnail, update_progress_bar

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")

LOCAL_PATH = Path(os.environ.get("MMRECORDER_LOCAL_PATH", Path.home() / "Videos"))
SERIAL_PORT = os.environ.get("MMRECORDER_SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.environ.get("MMRECORDER_BAUD_RATE", "9600"))

executor = ThreadPoolExecutor(max_workers=5)


class CustomData:
    def __init__(self, image):
        self.imagecounter = 0
        self.image = image
        self.busy = False
        self.dot_state = False
        self.last_toggle_time = time.perf_counter()


def _save_image(image, filename):
    image.save(filename)


def on_new_image(tis, userdata, folder, cropping):
    if userdata.busy:
        return

    userdata.busy = True
    frame = tis.get_image()
    userdata.image = frame

    filename = folder / f"image{userdata.imagecounter}.jpg"
    image = Image.fromarray(np.squeeze(frame), mode="L")
    Left, Top, Right, Bottom = cropping.values()
    image = image.crop((Left, Top, Right, Bottom))
    executor.submit(_save_image, image, str(filename))

    thumbnail, userdata.dot_state, userdata.last_toggle_time = create_thumbnail(
        frame, userdata.dot_state, userdata.last_toggle_time
    )
    cv2.imshow("Maze Recorder", thumbnail)
    cv2.waitKey(1)

    userdata.imagecounter += 1
    userdata.busy = False


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} FOLDERNAME FPS DURATION PRESETS")
        sys.exit(1)

    folder_name = sys.argv[1]
    fps = int(sys.argv[2])
    duration = int(sys.argv[3])
    camera_settings = sys.argv[4]

    folder = LOCAL_PATH / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    with open(camera_settings) as f:
        cameraconfigs = json.load(f)
    cropping = cameraconfigs["cropping"]

    CD = CustomData(None)
    camera = configure_camera(camera_settings, hardware_trigger=True)
    camera.set_image_callback(on_new_image, CD, folder, cropping)

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    ser.close()
    time.sleep(2)
    ser.open()

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").rstrip()
            if line == "Arduino Ready":
                print("Arduino connection established")
                break

    ser.write("start\n".encode("utf-8"))
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
        if time.time() - start_time > 10:
            raise RuntimeError("No acknowledgment received from Arduino")
        time.sleep(0.1)

    print(f"Acknowledgment received: {''.join(arduino_output)}\nStarting recording.")

    with tqdm(total=duration, desc="Progress", bar_format="{l_bar}{bar}") as pbar:
        start = time.perf_counter()
        last_update = start
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").rstrip()
                if line == "done":
                    break
            current_time = time.perf_counter()
            if current_time - last_update >= 1:
                update_progress_bar(pbar, start, duration)
                last_update = current_time

    print(f"Program duration: {time.perf_counter() - start:0.4f} seconds")
    print(f"Saved {CD.imagecounter} images")

    camera.stop_pipeline()
    executor.shutdown(wait=True)
    folder.rename(folder.parent / (folder.name + "_Recorded"))
    ser.close()
    print("Program end")


if __name__ == "__main__":
    main()
