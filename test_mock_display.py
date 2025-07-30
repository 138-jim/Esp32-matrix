#!/usr/bin/env python3
"""
Test script for the mock display functionality
"""

import sys
import os

# Add current directory to path so we can import the controller
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from led_matrix_controller_windows_test import LEDMatrix, MockDisplay, PatternGenerator
import time

def test_mock_display():
    """Test the mock display with different patterns"""
    print("Testing Mock Display...")
    
    # Create matrix and display
    matrix = LEDMatrix(16, 16)
    display = MockDisplay(16, 16, 25)
    
    print("GUI window should be open now...")
    
    try:
        # Test 1: Simple text pattern
        print("Test 1: Drawing simple pattern...")
        matrix.clear()
        matrix.fill(50, 0, 0)  # Dim red background
        matrix.draw_text("HI", 2, 4, (0, 255, 0))  # Green text
        display.update(matrix)
        time.sleep(2)
        
        # Test 2: Rainbow pattern
        print("Test 2: Rainbow pattern...")
        for i in range(30):  # Run for 30 frames
            PatternGenerator.rainbow(matrix, i * 0.1)
            display.update(matrix)
            time.sleep(0.1)
        
        # Test 3: Spiral pattern
        print("Test 3: Spiral pattern...")
        for i in range(30):
            PatternGenerator.spiral(matrix, i * 0.1)
            display.update(matrix)
            time.sleep(0.1)
        
        # Test 4: Wave pattern
        print("Test 4: Wave pattern...")
        for i in range(30):
            PatternGenerator.wave(matrix, i * 0.1)
            display.update(matrix)
            time.sleep(0.1)
        
        # Test 5: Scrolling text
        print("Test 5: Scrolling text simulation...")
        text = "HELLO WORLD!"
        for pos in range(matrix.width, -len(text) * 6, -1):
            matrix.clear()
            matrix.draw_text(text, pos, 4, (255, 255, 0))  # Yellow text
            display.update(matrix)
            time.sleep(0.1)
        
        print("Tests completed! Close the GUI window to exit.")
        
        # Keep the display open
        input("Press Enter to close...")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    finally:
        display.close()
        print("Mock display closed")

if __name__ == "__main__":
    test_mock_display()