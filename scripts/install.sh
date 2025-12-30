#!/bin/bash
# Simple installation helper for netgear-lm1200-sms-gateway
#
# Version: 1.0.0
# Created: 2025-12-30

set -euo pipefail

echo "=== Netgear LM1200 SMS Gateway Installer ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Please install Python 3.10 or higher."
    exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
    echo "ERROR: systemd not found. This script requires systemd."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "WARNING: jq not found. Install jq for easier SMS debugging."
fi

echo "✓ Prerequisites OK"
echo ""

# Detect repository directory
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Repository: ${REPO_DIR}"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
cd "${REPO_DIR}"

if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Create state directory
echo "Creating state directory..."
sudo mkdir -p /var/lib/netgear-sms-gateway
sudo chown "$USER:$USER" /var/lib/netgear-sms-gateway
echo "✓ State directory created: /var/lib/netgear-sms-gateway"
echo ""

# Install configuration
echo "Installing configuration..."
sudo mkdir -p /etc/netgear-sms-gateway

if [[ ! -f /etc/netgear-sms-gateway/config.env ]]; then
    sudo cp "${REPO_DIR}/config/config.example.env" /etc/netgear-sms-gateway/config.env
    sudo chown root:root /etc/netgear-sms-gateway/config.env
    sudo chmod 600 /etc/netgear-sms-gateway/config.env
    echo "✓ Config file created: /etc/netgear-sms-gateway/config.env"
    echo "⚠️  IMPORTANT: Edit config file with your credentials!"
else
    echo "⚠️  Config already exists, skipping (keeping existing config)"
fi
echo ""

# Install systemd units
echo "Installing systemd units..."
sudo cp "${REPO_DIR}/systemd/netgear-sms-poller.service" /etc/systemd/system/
sudo cp "${REPO_DIR}/systemd/netgear-sms-poller.timer" /etc/systemd/system/

# Update user in service file
sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/netgear-sms-poller.service

echo "✓ systemd units installed"
echo ""

# Install symlink
echo "Creating symlink..."
sudo ln -sf "${REPO_DIR}/src/netgear_sms_wrapper.sh" /usr/local/bin/netgear-sms-poller
sudo chmod +x "${REPO_DIR}/src/netgear_sms_wrapper.sh"
echo "✓ Symlink created: /usr/local/bin/netgear-sms-poller"
echo ""

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "✓ systemd reloaded"
echo ""

# Print next steps
echo "═══════════════════════════════════════════════════════════"
echo "✅ Installation complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "⚠️  CRITICAL: Configure modem BEFORE enabling service!"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure modem (MANDATORY!):"
echo "   - Open: http://192.168.0.201"
echo "   - Set Network Mode to 'Auto' (NOT 'LTE Only'!)"
echo "     → Network → LTE Settings → Band Selection → Auto"
echo "   - Enable SMS Alerts: Settings → General → Alerts → On"
echo ""
echo "2. Edit configuration file:"
echo "   sudo nano /etc/netgear-sms-gateway/config.env"
echo ""
echo "   Required settings:"
echo "     NETGEAR_IP=192.168.0.201"
echo "     NETGEAR_ADMIN_PASSWORD=your_admin_password"
echo ""
echo "   Optional (Telegram forwarding):"
echo "     TELEGRAM_BOT_TOKEN=your_bot_token"
echo "     TELEGRAM_CHAT_ID=your_chat_id"
echo ""
echo "3. Enable and start timer:"
echo "   sudo systemctl enable --now netgear-sms-poller.timer"
echo ""
echo "4. Test manually:"
echo "   sudo systemctl start netgear-sms-poller.service"
echo "   journalctl -u netgear-sms-poller.service -n 50"
echo ""
echo "5. Send test SMS to modem SIM card and wait 5 minutes"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Documentation:"
echo "  - Setup Guide:        ${REPO_DIR}/docs/SETUP.md"
echo "  - API Reference:      ${REPO_DIR}/docs/API_REFERENCE.md"
echo "  - Troubleshooting:    ${REPO_DIR}/docs/TROUBLESHOOTING.md"
echo ""
echo "═══════════════════════════════════════════════════════════"
