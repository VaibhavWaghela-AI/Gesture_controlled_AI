import cv2
import mediapipe as mp
import pyautogui
import math
import time
import numpy as np

# --- CONFIGURATION ---
pyautogui.FAILSAFE = False
MOUSE_SMOOTHING = 5
SCROLL_SPEED = 50       # How fast it scrolls when tilted
VOL_COOLDOWN = 0.2      # Delay for volume ticks
SLIDE_COOLDOWN = 1.0    # Delay for slide changes

# --- SETUP ---
screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# State Variables
plocX, plocY = 0, 0
last_vol_time = 0
last_slide_time = 0

def get_hand_orientation(lm):
    """
    Calculates 'Pitch' (Up/Down tilt) and 'Roll' (Rotation)
    mimicking an MPU6050 sensor.
    """
    # 1. Calculate PITCH (Tilt Up/Down)
    # Compare Wrist (0) y-coord vs Middle Finger MCP (9) y-coord
    wrist_y = lm[0].y
    knuckle_y = lm[9].y
    
    # If knuckle is significantly higher/lower than wrist
    diff_y = wrist_y - knuckle_y
    
    pitch = "NEUTRAL"
    if diff_y > 0.15:  pitch = "UP"      # Hand pointing up
    elif diff_y < -0.15: pitch = "DOWN"  # Hand pointing down
    
    # 2. Calculate ROLL (Rotation Left/Right)
    # Angle between Wrist(0) and Middle Finger(9)
    x1, y1 = lm[0].x, lm[0].y
    x2, y2 = lm[9].x, lm[9].y
    angle = math.degrees(math.atan2(y1 - y2, x1 - x2))
    
    # Normalize angle (0 is straight up)
    # 90 is Left, -90 is Right roughly (depends on hand)
    roll = "NEUTRAL"
    if angle < 60: roll = "RIGHT"
    elif angle > 120: roll = "LEFT"
    
    return pitch, roll

def count_fingers(lm):
    fingers = []
    # Check 4 fingers (Tip vs Pip)
    for id in [8, 12, 16, 20]:
        if lm[id].y < lm[id-2].y: # Tip higher than knuckle
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

print(">>> GYRO SIMULATOR ACTIVE")
print(">>> INDEX OUT = Mouse")
print(">>> FIST = Gyro Mode (Tilt to Scroll/Vol)")

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    status_text = "IDLE"
    color = (200, 200, 200)
    
    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            lm = hand_lms.landmark
            
            fingers = count_fingers(lm)
            num_fingers = fingers.count(1)
            
            # --- MODE 1: MOUSE (Index Finger Open) ---
            if fingers[0] == 1 and num_fingers == 1: # Only Index is UP
                status_text = "MOUSE MODE"
                color = (255, 0, 255)
                
                # Move Mouse
                x1, y1 = int(lm[8].x * w), int(lm[8].y * h)
                cv2.rectangle(img, (100, 100), (w-100, h-100), (255, 0, 255), 1)
                
                # Smooth Map
                x3 = np.interp(x1, (100, w-100), (0, screen_w))
                y3 = np.interp(y1, (100, h-100), (0, screen_h))
                
                clocX = plocX + (x3 - plocX) / MOUSE_SMOOTHING
                clocY = plocY + (y3 - plocY) / MOUSE_SMOOTHING
                try: pyautogui.moveTo(clocX, clocY) 
                except: pass
                plocX, plocY = clocX, clocY
                
                # Click (Thumb + Index Pinch)
                x2, y2 = int(lm[4].x * w), int(lm[4].y * h)
                if math.hypot(x2 - x1, y2 - y1) < 30:
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()

            # --- MODE 2: GYRO / GESTURE (Fist / 0 Fingers) ---
            elif num_fingers == 0: 
                pitch, roll = get_hand_orientation(lm)
                status_text = f"GYRO: {pitch} / {roll}"
                color = (255, 255, 0) # Cyan
                
                # A. PITCH -> SCROLL / SLIDES
                if pitch == "UP":
                    status_text = "SCROLL UP / PREV"
                    # Continuous Scroll
                    pyautogui.scroll(SCROLL_SPEED)
                    # OR Slide Change (Uncomment below for PPT)
                    # if time.time() - last_slide_time > SLIDE_COOLDOWN:
                    #     pyautogui.press('left')
                    #     last_slide_time = time.time()
                        
                elif pitch == "DOWN":
                    status_text = "SCROLL DOWN / NEXT"
                    # Continuous Scroll
                    pyautogui.scroll(-SCROLL_SPEED)
                    # OR Slide Change (Uncomment below for PPT)
                    # if time.time() - last_slide_time > SLIDE_COOLDOWN:
                    #     pyautogui.press('right')
                    #     last_slide_time = time.time()

                # B. ROLL -> VOLUME
                # We check Roll only if Pitch is Neutral (to avoid accidental triggers)
                if pitch == "NEUTRAL":
                    if roll == "RIGHT": # Tilted Right
                        status_text = "VOL UP ++"
                        if time.time() - last_vol_time > VOL_COOLDOWN:
                            pyautogui.press('volumeup')
                            last_vol_time = time.time()
                    elif roll == "LEFT": # Tilted Left
                        status_text = "VOL DOWN --"
                        if time.time() - last_vol_time > VOL_COOLDOWN:
                            pyautogui.press('volumedown')
                            last_vol_time = time.time()

    # Draw UI
    cv2.rectangle(img, (0,0), (640, 60), (0,0,0), -1)
    cv2.putText(img, status_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Gyro Simulator", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()