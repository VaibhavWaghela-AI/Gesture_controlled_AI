import serial
import csv
import time
import os

# --- CONFIGURATION ---
SERIAL_PORT = 'COM6'   # <--- CHECK THIS!
BAUD_RATE = 115200
FILENAME = 'imu_data.csv'

# The 5 Physical Gestures we need to train
LABELS = {
    0: "IDLE (Relaxed/Typing)",
    1: "FLICK_RIGHT (Next/New)", 
    2: "FLICK_LEFT (Prev/Close)",
    3: "TWIST_CW (Vol Up/Start)",
    4: "TWIST_CCW (Vol Down/End)",
    5: "SHAKE (Play/Pause/Refresh)"
}

# Connect to Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # Reset ESP32 to ensure clean start
    ser.setDTR(False); time.sleep(1); ser.setDTR(True)
    print(f"Connected to {SERIAL_PORT}")
except:
    print(f"ERROR: Could not find ESP32 on {SERIAL_PORT}")
    exit()

# Initialize CSV (Create header if new)
if not os.path.exists(FILENAME):
    with open(FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["label", "ax", "ay", "az", "gx", "gy", "gz"])

print("\n--- CLEAN DATA COLLECTOR ---")
for k, v in LABELS.items():
    print(f"  {k}: {v}")
print("-----------------------------")

while True:
    try:
        user_input = input(f"\nEnter Label ID (0-5) to Record or 'q' to quit: ")
        if user_input.lower() == 'q': break
        
        current_label = int(user_input)
        if current_label not in LABELS:
            print("Invalid Label!")
            continue
            
        print(f"GET READY... Recording {LABELS[current_label]} in 3 seconds...")
        time.sleep(1); print("2..."); time.sleep(1); print("1...")
        time.sleep(1)
        print(">>> RECORDING! PERFORM GESTURE CONTINUOUSLY! <<<")
        print("(Press Ctrl+C to STOP and save this batch)")

        # Recording Loop
        with open(FILENAME, 'a', newline='') as f:
            writer = csv.writer(f)
            while True:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8').strip()
                        
                        # --- CLEAN SPLIT: Expects "ax,ay,az,gx,gy,gz" ---
                        vals = line.split(',')
                        
                        if len(vals) == 6:
                            # Verify data is valid float (removes glitches)
                            float(vals[0]) 
                            
                            row = [current_label] + vals
                            writer.writerow(row)
                            print(f"Saved: {row}")
                    except ValueError:
                        pass # Ignore partial lines
                        
    except KeyboardInterrupt:
        print("\nBatch Saved! Select next label.")
        ser.reset_input_buffer()
        continue
    except ValueError:
        print("Please enter a number.")

ser.close()
print("Collection Complete.")
