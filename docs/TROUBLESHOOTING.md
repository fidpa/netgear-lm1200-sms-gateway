# Troubleshooting Guide

**Version**: 1.0.0
**Date**: 2025-12-30

## Common Issues

### 1. No SMS Received (msgCount = 0) ⚠️ CRITICAL

**Symptoms**:
- Modem doesn't receive SMS
- API shows `"msgCount": 0`
- Test SMS sent but not appearing in inbox

**Root Cause**:
1. **Network Mode "LTE Only"** blocks SMS reception
2. **SMS Alerts not enabled** in modem settings

**Technical Background** (Germany-specific):
- 3G was shut down in 2021 (Telekom/Vodafone/O2)
- LM1200 in "LTE Only" mode has NO fallback mechanism
- SMS over LTE (IMS/VoLTE) requires provider support
- 1&1 doesn't fully support SMS over LTE
- → SMS cannot be physically delivered at network level

**Solution** (both steps required):

**Step 1: Set Network Mode to "Auto"**
```
1. Open modem web UI: http://192.168.0.201
2. Login with admin password
3. Navigate: Network → LTE Settings → Band Selection
4. Select "Auto" (NOT "LTE Only"!)
5. Click Apply
6. Wait ~30 seconds for reconnect
```

**Step 2: Enable SMS Alerts**
```
1. Open modem web UI: http://192.168.0.201
2. Login with admin password
3. Navigate: Settings → General → Alerts
4. Set radio button to "On"
5. (Optional) Enter any target phone number
6. Click Submit
```

**Verification**:
```bash
# Check network mode (should show "Auto")
curl -s http://192.168.0.201/api/model.json | jq '.wwan.bandRegion[] | select(.current == true) | .name'
# Expected output: "Auto"

# Check alerts enabled (should show true)
curl -s http://192.168.0.201/api/model.json | jq '.sms.alertEnabled'
# Expected output: true

# Send test SMS and check after 1-2 minutes
curl -s http://192.168.0.201/api/model.json | jq '.sms.msgCount'
# Expected output: > 0
```

**IMPORTANT**:
- **NEVER switch back to "LTE Only"** mode
- Network mode must **permanently stay on "Auto"**
- Otherwise SMS reception will stop working again

---

### 2. Wrong API Field Names

**Symptoms**:
- Python script runs without errors
- SMS are detected but fields are empty
- Telegram messages show "Unknown" sender or empty content

**Root Cause**:
The real LM1200 API uses different field names than documented in some GitHub projects:

**Incorrect** (from outdated docs):
```json
{
  "id": "1",
  "number": "+49...",
  "time": "...",
  "content": "..."
}
```

**Correct** (actual LM1200 API):
```json
{
  "id": "1",
  "sender": "+49...",    // Not "number"!
  "rxTime": "...",       // Not "time"!
  "text": "...",         // Not "content"!
  "read": false
}
```

**Solution**:
Update your code to use the correct field names:
```python
sms = SMSMessage(
    id=int(msg.get('id', 0)),
    number=msg.get('sender', ''),      # Use 'sender'
    time=msg.get('rxTime', ''),        # Use 'rxTime'
    content=msg.get('text', ''),       # Use 'text'
    read=bool(msg.get('read', False))
)
```

**Note**: This repository already uses the correct field names.

---

### 3. Authentication Failed (Exit Code 1)

**Symptoms**:
- Service fails with "Login failed with HTTP 403"
- Logs show authentication errors

**Possible Causes**:

**A) Wrong Password**
```bash
# Check config file
cat /etc/netgear-sms-gateway/config.env | grep NETGEAR_ADMIN_PASSWORD

# Test login manually via API
curl -s http://192.168.0.201/api/model.json | jq '.session.secToken'
```

**B) Modem Not Reachable**
```bash
# Test connectivity
ping -c 3 192.168.0.201

# Check modem status
curl -v http://192.168.0.201/api/model.json
```

**C) Wrong IP Address**
```bash
# Check if modem IP was changed
# Default is 192.168.0.201, but can be customized

# Update config if needed
sudo nano /etc/netgear-sms-gateway/config.env
# Set: NETGEAR_IP=your_modem_ip
```

---

### 4. Telegram Alerts Not Received

**Symptoms**:
- SMS are received and processed (exit code 2)
- But no Telegram notification appears

**Possible Causes**:

**A) Telegram Not Configured**
```bash
# Check config
cat /etc/netgear-sms-gateway/config.env | grep TELEGRAM

# If empty, Telegram is disabled (by design)
# Script works fine without Telegram (only local JSON storage)
```

**B) Wrong Telegram Credentials**
```bash
# Test Telegram manually
TELEGRAM_BOT_TOKEN="your_token_here"
TELEGRAM_CHAT_ID="your_chat_id_here"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=Test from SMS Gateway"

# If this fails, check:
# 1. Bot token is correct (from @BotFather)
# 2. Chat ID is correct (your personal chat or group)
# 3. Bot has been started (send /start to bot first)
```

**C) Rate Limiting Active**
```bash
# Check logs for rate limit messages
journalctl -u netgear-sms-poller.service -n 50 | grep "rate limit"

# Rate limit default: 5 minutes
# If multiple SMS arrive within 5min, only first triggers Telegram

# Reset rate limit manually (if needed)
rm /var/lib/netgear-sms-gateway/.last_alert_*
```

---

### 5. SMS Not Forwarded (Exit Code 0)

**Symptoms**:
- Service runs successfully
- But no SMS detected/forwarded
- Exit code 0 (no new SMS)

**Possible Causes**:

**A) No New SMS**
```bash
# Check modem inbox directly
cd /path/to/repo/src
../venv/bin/python netgear_sms_poller.py list

# If empty: No SMS in modem, send test SMS first
```

**B) All SMS Already Processed**
```bash
# Check state file
cat /var/lib/netgear-sms-gateway/sms-poller-state.json | jq .

# If last_processed_sms_id >= highest SMS ID in modem:
# → All SMS already processed

# Reset state to re-process all SMS
cd /path/to/repo/src
../venv/bin/python netgear_sms_poller.py reset
```

---

### 6. Python Script Not Found

**Symptoms**:
- Service fails with "Python script not found"
- Or "No such file or directory"

**Solution**:
```bash
# Verify Python script exists
ls -la /path/to/repo/src/netgear_sms_poller.py

# Verify venv exists
ls -la /path/to/repo/src/venv/bin/python

# Recreate venv if missing
cd /path/to/repo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Update symlink
sudo ln -sf "$(pwd)/src/netgear_sms_wrapper.sh" /usr/local/bin/netgear-sms-poller
```

---

### 7. Permission Denied Errors

**Symptoms**:
- Service fails with "Permission denied"
- Cannot write to state directory

**Solution**:
```bash
# Create state directory with correct ownership
sudo mkdir -p /var/lib/netgear-sms-gateway
sudo chown $USER:$USER /var/lib/netgear-sms-gateway

# Verify permissions
ls -ld /var/lib/netgear-sms-gateway
# Should show: drwxr-xr-x your_user your_user

# Update systemd service user if needed
sudo nano /etc/systemd/system/netgear-sms-poller.service
# Set: User=your_username
# Set: Group=your_username

sudo systemctl daemon-reload
sudo systemctl restart netgear-sms-poller.service
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
# Check service logs
journalctl -u netgear-sms-poller.service -f

# Show only errors
journalctl -u netgear-sms-poller.service -p err

# Show last 100 lines
journalctl -u netgear-sms-poller.service -n 100
```

### Manual Test Run

```bash
# Run wrapper manually (as your user)
cd /path/to/repo/src
./netgear_sms_wrapper.sh

# Run Python script directly
../venv/bin/python netgear_sms_poller.py check

# Check state
../venv/bin/python netgear_sms_poller.py status

# List SMS in modem
../venv/bin/python netgear_sms_poller.py list
```

### API Direct Test

```bash
# Check modem API directly
curl -s http://192.168.0.201/api/model.json | jq '.sms'

# Expected output:
# {
#   "ready": true,
#   "alertEnabled": true,   ← Must be true!
#   "msgCount": X,          ← Should be > 0 if SMS sent
#   "msgs": [...]
# }
```

### Check Network Mode

```bash
# Verify network mode is "Auto"
curl -s http://192.168.0.201/api/model.json | jq '.wwan.bandRegion[] | select(.current == true) | .name'

# Should output: "Auto"
# NOT: "LTE Only" or "Only4G"
```

---

## Performance Issues

### High CPU Usage

**Cause**: Too frequent polling (e.g., every 1 minute)

**Solution**:
```bash
# Increase polling interval
sudo nano /etc/systemd/system/netgear-sms-poller.timer

# Change to 5 or 15 minutes
OnUnitActiveSec=5min

sudo systemctl daemon-reload
sudo systemctl restart netgear-sms-poller.timer
```

### Slow API Response

**Cause**: Modem may be slow or overloaded

**Solution**:
```bash
# Increase timeout in Python script
nano src/netgear_sms_poller.py

# Change timeout parameter (currently 10 seconds)
async with session.get(API_URL, allow_redirects=True, timeout=20) as response:
```

---

## Recovery Procedures

### Complete Reset

```bash
# Stop service
sudo systemctl stop netgear-sms-poller.timer
sudo systemctl stop netgear-sms-poller.service

# Reset state
cd /path/to/repo/src
../venv/bin/python netgear_sms_poller.py reset

# Clear rate limit files
rm /var/lib/netgear-sms-gateway/.last_alert_*

# Restart service
sudo systemctl start netgear-sms-poller.timer
```

### Modem Reboot

```bash
# If modem becomes unresponsive
# Login to web UI: http://192.168.0.201
# Settings → General → Reboot

# Or via API (if authenticated)
# (Not recommended - requires fresh security token)
```

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs first**: `journalctl -u netgear-sms-poller.service -n 100`
2. **Verify modem config**: Network mode "Auto" + Alerts "On"
3. **Test API manually**: `curl -s http://192.168.0.201/api/model.json | jq .`
4. **Open GitHub issue**: Include logs, config (without passwords), and error messages

---

## Related Documentation

- **Setup Guide**: [SETUP.md](SETUP.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Repository**: https://github.com/fidpa/netgear-lm1200-sms-gateway

---

**Version**: 1.0.0
**Last Updated**: 2025-12-30
**Status**: ✅ Complete
