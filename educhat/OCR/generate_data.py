import os
import random
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 1. THIẾT LẬP THÔNG SỐ
NUM_TRAIN = 100   # Giảm xuống 100 ảnh để train nháp nhanh chóng
NUM_TEST = 20     # Giảm xuống 20 ảnh
DATA_DIR = "data"
FONT_SIZE = 32

# Tạo thư mục data nếu chưa có
os.makedirs(DATA_DIR, exist_ok=True)

vocab = [
    "Nguyễn Văn A", "Trần Thị B", "Lê Văn C", "Cộng hòa Xã hội", "Chủ nghĩa Việt Nam",
    "Độc lập", "Tự do", "Hạnh phúc", "Số Căn cước", "Ngày sinh", "Quê quán",
    "Nơi thường trú", "Có giá trị đến", "Cục trưởng Cục Cảnh sát", "Quản lý hành chính",
    "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Cần Thơ", "Hải Phòng", "Quảng Ninh",
    "0123456789", "12/05/1998", "30-04-1975", "02/09/1945"
]

def generate_random_text():
    num_words = random.randint(1, 3)
    return " ".join(random.sample(vocab, num_words))

def create_image_with_text(text, filename):
    # Dùng font mặc định của PIL để không bao giờ bị lỗi thiếu file font
    font = ImageFont.load_default()
    
    # Tính kích thước chữ (Font mặc định thường rất nhỏ nên ta tính thủ công)
    text_width = len(text) * 6
    text_height = 15
    
    bg_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    image = Image.new('RGB', (text_width + 40, text_height + 40), color=bg_color)
    draw = ImageDraw.Draw(image)

    text_color = (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50))
    draw.text((20, 10), text, font=font, fill=text_color)

    # Lưu ảnh trực tiếp vào thư mục data
    filepath = os.path.join(DATA_DIR, filename)
    image.save(filepath)
    return os.path.exists(filepath) # Xác nhận đã lưu file thành công

def generate_dataset(num_samples, csv_filename, prefix):
    data = []
    print(f"Đang tạo {num_samples} ảnh cho tập {prefix}...")
    for i in range(num_samples):
        text = generate_random_text()
        filename = f"{prefix}_{i:05d}.jpg"
        
        if create_image_with_text(text, filename):
            data.append({"file_name": filename, "text": text})
            
    df = pd.DataFrame(data)
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"Hoàn thành tạo {csv_filename}!")

if __name__ == "__main__":
    print(f"Đang tạo dữ liệu trong thư mục: {os.path.abspath(DATA_DIR)}")
    generate_dataset(NUM_TRAIN, "train.csv", "train")
    generate_dataset(NUM_TEST, "test.csv", "test")
    print("Mọi thứ đã sẵn sàng để bạn mang đi Train!")
