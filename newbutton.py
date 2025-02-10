import tkinter as tk
from tkinter import Label, Entry, Button
from tkcalendar import DateEntry
from datetime import datetime
from pymongo import MongoClient
from tkinter import messagebox

def create_new_member_window():
    new_window = tk.Toplevel()
    new_window.geometry("500x400")

    create_new_member_frame(new_window)

def create_new_member_frame(parent_frame):
    # MongoDB connection setup
    client = MongoClient("mongodb://localhost:27017/")
    db = client["church"]
    members_collection = db["members"]

    # Clear the parent frame
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    # Create a new frame or set of widgets within the parent frame
    frame = tk.Frame(parent_frame, bg='#068f2b')
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Create a heading label with specific font styling
    heading_label = Label(frame, text="Register Member:", font=("Verdana", 30, "bold"), fg="blue", bg='#068f2b')
    heading_label.pack(pady=25)
    
    start_y = 40  # Define the starting y-coordinate

    name_label = Label(frame, text="Enter Name:", font=("Comic Sans MS", 16, "bold"),bg='#068f2b')
    name_label.place(x=40, y=start_y + 60)
    name_entry = Entry(frame, bg='#068f2b', width=800, font=("Helvetica", 16))
    name_entry.place(x=250, y=start_y + 70, width=300)

    address_label = Label(frame, text="Enter Address:", font=("Comic Sans MS", 16, "bold"), bg='#068f2b')
    address_label.place(x=40, y=start_y + 100)
    address_entry = Entry(frame, font=("Helvetica", 16),  bg='#068f2b')
    address_entry.place(x=250, y=start_y + 110, width=300)

    phone_label = Label(frame, text="Enter Phone Number:", font=("Comic Sans MS", 14, "bold"), bg='#068f2b')
    phone_label.place(x=40, y=start_y + 140)
    phone_entry = Entry(frame, font=("Helvetica", 16),  bg='#068f2b')
    phone_entry.place(x=250, y=start_y + 150, width=300)

    birthday_label = Label(frame, text="Enter Birthday:", font=("Comic Sans MS", 14, "bold"), bg='#068f2b')
    birthday_label.place(x=40, y=start_y + 180)
    birthday_entry = DateEntry(frame, width=17, year=2000, date_pattern='y-mm-dd',
                            selectbackground='blue', selectforeground='white', background='white', foreground='black')
    birthday_entry.place(x=250, y=start_y + 190, width=300)

    occupation_label = Label(frame, text="Enter Occupation:", font=("Comic Sans MS", 16, "bold"), bg='#068f2b')
    occupation_label.place(x=40, y=start_y + 220)
    occupation_entry = Entry(frame, font=("Helvetica", 16),  bg='#068f2b')
    occupation_entry.place(x=250, y=start_y + 230, width=300)


    age_label = Label(frame, text="Age: ", font=("Comic Sans MS", 16, "bold"), bg='#068f2b')
    age_label.place(x=40, y=start_y + 260)
    age_value_label = Label(frame, text="", font=("Helvetica", 16),  bg='#068f2b')
    age_value_label.place(x=250, y=start_y + 270)

    fingerprint_label = Label(frame, text="Fingerprint ", font=("Helvetica", 16),  bg='#068f2b')
    fingerprint_label.place(x=300, y=start_y + 260)
    fingerprint_checker = Label(frame, text="", bg='#068f2b')
    fingerprint_checker.place(x=350, y=start_y + 300)
    
    def calculate_age():
        try:
            birthday = datetime.strptime(birthday_entry.get(), '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            age_value_label.config(text=str(age))
        except Exception as e:
            print("Error in date format:", e)
            birthday_entry.configure(background="red")

    # Bind the date selection event to the age calculation
    birthday_entry.bind("<<DateEntrySelected>>", lambda event: calculate_age())

    def validate_entries():
        valid = True

        name = name_entry.get()
        if any(char.isdigit() for char in name) or not name:
            name_entry.config(bg="red")
            valid = False
        else:
            name_entry.config(bg="white")

        phone = phone_entry.get()
        if not phone.isdigit() or len(phone) != 11 or not phone:
            phone_entry.config(bg="red")
            valid = False
        else:
            phone_entry.config(bg="white")

        address = address_entry.get()
        if not address:
            address_entry.config(bg="red")
            valid = False
        else:
            address_entry.config(bg="white")
        
        occupation = occupation_entry.get()
        if not occupation:
            occupation_entry.config(bg="red")
            valid = False
        else:
            occupation_entry.config(bg="white")

        birthday_entry.config(background="white")  

        calculate_age()

        if valid:
            save_to_database(name, address, phone, birthday_entry.get(), occupation, age_value_label.cget("text"))
        else:
            print("Some entries are invalid. Please correct them.") 

    def save_to_database(name, address, phone, birthday, occupation, age):
        member_data = {
            "name": name,
            "address": address,
            "phone": phone,
            "birthday": birthday,
            "occupation": occupation,
            "age": int(age)
        }
        try:
            members_collection.insert_one(member_data)
            messagebox.showinfo("Success", "Member registered successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to database: {e}")

    submit_button = Button(frame, text="Submit", font=("Comic Sans MS", 16, "bold"),bg='#068f2b', command=validate_entries)
    submit_button.place(x=200, y=start_y + 300)

    return frame
