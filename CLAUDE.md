# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an ESP32 LED matrix control system with multiple deployment configurations:
- **ESP32 Hardware**: Three Arduino sketches for different use cases
- **Raspberry Pi Controller**: Python-based frame renderer and serial communicator 
- **Cross-platform Testing**: Windows-compatible version with GUI mock display
- **Multi-Panel System**: Configurable multi-panel LED matrix with GUI configuration
- **Web Interface**: Vercel-hosted API for remote message control
- **Auto-updater**: Git-based automatic deployment system for Raspberry Pi

## Architecture

The system uses a distributed architecture where different components handle specific responsibilities:

### ESP32 Firmware
- `esp32_frame_display.ino`: Serial-controlled frame display (works with Raspberry Pi)
- `code_for_esp32/code_for_esp32.ino`: WiFi-enabled version that fetches messages from web API
- `esp32_multi_panel_display.ino`: Enhanced version supporting dynamic panel configurations and variable frame sizes

### Python Controllers
- `led_matrix_controller.py`: Main Raspberry Pi controller with text rendering and pattern generation
- `led_matrix_controller_windows_test.py`: Cross-platform version with mock display capabilities
- `rpi_led_controller.py`: Simplified ESP32 communication wrapper
- `multi_panel_led_controller.py`: Multi-panel system with GUI configuration and panel management
- `multi_panel_esp32_controller.py`: Enhanced ESP32 communication supporting dynamic configurations

### Communication Protocol
ESP32 receives serial commands:

**Standard Protocol** (single 16x16 panel):
- `FRAME:<768 bytes RGB data>:END` - Display 16x16 RGB frame
- `BRIGHTNESS:<0-255>\n` - Set LED brightness
- `CLEAR\n` - Clear display

**Enhanced Multi-Panel Protocol**:
- `CONFIG:width,height\n` - Configure total display dimensions
- `FRAME:size:<variable bytes RGB data>:END` - Display frame with specified size
- `STATUS\n` - Get current configuration and status
- `INFO\n` - Show available commands

## Development Commands

### Python Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Or use the provided script
./install_dependencies.sh
```

### Running Controllers
```bash
# Main Raspberry Pi controller
python3 led_matrix_controller.py

# Cross-platform testing with mock display
python3 led_matrix_controller_windows_test.py --mock --gui

# Cross-platform testing with ASCII output
python3 led_matrix_controller_windows_test.py --mock --ascii

# Multi-panel controller (GUI mock mode)
python3 multi_panel_led_controller.py --mock

# Multi-panel controller with ESP32 hardware
python3 multi_panel_led_controller.py --esp32 --port COM3

# Test ESP32 multi-panel controller
python3 multi_panel_esp32_controller.py --width 32 --height 16
```

### Vercel Web Interface
```bash
cd vercel-website/

# Local development
npm run dev

# Deploy to production
vercel --prod
```

### Auto-updater System
```bash
# Install as systemd service (Raspberry Pi)
sudo ./install_updater.sh

# Manual run
python3 auto_updater.py
```

## Key Configuration Points

### ESP32 Hardware Settings
In Arduino sketches, configure:
- `LED_PIN`: GPIO pin for LED data (default: 26)
- `MATRIX_WIDTH/HEIGHT`: Display dimensions (default: 16x16)
- `FLIP_HORIZONTAL/VERTICAL`: Orientation adjustments
- `SERPENTINE_LAYOUT`: Wiring pattern (zigzag vs row-by-row)

### WiFi-enabled ESP32 
Update in `code_for_esp32.ino`:
- WiFi credentials (ssid/password)
- Server URL for message API
- Update interval timing

### Raspberry Pi Integration
The auto-updater monitors git repository changes and restarts the controller automatically. Default paths in `auto_updater.py`:
- Repository: `/home/jim/Esp32-matrix`
- Target script: `led_matrix_controller.py`
- Check interval: 30 seconds

## Testing and Mock Mode

The Windows-compatible version includes comprehensive testing capabilities:
- `--mock`: Enable software-only mode (no serial hardware required)
- `--gui`: Tkinter-based visual LED matrix simulator  
- `--ascii`: Console-based matrix display with Unicode blocks
- `--port`: Specify serial port (auto-detects COM3 on Windows, /dev/ttyUSB0 on Linux)

Mock mode supports all controller features including scrolling text, patterns (rainbow, spiral, wave), and brightness control.

## Serial Communication

Hardware controllers expect specific serial configuration:
- Baud rate: 115200
- Port: `/dev/ttyUSB0` (Raspberry Pi), `COM3` (Windows)
- Frame format: Binary RGB data in serpentine layout for LED strips

## Multi-Panel System

The multi-panel system allows combining multiple LED matrix panels into larger displays with individual panel controls.

### Key Features
- **Dynamic Panel Configuration**: Add/remove panels with custom dimensions and positions
- **Individual Panel Rotation**: Rotate each panel independently (0°, 90°, 180°, 270°)
- **GUI Configuration Interface**: Visual panel layout editor with real-time preview
- **Save/Load Configurations**: JSON-based panel configuration persistence
- **Cross-Platform Display**: Works with both mock GUI display and ESP32 hardware
- **Text Distribution**: Automatically distributes scrolling text across all configured panels

### Usage Examples
```bash
# Run multi-panel controller with default 2x1 layout (mock display)
python3 multi_panel_led_controller.py

# Connect to ESP32 hardware
python3 multi_panel_led_controller.py --esp32

# Test ESP32 communication with 4x2 layout (64x32 total)
python3 multi_panel_esp32_controller.py --width 64 --height 32
```

### Panel Configuration
Use the GUI configuration interface to:
1. Add/remove panels with custom dimensions
2. Set panel positions (X/Y offsets) 
3. Configure individual panel rotations
4. Preview the complete layout
5. Save/load configurations as JSON files

The system automatically calculates total display dimensions and distributes text rendering across all configured panels.

## Dependencies

### Python Requirements
- `pyserial>=3.5`: Serial communication with ESP32
- `numpy>=1.19.0`: Matrix operations and frame buffering  
- `Pillow>=8.0.0`: Text rendering and image processing
- `tkinter`: GUI interface (usually included with Python)

### Arduino Libraries
- `FastLED`: LED strip control
- `WiFi`: ESP32 network connectivity (WiFi version only)
- `HTTPClient`: Web API requests (WiFi version only)
- `ArduinoJson`: JSON parsing (WiFi version only)

### Node.js Dependencies
- `next`: React framework for web interface
- `react/react-dom`: UI components
- `typescript`: Type checking support