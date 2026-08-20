import tkinter as tk
import serial
import numpy as np
import tensorflow as tf
import pyautogui
import threading
import time
import re
import os
import joblib 

# --- CONFIGURATION ---
SERIAL_PORT = 'COM6'   
BAUD_RATE = 115200

# --- MOUSE SETTINGS ---
MOUSE_SENSITIVITY = 25  
MOUSE_DEADZONE = 2.0    
MOVE_ENERGY_LIMIT = 5000       # Move if slower than this
CLICK_ENERGY_THRESHOLD = 12000 # Click if faster than this

# --- GESTURE SETTINGS ---
CONF_THRESHOLD = 0.75          
COOLDOWN = 1.0                 

# --- OFFSETS ---
OFFSET_AX = 0
OFFSET_AY = 0
OFFSET_AZ = 0

MODE_MAPPINGS = {
    "SLIDESHOW": { 1: ("right",), 2: ("left",), 3: ("f5",), 4: ("esc",), 5: ("b",) },
    "BROWSER": { 1: ("ctrl", "pagedown"), 2: ("ctrl", "pageup"), 3: ("ctrl", "t"), 4: ("ctrl", "w"), 5: ("f5",) },
    
    # --- UPDATED MEDIA MODE FOR YOUTUBE ---
    "MEDIA": { 
        1: ("right",),        # FLICK RIGHT -> Skip Forward 5 sec
        2: ("left",),         # FLICK LEFT -> Skip Backward 5 sec
        3: ("up",),           # TWIST CW -> Volume Up (YouTube shortcut)
        4: ("down",),         # TWIST CCW -> Volume Down (YouTube shortcut)
        5: ("k",)             # SHAKE -> Play/Pause (Bulletproof YouTube shortcut)
    },
    
    "SYSTEM": { 1: ("alt", "tab"), 2: ("win", "d"), 3: ("win", "tab"), 4: ("alt", "f4"), 5: ("win", "l") }
}

GESTURE_NAMES = {0: "IDLE", 1: "FLICK_RIGHT", 2: "FLICK_LEFT", 3: "TWIST_CW", 4: "TWIST_CCW", 5: "SHAKE"}

class GestureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestura: MVP Edition")
        self.root.geometry("700x600")
        self.root.configure(bg="#2d3436")
        
        # KEYBOARD ESCAPE HATCH (Only way to exit mouse mode now)
        root.bind('<Escape>', self.emergency_exit) 

        tk.Label(root, text="GESTURA CONTROLLER", font=("Arial", 26, "bold"), bg="#2d3436", fg="#00cec9").pack(pady=20)
        self.status = tk.Label(root, text="Status: CONNECTING...", font=("Arial", 12), bg="#2d3436", fg="orange")
        self.status.pack(pady=5)

        # BUTTONS
        btn_frame = tk.Frame(root, bg="#2d3436")
        btn_frame.pack(pady=20)
        self.create_btn(btn_frame, "📊 SLIDESHOW", "SLIDESHOW", "#0984e3", 0, 0)
        self.create_btn(btn_frame, "🌐 BROWSER", "BROWSER", "#6c5ce7", 0, 1)
        self.create_btn(btn_frame, "🎵 MEDIA", "MEDIA", "#00b894", 1, 0)
        self.create_btn(btn_frame, "💻 SYSTEM", "SYSTEM", "#d63031", 1, 1)

        tk.Button(btn_frame, text="🖱️ AIR MOUSE", bg="#e17055", fg="white", font=("Arial", 12, "bold"), 
                  width=40, height=2, command=lambda: self.set_mode("MOUSE")).grid(row=2, column=0, columnspan=2, pady=20)

        self.mode_label = tk.Label(root, text="MODE: NONE", font=("Arial", 14, "bold"), bg="#2d3436", fg="white")
        self.mode_label.pack()

        self.console = tk.Text(root, height=10, width=70, bg="black", fg="#55efc4", font=("Consolas", 10))
        self.console.pack(pady=10)
        
        self.current_mode = "NONE"
        self.running = True
        self.scaler = None

    def create_btn(self, parent, text, mode, color, r, c):
        tk.Button(parent, text=text, bg=color, fg="white", font=("Arial", 11, "bold"), width=18, height=2,
                  command=lambda: self.set_mode(mode)).grid(row=r, column=c, padx=10, pady=10)

    def set_mode(self, mode):
        self.current_mode = mode
        self.mode_label.config(text=f"MODE: {mode}")
        self.log(f"--> SWITCHED TO {mode}")
        if mode == "MOUSE":
            self.log("⚠️ AIR MOUSE ACTIVE: Press 'ESC' on keyboard to exit.")

    def emergency_exit(self, event):
        if self.current_mode == "MOUSE":
            self.set_mode("NONE")
            self.log("🛑 EXITED MOUSE MODE VIA ESCAPE KEY.")

    def log(self, msg):
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)

def map_mouse_value(value, deadzone, sensitivity):
    if abs(value) < deadzone: return 0
    val = (abs(value) - deadzone) * sensitivity
    return val if value > 0 else -val

def run_hybrid_thread(app):
    global OFFSET_AX, OFFSET_AY, OFFSET_AZ
    
    try:
        model = tf.keras.models.load_model("imu_model.h5")
        if os.path.exists("scaler.save"): app.scaler = joblib.load("scaler.save")
        app.log("✅ AI System Online")
    except:
        app.log("❌ ERROR: Model Missing")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        ser.setDTR(False); time.sleep(1); ser.setDTR(True)
        app.status.config(text="Status: CONNECTED", fg="#00cec9")
    except:
        app.log("❌ ERROR: Check USB")
        return

    # AUTO-CALIBRATION
    app.log("✋ HOLD HAND STILL FOR CALIBRATION...")
    time.sleep(1)
    
    cal_readings = []
    start_cal = time.time()
    while time.time() - start_cal < 2.0:
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                nums = re.findall(r'-?\d+\.?\d*', line)
                if len(nums) == 6:
                    cal_readings.append([float(x)/1000.0 for x in nums])
            except: pass
            
    if len(cal_readings) > 0:
        avgs = np.mean(cal_readings, axis=0)
        OFFSET_AX, OFFSET_AY, OFFSET_AZ = avgs[0], avgs[1], avgs[2]
        app.log(f"✅ CALIBRATED!")
    else:
        app.log("⚠️ Calibration Failed")

    last_action_time = 0
    last_click_time = 0
    last_gesture_id = 0
    pyautogui.FAILSAFE = False

    while app.running:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                numbers = re.findall(r'-?\d+\.?\d*', line)
                
                if len(numbers) == 6:
                    raw_vals = np.array(numbers, dtype=float)
                    gx, gy, gz = raw_vals[3], raw_vals[4], raw_vals[5]
                    total_energy = abs(gx) + abs(gy) + abs(gz)
                    current_time = time.time()

                    # ---------------------------
                    # MODE A: AIR MOUSE 
                    # ---------------------------
                    if app.current_mode == "MOUSE":
                        ax = (raw_vals[0] / 1000.0) - OFFSET_AX
                        ay = (raw_vals[1] / 1000.0) - OFFSET_AY
                        
                        if total_energy > CLICK_ENERGY_THRESHOLD and (current_time - last_click_time > 1.0):
                            app.log(f">>> CLICK! ({int(total_energy)}) <<<")
                            pyautogui.mouseDown(); time.sleep(0.1); pyautogui.mouseUp()
                            last_click_time = current_time
                            time.sleep(0.4) 

                        elif total_energy < MOVE_ENERGY_LIMIT and (current_time - last_click_time > 0.4):
                            move_x = map_mouse_value(ax, MOUSE_DEADZONE, MOUSE_SENSITIVITY) 
                            move_y = map_mouse_value(ay, MOUSE_DEADZONE, MOUSE_SENSITIVITY) * -1
                            pyautogui.move(move_x, move_y)
# ---------------------------
                    # MODE B: GESTURES (PURE AI - MVP RESTORE)
                    # ---------------------------
                    elif app.current_mode != "NONE":
                        # 1. NOISE FILTER (Ignores resting hand jitters)
                        if total_energy < 3000:
                            continue

                        # 2. FEED THE EXACT DATA THE AI WAS TRAINED ON
                        # We must send 'raw_vals', otherwise your pre-trained AI won't recognize it!
                        input_data = np.array([raw_vals])
                        
                        # Apply your existing scaler
                        if app.scaler: 
                            input_data = app.scaler.transform(input_data)
                        
                        # 3. LET THE AI DECIDE
                        prediction = model.predict(input_data, verbose=0)
                        class_id = np.argmax(prediction)
                        confidence = np.max(prediction)

                        # 4. EXECUTE THE GESTURE
                        if confidence > CONF_THRESHOLD and class_id != 0:
                            if app.current_mode in MODE_MAPPINGS:
                                keys = MODE_MAPPINGS[app.current_mode].get(class_id)
                                
                                if keys and (current_time - last_action_time > COOLDOWN):
                                    gesture_name = GESTURE_NAMES.get(class_id)
                                    
                                    # See exactly how confident the AI is!
                                    app.log(f"!!! {gesture_name} -> {keys} [AI Confidence: {int(confidence*100)}%] !!!")
                                    
                                    if len(keys) == 1: pyautogui.press(keys[0])
                                    elif len(keys) == 2: pyautogui.hotkey(keys[0], keys[1])
                                    
                                    last_action_time = current_time

            except Exception as e:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureApp(root)
    t = threading.Thread(target=run_hybrid_thread, args=(app,))
    t.daemon = True
    t.start()
    root.mainloop()
    app.running = False