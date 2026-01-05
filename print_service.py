import os
# Fix for Windows DLL loading (Python 3.8+)
if os.name == 'nt' and hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(os.getcwd())
    except Exception:
        pass

from flask import Flask, request, jsonify
from flask_cors import CORS
from escpos.printer import Usb, Dummy

# --- Configuration ---
# USB Printer Vendor ID and Product ID (Decimal or Hex)
# Common EPSON/generic values often found: VID=0x04b8, PID=0x0e15 (adjust as needed)
PRINTER_VID = 0x0471  # USB\VID_0471&PID_0055&REV_0100
PRINTER_PID = 0x0055
PRINTER_EP_OUT = 0x02 # Detected via debug_endpoints.py

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_printer():
    """Attempt to connect to USB printer. Fallback to Dummy if failed."""
    try:
        # Explicitly set the OUT endpoint to 0x02 as detected
        p = Usb(PRINTER_VID, PRINTER_PID, out_ep=PRINTER_EP_OUT, profile="TM-T88V")
        return p, "USB"
    except Exception as e:
        # Catching generic Exception covers usb.core.NoBackendError and others
        print(f"printer_error: Could not connect to USB printer ({PRINTER_VID:04x}:{PRINTER_PID:04x}). Using Dummy. Error: {e}")
        return Dummy(), "DUMMY"

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint."""
    return jsonify({"status": "running", "service": "Canteen Print Service"})

@app.route('/print', methods=['POST'])
def print_bill():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload provided"}), 400

    try:
        p, mode = get_printer()
        
        # --- RECEIPT LAYOUT ---
        # Initialize
        p.hw('INIT')
        p.set(align='center')
        
        # Header (Compacted)
        p.set(bold=True, double_height=True, double_width=True)
        p.text("GATE Central Canteen\n")
        p.set(bold=False, double_height=False, double_width=False, align='center')
        p.text("--------------------------------\n")
        
        # Bill Info (Compacted)
        p.set(align='left')
        # Combined Bill No and Date
        # Bill: 123456  Dt: 2026-01-03
        sys_date = data.get('date', 'N/A')
        date_short = sys_date[:10] if len(sys_date) >= 10 else sys_date
        bill_short = str(data.get('bill_no', 'N/A'))
        if len(bill_short) > 6: bill_short = bill_short[-6:]
        
        p.text(f"Bill: {bill_short}  Dt: {date_short}\n")
        
        if 'customer' in data:
            c = data['customer']
            c_name = c.get('name', 'Guest')[:15]
            c_id = c.get('id')
            if c_id:
                p.text(f"ID: {c_id}  Nm: {c_name}\n")
            else:
                p.text(f"Name: {c_name}\n")

        # Items (Small Font)
        p.set(font='b') 
        p.text("------------------------------------------\n")
        
        # Items Body (Multi-line)
        items = data.get('items', [])
        
        cust_type = ''
        if 'customer' in data and 'type' in data['customer']:
             cust_type = data['customer']['type'].lower()

        for item in items:
            name = item.get('name', 'Item')
            price = item.get('price', 0)
            
            p.text(f"Item: {name}\n")
            
            # Show Price only for normal customers
            if cust_type not in ['hostel', 'staff']:
                 p.text(f"Price: {float(price):.2f}\n")
            
            p.text("\n") # Spacing between items
            
        p.text("------------------------------------------\n")
        p.set(font='a') # Reset to normal
        
        # Total
        if cust_type not in ['hostel', 'staff']:
            total = data.get('total', 0)
            p.set(align='right', bold=True)
            p.text(f"Total: Rs. {total}\n")
            p.set(bold=False)
            
        p.text("\n\n") # Minimum for cutter
        
        # Cut
        p.cut()
        
        # If dummy, output to console for verification
        if mode == "DUMMY":
            print("--- VIRTUAL RECEIPT START ---")
            print(p.output.decode('utf-8', errors='ignore'))
            print("--- VIRTUAL RECEIPT END ---")
        else:
            p.close()

        return jsonify({"status": "success", "message": "Printed successfully", "mode": mode})

    except Exception as e:
        print(f"Print failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting Print Service on port 5001...")
    print("Ensure USB Printer is connected.")
    # Threaded=True to handle multiple requests if needed, though usually sequential
    app.run(host='0.0.0.0', port=5001, debug=True)
