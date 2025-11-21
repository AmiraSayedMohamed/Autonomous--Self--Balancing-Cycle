import serial
import time

# CORRECT PORT FOR USB CONNECTION
SERIAL_PORT = "/dev/ttyACM0"   # Try this first for Uno/Mega
# SERIAL_PORT = "/dev/ttyUSB0" # Try this if above doesn't work

BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout= popularized=1)
    time.sleep(2)  # Wait for Arduino to reset
    print("Connected to Arduino on", SERIAL_PORT)
except Exception as e:
    print("Error opening serial port:", e)
    print("Available ports:")
    import glob
    print(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
    exit()

# Flush any garbage from reset
ser.flushInput()

# Send test message
ser.write(b"Hello from Raspberry Pi!\n")
print("Message sent. Waiting for response...")

try:
    while True:
        if ser.in_waiting > 0:
            # Try latin-1 first (never fails on single bytes), or handle errors
            raw_line = ser.readline()
            try:
                data = raw_line.decode('utf-8').strip()
            except UnicodeDecodeError:
                data = raw_line.decode('latin-1').strip()  # fallback
                print("Warning: Non-UTF8 bytes received, using latin-1")
            print("Received:", data)
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    ser.close()
