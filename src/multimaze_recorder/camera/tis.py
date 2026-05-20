import time
from collections import namedtuple

import os
import re
import gi
import numpy
from enum import Enum

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")
os.environ['GST_DEBUG'] = '3'

from gi.repository import GLib, Gst, Tcam


DeviceInfo = namedtuple("DeviceInfo", "status name identifier connection_type")
CameraProperty = namedtuple(
    "CameraProperty", "status value min max default step type flags category group"
)


class SinkFormats(Enum):
    GRAY8 = "GRAY8"
    GRAY16_LE = "GRAY16_LE"
    BGRA = "BGRx"
    BGRX = "BGRx"


class TIS:
    "The Imaging Source Camera"

    def __init__(self, properties):
        try:
            if not Gst.is_initialized():
                Gst.init(())
        except gi.overrides.Gst.NotInitialized:
            Gst.init(())
        self.serialnumber = ""
        self.height = 0
        self.width = 0
        self.framerate = "15/1"
        self.sinkformat = SinkFormats.BGRA
        self.img_mat = None
        self.ImageCallback = None
        self.pipeline = None
        self.source = None
        self.appsink = None
        self.properties = properties

    def open_device(
        self,
        serial,
        width,
        height,
        framerate,
        sinkformat: SinkFormats,
        showvideo: bool,
        conversion: str = "",
    ):
        if serial is None:
            serial = self.__get_serial_by_index(0)
        self.serialnumber = serial
        self.height = height
        self.width = width
        self.framerate = framerate
        self.sinkformat = sinkformat
        self._create_pipeline(conversion, showvideo)
        self.source.set_property("serial", self.serialnumber)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.get_state(40000000)

    def _create_pipeline(self, conversion: str, showvideo: bool):
        if conversion and not conversion.strip().endswith("!"):
            conversion += " !"
        p = "tcambin name=source ! capsfilter name=caps"
        if showvideo:
             p += " ! tee name=t"
             p += " t. ! queue ! videoconvert ! ximagesink"
             p += f" t. ! queue ! {conversion} appsink name=sink"
        else:
            p += f" ! queue ! {conversion} appsink name=sink"

        print(p)
        try:
            self.pipeline = Gst.parse_launch(p)
        except GLib.Error as error:
            print("Error creating pipeline: {0}".format(error))
            raise

        self.source = self.pipeline.get_by_name("source")

        appsink = self.pipeline.get_by_name("sink")
        appsink.set_property("max-buffers", 5)
        appsink.set_property("drop", True)
        appsink.set_property("emit-signals", True)
        appsink.set_property("enable-last-sample", True)
        appsink.connect("new-sample", self.__on_new_buffer)
        self.appsink = appsink

    def __on_new_buffer(self, appsink):
        sample = appsink.get_property("last-sample")
        if sample and self.ImageCallback is not None:
            buf = sample.get_buffer()
            data = buf.extract_dup(0, buf.get_size())
            caps = sample.get_caps()
            self.img_mat = self.__convert_to_numpy(data, caps)
            self.ImageCallback(self, *self.ImageCallbackData)
        return Gst.FlowReturn.OK

    def set_sink_format(self, sf: SinkFormats):
        self.sinkformat = sf

    def show_live(self, show: bool):
        self.livedisplay = show

    def _setcaps(self):
        caps = Gst.Caps.from_string(
            "video/x-raw,format=%s,width=%d,height=%d,framerate=%s"
            % (self.sinkformat.value, self.width, self.height, self.framerate)
        )
        capsfilter = self.pipeline.get_by_name("caps")
        capsfilter.set_property("caps", caps)

    def start_pipeline(self):
        self._setcaps()
        self.pipeline.set_state(Gst.State.PLAYING)
        error = self.pipeline.get_state(5000000000)
        if error[1] != Gst.State.PLAYING:
            print("Error starting pipeline. {0}".format(""))
            return False
        return True

    def __convert_to_numpy(self, data, caps):
        s = caps.get_structure(0)
        fmt = s.get_value("format")

        if fmt == "BGRx":
            dtype = numpy.uint8
            bpp = 4
        elif fmt == "GRAY8":
            dtype = numpy.uint8
            bpp = 1
        elif fmt == "GRAY16_LE":
            dtype = numpy.uint16
            bpp = 1
        else:
            raise RuntimeError(f"Unknown format in conversion to numpy array: {fmt}")

        img_mat = numpy.ndarray(
            (s.get_value("height"), s.get_value("width"), bpp), buffer=data, dtype=dtype
        )
        return img_mat

    def snap_image(self, timeout, convert_to_mat=True):
        if self.ImageCallback is not None:
            print("Snap_image can not be called, if a callback is set.")
            return None

        sample = self.appsink.emit("try-pull-sample", timeout * Gst.SECOND)
        buf = sample.get_buffer()
        data = buf.extract_dup(0, buf.get_size())
        if convert_to_mat and sample is not None:
            try:
                self.img_mat = self.__convert_to_numpy(data, sample.get_caps())
            except RuntimeError:
                pass

        return data

    def get_image(self):
        return self.img_mat

    def stop_pipeline(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)

    def get_source(self):
        return self.source

    def list_properties(self):
        property_names = self.source.get_tcam_property_names()
        for name in property_names:
            try:
                base = self.source.get_tcam_property(name)
                print("{}\t{}".format(base.get_display_name(), name))
            except Exception as error:
                raise RuntimeError(f"Failed to get property '{name}'") from error

    def get_property(self, property_name):
        try:
            baseproperty = self.source.get_tcam_property(property_name)
            return baseproperty.get_value()
        except Exception as error:
            raise RuntimeError(f"Failed to get property '{property_name}'") from error

    def set_property(self, property_name, value):
        try:
            baseproperty = self.source.get_tcam_property(property_name)
            baseproperty.set_value(value)
        except Exception as error:
            raise RuntimeError(f"Failed to set property '{property_name}'") from error

    def execute_command(self, property_name):
        try:
            baseproperty = self.source.get_tcam_property(property_name)
            baseproperty.set_command()
        except Exception as error:
            raise RuntimeError(f"Failed to execute '{property_name}'") from error

    def set_image_callback(self, function, *data):
        self.ImageCallback = function
        self.ImageCallbackData = data

    def __get_serial_by_index(self, index: int):
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source/tcam")
        devices = monitor.get_devices()
        if (index < 0) or (index > len(devices) - 1):
            raise RuntimeError("Index out of bounds")
        device = devices[index]
        return device.get_properties().get_string("serial")

    def select_device(self):
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source/tcam")
        serials = []
        i = 0
        for device in monitor.get_devices():
            struc = device.get_properties()
            i += 1
            print(
                "{} : Model: {} Serial: {} {} ".format(
                    i,
                    struc.get_string("model"),
                    struc.get_string("serial"),
                    struc.get_string("type"),
                )
            )
            serials.append(
                "{}-{}".format(struc.get_string("serial"), struc.get_string("type"))
            )

        if i > 0:
            i = int(input("Select : "))
            if i == 0:
                return False
            self.serialnumber = serials[i - 1]
            print(self.serialnumber)
            return self.select_format()

        return False

    def select_format(self):
        formats = self.create_formats()
        i = 0
        f = []
        for key, value in formats.items():
            f.append(key)
            i = i + 1
            print("{}: {}".format(i, key))

        i = int(input("Select : "))
        if i == 0:
            return False

        formatindex = f[i - 1]
        i = 0
        for res in formats[formatindex].res_list:
            i = i + 1
            print("{}:  {}x{}".format(i, res.width, res.height))

        i = int(input("Select : "))
        if i == 0:
            return False

        width = formats[formatindex].res_list[i - 1].width
        height = formats[formatindex].res_list[i - 1].height
        o = 0
        for rate in formats[formatindex].res_list[i - 1].fps:
            o += 1
            print("{}:  {}".format(o, rate))

        framerate = formats[formatindex].res_list[i - 1].fps[o - 1]
        o = int(input("Select : "))
        if o == 0:
            return False

        framerate = formats[formatindex].res_list[i - 1].fps[o - 1]
        self.open_device(
            self.serialnumber, width, height, framerate, SinkFormats.BGRA, True
        )
        return True

    def create_formats(self):
        source = Gst.ElementFactory.make("tcambin")
        source.set_property("serial", self.serialnumber)
        source.set_state(Gst.State.READY)

        caps = source.get_static_pad("src").query_caps()
        format_dict = {}

        for x in range(caps.get_size()):
            structure = caps.get_structure(x)
            name = structure.get_name()
            try:
                videoformat = structure.get_value("format")
                width = structure.get_value("width")
                height = structure.get_value("height")
                rates = self.get_framerates(structure)
                tmprates = [str(rate) for rate in rates]

                if type(videoformat) == Gst.ValueList:
                    videoformats = videoformat
                else:
                    videoformats = [videoformat]
                for fmt in videoformats:
                    if videoformat not in format_dict:
                        format_dict[fmt] = FmtDesc(name, videoformat)
                    format_dict[fmt].res_list.append(ResDesc(width, height, tmprates))
            except Exception as error:
                print(f"Exception during format enumeration: {str(error)}")

        source.set_state(Gst.State.NULL)
        source.set_property("serial", "")
        source = None

        return format_dict

    def get_framerates(self, fmt):
        try:
            tmprates = fmt.get_value("framerate")
            if type(tmprates) == Gst.FractionRange:
                rates = []
                rates.append(
                    "{0}/{1}".format(int(tmprates.start.num), int(tmprates.start.denom))
                )
                r = int((tmprates.start.num + 10) / 10) * 10
                while r < (tmprates.stop.num / tmprates.stop.denom):
                    rates.append("{0}/1".format(r))
                    r += 10
                rates.append(
                    "{0}/{1}".format(int(tmprates.stop.num), int(tmprates.stop.denom))
                )
            else:
                rates = tmprates
        except TypeError:
            substr = fmt.to_string()[fmt.to_string().find("framerate="):]
            field, values, remain = re.split("{|}", substr, maxsplit=3)
            rates = [x.strip() for x in values.split(",")]
        return rates

    def applyProperties(self):
        for prop in self.properties:
            try:
                self.set_property(prop["property"], prop["value"])
            except Exception as error:
                print(error)


class ResDesc:
    def __init__(self, width: int, height: int, fps: list):
        self.width = width
        self.height = height
        self.fps = fps


class FmtDesc:
    def __init__(self, name: str = "", fmt: str = ""):
        self.name = name
        self.fmt = fmt
        self.res_list = []

    def get_name(self):
        if self.name == "image/jpeg":
            return "jpeg"
        else:
            return self.fmt

    def get_resolution_list(self):
        return [entry.resolution for entry in self.res_list]

    def get_fps_list(self, resolution: str):
        for entry in self.res_list:
            if entry.resolution == resolution:
                return entry.fps

    def generate_caps_string(self, resolution: str, fps: str):
        if self.name == "image/jpeg":
            return "{},width={},height={},framerate={}".format(
                self.name, resolution.split("x")[0], resolution.split("x")[1], fps
            )
        else:
            return "{},format={},width={},height={},framerate={}".format(
                self.name,
                self.fmt,
                resolution.split("x")[0],
                resolution.split("x")[1],
                fps,
            )
