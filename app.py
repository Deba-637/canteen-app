from flask import Flask, request, jsonify, send_file, send_from_directory
try:
    import sqlite3
except ImportError:
    sqlite3 = None
    print("WARNING: sqlite3 module not found. DB features will fail.")
import os
import datetime
import csv
import io
import hashlib

app = Flask(__name__, static_folder='static', static_url_path='')

# Railway Persistent Storage: Use /app/data if available
if os.path.exists('/app/data'):
    DB_FILE = '/app/data/canteen.db'
else:
    DB_FILE = 'canteen.db'

def get_db_connection():
    if sqlite3 is None:
        raise Exception("sqlite3 module is missing on this server.")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 breakfast_count INTEGER DEFAULT 0,
                 lunch_count INTEGER DEFAULT 0,
                 dinner_count INTEGER DEFAULT 0,
                 payment_status TEXT DEFAULT 'Unpaid',
                 payment_mode TEXT DEFAULT 'Cash'
                 )''')
    
    # Operators Table
    c.execute('''CREATE TABLE IF NOT EXISTS operators (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL
                 )''')

    # Bills Table
    c.execute('''CREATE TABLE IF NOT EXISTS bills (
                 bill_no INTEGER PRIMARY KEY AUTOINCREMENT,
                 date_time TEXT NOT NULL,
                 user_type TEXT NOT NULL,
                 student_id INTEGER,
                 guest_name TEXT,
                 meal_type TEXT NOT NULL,
                 amount REAL,
                 payment_mode TEXT NOT NULL,
                 operator_id INTEGER
                 )''')

    # Seed Default Data
    # Default Admin (Conceptual, handled by frontend logic or simple auth)
    # Default Operator
    c.execute("SELECT count(*) FROM operators")
    if c.fetchone()[0] == 0:
        # Default operator: user/pass
        c.execute("INSERT INTO operators (username, password) VALUES (?, ?)", ('operator', 'pass123'))
    
    conn.commit()
    conn.close()
    print("Database initialized.")

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

@app.route('/bill-view/<int:bill_id>')
def bill_view(bill_id):
    return send_from_directory('static', 'bill.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON data"}), 400
            
        role = data.get('role')
        username = data.get('username')
        password = data.get('password')

        if role == 'admin':
            # Hardcoded Admin for simplicity as requested
            if username == 'admin' and password == 'admin123':
                return jsonify({"status": "success", "role": "admin"})
            else:
                return jsonify({"status": "error", "message": "Invalid Admin Credentials"}), 401
        
        elif role == 'operator':
            try:
                init_db() # Ensure DB exists (lazy init)
            except: 
                pass 

            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM operators WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            conn.close()
            
            if user:
                return jsonify({"status": "success", "role": "operator", "id": user['id'], "username": user['username']})
            else:
                return jsonify({"status": "error", "message": "Invalid Operator Credentials"}), 401

        return jsonify({"status": "error", "message": "Invalid Role"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Login server error"}), 500

# --- Student Management (Admin) ---

@app.route('/api/students', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_students():
    conn = get_db_connection()
    if request.method == 'GET':
        students = conn.execute('SELECT * FROM students ORDER BY id').fetchall()
        conn.close()
        return jsonify([dict(row) for row in students])
    
    elif request.method == 'POST':
        data = request.json
        try:
            # Calculate next sequential ID
            curr_cursor = conn.execute('SELECT id FROM students ORDER BY id ASC')
            existing_ids = [row[0] for row in curr_cursor.fetchall()]
            
            new_id = 1
            for existing_id in existing_ids:
                if new_id < existing_id:
                    break
                new_id += 1
            
            # Roll No
            roll = data.get('roll')
            if not roll:
                import time
                roll = f"R-{int(time.time())}"
            dept = data.get('dept', 'General')
            
            conn.execute('INSERT INTO students (id, name, roll, dept, payment_status, payment_mode, amount_paid) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (new_id, data['name'], roll, dept, data['payment_status'], data['payment_mode'], data.get('amount_paid', 0)))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "id": new_id})
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    elif request.method == 'PUT':
        data = request.json
        try:
            student_id = data.get('id')
            if not student_id:
                conn.close()
                return jsonify({"status": "error", "message": "Missing Student ID"}), 400
            
            conn.execute('''UPDATE students SET 
                            name=?, roll=?, dept=?, payment_status=?, payment_mode=?, amount_paid=?
                            WHERE id=?''', 
                         (data['name'], data.get('roll'), data.get('dept'), 
                          data['payment_status'], data['payment_mode'], data.get('amount_paid', 0),
                          student_id))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    elif request.method == 'DELETE':
        student_id = request.args.get('id')
        conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})

# --- Operator Management (Admin) ---

@app.route('/api/operators', methods=['GET', 'POST', 'DELETE'])
def manage_operators():
    conn = get_db_connection()
    if request.method == 'GET':
        operators = conn.execute('SELECT id, username FROM operators').fetchall()
        conn.close()
        return jsonify([dict(row) for row in operators])

    elif request.method == 'POST':
        data = request.json
        try:
            conn.execute('INSERT INTO operators (username, password) VALUES (?, ?)',
                         (data['username'], data['password']))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
        except Exception as e:
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500
            
    elif request.method == 'DELETE':
        op_id = request.args.get('id')
        conn.execute('DELETE FROM operators WHERE id = ?', (op_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})

# --- Billing (Operator) ---

@app.route('/api/bill', methods=['POST'])
def create_bill():
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Insert Bill
        c.execute('''INSERT INTO bills (date_time, user_type, student_id, guest_name, meal_type, amount, payment_mode, operator_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   data['user_type'],
                   data.get('student_id'),
                   data.get('guest_name'),
                   data['meal_type'],
                   data['amount'],
                   data['payment_mode'],
                   data['operator_id']))
        
        bill_no = c.lastrowid
        
        # Update Student Meal Count if Hosteler
        if data['user_type'] == 'hostel' and data.get('student_id'):
            meal_col = f"{data['meal_type'].lower()}_count"
            if meal_col in ['breakfast_count', 'lunch_count', 'dinner_count']:
                c.execute(f"UPDATE students SET {meal_col} = {meal_col} + 1 WHERE id = ?", (data['student_id'],))

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "bill_no": bill_no})

    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bills/<int:bill_id>', methods=['GET'])
def get_bill(bill_id):
    conn = get_db_connection()
    bill = conn.execute('''
        SELECT bills.*, students.name as student_name 
        FROM bills 
        LEFT JOIN students ON bills.student_id = students.id 
        WHERE bills.bill_no = ?
    ''', (bill_id,)).fetchone()
    conn.close()
    if bill:
        return jsonify(dict(bill))
    else:
        return jsonify({"status": "error", "message": "Bill not found"}), 404

@app.route('/api/reports/meals', methods=['GET'])
def get_meal_stats():
    # Only for today
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    
    # Query bills for today
    rows = conn.execute(f"SELECT meal_type, count(*) as count FROM bills WHERE date_time LIKE '{today}%' GROUP BY meal_type").fetchall()
    
    stats = {"Breakfast": 0, "Lunch": 0, "Dinner": 0}
    for row in rows:
        m_type = row['meal_type']
        if m_type.capitalize() in stats:
            stats[m_type.capitalize()] = row['count']
            
    conn.close()
    return jsonify(stats)

# --- CSV Export (Admin) ---

@app.route('/api/export', methods=['GET'])
def export_bills():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills")
    rows = cursor.fetchall()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([i[0] for i in cursor.description])
    
    # Data
    writer.writerows(rows)
    
    output.seek(0)
    conn.close()
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'bills_export_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
    )

# Initialize DB on startup (ensures tables exist for Gunicorn)
# Removed global init to prevent boot crash. Will init lazily in routes as needed.

if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)
