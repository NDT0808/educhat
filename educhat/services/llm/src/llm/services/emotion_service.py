import os

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from loguru import logger

class EmotionService:
    def __init__(self, model_name_or_path: str = None):
        # Danh sách các đường dẫn tiềm năng (cả trên Windows và trong Docker)
        possible_paths = [
            r"c:\Users\ASUS\Downloads\educhat\educhat\services\llm\models\emotion_v2", # Windows
            "/app/services/llm/models/emotion_v2",                                    # Docker
            "./services/llm/models/emotion_v2"                                         # Relative
        ]
        
        self.model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.model_path = path
                logger.success(f"Đã tìm thấy mô hình huấn luyện nội bộ tại: {path}")
                break
        
        if not self.model_path:
            self.model_path = model_name_or_path or "thnhan3/phobert-vietnamese-students-feedback"
            logger.warning(f"Không tìm thấy mô hình nội bộ. Sử dụng mô hình dự phòng: {self.model_path}")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            
            self.label_map = {
                0: "Tich cuc",
                1: "Trung tinh",
                2: "Ap luc nhe",
                3: "Ap luc cao"
            }
        except Exception as e:
            logger.error(f"Lỗi khi nạp mô hình PhoBERT: {e}")
            self.model = None

    def analyze(self, text: str) -> str:
        if not self.model:
            return self._fallback_analyze(text)
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=64).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                label_idx = torch.argmax(probs, dim=-1).item()
            
            return self.label_map.get(label_idx, "Trung tính")
        except Exception as e:
            logger.warning(f"Phân tích thất bại: {e}")
            return self._fallback_analyze(text)

    def _fallback_analyze(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["mệt", "áp lực", "stress", "kiệt sức", "bế tắc"]):
            return "Ap luc cao"
        if any(k in text_lower for k in ["lo", "sợ", "băn khoăn"]):
            return "Ap luc nhe"
        if any(k in text_lower for k in ["tốt", "hay", "vui", "cảm ơn"]):
            return "Tich cuc"
        return "Trung tinh"
