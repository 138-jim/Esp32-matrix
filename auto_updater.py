#!/usr/bin/env python3
"""
Auto-updater script for Raspberry Pi LED Matrix Controller
Monitors git repository for changes and automatically restarts the controller
"""

import os
import sys
import subprocess
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

class AutoUpdater:
    def __init__(self,
                 repo_path: str = "/home/jim/Esp32-matrix",
                 service_name: str = "led-driver.service",
                 check_interval: int = 30,
                 log_file: str = "/tmp/auto_updater.log",
                 watch_paths: list = None):

        self.repo_path = Path(repo_path)
        self.service_name = service_name
        self.check_interval = check_interval
        self.log_file = log_file
        self.current_commit = None
        self.running = True

        # Paths to watch for changes (if any of these change, restart)
        self.watch_paths = watch_paths or [
            "rpi_driver/",
            "static/",
            "configs/",
            "requirements.txt"
        ]
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _get_current_commit(self) -> str:
        """Get the current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get current commit: {e}")
            return None
    
    def _check_for_updates(self) -> bool:
        """Check if there are new commits on the remote"""
        try:
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            
            # Get remote commit hash
            result = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            remote_commit = result.stdout.strip()
            
            # Check if watched paths were modified
            if self.current_commit and remote_commit != self.current_commit:
                # Check if any watched paths were modified in the new commits
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{self.current_commit}..{remote_commit}"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                changed_files = result.stdout.strip().split('\n')

                # Check if any changed file is in our watch paths
                relevant_change = False
                for changed_file in changed_files:
                    for watch_path in self.watch_paths:
                        if changed_file.startswith(watch_path):
                            relevant_change = True
                            self.logger.info(f"Watched file changed: {changed_file}")
                            break
                    if relevant_change:
                        break

                if relevant_change:
                    self.logger.info(f"Relevant changes detected in commit {remote_commit}")
                    return True
                else:
                    self.logger.info(f"New commit {remote_commit} found, but no watched paths changed")
                    self.current_commit = remote_commit
                    return False
            
            return remote_commit != self.current_commit
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return False
    
    def _pull_updates(self) -> bool:
        """Pull the latest changes from git"""
        try:
            subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            self.current_commit = self._get_current_commit()
            self.logger.info(f"Successfully pulled updates, now at commit {self.current_commit}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to pull updates: {e}")
            return False
    
    def _restart_service(self) -> bool:
        """Restart the systemd service"""
        try:
            self.logger.info(f"Restarting service {self.service_name}...")
            subprocess.run(
                ["sudo", "systemctl", "restart", self.service_name],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            self.logger.info(f"Service {self.service_name} restarted successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to restart service: {e}")
            return False

    def _check_service_health(self) -> bool:
        """Check if the systemd service is running"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.service_name],
                capture_output=True,
                text=True
            )
            is_active = result.stdout.strip() == "active"
            if not is_active:
                self.logger.warning(f"Service {self.service_name} is not active: {result.stdout.strip()}")
            return is_active
        except Exception as e:
            self.logger.error(f"Failed to check service health: {e}")
            return False
    
    def run(self):
        """Main update loop"""
        self.logger.info("Auto-updater starting...")
        self.logger.info(f"Monitoring service: {self.service_name}")
        self.logger.info(f"Watching paths: {', '.join(self.watch_paths)}")

        # Get initial commit
        self.current_commit = self._get_current_commit()
        if not self.current_commit:
            self.logger.error("Failed to get initial commit, exiting")
            return

        self.logger.info(f"Starting with commit {self.current_commit}")

        # Check if service is running
        if not self._check_service_health():
            self.logger.warning("Service not running at startup")

        # Main monitoring loop
        while self.running:
            try:
                # Check if service is still running
                if not self._check_service_health():
                    self.logger.info("Service not running, attempting restart...")
                    if not self._restart_service():
                        self.logger.error("Failed to restart service")
                        time.sleep(self.check_interval)
                        continue

                # Check for updates
                if self._check_for_updates():
                    self.logger.info("Updates found, pulling and restarting...")

                    # Pull updates
                    if self._pull_updates():
                        # Restart service with new code
                        if not self._restart_service():
                            self.logger.error("Failed to restart service with updates")
                    else:
                        self.logger.error("Failed to pull updates")

                # Wait before next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.check_interval)

        self.logger.info("Auto-updater stopped")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-updater for LED Display Driver")
    parser.add_argument("--repo-path", default="/home/jim/Esp32-matrix",
                       help="Path to git repository")
    parser.add_argument("--service", default="led-driver.service",
                       help="Systemd service name to monitor and restart")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds")
    parser.add_argument("--log-file", default="/tmp/auto_updater.log",
                       help="Log file path")
    parser.add_argument("--watch-paths", nargs="+",
                       default=["rpi_driver/", "static/", "configs/", "requirements.txt"],
                       help="Paths to watch for changes")

    args = parser.parse_args()

    updater = AutoUpdater(
        repo_path=args.repo_path,
        service_name=args.service,
        check_interval=args.interval,
        log_file=args.log_file,
        watch_paths=args.watch_paths
    )

    updater.run()

if __name__ == "__main__":
    main()