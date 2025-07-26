import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from datetime import datetime
import mysql.connector
import cv2
import os
from deepface import DeepFace
import logging
import traceback
from hashlib import sha256
from tkinter import simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont

logging.getLogger('tensorflow').disabled = True  # Disable TensorFlow logging

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
        self._force_create_tables()  # Replace create_tables with this
        self._populate_default_admin()

    def _force_create_tables(self):
        """Forcefully recreates all tables with correct schema"""
        try:
            # Drop tables if they exist (WARNING: This will delete all data)
            self.cursor.execute("DROP TABLE IF EXISTS attendance")
            self.cursor.execute("DROP TABLE IF EXISTS members")
            self.cursor.execute("DROP TABLE IF EXISTS admin_users")
            
            # Recreate members table with all required columns
            self.cursor.execute("""
                CREATE TABLE members (
                    face_id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    middle_initial CHAR(3),
                    last_name VARCHAR(100) NOT NULL,
                    address VARCHAR(255),
                    contact_number VARCHAR(11),
                    bday DATE,
                    age INT,
                    sex CHAR(1),
                    face_image VARCHAR(255), 
                    is_deceased BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Recreate other tables
            self.cursor.execute("""
                CREATE TABLE attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    face_id INT NOT NULL,
                    date DATE NOT NULL,
                    time_in TIME NOT NULL,
                    FOREIGN KEY (face_id) REFERENCES members(face_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE admin_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL DEFAULT 'admin',
                    password_hash VARCHAR(255) NOT NULL,
                    security_question_answer VARCHAR(100) NOT NULL DEFAULT 'dog',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            print("Database tables recreated successfully")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Database Error", f"Error creating tables: {str(e)}")
            raise
            

    def _ensure_columns_exist(self):
        """Ensure all required columns exist in the members table"""
        try:
            # List of columns to check/add
            columns = [
                ('sex', "CHAR(1)"),
                ('is_deceased', "BOOLEAN DEFAULT FALSE")
            ]
            
            for column_name, column_def in columns:
                self.cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = 'members' AND column_name = '{column_name}'
                """)
                if self.cursor.fetchone()[0] == 0:
                    self.cursor.execute(f"ALTER TABLE members ADD COLUMN {column_name} {column_def}")
                    print(f"Added missing column: {column_name}")
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error ensuring columns exist: {str(e)}")

    def _ensure_columns_exist(self):
        """Ensure all required columns exist in the database"""
        columns_to_check = [
            ('sex', "CHAR(1)"),
            ('is_deceased', "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_def in columns_to_check:
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'members' AND column_name = '{column_name}'
            """)
            if self.cursor.fetchone()[0] == 0:
                try:
                    self.cursor.execute(f"ALTER TABLE members ADD COLUMN {column_name} {column_def}")
                    self.conn.commit()
                    print(f"Added missing column: {column_name}")
                except Exception as e:
                    print(f"Error adding column {column_name}: {str(e)}")
                    self.conn.rollback()

    def register_member(self, member_data):
        try:
            query = """
                INSERT INTO members 
                (first_name, middle_initial, last_name, address, contact_number, 
                bday, age, sex, face_image) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, member_data)
            member_id = self.cursor.lastrowid
            self.conn.commit()  # No automatic Sunday attendance
            return member_id
        except Exception as e:
            messagebox.showerror("Database Error", f"Error: {str(e)}")
            return None
            
# FACE RECOGNITION

class FaceRecognizer:
    def __init__(self, db):
        self.db = db
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.recognizer_trained = True
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
        self.recognizer_trained = True
        print("DeepFace recognizer ready (no training required)")

    def recognize_faces(self):
        if not self.recognizer_trained:
            self.train_recognizer()
        
        # Create a new window for face recognition with member list
        recognition_window = tk.Toplevel()
        recognition_window.title("Face Recognition")
        recognition_window.geometry("1200x700")
        
        # Main container frame
        main_container = tk.Frame(recognition_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Camera frame (takes remaining space)
        camera_frame = tk.Frame(main_container, bg='black')
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Member list frame (fixed width)
        member_frame = tk.Frame(main_container, width=150, bg='#f0f0f0')
        member_frame.pack(side=tk.RIGHT, fill=tk.Y)
        member_frame.pack_propagate(False)  # Prevent frame from resizing to content
        
        # Title for member list
        tk.Label(
            member_frame, 
            text="Members", 
            font=('Arial', 12, 'bold'),
            bg='#f0f0f0'
        ).pack(pady=5, padx=5)
        
        # Create treeview with scrollbars for members
        tree_container = tk.Frame(member_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        member_tree = ttk.Treeview(
            tree_container,
            columns=("Name"),
            show="headings",
            height=30,
            selectmode='browse'
        )
        member_tree.heading("Name", text="Name")
        member_tree.column("Name", width=120, anchor='w')  # Matches frame width
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=member_tree.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=member_tree.xview)
        member_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Grid layout for tree and scrollbars
        member_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Load members into the tree
        try:
            self.db.cursor.execute("SELECT face_id, first_name, last_name FROM members ORDER BY last_name, first_name")
            members = self.db.cursor.fetchall()
            for face_id, first_name, last_name in members:
                display_name = f"{first_name[0]}. {last_name}" if first_name else last_name
                member_tree.insert("", tk.END, values=(display_name,), tags=(face_id,))
        except Exception as e:
            print(f"Error loading members: {str(e)}")
        
        # Attendance count label
        attendance_label = tk.Label(
            member_frame,
            text=f"Present: {len(self.today_attendance)}",
            font=('Arial', 10),
            bg='#f0f0f0'
        )
        attendance_label.pack(pady=5)
        
        # Function to handle member selection
        def on_member_select(event):
            selected = member_tree.selection()
            if not selected:
                return
            
            face_id = member_tree.item(selected[0], 'tags')[0]
            member_name = member_tree.item(selected[0])['values'][0]
            
            if face_id not in self.today_attendance:
                if messagebox.askyesno("Confirm", f"Mark {member_name} as present?"):
                    self.record_attendance(face_id)
                    self.today_attendance.add(face_id)
                    member_tree.item(selected[0], tags=(face_id, 'attended'))
                    member_tree.tag_configure('attended', foreground='green')
                    attendance_label.config(text=f"Present: {len(self.today_attendance)}")
            else:
                messagebox.showinfo("Info", f"{member_name} is already marked present")
        
        member_tree.bind("<Double-1>", on_member_select)
        
        # Camera setup
        cam = cv2.VideoCapture(0)
        cam.set(3, 640)
        cam.set(4, 480)
        
        # Video label for camera feed (will fill the camera_frame)
        video_label = tk.Label(camera_frame)
        video_label.pack(fill=tk.BOTH, expand=True)
        
        # Load member data for recognition
        try:
            self.db.cursor.execute("SELECT face_id, first_name, face_image FROM members")
            members = self.db.cursor.fetchall()
            if not members:
                print("Warning: No members found in database.")
                messagebox.showwarning("Warning", "No registered members found.")
                cam.release()
                recognition_window.destroy()
                return 0
        except Exception as e:
            print(f"Error fetching members: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to load members: {str(e)}")
            cam.release()
            recognition_window.destroy()
            return 0
        
        # Recognition parameters
        min_face_size = 15000
        required_confirmations = 5
        confirmations = 0
        last_face_id = None
        last_name = None
        distance_threshold = 0.5
        
        def update_frame():
            nonlocal confirmations, last_face_id, last_name
            
            ret, img = cam.read()
            if not ret:
                print("Error: Could not read frame from camera.")
                recognition_window.after(10, update_frame)
                return
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=6, minSize=(120, 120))
            
            for (x, y, w, h) in faces:
                face_area = w * h
                if face_area < min_face_size:
                    continue
                    
                face_img = img[y:y+h, x:x+w]
                temp_path = "temp_face.jpg"
                cv2.imwrite(temp_path, face_img)
                best_face_id, best_distance, best_name = None, float('inf'), None
                
                for face_id, first_name, img_path in members:
                    if not os.path.exists(img_path):
                        print(f"Warning: Image not found at {img_path}")
                        continue
                    
                    try:
                        result = DeepFace.verify(
                            temp_path,
                            img_path,
                            model_name="ArcFace",
                            detector_backend="opencv",
                            enforce_detection=False
                        )
                        distance = result["distance"]
                        if result["verified"] and distance < best_distance and distance < distance_threshold:
                            best_face_id, best_distance, best_name = face_id, distance, first_name
                    except Exception as e:
                        print(f"Error verifying face for {img_path}: {str(e)}")
                
                if best_face_id is not None:
                    if best_face_id == last_face_id:
                        confirmations += 1
                    else:
                        confirmations = 1
                        last_face_id = best_face_id
                        last_name = best_name
                    
                    if confirmations >= required_confirmations:
                        display_text = f"{last_name} ({(1-best_distance)*100:.1f}%)"
                        cv2.putText(img, display_text, (x+5, y-5), self.font, 1, (0, 255, 0), 2)
                        if best_face_id not in self.today_attendance:
                            self.record_attendance(best_face_id)
                            self.today_attendance.add(best_face_id)
                            attendance_label.config(text=f"Present: {len(self.today_attendance)}")
                            # Update the treeview to show this member as attended
                            for child in member_tree.get_children():
                                if member_tree.item(child, 'tags')[0] == best_face_id:
                                    member_tree.item(child, tags=(best_face_id, 'attended'))
                                    member_tree.tag_configure('attended', foreground='green')
                                    break
                    else:
                        cv2.putText(img, "Verifying...", (x+5, y-5), self.font, 1, (255, 255, 0), 2)
                else:
                    cv2.putText(img, "Guest", (x+5, y-5), self.font, 1, (0, 0, 255), 2)
                    confirmations = 0
                
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Convert image for Tkinter and resize to fit the frame
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            
            # Get frame dimensions
            frame_width = camera_frame.winfo_width()
            frame_height = camera_frame.winfo_height()
            
            if frame_width > 0 and frame_height > 0:
                img.thumbnail((frame_width, frame_height), Image.LANCZOS)
            
            img = ImageTk.PhotoImage(image=img)
            
            # Update the label with the new image
            video_label.img = img
            video_label.config(image=img)
            
            # Schedule the next update
            recognition_window.after(10, update_frame)
        
        # Make the camera frame expand when window resizes
        def on_resize(event):
            if event.widget == recognition_window:
                camera_frame.config(width=event.width - 160)  # Account for member frame width
        
        recognition_window.bind("<Configure>", on_resize)
        
        # Start the video feed
        update_frame()
        
        # Handle window closing
        def on_closing():
            cam.release()
            if os.path.exists("temp_face.jpg"):
                os.remove("temp_face.jpg")
            recognition_window.destroy()
        
        recognition_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Wait for the window to close
        recognition_window.wait_window()
        
        return len(self.today_attendance)
        
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
    if not os.path.exists("dataset"):
        os.makedirs("dataset")
    # Use timestamp to ensure unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = f"dataset/{name}_{timestamp}.jpg"
    best_face = None
    start_time = datetime.now()
    preview_shown = False
    min_face_size = 15000
    
    while True:
        ret, img = cam.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 6, minSize=(120, 120))
        for (x, y, w, h) in faces:
            face_area = w * h
            if face_area < min_face_size:
                continue
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            if (datetime.now() - start_time).total_seconds() >= 5:
                best_face = gray[y:y+h, x:x+w]
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
        print(f"\n [INFO] Face captured and saved to {img_path}")
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
        self.preview_images = []
        self.current_preview = 0
        self._setup_validation_rules()
        self._setup_gui()

    def _setup_gui(self):
        """Initialize all GUI elements"""
        # Title
        tk.Label(
            self.frame, 
            text="Register Member:", 
            font=AppConfig.FONTS['title'], 
            fg="blue", 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).pack(pady=25)
        
        self.entries = {}
        
        # Preview frame
        self.preview_frame = tk.Frame(self.frame, bg='white', width=200, height=200)
        self.preview_frame.place(x=600, y=100)
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack(fill='both', expand=True)
        
        # Name fields
        self._create_label_entry("First Name:", 'first_name', 80, width=300)
        self._create_label_entry("Middle Initial:", 'middle_initial', 130, width=50)
        self._create_label_entry("Last Name:", 'last_name', 180, width=300)
        
        # Other fields
        self._create_label_entry("Address:", 'address', 230, width=300)
        self._create_label_entry("Contact Number:", 'phone', 280, width=300)
        
        # Birthday field
        tk.Label(
            self.frame, 
            text="Birthday:", 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=25, y=330)
        
        self.birthday_entry = DateEntry(
            self.frame,
            width=17,
            background='white',
            foreground='black',
            borderwidth=2,
            year=2000,
            month=1,
            day=1,
            date_pattern='y-mm-dd',
            font=AppConfig.FONTS['body'],
            selectbackground='#4CAF50',
            normalbackground='white'
        )
        self.birthday_entry.place(x=250, y=340, width=300)
        self.birthday_entry.bind("<<DateEntrySelected>>", lambda e: self._validate_birthday())
        
        # Age display
        tk.Label(
            self.frame, 
            text="Age:", 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=25, y=380)
        self.age_label = tk.Label(
            self.frame, 
            text="", 
            font=AppConfig.FONTS['body'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        )
        self.age_label.place(x=250, y=390)

        tk.Label(
            self.frame, 
            text="Sex:", 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=25, y=430)

        self.sex_var = tk.StringVar()
        sex_frame = tk.Frame(self.frame, bg=AppConfig.COLOR_SCHEME['form_bg'])
        sex_frame.place(x=250, y=440)
        
        tk.Radiobutton(
            sex_frame,
            text="Male",
            variable=self.sex_var,
            value='M',
            font=AppConfig.FONTS['body'],
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).pack(side='left')
        
        tk.Radiobutton(
            sex_frame,
            text="Female",
            variable=self.sex_var,
            value='F',
            font=AppConfig.FONTS['body'],
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).pack(side='left')
        
        # Submit button - Now properly defined before being placed
        submit_btn = tk.Button(
            self.frame,
            text="Scan Face & Register",
            font=AppConfig.FONTS['heading'],
            command=self._validate_all_fields,
            bg=AppConfig.COLOR_SCHEME['primary'],
            fg='white'
        )
        submit_btn.place(x=400, y=480)
        submit_btn.bind("<Enter>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary_dark']))
        submit_btn.bind("<Leave>", lambda e: e.widget.config(bg=AppConfig.COLOR_SCHEME['primary']))
    def _create_label_entry(self, label_text, field_name, y_pos, width):
        """Helper method to create consistent label+entry pairs"""
        tk.Label(
            self.frame, 
            text=label_text, 
            font=AppConfig.FONTS['heading'], 
            bg=AppConfig.COLOR_SCHEME['form_bg']
        ).place(x=25, y=y_pos)
        
        self.entries[field_name] = tk.Entry(
            self.frame, 
            font=AppConfig.FONTS['body'],
            highlightthickness=1,
            highlightbackground="white"
        )
        self.entries[field_name].place(x=250, y=y_pos+10, width=width)
        self.entries[field_name].bind('<KeyRelease>', lambda e, f=field_name: self._clear_field_error(f))

    def _setup_validation_rules(self):
        """Define validation rules for each field"""
        self.validation_rules = {
            'first_name': {
                'validator': lambda x: bool(x) and not any(char.isdigit() for char in x),
                'error_msg': "First name cannot be empty or contain numbers"
            },
            'middle_initial': {
                'validator': lambda x: len(x) <= 1 and not any(char.isdigit() for char in x),
                'error_msg': "Middle initial should be one letter or blank"
            },
            'last_name': {
                'validator': lambda x: bool(x) and not any(char.isdigit() for char in x),
                'error_msg': "Last name cannot be empty or contain numbers"
            },
            'address': {
                'validator': lambda x: bool(x),
                'error_msg': "Address cannot be empty"
            },
            'phone': {
                'validator': lambda x: x.isdigit() and len(x) == 11 and x.startswith("09"),
                'error_msg': "Contact Number must be 11 digits starting with 09"
            }
        }

    def _validate_all_fields(self):
        """Validate all form fields before registration"""
        errors = []
        
        # Validate regular fields
        for field, rules in self.validation_rules.items():
            if not self._validate_field(field, rules['validator']):
                errors.append(rules['error_msg'])
        
        # Validate birthday
        if not self._validate_birthday():
            errors.append("Invalid birthday date")
            
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
            
        return self._register_member()

    def _validate_field(self, field_name, validator):
        """Validate a single field"""
        value = self.entries[field_name].get().strip()
        is_valid = validator(value)
        
        if not is_valid:
            self.entries[field_name].config(
                highlightbackground='red',
                highlightthickness=1,
                background='#ffdddd'
            )
        else:
            self.entries[field_name].config(
                highlightbackground='white',
                highlightthickness=1,
                background='white'
            )
            
        return is_valid

    def _clear_field_error(self, field_name):
        """Clear error styling when user starts typing"""
        self.entries[field_name].config(
            highlightbackground='white',
            highlightthickness=1,
            background='white'
        )

    def _validate_birthday(self):
        """Validate the birthday date entry"""
        try:
            selected_date = datetime.strptime(self.birthday_entry.get(), '%Y-%m-%d')
            today = datetime.today()
            max_age = 100
            
            if selected_date > today:
                self._show_birthday_error()
                return False
            
            age = today.year - selected_date.year
            if (today.month, today.day) < (selected_date.month, selected_date.day):
                age -= 1
                
            if age > max_age:
                self._show_birthday_error()
                return False
                
            self._clear_birthday_error()
            self._calculate_age()
            return True
            
        except ValueError:
            self._show_birthday_error()
            return False

    def _show_birthday_error(self):
        """Highlight birthday field as invalid"""
        self.birthday_entry.config(background='#ffdddd', foreground='red')

    def _clear_birthday_error(self):
        """Reset birthday field styling"""
        self.birthday_entry.config(background='white', foreground='black')

    def _calculate_age(self):
        """Calculate age from birthday"""
        try:
            birthday = datetime.strptime(self.birthday_entry.get(), '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birthday.year
            if (today.month, today.day) < (birthday.month, birthday.day):
                age -= 1
            self.age_label.config(text=str(age))
        except ValueError:
            pass

    def show_preview(self, img_array):
        """Display the captured face preview"""
        try:
            img = Image.fromarray(img_array)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.preview_images = [photo]
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            print(f"Preview error: {str(e)}")

    def _register_member(self):
        """Handle the member registration process"""
        try:
            first_name = self.entries['first_name'].get().strip()
            middle_initial = self.entries['middle_initial'].get().strip()
            last_name = self.entries['last_name'].get().strip()
            
            name = f"{first_name}_{middle_initial}_{last_name}" if middle_initial else f"{first_name}_{last_name}"
            
            img_path = face_scanning(name, preview_callback=self.show_preview)
            if not img_path:
                messagebox.showwarning("Cancelled", "Face scan was cancelled")
                return False

            if messagebox.askyesno("Confirm", "Save this face image?"):
                member_data = (
                    first_name,
                    middle_initial,
                    last_name,
                    self.entries['address'].get().strip(),
                    self.entries['phone'].get().strip(),
                    self.birthday_entry.get(),
                    self.age_label.cget("text"),
                    self.sex_var.get(),  # Include sex
                    img_path
                )
                
                member_id = self.db.register_member(member_data)
                if member_id:
                    messagebox.showinfo("Success", f"Member registered! ID: {member_id}")
                    self._reset_form()
                    self.on_success()
                    
                    # Update attendance count if registered on Saturday
                    # Update attendance count if registered on Sunday
                    if datetime.now().weekday() == 6:  # 6 = Sunday (changed from 5=Saturday)
                        if hasattr(self.master.master, 'attendance_label'):
                            today = datetime.now().strftime('%Y-%m-%d')
                            try:
                                self.db.cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = %s", (today,))
                                count = self.db.cursor.fetchone()[0]
                                self.master.master.attendance_label.config(text=f"Attendance Today: {count}")
                            except:
                                pass
                    return True
                else:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    messagebox.showerror("Error", "Failed to register member")
                    return False
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")
            print(traceback.format_exc())
            return False

    def _reset_form(self):
        """Reset all form fields"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
            entry.config(
                highlightbackground='white',
                highlightthickness=1,
                background='white'
            )
        self.birthday_entry.set_date(datetime(2000, 1, 1))
        self._clear_birthday_error()
        self.age_label.config(text="")
        self.preview_images = []
        self.preview_label.config(image='')
# MAIN APPLICATION

class FaceIDSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Identification System")
        self.root.geometry("1000x700")
        self.db = Database()
        self.show_password_prompt()
        self.password_manager = PasswordManager(self.db)
        self.show_login_window()
        
class PasswordManager:
    def __init__(self, db):
        self.db = db
        self.SECURITY_QUESTION = "What is the name of your first pet?"
        
    def verify_answer(self, answer):
        try:
            self.db.cursor.execute("SELECT security_question_answer FROM admin_users LIMIT 1")
            result = self.db.cursor.fetchone()
            if result:
                return answer.lower() == result[0].lower()
            return False
        except Exception as e:
            print(f"Error verifying answer: {e}")
            return False
            
    def update_security_answer(self, new_answer):
        try:
            self.db.cursor.execute("UPDATE admin_users SET security_question_answer = %s", (new_answer,))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating security answer: {e}")
            return False
            
    def update_password(self, new_password):
        try:
            self.db.cursor.execute("UPDATE admin_users SET password_hash = %s", 
                                 (sha256(new_password.encode()).hexdigest(),))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False

# Update the LoginWindow class
class LoginWindow(tk.Toplevel):
    def __init__(self, parent, db, on_success):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.password_manager = PasswordManager(db)
        self.on_success = on_success
        self.PASSWORD = "mypassword"  # Default password
        
        self.title("Login")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Handle window closing properly
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_widgets()
        self.grab_set()  # Make window modal
    
    def _create_widgets(self):
        """Create all widgets for the login window"""
        # Password Entry
        tk.Label(self, text="Password:", font=('Arial', 12)).pack(pady=5)
        self.password_entry = tk.Entry(self, show="*", font=('Arial', 12))
        self.password_entry.pack(pady=5)
        self.password_entry.focus_set()
        
        # Login Button
        tk.Button(self, 
                 text="Login", 
                 command=self._verify_password, 
                 bg=AppConfig.COLOR_SCHEME['primary'], 
                 fg='white').pack(pady=10)
        
        # Forgot Password Link
        forgot_link = tk.Label(self, text="Forgot Password?", fg="blue", cursor="hand2")
        forgot_link.pack(pady=5)
        forgot_link.bind("<Button-1>", lambda e: self._show_password_reset())
        
        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self._verify_password())
    
    def _on_close(self):
        """Handle window closing"""
        self.parent.destroy()  # Close the entire application
    
    def _verify_password(self):
        """Verify the entered password"""
        entered_password = self.password_entry.get()
        if entered_password == self.PASSWORD:
            self.destroy()  # Close login window
            self.on_success()  # Proceed to main application
        else:
            messagebox.showerror("Error", "Incorrect password")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
    
    def _show_password_reset(self):
        """Handle password reset flow"""
        answer = simpledialog.askstring("Password Reset", 
                                      f"{self.password_manager.SECURITY_QUESTION}")
        if answer and self.password_manager.verify_answer(answer):
            self._show_new_password_dialog()
        else:
            messagebox.showerror("Error", "Incorrect answer to security question")
    
    def _show_new_password_dialog(self):
        """Show dialog to set new password"""
        reset_window = tk.Toplevel(self)
        reset_window.title("Set New Password")
        reset_window.geometry("300x200")
        reset_window.resizable(False, False)
        
        # New Password
        tk.Label(reset_window, text="New Password:", font=('Arial', 12)).pack(pady=5)
        new_pass_entry = tk.Entry(reset_window, show="*", font=('Arial', 12))
        new_pass_entry.pack(pady=5)
        
        # Confirm Password
        tk.Label(reset_window, text="Confirm Password:", font=('Arial', 12)).pack(pady=5)
        confirm_pass_entry = tk.Entry(reset_window, show="*", font=('Arial', 12))
        confirm_pass_entry.pack(pady=5)
        
        def set_new_password():
            new_pass = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            
            if not new_pass:
                messagebox.showerror("Error", "Password cannot be empty")
                return
                
            if new_pass != confirm_pass:
                messagebox.showerror("Error", "Passwords don't match")
                return
                
            # Update both in-memory and database password
            self.PASSWORD = new_pass
            if self.password_manager.update_password(new_pass):
                messagebox.showinfo("Success", "Password changed successfully!")
                reset_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to update password")
        
        tk.Button(reset_window, 
                 text="Set Password", 
                 command=set_new_password,
                 bg=AppConfig.COLOR_SCHEME['primary'], 
                 fg='white').pack(pady=10)
class FaceIDSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Identification System")
        self.root.geometry("1000x700")
        self.db = Database()
        
        # Initialize password manager
        self.password_manager = PasswordManager(self.db)
        
        # Start with login window
        self.show_login_window()
        
    def show_login_window(self):
        # Hide main window until logged in
        self.root.withdraw()
        
        # Create login window
        self.login_window = LoginWindow(
            self.root, 
            self.db, 
            self.on_login_success
        )
        
        # When login window closes, check if we should show main window
        self.login_window.wait_window()
        if not self.root.winfo_exists():
            return  # App was closed
        
    def on_login_success(self):
        # Show main window
        self.root.deiconify()
        self.setup_ui()
        
        # Add admin config button to main interface
        admin_btn = tk.Button(
            self.root,
            text="Admin Config",
            command=self.show_admin_config,
            bg=AppConfig.COLOR_SCHEME['primary_dark'],
            fg='white'
        )
        admin_btn.place(x=10, y=10)
        
        try:
            img = Image.open("fingerprint.png").resize((100, 100), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.bg_image).place(x=5, y=5)
        except FileNotFoundError:
            pass

    def show_admin_config(self):
        """Admin configuration panel to change security answer"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Admin Configuration")
        config_window.geometry("400x300")
        config_window.resizable(False, False)
        
        # Get current security answer
        try:
            self.db.cursor.execute("SELECT security_question_answer FROM admin_users LIMIT 1")
            current_answer = self.db.cursor.fetchone()[0]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load security settings: {str(e)}")
            config_window.destroy()
            return
        
        # Security question display
        tk.Label(config_window, 
                text="Security Question:", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(config_window, 
                text=self.password_manager.SECURITY_QUESTION,
                font=('Arial', 12)).pack()
        
        # Current answer
        tk.Label(config_window, 
                text="Current Answer:", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(config_window, 
                text=current_answer,
                font=('Arial', 12)).pack()
        
        # New answer entry
        tk.Label(config_window, 
                text="New Answer:", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        new_answer_entry = tk.Entry(config_window, font=('Arial', 12))
        new_answer_entry.pack()
        new_answer_entry.focus_set()
        
        # Update button
        def update_answer():
            new_answer = new_answer_entry.get().strip()
            if new_answer:
                if self.password_manager.update_security_answer(new_answer):
                    messagebox.showinfo("Success", "Security answer updated!")
                    config_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update security answer")
            else:
                messagebox.showwarning("Warning", "Please enter a new answer")
        
        tk.Button(config_window, 
                 text="Update", 
                 command=update_answer,
                 bg=AppConfig.COLOR_SCHEME['primary'],
                 fg='white').pack(pady=20)

# Update your FaceIDSystem class
class FaceIDSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Identification System")
        self.root.geometry("1000x700")
        self.db = Database()
        self.db.debug_database_schema() 
        self.show_login_window()
        
    def show_login_window(self):
        LoginWindow(self.root, self.db, self.on_login_success)
        
    def on_login_success(self):
        self.setup_ui()
        try:
            img = Image.open("fingerprint.png").resize((100, 100), Image.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.bg_image).place(x=5, y=5)
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
    
    def debug_database_schema(self):
        """Temporary method to debug database schema"""
        try:
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            print("Tables in database:", tables)
            
            self.cursor.execute("DESCRIBE members")
            columns = self.cursor.fetchall()
            print("Members table columns:")
            for col in columns:
                print(col)
                
        except Exception as e:
            print("Debug error:", str(e))

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
        if hasattr(self, 'attendance_label'):
            self.attendance_label.config(text=f"Attendance Today: {new_count}")

    def show_register(self):
        self.clear_frame()
        RegistrationForm(self.main_frame, self.db, self.show_home).frame.pack(fill="both", expand=True)

    def show_database(self):
        """Show members list with search functionality"""
        self.clear_frame()    

        header_frame = tk.Frame(self.main_frame, bg='#f0f0f0')
        header_frame.pack(fill='x', padx=10, pady=10)

        # Title label on left
        tk.Label(
            header_frame,
            text="Members List",
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        ).pack(side='left')

        # Search bar on right
        search_frame = tk.Frame(header_frame, bg='#f0f0f0')
        search_frame.pack(side='right')

        tk.Label(search_frame, text="Search:", bg='#f0f0f0').pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 12),
            width=25
        )
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', self._filter_members)

        # Treeview with scrollbars
        tree_frame = tk.Frame(self.main_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

        self.members_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "First Name", "Middle Name", "Last Name", "Sex", "Address", 
                    "Contact Number", "Birthday", "Age", "Status", "Actions"),
            show="headings",
            height=20
        )

        # Configure columns
        columns = [
            ("ID", 50, 'center'),
            ("First Name", 120, 'w'),
            ("Middle Name", 80, 'w'),
            ("Last Name", 120, 'w'),
            ("Sex", 50, 'center'),
            ("Address", 180, 'w'),
            ("Contact Number", 120, 'center'),
            ("Birthday", 100, 'center'),
            ("Age", 50, 'center'),
            ("Status", 80, 'center'),
            ("Actions", 80, 'center')
        ]

        for col, width, anchor in columns:
            self.members_tree.heading(col, text=col)
            self.members_tree.column(col, width=width, anchor=anchor)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.members_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.members_tree.xview)
        self.members_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.members_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

        # Load data
        self._load_members_data()

        # Bind click event for Edit button
        self.members_tree.bind("<Button-1>", self._on_member_tree_click)

        # Refresh button
        refresh_btn = tk.Button(
            self.main_frame,
            text="Refresh",
            command=self._load_members_data,
            bg='#4CAF50',
            fg='white',
            width=15
        )
        refresh_btn.pack(pady=(0,10))

    def _load_members_data(self):
        """Load members data into treeview"""
        # Clear existing data
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        
        try:
            # Get search term if any
            search_term = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
            
            self.db.cursor.execute("""
                SELECT face_id, first_name, middle_initial, last_name, sex, address, 
                    contact_number, DATE_FORMAT(bday, '%Y-%m-%d'), age, is_deceased
                FROM members
                ORDER BY last_name, first_name
            """)
            members_data = self.db.cursor.fetchall()
            
            for member in members_data:
                # Check if member matches search term
                member_text = " ".join(str(x) for x in member).lower()
                if not search_term or search_term in member_text:
                    status = "Deceased" if member[9] else "Active"
                    self.members_tree.insert("", tk.END, 
                                        values=(member[0], member[1], member[2], member[3],
                                                member[4], member[5], member[6], member[7],
                                                member[8], status, "Edit"))
                    
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load members: {str(e)}")

    def _filter_members(self, event=None):
        """Filter members list based on search term"""
        self._load_members_data()

    def _on_member_tree_click(self, event):
        """Handle click on members tree"""
        region = self.members_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.members_tree.identify_column(event.x)
            # Columns are 1-indexed, and "Actions" is the 11th column (index 10)
            if column == "#11":  # Changed from #9 to #11 since we have 11 columns
                item = self.members_tree.identify_row(event.y)
                member_id = self.members_tree.item(item)['values'][0]
                
                self.db.cursor.execute("""
                    SELECT face_id, first_name, middle_initial, last_name, sex, address, 
                        contact_number, bday, age, is_deceased, face_image
                    FROM members
                    WHERE face_id = %s
                """, (member_id,))
                member_data = self.db.cursor.fetchone()
                
                if member_data:
                    self.show_edit_form(member_data)


    def show_edit_form(self, member_data):
        """Show form to edit member information"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Member")
        edit_window.geometry("800x600")
        
        # Store member data
        self.current_edit_member = member_data
        self.edit_window = edit_window
        
        # Form title
        tk.Label(edit_window, text="Edit Member Information", font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Form frame
        form_frame = tk.Frame(edit_window)
        form_frame.pack(pady=10)
        
        # Field configuration - now explicitly using the correct indices from member_data
        fields = [
            ("First Name:", "first_name", 0, member_data[1], "entry"),        # index 1
            ("Middle Initial:", "middle_initial", 1, member_data[2], "entry"), # index 2
            ("Last Name:", "last_name", 2, member_data[3], "entry"),          # index 3
            ("Address:", "address", 3, member_data[5], "entry"),              # index 5 (address)
            ("Contact Number:", "contact_number", 4, member_data[6], "entry"), # index 6 (phone)
            ("Birthday:", "bday", 5, member_data[7], "date"),                 # index 7 (birthday)
            ("Age:", "age", 6, member_data[8], "entry")                       # index 8 (age)
        ]
        
        self.edit_entries = {}
        
        for label, field_name, row, value, widget_type in fields:
            # Create label
            tk.Label(form_frame, text=label, font=('Arial', 12)).grid(
                row=row, column=0, padx=5, pady=5, sticky='e')
            
            # Create widget
            if widget_type == "date":
                entry = DateEntry(
                    form_frame,
                    width=17,
                    background='white',
                    foreground='black',
                    borderwidth=2,
                    date_pattern='y-mm-dd',
                    font=('Arial', 12))
                if value:
                    try:
                        entry.set_date(datetime.strptime(str(value), '%Y-%m-%d'))
                    except ValueError:
                        # Handle invalid date format
                        entry.set_date(datetime.today())
                        print(f"Warning: Invalid date format for {value}")
                
                # Bind date change event
                def on_date_change(event, e=entry):
                    self._handle_birthday_change(e)
                entry.bind("<<DateEntrySelected>>", on_date_change)
                
            else:
                entry = tk.Entry(form_frame, font=('Arial', 12), width=30)
                if value:
                    entry.insert(0, str(value))
            
            entry.grid(row=row, column=1, padx=5, pady=5, sticky='w')
            self.edit_entries[field_name] = entry
        
        # Age is read-only
        self.edit_entries['age'].config(state='readonly')
        
        # Face image preview
        self._setup_face_preview(edit_window, member_data)
        
        # Sex/Gender selection
        self.sex_var = tk.StringVar(value=member_data[4] if len(member_data) > 4 else 'M')  # index 4 (sex)
        tk.Label(form_frame, text="Sex:", font=('Arial', 12)).grid(
            row=8, column=0, padx=5, pady=5, sticky='e')
        
        sex_frame = tk.Frame(form_frame)
        sex_frame.grid(row=8, column=1, sticky='w')
        
        tk.Radiobutton(
            sex_frame,
            text="Male",
            variable=self.sex_var,
            value='M',
            font=('Arial', 12)
        ).pack(side='left')
        
        tk.Radiobutton(
            sex_frame,
            text="Female",
            variable=self.sex_var,
            value='F',
            font=('Arial', 12)
        ).pack(side='left')
        
        # Deceased checkbox
        self.is_deceased_var = tk.BooleanVar(value=member_data[9] if len(member_data) > 9 else False)  # index 9 (is_deceased)
        tk.Label(form_frame, text="Deceased:", font=('Arial', 12)).grid(
            row=9, column=0, padx=5, pady=5, sticky='e')
        
        tk.Checkbutton(
            form_frame,
            variable=self.is_deceased_var,
            onvalue=True,
            offvalue=False
        ).grid(row=9, column=1, padx=5, pady=5, sticky='w')

        # Action buttons - THIS SHOULD BE CALLED ONLY ONCE AND AFTER ALL OTHER ELEMENTS
        self._setup_action_buttons(edit_window)

    def _handle_birthday_change(self, date_entry):
        """Update age when birthday changes"""
        try:
            selected_date = datetime.strptime(date_entry.get(), '%Y-%m-%d')
            today = datetime.today()
            age = today.year - selected_date.year
            
            if (today.month, today.day) < (selected_date.month, selected_date.day):
                age -= 1
            
            self.edit_entries['age'].config(state='normal')
            self.edit_entries['age'].delete(0, tk.END)
            self.edit_entries['age'].insert(0, str(age))
            self.edit_entries['age'].config(state='readonly')
            self.edit_entries['bday'].config(background='white', foreground='black')
        except ValueError:
            self.edit_entries['bday'].config(background='#ffdddd', foreground='red')

    def _setup_face_preview(self, parent_window, member_data):
        """Setup face image preview section with proper error handling"""
        self.preview_frame = tk.Frame(parent_window, bg='white', width=200, height=200)
        self.preview_frame.pack(pady=10)
        
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack(fill='both', expand=True)
        
        # Get image path (index 10 is face_image in our query)
        self.current_image_path = member_data[10] if len(member_data) > 10 else None
        
        # Try multiple locations if image not found
        possible_paths = [
            self.current_image_path,
            os.path.join("dataset", os.path.basename(self.current_image_path)) if self.current_image_path else None,
            os.path.join(os.path.dirname(__file__), "dataset", os.path.basename(self.current_image_path)) if self.current_image_path else None
        ]
        
        img_found = False
        for path in possible_paths:
            if path and os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=photo)
                    self.preview_label.image = photo  # Keep reference
                    self.current_image_path = path  # Update to found path
                    img_found = True
                    break
                except Exception as e:
                    print(f"Error loading image {path}: {str(e)}")
                    continue
        
        if not img_found:
            # Create a placeholder with member initials
            first_name = member_data[1] if len(member_data) > 1 else ""
            last_name = member_data[3] if len(member_data) > 3 else ""
            initials = f"{first_name[0] if first_name else ''}{last_name[0] if last_name else ''}"
            
            # Create blank image with initials
            img = Image.new('RGB', (200, 200), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            w, h = draw.textsize(initials, font=font)
            draw.text(((200-w)/2, (200-h)/2), initials, fill="black", font=font)
            
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
            tk.Label(self.preview_frame, 
                    text="Image not found\nShowing initials", 
                    font=('Arial', 8),
                    bg='white').pack()

    def _setup_action_buttons(self, parent_window):
        """Setup action buttons with proper commands and styling"""
        btn_frame = tk.Frame(parent_window)
        btn_frame.pack(pady=10)
        
        # Update Face Image Button
        update_img_btn = tk.Button(
            btn_frame,
            text="Update Face Image",
            command=self._update_face_image,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12),
            width=15
        )
        update_img_btn.pack(side='left', padx=5)
        
        # Save Changes Button
        save_btn = tk.Button(
            btn_frame,
            text="Save Changes",
            command=self._save_member_changes,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12),
            width=15
        )
        save_btn.pack(side='left', padx=5)
        
        # Cancel Button
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=parent_window.destroy,
            bg='#f44336',
            fg='white',
            font=('Arial', 12),
            width=15
        )
        cancel_btn.pack(side='left', padx=5)
        
        # Add hover effects
        for btn in [update_img_btn, save_btn, cancel_btn]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg='#45a049' if e.widget['text'] != 'Cancel' else '#d32f2f'))
            btn.bind("<Leave>", lambda e: e.widget.config(bg='#4CAF50' if e.widget['text'] != 'Cancel' else '#f44336'))

    def _update_face_image(self):
        """Handle face image updates"""
        first_name = self.edit_entries['first_name'].get()
        middle_initial = self.edit_entries['middle_initial'].get()
        last_name = self.edit_entries['last_name'].get()
        
        name = f"{first_name}_{middle_initial}_{last_name}" if middle_initial else f"{first_name}_{last_name}"
        
        def preview_callback(img_array):
            try:
                img = Image.fromarray(img_array)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=photo)
                self.preview_label.image = photo
            except Exception as e:
                print(f"Preview error: {str(e)}")

        new_img_path = face_scanning(name, preview_callback=preview_callback)
        
        if new_img_path:
            if (os.path.exists(self.current_image_path) and 
                os.path.abspath(self.current_image_path) != os.path.abspath(new_img_path)):
                try:
                    os.remove(self.current_image_path)
                except Exception as e:
                    print(f"Warning: Could not delete old image: {str(e)}")
            
            self.current_image_path = new_img_path
            messagebox.showinfo("Success", "Face image updated!")

    def _save_member_changes(self):
        """Validate and save member changes"""
        # Validate fields
        if not self._validate_fields():
            return
        
        # Save to database
        try:
            updated_data = (
                self.edit_entries['first_name'].get(),
                self.edit_entries['middle_initial'].get(),
                self.edit_entries['last_name'].get(),
                self.edit_entries['address'].get(),
                self.edit_entries['contact_number'].get(),
                self.edit_entries['bday'].get(),
                self.edit_entries['age'].get(),
                self.sex_var.get(),  # NEW: Sex value
                self.is_deceased_var.get(),
                self.current_image_path,
                self.current_edit_member[0]  # face_id
            )
            
            self.db.cursor.execute("""
                UPDATE members 
                SET first_name=%s, middle_initial=%s, last_name=%s, 
                    address=%s, contact_number=%s, bday=%s, 
                    age=%s, sex=%s, is_deceased=%s, face_image=%s
                WHERE face_id=%s
            """, updated_data)
            
            self.db.conn.commit()
            messagebox.showinfo("Success", "Member updated successfully!")
            self.edit_window.destroy()
            self.show_database()  # Refresh view
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update member: {str(e)}")
            print(traceback.format_exc())

    def _validate_fields(self):
        """Validate all form fields"""
        errors = []
        
        # Validate birthday
        try:
            selected_date = datetime.strptime(self.edit_entries['bday'].get(), '%Y-%m-%d')
            if selected_date > datetime.today():
                errors.append("Birthday cannot be in the future")
                self.edit_entries['bday'].config(background='#ffdddd', foreground='red')
        except ValueError:
            errors.append("Invalid date format (YYYY-MM-DD)")
            self.edit_entries['bday'].config(background='#ffdddd', foreground='red')
        
        # Validate other fields
        validation_rules = {
            'first_name': (
                lambda x: bool(x.strip()) and not any(c.isdigit() for c in x),
                "First name required (no numbers)"),
            'last_name': (
                lambda x: bool(x.strip()) and not any(c.isdigit() for c in x),
                "Last name required (no numbers)"),
            'contact_number': (
                lambda x: x.strip().isdigit() and len(x.strip()) == 11 and x.strip().startswith("09"),
                "11-digit number starting with 09 required")
        }
        
        for field, (validator, error_msg) in validation_rules.items():
            if not validator(self.edit_entries[field].get()):
                errors.append(error_msg)
                self.edit_entries[field].config(background='#ffdddd', foreground='red')
        
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
        return True
    #for attendance record
    def show_records(self):
        self.clear_frame()

        tk.Label(
            self.main_frame,
            text="Attendance Records",
            font=('Arial', 16, 'bold'),
            bg=AppConfig.COLOR_SCHEME['main_bg']
        ).pack(pady=10)

        # Create treeview with scrollbars
        tree_frame = tk.Frame(self.main_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.records_tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "Status"),
            show="headings",
            height=20
        )

        # Configure columns
        columns = [
            ("Name", 300, 'w'),
            ("Status", 100, 'center')
        ]

        for col, width, anchor in columns:
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=width, anchor=anchor)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.records_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.records_tree.xview)
        self.records_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.records_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

        # Load data
        self._load_attendance_records()

        # Bind click event
        self.records_tree.bind("<Double-1>", self._show_member_attendance)

        # Refresh button
        refresh_btn = tk.Button(
            self.main_frame,
            text="Refresh",
            command=self._load_attendance_records,
            bg='#4CAF50',
            fg='white',
            width=15
        )
        refresh_btn.pack(pady=10)
        
    def _show_member_attendance(self, event):
        """Show ALL attendance dates for selected member (not just Sundays)"""
        selected = self.records_tree.selection()
        if not selected:
            return
            
        # Get member_id from the hidden tag
        member_id = self.records_tree.item(selected[0], 'tags')[0]
        member_name = self.records_tree.item(selected[0])['values'][0]
        
        # Create new window
        log_window = tk.Toplevel(self.root)
        log_window.title(f"Full Attendance History - {member_name}")
        log_window.geometry("600x400")
        
        # Title
        tk.Label(
            log_window,
            text=f"All Attendance Records for {member_name}",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Treeview with scrollbars
        tree_frame = tk.Frame(log_window)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        log_tree = ttk.Treeview(
            tree_frame,
            columns=("Date", "Time In"),
            show="headings",
            height=15
        )
        
        # Configure columns
        log_tree.heading("Date", text="Date")
        log_tree.column("Date", width=150, anchor='center')
        
        log_tree.heading("Time In", text="Time In")
        log_tree.column("Time In", width=150, anchor='center')

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=log_tree.yview)
        log_tree.configure(yscrollcommand=y_scroll.set)

        log_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')

        # Load ALL attendance dates (no Sunday filter)
        try:
            self.db.cursor.execute("""
                SELECT date, time_in 
                FROM attendance 
                WHERE face_id = %s
                ORDER BY date DESC, time_in DESC
            """, (member_id,))
            
            records = self.db.cursor.fetchall()
            for date, time_in in records:
                log_tree.insert("", tk.END, values=(date, time_in))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {str(e)}")

        # Close button
        tk.Button(
            log_window,
            text="Close",
            command=log_window.destroy,
            bg='#4CAF50',
            fg='white',
            width=15
        ).pack(pady=10)

    def _load_attendance_records(self):
        # Clear existing data first
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
            
        try:
            self.db.cursor.execute("""
                SELECT 
                    m.face_id, 
                    CONCAT(m.first_name, ' ', m.last_name) AS name,
                    m.is_deceased,
                    MAX(a.date) AS last_attended
                FROM members m
                LEFT JOIN attendance a ON m.face_id = a.face_id
                GROUP BY m.face_id
                ORDER BY m.last_name, m.first_name
            """)
            members = self.db.cursor.fetchall()
            
            for face_id, name, is_deceased, last_attended in members:
                if is_deceased:
                    status = "Deceased"
                elif last_attended == datetime.now().date():
                    status = "Present Today"
                elif last_attended:
                    days_ago = (datetime.now().date() - last_attended).days
                    status = f"Last attended {days_ago} days ago"
                else:
                    status = "Never attended"
                    
                self.records_tree.insert("", tk.END, values=(name, status), tags=(face_id,))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load records: {str(e)}")

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

# RUN APPLICATION
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceIDSystem(root)
    root.mainloop()
