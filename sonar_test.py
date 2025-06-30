import time
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

SONAR_PIN = 12

sonar = GroveUltrasonicRanger(SONAR_PIN)

print(f"--- Ultrasonic Sensor Test on BCM {SONAR_PIN} ---")
print("Move objects in front of the sensor. Place your empty cup under it.")
print("Press Ctrl+C to exit.")

try:
    while True:
        distance = sonar.get_distance()
        print(f"[{time.strftime('%H:%M:%S')}] Distance: {distance:.1f} cm")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Ultrasonic sensor test stopped.")
