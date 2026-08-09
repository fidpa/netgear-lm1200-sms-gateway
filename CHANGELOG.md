# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.1] - 2026-08-09

### Fixed
- **Version is now read from a single source** - the wrapper reported `1.2.0` while the released tag was `v1.3.0`
  - `src/netgear_sms_wrapper.sh` carried `readonly SCRIPT_VERSION="1.2.0"`, one minor release behind the tag
  - `scripts/install.sh` carried a separate `# Version: 1.0.2`, four releases behind
  - New `VERSION` file in the repository root is the only place a version number lives
  - The wrapper resolves it at runtime and falls back to `unknown` if the file is missing or empty, so a broken version file can never stop the service from starting
- **Startup log line now states the running version** - `=== Netgear LM1200 SMS Poller Check (v1.3.1) ===`
  - Previously the version constant was defined but read by nothing, which is why the drift went unnoticed across six releases
  - `journalctl -u netgear-sms-poller.service` now answers "which build is running here?"
- **Ruff rule set pinned** - CI installed Ruff unpinned and the tool's default rule set is not a stable contract
  - Ruff 0.16 enables 415 rules by default; earlier versions enabled four groups
  - Result: 17 findings on an unchanged tree, i.e. the next push would have turned CI red without a single code change
  - New `ruff.toml` fixes the selection to `E4`, `E7`, `E9`, `F` - the contract every release up to v1.3.0 was verified against
  - `lint.yml` pins `ruff==0.16.0` so the default cannot shift underneath the repository again

### Changed
- **Release notes are cut from CHANGELOG.md instead of generated from commits**
  - `generate_release_notes: true` produced a 95-byte body for v1.3.0: one compare link, nothing else, because the commit history consists of bare `vX.Y.Z` lines
  - `release.yml` now extracts the changelog section for the tag and fails the workflow if that section is empty, rather than publishing an empty release
  - `softprops/action-gh-release` upgraded v1 → v2 (v1 runs on a deprecated Node runtime)
- Removed the changelog block duplicated in the `netgear_sms_wrapper.sh` header - `CHANGELOG.md` is the single record
- `.gitignore` now covers `*.key` and local agent tooling (`.claude/`, `CLAUDE.md`)

### Migration Notes
- No breaking changes, 100% backward compatible - no configuration variable, exit code, state file or systemd unit changed
- **Deployments that copy `src/` without the repository root must now also ship `VERSION`**, otherwise the log line reads `v unknown`. The supported install path (`scripts/install.sh`, which symlinks into the checked-out repository) is unaffected
- Anyone running `ruff` locally against this repository will see fewer findings than before; the stricter modern default is not the project's lint contract

## [1.3.0] - 2026-02-14

### Added
- **Transient Failure Alert Suppression** - No more false alerts during modem reboots (#7)
  - Consecutive failure tracking via persistent counter file
  - Configurable threshold: `SMS_FAILURE_THRESHOLD` (default: 3 failures = ~15 min)
  - Recovery alerts when service recovers after threshold breach
  - Extended retry defaults: 5 attempts with 10s initial delay (~3 min coverage)
  - systemd TimeoutStartSec raised from 120s to 240s

### Changed
- Default retry parameters: `SMS_RETRY_MAX_ATTEMPTS` 3→5, `SMS_RETRY_INITIAL_DELAY` 5→10
- Bash wrapper version: 1.1.1 → 1.2.0

### Migration Notes
- No breaking changes, 100% backward compatible
- Previous behavior (immediate alert on first failure) can be restored with `SMS_FAILURE_THRESHOLD=1`
- New file created in state directory: `failure_count` (auto-managed, safe to delete)

## [1.2.1] - 2026-01-22

### Fixed
- Ruff linting: Unused variable in modem reachability check (`response` → `_`)

### Changed
- README: Updated badge layout (removed redundant GitHub Stars badge)

## [1.2.0] - 2026-01-21

### Added
- **CI/CD pipeline with GitHub Actions**
  - ShellCheck linting for Bash scripts
  - Ruff linting for Python code
  - Automated syntax validation
  - Automated GitHub Releases via tags
- **Encrypted SMS Storage** - Optional AES-256 encryption for SMS content (#1)
  - New CLI mode: `generate-key` for encryption key generation
  - Hybrid state support: plaintext and encrypted SMS coexist
  - Backward compatible: encryption disabled by default
- **Retry Logic** - Exponential backoff for transient network errors (#2)
  - Smart error classification: transient vs permanent
  - Configurable: max attempts, delays via ENV vars
  - Default: 3 attempts with 5s → 10s → 20s backoff
- **Health Check Endpoint** - New CLI mode for monitoring integration (#3)
  - Exit codes: 0 (healthy), 1 (degraded), 2 (down)
  - Prometheus/Uptime Kuma compatible
- **Configurable Log Level** - LOG_LEVEL ENV var support (#4)
  - Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Default: INFO (backward compatible)
- **Magic Numbers as Constants** - Improved code readability (#5)
  - HTTP_TIMEOUT_SECONDS, HASH_LIST_MAX_SIZE, HASH_LIST_TRIM_SIZE
- **jq Prerequisite Check** - Explicit validation at startup (#6)
  - Multi-distro installation instructions (apt, dnf, pacman)

### Changed
- **Encryption is now optional**: Gateway works without `cryptography` installed
- Graceful degradation: All features work without encryption (retry, health check, etc.)
- `requirements.txt`: `cryptography` commented out (optional dependency)

### Documentation
- New guide: docs/ENCRYPTION.md (encryption setup, key management)
- New guide: docs/MONITORING.md (health check integration)
- Updated: README.md (new features, advanced configuration)
- Updated: config.example.env (all new ENV vars documented)

### Migration Notes
- No breaking changes, 100% backward compatible
- All new features opt-in via ENV vars
- Encryption: existing plaintext SMS remain readable

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

[Unreleased]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.3.0
[1.2.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.2.1
[1.1.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.1
[1.1.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.0
[1.0.4]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.4
[1.0.3]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.3
[1.0.2]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.2
[1.0.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.1
[1.0.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.0
