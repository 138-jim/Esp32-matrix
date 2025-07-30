#!/usr/bin/env python3
"""
Enhanced ESP32 Controller for Multi-Panel LED Matrix
Supports dynamic panel configuration and variable frame sizes
"""

import serial
import time
import sys
from typing import Optional, Tuple
import numpy as np


class MultiPanelESP32Controller:
    """Enhanced ESP32 controller supporting dynamic multi-panel configurations"""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        
        # Configuration tracking
        self.configured_width = 0
        self.configured_height = 0
        self.configured_leds = 0
        self.is_configured = False
        
        # Auto-detect port on Windows
        if sys.platform.startswith('win') and port == '/dev/ttyUSB0':
            self.port = 'COM3'
    
    def connect(self) -> bool:
        """Connect to ESP32 with enhanced error handling"""
        try:
            print(f"Attempting to connect to ESP32 on {self.port}...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for ESP32 to initialize
            time.sleep(2)
            
            # Clear any pending data
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            # Test communication
            if self._send_command("INFO"):
                self.connected = True
                print("✓ Connected to ESP32 Multi-Panel Controller")
                
                # Get current status
                self._get_status()
                return True
            else:
                print("✗ Failed to communicate with ESP32")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.serial_connection:
            try:
                self.serial_connection.close()
                print("Disconnected from ESP32")
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.serial_connection = None
                self.connected = False
                self.is_configured = False
    
    def configure_display(self, total_width: int, total_height: int) -> bool:
        """Configure the ESP32 for a specific total display size"""
        if not self.connected:
            print("Error: Not connected to ESP32")
            return False
        
        total_leds = total_width * total_height
        
        # Check reasonable limits
        if total_leds > 2048:
            print(f"Error: Too many LEDs ({total_leds}). Maximum supported: 2048")
            return False
        
        print(f"Configuring ESP32 for {total_width}x{total_height} display ({total_leds} LEDs)...")
        
        if self._send_command(f"CONFIG:{total_width},{total_height}"):
            self.configured_width = total_width
            self.configured_height = total_height
            self.configured_leds = total_leds
            self.is_configured = True
            print(f"✓ ESP32 configured for {total_width}x{total_height} display")
            return True
        else:
            print("✗ Failed to configure ESP32")
            return False
    
    def send_frame(self, frame_data: np.ndarray) -> bool:
        """Send a frame to the ESP32 with the new protocol"""
        if not self.connected:
            print("Error: Not connected to ESP32")
            return False
        
        if not self.is_configured:
            print("Error: ESP32 not configured. Call configure_display() first.")
            return False
        
        # Validate frame dimensions
        expected_shape = (self.configured_height, self.configured_width, 3)
        if frame_data.shape != expected_shape:
            print(f"Error: Frame shape {frame_data.shape} doesn't match configured {expected_shape}")
            return False
        
        # Convert to bytes
        frame_bytes = frame_data.flatten().astype(np.uint8).tobytes()
        frame_size = len(frame_bytes)
        
        # Prepare command
        command = f"FRAME:{frame_size}:"
        command_bytes = command.encode('ascii') + frame_bytes + b":END"
        
        try:
            self.serial_connection.write(command_bytes)
            self.serial_connection.flush()
            
            # Wait for response
            response = self._read_response()
            
            if response == "FRAME_OK":
                return True
            else:
                print(f"Frame send failed: {response}")
                return False
                
        except Exception as e:
            print(f"Error sending frame: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness (0-255)"""
        if not self.connected:
            return False
        
        if not (0 <= brightness <= 255):
            print("Error: Brightness must be 0-255")
            return False
        
        return self._send_command(f"BRIGHTNESS:{brightness}")
    
    def clear_display(self) -> bool:
        """Clear the display"""
        if not self.connected:
            return False
        
        return self._send_command("CLEAR")
    
    def get_status(self) -> dict:
        """Get ESP32 status information"""
        if not self.connected:
            return {}
        
        try:
            self.serial_connection.write(b"STATUS\n")
            self.serial_connection.flush()
            
            response = self._read_response()
            if response.startswith("STATUS:"):
                # Parse status response
                status_parts = response[7:].strip().split()
                status = {}
                
                for part in status_parts:
                    if 'x' in part and 'LEDs:' not in part:
                        # Dimensions
                        dims = part.split('x')
                        if len(dims) == 2:
                            status['width'] = int(dims[0])
                            status['height'] = int(dims[1])
                    elif part.startswith('LEDs:'):
                        status['leds'] = int(part[5:])
                    elif part.startswith('Brightness:'):
                        status['brightness'] = int(part[11:])
                    elif part.startswith('Memory:'):
                        status['free_memory'] = int(part[7:])
                
                return status
                
        except Exception as e:
            print(f"Error getting status: {e}")
        
        return {}
    
    def _get_status(self):
        """Get and display current status"""
        status = self.get_status()
        if status:
            print(f"ESP32 Status: {status.get('width', '?')}x{status.get('height', '?')} "
                  f"LEDs:{status.get('leds', '?')} Brightness:{status.get('brightness', '?')} "
                  f"Memory:{status.get('free_memory', '?')} bytes")
    
    def _send_command(self, command: str) -> bool:
        """Send a command and wait for response"""
        if not self.connected or not self.serial_connection:
            return False
        
        try:
            # Send command
            self.serial_connection.write(f"{command}\n".encode())
            self.serial_connection.flush()
            
            # Wait for response
            response = self._read_response()
            
            # Check for success responses
            success_responses = [
                "CONFIG_OK", "FRAME_OK", "BRIGHTNESS_OK", "CLEAR_OK", "INFO"
            ]
            
            return any(response.startswith(success) for success in success_responses)
            
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return False
    
    def _read_response(self, timeout: float = None) -> str:
        """Read response from ESP32"""
        if timeout is None:
            timeout = self.timeout
        
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting > 0:
                try:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        return line
                except Exception as e:
                    print(f"Error reading response: {e}")
                    break
            time.sleep(0.01)
        
        return "TIMEOUT"
    
    def test_patterns(self):
        """Send test patterns to verify functionality"""
        if not self.is_configured:
            print("Error: ESP32 not configured")
            return
        
        print("Testing with solid colors...")
        
        # Test solid colors
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        color_names = ["Red", "Green", "Blue", "White"]
        
        for color, name in zip(colors, color_names):
            print(f"  Testing {name}...")
            frame = np.full((self.configured_height, self.configured_width, 3), color, dtype=np.uint8)
            
            if self.send_frame(frame):
                print(f"  ✓ {name} sent successfully")
            else:
                print(f"  ✗ {name} failed")
            
            time.sleep(1)
        
        # Clear display
        print("  Clearing display...")
        self.clear_display()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class MultiPanelFrameGenerator:
    """Generate frames for multi-panel displays"""
    
    def __init__(self, total_width: int, total_height: int):
        self.total_width = total_width
        self.total_height = total_height
        self.frame = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    
    def clear(self):
        """Clear the frame"""
        self.frame.fill(0)
    
    def fill(self, r: int, g: int, b: int):
        """Fill frame with solid color"""
        self.frame[:, :] = [r, g, b]
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set a single pixel"""
        if 0 <= x < self.total_width and 0 <= y < self.total_height:
            self.frame[y, x] = [r, g, b]
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Draw text using 5x7 font"""
        font_5x7 = self._get_font_5x7()
        current_x = x
        
        for char in text:
            if char in font_5x7:
                char_data = font_5x7[char]
                for col in range(5):
                    for row in range(7):
                        if char_data[col] & (1 << row):
                            self.set_pixel(current_x + col, y + row, *color)
                current_x += 6
    
    def get_frame(self) -> np.ndarray:
        """Get the current frame"""
        return self.frame.copy()
    
    def _get_font_5x7(self) -> dict:
        """Basic 5x7 font"""
        return {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x41, 0x3E],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x41, 0x51, 0x73],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x1C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x26, 0x49, 0x49, 0x49, 0x32],
            'T': [0x03, 0x01, 0x7F, 0x01, 0x03],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x59, 0x49, 0x4D, 0x43],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x72, 0x49, 0x49, 0x49, 0x46],
            '3': [0x21, 0x41, 0x49, 0x4D, 0x33],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x31],
            '7': [0x41, 0x21, 0x11, 0x09, 0x07],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x46, 0x49, 0x49, 0x29, 0x1E],
        }


def main():
    """Test the multi-panel ESP32 controller"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Panel ESP32 Controller Test")
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('--width', type=int, default=32, help='Total display width')
    parser.add_argument('--height', type=int, default=16, help='Total display height')
    args = parser.parse_args()
    
    print("Multi-Panel ESP32 Controller Test")
    print("=" * 40)
    
    # Connect to ESP32
    with MultiPanelESP32Controller(port=args.port) as controller:
        if not controller.connect():
            print("Failed to connect to ESP32")
            return
        
        # Configure for multi-panel display
        if not controller.configure_display(args.width, args.height):
            print("Failed to configure ESP32")
            return
        
        # Run test patterns
        controller.test_patterns()
        
        # Test text rendering
        print("Testing text rendering...")
        frame_gen = MultiPanelFrameGenerator(args.width, args.height)
        frame_gen.clear()
        frame_gen.draw_text("MULTI-PANEL", 0, 4, (255, 0, 0))
        
        if controller.send_frame(frame_gen.get_frame()):
            print("✓ Text frame sent successfully")
        else:
            print("✗ Text frame failed")
        
        time.sleep(3)
        controller.clear_display()
        
        print("Test complete!")


if __name__ == "__main__":
    main()