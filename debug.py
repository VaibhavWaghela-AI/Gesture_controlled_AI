import serial
import csv
import time
import os

# --- CONFIGURATION ---
SERIAL_PORT = 'COM6'   # <--- Confirm this matches!
BAUD_RATE = 115200     
FILENAME = 'imu_data.csv'

# CHANGE THIS TO RECORD DIFFERENT GESTURES!
# 0=IDLE, 1=FLICK_R, 2=FLICK_L, 3=TWIST_CW, 4=TWIST_CCW, 5=SHAKE
CURRENT_LABEL = 0      
DURATION_SEC = 30      # How long to record

print(f"--- CONNECTING TO {SERIAL_PORT} ---")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # Toggle DTR to reset ESP32
    ser.setDTR(False)
    time.sleep(1)
    ser.flushInput()
    ser.setDTR(True)
    print(">>> PORT OPENED SUCCESSFULLY")

except Exception as e:
    print(f"ERROR: {e}")
    print("Did you close the Arduino Serial Monitor?")
    exit()

# Initialize CSV
if not os.path.exists(FILENAME):
    with open(FILENAME, 'w', newline='') as f:
        csv.writer(f).writerow(["label", "ax", "ay", "az", "gx", "gy", "gz"])

print(f"\n>>> RECORDING LABEL {CURRENT_LABEL} FOR {DURATION_SEC} SECONDS...")
print("PERFORM THE GESTURE NOW!")

start_time = time.time()
count = 0

with open(FILENAME, 'a', newline='') as f:
    writer = csv.writer(f)
    
    while (time.time() - start_time) < DURATION_SEC:
        if ser.in_waiting > 0:
            try:
                # Read and clean data
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                vals = line.split(',')
                
                # Verify we have 6 numbers
                if len(vals) == 6:
                    row = [CURRENT_LABEL] + vals
                    writer.writerow(row)
                    count += 1
                    
                    if count % 10 == 0:
                        print(f"Saved {count} rows... Last: {vals}")
                else:
                    print(f"Ignored junk: {line}")
                    
            except Exception as e:
                pass

print(f"\nDONE! Saved {count} rows to {FILENAME}")
ser.close()