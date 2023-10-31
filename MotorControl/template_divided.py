import numpy as np
from skimage.io import imshow, imread
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage.feature import match_template
from skimage.feature import peak_local_max
import time
#import cv2

#sample = imread('python\image0.jpg')
#sample_g = rgb2gray(sample)
#fig, ax = plt.subplots(1,2,figsize=(10,5))
#ax[0].imshow(sample)
#ax[1].imshow(sample_g,cmap='gray')
#ax[0].set_title('Colored Image',fontsize=15)
#ax[1].set_title('Grayscale Image',fontsize=15)
#plt.show()


divide_regions = [[25,550,130,450],  [1520,2050,130,450],[3020,3520,130,450],
                  [25,550,1300,1650],[1520,2050,1300,1650] , [3020,3520,1300,1650],
                  [25,550,2420,2820],[1520,2050,2420,2820], [3020,3520,2420,2820]]

patch_x_min=200
patch_x_max=230
patch_y_min=245
patch_y_max=275

#fig, ax = plt.subplots(1,2,figsize=(10,10))
#sample5 = sample[1300:1650, 1520:2050]
#ax[0].imshow(sample5,cmap='gray')
#ax[0].add_patch(Rectangle((patch_x_min, patch_y_min), patch_x_max-patch_x_min, patch_y_max-patch_y_min, edgecolor='b', facecolor='none'));
#ax[0].set_title('Patch Location',fontsize=15)

#Showing Patch
#patch = sample5[patch_y_min:patch_y_max, patch_x_min:patch_x_max]
#ax[1].imshow(patch,cmap='gray')
#ax[1].set_title('Patch',fontsize=15)
#plt.show()
#patch = imread('python\patch.jpg')
patch = imread('patch.jpg')

#patch = sample[patch_x_min:patch_x_max, patch_y_min:patch_y_max]


sample2 = imread('/home/matthias/Videos/MotorControlRecording/image5939.jpg')

#fig, ax = plt.subplots(1,2,figsize=(10,10))
#ax[0].imshow(sample2,cmap='gray')
#ax[1].imshow(sample2,cmap='gray')
fig, ax = plt.subplots(1,2,figsize=(10,10))
ax[0].imshow(sample2,cmap='gray')
ax[1].imshow(sample2,cmap='gray')

t0=time.time()

for region in divide_regions:
#ax[0].set_title('Grayscale',fontsize=15)
#ax[1].set_title('Template Matching',fontsize=15)
    a=[]

    y_min, y_max, x_min, x_max = region
    sample_div = sample2[x_min:x_max, y_min:y_max]
    #fig, ax = plt.subplots(1,2,figsize=(10,10))
    #ax[0].imshow(sample_div,cmap='gray')

    #plt.show()
    sample_mt = match_template(sample_div, patch)

    patch_width, patch_height = patch.shape
    for x, y in peak_local_max(sample_mt, threshold_abs=0.75):
        rect = plt.Rectangle((y+y_min, x+x_min), patch_height, patch_width, color='r', 
                            fc='none')
        a.append([x+x_min,y+y_min])
        ax[1].add_patch(rect)

    #print(region," ---------------  ")
    #print(a)
    #ax[0].set_title('divided',fontsize=15)

    #plt.show()
print(time.time()-t0)

ax[0].set_title('Grayscale',fontsize=15)
ax[1].set_title('Template Matched',fontsize=15);
plt.show()
