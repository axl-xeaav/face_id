import os
import cv2
import numpy as np
from deepface import DeepFace
import mysql.connector
from tqdm import tqdm
import traceback

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='mypassword',
        database='mydb'
    )

def migrate():
    print("Starting migration with retry logic...")
    db = get_db_connection()
    cursor = db.cursor()

    try:
        # Verify/Add column
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'members' AND column_name = 'face_vector'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE members ADD COLUMN face_vector BLOB")
            db.commit()

        # Get members
        cursor.execute("SELECT face_id, face_image FROM members WHERE face_image IS NOT NULL")
        members = cursor.fetchall()

        success = 0
        for face_id, img_path in tqdm(members, desc="Processing"):
            try:
                if not os.path.exists(img_path):
                    print(f"\nImage missing: {img_path}")
                    continue

                img = cv2.imread(img_path)
                if img is None:
                    print(f"\nInvalid image: {img_path}")
                    continue

                # Try with multiple models if needed
                models = ["Facenet", "VGG-Face", "OpenFace"]
                vector = None
                
                for model in models:
                    try:
                        result = DeepFace.represent(
                            img,
                            model_name="VGG-Face",
                            enforce_detection=False
                        )
                        vector = np.array(result[0]["embedding"])
                        break
                    except Exception as e:
                        print(f"\n{model} failed, trying next...")

                if vector is None:
                    print(f"\nAll models failed for {face_id}")
                    continue

                cursor.execute(
                    "UPDATE members SET face_vector = %s WHERE face_id = %s",
                    (vector.tobytes(), face_id)
                )
                db.commit()
                success += 1

            except Exception as e:
                db.rollback()
                print(f"\nError processing {face_id}:")
                traceback.print_exc()

        print(f"\nSuccessfully migrated {success}/{len(members)} members")

    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
