import time
from grove.gpio import GPIO

BUTTON_PIN = 16
button = GPIO(BUTTON_PIN, GPIO.IN)

print(f"--- Button Test on BCM {BUTTON_PIN} ---")

try:
    while True:
        button_state = button.read()
        if button_state == 0:
            print(f"[{time.strftime('%H:%M:%S')}] Button IS PRESSED (State: {button_state})")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Button NOT PRESSED (State: {button_state})")
        time.sleep(0.2)
