import os
from typing import Dict, Any, List
from common.schemas import RetrievalResult, ChunkMetadata
from common.resilience import create_async_client, retry_request
from common.auth import INTERNAL_API_KEY, INTERNAL_TOKEN_HEADER_NAME
from common.logging import setup_logger

PROMPT_SERVICE_URL = os.getenv("PROMPT_SERVICE_URL", "http://prompt:8000")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag:8000")
logger = setup_logger("llm_internal_clients")

# Shared client instances for connection pooling
# In a real app, these might be lifecycle-managed, but global is fine for now
prompt_http = create_async_client()
rag_http = create_async_client()

class PromptClient:
    @retry_request
    async def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        try:
            resp = await prompt_http.post(
                f"{PROMPT_SERVICE_URL}/v1/render", 
                json={
                    "template_name": template_name,
                    "variables": variables
                },
                headers={INTERNAL_TOKEN_HEADER_NAME: INTERNAL_API_KEY}
            )
            resp.raise_for_status()
            return resp.json()["rendered_prompt"]
        except Exception as e:
            logger.warning(f"Prompt service unavailable at {PROMPT_SERVICE_URL}: {e}")
            context = variables.get("context", "")
            question = variables.get("question", "")
            if context:
                return (
                    "Bạn là trợ lý tư vấn học vụ. Hãy chỉ trả lời dựa trên ngữ cảnh được cung cấp.\n\n"
                    f"Ngữ cảnh:\n{context}\n\n"
                    f"Câu hỏi:\n{question}"
                )
            return (
                "Bạn là trợ lý tư vấn học vụ. Nếu không có tài liệu tham chiếu, "
                "hãy trả lời ngắn gọn và nêu rõ khi thông tin cần được kiểm chứng.\n\n"
                f"Câu hỏi:\n{question}"
            )

class RagClient:
    @retry_request
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve results from RAG service.
        Returns List[Dict] with keys: content, metadata, score
        """
        try:
            resp = await rag_http.get(
                f"{RAG_SERVICE_URL}/v1/retrieve", 
                params={"query": query, "top_k": top_k},
                headers={INTERNAL_TOKEN_HEADER_NAME: INTERNAL_API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()
            # Return raw dict structure without Pydantic validation
            return data
        except Exception as e:
            logger.warning(f"RAG service unavailable at {RAG_SERVICE_URL}: {e}")
            return []
