import sqlite3
import os

def verify_database():
    # 1. Connect to an in-memory database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 2. Read and execute the SQL schema details
    sql_file = "curriculum_schema.sql"
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found.")
        return

    with open(sql_file, "r", encoding="utf-8") as f:
        sql_script = f.read()
    
    try:
        cursor.executescript(sql_script)
        print("✅ Schema and data executed successfully.\n")
    except sqlite3.Error as e:
        print(f"❌ SQL Execution Error: {e}")
        return

    # 3. Validation Queries

    print("--- Verifying Course Counts by Year ---")
    query_counts = """
        SELECT y.name, COUNT(c.id) 
        FROM Years y
        LEFT JOIN KnowledgeBlocks kb ON y.id = kb.year_id
        LEFT JOIN Courses c ON kb.id = c.knowledge_block_id
        GROUP BY y.name
        ORDER BY y.id;
    """
    cursor.execute(query_counts)
    counts = cursor.fetchall()
    for year_name, count in counts:
        print(f"  - {year_name}: {count} courses/modules")
    
    print("\n--- Verifying Hierarchical Courses (Thực hành + Đợt) ---")
    query_hierarchy = """
        SELECT parent.name AS ParentCourse, child.name AS Phase
        FROM Courses child
        JOIN Courses parent ON child.parent_course_id = parent.id
        WHERE parent.name IN ('Thực hành Nội khoa', 'Giải phẫu đại cương', 'Pháp y')
        ORDER BY parent.name, child.name;
    """
    cursor.execute(query_hierarchy)
    phases = cursor.fetchall()
    
    if phases:
        for parent, phase in phases:
             print(f"  - {parent} -> {phase}")
    else:
        print("  ❌ No multi-phase courses found for 'Thực hành Nội khoa'.")

    conn.close()

if __name__ == "__main__":
    verify_database()
