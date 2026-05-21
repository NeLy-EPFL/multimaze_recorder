import cv2
import numpy as np
from matplotlib import pyplot as plt

#read image
img = cv2.imread(f'image0.jpg')
#convert to grayscale
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

#setting threshold of gray image
_, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

#find contours in threshold image
contours, _ = cv2.findContours(threshold,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

i = 0

# Loop through contours
for contour in contours:
    # Skip the first contour
    if contour.shape[0] < 4:
        continue
    
    # Approximate the shape
    approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
    
    # Draw only if the shape is a quadrilateral with edge size between min_size and max_size
    if len(approx) == 4:
        edge_lengths = [np.linalg.norm(approx[i] - approx[(i + 1) % 4]) for i in range(4)]
        min_size = 50  # Adjust this value as needed
        max_size = 500  # Adjust this value as needed
        if all(min_size <= length <= max_size for length in edge_lengths):
            cv2.drawContours(img, [contour], 0, (0, 0, 255), 5)
        
# Resize the image to the desired dimensions
desired_width = 800  # Adjust this value as needed
desired_height = 600  # Adjust this value as needed
img_resized = cv2.resize(img, (desired_width, desired_height))

# displaying the image after drawing contours
cv2.imshow('shapes', img_resized)
  
cv2.waitKey(0)
cv2.destroyAllWindows()