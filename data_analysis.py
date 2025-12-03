import os
import pandas as pd
import matplotlib.pyplot as plt

def fix_withdraw_volumes(df):
    inflate = df[df["Pump State"] == "I"]
    withdraw = df[df["Pump State"] == "W"]

    if inflate.empty or withdraw.empty:
        return df

    corrected = df.copy()

    #Fix Volume
    Vmax = inflate["Pump Volume (mL)"].iloc[-1]
    corrected.loc[withdraw.index, "Pump Volume (mL)"] = (
        Vmax - withdraw["Pump Volume (mL)"]
    )

    #Fix time
    Tmax = inflate["Timestamp (s)"].iloc[-1]
    T0_W = withdraw["Timestamp (s)"].iloc[0]

    corrected.loc[withdraw.index, "Timestamp (s)"] = (
        Tmax + (withdraw["Timestamp (s)"] - T0_W)
    )

    #Round all numeric columns to 2 decimals
    num_cols = corrected.select_dtypes(include="number").columns
    corrected[num_cols] = corrected[num_cols].round(2)

    return corrected

def plot_pump_data(df, output_folder, prefix=""):
    """Generate 4 plots and save them to output_folder."""
    os.makedirs(output_folder, exist_ok=True)

    # Volume vs Time
    plt.figure(figsize=(10,5))
    plt.plot(df["Timestamp (s)"], df["Pump Volume (mL)"], linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Volume (mL)")
    plt.title("Pump Volume vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_volume_vs_time.png"))
    plt.close()

    # Pressure vs Time
    plt.figure(figsize=(10,5))
    plt.plot(df["Timestamp (s)"], df["Pressure (mmHg)"], linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Pressure (mmHg)")
    plt.title("Pressure vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_pressure_vs_time.png"))
    plt.close()

    # Volume vs Time by Pump State
    df_I = df[df["Pump State"] == "I"]
    df_W = df[df["Pump State"] == "W"]

    plt.figure(figsize=(10,5))
    plt.plot(df_I["Timestamp (s)"], df_I["Pump Volume (mL)"], label="Inflate", linewidth=2)
    plt.plot(df_W["Timestamp (s)"], df_W["Pump Volume (mL)"], label="Withdraw", linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Volume (mL)")
    plt.title("Volume vs Time by Pump State")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_volume_by_state.png"))
    plt.close()

    # Pressure vs Volume
    plt.figure(figsize=(6,6))
    plt.scatter(df["Pump Volume (mL)"], df["Pressure (mmHg)"], s=35)
    plt.xlabel("Volume (mL)")
    plt.ylabel("Pressure (mmHg)")
    plt.title("Pressure vs Volume")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_pressure_vs_volume.png"))
    plt.close()

def combine_experiment_trials(path_to_experiment_folder):
    """
    For each trial folder:
        - Finds the trial CSV automatically
        - Fixes time + volume
        - Saves Data_FIXED.csv
        - Saves 4 graphs

    Creates:
        Combined_Data_RAW.csv
        Combined_Data_FIXED.csv
    """

    trial_folders = sorted([
        f for f in os.listdir(path_to_experiment_folder)
        if f.lower().startswith("trial") and
           os.path.isdir(os.path.join(path_to_experiment_folder, f))
    ])

    if not trial_folders:
        print("No trial folders found!")
        return

    combined_raw_frames = []
    combined_fixed_frames = []

    # Loop through trial folders
    for trial_name in trial_folders:
        trial_path = os.path.join(path_to_experiment_folder, trial_name)

        # Dynamically find the CSV file (first CSV inside the trial folder)
        csv_files = [f for f in os.listdir(trial_path) if f.lower().endswith(".csv")]
        if not csv_files:
            print(f"No CSV found inside {trial_name}, skipping.")
            continue

        csv_path = os.path.join(trial_path, csv_files[0])
        print(f"Processing {csv_path}")

        # Load raw CSV
        df_raw = pd.read_csv(csv_path)
        df_raw["Trial"] = trial_name
        combined_raw_frames.append(df_raw)

        # Fix values
        df_fixed = fix_withdraw_volumes(df_raw)
        df_fixed["Trial"] = trial_name

        # Save fixed CSV
        # Dynamically create fixed CSV name
        base_name, ext = os.path.splitext(csv_files[0])
        fixed_csv_filename = f"{base_name}_fixed{ext}"
        fixed_csv_path = os.path.join(trial_path, fixed_csv_filename)

        # Save fixed CSV
        df_fixed.to_csv(fixed_csv_path, index=False)
        print(f"Saved fixed CSV: {fixed_csv_path}")

        # Save graphs for this trial
        graphs_folder = os.path.join(trial_path, "Graphs")
        plot_pump_data(df_fixed, graphs_folder, prefix=trial_name)
        print(f"Graphs saved for {trial_name}")

        combined_fixed_frames.append(df_fixed)

    # Combine all trials
    combined_raw = pd.concat(combined_raw_frames, ignore_index=True)
    combined_fixed = pd.concat(combined_fixed_frames, ignore_index=True)

    # Save combined datasets
    raw_out = os.path.join(path_to_experiment_folder, "Combined_Data_RAW.csv")
    fixed_out = os.path.join(path_to_experiment_folder, "Combined_Data_FIXED.csv")

    combined_raw.to_csv(raw_out, index=False)
    combined_fixed.to_csv(fixed_out, index=False)

    print("\nSaved combined CSV files:")
    print(f" - RAW Data:   {raw_out}")
    print(f" - FIXED Data: {fixed_out}")



