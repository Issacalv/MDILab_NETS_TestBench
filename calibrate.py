import os
import cv2
import time
import glob
import pickle
import random
import numpy as np
import matplotlib.pyplot as plt

CAMERA_ID = 0
SQUARE_SIZE = 3  # in centimeters
CHESSBOARD_SIZE = (6, 4)
MAX_IMAGES = 30
CAPTURE_INTERVAL = 2
SAVE_UNDISTORTED = False
CALIBRATION_IMAGES_PATH = 'calibration_images/*.jpg'
OUTPUT_DIRECTORY = 'calibration_images'

def capture_calibration_images():
    """
    Automatically capture chessboard images from a camera for calibration.
    """
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print(f"Error: Could not open camera {CAMERA_ID}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera resolution: {width}x{height}")
    print("Automatic capture running... Press 'q' or ESC to quit")

    img_counter = len(glob.glob(CALIBRATION_IMAGES_PATH))
    last_capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

        if found:
            cv2.drawChessboardCorners(frame, CHESSBOARD_SIZE, corners, found)
            cv2.putText(frame, "Chessboard detected!", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            current_time = time.time()
            if current_time - last_capture_time > CAPTURE_INTERVAL:
                img_name = os.path.join(OUTPUT_DIRECTORY, f"calibration_{img_counter:02d}.jpg")
                cv2.imwrite(img_name, frame)
                print(f"Captured {img_name}")
                img_counter += 1
                last_capture_time = current_time

                if MAX_IMAGES and img_counter >= MAX_IMAGES:
                    print(f"Captured {MAX_IMAGES} images. Exiting...")
                    break

        cv2.putText(frame, f"Captured: {img_counter}", (50, height - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Camera Calibration', frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):  # 'q' or ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Captured {img_counter} images for calibration.")

def calibrate_camera():
    """
    Calibrates the camera using the captured chessboard images.
    """
    objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE

    objpoints, imgpoints = [], []
    images = glob.glob(CALIBRATION_IMAGES_PATH)

    if not images:
        print(f"No images found at {CALIBRATION_IMAGES_PATH}")
        return None, None, None, None, None

    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    print(f"Found {len(images)} calibration images")

    for idx, fname in enumerate(images):
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

        if ret:
            objpoints.append(objp)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            cv2.drawChessboardCorners(img, CHESSBOARD_SIZE, corners2, ret)
            output_path = os.path.join(OUTPUT_DIRECTORY, f'corners_{os.path.basename(fname)}')
            cv2.imwrite(output_path, img)
            print(f"[{idx+1}/{len(images)}] Chessboard found: {fname}")
        else:
            print(f"[{idx+1}/{len(images)}] Chessboard NOT found: {fname}")

    if not objpoints:
        print("No chessboard patterns were detected in any images.")
        return None, None, None, None, None

    print("Calibrating camera...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    calibration_data = {
        'camera_matrix': mtx,
        'distortion_coefficients': dist,
        'rotation_vectors': rvecs,
        'translation_vectors': tvecs,
        'reprojection_error': ret
    }

    with open(os.path.join(OUTPUT_DIRECTORY, 'calibration_data.pkl'), 'wb') as f:
        pickle.dump(calibration_data, f)

    np.savetxt(os.path.join(OUTPUT_DIRECTORY, 'camera_matrix.txt'), mtx)
    np.savetxt(os.path.join(OUTPUT_DIRECTORY, 'distortion_coefficients.txt'), dist)

    print(f"Calibration complete! RMS error: {ret}")
    return ret, mtx, dist, rvecs, tvecs

def undistort_images(mtx, dist):
    """
    Undistorts images using calibration results.
    """
    if not SAVE_UNDISTORTED:
        return

    images = glob.glob(CALIBRATION_IMAGES_PATH)
    if not images:
        print(f"No images found at {CALIBRATION_IMAGES_PATH}")
        return

    undistorted_dir = os.path.join(OUTPUT_DIRECTORY, 'undistorted')
    os.makedirs(undistorted_dir, exist_ok=True)

    print(f"Undistorting {len(images)} images...")

    for idx, fname in enumerate(images):
        img = cv2.imread(fname)
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        x, y, w, h = roi
        dst = dst[y:y + h, x:x + w]
        out_path = os.path.join(undistorted_dir, f'undistorted_{os.path.basename(fname)}')
        cv2.imwrite(out_path, dst)
        print(f"Undistorted [{idx+1}/{len(images)}]: {fname}")

    print(f"Undistorted images saved to {undistorted_dir}")

def calculate_reprojection_error(objpoints, imgpoints, mtx, dist, rvecs, tvecs):
    """
    Calculates mean reprojection error.
    """
    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error
        print(f"Reprojection error for image {i+1}: {error:.4f}")

    mean_error = total_error / len(objpoints)
    print(f"Mean reprojection error: {mean_error:.4f}")
    return mean_error

def plot_before_after():
    """
    Display and save two random 'before and after' pairs of original vs. undistorted images.
    """
    original_images = sorted(glob.glob(os.path.join(OUTPUT_DIRECTORY, 'calibration_*.jpg')))
    undistorted_images = sorted(glob.glob(os.path.join(OUTPUT_DIRECTORY, 'undistorted', 'undistorted_*.jpg')))

    if not original_images or not undistorted_images:
        print("Error: No matching original and undistorted images found.")
        return

    num_pairs = min(len(original_images), len(undistorted_images))
    selected_indices = random.sample(range(num_pairs), min(2, num_pairs))

    fig, axes = plt.subplots(len(selected_indices), 2, figsize=(12, 6))
    fig.suptitle("Before and After Undistortion Comparison", fontsize=16)

    for i, idx in enumerate(selected_indices):
        orig = cv2.imread(original_images[idx])
        undist = cv2.imread(undistorted_images[idx])

        orig_rgb = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
        undist_rgb = cv2.cvtColor(undist, cv2.COLOR_BGR2RGB)

        ax1 = axes[i, 0] if len(selected_indices) > 1 else axes[0]
        ax2 = axes[i, 1] if len(selected_indices) > 1 else axes[1]

        ax1.imshow(orig_rgb)
        ax1.set_title(f'Original ({os.path.basename(original_images[idx])})')
        ax1.axis('off')

        ax2.imshow(undist_rgb)
        ax2.set_title(f'Undistorted ({os.path.basename(undistorted_images[idx])})')
        ax2.axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    output_path = os.path.join(OUTPUT_DIRECTORY, 'before_after_comparison.png')
    plt.savefig(output_path)
    print(f"Saved before/after comparison figure to: {output_path}")

    plt.close(fig)

def main():
    print("Starting camera calibration...")

    existing_images = glob.glob(CALIBRATION_IMAGES_PATH)
    if len(existing_images) >= MAX_IMAGES:
        print(f"{len(existing_images)} calibration images already found. Skipping capture.")
    else:
        print(f"Only found {len(existing_images)} images. Starting capture...")
        capture_calibration_images()

    calibration_file = os.path.join(OUTPUT_DIRECTORY, 'calibration_data.pkl')

    if os.path.exists(calibration_file):
        print("Existing calibration file found. Loading...")
        with open(calibration_file, 'rb') as f:
            calibration_data = pickle.load(f)
        mtx = calibration_data['camera_matrix']
        dist = calibration_data['distortion_coefficients']
        rvecs = calibration_data['rotation_vectors']
        tvecs = calibration_data['translation_vectors']
        ret = calibration_data['reprojection_error']
        print(f"Loaded camera matrix. RMS error: {ret}")
    else:
        print("No calibration data found. Calibrating now...")
        ret, mtx, dist, rvecs, tvecs = calibrate_camera()
        if mtx is None:
            print("Calibration failed.")
            return

    undistort_images(mtx, dist)
    if SAVE_UNDISTORTED:
        plot_before_after()
    print("Camera calibration completed successfully!")


if __name__ == "__main__":
    main()
