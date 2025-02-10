'''
import cv2

# Load the image
image = cv2.imread('C://Users/user/Pictures/Screenshots/Screenshot2.jpg')

# Let the user select the ROI
roi = cv2.selectROI('Select ROI', image, showCrosshair=True, fromCenter=False)

# Extract the coordinates from the ROI
x, y, w, h = roi

# Extract the ROI from the image
selected_roi = image[y:y+h, x:x+w]

# Apply Gaussian blur to the ROI
blurred_roi = cv2.GaussianBlur(selected_roi, (15, 15), 0)

# Replace the original ROI with the blurred ROI in the image
image[y:y+h, x:x+w] = blurred_roi

# Display the result
cv2.imshow('Blurred Area', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
'''

names = ["axel"]
for _ in names:
    print(type(names))