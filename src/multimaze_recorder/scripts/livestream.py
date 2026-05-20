"""Live stream preview using the TIS camera."""

import os
import sys
import cv2
from pathlib import Path
from multimaze_recorder.utilities import configure_camera

_PACKAGE_CONFIG_DIR = Path(__file__).parent.parent / "gui" / "config"
DEFAULT_PRESETS = str(_PACKAGE_CONFIG_DIR / "Presets" / "standard_set.json")


def main():
    presets = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "MMRECORDER_PRESETS", DEFAULT_PRESETS
    )

    camera = configure_camera(presets)

    while True:
        if camera.snap_image(1):
            frame = camera.get_image()
            thumbnail = cv2.resize(frame, (640, 480))
            cv2.imshow("Live Stream", thumbnail)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    camera.stop_pipeline()
    cv2.destroyAllWindows()
    print("Program ends")


if __name__ == "__main__":
    main()
