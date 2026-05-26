import sqlite3
import itertools
from typing import List, Dict, Any

import os

# DB_PATH is read at runtime (inside __init__) to ensure env vars are loaded first

def day_string_to_slug(day_str):
    mapping = {
        "Thứ 2": "monday", "Thứ 3": "tuesday", "Thứ 4": "wednesday", 
        "Thứ 5": "thursday", "Thứ 6": "friday", "Thứ 7": "saturday", "Chủ nhật": "sunday"
    }
    return mapping.get(day_str, "")

class ScheduleOptimizerService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("DB_PATH", "data/sgu_schedules.db")

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_course_offerings(self, course_codes: List[str], semester: str = "2024.1") -> Dict[str, List[Dict]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        offerings_by_course = {}
        
        try:
            for code in course_codes:
                cursor.execute("""
                    SELECT co.*, c.course_code, c.name, c.credits 
                    FROM course_offerings co
                    JOIN courses c ON co.course_id = c.id
                    WHERE c.course_code = ?
                """, (code,))
                rows = [dict(row) for row in cursor.fetchall()]
                if rows:
                    offerings_by_course[code] = rows
        finally:
            conn.close()
        
        return offerings_by_course

    def get_all_courses(self) -> List[Dict[str, str]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, course_code, name FROM courses ORDER BY course_code")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def check_overlap(self, s1: Dict, s2: Dict) -> bool:
        if s1['day_of_week'] != s2['day_of_week']:
            return False
        return max(s1['start_period'], s2['start_period']) <= min(s1['end_period'], s2['end_period'])

    def check_constraints(self, schedule: List[Dict], constraints: List[str]) -> float:
        score = 0
        days_with_classes = {} # day -> list of (start, end)
        
        for class_item in schedule:
            day = class_item['day_of_week']
            start = class_item['start_period']
            end = class_item['end_period']
            
            if day not in days_with_classes:
                days_with_classes[day] = []
            days_with_classes[day].append((start, end))
            
            # Weighted Constraints
            # User Definition: Morning = 1-6, Afternoon = 7+
            if "morning_only" in constraints and end > 6:
                score -= 50 # Penalty if it extends into Period 7+
            if "afternoon_only" in constraints and start <= 6:
                score -= 50 # Penalty if it starts in Period 1-6
            # Hard constraint: Nếu có ngày bận, loại bỏ luôn schedule này
            day_slug = day_string_to_slug(day)
            if f"no_{day_slug}" in constraints:
                return -999999 # Phạt cực nặng để loại bỏ phương án này
            
            # Check for specific period constraints
            for constraint in constraints:
                if constraint.startswith("no_period_"):
                    try:
                        forbidden_period = int(constraint.split("_")[-1])
                        if start <= forbidden_period <= end:
                             score -= 500 # Very high penalty for specific blocked period
                    except ValueError:
                        pass
        
        # Gap Penalty Calculation
        gap_penalty = 0
        for day, periods in days_with_classes.items():
            # Sort by start period
            periods.sort(key=lambda x: x[0])
            
            for i in range(len(periods) - 1):
                current_end = periods[i][1]
                next_start = periods[i+1][0]
                gap = next_start - current_end - 1
                if gap > 0:
                    gap_penalty += gap * 5 # Penalize 5 points per idle period
        
        score -= gap_penalty
        
        if "minimize_days" in constraints:
            score -= len(days_with_classes) * 20 # Stronger incentive to compact days
            
        return score

    
    def get_courses_by_year(self, year: int) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # course_type could be used to prioritize BatBuoc
            cursor.execute("SELECT course_code FROM courses WHERE recommended_year = ?", (year,))
            rows = cursor.fetchall()
            return [row['course_code'] for row in rows]
        finally:
            conn.close()

    async def extract_query_intent(self, user_query: str, prompt_client, llm_client, model) -> Dict[str, Any]:
        """
        Uses LLM to extract JSON structure from query:
        { "year": int, "courses": [], "constraints": [], "min_credits": int, "max_credits": int }
        """
        import json
        
        system_prompt = await prompt_client.render("schedule_extraction", {
            "query": user_query
        })
        
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        # Basic cleanup if Markdown code block is returned
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {content}")
            return {"year": None, "courses": [], "constraints": []}

    def optimize(self, course_codes: List[str], constraints: List[str], semester: str = "2024.1", min_credits: int = 0, max_credits: int = 30) -> List[Dict[str, Any]]:
        offerings_map = self.get_course_offerings(course_codes, semester)
        if not offerings_map:
            return []
        
        course_list = list(offerings_map.keys())
        if not course_list:
            return []

        all_section_groups = [offerings_map[code] for code in course_list]
        potential_schedules = itertools.product(*all_section_groups)
        
        valid_schedules = []
        
        # Limit processing to avoid timeout on massive combinations
        count = 0
        MAX_COMBINATIONS = 5000 
        
        for schedule_tuple in potential_schedules:
            count += 1
            if count > MAX_COMBINATIONS:
                break
                
            schedule = list(schedule_tuple)
            
            # Check total credits
            total_credits = sum(item['credits'] for item in schedule)
            if total_credits < min_credits or total_credits > max_credits:
                continue
            
            has_overlap = False
            for i in range(len(schedule)):
                for j in range(i + 1, len(schedule)):
                    if self.check_overlap(schedule[i], schedule[j]):
                        has_overlap = True
                        break
                if has_overlap: break
            
            if has_overlap:
                continue
                
            score = self.check_constraints(schedule, constraints)
            
            # Nếu vi phạm ràng buộc cứng (điểm cực thấp), loại bỏ hoàn toàn
            if score < -500000:
                continue
                
            valid_schedules.append({'schedule': schedule, 'score': score})
            
        valid_schedules.sort(key=lambda x: x['score'], reverse=True)
        return [item['schedule'] for item in valid_schedules[:5]]
