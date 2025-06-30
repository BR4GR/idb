import time
from grove.gpio import GPIO
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from grove.grove_temperature_humidity_sensor import DHT
import os

# --- Hardware Pin Definitions ---
DHT_PIN = 5
BUTTON_PIN = 16
SONAR_PIN = 12

# --- Constants ---
DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM = 15.0

CALIBRATION_DELAY_S = 1.5
CALIBRATION_READS = 5

MIN_READING_INTERVAL_POURING_S = 0.1

# --- Output File Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV_FILENAME = os.path.join(SCRIPT_DIR, "session_data.csv")
CSV_HEADER = "Time,Temp,Hum,FillLevelCM"


# --- Global Variables for Program State ---
measurement_data = []
is_cup_present = False
is_measuring = False
calibrated_empty_cup_distance = DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM
read_temp = True
hum = -1
temp = -1

# --- Sensor and Component Setup ---
dht_sensor = DHT("11", DHT_PIN)
button = GPIO(BUTTON_PIN, GPIO.IN)
sonar = GroveUltrasonicRanger(SONAR_PIN)

def output_csv_results():
    global measurement_data

    if not measurement_data:
        print("--- No data collected for this pouring session. ---")
        return

    print("--- Session Data ---")
    print(CSV_HEADER)
    for row in measurement_data:
        print(f"{row[0]},{row[1]:.1f},{row[2]:.1f},{row[3]:.1f}")
    print("--- End of Session Data ---")

    try:
        with open(OUTPUT_CSV_FILENAME, "w") as f:
            f.write(CSV_HEADER)

            for row in measurement_data:
                line = f"{row[0]},{row[1]:.1f},{row[2]:.1f},{row[3]:.1f}"
                f.write(line)
        print(f"Session data successfully saved to {OUTPUT_CSV_FILENAME}")
    except IOError as e:
        print(f"ERROR: Could not write to {OUTPUT_CSV_FILENAME}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving CSV: {e}")

    measurement_data.clear()

print("System Ready. Waiting for cup...")

while True:
    current_time_str = time.strftime("%H:%M:%S")

    if not is_cup_present:
        if button.read() == 1:
            is_cup_present = True
            print(f"[{current_time_str}] Cup detected! Waiting {CALIBRATION_DELAY_S}s for stabilization...")
            time.sleep(CALIBRATION_DELAY_S)

            print(f"[{current_time_str}] Calibrating empty cup distance")
            distances = []
            for _ in range(CALIBRATION_READS):
                try:
                    dist = sonar.get_distance()
                    if dist > 0:
                        distances.append(dist)
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] Sonar calibration error: {e}")

            if distances:
                calibrated_empty_cup_distance = sum(distances) / len(distances)
                print(f"[{time.strftime('%H:%M:%S')}] Calibrated empty cup distance: {calibrated_empty_cup_distance:.1f} cm")
            else:
                calibrated_empty_cup_distance = DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM
                print(f"[{time.strftime('%H:%M:%S')}] WARNING: Failed to calibrate. Using default empty cup distance: {calibrated_empty_cup_distance:.1f} cm")

            is_measuring = True
            print(f"[{time.strftime('%H:%M:%S')}] Starting measurement...")

    # Pouring/Measuring
    if is_measuring:
        start_loop_time = time.monotonic()

        if button.read() == 0:
            is_cup_present = False
            is_measuring = False
            print(f"[{current_time_str}] Cup removed! Stopping measurement.")
            output_csv_results()
            continue

        distance_cm = -1.0
        fill_level_cm = -1.0

        if read_temp:
            hum, temp = dht_sensor.read()
            if hum is None or temp is None:
                print("DHT sensor read returned None values.")
        read_temp = not read_temp

        try:
            distance_cm = sonar.get_distance()
            fill_level_cm = calibrated_empty_cup_distance - distance_cm
        except Exception as e:
            print(f"[{current_time_str}] Sonar error: {e}")
            fill_level_cm = -1.0

        measurement_data.append((current_time_str, temp, hum, fill_level_cm))
        print(f"[{current_time_str}] Temp:{temp:.1f}°C Hum:{hum:.1f}% Fill:{fill_level_cm:.1f}cm")

        end_loop_time = time.monotonic()
        elapsed = end_loop_time - start_loop_time

