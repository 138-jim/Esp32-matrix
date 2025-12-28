#!/usr/bin/env python3
"""
Frame Receiver - Multi-protocol frame input
Handles UDP and named pipe protocols for receiving frames
"""

import logging
import socket
import threading
import queue
import struct
import os
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class UDPFrameReceiver:
    """
    Receive frames via UDP socket

    Protocol format:
    - Header: 4 bytes magic 'LEDF' (0x4C 0x45 0x44 0x46)
    - Width: 2 bytes (uint16, big-endian)
    - Height: 2 bytes (uint16, big-endian)
    - Data: width * height * 3 bytes (RGB)
    """

    MAGIC = b'LEDF'
    HEADER_SIZE = 8  # 4 bytes magic + 2 bytes width + 2 bytes height

    def __init__(self, port: int, frame_queue: queue.Queue,
                 expected_width: int, expected_height: int):
        """
        Initialize UDP frame receiver

        Args:
            port: UDP port to listen on
            frame_queue: Queue to push received frames to
            expected_width: Expected frame width
            expected_height: Expected frame height
        """
        self.port = port
        self.frame_queue = frame_queue
        self.expected_width = expected_width
        self.expected_height = expected_height

        self.running = False
        self.thread = None
        self.socket = None

        self.frames_received = 0
        self.frames_dropped = 0

    def start(self) -> None:
        """Start UDP receiver thread"""
        if self.running:
            logger.warning("UDP receiver already running")
            return

        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)  # Allow periodic checks

            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

            logger.info(f"UDP frame receiver started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start UDP receiver: {e}")
            raise

    def stop(self) -> None:
        """Stop UDP receiver thread"""
        if not self.running:
            return

        logger.info("Stopping UDP frame receiver...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        if self.socket:
            self.socket.close()
            self.socket = None

        logger.info("UDP frame receiver stopped")

    def _run_loop(self) -> None:
        """Main receive loop (runs in thread)"""
        logger.info("UDP receive loop started")

        while self.running:
            try:
                # Receive data (blocks with timeout)
                data, addr = self.socket.recvfrom(65536)

                # Parse and validate frame
                frame = self._parse_frame(data)
                if frame is not None:
                    # Try to add to queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame)
                        self.frames_received += 1
                    except queue.Full:
                        self.frames_dropped += 1
                        logger.warning("Frame queue full, dropping frame")

            except socket.timeout:
                # Normal timeout, continue
                continue
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    logger.error(f"Error receiving UDP frame: {e}")

        logger.info("UDP receive loop ended")

    def _parse_frame(self, data: bytes) -> Optional[np.ndarray]:
        """
        Parse UDP packet into frame

        Args:
            data: Raw UDP packet data

        Returns:
            Frame array or None if invalid
        """
        try:
            # Check minimum size
            if len(data) < self.HEADER_SIZE:
                logger.warning(f"Packet too small: {len(data)} bytes")
                return None

            # Parse header
            magic = data[0:4]
            if magic != self.MAGIC:
                logger.warning(f"Invalid magic: {magic.hex()}")
                return None

            width, height = struct.unpack('>HH', data[4:8])

            # Validate dimensions
            if width != self.expected_width or height != self.expected_height:
                logger.warning(f"Invalid dimensions: {width}x{height}, "
                             f"expected {self.expected_width}x{self.expected_height}")
                return None

            # Calculate expected data size
            expected_data_size = width * height * 3
            if len(data) != self.HEADER_SIZE + expected_data_size:
                logger.warning(f"Invalid data size: {len(data)-self.HEADER_SIZE} bytes, "
                             f"expected {expected_data_size}")
                return None

            # Extract RGB data
            rgb_data = data[self.HEADER_SIZE:]
            frame = np.frombuffer(rgb_data, dtype=np.uint8).reshape((height, width, 3))

            return frame

        except Exception as e:
            logger.error(f"Error parsing frame: {e}")
            return None


class PipeFrameReceiver:
    """
    Receive frames via named pipe (Unix/Linux only)

    Frame format: Raw RGB bytes (width * height * 3)
    """

    def __init__(self, pipe_path: str, frame_queue: queue.Queue,
                 expected_width: int, expected_height: int):
        """
        Initialize named pipe frame receiver

        Args:
            pipe_path: Path to named pipe
            frame_queue: Queue to push received frames to
            expected_width: Expected frame width
            expected_height: Expected frame height
        """
        self.pipe_path = Path(pipe_path)
        self.frame_queue = frame_queue
        self.expected_width = expected_width
        self.expected_height = expected_height

        self.running = False
        self.thread = None

        self.frames_received = 0
        self.frame_size = expected_width * expected_height * 3

    def start(self) -> None:
        """Start pipe receiver thread"""
        if self.running:
            logger.warning("Pipe receiver already running")
            return

        try:
            # Create named pipe if it doesn't exist
            if not self.pipe_path.exists():
                os.mkfifo(self.pipe_path)
                logger.info(f"Created named pipe: {self.pipe_path}")

            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

            logger.info(f"Pipe frame receiver started: {self.pipe_path}")

        except Exception as e:
            logger.error(f"Failed to start pipe receiver: {e}")
            raise

    def stop(self) -> None:
        """Stop pipe receiver thread"""
        if not self.running:
            return

        logger.info("Stopping pipe frame receiver...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        logger.info("Pipe frame receiver stopped")

    def _run_loop(self) -> None:
        """Main receive loop (runs in thread)"""
        logger.info("Pipe receive loop started")

        while self.running:
            try:
                # Open pipe for reading (blocks until writer connects)
                with open(self.pipe_path, 'rb') as pipe:
                    while self.running:
                        # Read frame data
                        data = pipe.read(self.frame_size)

                        if len(data) == 0:
                            # Writer closed pipe
                            break

                        if len(data) == self.frame_size:
                            # Parse frame
                            frame = np.frombuffer(data, dtype=np.uint8).reshape(
                                (self.expected_height, self.expected_width, 3)
                            )

                            # Try to add to queue
                            try:
                                self.frame_queue.put_nowait(frame)
                                self.frames_received += 1
                            except queue.Full:
                                logger.warning("Frame queue full, dropping frame")
                        else:
                            logger.warning(f"Incomplete frame: {len(data)} bytes")

            except Exception as e:
                if self.running:  # Only log if not shutting down
                    logger.error(f"Error receiving pipe frame: {e}")
                time.sleep(0.1)

        logger.info("Pipe receive loop ended")


def validate_frame_data(data: bytes, expected_width: int, expected_height: int) -> Tuple[bool, str]:
    """
    Validate raw frame data

    Args:
        data: Raw frame data (RGB bytes)
        expected_width: Expected frame width
        expected_height: Expected frame height

    Returns:
        Tuple of (is_valid, error_message)
    """
    expected_size = expected_width * expected_height * 3

    if len(data) != expected_size:
        return False, f"Invalid data size: {len(data)} bytes, expected {expected_size}"

    return True, ""


def bytes_to_frame(data: bytes, width: int, height: int) -> np.ndarray:
    """
    Convert raw bytes to frame array

    Args:
        data: Raw RGB bytes
        width: Frame width
        height: Frame height

    Returns:
        Frame array of shape (height, width, 3)
    """
    return np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))


def frame_to_bytes(frame: np.ndarray) -> bytes:
    """
    Convert frame array to raw bytes

    Args:
        frame: Frame array of shape (height, width, 3)

    Returns:
        Raw RGB bytes
    """
    return frame.tobytes()
