import time
import board
import analogio
import os
os.environ["BLINKA_MCP2221"] = "1"

# Initialize ADC once
adc = analogio.AnalogIn(board.G3)

# Sensor parameters
PSI_RANGE = 5
VOLTAGE_MIN = 0.5
VOLTAGE_MAX = 4.5

# Shared pressure state
latest_pressure = {
    "raw": 0,
    "voltage": 0,
    "psi": 0,
    "mmhg": 0
}

def _get_voltage(raw):
    return (raw / 65535) * 5.0


def read_pressure_once():
    raw = adc.value
    voltage = _get_voltage(raw)

    if voltage < VOLTAGE_MIN:
        pressure_psi = 0.0
    else:
        pressure_psi = ((voltage - VOLTAGE_MIN) /
                        (VOLTAGE_MAX - VOLTAGE_MIN)) * PSI_RANGE

    pressure_mmhg = pressure_psi * 51.7149

    return raw, voltage, pressure_psi, pressure_mmhg


def pressure_thread(stop_event):
    """Continuously update latest_pressure dict."""
    while not stop_event.is_set():
        raw, voltage, psi, mmhg = read_pressure_once()
        latest_pressure["raw"] = raw
        latest_pressure["voltage"] = voltage
        latest_pressure["psi"] = psi
        latest_pressure["mmhg"] = mmhg
        time.sleep(0.1)  # update rate
