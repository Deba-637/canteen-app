# Silent Thermal Printer Setup Guide

This system uses a **Local Python Service** to bypass the browser print dialog and print directly to your thermal printer.

## 1. Install Credentials
You need Python installed on your Windows machine.
Install the required libraries:

```powershell
pip install flask flask-cors python-escpos pyusb
```

## 2. Connect Your Printer
1. Connect your Thermal Printer via USB.
2. Ensure it is turned on and paper is loaded.
3. You may need to install the **Zadig** tool to replace the Windows driver with a Generic WinUSB driver so Python can talk to it directly.
    - Download Zadig: https://zadig.akeo.ie/
    - Open Zadig -> Options -> List All Devices.
    - Select your Printer (often shows as "Unknown" or "USB Printing Support").
    - Select "WinUSB" in the target box.
    - Click "Replace Driver" or "Install Driver".

## 3. Configure PID/VID (Optional)
If the printer is not detected automatically or falls back to "DUMMY" mode:
1. Find your Printer's Vendor ID (VID) and Product ID (PID) from Device Manager or Zadig.
2. Edit `print_service.py`:
   ```python
   PRINTER_VID = 0x0416  # Change these values
   PRINTER_PID = 0x5011
   ```

## 4. Run the Service
Run the following command in a terminal **and keep it open**:

```powershell
cd "c:\Users\deban\.gemini\antigravity\scratch\canteen project"
python print_service.py
```

You should see:
> Starting Print Service on port 5001...
> Ensure USB Printer is connected.

## 5. Test
1. Open the Operator Dashboard.
2. Make a bill.
3. Click **PRINT BILL**.
4. The button should show "Printing..." briefly.
5. Receipt should print instantly.

## Troubleshooting
- **"Bill Saved. Local Print Service is not running"**: Check if the python terminal is open and running.
- **"Printer Error"**: Check USB connection and Zadig driver installation.
- **Prints to Console (DUMMY)**: The service couldn't connect to USB, so it printed to the terminal window instead. Check VID/PID.
