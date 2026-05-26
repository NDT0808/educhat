from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from services.advisor.advisor_service import get_advice

app = FastAPI(title="Medical Course Advisor API", version="1.0")

class StudentQuery(BaseModel):
    user_prompt: str
    student_id: int

class AdviceResponse(BaseModel):
    success: bool
    advice: Optional[str] = None
    sql_executed: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

@app.post("/api/v1/advising/query", response_model=AdviceResponse)
async def query_advisor(query: StudentQuery):
    """
    Endpoint to get course registration advice based on student prompt.
    """
    try:
        result = get_advice(query.user_prompt, query.student_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
