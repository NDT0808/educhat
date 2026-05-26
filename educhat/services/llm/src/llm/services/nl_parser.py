import json
import re
from typing import Dict, Any, Optional
from common.schemas import (
    NLParseRequest, NLParseResponse, RegisterConstraints, 
    RegistrationPreferences, DesiredCredits, TimeRange, SlotRange,
    CourseWishlist
)
from common.logging import setup_logger
from .course_resolver import CourseResolver

logger = setup_logger("nl_parser")

class NLParserService:
    def __init__(self, prompt_client, llm_client, model: str, course_resolver: CourseResolver):
        self.prompt_client = prompt_client
        self.llm_client = llm_client
        self.model = model
        self.course_resolver = course_resolver

    async def parse_request(self, request: NLParseRequest) -> NLParseResponse:
        # 1. Calls LLM to extract JSON
        try:
            parsed_dict = await self._call_llm(request.text, request.context)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to simple intent if LLM fails completely
            return self._create_fallback_response(request.text)

        # 2. Validate & Sanitize using Pydantic
        try:
            constraints = RegisterConstraints(**parsed_dict.get("constraints", {}))
            intent = parsed_dict.get("intent", "BUILD_PLAN")
        except Exception as e:
             logger.error(f"Pydantic validation failed: {e}")
             # Attempt to salvage basics
             constraints = RegisterConstraints()
             intent = "BUILD_PLAN"

        # 3. Handle advisor_only mode
        if request.context and request.context.get("mode") == "advisor_only":
            intent = "ADVICE"

        # 4. Post-process constraints (normalization)
        self._normalize_constraints(constraints)

        # 4. Resolve courses
        wishlist_queries = [c.query for c in constraints.course_wishlist]
        resolution_result = self.course_resolver.resolve(wishlist_queries)

        # 5. Determine Next Action
        next_action = self._determine_next_action(intent, resolution_result)

        return NLParseResponse(
            intent=intent,
            constraints=constraints,
            course_resolution=resolution_result,
            next_action=next_action,
            next_action_params=parsed_dict.get("next_action_params"),
            raw_query=request.text
        )

    async def _call_llm(self, text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = await self.prompt_client.render("nl_register_parse", {
            "text": text,
            "context": context or {}
        })
        
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)

    def _normalize_constraints(self, constraints: RegisterConstraints):
        # Normalize days to uppercase MON..SUN
        day_map = {
            "T2": "MON", "THU 2": "MON", "THU HAI": "MON", "MONDAY": "MON", "THỨ 2": "MON", "THỨ HAI": "MON",
            "T3": "TUE", "THU 3": "TUE", "THU BA": "TUE", "TUESDAY": "TUE", "THỨ 3": "TUE", "THỨ BA": "TUE",
            "T4": "WED", "THU 4": "WED", "THU TU": "WED", "WEDNESDAY": "WED", "THỨ 4": "WED", "THỨ TƯ": "WED",
            "T5": "THU", "THU 5": "THU", "THU NAM": "THU", "THURSDAY": "THU", "THỨ 5": "THU", "THỨ NĂM": "THU",
            "T6": "FRI", "THU 6": "FRI", "THU SAU": "FRI", "FRIDAY": "FRI", "THỨ 6": "FRI", "THỨ SÁU": "FRI",
            "T7": "SAT", "THU 7": "SAT", "THU BAY": "SAT", "SATURDAY": "SAT", "THỨ 7": "SAT", "THỨ BẢY": "SAT",
            "CN": "SUN", "CHU NHAT": "SUN", "SUNDAY": "SUN", "CHỦ NHẬT": "SUN"
        }
        
        # Avoid Days - handle merged string like "Thứ 2, 4, 6"
        normalized_avoid = []
        raw_avoid_str = " ".join(constraints.preferences.avoid_days).upper()
        
        if "2" in raw_avoid_str or "HAI" in raw_avoid_str or "MON" in raw_avoid_str: normalized_avoid.append("MON")
        if "3" in raw_avoid_str or "BA" in raw_avoid_str or "TUE" in raw_avoid_str: normalized_avoid.append("TUE")
        if "4" in raw_avoid_str or "TƯ" in raw_avoid_str or "TU" in raw_avoid_str or "WED" in raw_avoid_str: normalized_avoid.append("WED")
        if "5" in raw_avoid_str or "NĂM" in raw_avoid_str or "NAM" in raw_avoid_str or "THU" in raw_avoid_str: normalized_avoid.append("THU")
        if "6" in raw_avoid_str or "SÁU" in raw_avoid_str or "SAU" in raw_avoid_str or "FRI" in raw_avoid_str: normalized_avoid.append("FRI")
        if "7" in raw_avoid_str or "BẢY" in raw_avoid_str or "BAY" in raw_avoid_str or "SAT" in raw_avoid_str: normalized_avoid.append("SAT")
        if "CN" in raw_avoid_str or "NHẬT" in raw_avoid_str or "NHAT" in raw_avoid_str or "SUN" in raw_avoid_str: normalized_avoid.append("SUN")
        
        constraints.preferences.avoid_days = list(set(normalized_avoid))

        # Blocked Slots
        # Iterate over all availability keys if they exist, commonly "blocked_slots"
        if "blocked_slots" in constraints.availability:
             for slot in constraints.availability["blocked_slots"]:
                 clean_d = slot.day.upper().strip()
                 if clean_d in day_map:
                     slot.day = day_map[clean_d]

    def _determine_next_action(self, intent: str, resolution: Any) -> str:
        if resolution.needs_clarification:
            return "ask_clarification"
        
        if intent == "BUILD_PLAN":
            return "generate_plans"
        elif intent == "MODIFY_PLAN":
            return "generate_plans" # Re-generate with new constraints
        elif intent == "CHECK_SELECTION":
            return "check_selection"
        elif intent == "EXPORT_ICS":
            return "export_ics"
        elif intent == "ADVICE":
            return "provide_advice"
        
        return "generate_plans" # Default

    def _create_fallback_response(self, text: str) -> NLParseResponse:
        # Minimal regex extraction for credits or days could go here
        return NLParseResponse(
            intent="BUILD_PLAN",
            constraints=RegisterConstraints(),
            course_resolution=self.course_resolver.resolve([]),
            next_action="generate_plans"
        )
