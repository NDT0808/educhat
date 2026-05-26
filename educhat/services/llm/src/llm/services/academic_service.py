import sqlite3
import os
import json
import itertools
from typing import List, Dict, Any, Optional
import random
from datetime import datetime
from common.schemas import (
    PlannerRequest, PlannerResponse, GeneratedPlan, OfferingDetail, ScoreBreakdown,
    CheckerRequest, CheckerResponse, ConflictResult,
    FeedbackSubmitRequest, HeatmapResult
)

DB_PATH = os.getenv("DB_PATH", "data/hmu_schedules.db")

class AcademicService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Planner logic ---

    def generate_plans(self, request: PlannerRequest) -> PlannerResponse:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. Get eligible courses (not yet passed)
        cursor.execute("""
            SELECT c.* FROM courses c
            LEFT JOIN student_registrations sr ON c.id = sr.course_id AND sr.student_id = ? AND sr.status = 'Passed'
            WHERE sr.id IS NULL
        """, (request.student_id,))
        eligible_courses = [dict(row) for row in cursor.fetchall()]
        
        # 2. Filter by credits and core status (BatBuoc)
        cursor.execute("SELECT admission_year FROM students WHERE id = ?", (request.student_id,))
        student = cursor.fetchone()
        admission_year = student['admission_year'] if student else 2024
        
        current_year = max(1, 2024 - admission_year + 1)
        
        # Logic for strict_mode: if true, only include desired courses
        if request.strict_mode:
            relevant_courses = [c for c in eligible_courses if c['id'] in request.desired_course_ids]
        else:
            # Use recommended year logic as base
            relevant_courses = [c for c in eligible_courses if c['recommended_year'] <= current_year]
            
            # Ensure desired courses are included even if not in recommended year
            if request.desired_course_ids:
                for cid in request.desired_course_ids:
                    if not any(c['id'] == cid for c in relevant_courses):
                        course = next((c for c in eligible_courses if c['id'] == cid), None)
                        if course:
                            relevant_courses.append(course)
        
        # 3. Find offerings for these courses in the target term
        offerings_by_course = {}
        for course in relevant_courses:
            cursor.execute("SELECT * FROM course_offerings WHERE course_id = ? AND semester = ?", 
                          (course['id'], request.term_id))
            offering_rows = [dict(row) for row in cursor.fetchall()]
            if offering_rows:
                offerings_by_course[course['id']] = offering_rows
        
        # 4. Deterministic Beam Search
        course_ids = list(offerings_by_course.keys())
        
        # Identify required courses from request
        required_ids = [cid for cid in course_ids if cid in request.desired_course_ids]
        
        # Helper to get offering by ID
        all_offerings_map = {}
        for offs in offerings_by_course.values():
            for o in offs:
                all_offerings_map[o['id']] = o

        # Sort courses: Required -> Core -> Credits(Desc) -> Code
        def course_priority(c):
            is_req = c['id'] in required_ids
            is_core = c['course_type'] == 'BatBuoc'
            return (not is_req, not is_core, -c['credits'], c['course_code'])
            
        # Only consider courses that have offerings
        search_courses = [c for c in relevant_courses if c['id'] in offerings_by_course]
        search_courses.sort(key=course_priority)
        
        # Beam State: (offering_ids, total_credits, penalty_score, schedule_map)
        # schedule_map: dict { day: set(periods) }
        # Start with empty plan
        initial_state = ([], 0, 0.0, {}) 
        beams = [initial_state]
        BEAM_WIDTH = 50 # Increase width for better quality
        
        for course in search_courses:
            course_id = course['id']
            offerings = offerings_by_course[course_id]
            next_beams = []
            
            for (p_ids, p_credits, p_penalty, p_map) in beams:
                # Option 1: Skip Course 
                # (Always allowed, but we penalized it implicitly by having lower credits)
                # If course is REQUIRED, we really should try to fit it. 
                # Penalize skipping required course heavily? 
                # For now, let credit maximization handle it (required are high priority so they are processed first).
                # If we skip a required course here, it might get beaten by a plan that includes it.
                next_beams.append((p_ids, p_credits, p_penalty, p_map))
                
                # Option 2: Try each offering
                for off in offerings:
                    # Check Max Credits
                    if p_credits + course['credits'] > request.max_credits:
                        continue
                        
                    # Check Hard Conflicts (Time)
                    day = off['day_of_week']
                    start, end = off['start_period'], off['end_period']
                    periods = set(range(start, end + 1))
                    
                    if day in p_map and not p_map[day].isdisjoint(periods):
                        continue # Overlap
                        
                    # Calculate Preference Penalty for this offering
                    new_penalty = p_penalty
                    
                    # Basic preference checks (Soft Constraints)
                    # Note: Full scoring happens at the end, this is just heuristic for search
                    prefs = request.preferences
                    
                    # Map Vietnamese day to English normalized day
                    db_to_en = {
                        "Thứ 2": "MON", "Thứ 3": "TUE", "Thứ 4": "WED",
                        "Thứ 5": "THU", "Thứ 6": "FRI", "Thứ 7": "SAT",
                        "Chủ nhật": "SUN"
                    }
                    # Avoid Days (HARD CONSTRAINT)
                    if day in prefs.avoid_days:
                         continue
                         
                    # "Morning Only" (HARD CONSTRAINT: Must END by Period 5)
                    if prefs.prefer_morning and end > 5:
                        continue # Loại bỏ luôn nếu dính buổi chiều
                        
                    # "No Evening" (HARD CONSTRAINT khi ưu tiên học sáng)
                    if (prefs.prefer_morning or getattr(prefs, 'no_evening', False)) and end >= 10:
                         continue # Loại bỏ luôn các tiết tối nếu muốn học sáng
                         
                    # Compact days penalty during search (Extreme)
                    if getattr(prefs, 'compact_days', False) and day not in p_map:
                         # Phạt lũy tiến: Càng nhiều ngày càng phạt nặng khủng khiếp
                         new_penalty += (len(p_map) + 1) * 200 
                    
                    # Create new state
                    new_ids = p_ids + [off['id']]
                    new_credits = p_credits + course['credits']
                    new_map = p_map.copy()
                    if day not in new_map: new_map[day] = set()
                    new_map[day] = new_map[day] | periods # Union
                    
                    next_beams.append((new_ids, new_credits, new_penalty, new_map))
            
            # Prune
            # Sort by: Total Credits DESC, Penalty ASC
            # Use unique signature (tuple of sorted ids) to dedup identical plans if needed, 
            # but usually path-dependence makes them unique.
            # Phân hạng: Nếu dồn lịch, Penalty sẽ có trọng số cực lớn để lấn át cả số tín chỉ
            if getattr(prefs, 'compact_days', False):
                # Công thức: Tín chỉ - (Penalty / 50). Ví dụ: 18 tín - (300 phạt / 50) = 12 điểm. 
                # Nó sẽ thua bộ lịch 15 tín - (100 phạt / 50) = 13 điểm.
                next_beams.sort(key=lambda x: (x[1] - (x[2] / 50), -x[2]), reverse=True)
            else:
                next_beams.sort(key=lambda x: (x[1], -x[2]), reverse=True)
                
            beams = next_beams[:BEAM_WIDTH]
            
        # 5. Filter by min_credits and evaluate quality
        valid_plans = []
        plans = []
        unique_plans = set()
        
        for (p_ids, p_credits, p_penalty, _) in beams:
             if p_credits < request.min_credits:
                 continue
                 
             # Dedup based on set of IDs
             ids_tuple = tuple(sorted(p_ids))
             if ids_tuple in unique_plans:
                 continue
             unique_plans.add(ids_tuple)
             
             current_plan_offerings = [all_offerings_map[oid] for oid in p_ids]
             
             if not current_plan_offerings:
                 continue

             # Calculate final rigorous quality score
             score, breakdown = self._calculate_quality_score(current_plan_offerings, request.preferences)
             
             # Apply search penalty if we want stricter adherence, 
             # but _calculate_quality_score covers most standard metrics (gaps, days).
             # Let's trust _calculate_quality_score but ensure penalties from search are reflected if missing.
             # Actually, let's just use the rigorous score. It's robust.
             
             # Populate detailed offering info
             offering_details = []
             for o in current_plan_offerings:
                    course = next((c for c in relevant_courses if c['id'] == o['course_id']), None)
                    if course:
                        offering_details.append(OfferingDetail(
                            id=o['id'],
                            course_id=o['course_id'],
                            course_code=course['course_code'],
                            course_name=course['name'],
                            class_code=o['class_code'],
                            credits=course['credits'],
                            day=o['day_of_week'],
                            start_period=o['start_period'],
                            end_period=o['end_period'],
                            room=o['room']
                        ))

             plans.append(GeneratedPlan(
                    offering_ids=p_ids,
                    offerings=offering_details,
                    total_credits=p_credits,
                    quality_score=score,
                    score_breakdown=breakdown,
                    explanation=f"Kế hoạch tối ưu: {p_credits} tín chỉ, mức độ tối ưu {score:.1f}/100."
             ))
             
             # Calculate for all final beams to ensure we find the true best score
             # (Beam search penalty was heuristic, this score is accurate)
        
        # Sort plans by Total Credits (Descending) then Quality Score (Descending)
        plans.sort(key=lambda x: (x.total_credits, x.quality_score), reverse=True)
        
        return PlannerResponse(status="success", plans=plans[:5])

    def _check_conflicts(self, offerings: List[Dict]) -> List[ConflictResult]:
        conflicts = []
        for i in range(len(offerings)):
            for j in range(i + 1, len(offerings)):
                o1, o2 = offerings[i], offerings[j]
                if o1['day_of_week'] == o2['day_of_week']:
                    # Period overlap check
                    if max(o1['start_period'], o2['start_period']) <= min(o1['end_period'], o2['end_period']):
                        conflicts.append(ConflictResult(
                            offering_id_a=o1['id'],
                            offering_id_b=o2['id'],
                            reason=f"Xung đột vào {o1['day_of_week']} (Tiết {o1['start_period']}-{o1['end_period']} vs {o2['start_period']}-{o2['end_period']})"
                        ))
        return conflicts

    def _calculate_quality_score(self, offerings: List[Dict], prefs: Any) -> (float, ScoreBreakdown):
        # Scoring logic based on design doc
        days_on_campus = len(set(o['day_of_week'] for o in offerings))
        
        # Calculate gaps
        total_gap_mins = 0
        back_to_back = 0
        evening_count = 0
        earliest = 99
        latest = 0
        
        days_map = {}
        for o in offerings:
            day = o['day_of_week']
            if day not in days_map: days_map[day] = []
            days_map[day].append((o['start_period'], o['end_period']))
            if o['start_period'] < earliest: earliest = o['start_period']
            if o['end_period'] > latest: latest = o['end_period']
            if o['end_period'] > 8: evening_count += 1 # Rough estimate for evening
            
        for day, sessions in days_map.items():
            sessions.sort()
            for i in range(len(sessions) - 1):
                gap = sessions[i+1][0] - sessions[i][1] - 1
                if gap == 0: back_to_back += 1
                elif gap > 0: total_gap_mins += gap * 45 # Each period approx 45-50 mins
                
        # Base score 100
        score = 100
        
        if getattr(prefs, 'compact_days', False):
            # Exponential Penalty: (days^2) * 20
            score -= (days_on_campus ** 2) * 20 
        else:
            score -= max(0, (days_on_campus - 3) * 10)
            
        score -= (total_gap_mins // 15) * 2
        
        if (prefs.prefer_morning or getattr(prefs, 'no_evening', False)) and evening_count > 0: 
            score -= 80 # Phạt nặng nếu có tiết tối khi đang ưu tiên học sáng
        if prefs.prefer_morning and earliest > 4: 
            score -= 50 # Phạt nếu tiết đầu tiên bắt đầu quá muộn (sau tiết 4)
        
        breakdown = ScoreBreakdown(
            days_on_campus=days_on_campus,
            gaps_total_minutes=total_gap_mins,
            earliest_start=f"Tiết {earliest}",
            latest_end=f"Tiết {latest}",
            back_to_back_count=back_to_back,
            evening_count=evening_count
        )
        
        return max(0.0, float(score)), breakdown

    # --- Apply Plan logic ---

    def apply_plan(self, student_id: int, term_id: str, offering_ids: List[int]) -> Dict:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Xóa các đăng ký cũ của học kỳ này trước khi lưu lịch mới
        cursor.execute(
            "DELETE FROM student_registrations WHERE student_id = ? AND semester = ?",
            (student_id, term_id)
        )
        
        registered_courses = []
        for oid in offering_ids:
            cursor.execute("SELECT * FROM course_offerings WHERE id = ?", (oid,))
            offering = cursor.fetchone()
            if not offering:
                continue
            offering = dict(offering)
            
            # Check if already registered
            cursor.execute(
                "SELECT id FROM student_registrations WHERE student_id = ? AND course_id = ? AND semester = ?",
                (student_id, offering['course_id'], term_id)
            )
            if cursor.fetchone():
                continue  # Skip duplicates
            
            # Kiểm tra xem cột offering_id có tồn tại không
            cursor.execute("PRAGMA table_info(student_registrations)")
            columns = [col['name'] for col in cursor.fetchall()]
            
            if 'offering_id' in columns:
                cursor.execute(
                    "INSERT INTO student_registrations (student_id, course_id, status, semester, offering_id) VALUES (?, ?, 'Studying', ?, ?)",
                    (student_id, offering['course_id'], term_id, oid)
                )
            else:
                cursor.execute(
                    "INSERT INTO student_registrations (student_id, course_id, status, semester) VALUES (?, ?, 'Studying', ?)",
                    (student_id, offering['course_id'], term_id)
                )
            
            # Get course name for confirmation
            cursor.execute("SELECT name, course_code FROM courses WHERE id = ?", (offering['course_id'],))
            course = cursor.fetchone()
            if course:
                course = dict(course)
                registered_courses.append({
                    "course_code": course['course_code'],
                    "name": course['name'],
                    "class_code": offering['class_code'],
                    "day": offering['day_of_week'],
                    "period": f"Tiết {offering['start_period']}-{offering['end_period']}",
                    "room": offering['room']
                })
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Đã đăng ký thành công {len(registered_courses)} môn học.",
            "registered_courses": registered_courses
        }

    def get_student_timetable(self, student_id: int, term_id: str) -> List[Dict]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Check if offering_id column exists
            cursor.execute("PRAGMA table_info(student_registrations)")
            columns = [col['name'] for col in cursor.fetchall()]
            
            if 'offering_id' in columns:
                cursor.execute("""
                    SELECT 
                        c.course_code, c.name, c.credits,
                        co.class_code, co.day_of_week, co.start_period, co.end_period, co.room
                    FROM student_registrations sr
                    JOIN courses c ON sr.course_id = c.id
                    JOIN course_offerings co ON sr.offering_id = co.id
                    WHERE sr.student_id = ? AND sr.semester = ?
                """, (student_id, term_id))
            else:
                # Fallback join: ignore semester mismatch in mock data for course offerings
                cursor.execute("""
                    SELECT 
                        c.course_code, c.name, c.credits,
                        co.class_code, co.day_of_week, co.start_period, co.end_period, co.room
                    FROM student_registrations sr
                    JOIN courses c ON sr.course_id = c.id
                    JOIN course_offerings co ON sr.course_id = co.course_id
                    WHERE sr.student_id = ? AND sr.semester = ?
                """, (student_id, term_id))
            
            rows = cursor.fetchall()
            timetable = []
            for row in rows:
                timetable.append(dict(row))
                
            return timetable
        finally:
            conn.close()

    # --- Checker logic ---

    def check_registration(self, request: CheckerRequest) -> CheckerResponse:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. Get offering details
        cursor.execute(f"SELECT * FROM course_offerings WHERE id IN ({','.join(['?']*len(request.offering_ids))})", request.offering_ids)
        selected_offerings = [dict(row) for row in cursor.fetchall()]
        
        # 2. Check conflicts
        conflicts = self._check_conflicts(selected_offerings)
        
        # 3. Check prerequisites
        course_ids = [o['course_id'] for o in selected_offerings]
        missing_prereqs = []
        for course_id in course_ids:
            cursor.execute("""
                SELECT p.prereq_id, c.course_code FROM course_prerequisites p
                JOIN courses c ON p.prereq_id = c.id
                WHERE p.course_id = ?
            """, (course_id,))
            prereqs = cursor.fetchall()
            for p in prereqs:
                cursor.execute("SELECT id FROM student_registrations WHERE student_id = ? AND course_id = ? AND status = 'Passed'",
                             (request.student_id, p['prereq_id']))
                if not cursor.fetchone():
                    missing_prereqs.append(p['course_code'])
        
        return CheckerResponse(
            conflicts=conflicts,
            missing_prereqs=list(set(missing_prereqs)),
            missing_coreqs=[],
            capacity_issues=[], # Static for now
            warnings=[]
        )

    # --- Feedback logic ---

    def submit_feedback(self, request: FeedbackSubmitRequest):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO course_feedback 
            (student_id, course_id, term_id, workload, materials, practical, fairness, support, overall, tags, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (request.student_id, request.course_id, request.term_id, 
              request.workload, request.materials, request.practical, 
              request.fairness, request.support, request.overall, 
              ",".join(request.tags), request.comment))
        conn.commit()
        conn.close()

    def get_heatmap(self, term_id: str, course_id: Optional[int] = None) -> HeatmapResult:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM course_feedback WHERE term_id = ?"
        params = [term_id]
        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)
            
        cursor.execute(query, params)
        feedbacks = [dict(row) for row in cursor.fetchall()]
        
        if len(feedbacks) < 5: # privacy threshold
            return HeatmapResult(avg_scores={}, tag_counts={}, sample_size=len(feedbacks))
            
        # Aggregation
        metrics = ['workload', 'materials', 'practical', 'fairness', 'support', 'overall']
        avg_scores = {m: sum(f[m] for f in feedbacks) / len(feedbacks) for m in metrics}
        
        all_tags = []
        for f in feedbacks:
            if f['tags']: all_tags.extend(f['tags'].split(","))
            
        tag_counts = {}
        for t in all_tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
            
        return HeatmapResult(avg_scores=avg_scores, tag_counts=tag_counts, sample_size=len(feedbacks))

    # --- Calendar logic ---

    def get_ics_content(self, student_id: int, term_id: str) -> str:
        # P0: simplified ICS generation
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT co.*, c.name as course_name, c.course_code, t.start_date, t.end_date 
            FROM student_registrations sr
            JOIN course_offerings co ON sr.course_id = co.course_id AND sr.semester = co.semester
            JOIN courses c ON co.course_id = c.id
            JOIN terms t ON co.semester = t.id
            WHERE sr.student_id = ? AND sr.semester = ? AND sr.status = 'Studying'
        """, (student_id, term_id))
        
        rows = cursor.fetchall()
        
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//EduChat//NONSGML Academic Calendar//EN",
            "X-WR-TIMEZONE:Asia/Ho_Chi_Minh"
        ]
        
        # Day mapping for RRULE
        day_map = {"Thứ 2": "MO", "Thứ 3": "TU", "Thứ 4": "WE", "Thứ 5": "TH", "Thứ 6": "FR", "Thứ 7": "SA", "Chủ nhật": "SU"}
        
        # Period to time mapping (Example)
        time_map = {
            1: "073000", 2: "082000", 3: "091000", 4: "101000", 5: "110000",
            6: "130000", 7: "135000", 8: "144000", 9: "154000", 10: "163000",
            11: "180000", 12: "190000"
        }
        
        # Period end mapping
        time_end_map = {
            1: "082000", 2: "091000", 3: "100000", 4: "110000", 5: "115000",
            6: "135000", 7: "144000", 8: "153000", 9: "163000", 10: "172000",
            11: "185000", 12: "195000"
        }

        for row in rows:
            start_date_str = row['start_date'].replace("-", "")
            end_date_str = row['end_date'].replace("-", "")
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:{row['course_code']} - {row['course_name']}",
                f"LOCATION:{row['room']}",
                f"DTSTART;TZID=Asia/Ho_Chi_Minh:{start_date_str}T{time_map.get(row['start_period'], '080000')}",
                f"DTEND;TZID=Asia/Ho_Chi_Minh:{start_date_str}T{time_end_map.get(row['end_period'], '090000')}",
                f"RRULE:FREQ=WEEKLY;BYDAY={day_map.get(row['day_of_week'], 'MO')};UNTIL={end_date_str}T235959Z",
                "END:VEVENT"
            ])
            
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
