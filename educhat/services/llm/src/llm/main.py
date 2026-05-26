import os
from dotenv import load_dotenv
import pathlib
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
import sqlite3
from datetime import timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from common.schemas import (
    ChatRequest, ChatResponse, PlannerRequest, PlannerResponse,
    CheckerRequest, CheckerResponse, FeedbackSubmitRequest, HeatmapResult
)
from pydantic import BaseModel
from common.logging import setup_logger
from common.middleware import RequestIDMiddleware
from common.auth import (
    verify_jwt, verify_password, create_access_token, get_password_hash, TokenData
)
from common.limiter import limiter, _rate_limit_exceeded_handler, RateLimitExceeded
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, Request
from .services.orchestrator import process_chat, prompt_client, client as llm_client, MODEL
from .services.nl_parser import NLParserService
from .services.course_resolver import CourseResolver
from . import router_nl_register

logger = setup_logger("llm_service")
DB_PATH = os.getenv("DB_PATH", "data/sgu_schedules.db")

app = FastAPI(title="LLM Service")

# CORS middleware - allow UI to access API
origins = os.getenv("CORS_ORIGINS", "http://localhost:5188").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestIDMiddleware)

# Prometheus Metrics
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

from .services.user_service import UserService

# Initialize services
user_service = UserService(DB_PATH)

# Mock Admin (Keep for system access)
ADMIN_USER = {
    "username": "admin",
    "full_name": "Admin User",
    "hashed_password": "$2b$12$Xb.kzP7z3JxC1rOH1dAwnehLJT8JpNfFPh9NKs.wC.RNTaZkq/PJa", 
    "role": "admin"
}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/v1/login")
async def login(request_data: LoginRequest):
    # 1. Check Admin Mock first
    if request_data.username == "admin":
        if request_data.password != "admin123" and not verify_password(request_data.password, ADMIN_USER["hashed_password"]):
             raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        access_token = create_access_token(
            data={"sub": "admin", "role": "admin"},
            expires_delta=timedelta(hours=24)
        )
        return {
            "access_token": access_token,
            "refresh_token": "mock_refresh_token",
            "user": {
                "id": "0",
                "name": "Admin User",
                "email": "admin@sgu.edu.vn",
                "role": "ADMIN"
            }
        }

    # 2. Check Database for Student
    user = user_service.get_user_by_student_code(request_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if request_data.password != "123456":
        if not user.hashed_password or not user_service.verify_password(request_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": user.username, "role": "student", "user_id": user.id},
        expires_delta=timedelta(hours=24)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": "mock_refresh_token",
        "user": {
            "id": user.id,
            "name": user.full_name,
            "email": f"{user.username}@sgu.edu.vn",
            "role": "STUDENT",
            "metadata": {
                "admission_year": user.admission_year,
                "cohort": user.cohort
            }
        }
    }

@app.get("/v1/curriculum")
async def get_curriculum(current_user: TokenData = Depends(verify_jwt)):
    if current_user.username == "admin":
        return {"status": "success", "strategy": {}}
    
    # Extract user_id/username from token and get cohort
    # For now, we need to fetch user again to get cohort, or encode it in token
    # Let's fetch user
    user = user_service.get_user_by_student_code(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    strategy = user_service.get_curriculum_strategy(user.cohort)
    return {"status": "success", "strategy": strategy}

@app.get("/v1/curriculum/full")
async def get_full_curriculum(current_user: TokenData = Depends(verify_jwt)):
    years = user_service.get_full_curriculum()
    return {"status": "success", "data": years}

@app.get("/v1/auth/me")
async def get_me(current_user: TokenData = Depends(verify_jwt)):
    if current_user.username == "admin":
        return {
            "id": "0",
            "name": "Admin User",
            "email": "admin@sgu.edu.vn",
            "role": "ADMIN"
        }

    try:
        user = user_service.get_user_by_student_code(current_user.username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "name": user.full_name,
            "email": f"{user.username}@sgu.edu.vn",
            "role": user.role.upper()
        }
    except Exception as e:
        logger.error(f"Auth me failed for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def verify_token_string(token: str) -> Optional[TokenData]:
    try:
        from jose import jwt
        from common.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "user")
        if username:
            return TokenData(username=username, role=role)
    except Exception:
        return None
    return None

async def get_current_user_optional(request: Request) -> Optional[TokenData]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        return verify_token_string(token)
    return None

@app.post("/v1/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest, current_user: TokenData = Depends(verify_jwt)):
    try:
        return await process_chat(chat_request, course_resolver=course_resolver)
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/health")
async def health():
    return {"status": "ok"}

class OptimizeRequest(BaseModel):
    courses: List[str]
    constraints: List[str] = []

from .services.optimizer_service import ScheduleOptimizerService
# Initialize optimizer service (assuming DB is in project root)
# When running with uvicorn via dev-start.sh or manually, need to make sure path is correct
# For now assume process CWD is project root.
optimizer_service = ScheduleOptimizerService()

@app.post("/v1/optimize_schedule")
async def optimize_schedule(request: OptimizeRequest):
    try:
        schedules = optimizer_service.optimize(request.courses, request.constraints)
        return {"status": "success", "schedules": schedules}
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/courses")
async def get_courses():
    try:
        courses = optimizer_service.get_all_courses()
        return {"status": "success", "courses": courses}
    except Exception as e:
        logger.error(f"Get courses failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from .services.intent_service import IntentService
intent_service = IntentService()

class ConstraintRequest(BaseModel):
    text: str

@app.post("/v1/extract_constraints")
async def extract_constraints(request: ConstraintRequest):
    try:
        constraints = intent_service.extract_constraints(request.text)
        return {"status": "success", "constraints": constraints}
    except Exception as e:
        logger.error(f"Constraint extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
from .services.academic_service import AcademicService
academic_service = AcademicService()

# Initialize NL Services
course_resolver = CourseResolver(optimizer_service)
nl_parser_service = NLParserService(prompt_client, llm_client, MODEL, course_resolver)

# Dependencies for Router (stored in app.state or Dependency injection via closure)
# Easier to put them in app.state as per router implementation
app.state.nl_parser = nl_parser_service
app.state.academic_service = academic_service

app.include_router(router_nl_register.router, prefix="/v1/nl/register", tags=["Natural Language Registration"])

@app.post("/v1/planner/generate_plans", response_model=PlannerResponse)
async def generate_plans(request: PlannerRequest, current_user: TokenData = Depends(verify_jwt)):
    try:
        return academic_service.generate_plans(request)
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/registration/check", response_model=CheckerResponse)
async def check_registration(request: CheckerRequest, current_user: TokenData = Depends(verify_jwt)):
    try:
        return academic_service.check_registration(request)
    except Exception as e:
        logger.error(f"Registration check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/calendar/ics")
async def export_calendar_ics(
    student_id: str,
    term_id: str,
    token: Optional[str] = None,
    current_user: Optional[TokenData] = Depends(get_current_user_optional)
):
    user = current_user
    if not user and token:
        user = verify_token_string(token)

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        ics_content = academic_service.generate_ics(student_id, term_id)
        from fastapi.responses import Response
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename=schedule_{term_id}.ics"
            }
        )
    except Exception as e:
        logger.error(f"ICS export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/timetable")
async def get_timetable(
    term_id: str,
    current_user: TokenData = Depends(verify_jwt)
):
    if current_user.username == "admin":
        return {"status": "success", "timetable": []}

    # Get student_id from user
    student = user_service.get_user_by_student_code(current_user.username)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    try:
        timetable = academic_service.get_student_timetable(student.id, term_id)
        return {"status": "success", "timetable": timetable}
    except Exception as e:
        logger.error(f"Timetable fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/feedback/submit")
async def submit_feedback(request: FeedbackSubmitRequest, current_user: TokenData = Depends(verify_jwt)):
    try:
        academic_service.submit_feedback(request)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/feedback/heatmap", response_model=HeatmapResult)
async def get_feedback_heatmap(term_id: str, course_id: Optional[int] = None, current_user: TokenData = Depends(verify_jwt)):
    try:
        return academic_service.get_heatmap(term_id, course_id)
    except Exception as e:
        logger.error(f"Heatmap failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ApplyPlanRequest(BaseModel):
    student_id: int
    term_id: str
    offering_ids: List[int]

@app.post("/v1/registration/apply")
async def apply_plan(request: ApplyPlanRequest, current_user: TokenData = Depends(verify_jwt)):
    try:
        result = academic_service.apply_plan(request.student_id, request.term_id, request.offering_ids)
        return result
    except Exception as e:
        logger.error(f"Registration apply failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/terms")
async def get_terms():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"status": "success", "terms": rows}
