#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/gtm-gateway"
LOG_DIR="/var/log/gtm-gateway/sessions"
SERVICE_USER="gtm"

echo "=== GTM Telemetry Gateway — Install ==="

# Create service user if it doesn't exist
if ! id -u "$SERVICE_USER" &>/dev/null; then
    echo "Creating user $SERVICE_USER..."
    sudo useradd --system --shell /usr/sbin/nologin --home-dir "$INSTALL_DIR" "$SERVICE_USER"
    sudo usermod -aG dialout "$SERVICE_USER"
fi

# Create directories
echo "Creating directories..."
sudo mkdir -p "$INSTALL_DIR" "$LOG_DIR"
sudo chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"

# Copy gateway files
echo "Installing gateway to $INSTALL_DIR..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo cp -r "$SCRIPT_DIR/gateway" "$INSTALL_DIR/"
sudo cp "$SCRIPT_DIR/run_gateway.py" "$INSTALL_DIR/"
sudo cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

# Copy shared protocol (needed for canonical decode)
sudo mkdir -p "$INSTALL_DIR/lib"
sudo cp -r "$SCRIPT_DIR/../shared" "$INSTALL_DIR/lib/"

# Set up Python venv
echo "Setting up Python venv..."
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/.venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# Install systemd service
echo "Installing systemd service..."
sudo cp "$SCRIPT_DIR/systemd/gtm-gateway.service" /etc/systemd/system/
sudo systemctl daemon-reload

# Install logrotate config
if [ -d /etc/logrotate.d ]; then
    echo "Installing logrotate config..."
    sudo cp "$SCRIPT_DIR/systemd/gtm-gateway-logrotate.conf" /etc/logrotate.d/gtm-gateway
fi

echo ""
echo "=== Install complete ==="
echo "  Enable:  sudo systemctl enable gtm-gateway"
echo "  Start:   sudo systemctl start gtm-gateway"
echo "  Status:  sudo systemctl status gtm-gateway"
echo "  Logs:    sudo journalctl -u gtm-gateway -f"
echo "  API:     curl http://localhost:8420/health"
