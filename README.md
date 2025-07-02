# Smart Parking Spot Indicator (IoT Project)

## Project Overview

This project demonstrates a simple Internet of Things (IoT) system designed to indicate the occupancy status of a parking spot and report these events to a central server. It utilizes a Raspberry Pi Zero as the edge device, equipped with an ultrasonic distance sensor and an LED, simulating a common application in smart parking garages.

## Architecture Diagram: Tiers and Protocols

The system is structured into three main "Tiers" (Schichten), each interacting using specific protocols and data formats (payloads).

```plaintext

+---------------------+
|      Tier 1:        |
|  Edge Device (RPI0) |
+---------------------+
| - Ultrasonic Sensor | <--- Digital GPIO (High/Low Pulses)
| - LED               | <--- Digital GPIO (High/Low)
| - Python Script     |
+---------|-----------+
          |
          | (HTTP/S POST Requests - JSON Payload)
          |
+---------|-----------+
|      Tier 2:        |
|  Cloud/Server (API) |
+---------------------+
| - Web Server        |
| - API Endpoint      |
| - Database          |
+---------|-----------+
          |
          | (HTTP/S GET Requests - JSON Payload)
          |
+---------|-----------+
|      Tier 3:        |
|   User Interface    |
+---------------------+
| - Web Browser       |
| - Mobile App (opt.) |
+---------------------+
```

### Explanation of Tiers and Protocols

**Tier 1: Edge Device (Raspberry Pi Zero)**

* **Components:**
  * **Raspberry Pi Zero:** The core computing unit running a Python script.
  * **Ultrasonic Distance Sensor (Grove):** Detects objects (e.g., a car) by measuring distance. It communicates by measuring the *duration* of a digital pulse.
  * **LED (Grove):** Provides a visual indicator of the parking spot's status, controlled by setting a digital GPIO pin to HIGH (ON) or LOW (OFF).
* **Protocols/Communication:**
  * **GPIO (General Purpose Input/Output):** This is the direct hardware interface between the Raspberry Pi Zero and the sensors/LEDs. The `grove.py` library handles this low-level interaction.
  * **HTTP/S (Hypertext Transfer Protocol Secure):** This is the application-layer protocol used for communicating with the backend server.
    * **Method:** `POST` requests are used to send event data (`/arrival` or `/departure`).
    * **Request Payload:** No payload is sent, the only information needed is in the routes.
    * **Response Payload:** The server responds with a JSON object, indicating success or failure and providing details about the event.
      * **Example `arrival` response (on failure):**

      ```json
      {"success":false,"message":"Parking spot is already occupied"}
      ```

      * **Example `departure` response (on success):**

      ```json
      {"success":true,"message":"Car departure recorded","data":{"event_type":"departure","event_time":"2025-06-30T00:33:37.000000Z","id":12}}
      ```

**Tier 2: Cloud/Server (API)**

* **Components:** This tier represents a remote server infrastructure.
  * **Web Server:**  Listens for incoming HTTP/S requests.
  * **API Endpoint:** A specific URL (`https://dpo.been-jammin.ch/api/parking/...`) designed to receive and process the data.
  * **Database:** Stores the received parking events (arrival/departure timestamps).
* **Protocols/Communication:**
  * **HTTP/S:** Receives `POST` requests from the Edge Device.
  * **Internal Protocols:** Uses various internal protocols and database drivers to store data.
  * **HTTP/S (GET Requests):** Provides data to the User Interface (Tier 3).
    * **Method:** `GET` requests are used to retrieve status or event logs.
    * **Response Payload (Data Format):** The API returns data in JSON format for the user interface.
    * **Example `/status` response:**

    ```json
    {
      "success": true,
      "data": {
        "occupied": true,
        "status": "occupied",
        "last_event": {
          "id": 10,
          "event_type": "arrival",
          "event_time": "2024-06-30T00:14:44.000000Z"
        }
      }
    }
    ```

    * **Example `/events` response:**

    ```json
    {
      "success": true,
      "data": [
        {"id": 12, "event_type": "departure", "event_time": "2025-06-30T00:33:37.000000Z"},
        {"id": 11, "event_type": "arrival", "event_time": "2025-06-30T00:14:44.000000Z"},
        // ... more events
      ],
      "total": 12
    }
    ```

**Tier 3: User Interface**

* **Components:** This is how a human user interacts with the system.
  * **Web Browser:** Accesses a web application.
  * **curl:** from the command line.
* **Protocols/Communication:**
  * **HTTPS:** Makes `GET` requests to the Server API (Tier 2) to fetch parking status or event logs.
  * **Payload (Data Format):** Receives data in JSON format from the API.

## Project Files

The main application file is `parking_light.py`, which runs on the Raspberry Pi Zero. It continuously monitors the ultrasonic sensor and when the sensor detects a state change (spot becomes occupied or empty), it controls the LED accordingly and sends an HTTP POST request to the cloud API endpoint, effectively logging the event.

### File Structure

- `parking_light.py` - Main parking spot monitoring application with API integration
- `tea_meter.py` - Alternative sensor application for measuring liquid levels
- `blink.py` - Simple LED blinking test
- `dht.py` - Temperature and humidity sensor module
- Test files:
  - `blinkatest.py` - Blinka library hardware test
  - `button_test.py` - Button functionality test
  - `dht11_test.py` - DHT11 sensor test
  - `sonar_test.py` - Ultrasonic sensor test

## Hardware Requirements

- Raspberry Pi Zero (or similar)
- Grove Ultrasonic Distance Sensor
- Grove LED
- Grove DHT11 Temperature & Humidity Sensor (optional)
- Grove Button (for tea meter application)
- Grove Base Hat or compatible GPIO interface

## Software Dependencies

This project requires the following Python libraries:
- `grove.py` - Grove sensor library for Raspberry Pi
- `requests` - For HTTP API communication
- `time` - Built-in Python time module
- `board` and `digitalio` (from Adafruit Blinka) - For hardware abstraction

## Installation and Setup

1. Install the required Grove.py library on your Raspberry Pi:
   ```bash
   curl -sL https://github.com/Seeed-Studio/grove.py/raw/master/install.sh | sudo bash -s -
   ```

2. Install additional Python dependencies:
   ```bash
   pip3 install requests adafruit-blinka
   ```

3. Connect your Grove sensors to the appropriate pins as defined in the code
4. Run the main application:
   ```bash
   python3 parking_light.py
   ```

## API Integration

The system integrates with a remote API at `https://dpo.been-jammin.ch/api/parking/` with the following endpoints:
- `POST /arrival` - Records when a car arrives
- `POST /departure` - Records when a car leaves  
- `GET /status` - Gets current parking spot status
- `GET /events` - Gets historical parking events
