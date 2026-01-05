import platform
import ctypes
import os
import usb.core

print(f"Python Architecture: {platform.architecture()}")
dll_path = os.path.abspath("libusb-1.0.dll")
print(f"Looking for DLL at: {dll_path}")

# 1. Try manual load
try:
    lib = ctypes.CDLL(dll_path)
    print("SUCCESS: Loaded DLL via ctypes directly.")
except Exception as e:
    print(f"FAIL: Could not load DLL via ctypes: {e}")

# 2. Configure Environment for PyUSB
os.environ['PATH'] = os.getcwd() + os.pathsep + os.environ['PATH']
if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(os.getcwd())
        print("Added current directory to DLL search path.")
    except Exception as e:
        print(f"Error adding DLL directory: {e}")

# 3. Try PyUSB Find
try:
    # Check for any backend match
    dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)
    if dev:
        print("SUCCESS: PyUSB found the specific device!")
    else:
        # Check if backend is even loaded
        import usb.backend.libusb1
        b = usb.backend.libusb1.get_backend()
        if b:
            print("SUCCESS: PyUSB loaded the backend, but device not found (Check Zadig/Connection).")
        else:
            print("FAIL: PyUSB could not load the backend.")
except Exception as e:
    print(f"FAIL: PyUSB Error: {e}")
