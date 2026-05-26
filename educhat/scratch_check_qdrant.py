import requests
import json

try:
    resp = requests.get("http://localhost:6333/collections/universities_hybrid")
    data = resp.json()
    if "result" in data:
        print(f"Points count: {data['result']['points_count']}")
        print(f"Vectors count: {data['result']['vectors_count']}")
        print(f"Status: {data['result']['status']}")
        print(f"Vectors config: {json.dumps(data['result']['config']['params']['vectors'], indent=2)}")
    else:
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
