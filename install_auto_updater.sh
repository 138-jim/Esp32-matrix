#!/bin/bash
# Install Auto-Updater Service

set -e

echo "Installing Auto-Updater Service..."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run with sudo"
    echo "Usage: sudo ./install_auto_updater.sh"
    exit 1
fi

# Get the current directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$REPO_DIR/auto-updater.service"

# Check if service file exists
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Update WorkingDirectory and ExecStart in service file to current location
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO_DIR|" "$SERVICE_FILE"
sed -i "s|ExecStart=.*|ExecStart=/usr/bin/python3 $REPO_DIR/auto_updater.py --repo-path $REPO_DIR --service led-driver.service --interval 30|" "$SERVICE_FILE"

# Copy service file to systemd directory
cp "$SERVICE_FILE" /etc/systemd/system/
echo "✓ Copied service file to /etc/systemd/system/"

# Reload systemd daemon
systemctl daemon-reload
echo "✓ Reloaded systemd daemon"

# Enable the service (start on boot)
systemctl enable auto-updater.service
echo "✓ Enabled service to start on boot"

# Start the service
systemctl start auto-updater.service
echo "✓ Started service"

# Show service status
echo ""
echo "Service status:"
systemctl status auto-updater.service --no-pager

echo ""
echo "================================"
echo "Auto-Updater Installation Complete!"
echo "================================"
echo ""
echo "The auto-updater will now:"
echo "  - Check for git updates every 30 seconds"
echo "  - Automatically pull changes from GitHub"
echo "  - Restart led-driver.service when code changes"
echo ""
echo "Useful commands:"
echo ""
echo "  View logs:        sudo journalctl -u auto-updater.service -f"
echo "  Stop service:     sudo systemctl stop auto-updater.service"
echo "  Start service:    sudo systemctl start auto-updater.service"
echo "  Restart service:  sudo systemctl restart auto-updater.service"
echo "  Disable service:  sudo systemctl disable auto-updater.service"
echo "  Service status:   sudo systemctl status auto-updater.service"
echo ""
