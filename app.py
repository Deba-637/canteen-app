import os
import sqlite3
import datetime
import json
from flask import Flask, request, jsonify, send_from_directory, session, redirect

# Initialize Flask App
app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_keep_it_safe')

# Railway Persistent Storage Logic
if os.environ.get('DB_PATH'):
    DB_FILE = os.environ.get('DB_PATH')
elif os.path.exists('/app/data'):
    DB_FILE = '/app/data/canteen.db'
else:
    DB_FILE = 'canteen.db'

print(f"Using Database File: {DB_FILE}")

# --- Database Helper ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Students Table
        c.execute('''CREATE TABLE IF NOT EXISTS students (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT NOT NULL,
                     roll TEXT NOT NULL UNIQUE,
                     dept TEXT NOT NULL,
                     phone TEXT,
                     payment_status TEXT DEFAULT 'Unpaid',
                     payment_mode TEXT DEFAULT 'Cash',
                     amount_paid INTEGER DEFAULT 0,
                     remaining_amount REAL DEFAULT 0
                     )''')

        # Migration: Add phone column if missing
        try:
            c.execute("PRAGMA table_info(students)")
            stud_cols = [info[1] for info in c.fetchall()]
            if 'phone' not in stud_cols:
                print("Migrating: Adding phone column to students table...")
                c.execute("ALTER TABLE students ADD COLUMN phone TEXT")
            
            if 'payment_status' not in stud_cols:
                 c.execute("ALTER TABLE students ADD COLUMN payment_status TEXT DEFAULT 'Unpaid'")
            if 'payment_mode' not in stud_cols:
                 c.execute("ALTER TABLE students ADD COLUMN payment_mode TEXT DEFAULT 'Cash'")
            if 'amount_paid' not in stud_cols:
                print("Migrating: Adding amount_paid column...")
                c.execute("ALTER TABLE students ADD COLUMN amount_paid INTEGER DEFAULT 0")
            if 'remaining_amount' not in stud_cols:
                print("Migrating: Adding remaining_amount column...")
                c.execute("ALTER TABLE students ADD COLUMN remaining_amount REAL DEFAULT 0")
                
        except Exception as e: print(f"Migration Error (Students): {e}")

        # Meals Table (Tracking daily meals)
        c.execute('''CREATE TABLE IF NOT EXISTS meals (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     student_id INTEGER,
                     date TEXT NOT NULL,
                     breakfast INTEGER DEFAULT 0,
                     lunch INTEGER DEFAULT 0,
                     dinner INTEGER DEFAULT 0,
                     FOREIGN KEY(student_id) REFERENCES students(id))''')

        # Payments Table (Historical)
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     student_id INTEGER,
                     month TEXT NOT NULL,
                     is_paid INTEGER DEFAULT 0,
                     FOREIGN KEY(student_id) REFERENCES students(id))''')
                     
        # Operators Table (Auth)
        c.execute('''CREATE TABLE IF NOT EXISTS operators (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE NOT NULL,
                     password TEXT NOT NULL, 
                     role TEXT DEFAULT 'operator'
                     )''')
                     
        # Migration: Add role column if missing (for existing DBs)
        try:
            c.execute("PRAGMA table_info(operators)")
            columns = [info[1] for info in c.fetchall()]
            if 'role' not in columns:
                print("Migrating: Adding role column to operators table...")
                c.execute("ALTER TABLE operators ADD COLUMN role TEXT DEFAULT 'operator'")
        except Exception as e: print(f"Migration Error (Operators): {e}")
                     
        # Bills Table Handling
        c.execute("PRAGMA table_info(bills)")
        cols = [r[1] for r in c.fetchall()]
        # If table exists but lacks 'details' (our new schema), rename it
        if cols and 'details' not in cols:
            print("Legacy bills table detected. Archiving...")
            c.execute(f"ALTER TABLE bills RENAME TO bills_legacy_{int(datetime.datetime.now().timestamp())}")
        
        # Create New Bills Table
        c.execute('''CREATE TABLE IF NOT EXISTS bills (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     bill_no TEXT UNIQUE,
                     date TEXT,
                     operator_id INTEGER,
                     amount REAL,
                     details TEXT,
                     payment_mode TEXT
                     )''')

                     # Student Transactions Table (For Payment History)
        c.execute('''CREATE TABLE IF NOT EXISTS student_transactions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     student_id INTEGER,
                     amount REAL,
                     date TEXT,
                     mode TEXT,
                     type TEXT,
                     remarks TEXT,
                     FOREIGN KEY(student_id) REFERENCES students(id)
                     )''')
                     
        # Migration: Ensure 'amount' and 'payment_mode' columns exist
        try:
            c.execute("PRAGMA table_info(bills)")
            bill_cols = [info[1] for info in c.fetchall()]
            if 'amount' not in bill_cols:
                print("Migrating: Adding amount column to bills table...")
                c.execute("ALTER TABLE bills ADD COLUMN amount REAL DEFAULT 0")
            if 'payment_mode' not in bill_cols:
                print("Migrating: Adding payment_mode column to bills table...")
                c.execute("ALTER TABLE bills ADD COLUMN payment_mode TEXT DEFAULT 'Cash'")
                
            # Migration: Ensure 'type' in student_transactions
            c.execute("PRAGMA table_info(student_transactions)")
            trans_cols = [info[1] for info in c.fetchall()]
            if 'type' not in trans_cols:
                print("Migrating: Adding type column to student_transactions...")
                c.execute("ALTER TABLE student_transactions ADD COLUMN type TEXT DEFAULT 'Payment'")
            if 'remarks' not in trans_cols:
                print("Migrating: Adding remarks column to student_transactions...")
                c.execute("ALTER TABLE student_transactions ADD COLUMN remarks TEXT")
                
        except Exception as e: print(f"Migration Error (Bills/Trans): {e}")
        
        # Create Default Admin if not exists
        c.execute("SELECT id FROM operators WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO operators (username, password, role) VALUES (?, ?, ?)", 
                      ('admin', 'admin123', 'admin'))
            print("Created default admin user (admin/admin123)")

        # Create Default Operator if not exists
        c.execute("SELECT id FROM operators WHERE username='operator'")
        if not c.fetchone():
            c.execute("INSERT INTO operators (username, password, role) VALUES (?, ?, ?)", 
                      ('operator', 'pass123', 'operator'))
            print("Created default operator user (operator/pass123)")

        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Init DB Error: {e}")

# --- Routes ---

@app.route('/')
def index():
    return send_from_directory('static', 'login.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')

@app.route('/operator')
def operator_page():
    return send_from_directory('static', 'operator.html')

# --- API: Auth ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'operator')
    
    conn = get_db()
    c = conn.cursor()
    
    if role == 'admin':
        # Admin check
        c.execute("SELECT * FROM operators WHERE username=? AND role='admin'", (username,))
        user = c.fetchone()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['role'] = 'admin'
            return jsonify({'status': 'success', 'role': 'admin', 'username': username})
    else:
        # Operator check
        c.execute("SELECT * FROM operators WHERE username=? AND role='operator'", (username,))
        user = c.fetchone()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['role'] = 'operator'
            return jsonify({'status': 'success', 'role': 'operator', 'username': username, 'id': user['id']})
            
    conn.close()
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success'})

# --- API: Students ---
@app.route('/api/students', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_students():
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM students")
        rows = c.fetchall()
        # Get meal counts for today
        today = datetime.date.today().isoformat()
        students = []
        for row in rows:
            s_data = dict(row)
            c.execute("SELECT breakfast, lunch, dinner FROM meals WHERE student_id=? AND date=?", (s_data['id'], today))
            meal_row = c.fetchone()
            s_data['breakfast_count'] = meal_row['breakfast'] if meal_row else 0
            s_data['lunch_count'] = meal_row['lunch'] if meal_row else 0
            s_data['dinner_count'] = meal_row['dinner'] if meal_row else 0
            # Ensure safe defaults if column is null
            s_data['remaining_amount'] = s_data.get('remaining_amount') or 0
            students.append(s_data)
        conn.close()
        return jsonify(students)

    if request.method == 'POST':
        data = request.json
        try:
            # Custom Sequential ID Logic (Reuse gaps)
            c.execute("SELECT id FROM students ORDER BY id ASC")
            existing_ids = [row['id'] for row in c.fetchall()]
            
            new_id = 1
            for current_id in existing_ids:
                if current_id == new_id:
                    new_id += 1
                else:
                    break
            
            # Insert with explicit ID
            c.execute("INSERT INTO students (id, name, roll, dept, phone, payment_status, payment_mode, amount_paid, remaining_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (new_id, data['name'], data.get('roll',''), data.get('dept',''), data.get('phone',''), 
                       data.get('payment_status','Unpaid'), data.get('payment_mode','Cash'), data.get('amount_paid', 0), data.get('remaining_amount', 0)))
            conn.commit()
            return jsonify({'status': 'success', 'id': new_id})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Roll number already exists'}), 409
        finally:
            conn.close()

    if request.method == 'PUT':
        data = request.json
        c.execute("UPDATE students SET name=?, roll=?, dept=?, phone=?, payment_status=?, payment_mode=?, amount_paid=?, remaining_amount=? WHERE id=?",
                  (data['name'], data.get('roll'), data.get('dept'), data.get('phone'), 
                   data.get('payment_status'), data.get('payment_mode'), data.get('amount_paid'), data.get('remaining_amount'), data['id']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})

    if request.method == 'DELETE':
        std_id = request.args.get('id')
        c.execute("DELETE FROM students WHERE id=?", (std_id,))
        c.execute("DELETE FROM meals WHERE student_id=?", (std_id,))
        c.execute("DELETE FROM payments WHERE student_id=?", (std_id,))
        c.execute("DELETE FROM student_transactions WHERE student_id=?", (std_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})

@app.route('/api/students/pay', methods=['POST'])
def pay_student_fees():
    data = request.json
    s_id = data.get('student_id')
    amount = float(data.get('amount', 0))
    mode = data.get('mode', 'Cash')
    remarks = data.get('remarks', '')
    
    if not s_id or amount <= 0:
        return jsonify({'error': 'Invalid Id or Amount'}), 400
        
    conn = get_db()
    c = conn.cursor()
    try:
        # 1. Update Student Debt
        c.execute("SELECT remaining_amount, amount_paid FROM students WHERE id=?", (s_id,))
        row = c.fetchone()
        if not row: return jsonify({'error': 'Student not found'}), 404
        
        new_remaining = (row['remaining_amount'] or 0) - amount
        new_paid = (row['amount_paid'] or 0) + amount
        
        c.execute("UPDATE students SET remaining_amount=?, amount_paid=? WHERE id=?", (new_remaining, new_paid, s_id))
        
        # 1.1 Update Payment Status
        new_status = 'Unpaid'
        if new_remaining <= 0:
            new_status = 'Paid'
        elif new_paid > 0:
            new_status = 'Partial' 
            
        c.execute("UPDATE students SET payment_status=? WHERE id=?", (new_status, s_id))

        # 2. Record Transaction
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO student_transactions (student_id, amount, date, mode, remarks) VALUES (?, ?, ?, ?, ?)",
                  (s_id, amount, date_str, mode, remarks))
                  
        conn.commit()
        return jsonify({'status': 'success', 'new_remaining': new_remaining, 'new_status': new_status})
    except Exception as e:
        print(f"Payment Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# --- API: Operators ---
@app.route('/api/operators', methods=['GET', 'POST', 'DELETE'])
def manage_operators():
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM operators WHERE role='operator'")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(rows)

    if request.method == 'POST':
        data = request.json
        try:
            c.execute("INSERT INTO operators (username, password, role) VALUES (?, ?, 'operator')",
                      (data['username'], data['password']))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username exists'}), 409

    if request.method == 'DELETE':
        op_id = request.args.get('id')
        c.execute("DELETE FROM operators WHERE id=? AND role='operator'", (op_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})

# --- API: Billing ---
@app.route('/api/bill', methods=['POST'])
def create_bill():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    bill_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save bill
    details = json.dumps({
        'user_type': data.get('user_type'),
        'student_id': data.get('student_id'),
        'guest_name': data.get('guest_name'),
        'meal_type': data.get('meal_type')
    })
    
    try:
        c.execute("INSERT INTO bills (bill_no, date, operator_id, amount, details, payment_mode) VALUES (?, ?, ?, ?, ?, ?)",
                  (bill_no, date_str, data.get('operator_id'), data.get('amount'), details, data.get('payment_mode')))
        
        # If student, record meal
        if data.get('user_type') == 'hostel' and data.get('student_id'):
            s_id = data.get('student_id')
            today = datetime.date.today().isoformat()
            meal_type = data.get('meal_type').lower() # breakfast, lunch, dinner
            
            # Check if valid meal type column
            if meal_type in ['breakfast', 'lunch', 'dinner']:
                 # Upsert meal
                c.execute("SELECT id FROM meals WHERE student_id=? AND date=?", (s_id, today))
                row = c.fetchone()
                if row:
                    c.execute(f"UPDATE meals SET {meal_type}=1 WHERE id=?", (row[0],))
                else:
                    vals = {'breakfast':0, 'lunch':0, 'dinner':0}
                    vals[meal_type] = 1
                    c.execute("INSERT INTO meals (student_id, date, breakfast, lunch, dinner) VALUES (?, ?, ?, ?, ?)",
                              (s_id, today, vals['breakfast'], vals['lunch'], vals['dinner']))

            # Handle 'Account' Payment (Credit/Debt)
            if data.get('payment_mode') == 'Account':
                # Increase remaining_amount (Debt)
                c.execute("UPDATE students SET remaining_amount = remaining_amount + ? WHERE id=?", 
                          (data.get('amount'), s_id))
                
                # Log Transaction
                c.execute("INSERT INTO student_transactions (student_id, amount, date, mode, type, remarks) VALUES (?, ?, ?, ?, ?, ?)",
                          (s_id, data.get('amount'), date_str, 'Account', 'Food', f"Meal: {data.get('meal_type')}"))

        conn.commit()
        return jsonify({'status': 'success', 'bill_no': bill_no})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/bill-view/<bill_no>')
def view_bill(bill_no):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bills WHERE bill_no=?", (bill_no,))
    row = c.fetchone()
    conn.close()
    
    if not row: return "Bill not found", 404
    
    details = json.loads(row['details'])
    
    html = f"""
    <html>
    <head>
        <title>Bill {bill_no}</title>
        <style>
            @page {{ size: auto; margin: 0; }}
            body {{ font-family: 'Courier New', monospace; padding: 5px; margin: 0; width: 100%; }}
            .bill-box {{ width: 100%; max-width: 280px; margin: 0 auto; padding: 5px; border: none; }}
            h2 {{ text-align: center; font-size: 1.2em; margin: 5px 0; }}
            .meta {{ text-align: center; font-size: 0.8em; margin-bottom: 5px; }}
            .line {{ display: flex; justify-content: space-between; margin: 2px 0; font-size: 0.9em; }}
            .total {{ border-top: 2px dashed #000; border-bottom: 2px dashed #000; font-weight: bold; margin-top: 5px; padding: 5px 0; font-size: 1.1em; }}
            .footer {{ text-align: center; margin-top: 10px; font-size: 0.7em; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="bill-box">
            <h2>CANTEEN RECEIPT</h2>
            <div class="meta">
                Date: {row['date']}<br>
                Bill No: {bill_no}
            </div>
            <hr>
            <div class="line"><span>Item:</span> <span>{details.get('meal_type', 'Meal')}</span></div>
            <div class="line"><span>Type:</span> <span>{details.get('user_type')}</span></div>
            {f'<div class="line"><span>Name:</span> <span>{details.get("guest_name", "N/A")}</span></div>' if details.get('guest_name') else ''}
            {f'<div class="line"><span>Student ID:</span> <span>{details.get("student_id")}</span></div>' if details.get('student_id') else ''}
            
            <div class="line total"><span>TOTAL:</span> <span>₹{row['amount']}</span></div>
            <div class="line"><span>Mode:</span> <span>{row['payment_mode']}</span></div>
            
            <div class="footer">Thank you! Visit Again.</div>
        </div>
    </body>
    </html>
    """
    return html

# --- API: Reports ---
@app.route('/api/reports/meals')
def get_meal_report():
    conn = get_db()
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    
    # Fetch all bills for today to aggregate stats manually (covers all user types)
    c.execute("SELECT details, amount FROM bills WHERE date LIKE ?", (today + '%',))
    daily_bills = c.fetchall()
    
    counts = {'Breakfast': 0, 'Lunch': 0, 'Dinner': 0}
    total_revenue = 0.0
    
    for b in daily_bills:
        # Revenue
        total_revenue += b['amount'] if b['amount'] else 0
        
        # Meal Count
        try:
            if b['details']:
                d = json.loads(b['details'])
                m_type = d.get('meal_type')
                # Handle Case Sensitivity or exact match (Frontend sends Title Case)
                if m_type in counts:
                    counts[m_type] += 1
        except Exception as e:
            print(f"Stats Parse Error: {e}")
            
    conn.close()
    
    return jsonify({
        'Breakfast': counts['Breakfast'],
        'Lunch': counts['Lunch'],
        'Dinner': counts['Dinner'],
        'revenue': total_revenue
    })

@app.route('/api/reports/student/<int:student_id>')
def get_student_report(student_id):
    conn = get_db()
    c = conn.cursor()
    
    # 1. Student Details
    c.execute("SELECT * FROM students WHERE id=?", (student_id,))
    student = c.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': 'Student not found'}), 404
        
    student_data = dict(student)
    
    # 2. Meal History
    c.execute("SELECT date, breakfast, lunch, dinner FROM meals WHERE student_id=? ORDER BY date DESC", (student_id,))
    meals = [dict(row) for row in c.fetchall()]
    
    # 3. Transaction History (from bills table for now where student_id is recorded)
    #    We extract amount and mode. 
    #    Note: 'bills' stores JSON details. We can filter by details like '%"student_id": "123"%' or do param binding if we structured it better.
    #    For now, scanning rows is inefficient but acceptable for small scale. 
    #    Or better: we have a student_id in details JSON. SQL LIKE is tricky for JSON.
    #    However, we are not storing student_id as a column in bills, only operator_id.
    #    Wait! The 'bills' table doesn't have student_id column, only details JSON.
    #    Let's use Python to filter for this student (inefficient but safe for now) OR rely on a future migration.
    #    Actually current 'bills' schema: id, bill_no, date, operator_id, amount, details, payment_mode.
    
    c.execute("SELECT * FROM bills ORDER BY date DESC")
    all_bills = c.fetchall()
    
    # Combined Transactions List
    transactions = []
    
    # Add Bills (Type: Debit/Food)
    for b in all_bills:
        try:
            d = json.loads(b['details'])
            if str(d.get('student_id')) == str(student_id):
                transactions.append({
                    'type': 'Food',
                    'date': b['date'],
                    'item': d.get('meal_type', 'N/A'),
                    'amount': b['amount'],
                    'mode': b['payment_mode'],
                    'color': 'red' # Debt increases (or paid immediately but shows consumption)
                })
        except: pass
        
    # Add Payments (Type: Credit)
    c.execute("SELECT * FROM student_transactions WHERE student_id=? ORDER BY date DESC", (student_id,))
    payments = [dict(row) for row in c.fetchall()]
    for p in payments:
        transactions.append({
            'id': p['id'],
            'type': p.get('type', 'Payment'),
            'date': p['date'],
            'item': p.get('remarks') or 'Fee Payment', # Use remarks if available
            'amount': p['amount'],
            'mode': p['mode'],
            'color': 'green' # Debt decreases
        })
        
    # Sort combined list by date desc
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    conn.close()
    
    return jsonify({
        'student': student_data,
        'meals': meals,
        'transactions': transactions
    })

@app.route('/api/transactions', methods=['DELETE'])
def delete_transaction():
    t_id = request.args.get('id')
    if not t_id: return jsonify({'error': 'Missing ID'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # 1. Fetch Transaction
        c.execute("SELECT * FROM student_transactions WHERE id=?", (t_id,))
        row = c.fetchone()
        if not row: return jsonify({'error': 'Transaction not found'}), 404
        tx = dict(row)
        
        # 2. Validation (Only allow deleting Payments for now, or careful handling of Food)
        # We only safe delete 'Payment' types to reverse debt. 
        # If we delete 'Food' (account), we need to reduce debt.
        
        s_id = tx['student_id']
        amount = tx['amount']
        type_ = tx.get('type', 'Payment')
        
        # 3. Reverse Balance
        c.execute("SELECT remaining_amount, amount_paid FROM students WHERE id=?", (s_id,))
        student = c.fetchone()
        if not student: return jsonify({'error': 'Student not found'}), 404
        
        curr_remaining = student['remaining_amount'] or 0
        curr_paid = student['amount_paid'] or 0
        
        if type_ == 'Payment':
            # It was a payment (reduced debt). Reversing it means:
            # Increase Debt (Remaining)
            # Decrease Amount Paid
            new_remaining = curr_remaining + amount
            new_paid = curr_paid - amount
        elif type_ == 'Food':
            # It was a food charge (increased debt). Reversing it means:
            # Decrease Debt
            # Amount Paid unaffected
            new_remaining = curr_remaining - amount
            new_paid = curr_paid
        else:
            # Fallback if type is missing (legacy) - assume Payment if it's in this table and not food?
            # Safest to assume Payment if we stick to the UI button only appearing for Payments
            new_remaining = curr_remaining + amount
            new_paid = curr_paid - amount

        # 4. Update Student
        # Recalculate status
        new_status = 'Unpaid'
        if new_remaining <= 0:
            new_status = 'Paid'
        elif new_paid > 0:
            new_status = 'Partial'
            
        c.execute("UPDATE students SET remaining_amount=?, amount_paid=?, payment_status=? WHERE id=?", 
                  (new_remaining, new_paid, new_status, s_id))
        
        # 5. Delete Transaction
        c.execute("DELETE FROM student_transactions WHERE id=?", (t_id,))
        conn.commit()
        
        return jsonify({'status': 'success', 'message': 'Transaction reversed'})
        
    except Exception as e:
        print(f"Delete Tx Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/export')
def export_data():
    conn = get_db()
    c = conn.cursor()
    
    export_type = request.args.get('type', 'all')
    
    if export_type == 'daily':
        today = datetime.date.today().isoformat()
        c.execute("SELECT * FROM bills WHERE date LIKE ? ORDER BY date DESC", (today + '%',))
    else:
        c.execute("SELECT * FROM bills ORDER BY date DESC")
        
    rows = c.fetchall()
    
    # BOM for Excel compatibility with UTF-8
    # Added separate Date and Time columns
    output = "\ufeffBill No,Date,Time,Name,Student ID,Meal Type,Amount,Mode,User Type\n"
    
    for row in rows:
        try:
            d = json.loads(row['details'])
            name = d.get('guest_name', 'N/A')
            sid = d.get('student_id', '-')
            meal = d.get('meal_type', '-')
            utype = d.get('user_type', '-')
            
            # Sanitize CSV fields
            name = str(name).replace(',', ' ')
            meal = str(meal).replace(',', ' ')
            
            # Split Date and Time (Assumes format YYYY-MM-DD HH:MM:SS)
            full_date = row['date']
            try:
                date_part, time_part = full_date.split(' ')
            except:
                date_part, time_part = full_date, ''

            # Format Bill No as text for Excel (prepend tab)
            bill_no = f"\t{row['bill_no']}"
            
            output += f"{bill_no},{date_part},{time_part},{name},{sid},{meal},{row['amount']},{row['payment_mode']},{utype}\n"
        except Exception as e:
            output += f"\t{row['bill_no']},{row['date']},,Error Parsing Details,-,-,{row['amount']},{row['payment_mode']},Error\n"
    
    conn.close()
    
    from flask import Response
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=daily_report_{datetime.date.today()}.csv"}
    )

# --- API: Backup ---
@app.route('/api/backup/excel', methods=['POST'])
def backup_excel_api():
    try:
        from backup_excel import update_excel_sheet
        if update_excel_sheet():
            return jsonify({'status': 'success', 'message': 'Excel updated successfully.'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update Excel.'}), 500
    except Exception as e:
        print(f"Backup Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Initialize DB (Global - runs on gunicorn worker start)
# Initialize DB (Global - runs on gunicorn worker start)
if os.environ.get('FLASK_ENV') != 'testing':
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    print(f"Starting Flask Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
