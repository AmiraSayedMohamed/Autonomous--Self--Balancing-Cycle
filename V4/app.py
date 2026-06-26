#!/usr/bin/env python3
import serial
import time
import struct
import threading
from flask import Flask, Response, render_template
from picamera2 import Picamera2
from PIL import Image
import io

app = Flask(__name__)

# ================== CONFIG ==================
LIDAR_PORT = '/dev/serial0'
ARDUINO_PORT = '/dev/ttyACM0'
BAUD_LIDAR = 230400
BAUD_ARDUINO = 115200
SAFE_DIST = 450  # mm ≈ 45cm

# Serial Connections
try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_ARDUINO, timeout=0.1)
    lidar = serial.Serial(LIDAR_PORT, BAUD_LIDAR, timeout=0.1)
    print("✅ Connected to Arduino and LiDAR successfully")
except Exception as e:
    print("❌ Serial Error:", e)
    print("Run: ls /dev/tty*   to check ports")

time.sleep(2)

# Camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (800, 600)}))
picam2.start()

# Global
auto_mode = False
buffer = b''
lock = threading.Lock()

# ================== LIDAR FUNCTIONS ==================
def parse_ld06_packet(data):
    if len(data) < 47 or data[0] != 0x54 or data[1] != 0x2C:
        return []
    try:
        n = data[3]
        points = []
        for i in range(n):
            idx = 4 + i * 3
            angle = struct.unpack('<H', data[idx:idx+2])[0] / 100.0
            dist = struct.unpack('<H', data[idx+2:idx+4])[0]
            if 100 < dist < 12000:
                points.append((angle - 180, dist))  # angle offset
        return points
    except:
        return []

def get_distances(points):
    front = [d for a, d in points if -45 <= a <= 45]
    left  = [d for a, d in points if 45 < a <= 135]
    right = [d for a, d in points if -135 <= a < -45]
    return (min(front) if front else 99999,
            min(left) if left else 99999,
            min(right) if right else 99999)

# ================== AVOIDANCE ==================
def avoidance_loop():
    global auto_mode, buffer
    print("🚨 Obstacle Avoidance Started")
    while auto_mode:
        try:
            data = lidar.read(1200)
            if data:
                with lock:
                    buffer += data
                while len(buffer) >= 47:
                    header = buffer.find(b'\x54\x2C')
                    if header == -1:
                        buffer = b''
                        break
                    buffer = buffer[header:]
                    pkt_len = 5 + buffer[3]*3 + 2
                    if len(buffer) < pkt_len: break
                    packet = buffer[:pkt_len]
                    buffer = buffer[pkt_len:]

                    points = parse_ld06_packet(packet)
                    if len(points) > 8:
                        f, l, r = get_distances(points)
                        print(f"📡 F:{f/10:.1f}cm  L:{l/10:.1f}cm  R:{r/10:.1f}cm")

                        if f > SAFE_DIST:
                            arduino.write(b'FORWARD\n')
                        else:
                            arduino.write(b'STOP\n')
                            time.sleep(0.5)
                            arduino.write(b'LEFT\n' if l < r else b'RIGHT\n')
                            time.sleep(1.0)
        except:
            time.sleep(0.2)
    arduino.write(b'STOP\n')
    print("🛑 Avoidance Stopped")

# ================== CAMERA STREAM ==================
def generate():
    while True:
        array = picam2.capture_array()
        img = Image.fromarray(array)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.getvalue() + b'\r\n')

# ================== ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/command/<cmd>')
def command(cmd):
    valid_cmds = ['FORWARD', 'BACKWARD', 'STOP', 'LEFT', 'RIGHT', 'STRAIGHT']
    if cmd in valid_cmds:
        send_cmd = b'STRAIGHT\n' if cmd == 'STRAIGHT' else (cmd + '\n').encode()
        arduino.write(send_cmd)
        return 'OK'
    return 'Invalid', 400

@app.route('/start_auto')
def start_auto():
    global auto_mode
    with lock:
        auto_mode = True
    threading.Thread(target=avoidance_loop, daemon=True).start()
    return 'Auto Started'

@app.route('/stop_auto')
def stop_auto():
    global auto_mode
    auto_mode = False
    arduino.write(b'STOP\n')
    return 'Auto Stopped'

# ================== RUN ==================
if __name__ == '__main__':
    try:
        print("🌐 Server running on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        auto_mode = False
        arduino.write(b'STOP\n')
        lidar.close()
        arduino.close()
        picam2.stop()