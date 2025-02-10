#without @property
class Class:

    def __init__(self, house=None):
        self._house = house
    #getter retrieves value of an attribute. Decorator: '@property. mostly just 1 parameter
    def get_house(self):
        return self._house  #use convention only for private not public. 
        #conventions are private, cant use outside the class. while not convention can be used outside
    #setter updates value. Decorator '@<attribute>.setter. 2 or more parameter
    def set_house(self, house):
        if not isinstance(house, str):
            raise ValueError("house must be string")
        self._house = house
obj = Class()
obj.set_house("New House") #set the house
print(obj.get_house()) #get the house

#has @propoerty
class MyClass:
    def __init__(self, house=None):
        self._house = house

    @property
    def house(self):
        return self._house

    @house.setter
    def house(self, house):
        if not isinstance(house, str):
            raise ValueError("house must be a string")
        self._house = house
obj = MyClass()
obj.house = 'My House'  # Set the house (calls the setter)
print(obj.house)         # Get the house (calls the getter)

#@staticmethod
#What it does: Defines a method within a class that doesn't require access to instance variables. 
# It behaves like a regular function but is logically grouped within the class.
#When to use it: When a method in a class doesn't need access to instance variables (attributes), and you want to logically associate it with the class.
# @classmethod
#What it does: Defines a method within a class that operates on the class itself, rather than 
# on instances of the class. It takes a reference to the class as its first parameter (cls).
#When to use it: When a method in a class needs to access or modify class-level variables or perform some action related to the class, not specific instances.


#inheritance is like if the other doesn't have a argument, they can borrow somewhere in class
class Container:
    def __init__(self, door):
        if not door:
            print("No door")
        self.door = door
        
class House(Container): #inside parentheses is inheritance
    def __init__(self, door):
        super().__init__(door)
        self.door = door

class Building(Container):
    def __init__(self, door):
        super().__init__(door)
        self.door = door

container = Container("Metal")
house = House("Wood")
building = Building("Automatic Door")

import numpy as np
import cv2 as cv

blank = np.zeros((1000, 800, 3 ), dtype="uint8")
#cv.imshow("Blank", blank)

cv.rectangle(blank, (200,100),(500,500), (0,255,0), thickness=2) # first is position(x,y), second width, height (x,y) third color
#cv.imshow("Rectangle", blank)

cv.putText(blank, "Name: ", (250,550), cv.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)
cv.imshow("Text", blank)

blur = cv.GaussianBlur(img, (7,7), cv.BORDER_DEFAULT)
cv.imshow('blur', blur)

canny = cv.Canny(blur, 125, 175)
cv.imshow('Canny Edges', canny)

dilate = cv.dilate(canny,(3,3), iterations=1)
cv.imshow('dDilate',dilate)

eroded = cv.eroded(dilate,(3,3), iterations=3)
cv.imshow('Eroded', eroded)

resize = cv.resize(img, (500,500), interpolation=cv.INTER_AREA)
cv.imshow('Resized', resize)

cropped = img[50:200, 200:400]
cv.imshow('Cropped', cropped)








cv.waitKey(0)