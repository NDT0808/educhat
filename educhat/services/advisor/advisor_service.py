import sqlite3
import re
import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI Client (Assuming Key in Ent)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or "dummy",
    base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
)
MODEL = os.getenv("OPENAI_MODEL") or "gpt-4o"

DB_PATH = os.path.join(os.path.dirname(__file__), "advisor.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =======================================================
# MODULE 1: TEXT-TO-SQL
# =======================================================

SYSTEM_PROMPT = """Bạn là một trợ lý ảo chuyên về cơ sở dữ liệu Y khoa. Khi nhận được yêu cầu từ sinh viên, bạn chỉ được phép truy vấn trong phạm vi các bảng đã cho.

Schema:
1. Years (id, name, description) -- Danh sách năm học (Năm 1, Năm 2...)
2. CourseTypes (id, name, code) -- Loại môn học (Lý thuyết, Thực hành, Lâm sàng, Module tích hợp)
3. KnowledgeBlocks (id, name, year_id) -- Khối kiến thực thuộc từng năm
4. Courses (id, name, code, credits, knowledge_block_id, course_type_id, parent_course_id) -- Môn học chi tiết. parent_course_id liên kết môn 'Thực hành' với môn 'Lý thuyết' tương ứng.
5. Students (id, name, student_code, admission_year, cohort) -- Thông tin sinh viên. 'cohort' tương ứng với năm học hiện tại (1=Năm 1, 2=Năm 2...).

Nguyên tắc 1: Để tìm môn học theo năm, hãy JOIN Courses -> KnowledgeBlocks -> Years.
Nguyên tắc 2: Để tìm môn thực hành của một môn lý thuyết, hãy truy vấn Courses có parent_course_id bằng id của môn lý thuyết đó.
Nguyên tắc 3: Output SQL phải tuân thủ cú pháp SQLite và luôn kết thúc bằng dấu chấm phẩy.
Nguyên tắc 4: Chỉ trả về mã SQL thuần túy, không định dạng Markdown.

Ví dụ:
User: "Tôi năm 2, muốn tìm các môn module hệ tim mạch"
SQL: SELECT c.name, c.credits FROM Courses c JOIN KnowledgeBlocks kb ON c.knowledge_block_id = kb.id JOIN Years y ON kb.year_id = y.id WHERE y.id = 2 AND c.name LIKE '%Tim mạch%';
"""

def generate_sql(user_prompt: str, student_id: int) -> str:
    """
    Generates SQL query from user prompt using LLM.
    """
    # Fetch student info to contextualize the prompt
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM Students WHERE id = ?", (student_id,)).fetchone()
    conn.close()

    if not student:
        raise ValueError(f"Student ID {student_id} not found.")

    context = f"Student Information: Year {student['cohort']}, Name {student['name']}."
    full_prompt = f"{context}\nUser Query: {user_prompt}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0
    )

    sql_query = response.choices[0].message.content.strip()
    
    # Cleaning Markdown if present
    sql_query = re.sub(r"```sql", "", sql_query)
    sql_query = re.sub(r"```", "", sql_query).strip()
    
    return sql_query

# =======================================================
# MODULE 2: EXECUTION (SAFE)
# =======================================================

def execute_sql(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executes the generated SQL query safely.
    """
    # Basic Safety Checks
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
        raise ValueError("Unsafe SQL query detected.")

    conn = get_db_connection()
    try:
        cursor = conn.execute(sql_query)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except sqlite3.Error as e:
        conn.close()
        raise ValueError(f"Database Execution Error: {e}")

# =======================================================
# MODULE 3: REFINEMENT
# =======================================================

def refine_response(user_prompt: str, sql_results: List[Dict[str, Any]]) -> str:
    """
    Converts raw SQL results into a friendly advice message.
    """
    if not sql_results:
        return "Hiện tại tôi không tìm thấy môn học nào phù hợp với yêu cầu của bạn hoặc các lớp đã đóng."

    data_str = json.dumps(sql_results, ensure_ascii=False, indent=2)
    
    refinement_prompt = f"""
    Bạn là tư vấn viên học vụ. Dựa vào kết quả dữ liệu dưới đây, hãy trả lời câu hỏi của sinh viên.
    
    Câu hỏi: "{user_prompt}"
    Dữ liệu tìm được: {data_str}
    
    Yêu cầu:
    1. Trả lời thân thiện, khuyến khích.
    2. Trình bày danh sách môn học dưới dạng Bullet points (Tên môn - Số tín chỉ).
    3. Nếu có mô tả môn học, hãy tóm tắt ngắn gọn.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Bạn là trợ lý học vụ hữu ích."},
            {"role": "user", "content": refinement_prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# =======================================================
# ORCHESTRATOR
# =======================================================

def get_advice(user_prompt: str, student_id: int) -> Dict[str, Any]:
    try:
        # 1. Text-to-SQL
        sql = generate_sql(user_prompt, student_id)
        
        # 2. Execution
        raw_data = execute_sql(sql)
        
        # 3. Refinement
        advice = refine_response(user_prompt, raw_data)
        
        return {
            "success": True,
            "sql_executed": sql,
            "data": raw_data,
            "advice": advice
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
