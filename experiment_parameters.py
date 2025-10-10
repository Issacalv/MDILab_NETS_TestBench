def normalize_strings(string):
    """
    Normalizes a given string by stripping whitespace and converting it to lowercase.

    This ensures consistent formatting of user-defined units and parameter names
    (e.g., "ML", " ml ", "Ml" → "ml").

    Args:
        string (str): Input string to normalize.

    Returns:
        str: The normalized (lowercased, trimmed) string.
    """

    return string.strip().lower()

# --- Syringe Configuration ---
SYRINGE_DIAMETER_MM = 29.2          # Inner diameter of the syringe in millimeters
SYRINGE_VOLUME = 60                 # Total syringe capacity (numerical value)
SYRINGE_VOLUME_UNIT = normalize_strings("ml")   # Unit of syringe volume (L, mL, or µL)

# --- Infusion Settings ---
TARGET_VOLUME_INFUSE = 60           # Volume to infuse per trial
TARGET_VOLUME_INFUSE_UNIT = normalize_strings("ml")   # Unit for infusion target volume
INFUSION_RATE = 126                 # Flow rate during infusion
INFUSION_RATE_UNIT = normalize_strings("ml/min")      # Infusion rate units (L/min, mL/min, etc.)

# --- Withdrawal Settings ---
TARGET_VOLUME_WITHDRAW = 60         # Volume to withdraw per trial
TARGET_VOLUME_WITHDRAW_UNIT = normalize_strings("ml") # Unit for withdrawal target volume
WITHDRAW_RATE = 126                 # Flow rate during withdrawal
WITHDRAW_RATE_UNIT = normalize_strings("ml/min")      # Withdrawal rate units

# --- Experiment Metadata ---
DATA_FOLDER_NAME = "Data"           # Root directory for saving all experiment data
EXPERIMENT_TYPE = "AirTest"         # Label for the experiment (used in folder naming)
MATERIAL_TYPE = "EcoFlex20"         # Material being tested
N_TRIALS = 1                        # Number of experiment trials to perform

# --- Camera and Timing Settings ---
CAMERA_ID = 0                       # ID/index of the connected camera (0 = default)
DELAY_CAMERA_BOOT = 3               # Delay (in seconds) before starting the pump after video starts
INFUSION_PAUSE = 1                  # Pause (in seconds) between infusion and withdrawal phases


def check_syringe_limits():
    """
    Validates that syringe and target volume settings are physically consistent.

    Checks that all specified units are valid, that the target infusion and withdrawal
    volumes do not exceed the total syringe capacity, and that the units can be
    converted properly.

    Raises:
        ValueError: If any of the following conditions occur:
            - A volume unit is invalid or unsupported.
            - The infusion or withdrawal volume exceeds syringe capacity.
        Prints confirmation if all checks pass.

    Notes:
        This function should be called before starting an experiment to prevent
        hardware misuse or incorrect parameter settings.
    """


    unit_conversion = {"l":1000, "ml": 1, "ul": 0.001}
    allowed_units = ", ".join(unit_conversion.keys())

    if SYRINGE_VOLUME_UNIT not in unit_conversion:
        raise ValueError(f"Invalid syringe unit: {SYRINGE_VOLUME_UNIT}. Must be one of: {allowed_units}.")
    if TARGET_VOLUME_WITHDRAW_UNIT not in unit_conversion:
        raise ValueError(f"Invalid withdraw unit: {TARGET_VOLUME_WITHDRAW_UNIT}. Must be one of: {allowed_units}.")
    if TARGET_VOLUME_INFUSE_UNIT not in unit_conversion:
        raise ValueError(f"Invalid infuse unit: {TARGET_VOLUME_INFUSE_UNIT}. Must be one of: {allowed_units}.")

    syringe_volume_ml = SYRINGE_VOLUME * unit_conversion[SYRINGE_VOLUME_UNIT]
    withdraw_ml = TARGET_VOLUME_WITHDRAW * unit_conversion[TARGET_VOLUME_WITHDRAW_UNIT]
    infuse_ml = TARGET_VOLUME_INFUSE * unit_conversion[TARGET_VOLUME_INFUSE_UNIT]

    if withdraw_ml > syringe_volume_ml:
        raise ValueError(f"Withdraw volume {withdraw_ml} mL exceeds syringe capacity ({syringe_volume_ml} mL).")
    if infuse_ml > syringe_volume_ml:
        raise ValueError(f"Infuse volume {infuse_ml} mL exceeds syringe capacity ({syringe_volume_ml} mL).")

    print("Syringe configuration is valid.")


def calculate_flow_rates():
    """
    Calculates and validates flow rate limits based on syringe geometry.

    Uses reference syringe specifications to scale minimum and maximum
    flow rate limits, ensuring that the configured infusion and withdrawal
    rates are within safe and supported bounds.

    Raises:
        ValueError: If any of the following conditions occur:
            - An invalid flow rate unit is specified.
            - The syringe diameter is zero or negative.
            - The infusion or withdrawal rate exceeds or falls below allowed limits.

    Notes:
        - Reference values are based on the Harvard PHD Ultra pump specifications.
        - Adds a small buffer (`FLOW_BUFFER_ML_PER_MIN`) to prevent edge case errors.
    """

    SYRINGE_ID_REF = 14.427
    SYRINGE_MIN_RATE_REF = 30.0640
    SYRINGE_MIN_RATE_REF_UNIT = "nl/min"  # change to "ul/min" if needed
    SYRINGE_MAX_RATE_REF = 31.2204
    SYRINGE_MAX_RATE_REF_UNIT = "ml/min"

    # how much cushion around the valid range (mL/min)
    FLOW_BUFFER_ML_PER_MIN = 1.0

    # --- unit conversions to mL/min ---
    flow_unit_conversion = {
        "l/min": 1000.0,
        "ml/min": 1.0,
        "ul/min": 0.001,
        "nl/min": 0.000001,
    }

    # --- convert references to mL/min ---
    try:
        min_rate_ref_mlmin = SYRINGE_MIN_RATE_REF * flow_unit_conversion[SYRINGE_MIN_RATE_REF_UNIT]
        max_rate_ref_mlmin = SYRINGE_MAX_RATE_REF * flow_unit_conversion[SYRINGE_MAX_RATE_REF_UNIT]
    except KeyError as e:
        raise ValueError(f"Invalid flow unit: {e.args[0]}. Must be one of: {', '.join(flow_unit_conversion)}")

    # --- validate syringe diameter ---
    if SYRINGE_DIAMETER_MM <= 0:
        raise ValueError("Syringe diameter must be greater than zero.")

    # --- compute scaled limits ---
    scaling_factor = round((SYRINGE_DIAMETER_MM / SYRINGE_ID_REF) ** 2, 9)
    min_allowed_flowrate = (min_rate_ref_mlmin * scaling_factor) + FLOW_BUFFER_ML_PER_MIN
    max_allowed_flowrate = (max_rate_ref_mlmin * scaling_factor) - FLOW_BUFFER_ML_PER_MIN

    infusion_rate_mlmin = INFUSION_RATE * 1.0  # already in mL/min
    withdraw_rate_mlmin = WITHDRAW_RATE * 1.0

    # --- Flow-rate checks ---
    if infusion_rate_mlmin > max_allowed_flowrate:
        raise ValueError(
            f"Infusion rate ({infusion_rate_mlmin:.6f} mL/min) exceeds "
            f"max allowed ({max_allowed_flowrate:.6f} mL/min)."
        )
    if infusion_rate_mlmin < min_allowed_flowrate:
        raise ValueError(
            f"Infusion rate ({infusion_rate_mlmin:.6f} mL/min) below "
            f"min allowed ({min_allowed_flowrate:.6f} mL/min)."
        )
    if withdraw_rate_mlmin > max_allowed_flowrate:
        raise ValueError(
            f"Withdraw rate ({withdraw_rate_mlmin:.6f} mL/min) exceeds "
            f"max allowed ({max_allowed_flowrate:.6f} mL/min)."
        )
    if withdraw_rate_mlmin < min_allowed_flowrate:
        raise ValueError(
            f"Withdraw rate ({withdraw_rate_mlmin:.6f} mL/min) below "
            f"min allowed ({min_allowed_flowrate:.6f} mL/min)."
        )
