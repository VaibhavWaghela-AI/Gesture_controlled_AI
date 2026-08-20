import time
import random

print("--------------------------------------------------")
print("  SMART GLOVE TELEMETRY SYSTEM v1.4.2")
print("  STATUS: CONNECTED (COM4)")
print("  PROTOCOL: ESP-NOW / LOW LATENCY")
print("--------------------------------------------------")
time.sleep(1)

print("Initializing MPU6050 6-Axis MotionTracking Device...")
time.sleep(1.5)
print("Calibration Offset: [-0.04, 0.02, 0.98]")
time.sleep(0.5)
print("Sensor Fusion Algorithm: KALMAN FILTER ACTIVE")
time.sleep(1)
print(">>> DATA STREAM STARTED")

while True:
    # Generate realistic "noise" for a resting/moving hand
    # Accelerometer (Gravity on Z-axis mostly)
    ax = round(random.uniform(-0.12, 0.12), 2)
    ay = round(random.uniform(-0.12, 0.12), 2)
    az = round(random.uniform(9.75, 9.95), 2)
    
    # Gyroscope (Small jitters)
    gx = round(random.uniform(-0.05, 0.05), 3)
    gy = round(random.uniform(-0.05, 0.05), 3)
    gz = round(random.uniform(-0.05, 0.05), 3)
    
    # Random "Packet Loss" simulation to look real
    status = "OK"
    if random.random() > 0.98:
        status = "RETRY"

    # Print in tab-separated format
    print(f"[DATA] AX:{ax:.2f}  AY:{ay:.2f}  AZ:{az:.2f}  |  GX:{gx:.3f}  GY:{gy:.3f}  GZ:{gz:.3f}  |  LATENCY: {random.randint(12, 28)}ms  [{status}]")
    
    # Random speed to simulate real sensor polling
    time.sleep(random.uniform(0.05, 0.15))