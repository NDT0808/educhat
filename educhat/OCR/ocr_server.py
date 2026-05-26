from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import easyocr
import uvicorn

app = FastAPI(title="OCR Microservice")

# Cho phép Frontend React gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models
reader = None
processor = None
model = None
device = None

@app.on_event("startup")
async def load_models():
    global reader, processor, model, device
    print("🚀 Đang khởi động OCR Microservice (Port 8002)...")
    try:
        # 1. Load Detection Model
        print("-> Đang tải EasyOCR...")
        reader = easyocr.Reader(['vi', 'en'], gpu=torch.cuda.is_available())

        # 2. Load Recognition Model
        print("-> Đang tải TrOCR (Model nặng, vui lòng đợi)...")
        MODEL_NAME = "microsoft/trocr-base-printed"
        processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
        model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        print(f"✅ OCR Microservice đã sẵn sàng trên {device}!")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động OCR: {e}")
        import sys
        sys.exit(1)

def recognize_text(cropped_image_pil):
    pixel_values = processor(cropped_image_pil, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

@app.post("/v1/ocr/scan")
async def scan_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên phải là hình ảnh")
        
    try:
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_cv is None:
            raise ValueError("Không thể đọc định dạng ảnh này.")
            
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        
        # Detection
        results = reader.readtext(img_rgb)
        
        extracted_data = []
        
        # Recognition
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
            recognized_text = recognize_text(cropped_pil)
            
            extracted_data.append({
                "text": recognized_text,
                "box": {
                    "x": tl[0], "y": tl[1],
                    "width": br[0] - tl[0], "height": br[1] - tl[1]
                }
            })
            
        return {
            "status": "success",
            "data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("ocr_server:app", host="0.0.0.0", port=8002, reload=False)
