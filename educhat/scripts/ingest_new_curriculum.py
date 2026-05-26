import requests
import os
import time

RAG_URL = "http://localhost:8002"
headers = {
    "X-Internal-Token": "internal_secret_key_change_me"
}
def ingest_curriculum():
    file_path = "sgu_curriculum.txt"
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"📄 Đang chuẩn bị nạp {len(content)} ký tự dữ liệu vào RAG...")

    # Chia nhỏ content thành các khối (chunks) để RAG hoạt động tốt hơn
    # Mỗi chunk khoảng 1000 ký tự
    chunk_size = 1000
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
    
    payload = {
        "source": "sgu_curriculum_2428",
        "documents": chunks,
        "metadatas": [{"source": "sgu_curriculum_2428", "page": i//(len(chunks)//66 + 1)} for i in range(len(chunks))]
    }

    try:
        print(f"📤 Đang gửi {len(chunks)} đoạn văn bản tới RAG service...")
        resp = requests.post(f"{RAG_URL}/v1/ingest", json=payload, headers=headers)
        
        if resp.status_code == 200:
            job_id = resp.json().get("job_id")
            print(f"✅ Đã gửi thành công! Job ID: {job_id}")
            
            # Kiểm tra trạng thái
            while True:
                time.sleep(2)
                status_resp = requests.get(f"{RAG_URL}/v1/jobs/{job_id}", headers=headers)
                status_data = status_resp.json()
                status = status_data.get("status")
                print(f"⏳ Trạng thái: {status}...")
                
                if status == "completed":
                    print("✨ Hoàn tất nạp dữ liệu mới vào hệ thống RAG!")
                    break
                elif status == "failed":
                    print(f"❌ Lỗi: {status_data.get('error')}")
                    break
        else:
            print(f"❌ Lỗi API: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    ingest_curriculum()
