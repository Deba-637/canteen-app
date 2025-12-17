import sqlite3
import os

DB_FILE = 'canteen.db'

def inspect():
    if not os.path.exists(DB_FILE):
        print(f"Database file '{DB_FILE}' not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    print("=== Students ===")
    try:
        c.execute("SELECT * FROM students")
        rows = c.fetchall()
        if not rows:
            print("No students found.")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading students: {e}")

    print("\n=== Meals ===")
    try:
        c.execute("SELECT * FROM meals")
        rows = c.fetchall()
        if not rows:
            print("No meals records found.")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading meals: {e}")

    print("\n=== Payments ===")
    try:
        c.execute("SELECT * FROM payments")
        rows = c.fetchall()
        if not rows:
            print("No payment records found.")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error reading payments: {e}")

    print("\n=== Bills Schema ===")
    try:
        c.execute("PRAGMA table_info(bills)")
        columns = c.fetchall()
        for col in columns:
            print(col)
        print("\n=== Bills Data ===")
        c.execute("SELECT * FROM bills LIMIT 5")
        for row in c.fetchall():
            print(row)
    except Exception as e:
        print(f"Error reading bills: {e}")

    conn.close()

if __name__ == "__main__":
    inspect()
