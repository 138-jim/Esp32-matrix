#!/bin/bash

# Installation script for LED Matrix Auto-Updater Service

set -e

echo "Installing LED Matrix Auto-Updater Service..."

# Check if running as root (needed for systemd operations)
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Get the current directory (should be the repo root)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$REPO_DIR/led-matrix-updater.service"
UPDATER_SCRIPT="$REPO_DIR/auto_updater.py"

# Verify files exist
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

if [ ! -f "$UPDATER_SCRIPT" ]; then
    echo "Error: Auto-updater script not found at $UPDATER_SCRIPT"
    exit 1
fi

# Make the auto-updater script executable
chmod +x "$UPDATER_SCRIPT"
echo "Made auto-updater script executable"

# Copy service file to systemd directory
cp "$SERVICE_FILE" /etc/systemd/system/
echo "Copied service file to /etc/systemd/system/"

# Reload systemd daemon
systemctl daemon-reload
echo "Reloaded systemd daemon"

# Enable the service (start on boot)
systemctl enable led-matrix-updater.service
echo "Enabled auto-updater service"

# Start the service
systemctl start led-matrix-updater.service
echo "Started auto-updater service"

# Show service status
echo ""
echo "Service status:"
systemctl status led-matrix-updater.service --no-pager

echo ""
echo "Installation complete!"
echo ""
echo "Useful commands:"
echo "  View logs:        journalctl -u led-matrix-updater.service -f"
echo "  Stop service:     sudo systemctl stop led-matrix-updater.service"
echo "  Start service:    sudo systemctl start led-matrix-updater.service"
echo "  Restart service:  sudo systemctl restart led-matrix-updater.service"
echo "  Disable service:  sudo systemctl disable led-matrix-updater.service"