#!/usr/bin/env python3
"""
Display Controller - Main Display Loop
Pulls frames from queue, applies coordinate mapping, and updates LEDs
"""

import logging
import time
import threading
import queue
import numpy as np
from typing import Optional

from .led_driver import LEDDriver
from .coordinate_mapper import CoordinateMapper
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class DisplayController:
    """
    Main display controller loop

    Runs in dedicated thread, pulling frames from queue and updating LEDs
    Supports hot-reload of configuration without restart
    """

    def __init__(self,
                 led_driver: LEDDriver,
                 mapper: CoordinateMapper,
                 frame_queue: queue.Queue,
                 config_reload_event: threading.Event,
                 config_path: str,
                 target_fps: int = 30):
        """
        Initialize display controller

        Args:
            led_driver: LED driver instance
            mapper: Coordinate mapper instance
            frame_queue: Thread-safe queue for incoming frames
            config_reload_event: Event signaling configuration reload
            config_path: Path to configuration file
            target_fps: Target frame rate (frames per second)
        """
        self.led_driver = led_driver
        self.mapper = mapper
        self.frame_queue = frame_queue
        self.config_reload_event = config_reload_event
        self.config_path = config_path
        self.target_fps = target_fps

        self.running = False
        self.thread = None

        # Statistics
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        self.dropped_frames = 0

        # Frame timing
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0
        self.last_frame_time = 0

        logger.info(f"Display controller initialized: target {target_fps} FPS")

    def start(self) -> None:
        """Start the display controller thread"""
        if self.running:
            logger.warning("Display controller already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Display controller started")

    def stop(self) -> None:
        """Stop the display controller thread"""
        if not self.running:
            return

        logger.info("Stopping display controller...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        # Clear display
        self.led_driver.clear()
        self.led_driver.show()

        logger.info("Display controller stopped")

    def _run_loop(self) -> None:
        """Main display loop (runs in thread)"""
        logger.info("Display loop started")

        while self.running:
            try:
                # Check for configuration reload
                if self.config_reload_event.is_set():
                    self._handle_config_reload()

                # Get frame from queue (non-blocking with timeout)
                try:
                    frame = self.frame_queue.get(block=True, timeout=0.01)
                    self._display_frame(frame)
                except queue.Empty:
                    # No frame available, continue
                    pass

                # Maintain frame rate
                self._maintain_frame_rate()

                # Update FPS statistics
                self._update_fps_stats()

            except Exception as e:
                logger.error(f"Error in display loop: {e}", exc_info=True)
                time.sleep(0.1)  # Prevent tight error loop

        logger.info("Display loop ended")

    def _handle_config_reload(self) -> None:
        """Handle configuration reload event"""
        try:
            logger.info("Configuration reload detected")

            # Load new configuration
            config_manager = ConfigManager()
            new_config = config_manager.load_config(self.config_path)

            # Clear display during reload
            self.led_driver.clear()
            self.led_driver.show()

            # Reload mapper with new configuration
            self.mapper.reload_config(new_config)

            # Clear reload event
            self.config_reload_event.clear()

            logger.info("Configuration reload complete")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}", exc_info=True)
            self.config_reload_event.clear()

    def _display_frame(self, virtual_frame: np.ndarray) -> None:
        """
        Display a frame on the LEDs

        Args:
            virtual_frame: Frame in virtual coordinate space
        """
        try:
            # Map virtual frame to physical LED order
            physical_frame = self.mapper.map_frame(virtual_frame)

            # Send to LED driver
            self.led_driver.set_frame(physical_frame)
            self.led_driver.show()

            self.frame_count += 1

        except Exception as e:
            logger.error(f"Error displaying frame: {e}", exc_info=True)

    def _maintain_frame_rate(self) -> None:
        """Maintain target frame rate"""
        if self.frame_interval <= 0:
            return

        current_time = time.time()
        elapsed = current_time - self.last_frame_time

        if elapsed < self.frame_interval:
            sleep_time = self.frame_interval - elapsed
            time.sleep(sleep_time)

        self.last_frame_time = time.time()

    def _update_fps_stats(self) -> None:
        """Update FPS statistics"""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:  # Update every second
            self.current_fps = self.frame_count / elapsed
            logger.debug(f"FPS: {self.current_fps:.1f}, Dropped: {self.dropped_frames}")

            self.frame_count = 0
            self.last_fps_time = current_time

    def get_fps(self) -> float:
        """Get current FPS"""
        return self.current_fps

    def get_queue_size(self) -> int:
        """Get current frame queue size"""
        return self.frame_queue.qsize()

    def clear_queue(self) -> None:
        """Clear all pending frames from queue"""
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Frame queue cleared")

    def set_target_fps(self, fps: int) -> None:
        """
        Set target frame rate

        Args:
            fps: Target frames per second
        """
        if fps > 0:
            self.target_fps = fps
            self.frame_interval = 1.0 / fps
            logger.info(f"Target FPS set to {fps}")
        else:
            logger.warning(f"Invalid FPS: {fps}")
