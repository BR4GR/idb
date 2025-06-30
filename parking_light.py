import time
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger
from grove.grove_led import GroveLed
import requests # Import the requests library

# --- Hardware Pin Definitions ---
SONAR_PIN = 12
LED_PIN = 16

# --- Constants ---
DISTANCE_THRESHOLD_CM = 10.0
CHECK_INTERVAL_S = 0.2

# --- API Endpoints ---
API_BASE_URL = "https://dpo.been-jammin.ch/api/parking"
API_ARRIVAL_URL = f"{API_BASE_URL}/arrival"
API_DEPARTURE_URL = f"{API_BASE_URL}/departure"
API_STATUS_URL = f"{API_BASE_URL}/status" # Not used in loop, but useful for testing

# --- Sensor and Component Setup ---
sonar = GroveUltrasonicRanger(SONAR_PIN)
led = GroveLed(LED_PIN)

# --- Global State for API Logic ---
# Track the previous state of the parking spot to send events only on change
# Initialize assuming spot is initially empty (LED ON)
last_spot_state_taken = False # True if car was previously detected, False if spot was empty


# --- Helper Function for API Calls ---
def send_event_to_api(event_type):
    """Sends a POST request to the specified API endpoint."""
    url = ""
    if event_type == "arrival":
        url = API_ARRIVAL_URL
    elif event_type == "departure":
        url = API_DEPARTURE_URL
    else:
        print(f"[{time.strftime('%H:%M:%S')}] ERROR: Invalid event type '{event_type}'.")
        return

    try:
        response = requests.post(url, timeout=5) # Add a timeout for network requests
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] API call '{event_type}' successful. Response: {response.text}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] API call '{event_type}' failed. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%H:%M:%S')}] API connection error for '{event_type}': {e}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] An unexpected error occurred during API call: {e}")


# --- Main Program Loop ---
print("Parking Spot Light System Ready (with API integration).")
print(f"Checking for objects within {DISTANCE_THRESHOLD_CM:.1f} cm (Spot Taken).")
print("Ctrl+C to exit.")

# --- Initial State Check and API Event ---
# After startup, determine current spot state and send initial event to sync API
# Get an initial distance reading (it might fail once or twice after startup)
initial_distance = -1.0
for _ in range(3): # Try a few times to get a valid initial reading
    try:
        initial_distance = sonar.get_distance()
        if initial_distance >= 0:
            break
    except:
        time.sleep(0.1)

if initial_distance >= 0 and initial_distance <= DISTANCE_THRESHOLD_CM:
    # Spot is initially taken
    print(f"[{time.strftime('%H:%M:%S')}] Initial state: Spot is TAKEN (Distance: {initial_distance:.1f} cm).")
    led.off()
    last_spot_state_taken = True
    send_event_to_api("arrival") # Send arrival if spot already taken
else:
    # Spot is initially empty
    print(f"[{time.strftime('%H:%M:%S')}] Initial state: Spot is EMPTY (Distance: {initial_distance:.1f} cm).")
    led.on()
    last_spot_state_taken = False
    send_event_to_api("departure") # Send departure if spot already empty


try:
    while True:
        try:
            distance_cm = sonar.get_distance()

            if distance_cm < 0:
                print(f"[{time.strftime('%H:%M:%S')}] Sensor error or out of range. Distance: {distance_cm:.1f} cm")
                time.sleep(CHECK_INTERVAL_S) # Still sleep even if sensor fails
                continue

            current_spot_state_taken = (distance_cm <= DISTANCE_THRESHOLD_CM)

            # --- Logic for Parking Light & API Calls ---
            if current_spot_state_taken: # Spot is TAKEN
                if not last_spot_state_taken:
                    # State changed from EMPTY to TAKEN
                    print(f"[{time.strftime('%H:%M:%S')}] Distance: {distance_cm:.1f} cm. State changed: Spot TAKEN. Turning LED OFF.")
                    led.off()
                    send_event_to_api("arrival") # Send arrival event
                    last_spot_state_taken = True # Update state tracker
            else: # Spot is EMPTY
                if last_spot_state_taken:
                    # State changed from TAKEN to EMPTY
                    print(f"[{time.strftime('%H:%M:%S')}] Distance: {distance_cm:.1f} cm. State changed: Spot EMPTY. Turning LED ON.")
                    led.on()
                    send_event_to_api("departure") # Send departure event
                    last_spot_state_taken = False # Update state tracker

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] General error in loop: {e}")

        time.sleep(CHECK_INTERVAL_S)

except KeyboardInterrupt:
    print("\nParking Spot Light System stopped.")
    led.off() # Ensure LED is off when program exits cleanly
