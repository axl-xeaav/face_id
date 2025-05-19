import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from datetime import datetime
import mysql.connector
import cv2
import os
import numpy as np
import csv

# APP CONFIGURATION

class AppConfig:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'mypassword',
        'database': 'mydb'
    }
    COLOR_SCHEME = {
        'primary': '#4CAF50',
        'primary_dark': '#45a049',
        'form_bg': '#068f2b',
        'main_bg': '#f0f0f0'
    }
    FONTS = {
        'title': ('Verdana', 30, 'bold'),
        'heading': ('Comic Sans MS', 16, 'bold'),
        'body': ('Helvetica', 16)
    }

# DATABASE HANDLER

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(**AppConfig.DB_CONFIG)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    face_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    address VARCHAR(255),
                    phone_number VARCHAR(20),
                    bday DATE,
                    occupation VARCHAR(100),
                    age INT,
                    face_image VARCHAR(255)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    face_id INT NOT NULL,
                    date DATE NOT NULL,
                    time_in TIME NOT NULL,
                    FOREIGN KEY (face_id) REFERENCES members(face_id)
                )
            """)
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Error creating tables: {str(e)}")

    def register_member(self, member_data):
        try:
            query = """
                INSERT INTO members 
                (full_name, address, phone_number, bday, occupation, age, face_image) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, member_data)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            messagebox.showerror("Database Error", f"Error: {str(e)}")
            return None

# FACE RECOGNITION

class FaceRecognizer:
    def __init__(self, db):
        self.db = db
        
        # Initialize face recognizer with fallbacks
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            try:
                self.recognizer = cv2.face.createLBPHFaceRecognizer()
            except AttributeError:
                self.recognizer = cv2.face_FaceRecognizer.createLBPHFaceRecognizer()
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.recognizer_trained = False
        self.today_attendance = set()
        self.load_current_date_attendance()
        
    def load_current_date_attendance(self):
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            self.db.cursor.execute("SELECT face_id FROM attendance WHERE date = %s", (today,))
            self.today_attendance = {row[0] for row in self.db.cursor.fetchall()}
        except Exception as e:
            print(f"Warning: Could not load attendance. Error: {str(e)}")
            self.today_attendance = set()

    def train_recognizer(self):
        try:
            self.db.cursor.execute("SELECT face_id, face_image FROM members")
            faces = self.db.cursor.fetchall()
            
            if not faces:
                messagebox.showwarning("Warning", "No faces in database to train recognizer")
                return
                
            face_samples = []
            ids = []
            
            for face_id, img_path in faces:
                if os.path.exists(img_path):
                    pil_img = Image.open(img_path).convert('L')
                    img_numpy = np.array(pil_img, 'uint8')
                    face_samples.append(img_numpy)
                    ids.append(face_id)
                else:
                    print(f"Warning: Image not found at {img_path}")
            
            if face_samples:
                self.recognizer.train(face_samples, np.array(ids))
                self.recognizer_trained = True
                print(f"Recognizer trained with {len(face_samples)} samples")
            else:
                messagebox.showwarning("Warning", "No valid face images found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to train recognizer: {str(e)}")

    def recognize_faces(self):
        if not self.recognizer_trained:
            self.train_recognizer()
            if not self.recognizer_trained:
                return 0

        cam = cv2.VideoCapture(0)
        cam.set(3, 640)
        cam.set(4, 480)
        
        attendance_count = len(self.today_attendance)
        min_confidence = 60  # Lowered from 70 to be more strict
        min_face_size = 15000
        required_confirmations = 5  # Require N consistent recognitions
        confirmations = 0
        last_face_id = None
        last_name = None

        
        while True:
            ret, img = cam.read()
            if not ret:
                print("Error: Could not read frame.")
                break
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,  # Increased from 1.1
                minNeighbors=6,   # Increased from 5
                minSize=(120, 120)) # Increased from 100
            
            for (x, y, w, h) in faces:
                face_area = w * h
                if face_area < min_face_size:
                    continue
                    
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                face_id, confidence = self.recognizer.predict(gray[y:y+h, x:x+w])
                
                if confidence < min_confidence:
                    self.db.cursor.execute("SELECT full_name FROM members WHERE face_id = %s", (face_id,))
                    result = self.db.cursor.fetchone()
                    
                    if result:
                        current_name = result[0]
                        
                        # Verification system
                        if face_id == last_face_id:
                            confirmations += 1
                        else:
                            confirmations = 1
                            last_face_id = face_id
                            last_name = current_name
                        
                        # Only show name after multiple confirmations
                        if confirmations >= required_confirmations:
                            display_text = f"{last_name} ({100-confidence:.1f}%)" #display confidence level
                            cv2.putText(img, display_text, (x+5, y-5), self.font, 1, (0, 255, 0), 2)
                            
                            if face_id not in self.today_attendance:
                                self.record_attendance(face_id)
                                self.today_attendance.add(face_id)
                                attendance_count += 1
                                print(f"Verified attendance for {last_name}")
                        else:
                            cv2.putText(img, "Verifying...", (x+5, y-5), self.font, 1, (255, 255, 0), 2)
                else:
                    cv2.putText(img, "Unknown", (x+5, y-5), self.font, 1, (0, 0, 255), 2)
                    confirmations = 0
                    
            cv2.putText(img, f"Attendance Today: {attendance_count}", (10, 30), 
                       self.font, 1, (0, 255, 0), 2)
            cv2.imshow('Face ID System', img)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
        cam.release()
        cv2.destroyAllWindows()
        return attendance_count
        
    def record_attendance(self, face_id):
        try:
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M:%S')
            
            self.db.cursor.execute("""
                INSERT INTO attendance (face_id, date, time_in)
                VALUES (%s, %s, %s)
            """, (face_id, date_str, time_str))
            self.db.conn.commit()
            print(f"Attendance recorded for ID: {face_id}")
        except Exception as e:
            print(f"Error recording attendance: {str(e)}")
            self.db.conn.rollback()

# FACE SCANNER FOR REGISTRATION

def face_scanning(name, preview_callback=None):
    cam = cv2.VideoCapture(0)
    cam.set(3, 640)
    cam.set(4, 480)
    
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print(f"\n [INFO] Initializing face capture for {name}. Look at the camera...")
    
    img_path = f"dataset/{name}.jpg"
    
    if not os.path.exists("dataset"):
        os.makedirs("dataset")
    
    best_face = None
    start_time = datetime.now()
    preview_shown = False
    
    while True:
        ret, img = cam.read()
        if not ret:
            continue
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Wait for 5 seconds before capturing
            if (datetime.now() - start_time).total_seconds() >= 5:
                best_face = gray[y:y+h, x:x+w]
                
                # Show preview 
                if preview_callback and not preview_shown:
                    color_face = img[y:y+h, x:x+w]
                    color_face = cv2.cvtColor(color_face, cv2.COLOR_BGR2RGB)
                    preview_callback(color_face)
                    preview_shown = True
                
        cv2.imshow('Register Face', img)
        
        if best_face is not None or cv2.waitKey(1) & 0xFF == 27:
            break
            
    if best_face is not None:
        cv2.imwrite(img_path, best_face)
        print("\n [INFO] Face captured and saved to dataset")
    else:
        print("\n [INFO] Face capture cancelled")
        img_path = None
        
    cam.release()
    cv2.destroyAllWindows()
    return img_path

# REGISTRATION FORM

class RegistrationForm:
    def __init__(self, parent, db, on_success_callback):
        self.frame = tk.Frame(parent, bg=AppConfig.COLOR_SCHEME['form_bg'])
        self.db = db
        self.on_success = on_success_callback
        self.preview_label = None
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(
            self.frame, 
            text="Register Member:", 
            font=AppConfig.FONTS['title'], 
            fg="blue", 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).pack(pady=25)

        self.entries = {}
        fields = [
            ('Name', 'name', 80),
            ('Address', 'address', 120),
            ('Phone Number', 'phone', 155),
            ('Occupation', 'occupation', 240)
        ]

        for label, key, y_pos in fields:
            tk.Label(
                self.frame, 
                text=f"Enter {label}:", 
                font=AppConfig.FONTS['heading'], 
                bg=AppConfig.COLOR_SCHEME['form_bg']
            ).place(x=25, y=y_pos)
            
            self.entries[key] = tk.Entry(self.frame, font=AppConfig.FONTS['body'])
            self.entries[key].place(x=250, y=y_pos+10, width=300)

        tk.Label(
            self.frame, 
            text="Enter Birthday:", 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=25, y=185)
        
        self.birthday_entry = DateEntry(
            self.frame, 
            width=17, 
            year=2000, 
            date_pattern='y-mm-dd',
            font=AppConfig.FONTS['body']
        )
        self.birthday_entry.place(x=250, y=200, width=300)

        tk.Label(
            self.frame, 
            text="Age:", 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=40, y=280)
        
        self.age_label = tk.Label(
            self.frame, 
            text="", 
            font=AppConfig.FONTS['body'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        )
        self.age_label.place(x=250, y=290)
        
        self.birthday_entry.bind("<<DateEntrySelected>>", lambda e: self.calculate_age())

        submit_btn = tk.Button(
            self.frame,
            text="Register",
            font=AppConfig.FONTS['heading'],
            command=self.validate,
            bg=AppConfig.COLOR_SCHEME['primary'],
            fg='white'
        )
        self.preview_frame = tk.Frame(self.frame, bg='white', width=200, height=200)
        self.preview_frame.place(x=600, y=100)
        
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack(fill='both', expand=True)
        
        # Modify submit button
        submit_btn = tk.Button(
            self.frame,
            text="Scan Face & Register",
            font=AppConfig.FONTS['heading'],
            command=self.validate,
            bg=AppConfig.COLOR_SCHEME['primary'],
            fg='white'
        )
        submit_btn.place(x=400, y=320)
        submit_btn.place(x=400, y=320)
        submit_btn.bind("<Enter>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary_dark']))
        submit_btn.bind("<Leave>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary']))
    def show_preview(self, img_array):
        """Show preview of the captured face"""
        img = Image.fromarray(img_array)
        img.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(img)
        
        self.preview_label.config(image=photo)
        self.preview_label.image = photo  # Keep reference

    def calculate_age(self):
        try:
            birthday = datetime.strptime(self.birthday_entry.get(), '%Y-%m-%d')
            age = datetime.today().year - birthday.year
            if (datetime.today().month, datetime.today().day) < (birthday.month, birthday.day):
                age -= 1
            self.age_label.config(text=str(age))
        except ValueError:
            pass

    def validate(self):
        valid = True
        name = self.entries['name'].get().strip()
        phone = self.entries['phone'].get().strip()
        
        if not name or any(char.isdigit() for char in name):
            self.entries['name'].config(bg="red")
            valid = False
        
        if not phone.isdigit() or len(phone) != 11:
            self.entries['phone'].config(bg="red")
            valid = False

        if valid:
            self.register_member()

    def register_member(self):
        name = self.entries['name'].get().strip()
        
        # First show preview, then confirm
        img_path = face_scanning(name.replace(" ", "_"), preview_callback=self.show_preview)
        
        if img_path:
            if messagebox.askyesno("Confirm", "Save this face image?"):
                member_data = (
                    name,
                    self.entries['address'].get().strip(),
                    self.entries['phone'].get().strip(),
                    self.birthday_entry.get(),
                    self.entries['occupation'].get().strip(),
                    self.age_label.cget("text"),
                    img_path
                )
                
                if self.db.register_member(member_data):
                    messagebox.showinfo("Success", "Member registered successfully!")
                    self.on_success()
            else:
                # Delete the captured image if user cancels
                if os.path.exists(img_path):
                    os.remove(img_path)
# MAIN APPLICATION

class FaceIDSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Identification System")
        self.root.geometry("1000x700")
        self.db = Database()
        self.setup_ui()
        
        try:
            img = Image.open("fingerprint.png").resize((100, 100), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            tk.Label(root, image=self.bg_image).place(x=5, y=5)
        except FileNotFoundError:
            pass

    def setup_ui(self):
        self.sidebar = tk.Frame(
            self.root, 
            bg=AppConfig.COLOR_SCHEME['primary'], 
            width=240, 
            height=700
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_frame = tk.Frame(
            self.root, 
            bg=AppConfig.COLOR_SCHEME['main_bg'], 
            highlightbackground="#e0e0e0", 
            highlightthickness=2
        )
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.create_nav_buttons()
        self.show_home()

    def create_nav_buttons(self):
        buttons = [
            ("Register Member", self.show_register),
            ("Open Face ID", self.show_home),
            ("Members List", self.show_database),
            ("Attendance Records", self.show_records),
            ("About Us", self.show_about)

        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=('Arial', 15),
                fg='white',
                bd=0,
                bg=AppConfig.COLOR_SCHEME['primary'],
                command=command
            )
            btn.place(x=10, y=150 + i*100, width=220)
            btn.bind("<Enter>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary_dark']))
            btn.bind("<Leave>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary']))

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_frame()
        
        tk.Label(
            self.main_frame, 
            text="Face ID System", 
            font=('Arial', 24, 'bold'), 
            bg=AppConfig.COLOR_SCHEME['main_bg']
        ).pack(pady=20)
        
        start_btn = tk.Button(
            self.main_frame,
            text="Start Face Recognition",
            command=self.start_face_recognition,
            font=('Arial', 16),
            bg='#4CAF50',
            fg='white',
            width=25,
            height=2
        )
        start_btn.pack(pady=50)
        
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            self.db.cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = %s", (today,))
            count = self.db.cursor.fetchone()[0]
        except:
            count = 0
    
        self.attendance_label = tk.Label(
            self.main_frame,
            text=f"Attendance Today: {count}",
            font=('Arial', 16),
            bg=AppConfig.COLOR_SCHEME['main_bg']
        )
        self.attendance_label.pack(pady=20)
        
        tk.Label(
            self.main_frame,
            text="Instructions:\n1. Click 'Start Face Recognition'\n2. Look at the camera\n3. Press ESC to exit",
            font=('Arial', 14),
            bg=AppConfig.COLOR_SCHEME['main_bg'],
            justify='left'
        ).pack(pady=20)

    def start_face_recognition(self):
        if not hasattr(self, 'face_recognizer'):
            self.face_recognizer = FaceRecognizer(self.db)
    
        new_count = self.face_recognizer.recognize_faces()
        self.attendance_label.config(text=f"Attendance Today: {new_count}")

    def show_register(self):
        self.clear_frame()
        RegistrationForm(self.main_frame, self.db, self.show_home).frame.pack(fill="both", expand=True)

    def show_database(self):
        self.clear_frame()

        title_label = tk.Label(
            self.main_frame,
            text="Members List",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        )
        title_label.pack(pady=10)

        tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Name", "Address", "Phone", "Birthday", "Age", "Occupation", "Actions"),
            show="headings",
            height=20
        )

        columns = [
            ("ID", 50, 'center'),
            ("Name", 150, 'w'),
            ("Address", 200, 'w'),
            ("Phone", 100, 'center'),
            ("Birthday", 100, 'center'),
            ("Age", 50, 'center'),
            ("Occupation", 150, 'w'),
            ("Actions", 100, 'center')
        ]

        for col, width, anchor in columns:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=anchor)

        try:
            self.db.cursor.execute("""
                SELECT face_id, full_name, address, phone_number, 
                        DATE_FORMAT(bday, '%Y-%m-%d') as birthday, 
                        age, occupation
                FROM members
                ORDER BY face_id
            """)
            members_data = self.db.cursor.fetchall()
            
            for member in members_data:
                tree.insert("", tk.END, values=(*member, "Delete"))
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load members: {str(e)}")

        y_scroll = ttk.Scrollbar(self.main_frame, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(self.main_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        tree.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")

        def on_tree_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                if column == "#8":
                    item = tree.identify_row(event.y)
                    face_id = tree.item(item)['values'][0]
                    
                    if messagebox.askyesno("Confirm", "Permanently delete from database?"):
                        try:
                            # First delete attendance records
                            self.db.cursor.execute("DELETE FROM attendance WHERE face_id = %s", (face_id,))
                            # Then delete member
                            self.db.cursor.execute("DELETE FROM members WHERE face_id = %s", (face_id,))
                            deleted_rows = self.db.cursor.rowcount
                            self.db.conn.commit()
                            
                            if deleted_rows > 0:
                                messagebox.showinfo("Success", "Deleted from database")
                                self.show_database()
                            else:
                                messagebox.showerror("Error", "No member found with this ID")
                                
                        except Exception as e:
                            self.db.conn.rollback()
                            messagebox.showerror("Error", f"Database deletion failed: {str(e)}")

        tree.bind("<Button-1>", on_tree_click)

        btn_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        btn_frame.pack(pady=10)

        refresh_btn = tk.Button(
            btn_frame,
            text="Refresh",
            command=self.show_database,
            bg='#4CAF50',
            fg='white',
            width=15
        )
        refresh_btn.pack(side='left', padx=5)
    
    def show_records(self):
        self.clear_frame()

        title_label = tk.Label(
        self.main_frame,
        text="Attendance Records",
        font=('Arial', 16, 'bold'),
        bg='#f0f0f0'
    )
        title_label.pack(pady=10)

        tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Name", "Date", "Time In"),
            show="headings",
            height=20
        )

        columns = [
            ("ID", 50, 'center'),
            ("Name", 150, 'w'),
            ("Date", 100, 'center'),
            ("Time In", 100, 'center')
        ]

        for col, width, anchor in columns:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=anchor)

        try:
            self.db.cursor.execute("""
                SELECT a.id, m.full_name, a.date, a.time_in 
                FROM attendance a
                JOIN members m ON a.face_id = m.face_id
                ORDER BY a.date DESC, a.time_in DESC
            """)
            attendance_data = self.db.cursor.fetchall()
            
            for record in attendance_data:
                tree.insert("", tk.END, values=record)
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load attendance: {str(e)}")

        y_scroll = ttk.Scrollbar(self.main_frame, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(self.main_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        tree.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")

        btn_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        btn_frame.pack(pady=10)

        refresh_btn = tk.Button(
            btn_frame,
            text="Refresh",
            command=self.show_records,
            bg='#4CAF50',
            fg='white',
            width=15
        )
        refresh_btn.pack(side='left', padx=5)

    def show_about(self):
        self.clear_frame()
        tk.Label(
            self.main_frame, 
            text="Created By:", 
            font=('Arial', 20), 
            bg=AppConfig.COLOR_SCHEME['main_bg']
        ).pack(pady=50)
        
        for name in ["Daniel Pablo Amper", "Axel De Jesus", "Clarence A. Suan"]:
            tk.Label(
                self.main_frame, 
                text=name, 
                font=('Arial', 16), 
                bg=AppConfig.COLOR_SCHEME['main_bg']
            ).pack(pady=10)
        
        for texts in ["This is Capstone Project"]:
            tk.Label(
                self.main_frame, 
                text=name, 
                font=('Arial', 16), 
                bg=AppConfig.COLOR_SCHEME['main_bg']
            ).pack(pady=20)

# RUN APPLICATION
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceIDSystem(root)
    root.mainloop()

# issues
# 1. add picture preview when registering before confirming it
# 2. different user wrong name display
