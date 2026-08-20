import serial
import time

ser = serial.Serial('COM6', 115200, timeout=1)
print("Reading raw data...")

while True:
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"RAW: {line}")