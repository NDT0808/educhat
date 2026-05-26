import sys
import os

# Add paths to PYTHONPATH
project_root = r"c:\Users\ASUS\Downloads\educhat\educhat"
sys.path.append(os.path.join(project_root, "services", "llm", "src"))
sys.path.append(os.path.join(project_root, "libs", "common", "src"))

from llm.services.emotion_service import EmotionService

def test():
    service = EmotionService()
    texts = [
        "Tôi cảm thấy rất áp lực vì kỳ thi sắp tới, quá tải thực sự.",
        "Cảm ơn bạn, mình đã hiểu bài rồi, rất tuyệt vời!",
        "Hôm nay bình thường, không có gì đặc biệt.",
        "Mình hơi lo vì chưa xong bài tập."
    ]
    
    for t in texts:
        res = service.analyze(t)
        print(f"Text: {t}")
        print(f"Result: {res}")
        print("-" * 20)

if __name__ == "__main__":
    test()
