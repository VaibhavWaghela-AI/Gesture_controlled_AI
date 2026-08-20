import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
import re
import numpy as np

# --- CONFIGURATION ---
SERIAL_PORT = 'COM6'   # <--- CHECK THIS
BAUD_RATE = 115200

# --- SENSOR RANGES (Adjust these to zoom the bars) ---
ACCEL_RANGE = 20000    # Raw Accelerometer Max (Usually ~16000)
GYRO_RANGE = 30000     # Raw Gyro Max

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestura Hardware Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg="#2d3436")
        
        tk.Label(root, text="HARDWARE DASHBOARD", font=("Arial", 24, "bold"), bg="#2d3436", fg="#00cec9").pack(pady=10)
        
        self.status = tk.Label(root, text="Waiting for USB...", font=("Arial", 14), bg="#2d3436", fg="orange")
        self.status.pack(pady=5)

        # --- SECTION 1: MOUSE TILT (Accelerometer) ---
        frame_mouse = tk.LabelFrame(root, text=" 🖱️ AIR MOUSE (Tilt) ", font=("Arial", 12, "bold"), bg="#2d3436", fg="white", bd=2)
        frame_mouse.pack(fill="x", padx=20, pady=10)

        # X-AXIS BAR
        tk.Label(frame_mouse, text="Left <--- X (Roll) ---> Right", bg="#2d3436", fg="#dfe6e9").pack()
        self.bar_x = ttk.Progressbar(frame_mouse, length=600, mode='determinate', maximum=ACCEL_RANGE*2)
        self.bar_x.pack(pady=5)
        self.label_x = tk.Label(frame_mouse, text="0", bg="#2d3436", fg="#ffeaa7")
        self.label_x.pack()

        # Y-AXIS BAR
        tk.Label(frame_mouse, text="Forward <--- Y (Pitch) ---> Back", bg="#2d3436", fg="#dfe6e9").pack()
        self.bar_y = ttk.Progressbar(frame_mouse, length=600, mode='determinate', maximum=ACCEL_RANGE*2)
        self.bar_y.pack(pady=5)
        self.label_y = tk.Label(frame_mouse, text="0", bg="#2d3436", fg="#ffeaa7")
        self.label_y.pack()

        # --- SECTION 2: GESTURE FLICK (Gyroscope) ---
        frame_gyro = tk.LabelFrame(root, text=" 👋 FLICK DIRECTION (Gyro Z) ", font=("Arial", 12, "bold"), bg="#2d3436", fg="white", bd=2)
        frame_gyro.pack(fill="x", padx=20, pady=10)

        self.bar_z = ttk.Progressbar(frame_gyro, length=600, mode='determinate', maximum=GYRO_RANGE*2)
        self.bar_z.pack(pady=5)
        self.label_z = tk.Label(frame_gyro, text="ROTATION: 0", font=("Arial", 12, "bold"), bg="#2d3436", fg="#fab1a0")
        self.label_z.pack(pady=5)

        self.running = True

    def update_bars(self, ax, ay, gz):
        # Center the bars (Value 0 is at 50% of the bar)
        center_accel = ACCEL_RANGE
        center_gyro = GYRO_RANGE

        self.bar_x['value'] = center_accel + ay  # Note: Swap ax/ay if needed
        self.bar_y['value'] = center_accel + ax
        self.bar_z['value'] = center_gyro + gz

        self.label_x.config(text=f"Raw X: {int(ay)}")
        self.label_y.config(text=f"Raw Y: {int(ax)}")
        
        # Logic for Flick Direction
        direction = "---"
        if gz > 3000: direction = "<< FLICK LEFT <<" # Adjust threshold based on observation
        elif gz < -3000: direction = ">> FLICK RIGHT >>"
        
        self.label_z.config(text=f"Gyro Z: {int(gz)}  [{direction}]")

def read_serial(app):
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        app.status.config(text="CONNECTED! Move your hand.", fg="#00cec9")
    except:
        app.status.config(text="ERROR: Check COM Port", fg="red")
        return

    while app.running:
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                nums = re.findall(r'-?\d+\.?\d*', line)
                
                if len(nums) == 6:
                    # RAW VALUES (Do not divide by 1000 here, we want to see the RAW truth)
                    vals = [float(x) for x in nums]
                    
                    # ax=0, ay=1, az=2, gx=3, gy=4, gz=5
                    ax = vals[0]
                    ay = vals[1]
                    gz = vals[5] 

                    # Update GUI
                    app.root.after(0, app.update_bars, ax, ay, gz)
            except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    t = threading.Thread(target=read_serial, args=(app,))
    t.daemon = True
    t.start()
    root.mainloop()
    app.running = False