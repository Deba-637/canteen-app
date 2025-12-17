import sqlite3

conn = sqlite3.connect('canteen.db')
c = conn.cursor()

print("--- Students Table Schema ---")
try:
    c.execute("PRAGMA table_info(students)")
    for col in c.fetchall():
        print(col)
except Exception as e:
    print(e)
conn.close()
