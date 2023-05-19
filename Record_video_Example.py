#!/usr/bin/env python3


#

# This example will show you how to save a video stream to a file

#


import time

import sys

import gi


gi.require_version("Gst", "1.0")


from gi.repository import Gst


def main():
    Gst.init(sys.argv)  # init gstreamer

    # this line sets the gstreamer default logging level

    # it can be removed in normal applications

    # gstreamer logging can contain verry useful information

    # when debugging your application

    # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html

    # for further details

    Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

    serial = None

    pipeline = Gst.parse_launch(
        "tcambin name=bin"
        " ! video/x-raw,format=GRAY8,width=4096,height=3000,framerate=30/1"
        " ! tee name=t"
        " ! queue"
        " ! videoconvert"
        " ! ximagesink"
        " t."
        " ! queue"
        " ! videoconvert"
        " ! avimux"
        " ! filesink name=fsink"
    )

    # to save a video without live view reduce the pipeline to the following:

    # pipeline = Gst.parse_launch("tcambin name=bin"

    #                             " ! video/x-raw,format=BGRx,width=640,height=480,framerate=30/1"

    #                             " ! videoconvert"

    #                             " ! mp4mux -e"

    #                             " ! filesink name=fsink")

    # serial is defined, thus make the source open that device

    if serial is not None:
        camera = pipeline.get_by_name("bin")

        camera.set_property("serial", serial)

    file_location = "/home/matthias/Videos/Test/video.mp4"

    fsink = pipeline.get_by_name("fsink")

    fsink.set_property("location", file_location)

    pipeline.set_state(Gst.State.PLAYING)

    print("Press Ctrl-C to stop.")
    
    Duration = 10

    time.sleep(Duration)

    pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()
