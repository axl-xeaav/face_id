from tkinter import *
from PIL import Image, ImageTk
import subprocess


root = Tk() 
root.title("FingerprintChecker")
icon = PhotoImage(file= "C:\\Users\\user\\Documents\\pythonProjects\\CapstoneFiles\\fingerprint.png")
root.wm_iconphoto(True, icon)
root.geometry("1300x900")


def member_list():
    try:
        church = "church"  #database name
        connection_string = f"mongodb://localhost:27017/{church}"
        subprocess.Popen(["C:\\Users\\user\\AppData\\Local\\MongoDBCompass\\MongoDBCompass", connection_string])
    except Exception as e:
        print("Error opening MongoDB Compass, please restart again.", e)


def new_member():  # Define new_member here
    #try to fix the shaded radiobutton when running this file
    import newbutton
    print("jiu")

def current_member(): 
    current_button.pack_forget()
    print("haha")

def attendance_checker(): 
    attendance_checker_button.pack_forget()
    print("kl")

def about_us(): 
    about_us_button.pack_forget()
    print("js")


#designing the main menu interface

wallpaper_path = "C:/Users/user/Documents/pythonProjects/CapstoneFiles/wallpaper.jpg"
wallpaper_image = Image.open(wallpaper_path)
resized_wallpaper = wallpaper_image.resize((1300, 900), Image.LANCZOS)
wallpaper = ImageTk.PhotoImage(resized_wallpaper)

# Create label for wallpaper and pack it for fullscreen
wallpaper_label = Label(root, image=wallpaper)
wallpaper_label.pack(fill=BOTH, expand=True)

#create buttons 
button_frame = Frame(root, bg="black")  
button_frame.place(relx=0.5, rely=0.6, anchor=CENTER)

new_member = Button(button_frame, text="New Member", command= new_member, bg="yellow", border=10,borderwidth=12, highlightthickness=0, highlightbackground="white", width=60, height=5)
new_member.grid(row=0, pady=10)

current_button = Button(button_frame, text="Current Member", command=current_member, border=10, bg="yellow", borderwidth=12, highlightthickness=0, highlightbackground="white", width=60, height=5)
current_button.grid(row=1, pady=10)

member_list_button = Button(button_frame, text="Member List", command=member_list, border=10, bg="yellow", borderwidth=12, highlightthickness=0, highlightbackground="white", width=60, height=5)
member_list_button.grid(row=2, pady=10)

attendance_checker_button = Button(button_frame, text="Attendance Records", command=attendance_checker, border=10, bg="yellow", borderwidth=12, highlightthickness=0, highlightbackground="white", width=60, height=5)
attendance_checker_button.grid(row=3, pady=10)

about_us_button = Button(button_frame, text="About Us", command=about_us, border=10, bg="yellow", borderwidth=12, highlightthickness=0, highlightbackground="white", width=60, height=5)
about_us_button.grid(row=4, pady=10)



root.mainloop()
