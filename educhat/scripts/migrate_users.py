
import sqlite3
import os
import secrets
import string
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_PATH = '/home/tiennguyen/Documents/educhat/data/hmu_schedules.db'

def get_password_hash(password):
    return pwd_context.hash(password)

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Check if column exists
        cursor.execute("PRAGMA table_info(students)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'password_hash' not in columns:
            print("Adding password_hash column...")
            cursor.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")
            conn.commit()
        else:
            print("password_hash column already exists.")

        # 2. Seed default passwords for existing students
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits
        default_pass = ''.join(secrets.choice(alphabet) for _ in range(12))
        default_hash = get_password_hash(default_pass)
        
        print(f"Seeding securely generated default password for all students...")
        cursor.execute("UPDATE students SET password_hash = ? WHERE password_hash IS NULL", (default_hash,))
        conn.commit()
        
        # 3. Verify
        cursor.execute("SELECT count(*) FROM students WHERE password_hash IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"Migration complete. {count} students have passwords.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
