import serial
import time
sdata = serial.Serial('dev/ttyS0', baudrate=9600, timeout=1)
time.sleep(2)  # wait for the serial connection to initialize

sdata.reset_input_buffer()
print("Arduino Connected")

try:
    while True:
        time.sleep(0.01)
        if sdata.in_waiting > 0:
            mydata = sdata.readline().decode('utf-8').rstrip()
            print(mydata)
except KeyboardInterrupt:
    print("Serial Comes Closed")
    sdata.close()
