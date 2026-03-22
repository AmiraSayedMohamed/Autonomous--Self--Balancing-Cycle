#!/usr/bin/env python3
import serial
import time
import struct
import threading
import RPi.GPIO as GPIO
from flask import Flask, Response, render_template, request
from picamera2 import Picamera2
from PIL import Image
import io

app = Flask(__name__)

# ================== CONFIG ==================
LIDAR_PORT = '/dev/serial0'
ARDUINO_PORT = '/dev/ttyACM0'          # check with ls /dev/tty*
BAUD = 230400
SAFE_DIST = 500  # mm (50 cm)

PWM_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWM_PIN, GPIO.OUT)
pwm = GPIO.PWM(PWM_PIN, 10)
pwm.start(50)

# Serial connections
arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
time.sleep(2)
print(arduino.readline().decode().strip())

lidar = serial.Serial(LIDAR_PORT, BAUD, timeout=1)
time.sleep(1)

# Camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

# Global state
auto_mode = False
avoidance_thread = None
buffer = b''

# ================== LIDAR PARSING (your original, kept) ==================
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
    return (min(front) if front else 99999,
            min(left) if left else 99999,
            min(right) if right else 99999)

# ================== AVOIDANCE THREAD ==================
def avoidance_loop():
    global auto_mode, buffer
    print("Obstacle avoidance thread started")
    while auto_mode:
        try:
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
                    print(f"F:{f/10:.1f}cm L:{l/10:.1f}cm R:{r/10:.1f}cm")

                    if f > SAFE_DIST:
                        arduino.write(b'FORWARD\n')
                    else:
                        arduino.write(b'STOP\n')
                        time.sleep(0.8)

                        # Turn + automatic counter-turn to straighten wheel
                        if l < r:
                            turn_cmd = b'RIGHT\n'
                            counter_cmd = b'LEFT\n'
                            print("← Turning RIGHT (then auto-center)")
                        else:
                            turn_cmd = b'LEFT\n'
                            counter_cmd = b'RIGHT\n'
                            print("→ Turning LEFT (then auto-center)")

                        arduino.write(turn_cmd)
                        time.sleep(1.0)      # turn duration
                        arduino.write(counter_cmd)
                        time.sleep(1.0)      # counter-turn to center wheel
                        arduino.write(b'FORWARD\n')
        except Exception as e:
            print("LIDAR error:", e)
            break
    arduino.write(b'STOP\n')
    print("Avoidance stopped")

# ================== CAMERA STREAM ==================
def generate():
    while True:
        array = picam2.capture_array()
        img = Image.fromarray(array)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.getvalue() + b'\r\n')

# ================== FLASK ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/command/<cmd>')
def command(cmd):
    cmds = {
        'STRAIGHT': b'FORWARD\n',
        'FORWARD': b'FORWARD\n',
        'BACKWARD': b'BACKWARD\n',
        'STOP': b'STOP\n',
        'LEFT': b'LEFT\n',
        'RIGHT': b'RIGHT\n'
    }
    if cmd in cmds:
        arduino.write(cmds[cmd])
        return 'OK'
    return 'Invalid'

@app.route('/start_auto')
def start_auto():
    global auto_mode, avoidance_thread
    auto_mode = True
    if avoidance_thread is None or not avoidance_thread.is_alive():
        avoidance_thread = threading.Thread(target=avoidance_loop, daemon=True)
        avoidance_thread.start()
    return 'Auto mode started'

@app.route('/stop_auto')
def stop_auto():
    global auto_mode
    auto_mode = False
    arduino.write(b'STOP\n')
    return 'Auto mode stopped'

# ================== RUN ==================
if __name__ == '__main__':
    try:
        print("Starting Bicycle Dashboard on http://raspberrypi.local:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        lidar.close()
        arduino.close()
        pwm.stop()
        GPIO.cleanup()
        picam2.stop()