import calibrate
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


def create_data_folders(experiment_name, materials, num_trials):

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
    calibrate.main()
    Harvard_Port = initialize_devices()
    Harvard_Serial = harvard_control(Harvard_Port, BAUD_RATE=115200)
    return Harvard_Serial

def save_trial_parameters(experiment_path):
    now = datetime.now()
    parameters_path_txt = os.path.join(experiment_path, f"Data_Parameters.txt")
    try:
        with open(parameters_path_txt, "w") as f:
    
            f.write(f"Trial Date: {now.strftime("%m_%d %H-%M-%S")}\n")
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

    data_path_csv = os.path.join(trial_folder, f"Data_{trial_number}.csv")
    
    
    try:
        with open(data_path_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Pump Time (s)", "Volume (mL)", "State"])
            writer.writerows(trial_data)
        print(f"Saved data log: {data_path_csv}")


    except Exception as e:
        print(f"Error saving data for Trial {trial_number}: {e}")


def run_experiment(N_TRIALS):
    Harvard_Serial = initial_setup()
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
        stop_video_event, video_thread = start_video_recording(trial + 1, trial_folder)
        time.sleep(DELAY_CAMERA_BOOT)

        send_cmd(Harvard_Serial, HARVARD_INFUSE_RUN)


        infusion_complete = False
        withdrawing = False
        last_status_time = 0

        while True:
            response = Harvard_Serial.readline().decode('ascii', errors='ignore').strip()
            if response:
                print("Pump response:", response)
                if HARVARD_TARGET_REACHED in response:
                    infusion_complete = True

            last_status_time = poll_pump_status(Harvard_Serial, trial_data, last_status_time)

            if infusion_complete:
                withdrawing = set_target_withdraw(Harvard_Serial)
                break
            time.sleep(0.1)

        while withdrawing:
            response = Harvard_Serial.readline().decode('ascii', errors='ignore').strip()
            if response:
                print("Pump response:", response)
                if HARVARD_TARGET_REACHED in response:
                    withdrawing = False
                    break

            last_status_time = poll_pump_status(Harvard_Serial, trial_data, last_status_time)

            time.sleep(0.1)

        stop_video_event.set()
        video_thread.join()

        save_trial_data(trial_folder, trial + 1, trial_data)

    Harvard_Serial.close()
    print("\n=== All trials complete ===")



check_syringe_limits()
calculate_flow_rates()
run_experiment(N_TRIALS)
