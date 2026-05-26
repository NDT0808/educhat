from fastapi import APIRouter, Depends, HTTPException, Request
from common.schemas import (
    NLParseRequest, NLParseResponse, NLExecuteRequest, NLExecuteResponse,
    PlannerRequest, PlannerPreferences
)
from common.auth import verify_jwt, TokenData
from common.logging import setup_logger
from .services.nl_parser import NLParserService
from .services.academic_service import AcademicService
import sys
import os
# Add project root to path to import advisor service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from services.advisor.advisor_service import get_advice

logger = setup_logger("router_nl_register")
router = APIRouter()

def get_nl_parser(request: Request) -> NLParserService:
    return request.app.state.nl_parser

def get_academic_service(request: Request) -> AcademicService:
    return request.app.state.academic_service

@router.post("/parse", response_model=NLParseResponse)
async def parse_intent(
    request: NLParseRequest,
    current_user: TokenData = Depends(verify_jwt),
    parser: NLParserService = Depends(get_nl_parser)
):
    try:
        return await parser.parse_request(request)
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=NLExecuteResponse)
async def execute_plan(
    request: NLExecuteRequest,
    current_user: TokenData = Depends(verify_jwt),
    academic_service: AcademicService = Depends(get_academic_service)
):
    try:
        response = NLExecuteResponse()
        
        
        # Map resolved courses to desired_course_ids
        desired_ids = []
        if request.parsed.course_resolution and request.parsed.course_resolution.resolved:
            for r in request.parsed.course_resolution.resolved:
                desired_ids.append(r.course_id)
        
        # Handle clarification answers
        if request.clarification_answers:
            for _, cid in request.clarification_answers.items():
                if cid not in desired_ids:
                    desired_ids.append(cid)

        # Define constraints
        constraints = request.parsed.constraints

        # Build Planner Request
        # Map TimeRange to standard ISO or whatever Planner expects (PlannerPreferences expects Strings? List[str])
        # PlannerPreferences: avoid_time_ranges: List[str] e.g. ["18:00-22:00"]
        avoid_times = []
        for tr in constraints.preferences.avoid_time_ranges:
            avoid_times.append(f"{tr.start}-{tr.end}")

        # Determine strict mode
        is_full_plan = True
        if request.parsed.next_action_params:
            is_full_plan = request.parsed.next_action_params.get("full_plan_requested", True)
        
        strict_mode = not is_full_plan

        planner_req = PlannerRequest(
            student_id=int(request.student_id), # Ensure int
            term_id=constraints.term_id or "2024.1", # Default term 2024.1 if missing
            min_credits=constraints.desired_credits.min if constraints.desired_credits else (15 if is_full_plan else 0),
            max_credits=constraints.desired_credits.max if constraints.desired_credits else 25,
            preferences=PlannerPreferences(
                avoid_days=constraints.preferences.avoid_days,
                avoid_time_ranges=avoid_times,
                compact_days=True if constraints.preferences.compact_days else False, # Simplified mapping
                no_evening=constraints.preferences.no_evening or False,
                max_gap_minutes=constraints.preferences.max_gap_minutes or 120,
                prefer_morning=constraints.preferences.prefer_morning or False
            ),
            desired_course_ids=desired_ids,
            strict_mode=strict_mode
        )
        
        # Execute Action
        # If intent is BUILD/MODIFY/REGISTER -> generate plans
        if request.parsed.intent in ["BUILD_PLAN", "MODIFY_PLAN", "REGISTER"]:
             planner_response = academic_service.generate_plans(planner_req)
             response.plans = planner_response.plans
             
        elif request.parsed.intent == "EXPORT_ICS":
             # Provide download URL -> logic handled by frontend usually, or return URL here
             # We return a link that frontend calls: /v1/calendar/ics?student_id=...
             response.ics_export_url = f"/v1/calendar/ics?student_id={request.student_id}&term_id={planner_req.term_id}"

        elif request.parsed.intent == "ADVICE":
            # Call our Text-to-SQL Advisor logic
            query_text = request.parsed.raw_query or "Tư vấn chọn môn học"
            
            advice_result = get_advice(query_text, int(request.student_id))
            if isinstance(advice_result, dict):
                 response.advice = advice_result.get("advice", "No advice generated.")
            else:
                 response.advice = str(advice_result)

        # Suggestions / Checks could be added here
        
        return response
        
    except Exception as e:
        logger.error(f"Execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
