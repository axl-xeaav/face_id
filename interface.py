import cv2
import numpy as np

def load_image(file_path):
    # Load the fingerprint image in grayscale
    image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    return image
file_path = r"C:\Users\user\Documents\pythonProjects\CapstoneFiles\SOCOFing\Altered\Altered-Easy\1__M_Left_index_finger_CR.bmp"

def binarize_image(image):
    # Apply adaptive thresholding to binarize the image
    _, binary_image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
    return binary_image

def thin_image(image):
    # Thinning (skeletonization) using morphological operations
    size = np.size(image)
    skeleton = np.zeros(image.shape, np.uint8)
    
    ret, image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    done = False
    
    while not done:
        eroded = cv2.erode(image, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(image, temp)
        skeleton = cv2.bitwise_or(skeleton, temp)
        image = eroded.copy()
        
        done = (cv2.countNonZero(image) == 0)
    
    return skeleton

def minutiae_detection(thinned_image):
    minutiae_points = []
    rows, cols = thinned_image.shape
    
    for i in range(1, rows-1):
        for j in range(1, cols-1):
            if thinned_image[i, j] == 255:  # If the pixel is part of a ridge
                # Count the number of neighbors
                neighbors = [
                    thinned_image[i-1, j-1], thinned_image[i-1, j], thinned_image[i-1, j+1],
                    thinned_image[i, j-1],                     thinned_image[i, j+1],
                    thinned_image[i+1, j-1], thinned_image[i+1, j], thinned_image[i+1, j+1]
                ]
                count = sum(n == 255 for n in neighbors)
                
                if count == 1:
                    minutiae_points.append((i, j, 'ending'))
                elif count == 3:
                    minutiae_points.append((i, j, 'bifurcation'))
    
    return minutiae_points

def draw_minutiae_points(image, minutiae_points):
    # Draw minutiae points on the image
    for point in minutiae_points:
        y, x, m_type = point
        if m_type == 'ending':
            cv2.circle(image, (x, y), 3, (0, 255, 0), -1)  # Green for endings
        elif m_type == 'bifurcation':
            cv2.circle(image, (x, y), 3, (0, 0, 255), -1)  # Red for bifurcations
    return image

def main():
    # Load the fingerprint image
    image = load_image('fingerprint.png')
    
    # Preprocess the image
    binary_image = binarize_image(image)
    thinned_image = thin_image(binary_image)
    
    # Detect minutiae points
    minutiae_points = minutiae_detection(thinned_image)
    
    # Draw minutiae points on the original image for visualization
    image_with_minutiae = draw_minutiae_points(image.copy(), minutiae_points)
    
    # Display the results
    cv2.imshow('Original Image', image)
    cv2.imshow('Binary Image', binary_image)
    cv2.imshow('Thinned Image', thinned_image)
    cv2.imshow('Minutiae Points', image_with_minutiae)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
