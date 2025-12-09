import time
import serial

# -------------------------------
# Serial Cleaning Helper
# -------------------------------
def clear_serial_buffers(ser):
    """Flush input and output buffers for a clean communication state."""
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception as e:
        print(f"⚠️ Failed to clear buffers: {e}")


# -------------------------------
# Communication Test
# -------------------------------
def test_pump_status(ser):
    """
    Sends 'status' and returns the clean response.
    Returns None if pump does not reply.
    """
    try:
        ser.write(b"status\r\n")
        time.sleep(0.1)
        resp = ser.readline().decode("ascii", errors="ignore").strip()
        return resp if resp else None
    except Exception as e:
        print(f"⚠️ Error testing pump status: {e}")
        return None


# -------------------------------
# Main Reset Function
# -------------------------------
def reset_harvard_pump(ser):
    """
    Safely reset the Harvard PHD Ultra pump when it becomes unresponsive.

    Actions performed:
    1. Flush serial buffers
    2. Stop pump
    3. Clear target time + volume
    4. Reload Quick Start Infuse/Withdraw mode
    5. Flush buffers again
    6. Confirm pump is responding to 'status'
    """
    print("\n=== 🔧 Resetting Harvard Pump ===")

    # Step 1: clean buffers
    clear_serial_buffers(ser)

    # Step 2: send STOP (ignored if idle)
    print("→ Sending STOP")
    ser.write(b"stop\r\n")
    time.sleep(0.1)

    # Step 3: clear targets
    print("→ Clearing target volume/time")
    ser.write(b"ctvolume\r\n")
    ser.write(b"cttime\r\n")
    time.sleep(0.1)

    # Step 4: reload fresh Quick Start IW mode
    print("→ Loading Quick Start Infuse/Withdraw mode")
    ser.write(b"load qs iw\r\n")
    time.sleep(0.2)

    # Step 5: clear buffers again
    clear_serial_buffers(ser)

    # Step 6: verify pump is alive
    print("→ Testing communication...")
    resp = test_pump_status(ser)

    if resp is None:
        print("❌ Pump did NOT respond. A manual power cycle may be required.")
        return False

    print(f"✅ Pump responded successfully: {resp}")
    return True


# -------------------------------
# Optional: Standalone Test Mode
# -------------------------------
if __name__ == "__main__":
    print("Opening COM4 for Harvard Pump reset test...")

    try:
        ser = serial.Serial(
            port="COM7",
            baudrate=115200,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS,
            timeout=1
        )
    except Exception as e:
        print(f"❌ Could not open COM port: {e}")
        raise SystemExit

    reset_harvard_pump(ser)
    ser.close()
    print("Done.")
