
import sqlite3
import os
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = 'data/hmu_schedules.db'

def seed_password(student_code, password="123456"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    hashed = pwd_context.hash(password)
    print(f"Setting password for {student_code}...")
    cursor.execute("UPDATE students SET password_hash = ? WHERE student_code = ?", (hashed, student_code))
    conn.commit()
    
    # Verify
    cursor.execute("SELECT password_hash FROM students WHERE student_code = ?", (student_code,))
    row = cursor.fetchone()
    if row and row[0]:
        print("Password set successfully.")
    else:
        print("Failed to set password.")
    conn.close()

if __name__ == "__main__":
    seed_password("2500001")
    seed_password("2500000")
