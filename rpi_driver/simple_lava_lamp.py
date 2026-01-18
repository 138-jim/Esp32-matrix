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

        # 10 blobs matching original shader (speeds 2x faster as requested)
        # Format: x_speed, x_range, y_speed, y_range, circles (each circle: x_offset, y_offset, radius)
        self.blobs = [
            # Blob 0
            {'x_speed': 0.02, 'x_range': 0.3, 'y_speed': 0.50, 'y_range': 0.4, 'x_flip': -1,
             'circles': [(0.01, 0.0, 0.03), (0.02, 0.0, 0.02)]},
            # Blob 1
            {'x_speed': 0.04, 'x_range': 0.1, 'y_speed': 0.40, 'y_range': 0.5, 'x_flip': 1,
             'circles': [(-0.015, -0.02, 0.018), (-0.005, 0.0, 0.03), (-0.02, 0.01, 0.02)]},
            # Blob 2
            {'x_speed': 0.05, 'x_range': 0.3, 'y_speed': 0.20, 'y_range': 0.5, 'x_flip': -1,
             'circles': [(0.02, 0.02, 0.03), (0.0, -0.02, 0.015), (-0.02, 0.0, 0.025)]},
            # Blob 3
            {'x_speed': 0.04, 'x_range': 0.2, 'y_speed': 0.36, 'y_range': 0.5, 'x_flip': 1,
             'circles': [(0.0, -0.03, 0.04), (0.04, 0.01, 0.03)]},
            # Blob 4
            {'x_speed': 0.06, 'x_range': 0.3, 'y_speed': 0.50, 'y_range': 0.4, 'x_flip': 1,
             'circles': [(0.03, 0.02, 0.025), (0.0, 0.0, 0.03), (0.03, 0.0, 0.035)]},
            # Blob 5
            {'x_speed': 0.06, 'x_range': 0.1, 'y_speed': 0.30, 'y_range': 0.5, 'x_flip': -1,
             'circles': [(0.0, 0.0, 0.035)]},
            # Blob 6
            {'x_speed': 0.02, 'x_range': 0.3, 'y_speed': 0.20, 'y_range': 0.5, 'x_flip': -1,
             'circles': [(0.0, 0.0, 0.045)]},
            # Blob 7
            {'x_speed': 0.04, 'x_range': 0.2, 'y_speed': 0.24, 'y_range': 0.5, 'x_flip': 1,
             'circles': [(0.0, -0.03, 0.03), (0.0, 0.0, 0.025), (0.03, -0.02, 0.03)]},
            # Blob 8
            {'x_speed': 0.048, 'x_range': 0.3, 'y_speed': 0.44, 'y_range': 0.5, 'x_flip': -1,
             'circles': [(0.0, 0.0, 0.035), (-0.03, -0.02, 0.035), (0.02, 0.0, 0.025)]},
            # Blob 9
            {'x_speed': 0.06, 'x_range': 0.1, 'y_speed': 0.60, 'y_range': 0.5, 'x_flip': 1,
             'circles': [(0.0, 0.0, 0.035), (0.01, 0.02, 0.015), (0.03, 0.0, 0.025), (0.05, -0.03, 0.015)]},
        ]

    def scale_by_temp(self, y_norm: float) -> float:
        """Scale blob size by temperature (height) - hotter = bigger"""
        return 1.0 / math.log(y_norm + 2.0) - 0.6

    def get_blob_position(self, blob_idx: int, t: float) -> tuple:
        """Get blob center position at time t using sin/cos animation"""
        blob = self.blobs[blob_idx]

        x = blob['x_flip'] * math.sin(t * blob['x_speed']) * blob['x_range']
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

        # Add contribution from all blobs and their circles
        for i in range(len(self.blobs)):
            blob_x, blob_y = self.get_blob_position(i, t)

            # Temperature scaling based on Y position (reduced scaling)
            temp_scale = self.scale_by_temp(blob_y + 0.5)
            temp_multiplier = max(0.8, temp_scale * 0.8)

            # Add each circle in this blob
            for circle_x_offset, circle_y_offset, base_radius in self.blobs[i]['circles']:
                # Position this circle
                circle_x = blob_x + circle_x_offset
                circle_y = blob_y + circle_y_offset

                # Scale radius by temperature
                radius = base_radius * temp_multiplier

                # Distance from each pixel to circle center (vectorized)
                dx = xx - circle_x
                dy = yy - circle_y
                dist = np.sqrt(dx * dx + dy * dy) + 0.001  # Add small value to avoid division by zero

                # Metaball contribution: radius / (distance * 0.9) - matching original shader
                field += radius / (dist * 0.9)

        # Create frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Background color - dark purple
        frame[:, :] = [10, 0, 20]

        # Apply threshold and color (matching original shader threshold)
        mask = field > 0.75
        if np.any(mask):
            # Normalize field for color intensity
            intensity = np.clip(field / 2.0, 0, 1)

            # Temperature based on Y position (0 = bottom/hot, 1 = top/cool)
            temp = np.linspace(1, 0, self.height)[:, np.newaxis]  # Flipped so hot is at bottom

            # Color channels based on temperature and intensity
            r = np.where(temp < 0.3, 255, np.where(temp < 0.6, 255, 220)) * intensity
            g = np.where(temp < 0.3, 200, np.where(temp < 0.6, 150, 50)) * intensity
            b = np.where(temp < 0.3, 50, np.where(temp < 0.6, 30, 20)) * intensity

            # Apply colors where field exceeds threshold
            frame[mask, 0] = r[mask].astype(np.uint8)
            frame[mask, 1] = g[mask].astype(np.uint8)
            frame[mask, 2] = b[mask].astype(np.uint8)

        return frame
