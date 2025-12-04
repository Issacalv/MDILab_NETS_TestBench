import cv2
import numpy as np
import math
import os
import time

# --- A. VIDEO AND MODE SETTINGS ---
VIDEO_FILE = r'C:\Users\Issac\Desktop\MDILab_TestBench\MDI_NETS_TestBench\TestVideo\Video Clip (2025-08-11 19_02_22).mp4'
ANNOTATED_VIDEO_FILE = 'annotated_output.mp4' # Output file for annotated video

# Set to True for the first run (to click the tube tip).
# Set to False for silent data processing and video annotation runs.
CALIBRATION_MODE = False 

# These coordinates define the protractor's reference system and should be FIXED.
P_pivot_fixed = (368, 93)     # Protractor Center (Fixed Pivot)
P_A_fixed = (651, 95)         # Reference A (e.g., 0 degrees line)

# --- C. INITIAL TIP FILE PATH ---
TIP_FILE_PATH = 'tip_initial_position.txt'

# ==============================================================================
#                 CORE FUNCTIONS
# ==============================================================================

lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

p0_tip = None
tracking_initialized = False
window_name = 'Tube Angle Tracker Setup'

def calculate_protractor_angle(pivot, ref_a, tip):
    """Calculates the angle of the tip relative to the protractor reference point A."""
    vec_A = np.array(ref_a) - np.array(pivot) 
    vec_tip = np.array(tip) - np.array(pivot) 

    angle_A_rad = math.atan2(vec_A[0], vec_A[1]) 
    angle_tip_rad = math.atan2(vec_tip[0], vec_tip[1])

    relative_angle_rad = angle_tip_rad - angle_A_rad
    relative_angle_deg = math.degrees(relative_angle_rad)
    
    if relative_angle_deg > 180:
        relative_angle_deg -= 360
    elif relative_angle_deg < -180:
        relative_angle_deg += 360
        
    return relative_angle_deg

def load_initial_tip_point(file_path):
    """Loads the initial tip coordinate from a file."""
    if not os.path.exists(file_path):
        print(f"ERROR: Calibration file '{file_path}' not found. Please run in CALIBRATION_MODE = True first.")
        return None
        
    try:
        with open(file_path, 'r') as f:
            x_str, y_str = f.read().strip().split(',')
            x, y = int(x_str), int(y_str)
            return np.array([[[x, y]]], dtype=np.float32)
    except Exception as e:
        print(f"ERROR: Could not parse calibration file. {e}")
        return None

def select_tip_point(event, x, y, flags, param):
    """Mouse callback to capture the initial tip point during calibration."""
    global p0_tip, tracking_initialized
    
    if tracking_initialized:
        return

    if event == cv2.EVENT_LBUTTONDOWN and p0_tip is None:
        p0_tip = np.array([[[x, y]]], dtype=np.float32)
        tracking_initialized = True
        print(f"Initial Tip Point selected at (x, y): ({x}, {y}).")
        
        # Display feedback
        temp_frame = param['frame'].copy()
        cv2.circle(temp_frame, (x, y), 8, (0, 255, 255), -1)
        cv2.putText(temp_frame, "SETUP COMPLETE. PRESS ANY KEY TO SAVE & EXIT.", 
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow(window_name, temp_frame)


def run_tracker(video_path, tip_file_path, annotated_video_path, calibration_mode=False):
    """Main function to run the calibration or tracking process."""
    global p0_tip, tracking_initialized, window_name
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Could not open video file at {video_path}")
        return []

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    video_writer = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))
    
    time_angle_data = []

    ret, initial_frame = cap.read()
    if not ret:
        cap.release()
        video_writer.release()
        return []

    # ==========================================================================
    #                 PHASE 1: CALIBRATION SETUP
    # ==========================================================================
    if calibration_mode:
        print("\n--- PHASE 1: CALIBRATION MODE ACTIVE ---")        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        temp_frame = initial_frame.copy()
        
        cv2.circle(temp_frame, P_pivot_fixed, 8, (0, 0, 255), -1) 
        cv2.circle(temp_frame, P_A_fixed, 8, (0, 255, 0), -1)    
        cv2.putText(temp_frame, "CLICK TUBE TIP", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        param = {'frame': initial_frame}
        cv2.setMouseCallback(window_name, select_tip_point, param)
        cv2.imshow(window_name, temp_frame)

        while not tracking_initialized:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                cap.release()
                video_writer.release()
                return []
        
        cv2.waitKey(0) 

        if p0_tip is not None:
            x_coord, y_coord = p0_tip[0][0].astype(int)
            with open(tip_file_path, 'w') as f:
                f.write(f"{x_coord},{y_coord}")
            print(f"\nCalibration saved to {tip_file_path}: ({x_coord}, {y_coord}).")
        
        cv2.destroyAllWindows()
        cap.release()
        video_writer.release()
        return [] 

    # ==========================================================================
    #                 PHASE 2: SILENT TRACKING AND VIDEO ANNOTATION
    # ==========================================================================
    print("\n--- PHASE 2: SILENT TRACKING MODE ACTIVE ---")
    
    # Load the initial tip point (p0_tip)
    p0_tip = load_initial_tip_point(tip_file_path)
    if p0_tip is None:
        cap.release()
        video_writer.release()
        return []
    
    old_gray = cv2.cvtColor(initial_frame, cv2.COLOR_BGR2GRAY)

    # print(f"Tracking with P_pivot={P_pivot_fixed} and Ref_A={P_A_fixed}. Saving annotated video to {annotated_video_path}")
    # print("Time (s) | Angle (deg)")
    # print("---------------------")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        current_time = frame_num / fps
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        P_tip = None

        if p0_tip is not None and len(p0_tip) > 0:
            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0_tip, None, **lk_params)
            good_new = p1[st==1]
            
            if len(good_new) > 0:
                x_tip, y_tip = good_new[0].ravel()
                P_tip = (int(x_tip), int(y_tip))
                p0_tip = good_new.reshape(-1, 1, 2)
            else:
                p0_tip = None
                print(f"{current_time:.3f}    | TRACKING LOST. Data recording stopped.")
        
        # --- ANGLE CALCULATION AND ANNOTATION ---
        if P_tip:
            angle_deg = calculate_protractor_angle(P_pivot_fixed, P_A_fixed, P_tip)
            time_angle_data.append((current_time, angle_deg))
            
            print(f"{current_time:.3f}    | {angle_deg:.2f}")

            cv2.line(frame, P_pivot_fixed, P_tip, (255, 0, 0), 2)     
            cv2.circle(frame, P_pivot_fixed, 8, (0, 0, 255), -1)       # Red
            cv2.circle(frame, P_tip, 8, (0, 255, 255), -1)           # Yellow

            text = f"Time: {current_time:.2f}s | Angle: {angle_deg:.2f} deg"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        
        video_writer.write(frame)

        old_gray = frame_gray.copy()

    cap.release()
    video_writer.release()
    
    print("\n--- TRACKING COMPLETE ---")
    print(f"Annotated video saved to: {annotated_video_path}")
    return time_angle_data


if __name__ == "__main__":
    if not os.path.exists(VIDEO_FILE):
        print(f"FATAL ERROR: Video file not found at '{VIDEO_FILE}'. Please correct the path.")
    else:
        run_tracker(VIDEO_FILE, TIP_FILE_PATH, ANNOTATED_VIDEO_FILE, CALIBRATION_MODE)