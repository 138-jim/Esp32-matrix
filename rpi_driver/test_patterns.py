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


# Perlin Noise Implementation
class PerlinNoise:
    """2D Perlin noise generator"""

    def __init__(self, seed=0):
        """Initialize with permutation table"""
        # Permutation table
        np.random.seed(seed)
        self.p = np.arange(256, dtype=int)
        np.random.shuffle(self.p)
        self.p = np.concatenate([self.p, self.p])  # Duplicate for wrapping

    def fade(self, t):
        """Fade function: 6t^5 - 15t^4 + 10t^3"""
        return t * t * t * (t * (t * 6 - 15) + 10)

    def lerp(self, a, b, t):
        """Linear interpolation"""
        return a + t * (b - a)

    def grad(self, hash_val, x, y):
        """Gradient function - convert hash to gradient vector"""
        # Take the hash value and convert to one of 8 gradient directions
        h = hash_val & 7
        u = x if h < 4 else y
        v = y if h < 4 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def noise(self, x, y):
        """Generate 2D Perlin noise at coordinates (x, y)"""
        # Find unit square that contains point
        X = int(np.floor(x)) & 255
        Y = int(np.floor(y)) & 255

        # Find relative x, y of point in square
        x -= np.floor(x)
        y -= np.floor(y)

        # Compute fade curves
        u = self.fade(x)
        v = self.fade(y)

        # Hash coordinates of square corners
        a = self.p[X] + Y
        aa = self.p[a]
        ab = self.p[a + 1]
        b = self.p[X + 1] + Y
        ba = self.p[b]
        bb = self.p[b + 1]

        # Blend results from corners
        x1 = self.lerp(self.grad(self.p[aa], x, y),
                       self.grad(self.p[ba], x - 1, y), u)
        x2 = self.lerp(self.grad(self.p[ab], x, y - 1),
                       self.grad(self.p[bb], x - 1, y - 1), u)

        return self.lerp(x1, x2, v)


# Create global Perlin noise instance
_perlin = PerlinNoise(seed=42)


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
            brightness = int(5 + (y / height) * 3)
            frame[y, x] = [brightness // 2, brightness // 2, brightness // 2]

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


def fireflies(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create fireflies effect with gentle blinking lights

    Fireflies drift slowly with pulsing yellow-green bioluminescent glow

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with fireflies effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Very dark nighttime background (almost black with slight blue tint)
    for y in range(height):
        for x in range(width):
            # Very subtle gradient
            brightness = int(2 + (y / height) * 1)
            frame[y, x] = [0, brightness // 2, brightness]

    # Number of fireflies
    num_fireflies = 40

    for fly_id in range(num_fireflies):
        # Base position with slow drift
        drift_speed_x = 0.3 + (fly_id % 10) * 0.1
        drift_speed_y = 0.2 + (fly_id % 14) * 0.08

        base_x = (fly_id * 67) % width
        base_y = (fly_id * 97) % height

        # Slow circular drift pattern
        drift_x = math.sin(offset * drift_speed_x + fly_id * 0.5) * 2.0
        drift_y = math.cos(offset * drift_speed_y + fly_id * 0.3) * 1.5

        fly_x = int((base_x + drift_x) % width)
        fly_y = int((base_y + drift_y) % height)

        # Pulsing brightness (each firefly has different pulse speed and phase)
        pulse_speed = 0.8 + (fly_id % 6) * 0.3
        pulse_phase = (fly_id * 1.3) % (2 * math.pi)

        # Create a more natural pulse pattern (quick flash then slow fade)
        pulse_raw = math.sin(offset * pulse_speed + pulse_phase)

        # Transform sine wave to have quick rise and slow fall
        if pulse_raw > 0:
            pulse = pulse_raw ** 0.5  # Square root for quick rise
        else:
            pulse = 0  # Off when negative

        brightness = pulse

        # Only draw when bright enough to see
        if brightness > 0.1:
            # Firefly color - warm yellow-green
            # Vary between more yellow and more green
            if fly_id % 3 == 0:
                # More yellow
                hue = 0.15  # Yellow-orange
            elif fly_id % 3 == 1:
                # Yellow-green
                hue = 0.18
            else:
                # More green
                hue = 0.22

            r, g, b = colorsys.hsv_to_rgb(hue, 0.95, brightness)
            color = (int(r * 255), int(g * 255), int(b * 255))

            # Determine firefly size (2x2 or 1x1)
            size = 2 if fly_id % 2 == 0 else 1

            # Draw firefly
            if 0 <= fly_y < height and 0 <= fly_x < width:
                if size == 2:
                    # 2x2 firefly (larger, brighter)
                    for dy in [0, 1]:
                        for dx in [0, 1]:
                            pixel_x = (fly_x + dx) % width
                            pixel_y = fly_y + dy
                            if 0 <= pixel_y < height:
                                frame[pixel_y, pixel_x] = color
                else:
                    # 1x1 firefly (smaller)
                    frame[fly_y, fly_x] = color

    return frame


def aquarium(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create aquarium effect with swimming fish and rising bubbles

    Fish swim horizontally with varying speeds and bubbles rise from bottom

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with aquarium effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Blue water background (gradient from light blue at top to deeper blue at bottom)
    # Y=0 is bottom, Y=height-1 is top
    for y in range(height):
        depth_factor = (height - 1 - y) / height  # Inverted: top=1.0, bottom=0.0
        # Light blue at top (high depth_factor), darker blue at bottom (low depth_factor)
        blue_intensity = int(100 + depth_factor * 3)  # 100-180
        green_intensity = int(60 + depth_factor * 3)   # 60-100
        frame[y, :] = [0, green_intensity // 4, blue_intensity // 4]

    # Draw seaweed/plants at bottom (Y=0)
    num_plants = 5
    for plant_id in range(num_plants):
        plant_x = (plant_id * 7 + 3) % width
        plant_height = 3 + (plant_id % 3)

        # Swaying effect
        sway = int(math.sin(offset * 1.5 + plant_id) * 1.5)

        for seg in range(plant_height):
            seg_y = seg  # Start at Y=0 (bottom) and grow upward
            seg_x = (plant_x + (sway if seg > 1 else 0)) % width
            if 0 <= seg_y < height:
                # Dark green plant
                frame[seg_y, seg_x] = [10, 80 + seg * 10, 20]

    # Swimming fish
    num_fish = 8
    for fish_id in range(num_fish):
        # Fish swim horizontally at different speeds
        speed = 3.0 + (fish_id % 4) * 1.5

        # Some fish swim left, some right
        if fish_id % 3 == 0:
            direction = -1  # Left
        else:
            direction = 1   # Right

        fish_x_raw = (offset * speed * direction + fish_id * 40) % (width + 8)
        fish_x = int(fish_x_raw) - 4

        # Fish at different depths
        fish_y = 5 + (fish_id * 3) % (height - 10)

        # Vertical bobbing
        bob = int(math.sin(offset * 2.0 + fish_id * 0.7) * 1.0)
        fish_y = fish_y + bob

        # Fish color variations (orange, yellow, red, blue)
        if fish_id % 4 == 0:
            fish_color = [255, 140, 0]   # Orange
        elif fish_id % 4 == 1:
            fish_color = [255, 200, 0]   # Yellow
        elif fish_id % 4 == 2:
            fish_color = [255, 60, 60]   # Red
        else:
            fish_color = [100, 150, 255] # Light blue

        # Draw fish (simple 3-pixel shape)
        # Body: 2 pixels, tail: 1 pixel
        if 0 <= fish_y < height:
            # Body (2x2 square)
            for dy in [0, 1]:
                for dx in [0, 1]:
                    px = fish_x + dx
                    py = fish_y + dy
                    if 0 <= px < width and 0 <= py < height:
                        frame[py, px] = fish_color

            # Tail (1 pixel behind, in swimming direction)
            tail_x = fish_x - direction
            tail_y = fish_y
            if 0 <= tail_x < width and 0 <= tail_y < height:
                # Darker tail
                frame[tail_y, tail_x] = [
                    fish_color[0] // 2,
                    fish_color[1] // 2,
                    fish_color[2] // 2
                ]

    # Rising bubbles
    num_bubbles = 15
    for bubble_id in range(num_bubbles):
        # Bubbles rise from bottom (Y=0) to top (Y=height-1)
        rise_speed = 2.0 + (bubble_id % 3) * 0.5

        bubble_y_raw = (offset * rise_speed + bubble_id * 7) % (height + 10)
        bubble_y = int(bubble_y_raw)  # Rise from 0 upward

        bubble_x = (bubble_id * 11 + 2) % width

        # Slight horizontal drift
        drift = int(math.sin(offset * 1.0 + bubble_id * 0.5) * 1.0)
        bubble_x = (bubble_x + drift) % width

        # Draw bubble (white/light cyan, semi-transparent effect)
        if 0 <= bubble_y < height and 0 <= bubble_x < width:
            # Small bubble - single bright pixel
            frame[bubble_y, bubble_x] = [200, 220, 255]

    return frame


def ocean_waves(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create ocean waves effect using multi-layered noise

    Rolling waves with organic movement using multiple sine wave layers
    for non-repeating patterns

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with ocean waves effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Create wave height field using multiple sine wave layers (simplified Perlin noise)
    wave_field = np.zeros((height, width), dtype=float)

    # Layer 1: Large slow waves
    for x in range(width):
        for y in range(height):
            wave1 = math.sin(x * 0.3 + offset * 0.8) * 3.0
            wave_field[y, x] += wave1

    # Layer 2: Medium waves at different angle
    for x in range(width):
        for y in range(height):
            wave2 = math.sin(x * 0.5 + y * 0.2 + offset * 1.2) * 2.0
            wave_field[y, x] += wave2

    # Layer 3: Small fast ripples
    for x in range(width):
        for y in range(height):
            wave3 = math.sin(x * 0.8 - y * 0.3 + offset * 2.0) * 1.0
            wave_field[y, x] += wave3

    # Layer 4: Very slow large swell
    for x in range(width):
        for y in range(height):
            wave4 = math.sin(x * 0.15 + offset * 0.4) * 2.5
            wave_field[y, x] += wave4

    # Layer 5: Medium frequency diagonal waves
    for x in range(width):
        for y in range(height):
            wave5 = math.sin(x * 0.6 + y * 0.4 + offset * 1.5) * 1.5
            wave_field[y, x] += wave5

    # Layer 6: High frequency cross-waves
    for x in range(width):
        for y in range(height):
            wave6 = math.sin(x * 1.0 + y * 0.1 + offset * 2.5) * 0.8
            wave_field[y, x] += wave6

    # Layer 7: Opposite direction waves
    for x in range(width):
        for y in range(height):
            wave7 = math.sin(-x * 0.4 + y * 0.25 + offset * 1.0) * 1.2
            wave_field[y, x] += wave7

    # Normalize wave field to 0-1 range
    wave_min = np.min(wave_field)
    wave_max = np.max(wave_field)
    if wave_max - wave_min > 0:
        wave_field = (wave_field - wave_min) / (wave_max - wave_min)

    # Color the waves based on height and depth
    for y in range(height):
        for x in range(width):
            wave_height = wave_field[y, x]

            # Depth gradient (Y=0 is bottom, Y=height-1 is top)
            depth = (height - 1 - y) / height  # 0 at bottom, 1 at top

            # Dark ocean colors (deep blues)
            # Much darker base colors for deep ocean look
            base_blue = int(20 + depth * 40 + wave_height * 30)  # 20-90 (darker)
            base_green = int(5 + depth * 25 + wave_height * 20)  # 5-50 (much darker)

            # Wave crests (high wave_height) get lighter/white
            if wave_height > 0.75:
                # White foam on crests
                foam_intensity = (wave_height - 0.75) / 0.25
                r = int(foam_intensity * 180)
                g = int(base_green + foam_intensity * (200 - base_green))
                b = int(base_blue + foam_intensity * (220 - base_blue))
                frame[y, x] = [r, g, b]
            elif wave_height > 0.6:
                # Light cyan on upper waves
                r = 0
                g = int(base_green + (wave_height - 0.6) * 60)
                b = int(base_blue + (wave_height - 0.6) * 70)
                frame[y, x] = [r, g, b]
            else:
                # Deep dark ocean blue
                frame[y, x] = [0, base_green // 2, base_blue // 2]

    return frame


def northern_lights(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create northern lights (aurora borealis) effect

    Flowing vertical curtains of green and purple light with shimmer

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with aurora effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark night sky background with stars
    for y in range(height):
        for x in range(width):
            # Very dark background
            frame[y, x] = [0, 0, 5]

    # Add stars
    num_stars = 30
    for star_id in range(num_stars):
        star_x = (star_id * 73) % width
        star_y = (star_id * 97) % height

        # Only show stars in upper half (aurora is typically lower in sky)
        if star_y > height // 2:
            # Twinkling
            twinkle = 0.3 + 0.7 * abs(math.sin(offset * 2.0 + star_id * 0.3))
            brightness = int(200 * twinkle)
            frame[star_y, star_x] = [brightness, brightness, brightness]

    # Create aurora curtains using vertical waves
    for x in range(width):
        # Multiple wave layers for aurora curtains
        # Wave 1: Main flowing curtain
        wave1 = math.sin(x * 0.4 + offset * 1.5) * 8.0
        wave2 = math.sin(x * 0.6 - offset * 1.2) * 5.0
        wave3 = math.sin(x * 0.3 + offset * 0.8) * 6.0

        # Combine waves to get curtain position and intensity
        curtain_center = height * 0.4 + wave1 + wave2 + wave3

        # Secondary curtain
        wave4 = math.sin(x * 0.5 + offset * 1.0 + 2.0) * 7.0
        wave5 = math.sin(x * 0.35 - offset * 1.3 + 1.5) * 4.0
        curtain2_center = height * 0.5 + wave4 + wave5

        # Draw vertical aurora columns
        for y in range(height):
            # Distance from curtain centers
            dist1 = abs(y - curtain_center)
            dist2 = abs(y - curtain2_center)

            # Aurora intensity based on distance (Gaussian-like falloff)
            intensity1 = max(0, 1.0 - (dist1 / 8.0))
            intensity2 = max(0, 1.0 - (dist2 / 7.0))

            # Shimmer effect
            shimmer = 0.7 + 0.3 * math.sin(offset * 4.0 + x * 0.2 + y * 0.1)

            # Color variations
            # Primary curtain: Green (main aurora color)
            if intensity1 > 0.1:
                color_shift = math.sin(offset * 0.5 + x * 0.1)
                if color_shift > 0.3:
                    # More yellow-green
                    r1 = int(intensity1 * shimmer * 40)
                    g1 = int(intensity1 * shimmer * 255)
                    b1 = int(intensity1 * shimmer * 80)
                else:
                    # Pure green
                    r1 = int(intensity1 * shimmer * 10)
                    g1 = int(intensity1 * shimmer * 255)
                    b1 = int(intensity1 * shimmer * 50)

                # Blend with existing
                frame[y, x] = [
                    min(255, frame[y, x][0] + r1),
                    min(255, frame[y, x][1] + g1),
                    min(255, frame[y, x][2] + b1)
                ]

            # Secondary curtain: Purple/Pink
            if intensity2 > 0.1:
                shimmer2 = 0.6 + 0.4 * math.sin(offset * 3.5 + x * 0.15 + y * 0.12)

                # Purple/magenta aurora
                r2 = int(intensity2 * shimmer2 * 200)
                g2 = int(intensity2 * shimmer2 * 50)
                b2 = int(intensity2 * shimmer2 * 180)

                # Blend with existing
                frame[y, x] = [
                    min(255, frame[y, x][0] + r2),
                    min(255, frame[y, x][1] + g2),
                    min(255, frame[y, x][2] + b2)
                ]

    return frame


def plasma(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create plasma ball effect with electrical arcs

    Simulates a plasma ball with lightning tendrils radiating from center

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with plasma ball effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Black background
    # (frame already initialized to zeros = black)

    # Center of plasma ball
    cx = width / 2.0
    cy = height / 2.0

    # Create electrical arc tendrils with appearing/disappearing behavior
    num_arcs = 12  # More arcs for variety
    for arc_id in range(num_arcs):
        # Arc lifetime (some arcs fade in/out)
        lifetime_phase = (offset * 0.5 + arc_id * 0.8) % 3.0

        # Arc is active for 2 seconds, off for 1 second
        if lifetime_phase > 2.0:
            continue  # Arc is not visible

        # Fade in/out at boundaries
        if lifetime_phase < 0.3:
            arc_alpha = lifetime_phase / 0.3  # Fade in
        elif lifetime_phase > 1.7:
            arc_alpha = (2.0 - lifetime_phase) / 0.3  # Fade out
        else:
            arc_alpha = 1.0  # Full brightness

        # Each arc has a base angle
        base_angle = (arc_id / num_arcs) * 2 * math.pi

        # Arc flickers/moves
        angle_offset = math.sin(offset * 2.0 + arc_id * 0.5) * 0.3

        # Draw arc from center to edges
        max_length = max(width, height) * 0.8  # Reach edges

        for step in range(int(max_length)):
            # Normalized distance along arc (0 to 1)
            t = step / max_length

            # Arc angle with some wobble
            wobble = math.sin(offset * 3.0 + arc_id + t * 5.0) * 0.2
            angle = base_angle + angle_offset + wobble

            # Position along arc
            x = cx + math.cos(angle) * step
            y = cy + math.sin(angle) * step

            ix = int(x)
            iy = int(y)

            if 0 <= ix < width and 0 <= iy < height:
                # Arc brightness decreases with distance
                intensity = (1.0 - t) ** 1.2 * arc_alpha

                # Flickering
                flicker = 0.8 + 0.2 * math.sin(offset * 8.0 + arc_id * 1.2 + t * 10.0)
                intensity *= flicker

                # Only draw if bright enough
                if intensity > 0.05:
                    # Plasma colors - RED and BLUE only (no green)
                    if intensity > 0.7:
                        # Bright magenta core
                        r = int(255 * intensity)
                        g = 0
                        b = int(255 * intensity)
                    elif intensity > 0.4:
                        # Magenta-purple
                        r = int(255 * intensity)
                        g = 0
                        b = int(220 * intensity)
                    elif intensity > 0.2:
                        # Purple
                        r = int(200 * intensity)
                        g = 0
                        b = int(255 * intensity)
                    else:
                        # Dim purple outer glow
                        r = int(150 * intensity)
                        g = 0
                        b = int(200 * intensity)

                    # Draw 1-pixel center trail
                    frame[iy, ix] = [
                        min(255, frame[iy, ix][0] + r),
                        0,  # No green
                        min(255, frame[iy, ix][2] + b)
                    ]

                    # Add fading glow around the center trail
                    # Multiple rings with decreasing intensity
                    for ring in range(1, 4):  # 3 rings of glow
                        glow_intensity = intensity * (0.5 / ring)  # Fade with each ring
                        if glow_intensity > 0.02:
                            glow_r = int(r * (0.5 / ring))
                            glow_b = int(b * (0.5 / ring))

                            for glow_dy in range(-ring, ring + 1):
                                for glow_dx in range(-ring, ring + 1):
                                    # Skip center pixel (already drawn)
                                    if glow_dx == 0 and glow_dy == 0:
                                        continue

                                    # Only draw on the ring perimeter
                                    dist = max(abs(glow_dx), abs(glow_dy))
                                    if dist != ring:
                                        continue

                                    gx = ix + glow_dx
                                    gy = iy + glow_dy
                                    if 0 <= gx < width and 0 <= gy < height:
                                        frame[gy, gx] = [
                                            min(255, frame[gy, gx][0] + glow_r),
                                            0,  # No green
                                            min(255, frame[gy, gx][2] + glow_b)
                                        ]

    # Bright core at center
    core_radius = 2
    for dy in range(-core_radius, core_radius + 1):
        for dx in range(-core_radius, core_radius + 1):
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= core_radius:
                core_x = int(cx + dx)
                core_y = int(cy + dy)
                if 0 <= core_x < width and 0 <= core_y < height:
                    # Pulsing bright core - magenta (red + blue, no green)
                    pulse = 0.8 + 0.2 * math.sin(offset * 4.0)
                    intensity = (1.0 - dist / core_radius) * pulse
                    frame[core_y, core_x] = [
                        min(255, frame[core_y, core_x][0] + int(255 * intensity)),
                        0,  # No green
                        min(255, frame[core_y, core_x][2] + int(255 * intensity))
                    ]

    return frame


def perlin_noise_flow(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create flowing organic color fields using Perlin noise

    Smooth, organic color patterns that flow and evolve over time

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with Perlin noise flow
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Parameters for noise sampling
    scale = 0.15  # Larger scale = larger features
    time_scale = 0.6  # Speed of animation (2x faster)

    for y in range(height):
        for x in range(width):
            # Sample Perlin noise with multiple octaves for detail
            # Octave 1: Large features
            noise1 = _perlin.noise(x * scale + offset * time_scale,
                                   y * scale + offset * time_scale * 0.8)

            # Octave 2: Medium features
            noise2 = _perlin.noise(x * scale * 2 + offset * time_scale * 1.2,
                                   y * scale * 2 + offset * time_scale) * 0.5

            # Octave 3: Small features
            noise3 = _perlin.noise(x * scale * 4 + offset * time_scale * 0.7,
                                   y * scale * 4 + offset * time_scale * 1.5) * 0.25

            # Combine octaves
            combined_noise = noise1 + noise2 + noise3

            # Normalize to 0-1 range (Perlin noise returns roughly -1 to 1)
            value = (combined_noise + 1.75) / 3.5  # Adjusted for 3 octaves
            value = max(0.0, min(1.0, value))

            # Create flowing hue from noise
            # Use second noise sample for color variation
            hue_noise = _perlin.noise(x * scale * 0.5 - offset * time_scale * 0.5,
                                      y * scale * 0.5 + offset * time_scale * 0.3)
            hue = (hue_noise + value + offset * 0.05) % 1.0

            # Saturation and brightness from noise
            saturation = 0.7 + value * 0.3  # High saturation for vibrant colors
            brightness = 0.5 + value * 0.5  # Variable brightness

            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)

            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    return frame


def kaleidoscope(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create kaleidoscope effect with symmetric mirroring

    Rotating colorful patterns with radial symmetry

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with kaleidoscope effect
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Center of kaleidoscope
    cx = width / 2.0
    cy = height / 2.0

    # Number of mirror segments (6-fold symmetry)
    num_segments = 6
    segment_angle = (2 * math.pi) / num_segments

    # Rotation animation
    rotation = offset * 0.5

    for y in range(height):
        for x in range(width):
            # Convert to polar coordinates relative to center
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)

            # Apply rotation
            angle += rotation

            # Map to one segment using modulo (create symmetry)
            segment_angle_pos = angle % segment_angle

            # Mirror every other segment for more complexity
            segment_id = int(angle / segment_angle) % num_segments
            if segment_id % 2 == 1:
                segment_angle_pos = segment_angle - segment_angle_pos

            # Create pattern based on distance and angle within segment
            # Multiple layers of patterns
            pattern1 = math.sin(dist * 0.5 + segment_angle_pos * 3 + offset * 0.8) * 0.5 + 0.5
            pattern2 = math.sin(dist * 0.3 - segment_angle_pos * 5 + offset * 1.2) * 0.5 + 0.5
            pattern3 = math.sin(dist * 0.8 + segment_angle_pos * 2 - offset * 0.6) * 0.5 + 0.5

            # Combine patterns
            combined = (pattern1 + pattern2 * 0.7 + pattern3 * 0.5) / 2.2

            # Distance-based brightness falloff
            brightness_falloff = 1.0 - (dist / (max(width, height) * 0.7))
            brightness_falloff = max(0.3, min(1.0, brightness_falloff))

            # Color based on angle and distance
            hue = (segment_angle_pos / segment_angle + dist * 0.02 + offset * 0.1) % 1.0

            # High saturation for vibrant colors
            saturation = 0.9 + combined * 0.1

            # Brightness varies with pattern
            brightness = (0.5 + combined * 0.5) * brightness_falloff

            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)

            frame[y, x] = [int(r * 255), int(g * 255), int(b * 255)]

    return frame


def geometric_patterns(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create animated geometric patterns with rotating shapes

    Multiple geometric shapes (triangles, squares, hexagons, circles)
    rotating and scaling with vibrant colors

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with geometric patterns
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark background
    frame[:, :] = [10, 10, 15]

    # Center point
    cx = width / 2.0
    cy = height / 2.0

    # Draw multiple rotating shapes
    num_shapes = 4
    for shape_id in range(num_shapes):
        # Each shape has different properties
        rotation = offset * (0.5 + shape_id * 0.3)
        scale = 0.3 + shape_id * 0.15

        # Shape type cycles through: triangle, square, hexagon, circle
        shape_type = shape_id % 4

        # Color for this shape
        hue = (shape_id * 0.25 + offset * 0.05) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = [int(r * 255), int(g * 255), int(b * 255)]

        # Oscillating size
        size_mod = 0.8 + 0.2 * math.sin(offset * 2.0 + shape_id)
        radius = (5 + shape_id * 3) * scale * size_mod

        if shape_type == 0:
            # Triangle (3 vertices)
            draw_polygon(frame, cx, cy, radius, 3, rotation, color)
        elif shape_type == 1:
            # Square (4 vertices)
            draw_polygon(frame, cx, cy, radius, 4, rotation, color)
        elif shape_type == 2:
            # Hexagon (6 vertices)
            draw_polygon(frame, cx, cy, radius, 6, rotation, color)
        else:
            # Circle
            draw_circle(frame, cx, cy, radius, color)

    return frame


def draw_polygon(frame, cx, cy, radius, num_sides, rotation, color):
    """Draw a polygon outline"""
    height, width = frame.shape[:2]

    # Calculate vertices
    vertices = []
    for i in range(num_sides):
        angle = rotation + (i / num_sides) * 2 * math.pi
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        vertices.append((x, y))

    # Draw lines between vertices
    for i in range(num_sides):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % num_sides]
        draw_line(frame, x1, y1, x2, y2, color)


def draw_line(frame, x1, y1, x2, y2, color):
    """Draw a line using Bresenham's algorithm"""
    height, width = frame.shape[:2]

    # Bresenham's line algorithm
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < width and 0 <= y1 < height:
            frame[y1, x1] = color

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def draw_circle(frame, cx, cy, radius, color):
    """Draw a circle outline"""
    height, width = frame.shape[:2]

    # Midpoint circle algorithm
    x = 0
    y = int(radius)
    d = 1 - radius

    def plot_circle_points(xc, yc, x, y):
        points = [
            (xc + x, yc + y), (xc - x, yc + y),
            (xc + x, yc - y), (xc - x, yc - y),
            (xc + y, yc + x), (xc - y, yc + x),
            (xc + y, yc - x), (xc - y, yc - x)
        ]
        for px, py in points:
            ix, iy = int(px), int(py)
            if 0 <= ix < width and 0 <= iy < height:
                frame[iy, ix] = color

    plot_circle_points(cx, cy, x, y)

    while x < y:
        x += 1
        if d < 0:
            d += 2 * x + 1
        else:
            y -= 1
            d += 2 * (x - y) + 1
        plot_circle_points(cx, cy, x, y)


def starfield(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create meteor shower effect

    Meteors falling at an angle with glowing trails

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with meteor shower
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark night sky with slight gradient
    for y in range(height):
        darkness = int(2 + (y / height) * 3)
        frame[y, :] = [darkness // 3, darkness // 3, darkness]

    # Create meteors with randomized properties
    num_meteors = 15
    for meteor_id in range(num_meteors):
        # Use only meteor_id for consistent pseudo-random properties
        seed = meteor_id * 97

        # Random starting position (consistent per meteor)
        base_x = (seed * 73) % (width + 30)
        start_y = (seed * 137) % (height + 25)

        # Random speed (2.0 to 6.0) - consistent per meteor
        speed = 2.0 + ((seed * 41) % 40) / 10.0

        # Random trail length (3 to 9) - consistent per meteor
        trail_length = 3 + ((seed * 23) % 7)

        # Random angle variation - consistent per meteor
        angle_factor = 0.3 + ((seed * 17) % 30) / 100.0

        # Meteor moves diagonally
        progress = offset * speed
        meteor_x = base_x + int(progress * angle_factor)
        meteor_y_raw = (start_y + int(progress)) % (height + 30)
        meteor_y = height - 1 - (meteor_y_raw % height)

        # Random color variations
        color_seed = (seed * 13) % 10
        if color_seed < 2:
            color = [200, 220, 255]  # Blue-white (hot)
        elif color_seed < 5:
            color = [255, 240, 180]  # Yellow-white
        else:
            color = [255, 255, 255]  # Pure white

        # Draw meteor trail (diagonal streak)
        for i in range(trail_length):
            # Trail goes up and to the left from meteor head
            trail_x = (meteor_x - i) % width
            trail_y = meteor_y + i

            if 0 <= trail_y < height and 0 <= trail_x < width:
                # Fade from bright at head to dim at tail
                fade = (1.0 - i / trail_length) ** 2
                pixel_color = [
                    int(color[0] * fade),
                    int(color[1] * fade),
                    int(color[2] * fade)
                ]

                # Brightest pixel at head (i=0)
                if i == 0:
                    frame[trail_y, trail_x] = pixel_color
                else:
                    # Blend with existing pixel
                    frame[trail_y, trail_x] = [
                        min(255, frame[trail_y, trail_x][0] + pixel_color[0]),
                        min(255, frame[trail_y, trail_x][1] + pixel_color[1]),
                        min(255, frame[trail_y, trail_x][2] + pixel_color[2])
                    ]

    return frame


def matrix_rain(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create Matrix-style falling characters

    Green characters falling at different speeds

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with Matrix rain
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark background with slight green tint
    frame[:, :] = [0, 5, 0]

    # Create falling columns with randomized properties
    num_columns = width
    for col_x in range(num_columns):
        # Use only col_x for consistent pseudo-random properties
        seed = col_x * 53

        # Random speed (2.0 to 7.0) - consistent per column
        speed = 2.0 + ((seed * 31) % 50) / 10.0

        # Random phase offset - consistent per column
        phase = (seed * 19) % (height + 10)

        # Column position (falls downward - flip coordinate)
        col_y_raw = (offset * speed + phase) % (height + 20)
        col_y = height - 1 - (col_y_raw % height)

        # Random trail length (5 to 12) - consistent per column
        trail_length = 5 + ((seed * 17) % 8)
        for i in range(trail_length):
            char_y = int(col_y + i)
            if 0 <= char_y < height:
                # Fade from bright at head to dark at tail
                intensity = (1.0 - i / trail_length) ** 2
                green = int(255 * intensity)

                # Brightest pixel at head
                if i == 0:
                    frame[char_y, col_x] = [200, 255, 200]  # Bright white-green
                else:
                    frame[char_y, col_x] = [0, green, 0]

    return frame


def lava_lamp(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create lava lamp effect with physics simulation

    Simulates actual lava lamp behavior: blobs heat up at bottom, rise,
    cool at top, and sink back down.

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with lava lamp
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark background
    frame[:, :] = [10, 0, 20]

    # Simulate blobs with physics
    num_blobs = 6
    blob_data = []

    for blob_id in range(num_blobs):
        # Each blob has its own cycle period
        blob_seed = blob_id * 137
        cycle_period = 15.0 + ((blob_seed * 23) % 50) / 10.0  # 15-20 seconds per cycle
        phase_offset = ((blob_seed * 41) % 100) / 10.0

        # Current position in cycle (0 to 1)
        cycle_pos = ((offset + phase_offset) / cycle_period) % 1.0

        # Blob oscillates vertically like real lava lamp
        # Bottom: Y=0-5, Top: Y=height-5 to height
        if cycle_pos < 0.45:
            # Rising phase (bottom to top)
            rise_progress = cycle_pos / 0.45
            # Ease in-out for smooth motion
            eased = rise_progress * rise_progress * (3.0 - 2.0 * rise_progress)
            blob_y = 3 + eased * (height - 6)
        elif cycle_pos < 0.55:
            # Pause at top
            blob_y = height - 3
        else:
            # Sinking phase (top to bottom)
            sink_progress = (cycle_pos - 0.55) / 0.45
            # Ease in-out for smooth motion
            eased = sink_progress * sink_progress * (3.0 - 2.0 * sink_progress)
            blob_y = (height - 3) - eased * (height - 6)

        # Slight horizontal drift
        drift_offset = ((blob_seed * 19) % width)
        blob_x = width / 2 + 3 * math.sin(offset * 0.3 + blob_id * 2.1) + (drift_offset % 10) - 5

        # Temperature based on height (hot at bottom, cool at top)
        temp_factor = 1.0 - (blob_y / height)  # 1.0 at bottom, 0.0 at top

        # Blob size varies slightly with temperature (larger when hot)
        base_size = 28.0 + ((blob_seed * 17) % 10)
        blob_size = base_size * (0.9 + temp_factor * 0.2)

        blob_data.append((blob_x, blob_y, blob_size, temp_factor))

    # Calculate metaball field for each pixel
    for y in range(height):
        for x in range(width):
            # Sum of inverse distances (metaball formula)
            field = 0.0
            weighted_temp = 0.0

            for blob_x, blob_y, blob_size, temp_factor in blob_data:
                dx = x - blob_x
                dy = y - blob_y
                dist_sq = dx * dx + dy * dy
                if dist_sq > 0.1:  # Avoid division by zero
                    contribution = blob_size / dist_sq
                    field += contribution
                    weighted_temp += contribution * temp_factor

            # Threshold to create blob shape
            if field > 2.0:
                # Average temperature at this pixel
                avg_temp = weighted_temp / field if field > 0 else 0.5

                # Color based on temperature (hot = yellow/orange, cool = red/dark red)
                intensity = min(1.0, (field - 2.0) / 3.0)

                # Temperature affects color
                if avg_temp > 0.7:
                    # Hot - bright yellow/orange
                    r, g, b = 255, int(180 + avg_temp * 75), 0
                elif avg_temp > 0.4:
                    # Warm - orange
                    r, g, b = 255, int(80 + avg_temp * 120), 0
                elif avg_temp > 0.2:
                    # Cool - red
                    r, g, b = int(200 + avg_temp * 55), int(avg_temp * 50), 0
                else:
                    # Cold - dark red
                    r, g, b = int(150 + avg_temp * 100), 0, 0

                frame[y, x] = [
                    int(r * intensity),
                    int(g * intensity),
                    int(b * intensity)
                ]

    return frame


def dna_helix(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create rotating DNA double helix

    Two intertwined helical strands with connecting base pairs

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with DNA helix
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark background
    frame[:, :] = [2, 2, 5]

    # Draw helix along vertical axis
    cx = width / 2.0
    num_points = height

    for i in range(num_points):
        y = i
        progress = i / height

        # Two strands rotating in opposite directions
        angle1 = progress * 4 * math.pi + offset * 1.5
        angle2 = angle1 + math.pi  # Opposite side

        # Radius of helix
        radius = width * 0.25

        # Strand 1 (cyan)
        x1 = cx + radius * math.cos(angle1)
        if 0 <= int(x1) < width and 0 <= y < height:
            frame[y, int(x1)] = [0, 200, 255]
            # Make strand thicker
            if int(x1) + 1 < width:
                frame[y, int(x1) + 1] = [0, 150, 200]

        # Strand 2 (magenta)
        x2 = cx + radius * math.cos(angle2)
        if 0 <= int(x2) < width and 0 <= y < height:
            frame[y, int(x2)] = [255, 0, 200]
            # Make strand thicker
            if int(x2) + 1 < width:
                frame[y, int(x2) + 1] = [200, 0, 150]

        # Base pairs connecting strands (every few rows)
        if i % 3 == 0:
            # Draw line between strands
            x1_int = int(x1)
            x2_int = int(x2)
            if x1_int < x2_int:
                for x in range(x1_int, x2_int + 1):
                    if 0 <= x < width and 0 <= y < height:
                        frame[y, x] = [100, 100, 150]
            else:
                for x in range(x2_int, x1_int + 1):
                    if 0 <= x < width and 0 <= y < height:
                        frame[y, x] = [100, 100, 150]

    return frame


def _select_burst_type(seed: int) -> str:
    """
    Select firework burst type based on seed

    Args:
        seed: Deterministic seed value

    Returns:
        Burst type: 'peony', 'willow', 'palm', or 'ring'
    """
    type_index = ((seed * 41) % 100)
    if type_index < 25:
        return 'peony'  # 25% - basic spherical
    elif type_index < 50:
        return 'willow'  # 25% - drooping trails
    elif type_index < 75:
        return 'palm'    # 25% - thick arcing trails
    else:
        return 'ring'    # 25% - expanding rings


def _select_color_effect(seed: int) -> str:
    """
    Select firework color effect based on seed

    Args:
        seed: Deterministic seed value

    Returns:
        Color effect: 'solid', 'multicolor', 'changing', or 'glitter'
    """
    effect_index = ((seed * 53) % 100)
    if effect_index < 25:
        return 'solid'      # 25% - single color
    elif effect_index < 50:
        return 'multicolor' # 25% - rainbow
    elif effect_index < 75:
        return 'changing'   # 25% - color shift over time
    else:
        return 'glitter'    # 25% - sparkles


def _select_special_effect(seed: int) -> str:
    """
    Select firework special effect based on seed

    Args:
        seed: Deterministic seed value

    Returns:
        Special effect: 'none', 'crossette', 'strobe', or 'trail'
    """
    effect_index = ((seed * 67) % 100)
    if effect_index < 40:
        return 'none'      # 40% - basic particles (higher probability for simpler fireworks)
    elif effect_index < 60:
        return 'crossette' # 20% - secondary bursts
    elif effect_index < 80:
        return 'strobe'    # 20% - pulsing
    else:
        return 'trail'     # 20% - comet tails


def _get_particle_color(base_hue: float, particle_id: int, num_particles: int,
                       explosion_time: float, color_effect: str, seed: int,
                       offset: float) -> tuple:
    """
    Calculate particle color based on color effect type

    Args:
        base_hue: Base hue value (0.0-1.0)
        particle_id: Index of particle
        num_particles: Total number of particles
        explosion_time: Time since explosion started
        color_effect: Type of color effect ('solid', 'multicolor', 'changing', 'glitter')
        seed: Seed for deterministic randomness
        offset: Animation offset for glitter timing

    Returns:
        (r, g, b) color tuple
    """
    if color_effect == 'solid':
        # Single solid color
        hue = base_hue
        saturation = 1.0
        brightness = 1.0

    elif color_effect == 'multicolor':
        # Rainbow - each particle gets different hue
        hue = (particle_id / num_particles) % 1.0
        saturation = 1.0
        brightness = 1.0

    elif color_effect == 'changing':
        # Color shifts over time
        hue = (base_hue + (explosion_time * 0.3)) % 1.0
        saturation = 1.0
        brightness = 1.0

    elif color_effect == 'glitter':
        # Random sparkles - some particles get brightness boost
        hue = base_hue
        saturation = 1.0
        # Deterministic sparkle timing
        sparkle_check = ((seed + particle_id + int(offset * 10)) % 7)
        brightness = 2.0 if sparkle_check == 0 else 1.0

    else:
        hue = base_hue
        saturation = 1.0
        brightness = 1.0

    # Convert to RGB and clamp to 0-255 range
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return (
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255)))
    )


def _apply_burst_physics(center_x: float, center_y: float, angle: float,
                        speed: float, explosion_time: float, burst_type: str,
                        particle_id: int, num_particles: int) -> tuple:
    """
    Apply physics based on burst type

    Args:
        center_x: Explosion center X coordinate
        center_y: Explosion center Y coordinate
        angle: Particle launch angle
        speed: Particle speed
        explosion_time: Time since explosion
        burst_type: Type of burst ('peony', 'willow', 'palm', 'ring')
        particle_id: Index of particle
        num_particles: Total number of particles

    Returns:
        (px, py) particle position tuple
    """
    if burst_type == 'peony':
        # Standard spherical burst
        px = center_x + speed * explosion_time * math.cos(angle)
        py = center_y + speed * explosion_time * math.sin(angle)
        # Standard gravity
        py -= explosion_time * explosion_time * 2

    elif burst_type == 'willow':
        # Drooping trails with stronger gravity and slower horizontal movement
        px = center_x + speed * explosion_time * math.cos(angle) * 0.6  # Slower horizontal
        py = center_y + speed * explosion_time * math.sin(angle) * 0.7  # Slower vertical
        # Stronger gravity (3x) and downward velocity bias
        py -= explosion_time * explosion_time * 6
        py -= explosion_time * 2  # Reduced from 3 to 2 for slower droop

    elif burst_type == 'palm':
        # Thick arcing trails, more vertical
        # Bias angle toward vertical
        vertical_bias = 0.3 * math.pi * math.sin(angle)
        biased_angle = angle + vertical_bias
        px = center_x + speed * explosion_time * math.cos(biased_angle) * 0.7
        py = center_y + speed * explosion_time * math.sin(biased_angle)
        # Moderate gravity
        py -= explosion_time * explosion_time * 3

    elif burst_type == 'ring':
        # Expanding concentric rings
        # Particles at discrete radii
        ring_index = particle_id % 3  # 3 rings
        ring_radius = (ring_index + 1) * speed * explosion_time * 0.8
        px = center_x + ring_radius * math.cos(angle)
        py = center_y + ring_radius * math.sin(angle)
        # Light gravity
        py -= explosion_time * explosion_time * 1.5

    else:
        # Default to peony
        px = center_x + speed * explosion_time * math.cos(angle)
        py = center_y + speed * explosion_time * math.sin(angle)
        py -= explosion_time * explosion_time * 2

    return (px, py)


def _render_particle_with_effects(frame: np.ndarray, px: float, py: float,
                                  base_color: tuple, fade: float, explosion_time: float,
                                  special_effect: str, seed: int, particle_id: int,
                                  angle: float, speed: float, offset: float,
                                  width: int, height: int, burst_type: str) -> None:
    """
    Render particle with special effects

    Args:
        frame: Frame array to draw on
        px, py: Particle position
        base_color: Base RGB color tuple
        fade: Fade factor (0.0-1.0)
        explosion_time: Time since explosion
        special_effect: Type of effect ('none', 'crossette', 'strobe', 'trail')
        seed: Seed for deterministic randomness
        particle_id: Index of particle
        angle: Particle angle
        speed: Particle speed
        offset: Animation offset
        width, height: Frame dimensions
        burst_type: Type of burst for trail rendering
    """
    # Apply fade to color
    faded_color = [
        int(base_color[0] * fade),
        int(base_color[1] * fade),
        int(base_color[2] * fade)
    ]

    px_int = int(px)
    py_int = int(py)

    if special_effect == 'none':
        # Standard particle rendering
        if 0 <= px_int < width and 0 <= py_int < height:
            frame[py_int, px_int] = faded_color

    elif special_effect == 'strobe':
        # Pulsing particles - slower pulse with minimum brightness
        strobe_wave = abs(math.sin(offset * 6 + particle_id * 0.5))  # Slower: 6Hz instead of 20Hz
        strobe_intensity = 0.3 + (strobe_wave * 0.7)  # Range: 0.3 to 1.0 (never fully dark)
        strobed_color = [
            int(faded_color[0] * strobe_intensity),
            int(faded_color[1] * strobe_intensity),
            int(faded_color[2] * strobe_intensity)
        ]
        if 0 <= px_int < width and 0 <= py_int < height:
            frame[py_int, px_int] = strobed_color

    elif special_effect == 'trail':
        # Comet trails - draw main particle and fading trail
        if 0 <= px_int < width and 0 <= py_int < height:
            frame[py_int, px_int] = faded_color

        # Draw 3-4 trail pixels behind particle
        trail_length = 3 if burst_type == 'ring' else 4
        for i in range(1, trail_length + 1):
            trail_factor = 1.0 - (i / trail_length)
            trail_px = px - i * math.cos(angle) * 0.5
            trail_py = py - i * math.sin(angle) * 0.5
            trail_px_int = int(trail_px)
            trail_py_int = int(trail_py)

            if 0 <= trail_px_int < width and 0 <= trail_py_int < height:
                trail_color = [
                    int(faded_color[0] * trail_factor),
                    int(faded_color[1] * trail_factor),
                    int(faded_color[2] * trail_factor)
                ]
                # Additive blending for trails
                current = frame[trail_py_int, trail_px_int]
                frame[trail_py_int, trail_px_int] = [
                    min(255, current[0] + trail_color[0]),
                    min(255, current[1] + trail_color[1]),
                    min(255, current[2] + trail_color[2])
                ]

    elif special_effect == 'crossette':
        # Main particle
        if 0 <= px_int < width and 0 <= py_int < height:
            frame[py_int, px_int] = faded_color

        # Secondary bursts - longer duration and more visible
        if 0.8 < explosion_time < 2.5:  # Longer window: 0.8-2.5s instead of 1.4-1.8s
            # Spawn 4-6 secondary particles
            num_secondary = 4 + ((seed + particle_id) % 3)
            burst_start_time = 0.8
            burst_progress = explosion_time - burst_start_time

            for sec_id in range(num_secondary):
                sec_angle = (sec_id / num_secondary) * 2 * math.pi
                sec_distance = burst_progress * speed * 2.0  # Faster secondary particles
                sec_px = px + sec_distance * math.cos(sec_angle)
                sec_py = py + sec_distance * math.sin(sec_angle)
                sec_px_int = int(sec_px)
                sec_py_int = int(sec_py)

                if 0 <= sec_px_int < width and 0 <= sec_py_int < height:
                    # Much brighter secondary particles that fade over time
                    secondary_fade = 1.0 - (burst_progress / 1.7)  # Fade over 1.7s
                    if secondary_fade > 0:
                        sec_color = [
                            min(255, int(faded_color[0] * 2.0 * secondary_fade)),
                            min(255, int(faded_color[1] * 2.0 * secondary_fade)),
                            min(255, int(faded_color[2] * 2.0 * secondary_fade))
                        ]
                        # Draw a 3x3 cluster for more visibility
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                cluster_x = sec_px_int + dx
                                cluster_y = sec_py_int + dy
                                if 0 <= cluster_x < width and 0 <= cluster_y < height:
                                    brightness_mult = 1.0 if (dx == 0 and dy == 0) else 0.5
                                    cluster_color = [
                                        int(sec_color[0] * brightness_mult),
                                        int(sec_color[1] * brightness_mult),
                                        int(sec_color[2] * brightness_mult)
                                    ]
                                    current = frame[cluster_y, cluster_x]
                                    frame[cluster_y, cluster_x] = [
                                        min(255, current[0] + cluster_color[0]),
                                        min(255, current[1] + cluster_color[1]),
                                        min(255, current[2] + cluster_color[2])
                                    ]

    else:
        # Default rendering
        if 0 <= px_int < width and 0 <= py_int < height:
            frame[py_int, px_int] = faded_color


def fireworks(width: int, height: int, offset: float = 0) -> np.ndarray:
    """
    Create enhanced fireworks particle system

    Multiple burst types, color effects, and special effects for variety

    Burst Types:
    - Peony: Classic spherical burst
    - Willow: Drooping trails
    - Palm: Thick arcing trails
    - Ring: Expanding concentric rings

    Color Effects:
    - Solid: Single color per firework
    - Multicolor: Rainbow of colors in single burst
    - Changing: Color shifts over time
    - Glitter: Random bright sparkles

    Special Effects:
    - None: Basic particles
    - Crossette: Secondary mid-air bursts
    - Strobe: Pulsing particles
    - Trail: Comet-like trailing effect

    Args:
        width: Frame width (32)
        height: Frame height (32)
        offset: Animation time offset

    Returns:
        Frame array with fireworks
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Dark night sky
    frame[:, :] = [0, 0, 1]

    # Multiple fireworks with randomized properties
    num_fireworks = 4
    for fw_id in range(num_fireworks):
        # Base seed from firework ID
        base_seed = fw_id * 79
        cycle_offset = ((base_seed * 31) % 50) / 10.0

        # Random cycle duration (3 to 6 seconds) - consistent per firework
        cycle_duration = 3.0 + ((base_seed * 23) % 30) / 10.0
        cycle_time = (offset + cycle_offset) % cycle_duration

        # Calculate which cycle we're in (changes over time for variety)
        cycle_number = int((offset + cycle_offset) / cycle_duration)

        # Seed that changes each cycle for varied effects
        seed = base_seed + cycle_number * 997

        # Random launch x position - varies each cycle
        launch_x = 5 + ((seed * 47) % (width - 10))

        # Random explosion height (50% to 75% of height) - varies each cycle
        explosion_height = 0.5 + ((seed * 37) % 25) / 100.0

        # Select effect types for this firework (changes each cycle)
        burst_type = _select_burst_type(seed)
        color_effect = _select_color_effect(seed)
        special_effect = _select_special_effect(seed)

        # Launch phase (0-1 sec)
        if cycle_time < 1.0:
            # Rising rocket (launches from bottom upward)
            launch_progress = cycle_time
            rocket_y = int(launch_progress * height * explosion_height)
            rocket_x = launch_x

            if 0 <= rocket_y < height and 0 <= rocket_x < width:
                frame[rocket_y, rocket_x] = [255, 255, 255]
                # Trail below the rocket (lower Y in flipped coords)
                if rocket_y - 1 >= 0:
                    frame[rocket_y - 1, rocket_x] = [150, 150, 150]

        # Explosion phase (1-4+ sec)
        elif cycle_time < cycle_duration - 0.5:
            explosion_time = cycle_time - 1.0
            center_y = explosion_height * height
            center_x = float(launch_x)

            # Base hue for this firework
            base_hue = ((seed * 13) % 100) / 100.0

            # Particle count varies by burst type
            if burst_type == 'palm':
                num_particles = 8 + ((seed * 19) % 5)  # 8-12 particles
            elif burst_type == 'ring':
                num_particles = 24  # Multiple of 3 for 3 rings
            else:
                num_particles = 15 + ((seed * 19) % 16)  # 15-30 particles

            # Particle speed
            particle_speed = 4.0 + ((seed * 29) % 25) / 10.0

            for particle_id in range(num_particles):
                angle = (particle_id / num_particles) * 2 * math.pi

                # Apply burst-specific physics
                px, py = _apply_burst_physics(
                    center_x, center_y, angle, particle_speed,
                    explosion_time, burst_type, particle_id, num_particles
                )

                # Calculate particle color with effects
                base_color = _get_particle_color(
                    base_hue, particle_id, num_particles, explosion_time,
                    color_effect, seed, offset
                )

                # Fade out over time
                fade = 1.0 - (explosion_time / 3.0)
                if fade > 0:
                    # Render particle with special effects
                    _render_particle_with_effects(
                        frame, px, py, base_color, fade, explosion_time,
                        special_effect, seed, particle_id, angle,
                        particle_speed, offset, width, height, burst_type
                    )

                    # Palm burst: render thicker particles (3-5 pixels wide)
                    if burst_type == 'palm' and fade > 0:
                        faded_color = [
                            int(base_color[0] * fade),
                            int(base_color[1] * fade),
                            int(base_color[2] * fade)
                        ]
                        # Draw thicker particles
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                thick_px = int(px) + dx
                                thick_py = int(py) + dy
                                if 0 <= thick_px < width and 0 <= thick_py < height:
                                    if dx == 0 and dy == 0:
                                        continue  # Already drawn by main render
                                    # Dimmer for outer pixels
                                    dim_color = [
                                        int(faded_color[0] * 0.6),
                                        int(faded_color[1] * 0.6),
                                        int(faded_color[2] * 0.6)
                                    ]
                                    current = frame[thick_py, thick_px]
                                    frame[thick_py, thick_px] = [
                                        min(255, current[0] + dim_color[0]),
                                        min(255, current[1] + dim_color[1]),
                                        min(255, current[2] + dim_color[2])
                                    ]

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
    "fireflies": fireflies,
    "aquarium": aquarium,
    "ocean_waves": ocean_waves,
    "northern_lights": northern_lights,
    "plasma": plasma,
    "perlin_noise_flow": perlin_noise_flow,
    "kaleidoscope": kaleidoscope,
    "geometric_patterns": geometric_patterns,
    "starfield": starfield,
    "matrix_rain": matrix_rain,
    "lava_lamp": lava_lamp,
    "dna_helix": dna_helix,
    "fireworks": fireworks,
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
