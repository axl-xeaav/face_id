import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
import subprocess

import newbutton
import cal

# Initialize main window
root = tk.Tk()
root.title("Face Identification System")
root.geometry("1000x700")

# Set window icon
icon_path = "C://Users/user/Documents/coding_files/python/projects/fingerprint_scanner/fingerprint.png"
icon_image = Image.open(icon_path)
icon_image = icon_image.resize((32, 32), Image.LANCZOS)
icon_photo = ImageTk.PhotoImage(icon_image)
root.wm_iconphoto(True, icon_photo)

# Load and resize fingerprint image
image_path = "C://Users/user/Documents/coding_files/python/projects/fingerprint_scanner/fingerprint.png"
finger_image = Image.open(image_path)
finger_image = finger_image.resize((250, 250), Image.LANCZOS)
photo = ImageTk.PhotoImage(finger_image)

# Display fingerprint image
image_label = tk.Label(root, image=photo)
image_label.image = photo
image_label.place(x=5, y=5)

# Define functions for button actions
def newButton():
    newbutton.create_new_member_frame(main_frame)

def attendancebutton():
    cal.CalendarApp(main_frame)

def about_us():
    for widget in main_frame.winfo_children():
        widget.destroy()  # Clear previous widgets in main_frame

    label = tk.Label(main_frame, text="Created By:", font=('Tahoma', 20, 'bold'), bg='#f0f0f0')
    label.pack(pady=90)

    names = ["Daniel Pablo Amper", "Axel De Jesus", "Clarence A. Suan"]
    for name in names:
        name_label = tk.Label(main_frame, text=name, font=('Tahoma', 18), bg='#f0f0f0')
        name_label.pack(pady=20)

def members_list():
    for widget in main_frame.winfo_children():
        widget.destroy()
    member_label = tk.Label(main_frame, text="Loading...", font=('Arial', 18), bg='#f0f0f0')
    member_label.pack()
    subprocess.Popen(["C://Users/user/AppData/Local/MongoDBCompass/MongoDBCompass"])

# Change cursor on hover
def on_enter(event):
    event.widget.config(cursor="hand2")

def on_leave(event):
    event.widget.config(cursor="")

# Highlight active button
def hide_indicators():
    new_label.config(bg='#4CAF50')
    current_label.config(bg='#4CAF50')
    attendance_label.config(bg='#4CAF50')
    about_label.config(bg='#4CAF50')

def indicate(lb):
    hide_indicators()
    lb.config(bg='#45a049')

# Design of interface
options_frame = tk.Frame(root, bg="#4CAF50")  # Green background for sidebar

# Buttons for navigation
new_button = tk.Button(options_frame, text="New Member", font=('Arial', 15),
                       fg='white', bd=0, bg='#4CAF50', command=newButton)
new_button.place(x=10, y=150)
new_button.bind("<Enter>", on_enter)
new_button.bind("<Leave>", on_leave)

new_label = tk.Label(options_frame, text="", bg='#45a049')
new_label.place(x=3, y=150, width=5, height=40)

current_button = tk.Button(options_frame, text="Current Member", font=('Arial', 15),
                           fg='white', bd=0, bg='#4CAF50')
current_button.place(x=10, y=250)
current_button.bind("<Enter>", on_enter)
current_button.bind("<Leave>", on_leave)

current_label = tk.Label(options_frame, text="", bg='#45a049')
current_label.place(x=3, y=250, width=5, height=40)

member_button = tk.Button(options_frame, text="Members List", font=('Arial', 15),
                          fg='white', bd=0, bg='#4CAF50', command=members_list)
member_button.place(x=10, y=350)
member_button.bind("<Enter>", on_enter)
member_button.bind("<Leave>", on_leave)

attendance_label = tk.Label(options_frame, text="", bg='#45a049')
attendance_label.place(x=3, y=350, width=5, height=40)

attendance_button = tk.Button(options_frame, text="Attendance Records", font=('Arial', 15),
                              fg='white', bd=0, bg='#4CAF50', command=attendancebutton)
attendance_button.place(x=10, y=450)
attendance_button.bind("<Enter>", on_enter)
attendance_button.bind("<Leave>", on_leave)

attendance_label = tk.Label(options_frame, text="", bg='#45a049')
attendance_label.place(x=3, y=450, width=5, height=40)

about_button = tk.Button(options_frame, text="About Us", font=('Arial', 15),
                         fg='white', bd=0, bg='#4CAF50', command=about_us)
about_button.place(x=10, y=550)
about_button.bind("<Enter>", on_enter)
about_button.bind("<Leave>", on_leave)

about_label = tk.Label(options_frame, text="", bg='#45a049')
about_label.place(x=3, y=550, width=5, height=40)

options_frame.pack(side=tk.LEFT)
options_frame.pack_propagate(False)
options_frame.configure(width=200, height=700)

# Main content frame
main_frame = tk.Frame(root, highlightbackground="#e0e0e0", highlightthickness=2, bg='#f0f0f0')
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
main_frame.pack_propagate(False)
main_frame.configure(height=700, width=800)

root.mainloop()