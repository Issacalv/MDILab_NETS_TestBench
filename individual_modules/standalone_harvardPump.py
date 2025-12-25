import serial
import time
import sys

'''

GPT Generated

Change variable HARVARD_COM_PORT = "COM4"
to actual COMport if needed

'''

# ================================================================
#  SERIAL SETUP — REQUIRED FOR HARVARD PHD ULTRA
# ================================================================
def open_harvard_port(port="COM4"):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS,
            timeout=1
        )
        print(f"✅ Connected to Harvard pump on {port}")
        return ser
    except Exception as e:
        print(f"❌ Could not open {port}: {e}")
        sys.exit(1)


# ================================================================
# SEND COMMAND (safe wrapper)
# ================================================================
def send_cmd(ser, cmd):
    """Send a command and print pump response."""
    full = (cmd + "\r\n").encode("ascii")
    ser.write(full)
    time.sleep(0.05)

    responses = []
    while True:
        line = ser.readline().decode("ascii", errors="ignore").strip()
        if not line:
            break
        responses.append(line)

    if responses:
        for r in responses:
            print(f"Pump → {r}")
    else:
        print("Pump → (no response)")

    return responses


# ================================================================
#  PUMP RESET (in case it freezes or ignores commands)
# ================================================================
def reset_pump(ser):
    print("\n=== 🔧 Resetting Harvard Pump ===")
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except:
        pass

    send_cmd(ser, "stop")
    send_cmd(ser, "ctvolume")
    send_cmd(ser, "cttime")
    send_cmd(ser, "load qs iw")

    # Test communication
    print("Testing status…")
    resp = send_cmd(ser, "status")

    if not resp:
        print("⚠️ Pump did not respond — manual power cycle may be needed.")
    else:
        print("✅ Pump reset complete.\n")


# ================================================================
#  SIMPLE TIMED MOVEMENT FUNCTIONS
# ================================================================
def pulse_run(ser, seconds=1.0):
    """Simulate pressing RUN for a short time."""
    print(f"▶️ RUN for {seconds}s")
    send_cmd(ser, "run")
    time.sleep(seconds)
    send_cmd(ser, "stop")


def pulse_infuse(ser, seconds=1.0):
    print(f"💧 Infusing for {seconds}s")
    send_cmd(ser, "irun")
    time.sleep(seconds)
    send_cmd(ser, "stop")


def pulse_withdraw(ser, seconds=1.0):
    print(f"⬅️ Withdrawing for {seconds}s")
    send_cmd(ser, "wrun")
    time.sleep(seconds)
    send_cmd(ser, "stop")


# ================================================================
#  INTERACTIVE MANUAL CONTROL CONSOLE
# ================================================================
def manual_console(ser):
    print("""
=========================================================
      🟦 HARVARD PHD ULTRA — MANUAL CONTROL MODE 🟦
=========================================================
Controls:
   I → Infuse 1 second
   W → Withdraw 1 second
   R → Run (current direction) 1 second
   S → STOP immediately
   T → Show status
   X → Reset pump (stop, clear targets, reload QS)
   Q → Quit
=========================================================
""")

    while True:
        cmd = input("Enter command: ").strip().lower()

        if cmd == "i":
            pulse_infuse(ser, 1)

        elif cmd == "w":
            pulse_withdraw(ser, 1)

        elif cmd == "r":
            pulse_run(ser, 1)

        elif cmd == "s":
            send_cmd(ser, "stop")

        elif cmd == "t":
            send_cmd(ser, "status")

        elif cmd == "x":
            reset_pump(ser)

        elif cmd == "q":
            print("Exiting manual control.")
            break

        else:
            print("Unknown command. Use I, W, R, S, T, X, or Q.")


# ================================================================
#  MAIN ENTRY POINT
# ================================================================
if __name__ == "__main__":
    HARVARD_COM_PORT = "COM4"
    ser = open_harvard_port(HARVARD_COM_PORT)

    print("Clearing buffers…")
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except:
        pass

    # Optional: send an initial STOP
    send_cmd(ser, "stop")

    # Launch manual console
    manual_console(ser)

    ser.close()
    print("Serial port closed.")
