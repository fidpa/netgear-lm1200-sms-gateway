# Security Policy

## Supported Versions

| Version   | Supported          |
|-----------|--------------------|
| 1.3.x     | :white_check_mark: |
| <= 1.2.x  | :x:                |

Fixes go into the current minor release line. Older versions are not patched;
[docs/UPGRADE_GUIDE.md](docs/UPGRADE_GUIDE.md) covers the state-file migration
from the 1.0.x line.

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Please report security issues via:
- **Email**: security@fidpa.de
- **GitHub Security Advisory**: [Create Private Security Advisory](https://github.com/fidpa/netgear-lm1200-sms-gateway/security/advisories/new)

### Response Timeline

- **Initial Response**: 48 hours
- **Status Update**: 7 days
- **Resolution**: 30 days (depending on severity)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

## Security Best Practices

### Configuration

- Store credentials in `/etc/netgear-sms-gateway/config.env` with `chmod 600`
- Never commit `config.env` or credentials to version control
- Change the modem web UI password from the factory default before deploying

### Network Security

- Modem admin UI (192.168.0.201) should NOT be exposed to public networks
- Use firewall rules to restrict modem access to local network only
- Consider VPN if remote SMS access is required

### systemd Hardening

The service includes security hardening:
- `ProtectSystem=strict` - Read-only filesystem except state directory
- `ProtectHome=read-only` - Home directories readable, not writable
- `PrivateTmp=yes` - Private /tmp namespace
- `NoNewPrivileges=yes` - Prevent privilege escalation
- `ReadWritePaths=/var/lib/netgear-sms-gateway` - Minimal write access

### SMS Content

- SMS messages may contain sensitive data (2FA codes, OTP tokens)
- Stored in `/var/lib/netgear-sms-gateway/`, whose permissions you set (see
  Known Security Considerations below)
- One archive file per month keeps a single file from growing without bound; nothing deletes old files, so prune them yourself if disk space matters
- Consider encrypting state directory if storing on shared systems

### Telegram Bot

- Keep Telegram Bot Token secret (never log or expose)
- Use dedicated bot for SMS forwarding (not shared with other services)
- Verify Chat ID to prevent unauthorized access
- Consider rate limiting in config (`RATE_LIMIT_SECONDS=300`)

## Known Security Considerations

### Modem API Authentication

- The admin interface serves plain HTTP, with no TLS option
- The poller reads `secToken` from `/api/model.json` and posts it together with
  the admin password as form fields to `/Forms/config`, then reuses the session
  cookie. The password crosses the LAN unencrypted on every polling cycle
- Mitigation: keep the modem reachable only from a trusted local network. The
  trust anchor here is the network, not the transport

### SMS Storage

- SMS bodies are stored in plaintext JSON unless
  `SMS_ENCRYPTION_ENABLED=true` turns on Fernet encryption (AES-128-CBC plus
  HMAC-SHA256), available since 1.2.0 and off by default. See
  [docs/ENCRYPTION.md](docs/ENCRYPTION.md)
- Encryption covers the archive and the `latest_sms` field of the state file. It
  does not cover the Telegram message: the wrapper decrypts before sending
- The poller creates the state directory without an explicit mode, so its
  permissions follow the umask of whoever creates it, and `scripts/install.sh`
  sets the owner but not the mode. On a shared host, `chmod 700` it yourself

## Security Changelog

### v1.2.0 (2026-01-22, released as the `v1.2.1` tag)

- Optional Fernet encryption for stored SMS bodies (`SMS_ENCRYPTION_ENABLED`)

### v1.0.0 (2025-12-30)

- Initial release with systemd hardening
- Credential storage in `/etc/netgear-sms-gateway/config.env`, mode 600
- Rate limiting for Telegram forwarding
