import cv2
from Utilities import *

presets = "/home/matthias/multimaze_recorder/GUI/Presets/standard_set.json"

camera = configure_camera(presets)

while True:
    if camera.snap_image(1):
        frame = camera.get_image()
        thumbnail = cv2.resize(frame, (640, 480))
        cv2.imshow("Live Stream", thumbnail)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Stop the pipeline and clean up
camera.stop_pipeline()
cv2.destroyAllWindows()
print("Program ends")
