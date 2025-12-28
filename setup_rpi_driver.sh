#!/bin/bash
# Setup script for LED Display Driver on Raspberry Pi

set -e

echo "================================"
echo "LED Display Driver Setup"
echo "================================"
echo ""

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "The driver will install but GPIO control may not work"
    echo ""
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script should be run with sudo"
    echo "Usage: sudo ./setup_rpi_driver.sh"
    exit 1
fi

echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-dev scons swig git

echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --break-system-packages

echo ""
echo "Setting up GPIO permissions..."
# Add user to gpio group
if getent group gpio > /dev/null 2>&1; then
    usermod -a -G gpio $SUDO_USER
    echo "✓ Added $SUDO_USER to gpio group"
else
    echo "⚠️  gpio group not found, you may need to run with sudo"
fi

# Add user to dialout group (for serial access if needed)
usermod -a -G dialout $SUDO_USER 2>/dev/null || true

echo ""
echo "Creating directories..."
mkdir -p configs/backup
mkdir -p static
mkdir -p logs

# Set ownership
chown -R $SUDO_USER:$SUDO_USER configs logs

echo ""
echo "Making scripts executable..."
chmod +x rpi_driver/main.py

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. LOGOUT AND LOGIN AGAIN for group changes to take effect"
echo ""
echo "2. Run the driver:"
echo "   sudo python3 -m rpi_driver.main --config configs/current.json"
echo ""
echo "3. Or install as systemd service:"
echo "   sudo ./install_service.sh"
echo ""
echo "4. Open web interface:"
echo "   http://$(hostname).local:8080"
echo "   or http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "5. Test in mock mode (no hardware):"
echo "   python3 -m rpi_driver.main --mock"
echo ""
