import sys
import cv2
import time
from tqdm import tqdm
import json
import TIS


def progress(count, total, status=""):
    """
    Progress bar for the terminal

    Parameters
    ----------
    count : int
        Current progress
    total : int
        Total progress
    status : str, optional
        Status message, by default ''

    """
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)

    sys.stdout.write("[%s] %s%s ...%s\r" % (bar, percents, "%", status))
    sys.stdout.flush()


def create_thumbnail(frame, dot_state, last_toggle_time):
    """
    Create a thumbnail image with a blinking red dot on the top left corner

    Parameters
    ----------
    frame : numpy.ndarray
        Image array
    dot_state : bool
        State of the dot
    last_toggle_time : float
        Time since the last toggle

    Returns
    -------
    numpy.ndarray
        Thumbnail image
    bool
        State of the dot
    float
        Time since the last toggle
    """

    thumbnail = cv2.resize(frame, (640, 480))
    # Convert to RGB
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_GRAY2RGB) 
    
    # Draw a blinking red dot on the top left corner of the thumbnail image
    if dot_state:
        cv2.circle(thumbnail, (20, 20), 15, (0, 0, 255), -1)

    # Check if enough time has elapsed since the last toggle
    current_time = time.perf_counter()
    if current_time - last_toggle_time >= 0.5:
        # Toggle the dot_state variable
        dot_state = not dot_state
        # Update the last_toggle_time variable
        last_toggle_time = current_time

    return thumbnail, dot_state, last_toggle_time

def update_progress_bar(pbar, start_time, total_time):
    """
    Update the progress bar every second

    Parameters
    ----------
    pbar : tqdm
        Progress bar
    start_time : float
        Start time
    total_time : float
        Total time
    """
    # Update the progress bar every second
    elapsed_time = int(time.perf_counter() - start_time)
    if elapsed_time > pbar.n:  # If more than a second has passed since last update
        pbar.update(elapsed_time - pbar.n)  # Update progress bar to current elapsed time

    # Convert elapsed time to hours, minutes, and seconds
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Convert total time to hours, minutes, and seconds
    total_hours, total_remainder = divmod(total_time, 3600)
    total_minutes, total_seconds = divmod(total_remainder, 60)
    # Update the progress bar format to include the elapsed time and total time
    pbar.set_description(f"Recording time: {hours:02}:{minutes:02}:{seconds:02}/{total_hours:02}:{total_minutes:02}:{total_seconds:02}")
    

def configure_camera(presets, hardware_trigger=False):
    """
    Configure the camera based on the provided presets.

    Parameters
    ----------
    presets : str
        Path to the JSON file containing the camera presets.
    
    hardware_trigger : bool, optional
        Whether to use hardware triggering, by default False

    Returns
    -------
    TIS.TIS
        Configured TIS object.
    """

    # Load camera configs
    with open(presets) as jsonFile:
        cameraconfigs = json.load(jsonFile)

    format = cameraconfigs["format"]

    # Create and configure TIS object
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
    
    if hardware_trigger:
        Tis.set_property("TriggerMode", "On")
        Tis.set_property("TriggerActivation", "Rising Edge")
    state = camera.get_property("tcam-properties-json")
    
    print(f"State of device is:\n{state}")

    return Tis