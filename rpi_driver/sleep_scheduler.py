#!/usr/bin/env python3
"""
Sleep Scheduler for LED Display
Automatically turns display on/off at scheduled times
"""

import logging
import threading
import time
from datetime import datetime, time as dt_time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SleepScheduler:
    """
    Manages sleep schedule for LED display
    Turns display off and on at specified times
    """

    def __init__(self, set_brightness_callback: Callable[[int], None], get_brightness_callback: Callable[[], int]):
        """
        Initialize sleep scheduler

        Args:
            set_brightness_callback: Function to call to set brightness
            get_brightness_callback: Function to get current brightness
        """
        self.set_brightness = set_brightness_callback
        self.get_brightness = get_brightness_callback
        self.enabled = False
        self.off_time: Optional[dt_time] = None  # Time to turn off (e.g., 23:00)
        self.on_time: Optional[dt_time] = None   # Time to turn on (e.g., 07:00)
        self.running = False
        self.thread = None
        self.saved_brightness = 128  # Brightness to restore when waking
        self.is_sleeping = False

        logger.info("Sleep scheduler initialized")

    def set_schedule(self, off_time_str: str, on_time_str: str, enabled: bool = True) -> None:
        """
        Set sleep schedule

        Args:
            off_time_str: Time to turn off in HH:MM format (24-hour)
            on_time_str: Time to turn on in HH:MM format (24-hour)
            enabled: Whether schedule is enabled
        """
        try:
            # Parse time strings
            off_hour, off_minute = map(int, off_time_str.split(':'))
            on_hour, on_minute = map(int, on_time_str.split(':'))

            self.off_time = dt_time(off_hour, off_minute)
            self.on_time = dt_time(on_hour, on_minute)
            self.enabled = enabled

            logger.info(f"Sleep schedule set: Off at {off_time_str}, On at {on_time_str}, "
                       f"Enabled: {enabled}")

        except Exception as e:
            logger.error(f"Error setting sleep schedule: {e}")
            raise ValueError(f"Invalid time format. Use HH:MM (24-hour)")

    def get_schedule(self) -> dict:
        """Get current schedule"""
        return {
            "enabled": self.enabled,
            "off_time": self.off_time.strftime("%H:%M") if self.off_time else None,
            "on_time": self.on_time.strftime("%H:%M") if self.on_time else None,
            "is_sleeping": self.is_sleeping
        }

    def start(self) -> None:
        """Start the scheduler thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()
            logger.info("Sleep scheduler started")

    def stop(self) -> None:
        """Stop the scheduler thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=2.0)
            logger.info("Sleep scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop (runs in background thread)"""
        while self.running:
            try:
                if self.enabled and self.off_time and self.on_time:
                    current_time = datetime.now().time()

                    # Check if it's time to sleep
                    if self._should_sleep(current_time):
                        if not self.is_sleeping:
                            logger.info(f"Sleep time - turning off display at {current_time.strftime('%H:%M:%S')}")
                            self.saved_brightness = self.get_brightness()  # Save current brightness
                            logger.info(f"Saved brightness: {self.saved_brightness}")
                            self.set_brightness(0)
                            self.is_sleeping = True

                    # Check if it's time to wake
                    elif self._should_wake(current_time):
                        if self.is_sleeping:
                            logger.info(f"Wake time - turning on display at {current_time.strftime('%H:%M:%S')}")
                            logger.info(f"Restoring brightness to: {self.saved_brightness}")
                            self.set_brightness(self.saved_brightness)
                            self.is_sleeping = False

                # Check every 30 seconds
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

    def _should_sleep(self, current_time: dt_time) -> bool:
        """Check if display should be sleeping"""
        if not self.off_time or not self.on_time:
            return False

        # Handle schedules that span midnight
        if self.off_time > self.on_time:
            # Schedule spans midnight (e.g., off at 23:00, on at 07:00)
            # Sleep when: current >= 23:00 OR current < 07:00
            return current_time >= self.off_time or current_time < self.on_time
        else:
            # Schedule within same day (e.g., off at 01:00, on at 06:00)
            # Sleep when: 01:00 <= current < 06:00
            return self.off_time <= current_time < self.on_time

    def _should_wake(self, current_time: dt_time) -> bool:
        """Check if display should be awake"""
        if not self.off_time or not self.on_time:
            return True  # If no schedule, always awake

        # Inverse of should_sleep
        return not self._should_sleep(current_time)
