import cv2
import threading
import os
from experiment_parameters import CAMERA_ID


def record_video(CAMERA=CAMERA_ID, VIDEO_TYPE="mp4v", TRIAL_NUM=None, stop_event=None, output_path=None):

    """
    Continuously records video frames from a connected camera and saves them to a file.

    Opens a video capture stream using OpenCV, displays the live video feed, 
    and writes frames to disk until the recording is stopped either manually or programmatically.

    Args:
        CAMERA (int or str, optional): The camera index or device path to open (default: CAMERA_ID from experiment_parameters).
        VIDEO_TYPE (str, optional): Four-character video codec code (e.g., "mp4v" or "XVID").
        TRIAL_NUM (int, optional): Current trial number, used to label the display window and log messages.
        stop_event (threading.Event, optional): A threading event that signals when to stop recording.
        output_path (str, optional): Full path (including filename) where the recorded video should be saved.

    Behavior:
        - Press **'q'** to manually stop recording from the display window.
        - If `stop_event` is set externally, the recording stops automatically.
        - Each recorded video is saved to the specified output path.

    Notes:
        The function runs in a blocking loop and is intended to be used within a separate thread
        so it does not interfere with experiment control or data logging.
    """

    cap = cv2.VideoCapture(CAMERA)

    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30

    fourcc = cv2.VideoWriter_fourcc(*VIDEO_TYPE)
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    print(f"Recording video: {output_path}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        out.write(frame)
        cv2.imshow(f"Trial#{TRIAL_NUM}", frame)


        if stop_event and stop_event.is_set():
            print(f"Stopping recording for Trial#{TRIAL_NUM}")
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print(f"Recording manually stopped for Trial#{TRIAL_NUM}")
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Video saved: {output_path}")


def start_video_recording(trial_number, trial_folder):

    """
    Starts a threaded video recording process for a given experimental trial.

    Creates a dedicated thread that runs the `record_video()` function 
    and returns a `stop_event` object used to terminate the recording externally.

    Args:
        trial_number (int): The current experimental trial number (used for naming the output video).
        trial_folder (str): Directory path where the video file will be saved.

    Returns:
        tuple:
            - stop_event (threading.Event): Event that can be set to stop the video recording.
            - video_thread (threading.Thread): The running thread executing the video recording process.

    Notes:
        The video file is automatically named as `Video_Trial_<trial_number>.mp4`
        and saved inside the provided `trial_folder`.
    """

    stop_event = threading.Event()
    video_path = os.path.join(trial_folder, f"Video_Trial_{trial_number}.mp4")

    video_thread = threading.Thread(
        target=record_video,
        kwargs={
            "TRIAL_NUM": trial_number,
            "stop_event": stop_event,
            "output_path": video_path,
        }
    )

    video_thread.start()
    print(f"Video thread started for Trial {trial_number}")
    return stop_event, video_thread