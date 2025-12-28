#!/usr/bin/env python3
"""
LED Display Driver - Main Entry Point
Initializes and orchestrates all system components
"""

import argparse
import logging
import signal
import sys
import queue
import threading
from pathlib import Path

import uvicorn

from .config_manager import ConfigManager
from .led_driver import LEDDriver, MockLEDDriver
from .coordinate_mapper import CoordinateMapper
from .display_controller import DisplayController
from .frame_receiver import UDPFrameReceiver, PipeFrameReceiver
from .web_api import WebAPIServer
from .sleep_scheduler import SleepScheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('led_driver.log')
    ]
)

logger = logging.getLogger(__name__)


class LEDDisplaySystem:
    """
    Main LED display system

    Orchestrates all components:
    - LED driver (GPIO control)
    - Coordinate mapper (virtual->physical mapping)
    - Display controller (main loop)
    - Frame receivers (UDP, pipe)
    - Web API (configuration and control)
    """

    def __init__(self, config_path: str, port: int = 8080, mock_mode: bool = False,
                 udp_port: int = 5555, enable_pipe: bool = True):
        """
        Initialize LED display system

        Args:
            config_path: Path to configuration file
            port: Web API server port
            mock_mode: Run in mock mode (no GPIO hardware required)
            udp_port: UDP port for frame input
            enable_pipe: Enable named pipe frame input
        """
        self.config_path = config_path
        self.port = port
        self.mock_mode = mock_mode
        self.udp_port = udp_port
        self.enable_pipe = enable_pipe

        # Components
        self.config_manager = None
        self.led_driver = None
        self.mapper = None
        self.display_controller = None
        self.udp_receiver = None
        self.pipe_receiver = None
        self.web_api = None

        # Thread coordination
        self.frame_queue = queue.Queue(maxsize=10)
        self.config_reload_event = threading.Event()

        # Shutdown flag
        self.running = False

        logger.info("LED Display System initializing...")

    def initialize(self) -> bool:
        """
        Initialize all components

        Returns:
            True if successful
        """
        try:
            # Load configuration
            logger.info(f"Loading configuration from {self.config_path}")
            self.config_manager = ConfigManager()
            config = self.config_manager.load_config(self.config_path)

            # Calculate LED count
            led_count = self.config_manager.get_total_leds(config)
            width, height = self.config_manager.get_display_dimensions(config)

            logger.info(f"Display: {width}x{height} ({led_count} LEDs)")

            # Initialize LED driver
            if self.mock_mode:
                logger.info("Initializing MOCK LED driver (no hardware)")
                self.led_driver = MockLEDDriver(led_count)
            else:
                logger.info("Initializing hardware LED driver")
                self.led_driver = LEDDriver(led_count, gpio_pin=18, brightness=128)

            # Initialize coordinate mapper
            logger.info("Initializing coordinate mapper")
            self.mapper = CoordinateMapper(config)

            # Initialize display controller
            logger.info("Initializing display controller")
            self.display_controller = DisplayController(
                self.led_driver,
                self.mapper,
                self.frame_queue,
                self.config_reload_event,
                self.config_path,
                target_fps=30
            )

            # Initialize UDP receiver
            if self.udp_port > 0:
                logger.info(f"Initializing UDP frame receiver on port {self.udp_port}")
                self.udp_receiver = UDPFrameReceiver(
                    self.udp_port,
                    self.frame_queue,
                    width,
                    height
                )

            # Initialize pipe receiver
            if self.enable_pipe:
                logger.info("Initializing named pipe frame receiver")
                self.pipe_receiver = PipeFrameReceiver(
                    "/tmp/led_frames.pipe",
                    self.frame_queue,
                    width,
                    height
                )

            # Initialize sleep scheduler
            logger.info("Initializing sleep scheduler")
            self.sleep_scheduler = SleepScheduler(
                set_brightness_callback=self.led_driver.set_brightness,
                get_brightness_callback=self.led_driver.get_brightness
            )
            self.sleep_scheduler.start()

            # Initialize web API
            logger.info(f"Initializing web API server on port {self.port}")
            self.web_api = WebAPIServer(
                self.frame_queue,
                self.config_reload_event,
                self.led_driver,
                self.mapper,
                self.display_controller,
                self.config_path,
                sleep_scheduler=self.sleep_scheduler,
                static_dir="static"
            )

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}", exc_info=True)
            return False

    def start(self) -> None:
        """Start all components"""
        logger.info("Starting LED Display System...")

        try:
            # Start display controller
            self.display_controller.start()

            # Start frame receivers
            if self.udp_receiver:
                self.udp_receiver.start()

            if self.pipe_receiver:
                try:
                    self.pipe_receiver.start()
                except Exception as e:
                    logger.warning(f"Failed to start pipe receiver: {e}")

            # Start web API server (blocking)
            logger.info(f"Starting web server on http://0.0.0.0:{self.port}")
            logger.info(f"Access locally: http://localhost:{self.port}")
            logger.info(f"Access over LAN: http://192.168.1.15:{self.port}")
            logger.info("Or use your device's IP address")

            self.running = True

            # Run web server
            uvicorn.run(
                self.web_api.get_app(),
                host="0.0.0.0",
                port=self.port,
                log_level="info"
            )

        except Exception as e:
            logger.error(f"Error starting system: {e}", exc_info=True)
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown all components gracefully"""
        if not self.running:
            return

        logger.info("Shutting down LED Display System...")
        self.running = False

        # Stop display controller
        if self.display_controller:
            self.display_controller.stop()

        # Stop frame receivers
        if self.udp_receiver:
            self.udp_receiver.stop()

        if self.pipe_receiver:
            self.pipe_receiver.stop()

        # Stop sleep scheduler
        if hasattr(self, 'sleep_scheduler') and self.sleep_scheduler:
            self.sleep_scheduler.stop()

        logger.info("LED Display System shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LED Display Driver - Control 4x 16x16 WS2812B panels via Raspberry Pi GPIO"
    )

    parser.add_argument(
        '--config',
        type=str,
        default='configs/current.json',
        help='Path to configuration file (default: configs/current.json)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Web API server port (default: 8080)'
    )

    parser.add_argument(
        '--mock',
        action='store_true',
        help='Run in mock mode (no GPIO hardware required)'
    )

    parser.add_argument(
        '--udp-port',
        type=int,
        default=5555,
        help='UDP port for frame input (default: 5555, 0 to disable)'
    )

    parser.add_argument(
        '--no-pipe',
        action='store_true',
        help='Disable named pipe frame input'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Print banner
    print("=" * 60)
    print("LED Display Driver v1.0.0")
    print("Raspberry Pi WS2812B Panel Controller")
    print("=" * 60)
    print()

    if args.mock:
        print("⚠️  Running in MOCK MODE - no hardware will be controlled")
        print()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and initialize system
    system = LEDDisplaySystem(
        config_path=args.config,
        port=args.port,
        mock_mode=args.mock,
        udp_port=args.udp_port,
        enable_pipe=not args.no_pipe
    )

    if not system.initialize():
        logger.error("Failed to initialize system")
        sys.exit(1)

    # Start system (blocks until shutdown)
    try:
        system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        system.shutdown()


if __name__ == "__main__":
    main()
