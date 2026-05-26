from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- RAG Schemas ---

class IngestRequest(BaseModel):
    source: str = Field(..., description="Source of the document (e.g., 'upload', 'repo')")
    documents: List[str] = Field(..., description="List of text content to ingest")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="Metadata for each document")

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class ChunkMetadata(BaseModel):
    source: str
    doc_id: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RetrievalResult(BaseModel):
    content: str
    metadata: ChunkMetadata
    score: float

# --- Prompt Schemas ---

class RenderRequest(BaseModel):
    template_name: str
    variables: Dict[str, Any]

# --- OCR Schemas ---

class OCRResponse(BaseModel):
    doc_id: str
    text_blocks: List[str]
    full_text: str

# --- LLM Schemas ---

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_context: Optional[Dict[str, Any]] = None
    doc_ids: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[RetrievalResult]
    emotion: Optional[str] = None

# --- Academic Schemas ---

class PlannerPreferences(BaseModel):
    avoid_days: List[str] = []
    avoid_time_ranges: List[str] = []
    compact_days: bool = False
    no_evening: bool = False
    max_gap_minutes: int = 120
    prefer_morning: bool = False

class PlannerRequest(BaseModel):
    student_id: int
    term_id: str
    min_credits: float
    max_credits: float
    preferences: PlannerPreferences
    pinned_offerings: List[int] = []
    desired_course_ids: List[int] = []
    strict_mode: bool = False

class ScoreBreakdown(BaseModel):
    days_on_campus: int
    gaps_total_minutes: int
    earliest_start: str
    latest_end: str
    back_to_back_count: int
    evening_count: int

class OfferingDetail(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_name: str
    class_code: str
    credits: float
    day: str
    start_period: int
    end_period: int
    room: str

class GeneratedPlan(BaseModel):
    offering_ids: List[int]
    offerings: List[OfferingDetail] = []
    total_credits: float
    quality_score: float
    score_breakdown: ScoreBreakdown
    explanation: str

class PlannerResponse(BaseModel):
    status: str
    plans: List[GeneratedPlan]

class CheckerRequest(BaseModel):
    student_id: int
    term_id: str
    offering_ids: List[int]

class ConflictResult(BaseModel):
    offering_id_a: int
    offering_id_b: int
    reason: str

class CheckerResponse(BaseModel):
    conflicts: List[ConflictResult]
    missing_prereqs: List[str]
    missing_coreqs: List[str]
    capacity_issues: List[int]
    warnings: List[str]

class FeedbackSubmitRequest(BaseModel):
    student_id: int
    course_id: int
    term_id: str
    workload: int
    materials: int
    practical: int
    fairness: int
    support: int
    overall: int
    tags: List[str]
    comment: Optional[str] = None

class HeatmapResult(BaseModel):
    avg_scores: Dict[str, float]
    tag_counts: Dict[str, int]
    sample_size: int

# --- NL Registration Schemas ---

class SlotRange(BaseModel):
    day: str  # MON, TUE, WED, THU, FRI, SAT, SUN
    start: str  # HH:MM
    end: str    # HH:MM
    reason: Optional[str] = None

class TimeRange(BaseModel):
    start: str # HH:MM
    end: str   # HH:MM

class DesiredCredits(BaseModel):
    min: float
    max: float

class RegistrationPreferences(BaseModel):
    avoid_days: List[str] =Field(default_factory=list)
    avoid_time_ranges: List[TimeRange] = Field(default_factory=list)
    compact_days: Optional[int] = None
    no_evening: Optional[bool] = None
    max_gap_minutes: Optional[int] = None
    prefer_morning: Optional[bool] = None

class CourseWishlist(BaseModel):
    query: str
    course_code: Optional[str] = None
    priority: int = 1

class RegisterConstraints(BaseModel):
    term_id: Optional[str] = None
    desired_credits: Optional[DesiredCredits] = None
    preferences: RegistrationPreferences = Field(default_factory=RegistrationPreferences)
    availability: Dict[str, List[SlotRange]] = Field(default_factory=dict) # e.g. {"blocked_slots": [...]}
    course_wishlist: List[CourseWishlist] = Field(default_factory=list)
    constraints_version: int = 1

class CourseCandidate(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    confidence: float

class ResolvedCourse(BaseModel):
    query: str
    course_id: int
    confidence: float

class AmbiguousCourse(BaseModel):
    query: str
    candidates: List[CourseCandidate]
    reason: str

class CourseResolutionResult(BaseModel):
    resolved: List[ResolvedCourse] = Field(default_factory=list)
    needs_clarification: List[AmbiguousCourse] = Field(default_factory=list)

class NLParseResponse(BaseModel):
    intent: str # BUILD_PLAN, MODIFY_PLAN, CHECK_SELECTION, EXPORT_ICS, ASK_POLICY, ADVICE
    constraints: RegisterConstraints
    course_resolution: CourseResolutionResult
    next_action: str
    next_action_params: Optional[Dict[str, Any]] = None
    raw_query: Optional[str] = None

class NLParseRequest(BaseModel):
    student_id: str
    text: str
    context: Optional[Dict[str, Any]] = None

class NLExecuteRequest(BaseModel):
    student_id: str
    parsed: NLParseResponse
    clarification_answers: Optional[Dict[str, int]] = None # query -> selected_course_id

class NLExecuteResponse(BaseModel):
    plans: List[GeneratedPlan] = Field(default_factory=list)
    checks: Optional[CheckerResponse] = None
    backups: Optional[Dict[str, Any]] = None
    selected_plan_id: Optional[str] = None
    ics_export_url: Optional[str] = None
    advice: Optional[str] = None
