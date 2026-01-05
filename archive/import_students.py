import sqlite3
import openpyxl
import os

DB_FILE = 'canteen.db'
EXCEL_FILE = 'Name List for Canteen e-Recipts.xlsx'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def import_students():
    if not os.path.exists(EXCEL_FILE):
        print(f"File not found: {EXCEL_FILE}")
        return

    print(f"Reading {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    conn = get_db()
    c = conn.cursor()
    
    # Get existing Regd Nos to avoid duplicates
    try:
        c.execute("SELECT regd_no FROM students")
        existing_regds = set(row['regd_no'] for row in c.fetchall())
    except Exception as e:
        print(f"Error fetching existing students: {e}")
        return

    added_count = 0
    skipped_count = 0
    
    # Iterate rows (SKIP HEADER)
    # Headers: Student ID, Name, Cource, Regestration No, Contact No
    # Indices(0-based): 0, 1, 2, 3, 4
    
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        name = row[1]
        dept = row[2]
        regd_no = row[3]
        phone = row[4]
        
        if not name:
            continue
            
        # Normalization
        name = str(name).strip()
        dept = str(dept).strip() if dept else 'General'
        phone = str(phone).strip() if phone else ''
        
        # Handle Regd No
        if regd_no:
            regd_no = str(regd_no).strip()
        else:
            # Generate Temp Regd No
            # Format: TEMP-{RowIndex} to ensure uniqueness in this batch
            regd_no = f"TEMP-{i+1}"
            
        # Check uniqueness against DB
        original_regd = regd_no
        suffix = 1
        while regd_no in existing_regds:
            regd_no = f"{original_regd}_{suffix}"
            suffix += 1
            
        try:
            # Insert
            # We let ID be AUTOINCREMENT
            c.execute("""
                INSERT INTO students (name, regd_no, dept, phone, payment_status, payment_mode, remaining_amount)
                VALUES (?, ?, ?, ?, 'Unpaid', 'Cash', 0)
            """, (name, regd_no, dept, phone))
            
            existing_regds.add(regd_no)
            added_count += 1
            print(f"Added: {name} ({regd_no})")
            
        except sqlite3.IntegrityError:
            print(f"Skipped (Duplicate logic fail?): {name} ({regd_no})")
            skipped_count += 1
        except Exception as e:
            print(f"Error adding {name}: {e}")
            skipped_count += 1

    conn.commit()
    conn.close()
    print(f"\nImport Complete!")
    print(f"Added: {added_count}")
    print(f"Skipped/Error: {skipped_count}")

def clear_database():
    conn = get_db()
    c = conn.cursor()
    print("Clearing existing student data...")
    try:
        # Delete related data first
        c.execute("DELETE FROM meals")
        c.execute("DELETE FROM payments")
        c.execute("DELETE FROM student_transactions")
        c.execute("DELETE FROM bills")
        # Delete students
        c.execute("DELETE FROM students")
        # Reset Auto-increment counters
        c.execute("DELETE FROM sqlite_sequence WHERE name='students'")
        conn.commit()
        print("Database cleared.")
    except Exception as e:
        print(f"Error clearing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clear_database()
    import_students()
