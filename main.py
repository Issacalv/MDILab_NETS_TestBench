from calibrate import camera_calibration_main
from serial_connection import initialize_devices
from harvard_aparatus import harvard_control
from record_video import start_video_recording
import threading
import time
import os
from datetime import datetime
import csv
from experiment_parameters import *
from harvard_aparatus import *
from pressure_sensor import latest_pressure, pressure_thread




def create_data_folders(experiment_name, materials, num_trials):
    """
    Creates a structured directory hierarchy for storing experiment data.

    Each run is organized by date and timestamp, containing subfolders for each trial.

    Args:
        experiment_name (str): Name of the experiment (e.g., "AirTest").
        materials (str): Type of material tested (e.g., "EcoFlex20").
        num_trials (int): Number of experimental trials to create folders for.

    Returns:
        str: Path to the main experiment folder where all trial folders are created.
    """

    now = datetime.now()
    date_folder = now.strftime("%m-%d")
    time_stamp = now.strftime("%H-%M-%S")
    
    base_path = os.path.join(os.getcwd(), DATA_FOLDER_NAME)
    os.makedirs(base_path, exist_ok=True)

    date_path = os.path.join(base_path, date_folder)
    os.makedirs(date_path, exist_ok=True)

    experiment_folder = f"{experiment_name}_{materials}_{time_stamp}"
    experiment_path = os.path.join(date_path, experiment_folder)
    os.makedirs(experiment_path, exist_ok=True)

    for i in range(1, num_trials + 1):
        trial_folder = os.path.join(experiment_path, f"Trial_{i}")
        os.makedirs(trial_folder, exist_ok=True)

    print(f"Created data folders under:\n{experiment_path}")
    return experiment_path

def initial_setup():
    """
    Performs initial setup of the experiment system, including camera calibration 
    and serial connection to the Harvard syringe pump.

    Runs camera calibration using the calibration module, 
    scans available COM ports, and initializes serial communication.

    Returns:
        serial.Serial: An active serial connection object to the Harvard pump.
    """
    camera_calibration_main()
    Harvard_Port = initialize_devices()
    Harvard_Serial = harvard_control(Harvard_Port, BAUD_RATE=115200)
    return Harvard_Serial

def save_trial_parameters(experiment_path):
    """
    Saves experiment configuration parameters (e.g., syringe size, flow rates, materials)
    to a text file within the experiment folder.

    Args:
        experiment_path (str): Path to the current experiment's directory.

    Notes:
        This helps document all relevant conditions for each experimental run.
        If an error occurs during file writing, it prints an error message.
    """

    now = datetime.now()
    parameters_path_txt = os.path.join(experiment_path, f"Data_Parameters.txt")
    try:
        with open(parameters_path_txt, "w") as f:
    
            f.write(f"Trial Date: {now.strftime('%m_%d %H-%M-%S')}\n")
            f.write(f"Number of Trials: {N_TRIALS}\n")
            f.write(f"Experiment Type: {EXPERIMENT_TYPE}\n")
            f.write(f"Material Type: {MATERIAL_TYPE}\n")
            f.write(f"\n")
            f.write(f"Syringe Diameter (mm): {SYRINGE_DIAMETER_MM}\n")
            f.write(f"Syringe Volume ({SYRINGE_VOLUME_UNIT}): {SYRINGE_VOLUME}\n")
            f.write("\n")
            f.write(f"Target Volume Infuse ({TARGET_VOLUME_INFUSE_UNIT}): {TARGET_VOLUME_INFUSE}\n")
            f.write(f"Infuse Rate ({INFUSION_RATE_UNIT}): {INFUSION_RATE}")
            f.write("\n")
            f.write(f"Target Volume Withdraw ({TARGET_VOLUME_WITHDRAW_UNIT}): {TARGET_VOLUME_WITHDRAW}\n")
            f.write(f"Withdraw Rate ({WITHDRAW_RATE_UNIT}): {WITHDRAW_RATE}")
    except Exception as e:
        print(f"Error saving parameters for Trial")
    

def save_trial_data(trial_folder, trial_number, trial_data):
    """
    Saves collected pump data (time, volume, and state) from a single trial into a CSV file.

    Args:
        trial_folder (str): Folder path where the trial data should be saved.
        trial_number (int): The current trial number (for filename labeling).
        trial_data (list[tuple]): List of tuples containing pump data 
            in the form (time_seconds, volume_mL, state).

    Notes:
        Each CSV file is labeled as Data_<trial_number>.csv.
        If an error occurs during saving, an error message is printed.
    """


    data_path_csv = os.path.join(trial_folder, f"Data_{trial_number}.csv")
    
    
    try:
        with open(data_path_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp (s)",
                "Pump Volume (mL)",
                "Pump State",
                "Pressure (PSI)",
                "Pressure (mmHg)"
            ])

            writer.writerows(trial_data)
        print(f"Saved data log: {data_path_csv}")


    except Exception as e:
        print(f"Error saving data for Trial {trial_number}: {e}")


def run_experiment(N_TRIALS):
    """
    Coordinates the full experimental workflow for the given number of trials.

    Performs pump initialization, video recording, infusion and withdrawal control, 
    and data logging for each trial. Automatically creates folders and saves results.
    """

    Harvard_Serial = initial_setup()

    # Start pressure monitoring thread
    pressure_stop_event = threading.Event()
    threading.Thread(
        target=pressure_thread,
        args=(pressure_stop_event,),
        daemon=True
    ).start()

    print("Pressure sensor thread started.")

    experiment_path = create_data_folders(EXPERIMENT_TYPE, MATERIAL_TYPE, N_TRIALS)
    save_trial_parameters(experiment_path)
    set_machine_params(Harvard_Serial)

    for trial in range(N_TRIALS):
        print(f"\n=== Starting Trial {trial + 1}/{N_TRIALS} ===")

        send_cmd(Harvard_Serial, HARVARD_STOP)
        send_cmd(Harvard_Serial, HARVARD_QUICK_START_IW)
        set_target_infused(Harvard_Serial)

        trial_data = []
        trial_folder = os.path.join(experiment_path, f"Trial_{trial + 1}")

        # Start video recording thread
        stop_video_event, camera_ready_event, video_thread = start_video_recording(
            trial + 1,
            trial_folder
        )
        camera_ready_event.wait()  # Ensure camera is fully booted

        send_cmd(Harvard_Serial, HARVARD_INFUSE_RUN)

        infusion_complete = False
        withdrawing = False
        last_status_time = 0  # timestamp when pump was last polled

        # -------------------------------
        #        INFUSION LOOP
        # -------------------------------
        while True:
            response = Harvard_Serial.readline().decode("ascii", errors="ignore").strip()
            if response:
                print("Pump response:", response)
                if HARVARD_TARGET_REACHED in response:
                    infusion_complete = True

            # Pump status polling
            t_s, vol_mL, pump_state, last_status_time = poll_pump_status(
                Harvard_Serial, last_status_time
            )

            if t_s is not None:
                # Read current pressure
                pressure_psi = latest_pressure["psi"]
                pressure_mmhg = latest_pressure["mmhg"]

                # Unified row appended
                trial_data.append((
                    t_s,
                    vol_mL,
                    pump_state,
                    pressure_psi,
                    pressure_mmhg
                ))

            if infusion_complete:
                withdrawing = set_target_withdraw(Harvard_Serial)
                break

            time.sleep(0.1)

        # -------------------------------
        #       WITHDRAWAL LOOP
        # -------------------------------
        while withdrawing:
            response = Harvard_Serial.readline().decode("ascii", errors="ignore").strip()
            if response:
                print("Pump response:", response)
                if HARVARD_TARGET_REACHED in response:
                    withdrawing = False
                    break

            # Poll pump
            t_s, vol_mL, pump_state, last_status_time = poll_pump_status(
                Harvard_Serial, last_status_time
            )

            if t_s is not None:
                pressure_psi = latest_pressure["psi"]
                pressure_mmhg = latest_pressure["mmhg"]

                trial_data.append((
                    t_s,
                    vol_mL,
                    pump_state,
                    pressure_psi,
                    pressure_mmhg
                ))

            time.sleep(0.1)

        # Stop video thread for this trial
        stop_video_event.set()
        video_thread.join()

        # Save unified pump+pressure data
        save_trial_data(trial_folder, trial + 1, trial_data)

    # Stop pressure thread
    pressure_stop_event.set()

    Harvard_Serial.close()
    print("\n=== All trials complete ===")


def main():
    """
    Main entry point of the program.

    Validates syringe parameters and flow rate safety before 
    starting the experiment run sequence.
    """

    check_syringe_limits()
    calculate_flow_rates()
    run_experiment(N_TRIALS)


if __name__ == "__main__":
    main()
