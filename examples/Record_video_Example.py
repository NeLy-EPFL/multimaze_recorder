"""Example: record a raw video stream directly via GStreamer pipeline."""

import time
import sys
from pathlib import Path

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst


def main():
    Gst.init(sys.argv)
    Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

    serial = None  # Set to a camera serial string to target a specific device
    output_file = Path("~/Videos/recording.avi").expanduser()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    pipeline = Gst.parse_launch(
        "tcambin name=bin"
        " ! video/x-raw,format=GRAY8,width=4096,height=3000,framerate=30/1"
        " ! tee name=t"
        " t. ! queue ! videoconvert ! ximagesink"
        " t. ! queue ! videoconvert ! avimux ! filesink name=fsink"
    )

    if serial is not None:
        pipeline.get_by_name("bin").set_property("serial", serial)

    pipeline.get_by_name("fsink").set_property("location", str(output_file))

    pipeline.set_state(Gst.State.PLAYING)
    print(f"Recording to {output_file}. Press Ctrl-C to stop.")

    duration = 10
    time.sleep(duration)

    pipeline.set_state(Gst.State.NULL)
    print("Done.")


if __name__ == "__main__":
    main()
