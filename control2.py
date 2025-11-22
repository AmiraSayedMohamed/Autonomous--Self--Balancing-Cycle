#!/usr/bin/env python3
import serial
import time
import struct
import RPi.GPIO as GPIO

# ================== CONFIG ==================
LIDAR_PORT = '/dev/serial0'
ARDUINO_PORT = '/dev/ttyACM0'   # or /dev/ttyUSB0 – check with ls /dev/tty*
BAUD = 230400                   # LD06 default baudrate
SAFE_DIST = 500                 # 50 cm in mm

# PWM for LIDAR motor spin (10 Hz)
PWM_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWM_PIN, GPIO.OUT)
pwm = GPIO.PWM(PWM_PIN, 10)
pwm.start(50)

# Connect to Arduino
arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
time.sleep(2)
print(arduino.readline().decode().strip())  # Should print "Arduino Ready"

# Connect to LD06
lidar = serial.Serial(LIDAR_PORT, BAUD, timeout=1)
time.sleep(1)

def parse_ld06_packet(data):
    if len(data) < 47 or data[0] != 0x54 or data[1] != 0x2C:
        return []
    points = []
    n = data[3]
    if len(data) < 5 + n*3 + 2:
        return []
    for i in range(n):
        idx = 4 + i*3
        angle = struct.unpack('<H', data[idx:idx+2])[0] / 100.0
        dist = struct.unpack('<H', data[idx+2:idx+3] + b'\x00')[0]
        if dist > 0:
            points.append((angle, dist))
    return points

def get_distances(points):
    front, left, right = [], [], []
    for angle, dist in points:
        if abs(angle) <= 45:
            front.append(dist)
        elif 45 < angle <= 135:
            right.append(dist)
        elif 225 < angle <= 315 or -135 <= angle <= -45:
            left.append(dist)

    min_f = min(front) if front else 99999
    min_l = min(left) if left else 99999
    min_r = min(right) if right else 99999
    return min_f, min_l, min_r

print("Starting obstacle avoidance bicycle...")
buffer = b''

try:
    while True:
        data = lidar.read(1000)
        buffer += data

        while len(buffer) >= 47:
            header = buffer.find(b'\x54\x2C')
            if header == -1:
                buffer = b''
                break
            buffer = buffer[header:]

            pkt_len = 5 + buffer[3]*3 + 2
            if len(buffer) < pkt_len:
                break

            packet = buffer[:pkt_len]
            buffer = buffer[pkt_len:]

            points = parse_ld06_packet(packet)
            if len(points) > 10:
                f, l, r = get_distances(points)
                print(f"F:{f/10:.1f}cm  L:{l/10:.1f}cm  R:{r/10:.1f}cm")

                if f > SAFE_DIST:
                    arduino.write(b'FORWARD\n')
                else:
                    arduino.write(b'STOP\n')
                    time.sleep(0.8)

                    if l < r:
                        arduino.write(b'RIGHT\n')
                        print("← Turning RIGHT")
                    else:
                        arduino.write(b'LEFT\n')
                        print("→ Turning LEFT")
                    time.sleep(1.5)
                    arduino.write(b'FORWARD\n')

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    lidar.close()
    arduino.close()
    pwm.stop()
    GPIO.cleanup()
