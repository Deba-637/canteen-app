import sqlite3
import openpyxl
from openpyxl.styles import Font
import os
import datetime

DB_FILE = 'canteen.db'
EXCEL_FILE = 'hostel_students.xlsx'

def update_excel_sheet():
    if not os.path.exists(DB_FILE):
        print("Database not found.")
        return False

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM students ORDER BY id ASC")
        rows = c.fetchall()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Hostel Students"
        
        # Headers
        headers = ['ID', 'Name', 'Regd No', 'Dept', 'Payment Status', 'Payment Mode', 'Amount Paid']
        ws.append(headers)
        
        # Style Headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            
        # Data
        for row in rows:
            ws.append([
                row['id'],
                row['name'],
                row['regd_no'],
                row['dept'],
                row['payment_status'],
                row['payment_mode'],
                row['amount_paid']
            ])
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Adjust column widths
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        wb.save(EXCEL_FILE)
        conn.close()
        print(f"Excel updated successfully at {timestamp}")
        return True
    except Exception as e:
        print(f"Error updating Excel: {e}")
        return False

if __name__ == "__main__":
    update_excel_sheet()
