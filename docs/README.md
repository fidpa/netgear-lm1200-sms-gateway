# Documentation

> Comprehensive guides for Netgear LM1200 SMS Gateway installation, configuration, and troubleshooting.

## 📖 Overview

| Document | Description | Audience |
|----------|-------------|----------|
| [SETUP.md](SETUP.md) | Complete installation & configuration guide | New users, sysadmins |
| [API_REFERENCE.md](API_REFERENCE.md) | Netgear LM1200 API documentation | Developers, integrators |
| [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) | Migrating from v1.0.x to v1.1.0 | Existing users |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues & solutions | All users |

## 🚀 Quick Links

### Installation & Configuration

- **First-time setup**: [SETUP.md § Installation & Deployment](SETUP.md#-installation--deployment)
- **Critical modem config**: [SETUP.md § Modem Configuration](SETUP.md#-critical-modem-configuration-do-this-first)
- **systemd service setup**: [SETUP.md § systemd Setup](SETUP.md#systemd-setup)
- **Telegram integration**: [SETUP.md § Telegram](SETUP.md#telegram-integration-optional)

### Troubleshooting

- **No SMS received**: [TROUBLESHOOTING.md § No SMS](TROUBLESHOOTING.md#1-no-sms-received-msgcount--0--critical)
- **Service errors**: [TROUBLESHOOTING.md § Service Crashes](TROUBLESHOOTING.md#2-service-crashes-exit-code--0)
- **Telegram issues**: [TROUBLESHOOTING.md § Telegram Not Working](TROUBLESHOOTING.md#3-telegram-forwarding-not-working)
- **Modem unreachable**: [TROUBLESHOOTING.md § Connection Issues](TROUBLESHOOTING.md#4-connection-refused-or-timeout)

### API & Development

- **SMS endpoints**: [API_REFERENCE.md § SMS Operations](API_REFERENCE.md#sms-operations)
- **Response formats**: [API_REFERENCE.md § Response Types](API_REFERENCE.md#response-types)
- **Rate limits**: [API_REFERENCE.md § Rate Limiting](API_REFERENCE.md#rate-limiting)

## 📝 Documentation Standards

All documentation in this directory follows these principles:

- **⚡ TL;DR sections**: Quick summaries for rapid orientation
- **Progressive disclosure**: `<details>` blocks for in-depth content
- **Real-world examples**: Copy-paste commands with actual values
- **Device-tested**: All instructions verified on Netgear LM1200
- **Security-first**: Credentials, permissions, and hardening explicitly covered

## 🔗 External Resources

- [Netgear LM1200 Product Page](https://www.netgear.com/home/mobile-wifi/lte-modems/lm1200/)
- [Netgear Support Portal](https://kb.netgear.com/)
- [Home Assistant NETGEAR LTE Integration](https://www.home-assistant.io/integrations/netgear_lte/)
- [svbnet/netgear-sms Python Library](https://github.com/svbnet/netgear-sms)

## 🤝 Contributing to Docs

Found an error or have suggestions? Please:

1. Open an issue describing the documentation problem
2. Submit a PR with corrections/improvements
3. Follow the documentation standards above

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.

---

**Last Updated**: 2026-01-21
**Maintainer**: fidpa
