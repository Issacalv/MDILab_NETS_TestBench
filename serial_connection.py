import serial
import serial.tools.list_ports
from variables import *


def scan_COMports(DEVICE = None, PORT_NUMBER=None, HARDWARE_ID=None, MANUFACTURE_NAME=None):
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if str(port.device) == str(PORT_NUMBER):
            print(f"COM port located at {port.device}")
            return port.device
        elif str(port.hwid) == str(HARDWARE_ID):
            print(f"COM port located at {port.device}")
            return port.device
        elif MANUFACTURE_NAME and str(MANUFACTURE_NAME) in str(port.description):
            print(f"COM port located at {port.device}")
            return port.device
    print(f"""\nCould not locate the device "{DEVICE}" on any available COM port.

Troubleshooting steps:
1. Ensure the device is properly connected via USB/Serial cable.
2. Verify that the correct drivers are installed for your operating system.
3. Double-check that the expected COM port is visible in your system’s device manager.
4. If using PORT_NUMBER, confirm it matches exactly (e.g., 'COM3' on Windows).
5. If using hardware ID or manufacturer name, confirm those constants are correct.
6. Try disconnecting and reconnecting the device, then rerun this program.

Current variables (at least one needs to be populated):
    MANUFACTURE_NAME = {MANUFACTURE_NAME}
    HARDWARE_ID = {HARDWARE_ID}
    PORT_NUMBER = {PORT_NUMBER}

List of available devices:
""")
    for port in ports:
        print(f"  Port: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        print("-" * 20)

    raise OSError("Device not found. See troubleshooting output above.")


def initialize_devices():
    Harvard_Port = scan_COMports(DEVICE = "Harvard Aparatus", HARDWARE_ID = HARVARD_APARATUS_HARDWARE_ID, MANUFACTURE_NAME = HARVARD_APARATUS_DESCRIPTION)
    print(f"Harvard Aparatus Port: {Harvard_Port}")
    
    
    return Harvard_Port

