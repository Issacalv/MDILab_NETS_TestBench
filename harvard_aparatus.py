"""
==========================
 PHD Ultra Pump Commands
==========================

System / Setup:
- address [0–99]        → Set/display pump address (0=master, others=slaves)
- ascale [1–100]        → Set/display analog scaling (% of max speed)
- baud [rate]           → Set baud rate (9600 … 921600)
- nvram none            → Disable NVRAM writes (recommended for PC control)
- dim [0–100]           → Set backlight brightness
- ver / version         → Show firmware and device info

Run Control (Quick Start mode only):
- irun                  → Infuse (forward run)
- wrun                  → Withdraw (reverse run)
- rrun                  → Run opposite direction
- run                   → Simulate Run button press
- stop / stp            → Stop pump immediately

Syringe Setup (Quick Start mode only):
- diameter {mm}         → Set syringe diameter in mm
- svolume {vol} {ul|ml} → Set syringe volume
- syrm {code}           → Select syringe manufacturer (hm1, bdp, etc.)
- gang {#}              → Number of syringes in gang

Rates (Quick Start mode only):
- irate {rate} {units}  → Set infusion rate (e.g. 2.5 ml/min)
- wrate {rate} {units}  → Set withdrawal rate
- crate                 → Display current motor rate
- iramp ...             → Infusion ramp (start→end over time)
- wramp ...             → Withdrawal ramp

Volumes:
- tvolume {vol}{unit}   → Set target volume
- ivolume               → Show infused volume
- wvolume               → Show withdrawn volume
- civolume / cwvolume   → Clear infused / withdrawn volume
- cvolume               → Clear both volumes

Times:
- ttime {seconds}       → Set target time
- itime                 → Show infused time
- wtime                 → Show withdrawn time
- citime / cwtime       → Clear infused / withdrawn time
- ctime                 → Clear both times

Digital I/O:
- input                 → Read trigger input (High/Low)
- output {1|2} {hi/lo}  → Set digital output
- sync {high|low}       → Set sync port
- valve {on|off|auto}   → Control valve state

Computer Control:
- lock [on|name]        → Enter satellite (PC control) mode
- unlock                → Exit satellite mode
- load [method/qs]      → Load method or Quick Start
- status                → Raw pump status (rate, time, vol, flags)

Prompts (pump responses):
- ":"  → Idle
- ">"  → Infusing
- "<"  → Withdrawing
- "*"  → Stalled
- "T*" → Target reached

==========================
"""
from experiment_parameters import TARGET_VOLUME_INFUSE, TARGET_VOLUME_INFUSE_UNIT, TARGET_VOLUME_WITHDRAW, TARGET_VOLUME_WITHDRAW_UNIT, INFUSION_PAUSE, SYRINGE_DIAMETER_MM, SYRINGE_VOLUME, SYRINGE_VOLUME_UNIT, INFUSION_RATE, INFUSION_RATE_UNIT, WITHDRAW_RATE, WITHDRAW_RATE_UNIT
import serial
import time

# --- Harvard Apparatus Pump Command Definitions ---
# --- Do NOT modify ----

HARVARD_STOP = "stop"  
# Immediately stops the pump operation (equivalent to pressing the STOP button).

HARVARD_QUICK_START_IW = "load qs iw"  
# Loads the "Quick Start Infuse/Withdraw" method on the pump.

HARVARD_CLEAR_TARGET_TIME = "cttime"  
# Clears any previously set target run time on the pump.

HARVARD_CLEAR_TARGET_VOLUME = "ctvolume"  
# Clears any previously set target volume (resets volume tracking).

HARVARD_SET_TARGET_VOLUME_INFUSE = f"tvolume {TARGET_VOLUME_INFUSE} {TARGET_VOLUME_INFUSE_UNIT}"  
# Sets the infusion target volume (how much to infuse before stopping).

HARVARD_SET_TARGET_VOLUME_WITHDRAW = f"tvolume {TARGET_VOLUME_WITHDRAW} {TARGET_VOLUME_WITHDRAW_UNIT}"  
# Sets the withdrawal target volume (how much to withdraw before stopping).

HARVARD_INFUSE_RUN = "irun"  
# Starts infusion (forward motion of the syringe plunger).

HARVARD_WITHDRAW_RUN = "wrun"  
# Starts withdrawal (reverse motion of the syringe plunger).

HARVARD_SYRINGE_SET_DIAMETER = f"diameter {SYRINGE_DIAMETER_MM}"  
# Configures the syringe diameter in millimeters — required for volume calculations.

HARVARD_SYRINGE_SET_VOLUME = f"svolume {SYRINGE_VOLUME} {SYRINGE_VOLUME_UNIT}"  
# Sets the syringe’s total volume and unit (e.g., 60 mL).

HARVARD_SET_INFUSION_RATE = f"irate {INFUSION_RATE} {INFUSION_RATE_UNIT}"  
# Sets the infusion (forward) flow rate and its unit (e.g., 126 mL/min).

HARVARD_SET_WITHDRAW_RATE = f"wrate {WITHDRAW_RATE} {WITHDRAW_RATE_UNIT}"  
# Sets the withdrawal (reverse) flow rate and its unit (e.g., 126 mL/min).

HARVARD_TARGET_REACHED = "T*"  
# Response flag from the pump indicating that the set target volume or time has been reached.

# --- Pump Status Flags ---
INFUSION_FLAG_LIST = ["I", "i"]  
# Identifies infusion states in the pump’s status string.

WITHDRAW_FLAG_LIST = ["W", "w"]  
# Identifies withdrawal states in the pump’s status string.


def harvard_control(COM_PORT = None, BAUD_RATE = None):
    if COM_PORT is None:
        raise ValueError("COM not set")

    if BAUD_RATE is None:
        raise ValueError("BAUD_RATE not set")
    
    ser = serial.Serial(
        port=COM_PORT,
        baudrate=BAUD_RATE,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.SEVENBITS,
        timeout=1
    )

    if ser.isOpen() is False:
        raise OSError("Serial Monitor could not be opened")
    else:
        print("Serial port opened successfully")

    return ser


def send_cmd(ser, command: str):
    """Send command to pump and print response"""
    ser.write((command + '\r\n').encode('ascii'))
    print(f"Sent command: {command}")

    time.sleep(0.02) 

    while True:
        response = ser.readline().decode('ascii', errors='ignore').strip()
        if not response:
            break
        print("Pump response:", response)


def set_machine_params(HarvardSerial):
    send_cmd(HarvardSerial, HARVARD_SYRINGE_SET_DIAMETER)
    send_cmd(HarvardSerial, HARVARD_SYRINGE_SET_VOLUME)

    send_cmd(HarvardSerial, HARVARD_SET_INFUSION_RATE)
    send_cmd(HarvardSerial, HARVARD_SET_WITHDRAW_RATE)
    return None


def set_target_infused(HarvardSerial):
    send_cmd(HarvardSerial, HARVARD_CLEAR_TARGET_TIME)
    send_cmd(HarvardSerial, HARVARD_CLEAR_TARGET_VOLUME)
    send_cmd(HarvardSerial, HARVARD_SET_TARGET_VOLUME_INFUSE)
    return None


def set_target_withdraw(Harvard_Serial):
    send_cmd(Harvard_Serial, HARVARD_STOP)
    time.sleep(INFUSION_PAUSE)
    send_cmd(Harvard_Serial, HARVARD_CLEAR_TARGET_TIME)
    send_cmd(Harvard_Serial, HARVARD_CLEAR_TARGET_VOLUME)
    send_cmd(Harvard_Serial, HARVARD_SET_TARGET_VOLUME_WITHDRAW)
    print("Starting withdrawal...")
    send_cmd(Harvard_Serial, HARVARD_WITHDRAW_RUN)
    
    withdrawing = True 
    return withdrawing

def poll_pump_status(Harvard_Serial, last_status_time, interval=1.0):
    """
    Polls the Harvard pump for status at a controlled interval.

    Returns:
        (timestamp, volume_mL, pump_state, new_last_status_time)
        OR
        (None, None, None, last_status_time)
    """

    now = time.time()

    # Too early to poll again
    if now - last_status_time < interval:
        return None, None, None, last_status_time

    # Poll pump
    send_cmd(Harvard_Serial, "status")
    time.sleep(0.1)

    status_resp = Harvard_Serial.readline().decode("ascii", errors="ignore").strip()

    new_last_time = now  # update regardless of success

    if not status_resp:
        return None, None, None, new_last_time

    print("Status:", status_resp)

    t_s, vol_mL, state = parse_status_line(status_resp)

    if t_s is None:
        return None, None, None, new_last_time

    return t_s, vol_mL, state, new_last_time



    
def parse_status_line(status_line):
    parts = status_line.split()
    if len(parts) < 4:
        return None, None, None

    try:
        rate_fL_s = float(parts[0])
        time_ms = float(parts[1])
        volume_fL = float(parts[2])
        flags = parts[3]

        time_s = time_ms / 1000.0
        volume_mL = round(volume_fL / 1e12, 3)

        first_flag = flags[0] if flags else ""
        if first_flag in INFUSION_FLAG_LIST:
            state = "I"
        elif first_flag in WITHDRAW_FLAG_LIST:
            state = "W"
        else:
            state = "Idle"

        return time_s, volume_mL, state
    except ValueError:
        return None, None, None
    
