# Netgear LM1200 SMS Gateway

[![Release](https://img.shields.io/github/v/release/fidpa/netgear-lm1200-sms-gateway?style=flat-square)](https://github.com/fidpa/netgear-lm1200-sms-gateway/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![CI](https://github.com/fidpa/netgear-lm1200-sms-gateway/actions/workflows/lint.yml/badge.svg)](https://github.com/fidpa/netgear-lm1200-sms-gateway/actions/workflows/lint.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux&logoColor=white)](https://www.linux.org/)
[![Netgear LM1200](https://img.shields.io/badge/Netgear-LM1200-blue?style=flat-square)](https://www.netgear.com/home/mobile-wifi/lte-modems/lm1200/)
[![Maintenance](https://img.shields.io/badge/Maintained-yes-brightgreen?style=flat-square)](https://github.com/fidpa/netgear-lm1200-sms-gateway/commits/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

> Automated SMS reception and forwarding for Netgear LM1200 4G LTE Modem — 2FA/OTP codes directly to Telegram.

## ⚡ Features

- 📱 Automatic SMS polling (every 5 minutes via systemd timer)
- 📨 Optional Telegram forwarding for 2FA/OTP codes
- 💾 Local JSON storage (monthly rotated files)
- 🔄 State management (no duplicates, no lost messages)
- 🔒 Hash-based deduplication (robust against ID resets)
- 🐍 Python 3.10+ with async/await
- 🔒 systemd security hardening
- 🔐 **Optional SMS Encryption** (AES-256 via Fernet)
- 🔄 **Retry Logic** (exponential backoff for transient errors)
- 🏥 **Health-Check Endpoint** (monitoring integration)

## 🚨 Critical: Germany-Specific Setup

**IMPORTANT**: SMS reception requires specific modem configuration:

1. ✅ Network Mode: "Auto" (NOT "LTE Only"!)
2. ✅ SMS Alerts: Enabled in modem settings

Without these settings, SMS will NOT be received. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for details.

## 🚀 Quick Start

### Prerequisites

- Netgear LM1200 4G LTE Modem with active SIM card
- Linux system with Python 3.10+ and systemd
- `jq` command-line JSON processor (for SMS parsing)
- (Optional) Telegram Bot Token for SMS forwarding

Install `jq`:
```bash
# Debian/Ubuntu
sudo apt install jq

# RHEL/Fedora
sudo dnf install jq
```

### Installation

1. Clone repository:
   ```bash
   git clone https://github.com/fidpa/netgear-lm1200-sms-gateway
   cd netgear-lm1200-sms-gateway
   ```

2. Install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure modem (CRITICAL!):
   - Open modem web UI: http://192.168.0.201
   - Set Network Mode to "Auto" (Network → LTE Settings → Band Selection)
   - Enable SMS Alerts (Settings → General → Alerts → "On")

4. Create configuration:
   ```bash
   sudo mkdir -p /etc/netgear-sms-gateway
   sudo cp config/config.example.env /etc/netgear-sms-gateway/config.env
   sudo nano /etc/netgear-sms-gateway/config.env
   ```

5. Install systemd units:
   ```bash
   sudo cp systemd/*.{service,timer} /etc/systemd/system/

   # IMPORTANT: Edit service file and replace YOUR_USERNAME with your actual username
   sudo nano /etc/systemd/system/netgear-sms-poller.service
   # Change: User=YOUR_USERNAME → User=yourname
   # Change: Group=YOUR_USERNAME → Group=yourname

   sudo systemctl daemon-reload
   sudo systemctl enable --now netgear-sms-poller.timer
   ```

6. Create symlink (REQUIRED):
   ```bash
   sudo ln -sf "$(pwd)/src/netgear_sms_wrapper.sh" /usr/local/bin/netgear-sms-poller
   ```

7. Test:
   ```bash
   # Send test SMS to modem SIM card
   # Wait 5 minutes or trigger manually:
   sudo systemctl start netgear-sms-poller.service

   # Check logs:
   journalctl -u netgear-sms-poller.service -n 50
   ```

## 📖 Documentation

- [Documentation Index](docs/README.md) - Overview & quick links
- [Setup Guide](docs/SETUP.md) - Detailed installation & configuration
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues & solutions

## 🔧 Configuration

### Minimal (SMS Storage Only)

```env
# /etc/netgear-sms-gateway/config.env
NETGEAR_IP=192.168.0.201
NETGEAR_ADMIN_PASSWORD=your_admin_password
SMS_STATE_DIR=/var/lib/netgear-sms-gateway
```

### Optional (With Telegram Forwarding)

```env
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=12345678
TELEGRAM_PREFIX="[SMS Gateway]"
RATE_LIMIT_SECONDS=300
```

### Advanced Configuration

#### Debug Logging
```env
LOG_LEVEL=DEBUG  # Shows detailed hash checks, ID comparisons
```

#### SMS Encryption (Optional)

**Requires:** `pip install cryptography>=42.0.0`

```env
SMS_ENCRYPTION_ENABLED=true
SMS_ENCRYPTION_KEY_FILE=/etc/netgear-sms-gateway/.encryption.key
```

Generate key: `./src/netgear_sms_poller.py generate-key`

See [docs/ENCRYPTION.md](docs/ENCRYPTION.md) for full guide.

**Note:** Gateway works without encryption - install only if you need this feature.

#### Health Check
```bash
./src/netgear_sms_poller.py health
# Returns: 0 (healthy), 1 (degraded), 2 (down)
```

See [docs/MONITORING.md](docs/MONITORING.md) for integration examples.

## 🛡️ Security

- Credentials stored in `/etc/netgear-sms-gateway/config.env` (chmod 600)
- systemd sandboxing: ProtectSystem=strict, PrivateTmp=yes
- SMS content stored in `/var/lib/netgear-sms-gateway/` (restricted access)

For vulnerability reporting and security best practices, see [SECURITY.md](SECURITY.md).

## 📊 Use Cases

- ✅ 2FA/OTP code reception (banking, services)
- ✅ Automated SMS backup/archival
- ✅ SMS-to-Telegram bridge for mobile access
- ✅ Home automation SMS triggers

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [svbnet/netgear-sms](https://github.com/svbnet/netgear-sms) - SMS API for Netgear LTE modems
- [Home Assistant NETGEAR LTE Integration](https://www.home-assistant.io/integrations/netgear_lte/)
