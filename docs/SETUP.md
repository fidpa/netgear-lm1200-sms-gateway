# Netgear LM1200 SMS Gateway Setup Guide

**Version**: 1.0.0
**Date**: 2025-12-30
**Status**: ✅ Production Ready

## ⚡ TL;DR (20 words)

SMS Gateway for Netgear LM1200: Automatic forwarding of 2FA/OTP codes via Telegram every 5 minutes.

## 🎯 Essential Context (100 words)

The Netgear LM1200 LTE modem can receive SMS, even though no SMS UI is available in the web interface. This guide describes the complete setup of an SMS gateway service that:

- Polls SMS from the modem every 5 minutes (authenticated API)
- Automatically forwards new SMS via Telegram (ideal for 2FA/OTP codes)
- Stores SMS locally in monthly rotated JSON files (backup/history)
- Uses state management (no duplicates, no lost SMS)

**Use Case**: Automatically receive 2FA/OTP codes from banking, services etc. on Telegram, even when away from home.

---

<details>
<summary>📖 Complete Guide (click to expand)</summary>

## 📋 Prerequisites

### Hardware
- Netgear LM1200 4G LTE Modem (with SIM card)
- Linux system with Python 3.10+ and systemd

### Software
- Python 3.10+ with aiohttp (installed via venv)
- systemd (already present)
- `jq` command-line JSON processor (for SMS parsing)
- Optional: Telegram Bot Token for SMS forwarding

**Install jq:**
```bash
# Debian/Ubuntu
sudo apt install jq

# RHEL/Fedora
sudo dnf install jq
```

### Credentials
- **NETGEAR_ADMIN_PASSWORD**: Admin password for LM1200
- **Telegram Bot Token**: For SMS forwarding (optional)
- **Telegram Chat ID**: Target chat for SMS alerts (optional)

---

## 🚨 CRITICAL Modem Configuration (DO THIS FIRST!)

**⚠️ IMPORTANT:** Without these steps, SMS reception will NOT work!

### 1. Set Network Mode to "Auto"

**Problem:**
- "LTE Only" mode blocks SMS reception in Germany
- 3G was shut down in 2021 (Telekom/Vodafone/O2)
- 1&1 doesn't fully support SMS over LTE (IMS/VoLTE)
- **Without "Auto" mode, NO SMS will be received!**

**Solution:**

1. Open LM1200 Web UI: `http://192.168.0.201`
2. Login with admin password
3. Navigation: **Network → LTE Settings → Band Selection**
4. Set **"Auto"** (NOT "LTE Only"!)
5. Click **Apply**
6. Wait ~30 seconds for reconnect

**Verification:**
```bash
# Check API (should show "Auto", not "Only4G")
curl -s http://192.168.0.201/api/model.json | jq '.wwan.bandRegion[] | select(.current == true) | .name'
# Expected: "Auto"
```

### 2. Enable SMS Alerts

**Problem:**
- SMS subsystem only becomes active when alerts are configured
- Default is "Off" or no target number

**Solution:**

1. Open LM1200 Web UI: `http://192.168.0.201`
2. Login with admin password
3. Navigation: **Settings → General → Alerts**
4. Set radio button to **"On"**
5. (Optional) Enter a target number (can be arbitrary)
6. Click **Submit**

**Verification:**
```bash
# Check API (should show true)
curl -s http://192.168.0.201/api/model.json | jq '.sms.alertEnabled'
# Expected: true
```

**After these steps:**
- Send a test SMS to the modem number
- Wait 1-2 minutes
- SMS should now be visible in `/api/model.json`

---

## 🚀 Installation & Deployment

### 1. Clone Repository

```bash
git clone https://github.com/fidpa/netgear-lm1200-sms-gateway
cd netgear-lm1200-sms-gateway
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Modem (CRITICAL!)

Follow the steps in "CRITICAL Modem Configuration" above.

### 4. Create Configuration

```bash
sudo mkdir -p /etc/netgear-sms-gateway
sudo cp config/config.example.env /etc/netgear-sms-gateway/config.env
sudo nano /etc/netgear-sms-gateway/config.env
```

**Required settings:**
```env
NETGEAR_IP=192.168.0.201
NETGEAR_ADMIN_PASSWORD=your_admin_password
SMS_STATE_DIR=/var/lib/netgear-sms-gateway
```

**Optional (Telegram):**
```env
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=12345678
TELEGRAM_PREFIX="[SMS Gateway]"
RATE_LIMIT_SECONDS=300
```

### 5. Create State Directory

```bash
sudo mkdir -p /var/lib/netgear-sms-gateway
sudo chown $USER:$USER /var/lib/netgear-sms-gateway
```

### 6. Install systemd Units

```bash
sudo cp systemd/*.{service,timer} /etc/systemd/system/

# Update user in service file
sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/netgear-sms-poller.service

sudo systemctl daemon-reload
sudo systemctl enable --now netgear-sms-poller.timer
```

### 7. Create Symlink (REQUIRED)

**⚠️ The systemd service expects the wrapper at `/usr/local/bin/netgear-sms-poller`!**

```bash
sudo ln -sf "$(pwd)/src/netgear_sms_wrapper.sh" /usr/local/bin/netgear-sms-poller
```

Alternative: Adjust `ExecStart` in `/etc/systemd/system/netgear-sms-poller.service` to point to the full path of `src/netgear_sms_wrapper.sh`.

---

## 🧪 Testing

### Manual SMS Check

```bash
# Check current state
cd src
../venv/bin/python netgear_sms_poller.py status

# List all SMS in modem inbox
../venv/bin/python netgear_sms_poller.py list

# Manual check (via wrapper)
./netgear_sms_wrapper.sh
```

### Send Test SMS

1. **Send SMS to LM1200 SIM card** (from mobile phone)
   - Example: "Test OTP: 123456"

2. **Wait 5 minutes** (or trigger manually):
   ```bash
   sudo systemctl start netgear-sms-poller.service
   ```

3. **Verify Telegram alert received**:
   - Check Telegram chat for new message
   - Format: "📱 New SMS\nFrom: +49...\nTime: ...\n\nTest OTP: 123456"

4. **Verify JSON storage**:
   ```bash
   cat /var/lib/netgear-sms-gateway/sms-inbox-$(date +%Y-%m).json | jq .
   ```

5. **Verify state updated**:
   ```bash
   cat /var/lib/netgear-sms-gateway/sms-poller-state.json | jq .
   ```

### Rate Limiting Test

```bash
# Send 2 SMS within 5 minutes
# Expected: Only FIRST SMS triggers Telegram (rate limit active)
# Verify: BOTH SMS saved to JSON

# Check rate limit status
journalctl -u netgear-sms-poller.service -n 50 | grep "rate limit"
```

---

## 📊 Monitoring

### Check Service Status

```bash
# Timer status
systemctl status netgear-sms-poller.timer

# Service status (last run)
systemctl status netgear-sms-poller.service

# Next trigger
systemctl list-timers netgear-sms-poller.timer
```

### View Logs

```bash
# Last 50 lines
journalctl -u netgear-sms-poller.service -n 50

# Follow logs
journalctl -u netgear-sms-poller.service -f

# Today's logs
journalctl -u netgear-sms-poller.service --since today

# Errors only
journalctl -u netgear-sms-poller.service -p err
```

### Check State

```bash
# Current state (via CLI)
cd src
../venv/bin/python netgear_sms_poller.py status

# State file
cat /var/lib/netgear-sms-gateway/sms-poller-state.json | jq .
```

---

## 🔧 Configuration

### Polling Frequency

**Default**: 5 minutes (OnUnitActiveSec=5min)

**Change**:
```bash
# Edit timer unit
sudo nano /etc/systemd/system/netgear-sms-poller.timer

# Change OnUnitActiveSec
OnUnitActiveSec=1min   # For 1-minute polling (faster for OTP)
OnUnitActiveSec=15min  # For 15-minute polling (less API load)

# Reload & restart
sudo systemctl daemon-reload
sudo systemctl restart netgear-sms-poller.timer
```

### Telegram Rate Limit

**Default**: 5 minutes (RATE_LIMIT_SECONDS=300)

**Change**:
```bash
# Edit config file
sudo nano /etc/netgear-sms-gateway/config.env

# Change RATE_LIMIT_SECONDS
RATE_LIMIT_SECONDS=60    # 1 minute (more alerts)
RATE_LIMIT_SECONDS=1800  # 30 minutes (fewer alerts)

# Restart service
sudo systemctl restart netgear-sms-poller.service
```

### SMS Storage Retention

**Default**: Unlimited (all SMS are stored)

**Cleanup** (optional, via cronjob):
```bash
# Delete SMS older than 6 months
find /var/lib/netgear-sms-gateway/sms-inbox-*.json -type f -mtime +180 -delete
```

---

## 🛠️ Troubleshooting

### ⚠️ CRITICAL: No SMS Received (msgCount = 0)

**Problem**: Modem receives NO SMS, API shows `"msgCount": 0` despite test SMS sent

**Root Cause**: Network Mode "LTE Only" + 3G shutdown in Germany (2021)

**Symptoms**:
```bash
# API shows no SMS
curl -s http://192.168.0.201/api/model.json | jq '.sms.msgCount'
# Output: 0 (despite sent SMS)

# bandRegion shows "LTE Only"
curl -s http://192.168.0.201/api/model.json | jq '.wwan.RAT'
# Output: "Only4G"
```

**Cause**:
1. **3G shut down** (Telekom/Vodafone/O2 since 2021)
2. **"LTE Only" mode** blocks SMS fallback mechanisms
3. **1&1 provider** doesn't fully support SMS over LTE (IMS/VoLTE)
4. **Alerts disabled** - SMS subsystem inactive

**Fix** (in this order):

**1. Set Network Mode to "Auto":**
```
1. Web UI: http://192.168.0.201
2. Login
3. Network → LTE Settings → Band Selection
4. Select "Auto" (NOT "LTE Only"!)
5. Apply
6. Wait ~30 seconds
```

**2. Enable SMS Alerts:**
```
1. Web UI: http://192.168.0.201
2. Login
3. Settings → General → Alerts
4. Radio button "On"
5. Submit
```

**3. Send test SMS:**
- Wait 1-2 minutes
- SMS should now arrive

**Verification:**
```bash
# Check network mode
curl -s http://192.168.0.201/api/model.json | jq '.wwan.bandRegion[] | select(.current == true) | .name'
# Expected: "Auto"

# Check alerts
curl -s http://192.168.0.201/api/model.json | jq '.sms.alertEnabled'
# Expected: true

# Check SMS (after test SMS)
curl -s http://192.168.0.201/api/model.json | jq '.sms.msgCount'
# Expected: > 0
```

**Important:**
- **NEVER switch back to "LTE Only"**!
- Network mode must **PERMANENTLY stay on "Auto"**
- Otherwise SMS reception stops working

---

### SMS Not Forwarded (Exit Code 0)

**Problem**: Service runs successfully, but no SMS forwarded

**Causes**:
1. **No new SMS**: Modem inbox is empty or all SMS already processed
2. **last_processed_sms_id too high**: State file shows higher ID than actual SMS

**Fix**:
```bash
# Check modem inbox
cd src
../venv/bin/python netgear_sms_poller.py list

# Check state
cat /var/lib/netgear-sms-gateway/sms-poller-state.json | jq .

# Reset state (re-process all SMS)
cd src
../venv/bin/python netgear_sms_poller.py reset
```

### Authentication Error (Exit Code 1)

**Problem**: "Login failed with HTTP 403"

**Causes**:
1. **Wrong password**: NETGEAR_ADMIN_PASSWORD incorrect
2. **Modem not reachable**: IP 192.168.0.201 not available

**Fix**:
```bash
# Verify password
grep "^NETGEAR_ADMIN_PASSWORD=" /etc/netgear-sms-gateway/config.env

# Test modem connectivity
ping -c 3 192.168.0.201

# Test login manually
curl -v http://192.168.0.201/api/model.json
```

### Telegram Alerts Not Received

**Problem**: SMS received, but no Telegram alert

**Causes**:
1. **Rate limit active**: Too many SMS within 5 minutes
2. **Telegram not configured**: BOT_TOKEN or CHAT_ID empty
3. **Wrong Chat ID**: TELEGRAM_CHAT_ID incorrect

**Fix**:
```bash
# Check logs for rate limit
journalctl -u netgear-sms-poller.service -n 50 | grep "rate limit"

# Check config
grep "^TELEGRAM" /etc/netgear-sms-gateway/config.env

# Test Telegram manually
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=Test from SMS Gateway"
```

---

## 📁 File Locations

### Scripts
- **Python Script**: `src/netgear_sms_poller.py`
- **Bash Wrapper**: `src/netgear_sms_wrapper.sh`
- **Symlink**: `/usr/local/bin/netgear-sms-poller` → Bash Wrapper

### systemd Units
- **Service**: `/etc/systemd/system/netgear-sms-poller.service`
- **Timer**: `/etc/systemd/system/netgear-sms-poller.timer`
- **Config**: `systemd/` (repository)

### State & Storage
- **State File**: `/var/lib/netgear-sms-gateway/sms-poller-state.json`
- **SMS Storage**: `/var/lib/netgear-sms-gateway/sms-inbox-YYYY-MM.json` (monthly rotated)

### Credentials
- **Config**: `/etc/netgear-sms-gateway/config.env`

---

## 🔗 Related Documentation

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Repository**: https://github.com/fidpa/netgear-lm1200-sms-gateway

---

## 📚 External References

- [GitHub: svbnet/netgear-sms](https://github.com/svbnet/netgear-sms) - SMS API for Netgear LTE modems
- [GitHub: amelchio/eternalegypt](https://github.com/amelchio/eternalegypt) - Python API for Netgear LTE modems
- [Home Assistant: NETGEAR LTE Integration](https://www.home-assistant.io/integrations/netgear_lte/) - Official integration
- [Netgear LM1200 User Manual](https://www.downloads.netgear.com/files/GDC/LM1200/LM1200_UM_EN.pdf) - Official documentation

---

</details>

**Version**: 1.0.0
**Last Updated**: 2025-12-30
**Status**: ✅ Production Ready
