import time
from grove.grove_temperature_humidity_sensor import DHT

DHT_PIN = 5

dht_sensor = DHT("11", DHT_PIN)

print(f"--- DHT11 Sensor Test on BCM {DHT_PIN} ---")
print("Reading temperature and humidity. Press Ctrl+C to exit.")

try:
    while True:
        humi, temp = dht_sensor.read()
        if humi is None or temp is None:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to read DHT sensor.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Temperature: {temp:.1f}°C, Humidity: {humi:.1f}%")
        time.sleep(1)
except KeyboardInterrupt:
    print("DHT11 test stopped.")
