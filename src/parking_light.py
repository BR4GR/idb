#!/usr/bin/env python3
"""
Smart Parking Spot Indicator - Main Application

This module implements an IoT parking spot monitoring system that uses
an ultrasonic sensor to detect vehicle presence and reports events to a cloud API.

Author: Benjamin
Date: July 2, 2025
License: MIT
"""

import logging
import time
from typing import Optional

import requests
from grove.grove_led import GroveLed
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

# --- Configuration ---
SONAR_PIN = 12
LED_PIN = 16
DISTANCE_THRESHOLD_CM = 10.0
CHECK_INTERVAL_S = 0.2
API_TIMEOUT_S = 5
MAX_RETRY_ATTEMPTS = 3
SENSOR_RETRY_DELAY_S = 0.1

# --- API Configuration ---
API_BASE_URL = "https://dpo.been-jammin.ch/api/parking"
API_ENDPOINTS = {
    "arrival": f"{API_BASE_URL}/arrival",
    "departure": f"{API_BASE_URL}/departure",
    "status": f"{API_BASE_URL}/status"
}

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('parking_spot.log')
    ]
)
logger = logging.getLogger(__name__)

class ParkingSpotMonitor:
    """Main class for monitoring parking spot occupancy."""
    
    def __init__(self):
        """Initialize the parking spot monitor."""
        self.sonar = GroveUltrasonicRanger(SONAR_PIN)
        self.led = GroveLed(LED_PIN)
        self.last_spot_state_taken = False
        logger.info("Parking Spot Monitor initialized")
    
    def get_sensor_reading(self) -> Optional[float]:
        """Get a reliable distance reading from the ultrasonic sensor.
        
        Returns:
            Distance in cm, or None if reading failed
        """
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                distance = self.sonar.get_distance()
                if distance >= 0:
                    return distance
            except Exception as e:
                logger.warning(f"Sensor reading attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    time.sleep(SENSOR_RETRY_DELAY_S)
        
        logger.error("All sensor reading attempts failed")
        return None
    
    def send_event_to_api(self, event_type: str) -> bool:
        """Send a parking event to the API.
        
        Args:
            event_type: Either 'arrival' or 'departure'
            
        Returns:
            True if successful, False otherwise
        """
        if event_type not in API_ENDPOINTS:
            logger.error(f"Invalid event type: {event_type}")
            return False
        
        url = API_ENDPOINTS[event_type]
        
        try:
            response = requests.post(url, timeout=API_TIMEOUT_S)
            if response.status_code == 200:
                logger.info(f"API call '{event_type}' successful: {response.text}")
                return True
            else:
                logger.warning(f"API call '{event_type}' failed. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"API call '{event_type}' timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f"API connection error for '{event_type}': Unable to connect to server")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error for '{event_type}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error during API call '{event_type}': {e}")
        
        return False
    
    def update_led_state(self, spot_taken: bool) -> None:
        """Update LED based on parking spot state.
        
        Args:
            spot_taken: True if spot is occupied, False if empty
        """
        try:
            if spot_taken:
                self.led.off()  # LED off when spot is taken
            else:
                self.led.on()   # LED on when spot is empty
        except Exception as e:
            logger.error(f"Failed to update LED state: {e}")
    
    def initialize_state(self) -> None:
        """Initialize the parking spot state on startup."""
        logger.info("Initializing parking spot state...")
        
        initial_distance = self.get_sensor_reading()
        
        if initial_distance is not None:
            spot_taken = initial_distance <= DISTANCE_THRESHOLD_CM
            self.last_spot_state_taken = spot_taken
            self.update_led_state(spot_taken)
            
            event_type = "arrival" if spot_taken else "departure"
            logger.info(f"Initial state: Spot {'TAKEN' if spot_taken else 'EMPTY'} (Distance: {initial_distance:.1f} cm)")
            self.send_event_to_api(event_type)
        else:
            logger.warning("Failed to get initial sensor reading, assuming spot is empty")
            self.last_spot_state_taken = False
            self.update_led_state(False)
    
    def process_sensor_reading(self, distance: float) -> None:
        """Process a sensor reading and handle state changes.
        
        Args:
            distance: Distance reading in cm
        """
        current_spot_taken = distance <= DISTANCE_THRESHOLD_CM
        
        # Check for state change
        if current_spot_taken != self.last_spot_state_taken:
            if current_spot_taken:
                logger.info(f"Distance: {distance:.1f} cm. State changed: Spot TAKEN")
                self.update_led_state(True)
                self.send_event_to_api("arrival")
            else:
                logger.info(f"Distance: {distance:.1f} cm. State changed: Spot EMPTY")
                self.update_led_state(False)
                self.send_event_to_api("departure")
            
            self.last_spot_state_taken = current_spot_taken
    
    def cleanup(self) -> None:
        """Clean up resources on shutdown."""
        try:
            self.led.off()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run(self) -> None:
        """Main monitoring loop."""
        logger.info("Parking Spot Light System Ready (with API integration)")
        logger.info(f"Monitoring for objects within {DISTANCE_THRESHOLD_CM:.1f} cm")
        logger.info("Press Ctrl+C to exit")
        
        self.initialize_state()
        
        try:
            while True:
                distance = self.get_sensor_reading()
                
                if distance is not None:
                    self.process_sensor_reading(distance)
                else:
                    logger.warning("Failed to get sensor reading, skipping this cycle")
                
                time.sleep(CHECK_INTERVAL_S)
                
        except KeyboardInterrupt:
            logger.info("Parking Spot Light System stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    monitor = ParkingSpotMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
