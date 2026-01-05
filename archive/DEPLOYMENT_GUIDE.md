# Complete Deployment Guide - Canteen System

Follow this step-by-step guide to set up the Canteen App and Silent Thermal Printer on a Windows computer.

## 1. Install Python
1.  Download Python (latest version) from [python.org](https://www.python.org/downloads/).
2.  Run the installer.
3.  **CRITICAL:** Check the box **"Add Python to PATH"** at the bottom before clicking Install.

## 2. Printer Driver Setup (One-Time)
Windows does not let Python talk to USB printers securely by default. You must replace the driver.
1.  **Connect Printer**: Plug in your USB Thermal Printer and turn it on.
2.  **Download Zadig**: Go to [zadig.akeo.ie](https://zadig.akeo.ie/) and download the tool.
3.  **Replace Driver**:
    -   Open Zadig.
    -   Go to **Options** -> **List All Devices**.
    -   Select your printer from the dropdown (might be named "USB Printing Support" or specific model).
    -   In the green arrow box, confirm the target driver is **WinUSB**.
    -   Click **"Replace Driver"** or **"Install WCID Driver"**.
4.  **Install Library**:
    -   The project folder (`canteen project`) must contain `libusb-1.0.dll`. (This has been done for you).

## 3. Project Initialization
1.  Open the `canteen project` folder.
2.  Double-click **`setup.bat`**.
    -   A black window will open and install necessary software.
    -   Wait for it to close or say "Setup Complete".

## 4. Verify Printer Configuration
1.  Open `print_service.py` (Right-click -> Edit with IDLE or Notepad).
2.  Ensure these lines match your printer:
    ```python
    PRINTER_VID = 0x0471
    PRINTER_PID = 0x0055
    PRINTER_EP_OUT = 0x02
    ```
    *(If you change printers, you must update these values).*

## 5. Create Desktop Shortcut
1.  Double-click the file **`create_shortcut.vbs`**.
2.  A message box will pop up saying "Shortcut created successfully".
3.  A shortcut named **"Canteen App"** will appear on your Desktop.

## 6. Daily Usage
1.  **Double-click "Canteen App"** on the Desktop.
2.  **Two Black Windows** will open:
    -   *Canteen Web Server*: Runs the website.
    -   *Canteen Print Service*: Talks to the printer.
    -   **DO NOT CLOSE THEM.** Minimize them to the taskbar.
3.  The Application will open in your default browser automatically.
4.  **Logins**:
    -   **Admin**: `admin` / `admin123`
    -   **Operator**: `operator` / `pass123`

## 7. Troubleshooting
-   **"Printer Service Unreachable"**:
    -   Make sure the "Canteen Print Service" black window is open.
    -   If the printer was unplugged, close the black window and double-click the Shortcut again.
-   **"Bill Saved but not printing"**:
    -   Check if the printer has paper and lid is closed.
    -   Check USB cable connection.

## 8. Backup
-   Copy `canteen.db` to a Pendrive or Google Drive regularly to back up student balances and transactions.

## 9. Bulk Student Import (Excel)
If you need to re-import students:
1.  Place your Excel file (`.xlsx`) in the Project folder.
2.  Rename it to `Name List for Canteen e-Recipts.xlsx` (or update `import_students.py`).
3.  **Run the Import Script**:
    -   Double-click `import_students.py` (if set to open with Python) OR
    -   Open CMD, type `python import_students.py`.
    -   **Warning**: This deletes all old data and imports fresh from the Excel file.
