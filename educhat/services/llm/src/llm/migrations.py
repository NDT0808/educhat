import sqlite3
import os

def run_migrations():
    db_path = os.getenv("DB_PATH", "data/sgu_schedules.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Running migrations on {db_path}...")
    
    # 1. Course Prerequisites
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS course_prerequisites (
        course_id INTEGER,
        prereq_id INTEGER,
        type TEXT DEFAULT 'prereq',
        PRIMARY KEY (course_id, prereq_id),
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(prereq_id) REFERENCES courses(id)
    );
    """)
    
    # 2. Terms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS terms (
        id TEXT PRIMARY KEY,
        name TEXT,
        start_date DATE,
        end_date DATE,
        reg_start DATE,
        reg_end DATE
    );
    """)
    
    # 3. Course Feedback
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS course_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        term_id TEXT,
        workload INTEGER,
        materials INTEGER,
        practical INTEGER,
        fairness INTEGER,
        support INTEGER,
        overall INTEGER,
        tags TEXT,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(term_id) REFERENCES terms(id)
    );
    """)
    
    # Seed some basic data for terms
    cursor.execute("INSERT OR IGNORE INTO terms VALUES ('2024.1', 'Học kỳ 1 - 2024-2025', '2024-09-01', '2025-01-15', '2024-08-01', '2024-08-15')")
    cursor.execute("INSERT OR IGNORE INTO terms VALUES ('2024.2', 'Học kỳ 2 - 2024-2025', '2025-02-15', '2025-06-30', '2025-01-15', '2025-01-30')")
    
    conn.commit()
    conn.close()
    print("Migrations completed successfully.")

if __name__ == "__main__":
    run_migrations()
