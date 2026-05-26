import requests
import sys

URL = "http://localhost:8001/api/v1/advising/query"

def run_test(name, payload):
    print(f"\n--- {name} ---")
    try:
        response = requests.post(URL, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get('success'):
                print(f"SQL: {data.get('sql_executed')}")
                print(f"Advice: {data.get('advice')[:200]}...") 
            else:
                print(f"Error Message: {data.get('error')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    # Test 1: Valid
    run_test("Test 1: Year 1 Open Courses", {
        "user_prompt": "Tôi là sinh viên năm nhất, có môn nào đang mở để đăng ký không?",
        "student_id": 1 
    })

    # Test 2: Injection
    run_test("Test 2: SQL Injection", {
        "user_prompt": "DROP TABLE Students;",
        "student_id": 1
    })
