#!/usr/bin/env python3
"""
Test Patterns for LED Display
Built-in patterns for alignment testing and visual effects
"""

import numpy as np
import math
import colorsys
from datetime import datetime, timedelta
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


def solid_color(width: int, height: int, r: int, g: int, b: int) -> np.ndarray:
    """
    Create solid color frame

    Args:
        width: Frame width
        height: Frame height
        r, g, b: RGB color values (0-255)

    Returns:
        Frame array of shape (height, width, 3)
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = [r, g, b]
    return frame


def corner_markers(width: int, height: int, size: int = 3) -> np.ndarray:
    """
    Create frame with colored markers in each corner

    Useful for verifying panel positions and rotations

    Args:
        width: Frame width
        height: Frame height
        size: Size of corner markers in pixels

    Returns:
        Frame array with colored corners
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Define corner colors
    corners = [
        (0, 0, [255, 0, 0]),                    # Top-left: Red
        (0, width-1, [0, 255, 0]),              # Top-right: Green
        (height-1, 0, [0, 0, 255]),             # Bottom-left: Blue
        (height-1, width-1, [255, 255, 0])      # Bottom-right: Yellow
    ]

    # Draw markers
    for corner_y, corner_x, color in corners:
        for dy in range(-size, size+1):
            for dx in range(-size, size+1):
                ny, nx = corner_y + dy, corner_x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    # Draw cross pattern
                    if ny == corner_y or nx == corner_x:
                        frame[ny, nx] = color

    return frame


def cross_hair(width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Create frame with crosshair in center

    Args:
        width: Frame width
        height: Frame height
        color: RGB color tuple

    Returns:
        Frame array with crosshair
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    mid_x, mid_y = width // 2, height // 2

    # Horizontal line
    frame[mid_y, :] = color

    # Vertical line
    frame[:, mid_x] = color

    return frame


def checkerboard(width: int, height: int, cell_size: int = 4,
                 color1: Tuple[int, int, int] = (255, 255, 255),
                 color2: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
    """
    Create checkerboard pattern

    Args:
        width: Frame width
        height: Frame height
        cell_size: Size of each checker cell
        color1: First color
        color2: Second color

    Returns:
        Frame array with checkerboard pattern
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            if (x // cell_size + y // cell_size) % 2 == 0:
                frame[y, x] = color1
            else:
                frame[y, x] = color2

    return frame


def rainbow_gradient(width: int, height: int, orientation: str = "horizontal",
                    offset: float = 0) -> np.ndarray:
    """
    Create rainbow gradient

    Args:
        width: Frame width
        height: Frame height
        orientation: "horizontal", "vertical", or "diagonal"
        offset: Animation offset (0.0-1.0)

    Returns:
        Frame array with rainbow gradient
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            if orientation == "horizontal":
                hue = (x / width + offset) % 1.0
            elif orientation == "vertical":
                hue = (y / height + offset) % 1.0
            elif orientation == "diagonal":
                hue = ((x + y) / (width + height) + offset) % 1.0
            else:
                hue = 0.0

            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    return frame


def spiral_rainbow(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create spiral rainbow pattern

    Args:
        width: Frame width
        height: Frame height
        offset: Animation offset

    Returns:
        Frame array with spiral pattern
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    center_x, center_y = width / 2, height / 2

    for y in range(height):
        for x in range(width):
            dx, dy = x - center_x, y - center_y
            angle = math.atan2(dy, dx)
            distance = math.sqrt(dx*dx + dy*dy)

            hue = (angle / (2 * math.pi) + distance * 0.05 + offset) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    return frame


def wave_pattern(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create wave interference pattern

    Args:
        width: Frame width
        height: Frame height
        offset: Animation offset

    Returns:
        Frame array with wave pattern
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            # Two wave sources
            wave1 = math.sin((x + offset) * 0.3) * 0.5 + 0.5
            wave2 = math.sin((y + offset * 0.7) * 0.4) * 0.5 + 0.5

            intensity = (wave1 + wave2) / 2

            # Color based on intensity
            r = int(intensity * 255)
            g = int(intensity * 128)
            b = int((1 - intensity) * 255)

            frame[y, x] = [r, g, b]

    return frame


def fire_effect(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create fire effect pattern

    Args:
        width: Frame width
        height: Frame height
        offset: Animation offset

    Returns:
        Frame array with fire effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            # Fire rises from bottom
            flame_height = (height - y) / height

            # Add noise for flickering
            noise = (math.sin(x * 0.5 + offset) +
                    math.sin(y * 0.3 + offset * 1.5) +
                    math.sin((x + y) * 0.2 + offset * 2)) / 3

            intensity = max(0, min(1, flame_height + noise * 0.2))

            # Fire colors: yellow at bottom, red at top
            r = int(255 * intensity)
            g = int(200 * intensity * intensity)
            b = int(50 * intensity * intensity * intensity)

            frame[y, x] = [r, g, b]

    return frame


def moving_dot(width: int, height: int, offset: float = 0,
              color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Create single moving dot (useful for testing individual LEDs)

    Args:
        width: Frame width
        height: Frame height
        offset: Position offset (cycles through all pixels)
        color: Dot color

    Returns:
        Frame array with single dot
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    total_pixels = width * height
    pixel_index = int(offset * total_pixels) % total_pixels

    y = pixel_index // width
    x = pixel_index % width

    frame[y, x] = color

    return frame


def grid_lines(width: int, height: int, grid_size: int = 16,
              color: Tuple[int, int, int] = (64, 64, 64)) -> np.ndarray:
    """
    Create grid lines (useful for aligning panels)

    Args:
        width: Frame width
        height: Frame height
        grid_size: Size of grid cells (typically panel size: 16)
        color: Line color

    Returns:
        Frame array with grid lines
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Vertical lines
    for x in range(0, width, grid_size):
        frame[:, x] = color

    # Horizontal lines
    for y in range(0, height, grid_size):
        frame[y, :] = color

    return frame


def panel_numbers(width: int, height: int, panel_width: int = 16,
                 panel_height: int = 16) -> np.ndarray:
    """
    Create frame with panel ID numbers (simplified - just colored squares)

    Args:
        width: Total frame width
        height: Total frame height
        panel_width: Width of each panel
        panel_height: Height of each panel

    Returns:
        Frame array with colored panels
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    panels_wide = width // panel_width
    panels_high = height // panel_height

    panel_id = 0
    for py in range(panels_high):
        for px in range(panels_wide):
            # Generate unique color for each panel
            hue = (panel_id / (panels_wide * panels_high)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 0.5)

            # Fill panel area
            y_start = py * panel_height
            y_end = y_start + panel_height
            x_start = px * panel_width
            x_end = x_start + panel_width

            frame[y_start:y_end, x_start:x_end] = [
                int(r * 255), int(g * 255), int(b * 255)
            ]

            panel_id += 1

    return frame


def elapsed_time(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Display elapsed time since a specific date

    Shows time elapsed since July 29, 2025 00:00:00
    Format: Shows numbers in large format

    Args:
        width: Frame width
        height: Frame height
        offset: Animation offset (for color cycling)

    Returns:
        Frame array with elapsed time text
    """
    # Create blank frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Calculate elapsed time from reference date
    reference_date = datetime(2025, 7, 29, 0, 0, 0)
    now = datetime.now()
    elapsed = now - reference_date

    # Format the time
    total_seconds = abs(elapsed.total_seconds())
    days = int(total_seconds // 86400)
    hours = int((total_seconds % 86400) // 3600)
    minutes = int((total_seconds % 3600) // 60)

    # Animated color based on offset
    hue = (offset * 0.1) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    color = (int(r * 255), int(g * 255), int(b * 255))

    # For 32x32, split into 3 lines
    # Try to use the largest possible font
    try:
        # Try to load a larger TrueType font
        font_size = 14  # Large font for readability
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()
        font_size = 10

    # Create image at display resolution
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Format text - make it as simple as possible for the small display
    if days > 0:
        line1 = f"{days}D"
        line2 = f"{hours}H"
        line3 = f"{minutes}M"
    else:
        # Less than a day - show hours and minutes only
        line1 = f"{hours}H"
        line2 = f"{minutes}M"
        line3 = ""

    # Draw text on three lines, evenly spaced
    y_spacing = height // 4

    # Line 1
    bbox = draw.textbbox((0, 0), line1, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y_spacing), line1, fill=color, font=font)

    # Line 2
    bbox = draw.textbbox((0, 0), line2, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y_spacing * 2), line2, fill=color, font=font)

    # Line 3 (if exists)
    if line3:
        bbox = draw.textbbox((0, 0), line3, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_spacing * 3), line3, fill=color, font=font)

    # Convert to numpy array
    frame = np.array(img, dtype=np.uint8)

    return frame


# Pattern registry for easy access
PATTERNS = {
    "red": lambda w, h, o: solid_color(w, h, 255, 0, 0),
    "green": lambda w, h, o: solid_color(w, h, 0, 255, 0),
    "blue": lambda w, h, o: solid_color(w, h, 0, 0, 255),
    "white": lambda w, h, o: solid_color(w, h, 255, 255, 255),
    "corners": lambda w, h, o: corner_markers(w, h),
    "cross": lambda w, h, o: cross_hair(w, h),
    "checkerboard": lambda w, h, o: checkerboard(w, h),
    "rainbow": rainbow_gradient,
    "spiral": spiral_rainbow,
    "wave": wave_pattern,
    "fire": fire_effect,
    "dot": moving_dot,
    "grid": lambda w, h, o: grid_lines(w, h),
    "panels": lambda w, h, o: panel_numbers(w, h),
    "elapsed": elapsed_time,
}


def get_pattern(name: str, width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Get pattern by name

    Args:
        name: Pattern name (see PATTERNS dict)
        width: Frame width
        height: Frame height
        offset: Animation offset

    Returns:
        Frame array, or black frame if pattern not found
    """
    if name in PATTERNS:
        return PATTERNS[name](width, height, offset)
    else:
        return np.zeros((height, width, 3), dtype=np.uint8)


def list_patterns() -> list:
    """Get list of available pattern names"""
    return list(PATTERNS.keys())
