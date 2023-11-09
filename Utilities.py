import sys
import cv2
import time


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


def create_thumbnail(frame, userdata):
    """
    Create a thumbnail image with a blinking red dot on the top left corner

    Parameters
    ----------
    frame : numpy.ndarray
        Image array
    last_toggle_time : float
        Time since the last toggle
    dot_state : bool
        State of the dot

    Returns
    -------
    numpy.ndarray
        Thumbnail image
    float
        Time since the last toggle
    bool
        State of the dot

    """

    thumbnail = cv2.resize(frame, (640, 480))
    # Convert to RGB
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_GRAY2RGB) 
    
    # Draw a blinking red dot on the top left corner of the thumbnail image
    if userdata.dot_state:
        cv2.circle(thumbnail, (20, 20), 15, (0, 0, 255), -1)

    # Check if enough time has elapsed since the last toggle
    current_time = time.perf_counter()
    if current_time - userdata.last_toggle_time >= 0.5:
        # Toggle the dot_state variable
        userdata.dot_state = not userdata.dot_state
        # Update the last_toggle_time variable
        userdata.last_toggle_time = current_time

    return thumbnail