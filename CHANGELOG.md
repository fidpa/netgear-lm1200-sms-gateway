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

## [1.1.1] - 2026-01-21

### Fixed
- Config file permissions: Changed from `root:root 0600` to `$USER:$USER 0600` so service user can read credentials
- Signal handling: `shutdown_requested` flag is now checked at safe checkpoints (before polling, after HTTP requests)
- jq dependency: Changed from optional WARNING to mandatory ERROR in install.sh (required for SMS forwarding)
- Config loading: Added readable check (`-r`) before sourcing config file, with proper error messages

### Changed
- `signal_handler()` now logs signal name (SIGTERM/SIGINT) for better debugging
- `poll_sms()` returns exit code 130 on graceful shutdown via signal
- Feature description updated: "Graceful shutdown on SIGTERM/SIGINT (exits at safe checkpoints)"

## [1.1.0] - 2026-01-21

### Added
- Hash-based SMS deduplication (prevents duplicates on ID reset)
- `max_sms_id_seen` tracking for ID reset detection
- Automatic state migration (v1.0.x → v1.1.0)
- `compute_sms_hash()` and `compute_sms_hash_dict()` utility functions
- `is_new_sms()` multi-layer check (hash + ID + reset detection)

### Changed
- `SMSPollerState` now tracks `processed_hashes` (list) and `max_sms_id_seen` (int)
- `save_sms_to_json()` uses hash-based merging instead of ID-based
- `poll_sms()` returns exit code 1 on critical state save failures
- Improved error handling with explicit exit codes

### Fixed
- Duplicate SMS after modem ID reset (hash-based detection prevents this)
- Silent state save failures (now logged and return exit code 1)

### Migration
- Existing v1.0.x state files automatically migrate on first run
- No manual intervention required (backward compatible)

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

[Unreleased]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.1
[1.1.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.0
[1.0.4]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.4
[1.0.3]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.3
[1.0.2]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.2
[1.0.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.1
[1.0.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.0
