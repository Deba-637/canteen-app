import requests
import os

BASE_URL = 'http://localhost:8000/api'
EXCEL_FILE = 'hostel_students.xlsx'

def test_excel_backup():
    print("Testing Excel Backup...")
    
    # 1. Trigger Backup
    try:
        res = requests.post(f'{BASE_URL}/backup/excel')
        if res.status_code == 200:
            print("✅ API Call Success")
        else:
            print(f"❌ API Call Failed: {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Check File Existence
    if os.path.exists(EXCEL_FILE):
        print(f"✅ Excel File Created: {EXCEL_FILE}")
        # Optional: check size > 0
        if os.path.getsize(EXCEL_FILE) > 0:
            print("✅ File has content")
        else:
            print("❌ File is empty")
    else:
        print("❌ Excel File NOT found")

if __name__ == '__main__':
    test_excel_backup()
