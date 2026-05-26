import fitz
import pytesseract
from PIL import Image
import os
import time

# Đường dẫn
pdf_path = r"c:\Users\ASUS\Downloads\CNTT_CLC_MoTa_CTDT_2428.pdf"
output_path = r"c:\Users\ASUS\Downloads\educhat\educhat\sgu_curriculum.txt"

def process_ocr_all():
    print("🚀 Bắt đầu trích xuất toàn bộ 66 trang bằng Tesseract...")
    if not os.path.exists(pdf_path):
        print("❌ Không tìm thấy file PDF.")
        return

    doc = fitz.open(pdf_path)
    full_text = []

    for i in range(len(doc)):
        start_page = time.time()
        page = doc[i]
        
        # Chuyển trang thành ảnh
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Increase DPI for better quality
        img_path = f"page_{i}.png"
        pix.save(img_path)
        
        # OCR
        try:
            # Try to use Vietnamese if available, else English
            text = pytesseract.image_to_string(Image.open(img_path), lang='eng')
            full_text.append(f"\n--- TRANG {i+1} ---\n{text}")
            print(f"✅ Xong trang {i+1}/{len(doc)}")
        except Exception as e:
            print(f"❌ Lỗi trang {i+1}: {e}")
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
        
        elapsed = time.time() - start_page
        print(f"✅ Xong trang {i+1}/{len(doc)} ({elapsed:.2f}s)")

        # Lưu sau mỗi 10 trang
        if (i + 1) % 10 == 0:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(full_text))

    # Lưu bản cuối cùng
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_text))
    
    print(f"\n✨ Hoàn thành! Đã trích xuất {len(doc)} trang vào {output_path}")
    doc.close()

if __name__ == "__main__":
    process_ocr_all()
