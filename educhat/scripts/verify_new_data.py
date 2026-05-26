import requests
import json

RAG_URL = "http://localhost:8002"
headers = {"X-Internal-Token": "internal_secret_key_change_me"}

def verify_new_data():
    query = "ngành công nghệ thông tin chất lượng cao mã ngành 7480201CLC"
    print(f"🔍 Đang kiểm tra dữ liệu mới với câu hỏi: '{query}'")
    
    try:
        resp = requests.get(
            f"{RAG_URL}/v1/retrieve",
            params={"query": query, "top_k": 3},
            headers=headers
        )
        if resp.status_code == 200:
            results = resp.json()
            if len(results) > 0:
                print(f"✅ Tìm thấy {len(results)} kết quả liên quan!")
                for i, res in enumerate(results):
                    print(f"\n--- Kết quả {i+1} (Score: {res['score']:.4f}) ---")
                    print(res['content'][:300] + "...")
            else:
                print("❌ Không tìm thấy kết quả nào. Có thể dữ liệu chưa được index xong hoặc query chưa khớp.")
        else:
            print(f"❌ Lỗi: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    verify_new_data()
