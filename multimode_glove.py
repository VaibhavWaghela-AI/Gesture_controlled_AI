import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pyautogui
import math
import time

# --- CONFIGURATION ---
pyautogui.FAILSAFE = False
MOUSE_SMOOTHING = 5
SWITCH_HOLD_TIME = 1.5  # Seconds to hold "Peace" to switch modes
ACTION_COOLDOWN = 1.0   # Seconds between actions (prevents spam)

# --- LOAD AI MODEL ---
# Make sure you ran '2_train_model.py' first!
try:
    model = tf.keras.models.load_model("gesture_model_7class.h5")
except:
    print("ERROR: Model not found. Run '2_train_model.py' first.")
    exit()

# SHAPE LABELS (What the AI sees)
SHAPES = {
    0: "IDLE",
    1: "POINTING",
    2: "PEACE",
    3: "FIST",
    4: "PALM",
    5: "THUMBS_UP",
    6: "THUMBS_DOWN"
}

# MODES (The Contexts)
MODES = ["MOUSE", "PPT", "MEDIA", "AUDIO", "SYSTEM"]
curr_mode_index = 0

# SETUP
screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# STATE VARIABLES
plocX, plocY = 0, 0
last_action_time = 0
mode_switch_start = 0

print(">>> INTELLIGENT GLOVE ACTIVE")
print(">>> HOLD 'PEACE SIGN' (2s) TO SWITCH MODES")

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    mode_name = MODES[curr_mode_index]
    status_text = "Scanning..."
    color = (200, 200, 200)
    
    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # 1. PREPARE INPUT FOR AI
            row = []
            for lm in hand_lms.landmark:
                row.append(lm.x)
                row.append(lm.y)
            
            # 2. GET AI PREDICTION
            input_data = np.array([row])
            prediction = model.predict(input_data, verbose=0)
            class_id = np.argmax(prediction)
            confidence = np.max(prediction)
            
            current_shape = SHAPES[class_id]
            
            if confidence > 0.8: # High Confidence Only
                
                # --- GLOBAL: MODE SWITCHING (PEACE SIGN) ---
                if current_shape == "PEACE":
                    if mode_switch_start == 0:
                        mode_switch_start = time.time()
                    
                    elapsed = time.time() - mode_switch_start
                    cv2.putText(img, f"SWITCHING... {int(elapsed*100)}%", (w-300, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    
                    if elapsed > SWITCH_HOLD_TIME:
                        curr_mode_index = (curr_mode_index + 1) % len(MODES)
                        mode_switch_start = 0 # Reset
                        last_action_time = time.time() + 1.0 # Cooldown
                else:
                    mode_switch_start = 0 # Reset if gesture broken

                # --- EXECUTE ACTIONS BASED ON MODE ---
                if time.time() > last_action_time:
                    
                    # 🔵 MODE 1: MOUSE (General PC Use)
                    if mode_name == "MOUSE":
                        color = (255, 0, 255)
                        if current_shape == "POINTING":
                            # Move Mouse
                            x1 = int(hand_lms.landmark[8].x * w)
                            y1 = int(hand_lms.landmark[8].y * h)
                            # Smooth Map
                            x3 = np.interp(x1, (100, w-100), (0, screen_w))
                            y3 = np.interp(y1, (100, h-100), (0, screen_h))
                            clocX = plocX + (x3 - plocX) / MOUSE_SMOOTHING
                            clocY = plocY + (y3 - plocY) / MOUSE_SMOOTHING
                            try: pyautogui.moveTo(clocX, clocY) 
                            except: pass
                            plocX, plocY = clocX, clocY
                            status_text = "MOUSE MOVING"
                            
                        elif current_shape == "THUMBS_UP":
                            pyautogui.click()
                            status_text = "LEFT CLICK"
                            # Small cooldown for clicks
                            # last_action_time = time.time() + 0.2 

                    # 🟠 MODE 2: PPT (Presentations)
                    elif mode_name == "PPT":
                        color = (255, 165, 0) # Orange
                        if current_shape == "THUMBS_UP":
                            pyautogui.press('right')
                            status_text = "NEXT SLIDE >>"
                            last_action_time = time.time() + ACTION_COOLDOWN
                        elif current_shape == "THUMBS_DOWN":
                            pyautogui.press('left')
                            status_text = "<< PREV SLIDE"
                            last_action_time = time.time() + ACTION_COOLDOWN
                        elif current_shape == "FIST":
                            # Laser Pointer Simulation (Hold 'Ctrl' + Click in PPT)
                            # For demo, let's just use 'B' for Black Screen
                            pyautogui.press('b')
                            status_text = "BLACK SCREEN"
                            last_action_time = time.time() + ACTION_COOLDOWN

                    # 🔴 MODE 3: MEDIA (YouTube/Movies)
                    elif mode_name == "MEDIA":
                        color = (0, 0, 255) # Red
                        if current_shape == "PALM":
                            pyautogui.press('space') # Play/Pause
                            status_text = "PLAY / PAUSE"
                            last_action_time = time.time() + ACTION_COOLDOWN
                        elif current_shape == "FIST":
                            pyautogui.press('volumemute')
                            status_text = "MUTE AUDIO"
                            last_action_time = time.time() + ACTION_COOLDOWN

                    # 🟢 MODE 4: AUDIO (Volume Master)
                    elif mode_name == "AUDIO":
                        color = (0, 255, 0) # Green
                        if current_shape == "THUMBS_UP":
                            pyautogui.press('volumeup')
                            status_text = "VOLUME UP ++"
                            time.sleep(0.1) # Fast repeat
                        elif current_shape == "THUMBS_DOWN":
                            pyautogui.press('volumedown')
                            status_text = "VOLUME DOWN --"
                            time.sleep(0.1)

                    # ⚫ MODE 5: SYSTEM (Admin/Lock)
                    elif mode_name == "SYSTEM":
                        color = (50, 50, 50) # Dark Grey
                        if current_shape == "FIST":
                            status_text = "LOCKING PC..."
                            cv2.putText(img, "LOCKING...", (w//2-100, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
                            cv2.imshow("Smart Glove", img)
                            cv2.waitKey(1000) # Give user a second to see msg
                            pyautogui.hotkey('win', 'l')
                            last_action_time = time.time() + 5.0
                        elif current_shape == "PALM":
                            pyautogui.hotkey('win', 'd') # Show Desktop
                            status_text = "SHOW DESKTOP"
                            last_action_time = time.time() + ACTION_COOLDOWN

    # HUD (Heads Up Display)
    # Top Bar
    cv2.rectangle(img, (0, 0), (w, 80), (0, 0, 0), -1)
    # Mode Text
    cv2.putText(img, f"MODE: {mode_name}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    # Action Text
    cv2.putText(img, f"ACTION: {status_text}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    # Shape Debug
    # cv2.putText(img, f"AI SEE: {SHAPES.get(class_id, '?')}", (w-250, 120), cv2.FONT_HERSHEY_PLAIN, 1.5, (200,200,200), 2)

    cv2.imshow("Smart Glove", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()