#!/usr/bin/env python3
"""
LED Driver for WS2812B panels via Raspberry Pi GPIO
Wraps rpi-ws281x library with clean interface
"""

import logging
import numpy as np
from typing import Tuple

try:
    from rpi_ws281x import PixelStrip, Color, ws
    RPI_WS281X_AVAILABLE = True
except ImportError:
    RPI_WS281X_AVAILABLE = False
    # Mock for development on non-Raspberry Pi systems
    class Color:
        @staticmethod
        def __call__(r, g, b):
            return (r << 16) | (g << 8) | b

    class PixelStrip:
        def __init__(self, *args, **kwargs):
            pass
        def begin(self):
            pass
        def setPixelColor(self, n, color):
            pass
        def show(self):
            pass
        def setBrightness(self, b):
            pass
        def numPixels(self):
            return 1024

    class ws:
        WS2811_STRIP_GRB = 0


logger = logging.getLogger(__name__)


class LEDDriver:
    """
    LED Driver for WS2812B LED strips/panels

    Wraps rpi-ws281x library to provide clean interface for display control
    """

    # LED strip configuration defaults
    DEFAULT_LED_PIN = 18          # GPIO pin (BCM numbering)
    DEFAULT_LED_FREQ_HZ = 800000  # LED signal frequency (usually 800khz)
    DEFAULT_LED_DMA = 10          # DMA channel
    DEFAULT_LED_BRIGHTNESS = 128  # Initial brightness (0-255)
    DEFAULT_LED_INVERT = False    # Invert signal for NPN transistor
    DEFAULT_LED_CHANNEL = 0       # 0 or 1
    DEFAULT_LED_STRIP = ws.WS2811_STRIP_GRB  # Strip type (GRB for most WS2812B)

    def __init__(self,
                 led_count: int,
                 gpio_pin: int = DEFAULT_LED_PIN,
                 freq_hz: int = DEFAULT_LED_FREQ_HZ,
                 dma: int = DEFAULT_LED_DMA,
                 brightness: int = DEFAULT_LED_BRIGHTNESS,
                 invert: bool = DEFAULT_LED_INVERT,
                 channel: int = DEFAULT_LED_CHANNEL,
                 strip_type: int = DEFAULT_LED_STRIP):
        """
        Initialize LED driver

        Args:
            led_count: Total number of LEDs in the strip
            gpio_pin: GPIO pin number (BCM numbering, must support PWM)
            freq_hz: LED signal frequency in Hz
            dma: DMA channel to use
            brightness: Initial brightness (0-255)
            invert: True to invert signal
            channel: PWM channel (0 or 1)
            strip_type: LED strip type constant
        """
        self.led_count = led_count
        self.gpio_pin = gpio_pin
        self.brightness = brightness

        logger.info(f"Initializing LED driver: {led_count} LEDs on GPIO {gpio_pin}")

        # Check if running on Raspberry Pi
        if not RPI_WS281X_AVAILABLE:
            logger.warning("rpi-ws281x not available - running in MOCK MODE")
            logger.warning("LED output will not work. Install rpi-ws281x on Raspberry Pi.")

        # Create PixelStrip object
        self.strip = PixelStrip(
            led_count,
            gpio_pin,
            freq_hz,
            dma,
            invert,
            brightness,
            channel,
            strip_type
        )

        # Initialize the library (must be called once)
        try:
            self.strip.begin()
            logger.info("LED driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LED driver: {e}")
            logger.error("Make sure you're running with sudo or have GPIO permissions")
            raise

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """
        Set color for a single LED

        Args:
            index: LED index (0 to led_count-1)
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        if 0 <= index < self.led_count:
            color = Color(r, g, b)
            self.strip.setPixelColor(index, color)
        else:
            logger.warning(f"LED index {index} out of range (0-{self.led_count-1})")

    def set_frame(self, rgb_array: np.ndarray) -> None:
        """
        Set all LEDs from numpy array

        Args:
            rgb_array: NumPy array of shape (led_count, 3) with RGB values
        """
        if rgb_array.shape != (self.led_count, 3):
            logger.error(f"Invalid frame shape: {rgb_array.shape}, expected ({self.led_count}, 3)")
            return

        # Set all pixels from array
        for i in range(self.led_count):
            r, g, b = rgb_array[i]
            color = Color(int(r), int(g), int(b))
            self.strip.setPixelColor(i, color)

    def show(self) -> None:
        """
        Update the physical LEDs with buffered colors
        Call this after setting pixels to make changes visible
        """
        self.strip.show()

    def clear(self) -> None:
        """Clear all LEDs (set to black)"""
        for i in range(self.led_count):
            self.strip.setPixelColor(i, Color(0, 0, 0))

    def set_brightness(self, brightness: int) -> None:
        """
        Set global brightness level

        Args:
            brightness: Brightness level (0-255)
        """
        if 0 <= brightness <= 255:
            self.brightness = brightness
            self.strip.setBrightness(brightness)
            logger.info(f"Brightness set to {brightness}")
        else:
            logger.warning(f"Invalid brightness {brightness}, must be 0-255")

    def get_brightness(self) -> int:
        """Get current brightness level"""
        return self.brightness

    def fill(self, r: int, g: int, b: int) -> None:
        """
        Fill all LEDs with a single color

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        color = Color(r, g, b)
        for i in range(self.led_count):
            self.strip.setPixelColor(i, color)

    def get_led_count(self) -> int:
        """Get total number of LEDs"""
        return self.led_count


class MockLEDDriver(LEDDriver):
    """
    Mock LED driver for testing without hardware
    Logs operations instead of controlling actual LEDs
    """

    def __init__(self, led_count: int, **kwargs):
        """Initialize mock driver"""
        self.led_count = led_count
        self.brightness = kwargs.get('brightness', 128)
        self.gpio_pin = kwargs.get('gpio_pin', 18)

        # Create mock buffer
        self.buffer = np.zeros((led_count, 3), dtype=np.uint8)

        logger.info(f"Mock LED driver initialized: {led_count} LEDs")
        logger.info("Running in MOCK MODE - no hardware will be controlled")

    def set_pixel(self, index: int, r: int, g: int, b: int) -> None:
        """Set pixel in mock buffer"""
        if 0 <= index < self.led_count:
            self.buffer[index] = [r, g, b]

    def set_frame(self, rgb_array: np.ndarray) -> None:
        """Set frame in mock buffer"""
        if rgb_array.shape == (self.led_count, 3):
            self.buffer = rgb_array.copy()

    def show(self) -> None:
        """Mock show - just log"""
        non_black = np.sum(np.any(self.buffer > 0, axis=1))
        logger.debug(f"Mock show: {non_black}/{self.led_count} LEDs lit")

    def clear(self) -> None:
        """Clear mock buffer"""
        self.buffer.fill(0)

    def set_brightness(self, brightness: int) -> None:
        """Set mock brightness"""
        if 0 <= brightness <= 255:
            self.brightness = brightness
            logger.debug(f"Mock brightness set to {brightness}")

    def fill(self, r: int, g: int, b: int) -> None:
        """Fill mock buffer"""
        self.buffer[:] = [r, g, b]
