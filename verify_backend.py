import urllib.request
import urllib.error
import json

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
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise

def test_add_student():
    print("Testing Add Student...")
    payload = {
        "name": "Backend Test Student",
        "payment_status": "Unpaid",
        "payment_mode": "Cash"
    }
    try:
        res = make_request(f"{BASE_URL}/students", "POST", payload)
        print(f"PASS: Add Student ({res})")
    except:
        print("FAIL: Add Student")

def test_get_students():
    print("Testing Get Students...")
    try:
        students = make_request(f"{BASE_URL}/students", "GET")
        print(f"PASS: Get Students (Count: {len(students)})")
        found = any(s['name'] == "Backend Test Student" for s in students)
        if found: 
            print("PASS: Student Found in List")
            return students
        else:
            print("FAIL: Student NOT Found")
            # print all names for debugging
            print(f"Existing names: {[s['name'] for s in students]}")
            return []
    except:
        print("FAIL: Get Students")
        return []

def test_delete_student(students):
    print("Testing Delete Student...")
    target = next((s for s in students if s['name'] == "Backend Test Student"), None)
    if not target:
        print("SKIP: Cannot delete (student not found)")
        return

    try:
        # urllib requires escaping params manually or simple concat
        res = make_request(f"{BASE_URL}/students?id={target['id']}", "DELETE")
        print("PASS: Delete Student")
    except:
        print("FAIL: Delete Student")

def main():
    test_add_student()
    students = test_get_students()
    test_delete_student(students)
    print("--- Done ---")

if __name__ == "__main__":
    main()
