import urllib.request
import json
import urllib.error

BASE_URL = "http://localhost:5000/api"

def call_api(method, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return {}
            content = response.read().decode()
            if content:
                return json.loads(content)
            return {}
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {method} {url}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_api():
    print("Testing API...")
    
    # 1. Get Students
    students = call_api('GET', 'students')
    if students is None: return
    ids = sorted([s['id'] for s in students])
    print(f"Current IDs: {ids}")
    
    # 2. Add Student
    new_s = {"name": "Test 4", "roll": "R-1004", "payment_status": "Unpaid", "payment_mode": "Cash"}
    res = call_api('POST', 'students', new_s)
    if res:
        print(f"Added Student. Got ID: {res.get('id')}")
    
    # 3. Delete ID 2 (if exists)
    if 2 in ids:
        print("Deleting ID 2...")
        # Query params for DELETE need to be in URL
        req = urllib.request.Request(f"{BASE_URL}/students?id=2", method='DELETE')
        try:
            urllib.request.urlopen(req)
            print("Deleted ID 2.")
        except Exception as e:
            print("Delete failed:", e)

    # 4. Add Gap Filler
    gap_s = {"name": "Gap Filler", "roll": "R-Gap", "payment_status": "Unpaid", "payment_mode": "Cash"}
    res = call_api('POST', 'students', gap_s)
    if res:
        print(f"Added Gap Filler. Got ID: {res.get('id')}")

    # 5. Edit Student ID 2
    print("Editing ID 2...")
    edit_data = {"id": 2, "name": "Gap Updated", "roll": "R-Gap-Upd", "dept": "ECE", "payment_status": "Unpaid", "payment_mode": "Cash"}
    res = call_api('PUT', 'students', edit_data)
    if res and res.get('status') == 'success':
        print("Edit Success.")
        # Verify
        students = call_api('GET', 'students')
        s2 = next((s for s in students if s['id'] == 2), None)
        if s2:
            print(f"Fetched ID 2: Name={s2['name']}, Roll={s2['roll']}")
        else:
            print("ID 2 not found after edit!")

if __name__ == "__main__":
    test_api()
