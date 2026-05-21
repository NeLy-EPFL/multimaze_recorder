import numpy as np
from skimage.io import imshow, imread
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage.feature import match_template
from skimage.feature import peak_local_max
import time
import cv2


# Open the video file
# Define the video file path
video_path = '/home/matthias/Videos/Screencasts/showcase.webm'
cap = cv2.VideoCapture(video_path)

# Get the video's frame dimensions
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# Desired frame size
desired_width = 3600
desired_height = 3000

# Calculate the scale factor for resizing frames
scale_factor_width = desired_width / frame_width
scale_factor_height = desired_height / frame_height

divide_regions = [[25,550,130,450],  [1520,2050,130,450],[3020,3520,130,450],
                  [25,550,1300,1650],[1520,2050,1300,1650] , [3020,3520,1300,1650],
                  [25,550,2420,2820],[1520,2050,2420,2820], [3020,3520,2420,2820]]

patch_x_min=200
patch_x_max=230
patch_y_min=245
patch_y_max=275



patch = imread('patch.jpg',as_gray=True)

#patch = sample[patch_x_min:patch_x_max, patch_y_min:patch_y_max]



        #print(region," ---------------  ")
        #print(a)
        #ax[0].set_title('divided',fontsize=15)

        #plt.show()

frame_count = 0


import os
import glob
folder = f"magnets"
i=516
# Loop through the video frames and extract them
while True:
    ret, frame = cap.read()
    if not ret:
        break
    


    frame1 = imread(folder+f"/image{i}.jpg")
    i+=1
    frame2=cv2.cvtColor(frame1, cv2.COLOR_GRAY2BGR)
    #frame1 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(frame.shape)

    # Resize the frame to the desired size
    #resized_frame = cv2.resize(frame1, (desired_width, desired_height))
    # Save the resized frame
    #frame_filename = f'frame_{frame_count:04d}.jpg'  # You can adjust the filename format
    frame_count += 1

    #cv2.imwrite(frame_filename, resized_frame)

    for region in divide_regions:
        #ax[0].set_title('Grayscale',fontsize=15)
        #ax[1].set_title('Template Matching',fontsize=15)
        a=[]

        y_min, y_max, x_min, x_max = region
        print(region," ---------------  ")
        sample_div = frame1[x_min:x_max, y_min:y_max]

        #fig, ax = plt.subplots(1,2,figsize=(10,10))
        #ax[0].imshow(sample_div,cmap='gray')

        #plt.show()
        sample_mt = match_template(sample_div, patch)

        patch_width, patch_height = patch.shape
        for x, y in peak_local_max(sample_mt, threshold_abs=0.75):
            cv2.rectangle(frame2, ((y+y_min), (x+x_min)), ((y+y_min+patch_width), (x+x_min+patch_height)),(0,0,255), 2)

    # Display the frame with rectangles
    resized_frame = cv2.resize(frame2, (800, 800))

    cv2.imshow("bu",resized_frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
#sample_g = rgb2gray(sample)
#fig, ax = plt.subplots(1,2,figsize=(10,5))
#ax[0].imshow(sample)
#ax[1].imshow(sample_g,cmap='gray')
#ax[0].set_title('Colored Image',fontsize=15)
#ax[1].set_title('Grayscale Image',fontsize=15)
#plt.show()


