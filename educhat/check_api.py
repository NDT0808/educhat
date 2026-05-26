
import requests
import json

try:
    response = requests.get("http://localhost:1820/v1/curriculum/full")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
