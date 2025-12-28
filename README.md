# LED Display Driver

Raspberry Pi GPIO-based driver for 4x 16x16 WS2812B LED panels with web-based configuration interface.

## Features

- **Direct GPIO Control**: No ESP32 required - Raspberry Pi controls LEDs directly via rpi-ws281x
- **Web Interface**: Configure panel positions and rotations via browser
- **Hot-Reload**: Apply configuration changes without restart
- **Multi-Protocol Input**: Receive frames via HTTP POST, WebSocket, UDP, or named pipe
- **Test Patterns**: Built-in patterns for alignment and testing
- **Real-time Stats**: FPS, queue size, and system status monitoring

## Quick Start

### Installation

```bash
# Clone repository
cd /home/jim/Esp32-matrix

# Run setup script
sudo ./setup_rpi_driver.sh

# Logout and login for GPIO permissions
```

### Running the Driver

**Option 1: Direct Run**
```bash
# Run with hardware
sudo python3 -m rpi_driver.main --config configs/current.json

# Run in mock mode (testing without hardware)
python3 -m rpi_driver.main --mock
```

**Option 2: Install as Service**
```bash
# Install systemd service (runs on boot)
sudo ./install_service.sh

# View logs
sudo journalctl -u led-driver.service -f
```

### Web Interface

The web interface is accessible over LAN. Open in your browser:
- From the Pi itself: `http://localhost:8080`
- From any device on your LAN: `http://192.168.1.15:8080` (replace with your Pi's IP)
- Or use hostname: `http://raspberrypi.local:8080`

## Usage

### Sending Frames from External Programs

**Python Example:**
```python
import numpy as np
import requests

# Create 32x32 frame (for 2x2 grid of 16x16 panels)
frame = np.zeros((32, 32, 3), dtype=np.uint8)
frame[10:20, 10:20] = [255, 0, 0]  # Red square

# Send to display
requests.post(
    'http://raspberrypi.local:8080/api/frame',
    data=frame.tobytes(),
    headers={'Content-Type': 'application/octet-stream'}
)
```

**UDP Example:**
```python
import socket
import struct
import numpy as np

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Create frame
frame = np.zeros((32, 32, 3), dtype=np.uint8)

# Build packet: magic + width + height + data
header = struct.pack('>4sHH', b'LEDF', 32, 32)
packet = header + frame.tobytes()

# Send to display
sock.sendto(packet, ('raspberrypi.local', 5555))
```

### Configuration

Edit `configs/current.json` to configure your panel layout:

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

Or use the web interface to adjust panel positions and rotations visually.

## Hardware Setup

### GPIO Connection
- **GPIO 18 (Pin 12)**: Data line to first LED panel
- **GND**: Common ground between Pi and LED power supply
- **External 5V PSU**: Power LED strips (do NOT power from Pi)

### Panel Wiring
Connect panels in daisy-chain order matching the `id` in configuration:
```
Raspberry Pi GPIO 18 → Panel 0 DIN
Panel 0 DOUT → Panel 1 DIN
Panel 1 DOUT → Panel 2 DIN
Panel 2 DOUT → Panel 3 DIN
```

## API Reference

### REST Endpoints

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/panels` - List all panels
- `PUT /api/panels/{id}` - Update single panel
- `POST /api/frame` - Submit frame (binary RGB data)
- `POST /api/brightness` - Set brightness (0-255)
- `POST /api/test-pattern` - Display test pattern
- `GET /api/status` - System status
- `GET /api/patterns` - List available test patterns

### WebSocket Endpoints

- `WS /ws/frames` - Stream frames (binary)
- `WS /ws/preview` - Live preview feed

## Troubleshooting

**"Permission denied" errors:**
```bash
# Run with sudo or add user to gpio group
sudo usermod -a -G gpio $USER
# Then logout and login
```

**"Failed to create mailbox device":**
```bash
# Disable onboard audio (conflicts with PWM)
echo "dtparam=audio=off" | sudo tee -a /boot/config.txt
sudo reboot
```

**LEDs show wrong colors:**
- Check LED strip type in `led_driver.py` (GRB vs RGB)
- Default is GRB for WS2812B

**Panels in wrong position:**
- Use test patterns (corners, grid) to identify panel order
- Adjust `position` and `rotation` in web interface

## Development

### File Structure
```
rpi_driver/            - Main driver code
├── main.py           - Entry point
├── led_driver.py     - rpi-ws281x wrapper
├── coordinate_mapper.py - Coordinate transformations
├── display_controller.py - Main display loop
├── frame_receiver.py - Multi-protocol input
├── web_api.py        - FastAPI server
├── config_manager.py - Configuration management
└── test_patterns.py  - Built-in test patterns

static/               - Web UI
├── index.html
└── app.js

configs/              - Panel configurations
└── current.json      - Active configuration
```

### Mock Mode

Test without hardware:
```bash
python3 -m rpi_driver.main --mock --verbose
```

All functionality works except physical LED control.

## License

See LICENSE file for details.
