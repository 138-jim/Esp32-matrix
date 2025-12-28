#!/bin/bash
# Install LED Display Driver as systemd service

set -e

echo "Installing LED Display Driver Service..."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run with sudo"
    echo "Usage: sudo ./install_service.sh"
    exit 1
fi

# Get the current directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$REPO_DIR/led-driver.service"

# Check if service file exists
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Update WorkingDirectory in service file to current location
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO_DIR|" "$SERVICE_FILE"

# Copy service file to systemd directory
cp "$SERVICE_FILE" /etc/systemd/system/
echo "✓ Copied service file to /etc/systemd/system/"

# Reload systemd daemon
systemctl daemon-reload
echo "✓ Reloaded systemd daemon"

# Enable the service (start on boot)
systemctl enable led-driver.service
echo "✓ Enabled service to start on boot"

# Start the service
systemctl start led-driver.service
echo "✓ Started service"

# Show service status
echo ""
echo "Service status:"
systemctl status led-driver.service --no-pager

echo ""
echo "================================"
echo "Service Installation Complete!"
echo "================================"
echo ""
echo "Useful commands:"
echo ""
echo "  View logs:        sudo journalctl -u led-driver.service -f"
echo "  Stop service:     sudo systemctl stop led-driver.service"
echo "  Start service:    sudo systemctl start led-driver.service"
echo "  Restart service:  sudo systemctl restart led-driver.service"
echo "  Disable service:  sudo systemctl disable led-driver.service"
echo "  Service status:   sudo systemctl status led-driver.service"
echo ""
echo "Web interface:"
echo "  http://$(hostname).local:8080"
echo "  or http://$(hostname -I | awk '{print $1}'):8080"
echo ""
