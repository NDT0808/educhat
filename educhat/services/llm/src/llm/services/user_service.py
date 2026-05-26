
import sqlite3
import os
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from pydantic import BaseModel

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB_PATH is resolved at runtime to pick up Docker env vars correctly

class User(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    hashed_password: str
    admission_year: int
    cohort: int # 1, 2, 3...

class UserService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("DB_PATH", "data/sgu_schedules.db")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_user_by_student_code(self, student_code: str) -> Optional[User]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Try with password_hash first, fallback for legacy schema
            try:
                cursor.execute(
                    "SELECT id, student_code, name, password_hash, admission_year, cohort FROM students WHERE student_code = ?",
                    (student_code,)
                )
            except sqlite3.OperationalError:
                # Column password_hash doesn't exist → use dummy value (master password works)
                cursor.execute(
                    "SELECT id, student_code, name, admission_year, cohort FROM students WHERE student_code = ?",
                    (student_code,)
                )
            row = cursor.fetchone()
            
            if row:
                keys = row.keys()
                return User(
                    id=str(row['id']),
                    username=row['student_code'],
                    full_name=row['name'],
                    role="student",
                    hashed_password=row['password_hash'] if 'password_hash' in keys else "",
                    admission_year=row['admission_year'],
                    cohort=row['cohort']
                )
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()

    def get_recommended_courses(self, year: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Get courses recommended for this year
            cursor.execute(
                "SELECT course_code, name, credits, semester_default FROM courses WHERE recommended_year = ? ORDER BY semester_default, course_code",
                (year,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching recommended courses: {e}")
            return []
        finally:
            conn.close()

    def get_curriculum_strategy(self, cohort: int) -> Dict[str, Any]:
        """
        Return curriculum strategy based on student year (cohort) for SGU IT.
        """
        strategy = {
            "year": cohort,
            "focus": "",
            "recommended_types": [],
            "message": "",
            "recommended_courses": []
        }
        
        if cohort == 1:
            strategy["focus"] = "Đại cương"
            strategy["recommended_types"] = ["Kiến thức giáo dục đại cương"]
            strategy["message"] = "Năm 1: Tập trung hoàn thành các môn Toán, Tiếng Anh và Lý luận chính trị."
        elif cohort == 2:
            strategy["focus"] = "Cơ sở ngành"
            strategy["recommended_types"] = ["Kiến thức cơ sở"]
            strategy["message"] = "Năm 2: Xây dựng nền tảng với Cơ sở lập trình, Cấu trúc dữ liệu và Kiến trúc máy tính."
        elif cohort == 3:
            strategy["focus"] = "Kiến thức ngành"
            strategy["recommended_types"] = ["Kiến thức ngành", "Chuyên ngành"]
            strategy["message"] = "Năm 3: Học chuyên sâu về OOP, Cơ sở dữ liệu, Web, Mobile và Trí tuệ nhân tạo."
        elif cohort >= 4:
            strategy["focus"] = "Đồ án & Thực tập"
            strategy["recommended_types"] = ["Chuyên ngành", "Thực tập", "Khóa luận"]
            strategy["message"] = f"Năm {cohort}: Hoàn thiện kỹ năng chuyên môn, thực tập thực tế và làm Khóa luận tốt nghiệp."
        
        # Fetch actual courses from DB
        strategy["recommended_courses"] = self.get_recommended_courses(cohort)
        
        return strategy

    def get_full_curriculum(self) -> List[Dict[str, Any]]:
        """
        Fetch the full IT curriculum grouped by year from the main schedule DB.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    recommended_year,
                    course_type,
                    name as course_name,
                    course_code,
                    credits
                FROM courses
                ORDER BY recommended_year ASC, course_type ASC, course_code ASC
            """)
            rows = cursor.fetchall()
            
            # Group by year
            years_map = {
                1: {"name": "Năm 1", "description": "Kiến thức Giáo dục Đại cương"},
                2: {"name": "Năm 2", "description": "Kiến thức Cơ sở ngành"},
                3: {"name": "Năm 3", "description": "Kiến thức Ngành & Chuyên ngành"},
                4: {"name": "Năm 4", "description": "Thực tập & Khóa luận Tốt nghiệp"}
            }
            
            years = {}
            for row in rows:
                y_num = row['recommended_year']
                if not y_num or y_num < 1: y_num = 1
                if y_num > 4: y_num = 4
                
                y_name = years_map[y_num]["name"]
                if y_name not in years:
                    years[y_name] = {
                        "name": y_name,
                        "description": years_map[y_num]["description"],
                        "courses": []
                    }
                
                years[y_name]["courses"].append({
                    "name": row['course_name'],
                    "code": row['course_code'],
                    "credits": float(row['credits']),
                    "block": row['course_type'],
                    "type": "Bắt buộc" if "BatBuoc" in row['course_type'] else "Tự chọn"
                })
            
            # Convert to list and sort by year number
            return sorted(list(years.values()), key=lambda x: x["name"])
        except Exception as e:
            print(f"Error fetching full curriculum: {e}")
            return []
        finally:
            conn.close()
