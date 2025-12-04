import os
import pandas as pd
import matplotlib.pyplot as plt
from experiment_parameters import INFUSION_PAUSE

def fix_withdraw_volumes(df):
    inflate = df[df["Pump State"] == "I"]
    withdraw = df[df["Pump State"] == "W"]

    if inflate.empty or withdraw.empty:
        return df

    corrected = df.copy()

    # Fix Volume
    Vmax = inflate["Pump Volume (mL)"].iloc[-1]
    corrected.loc[withdraw.index, "Pump Volume (mL)"] = (
        Vmax - withdraw["Pump Volume (mL)"]
    )

    Tmax = inflate["Timestamp (s)"].iloc[-1]
    T0_W = withdraw["Timestamp (s)"].iloc[0]

    corrected.loc[withdraw.index, "Timestamp (s)"] = (
        Tmax + INFUSION_PAUSE + (withdraw["Timestamp (s)"] - T0_W)
    )

    num_cols = corrected.select_dtypes(include="number").columns
    corrected[num_cols] = corrected[num_cols].round(2)

    return corrected



# ============================================================
#                       PLOTTING
# ============================================================

def plot_pump_data(df, output_folder, prefix=""):
    os.makedirs(output_folder, exist_ok=True)

    df = df.rename(columns={
        "time": "Timestamp (s)",
        "angle": "Angle (deg)"
    })

    # Volume vs Time
    plt.figure(figsize=(10, 5))
    plt.plot(df["Timestamp (s)"], df["Pump Volume (mL)"], linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Volume (mL)")
    plt.title("Pump Volume vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_volume_vs_time.png"))
    plt.close()

    # Pressure vs Time
    plt.figure(figsize=(10, 5))
    plt.plot(df["Timestamp (s)"], df["Pressure (mmHg)"], linewidth=2)
    plt.xlabel("Time (s)")
    plt.ylabel("Pressure (mmHg)")
    plt.title("Pressure vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_pressure_vs_time.png"))
    plt.close()

    # Volume vs Time by State
    df_I = df[df["Pump State"] == "I"]
    df_W = df[df["Pump State"] == "W"]

    plt.figure(figsize=(10, 5))
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
    plt.figure(figsize=(6, 6))
    plt.scatter(df["Pump Volume (mL)"], df["Pressure (mmHg)"], s=35)
    plt.xlabel("Volume (mL)")
    plt.ylabel("Pressure (mmHg)")
    plt.title("Pressure vs Volume")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{prefix}_pressure_vs_volume.png"))
    plt.close()

    if "Angle (deg)" in df.columns:

        # Angle vs Time
        plt.figure(figsize=(10, 5))
        plt.plot(df["Timestamp (s)"], df["Angle (deg)"], linewidth=2)
        plt.xlabel("Time (s)")
        plt.ylabel("Angle (deg)")
        plt.title("Angle vs Time")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, f"{prefix}_angle_vs_time.png"))
        plt.close()

        # Angle vs Volume
        plt.figure(figsize=(6, 6))
        plt.scatter(df["Pump Volume (mL)"], df["Angle (deg)"], s=35)
        plt.xlabel("Volume (mL)")
        plt.ylabel("Angle (deg)")
        plt.title("Angle vs Volume")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, f"{prefix}_angle_vs_volume.png"))
        plt.close()

        # Angle vs Pressure
        plt.figure(figsize=(6, 6))
        plt.scatter(df["Pressure (mmHg)"], df["Angle (deg)"], s=35)
        plt.xlabel("Pressure (mmHg)")
        plt.ylabel("Angle (deg)")
        plt.title("Angle vs Pressure")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, f"{prefix}_angle_vs_pressure.png"))
        plt.close()

        # Angle vs Time by Pump State
        plt.figure(figsize=(10, 5))
        plt.plot(df_I["Timestamp (s)"], df_I["Angle (deg)"], label="Inflate", linewidth=2)
        plt.plot(df_W["Timestamp (s)"], df_W["Angle (deg)"], label="Withdraw", linewidth=2)
        plt.xlabel("Time (s)")
        plt.ylabel("Angle (deg)")
        plt.title("Angle vs Time by Pump State")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, f"{prefix}_angle_by_state.png"))
        plt.close()

def merge_pump_and_angle(trial_path, pump_csv_path, tolerance=0.05):
    """
    Merges pump data (Data_N_fixed.csv) with video angle data by nearest timestamp.
    """

    # Find angle CSV
    angle_csv = None
    for fname in os.listdir(trial_path):
        if fname.lower().endswith("_angles.csv"):
            angle_csv = os.path.join(trial_path, fname)
            break

    if angle_csv is None:
        print(f"[WARNING] No video angle CSV found in {trial_path}")
        return None

    df_pump = pd.read_csv(pump_csv_path)
    df_angle = pd.read_csv(angle_csv)

    df_pump = df_pump.rename(columns={"Timestamp (s)": "time"})

    video_start = df_angle["time"].iloc[0]
    pump_start = df_pump["time"].iloc[0]

    df_angle["time"] = df_angle["time"] - video_start + pump_start

    df_pump = df_pump.sort_values("time")
    df_angle = df_angle.sort_values("time")

    merged = pd.merge_asof(
        df_pump,
        df_angle,
        on="time",
        direction="nearest",
        tolerance=tolerance
    )

    out_path = os.path.join(
        trial_path,
        os.path.splitext(os.path.basename(pump_csv_path))[0] + "_with_angle.csv"
    )
    merged.to_csv(out_path, index=False)

    print(f"[SAVED] Pump + angle merged CSV:\n{out_path}")
    return out_path

def combine_experiment_trials(path_to_experiment_folder):

    trial_folders = sorted([
        f for f in os.listdir(path_to_experiment_folder)
        if f.lower().startswith("trial") and os.path.isdir(os.path.join(path_to_experiment_folder, f))
    ])

    if not trial_folders:
        print("No trial folders found!")
        return

    for trial_name in trial_folders:
        trial_path = os.path.join(path_to_experiment_folder, trial_name)

        pump_csv_files = [
            f for f in os.listdir(trial_path)
            if f.lower().startswith("data_")
            and f.lower().endswith(".csv")
            and "_angles" not in f
            and "_fixed" not in f
            and "_with_angle" not in f
        ]

        if not pump_csv_files:
            print(f"No pump CSV found in {trial_name}, skipping.")
            continue

        pump_csv_path = os.path.join(trial_path, pump_csv_files[0])
        print(f"\nProcessing: {pump_csv_path}")

        df_raw = pd.read_csv(pump_csv_path)

        df_fixed = fix_withdraw_volumes(df_raw)

        # Save fixed CSV
        base_name, ext = os.path.splitext(pump_csv_files[0])
        fixed_csv_path = os.path.join(trial_path, f"{base_name}_fixed{ext}")
        df_fixed.to_csv(fixed_csv_path, index=False)
        print(f"Saved fixed CSV: {fixed_csv_path}")

        # MERGE WITH ANGLE DATA FIRST
        merged_path = merge_pump_and_angle(trial_path, fixed_csv_path)
        if merged_path is not None:
            df_plot = pd.read_csv(merged_path)
        else:
            df_plot = df_fixed

        graphs_folder = os.path.join(trial_path, "Graphs")
        plot_pump_data(df_plot, graphs_folder, prefix=trial_name)

    print("\nAll trial processing complete.")
