import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
import subprocess

import newbutton
import cal
'''
to fix
 - new button lagyan fingerprint label then for registering fingerprint aside from infos
 - current button put fingerprint to scan and searh database for matching fingerprint
 - put fingerprint image either top or bottom left

'''
root = tk.Tk()
root.title("Face Identification System")
root.geometry("1000x700")
icon_path = "C://Users/user/Documents/coding_files/python/projects/fingerprint_scanner/fingerprint.png"
icon_image = Image.open(icon_path)
icon_image = icon_image.resize((32, 32), Image.LANCZOS)
icon_photo = ImageTk.PhotoImage(icon_image)
root.wm_iconphoto(True, icon_photo)

image_path = "C://Users/user/Documents/coding_files/python/projects/fingerprint_scanner/fingerprint.png"
finger_image = Image.open(image_path)
finger_image = finger_image.resize((250, 250), Image.LANCZOS)
photo = ImageTk.PhotoImage(finger_image)


image_label = tk.Label(root, image=photo)
image_label.image = photo  
image_label.place(x=5, y=5)  

#show register form
def newButton():
    newbutton.create_new_member_frame(main_frame)

#show calendar
def attendancebutton():
    #print("Attendance Records Button Clicked")
    #CalendarApp(main_frame)
    cal.CalendarApp(main_frame)
#creators
def about_us():
    for widget in main_frame.winfo_children():
        widget.destroy()  # Clear previous widgets in main_frame

    label = tk.Label(main_frame, text="Created By:",font=('Tahoma', 20, 'bold'), bg='#068f2b')
    label.pack(pady=90)

    names = ["Daniel Pablo Amper", "Axel De Jesus", "Clarence A. Suan"]
    for name in names:
        name_label = tk.Label(main_frame, text=name, font=('Tahoma', 18), bg='#068f2b')
        name_label.pack(pady=20)

# show mongodb database collecction
def members_list():
    for widget in main_frame.winfo_children():
        widget.destroy()  
    member_label = tk.Label(text="Loading...", font=('Arial', 18))
    member_label.pack()
    subprocess.Popen(["C://Users/user/AppData/Local/MongoDBCompass/MongoDBCompass"])
#teach mongodb 

#change cursor in user interface
def on_enter(event):
    event.widget.config(cursor="hand2")  
#leave button crsor
def on_leave(event):
    event.widget.config(cursor="")  

#for highlighting
def hide_indicators():
    new_label.config(bg='#c3c3c3')
    current_label.config(bg='#c3c3c3')
    attendance_label.config(bg='#c3c3c3')
    about_label.config(bg='#c3c3c3')

#nakalimutan ko na nako
def indicate(lb):
    hide_indicators()
    lb.config(bg='#158aff')

# Design of interface
options_frame = tk.Frame(root, bg="#036ff2")

new_button = tk.Button(options_frame, text="New Member", font=('bold', 15),
                       fg='#003410', bd=0, bg= '#036ff2', command=newButton)
new_button.place(x=10, y=150)
new_button.bind("<Enter>", on_enter)  
new_button.bind("<Leave>", on_leave)  

new_label =  tk.Label(options_frame, text="", bg='#0f4d99')
new_label.place(x=3, y=150, width=5, height=40)

current_button  = tk.Button(options_frame, text="Current Member", font=('bold', 15),
                            fg='#003410', bd=0, bg= '#036ff2')
current_button.place(x=10, y=250)
current_button.bind("<Enter>", on_enter)  
current_button.bind("<Leave>", on_leave)  

current_label =  tk.Label(options_frame, text="", bg='#0f4d99')
current_label.place(x=3, y=250, width=5, height=40)

member_button = tk.Button(options_frame, text="Members List", font=('bold', 15),
                              fg='#003410', bd=0, bg= '#036ff2', command=members_list)
member_button.place(x=10, y=350)
member_button.bind("<Enter>", on_enter)  
member_button.bind("<Leave>", on_leave)  

attendance_label =  tk.Label(options_frame, text="", bg='#0f4d99')
attendance_label.place(x=3, y=350, width=5, height=40)

attendance_button = tk.Button(options_frame, text="Attendance Records", font=('bold', 15),
                              fg='#003410', bd=0, bg= '#036ff2', command=attendancebutton)
attendance_button.place(x=10, y=450)
attendance_button.bind("<Enter>", on_enter)  
attendance_button.bind("<Leave>", on_leave)  

attendance_label =  tk.Label(options_frame, text="", bg='#0f4d99')
attendance_label.place(x=3, y=450, width=5, height=40)

about_button = tk.Button(options_frame, text="About Us", font=('bold', 15),
                         fg='#003410', bd=0, bg= '#036ff2', command=about_us)
about_button.place(x=10, y=550)
about_button.bind("<Enter>", on_enter)  
about_button.bind("<Leave>", on_leave)  

about_label =  tk.Label(options_frame, text="", bg='#0f4d99')
about_label.place(x=3, y=550, width=5, height=40)

options_frame.pack(side=tk.LEFT)
options_frame.pack_propagate(False)
options_frame.configure(width=200, height=700)

main_frame = tk.Frame(root,highlightbackground="black", 
                      highlightthickness=5,) #bg=#068f2b
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
main_frame.pack_propagate(False)
main_frame.configure(height=700, width=800)

root.mainloop()
