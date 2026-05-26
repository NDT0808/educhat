import subprocess
import sys
import os

try:
    print("Đang lấy log từ Docker...")
    # Đi vào thư mục infra và lấy 50 dòng log cuối của container llm
    result = subprocess.run(
        ["docker", "compose", "logs", "llm", "--tail", "100"], 
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "infra"),
        capture_output=True, 
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    
    with open("docker_error_log.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        f.write(result.stderr)
except Exception as e:
    print("Lỗi khi lấy log:", e)
