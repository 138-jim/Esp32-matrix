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

    # Draw text on three lines with better spacing
    line_spacing = 10  # Pixels between lines
    start_y = 0  # Start at top of display

    # Get color based on global setting (controlled via web UI)
    color_mode = getattr(elapsed_time, 'color_mode', 'rainbow')

    if color_mode == 'rainbow':
        # Rainbow cycle
        hue = (offset * 0.1) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
    elif color_mode == 'cyan':
        color = (0, 255, 255)
    elif color_mode == 'magenta':
        color = (255, 0, 255)
    elif color_mode == 'white':
        color = (255, 255, 255)
    elif color_mode == 'red':
        color = (255, 0, 0)
    elif color_mode == 'green':
        color = (0, 255, 0)
    elif color_mode == 'blue':
        color = (0, 0, 255)
    elif color_mode == 'yellow':
        color = (255, 255, 0)
    elif color_mode == 'purple':
        color = (128, 0, 255)
    elif color_mode == 'orange':
        color = (255, 165, 0)
    else:
        # Default to rainbow
        hue = (offset * 0.1) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))

    # Line 1
    bbox = draw.textbbox((0, 0), line1, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, start_y), line1, fill=color, font=font)

    # Line 2
    bbox = draw.textbbox((0, 0), line2, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, start_y + line_spacing), line2, fill=color, font=font)

    # Line 3 (if exists)
    if line3:
        bbox = draw.textbbox((0, 0), line3, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, start_y + line_spacing * 2), line3, fill=color, font=font)

    # Rotate 180 degrees and flip horizontally to compensate for panel orientation
    img = img.rotate(180)
    img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # Convert to numpy array
    frame = np.array(img, dtype=np.uint8)

    return frame

def beating_heart(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create a beating heart pattern

    Args:
        width: Frame width
        height: Frame height
        offset: Animation offset for beating effect

    Returns:
        Frame array with beating heart
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Center of the display
    cx = width / 2.0
    cy = height / 2.0

    # Beating effect: scale oscillates between 0.8 and 1.2
    beat = 1.0 + 0.2 * math.sin(offset * 3.0)

    # Heart color (red with some variation)
    base_hue = 0.0  # Red
    hue_variation = math.sin(offset * 0.5) * 0.05
    hue = base_hue + hue_variation
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    color = (int(r * 255), int(g * 255), int(b * 255))

    # Draw heart shape using parametric equation
    for y in range(height):
        for x in range(width):
            # Normalize coordinates with vertical stretch for longer point
            # Shift down by 4 pixels from previous position
            nx = ((x - cx) / (width / 5.5)) / beat  # Decreased horizontal stretch
            ny = ((y - cy + 4) / (height / 5.5)) / beat  # Vertical stretch + shift down

            # Modified heart equation for deeper dip and longer point
            # (x^2 + (y - |x|^0.5)^2 - 1)^3 - x^2*y^3 <= 0
            # Using |x|^0.5 creates a deeper dip at the top
            y_adj = ny - abs(nx) ** 0.6  # Adjust for dip
            heart_eq = (nx * nx + y_adj * y_adj - 1) ** 3 - nx * nx * ny * ny * ny * 0.8

            if heart_eq <= 0:
                # Inside heart - full color
                frame[y, x] = color
            elif heart_eq <= 0.25:
                # Edge glow
                intensity = 1.0 - (heart_eq / 0.25)
                frame[y, x] = [
                    int(color[0] * intensity),
                    int(color[1] * intensity),
                    int(color[2] * intensity)
                ]

    return frame


def snow(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create snow effect with falling snowflakes and wind drift

    Snowflakes fall slowly with horizontal wind drift and varying sizes

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with snow effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark blue-gray winter sky background
    for y in range(height):
        for x in range(width):
            # Slightly lighter than rain for snowy day
            brightness = int(8 + (y / height) * 2)
            frame[y, x] = [brightness, brightness, brightness + 5]

    # Number of snowflakes
    num_flakes = 40

    # Wind effect (oscillates left/right)
    wind = math.sin(offset * 0.3) * 3.0

    for flake_id in range(num_flakes):
        # Consistent base x position for each flake
        base_x = (flake_id * 67) % width

        # Slower speed than rain
        speed = 0.8 + (flake_id % 4) * 0.3

        # Calculate flake y position (falls down slowly)
        flake_y_raw = int((offset * speed + flake_id * 5) % (height + 15))
        flake_y = height - 1 - flake_y_raw

        # Add wind drift - accumulates over time as flake falls
        wind_drift = int((flake_y_raw / height) * wind)
        flake_x = (base_x + wind_drift) % width

        # Snowflake size varies
        size = 1 + (flake_id % 3)  # Size 1, 2, or 3

        # Draw snowflake
        if 0 <= flake_y < height:
            if size == 1:
                # Small flake - single pixel
                frame[flake_y, flake_x] = [220, 220, 255]

            elif size == 2:
                # Medium flake - cross pattern
                frame[flake_y, flake_x] = [240, 240, 255]
                # Add cross arms
                if flake_x > 0:
                    frame[flake_y, flake_x - 1] = [180, 180, 220]
                if flake_x < width - 1:
                    frame[flake_y, (flake_x + 1) % width] = [180, 180, 220]
                if flake_y < height - 1:
                    frame[flake_y + 1, flake_x] = [180, 180, 220]
                if flake_y > 0:
                    frame[flake_y - 1, flake_x] = [180, 180, 220]

            else:  # size == 3
                # Large flake - plus with diagonals
                frame[flake_y, flake_x] = [255, 255, 255]
                # Cross
                if flake_x > 0:
                    frame[flake_y, flake_x - 1] = [200, 200, 240]
                if flake_x < width - 1:
                    frame[flake_y, (flake_x + 1) % width] = [200, 200, 240]
                if flake_y < height - 1:
                    frame[flake_y + 1, flake_x] = [200, 200, 240]
                if flake_y > 0:
                    frame[flake_y - 1, flake_x] = [200, 200, 240]
                # Diagonals
                if flake_y > 0 and flake_x > 0:
                    frame[flake_y - 1, flake_x - 1] = [160, 160, 200]
                if flake_y > 0 and flake_x < width - 1:
                    frame[flake_y - 1, (flake_x + 1) % width] = [160, 160, 200]

    return frame


def rain(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create rain effect with falling droplets and ripples

    Raindrops fall at varying speeds with ripple effects when they hit the ground

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with rain effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Very dark blue-gray background for rainy atmosphere
    for y in range(height):
        for x in range(width):
            # Gradient from very dark at top to slightly lighter at bottom
            brightness = int(3 + (y / height) * 2)
            frame[y, x] = [brightness // 2, brightness // 2, brightness]

    # Number of raindrops
    num_drops = 30

    for drop_id in range(num_drops):
        # Consistent x position for each drop
        drop_x = (drop_id * 73) % width

        # Different speeds for different drops (2x faster)
        speed = 4.0 + (drop_id % 5) * 1.0

        # Calculate drop y position (falls down from top to bottom)
        # Start at top (0) and move toward bottom (height-1)
        drop_y_raw = int((offset * speed + drop_id * 3) % (height + 10))

        # Flip coordinate so it falls downward visually
        drop_y = height - 1 - drop_y_raw

        # Draw raindrop (elongated)
        if 0 <= drop_y < height:
            # Main drop (bright)
            frame[drop_y, drop_x] = [180, 200, 255]

            # Trail behind drop (dimmer) - should be above the drop (higher y value in flipped coords)
            if drop_y < height - 1:
                frame[drop_y + 1, drop_x] = [100, 120, 180]
            if drop_y < height - 2:
                frame[drop_y + 2, drop_x] = [50, 60, 120]

        # Ripple effect when drop hits bottom (y near 0 in flipped coords)
        if drop_y <= 2:
            # Time since hitting ground (based on how close to y=0)
            ripple_time = 2 - drop_y + ((offset * speed) % 1.0)

            if ripple_time < 3.0:  # Ripple lasts for 3 frames
                ripple_radius = int(ripple_time) + 1
                ripple_intensity = 1.0 - (ripple_time / 3.0)

                # Draw ripple circle at ground level (y=0 is bottom now)
                ground_y = 0
                for dx in range(-ripple_radius, ripple_radius + 1):
                    ripple_x = (drop_x + dx) % width
                    dist = abs(dx)

                    if dist == ripple_radius:  # On the ripple edge
                        brightness = int(150 * ripple_intensity)
                        frame[ground_y, ripple_x] = [
                            min(255, frame[ground_y, ripple_x][0] + brightness // 2),
                            min(255, frame[ground_y, ripple_x][1] + brightness // 2),
                            min(255, frame[ground_y, ripple_x][2] + brightness)
                        ]

                # Also draw ripple one row up for visibility (y+1 in flipped coords)
                if ground_y < height - 1:
                    for dx in range(-ripple_radius, ripple_radius + 1):
                        ripple_x = (drop_x + dx) % width
                        dist = abs(dx)

                        if dist == ripple_radius:
                            brightness = int(100 * ripple_intensity)
                            frame[ground_y + 1, ripple_x] = [
                                min(255, frame[ground_y + 1, ripple_x][0] + brightness // 2),
                                min(255, frame[ground_y + 1, ripple_x][1] + brightness // 2),
                                min(255, frame[ground_y + 1, ripple_x][2] + brightness)
                            ]

    return frame


def sunset_sunrise_loop(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create sunset/sunrise animation loop (not synced to real time)

    Continuously cycles through day and night with animated sun/moon,
    clouds, and stars. Full cycle every 40 seconds.

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with sunset/sunrise effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Cycle through a full day every 40 seconds
    day_cycle = (offset / 40.0) % 1.0

    # Sun/Moon position (moves across sky from left to right)
    if 0.208 <= day_cycle < 0.875:  # Sun is up
        sun_progress = (day_cycle - 0.208) / (0.875 - 0.208)
        sun_x = int(sun_progress * width)
        sun_y = int(height * 0.8 - (4 * sun_progress * (1 - sun_progress)) * height * 0.5)
        celestial_body = "sun"
    else:  # Moon is up
        if day_cycle >= 0.875:
            moon_progress = (day_cycle - 0.875) / (1.0 - 0.875)
        else:
            moon_progress = (day_cycle + (1.0 - 0.875)) / (0.208 + (1.0 - 0.875))
        moon_x = int(moon_progress * width)
        moon_y = int(height * 0.8 - (4 * moon_progress * (1 - moon_progress)) * height * 0.5)
        celestial_body = "moon"

    # Draw sky gradient
    for y in range(height):
        v_pos = 1.0 - (y / height)

        for x in range(width):
            # Determine colors based on time of day
            if 0.208 <= day_cycle < 0.333:  # Sunrise
                phase = (day_cycle - 0.208) / (0.333 - 0.208)
                if v_pos < 0.3:
                    hue = 0.05 + phase * 0.05
                    saturation = 1.0
                    brightness = 0.6 + phase * 0.4
                elif v_pos < 0.6:
                    hue = 0.08 + phase * 0.07
                    saturation = 0.9 - phase * 0.3
                    brightness = 0.8 + phase * 0.2
                else:
                    hue = 0.15 + phase * 0.4
                    saturation = 0.5 - phase * 0.3
                    brightness = 0.7 + phase * 0.3

            elif 0.333 <= day_cycle < 0.75:  # Day
                if v_pos < 0.2:
                    hue = 0.52
                    saturation = 0.3
                    brightness = 0.95
                else:
                    hue = 0.55
                    saturation = 0.7
                    brightness = 0.95

            elif 0.75 <= day_cycle < 0.875:  # Sunset
                phase = (day_cycle - 0.75) / (0.875 - 0.75)
                if v_pos < 0.3:
                    hue = 0.05 - phase * 0.03
                    saturation = 0.95
                    brightness = 0.8 - phase * 0.3
                elif v_pos < 0.6:
                    hue = 0.95 - phase * 0.1
                    saturation = 0.8
                    brightness = 0.7 - phase * 0.2
                else:
                    hue = 0.7 - phase * 0.1
                    saturation = 0.7
                    brightness = 0.6 - phase * 0.3

            else:  # Night
                if v_pos < 0.4:
                    hue = 0.62
                    saturation = 0.8
                    brightness = 0.15
                else:
                    hue = 0.65
                    saturation = 0.75
                    brightness = 0.25

            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    # Draw stars at night
    if day_cycle >= 0.875 or day_cycle < 0.208:
        for star_id in range(40):
            sx = (star_id * 73) % width
            sy = (star_id * 97) % (height - 10)
            if sy < height * 0.7:
                twinkle = 0.5 + 0.5 * math.sin(offset * (0.5 + star_id % 3) + star_id)
                brightness = int(200 * twinkle)
                frame[sy, sx] = [brightness, brightness, brightness]

    # Draw clouds during day
    if 0.25 <= day_cycle < 0.875:
        cloud_offset = int(offset * 2) % width
        for cloud_id in range(3):
            cx = (cloud_offset + cloud_id * 15) % width
            cy = 5 + cloud_id * 6
            for dy in range(-1, 2):
                for dx in range(-2, 3):
                    cloud_y = cy + dy
                    cloud_x = (cx + dx) % width
                    if 0 <= cloud_y < height:
                        frame[cloud_y, cloud_x] = [
                            min(255, frame[cloud_y, cloud_x][0] + 80),
                            min(255, frame[cloud_y, cloud_x][1] + 80),
                            min(255, frame[cloud_y, cloud_x][2] + 80)
                        ]

    # Draw sun or moon
    if celestial_body == "sun":
        sun_radius = 3
        for dy in range(-sun_radius, sun_radius + 1):
            for dx in range(-sun_radius, sun_radius + 1):
                if dx*dx + dy*dy <= sun_radius*sun_radius:
                    sy = sun_y + dy
                    sx = sun_x + dx
                    if 0 <= sy < height and 0 <= sx < width:
                        frame[sy, sx] = [255, 220, 100]
    else:
        moon_radius = 2
        for dy in range(-moon_radius, moon_radius + 1):
            for dx in range(-moon_radius, moon_radius + 1):
                if dx*dx + dy*dy <= moon_radius*moon_radius:
                    my = moon_y + dy
                    mx = moon_x + dx
                    if 0 <= my < height and 0 <= mx < width:
                        frame[my, mx] = [240, 240, 200]

    return frame


def sunset_sunrise(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create sunset/sunrise animation with sun/moon and real-time sync

    Syncs to actual time of day (uses system clock) with animated sun/moon,
    clouds, and stars

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset (used for cloud movement and animations)

    Returns:
        Frame array with sunset/sunrise effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Use real time of day
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # Convert time to day_cycle (0.0 = midnight, 0.5 = noon, 1.0 = midnight)
    day_cycle = (hour + minute / 60.0) / 24.0

    # Determine time of day
    # Sunrise: 5am-8am (0.208-0.333)
    # Day: 8am-6pm (0.333-0.75)
    # Sunset: 6pm-9pm (0.75-0.875)
    # Night: 9pm-5am (0.875-1.0 and 0.0-0.208)

    # Sun/Moon position (moves across sky from left to right)
    if 0.208 <= day_cycle < 0.875:  # Sun is up (5am-9pm)
        # Map to 0-1 across the day
        sun_progress = (day_cycle - 0.208) / (0.875 - 0.208)
        sun_x = int(sun_progress * width)
        # Parabolic arc for sun height
        sun_y = int(height * 0.8 - (4 * sun_progress * (1 - sun_progress)) * height * 0.5)
        celestial_body = "sun"
    else:  # Moon is up
        # Moon path
        if day_cycle >= 0.875:
            moon_progress = (day_cycle - 0.875) / (1.0 - 0.875)
        else:
            moon_progress = (day_cycle + (1.0 - 0.875)) / (0.208 + (1.0 - 0.875))
        moon_x = int(moon_progress * width)
        moon_y = int(height * 0.8 - (4 * moon_progress * (1 - moon_progress)) * height * 0.5)
        celestial_body = "moon"

    # Draw sky gradient
    for y in range(height):
        v_pos = 1.0 - (y / height)

        for x in range(width):
            # Determine colors based on time of day
            if 0.208 <= day_cycle < 0.333:  # Sunrise (5am-8am)
                phase = (day_cycle - 0.208) / (0.333 - 0.208)
                if v_pos < 0.3:
                    hue = 0.05 + phase * 0.05
                    saturation = 1.0
                    brightness = 0.6 + phase * 0.4
                elif v_pos < 0.6:
                    hue = 0.08 + phase * 0.07
                    saturation = 0.9 - phase * 0.3
                    brightness = 0.8 + phase * 0.2
                else:
                    hue = 0.15 + phase * 0.4
                    saturation = 0.5 - phase * 0.3
                    brightness = 0.7 + phase * 0.3

            elif 0.333 <= day_cycle < 0.75:  # Day (8am-6pm)
                if v_pos < 0.2:
                    hue = 0.52
                    saturation = 0.3
                    brightness = 0.95
                else:
                    hue = 0.55
                    saturation = 0.7
                    brightness = 0.95

            elif 0.75 <= day_cycle < 0.875:  # Sunset (6pm-9pm)
                phase = (day_cycle - 0.75) / (0.875 - 0.75)
                if v_pos < 0.3:
                    hue = 0.05 - phase * 0.03
                    saturation = 0.95
                    brightness = 0.8 - phase * 0.3
                elif v_pos < 0.6:
                    hue = 0.95 - phase * 0.1
                    saturation = 0.8
                    brightness = 0.7 - phase * 0.2
                else:
                    hue = 0.7 - phase * 0.1
                    saturation = 0.7
                    brightness = 0.6 - phase * 0.3

            else:  # Night
                if v_pos < 0.4:
                    hue = 0.62
                    saturation = 0.8
                    brightness = 0.15
                else:
                    hue = 0.65
                    saturation = 0.75
                    brightness = 0.25

            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    # Draw stars at night
    if day_cycle >= 0.875 or day_cycle < 0.208:
        for star_id in range(40):
            sx = (star_id * 73) % width
            sy = (star_id * 97) % (height - 10)  # Keep stars in upper sky
            if sy < height * 0.7:  # Only upper 70%
                twinkle = 0.5 + 0.5 * math.sin(offset * (0.5 + star_id % 3) + star_id)
                brightness = int(200 * twinkle)
                frame[sy, sx] = [brightness, brightness, brightness]

    # Draw clouds during day
    if 0.25 <= day_cycle < 0.875:
        cloud_offset = int(offset * 2) % width
        for cloud_id in range(3):
            cx = (cloud_offset + cloud_id * 15) % width
            cy = 5 + cloud_id * 6
            # Simple cloud shape
            for dy in range(-1, 2):
                for dx in range(-2, 3):
                    cloud_y = cy + dy
                    cloud_x = (cx + dx) % width
                    if 0 <= cloud_y < height:
                        # White with some transparency
                        frame[cloud_y, cloud_x] = [
                            min(255, frame[cloud_y, cloud_x][0] + 80),
                            min(255, frame[cloud_y, cloud_x][1] + 80),
                            min(255, frame[cloud_y, cloud_x][2] + 80)
                        ]

    # Draw sun or moon
    if celestial_body == "sun":
        # Draw sun
        sun_radius = 3
        for dy in range(-sun_radius, sun_radius + 1):
            for dx in range(-sun_radius, sun_radius + 1):
                if dx*dx + dy*dy <= sun_radius*sun_radius:
                    sy = sun_y + dy
                    sx = sun_x + dx
                    if 0 <= sy < height and 0 <= sx < width:
                        # Bright yellow/orange sun
                        frame[sy, sx] = [255, 220, 100]
    else:
        # Draw moon
        moon_radius = 2
        for dy in range(-moon_radius, moon_radius + 1):
            for dx in range(-moon_radius, moon_radius + 1):
                if dx*dx + dy*dy <= moon_radius*moon_radius:
                    my = moon_y + dy
                    mx = moon_x + dx
                    if 0 <= my < height and 0 <= mx < width:
                        # White/pale yellow moon
                        frame[my, mx] = [240, 240, 200]

    return frame


def rgb_torch(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create flickering colored flame effect (rainbow torch)

    Similar to fire effect but with cycling rainbow colors instead of
    traditional fire colors

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with RGB torch effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Base hue cycles through rainbow
    base_hue = (offset * 0.1) % 1.0

    for y in range(height):
        for x in range(width):
            # Flame rises from bottom
            flame_height = (height - y) / height

            # Add noise for flickering using multiple sine waves
            noise = (math.sin(x * 0.5 + offset * 3) +
                    math.sin(y * 0.3 + offset * 4) +
                    math.sin((x + y) * 0.2 + offset * 5)) / 3

            # Intensity decreases with height and varies with noise
            intensity = max(0, min(1, flame_height + noise * 0.3))

            # Skip very low intensity pixels for torch effect
            if intensity < 0.1:
                continue

            # Hue varies slightly across the flame
            hue_variation = (x / width) * 0.2 - 0.1  # Slight horizontal variation
            hue = (base_hue + hue_variation) % 1.0

            # Saturation high at base, decreases toward top
            saturation = 0.8 + (flame_height * 0.2)

            # Brightness based on intensity
            brightness = intensity

            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)

            frame[y, x] = [
                int(r * 255),
                int(g * 255),
                int(b * 255)
            ]

    return frame


def gradient_waves(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create flowing gradient patterns using sine wave interference

    Multiple sine waves interfere to create smooth, flowing color patterns

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with gradient wave patterns
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            # Multiple sine waves with different frequencies and phases
            wave1 = math.sin(x * 0.2 + offset * 0.5)
            wave2 = math.sin(y * 0.2 + offset * 0.7)
            wave3 = math.sin((x + y) * 0.15 + offset * 0.3)
            wave4 = math.sin((x - y) * 0.1 + offset * 0.4)

            # Combine waves to create hue (color) - full rainbow spectrum
            combined = (wave1 + wave2 + wave3 + wave4) / 4.0
            hue = (combined + 1.0) / 2.0  # Normalize to 0-1

            # Use full saturation for vibrant colors (not pastel)
            saturation = 1.0

            # Vary brightness slightly based on waves for depth
            brightness_variation = (wave1 * wave2) * 0.2 + 0.8  # Range: 0.6 to 1.0
            brightness = max(0.6, min(1.0, brightness_variation))

            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)

            # Apply to frame
            frame[y, x] = [
                int(r * 255),
                int(g * 255),
                int(b * 255)
            ]

    return frame


def color_gradients(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create smooth cycling color gradient transitions

    Cycles through different gradient types: linear (horizontal, vertical, diagonal),
    and radial gradients with smooth color transitions

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset for color cycling

    Returns:
        Frame array with color gradients
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Cycle through different gradient modes every 10 seconds
    cycle_time = 10.0
    mode = int((offset / cycle_time) % 4)

    # Color offset for animation
    color_offset = (offset * 0.1) % 1.0

    if mode == 0:
        # Horizontal gradient
        for y in range(height):
            for x in range(width):
                hue = (x / width + color_offset) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    elif mode == 1:
        # Vertical gradient
        for y in range(height):
            for x in range(width):
                hue = (y / height + color_offset) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    elif mode == 2:
        # Diagonal gradient
        for y in range(height):
            for x in range(width):
                hue = ((x + y) / (width + height) + color_offset) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    else:  # mode == 3
        # Radial gradient from center
        cx, cy = width / 2.0, height / 2.0
        max_dist = math.sqrt(cx * cx + cy * cy)

        for y in range(height):
            for x in range(width):
                # Distance from center
                dx, dy = x - cx, y - cy
                dist = math.sqrt(dx * dx + dy * dy)

                # Normalize distance and apply color
                hue = (dist / max_dist + color_offset) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    return frame


def starry_night(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create starry night pattern with twinkling stars

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset for twinkling

    Returns:
        Frame array with twinkling stars on black background
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Generate consistent star positions using pseudo-random based on pixel position
    # This ensures stars stay in the same place across frames
    num_stars = 80  # Number of stars (adjust for density)

    for star_id in range(num_stars):
        # Use star_id as seed for consistent positioning
        # Simple hash function for pseudo-random but consistent positions
        x = (star_id * 73) % width
        y = (star_id * 97) % height

        # Star brightness varies with time (twinkling effect)
        # Different stars twinkle at different rates
        twinkle_speed = 0.5 + (star_id % 10) * 0.3  # Vary twinkle speed
        twinkle_phase = (star_id * 0.5) % (2 * math.pi)  # Different phases
        brightness = 0.5 + 0.5 * math.sin(offset * twinkle_speed + twinkle_phase)

        # Some stars are brighter than others
        base_brightness = 0.6 + (star_id % 4) * 0.1

        # Final brightness
        final_brightness = brightness * base_brightness

        # Star color - mostly white, some slightly yellow
        if star_id % 7 == 0:
            # Yellow-ish star
            color = (
                int(255 * final_brightness),
                int(255 * final_brightness),
                int(200 * final_brightness)
            )
        else:
            # White star
            color = (
                int(255 * final_brightness),
                int(255 * final_brightness),
                int(255 * final_brightness)
            )

        # Draw star (single pixel)
        frame[y, x] = color

        # Occasionally draw a slightly bigger/brighter star
        if star_id % 15 == 0 and final_brightness > 0.7:
            # Add glow to neighboring pixels
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width and (dx != 0 or dy != 0):
                        glow_intensity = final_brightness * 0.3
                        frame[ny, nx] = [
                            min(255, frame[ny, nx][0] + int(255 * glow_intensity)),
                            min(255, frame[ny, nx][1] + int(255 * glow_intensity)),
                            min(255, frame[ny, nx][2] + int(255 * glow_intensity))
                        ]

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
    "heart": beating_heart,
    "starry_night": starry_night,
    "color_gradients": color_gradients,
    "gradient_waves": gradient_waves,
    "rgb_torch": rgb_torch,
    "sunset_sunrise": sunset_sunrise,
    "sunset_sunrise_loop": sunset_sunrise_loop,
    "rain": rain,
    "snow": snow,
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
