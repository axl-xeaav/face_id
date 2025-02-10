import sys
import time
import re
import pymongo

members = pymongo.MongoClient("mongodb://localhost:27017/")
db = members["church"]
collection = db["members"]

def acceptTerms():
    print("Welcome to our service...") 
    time.sleep(2)

    while True:
        print("Before you proceed, please review and accept our privacy terms and regulations.")
        response = input("Do you accept our privacy terms and regulations? (yes/no): ").lower()
        if response == "yes":
            print("Thank you for accepting our privacy terms and regulations. You can proceed.")
            break
        elif response == "no":
            print("You need to accept our privacy terms and regulations to use our service.")
            print("Thank you for visiting. Goodbye!")
            sys.exit()
            time.sleep(3)
        else:
            print("Invalid response. Please enter 'yes' or 'no'.")

def idTag():
    idTag = ["Administrator", "Member"]

    print("Please pick a number: ")
    for i in range(1, 3):
        print(f"{i}. {idTag[i-1]}")

    option = None
    while option not in range(1, 3):
        try:
            option = int(input("Pick a number: "))
        except ValueError:
            print("Please put a number only.")
    chosenOption = idTag[option - 1]
    print(f"You selected: ", chosenOption)
    return chosenOption

def titles():
    titles = ["Sr.", "Ms.", "Mr.", "Mrs."]
    print("Please pick a number: ")
    for i in range(1, 5):
        print(f"{i}. {titles[i-1]}")

    option = None
    while option not in range(1, 5):
        try:
            option = int(input("Pick a number: "))
        except ValueError:
            print("Please put a number only.")

    nameTitle = titles[option-1]
    return nameTitle  

def fullname(nameTitle):  
    while True:
        fullName = input("Enter Full Name: ")
        if not fullName or any(c.isdigit() for c in fullName) or len(fullName) < 2:
            print("Please enter a valid full name.")
        else:
            break
    if "<" in fullName:
        last, first = fullName.split(",")
        fullName = f"{first} {last}" 
    return f"Hello, {nameTitle} {fullName}"
    return fullName

def address():
    address = input("Enter your address: ")
    return address

def birthday():
    while True:
        bday = input("When is your Birthdate? MM/DD//YY: ")
        if len(bday) != 8:
            print("Please put only numbers and slash. e.g 08/18/02")
            continue
        else:
            return bday
            break

def phonenumber():
    while True:
        try:
            phoneNumber = input("Enter your phone number: ")
            if len(phoneNumber) != 11:
                print("Check Number Again")
                continue
            else:
                return phoneNumber
        except ValueError:
            print("Invalid input. Please enter a valid phone number.")

def Occupation():
    occupation = input("What is your occupation? ")
    return occupation

def userInformation(chosenOption, fullName, address, bday, phoneNumber, occupation):
    print("User Information: ")
    print("ID Tag: ", chosenOption)
    print("Name: ", fullName)
    print("Address: ", address)
    print(f"Birthday: {bday}")
    print("Phone Number: ", phoneNumber)
    print("Occupation: ", occupation)

acceptTerms()
chosenOption = idTag()
nameTitle = titles()
fullName = fullname(nameTitle)
address = address()
bday = birthday()
phoneNumber = phonenumber()
occupation = Occupation()

userInformation(chosenOption, fullName, address, bday, phoneNumber, occupation)
def checkInfo():
    while True:
        checking = input("Are all informations correct? Yes/No: ").lower()
        if checking == 'yes':
            break
        else:
            category = input("What category is incorrect: 1. Id Tag 2. Name 3. Phone Number 4. Address 5. Occupation: ")
            if category == '1':
                fullName = input("Enter your Id Tag again(Either Administrator  or Member): ")
            elif category == '2':
                phoneNumber = input("Enter your Full Name again: ")
            elif category == '3':
                address = input("Enter your Phone Number again: ")
            elif category == '4':
                occupation = input("Enter your Address again: ")
            elif category == '5':
                occupation = input("Enter your Occupation again: ")
            else:
                print("You are registered")
                sys.exit
checkInfo()

document = {"ID Tag": chosenOption, "Name": fullName, "Address": address, "Phone Number": phoneNumber, "Occupation": occupation}
lists = collection.insert_one(document)
print("You are registered.")

#fix this, should loop again if the user type yes. current problem is address
def nextPerson(addr):
    next_input = input("Next Person to register? (Yes or No): ")
    if next_input.lower() == "yes":
        acceptTerms()
        chosen_option = idTag()
        name_title = titles()
        full_name = fullname(name_title)
        address = addr()
        bday = birthday()
        phone_number = phonenumber()
        occupation = Occupation()
        userInformation(chosen_option, full_name, address, bday, phone_number, occupation)
        check_info = checkInfo()
        return True
    else:
        print("Thank you and goodbye.")
        time.sleep(1)
        return False

# Main loop for registering users
while nextPerson(address):
    pass

