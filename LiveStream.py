import cv2
import json
import TIS
from Utilities import *

presets = "/home/matthias/multimaze_recorder/Presets/standard_set.json"

# Camera config
with open(presets) as jsonFile:
    cameraconfigs = json.load(jsonFile)
    jsonFile.close()

format = cameraconfigs["format"]

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
state = camera.get_property("tcam-properties-json")
print(f"State of device is:\n{state}")

while True:
    if Tis.snap_image(1):
        frame = Tis.get_image()
        thumbnail = cv2.resize(frame, (640, 480))
        cv2.imshow("Live Stream", thumbnail)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Stop the pipeline and clean up
Tis.stop_pipeline()
cv2.destroyAllWindows()
print("Program ends")
