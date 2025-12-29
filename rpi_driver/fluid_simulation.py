"""
Navier-Stokes Fluid Simulation for Lava Lamp Effect

Implements physically accurate fluid dynamics with temperature-based buoyancy.
Based on Jos Stam's "Stable Fluids" method.

Author: Claude Code
Date: 2025-12-29
"""

import numpy as np
import math
from typing import Tuple, List
import colorsys


class Blob:
    """Represents a blob particle in the lava lamp"""

    def __init__(self, x: float, y: float, size: float, temp: float = 0.5):
        self.x = x
        self.y = y
        self.size = size
        self.temp = temp
        self.vx = 0.0
        self.vy = 0.0


class FluidSimulation:
    """
    Navier-Stokes fluid simulation with temperature-based buoyancy

    Simulates realistic lava lamp behavior with heating at bottom,
    cooling at top, and fluid dynamics governing blob motion.
    """

    def __init__(self, width: int = 128, height: int = 128, dt: float = 0.1):
        """
        Initialize fluid simulation

        Args:
            width: Simulation grid width
            height: Simulation grid height
            dt: Time step for simulation
        """
        self.width = width
        self.height = height
        self.dt = dt

        # Fluid velocity fields
        self.velocity_u = np.zeros((height, width), dtype=np.float32)  # X velocity
        self.velocity_v = np.zeros((height, width), dtype=np.float32)  # Y velocity
        self.velocity_u_prev = np.zeros((height, width), dtype=np.float32)
        self.velocity_v_prev = np.zeros((height, width), dtype=np.float32)

        # Temperature field (drives buoyancy)
        self.temperature = np.zeros((height, width), dtype=np.float32)
        self.temperature_prev = np.zeros((height, width), dtype=np.float32)

        # Pressure field (for incompressibility)
        self.pressure = np.zeros((height, width), dtype=np.float32)
        self.divergence = np.zeros((height, width), dtype=np.float32)

        # Physical constants
        self.viscosity = 0.0001  # Fluid viscosity
        self.thermal_diffusion = 0.003  # Heat diffusion rate
        self.buoyancy_force = 0.8  # Temperature-driven lift
        self.gravity = 0.15  # Downward force

        # Solver parameters
        self.solver_iterations = 2  # Jacobi iterations for pressure/diffusion (minimal for performance)

        # Blob particles (lava wax)
        self.blobs: List[Blob] = []
        self._initialize_blobs()

        # Set boundary conditions
        self._setup_boundaries()

    def _initialize_blobs(self):
        """Initialize blob particles at random positions"""
        num_blobs = 3  # Reduced for performance

        for i in range(num_blobs):
            # Random position
            x = np.random.uniform(self.width * 0.2, self.width * 0.8)
            y = np.random.uniform(self.height * 0.1, self.height * 0.9)

            # Random size
            size = np.random.uniform(8.0, 15.0)

            # Temperature based on initial height
            temp = 1.0 - (y / self.height)

            self.blobs.append(Blob(x, y, size, temp))

    def _setup_boundaries(self):
        """Set up temperature boundary conditions"""
        # Hot bottom
        self.temperature[0:3, :] = 1.0

        # Cool top
        self.temperature[-3:, :] = 0.0

    def step(self):
        """Advance simulation by one time step"""
        # 1. Apply forces (buoyancy based on temperature)
        self._add_forces()

        # 2. Advect velocity by itself
        self._advect_velocity()

        # 3. Skip velocity diffusion for performance (projection smooths the field)
        # self._diffuse_velocity()

        # 4. Project velocity (make incompressible)
        self._project()

        # 5. Advect temperature
        self._advect_temperature()

        # 6. Diffuse temperature
        self._diffuse_temperature()

        # 7. Maintain boundary conditions
        self._setup_boundaries()

        # 8. Update blob particles
        self._update_blobs()

    def _add_forces(self):
        """Apply buoyancy force based on temperature"""
        # Buoyancy: hot fluid rises, cool fluid sinks
        # F = (T - T_ambient) * buoyancy_force - gravity
        T_ambient = 0.5
        buoyancy = (self.temperature - T_ambient) * self.buoyancy_force
        self.velocity_v += buoyancy - self.gravity

    def _advect_velocity(self):
        """Advect velocity field by itself (self-advection)"""
        self.velocity_u_prev[:] = self.velocity_u
        self.velocity_v_prev[:] = self.velocity_v

        self.velocity_u = self._advect_field(self.velocity_u_prev, self.velocity_u_prev, self.velocity_v_prev)
        self.velocity_v = self._advect_field(self.velocity_v_prev, self.velocity_u_prev, self.velocity_v_prev)

    def _advect_temperature(self):
        """Advect temperature field by velocity"""
        self.temperature_prev[:] = self.temperature
        self.temperature = self._advect_field(self.temperature_prev, self.velocity_u, self.velocity_v)

    def _advect_field(self, field: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """
        Semi-Lagrangian advection - trace particles backward in time

        Args:
            field: Field to advect
            u: X velocity field
            v: Y velocity field

        Returns:
            Advected field
        """
        result = np.zeros_like(field)
        h, w = field.shape

        for y in range(h):
            for x in range(w):
                # Trace particle backward in time
                prev_x = x - u[y, x] * self.dt
                prev_y = y - v[y, x] * self.dt

                # Clamp to boundaries
                prev_x = max(0.5, min(w - 1.5, prev_x))
                prev_y = max(0.5, min(h - 1.5, prev_y))

                # Bilinear interpolation
                result[y, x] = self._bilinear_interp(field, prev_x, prev_y)

        return result

    def _bilinear_interp(self, field: np.ndarray, x: float, y: float) -> float:
        """Bilinear interpolation at (x, y) position"""
        h, w = field.shape

        x0 = int(x)
        y0 = int(y)
        x1 = min(x0 + 1, w - 1)
        y1 = min(y0 + 1, h - 1)

        fx = x - x0
        fy = y - y0

        # Interpolate
        v00 = field[y0, x0]
        v10 = field[y0, x1]
        v01 = field[y1, x0]
        v11 = field[y1, x1]

        v0 = v00 * (1 - fx) + v10 * fx
        v1 = v01 * (1 - fx) + v11 * fx

        return v0 * (1 - fy) + v1 * fy

    def _diffuse_velocity(self):
        """Diffuse velocity field (viscosity)"""
        self.velocity_u = self._diffuse_field(self.velocity_u, self.viscosity)
        self.velocity_v = self._diffuse_field(self.velocity_v, self.viscosity)

    def _diffuse_temperature(self):
        """Diffuse temperature field (thermal diffusion)"""
        self.temperature = self._diffuse_field(self.temperature, self.thermal_diffusion)

    def _diffuse_field(self, field: np.ndarray, diffusion_rate: float) -> np.ndarray:
        """
        Implicit diffusion using Jacobi iteration

        Solves: (I - diffusion_rate * dt * ∇²) * field_new = field_old
        """
        a = self.dt * diffusion_rate
        result = field.copy()

        for _ in range(self.solver_iterations):
            result_new = result.copy()

            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    # Average of neighbors
                    neighbors = (
                        result[y - 1, x] + result[y + 1, x] +
                        result[y, x - 1] + result[y, x + 1]
                    )
                    result_new[y, x] = (field[y, x] + a * neighbors) / (1 + 4 * a)

            result = result_new

        return result

    def _project(self):
        """Project velocity field to make it divergence-free"""
        # Compute divergence
        self.divergence[:] = 0
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                self.divergence[y, x] = -0.5 * (
                    self.velocity_u[y, x + 1] - self.velocity_u[y, x - 1] +
                    self.velocity_v[y + 1, x] - self.velocity_v[y - 1, x]
                )

        self.pressure[:] = 0

        # Solve Poisson equation: ∇²p = div
        for _ in range(self.solver_iterations):
            pressure_new = self.pressure.copy()

            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    neighbors = (
                        self.pressure[y - 1, x] + self.pressure[y + 1, x] +
                        self.pressure[y, x - 1] + self.pressure[y, x + 1]
                    )
                    pressure_new[y, x] = (self.divergence[y, x] + neighbors) / 4.0

            self.pressure = pressure_new

        # Subtract pressure gradient from velocity
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                self.velocity_u[y, x] -= 0.5 * (self.pressure[y, x + 1] - self.pressure[y, x - 1])
                self.velocity_v[y, x] -= 0.5 * (self.pressure[y + 1, x] - self.pressure[y - 1, x])

    def _update_blobs(self):
        """Update blob particle positions and properties"""
        for blob in self.blobs:
            # Sample velocity at blob position
            u = self._sample_field(self.velocity_u, blob.x, blob.y)
            v = self._sample_field(self.velocity_v, blob.x, blob.y)

            # Update position
            blob.x += u * self.dt * 10  # Scale for visibility
            blob.y += v * self.dt * 10

            # Wrap around horizontally
            if blob.x < 0:
                blob.x += self.width
            elif blob.x >= self.width:
                blob.x -= self.width

            # Bounce at top/bottom
            if blob.y < 5:
                blob.y = 5
                blob.vy = -blob.vy * 0.5
            elif blob.y >= self.height - 5:
                blob.y = self.height - 5
                blob.vy = -blob.vy * 0.5

            # Update temperature based on height
            height_ratio = 1.0 - (blob.y / self.height)
            blob.temp = height_ratio

            # Adjust size based on temperature (hot = larger)
            blob.size = 8.0 + 7.0 * blob.temp

    def _sample_field(self, field: np.ndarray, x: float, y: float) -> float:
        """Sample field value at floating point position"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return 0.0
        return self._bilinear_interp(field, x, y)

    def render_frame(self) -> np.ndarray:
        """
        Render current simulation state to RGB frame

        Returns:
            128x128 RGB frame (height, width, 3) uint8
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Dark background
        frame[:, :] = [10, 0, 20]

        # Render blobs using metaball algorithm
        for y in range(self.height):
            for x in range(self.width):
                # Calculate metaball field
                field = 0.0
                weighted_temp = 0.0

                for blob in self.blobs:
                    dx = x - blob.x
                    dy = y - blob.y
                    dist_sq = dx * dx + dy * dy

                    if dist_sq > 0.1:  # Avoid division by zero
                        contribution = (blob.size * blob.size) / dist_sq
                        field += contribution
                        weighted_temp += contribution * blob.temp

                # Threshold to create blob shape
                if field > 2.0:
                    # Average temperature at this pixel
                    avg_temp = weighted_temp / field if field > 0 else 0.5

                    # Intensity based on field strength
                    intensity = min(1.0, (field - 2.0) / 3.0)

                    # Color based on temperature
                    # Hot (bottom): Yellow/orange
                    # Cool (top): Red/dark red
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


def downsample_frame(hires_frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Downsample high-res frame to target resolution using average pooling

    Args:
        hires_frame: High resolution frame (e.g., 128x128x3)
        target_size: Target dimensions (height, width), e.g., (32, 32)

    Returns:
        Downsampled frame (target_height, target_width, 3) uint8
    """
    h_in, w_in, channels = hires_frame.shape
    h_out, w_out = target_size

    scale_y = h_in // h_out
    scale_x = w_in // w_out

    # Reshape and average over blocks
    reshaped = hires_frame.reshape(
        h_out, scale_y,
        w_out, scale_x,
        channels
    )

    downsampled = reshaped.mean(axis=(1, 3)).astype(np.uint8)

    return downsampled
