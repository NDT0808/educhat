import sqlite3
import re
import random

DB_PATH = "data/sgu_schedules.db"
INPUT_FILE = "sgu_curriculum.txt"

# ===== Bảng học kỳ gợi ý theo chương trình SGU CNTT =====
SEMESTER_MAP = {
    # HK1 - Năm 1
    "Những nguyên lý cơ bản của Chủ nghĩa Mác - Lênin": 1,
    "Tiếng Anh B1-1": 1,
    "Giải tích": 1,
    "Cơ sở lập trình": 1,
    "Pháp luật đại cương": 1,
    # HK2 - Năm 1
    "Tư tưởng Hồ Chí Minh": 2,
    "Tiếng Anh B1-2": 2,
    "Đại số": 2,
    "Kỹ thuật lập trình": 2,
    "Xác suất thống kê A": 2,
    # HK3 - Năm 2
    "Đường lối cách mạng của ĐCSVN": 3,
    "Tiếng Anh B2-1": 3,
    "Phương pháp NCKH trong công nghệ thông tin": 3,
    "Kiến trúc máy tính": 3,
    "Toán rời rạc": 3,
    "Lập trình hướng đối tượng": 3,
    "Phát triển ứng dụng web 1": 3,
    # HK4 - Năm 2
    "Tiếng Anh B2-2": 4,
    "Mạng máy tính": 4,
    "Lập trình Java": 4,
    "Phát triển ứng dụng web 2": 4,
    "Cấu trúc dữ liệu và giải thuật": 4,
    "Lý thuyết đồ thị": 4,
    "Cơ sở dữ liệu": 4,
    # HK5 - Năm 3
    "Cơ sở trí tuệ nhân tạo": 5,
    "Công nghệ phần mềm": 5,
    "Hệ điều hành mã nguồn mở": 5,
    "Phân tích thiết kế hệ thống thông tin": 5,
    "Các hệ quản trị cơ sở dữ liệu": 5,
    "Phát triển ứng dụng trên thiết bị di động": 5,
    "Quản trị mạng": 5,
    "Đồ họa máy tính": 5,
    "Phân tích thiết kế hướng đối tượng": 5,
    # HK6 - Năm 3
    "Kiểm thử phần mềm": 6,
    "Chuyên đề tốt nghiệp": 6,
    "Hệ thống thông tin doanh nghiệp": 6,
    "Nhập môn thị giác máy tính": 6,
    "Thương mại điện tử và ứng dụng": 6,
    "Phân tích và thiết kế giải thuật": 6,
    "Quản lý dự án phần mềm": 6,
    "An ninh mạng máy tính": 6,
    "Kỹ năng nghề nghiệp công nghệ thông tin": 6,
    "Kiến thức nền tảng về bảo mật": 6,
    "Phát triển hệ thống nhúng": 6,
    "Phát triển ứng dụng internet of things": 6,
    # HK7 - Năm 4
    "Thực tập tốt nghiệp": 7,
    "Khai phá dữ liệu": 7,
    "Các công nghệ lập trình hiện đại": 7,
    "Thiết kế hệ thống mạng": 7,
    "Điện toán đám mây": 7,
    "Máy học": 7,
    # HK8 - Năm 4
    "Seminar chuyên đề": 8,
}


def create_schema(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS student_registrations")
    cursor.execute("DROP TABLE IF EXISTS course_offerings")
    cursor.execute("DROP TABLE IF EXISTS courses")
    cursor.execute("DROP TABLE IF EXISTS students")

    cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_code TEXT UNIQUE,
        name TEXT,
        admission_year INTEGER,
        cohort INTEGER,
        gpa REAL,
        credits_earned INTEGER,
        password_hash TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE,
        name TEXT,
        credits REAL,
        theory_credits REAL,
        practice_credits REAL,
        recommended_year INTEGER,
        course_type TEXT,
        semester_default TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE course_offerings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        class_code TEXT,
        semester TEXT,
        day_of_week TEXT,
        start_period INTEGER,
        end_period INTEGER,
        room TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE student_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        offering_id INTEGER,
        status TEXT,
        grade REAL,
        semester TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(offering_id) REFERENCES course_offerings(id)
    )
    """)

    conn.commit()


def parse_curriculum(file_path):
    print(f"Đang đọc chương trình đào tạo SGU từ {file_path}...")
    courses = []

    # Pattern: <số> <Tên môn học> <tổng TC> <LT> <TH>
    pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$")

    current_type = 'BatBuoc'
    code_counter = 1000

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()

            # Nhận diện phần tự chọn
            if "Tự chọn" in line:
                current_type = 'TuChon'
            elif "Bắt buộc" in line:
                current_type = 'BatBuoc'

            match = pattern.match(line)
            if not match:
                continue

            name = match.group(1).strip()
            total_cre = float(match.group(2))
            theo_cre = float(match.group(3))
            prac_cre = float(match.group(4))

            if len(name) < 3:
                continue

            # Lấy học kỳ từ bảng kế hoạch
            semester_num = SEMESTER_MAP.get(name, 5)
            # Tính năm học từ học kỳ (HK1-2 = năm 1, HK3-4 = năm 2, ...)
            recommended_year = (semester_num + 1) // 2

            code = f"IT{code_counter}"
            code_counter += 1

            courses.append({
                "code": code,
                "name": name,
                "credits": total_cre,
                "theory": theo_cre,
                "practice": prac_cre,
                "year": recommended_year,
                "type": current_type,
                "semester": "2024.1" if semester_num % 2 != 0 else "2024.2"
            })

    print(f"  → Tìm thấy {len(courses)} học phần.")
    return courses


def generate_schedule(conn, courses):
    cursor = conn.cursor()
    print("Đang sinh lịch học ngẫu nhiên...")

    rooms = [f"A{i}" for i in range(101, 115)] + \
            [f"B{i}" for i in range(201, 210)] + \
            ["Hội trường 1", "Hội trường 2", "Lab CNTT 1", "Lab CNTT 2", "Lab Mạng"]

    shifts = [
        (1, 3), (4, 6),        # Sáng 2 ca
        (7, 9), (10, 12),      # Chiều 2 ca
        (1, 4), (5, 8),        # Ca dài
    ]
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]

    occupied = set()

    for course in courses:
        if course['credits'] == 0:
            continue

        num_classes = random.randint(1, 3) if course['type'] == 'BatBuoc' else 1

        for i in range(num_classes):
            class_code = f"{course['code']}_{i+1:02d}"
            placed = False
            attempts = 0

            while not placed and attempts < 150:
                attempts += 1
                day = random.choice(days)
                shift = random.choice(shifts)
                start, end = shift
                room = random.choice(rooms)

                collision = any((day, p, room) in occupied for p in range(start, end + 1))

                if not collision:
                    for p in range(start, end + 1):
                        occupied.add((day, p, room))

                    cursor.execute("""
                    INSERT INTO course_offerings
                        (course_id, class_code, semester, day_of_week, start_period, end_period, room)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (course['db_id'], class_code, course['semester'],
                          day, start, end, room))
                    placed = True

            if not placed:
                print(f"  ⚠ Không thể xếp lịch cho: {course['name']}")

    conn.commit()


def generate_students(conn):
    import random
    random.seed(42) # Cố định danh sách sinh viên được sinh ra không bị đổi sau mỗi lần build
    
    cursor = conn.cursor()
    print("Đang tạo danh sách sinh viên mẫu (SGU CNTT)...")

    first_names = ["An", "Bình", "Châu", "Dũng", "Giang", "Hương", "Khánh",
                   "Lan", "Minh", "Nam", "Phong", "Quân", "Sơn", "Thảo",
                   "Uyên", "Vân", "Xuân", "Yến", "Tú", "Long", "Hải", "Đức"]
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh",
                  "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]

    for i in range(60):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        full_name = f"{lname} {fname}"
        year_of_study = random.randint(1, 4)          # SGU CNTT = 4 năm
        admission_year = 2025 - year_of_study + 1
        # Mã sinh viên SGU: 22XXXX (năm nhập học + số thứ tự)
        student_code = f"{admission_year % 100:02d}{i:04d}"
        gpa = round(random.uniform(2.0, 4.0), 2)
        credits = year_of_study * 34  # ~136 TC / 4 năm

        cursor.execute("""
        INSERT OR IGNORE INTO students
            (student_code, name, admission_year, cohort, gpa, credits_earned, password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_code, full_name, admission_year, year_of_study, gpa, credits, ""))

    # Tạo một tài khoản cố định không bao giờ thay đổi để dễ test
    cursor.execute("""
    INSERT OR IGNORE INTO students
        (student_code, name, admission_year, cohort, gpa, credits_earned, password_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("999999", "Sinh viên Cố định (Test)", 2022, 4, 3.8, 120, ""))

    conn.commit()
    print("  → Đã tạo 61 sinh viên (có 1 tài khoản cố định 999999).")


def populate_db():
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print(f"\n{'='*50}")
    print(f"  Tạo database SGU CNTT: {DB_PATH}")
    print(f"{'='*50}")

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    # 1. Parse & insert courses
    courses_data = parse_curriculum(INPUT_FILE)
    cursor = conn.cursor()
    db_courses = []

    for c in courses_data:
        try:
            cursor.execute("""
            INSERT INTO courses
                (course_code, name, credits, theory_credits, practice_credits,
                 recommended_year, course_type, semester_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (c['code'], c['name'], c['credits'], c['theory'], c['practice'],
                  c['year'], c['type'], c['semester']))
            c['db_id'] = cursor.lastrowid
            db_courses.append(c)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"  → Đã lưu {len(db_courses)} học phần vào DB.")

    # 2. Generate schedule
    generate_schedule(conn, db_courses)

    # 3. Generate students
    generate_students(conn)

    conn.close()
    print(f"\n✅ Hoàn tất! DB đã được tạo tại: {DB_PATH}")
    print(f"   Chứa: {len(db_courses)} môn học, lịch học, 60 sinh viên SGU CNTT")


if __name__ == "__main__":
    populate_db()
