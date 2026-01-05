import sqlite3
import datetime
import json
import os

DB_FILE = 'canteen.db'

def create_test_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Ensure a student exists
    c.execute("SELECT id FROM students LIMIT 1")
    row = c.fetchone()
    if not row:
        print("No student found. Creating one...")
        c.execute("INSERT INTO students (name, regd_no, dept) VALUES ('Test Student', 'TEST001', 'CSE')")
        student_id = c.lastrowid
    else:
        student_id = row[0]
        print(f"Using Student ID: {student_id}")

    # 2. Add Bills (Food - Direct)
    # Bill 1: Today (Should appear)
    details_1 = json.dumps({"student_id": student_id, "meal_type": "Lunch"})
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO bills (bill_no, date, amount, payment_mode, details) VALUES (?, ?, ?, ?, ?)",
              (f"TEST-B1-{int(datetime.datetime.now().timestamp())}", today, 50, "Cash", details_1))

    # Bill 2: Last Month (Should be filtered out if we select this month)
    last_month = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    details_2 = json.dumps({"student_id": student_id, "meal_type": "Breakfast"})
    c.execute("INSERT INTO bills (bill_no, date, amount, payment_mode, details) VALUES (?, ?, ?, ?, ?)",
              (f"TEST-B2-{int(datetime.datetime.now().timestamp())}", last_month, 30, "Cash", details_2))

    # 3. Add Student Transactions (Payment / Account Food)
    # Payment 1: Today
    c.execute("INSERT INTO student_transactions (student_id, date, amount, mode, type, remarks) VALUES (?, ?, ?, ?, ?, ?)",
              (student_id, today, 500, "Cash", "Payment", "Fee Payment"))

    # Transaction 2: Last Month (Account Food)
    c.execute("INSERT INTO student_transactions (student_id, date, amount, mode, type, remarks) VALUES (?, ?, ?, ?, ?, ?)",
              (student_id, last_month, 40, "Account", "Food", "Dinner"))

    conn.commit()
    print("Test Data Created.")
    print(f"Inserted Bill Today: {today}")
    print(f"Inserted Bill Last Month: {last_month}")
    conn.close()

if __name__ == "__main__":
    create_test_data()
