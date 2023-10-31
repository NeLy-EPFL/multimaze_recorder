import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load images
reference_image = cv2.imread('patch.jpg', cv2.IMREAD_GRAYSCALE)
target_image = cv2.imread('image4.jpg', cv2.IMREAD_GRAYSCALE)

# Initialize SIFT detector
sift = cv2.SIFT_create()

## Find keypoints and descriptors for reference pattern
keypoints_ref, descriptors_ref = sift.detectAndCompute(reference_image, None)
print("Number of keypoints in reference image:", len(keypoints_ref))

# Find keypoints and descriptors for target image
keypoints_target, descriptors_target = sift.detectAndCompute(target_image, None)
print("Number of keypoints in target image:", len(keypoints_target))

# Create a Brute Force Matcher
bf = cv2.BFMatcher()

# Match descriptors between reference pattern and target image
matches = bf.knnMatch(descriptors_ref, descriptors_target, k=2)
print("Number of initial matches:", len(matches))

# Apply ratio test to filter matches
good_matches = []
for m, n in matches:
    if m.distance < 0.99* n.distance:
        good_matches.append(m)
print("Number of good matches:", len(good_matches))

# Extract matched keypoints from both images
matched_keypoints_ref = [keypoints_ref[m.queryIdx] for m in good_matches]
matched_keypoints_target = [keypoints_target[m.trainIdx] for m in good_matches]

# Estimate affine transformation
src_pts = np.float32([kp.pt for kp in matched_keypoints_ref]).reshape(-1, 1, 2)
print(src_pts.shape)
dst_pts = np.float32([kp.pt for kp in matched_keypoints_target]).reshape(-1, 1, 2)
print(dst_pts.shape)
M, mask = cv2.estimateAffinePartial2D(src_pts, dst_pts, cv2.RANSAC)

# Apply transformation to reference pattern
transformed_pattern = cv2.warpAffine(reference_image, M, (target_image.shape[1], target_image.shape[0]))

# Display results
#cv2.imshow('Transformed Pattern', transformed_pattern)
#cv2.imshow('Target Image', target_image)
fig, ax = plt.subplots(1,2,figsize=(10,5))
ax[0].imshow(transformed_pattern)
ax[1].imshow(target_image,cmap='gray')
ax[0].set_title('TRANSFORMED Image',fontsize=15)
ax[1].set_title('TARGET Image',fontsize=15)
plt.show()
cv2.destroyAllWindows()
