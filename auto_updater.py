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
                 target_script: str = "led_matrix_controller.py",
                 check_interval: int = 30,
                 log_file: str = "/tmp/auto_updater.log"):
        
        self.repo_path = Path(repo_path)
        self.target_script = target_script
        self.check_interval = check_interval
        self.log_file = log_file
        self.current_process = None
        self.current_commit = None
        self.running = True
        
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
        if self.current_process:
            self._stop_current_process()
    
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
            
            # Check if target script was modified
            if self.current_commit and remote_commit != self.current_commit:
                # Check if our target script was modified in the new commits
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{self.current_commit}..{remote_commit}"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                changed_files = result.stdout.strip().split('\n')
                target_changed = any(self.target_script in file for file in changed_files)
                
                if target_changed:
                    self.logger.info(f"Target script {self.target_script} updated in commit {remote_commit}")
                    return True
                else:
                    self.logger.info(f"New commit {remote_commit} found, but target script unchanged")
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
    
    def _stop_current_process(self):
        """Stop the currently running script process"""
        if self.current_process and self.current_process.poll() is None:
            self.logger.info("Stopping current process...")
            self.current_process.terminate()
            
            # Wait up to 10 seconds for graceful shutdown
            try:
                self.current_process.wait(timeout=10)
                self.logger.info("Process stopped gracefully")
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't stop gracefully, killing...")
                self.current_process.kill()
                self.current_process.wait()
            
            self.current_process = None
    
    def _start_script(self) -> bool:
        """Start the target script"""
        script_path = self.repo_path / self.target_script
        
        if not script_path.exists():
            self.logger.error(f"Target script {script_path} does not exist")
            return False
        
        try:
            # Make sure script is executable
            os.chmod(script_path, 0o755)
            
            # Start the script
            self.current_process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )
            
            self.logger.info(f"Started {self.target_script} with PID {self.current_process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start script: {e}")
            return False
    
    def _check_script_health(self) -> bool:
        """Check if the current script is still running"""
        if not self.current_process:
            return False
        
        poll_result = self.current_process.poll()
        if poll_result is not None:
            self.logger.warning(f"Script exited with code {poll_result}")
            return False
        
        return True
    
    def run(self):
        """Main update loop"""
        self.logger.info("Auto-updater starting...")
        
        # Get initial commit
        self.current_commit = self._get_current_commit()
        if not self.current_commit:
            self.logger.error("Failed to get initial commit, exiting")
            return
        
        self.logger.info(f"Starting with commit {self.current_commit}")
        
        # Start initial script
        if not self._start_script():
            self.logger.error("Failed to start initial script, exiting")
            return
        
        # Main monitoring loop
        while self.running:
            try:
                # Check if script is still running
                if not self._check_script_health():
                    self.logger.info("Script not running, restarting...")
                    if not self._start_script():
                        self.logger.error("Failed to restart script")
                        time.sleep(self.check_interval)
                        continue
                
                # Check for updates
                if self._check_for_updates():
                    self.logger.info("Updates found, restarting script...")
                    
                    # Stop current process
                    self._stop_current_process()
                    
                    # Pull updates
                    if self._pull_updates():
                        # Start new version
                        if not self._start_script():
                            self.logger.error("Failed to start updated script")
                    else:
                        self.logger.error("Failed to pull updates, restarting old version")
                        self._start_script()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.check_interval)
        
        # Cleanup
        self._stop_current_process()
        self.logger.info("Auto-updater stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-updater for LED Matrix Controller")
    parser.add_argument("--repo-path", default="/home/jim/Esp32-matrix", 
                       help="Path to git repository")
    parser.add_argument("--script", default="led_matrix_controller.py",
                       help="Target script to monitor and restart")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds")
    parser.add_argument("--log-file", default="/tmp/auto_updater.log",
                       help="Log file path")
    
    args = parser.parse_args()
    
    updater = AutoUpdater(
        repo_path=args.repo_path,
        target_script=args.script,
        check_interval=args.interval,
        log_file=args.log_file
    )
    
    updater.run()

if __name__ == "__main__":
    main()