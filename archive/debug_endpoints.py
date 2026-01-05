import os
import usb.core
import usb.util

# Fix for Windows DLL loading
if os.name == 'nt' and hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(os.getcwd())
    except Exception:
        pass

# Find device
dev = usb.core.find(idVendor=0x0471, idProduct=0x0055)

if dev is None:
    print("Device not found")
else:
    print("Device Found!")
    for cfg in dev:
        print(f"Configuration {cfg.bConfigurationValue}")
        for intf in cfg:
            print(f"  Interface {intf.bInterfaceNumber}, Alt {intf.bAlternateSetting}")
            for ep in intf:
                print(f"    Endpoint Address: 0x{ep.bEndpointAddress:02x}")
                print(f"    Attributes: 0x{ep.bmAttributes:02x}")
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    print("      (OUT Endpoint)")
                else:
                    print("      (IN Endpoint)")
