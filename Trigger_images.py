import sys
import cv2
import numpy as np
from tqdm import tqdm
import time
from pathlib import Path
from PIL import Image
import json
from concurrent.futures import ThreadPoolExecutor
import gi
import serial
from Utilities import *

# TODO: better commenting and function documentation

# Create a ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")

# Constants
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
PRESETS_PATH = "/home/matthias/multimaze_recorder/Presets/standard_set.json"
LOCAL_PATH = "/home/matthias/Videos/"
REMOTE_PATH = (
    "/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/"
)


class CustomData:
    """
    User data structure to be passed to the on_new_image callback function

    Attributes
    ----------
    imagecounter : int
        Number of images saved
    image : numpy.ndarray
        Image array
    busy : bool
        Flag to indicate whether the callback function is busy
    dot_state : bool
        State of the dot in the thumbnail image
    last_toggle_time : float
        Time of the last toggle of the dot in the thumbnail image

    Methods
    -------
    __init__(self, image)
        Constructor

    """

    def __init__(self, image):
        self.imagecounter = 0
        self.image = image
        self.busy = False
        self.dot_state = False
        self.last_toggle_time = time.perf_counter()


def save_image(image, filename):
    image.save(filename)


def on_new_image(tis, userdata, folder, cropping):
    """
    Callback function that is called whenever an image is received from the camera

    Parameters
    ----------
    tis : tcam.camera
        Camera object
    userdata : CustomData
        User data object
    folder : pathlib.Path
        Path to the folder where the images are saved
    cropping : dict
        Dictionary containing the cropping parameters. inherited from the camera configuration file
    """
    # Avoid being called, while the callback is busy
    if userdata.busy is True:
        return

    userdata.busy = True
    # framestart = time.perf_counter()
    userdata.image = tis.get_image()
    frame = tis.get_image()

    # Doing a sample image processing

    filename = folder.joinpath("image" + str(userdata.imagecounter) + ".jpg").as_posix()
    image = Image.fromarray(np.squeeze(frame), mode="L")

    Left, Top, Right, Bottom = cropping.values()

    image = image.crop((Left, Top, Right, Bottom))

    # Submit the image saving task to the ThreadPoolExecutor
    future = executor.submit(save_image, image, filename)

    # Generate a thumbnail image to display in the GUI
    thumbnail, userdata.dot_state, userdata.last_toggle_time = create_thumbnail(
        frame, userdata.dot_state, userdata.last_toggle_time
    )

    cv2.imshow("Maze Recorder", thumbnail)
    cv2.waitKey(1)

    userdata.imagecounter += 1

    userdata.busy = False


def main():
    # Parse command-line arguments
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} FOLDERNAME")
        sys.exit(1)

    FolderName = sys.argv[1]
    fps = int(sys.argv[2])
    duration = int(sys.argv[3])

    folder = Path(LOCAL_PATH).joinpath(FolderName)
    folder.mkdir(parents=True, exist_ok=True)

    # Extract cropping parameters
    with open(PRESETS_PATH) as jsonFile:
        cameraconfigs = json.load(jsonFile)
    cropping = cameraconfigs["cropping"]

    # Create an instance of the CustomData class
    CD = CustomData(None)

    # Configure the camera
    camera = configure_camera(PRESETS_PATH, hardware_trigger=True)

    # Set the callback function
    camera.set_image_callback(on_new_image, CD, folder, cropping)

    # Open the serial port
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

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

    # Wait for acknowledgment from Arduino for 10 seconds. If no acknowledgement is received, abort the program and raise an exception
    while not ack_received:
        while ser.in_waiting > 0:
            line = ser.readline().decode("utf-8")
            arduino_output.append(line)
            ack_received = True
        if time.time() - start_time > 10:
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

    camera.stop_pipeline()

    executor.shutdown(wait=True)

    # Rename the folder with '_Recorded' suffix to tag it as a recorded folder
    folder.rename(folder.parent.joinpath(folder.name + "_Recorded"))

    ser.close()
    print("Program end")


if __name__ == "__main__":
    main()
