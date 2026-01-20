# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions
- ShellCheck linting for Bash scripts
- Ruff linting for Python code
- Automated syntax validation
- Automated GitHub Releases via tags

## [1.0.4] - 2026-01-20

### Added
- SECURITY.md with vulnerability reporting process
- CONTRIBUTING.md with development guidelines
- docs/README.md as documentation index

### Changed
- Expanded README badges from 3 to 7
- Improved documentation navigation

## [1.0.3] - 2025-12-30

### Changed
- Minor bug fixes and improvements

## [1.0.2] - 2025-12-30

### Changed
- Documentation updates

## [1.0.1] - 2025-12-30

### Fixed
- Bug fixes

## [1.0.0] - 2025-12-30

### Added
- Initial stable release
- Automatic SMS polling (every 5 minutes via systemd timer)
- Optional Telegram forwarding for 2FA/OTP codes
- Local JSON storage (monthly rotated files)
- State management (no duplicates, no lost messages)
- Python 3.10+ with async/await
- systemd security hardening (ProtectSystem=strict, PrivateTmp=yes)
- Complete API documentation
- Troubleshooting guide
- Setup documentation

[Unreleased]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.4
[1.0.3]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.3
[1.0.2]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.2
[1.0.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.1
[1.0.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.0
