import os
import asyncio
from typing import List, Optional
from loguru import logger
from openai import AsyncOpenAI

# Import chuẩn từ EduChat
from common.schemas import ChatRequest, ChatResponse, Message, RetrievalResult
from ..clients.internal import PromptClient, RagClient
from common.logging import setup_logger
from .optimizer_service import ScheduleOptimizerService
from .emotion_service import EmotionService

# Initialize logger
logger = setup_logger("llm_orchestrator")

# Initialize LLM client
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or "dummy",
    base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
)

# Shared Service instances
emotion_service = EmotionService()
rag_client = RagClient()
prompt_client = PromptClient()
optimizer_service = ScheduleOptimizerService()

MODEL = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gemini-2.5-flash"

# Load reranker if not disabled
reranker = None
try:
    if os.getenv("SKIP_RERANKER") == "true":
        raise RuntimeError("SKIP_RERANKER is enabled")

    from sentence_transformers import CrossEncoder
    logger.info("Loading CrossEncoder model on CPU...")
    reranker = CrossEncoder("thanhtantran/Vietnamese_Reranker", device="cpu")
    logger.info("CrossEncoder model loaded on CPU.")
except Exception as e:
    logger.warning(f"CrossEncoder unavailable; continuing without reranking: {e}")

def analyze_emotion(text: str) -> str:
    """Delegating to PhoBERT EmotionService"""
    return emotion_service.analyze(text)

async def process_chat(request: ChatRequest, course_resolver=None) -> ChatResponse:
    user_query_original = request.messages[-1].content
    user_query = user_query_original.lower()

    # 1. PHÂN TÍCH CẢM XÚC VỚI PHOBERT
    user_emotion = analyze_emotion(user_query_original)
    logger.info(f"Emotion detected by PhoBERT: {user_emotion}")

    # Safety: Prompt Injection Check
    from .safety import detect_prompt_injection, verify_grounding
    if detect_prompt_injection(user_query):
        return ChatResponse(
            answer="Hệ thống từ chối xử lý yêu cầu này vì phát hiện nội dung không an toàn.",
            citations=[]
        )

    # 2. Check for Schedule Optimization Intent
    schedule_keywords = ["lịch học", "thời khóa biểu", "xếp lịch", "đăng ký môn", "chọn môn", "tín chỉ"]
    if any(k in user_query for k in schedule_keywords):
        logger.info(f"Detected schedule intent: {user_query}")
        
        from openai import OpenAI
        sync_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or "dummy",
            base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        )
        
        intent = await optimizer_service.extract_query_intent(
            user_query, prompt_client, sync_client, MODEL
        )
        
        extracted_courses = intent.get("courses", [])
        courses_to_optimize = []
        
        if extracted_courses and course_resolver:
            courses_to_optimize = course_resolver.resolve_to_codes(extracted_courses)
            
        if not courses_to_optimize and intent.get("year"):
             courses_to_optimize = optimizer_service.get_courses_by_year(int(intent["year"]))
             
        if not courses_to_optimize:
            return ChatResponse(
                answer="Tôi chưa xác định được bạn muốn xếp lịch cho môn nào hay năm học nào.",
                citations=[],
                emotion=user_emotion
            )
            
        schedules = optimizer_service.optimize(
            courses_to_optimize, 
            intent.get("constraints", []),
            min_credits=intent.get("min_credits", 0),
            max_credits=intent.get("max_credits", 30)
        )
        
        if not schedules:
            return ChatResponse(
                answer="Rất tiếc, không tìm thấy lịch học phù hợp.",
                citations=[],
                emotion=user_emotion
            )
            
        best_schedule = schedules[0]
        response_text = f"Dựa trên yêu cầu của bạn, đây là lịch học đề xuất:\n\n"
        response_text += "| Môn học | Lớp | Thứ | Tiết | Phòng |\n|---|---|---|---|---|\n"
        for item in best_schedule:
            response_text += f"| {item['name']} | {item['class_code']} | {item['day_of_week']} | {item['start_period']}-{item['end_period']} | {item['room']} |\n"
            
        return ChatResponse(answer=response_text, citations=[], emotion=user_emotion)

    # 3. Retrieve Context
    logger.info(f"Retrieving context for: {user_query_original}")
    retrieval_results = await rag_client.retrieve(user_query_original, top_k=10)
    
    if retrieval_results and reranker is not None:
        documents = [r.get("content", "")[:2000] for r in retrieval_results]
        pairs = [[user_query_original, doc] for doc in documents]
        loop = asyncio.get_running_loop()
        scores = await loop.run_in_executor(None, reranker.predict, pairs)
        ranked_results = []
        for r, score in zip(retrieval_results, scores):
            r["score"] = float(score)
            ranked_results.append(r)
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        retrieval_results = ranked_results[:3]
    elif retrieval_results:
        retrieval_results = retrieval_results[:3]
    
    context_parts = []
    for r in retrieval_results:
        content = r.get("content", "")
        if len(content) > 4000:
            content = content[:4000] + "..."
        context_parts.append(content)
    context_text = "\n\n".join(context_parts)
    
    # 4. Render Prompt with EMOTION
    logger.info(f"Rendering system prompt with emotion: {user_emotion}")
    system_prompt = await prompt_client.render("chat_default", {
        "context": context_text,
        "question": user_query_original,
        "emotion": user_emotion
    })
    
    # 5. Call LLM
    logger.info(f"Calling LLM {MODEL}")
    history = request.messages[:-1]
    api_messages = [{"role": msg.role, "content": msg.content} for msg in history]
    api_messages.append({"role": "user", "content": system_prompt})
    
    response = await client.chat.completions.create(
        model=MODEL,
        messages=api_messages,
        temperature=0.7
    )
    
    answer = response.choices[0].message.content
    
    # Safety: Grounding Check
    is_grounded = await verify_grounding(client, MODEL, answer, context_text)
    if not is_grounded:
        answer += "\n\n(Lưu ý: Câu trả lời này có thể chứa thông tin không được tìm thấy trong tài liệu tham khảo.)"

    return ChatResponse(
        answer=answer,
        citations=[],
        emotion=user_emotion
    )
