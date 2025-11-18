#!/usr/bin/env python3
import serial
import time
import math
import struct
import RPi.GPIO as GPIO  # For optional PWM
import numpy as np  # For min calculations

# Serial to LIDAR (UART)
LIDAR_PORT = '/dev/serial0'
BAUD_RATE = 230400

# Optional PWM for LIDAR speed (GPIO18, 50% duty ~5Hz scan)
PWM_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWM_PIN, GPIO.OUT)
pwm = GPIO.PWM(PWM_PIN, 1000)  # 1kHz freq
pwm.start(50)  # 50% duty cycle

# Serial to Arduino
ARDUINO_PORT = '/dev/ttyACM0'
arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
time.sleep(2)
print(arduino.readline().decode('utf-8').strip())  # "Arduino Ready"

SAFE_DISTANCE = 500  # mm (50 cm)

class LD06Parser:
    def __init__(self):
        self.scan = []

    def parse(self, data):
        if len(data) < 47:  # Min packet size
            return
        # Header: 0x54 0x2C + type (0x00/0x01), then points
        if data[0] != 0x54 or data[1] != 0x2C:
            return
        type_byte = data[2]
        point_count = data[3]
        if point_count > 90 or len(data) < (5 + point_count * 3 + 2):  # Header + points*3 + CRC
            return
        
        self.scan = []
        start_angle = None
        for i in range(point_count):
            offset = 4 + i * 3
            angle = struct.unpack('<H', data[offset:offset+2])[0] / 10.0  # 0.1° units to degrees
            dist = struct.unpack('<H', data[offset+2:offset+3] + b'\x00')[0]  # 12-bit dist in mm
            if dist == 0:  # Invalid
                continue
            if start_angle is None:
                start_angle = angle
            self.scan.append((angle, dist))
        
        # CRC check (simple XOR for verification)
        crc = 0
        for i in range(4, 4 + point_count * 3):
            crc ^= data[i]
        if crc != struct.unpack('<H', data[-2:])[0]:
            return  # Bad packet
        print(f"Parsed scan: {len(self.scan)} points, start angle {start_angle}")

def process_scan(scan):
    front_dists = []
    left_dists = []
    right_dists = []
    
    for angle, dist in scan:
        # Normalize angle to -180 to 180
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        
        if abs(angle) <= 45:  # Front ±45°
            front_dists.append(dist)
        elif -90 <= angle < -45:  # Left
            left_dists.append(dist)
        elif 45 < angle <= 90:  # Right
            right_dists.append(dist)
    
    min_front = min(front_dists) if front_dists else float('inf')
    min_left = min(left_dists) if left_dists else float('inf')
    min_right = min(right_dists) if right_dists else float('inf')
    
    return min_front, min_left, min_right

# Main loop
parser = LD06Parser()
ser = serial.Serial(LIDAR_PORT, BAUD_RATE, timeout=1)

try:
    buffer = b''
    while True:
        data = ser.read(100)  # Read chunks
        if not data:
            continue
        buffer += data
        
        # Process full packets
        while len(buffer) >= 47:
            # Find next header
            header_pos = buffer.find(b'\x54\x2C')
            if header_pos == -1:
                buffer = b''
                break
            if header_pos > 0:
                buffer = buffer[header_pos:]
            if len(buffer) < 47:
                break
            
            # Extract one packet (assume fixed ~47-275 bytes)
            pkt_len = 5 + (buffer[3] * 3) + 2
            if len(buffer) >= pkt_len:
                pkt = buffer[:pkt_len]
                parser.parse(pkt)
                buffer = buffer[pkt_len:]
                
                if parser.scan:  # Process if valid scan
                    min_front, min_left, min_right = process_scan(parser.scan)
                    
                    if min_front > SAFE_DISTANCE:
                        arduino.write(b'FORWARD\n')
                        print(f"Clear path ({min_front/10:.1f}cm): Going forward")
                    else:
                        arduino.write(b'STOP\n')
                        print(f"Obstacle ahead ({min_front/10:.1f}cm): Stopped")
                        time.sleep(1)
                        
                        if min_left <= SAFE_DISTANCE and min_right > SAFE_DISTANCE:
                            arduino.write(b'RIGHT\n')
                            print(f"Obstacle left ({min_left/10:.1f}cm): Turning right")
                        elif min_right <= SAFE_DISTANCE and min_left > SAFE_DISTANCE:
                            arduino.write(b'LEFT\n')
                            print(f"Obstacle right ({min_right/10:.1f}cm): Turning left")
                        else:
                            arduino.write(b'BACKWARD\n')
                            print("Both sides blocked: Backing up")
                    
                    time.sleep(0.1)  # ~10Hz loop

except KeyboardInterrupt:
    print("Stopping")
finally:
    ser.close()
    arduino.close()
    pwm.stop()
    GPIO.cleanup()
