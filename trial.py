from tkinter import *
root = Tk()

root.title("Backgroound")
root.geometry("500x500")

def background():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
def achievement():
    for widget in main_frame.winfo_children():
        widget.destroy()
def contact():
    for widget in main_frame.winfo_children():
        widget.destroy()




backg = Button(root, text="Background", command=background)
backg.place(x=50, y=20)
achievements = Button(root, text="Achievements", command=achievement)
achievements.place(x=100, y=60)
contact = Button(root, text="Contact Info", command=contact)
contact.place(x=150, y=100)





root.mainloop()