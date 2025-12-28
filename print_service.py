import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from escpos.printer import Usb, Dummy

# --- Configuration ---
# USB Printer Vendor ID and Product ID (Decimal or Hex)
# Common EPSON/generic values often found: VID=0x04b8, PID=0x0e15 (adjust as needed)
PRINTER_VID = 0x0416  # Example: Zijiang / Generic
PRINTER_PID = 0x5011  # Example
# To find your VID/PID, run "lsusb" on Linux or use Device Manager on Windows.

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_printer():
    """Attempt to connect to USB printer. Fallback to Dummy if failed."""
    try:
        # 0x81 is the typical OUT endpoint, 0x03 is typical wIndex/Interface
        # However, python-escpos usually auto-detects endpoints if VID/PID are correct.
        p = Usb(PRINTER_VID, PRINTER_PID, profile="TM-T88V")
        return p, "USB"
    except Exception as e:
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
        
        # Header
        p.set(bold=True, double_height=True, double_width=True)
        p.text("COLLEGE CANTEEN\n")
        p.set(bold=False, double_height=False, double_width=False, align='center')
        p.text("Delicious & Fresh\n")
        p.text("--------------------------------\n")
        
        # Bill Info
        p.set(align='left')
        p.text(f"Bill No: {data.get('bill_no', 'N/A')}\n")
        p.text(f"Date:    {data.get('date', 'N/A')}\n")
        p.text(f"Op:      {data.get('operator', 'Unknown')}\n")
        if 'customer' in data:
            cust = data['customer']
            p.text(f"Cust:    {cust.get('name', 'Guest')}\n")
            if cust.get('type'):
                p.text(f"Type:    {cust.get('type')}\n")
        
        p.text("--------------------------------\n")
        
        # Items Header
        # Assuming 32 chars width (standard for 58mm/80mm usually wider but safe for both)
        # Item (20) Qty(4) Price(7)
        p.text("{:<18} {:>4} {:>8}\n".format("Item", "Qty", "Price"))
        p.text("--------------------------------\n")
        
        # Items Body
        items = data.get('items', [])
        for item in items:
            name = item.get('name', 'Item')[:18] # Truncate to 18 chars
            qty = item.get('qty', 1)
            price = item.get('price', 0)
            p.text("{:<18} {:>4} {:>8.2f}\n".format(name, qty, float(price)))
            
        p.text("--------------------------------\n")
        
        # Total
        total = data.get('total', 0)
        p.set(align='right', bold=True)
        p.text(f"Total: Rs. {total}\n")
        p.set(bold=False)
        
        # Footer
        p.set(align='center')
        p.text("--------------------------------\n")
        p.text("Thank you! Visit Again.\n")
        p.text("\n\n")
        
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
