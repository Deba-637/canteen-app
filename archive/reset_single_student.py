import sqlite3
import json
import os

DB_FILE = 'canteen.db'

def reset_student(student_id):
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print(f"Resetting history for Student ID: {student_id}...")
    
    try:
        # 1. Clear Meals
        c.execute("DELETE FROM meals WHERE student_id=?", (student_id,))
        print(f"Deleted {c.rowcount} meal records.")
        
        # 2. Clear Student Transactions (Ledger)
        c.execute("DELETE FROM student_transactions WHERE student_id=?", (student_id,))
        print(f"Deleted {c.rowcount} student transactions.")
        
        # 3. Clear Bills (Parse JSON details)
        c.execute("SELECT id, details FROM bills")
        all_bills = c.fetchall()
        bills_to_delete = []
        for row in all_bills:
            try:
                details = json.loads(row[1])
                if str(details.get('student_id')) == str(student_id):
                    bills_to_delete.append(row[0])
            except:
                pass
        
        if bills_to_delete:
            c.execute(f"DELETE FROM bills WHERE id IN ({','.join(['?']*len(bills_to_delete))})", bills_to_delete)
            print(f"Deleted {c.rowcount} bills.")
        else:
            print("No bills found for this student.")

        # 4. Reset Student Balance
        c.execute("UPDATE students SET amount_paid = 0, remaining_amount = 0, payment_status = 'Unpaid' WHERE id=?", (student_id,))
        print(f"Reset balance for student ID {student_id}.")

        conn.commit()
        print("Reset Complete.")
        
    except Exception as e:
        print(f"Error resetting student: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    sid = input("Enter Student ID to reset: ")
    if sid.strip():
        reset_student(sid.strip())
    else:
        print("Invalid ID")
