'''
When the script is run, the terminal will display a message in the following format:
"Opened camera index N"

Check the terminal output to determine which camera index corresponds to the correct camera.
You can toggle between cameras with 'n' and 'p'
Exit with 'q'

Once the correct camera has been identified, update the CAMERA_ID variable in the file 
experiment_parameters.py to the value of N shown in the terminal.

'''

import cv2

def open_cam(index):
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        print(f"Opened camera index {index}")
        return cap
    return None

current_index = 0
cap = open_cam(current_index)

while True:
    if cap:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Camera Viewer", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    # Next camera
    if key == ord('n'):
        if cap:
            cap.release()
        current_index += 1
        cap = open_cam(current_index)

    # Previous camera
    if key == ord('p') and current_index > 0:
        if cap:
            cap.release()
        current_index -= 1
        cap = open_cam(current_index)

cv2.destroyAllWindows()
