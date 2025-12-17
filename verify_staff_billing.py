import urllib.request
import urllib.error
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
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise

def test_staff_billing():
    print("Testing Staff Billing...")
    payload = {
        "user_type": "staff",
        "meal_type": "Lunch",
        "amount": 60,
        "payment_mode": "Cash",
        "guest_name": "Dr. Verification",
        "operator_id": 1
    }
    
    try:
        # Create Bill
        res = make_request(f"{BASE_URL}/bill", "POST", payload)
        print(f"Bill Creation Response: {res}")
        
        if res.get("status") == "success":
            bill_no = res.get("bill_no")
            print(f"PASS: Bill Created (ID: {bill_no})")
            
            # Verify Bill Details
            bill_res = make_request(f"{BASE_URL}/bills/{bill_no}", "GET")
            print(f"Bill Fetch Response: {bill_res}")
            
            if bill_res['user_type'] == 'staff' and bill_res['guest_name'] == 'Dr. Verification':
                print("PASS: Verified Bill Details (Correct Type and Name)")
            else:
                print(f"FAIL: Incorrect Bill Details. Got Type: {bill_res['user_type']}, Name: {bill_res['guest_name']}")
        else:
            print("FAIL: Bill Creation Failed")
            
    except Exception as e:
        print(f"FAIL: Exception during test - {e}")

if __name__ == "__main__":
    test_staff_billing()
