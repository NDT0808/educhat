from fastapi import FastAPI, HTTPException
from jinja2 import Environment, DictLoader 
from common.schemas import RenderRequest
from common.logging import setup_logger
from common.middleware import RequestIDMiddleware
from common.auth import verify_internal_token
from fastapi import Depends

logger = setup_logger("prompt_service")

app = FastAPI(title="Prompt Service")
app.add_middleware(RequestIDMiddleware)

# Prometheus Metrics
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# In-memory prompt registry for simplicity
PROMPTS = {
    "chat_default": "Bạn là trợ lý ảo AI hữu ích hỗ trợ tư vấn tuyển sinh. Hãy trả lời câu hỏi của người dùng HOÀN TOÀN bằng tiếng Việt.\n\nTrạng thái cảm xúc của người dùng: {{ emotion }}\n\nLƯU Ý QUAN TRỌNG: Nếu người dùng đang có cảm xúc tiêu cực (Áp lực nhẹ, Áp lực cao), bạn PHẢI bắt đầu câu trả lời bằng sự an ủi, thấu hiểu và động viên một cách chân thành. Sau đó mới cung cấp thông tin tư vấn.\n\nThông tin tham khảo:\n{{ context }}\n\nCâu hỏi: {{ question }}\n\nCâu trả lời:",
    "summarize": "Summarize the following text:\n\n{{ text }}",
    "schedule_extraction": """
    Bạn là một chuyên gia sắp xếp lịch học. Nhiệm vụ của bạn là trích xuất thông tin từ yêu cầu của sinh viên thành định dạng JSON.
    
    Yêu cầu của sinh viên: "{{ query }}"
    
    Hãy trích xuất các thông tin sau:
    1. "year": Năm học của sinh viên (ví dụ: 1, 2, 3, 4, 5, 6). Nếu không rõ, trả về null.
    2. "courses": Danh sách tên các môn học sinh viên muốn đăng ký. Nếu sinh viên nói "tất cả các môn" hoặc không liệt kê cụ thể, hãy trả về danh sách trống [].
    3. "constraints": Danh sách các ràng buộc:
       - "morning_only": Nếu sinh viên muốn học buổi sáng.
       - "afternoon_only": Nếu sinh viên muốn học buổi chiều.
       - "no_monday", "no_tuesday", ...: Nếu sinh viên bận hoặc không muốn học vào thứ đó.
       - "minimize_days": Tiết kiệm ngày lên trường.
    4. "min_credits": Số tín chỉ tối thiểu (mặc định 0 nếu không nêu).
    5. "max_credits": Số tín chỉ tối đa (mặc định 25 nếu không nêu).
    
    Output JSON format only:
    {
      "year": int | null,
      "courses": [string],
      "constraints": [string],
      "min_credits": int,
      "max_credits": int
    }
    """,
    "nl_register_parse": """
    Bạn là trợ lý ảo AI hỗ trợ đăng ký tín chỉ tại Đại học Y Hà Nội.
    Nhiệm vụ: Phân tích yêu cầu tự nhiên của sinh viên để trích xuất ý định (Intent) và các ràng buộc (Constraints) dưới dạng JSON.

    Context Info:
    {{ context | tojson }}

    Student Input: "{{ text }}"

    Yêu cầu trích xuất:
    1. Intent (Mục đích):
       - "BUILD_PLAN": Đăng ký môn, lập kế hoạch mới.
       - "MODIFY_PLAN": Thay đổi, điều chỉnh kế hoạch.
       - "CHECK_SELECTION": Kiểm tra lịch đã chọn.
       - "EXPORT_ICS": Xuất lịch ra file.
    
    2. Constraints (Ràng buộc):
       - "course_wishlist": Danh sách các môn học sinh viên nhắc đến cụ thể.
         Mỗi môn là object: {"query": "tên môn trong câu nói", "priority": 1, "required": true}
       - "preferences":
         - "avoid_days": Các thứ muốn tránh. CHÚ Ý: "tránh thứ 7" -> ["Thứ 7"], "nghỉ thứ 2" -> ["Thứ 2"].
         - "avoid_time_ranges": Khung giờ bận (VD: [{"start": "18:00", "end": "21:00"}]).
         - "no_evening": true nếu tránh học tối.
         - "prefer_morning": true nếu thích sáng.
         - "compact_days": true nếu muốn dồn lịch.
       - "desired_credits": {"min": int, "max": int} nếu có nhắc đến số tín chỉ.
    
    3. Next Action Params:
       - "full_plan_requested": true nếu người dùng muốn lập kế hoạch tổng thể, tối ưu số tín chỉ, hoặc không nói rõ môn nào. 
                                false nếu chỉ muốn liệt kê và đăng ký chính xác những môn được nêu tên.

    Output JSON Format (Strict JSON):
    {
      "intent": "BUILD_PLAN",
      "constraints": {
        "term_id": null,
        "desired_credits": null,
        "preferences": {
          "avoid_days": [],
          "avoid_time_ranges": [],
          "compact_days": null,
          "no_evening": null,
          "prefer_morning": null
        },
        "course_wishlist": [
           {"query": "Tên môn A", "priority": 1},
           {"query": "Tên môn B", "priority": 1}
        ]
      },
      "next_action_params": {
        "full_plan_requested": boolean
      }
    }
    """
}

env = Environment(loader=DictLoader(PROMPTS))

@app.get("/v1/prompts/{name}", dependencies=[Depends(verify_internal_token)])
async def get_prompt(name: str):
    if name not in PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"name": name, "template": PROMPTS[name]}

@app.post("/v1/prompts", dependencies=[Depends(verify_internal_token)])
async def create_prompt(name: str, template: str):
    PROMPTS[name] = template
    # Re-initialize environment to include new template
    global env
    env = Environment(loader=DictLoader(PROMPTS))
    return {"message": "Prompt created", "name": name}

@app.post("/v1/render", dependencies=[Depends(verify_internal_token)])
async def render_prompt(request: RenderRequest):
    try:
        template = env.get_template(request.template_name)
        rendered = template.render(**request.variables)
        return {"rendered_prompt": rendered}
    except Exception as e:
        logger.error(f"Error rendering prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/health")
async def health():
    return {"status": "ok"}
