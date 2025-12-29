#!/usr/bin/env python3
"""
Power Limiter for LED Display
Dynamically limits brightness to stay within current draw limits
"""

import logging
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class PowerLimiter:
    """
    Dynamically limits LED brightness to stay within current draw limits

    Prevents overloading power supply by calculating expected current draw
    and reducing brightness if necessary.
    """

    # WS2812B specifications (must match system_monitor.py)
    LED_VOLTAGE = 5.0  # Volts
    LED_CURRENT_PER_CHANNEL_MAX = 20.0  # mA at full brightness per channel
    LED_CURRENT_FULL_WHITE = 60.0  # mA per LED at full white

    def __init__(self,
                 led_count: int,
                 max_current_amps: float = 8.5,
                 enabled: bool = True):
        """
        Initialize power limiter

        Args:
            led_count: Total number of LEDs
            max_current_amps: Maximum allowed current in Amps
            enabled: Whether power limiting is enabled
        """
        self.led_count = led_count
        self.max_current_amps = max_current_amps
        self.enabled = enabled

        # Statistics
        self.limit_applied_count = 0
        self.last_limited_brightness = None

        logger.info(f"Power limiter initialized: {max_current_amps}A limit for {led_count} LEDs")
        logger.info(f"Max theoretical draw: {(led_count * self.LED_CURRENT_FULL_WHITE / 1000.0):.2f}A")
        logger.info(f"Power limiting: {'ENABLED' if enabled else 'DISABLED'}")

    def calculate_frame_current(self,
                                frame: np.ndarray,
                                brightness: int) -> float:
        """
        Calculate expected current draw for a frame at given brightness

        Args:
            frame: RGB frame array (led_count, 3)
            brightness: Global brightness (0-255)

        Returns:
            Expected current in Amps
        """
        if frame is None or frame.size == 0:
            return 0.0

        # Calculate brightness factor (0.0 to 1.0)
        brightness_factor = brightness / 255.0

        # Sum all RGB values across all LEDs
        total_rgb_sum = np.sum(frame)

        # Maximum possible sum if all pixels were full white
        max_possible_sum = self.led_count * 3 * 255

        # Calculate intensity factor (what fraction of max we're using)
        intensity_factor = total_rgb_sum / max_possible_sum if max_possible_sum > 0 else 0

        # Current per LED at this intensity and brightness
        current_per_led_ma = self.LED_CURRENT_FULL_WHITE * intensity_factor * brightness_factor

        # Total current in milliamps, then convert to Amps
        total_current_ma = current_per_led_ma * self.led_count
        total_current_a = total_current_ma / 1000.0

        return total_current_a

    def limit_brightness_for_frame(self,
                                   frame: np.ndarray,
                                   requested_brightness: int) -> Tuple[int, bool]:
        """
        Calculate safe brightness level for a frame to stay within current limit

        Args:
            frame: RGB frame array (led_count, 3)
            requested_brightness: Requested brightness level (0-255)

        Returns:
            Tuple of (safe_brightness, was_limited)
        """
        if not self.enabled:
            return requested_brightness, False

        if frame is None or frame.size == 0:
            return requested_brightness, False

        # Calculate current at requested brightness
        current_at_requested = self.calculate_frame_current(frame, requested_brightness)

        # If we're under the limit, no adjustment needed
        if current_at_requested <= self.max_current_amps:
            return requested_brightness, False

        # Calculate what brightness would keep us at the limit
        # current = (brightness/255) * base_current
        # So: safe_brightness = (max_current / current_at_full) * 255

        # First calculate current at full brightness for this frame
        current_at_full = self.calculate_frame_current(frame, 255)

        if current_at_full <= 0:
            return requested_brightness, False

        # Calculate brightness factor needed to stay at limit
        safe_brightness_factor = self.max_current_amps / current_at_full

        # Convert to brightness value (0-255)
        safe_brightness = int(safe_brightness_factor * 255)

        # Clamp to valid range
        safe_brightness = max(0, min(255, safe_brightness))

        # Only limit if we're actually reducing brightness
        if safe_brightness < requested_brightness:
            self.limit_applied_count += 1
            self.last_limited_brightness = safe_brightness

            if self.limit_applied_count % 100 == 1:  # Log occasionally
                logger.info(f"Power limit active: reducing brightness {requested_brightness} → {safe_brightness} "
                          f"(current would be {current_at_requested:.2f}A, limit {self.max_current_amps}A)")

            return safe_brightness, True

        return requested_brightness, False

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable power limiting

        Args:
            enabled: Whether to enable power limiting
        """
        self.enabled = enabled
        logger.info(f"Power limiting {'ENABLED' if enabled else 'DISABLED'}")

        if not enabled:
            self.limit_applied_count = 0
            self.last_limited_brightness = None

    def set_max_current(self, max_current_amps: float) -> None:
        """
        Set maximum current limit

        Args:
            max_current_amps: Maximum allowed current in Amps
        """
        if max_current_amps > 0:
            self.max_current_amps = max_current_amps
            logger.info(f"Power limit set to {max_current_amps}A")
        else:
            logger.warning(f"Invalid current limit: {max_current_amps}A")

    def get_stats(self) -> dict:
        """
        Get power limiter statistics

        Returns:
            Dictionary with limiter stats
        """
        return {
            'enabled': self.enabled,
            'max_current_amps': self.max_current_amps,
            'limit_applied_count': self.limit_applied_count,
            'last_limited_brightness': self.last_limited_brightness,
            'max_theoretical_current_a': self.led_count * self.LED_CURRENT_FULL_WHITE / 1000.0
        }
