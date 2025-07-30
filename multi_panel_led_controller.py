#!/usr/bin/env python3
"""
Multi-Panel LED Matrix Controller for Windows Testing
Renders text and patterns across multiple configurable LED matrix panels
"""

import serial
import time
import math
import threading
import colorsys
import sys
from typing import Tuple, List, Optional, Dict
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import queue
import json
import os


class Panel:
    """Represents a single LED matrix panel with rotation and position"""
    
    def __init__(self, panel_id: int, width: int = 16, height: int = 16, 
                 rotation: int = 0, x_offset: int = 0, y_offset: int = 0):
        self.panel_id = panel_id
        self.original_width = width
        self.original_height = height
        self.rotation = rotation % 360
        self.x_offset = x_offset
        self.y_offset = y_offset
        
        # Calculate actual dimensions after rotation
        if self.rotation in [90, 270]:
            self.width = height
            self.height = width
        else:
            self.width = width
            self.height = height
            
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def clear(self):
        """Clear the panel buffer"""
        self.buffer.fill(0)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set a pixel with rotation applied"""
        # Apply rotation
        rx, ry = self._rotate_coordinates(x, y)
        
        if 0 <= rx < self.width and 0 <= ry < self.height:
            self.buffer[ry, rx] = [r, g, b]
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get a pixel with rotation applied"""
        rx, ry = self._rotate_coordinates(x, y)
        
        if 0 <= rx < self.width and 0 <= ry < self.height:
            return tuple(self.buffer[ry, rx])
        return (0, 0, 0)
    
    def _rotate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Apply rotation to coordinates"""
        if self.rotation == 0:
            return x, y
        elif self.rotation == 90:
            return y, self.original_width - 1 - x
        elif self.rotation == 180:
            return self.original_width - 1 - x, self.original_height - 1 - y
        elif self.rotation == 270:
            return self.original_height - 1 - y, x
        else:
            return x, y
    
    def fill(self, r: int, g: int, b: int):
        """Fill entire panel with color"""
        self.buffer[:, :] = [r, g, b]


class MultiPanelMatrix:
    """Manages multiple LED matrix panels as a unified display"""
    
    def __init__(self):
        self.panels: List[Panel] = []
        self.total_width = 0
        self.total_height = 0
    
    def add_panel(self, panel: Panel):
        """Add a panel to the multi-panel display"""
        self.panels.append(panel)
        self._recalculate_dimensions()
    
    def remove_panel(self, panel_id: int):
        """Remove a panel by ID"""
        self.panels = [p for p in self.panels if p.panel_id != panel_id]
        self._recalculate_dimensions()
    
    def clear_all(self):
        """Clear all panels"""
        for panel in self.panels:
            panel.clear()
    
    def _recalculate_dimensions(self):
        """Recalculate total display dimensions"""
        if not self.panels:
            self.total_width = self.total_height = 0
            return
            
        max_x = max(panel.x_offset + panel.width for panel in self.panels)
        max_y = max(panel.y_offset + panel.height for panel in self.panels)
        
        self.total_width = max_x
        self.total_height = max_y
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set a pixel on the appropriate panel"""
        for panel in self.panels:
            if (panel.x_offset <= x < panel.x_offset + panel.width and 
                panel.y_offset <= y < panel.y_offset + panel.height):
                
                panel_x = x - panel.x_offset
                panel_y = y - panel.y_offset
                panel.set_pixel(panel_x, panel_y, r, g, b)
                break
    
    def get_combined_buffer(self) -> np.ndarray:
        """Get combined buffer of all panels"""
        if not self.panels:
            return np.zeros((16, 16, 3), dtype=np.uint8)
            
        combined = np.zeros((self.total_height, self.total_width, 3), dtype=np.uint8)
        
        for panel in self.panels:
            y_start = panel.y_offset
            y_end = panel.y_offset + panel.height
            x_start = panel.x_offset
            x_end = panel.x_offset + panel.width
            
            combined[y_start:y_end, x_start:x_end] = panel.buffer
        
        return combined
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Draw text across panels"""
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
            'a': [0x20, 0x54, 0x54, 0x78, 0x40],
            'b': [0x7F, 0x28, 0x44, 0x44, 0x38],
            'c': [0x38, 0x44, 0x44, 0x44, 0x28],
            'd': [0x38, 0x44, 0x44, 0x28, 0x7F],
            'e': [0x38, 0x54, 0x54, 0x54, 0x18],
            'f': [0x00, 0x08, 0x7E, 0x09, 0x02],
            'g': [0x18, 0xA4, 0xA4, 0x9C, 0x78],
            'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
            'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
            'j': [0x20, 0x40, 0x40, 0x3D, 0x00],
            'k': [0x7F, 0x10, 0x28, 0x44, 0x00],
            'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
            'm': [0x7C, 0x04, 0x78, 0x04, 0x78],
            'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
            'o': [0x38, 0x44, 0x44, 0x44, 0x38],
            'p': [0xFC, 0x18, 0x24, 0x24, 0x18],
            'q': [0x18, 0x24, 0x24, 0x18, 0xFC],
            'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
            's': [0x48, 0x54, 0x54, 0x54, 0x24],
            't': [0x04, 0x04, 0x3F, 0x44, 0x24],
            'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
            'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
            'w': [0x3C, 0x40, 0x30, 0x40, 0x3C],
            'x': [0x44, 0x28, 0x10, 0x28, 0x44],
            'y': [0x4C, 0x90, 0x90, 0x90, 0x7C],
            'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
        }


class PanelConfigurationGUI:
    """GUI for configuring multi-panel layout"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.panels_config = []
        self.setup_gui()
    
    def setup_gui(self):
        """Create the configuration GUI"""
        self.config_window = tk.Toplevel()
        self.config_window.title("Multi-Panel LED Matrix Configuration")
        self.config_window.geometry("800x600")
        self.config_window.resizable(True, True)
        
        # Main frame with scrolling
        canvas = tk.Canvas(self.config_window)
        scrollbar = ttk.Scrollbar(self.config_window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_frame = ttk.Frame(self.scrollable_frame)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(title_frame, text="Multi-Panel LED Matrix Configuration", 
                 font=('Arial', 16, 'bold')).pack()
        
        # Panel list frame
        self.panels_frame = ttk.LabelFrame(self.scrollable_frame, text="Panel Configuration")
        self.panels_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add panel button
        add_panel_frame = ttk.Frame(self.scrollable_frame)
        add_panel_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(add_panel_frame, text="Add Panel", command=self.add_panel).pack(side="left")
        ttk.Button(add_panel_frame, text="Load Configuration", command=self.load_config).pack(side="left", padx=5)
        ttk.Button(add_panel_frame, text="Save Configuration", command=self.save_config).pack(side="left")
        
        # Control buttons
        control_frame = ttk.Frame(self.scrollable_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="Apply Configuration", command=self.apply_config).pack(side="left")
        ttk.Button(control_frame, text="Preview Layout", command=self.preview_layout).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Close", command=self.config_window.destroy).pack(side="right")
        
        # Add first panel by default
        self.add_panel()
    
    def add_panel(self):
        """Add a new panel configuration"""
        panel_id = len(self.panels_config)
        
        panel_frame = ttk.LabelFrame(self.panels_frame, text=f"Panel {panel_id}")
        panel_frame.pack(fill="x", padx=5, pady=5)
        
        # Panel configuration variables
        config = {
            'id': panel_id,
            'width_var': tk.IntVar(value=16),
            'height_var': tk.IntVar(value=16),
            'rotation_var': tk.IntVar(value=0),
            'x_offset_var': tk.IntVar(value=panel_id * 16),
            'y_offset_var': tk.IntVar(value=0),
            'frame': panel_frame
        }
        
        # Create configuration widgets
        row1 = ttk.Frame(panel_frame)
        row1.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(row1, text="Width:").pack(side="left")
        ttk.Spinbox(row1, from_=8, to=64, width=5, textvariable=config['width_var']).pack(side="left", padx=5)
        
        ttk.Label(row1, text="Height:").pack(side="left", padx=(10,0))
        ttk.Spinbox(row1, from_=8, to=64, width=5, textvariable=config['height_var']).pack(side="left", padx=5)
        
        ttk.Label(row1, text="Rotation:").pack(side="left", padx=(10,0))
        rotation_combo = ttk.Combobox(row1, width=8, textvariable=config['rotation_var'],
                                    values=[0, 90, 180, 270], state="readonly")
        rotation_combo.pack(side="left", padx=5)
        
        row2 = ttk.Frame(panel_frame)
        row2.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(row2, text="X Offset:").pack(side="left")
        ttk.Spinbox(row2, from_=0, to=500, width=5, textvariable=config['x_offset_var']).pack(side="left", padx=5)
        
        ttk.Label(row2, text="Y Offset:").pack(side="left", padx=(10,0))
        ttk.Spinbox(row2, from_=0, to=500, width=5, textvariable=config['y_offset_var']).pack(side="left", padx=5)
        
        # Remove panel button
        ttk.Button(row2, text="Remove Panel", 
                  command=lambda: self.remove_panel(config)).pack(side="right", padx=5)
        
        self.panels_config.append(config)
    
    def remove_panel(self, config):
        """Remove a panel configuration"""
        if len(self.panels_config) <= 1:
            messagebox.showwarning("Warning", "At least one panel is required!")
            return
            
        config['frame'].destroy()
        self.panels_config.remove(config)
        
        # Renumber panels
        for i, panel_config in enumerate(self.panels_config):
            panel_config['id'] = i
            panel_config['frame'].configure(text=f"Panel {i}")
    
    def apply_config(self):
        """Apply the current configuration"""
        if self.callback:
            panels = []
            for config in self.panels_config:
                panel_data = {
                    'id': config['id'],
                    'width': config['width_var'].get(),
                    'height': config['height_var'].get(),
                    'rotation': config['rotation_var'].get(),
                    'x_offset': config['x_offset_var'].get(),
                    'y_offset': config['y_offset_var'].get()
                }
                panels.append(panel_data)
            self.callback(panels)
    
    def preview_layout(self):
        """Show a preview of the panel layout"""
        preview_window = tk.Toplevel(self.config_window)
        preview_window.title("Panel Layout Preview")
        preview_window.geometry("600x400")
        
        canvas = tk.Canvas(preview_window, bg='black')
        canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Calculate scaling
        max_x = max(config['x_offset_var'].get() + 
                   (config['height_var'].get() if config['rotation_var'].get() in [90, 270] 
                    else config['width_var'].get()) for config in self.panels_config)
        max_y = max(config['y_offset_var'].get() + 
                   (config['width_var'].get() if config['rotation_var'].get() in [90, 270] 
                    else config['height_var'].get()) for config in self.panels_config)
        
        scale_x = 500 / max(max_x, 1)
        scale_y = 300 / max(max_y, 1)
        scale = min(scale_x, scale_y, 10)  # Max 10px per LED
        
        # Draw panels
        colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'orange', 'pink']
        for i, config in enumerate(self.panels_config):
            width = config['width_var'].get()
            height = config['height_var'].get()
            rotation = config['rotation_var'].get()
            x_offset = config['x_offset_var'].get()
            y_offset = config['y_offset_var'].get()
            
            # Apply rotation to dimensions
            if rotation in [90, 270]:
                draw_width = height * scale
                draw_height = width * scale
            else:
                draw_width = width * scale
                draw_height = height * scale
            
            x1 = x_offset * scale + 50
            y1 = y_offset * scale + 50
            x2 = x1 + draw_width
            y2 = y1 + draw_height
            
            color = colors[i % len(colors)]
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='white', width=2)
            canvas.create_text(x1 + draw_width/2, y1 + draw_height/2, 
                             text=f"P{i}\n{rotation}°", fill='white', font=('Arial', 8))
    
    def save_config(self):
        """Save configuration to file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Save Panel Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            config_data = []
            for config in self.panels_config:
                config_data.append({
                    'width': config['width_var'].get(),
                    'height': config['height_var'].get(),
                    'rotation': config['rotation_var'].get(),
                    'x_offset': config['x_offset_var'].get(),
                    'y_offset': config['y_offset_var'].get()
                })
            
            try:
                with open(filename, 'w') as f:
                    json.dump(config_data, f, indent=2)
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="Load Panel Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config_data = json.load(f)
                
                # Clear existing panels
                for config in self.panels_config[:]:
                    config['frame'].destroy()
                self.panels_config.clear()
                
                # Add loaded panels
                for panel_data in config_data:
                    self.add_panel()
                    config = self.panels_config[-1]
                    config['width_var'].set(panel_data.get('width', 16))
                    config['height_var'].set(panel_data.get('height', 16))
                    config['rotation_var'].set(panel_data.get('rotation', 0))
                    config['x_offset_var'].set(panel_data.get('x_offset', 0))
                    config['y_offset_var'].set(panel_data.get('y_offset', 0))
                
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")


class MultiPanelDisplay:
    """GUI display for multi-panel matrix"""
    
    def __init__(self, pixel_size: int = 10):
        self.pixel_size = pixel_size
        self.update_queue = queue.Queue()
        self.panels: List[Panel] = []
        
        # Create window in separate thread
        self.display_thread = threading.Thread(target=self._create_window, daemon=True)
        self.display_thread.start()
        
        # Give window time to initialize
        time.sleep(0.5)
    
    def _create_window(self):
        """Create and run the tkinter window"""
        self.root = tk.Tk()
        self.root.title("Multi-Panel LED Matrix Display")
        self.root.resizable(True, True)
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(main_frame, bg='black', highlightthickness=1,
                               highlightbackground='gray')
        
        h_scroll = ttk.Scrollbar(main_frame, orient="horizontal", command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        # Pack scrollbars and canvas
        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Status frame
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="Multi-Panel LED Matrix Display",
                                   font=('Arial', 10), fg='green')
        self.status_label.pack(side="left")
        
        self.info_label = tk.Label(status_frame, text="No panels configured",
                                 font=('Arial', 8), fg='gray')
        self.info_label.pack(side="right")
        
        # Control frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(control_frame, text="Configure Panels", 
                  command=self.open_config).pack(side="left")
        
        # Set up periodic update check
        self.root.after(33, self._check_updates)  # ~30 FPS
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start the GUI loop
        self.root.mainloop()
    
    def open_config(self):
        """Open panel configuration GUI"""
        PanelConfigurationGUI(callback=self.update_panels)
    
    def update_panels(self, panels_data):
        """Update panel configuration"""
        try:
            # Create new panels from configuration
            new_panels = []
            for data in panels_data:
                panel = Panel(
                    panel_id=data['id'],
                    width=data['width'],
                    height=data['height'],
                    rotation=data['rotation'],
                    x_offset=data['x_offset'],
                    y_offset=data['y_offset']
                )
                new_panels.append(panel)
            
            self.panels = new_panels
            self.update_queue.put(('config_update', self.panels))
            
        except Exception as e:
            print(f"Error updating panels: {e}")
    
    def _check_updates(self):
        """Check for display updates from the main thread"""
        try:
            while True:
                update_type, data = self.update_queue.get_nowait()
                if update_type == 'display_update':
                    self._update_display(data)
                elif update_type == 'config_update':
                    self._update_configuration(data)
        except queue.Empty:
            pass
        
        # Schedule next check
        if self.root and self.root.winfo_exists():
            self.root.after(33, self._check_updates)
    
    def _update_configuration(self, panels):
        """Update display configuration"""
        # Clear canvas
        self.canvas.delete("all")
        
        if not panels:
            self.info_label.config(text="No panels configured")
            return
        
        # Calculate total dimensions
        max_x = max(p.x_offset + p.width for p in panels)
        max_y = max(p.y_offset + p.height for p in panels)
        
        # Update canvas size
        canvas_width = max_x * self.pixel_size
        canvas_height = max_y * self.pixel_size
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Create pixel rectangles for each panel
        self.pixel_rects = {}
        colors = ['#800000', '#008000', '#000080', '#808000', '#800080', '#008080']
        
        for panel in panels:
            panel_color = colors[panel.panel_id % len(colors)]
            
            for y in range(panel.height):
                for x in range(panel.width):
                    screen_x = (panel.x_offset + x) * self.pixel_size
                    screen_y = (panel.y_offset + y) * self.pixel_size
                    
                    rect_id = self.canvas.create_rectangle(
                        screen_x, screen_y,
                        screen_x + self.pixel_size, screen_y + self.pixel_size,
                        fill=panel_color, outline='#333333', width=1
                    )
                    
                    self.pixel_rects[(panel.panel_id, x, y)] = rect_id
        
        # Update info label
        self.info_label.config(text=f"Panels: {len(panels)} | Total: {max_x}x{max_y}")
    
    def _update_display(self, panels):
        """Update the display with new matrix data"""
        for panel in panels:
            for y in range(panel.height):
                for x in range(panel.width):
                    if (panel.panel_id, x, y) in self.pixel_rects:
                        r, g, b = panel.buffer[y, x]
                        
                        # Convert to hex color
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        
                        rect_id = self.pixel_rects[(panel.panel_id, x, y)]
                        self.canvas.itemconfig(rect_id, fill=hex_color)
    
    def update_display(self, panels):
        """Queue a display update"""
        self.update_queue.put(('display_update', panels))
    
    def _on_closing(self):
        """Handle window closing"""
        self.root.quit()
        self.root.destroy()


class ScrollingText:
    """Scrolling text across multi-panel display"""
    
    def __init__(self, text: str, matrix: MultiPanelMatrix, color: Tuple[int, int, int] = (255, 0, 0)):
        self.text = text
        self.matrix = matrix
        self.color = color
        self.position = matrix.total_width
        self.text_width = matrix.get_text_width(text)
    
    def update(self):
        """Update scrolling position"""
        self.matrix.clear_all()
        
        # Draw text at current position
        self.matrix.draw_text(self.text, self.position, 4, self.color)
        
        # Move text position
        self.position -= 1
        
        # Reset position when text fully scrolled off
        if self.position < -self.text_width:
            self.position = self.matrix.total_width
    
    def set_text(self, new_text: str):
        """Update the scrolling text"""
        self.text = new_text
        self.text_width = self.matrix.get_text_width(new_text)
        self.position = self.matrix.total_width
    
    def set_color(self, color: Tuple[int, int, int]):
        """Update text color"""
        self.color = color


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Panel LED Matrix Controller")
    parser.add_argument('--port', default='auto', help='Serial port for ESP32 (default: auto-detect)')
    parser.add_argument('--mock', action='store_true', help='Use mock display mode (no ESP32 hardware)')
    parser.add_argument('--esp32', action='store_true', help='Connect to ESP32 hardware')
    args = parser.parse_args()
    
    print("Multi-Panel LED Matrix Controller")
    print("=" * 40)
    
    # Auto-detect platform and set default port
    if args.port == 'auto':
        if sys.platform.startswith('win'):
            default_port = 'COM3'
        else:
            default_port = '/dev/ttyUSB0'
    else:
        default_port = args.port
    
    # Create multi-panel matrix
    matrix = MultiPanelMatrix()
    
    # Add default panels (2x1 layout)
    default_panels = [
        {'id': 0, 'width': 16, 'height': 16, 'rotation': 0, 'x_offset': 0, 'y_offset': 0},
        {'id': 1, 'width': 16, 'height': 16, 'rotation': 0, 'x_offset': 16, 'y_offset': 0}
    ]
    
    for panel_data in default_panels:
        panel = Panel(
            panel_id=panel_data['id'],
            width=panel_data['width'],
            height=panel_data['height'],
            rotation=panel_data['rotation'],
            x_offset=panel_data['x_offset'],
            y_offset=panel_data['y_offset']
        )
        matrix.add_panel(panel)
    
    # Initialize ESP32 controller if requested
    esp32_controller = None
    if args.esp32:
        try:
            from multi_panel_esp32_controller import MultiPanelESP32Controller
            esp32_controller = MultiPanelESP32Controller(port=default_port)
            if esp32_controller.connect():
                # Configure ESP32 for total display size
                if esp32_controller.configure_display(matrix.total_width, matrix.total_height):
                    print("✓ ESP32 configured for multi-panel display")
                else:
                    print("✗ Failed to configure ESP32")
                    esp32_controller = None
            else:
                print("✗ Failed to connect to ESP32")
                esp32_controller = None
        except ImportError:
            print("✗ ESP32 controller not available")
            esp32_controller = None
    
    # Create display (GUI mock display)
    display = MultiPanelDisplay(pixel_size=15)
    display.update_panels(default_panels)
    
    # Initialize scrolling text
    scroller = ScrollingText("HELLO MULTI-PANEL WORLD!", matrix, (255, 0, 0))
    
    mode_text = "ESP32 HARDWARE" if esp32_controller else "MOCK DISPLAY"
    print(f"\nRunning in {mode_text} mode")
    if esp32_controller:
        print(f"ESP32 Port: {default_port}")
    
    print("\nMulti-Panel Commands:")
    print("  text:<message> - Set scrolling text")
    print("  color:<r>,<g>,<b> - Set text color")
    print("  brightness:<0-255> - Set brightness (ESP32 only)")
    print("  config - Open panel configuration")
    print("  clear - Clear all panels")
    print("  quit - Exit")
    
    # Main loop with better input handling
    try:
        last_update = time.time()
        print("\nEnter commands (or 'quit' to exit):")
        
        while True:
            current_time = time.time()
            
            # Update display at ~15 FPS
            if current_time - last_update >= 1/15:
                scroller.update()
                display.update_display(matrix.panels)
                
                # Send to ESP32 if available
                if esp32_controller and esp32_controller.connected:
                    combined_buffer = matrix.get_combined_buffer()
                    try:
                        esp32_controller.send_frame(combined_buffer)
                    except Exception as e:
                        print(f"ESP32 communication error: {e}")
                
                last_update = current_time
            
            # Handle input (simplified for cross-platform compatibility)
            try:
                # Non-blocking input check
                if sys.platform.startswith('win'):
                    # Windows: use msvcrt for non-blocking input
                    import msvcrt
                    if msvcrt.kbhit():
                        command = input().strip()
                        handle_command(command, scroller, matrix, display, esp32_controller)
                else:
                    # Unix: use select for non-blocking input
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        command = input().strip()
                        handle_command(command, scroller, matrix, display, esp32_controller)
                        
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Input error: {e}")
            
            time.sleep(0.01)  # Small delay to prevent high CPU usage
    
    except KeyboardInterrupt:
        pass
    finally:
        if esp32_controller:
            esp32_controller.disconnect()
    
    print("\nShutting down...")


def handle_command(command, scroller, matrix, display, esp32_controller):
    """Handle user commands"""
    if command.lower() in ['quit', 'exit', 'q']:
        return False
    elif command.startswith('text:'):
        new_text = command[5:]
        scroller.set_text(new_text)
        print(f"Text updated: '{new_text}'")
    elif command.startswith('color:'):
        try:
            color_parts = command[6:].split(',')
            r, g, b = map(int, color_parts)
            scroller.set_color((r, g, b))
            print(f"Color updated: RGB({r}, {g}, {b})")
        except (ValueError, IndexError):
            print("Invalid color format. Use: color:r,g,b")
    elif command.startswith('brightness:') and esp32_controller:
        try:
            brightness = int(command[11:])
            if esp32_controller.set_brightness(brightness):
                print(f"Brightness updated: {brightness}")
            else:
                print("Failed to set brightness")
        except ValueError:
            print("Invalid brightness value. Use: brightness:0-255")
    elif command.lower() == 'config':
        PanelConfigurationGUI(callback=lambda panels: display.update_panels(panels))
    elif command.lower() == 'clear':
        matrix.clear_all()
        display.update_display(matrix.panels)
        if esp32_controller:
            esp32_controller.clear_display()
        print("Display cleared")
    elif command.lower() == 'status' and esp32_controller:
        status = esp32_controller.get_status()
        print(f"ESP32 Status: {status}")
    else:
        print("Unknown command")
    
    return True


if __name__ == "__main__":
    # Handle missing select module on Windows
    try:
        import select
    except ImportError:
        # Windows fallback - simplified input handling
        class MockSelect:
            @staticmethod
            def select(rlist, wlist, xlist, timeout):
                return [], [], []
        
        select = MockSelect()
    
    main()