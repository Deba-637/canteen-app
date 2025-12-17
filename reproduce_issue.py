import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:5000/api"

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    if data:
        jsondata = json.dumps(data).encode('utf-8')
        req.data = jsondata
    
    try:
        with urllib.request.urlopen(req) as r:
            res_body = r.read().decode('utf-8')
            return r.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"HTTP {e.code}: {body}")
        return e.code, body
    except Exception as e:
        print(f"Error: {e}")
        return 0, str(e)

def run():
    print("--- START REPRO ---")
    
    # 1. Add Student
    print("1. Adding Student...")
    s_name = f"DeleteTest_{int(time.time())}"
    status, res = make_request(f"{BASE_URL}/students", "POST", {
        "name": s_name,
        "payment_status": "Unpaid", 
        "payment_mode": "Cash"
    })
    if status != 200:
        print("Failed to add student")
        return

    # Find ID
    status, students = make_request(f"{BASE_URL}/students", "GET")
    target = next((s for s in students if s['name'] == s_name), None)
    if not target:
        print("Failed to find added student")
        return
    s_id = target['id']
    print(f"Student ID: {s_id}")

    # 2. Create Bill (to create dependency if any)
    print("2. Creating Bill...")
    status, res = make_request(f"{BASE_URL}/bill", "POST", {
        "user_type": "hostel",
        "student_id": str(s_id),
        "meal_type": "Lunch",
        "amount": 50,
        "payment_mode": "Cash",
        "operator_id": 1
    })
    print(f"Bill Status: {status}")

    # 3. Delete Student
    print("3. Deleting Student...")
    status, res = make_request(f"{BASE_URL}/students?id={s_id}", "DELETE")
    print(f"Delete Result: {status} -> {res}")
    
    print("--- END REPRO ---")

if __name__ == "__main__":
    run()
