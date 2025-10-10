def normalize_strings(string):
    return string.strip().lower()

SYRINGE_DIAMETER_MM = 29.2
SYRINGE_VOLUME = 60
SYRINGE_VOLUME_UNIT = normalize_strings("ml")

TARGET_VOLUME_INFUSE = 60
TARGET_VOLUME_INFUSE_UNIT = normalize_strings("ml")
INFUSION_RATE = 126
INFUSION_RATE_UNIT = normalize_strings("ml/min")

TARGET_VOLUME_WITHDRAW = 60
TARGET_VOLUME_WITHDRAW_UNIT = normalize_strings("ml")
WITHDRAW_RATE = 126
WITHDRAW_RATE_UNIT = normalize_strings("ml/min")


DATA_FOLDER_NAME = "Data"
EXPERIMENT_TYPE = "AirTest"
MATERIAL_TYPE = "EcoFlex20"
N_TRIALS = 1


DELAY_CAMERA_BOOT = 3      # Wait before starting pump after video starts
INFUSION_PAUSE = 1         # Pause before switching from infuse -> withdraw

def check_syringe_limits():

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
