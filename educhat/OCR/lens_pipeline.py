import cv2
import numpy as np
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import easyocr
import matplotlib.pyplot as plt

# ==========================================
# GIAI ĐOẠN 1: TEXT DETECTION (Dùng CRAFT qua thư viện EasyOCR)
# ==========================================
print("Đang tải mô hình Detection (CRAFT)...")
# Khởi tạo EasyOCR chỉ dùng cho Detection (bỏ qua Recognition của nó)
reader = easyocr.Reader(['vi', 'en'], gpu=torch.cuda.is_available())

# ==========================================
# GIAI ĐOẠN 2: TEXT RECOGNITION (TrOCR do bạn tự Train)
# ==========================================
print("Đang tải mô hình Recognition (TrOCR)...")
# Trong thực tế báo cáo NCKH, bạn sẽ trỏ đường dẫn này tới thư mục './my-final-trocr' chứa model bạn đã tự train.
# Ở đây ta dùng tạm model pre-trained của Microsoft để test luồng pipeline.
MODEL_NAME = "microsoft/trocr-base-printed"
processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

def recognize_text(cropped_image_pil):
    """Hàm nhận diện chữ từ mảnh ảnh đã cắt (TrOCR)"""
    pixel_values = processor(cropped_image_pil, return_tensors="pt").pixel_values.to(device)
    
    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
        
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return text

def google_lens_pipeline(image_path):
    print(f"--- Đang xử lý ảnh: {image_path} ---")
    # Đọc ảnh gốc bằng OpenCV
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        print("Không tìm thấy ảnh!")
        return
        
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    
    # 1. NHẬN DIỆN VÙNG CHỨA CHỮ (DETECTION)
    # readtext() trả về list gồm: (tọa độ bounding_box, text, độ tự tin)
    # Dù EasyOCR có đọc chữ (text), ta sẽ phớt lờ nó và lấy model TrOCR của chúng ta để tự đọc!
    results = reader.readtext(img_rgb)
    
    results_to_draw = img_cv.copy()
    
    print(f"Phát hiện được {len(results)} vùng chứa chữ.")
    
    # 2. XỬ LÝ TỪNG VÙNG CHỮ VÀ NHẬN DIỆN (RECOGNITION)
    for idx, (bbox, _easyocr_text, conf) in enumerate(results):
        # Lấy tọa độ 4 góc của khung chữ nhật
        (tl, tr, br, bl) = bbox
        tl = (int(tl[0]), int(tl[1]))
        br = (int(br[0]), int(br[1]))
        
        # Crop mảnh ảnh chứa chữ
        # Lưu ý: Cần xử lý cẩn thận tọa độ để không bị vượt quá khung hình
        y_min, y_max = max(0, tl[1]), min(img_rgb.shape[0], br[1])
        x_min, x_max = max(0, tl[0]), min(img_rgb.shape[1], br[0])
        
        cropped_img_cv = img_rgb[y_min:y_max, x_min:x_max]
        
        if cropped_img_cv.size == 0:
            continue
            
        # Chuyển mảnh cắt sang định dạng PIL cho TrOCR
        cropped_pil = Image.fromarray(cropped_img_cv)
        
        # Đưa vào model TrOCR của bạn để đọc chữ
        recognized_text = recognize_text(cropped_pil)
        print(f"[{idx+1}] Tọa độ: {tl}->{br} | Kết quả TrOCR: '{recognized_text}'")
        
        # Vẽ khung đỏ bao quanh chữ lên ảnh gốc
        cv2.rectangle(results_to_draw, tl, br, (0, 0, 255), 2)
        # Ghi chữ xanh lá cây lên trên khung
        cv2.putText(results_to_draw, recognized_text, (tl[0], tl[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # 3. HIỂN THỊ KẾT QUẢ CUỐI CÙNG NHƯ GOOGLE LENS
    # (Nếu chạy trên server không có màn hình, hãy dùng cv2.imwrite thay cho imshow)
    cv2.imwrite("google_lens_result.jpg", results_to_draw)
    print("Đã lưu kết quả thành công vào file 'google_lens_result.jpg'!")

# ==========================================
# CHẠY THỬ CHƯƠNG TRÌNH
# ==========================================
if __name__ == "__main__":
    test_image_path = "test_image.jpg" 
    google_lens_pipeline(test_image_path)
    print("Script đã sẵn sàng! Hãy bỏ comment 2 dòng cuối và truyền ảnh vào hàm google_lens_pipeline để test.")
