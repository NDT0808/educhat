import unidecode
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple
from common.schemas import ResolvedCourse, AmbiguousCourse, CourseCandidate, CourseResolutionResult
from common.logging import setup_logger

logger = setup_logger("course_resolver")

# SGU IT course aliases: common short names → full DB names
COURSE_ALIASES = {
    "ctdl": "Cấu trúc dữ liệu và Giải thuật",
    "gt1": "Toán cao cấp 1",
    "gt2": "Toán cao cấp 2",
    "hdt": "Lập trình hướng đối tượng",
    "csdl": "Cơ sở dữ liệu",
    "nmcn": "Nhập môn công nghệ phần mềm",
    "mmt": "Mạng máy tính",
    "ktmt": "Kiến trúc máy tính",
    "os": "Hệ điều hành",
    "web": "Lập trình Web",
    "ai": "Nhập môn Trí tuệ nhân tạo",
    "java": "Lập trình Java",
    "python": "Lập trình Python",
    "cpp": "Ngôn ngữ lập trình C++",
    "c": "Cơ sở lập trình",
    "lap trinh": "Cơ sở lập trình",
    "giai tich": "Toán cao cấp 1",
    "dai so": "Toán cao cấp 3",
}


class CourseResolver:
    def __init__(self, optimizer_service):
        self.optimizer_service = optimizer_service
        self.courses_cache = []  # List of {id, code, name, norm_name, norm_code}
        self.refresh_cache()

    def refresh_cache(self):
        """Load courses from optimizer service and normalize names for search."""
        raw_courses = self.optimizer_service.get_all_courses()
        self.courses_cache = []
        for c in raw_courses:
            c_id = c.get('id')
            c_code = c.get('course_code', '') or c.get('code', '')
            c_name = c.get('name', '')

            norm_name = self.normalize(c_name)
            norm_code = self.normalize(c_code)

            self.courses_cache.append({
                'id': c_id,
                'code': c_code,
                'name': c_name,
                'norm_name': norm_name,
                'norm_code': norm_code
            })
        logger.info(f"CourseResolver cache loaded: {len(self.courses_cache)} courses")

    def normalize(self, text: str) -> str:
        """Lowercase, strip accents, remove non-alphanumeric."""
        if not text:
            return ""
        text = unidecode.unidecode(text).lower()
        return " ".join(text.split())

    def _resolve_alias(self, query: str) -> Optional[str]:
        """Check if query matches any known alias. Returns the full course name or None."""
        norm_q = query.strip().lower()
        # Direct match
        if norm_q in COURSE_ALIASES:
            return COURSE_ALIASES[norm_q]
        # Normalized match
        ascii_q = self.normalize(query)
        for alias_key, alias_val in COURSE_ALIASES.items():
            if self.normalize(alias_key) == ascii_q:
                return alias_val
        return None

    def resolve(self, queries: List[str], threshold: float = 0.7) -> CourseResolutionResult:
        result = CourseResolutionResult()

        for q in queries:
            # 0. Check alias first
            alias_name = self._resolve_alias(q)
            if alias_name:
                logger.info(f"Alias resolved: '{q}' → '{alias_name}'")
                # Find the course in cache by name
                alias_norm = self.normalize(alias_name)
                alias_matches = [c for c in self.courses_cache if c['norm_name'] == alias_norm]
                if alias_matches:
                    result.resolved.append(ResolvedCourse(
                        query=q,
                        course_id=alias_matches[0]['id'],
                        confidence=1.0
                    ))
                    continue
                # Alias exists but course not in DB - fall through to fuzzy

            norm_q = self.normalize(q)

            # Dynamic threshold: lower for short queries
            effective_threshold = 0.5 if len(norm_q) <= 8 else threshold

            # 1. Exact match (code or name)
            exact_matches = [
                c for c in self.courses_cache
                if c['norm_code'] == norm_q or c['norm_name'] == norm_q
            ]

            if exact_matches:
                best = exact_matches[0]
                result.resolved.append(ResolvedCourse(
                    query=q,
                    course_id=best['id'],
                    confidence=1.0
                ))
                continue

            # 2. Fuzzy match
            scored_candidates = []
            for c in self.courses_cache:
                score_name = SequenceMatcher(None, norm_q, c['norm_name']).ratio()
                score_code = SequenceMatcher(None, norm_q, c['norm_code']).ratio()

                # Boost if query is a substring of name
                if norm_q in c['norm_name']:
                    score_name = max(score_name, 0.9)

                max_score = max(score_name, score_code)
                if max_score >= effective_threshold:
                    scored_candidates.append((max_score, c))

            scored_candidates.sort(key=lambda x: x[0], reverse=True)

            if not scored_candidates:
                # No candidates found - skip silently instead of blocking clarification
                logger.warning(f"No candidates found for query: '{q}'")
                result.needs_clarification.append(AmbiguousCourse(
                    query=q,
                    candidates=[],
                    reason="not_found"
                ))
            elif len(scored_candidates) == 1:
                score, match = scored_candidates[0]
                if score > 0.85:
                    result.resolved.append(ResolvedCourse(
                        query=q,
                        course_id=match['id'],
                        confidence=score
                    ))
                else:
                    result.needs_clarification.append(AmbiguousCourse(
                        query=q,
                        candidates=[self._to_candidate(match, score)],
                        reason="low_confidence"
                    ))
            else:
                top_score = scored_candidates[0][0]
                if top_score > 0.9 and (top_score - scored_candidates[1][0] > 0.1):
                    result.resolved.append(ResolvedCourse(
                        query=q,
                        course_id=scored_candidates[0][1]['id'],
                        confidence=top_score
                    ))
                else:
                    top_k = [self._to_candidate(c, s) for s, c in scored_candidates[:5]]
                    result.needs_clarification.append(AmbiguousCourse(
                        query=q,
                        candidates=top_k,
                        reason="ambiguous"
                    ))

        return result

    def resolve_to_codes(self, queries: List[str], threshold: float = 0.7) -> List[str]:
        """Convenience method for optimizer: returns only a list of course codes."""
        result = self.resolve(queries, threshold)
        codes = []
        for rc in result.resolved:
            # Find the code in cache
            match = [c for c in self.courses_cache if c['id'] == rc.course_id]
            if match:
                codes.append(match[0]['code'])
        return codes

    def _to_candidate(self, cache_item, score):
        return CourseCandidate(
            course_id=cache_item['id'],
            course_name=cache_item['name'],
            course_code=cache_item['code'],
            confidence=score
        )
