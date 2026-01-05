import sqlite3
import os

DB_FILE = 'canteen.db'

def reset_data():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("Resetting Test Data...")
    
    try:
        # 1. Clear Bills
        c.execute("DELETE FROM bills")
        print(f"Deleted {c.rowcount} bills.")
        
        # 2. Clear Meals (Attendance)
        c.execute("DELETE FROM meals")
        print(f"Deleted {c.rowcount} meal records.")
        
        # 3. Clear Student Transactions (Ledger)
        c.execute("DELETE FROM student_transactions")
        print(f"Deleted {c.rowcount} student transactions.")
        
        # 4. Clear Staff Transactions (Optional but recommended for full clean)
        c.execute("DELETE FROM staff_transactions")
        print(f"Deleted {c.rowcount} staff transactions.")

        # 5. Reset Student Balances
        c.execute("UPDATE students SET amount_paid = 0, remaining_amount = 0")
        print(f"Reset balances for {c.rowcount} students.")

        # 6. Delete "sqlite_sequence" for these tables to reset ID counters (Optional)
        tables = ['bills', 'meals', 'student_transactions', 'staff_transactions']
        for t in tables:
            c.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
            
        conn.commit()
        print("Reset Complete.")
        
    except Exception as e:
        print(f"Error resetting data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    confirm = input("Are you sure you want to DELETE ALL TRANSACTION DATA? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_data()
    else:
        print("Cancelled.")
