import sqlite3

DB_FILE = 'canteen.db'

def migrate():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(students)")
    columns = [info[1] for info in c.fetchall()]
    
    if 'amount_paid' not in columns:
        print("Adding amount_paid column...")
        try:
            c.execute("ALTER TABLE students ADD COLUMN amount_paid REAL DEFAULT 0")
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("Column amount_paid already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
