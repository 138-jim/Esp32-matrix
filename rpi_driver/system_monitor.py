#!/usr/bin/env python3
"""
System Monitor for LED Display Driver
Monitors CPU, RAM, and calculates power consumption
"""

import logging
import psutil
import numpy as np
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitors system resources and calculates power consumption
    """

    # WS2812B LED specifications
    # Each LED has 3 channels (R, G, B)
    # At 5V and full brightness:
    # - Per channel: ~6.67mA (20mA / 3)
    # - Full white (all channels max): ~20mA per LED
    # - Power per LED at full white: 0.1W (20mA * 5V)
    LED_VOLTAGE = 5.0  # Volts
    LED_CURRENT_PER_CHANNEL_MAX = 6.67  # mA at full brightness per channel
    LED_CURRENT_FULL_WHITE = 20.0  # mA per LED at full white

    # Raspberry Pi idle power consumption estimates (in Watts)
    # These are baseline values - actual will vary with model
    PI_MODELS = {
        'Pi 4': {'idle': 2.7, 'load': 6.4},
        'Pi 3': {'idle': 1.4, 'load': 3.7},
        'Pi 5': {'idle': 3.3, 'load': 8.0},
        'Unknown': {'idle': 2.5, 'load': 5.0}
    }

    def __init__(self, led_driver=None, led_count: int = 1024):
        """
        Initialize system monitor

        Args:
            led_driver: LED driver instance for brightness info
            led_count: Total number of LEDs
        """
        self.led_driver = led_driver
        self.led_count = led_count
        self.pi_model = self._detect_pi_model()

        logger.info(f"System monitor initialized - Detected: {self.pi_model}")
        logger.info(f"Monitoring {led_count} WS2812B LEDs")

    def _detect_pi_model(self) -> str:
        """
        Detect Raspberry Pi model from /proc/cpuinfo

        Returns:
            Pi model name
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Model' in line:
                        if 'Raspberry Pi 5' in line:
                            return 'Pi 5'
                        elif 'Raspberry Pi 4' in line:
                            return 'Pi 4'
                        elif 'Raspberry Pi 3' in line:
                            return 'Pi 3'
            return 'Unknown'
        except:
            return 'Unknown'

    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage

        Returns:
            CPU usage as percentage (0-100)
        """
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0

    def get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature in Celsius

        Returns:
            Temperature in Celsius, or None if unavailable
        """
        try:
            # Try thermal_zone method (works on most Pi models)
            temp_path = Path('/sys/class/thermal/thermal_zone0/temp')
            if temp_path.exists():
                temp = int(temp_path.read_text().strip()) / 1000.0
                return round(temp, 1)
        except Exception as e:
            logger.debug(f"Could not read CPU temperature: {e}")
        return None

    def get_ram_usage(self) -> Dict[str, float]:
        """
        Get RAM usage information

        Returns:
            Dictionary with total, used, free, and percent
        """
        try:
            mem = psutil.virtual_memory()
            return {
                'total_mb': round(mem.total / (1024 * 1024), 1),
                'used_mb': round(mem.used / (1024 * 1024), 1),
                'free_mb': round(mem.available / (1024 * 1024), 1),
                'percent': round(mem.percent, 1)
            }
        except Exception as e:
            logger.error(f"Error getting RAM usage: {e}")
            return {
                'total_mb': 0,
                'used_mb': 0,
                'free_mb': 0,
                'percent': 0
            }

    def estimate_pi_power(self) -> float:
        """
        Estimate Raspberry Pi power consumption based on CPU usage

        Returns:
            Estimated power in Watts
        """
        try:
            cpu_percent = self.get_cpu_usage()
            model_specs = self.PI_MODELS.get(self.pi_model, self.PI_MODELS['Unknown'])

            # Linear interpolation between idle and load power
            idle_power = model_specs['idle']
            load_power = model_specs['load']
            estimated_power = idle_power + (load_power - idle_power) * (cpu_percent / 100.0)

            return round(estimated_power, 2)
        except Exception as e:
            logger.error(f"Error estimating Pi power: {e}")
            return 0.0

    def calculate_led_power(self, frame: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Calculate LED power consumption based on current frame colors and brightness

        WS2812B power consumption:
        - Each channel (R, G, B) at max: ~6.67mA at 5V
        - Full white LED: ~20mA at 5V = 0.1W
        - Power scales linearly with color intensity and brightness

        Args:
            frame: Current frame array (height, width, 3) or None

        Returns:
            Dictionary with current_ma, current_a, power_w, max_power_w
        """
        try:
            # Get current brightness (0-255)
            if self.led_driver:
                brightness = self.led_driver.get_brightness()
            else:
                brightness = 128  # Default fallback

            brightness_factor = brightness / 255.0

            if frame is not None:
                # Calculate actual power based on frame content
                # Sum all RGB values across all pixels
                total_rgb_sum = np.sum(frame)  # Sum of all R+G+B values
                max_possible_sum = self.led_count * 3 * 255  # Max if all pixels full white

                # Calculate what fraction of max power we're using
                intensity_factor = total_rgb_sum / max_possible_sum

                # Current per LED at this intensity and brightness
                current_per_led_ma = self.LED_CURRENT_FULL_WHITE * intensity_factor * brightness_factor

                # Total current
                total_current_ma = current_per_led_ma * self.led_count
            else:
                # No frame available - estimate conservatively
                # Assume 30% average intensity (typical for most content)
                avg_intensity = 0.3
                current_per_led_ma = self.LED_CURRENT_FULL_WHITE * avg_intensity * brightness_factor
                total_current_ma = current_per_led_ma * self.led_count

            total_current_a = total_current_ma / 1000.0
            power_w = total_current_a * self.LED_VOLTAGE

            # Maximum possible power (all LEDs full white at current brightness)
            max_current_ma = self.LED_CURRENT_FULL_WHITE * self.led_count * brightness_factor
            max_power_w = (max_current_ma / 1000.0) * self.LED_VOLTAGE

            return {
                'current_ma': round(total_current_ma, 1),
                'current_a': round(total_current_a, 2),
                'power_w': round(power_w, 2),
                'max_power_w': round(max_power_w, 2),
                'brightness_percent': round(brightness_factor * 100, 1)
            }

        except Exception as e:
            logger.error(f"Error calculating LED power: {e}")
            return {
                'current_ma': 0,
                'current_a': 0,
                'power_w': 0,
                'max_power_w': 0,
                'brightness_percent': 0
            }

    def get_total_power(self, frame: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Get total system power consumption

        Args:
            frame: Current frame for LED power calculation

        Returns:
            Dictionary with pi_power_w, led_power_w, total_power_w
        """
        pi_power = self.estimate_pi_power()
        led_stats = self.calculate_led_power(frame)

        return {
            'pi_power_w': pi_power,
            'led_power_w': led_stats['power_w'],
            'led_max_power_w': led_stats['max_power_w'],
            'total_power_w': round(pi_power + led_stats['power_w'], 2),
            'led_current_a': led_stats['current_a']
        }

    def get_all_stats(self, frame: Optional[np.ndarray] = None) -> Dict:
        """
        Get all system statistics

        Args:
            frame: Current frame for LED power calculation

        Returns:
            Dictionary with all system stats
        """
        ram = self.get_ram_usage()
        power = self.get_total_power(frame)
        temp = self.get_cpu_temperature()

        return {
            'cpu_percent': self.get_cpu_usage(),
            'cpu_temp_c': temp,
            'ram_used_mb': ram['used_mb'],
            'ram_total_mb': ram['total_mb'],
            'ram_percent': ram['percent'],
            'pi_model': self.pi_model,
            'pi_power_w': power['pi_power_w'],
            'led_power_w': power['led_power_w'],
            'led_max_power_w': power['led_max_power_w'],
            'total_power_w': power['total_power_w'],
            'led_current_a': power['led_current_a'],
            'led_count': self.led_count
        }
