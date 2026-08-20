import serial.tools.list_ports

print("Searching for ports...")
ports = serial.tools.list_ports.comports()

if not ports:
    print("No ports found! Check your USB cable.")
else:
    for port, desc, hwid in ports:
        print(f"FOUND: {port} - {desc}")