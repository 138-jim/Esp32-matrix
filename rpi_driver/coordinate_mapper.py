#!/usr/bin/env python3
"""
Coordinate Mapper for LED Panel System
Maps virtual 2D coordinates to physical LED indices with rotation support
"""

import logging
import numpy as np
from typing import Dict, Any, Tuple
import threading

logger = logging.getLogger(__name__)


class CoordinateMapper:
    """
    Maps virtual 2D frame coordinates to physical LED strip indices

    Handles:
    - Multiple panel positions and rotations
    - Serpentine (zigzag) wiring within panels
    - Pre-computed lookup tables for fast mapping
    - Thread-safe hot-reload of configuration
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize coordinate mapper with configuration

        Args:
            config: Panel configuration dictionary
        """
        self.config = config
        self.lock = threading.Lock()

        # Extract configuration
        self.grid = config['grid']
        self.panels = config['panels']

        self.panel_width = self.grid['panel_width']
        self.panel_height = self.grid['panel_height']
        self.grid_width = self.grid['grid_width']
        self.grid_height = self.grid['grid_height']

        # Calculate total dimensions
        self.total_width = self.grid_width * self.panel_width
        self.total_height = self.grid_height * self.panel_height
        self.total_leds = len(self.panels) * self.panel_width * self.panel_height

        # Build lookup table
        self.lut = None
        self.build_lookup_table()

        logger.info(f"Coordinate mapper initialized: {self.total_width}x{self.total_height} "
                   f"({self.total_leds} LEDs)")

    def build_lookup_table(self) -> None:
        """
        Build lookup table for fast coordinate mapping

        Lookup table structure: lut[physical_led_index] = (virtual_y, virtual_x)
        """
        with self.lock:
            logger.info("Building coordinate lookup table...")

            # Initialize lookup table: [physical_index] -> (virt_y, virt_x)
            self.lut = np.zeros((self.total_leds, 2), dtype=np.int16)

            physical_index = 0

            # Iterate through panels in order of their ID (physical LED order)
            sorted_panels = sorted(self.panels, key=lambda p: p['id'])

            for panel in sorted_panels:
                panel_id = panel['id']
                pos_x, pos_y = panel['position']
                rotation = panel['rotation']

                # Virtual coordinate base (top-left of this panel in virtual space)
                base_x = pos_x * self.panel_width
                base_y = pos_y * self.panel_height

                logger.debug(f"Panel {panel_id}: position=[{pos_x},{pos_y}], "
                           f"rotation={rotation}, base=({base_x},{base_y})")

                # Iterate through each LED in this panel (physical order)
                leds_per_panel = self.panel_width * self.panel_height
                for led_idx in range(leds_per_panel):
                    # Decode LED index to panel-local coordinates
                    local_x, local_y = self._decode_led_index(
                        led_idx, self.panel_width, self.panel_height
                    )

                    # Apply rotation transformation
                    rotated_x, rotated_y = self._apply_rotation(
                        local_x, local_y, rotation,
                        self.panel_width, self.panel_height
                    )

                    # Translate to virtual coordinates
                    virt_x = base_x + rotated_x
                    virt_y = base_y + rotated_y

                    # Store in lookup table
                    if physical_index < self.total_leds:
                        self.lut[physical_index] = [virt_y, virt_x]
                        physical_index += 1

            logger.info(f"Lookup table built: {physical_index} LED mappings")

    def _decode_led_index(self, idx: int, width: int, height: int) -> Tuple[int, int]:
        """
        Convert LED index to panel-local coordinates

        Assumes serpentine (zigzag) wiring:
        - Even rows: left to right (0→width-1)
        - Odd rows: right to left (width-1→0)

        Args:
            idx: LED index within panel (0 to width*height-1)
            width: Panel width in pixels
            height: Panel height in pixels

        Returns:
            Tuple of (x, y) panel-local coordinates
        """
        row = idx // width
        col = idx % width

        # Serpentine: reverse direction on odd rows
        if row % 2 == 1:
            col = width - 1 - col

        return col, row

    def _apply_rotation(self, x: int, y: int, rotation: int,
                       width: int, height: int) -> Tuple[int, int]:
        """
        Apply rotation transformation to coordinates

        Args:
            x: X coordinate
            y: Y coordinate
            rotation: Rotation angle (0, 90, 180, 270)
            width: Panel width
            height: Panel height

        Returns:
            Tuple of (rotated_x, rotated_y)
        """
        if rotation == 0:
            return x, y
        elif rotation == 90:
            # 90° clockwise: (x, y) -> (height-1-y, x)
            return height - 1 - y, x
        elif rotation == 180:
            # 180°: (x, y) -> (width-1-x, height-1-y)
            return width - 1 - x, height - 1 - y
        elif rotation == 270:
            # 270° clockwise: (x, y) -> (y, width-1-x)
            return y, width - 1 - x
        else:
            logger.warning(f"Invalid rotation {rotation}, using 0°")
            return x, y

    def map_frame(self, virtual_frame: np.ndarray) -> np.ndarray:
        """
        Map virtual frame to physical LED order

        Uses pre-computed lookup table for fast mapping

        Args:
            virtual_frame: NumPy array of shape (height, width, 3) with RGB values
                          e.g., (32, 32, 3) for 2x2 grid of 16x16 panels

        Returns:
            physical_frame: NumPy array of shape (total_leds, 3) in physical LED order
        """
        with self.lock:
            # Validate frame dimensions
            expected_shape = (self.total_height, self.total_width, 3)
            if virtual_frame.shape != expected_shape:
                logger.error(f"Invalid frame shape: {virtual_frame.shape}, "
                           f"expected {expected_shape}")
                # Return black frame
                return np.zeros((self.total_leds, 3), dtype=np.uint8)

            # Use lookup table for vectorized mapping
            # Extract virtual coordinates from lookup table
            virt_y = self.lut[:, 0]
            virt_x = self.lut[:, 1]

            # Map pixels using advanced indexing
            physical_frame = virtual_frame[virt_y, virt_x].copy()

            return physical_frame

    def reload_config(self, config: Dict[str, Any]) -> None:
        """
        Reload configuration and rebuild lookup table

        Thread-safe hot-reload without interrupting display

        Args:
            config: New panel configuration dictionary
        """
        logger.info("Reloading configuration...")

        # Update configuration
        self.config = config
        self.grid = config['grid']
        self.panels = config['panels']

        self.panel_width = self.grid['panel_width']
        self.panel_height = self.grid['panel_height']
        self.grid_width = self.grid['grid_width']
        self.grid_height = self.grid['grid_height']

        # Recalculate dimensions
        self.total_width = self.grid_width * self.panel_width
        self.total_height = self.grid_height * self.panel_height
        self.total_leds = len(self.panels) * self.panel_width * self.panel_height

        # Rebuild lookup table
        self.build_lookup_table()

        logger.info("Configuration reloaded successfully")

    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get total display dimensions

        Returns:
            Tuple of (width, height) in pixels
        """
        return self.total_width, self.total_height

    def get_led_count(self) -> int:
        """
        Get total number of LEDs

        Returns:
            Total LED count
        """
        return self.total_leds

    def virtual_to_physical(self, x: int, y: int) -> int:
        """
        Convert virtual coordinates to physical LED index

        Useful for testing and debugging

        Args:
            x: Virtual X coordinate
            y: Virtual Y coordinate

        Returns:
            Physical LED index, or -1 if out of bounds
        """
        if not (0 <= x < self.total_width and 0 <= y < self.total_height):
            return -1

        # Search lookup table for matching coordinates
        with self.lock:
            for physical_idx in range(self.total_leds):
                virt_y, virt_x = self.lut[physical_idx]
                if virt_x == x and virt_y == y:
                    return physical_idx

        return -1


def create_test_frame(width: int, height: int, pattern: str = "gradient") -> np.ndarray:
    """
    Create test frame for coordinate mapper testing

    Args:
        width: Frame width
        height: Frame height
        pattern: Pattern type ("gradient", "corners", "cross", "checkerboard")

    Returns:
        NumPy array of shape (height, width, 3)
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    if pattern == "gradient":
        for y in range(height):
            for x in range(width):
                frame[y, x] = [x * 255 // width, y * 255 // height, 128]

    elif pattern == "corners":
        # Colored corners to test panel positioning
        frame[0, 0] = [255, 0, 0]              # Top-left: Red
        frame[0, width-1] = [0, 255, 0]        # Top-right: Green
        frame[height-1, 0] = [0, 0, 255]       # Bottom-left: Blue
        frame[height-1, width-1] = [255, 255, 0]  # Bottom-right: Yellow

        # Add small cross at each corner for visibility
        for corner_y, corner_x in [(0, 0), (0, width-1), (height-1, 0), (height-1, width-1)]:
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    ny, nx = corner_y + dy, corner_x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if ny == corner_y or nx == corner_x:
                            frame[ny, nx] = frame[corner_y, corner_x]

    elif pattern == "cross":
        # White cross in center
        mid_x, mid_y = width // 2, height // 2
        frame[mid_y, :] = [255, 255, 255]  # Horizontal line
        frame[:, mid_x] = [255, 255, 255]  # Vertical line

    elif pattern == "checkerboard":
        # Checkerboard pattern
        for y in range(height):
            for x in range(width):
                if (x // 4 + y // 4) % 2 == 0:
                    frame[y, x] = [255, 255, 255]

    return frame
