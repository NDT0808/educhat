import cv2
import numpy as np
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import easyocr
import io

class OCRService:
    def __init__(self):
        print("Đang khởi tạo OCR Service...")
        # 1. Load Detection Model (CRAFT)
        self.reader = easyocr.Reader(['vi', 'en'], gpu=torch.cuda.is_available())
        
        # 2. Load Recognition Model (TrOCR)
        MODEL_NAME = "microsoft/trocr-base-printed"
        self.processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        self.model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        print("OCR Service đã sẵn sàng!")

    def _recognize_text(self, cropped_image_pil):
        pixel_values = self.processor(cropped_image_pil, return_tensors="pt").pixel_values.to(self.device)
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return text

    async def scan_image(self, image_bytes: bytes) -> list:
        # Chuyển đổi bytes thành numpy array cho OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_cv is None:
            raise ValueError("Không thể đọc định dạng ảnh này.")
            
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        
        # 1. Detection
        results = self.reader.readtext(img_rgb)
        
        extracted_data = []
        
        # 2. Recognition
        for bbox, _easyocr_text, conf in results:
            (tl, tr, br, bl) = bbox
            tl = (int(tl[0]), int(tl[1]))
            br = (int(br[0]), int(br[1]))
            
            y_min, y_max = max(0, tl[1]), min(img_rgb.shape[0], br[1])
            x_min, x_max = max(0, tl[0]), min(img_rgb.shape[1], br[0])
            
            cropped_img_cv = img_rgb[y_min:y_max, x_min:x_max]
            
            if cropped_img_cv.size == 0:
                continue
                
            cropped_pil = Image.fromarray(cropped_img_cv)
            recognized_text = self._recognize_text(cropped_pil)
            
            extracted_data.append({
                "text": recognized_text,
                "box": {
                    "x": tl[0],
                    "y": tl[1],
                    "width": br[0] - tl[0],
                    "height": br[1] - tl[1]
                }
            })
            
        return extracted_data
