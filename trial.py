import cv2 as cv
import numpy as np

#-215 assertion error, check file name of img, video. or empty param

#img = imread('jeongcutie.jpg') #initialize pic

# cv.imshow("Girl", img) #display img

# cv.waitKey(0) #wait for seconds, 0 is infinite

#initializing videos and scalling, change resolution

# def change_res(height, width): #for live video only, external camera
#     vid.set(3, width)
#     vid.set(4, height)

# for scalling 
# img = cv.imread("jeongcutie.jpg")
# if img is None:
#         print("No image")
#         exit()
# resized_img = cv.resize(img,(300, 200), interpolation=cv.INTER_AREA)

# cv.imshow("resized", resized_img)
# while True:    
#     if cv.waitKey(5) & 0xFF==ord('q'):
#         break

# vid.release()
# cv.destroyAllWindows()

#drawing shapes and write on img

# blank = np.zeros((500,500, 3), dtype='uint8') #creates blank img. first 500 Y-axis, sec is X-axis
#cv.imshow("blank", blank)
# cv.waitKey(0)

#blank[200:300, 300:400] = 0, 0 , 255 # [location of color] rgb

#draw rectangle
#cv.rectangle(blank, (0,0), (250,250), (0, 255, 0), thickness=1) 
# first param = variable from img path
# second third param = location of rectangle
# fourth param = color of rectangle
# fifth param = thickness of rectangle

#cv.imshow("rectangle", blank)

#draw circle 
#cv.circle()
# first param = image
# sec param = center
# third  param = radius
# fourth param = color then thickness

# #put text
# cv.putText(blank, "hello", (255,255), cv.FONT_HERSHEY_PLAIN, 1.0) 

        #essential functions
#grayscale with scalling

img = cv.imread("jeongcutie.jpg")
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
#cv.imshow("gray", gray)

def rescale_gray():
        resized = cv.resize(gray, (500,500), interpolation=cv.INTER_AREA)
        return resized

resized_gray = rescale_gray()

cv.imshow("grayscale", resized_gray)

#






cv.waitKey(0)
cv.destroyAllWindows()