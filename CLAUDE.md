# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Raspberry Pi-based LED matrix control system supporting multiple WS2812B LED panels in configurable layouts. The Raspberry Pi directly controls the LED panels via GPIO pins using the rpi-ws281x library.

## Architecture

### Direct GPIO Control

This system uses **direct GPIO control** from the Raspberry Pi to WS2812B LED panels. No intermediary microcontroller (like ESP32) is used - the Raspberry Pi's PWM hardware directly generates the precise timing signals required by WS2812B LEDs.

**Key Components:**
- **rpi-ws281x library**: Low-level C library that uses Raspberry Pi PWM/DMA hardware for precise WS2812B timing
- **Panel Configuration**: JSON-based configuration defining panel layout, positioning, and rotation
- **Pattern Generation**: Python code for rendering text, animations, and patterns

### Panel Configuration Format

Panel layouts are defined in JSON files (e.g., `panel_config.json`):
```json
{
  "grid": {
    "grid_width": 2,
    "grid_height": 2,
    "panel_width": 16,
    "panel_height": 16,
    "wiring_pattern": "snake"
  },
  "panels": [
    {"id": 0, "rotation": 0, "position": [0, 0]},
    {"id": 1, "rotation": 0, "position": [1, 0]},
    {"id": 2, "rotation": 180, "position": [1, 1]},
    {"id": 3, "rotation": 180, "position": [0, 1]}
  ]
}
```

**Key Concepts:**
- `position`: Logical position in combined display (measured in panels, not pixels)
- `rotation`: 0, 90, 180, or 270 degrees to account for physical panel orientation
- `wiring_pattern`: "snake" (zigzag), "sequential" (left-to-right), or "vertical_snake"
- All panels are daisy-chained on a single GPIO pin with data flowing through panels in order

### Hardware Wiring

WS2812B panels must be connected in a daisy-chain configuration:
```
Raspberry Pi GPIO Pin 18 (PWM0) → Panel 0 DIN
Panel 0 DOUT → Panel 1 DIN
Panel 1 DOUT → Panel 2 DIN
...
```

**Important GPIO Pins:**
- **GPIO 18 (Pin 12)**: PWM0 - Most common for LED control (default for rpi-ws281x)
- **GPIO 13 (Pin 33)**: PWM1 - Alternative PWM pin
- **GPIO 10 (Pin 19)**: SPI MOSI - Can be used with SPI mode
- **GPIO 21 (Pin 40)**: PCM - Alternative using PCM hardware

**Power Considerations:**
- WS2812B LEDs draw significant current (up to 60mA per LED at full white)
- Use external 5V power supply for LED strips
- Connect Raspberry Pi ground to LED power supply ground
- Never power more than a few LEDs directly from Raspberry Pi 5V pins

## Development Commands

### Environment Setup

**On Raspberry Pi:**
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-dev scons swig

# Install Python dependencies
pip3 install -r requirements.txt

# Note: rpi-ws281x requires root access or proper permissions
# Run with sudo, or set up permissions:
sudo usermod -a -G gpio $USER
```

**Important**: The rpi-ws281x library requires root access or GPIO permissions. Most LED control scripts will need to be run with `sudo`.

### Configuration Generation

Generate panel configurations for different layouts:

```bash
# Use the configurator interactively
python3 configurator.py

# Or programmatically in your code:
from configurator import generate_panel_config
config = generate_panel_config(
    grid_width=2,
    grid_height=2,
    wiring_pattern="snake"
)
```

### Auto-Updater (Optional)

The auto-updater monitors the git repository and restarts the controller when changes are detected:

```bash
# Update auto_updater.py to point to your LED controller script
# Then run manually:
python3 auto_updater.py
```

## Creating a New LED Controller

Since all ESP32-specific code has been removed, you'll need to create a new controller that uses rpi-ws281x. Here's the basic structure:

```python
#!/usr/bin/env python3
import time
import numpy as np
from rpi_ws281x import PixelStrip, Color

# LED strip configuration
LED_COUNT = 1024      # Total number of LEDs (e.g., 4 panels of 16x16 = 1024)
LED_PIN = 18          # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal
LED_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (for NPN transistor level shift)
LED_CHANNEL = 0       # 0 or 1
LED_STRIP = ws.WS2811_STRIP_GRB  # Strip type (GRB for most WS2812B)

# Create LED strip object
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

# Initialize the library (must be called once before other functions)
strip.begin()

# Set pixel color (index, Color(R, G, B))
strip.setPixelColor(0, Color(255, 0, 0))  # Red
strip.show()
```

**Key Functions:**
- `strip.begin()`: Initialize the strip (call once at startup)
- `strip.setPixelColor(index, Color(r, g, b))`: Set color for LED at index
- `strip.show()`: Update the physical LEDs with buffered colors
- `strip.setBrightness(brightness)`: Set global brightness (0-255)
- `Color(r, g, b)` or `Color(r, g, b, w)`: Create color value

## Panel Mapping

When using multiple panels, you need to map 2D coordinates (x, y) to linear LED indices:

```python
def xy_to_index(x, y, panel_width=16, panel_height=16, panels_wide=2):
    """
    Convert 2D coordinates to LED strip index
    Assumes panels are in a snake pattern
    """
    panel_x = x // panel_width
    panel_y = y // panel_height
    pixel_x = x % panel_width
    pixel_y = y % panel_height

    # Calculate panel index (snake pattern)
    if panel_y % 2 == 0:
        panel_index = panel_y * panels_wide + panel_x
    else:
        panel_index = panel_y * panels_wide + (panels_wide - 1 - panel_x)

    # Calculate pixel within panel (typically snake pattern within panel too)
    if pixel_y % 2 == 0:
        pixel_index = pixel_y * panel_width + pixel_x
    else:
        pixel_index = pixel_y * panel_width + (panel_width - 1 - pixel_x)

    return panel_index * (panel_width * panel_height) + pixel_index
```

## Common Patterns

### Wiring Patterns

- **snake**: Most common for daisy-chained LED strips. Alternating left-to-right and right-to-left rows
- **sequential**: Always left-to-right (rare, requires longer wiring)
- **vertical_snake**: Alternating top-to-bottom and bottom-to-top columns

The pattern affects how you map 2D coordinates to LED indices.

### Panel Rotation

Physical panels may be mounted rotated to simplify wiring. Use the `rotation` parameter (0/90/180/270) in panel config. Your controller code should:
1. Generate content in logical coordinates
2. Apply rotation transformation
3. Map to physical LED indices

### Performance Tips

- **Update Rate**: rpi-ws281x can achieve 30-60 FPS depending on LED count
- **Minimize strip.show() calls**: Buffer multiple pixel updates, then call show() once
- **Use numpy**: For bulk pixel operations, numpy arrays are much faster than loops
- **Consider brightness**: Lower brightness = less power = cooler operation
- **CPU affinity**: For critical timing, consider dedicating a CPU core

## Troubleshooting

**"Failed to create mailbox device" or permission errors:**
- Run with `sudo python3 your_script.py`
- Or add user to gpio group and configure udev rules

**LEDs show wrong colors:**
- Check LED_STRIP type (GRB vs RGB vs other)
- Verify in code: `LED_STRIP = ws.WS2811_STRIP_GRB` or `ws.WS2811_STRIP_RGB`

**No output on LEDs:**
1. Verify GPIO pin number (BCM numbering, not physical pin)
2. Check power supply to LEDs
3. Verify ground connection between Pi and LED power supply
4. Check data line connection
5. Test with simple script setting all LEDs to one color

**Flickering or glitching:**
- Disable onboard audio: Add `dtparam=audio=off` to `/boot/config.txt`
- Use PCM instead of PWM: Use GPIO 21 instead of GPIO 18
- Check power supply stability

**Panel orientation wrong:**
1. Use corner test pattern to identify which corner is LED 0
2. Adjust rotation parameters in panel config
3. Verify wiring_pattern matches physical connection order

## Remaining Files

After ESP32 code removal, these files remain:

- **configurator.py**: Generate panel configuration JSON files
- **auto_updater.py**: Git-based auto-deployment system (needs updating with your controller script name)
- **panel_config*.json**: Example panel configurations
- **requirements.txt**: Python dependencies including rpi-ws281x

You will need to create new controller scripts that use rpi-ws281x for actual LED control.
