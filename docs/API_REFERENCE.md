# Netgear LM1200 SMS API Reference

**Version**: 1.0.0
**Date**: 2025-12-30

## ⚡ TL;DR (20 words)

Complete API reference for Netgear LM1200 SMS functions: Endpoints, Authentication flow, JSON schema, Exit codes, State management.

---

## 📡 API Endpoints

### Base URL

```
http://192.168.0.201
```

**Note**: Default IP of LM1200. Changeable via modem web interface.

---

### 1. GET /api/model.json

**Purpose**: Main endpoint for all modem data (including SMS)

**Authentication**: Optional (more data with authenticated request)

**Response**: JSON (Content-Type: text/plain - manual parsing required)

**Response Schema**:
```json
{
  "general": {
    "deviceName": "LM1200",
    "model": "LM1200"
  },
  "session": {
    "secToken": "12345678"
  },
  "sms": {
    "ready": true,
    "sendEnabled": true,
    "sendSupported": true,
    "alertSupported": true,
    "alertEnabled": true,
    "msgCount": 1,
    "unreadMsgs": 1,
    "msgs": [
      {
        "id": "1",
        "sender": "+491234567890",
        "rxTime": "29/12/25 11:00:00 PM",
        "text": "Your OTP code is 123456",
        "read": false
      }
    ]
  },
  "wwan": {
    "registerNetworkDisplay": "1&1",
    "connection": "Connected",
    "signalStrength": {
      "bars": 4
    }
  }
}
```

**SMS Data Location**: `data['sms']['msgs']`

**SMS Section Fields**:
- `ready` (bool): SMS subsystem ready
- `sendEnabled` (bool): SMS sending enabled
- `sendSupported` (bool): Hardware supports SMS sending
- `alertSupported` (bool): Hardware supports SMS alerts
- `alertEnabled` (bool): ⚠️ CRITICAL - Must be `true` for SMS reception!
- `msgCount` (int): Total SMS in inbox
- `unreadMsgs` (int): Count of unread SMS
- `msgs` (array): Array of SMS message objects

**SMS Message Object Fields**:
- `id` (string): Unique SMS ID (incrementing, as string!)
- `sender` (string): Sender phone number (format: "+491234567890")
- `rxTime` (string): Reception timestamp (format: "DD/MM/YY HH:MM:SS AM/PM")
- `text` (string): SMS message text content
- `read` (boolean): Read status (false=unread, true=read)

---

### 2. POST /Forms/config

**Purpose**: Login & Actions (login, reboot, SMS deletion)

**Content-Type**: application/x-www-form-urlencoded

#### Login Request

**Body**:
```
session.password=<ADMIN_PASSWORD>
token=<SECURITY_TOKEN>
```

**Response**: HTTP 200/204/302 (success), creates `sessionId` cookie

**Cookie**: `sessionId=<SESSION_ID>`

**Notes**:
- Security token from GET /api/model.json (unauthenticated)
- Session cookie valid for ~30 minutes
- Use CookieJar for session persistence

#### Reboot Request (Authenticated)

**Body**:
```
general.shutdown=restart
token=<SECURITY_TOKEN>
err_redirect=/error.json
ok_redirect=/success.json
```

**Response**: HTTP 200/204/302 (success)

**Notes**:
- Requires authenticated session (sessionId cookie)
- Fresh security token needed (from authenticated /api/model.json)

---

## 🔐 Authentication Flow

### 3-Step Login Process

```python
# Step 1: Get security token (unauthenticated)
async with session.get('http://192.168.0.201/api/model.json') as response:
    data = await response.json()
    token = data['session']['secToken']

# Step 2: Login (creates session cookie)
login_data = {
    'session.password': ADMIN_PASSWORD,
    'token': token
}
async with session.post('http://192.168.0.201/Forms/config', data=login_data) as response:
    # Successful if status in [200, 204, 302]
    # CookieJar automatically stores sessionId cookie

# Step 3: Access authenticated endpoints
async with session.get('http://192.168.0.201/api/model.json') as response:
    # Now returns full data (WWAN, signal, etc.)
    data = await response.json()
```

### Session Management

**Pattern**: aiohttp CookieJar

```python
jar = aiohttp.CookieJar(unsafe=True)
async with aiohttp.ClientSession(cookie_jar=jar) as session:
    # Login creates sessionId cookie in jar
    await login(session)

    # All subsequent requests use the same session
    data = await get_api_data(session)
```

**Session Lifetime**: ~30 minutes (automatic logout)

**Timeout**: 10 seconds (recommended for all requests)

---

## 📋 JSON Schemas

### SMSMessage (Dataclass)

```python
@dataclass
class SMSMessage:
    id: int              # Unique SMS ID
    number: str          # Sender phone number (e.g., "+491234567890")
    time: str            # Timestamp string (modem format)
    content: str         # SMS message text
    read: bool           # True if marked as read
```

**Example**:
```json
{
  "id": 1,
  "number": "+491234567890",
  "time": "2025-12-29 23:00:00",
  "content": "Your OTP code is 123456",
  "read": false
}
```

---

### SMSPollerState (State File)

**Location**: `/var/lib/netgear-sms-gateway/sms-poller-state.json`

**Schema**:
```python
@dataclass
class SMSPollerState:
    last_processed_sms_id: int      # ID of last processed SMS
    last_check: float               # Unix timestamp of last check
    total_sms_received: int         # Total count of SMS received
    last_sms_timestamp: float       # Unix timestamp of last SMS
    latest_sms: dict[str, str]      # Latest SMS for Telegram forwarding
```

**Example**:
```json
{
  "last_processed_sms_id": 5,
  "last_check": 1735513200.0,
  "total_sms_received": 3,
  "last_sms_timestamp": 1735513100.0,
  "latest_sms": {
    "number": "+491234567890",
    "time": "2025-12-29 23:00:00",
    "content": "Your OTP code is 123456"
  }
}
```

**Atomic Writes**: Via pathlib (temp file + rename)

---

### SMS Storage (Monthly JSON Files)

**Location**: `/var/lib/netgear-sms-gateway/sms-inbox-YYYY-MM.json`

**Format**: Array of SMSMessage objects

**Example**:
```json
[
  {
    "id": 1,
    "number": "+491234567890",
    "time": "2025-12-29 22:30:00",
    "content": "Banking OTP: 987654",
    "read": false
  },
  {
    "id": 2,
    "number": "+491234567890",
    "time": "2025-12-29 23:00:00",
    "content": "Your OTP code is 123456",
    "read": false
  }
]
```

**Rotation**: Automatically by month (YYYY-MM)

**Retention**: Unlimited (manual cleanup optional)

---

## 🔢 Exit Codes

### Python Script (netgear_sms_poller.py)

| Exit Code | Name | Description | Action |
|-----------|------|-------------|--------|
| 0 | NO_NEW_SMS | No new SMS received | Log info, no alert |
| 1 | ERROR | Authentication failed, API error | Log error, send Telegram alert |
| 2 | NEW_SMS_FORWARDED | New SMS received and processed | Forward via Telegram |
| 130 | SIGINT | Interrupted by user (Ctrl+C) | Log warning, graceful shutdown |

### Bash Wrapper (netgear_sms_wrapper.sh)

Handles Python exit codes:

```bash
case $sms_exit in
    0)  # No new SMS
        log_info "No new SMS received"
        return 0
        ;;

    1)  # Error
        log_error "SMS poller failed"
        send_telegram_alert "❌ SMS Poller Error"
        return 1
        ;;

    2)  # New SMS
        # Read latest_sms from state file
        # Send via Telegram
        send_telegram_alert "📱 New SMS..."
        return 0
        ;;
esac
```

---

## 🛠️ CLI Commands

### netgear_sms_poller.py

```bash
# Check for new SMS (default)
python netgear_sms_poller.py check

# Show current state
python netgear_sms_poller.py status

# Reset state (re-process all SMS)
python netgear_sms_poller.py reset

# List all SMS in modem inbox
python netgear_sms_poller.py list
```

**Environment Variables**:
- `NETGEAR_ADMIN_PASSWORD` (required): Admin password for modem
- `NETGEAR_IP` (optional): Modem IP (default: 192.168.0.201)
- `SMS_STATE_DIR` (optional): State directory (default: /var/lib/netgear-sms-gateway)

---

### netgear_sms_wrapper.sh (Bash Wrapper)

```bash
# Via symlink
/usr/local/bin/netgear-sms-poller

# Direct execution
./src/netgear_sms_wrapper.sh
```

**Features**:
- Loads credentials from config.env
- Calls Python script
- Telegram forwarding (optional)
- Rate-limited alerts (5min default)

---

## 📊 Rate Limiting

### Telegram Alerts

**Implementation**: Via inline function in Bash wrapper

**Default**: 5 minutes (RATE_LIMIT_SECONDS=300)

**Mechanism**:
1. Check last alert timestamp from state file
2. If (now - last_alert) < RATE_LIMIT_SECONDS → Skip alert
3. Else → Send alert & update state

**State File**: `/var/lib/netgear-sms-gateway/.last_alert_<type>`

**Override**:
```bash
export RATE_LIMIT_SECONDS=60  # 1 minute
```

---

## 🔄 Polling Strategy

### systemd Timer

**Configuration**:
```ini
[Timer]
OnBootSec=2min          # Wait 2 minutes after boot
OnUnitActiveSec=5min    # Run every 5 minutes after last execution
Persistent=true         # Catch up missed runs after reboot
```

**Behavior**:
- First run: 2 minutes after boot
- Subsequent runs: 5 minutes after last successful execution
- If system was offline: Runs immediately after boot (Persistent=true)

**Trade-offs**:
- 5min: Good balance (OTP codes still timely, low API load)
- 1min: Faster (better for OTP), higher API load
- 15min: Lower API load, slower OTP delivery

---

## 🛡️ Security Considerations

### Credentials Storage

**NETGEAR_ADMIN_PASSWORD**:
- Location: `/etc/netgear-sms-gateway/config.env`
- Permissions: 600 (your_user:your_user)

**Telegram Bot Token**:
- Location: `/etc/netgear-sms-gateway/config.env`
- Environment variable: TELEGRAM_BOT_TOKEN

**Telegram Chat ID**:
- Location: `/etc/netgear-sms-gateway/config.env`
- Less sensitive (only identifies chat, no auth)

### SMS Content Security

**Storage**:
- JSON files: 600 permissions (your_user:your_user)
- Location: /var/lib/netgear-sms-gateway/ (protected by ProtectSystem=strict)

**Telegram Forwarding**:
- SMS content sent to private Telegram chat (configured TELEGRAM_CHAT_ID)
- No logging of SMS content (only metadata in logs)

**Recommendations**:
- ✅ Set strong NETGEAR_ADMIN_PASSWORD
- ✅ Restrict /var/lib/netgear-sms-gateway/ access (already done via systemd)
- ✅ Periodic cleanup of old SMS files (6+ months)
- ✅ Use Telegram Bot Token from trusted bot

---

## ⚠️ CRITICAL: Network Mode & SMS Reception Dependency

### 🚨 Germany-Specific Problem (3G Shutdown 2021)

**Root Cause**: Network Mode "LTE Only" blocks SMS reception

**Symptom**: `msgCount: 0` despite sent SMS, `alertEnabled: false` or `true` doesn't matter

**Technical Background**:
1. **3G was shut down in 2021** in Germany (Telekom/Vodafone/O2)
2. **LM1200 Default**: "LTE Only" mode (no 2G/3G fallback)
3. **SMS over LTE** (IMS/VoLTE) is **not fully supported** by 1&1
4. **Result**: SMS cannot be physically delivered

**API Indicators**:
```json
{
  "wwan": {
    "RAT": "Only4G",              // ← Problem: LTE-only
    "bandRegion": [
      {"name": "LTE Only", "current": true},  // ← Blocks SMS
      {"name": "Auto", "current": false}
    ]
  },
  "sms": {
    "alertEnabled": true,           // ← Can be true, but doesn't help
    "msgCount": 0,                  // ← No SMS despite alerts
    "msgs": []
  }
}
```

**Fix: Network Mode "Auto"**:
```json
{
  "wwan": {
    "RAT": "Auto",                  // ← Fixed: Auto mode
    "bandRegion": [
      {"name": "Auto", "current": true},     // ← Enables SMS
      {"name": "LTE Only", "current": false}
    ]
  },
  "sms": {
    "alertEnabled": true,
    "msgCount": 4,                  // ← SMS now arrive!
    "msgs": [
      {"id": "1", "sender": "+49...", "text": "..."}
    ]
  }
}
```

**Configuration**:
- **Web UI**: Network → LTE Settings → Band Selection → **"Auto"**
- **CRITICAL**: **NEVER** switch back to "LTE Only"!
- **Permanent**: Setting persists after reboot

**Second Dependency: alertEnabled**:
- SMS subsystem only becomes active when alerts are configured
- `alertEnabled: false` = SMS reception blocked (even in "Auto" mode)
- **Fix**: Settings → General → Alerts → **"On"**

**Both Required**:
1. ✅ Network Mode: "Auto"
2. ✅ alertEnabled: true

**Only then**: SMS reception works in Germany with 1&1 provider

---

## 🔗 Related Documentation

- **Setup Guide**: [SETUP.md](SETUP.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Repository**: https://github.com/fidpa/netgear-lm1200-sms-gateway

---

## 📚 External API Documentation

- [GitHub: svbnet/netgear-sms](https://github.com/svbnet/netgear-sms) - Unofficial API documentation
- [Home Assistant: NETGEAR LTE Integration](https://www.home-assistant.io/integrations/netgear_lte/) - Reference implementation
- [Netgear LM1200 User Manual](https://www.downloads.netgear.com/files/GDC/LM1200/LM1200_UM_EN.pdf) - Official hardware documentation

---

**Version**: 1.0.0
**Last Updated**: 2025-12-30
**Status**: ✅ Complete
