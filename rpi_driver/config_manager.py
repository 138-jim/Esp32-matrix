#!/usr/bin/env python3
"""
Configuration Manager for LED Panel System
Handles loading, saving, validating, and backing up panel configurations
"""

import json
import os
import shutil
from datetime import datetime
from typing import Tuple, Dict, Any
from pathlib import Path


class ConfigManager:
    """Manages panel configuration files with validation and backup"""

    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir / "backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If config fails validation
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate configuration
        is_valid, error_msg = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {error_msg}")

        return config

    def save_config(self, config: Dict[str, Any], config_path: str,
                   create_backup: bool = True) -> None:
        """
        Save configuration to JSON file

        Args:
            config: Configuration dictionary
            config_path: Path to save configuration
            create_backup: If True, backup existing file before overwriting

        Raises:
            ValueError: If config fails validation
        """
        # Validate before saving
        is_valid, error_msg = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Cannot save invalid configuration: {error_msg}")

        config_path = Path(config_path)

        # Create backup of existing config
        if create_backup and config_path.exists():
            self.backup_config(config_path)

        # Save config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def backup_config(self, config_path: Path) -> Path:
        """
        Create timestamped backup of configuration file

        Args:
            config_path: Path to configuration file to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_path.stem}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(config_path, backup_path)

        # Keep only last 10 backups
        self._cleanup_old_backups(max_backups=10)

        return backup_path

    def _cleanup_old_backups(self, max_backups: int = 10):
        """Remove old backup files, keeping only the most recent"""
        backups = sorted(self.backup_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)

        # Remove oldest backups if we exceed max_backups
        while len(backups) > max_backups:
            oldest = backups.pop(0)
            oldest.unlink()

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate panel configuration

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required top-level keys
        required_keys = ['grid', 'panels']
        for key in required_keys:
            if key not in config:
                return False, f"Missing required key: '{key}'"

        # Validate grid configuration
        grid = config['grid']
        grid_required = ['grid_width', 'grid_height', 'panel_width', 'panel_height']
        for key in grid_required:
            if key not in grid:
                return False, f"Missing required grid key: '{key}'"
            if not isinstance(grid[key], int) or grid[key] <= 0:
                return False, f"Grid '{key}' must be a positive integer"

        # Validate panels
        panels = config['panels']
        if not isinstance(panels, list):
            return False, "'panels' must be a list"

        if len(panels) == 0:
            return False, "Configuration must have at least one panel"

        # Check for duplicate panel IDs
        panel_ids = [p.get('id') for p in panels]
        if len(panel_ids) != len(set(panel_ids)):
            return False, "Duplicate panel IDs found"

        # Validate each panel
        for i, panel in enumerate(panels):
            # Check required panel keys
            panel_required = ['id', 'position', 'rotation']
            for key in panel_required:
                if key not in panel:
                    return False, f"Panel {i}: Missing required key '{key}'"

            # Validate panel ID
            if not isinstance(panel['id'], int) or panel['id'] < 0:
                return False, f"Panel {i}: 'id' must be a non-negative integer"

            # Validate position
            position = panel['position']
            if not isinstance(position, list) or len(position) != 2:
                return False, f"Panel {i}: 'position' must be a list of [x, y]"

            pos_x, pos_y = position
            if not isinstance(pos_x, int) or not isinstance(pos_y, int):
                return False, f"Panel {i}: position coordinates must be integers"

            if pos_x < 0 or pos_y < 0:
                return False, f"Panel {i}: position coordinates must be non-negative"

            if pos_x >= grid['grid_width'] or pos_y >= grid['grid_height']:
                return False, f"Panel {i}: position {position} exceeds grid dimensions"

            # Validate rotation
            rotation = panel['rotation']
            valid_rotations = [0, 90, 180, 270]
            if rotation not in valid_rotations:
                return False, f"Panel {i}: rotation must be one of {valid_rotations}"

        # Check for overlapping panels
        panel_positions = [(p['position'][0], p['position'][1]) for p in panels]
        if len(panel_positions) != len(set(panel_positions)):
            return False, "Panels have overlapping positions"

        return True, ""

    def get_display_dimensions(self, config: Dict[str, Any]) -> Tuple[int, int]:
        """
        Calculate total display dimensions from configuration

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (width, height) in pixels
        """
        grid = config['grid']
        width = grid['grid_width'] * grid['panel_width']
        height = grid['grid_height'] * grid['panel_height']
        return width, height

    def get_total_leds(self, config: Dict[str, Any]) -> int:
        """
        Calculate total number of LEDs from configuration

        Args:
            config: Configuration dictionary

        Returns:
            Total number of LEDs
        """
        grid = config['grid']
        leds_per_panel = grid['panel_width'] * grid['panel_height']
        return len(config['panels']) * leds_per_panel


# Convenience functions
def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file"""
    manager = ConfigManager()
    return manager.load_config(config_path)


def save_config(config: Dict[str, Any], config_path: str,
               create_backup: bool = True) -> None:
    """Save configuration to file"""
    manager = ConfigManager()
    manager.save_config(config, config_path, create_backup)


def validate_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate configuration"""
    manager = ConfigManager()
    return manager.validate_config(config)
