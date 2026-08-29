# Netgear LM1200 SMS Gateway

[![Release](https://img.shields.io/github/v/release/fidpa/netgear-lm1200-sms-gateway?style=flat-square)](https://github.com/fidpa/netgear-lm1200-sms-gateway/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![CI](https://github.com/fidpa/netgear-lm1200-sms-gateway/actions/workflows/lint.yml/badge.svg)](https://github.com/fidpa/netgear-lm1200-sms-gateway/actions/workflows/lint.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux&logoColor=white)](https://www.linux.org/)
[![Netgear LM1200](https://img.shields.io/badge/Netgear-LM1200-blue?style=flat-square)](https://www.netgear.com/home/mobile-wifi/lte-modems/lm1200/)
[![Maintenance](https://img.shields.io/badge/Maintained-yes-brightgreen?style=flat-square)](https://github.com/fidpa/netgear-lm1200-sms-gateway/commits/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

> A systemd timer polls the inbox of a Netgear LM1200 4G LTE modem every five
> minutes, archives each message as JSON and forwards it to Telegram, so a 2FA
> code arriving on the SIM card reaches your phone.

## ⚡ Features

- **Polling every 5 minutes**: a systemd timer (`OnUnitActiveSec=5min`,
  `OnBootSec=2min`, `Persistent=true`) runs one `oneshot` service per cycle
- **Authenticated modem API**: the poller reads `secToken` from
  `/api/model.json`, posts it to `/Forms/config` and reuses the session cookie
- **Deduplication by content hash**: SHA-256 over `number|time|content`, first
  16 hex characters, so a modem-side ID reset does not replay old messages
- **JSON archive, one file per month**: `sms-inbox-YYYY-MM.json`, appended and
  written atomically through a temp file plus rename
- **Optional Telegram forwarding**: sender, timestamp and body, prefixed with
  `TELEGRAM_PREFIX`
- **Retry with exponential backoff**: only for transient failures (connection
  refused, timeout, HTTP 503 and 429); authentication failures and JSON decode
  errors fail on the first attempt
- **Alert suppression**: a Telegram failure alert goes out after
  `SMS_FAILURE_THRESHOLD` consecutive timer failures, three by default
- **Optional at-rest encryption**: Fernet (AES-128-CBC plus HMAC-SHA256),
  stored bodies carry an `ENC:` prefix
- **`health` subcommand**: exit code 0 healthy, 1 degraded, 2 down, for a
  monitoring check that runs the script
- **systemd sandboxing**: `ProtectSystem=strict`, `ProtectHome=read-only`,
  `PrivateTmp=yes`, `NoNewPrivileges=yes`
- **Python 3.10+**, `asyncio` and `aiohttp`, one runtime dependency

> [!IMPORTANT]
> **Known limitations**, all of them reproducible from the code:
>
> - **Telegram carries one SMS per polling cycle.** The state file keeps a
>   single `latest_sms` field, and the wrapper forwards that one. If three
>   messages arrive inside the same five-minute window, the JSON archive holds
>   all three and Telegram shows the last of them.
> - **The rate limit can drop a forward.** `RATE_LIMIT_SECONDS` (300 by
>   default) applies per alert type, and the SMS forward uses the type
>   `new_sms`. Two cycles in a row with new mail means the second forward is
>   skipped with a log line, while the archive stays complete. Lower the value
>   if delivery matters more than quiet.
> - **The modem session runs over plain HTTP.** The LM1200 web UI has no TLS,
>   so `NETGEAR_ADMIN_PASSWORD` crosses the LAN in a form POST. The trust
>   anchor is the local network, not the transport.
> - **The hash list is bounded.** It is trimmed to the 500 most recent entries
>   once it passes 1000. Beyond that window, deduplication falls back to the
>   `last_processed_sms_id` comparison.
> - **Tested on one device.** One LM1200 on a German network, firmware as
>   shipped in 2025. Other Netgear LTE modems expose a similar
>   `/api/model.json` and are untested here.

## 🚨 Modem configuration comes first

SMS reception depends on two settings in the modem web UI:

1. Network Mode set to **Auto**, not "LTE Only"
2. SMS Alerts switched **on**

The reason is specific to Germany and comparable markets: the 3G networks were
switched off in 2021, and the LM1200 in "LTE Only" mode has no fallback path
for messages that arrive over the legacy route. SMS over LTE needs IMS support
from the carrier, which is not universal. In "LTE Only" the modem reports
`msgCount: 0` no matter how many messages you send to the SIM card.

[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) has the diagnosis path and
the API call that reads back the active mode.

## 🚀 Quick Start

### Prerequisites

- Netgear LM1200 4G LTE modem with an active SIM card
- Linux with systemd and Python 3.10 or newer
- `jq`, used by the Bash wrapper to read the state file
- `curl`, used for the Telegram Bot API call
- Optional: a Telegram bot token and chat ID for forwarding

```bash
# Debian/Ubuntu
sudo apt install jq curl

# RHEL/Fedora
sudo dnf install jq curl
```

### Guided install

```bash
git clone https://github.com/fidpa/netgear-lm1200-sms-gateway
cd netgear-lm1200-sms-gateway
./scripts/install.sh
```

The script creates the virtualenv, installs `/etc/netgear-sms-gateway/config.env`
from the example with mode 600, copies both systemd units while substituting
your username, links the wrapper into `/usr/local/bin` and reloads systemd. It
stops short of enabling the timer, and prints the modem settings you still have
to make.

### Manual install

<details>
<summary>The same steps by hand</summary>

1. Clone and install the dependency:
   ```bash
   git clone https://github.com/fidpa/netgear-lm1200-sms-gateway
   cd netgear-lm1200-sms-gateway
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure the modem at `http://192.168.0.201`:
   - Network Mode: Network > LTE Settings > Band Selection > Auto
   - SMS Alerts: Settings > General > Alerts > On

3. Create the configuration:
   ```bash
   sudo mkdir -p /etc/netgear-sms-gateway
   sudo cp config/config.example.env /etc/netgear-sms-gateway/config.env
   sudo chown "$USER:$USER" /etc/netgear-sms-gateway/config.env
   sudo chmod 600 /etc/netgear-sms-gateway/config.env
   sudo nano /etc/netgear-sms-gateway/config.env
   ```

4. Create the state directory, owned by the user the service runs as:
   ```bash
   sudo mkdir -p /var/lib/netgear-sms-gateway
   sudo chown "$USER:$USER" /var/lib/netgear-sms-gateway
   sudo chmod 700 /var/lib/netgear-sms-gateway
   ```

5. Install the systemd units:
   ```bash
   sudo cp systemd/netgear-sms-poller.{service,timer} /etc/systemd/system/
   sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/netgear-sms-poller.service
   sudo systemctl daemon-reload
   ```

6. Link the wrapper, which the unit calls as
   `/usr/local/bin/netgear-sms-poller`:
   ```bash
   sudo ln -sf "$(pwd)/src/netgear_sms_wrapper.sh" /usr/local/bin/netgear-sms-poller
   ```

</details>

### Start and verify

```bash
sudo systemctl enable --now netgear-sms-poller.timer

# Send an SMS to the SIM card, then trigger a cycle instead of waiting:
sudo systemctl start netgear-sms-poller.service
journalctl -u netgear-sms-poller.service -n 50
```

## 💻 CLI Reference

The Python entry point takes one positional action. Run it with the virtualenv
active, since it imports `aiohttp` at module level.

```
usage: netgear_sms_poller.py [-h]
                             [{check,status,reset,list,generate-key,health}]

Netgear LM1200 SMS Poller

positional arguments:
  {check,status,reset,list,generate-key,health}
                        Action to perform (default: check)

options:
  -h, --help            show this help message and exit

Examples:
  netgear_sms_poller.py check                  # Poll for new SMS (standard mode)
  netgear_sms_poller.py status                 # Show current state
  netgear_sms_poller.py reset                  # Reset state (emergency)
  netgear_sms_poller.py list                   # List all SMS in modem inbox
```

`generate-key` and `health` are not in the argparse epilog, but they are valid
choices. Exit codes of `check`, which the wrapper reads: 0 no new SMS, 1 error,
2 new SMS forwarded, 130 interrupted. The unit declares
`SuccessExitStatus=0 2 130`, so only 1 marks a failed run.

## 🔧 Configuration

Everything is read from `/etc/netgear-sms-gateway/config.env`. Every key below
also appears in [config/config.example.env](config/config.example.env) with the
same default.

| Variable | Required | Description |
|----------|----------|-------------|
| `NETGEAR_IP` | Optional | Modem address. Default `192.168.0.201` |
| `NETGEAR_ADMIN_PASSWORD` | **Required** | Modem admin password. The poller aborts without it |
| `SMS_STATE_DIR` | Optional | State and archive directory. Default `/var/lib/netgear-sms-gateway` |
| `TELEGRAM_BOT_TOKEN` | Optional | Bot token. Empty disables forwarding and every alert |
| `TELEGRAM_CHAT_ID` | Optional | Target chat. Empty disables forwarding |
| `TELEGRAM_PREFIX` | Optional | Prefix on every message. Default `[SMS Gateway]` |
| `RATE_LIMIT_SECONDS` | Optional | Minimum gap per alert type, including SMS forwards. Default `300` |
| `LOG_LEVEL` | Optional | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Default `INFO`; an unknown value logs a warning and falls back to `INFO` |
| `SMS_ENCRYPTION_ENABLED` | Optional | Encrypt stored bodies. Default `false` |
| `SMS_ENCRYPTION_KEY_FILE` | Optional | Fernet key file. Default `/etc/netgear-sms-gateway/.encryption.key`; `SMS_ENCRYPTION_KEY` is the fallback |
| `SMS_RETRY_ENABLED` | Optional | Retry transient failures. Default `true` |
| `SMS_RETRY_MAX_ATTEMPTS` | Optional | Attempts including the first. Example config and unit file set `5`, the code default is `3` |
| `SMS_RETRY_INITIAL_DELAY` | Optional | First backoff step in seconds, doubling per attempt. Example config and unit file set `10`, the code default is `5` |
| `SMS_RETRY_MAX_DELAY` | Optional | Backoff ceiling in seconds. Default `60` |
| `SMS_FAILURE_THRESHOLD` | Optional | Consecutive failed runs before a Telegram alert. Default `3`, about 15 minutes at a 5-minute timer |
| `HEALTH_CHECK_STALE_THRESHOLD` | Optional | Age of `last_check` in seconds that makes `health` report DEGRADED. Default `1800` |
| `HEALTH_CHECK_PING_MODEM` | Optional | Let `health` open an HTTP connection to the modem. Default `false` |

The unit file sets `SMS_RETRY_MAX_ATTEMPTS`, `SMS_RETRY_INITIAL_DELAY` and
`SMS_FAILURE_THRESHOLD` through `Environment=`, which wins over
`EnvironmentFile=`. Change those three in
`/etc/systemd/system/netgear-sms-poller.service`, not in `config.env`.

### Encryption

Needs `pip install 'cryptography>=42.0.0'`, which the base install leaves out.
Without the module, `SMS_ENCRYPTION_ENABLED=true` logs a warning and stores
plaintext.

```bash
./src/netgear_sms_poller.py generate-key
```

The key protects the archive and the `latest_sms` field in the state file. It
does not protect the message on the way to Telegram: the wrapper decrypts
before sending. [docs/ENCRYPTION.md](docs/ENCRYPTION.md) has key rotation and
the read path for old files.

### Health check

```bash
./src/netgear_sms_poller.py health
# HEALTHY: Last check 42s ago, 17 SMS received
```

Exit 2 means the state file is missing or unparsable, exit 1 means the last
check is older than `HEALTH_CHECK_STALE_THRESHOLD` or, with pinging enabled,
the modem did not answer. [docs/MONITORING.md](docs/MONITORING.md) wires this
into a monitoring system.

## 🛡️ Security

What the setup does:

- The installer writes `config.env` with mode 600, owned by the service user
- `ProtectSystem=strict` and `ReadWritePaths=/var/lib/netgear-sms-gateway`
  leave the state directory as the only writable path
- Message bodies can be encrypted at rest, see above

What it does not do:

- **The state directory permissions are yours to set.** The code calls
  `mkdir(parents=True, exist_ok=True)` without a mode, so a directory created
  by the poller follows your umask. On a shared host, `chmod 700` it.
- **The modem password travels in cleartext over the LAN.** The LM1200 offers
  no HTTPS on the admin interface.
- **A forwarded SMS is a Telegram message.** 2FA codes then live on Telegram
  servers and on every device signed into that account.

[SECURITY.md](SECURITY.md) has the reporting address and the deployment notes.

## 📊 Where this fits

Good for:

- 2FA and OTP codes arriving on a SIM you do not carry
- Archiving the messages of a machine-to-machine SIM
- A single-user SMS-to-Telegram bridge on a home server

Not recommended for:

- **Anything that must not miss a message.** The rate limit and the
  one-per-cycle forward are documented above; the JSON archive is the complete
  record, Telegram is the notification
- **Multi-user or multi-tenant setups.** One chat ID, one modem, one state file
- **Time-critical delivery.** A five-minute timer means an average delay of two
  and a half minutes, and the modem polls no faster without a config change
- **Sending SMS.** Reception only; the modem API for sending is not implemented

## 📖 Documentation

- [Documentation index](docs/README.md)
- [Setup guide](docs/SETUP.md): installation and configuration in full
- [API reference](docs/API_REFERENCE.md): the LM1200 endpoints this uses
- [Encryption](docs/ENCRYPTION.md) and [monitoring](docs/MONITORING.md)
- [Upgrade guide](docs/UPGRADE_GUIDE.md): moving from 1.0.x to 1.1.0 state files
- [Troubleshooting](docs/TROUBLESHOOTING.md): no SMS, auth failures, silent Telegram
- [CHANGELOG.md](CHANGELOG.md): what changed per release

## 🤝 Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) has the lint setup (`ruff` and `shellcheck`,
both run in CI) and the commit conventions.

## 📜 License

MIT, see [LICENSE](LICENSE).

## 🔗 Related projects

- [svbnet/netgear-sms](https://github.com/svbnet/netgear-sms): an SMS API
  client for Netgear LTE modems, unaffiliated with this project. It covers more
  modems and can send messages, which this gateway cannot
- [Home Assistant NETGEAR LTE integration](https://www.home-assistant.io/integrations/netgear_lte/):
  the better route if you already run Home Assistant
