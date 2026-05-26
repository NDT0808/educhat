import sqlite3
import os

DB_PATH = "advisor.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Students
    cursor.execute("""
    CREATE TABLE Students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        year_of_study INTEGER NOT NULL
    );
    """)

    # 2. Courses
    cursor.execute("""
    CREATE TABLE Courses (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        credits INTEGER NOT NULL,
        description TEXT
    );
    """)

    # 3. Curriculum
    cursor.execute("""
    CREATE TABLE Curriculum (
        id INTEGER PRIMARY KEY,
        course_id INTEGER,
        recommended_year INTEGER NOT NULL,
        semester INTEGER NOT NULL,
        FOREIGN KEY (course_id) REFERENCES Courses(id)
    );
    """)

    # 4. OpenClasses
    cursor.execute("""
    CREATE TABLE OpenClasses (
        id INTEGER PRIMARY KEY,
        course_id INTEGER,
        semester_id TEXT NOT NULL, -- e.g., 'Sem1_2026'
        status TEXT NOT NULL CHECK(status IN ('open', 'closed')),
        FOREIGN KEY (course_id) REFERENCES Courses(id)
    );
    """)

    # ==========================
    # SEED DATA
    # ==========================
    
    # Students
    students = [
        (1, 'Nguyen Van A', 1),
        (2, 'Le Thi B', 2),
        (3, 'Tran Van C', 4)
    ]
    cursor.executemany("INSERT INTO Students (id, name, year_of_study) VALUES (?, ?, ?)", students)

    # Courses (Medical Data)
    courses = [
        (101, 'Giải phẫu đại cương', 3, 'Kiến thức về cấu trúc cơ thể người'),
        (102, 'Hóa sinh', 3, 'Các quá trình hóa học trong cơ thể'),
        (103, 'Sinh lý học', 4, 'Chức năng các cơ quan'),
        (201, 'Hệ Tim mạch', 4, 'Module tích hợp hệ tim mạch'),
        (202, 'Hệ Hô hấp', 4, 'Module tích hợp hệ hô hấp'),
        (401, 'Nội khoa cơ sở', 6, 'Lâm sàng Nội khoa'),
        (402, 'Ngoại khoa cơ sở', 6, 'Lâm sàng Ngoại khoa')
    ]
    cursor.executemany("INSERT INTO Courses (id, name, credits, description) VALUES (?, ?, ?, ?)", courses)

    # Curriculum
    # Year 1
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (101, 1, 1)")
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (102, 1, 1)")
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (103, 1, 2)")
    # Year 2
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (201, 2, 1)")
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (202, 2, 1)")
    # Year 4
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (401, 4, 1)")
    cursor.execute("INSERT INTO Curriculum (course_id, recommended_year, semester) VALUES (402, 4, 2)")

    # OpenClasses (Current Semester: Sem1_2026 for simulation)
    # Open: GP, Hoa Sinh, Tim mach
    # Closed: Ho hap
    open_classes = [
        (101, 'Sem1_2026', 'open'), # GP
        (102, 'Sem1_2026', 'open'), # Hoa Sinh
        (201, 'Sem1_2026', 'open'), # Tim mach
        (202, 'Sem1_2026', 'closed'), # Ho hap
        (401, 'Sem1_2026', 'open')  # Noi khoa
    ]
    cursor.executemany("INSERT INTO OpenClasses (course_id, semester_id, status) VALUES (?, ?, ?)", open_classes)

    conn.commit()
    conn.close()
    print("Database initialized and seeded.")

if __name__ == "__main__":
    init_db()
