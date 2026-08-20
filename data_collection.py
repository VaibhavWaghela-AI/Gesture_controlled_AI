import cv2
import numpy as np
import csv
import os
import sys

# --- THE "UNBREAKABLE" IMPORT BLOCK ---
try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except AttributeError:
    # If the standard way fails, try the internal path
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_draw
except ImportError:
    print("CRITICAL ERROR: MediaPipe is not installed correctly.")
    print("Run: pip install mediapipe==0.10.9")
    sys.exit()

# --- CONFIG ---
DATA_FILE = "gesture_data_final.csv"
LABELS = {
     0: "IDLE (Relaxed)", 
    1: "MOUSE (Index Pointing)", 
    2: "SWITCH_MODE (Peace Sign)", 
    3: "SCROLL/MUTE (Fist)", 
    4: "PLAY/PAUSE (Open Palm)", 
    5: "VOL_UP / NEXT (Thumbs Up)", 
    6: "VOL_DOWN / PREV (Thumbs Down)"
}

# Initialize Hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# Init CSV
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["label"] + [f"x{i}" for i in range(21)] + [f"y{i}" for i in range(21)]
        writer.writerow(header)

cap = cv2.VideoCapture(0)
print(">>> DATA COLLECTOR RUNNING <<<")

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    status_text = "Press 0-6 to Record"
    color = (200, 200, 200)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # Extract Data
            row = []
            for lm in hand_lms.landmark:
                row.append(lm.x)
                row.append(lm.y)
            
            # Key Logic
            key = cv2.waitKey(1)
            if key >= 48 and key <= 54: 
                label = key - 48
                with open(DATA_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([label] + row)
                status_text = f"SAVED: {LABELS[label]}"
                color = (0, 255, 0) # Green

    # UI
    cv2.rectangle(img, (0,0), (640, 60), (0,0,0), -1)
    cv2.putText(img, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Data Collector Final", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()