import cv2
import numpy as np
import math
import os
import re

P_pivot = None     # calibration: pivot point (center protractor)
P_refA = None      # calibration: 0-degree reference point
p0_tip = None      # calibration: tip point
calibration_stage = 0

tracking_initialized = False
window_name = 'Tube Angle Tracker Setup'

lk_params = dict(
    winSize=(15, 15),
    maxLevel=2,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
)


def calculate_protractor_angle(pivot, ref_a, tip):
    vec_A = np.array(ref_a) - np.array(pivot)
    vec_tip = np.array(tip) - np.array(pivot)

    angle_A_rad = math.atan2(vec_A[0], vec_A[1])
    angle_tip_rad = math.atan2(vec_tip[0], vec_tip[1])
    deg = math.degrees(angle_tip_rad - angle_A_rad)

    if deg > 180:
        deg -= 360
    elif deg < -180:
        deg += 360

    return deg

def load_calibration_file(path):
    if not os.path.exists(path):
        print(f"[ERROR] Calibration file not found:\n{path}")
        return None, None, None

    try:
        with open(path, "r") as f:
            lines = f.readlines()
            pivot = tuple(map(int, lines[0].split(',')))
            refA = tuple(map(int, lines[1].split(',')))
            x, y = map(int, lines[2].split(','))

        tip = np.array([[[x, y]]], dtype=np.float32)

        print(f"[LOADED] Calibration loaded: pivot={pivot}, refA={refA}, tip={x,y}")
        return pivot, refA, tip

    except Exception as e:
        print(f"[ERROR] Failed to parse calibration file: {e}")
        return None, None, None

def select_calibration_points(event, x, y, flags, param):
    global calibration_stage, P_pivot, P_refA, p0_tip, tracking_initialized

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    frame = param['frame'].copy()

    # Stage 0: click pivot
    if calibration_stage == 0:
        P_pivot = (x, y)
        calibration_stage = 1
        cv2.circle(frame, P_pivot, 8, (0, 0, 255), -1)
        cv2.putText(frame, "Pivot set Click 0 degrees reference",
                    (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    # Stage 1: click reference A
    elif calibration_stage == 1:
        P_refA = (x, y)
        calibration_stage = 2
        cv2.circle(frame, P_pivot, 8, (0, 0, 255), -1)
        cv2.circle(frame, P_refA, 8, (0, 255, 0), -1)
        cv2.putText(frame, "Reference set Click tube tip",
                    (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    # Stage 2: click tip
    elif calibration_stage == 2:
        p0_tip = np.array([[[x, y]]], dtype=np.float32)
        calibration_stage = 3
        tracking_initialized = True
        cv2.circle(frame, P_pivot, 8, (0, 0, 255), -1)
        cv2.circle(frame, P_refA, 8, (0, 255, 0), -1)
        cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
        cv2.putText(frame, "Calibration complete Press any key",
                    (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow(window_name, frame)


def run_tracker(video_path, calibration_file, annotated_video_path, calibration_mode=False):
    global p0_tip, calibration_stage, tracking_initialized, P_pivot, P_refA

    # Reset states
    p0_tip = None
    P_pivot = None
    P_refA = None
    calibration_stage = 0
    tracking_initialized = False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video:\n{video_path}")
        return []

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    video_writer = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))

    ret, initial_frame = cap.read()
    if not ret:
        print("[ERROR] Failed to read first frame.")
        return []

    '''
    PHASE 1 — CALIBRATION
    '''
    if calibration_mode:
        print("\n=== CALIBRATION MODE ===")

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        frame = initial_frame.copy()
        cv2.putText(frame, "CLICK PIVOT POINT (CENTER PROTRACTOR)",
                    (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        cv2.setMouseCallback(window_name, select_calibration_points,
                             {'frame': initial_frame})
        cv2.imshow(window_name, frame)

        while not tracking_initialized:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[ABORT] Calibration canceled.")
                return []

        cv2.waitKey(0)

        # Save calibration file
        # Used as reference
        with open(calibration_file, "w") as f:
            f.write(f"{P_pivot[0]},{P_pivot[1]}\n")
            f.write(f"{P_refA[0]},{P_refA[1]}\n")
            x, y = p0_tip[0][0].astype(int)
            f.write(f"{x},{y}\n")

        print(f"[SAVED] Calibration written to:\n{calibration_file}")

        cap.release()
        video_writer.release()
        cv2.destroyAllWindows()
        return []

    '''
    PHASE 2 - Tracking
    '''
    print("\n=== TRACKING MODE ===")

    P_pivot, P_refA, p0_tip = load_calibration_file(calibration_file)
    if P_pivot is None:
        print("[ERROR] Calibration missing.")
        return []

    old_gray = cv2.cvtColor(initial_frame, cv2.COLOR_BGR2GRAY)
    data = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        t = frame_num / fps
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0_tip, None, **lk_params)

        if st[0] == 1:
            x_tip, y_tip = p1[0][0]
            tip_point = (int(x_tip), int(y_tip))
            p0_tip = p1
        else:
            tip_point = None

        if tip_point:
            angle = calculate_protractor_angle(P_pivot, P_refA, tip_point)
            data.append((t, angle))

            cv2.circle(frame, tip_point, 8, (0,255,255), -1)
            cv2.circle(frame, P_pivot, 8, (0,0,255), -1)
            cv2.line(frame, P_pivot, tip_point, (255,0,0), 2)

            cv2.putText(frame, f"{t:.2f}s | {angle:.2f} deg",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (181, 186, 10), 2)

        video_writer.write(frame)
        old_gray = frame_gray.copy()

    cap.release()
    video_writer.release()

    print(f"[DONE] Saved annotated video:\n{annotated_video_path}")
    return data


VIDEO_REGEX = re.compile(r"^Video_Trial_\d+\.mp4$", re.IGNORECASE)

def find_all_trial_videos(root_folder):
    result = []
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if VIDEO_REGEX.match(file):
                video_path = os.path.join(root, file)
                trial_folder = os.path.dirname(video_path)
                exp_type_folder = os.path.dirname(trial_folder)
                result.append((video_path, trial_folder, exp_type_folder))
    return result


def anotation(TRIAL_FOLDER, CALIBRATION_MODE=True):
    trials = find_all_trial_videos(TRIAL_FOLDER)
    if not trials:
        print("[ERROR] No matching Video_Trial_N.mp4 files found.")
        return

    calibrated_types = set()

    for video_path, trial_folder, exp_type_folder in trials:

        type_name = os.path.basename(exp_type_folder)
        trial_name = os.path.basename(trial_folder)

        print(f"\n=== {type_name} / {trial_name} ===")

        calibration_file = os.path.join(exp_type_folder, "calibration_points.txt")

        video_file = os.path.basename(video_path)
        base_name, _ = os.path.splitext(video_file)
        annotated_video_path = os.path.join(trial_folder,
                                            f"{base_name}_annotation.mp4")

        # First run for each experiment type then calibrate
        if CALIBRATION_MODE and type_name not in calibrated_types:
            print(f"[CALIBRATION] Running for: {type_name}")

            # --- STEP 1: RUN CALIBRATION ---
            run_tracker(video_path, calibration_file, annotated_video_path, calibration_mode=True)
            calibrated_types.add(type_name)

            # --- STEP 2: RUN TRACKING IMMEDIATELY AFTER CALIBRATION FOR TRIAL 1 ---
            print(f"[TRACKING] Running tracking for Trial 1 after calibration...")
            data = run_tracker(video_path, calibration_file, annotated_video_path, calibration_mode=False)

            # --- STEP 3: SAVE ANGLES CSV ---
            csv_path = os.path.join(trial_folder, f"{base_name}_angles.csv")
            with open(csv_path, "w") as f:
                f.write("time,angle\n")
                for t, a in data:
                    f.write(f"{t:.4f},{a:.4f}\n")

            print(f"[SAVED] Angle CSV written to:\n{csv_path}")

            # Move to next video
            continue

        else:
            print(f"[TRACKING] Using calibration for: {type_name}")
            data = run_tracker(video_path, calibration_file, annotated_video_path, calibration_mode=False)

            csv_path = os.path.join(trial_folder, f"{base_name}_angles.csv")
            with open(csv_path, "w") as f:
                f.write("time,angle\n")
                for t, a in data:
                    f.write(f"{t:.4f},{a:.4f}\n")

            print(f"[SAVED] Angle CSV written to:\n{csv_path}")

