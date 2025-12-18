import os
import sqlite3

# Remove db if exists to test creation
if os.path.exists("canteen_test.db"):
    os.remove("canteen_test.db")

# Temporarily point to test db in app.py context if possible, 
# but simply importing app will use 'canteen.db'.
# To avoid messing with prod db, we can check if 'operators' table exists in current canteen.db
# assuming it might be there or not. 
# actually, let's just import and see if it runs without error and ensures table exists.

try:
    print("Importing app...")
    import app
    print("Import successful.")
    
    conn = sqlite3.connect('canteen.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operators'")
    row = c.fetchone()
    conn.close()
    
    if row:
        print("SUCCESS: 'operators' table exists.")
    else:
        print("FAILURE: 'operators' table does NOT exist.")

except Exception as e:
    print(f"FAILURE: Exception during import or check: {e}")
