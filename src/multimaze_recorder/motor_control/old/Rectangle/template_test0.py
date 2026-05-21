import numpy as np
from skimage.io import imshow, imread, imsave
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage.feature import match_template
from skimage.feature import peak_local_max
import time

sample = imread('image3.jpg')
#sample_g = rgb2gray(sample)
fig, ax = plt.subplots(1,2,figsize=(10,5))
ax[0].imshow(sample)
#ax[1].imshow(sample_g,cmap='gray')
ax[0].set_title('Colored Image',fontsize=15)
ax[1].set_title('Grayscale Image',fontsize=15)
plt.show()

patch_x_min=214
patch_x_max=541
patch_y_min=903
patch_y_max=1115

fig, ax = plt.subplots(1,2,figsize=(10,10))
ax[0].imshow(sample,cmap='gray')
ax[0].add_patch(Rectangle((patch_x_min, patch_x_max), patch_x_max-patch_x_min, patch_y_max-patch_y_min, edgecolor='b', facecolor='none'));
ax[0].set_title('Patch Location',fontsize=15)
#Showing Patch
patch = sample[patch_x_min:patch_x_max, patch_y_min:patch_y_max]
imsave('patch.jpg',patch)
ax[1].imshow(patch,cmap='gray')
ax[1].set_title('Patch',fontsize=15)
plt.show()

sample2 = imread('image4.jpg')
t0 = time.time()
sample_mt = match_template(sample2, patch)

fig, ax = plt.subplots(1,2,figsize=(10,10))
ax[0].imshow(sample2,cmap='gray')
ax[1].imshow(sample_mt,cmap='gray')
ax[0].set_title('Grayscale',fontsize=15)
ax[1].set_title('Template Matching',fontsize=15);

fig, ax = plt.subplots(1,2,figsize=(10,10))
ax[0].imshow(sample2,cmap='gray')
ax[1].imshow(sample2,cmap='gray')

patch_width, patch_height = patch.shape
a=[]
for x, y in peak_local_max(sample_mt, threshold_abs=0.7):
    rect = plt.Rectangle((y, x), patch_height, patch_width, color='r', 
                         fc='none')
    ax[1].add_patch(rect)
    #a.append([x,y])
ax[0].set_title('Grayscale',fontsize=15)
ax[1].set_title('Template Matched',fontsize=15);
plt.show()