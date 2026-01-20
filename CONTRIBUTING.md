# Contributing to Netgear LM1200 SMS Gateway

Thank you for your interest in contributing to this project!

## How to Contribute

### Bug Reports

1. Check [existing issues](https://github.com/fidpa/netgear-lm1200-sms-gateway/issues) first
2. Open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs. actual behavior
   - System info (OS, Python version, modem firmware)
   - Relevant logs (from `journalctl -u netgear-sms-poller.service`)

### Feature Requests

1. Open an issue describing:
   - Use case / problem to solve
   - Proposed solution
   - Alternative approaches considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly (see Development Setup below)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Netgear LM1200 modem (for integration testing)
- `jq` command-line tool

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/netgear-lm1200-sms-gateway.git
cd netgear-lm1200-sms-gateway

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-asyncio mypy black ruff
```

### Testing

```bash
# Manual test (requires modem access)
python3 src/netgear_sms_poller.py --config config/config.example.env

# Check logs
tail -f /var/lib/netgear-sms-gateway/sms_poller.log

# Verify systemd integration
sudo systemctl start netgear-sms-poller.service
journalctl -u netgear-sms-poller.service -n 50
```

## Code Style

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function signatures
- Async/await for I/O operations
- Error handling with explicit exceptions
- Logging via Python `logging` module

Example:
```python
async def fetch_sms(modem_ip: str, password: str) -> list[dict[str, str]]:
    """Fetch SMS messages from Netgear LM1200 modem.

    Args:
        modem_ip: Modem IP address (default: 192.168.0.201)
        password: Admin password for modem API

    Returns:
        List of SMS message dictionaries with 'from', 'date', 'content' keys

    Raises:
        aiohttp.ClientError: If modem is unreachable
    """
    # Implementation...
```

### Bash

- Follow [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- Use `set -euo pipefail` for robustness
- Quote variables: `"$variable"`
- Check command availability: `command -v jq >/dev/null 2>&1`

### Commit Messages

- Use imperative mood: "Add feature" (not "Added feature")
- Keep first line under 72 characters
- Reference issues: "Fix SMS parsing (#42)"

Good examples:
```
Add Telegram rate limiting support

Implement rate limiting for Telegram messages to prevent
API throttling. Configurable via RATE_LIMIT_SECONDS env var.

Fixes #23
```

## Project Structure

```
.
├── src/
│   ├── netgear_sms_poller.py      # Main SMS polling script
│   └── netgear_sms_wrapper.sh     # Bash wrapper for systemd
├── systemd/
│   ├── netgear-sms-poller.service # systemd service unit
│   └── netgear-sms-poller.timer   # systemd timer (5min polling)
├── config/
│   └── config.example.env         # Example configuration
├── docs/
│   ├── SETUP.md                   # Installation guide
│   ├── API_REFERENCE.md           # Modem API documentation
│   └── TROUBLESHOOTING.md         # Common issues
└── scripts/
    └── install.sh                 # Automated installer

```

## Documentation

- Update relevant docs in `docs/` for new features
- Include examples in docstrings
- Add troubleshooting entries for common issues
- Update README.md if user-facing changes

## Testing Checklist

Before submitting PR, verify:

- [ ] Code follows style guidelines
- [ ] New features are documented
- [ ] Manual testing on real modem (if applicable)
- [ ] No credentials or secrets in code
- [ ] Logs are meaningful and not spammy
- [ ] systemd service still works after changes

## Questions?

- Open an issue for general questions
- Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) first
- Contact maintainer: info@fidpa.de

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
Be respectful, inclusive, and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
