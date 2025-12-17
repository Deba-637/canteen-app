import sqlite3
import datetime

DB_FILE = 'canteen.db'

def fix():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Drop bills table
    new_name = f"bills_legacy_dropped_{int(datetime.datetime.now().timestamp())}"
    print(f"Archiving (RENAME) 'bills' table to '{new_name}'...")
    try:
        c.execute(f"ALTER TABLE bills RENAME TO {new_name}")
        print("Renamed existing bills table.")
        conn.commit()
    except Exception as e:
        print(f"Could not rename (maybe missing?): {e}")
        
    conn.close()

if __name__ == '__main__':
    fix()
