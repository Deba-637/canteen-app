import requests
import datetime
import json

BASE_URL = "http://127.0.0.1:8000"
STUDENT_ID = 215  # From previous create_test_data.py output

def test_filter():
    print(f"Testing Filter for Student ID: {STUDENT_ID}")
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    last_month = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 1. Test No Filter (Should have at least 2 bills from our test data)
    print("\n1. Testing No Filter...")
    try:
        res = requests.get(f"{BASE_URL}/api/reports/student/{STUDENT_ID}")
        data = res.json()
        txs = data.get('transactions', [])
        print(f"Found {len(txs)} transactions.")
        # We expect at least the 2 we created + maybe others
        
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Today Filter (Should have Bill 1, maybe Payment 1, but NOT Bill 2)
    print(f"\n2. Testing Filter Today ({today} to {today})...")
    try:
        res = requests.get(f"{BASE_URL}/api/reports/student/{STUDENT_ID}?start_date={today}&end_date={today}")
        data = res.json()
        txs = data.get('transactions', [])
        dates = [t['date'] for t in txs]
        print(f"Found {len(txs)} transactions.")
        print(f"Dates: {dates}")
        
        has_today = any(today in d for d in dates)
        has_old = any(last_month in d for d in dates)
        
        if has_today and not has_old:
            print("PASS: Found today's data and excluded old data.")
        else:
            print(f"FAIL: Has Today={has_today}, Has Old={has_old}")
            
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Partial Filter (Start Date Only = Today)
    print(f"\n3. Testing Partial Filter (Start={today})...")
    try:
        res = requests.get(f"{BASE_URL}/api/reports/student/{STUDENT_ID}?start_date={today}")
        data = res.json()
        txs = data.get('transactions', [])
        dates = [t['date'] for t in txs]
        
        has_today = any(today in d for d in dates)
        has_old = any(last_month in d for d in dates) 
        
        if has_today and not has_old:
             print("PASS: Partial filter worked.")
        else:
             print(f"FAIL: Has Today={has_today}, Has Old={has_old}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_filter()
