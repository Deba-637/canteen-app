import requests
import time
import subprocess
import sys
import os

# Start Server
print("Starting Server...")
server = subprocess.Popen([sys.executable, 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(3) # Wait for startup

BASE_URL = 'http://localhost:8000/api'
SESSION = requests.Session()

def test_login():
    print("Testing Login...")
    # Default admin
    res = SESSION.post(f'{BASE_URL}/login', json={'username': 'admin', 'password': 'admin123', 'role': 'admin'})
    if res.status_code == 200:
        print("✅ Login Success")
    else:
        print(f"❌ Login Failed: {res.text}")
        sys.exit(1)

def test_add_student():
    print("Testing Add Student...")
    data = {'name': 'Test Student', 'roll': 'TEST001', 'dept': 'CSE', 'payment_status': 'Unpaid'}
    res = SESSION.post(f'{BASE_URL}/students', json=data)
    if res.status_code == 200:
        print("✅ Add Student Success")
        return res.json()['id']
    elif res.status_code == 409:
        print("⚠️ Student already exists (Skip)")
        # Get existing ID
        res = SESSION.get(f'{BASE_URL}/students')
        for s in res.json():
            if s['roll'] == 'TEST001': return s['id']
    else:
        print(f"❌ Add Student Failed: {res.text}")
        sys.exit(1)

def test_billing(student_id):
    print("Testing Billing...")
    data = {
        'user_type': 'hostel',
        'student_id': student_id,
        'meal_type': 'Lunch',
        'amount': 50,
        'payment_mode': 'Cash',
        'operator_id': 1
    }
    res = SESSION.post(f'{BASE_URL}/bill', json=data)
    if res.status_code == 200:
        bill_no = res.json()['bill_no']
        print(f"✅ Billing Success. Bill No: {bill_no}")
        return bill_no
    else:
        print(f"❌ Billing Failed: {res.text}")
        sys.exit(1)

def test_bill_view(bill_no):
    print("Testing Bill View...")
    res = SESSION.get(f'http://localhost:8000/bill-view/{bill_no}')
    if res.status_code == 200 and 'CANTEEN RECEIPT' in res.text:
        print("✅ Bill View HTML Success")
    else:
        print(f"❌ Bill View Failed: {res.status_code}")

try:
    test_login()
    s_id = test_add_student()
    if s_id:
        bill_no = test_billing(s_id)
        test_bill_view(bill_no)
    
    print("\n🎉 ALL TESTS PASSED")
except Exception as e:
    print(f"\n❌ Exception: {e}")
    # Print server errors
    if server.poll() is not None:
        print(f"Server exited with code {server.returncode}")
        print("STDOUT:", server.stdout.read())
        print("STDERR:", server.stderr.read())
finally:
    print("Stopping Server...")
    server.terminate()
