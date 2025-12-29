"""
Simple Lava Lamp Animation
Based on Shadertoy implementation by Jessica Plotkin
https://www.shadertoy.com/view/NdSSzw

Uses simple sin/cos animation instead of physics simulation for performance.
"""

import numpy as np
import time
import math


class SimpleLavaLamp:
    """Simple lava lamp with sin/cos animated metaballs"""

    def __init__(self, width: int = 32, height: int = 32):
        self.width = width
        self.height = height
        self.start_time = time.time()

        # 10 blobs with different animation parameters
        self.blobs = [
            {'x_speed': 0.01, 'x_range': 0.3, 'y_speed': 0.25, 'y_range': 0.4, 'radius': 0.03},
            {'x_speed': 0.02, 'x_range': 0.1, 'y_speed': 0.2, 'y_range': 0.5, 'radius': 0.025},
            {'x_speed': 0.025, 'x_range': 0.3, 'y_speed': 0.1, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.02, 'x_range': 0.2, 'y_speed': 0.18, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.03, 'x_range': 0.3, 'y_speed': 0.25, 'y_range': 0.4, 'radius': 0.03},
            {'x_speed': 0.03, 'x_range': 0.1, 'y_speed': 0.15, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.01, 'x_range': 0.3, 'y_speed': 0.1, 'y_range': 0.5, 'radius': 0.045},
            {'x_speed': 0.02, 'x_range': 0.2, 'y_speed': 0.12, 'y_range': 0.5, 'radius': 0.028},
            {'x_speed': 0.024, 'x_range': 0.3, 'y_speed': 0.22, 'y_range': 0.5, 'radius': 0.032},
            {'x_speed': 0.03, 'x_range': 0.1, 'y_speed': 0.3, 'y_range': 0.5, 'radius': 0.030},
        ]

    def scale_by_temp(self, y_norm: float) -> float:
        """Scale blob size by temperature (height) - hotter = bigger"""
        return 1.0 / math.log(y_norm + 2.0) - 0.6

    def get_blob_position(self, blob_idx: int, t: float) -> tuple:
        """Get blob position at time t using sin/cos animation"""
        blob = self.blobs[blob_idx]

        x = math.sin(t * blob['x_speed']) * blob['x_range']
        y = math.cos(t * blob['y_speed']) * blob['y_range']

        return (x, y)

    def render_frame(self) -> np.ndarray:
        """Render current frame using vectorized NumPy operations"""
        # Current time
        t = time.time() - self.start_time

        # Create coordinate grids (vectorized)
        x = np.linspace(-0.5, 0.5, self.width)
        y = np.linspace(-0.5, 0.5, self.height)
        xx, yy = np.meshgrid(x, y)

        # Initialize metaball field
        field = np.zeros((self.height, self.width), dtype=np.float32)

        # Add contribution from all blobs
        for i in range(len(self.blobs)):
            blob_x, blob_y = self.get_blob_position(i, t)

            # Temperature scaling based on Y position
            temp_scale = self.scale_by_temp(blob_y + 0.5)
            radius = self.blobs[i]['radius'] * max(0.5, temp_scale * 2.0)

            # Distance from each pixel to blob center (vectorized)
            dx = xx - blob_x
            dy = yy - blob_y
            dist = np.sqrt(dx * dx + dy * dy) + 0.001  # Add small value to avoid division by zero

            # Metaball contribution: radius / distance
            field += radius / dist

        # Create frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Background color - dark purple
        frame[:, :] = [10, 0, 20]

        # Apply threshold and color
        mask = field > 0.5
        if np.any(mask):
            # Normalize field for color intensity
            intensity = np.clip(field / 2.0, 0, 1)

            # Temperature based on Y position (0 = top/hot, 1 = bottom/cool)
            temp = np.linspace(0, 1, self.height)[:, np.newaxis]

            # Color channels based on temperature and intensity
            r = np.where(temp < 0.3, 255, np.where(temp < 0.6, 255, 220)) * intensity
            g = np.where(temp < 0.3, 200, np.where(temp < 0.6, 150, 50)) * intensity
            b = np.where(temp < 0.3, 50, np.where(temp < 0.6, 30, 20)) * intensity

            # Apply colors where field exceeds threshold
            frame[mask, 0] = r[mask].astype(np.uint8)
            frame[mask, 1] = g[mask].astype(np.uint8)
            frame[mask, 2] = b[mask].astype(np.uint8)

        return frame
