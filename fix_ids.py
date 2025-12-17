import sqlite3

DB_FILE = 'canteen.db'

def fix_ids():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Enable foreign keys just in case, though we handle it manually
    c.execute("PRAGMA foreign_keys = ON")
    
    # Get all students ordered by current ID
    c.execute("SELECT id, name FROM students ORDER BY id ASC")
    students = c.fetchall()
    
    print(f"Found {len(students)} students.")
    
    # We can't update IDs in place easily if there are conflicts (e.g. changing 11 to 3 is fine, but if we had to swap 2 and 3 it's messier).
    # Since we are just compressing 1, 2, 11 -> 1, 2, 3, we can just iterate.
    # However, if we update ID 11 to 3, we must ensure 3 doesn't exist yet.
    # The safest way is to do it in memory or use a temporary mapping.
    # Since existing IDs are [1, 2, 11], and we want [1, 2, 3].
    
    # Mapping old_id -> new_id
    id_map = {}
    new_id_counter = 1
    
    for row in students:
        old_id = row[0]
        id_map[old_id] = new_id_counter
        new_id_counter += 1
        
    print("ID Mapping Plan:", id_map)
    
    # Perform updates
    # We must be careful not to violate primary key constraints during the process.
    # E.g. if we have 1, 2, 3 and we want to change 3->2 and 2->1.
    # Here we are only COMPACTING, so new_id <= old_id always.
    # So if we process in ASCENDING order, we technically *could* overwrite if we are not careful?
    # No, if new_id <= old_id, and we start from 1. 1->1 (ok), 2->2 (ok), 11->3 (ok).
    # Since 3 was not in the original set (implied by gap), it's safe.
    
    # But to be absolutely safe and avoid unique constraint errors if there is overlap in complex cases:
    # We will disable FK checks temporarily if needed (SQLite FKs are often off by default anyway unless enabled).
    
    try:
        # Check bills before
        print("Bills before update:")
        bills = c.execute("SELECT bill_no, student_id FROM bills WHERE student_id IS NOT NULL").fetchall()
        for b in bills:
            print(f"Bill {b[0]}: Student {b[1]}")

        for old_id, new_id in id_map.items():
            if old_id == new_id:
                continue
            
            print(f"Migrating Student {old_id} -> {new_id}")
            
            # Update Bills first (so they point to the 'future' new_id? No, bills point to data. 
            # Actually, standard practice: 
            # 1. Update Student ID. FLAGGED: If we update 11->3.
            # 2. Update Bill Student ID 11->3.
            
            # Since we can't defer constraints easily in a simple script without transactions...
            # We will just do it.
            
            # We need to temporarily set the ID to something negative to free up the 'old_id' spot? 
            # No, we are moving 11 -> 3. 3 is empty. So we can just update.
            # But what if we had 3 -> 4 (shift up)? Then updating 3->4 might hit 4 if 4 exists.
            # The prompt says: "ids are 1, 2, 11 not 1, 2, 3". So we are closing gaps.
            # So we are always moving from Higher to Lower (or Same).
            # Order ASC: 1->1, 2->2, 11->3.
            # When we process 1, 2, they stay.
            # When we process 11, we change it to 3. 3 is not taken.
            # So simple UPDATE is safe.
            
            # 1. Update Student
            c.execute("UPDATE students SET id = ? WHERE id = ?", (new_id, old_id))
            
            # 2. Update Bills
            c.execute("UPDATE bills SET student_id = ? WHERE student_id = ?", (new_id, old_id))
            
        conn.commit()
        print("Migration complete.")
        
        # Verify
        final_ids = [r[0] for r in c.execute("SELECT id FROM students").fetchall()]
        print("Final Student IDs:", final_ids)
        
    except Exception as e:
        print("Error during migration:", e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_ids()
