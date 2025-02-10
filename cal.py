import datetime
import calendar
import tkinter as tk
from tkinter import scrolledtext

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calendar")
        
        self.current_year = tk.IntVar()
        self.current_month = tk.IntVar()
        self.current_day = tk.IntVar()
        
        today = datetime.datetime.today()
        self.current_year.set(today.year)
        self.current_month.set(today.month)
        self.current_day.set(today.day)
        
        self.calendar_frame = tk.Frame(root)
        self.calendar_frame.pack(pady=20)
        
        self.create_widgets()
        self.update_calendar()
        
    def create_widgets(self):
        self.prev_button = tk.Button(self.calendar_frame, text="< Prev", command=self.prev_month)
        self.prev_button.grid(row=0, column=0, padx=10)
        
        self.next_button = tk.Button(self.calendar_frame, text="Next >", command=self.next_month)
        self.next_button.grid(row=0, column=6, padx=10)
        
        self.month_year_label = tk.Label(self.calendar_frame, textvariable="")
        self.month_year_label.grid(row=0, column=1, columnspan=5)
        
        for i, day in enumerate(calendar.day_abbr):
            day_label = tk.Label(self.calendar_frame, text=day)
            day_label.grid(row=1, column=i)
        
        self.date_buttons = [[None]*7 for _ in range(6)]
        for i in range(6):
            for j in range(7):
                self.date_buttons[i][j] = tk.Button(self.calendar_frame, text="", width=4, height=2, command=lambda i=i, j=j: self.show_date(i, j))
                self.date_buttons[i][j].grid(row=i+2, column=j, sticky="nsew")
                
        self.note_label = tk.Label(self.root, text="")
        self.note_label.pack()
        
        self.note_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=50, height=5)
        self.note_text.pack()

    def update_calendar(self):
        month_calendar = calendar.monthcalendar(self.current_year.get(), self.current_month.get())
        month_name = calendar.month_name[self.current_month.get()]
        self.month_year_label.config(text=f"{month_name} {self.current_year.get()}")
        
        # Pad the beginning and end of the month calendar with zeros
        while len(month_calendar) < 6:
            month_calendar.insert(0, [0] * 7)
        while len(month_calendar) > 6:
            month_calendar.pop()
        
        for i in range(6):
            for j in range(7):
                day = month_calendar[i][j]
                if day != 0:
                    self.date_buttons[i][j].config(text=day)
                else:
                    self.date_buttons[i][j].config(text="")
        
    def prev_month(self):
        if self.current_month.get() == 1:
            self.current_month.set(12)
            self.current_year.set(self.current_year.get() - 1)
        else:
            self.current_month.set(self.current_month.get() - 1)
        self.update_calendar()
        
    def next_month(self):
        if self.current_month.get() == 12:
            self.current_month.set(1)
            self.current_year.set(self.current_year.get() + 1)
        else:
            self.current_month.set(self.current_month.get() + 1)
        self.update_calendar()
        
    def show_date(self, row, column):
        date = self.date_buttons[row][column].cget("text")
        if date:
            day = int(date)
            note_label_text = f"Note for {day}/{self.current_month.get()}/{self.current_year.get()}:"
            self.note_label.config(text=note_label_text)
            self.note_text.delete("1.0", tk.END)
            self.note_text.pack()
    
            return frame

if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    
