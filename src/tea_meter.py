#!/usr/bin/env python3
"""
Smart Tea/Liquid Level Meter

This module implements an IoT liquid level monitoring system that uses
an ultrasonic sensor to measure liquid levels in cups with environmental monitoring.

Author: Benjamin
Date: July 2, 2025
License: MIT
"""

import logging
import os
import time
from typing import List, Optional, Tuple

from grove.gpio import GPIO
from grove.grove_temperature_humidity_sensor import DHT
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

# --- Configuration ---
DHT_PIN = 5
BUTTON_PIN = 16
SONAR_PIN = 12

DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM = 15.0
CALIBRATION_DELAY_S = 1.5
CALIBRATION_READS = 5
MIN_READING_INTERVAL_S = 0.1
TEMP_READ_INTERVAL = 2  # Read temperature every 2 cycles to reduce load

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tea_meter.log')
    ]
)
logger = logging.getLogger(__name__)

class TeaMeter:
    """Smart liquid level meter with environmental monitoring."""
    
    def __init__(self):
        """Initialize the tea meter."""
        self.dht_sensor = DHT("11", DHT_PIN)
        self.button = GPIO(BUTTON_PIN, GPIO.IN)
        self.sonar = GroveUltrasonicRanger(SONAR_PIN)
        
        # State variables
        self.measurement_data: List[Tuple[str, float, float, float]] = []
        self.is_cup_present = False
        self.is_measuring = False
        self.calibrated_empty_cup_distance = DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM
        self.temp_read_counter = 0
        self.last_temp = -1.0
        self.last_humidity = -1.0
        
        # Output configuration
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_csv_filename = os.path.join(script_dir, "../data/tea_session_data.csv")
        self.csv_header = "Time,Temp,Hum,FillLevelCM"
        
        logger.info("Tea Meter initialized")
    
    def read_environmental_data(self) -> Tuple[float, float]:
        """Read temperature and humidity from DHT sensor.
        
        Returns:
            Tuple of (humidity, temperature) or last known values if read fails
        """
        try:
            hum, temp = self.dht_sensor.read()
            if hum is not None and temp is not None:
                self.last_humidity = hum
                self.last_temp = temp
                return hum, temp
            else:
                logger.warning("DHT sensor returned None values, using last known values")
                return self.last_humidity, self.last_temp
        except Exception as e:
            logger.error(f"DHT sensor error: {e}")
            return self.last_humidity, self.last_temp
    
    def get_distance_reading(self) -> Optional[float]:
        """Get distance reading from ultrasonic sensor.
        
        Returns:
            Distance in cm, or None if reading failed
        """
        try:
            distance = self.sonar.get_distance()
            return distance if distance > 0 else None
        except Exception as e:
            logger.error(f"Sonar sensor error: {e}")
            return None
    
    def calibrate_empty_cup(self) -> bool:
        """Calibrate the distance to empty cup bottom.
        
        Returns:
            True if calibration successful, False otherwise
        """
        logger.info("Calibrating empty cup distance...")
        distances = []
        
        for i in range(CALIBRATION_READS):
            distance = self.get_distance_reading()
            if distance is not None:
                distances.append(distance)
                logger.debug(f"Calibration read {i+1}: {distance:.1f} cm")
            else:
                logger.warning(f"Calibration read {i+1} failed")
        
        if distances:
            self.calibrated_empty_cup_distance = sum(distances) / len(distances)
            logger.info(f"Calibrated empty cup distance: {self.calibrated_empty_cup_distance:.1f} cm")
            return True
        else:
            logger.warning(f"Calibration failed, using default: {DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM:.1f} cm")
            self.calibrated_empty_cup_distance = DEFAULT_DISTANCE_TO_EMPTY_CUP_BOTTOM_CM
            return False
    
    def calculate_fill_level(self, distance: float) -> float:
        """Calculate fill level based on distance reading.
        
        Args:
            distance: Current distance reading in cm
            
        Returns:
            Fill level in cm (positive = liquid present, negative = below empty level)
        """
        return self.calibrated_empty_cup_distance - distance
    
    def save_session_data(self) -> None:
        """Save measurement data to CSV file."""
        if not self.measurement_data:
            logger.info("No data collected for this session")
            return
        
        logger.info("--- Session Data Summary ---")
        logger.info(f"Total measurements: {len(self.measurement_data)}")
        
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.output_csv_filename), exist_ok=True)
            
            with open(self.output_csv_filename, "w") as f:
                f.write(self.csv_header + "\n")
                for row in self.measurement_data:
                    line = f"{row[0]},{row[1]:.1f},{row[2]:.1f},{row[3]:.1f}\n"
                    f.write(line)
            
            logger.info(f"Session data saved to {self.output_csv_filename}")
            
            # Print summary statistics
            if self.measurement_data:
                fill_levels = [row[3] for row in self.measurement_data if row[3] > 0]
                if fill_levels:
                    max_fill = max(fill_levels)
                    avg_fill = sum(fill_levels) / len(fill_levels)
                    logger.info(f"Max fill level: {max_fill:.1f} cm, Average: {avg_fill:.1f} cm")
                    
        except IOError as e:
            logger.error(f"Could not write to {self.output_csv_filename}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving CSV: {e}")
        
        self.measurement_data.clear()
    
    def process_measurement_cycle(self) -> None:
        """Process one measurement cycle when cup is present."""
        start_time = time.monotonic()
        current_time_str = time.strftime("%H:%M:%S")
        
        # Check if cup is still present
        if self.button.read() == 0:
            logger.info("Cup removed! Stopping measurement")
            self.is_cup_present = False
            self.is_measuring = False
            self.save_session_data()
            return
        
        # Read environmental data (not every cycle to reduce load)
        if self.temp_read_counter % TEMP_READ_INTERVAL == 0:
            humidity, temperature = self.read_environmental_data()
        else:
            humidity, temperature = self.last_humidity, self.last_temp
        
        self.temp_read_counter += 1
        
        # Read distance and calculate fill level
        distance = self.get_distance_reading()
        if distance is not None:
            fill_level = self.calculate_fill_level(distance)
        else:
            fill_level = -999.0  # Error value
        
        # Store measurement
        self.measurement_data.append((current_time_str, temperature, humidity, fill_level))
        
        # Log current status
        logger.info(f"Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%, Fill: {fill_level:.1f}cm")
        
        # Maintain minimum interval
        elapsed = time.monotonic() - start_time
        sleep_time = max(0, MIN_READING_INTERVAL_S - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def wait_for_cup(self) -> None:
        """Wait for cup to be detected and start measurement."""
        if self.button.read() == 1:
            logger.info("Cup detected! Starting calibration...")
            self.is_cup_present = True
            
            # Wait for stabilization
            time.sleep(CALIBRATION_DELAY_S)
            
            # Calibrate empty cup distance
            self.calibrate_empty_cup()
            
            # Start measuring
            self.is_measuring = True
            self.temp_read_counter = 0
            logger.info("Starting measurement session...")
    
    def run(self) -> None:
        """Main measurement loop."""
        logger.info("Tea Meter System Ready")
        logger.info("Place cup on sensor and press button to start measuring")
        logger.info("Press Ctrl+C to exit")
        
        try:
            while True:
                if not self.is_cup_present:
                    self.wait_for_cup()
                    time.sleep(0.1)  # Small delay when waiting
                
                if self.is_measuring:
                    self.process_measurement_cycle()
                
        except KeyboardInterrupt:
            logger.info("Tea Meter stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            if self.measurement_data:
                logger.info("Saving final session data...")
                self.save_session_data()
            logger.info("Tea Meter shutdown complete")


def main():
    """Main entry point."""
    meter = TeaMeter()
    meter.run()


if __name__ == "__main__":
    main()

