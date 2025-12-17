import urllib.request
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
            return json.loads(res_body)
    except Exception as e:
        print(f"Error: {e}")
        return None

def test():
    print("Testing Student Name on Bill...")
    
    # 1. Ensure we have a student
    students = make_request(f"{BASE_URL}/students", "GET")
    if not students:
        print("FAIL: No students found to test with.")
        return

    student = students[0]
    print(f"Selected Student: {student['name']} (ID: {student['id']})")
    
    # 2. Create Bill
    payload = {
        "user_type": "hostel",
        "student_id": student['id'],
        "meal_type": "Dinner",
        "amount": 50,
        "payment_mode": "Cash",
        "operator_id": 1
    }
    
    res = make_request(f"{BASE_URL}/bill", "POST", payload)
    if not res or res.get("status") != "success":
        print("FAIL: Bill creation failed")
        return

    bill_no = res.get("bill_no")
    print(f"Bill Created: {bill_no}")
    
    # 3. Fetch Bill and Check Name
    bill = make_request(f"{BASE_URL}/bills/{bill_no}", "GET")
    if bill:
         print(f"Bill Data: {bill}")
         if bill.get('student_name') == student['name']:
             print("PASS: Student Name is present and correct.")
         else:
             print(f"FAIL: Expected name '{student['name']}', got '{bill.get('student_name')}'")
    else:
        print("FAIL: Could not fetch bill")

if __name__ == "__main__":
    test()
