#!/usr/bin/env python3
"""
Multi-Panel LED Matrix Controller with GUI
Complete system for managing multiple LED matrix panels with rotation, configuration, and display modes
"""

import serial
import time
import math
import threading
import colorsys
import sys
import json
import os
from typing import Tuple, List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue


class LEDMatrix:
    def __init__(self, width: int = 16, height: int = 16):
        self.width = width
        self.height = height
        self.buffer = np.zeros((height, width, 3), dtype=np.uint8)
    
    def clear(self):
        """Clear the matrix buffer"""
        self.buffer.fill(0)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set a single pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = [r, g, b]
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get a single pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.buffer[y, x])
        return (0, 0, 0)
    
    def fill(self, r: int, g: int, b: int):
        """Fill entire matrix with color"""
        self.buffer[:, :] = [r, g, b]
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Draw text using built-in 5x7 font"""
        font_5x7 = self._get_font_5x7()
        current_x = x
        
        for char in text:
            if char in font_5x7:
                char_data = font_5x7[char]
                for col in range(5):
                    for row in range(7):
                        if char_data[col] & (1 << row):
                            self.set_pixel(current_x + col, y + row, *color)
                current_x += 6  # 5 pixels + 1 spacing
    
    def get_text_width(self, text: str) -> int:
        """Get text width in pixels"""
        return len(text) * 6 - 1
    
    def copy_region(self, source_matrix: 'LEDMatrix', src_x: int, src_y: int, dst_x: int, dst_y: int, w: int, h: int):
        """Copy a region from another matrix to this one"""
        for y in range(h):
            for x in range(w):
                if (src_x + x < source_matrix.width and src_y + y < source_matrix.height and
                    dst_x + x < self.width and dst_y + y < self.height):
                    r, g, b = source_matrix.get_pixel(src_x + x, src_y + y)
                    self.set_pixel(dst_x + x, dst_y + y, r, g, b)
    
    def rotate_90_cw(self) -> 'LEDMatrix':
        """Return a new matrix rotated 90 degrees clockwise"""
        rotated = LEDMatrix(self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.get_pixel(x, y)
                rotated.set_pixel(self.height - 1 - y, x, r, g, b)
        return rotated
    
    def rotate_180(self) -> 'LEDMatrix':
        """Return a new matrix rotated 180 degrees"""
        rotated = LEDMatrix(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.get_pixel(x, y)
                rotated.set_pixel(self.width - 1 - x, self.height - 1 - y, r, g, b)
        return rotated
    
    def rotate_270_cw(self) -> 'LEDMatrix':
        """Return a new matrix rotated 270 degrees clockwise"""
        rotated = LEDMatrix(self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.get_pixel(x, y)
                rotated.set_pixel(y, self.width - 1 - x, r, g, b)
        return rotated
    
    def _get_font_5x7(self) -> dict:
        """5x7 font definition"""
        return {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            '"': [0x00, 0x07, 0x00, 0x07, 0x00],
            '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
            '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
            '%': [0x23, 0x13, 0x08, 0x64, 0x62],
            '&': [0x36, 0x49, 0x56, 0x20, 0x50],
            "'": [0x00, 0x08, 0x07, 0x03, 0x00],
            '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
            ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
            '*': [0x2A, 0x1C, 0x7F, 0x1C, 0x2A],
            '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
            ',': [0x00, 0x80, 0x70, 0x30, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '.': [0x00, 0x00, 0x60, 0x60, 0x00],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
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
            ':': [0x00, 0x00, 0x14, 0x00, 0x00],
            ';': [0x00, 0x40, 0x34, 0x00, 0x00],
            '<': [0x00, 0x08, 0x14, 0x22, 0x41],
            '=': [0x14, 0x14, 0x14, 0x14, 0x14],
            '>': [0x00, 0x41, 0x22, 0x14, 0x08],
            '?': [0x02, 0x01, 0x59, 0x09, 0x06],
            '@': [0x3E, 0x41, 0x5D, 0x59, 0x4E],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
        }


class Panel:
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0, rotation: int = 0):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.rotation = rotation  # 0, 90, 180, 270 degrees
        self.matrix = LEDMatrix(width, height)
    
    def get_rotated_dimensions(self) -> Tuple[int, int]:
        """Get dimensions after rotation"""
        if self.rotation in [90, 270]:
            return (self.height, self.width)
        return (self.width, self.height)
    
    def get_rotated_matrix(self) -> LEDMatrix:
        """Get the matrix with rotation applied"""
        if self.rotation == 0:
            return self.matrix
        elif self.rotation == 90:
            return self.matrix.rotate_90_cw()
        elif self.rotation == 180:
            return self.matrix.rotate_180()
        elif self.rotation == 270:
            return self.matrix.rotate_270_cw()
        else:
            return self.matrix


class PatternGenerator:
    @staticmethod
    def rainbow(matrix: LEDMatrix, offset: float = 0):
        """Generate rainbow pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                hue = (x + y + offset) / (matrix.width + matrix.height)
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
                matrix.set_pixel(x, y, int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def spiral(matrix: LEDMatrix, offset: float = 0):
        """Generate spiral pattern"""
        center_x, center_y = matrix.width // 2, matrix.height // 2
        for y in range(matrix.height):
            for x in range(matrix.width):
                dx, dy = x - center_x, y - center_y
                angle = math.atan2(dy, dx) + offset
                distance = math.sqrt(dx*dx + dy*dy)
                hue = (angle + distance * 0.1) / (2 * math.pi)
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
                matrix.set_pixel(x, y, int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def wave(matrix: LEDMatrix, offset: float = 0):
        """Generate wave pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                wave1 = math.sin((x + offset) * 0.5) * 0.5 + 0.5
                wave2 = math.sin((y + offset) * 0.3) * 0.5 + 0.5
                intensity = (wave1 + wave2) / 2
                matrix.set_pixel(x, y, int(intensity * 255), int(intensity * 128), int(intensity * 64))

    @staticmethod
    def checkerboard(matrix: LEDMatrix, offset: float = 0):
        """Generate animated checkerboard pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                if ((x + int(offset)) + y) % 2 == 0:
                    matrix.set_pixel(x, y, 255, 0, 0)
                else:
                    matrix.set_pixel(x, y, 0, 0, 255)

    @staticmethod
    def fire(matrix: LEDMatrix, offset: float = 0):
        """Generate fire pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                # Create fire effect with noise-like pattern
                flame_height = (matrix.height - y) / matrix.height
                noise = (math.sin(x * 0.3 + offset) + math.sin(y * 0.2 + offset * 1.5)) * 0.5
                intensity = flame_height + noise * 0.3
                intensity = max(0, min(1, intensity))
                
                r = int(intensity * 255)
                g = int(intensity * intensity * 200)
                b = int(intensity * intensity * intensity * 50)
                matrix.set_pixel(x, y, r, g, b)


class MultiPanelSystem:
    def __init__(self):
        self.panels: List[Panel] = []
        self.combined_matrix: Optional[LEDMatrix] = None
        self.total_width = 0
        self.total_height = 0
    
    def add_panel(self, width: int, height: int, x: int = 0, y: int = 0, rotation: int = 0) -> Panel:
        """Add a new panel to the system"""
        panel = Panel(width, height, x, y, rotation)
        self.panels.append(panel)
        self._update_combined_matrix()
        return panel
    
    def remove_panel(self, panel: Panel):
        """Remove a panel from the system"""
        if panel in self.panels:
            self.panels.remove(panel)
            self._update_combined_matrix()
    
    def clear_panels(self):
        """Remove all panels"""
        self.panels.clear()
        self._update_combined_matrix()
    
    def _update_combined_matrix(self):
        """Update the combined matrix dimensions"""
        if not self.panels:
            self.total_width = 0
            self.total_height = 0
            self.combined_matrix = None
            return
        
        # Calculate total dimensions
        max_right = 0
        max_bottom = 0
        
        for panel in self.panels:
            rotated_width, rotated_height = panel.get_rotated_dimensions()
            max_right = max(max_right, panel.x + rotated_width)
            max_bottom = max(max_bottom, panel.y + rotated_height)
        
        self.total_width = max_right
        self.total_height = max_bottom
        self.combined_matrix = LEDMatrix(self.total_width, self.total_height)
    
    def render_combined_frame(self) -> Optional[LEDMatrix]:
        """Render all panels into a single combined frame"""
        if not self.combined_matrix:
            return None
        
        self.combined_matrix.clear()
        
        for panel in self.panels:
            rotated_matrix = panel.get_rotated_matrix()
            # Copy the rotated panel content to the combined matrix
            for y in range(rotated_matrix.height):
                for x in range(rotated_matrix.width):
                    if (panel.x + x < self.total_width and panel.y + y < self.total_height):
                        r, g, b = rotated_matrix.get_pixel(x, y)
                        self.combined_matrix.set_pixel(panel.x + x, panel.y + y, r, g, b)
        
        return self.combined_matrix
    
    def apply_pattern_to_all(self, pattern_func, offset: float = 0):
        """Apply a pattern to all panels"""
        for panel in self.panels:
            pattern_func(panel.matrix, offset)
    
    def apply_text_to_combined(self, text: str, color: Tuple[int, int, int], scroll_offset: int = 0):
        """Apply scrolling text across the combined display"""
        if not self.combined_matrix:
            return
        
        temp_matrix = LEDMatrix(self.total_width, self.total_height)
        text_width = temp_matrix.get_text_width(text)
        
        # Draw text with scroll offset
        temp_matrix.draw_text(text, scroll_offset, 0, color)
        
        # Distribute to panels
        for panel in self.panels:
            panel.matrix.clear()
            rotated_width, rotated_height = panel.get_rotated_dimensions()
            
            # Copy the relevant section to this panel
            for y in range(min(rotated_height, temp_matrix.height - panel.y)):
                for x in range(min(rotated_width, temp_matrix.width - panel.x)):
                    if panel.x + x < temp_matrix.width and panel.y + y < temp_matrix.height:
                        r, g, b = temp_matrix.get_pixel(panel.x + x, panel.y + y)
                        panel.matrix.set_pixel(x, y, r, g, b)
    
    def save_configuration(self, filename: str):
        """Save panel configuration to JSON file"""
        config = {
            "panels": [
                {
                    "width": panel.width,
                    "height": panel.height,
                    "x": panel.x,
                    "y": panel.y,
                    "rotation": panel.rotation
                }
                for panel in self.panels
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_configuration(self, filename: str):
        """Load panel configuration from JSON file"""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        self.clear_panels()
        
        for panel_config in config["panels"]:
            self.add_panel(
                width=panel_config["width"],
                height=panel_config["height"],
                x=panel_config["x"],
                y=panel_config["y"],
                rotation=panel_config["rotation"]
            )


class ESP32MultiPanelController:
    """ESP32 controller with multi-panel support using the enhanced protocol"""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, mock_mode: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        self.mock_mode = mock_mode
        self.mock_display = None
        self.current_width = 32
        self.current_height = 32
    
    def connect(self) -> bool:
        """Connect to ESP32 (real or mock)"""
        if self.mock_mode:
            return self._connect_mock()
        
        try:
            print(f"Attempting to connect to {self.port} at {self.baudrate} baud...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2.0,
                write_timeout=2.0
            )
            print(f"Serial connection established")
            
            # Test connection
            time.sleep(2)  # Wait for ESP32 to initialize
            
            # Clear any pending data
            self.serial_connection.reset_input_buffer()
            
            # Send INFO command and read multi-line response
            self.serial_connection.write(b"INFO\n")
            time.sleep(0.5)  # Give ESP32 time to respond
            
            response_lines = []
            start_time = time.time()
            while time.time() - start_time < 3.0:  # 3 second timeout
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        response_lines.append(line)
                        if "ESP32 Multi-Panel" in line:
                            self.connected = True
                            print(f"✓ Connected to ESP32 on {self.port}")
                            print(f"✓ Device: {line}")
                            return True
                else:
                    time.sleep(0.1)
            
            print(f"✗ Invalid or no response from {self.port}")
            if response_lines:
                print(f"Received: {response_lines}")
            return False
                
        except Exception as e:
            print(f"✗ Failed to connect to {self.port}: {e}")
            
            # On Windows, suggest common troubleshooting
            if sys.platform.startswith('win'):
                print("Windows troubleshooting:")
                print("- Check if ESP32 is connected via USB")
                print("- Try different COM ports (COM3, COM4, COM5, etc.)")
                print("- Ensure ESP32 drivers are installed")
                print("- Check Device Manager for the correct COM port")
                print("- Try enabling Mock Mode for testing without hardware")
            
            return False
    
    def _connect_mock(self) -> bool:
        """Connect in mock mode"""
        print("✓ Connected in mock mode")
        self.connected = True
        return True
    
    def configure_display(self, width: int, height: int) -> bool:
        """Configure the display dimensions using the CONFIG command"""
        if not self.connected:
            return False
        
        if self.mock_mode:
            print(f"Mock: Configure display to {width}x{height}")
            self.current_width = width
            self.current_height = height
            return True
        
        try:
            command = f"CONFIG:{width},{height}"
            
            # Clear input buffer and send command
            self.serial_connection.reset_input_buffer()
            self.serial_connection.write(f"{command}\n".encode())
            
            # Read multiple lines looking for CONFIG_OK
            start_time = time.time()
            response_lines = []
            config_ok = False
            
            while time.time() - start_time < 5.0:  # 5 second timeout for config
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        response_lines.append(line)
                        print(f"ESP32: {line}")  # Debug output
                        
                        if "CONFIG_OK" in line:
                            config_ok = True
                            break
                        elif "CONFIG_ERROR" in line or "ERROR" in line:
                            print(f"✗ Configuration error: {line}")
                            return False
                else:
                    time.sleep(0.1)
            
            if config_ok:
                self.current_width = width
                self.current_height = height
                print(f"✓ Display configured: {width}x{height}")
                return True
            else:
                print(f"✗ Configuration timeout or failed")
                if response_lines:
                    print(f"Received responses: {response_lines}")
                return False
                
        except Exception as e:
            print(f"Error configuring display: {e}")
            return False
    
    def send_frame(self, matrix: LEDMatrix) -> bool:
        """Send frame data using the FRAME command with size parameter"""
        if not self.connected:
            return False
        
        if self.mock_mode:
            print("Mock: Frame sent")
            return True
        
        try:
            # Convert matrix to RGB bytes
            rgb_data = bytearray()
            for y in range(matrix.height):
                for x in range(matrix.width):
                    r, g, b = matrix.get_pixel(x, y)
                    rgb_data.extend([r, g, b])
            
            data_size = len(rgb_data)
            
            # Send frame command with size: FRAME:size:<data>:END
            command_start = f"FRAME:{data_size}:"
            command_end = ":END"
            
            # Send as bytes
            full_command = command_start.encode() + rgb_data + command_end.encode()
            self.serial_connection.write(full_command)
            
            # Wait for FRAME_OK response with timeout
            start_time = time.time()
            while time.time() - start_time < 3.0:  # 3 second timeout
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if response == "FRAME_OK":
                        return True
                    elif "FRAME_ERROR" in response or "ERROR" in response:
                        print(f"Frame error: {response}")
                        return False
                time.sleep(0.01)
            
            print("Frame timeout - no response from ESP32")
            return False
            
        except Exception as e:
            print(f"Error sending frame: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness (0-255)"""
        if not self.connected:
            return False
        
        if self.mock_mode:
            print(f"Mock: Brightness set to {brightness}")
            return True
        
        try:
            command = f"BRIGHTNESS:{brightness}"
            response = self._send_command(command)
            return response == "BRIGHTNESS_OK"
        except Exception as e:
            print(f"Error setting brightness: {e}")
            return False
    
    def clear_display(self) -> bool:
        """Clear display"""
        if not self.connected:
            return False
        
        if self.mock_mode:
            print("Mock: Display cleared")
            return True
        
        try:
            response = self._send_command("CLEAR")
            return response == "CLEAR_OK"
        except Exception as e:
            print(f"Error clearing display: {e}")
            return False
    
    def get_status(self) -> Optional[str]:
        """Get ESP32 status"""
        if not self.connected:
            return None
        
        if self.mock_mode:
            return f"STATUS: {self.current_width}x{self.current_height} LEDs:{self.current_width*self.current_height} Brightness:128 Memory:200000"
        
        try:
            # STATUS command returns a single line response
            return self._send_command("STATUS", timeout=3.0)
        except Exception as e:
            print(f"Error getting status: {e}")
            return None
    
    def _send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send command and wait for response"""
        if not self.connected or not self.serial_connection:
            return None
        
        try:
            # Clear input buffer
            self.serial_connection.reset_input_buffer()
            
            # Send command
            self.serial_connection.write(f"{command}\n".encode())
            
            # Wait for response with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if response:  # Return first non-empty line
                        return response
                time.sleep(0.01)
            
            return None  # Timeout
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return None
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        self.connected = False


class MockGUIDisplay:
    """GUI mock display for testing"""
    
    def __init__(self, width: int = 32, height: int = 32, pixel_size: int = 10):
        self.width = width
        self.height = height
        self.pixel_size = pixel_size
        
        self.window = tk.Toplevel()
        self.window.title("LED Matrix Mock Display")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        canvas_width = width * pixel_size
        canvas_height = height * pixel_size
        
        self.canvas = tk.Canvas(
            self.window,
            width=canvas_width,
            height=canvas_height,
            bg='black'
        )
        self.canvas.pack()
        
        # Store rectangles for each pixel
        self.pixels = {}
        for y in range(height):
            for x in range(width):
                x1 = x * pixel_size
                y1 = y * pixel_size
                x2 = x1 + pixel_size
                y2 = y1 + pixel_size
                
                rect_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill='black',
                    outline='gray',
                    width=1
                )
                self.pixels[(x, y)] = rect_id
        
        self.closed = False
    
    def update_display(self, matrix: LEDMatrix):
        """Update the display with matrix data"""
        if self.closed:
            return
        
        try:
            for y in range(min(self.height, matrix.height)):
                for x in range(min(self.width, matrix.width)):
                    r, g, b = matrix.get_pixel(x, y)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    if (x, y) in self.pixels:
                        self.canvas.itemconfig(self.pixels[(x, y)], fill=color)
            
            self.window.update()
        except tk.TclError:
            self.closed = True
    
    def _on_close(self):
        """Handle window close"""
        self.closed = True
        self.window.destroy()


class MultiPanelControllerGUI:
    """Main GUI application for multi-panel LED controller"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Panel LED Matrix Controller")
        self.root.geometry("1200x800")
        
        # System components
        self.panel_system = MultiPanelSystem()
        self.controller = ESP32MultiPanelController(mock_mode=True)  # Start in mock mode
        self.mock_display = None
        
        # Animation state
        self.current_mode = "text"
        self.current_text = "HELLO WORLD!"
        self.current_color = (255, 0, 0)
        self.current_pattern = "rainbow"
        self.scroll_position = 0
        self.pattern_offset = 0
        self.brightness = 128
        
        # Animation thread
        self.animation_thread = None
        self.animation_running = False
        
        self.setup_gui()
        self.setup_default_panels()
        self.start_animation()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Right panel - Panel configuration
        config_frame = ttk.LabelFrame(main_frame, text="Panel Configuration")
        config_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_control_panel(control_frame)
        self.setup_config_panel(config_frame)
    
    def setup_control_panel(self, parent):
        """Setup the control panel"""
        # Connection controls
        conn_frame = ttk.LabelFrame(parent, text="Connection")
        conn_frame.pack(fill=tk.X, pady=5)
        
        self.port_var = tk.StringVar(value="/dev/ttyUSB0")
        ttk.Label(conn_frame, text="Port:").pack()
        ttk.Entry(conn_frame, textvariable=self.port_var).pack(fill=tk.X, padx=5)
        
        self.mock_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(conn_frame, text="Mock Mode", variable=self.mock_mode_var).pack()
        
        ttk.Button(conn_frame, text="Connect", command=self.connect_esp32).pack(pady=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_esp32).pack()
        
        # Display mode controls
        mode_frame = ttk.LabelFrame(parent, text="Display Mode")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(mode_frame, text="Scrolling Text", variable=self.mode_var, 
                       value="text", command=self.change_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Pattern", variable=self.mode_var, 
                       value="pattern", command=self.change_mode).pack(anchor=tk.W)
        
        # Text controls
        text_frame = ttk.LabelFrame(parent, text="Text Settings")
        text_frame.pack(fill=tk.X, pady=5)
        
        self.text_var = tk.StringVar(value=self.current_text)
        ttk.Label(text_frame, text="Text:").pack()
        ttk.Entry(text_frame, textvariable=self.text_var).pack(fill=tk.X, padx=5)
        ttk.Button(text_frame, text="Update Text", command=self.update_text).pack(pady=2)
        
        # Color controls
        color_frame = ttk.Frame(text_frame)
        color_frame.pack(fill=tk.X, pady=2)
        
        self.r_var = tk.IntVar(value=self.current_color[0])
        self.g_var = tk.IntVar(value=self.current_color[1])
        self.b_var = tk.IntVar(value=self.current_color[2])
        
        ttk.Label(color_frame, text="R:").grid(row=0, column=0)
        ttk.Scale(color_frame, from_=0, to=255, variable=self.r_var, 
                 orient=tk.HORIZONTAL, command=self.update_color).grid(row=0, column=1)
        
        ttk.Label(color_frame, text="G:").grid(row=1, column=0)
        ttk.Scale(color_frame, from_=0, to=255, variable=self.g_var, 
                 orient=tk.HORIZONTAL, command=self.update_color).grid(row=1, column=1)
        
        ttk.Label(color_frame, text="B:").grid(row=2, column=0)
        ttk.Scale(color_frame, from_=0, to=255, variable=self.b_var, 
                 orient=tk.HORIZONTAL, command=self.update_color).grid(row=2, column=1)
        
        # Pattern controls
        pattern_frame = ttk.LabelFrame(parent, text="Pattern Settings")
        pattern_frame.pack(fill=tk.X, pady=5)
        
        self.pattern_var = tk.StringVar(value=self.current_pattern)
        patterns = ["rainbow", "spiral", "wave", "checkerboard", "fire"]
        ttk.Label(pattern_frame, text="Pattern:").pack()
        ttk.Combobox(pattern_frame, textvariable=self.pattern_var, values=patterns).pack(fill=tk.X, padx=5)
        ttk.Button(pattern_frame, text="Apply Pattern", command=self.update_pattern).pack(pady=2)
        
        # Brightness control
        bright_frame = ttk.LabelFrame(parent, text="Brightness")
        bright_frame.pack(fill=tk.X, pady=5)
        
        self.brightness_var = tk.IntVar(value=self.brightness)
        ttk.Scale(bright_frame, from_=0, to=255, variable=self.brightness_var, 
                 orient=tk.HORIZONTAL, command=self.update_brightness).pack(fill=tk.X, padx=5)
        
        # Quick actions
        action_frame = ttk.LabelFrame(parent, text="Quick Actions")
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Clear Display", command=self.clear_display).pack(pady=2)
        ttk.Button(action_frame, text="Show Mock Display", command=self.show_mock_display).pack(pady=2)
        ttk.Button(action_frame, text="Get Status", command=self.show_status).pack(pady=2)
    
    def setup_config_panel(self, parent):
        """Setup the panel configuration area"""
        # Panel list
        list_frame = ttk.LabelFrame(parent, text="Panels")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview for panel list
        columns = ("Width", "Height", "X", "Y", "Rotation")
        self.panel_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        self.panel_tree.heading("#0", text="Panel")
        for col in columns:
            self.panel_tree.heading(col, text=col)
            self.panel_tree.column(col, width=70)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.panel_tree.yview)
        self.panel_tree.configure(yscrollcommand=scrollbar.set)
        
        self.panel_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Panel controls
        panel_controls = ttk.Frame(parent)
        panel_controls.pack(fill=tk.X, pady=5)
        
        # Add panel controls
        add_frame = ttk.LabelFrame(panel_controls, text="Add Panel")
        add_frame.pack(fill=tk.X, pady=2)
        
        add_inputs = ttk.Frame(add_frame)
        add_inputs.pack(fill=tk.X, padx=5, pady=5)
        
        self.panel_width_var = tk.IntVar(value=32)
        self.panel_height_var = tk.IntVar(value=32)
        self.panel_x_var = tk.IntVar(value=0)
        self.panel_y_var = tk.IntVar(value=0)
        self.panel_rotation_var = tk.IntVar(value=0)
        
        ttk.Label(add_inputs, text="W:").grid(row=0, column=0)
        ttk.Entry(add_inputs, textvariable=self.panel_width_var, width=5).grid(row=0, column=1)
        
        ttk.Label(add_inputs, text="H:").grid(row=0, column=2)
        ttk.Entry(add_inputs, textvariable=self.panel_height_var, width=5).grid(row=0, column=3)
        
        ttk.Label(add_inputs, text="X:").grid(row=1, column=0)
        ttk.Entry(add_inputs, textvariable=self.panel_x_var, width=5).grid(row=1, column=1)
        
        ttk.Label(add_inputs, text="Y:").grid(row=1, column=2)
        ttk.Entry(add_inputs, textvariable=self.panel_y_var, width=5).grid(row=1, column=3)
        
        ttk.Label(add_inputs, text="Rot:").grid(row=2, column=0)
        ttk.Combobox(add_inputs, textvariable=self.panel_rotation_var, 
                    values=[0, 90, 180, 270], width=5).grid(row=2, column=1)
        
        ttk.Button(add_frame, text="Add Panel", command=self.add_panel).pack(pady=5)
        
        # Panel management buttons
        mgmt_frame = ttk.Frame(panel_controls)
        mgmt_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(mgmt_frame, text="Remove Selected", command=self.remove_panel).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Clear All", command=self.clear_panels).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(mgmt_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=2)
        
        # Status display
        self.status_text = tk.Text(parent, height=6)
        self.status_text.pack(fill=tk.X, pady=5)
    
    def setup_default_panels(self):
        """Setup default panel configuration"""
        # Add single 32x32 panel
        self.panel_system.add_panel(32, 32, 0, 0, 0)
        self.update_panel_list()
    
    def update_panel_list(self):
        """Update the panel list display"""
        # Clear existing items
        for item in self.panel_tree.get_children():
            self.panel_tree.delete(item)
        
        # Add panels
        for i, panel in enumerate(self.panel_system.panels):
            self.panel_tree.insert("", "end", text=f"Panel {i+1}", 
                                 values=(panel.width, panel.height, panel.x, panel.y, panel.rotation))
        
        # Update status
        total_panels = len(self.panel_system.panels)
        total_leds = sum(p.width * p.height for p in self.panel_system.panels)
        self.status_text.insert(tk.END, f"Panels: {total_panels}, Total LEDs: {total_leds}, "
                               f"Display: {self.panel_system.total_width}x{self.panel_system.total_height}\n")
        self.status_text.see(tk.END)
    
    def add_panel(self):
        """Add a new panel"""
        try:
            width = self.panel_width_var.get()
            height = self.panel_height_var.get()
            x = self.panel_x_var.get()
            y = self.panel_y_var.get()
            rotation = self.panel_rotation_var.get()
            
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive")
                return
            
            self.panel_system.add_panel(width, height, x, y, rotation)
            self.update_panel_list()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
    
    def remove_panel(self):
        """Remove selected panel"""
        selection = self.panel_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a panel to remove")
            return
        
        # Get panel index from selection
        item = selection[0]
        index = self.panel_tree.index(item)
        
        if 0 <= index < len(self.panel_system.panels):
            panel = self.panel_system.panels[index]
            self.panel_system.remove_panel(panel)
            self.update_panel_list()
    
    def clear_panels(self):
        """Remove all panels"""
        if messagebox.askyesno("Confirm", "Remove all panels?"):
            self.panel_system.clear_panels()
            self.update_panel_list()
    
    def save_config(self):
        """Save panel configuration"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.panel_system.save_configuration(filename)
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load panel configuration"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.panel_system.load_configuration(filename)
                self.update_panel_list()
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def connect_esp32(self):
        """Connect to ESP32"""
        port = self.port_var.get()
        mock_mode = self.mock_mode_var.get()
        
        self.controller = ESP32MultiPanelController(port=port, mock_mode=mock_mode)
        
        if self.controller.connect():
            # Configure display size
            if self.panel_system.combined_matrix:
                success = self.controller.configure_display(
                    self.panel_system.total_width, 
                    self.panel_system.total_height
                )
                if success:
                    self.status_text.insert(tk.END, f"✓ Connected and configured {self.panel_system.total_width}x{self.panel_system.total_height}\n")
                else:
                    self.status_text.insert(tk.END, "✓ Connected but configuration failed\n")
            else:
                self.status_text.insert(tk.END, "✓ Connected (no panels configured)\n")
        else:
            self.status_text.insert(tk.END, "✗ Connection failed\n")
        
        self.status_text.see(tk.END)
    
    def disconnect_esp32(self):
        """Disconnect from ESP32"""
        if self.controller:
            self.controller.disconnect()
            self.status_text.insert(tk.END, "Disconnected\n")
            self.status_text.see(tk.END)
    
    def change_mode(self):
        """Change display mode"""
        self.current_mode = self.mode_var.get()
        self.status_text.insert(tk.END, f"Mode changed to: {self.current_mode}\n")
        self.status_text.see(tk.END)
    
    def update_text(self):
        """Update scrolling text"""
        self.current_text = self.text_var.get()
        self.scroll_position = self.panel_system.total_width  # Reset scroll
        self.status_text.insert(tk.END, f"Text updated: {self.current_text}\n")
        self.status_text.see(tk.END)
    
    def update_color(self, *args):
        """Update text color"""
        self.current_color = (self.r_var.get(), self.g_var.get(), self.b_var.get())
    
    def update_pattern(self):
        """Update current pattern"""
        self.current_pattern = self.pattern_var.get()
        self.status_text.insert(tk.END, f"Pattern updated: {self.current_pattern}\n")
        self.status_text.see(tk.END)
    
    def update_brightness(self, *args):
        """Update brightness"""
        self.brightness = self.brightness_var.get()
        if self.controller:
            self.controller.set_brightness(self.brightness)
    
    def clear_display(self):
        """Clear the display"""
        if self.controller:
            self.controller.clear_display()
        self.status_text.insert(tk.END, "Display cleared\n")
        self.status_text.see(tk.END)
    
    def show_mock_display(self):
        """Show or update mock display window"""
        if not self.panel_system.combined_matrix:
            messagebox.showwarning("Warning", "No panels configured")
            return
        
        if not self.mock_display or self.mock_display.closed:
            self.mock_display = MockGUIDisplay(
                self.panel_system.total_width, 
                self.panel_system.total_height
            )
        
        # Update with current frame
        combined_frame = self.panel_system.render_combined_frame()
        if combined_frame:
            self.mock_display.update_display(combined_frame)
    
    def show_status(self):
        """Show ESP32 status"""
        if self.controller:
            status = self.controller.get_status()
            if status:
                self.status_text.insert(tk.END, f"ESP32 Status: {status}\n")
                self.status_text.see(tk.END)
    
    def start_animation(self):
        """Start the animation thread"""
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
    
    def _animation_loop(self):
        """Main animation loop"""
        last_time = time.time()
        frame_rate = 1/15  # 15 FPS
        
        while self.animation_running:
            current_time = time.time()
            
            if current_time - last_time >= frame_rate:
                try:
                    self._update_frame()
                    last_time = current_time
                except Exception as e:
                    print(f"Animation error: {e}")
            
            time.sleep(0.01)  # Small sleep to prevent excessive CPU usage
    
    def _update_frame(self):
        """Update a single frame"""
        if not self.panel_system.panels:
            return
        
        if self.current_mode == "text":
            # Update scrolling text
            self.panel_system.apply_text_to_combined(
                self.current_text, 
                self.current_color, 
                self.scroll_position
            )
            
            # Update scroll position
            self.scroll_position -= 1
            text_width = LEDMatrix(1, 1).get_text_width(self.current_text)
            if self.scroll_position < -text_width:
                self.scroll_position = self.panel_system.total_width
        
        elif self.current_mode == "pattern":
            # Update pattern
            pattern_funcs = {
                "rainbow": PatternGenerator.rainbow,
                "spiral": PatternGenerator.spiral,
                "wave": PatternGenerator.wave,
                "checkerboard": PatternGenerator.checkerboard,
                "fire": PatternGenerator.fire,
            }
            
            pattern_func = pattern_funcs.get(self.current_pattern, PatternGenerator.rainbow)
            self.panel_system.apply_pattern_to_all(pattern_func, self.pattern_offset)
            
            # Update pattern offset
            self.pattern_offset += 0.1
        
        # Render combined frame
        combined_frame = self.panel_system.render_combined_frame()
        
        # Send to ESP32
        if combined_frame and self.controller and self.controller.connected:
            self.controller.send_frame(combined_frame)
        
        # Update mock display
        if self.mock_display and not self.mock_display.closed and combined_frame:
            self.mock_display.update_display(combined_frame)
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        finally:
            self.animation_running = False
            if self.animation_thread:
                self.animation_thread.join(timeout=1.0)
            if self.controller:
                self.controller.disconnect()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Panel LED Matrix Controller")
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port for ESP32')
    parser.add_argument('--mock', action='store_true', help='Start in mock mode')
    args = parser.parse_args()
    
    print("Multi-Panel LED Matrix Controller with GUI")
    print("=" * 50)
    
    app = MultiPanelControllerGUI()
    
    # Set initial port if specified, with Windows defaults
    if args.port == '/dev/ttyUSB0' and sys.platform.startswith('win'):
        app.port_var.set('COM3')  # Default Windows port
    else:
        app.port_var.set(args.port)
    app.mock_mode_var.set(args.mock)
    
    app.run()


if __name__ == "__main__":
    main()