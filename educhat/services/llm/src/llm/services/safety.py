import re
import logging
from typing import List

logger = logging.getLogger("safety_service")

# Basic patterns for prompt injection
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all instructions",
    r"system override",
    r"delete system prompt",
    r"you are not",
    r"forget everything",
    r"stop being",
    # Vietnamese patterns
    r"bỏ qua hướng dẫn",
    r"quên hết",
    r"xóa prompt",
    r"lờ đi hướng dẫn",
    r"xem như chưa có gì",
]

def detect_prompt_injection(query: str) -> bool:
    """
    Checks if the query contains common prompt injection patterns.
    Returns True if an injection attempt is detected.
    """
    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            logger.warning(f"Prompt injection detected: {pattern} in '{query}'")
            return True
    return False

async def verify_grounding(client, model: str, answer: str, context: str) -> bool:
    """
    Verifies if the answer is grounded in the provided context using an LLM call.
    Returns True if grounded (or if answer is a refusal), False otherwise.
    """
    # If answer is a refusal, it's considered safe/grounded
    refusals = ["tôi không có thông tin", "không tìm thấy", "i don't have information", "tôi chưa xác định được"]
    if any(r in answer.lower() for r in refusals):
        return True

    # If context is empty but answer provides info, likely hallucination
    if not context.strip() and len(answer) > 50:
        logger.warning("Grounding check failed: Answer provided despite empty context.")
        return False
        
    prompt = f"""
    You are a Fact Checker.
    
    Context:
    {context[:1000]}... (truncated)
    
    Answer:
    {answer}
    
    Does the Context support the Answer? 
    If the answer adds outside knowledge not in context, reply NO.
    If the answer is supported by context, reply YES.
    
    Reply only YES or NO.
    """
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        result = response.choices[0].message.content.strip().upper()
        logger.info(f"Grounding Check Result: {result}")
        return "YES" in result
    except Exception as e:
        logger.error(f"Grounding check error: {e}")
        # Fail open to avoid breaking user experience on check failure, but log it
        return True
