# Add path to python-common/TIS.py to the import path
import cv2
import numpy as np
import os
import sys
import time
sys.path.append("../python-common")
import json
from tkinter import Tk, Label
from PIL import ImageTk, Image

from pathlib import Path

import TIS

class CustomData:
    ''' Example class for user data passed to the on new image callback function
    '''
    def __init__(self, newImageReceived, image):
        self.newImageReceived = newImageReceived
        self.image = image
        self.busy = False

CD = CustomData(False, None)

def on_new_image(tis, userdata):
    '''
    Callback function, which will be called by the TIS class
    :param tis: the camera TIS class, that calls this callback
    :param userdata: This is a class with user data, filled by this call.
    :return:
    '''
    # Avoid being called, while the callback is busy
    if userdata.busy is True:
        return

    userdata.busy = True
    userdata.newImageReceived = True
    userdata.image = tis.get_image()
    userdata.busy = False

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
    True,
)

CD = TIS.CustomData(False, None)

#Tis.list_properties()
Tis.set_image_callback(on_new_image, CD)

#Tis.set_property("TriggerMode", "On")
Tis.start_pipeline()

Tis.applyProperties()

Tis.set_property("TriggerMode", "On")

camera = Tis.get_source()
state = camera.get_property("tcam-properties-json")
print(f"State of device is:\n{state}")

error = 0
count = 0

# root = Tk()
# label = Label(root)
# label.pack()

# screen_width = root.winfo_screenwidth()
# screen_height = root.winfo_screenheight()

duration = 20
fps = 30
count = 0
timeout = 1 / fps

folder = Path("/home/matthias/Videos/Test_trigger/")

# Cropping parameters

Left = 250
Top = 0
Right = 3850
Bottom = 3000

Width = Right - Left
Height = Bottom - Top

# Create a variable to store the times of each frame
times = []

print('Press Esc to stop')
lastkey = 0

#time.sleep(2)
print('Start recording')

Gstart = time.perf_counter()
while count < (duration * fps):
    framestart = time.perf_counter()
    Tis.execute_command("TriggerSoftware") # Send a software trigger

    tries = 5
    while CD.newImageReceived is False and tries > 0:
        time.sleep(0.001)
        tries -= 1

    #start = time.perf_counter()
    if CD.newImageReceived is True:
        CD.newImageReceived = False
        filename = folder.joinpath("image" + str(count) + ".jpg").as_posix()
        image = Image.fromarray(np.squeeze(CD.image), mode='L')
        
        image = image.crop((Left, Top, Right, Bottom))
        # image = image.resize((Width, Height), 
        #                      #Image.BICUBIC,
        #                      )
        image.save(filename,)
        
        # thumbnail_image = image.copy() # create a copy of the image for thumbnail
        # thumbnail_image.thumbnail((screen_width, screen_height), Image.ANTIALIAS) # resize to fit screen size
        
        # photo = ImageTk.PhotoImage(thumbnail_image)
        # label.config(image=photo)
        # label.image = photo # keep a reference to prevent garbage collection
        
        count += 1 
    
    # else:
    #     print("No image received")
    #stop = time.perf_counter()
    #print(f"Handled image in {stop - start:0.4f} seconds")
    
    
    framestop = time.perf_counter()
    print(f"Frame took {framestop - framestart:0.4f} seconds")
    
    time.sleep(timeout)
    
    times.append(framestop - framestart)
    
    #root.update() # update the Tkinter window
    # remaining = timeout - (time.perf_counter() - framestart)
    # if remaining > 0:
    #     print(f'sleeping for {remaining:0.4f} seconds')
    #     time.sleep(remaining)
        
    
    
    
Gstop = time.perf_counter()
print(f"Captured {count} frames in {Gstop - Gstart:0.4f} seconds")
print(f"Average frame time: {np.mean(times):0.4f} seconds")
print(f"cumulative frame time: {np.sum(times):0.4f} seconds")

# Stop the pipeline and clean ip
Tis.stop_pipeline()
#cv2.destroyAllWindows()
print('Program ends')