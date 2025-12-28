import os
import unittest
import json
import sqlite3
import datetime

# --- CONFIGURATION MUST BE BEFORE IMPORT ---
os.environ['FLASK_ENV'] = 'testing'
os.environ['DB_PATH'] = 'test_canteen.db'

# Now safe to import
from app import app, init_db, get_db

class CanteenSystemTests(unittest.TestCase):

    def setUp(self):
        """Set up a clean database before each test"""
        if os.path.exists('test_canteen.db'):
            os.remove('test_canteen.db')
        
        self.app = app.test_client()
        
        # Manually init DB for the test
        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up after test"""
        # Close any lingering connections?
        # get_db() contexts should be closed by Flask
        pass
        # We can leave the DB for inspection if it fails, or delete it
        if os.path.exists('test_canteen.db'):
            try:
                os.remove('test_canteen.db')
            except PermissionError:
                print("Warning: Could not delete test_canteen.db (locked)")

    def test_daily_report_logic(self):
        """Test if reports correctly distinguish between days"""
        print("\n--- Testing Daily Report Logic ---")
        
        # 1. Create Student
        res = self.app.post('/api/students', json={
            'name': 'Test Student', 'roll': '101', 'dept': 'CS', 'phone': '123'
        })
        self.assertEqual(res.status_code, 200)
        student_id = res.json['id']
        
        # 2. Simulate "Yesterday"
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        
        with app.app_context():
            conn = get_db()
            c = conn.cursor()
            # Meal yesterday
            c.execute("INSERT INTO meals (student_id, date, breakfast, lunch, dinner) VALUES (?, ?, 1, 1, 1)", 
                      (student_id, yesterday))
            # Bill yesterday (Revenue: 100)
            c.execute("INSERT INTO bills (bill_no, date, amount, details, payment_mode) VALUES (?, ?, ?, ?, ?)",
                      ('BILL_YESTERDAY', yesterday + " 10:00:00", 100.0, '{}', 'Cash'))
            conn.commit()
            conn.close()
            
        # 3. Simulate "Today"
        # Breakfast Bill (Revenue: 30)
        self.app.post('/api/bill', json={
            'user_type': 'hostel', 'student_id': student_id, 
            'meal_type': 'Breakfast', 'amount': 30, 'payment_mode': 'Cash'
        })
        
        # 4. Check Daily Stats Report (Should only show Today's data)
        res = self.app.get('/api/reports/meals')
        report = res.json
        print(f"Today's Report Data: {report}")
        
        self.assertEqual(report['Breakfast'], 1, "Report should only count today's meals")
        self.assertEqual(report['Lunch'], 0, "Report should only count today's meals")
        self.assertEqual(report['revenue'], 30.0, "Revenue should only include today's bills (30)")

    def test_export_logic(self):
        """Test the Export CSV endpoint to see if it filters by daily correctly"""
        print("\n--- Testing Export CSV Logic ---")
        
        # Yesterday
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        with app.app_context():
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO bills (bill_no, date, amount, details, payment_mode) VALUES (?, ?, ?, ?, ?)",
                      ('BILL_OLD', yesterday + " 10:00:00", 100, '{}', 'Cash'))
            c.execute("INSERT INTO bills (bill_no, date, amount, details, payment_mode) VALUES (?, ?, ?, ?, ?)",
                      ('BILL_NEW', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 50, '{}', 'Cash'))
            conn.commit()
            conn.close()
            
        # 1. Test DEFAULT (All)
        res = self.app.get('/api/export')
        csv_content = res.data.decode('utf-8')
        if 'BILL_OLD' in csv_content:
            print(">> Default Export matches All (Correct)")
        else:
            self.fail("Default export missing old bills")
            
        # 2. Test DAILY
        res = self.app.get('/api/export?type=daily')
        csv_daily = res.data.decode('utf-8')
        
        if 'BILL_OLD' not in csv_daily and 'BILL_NEW' in csv_daily:
            print(">> Daily Export filters correctly! (Success)")
        else:
            print(f"Daily CSV Content:\n{csv_daily}")
            self.fail("Daily export logic failed")

    def test_transaction_integrity(self):
        """Test Debt Updates and Balance consistency"""
        print("\n--- Testing Transaction Integrity ---")
        
        # Create Student
        res = self.app.post('/api/students', json={
            'name': 'Debt Student', 'roll': '102'
        })
        s_id = res.json['id']
        
        # 1. Bill on Account (50) -> Debt 50
        self.app.post('/api/bill', json={
            'user_type': 'hostel', 'student_id': s_id, 
            'meal_type': 'Lunch', 'amount': 50, 'payment_mode': 'Account'
        })
        
        # Check Status (Should be Unpaid)
        res = self.app.get('/api/students')
        student = next(s for s in res.json if s['id'] == s_id)
        print(f"Initial Status: {student['payment_status']}")
        
        # 2. Partial Pay (20) -> Debt 30
        self.app.post('/api/students/pay', json={
            'student_id': s_id, 'amount': 20, 'mode': 'Cash'
        })
        
        # Check Status (Should be Partial)
        res = self.app.get('/api/students')
        student = next(s for s in res.json if s['id'] == s_id)
        print(f"Partial Status: {student['payment_status']}")
        self.assertEqual(student['payment_status'], 'Partial')
        
        # 3. Full Pay (30) -> Debt 0
        self.app.post('/api/students/pay', json={
            'student_id': s_id, 'amount': 30, 'mode': 'Cash'
        })
        
        res = self.app.get('/api/students')
        student = next(s for s in res.json if s['id'] == s_id)
        print(f"Full Paid Status: {student['payment_status']}")
        self.assertEqual(student['payment_status'], 'Paid') 

    def test_delete_transaction(self):
        """Test Deleting a transaction (Undo Payment)"""
        print("\n--- Testing Undo Transaction ---")
        
        # 1. Setup Student with Debt 500
        res = self.app.post('/api/students', json={'name': 'Undo Student', 'roll': '103', 'remaining_amount': 500})
        s_id = res.json['id']
        
        # 2. Make Payment of 500 (Accidental)
        self.app.post('/api/students/pay', json={'student_id': s_id, 'amount': 500})
        
        # Verify Debt 0
        res = self.app.get('/api/students')
        student = next(s for s in res.json if s['id'] == s_id)
        self.assertEqual(student['remaining_amount'], 0)
        self.assertEqual(student['payment_status'], 'Paid')
        
        # 3. Find Transaction ID to delete
        res = self.app.get(f'/api/reports/student/{s_id}')
        txs = res.json['transactions']
        # Find the payment tx
        pay_tx = next(t for t in txs if t['type'] == 'Payment')
        tx_id = pay_tx['id']
        print(f"Deleting Transaction ID: {tx_id}")
        
        # 4. Delete Transaction
        res = self.app.delete(f'/api/transactions?id={tx_id}')
        self.assertEqual(res.status_code, 200)
        
        # 5. Verify Debt Restored (Should be 500)
        res = self.app.get('/api/students')
        student = next(s for s in res.json if s['id'] == s_id)
        print(f"Restored Debt: {student['remaining_amount']}")
        self.assertEqual(student['remaining_amount'], 500)
        self.assertEqual(student['payment_status'], 'Unpaid')
        
        print(">> Undo Payment Successful!") 

if __name__ == '__main__':
    unittest.main()
