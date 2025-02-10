from tkinter import *
from datetime import datetime

def submit():
    name = entry.get()
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    result_label.config(text=f"Hello {name}, You registered at {current_time}")

root = Tk()
root.title("Datetime")

just = Label(root, text="Enter Name: ")
just.pack(pady=10)


entry = Entry(root, width=30)
entry.pack(pady=10)

# Button to submit the name and display date and time
submit_button = Button(root, text="Submit", command=submit)
submit_button.pack()

# Label to display the result
result_label = Label(root, text="")
result_label.pack(pady=10)

root.mainloop()
