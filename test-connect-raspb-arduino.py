import serial
import time

# This is usually the Arduino port on Raspberry Pi
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # wait for Arduino reset
    print("Connected to Arduino!")
except Exception as e:
    print("Error:", e)
    exit()

# Test sending
ser.write(b"Hello from Raspberry Pi!\n")
print("Message sent. Waiting for response...")

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            print("Received:", data)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
