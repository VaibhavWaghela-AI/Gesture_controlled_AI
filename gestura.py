import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pyautogui
import time
from collections import Counter

# --- CONFIGURATION ---
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0 
CONF_THRESHOLD = 0.88 
HISTORY_LEN = 6        

# Match your specific labels exactly
CLASSES = {
    0: "IDLE (Relaxed)",
    1: "MOUSE (Index Pointing)",
    2: "SWITCH_MODE (Peace Sign)",
    3: "SCROLL/MUTE (Fist)",
    4: "PLAY/PAUSE (Open Palm)",
    5: "VOL_UP / NEXT (Thumbs Up)",
    6: "VOL_DOWN / PREV (Thumbs Down)"
}

# --- INITIALIZATION ---
print("Loading Glove AI v4.0...")
model = tf.keras.models.load_model("gesture_model_7class.h5")
screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

plocX, plocY = 0, 0
gesture_history = []
last_action_time = 0
last_gesture_id = 0
system_active = True  # Can be toggled by SWITCH_MODE

print(">>> GLOVE SYSTEM ONLINE. READY FOR EXHIBITION.")

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    current_status = "IDLE"
    color = (200, 200, 200)

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_lms, mp.solutions.hands.HAND_CONNECTIONS)
            
            # Prepare Input
            row = []
            for lm in hand_lms.landmark:
                row.extend([lm.x, lm.y])
            
            # AI Prediction
            prediction = model.predict(np.array([row]), verbose=0)
            class_id = np.argmax(prediction)
            confidence = np.max(prediction)

            # Smoothing
            gesture_history.append(class_id)
            if len(gesture_history) > HISTORY_LEN: gesture_history.pop(0)
            stable_class = Counter(gesture_history).most_common(1)[0][0]
            
            if confidence > CONF_THRESHOLD and gesture_history.count(stable_class) >= 3:
                current_status = CLASSES[stable_class]
                
                # --- GESTURE MAPPING ---

                # 2: SWITCH_MODE (Peace Sign) - Toggle System
                if stable_class == 2:
                    color = (255, 255, 0)
                    if time.time() - last_action_time > 1.0:
                        system_active = not system_active
                        print(f"System Active: {system_active}")
                        last_action_time = time.time()

                if system_active:
                    # 1: MOUSE (Index Pointing)
                    if stable_class == 1:
                        color = (255, 0, 255)
                        x_raw = hand_lms.landmark[8].x * w
                        y_raw = hand_lms.landmark[8].y * h
                        x_mapped = np.interp(x_raw, (100, w-100), (0, screen_w))
                        y_mapped = np.interp(y_raw, (100, h-100), (0, screen_h))
                        
                        # Move Mouse
                        pyautogui.moveTo(x_mapped, y_mapped, _pause=False)

                    # 3: SCROLL/MUTE (Fist)
                    elif stable_class == 3:
                        color = (0, 0, 255)
                        pyautogui.scroll(-50) # Set to scroll down by default

                    # 4: PLAY/PAUSE (Open Palm)
                    elif stable_class == 4:
                        color = (0, 255, 0)
                        if time.time() - last_action_time > 0.5:
                            pyautogui.press('playpause')
                            last_action_time = time.time()

                    # 5: VOL_UP / NEXT (Thumbs Up)
                    elif stable_class == 5:
                        color = (0, 255, 100)
                        if time.time() - last_action_time > 0.2:
                            pyautogui.press('volumeup')
                            last_action_time = time.time()

                    # 6: VOL_DOWN / PREV (Thumbs Down)
                    elif stable_class == 6:
                        color = (0, 100, 255)
                        if time.time() - last_action_time > 0.2:
                            pyautogui.press('volumedown')
                            last_action_time = time.time()

    # PRO UI
    display_text = f"MODE: {current_status}" if system_active else "SYSTEM LOCKED (PEACE TO UNLOCK)"
    cv2.rectangle(img, (0, 0), (w, 60), (30, 30, 30), -1)
    cv2.putText(img, display_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    cv2.imshow("Glove AI Master Console", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()