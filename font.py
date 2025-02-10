import tkinter as tk
from tkinter import font

root = tk.Tk()

# Get list of available fonts
available_fonts = font.families()

# Print out all available fonts
for font_family in available_fonts:
    print(font_family)

root.mainloop()
