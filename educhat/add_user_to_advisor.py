import sqlite3
import os

DB_PATH = "/home/tiennguyen/Documents/Edu Agent/services/advisor/advisor.db"

def add_user():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    user_id = 2500001
    cursor.execute("SELECT id FROM Students WHERE id = ?", (user_id,))
    if cursor.fetchone():
        print(f"User {user_id} already exists.")
    else:
        cursor.execute("INSERT INTO Students (id, name, year_of_study) VALUES (?, ?, ?)", (user_id, 'Ngô Minh', 1))
        print(f"User {user_id} added.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_user()
