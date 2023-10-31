import numpy as np
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.feature import match_template
from skimage.feature import peak_local_max
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import imageio

# Load the patch image
patch = imread('patch.jpg', as_gray=True)

# Define the video file path
video_path = '/home/matthias/Videos/Screencasts/showcase.webm'

# Read video using imageio
video_reader = imageio.get_reader(video_path)

# Convert the patch to grayscale if it's a color image
if patch.ndim == 3:
    patch = rgb2gray(patch)

# Define divide regions
divide_regions = [[25, 550, 130, 450], [1520, 2050, 130, 450], [3020, 3520, 130, 450],
                  [25, 550, 1300, 1650], [1520, 2050, 1300, 1650], [3020, 3520, 1300, 1650],
                  [25, 550, 2420, 2820], [1520, 2050, 2420, 2820], [3020, 3520, 2420, 2820]]

# Process frames and display them with rectangles
for frame_idx, frame in enumerate(video_reader):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(frame, cmap='gray')
    
    for region in divide_regions:
        y_min, y_max, x_min, x_max = region
        frame.resize(3060,3600)
        sample_div = frame[x_min:x_max, y_min:y_max]
        
        # Convert the sample_div to grayscale if it's a color image
        if sample_div.ndim == 3:
            sample_div = rgb2gray(sample_div)
        
        sample_mt = match_template(sample_div, patch)
        
        patch_width, patch_height = patch.shape
        for x, y in peak_local_max(sample_mt, threshold_abs=0.75):
            rect = Rectangle((y + y_min, x + x_min), patch_height, patch_width, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
    
    plt.title(f'Frame {frame_idx + 1} with Rectangles')
    plt.axis('off')
    plt.show()
