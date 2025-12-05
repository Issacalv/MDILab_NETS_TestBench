# 🧪 MDI_NETS_TestBench
## Harvard Apparatus Automation

Automated control and data logging system for the **Harvard PHD Ultra syringe pump**, with synchronized video recording, safety checks, and experiment management for MDI_NETS testing.

---

## 🚀 Features
- Automatically detects and connects to the Harvard PHD Ultra syringe pump  
- Calibrates and verifies syringe and flow rate limits for safety  
- Controls infusion and withdrawal cycles automatically  
- Records synchronized experiment videos via webcam  
- Logs pump status (time, volume, and direction) to CSV  
- Automatically organizes all experiment data into dated folders  
- Includes built-in camera calibration and lens correction tools  

---

## 🧰 Requirements

### Software
- Tested on **Python 3.13.10**  
  👉 [Download Python 3.13.10 (Windows 64-bit)](https://www.python.org/downloads/release/python-31310/)

- Recommended IDE: **VS Code**  
  👉 [Download Visual Studio Code](https://code.visualstudio.com)

- Version control: **Git**  
  👉 [Download Git for Windows](https://git-scm.com/install/windows)

- Works on **Windows 10/11**


### Hardware
- Harvard **PHD Ultra** syringe pump  
- Pressure Transducer  
- USB webcam  

---

## 🧱 Installation & Setup (in VS Code)

### Option A (Manual install)

1. Open a terminal (**Ctrl + `**) inside VS Code  

2. Search for desired directory to download repo (Example):

   ```bash
   cd Desktop/
   ```

3. **Clone or Download the Repository**
   ```bash
   git clone https://github.com/Issacalv/MDI_NETS_TestBench.git
   cd MDI_NETS_TestBench/
   ```

4. **Create a Python Virtual Environment**:

   - In this case, were downloading with python version 3.13 hence '-3.13'
   ```bash
   py -3.13 -m venv venv
   ```
   Activate the virtual environment:
   - **VS Code Terminal**
     ```bash
     venv\Scripts\activate
     ```

   **If activated properly, the terminal should go from**:
   ```bash
   C:\User\Name\Desktop\MDILab_NETS_TestBench
   ```

   **to**
   ```bash
   (venv) C:\User\Name\Desktop\MDILab_NETS_TestBench
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Connect Your Hardware**
   - Plug in the syringe pump and note its COM port (e.g., `COM3`).
   - Connect your USB webcam.  
   - Confirm both devices appear in Device Manager.

### Option B (Auto Install)

1. Open a terminal (**Ctrl + `**) inside VS Code  

2. Search for desired directory to download repo (Example):

   ```bash
   cd Desktop/
   ```

3. **Clone or Download the Repository**
   ```bash
   git clone https://github.com/Issacalv/MDI_NETS_TestBench.git
   cd MDI_NETS_TestBench/
   ```

4. **In the Terminal Run**
   ```bash
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

5. **Then run the auto installer file**

   ```bash
   .\AutoInstaller.ps1
   ```

6. **Connect Your Hardware**
   - Plug in the syringe pump and note its COM port (e.g., `COM3`).
   - Connect your USB webcam.  
   - Confirm both devices appear in Device Manager.

---

## ▶️ How to Run

1. **Open the Folder in VS Code**  
   - Click **File → Open Folder...**  
   - Choose your project folder  
   - Open a terminal (**Ctrl + `**) inside VS Code 
   - Ensure you're in your project folder:
      ```bash
      cd <Project Folder Path>
      ``` 
   - Activate environment
      ```bash
      .\venv\Scripts\activate
      ```

2. **Run the Main Script**
   ```bash
   python main.py
   ```
   The program will:
   - Run camera calibration if needed  
   - Detect and initialize the Harvard pump  
   - Start synchronized video recording  
   - Execute infusion → withdrawal cycles  
   - Save all experiment data in the `Data/` folder  

3. **View Output**
   - Pump logs → `Data/<date>/<experiment>/Trial_X/Data_X.csv`  
   - Parameter summary → `Data_Parameters.txt`  
   - Recorded videos → `Video_Trial_X.mp4`

---

## ⚙️ Customization

Modify **`experiment_parameters.py`** to configure your test setup:

```python
SYRINGE_DIAMETER_MM = 29.2      # Inner syringe diameter (mm)
SYRINGE_VOLUME = 60             # Syringe capacity
INFUSION_RATE = 126             # Infusion rate (mL/min)
WITHDRAW_RATE = 126             # Withdrawal rate (mL/min)
N_TRIALS = 3                    # Number of experiment repetitions
EXPERIMENT_TYPE = "AirTest"     # Experiment label
MATERIAL_TYPE = "EcoFlex20"     # Sample material name
```

### Timing
```python
DELAY_CAMERA_BOOT = 3   # Wait (seconds) before pump starts after video
INFUSION_PAUSE = 1      # Pause (seconds) between infuse and withdraw
```

All parameters are validated automatically before the test starts.

---

## 📁 Project Structure
```
📦 MDI_NETS_TestBench
├── main.py                     # Central experiment control script
├── calibrate.py                # Camera calibration and undistortion tools
├── record_video.py             # Threaded video recording functions
├── harvard_apparatus.py        # Pump command logic and serial protocol
├── serial_connection.py        # COM port scanning and initialization
├── experiment_parameters.py    # User-defined experiment and safety settings
├── variables.py                # Hardware IDs and COM port constants
├── pressure_sensor.py          # Pressure transducer logic and communication protocol
├── tracking.py                 # Logic for tracking point of interest
├── calibration_points.txt      # Auto-generated reference point log
├── data_analysis.py            # Post-process CSV data and annotate video
├── requirements.txt            # Python dependencies
📦 MDI_NETS_TestBench
│
├── Data/
│   └── 10-10/
│       └── AirTest_EcoFlex20_14-30-52/
│           ├── Data_Parameters.txt
│           ├── Trial_1/
│           │   ├── Data_1.csv                    # Raw pump data
│           │   ├── Video_Trial_1.mp4
│           │   ├── Video_Trial_1_Annotated.mp4
│           │   ├── Data_1_fixed.csv             #Generated by fix_withdraw_volumes()
│           │   ├── Data_1_fixed_with_angle.csv  #Generated by merge_pump_and_angle()
│           │   └── Graphs/                      #Created by plot_pump_data()
│           │       ├── Trial_1_volume_vs_time.png
│           │       ├── Trial_1_pressure_vs_time.png
│           │       ├── Trial_1_volume_by_state.png
│           │       ├── Trial_1_pressure_vs_volume.png
│           │       ├── Trial_1_angle_vs_time.png           # (only if angle CSV exists)
│           │       ├── Trial_1_angle_vs_volume.png         # (only if angle CSV exists)
│           │       ├── Trial_1_angle_vs_pressure.png       # (only if angle CSV exists)
│           │       ├── Trial_1_angle_by_state.png          # (only if angle CSV exists)
│           ├── Trial_2/
│           │   ├── Data_2.csv                    # Raw pump data
│           │   ├── Video_Trial_2.mp4
│           │   ├── Video_Trial_2_Annotated.mp4
│           │   ├── Data_2_fixed.csv             #Generated by fix_withdraw_volumes()
│           │   ├── Data_2_fixed_with_angle.csv  #Generated by merge_pump_and_angle()
│           │   └── Graphs/                      #Created by plot_pump_data()
│           │       ├── Trial_2_volume_vs_time.png
│           │       ├── Trial_2_pressure_vs_time.png
│           │       ├── Trial_2_volume_by_state.png
│           │       ├── Trial_2_pressure_vs_volume.png
│           │       ├── Trial_2_angle_vs_time.png           # (only if angle CSV exists)
│           │       ├── Trial_2_angle_vs_volume.png         # (only if angle CSV exists)
│           │       ├── Trial_2_angle_vs_pressure.png       # (only if angle CSV exists)
│           │       ├── Trial_2_angle_by_state.png          # (only if angle CSV exists)
│           ├── TrialSummary/
│           │   ├── MergedData.csv                    # Merged Data for N trials
│           │   ├── Angle_Stats.txt                  # Overview of angles
└── calibration_images/                # Auto-generated folder
    ├── calibration_00.jpg             # Captured chessboard images
    ├── corners_calibration_00.jpg     # Corner-detected images
    ├── calibration_data.pkl           # Saved calibration data
    ├── camera_matrix.txt              # Intrinsic parameters
    ├── distortion_coefficients.txt    # Lens distortion coefficients
    ├── undistorted/                   # (optional) corrected images
    └── before_after_comparison.png    # Before vs. after comparison plot

```

---

## ⚠️ Common ValueErrors and How to Fix Them

The system performs several safety checks at startup.  
If something is misconfigured, a **`ValueError`** message will appear — use the table below to troubleshoot.

### 🔧 Syringe and Volume Validation (`check_syringe_limits()`)

| Error Message | Meaning | How to Fix |
|----------------|----------|------------|
| `Invalid syringe unit: xyz. Must be one of: l, ml, ul.` | The syringe volume unit is not valid. | Use only `"l"`, `"ml"`, or `"ul"` in `experiment_parameters.py`. |
| `Withdraw volume 70 mL exceeds syringe capacity (60 mL).` | Withdraw volume exceeds the syringe’s total capacity. | Reduce `TARGET_VOLUME_WITHDRAW` or increase `SYRINGE_VOLUME`. |
| `Infuse volume 70 mL exceeds syringe capacity (60 mL).` | Infuse volume exceeds the syringe’s total capacity. | Reduce `TARGET_VOLUME_INFUSE` or increase `SYRINGE_VOLUME`. |

---

### 💨 Flow Rate Validation (`calculate_flow_rates()`)

| Error Message | Meaning | How to Fix |
|----------------|----------|------------|
| `Invalid flow unit: xyz. Must be one of: l/min, ml/min, ul/min, nl/min.` | Unsupported unit used for rates. | Set valid units for `INFUSION_RATE_UNIT` and `WITHDRAW_RATE_UNIT`. |
| `Syringe diameter must be greater than zero.` | Syringe diameter is not configured properly. | Set `SYRINGE_DIAMETER_MM` to your syringe’s actual diameter. |
| `Infusion rate (X mL/min) exceeds max allowed (Y mL/min).` | Infusion rate too high for syringe limits. | Lower `INFUSION_RATE`. |
| `Infusion rate (X mL/min) below min allowed (Y mL/min).` | Infusion rate too slow for accurate control. | Increase `INFUSION_RATE`. |
| `Withdraw rate (X mL/min) exceeds max allowed (Y mL/min).` | Withdrawal rate too high for syringe limits. | Lower `WITHDRAW_RATE`. |
| `Withdraw rate (X mL/min) below min allowed (Y mL/min).` | Withdrawal rate too slow for accuracy. | Increase `WITHDRAW_RATE`. |

---

### ⚙️ Serial Port or Connection Errors

| Error Message | Meaning | How to Fix |
|----------------|----------|------------|
| `Device not found. See troubleshooting output above.` | Pump not found on any COM port. | Check the USB cable, drivers, and `HARVARD_APARATUS_HARDWARE_ID` in `variables.py`. |
| `Serial Monitor could not be opened` | Serial port could not be initialized. | Ensure no other software is using the port and the baud rate is 115200. |
| `COM not set` or `BAUD_RATE not set` | Missing parameters in setup. | Make sure `initialize_devices()` and `harvard_control()` are called in `main.py`. |


# 🧩 Function Call Hierarchy (Simplified) [Out of Date]

This diagram outlines how functions call each other across the **MDI_NETS_TestBench** project.  
Library calls (e.g., OpenCV, Matplotlib, Serial) are labeled as **(library)**.

---

```
🔹 calculate_flow_rates (experiment_parameters.py)
   ➜ calls check_syringe_limits (experiment_parameters.py)

🔹 calibrate_camera (calibrate.py)
   ➜ calls cv2.findChessboardCorners (library)
   ➜ calls cv2.calibrateCamera (library)

🔹 camera_calibration_main (calibrate.py)
   ➜ calls capture_calibration_images (calibrate.py)
   ➜ calls calibrate_camera (calibrate.py)
   ➜ calls undistort_images (calibrate.py)
   ➜ calls plot_before_after (calibrate.py)

🔹 capture_calibration_images (calibrate.py)
   ➜ calls cv2.VideoCapture (library)
   ➜ calls cv2.findChessboardCorners (library)

🔹 check_syringe_limits (experiment_parameters.py)
   ➜ calls normalize_strings (experiment_parameters.py)

🔹 harvard_control (harvard_apparatus.py)
   ➜ calls serial.Serial (library)

🔹 initial_setup (main.py)
   ➜ calls camera_calibration_main (calibrate.py)
   ➜ calls initialize_devices (serial_connection.py)
   ➜ calls harvard_control (harvard_apparatus.py)

🔹 initialize_devices (serial_connection.py)
   ➜ calls scan_COMports (serial_connection.py)

🔹 main (main.py)
   ➜ calls check_syringe_limits (experiment_parameters.py)
   ➜ calls calculate_flow_rates (experiment_parameters.py)
   ➜ calls run_experiment (main.py)

🔹 plot_before_after (calibrate.py)
   ➜ calls matplotlib.pyplot (library)

🔹 poll_pump_status (harvard_apparatus.py)
   ➜ calls send_cmd (harvard_apparatus.py)
   ➜ calls parse_status_line (harvard_apparatus.py)

🔹 run_experiment (main.py)
   ➜ calls initial_setup (main.py)
   ➜ calls create_data_folders (main.py)
   ➜ calls save_trial_parameters (main.py)
   ➜ calls set_machine_params (harvard_apparatus.py)
   ➜ calls start_video_recording (record_video.py)
   ➜ calls send_cmd (harvard_apparatus.py)
   ➜ calls poll_pump_status (harvard_apparatus.py)
   ➜ calls set_target_withdraw (harvard_apparatus.py)
   ➜ calls save_trial_data (main.py)

🔹 set_machine_params (harvard_apparatus.py)
   ➜ calls send_cmd (harvard_apparatus.py)

🔹 set_target_infused (harvard_apparatus.py)
   ➜ calls send_cmd (harvard_apparatus.py)

🔹 set_target_withdraw (harvard_apparatus.py)
   ➜ calls send_cmd (harvard_apparatus.py)

🔹 start_video_recording (record_video.py)
   ➜ calls record_video (record_video.py)

🔹 undistort_images (calibrate.py)
   ➜ calls cv2.undistort (library)
```
