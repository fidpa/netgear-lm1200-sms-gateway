# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |

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
- Use strong admin password for modem web UI (default: password)

### Network Security

- Modem admin UI (192.168.0.201) should NOT be exposed to public networks
- Use firewall rules to restrict modem access to local network only
- Consider VPN if remote SMS access is required

### systemd Hardening

The service includes security hardening:
- `ProtectSystem=strict` - Read-only filesystem except state directory
- `PrivateTmp=yes` - Private /tmp namespace
- `NoNewPrivileges=yes` - Prevent privilege escalation
- `ReadWritePaths=/var/lib/netgear-sms-gateway` - Minimal write access

### SMS Content

- SMS messages may contain sensitive data (2FA codes, OTP tokens)
- Stored in `/var/lib/netgear-sms-gateway/` with restricted permissions
- Monthly rotation prevents unlimited log growth
- Consider encrypting state directory if storing on shared systems

### Telegram Bot

- Keep Telegram Bot Token secret (never log or expose)
- Use dedicated bot for SMS forwarding (not shared with other services)
- Verify Chat ID to prevent unauthorized access
- Consider rate limiting in config (`RATE_LIMIT_SECONDS=300`)

## Known Security Considerations

### Modem API Authentication

- Netgear LM1200 uses HTTP Basic Auth (not HTTPS)
- Admin password transmitted in base64-encoded form
- Mitigation: Ensure modem is only accessible on trusted local network

### SMS Storage

- SMS content stored in plaintext JSON files
- Mitigation: Filesystem permissions (`chmod 700` on state directory)
- Future: Consider encrypted storage option

## Security Changelog

### v1.0.0 (2025-12-30)

- Initial release with systemd hardening
- Secure credential storage in `/etc/`
- Rate limiting for Telegram forwarding
