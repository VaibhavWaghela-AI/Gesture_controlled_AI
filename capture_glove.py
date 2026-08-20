import cv2
import numpy as np
import csv
import os

# --- SETTINGS ---
DATA_FILE = "glove_data_v6.csv"
# Increased ROI to give you more room to move
ROI_W = 500 
ROI_H = 400

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["label"] + [f"pt{i}_{c}" for i in range(21) for c in ['x', 'y']]
        writer.writerow(header)

cap = cv2.VideoCapture(0)
# This ignores static objects (like your face/background) and looks for movement
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=False)

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    # 1. LARGER ROI
    x_start, y_start = (w - ROI_W)//2, (h - ROI_H)//2
    roi = frame[y_start:y_start+ROI_H, x_start:x_start+ROI_W]
    
    # 2. CLEANER DETECTION
    fg_mask = bg_subtractor.apply(roi)
    _, thresh = cv2.threshold(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 60, 255, cv2.THRESH_BINARY_INV)
    
    # Combine background subtraction and thresholding
    combined = cv2.bitwise_and(fg_mask, thresh)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

    # 3. FIND GLOVE SKELETON
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) > 2000:
            epsilon = 0.01 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            hull = cv2.convexHull(approx)
            
            cv2.drawContours(roi, [approx], -1, (0, 255, 0), 2)
            
            features = []
            for p in hull:
                pt = p[0]
                cv2.circle(roi, tuple(pt), 6, (0, 0, 255), -1)
                if len(features) < 42:
                    features.extend([pt[0]/ROI_W, pt[1]/ROI_H])

            while len(features) < 42: features.append(0)

            # 4. DATA COLLECTION
            key = cv2.waitKey(1)
            if 48 <= key <= 54:
                with open(DATA_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([key-48] + features)
                print(f"Captured {key-48} | Move your hand for variety!")

    # UI
    cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (0, 255, 255), 2)
    cv2.putText(frame, "KEEP GLOVE IN CYAN BOX", (x_start, y_start-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    cv2.imshow("Glove Tracker (Wide Mode)", frame)
    cv2.imshow("Mask", mask)
    
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()