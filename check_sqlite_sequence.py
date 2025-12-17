import sqlite3
import os

DB_FILE = 'canteen.db'

def inspect_sequence():
    if not os.path.exists(DB_FILE):
        print(f"Database file '{DB_FILE}' not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    print("=== sqlite_sequence Data ===")
    try:
        c.execute("SELECT * FROM sqlite_sequence")
        rows = c.fetchall()
        if not rows:
            print("Table is empty.")
        else:
            print(f"{'Table Name':<20} | {'Seq':<10}")
            print("-" * 35)
            for row in rows:
                print(f"{row[0]:<20} | {row[1]:<10}")
    except Exception as e:
        print(f"Error reading sqlite_sequence: {e}")
    
    conn.close()

if __name__ == "__main__":
    inspect_sequence()
