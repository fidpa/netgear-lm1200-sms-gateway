# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.5] - 2026-08-30: The documentation says what the code does

A pass over the four public documents measured every claim against the source.
`README.md` advertised `AES-256` for a Fernet feature that is AES-128-CBC plus
HMAC-SHA256, called the `health` action an endpoint, and promised "no
duplicates, no lost messages" while the wrapper forwards one SMS per polling
cycle and the rate limit can drop even that one. `SECURITY.md` described the
modem login as HTTP Basic Auth, which it has never been, and still called
encrypted storage a future option three releases after it shipped. Nothing in
the code changed; what changed is that the documents now match it.

### Changed

- **`README.md` rewritten against the code and the README quality standard.**
  Every claim now has a source in the repository, and the limits stand next to
  the features
  - Corrected: the encryption feature was labelled `AES-256`. Fernet is
    AES-128-CBC plus HMAC-SHA256, as `docs/ENCRYPTION.md` already stated
  - Corrected: the health check was called an "endpoint". It is the `health`
    action of `src/netgear_sms_poller.py`, with exit codes 0, 1 and 2
  - Corrected: "no duplicates, no lost messages" claimed more than the code
    delivers. The hash list is trimmed to 500 entries past 1000, Telegram
    receives one SMS per polling cycle (`latest_sms` holds one record), and
    `RATE_LIMIT_SECONDS` applies to the SMS forward itself
  - Added: a CLI Reference quoting `--help` verbatim, a configuration table
    covering all 17 keys of `config/config.example.env` including the retry,
    failure-threshold and health-check ones that were missing, and the note
    that the unit file overrides three of them via `Environment=`
  - Added: `scripts/install.sh` as the guided path, the `chmod 600` and
    `chmod 700` steps the manual path was missing, and a link to
    `docs/UPGRADE_GUIDE.md`
  - Added: known limitations, a "Not recommended for" list, and the honest
    security boundaries (plain HTTP to the modem, state directory permissions
    follow the umask, forwarded 2FA codes live on Telegram servers)
  - Removed: the em dash in the tagline and the `->` arrows in the setup paths,
    per rule 6 of the standard

- **`SECURITY.md` brought back in line with the code.** The document described a
  1.0.x-era gateway
  - Corrected: the modem login was described as HTTP Basic Auth with a
    base64-encoded password. The poller reads `secToken` from
    `/api/model.json` and posts it with the password as form fields to
    `/Forms/config`. Plain HTTP either way, now stated as what it is
  - Corrected: "SMS content stored in plaintext JSON files, future: consider
    encrypted storage" ignored the Fernet option shipped in 1.2.0, and the
    "restricted permissions" of the state directory were never set by anything.
    The directory is created without an explicit mode, and `scripts/install.sh`
    sets only the owner
  - Corrected: "monthly rotation prevents unlimited log growth". Nothing deletes
    old archives; the rotation splits the data, it does not bound it
  - Corrected: the supported-versions table listed 1.0.x at release 1.3.4, and
    the hardening list omitted `ProtectHome=read-only`
  - Corrected: the modem web UI default password was given as `password`, which
    contradicts `config/config.example.env`. The advice no longer names a value
  - Added: a security-changelog entry for the 1.2.0 encryption feature, and the
    note that encryption stops at the Telegram message, which the wrapper
    decrypts before sending

- **`docs/ENCRYPTION.md` and the `1.2.0` changelog entry no longer advertise
  `AES-256`.** Both now name Fernet, matching the algorithm line that
  `docs/ENCRYPTION.md` already carried

## [1.3.4] - 2026-08-28: GitHub identifies the project as MIT-licensed

### Changed

- **The repository page shows the MIT licence, and licence-filtered searches
  find the project.** `LICENSE` carried the repository URL on its own line
  under the copyright notice. GitHub reads a licence text with an extra line as
  modified and reports `NOASSERTION`, which leaves the licence field on the
  repository page empty. The line is gone; the MIT text and the copyright
  notice are byte-for-byte unchanged, and the URL is still in `README.md`.

## [1.3.3] - 2026-08-27: The Python entry point runs, and release titles say what changed

`v1.3.2` restored the execute bit on `src/netgear_sms_wrapper.sh` and
`scripts/install.sh`. It missed the third file the documentation tells people to run
directly: `src/netgear_sms_poller.py` has neither an execute bit nor a shebang, and has
had neither since `1.0.2`, where the copyright header replaced `#!/usr/bin/env python3`
on line 1.

The older sections were checked against the tags they describe and corrected where the
repository contradicted them; each correction is listed below. Every measured value,
file path and function name that survived the check was left alone.

### Fixed
- **`./src/netgear_sms_poller.py generate-key` works as documented** - the command
  in `README.md` and `docs/ENCRYPTION.md` failed with `Permission denied`
  - The file was tracked with mode `100644` and its first line was
    `# Copyright (c) 2025 ...`, so neither the execute bit nor an interpreter line
    was present
  - `README.md` and `docs/ENCRYPTION.md` document `./src/netgear_sms_poller.py` for
    `generate-key`, `health` and `reset`; all three were affected
  - Invocation through `netgear_sms_wrapper.sh` was never affected: it calls the file
    through the virtualenv interpreter (`PYTHON_VENV`), which needs neither
- **Release titles carry a headline instead of repeating the tag** - `release.yml`
  passed no `name:`, so `softprops/action-gh-release` fell back to the tag name and
  each release page was titled with its own version number and nothing else
  - Section headings now carry the headline after the date
    (`## [X.Y.Z] - YYYY-MM-DD: <headline>`), and the workflow reads it from there
  - The workflow logs a warning and falls back to the bare tag name when a heading
    carries no headline, rather than doing so silently
  - Leading blank lines are stripped from the extracted body, so a byte-for-byte
    comparison of release body and changelog section matches

### Changed
- **Removed the issue references `(#1)` through `(#7)` from the `1.2.0` section** -
  the repository has no issues and no pull requests, so GitHub rendered seven links
  that all resolve to 404
- **Corrected the retry-default claim in the `1.3.0` section** - it read as a change to
  the program defaults, which stayed at three attempts and five seconds
  (`netgear_sms_poller.py`, `SMS_RETRY_MAX_ATTEMPTS` and `SMS_RETRY_INITIAL_DELAY`
  fallbacks). What changed were the shipped values in
  `systemd/netgear-sms-poller.service` and `config/config.example.env`
- **Corrected two counts in the `1.3.1` section** - `scripts/install.sh` was seven
  published releases behind, not four, and the version drift it describes ran in three
  separate stretches rather than one run of six
- **Moved the CI pipeline entry from `1.2.0` to `1.1.0`** - `.github/workflows/lint.yml`
  and `.github/workflows/release.yml` are present in the `v1.1.0` tree
- **The `1.0.1` through `1.0.3` sections say what those versions changed** - they read
  `Bug fixes`, `Documentation updates` and `Minor bug fixes and improvements`, which is
  what a reader gets when nobody writes the entry
- Added the missing compare and tag links for `1.3.1`, `1.3.2` and `1.3.3`; the link
  block stopped at `1.3.0`

### Note on tags
Three tags in this repository do not sit on the commit their section describes, because
early releases were tagged out of order. The tags are left where they are; moving a
published tag is worse than documenting it.

- `v1.1.0` sits on the commit that added the CI workflows. The hash-based deduplication
  its section describes shipped one commit later and is first available in `v1.1.1`.
- `v1.2.0` sits on the same commit as `v1.1.1`. The encryption, retry and health-check
  work its section describes is in the following commit, which carries no tag, and is
  first available in `v1.2.1`. The compare link on the `v1.2.1` release page therefore
  shows that work as if it belonged to `1.2.1`.
- `v1.0.3` has a tag but no release, and its commit predates the commits tagged `v1.0.1`
  and `v1.0.2`.

### Migration Notes
- No breaking changes. No configuration variable, exit code, state file or systemd unit
  changed
- `src/netgear_sms_poller.py` gains mode `100755` and a `#!/usr/bin/env python3` line.
  A deployment that pins file modes will see the mode change; nothing else moved

## [1.3.2] - 2026-08-12: The wrapper and installer are executable again

### Fixed
- **`src/netgear_sms_wrapper.sh` and `scripts/install.sh` are executable again** - both were tracked with mode `100644` (no execute bit)
  - `docs/SETUP.md` and `docs/TROUBLESHOOTING.md` document running the wrapper directly as `./netgear_sms_wrapper.sh`; without the execute bit that fails with `Permission denied`
  - `scripts/install.sh` symlinks `netgear_sms_wrapper.sh` to `/usr/local/bin/netgear-sms-poller`, so a systemd unit invoking the symlink directly (rather than via `bash`) was equally affected
  - No content change - `git diff` between `v1.3.1` and this release is mode-only

## [1.3.1] - 2026-08-09: One version number, and a lint gate that cannot shift

### Fixed
- **Version is now read from a single source** - the wrapper reported `1.2.0` while the released tag was `v1.3.0`
  - `src/netgear_sms_wrapper.sh` carried `readonly SCRIPT_VERSION="1.2.0"`, one minor release behind the tag
  - `scripts/install.sh` carried a separate `# Version: 1.0.2`, seven published releases behind
  - New `VERSION` file in the repository root is the only place a version number lives
  - The wrapper resolves it at runtime and falls back to `unknown` if the file is missing or empty, so a broken version file cannot stop the service from starting
- **Startup log line now states the running version** - `=== Netgear LM1200 SMS Poller Check (v1.3.1) ===`
  - Previously the version constant was defined but read by nothing, which is why nobody noticed when it fell behind: it did so in three separate stretches (`1.0.3` held through two releases, `1.1.1` through two more, `1.2.0` through one)
  - `journalctl -u netgear-sms-poller.service` now answers "which build is running here?"
- **Ruff rule set pinned** - CI installed Ruff unpinned and the tool's default rule set is not a stable contract
  - Ruff 0.16 enables 415 rules by default; earlier versions enabled four groups
  - Result: 17 findings on an unchanged tree, i.e. the next push would have turned CI red without a single code change
  - New `ruff.toml` fixes the selection to `E4`, `E7`, `E9`, `F` - the rule groups Ruff enabled by default when CI was set up in v1.1.0, and therefore the contract the releases up to v1.3.0 were verified against
  - `lint.yml` pins `ruff==0.16.0` so the default cannot shift underneath the repository again

### Changed
- **Release notes are cut from CHANGELOG.md instead of generated from commits**
  - `generate_release_notes: true` produced a 95-byte body for v1.3.0: one compare link, nothing else, because the commit history consists of bare `vX.Y.Z` lines
  - `release.yml` now extracts the changelog section for the tag and fails the workflow if that section is empty, rather than publishing an empty release
  - `softprops/action-gh-release` upgraded from v1 to v2 (v1 runs on a deprecated Node runtime)
- Removed the changelog block duplicated in the `netgear_sms_wrapper.sh` header - `CHANGELOG.md` is the single record
- `.gitignore` now covers `*.key` and local agent tooling (`.claude/`, `CLAUDE.md`)

### Migration Notes
- No breaking changes, 100% backward compatible - no configuration variable, exit code, state file or systemd unit changed
- **Deployments that copy `src/` without the repository root must now also ship `VERSION`**, otherwise the log line reads `v unknown`. The supported install path (`scripts/install.sh`, which symlinks into the checked-out repository) is unaffected
- Anyone running `ruff` locally against this repository will see fewer findings than before; the stricter modern default is not the project's lint contract

## [1.3.0] - 2026-02-14: A modem reboot no longer triggers an alert

The poller alerted on the first failed API call. A modem reboot takes longer than one
timer interval, so a reboot that spanned a timer run produced an alert for a modem that
was on its way back up. Alerts now wait for a run of consecutive failures.

### Added
- **A modem reboot no longer produces an alert** - the wrapper counts consecutive
  failures and alerts only once the count reaches a threshold
  - `SMS_FAILURE_THRESHOLD` (default 3) in `netgear_sms_wrapper.sh`; at the timer's
    five-minute interval three failures span roughly fifteen minutes
  - The count lives in `failure_count` in the state directory and is reset by
    `reset_failure_count()` on the first successful poll
  - A recovery message is sent when the service comes back after the threshold was
    breached, so a silent recovery cannot be mistaken for a still-broken modem
  - `TimeoutStartSec` in `systemd/netgear-sms-poller.service` raised from 120s to 240s,
    because a run that retries now takes longer than the old limit allowed

### Changed
- **The shipped retry settings cover a longer outage** - `SMS_RETRY_MAX_ATTEMPTS` 3 to 5
  and `SMS_RETRY_INITIAL_DELAY` 5 to 10 in `systemd/netgear-sms-poller.service` and
  `config/config.example.env`. With the doubling backoff in `retry_with_backoff()` that
  is 10, 20, 40 and 80 seconds between attempts, so a single run tolerates about two and
  a half minutes of unreachable modem
  - The fallbacks compiled into `netgear_sms_poller.py` stay at 3 and 5; they apply only
    when neither the unit nor the config file sets the variables
- Wrapper header version: 1.1.1 to 1.2.0

### Migration Notes
- No breaking changes, 100% backward compatible
- Previous behavior (immediate alert on first failure) can be restored with `SMS_FAILURE_THRESHOLD=1`
- New file created in state directory: `failure_count` (auto-managed, safe to delete)

## [1.2.1] - 2026-01-22: The encryption and health-check release becomes installable

The work described under `1.2.0` is first available here: the `v1.2.0` tag sits on the
`v1.1.1` commit, so this is the tag that carries encrypted storage, retry logic and the
health-check mode. The changes listed below are what this release added on top of that.

### Fixed
- Ruff reported an unused variable in the modem reachability check; the discarded
  response is now bound to `_` in `netgear_sms_poller.py`

### Changed
- Removed the GitHub Stars badge from `README.md`, leaving eight

## [1.2.0] - 2026-01-21: Encrypted storage, retries and a health check

SMS bodies were stored as plaintext JSON, a transient network error ended the poll run,
and nothing outside the log said whether the gateway was healthy. This release adds all
three, each switched off or backward compatible by default.

Available from `v1.2.1`: the `v1.2.0` tag sits on the `v1.1.1` commit, and the commit
that contains this work carries no tag.

### Added
- **SMS bodies can be stored encrypted** - Fernet (AES-128-CBC plus HMAC-SHA256)
  via the optional `cryptography` package, off by default
  - New CLI mode `generate-key` writes the key; `docs/ENCRYPTION.md` covers key handling
  - Plaintext and encrypted entries coexist in the same state file, so enabling
    encryption does not require a migration or lose existing messages
- **A transient network error no longer ends the poll run** - `retry_with_backoff()`
  retries with a doubling delay, capped by `SMS_RETRY_MAX_DELAY` (default 60s)
  - `is_transient_error()` decides what is worth retrying; an authentication or JSON
    decode error fails immediately instead of burning attempts
  - Configurable through `SMS_RETRY_ENABLED`, `SMS_RETRY_MAX_ATTEMPTS` and
    `SMS_RETRY_INITIAL_DELAY`; the defaults are three attempts starting at five seconds
- **Monitoring can query the gateway's state** - new `health` CLI mode in
  `health_check()` exits 0 (healthy), 1 (degraded) or 2 (down)
  - The exit codes are what Prometheus textfile collectors and Uptime Kuma consume; no
    HTTP endpoint is opened
- **The log level is configurable** - `LOG_LEVEL` accepts DEBUG, INFO, WARNING, ERROR
  and CRITICAL; an unrecognised value falls back to INFO with a warning on stderr rather
  than failing the run
- **A missing `jq` is reported at startup** - `netgear_sms_wrapper.sh` checks for it and
  prints apt, dnf and pacman install lines, instead of failing later inside SMS parsing
- Named constants for the values that were previously inline: `HTTP_TIMEOUT_SECONDS`,
  `HASH_LIST_MAX_SIZE`, `HASH_LIST_TRIM_SIZE`

### Changed
- **The gateway runs without `cryptography` installed** - it is commented out in
  `requirements.txt` and only imported when encryption is enabled, so retry, health check
  and forwarding work on a plain Python 3.10 install

### Documentation
- New guide: `docs/ENCRYPTION.md` (encryption setup, key management)
- New guide: `docs/MONITORING.md` (health check integration)
- `README.md` and `config/config.example.env` cover the new environment variables

### Migration Notes
- No breaking changes, 100% backward compatible
- All new features are opt-in through environment variables
- Existing plaintext SMS remain readable after encryption is enabled

## [1.1.1] - 2026-01-21: Config the service user can read, and a shutdown that stops safely

An external code audit found four defects, two of which kept the service from working as
documented: `scripts/install.sh` created the config file as `root:root 0600`, which the
unprivileged service user cannot read, and a `SIGTERM` during an HTTP request was
recorded but never acted upon.

This is also the first tag that contains the hash-based deduplication described under
`1.1.0`.

### Fixed
- **The service user can read its own config** - `scripts/install.sh` created
  `/etc/netgear-sms-gateway/config.env` as `root:root 0600`, so the unit failed at
  startup; it is now created as `$USER:$USER 0600`
- **A shutdown signal now ends the run at a defined point** - `poll_sms()` checks
  `shutdown_requested` before polling and after each HTTP request, and returns exit code
  130, instead of finishing the whole cycle after the signal arrived
- **An unreadable config file is reported as such** - `netgear_sms_wrapper.sh` tests for
  `-r` before sourcing and names the file, instead of continuing with an empty
  configuration
- **A missing `jq` stops the installer** - `scripts/install.sh` treated it as a warning,
  although SMS forwarding cannot work without it

### Changed
- `signal_handler()` logs which signal it received (SIGTERM or SIGINT)
- The feature list in `README.md` states where a shutdown takes effect: "Graceful
  shutdown on SIGTERM/SIGINT (exits at safe checkpoints)"

## [1.1.0] - 2026-01-21: No duplicate SMS after a modem ID reset, and CI on every push

The modem restarts its SMS numbering after a reboot or power loss. Deduplication keyed on
that ID therefore treated already-forwarded messages as new and forwarded them again.

Available from `v1.1.1`: the `v1.1.0` tag sits on the commit that added the CI workflows,
and the commit containing the deduplication carries no tag.

### Added
- **A modem ID reset no longer replays old messages** - `is_new_sms()` decides on a
  content hash first and on the ID second
  - `compute_sms_hash()` and `compute_sms_hash_dict()` hash number, timestamp and body,
    so the same message keeps its identity across a numbering reset
  - `max_sms_id_seen` records the highest ID seen and is what detects the reset
  - `SMSPollerState` gained `processed_hashes` and `max_sms_id_seen`; a v1.0.x state file
    is migrated on the first run
- **Every push is linted** - `.github/workflows/lint.yml` runs ShellCheck against the
  Bash scripts and Ruff against the Python, and `.github/workflows/release.yml` publishes
  a release when a `v*` tag is pushed
  - `.shellcheckrc` holds the Bash rule set

### Fixed
- **A failed state save is no longer silent** - `save_sms_to_json()` logs the failure and
  `poll_sms()` returns exit code 1, so the wrapper can tell that a run lost its state
  rather than reporting success

### Migration Notes
- v1.0.x state files migrate on the first run; no manual step is required

## [1.0.4] - 2026-01-20: A security policy and a contribution guide

### Added
- `SECURITY.md` with the vulnerability reporting process
- `CONTRIBUTING.md` with development setup and code style
- `docs/README.md` as the index over the four existing guides

### Changed
- `README.md` badges expanded from three to seven and linked to the new documents

## [1.0.3] - 2026-01-17: The wrapper finds its virtualenv

An external code audit found that the wrapper looked for its interpreter in a directory
the setup guide never creates.

### Fixed
- **The wrapper finds the virtualenv the setup guide creates** - `PYTHON_VENV` in
  `netgear_sms_wrapper.sh` pointed at `${SCRIPT_DIR}/venv`, while `docs/SETUP.md` creates
  it in the repository root; it now resolves `${SCRIPT_DIR}/../venv`
- **`jq` is listed as a prerequisite** - `README.md` names it with apt and dnf install
  lines; SMS parsing depends on it
- **`LOG_LEVEL` removed from `config/config.example.env`** - the variable was documented
  but read by nothing, so setting it had no effect (it became functional in `1.2.0`)

### Changed
- `docs/SETUP.md` marks the `/usr/local/bin` symlink as required rather than optional,
  and the quick start covers the service user the unit expects
- `LICENSE` carries the copyright holder and the repository URL

### Note
This version has a tag but no GitHub release, and its commit precedes the commits tagged
`v1.0.1` and `v1.0.2`.

## [1.0.2] - 2025-12-30: License headers in the form the tooling expects

### Changed
- The `SPDX-License-Identifier` line and the copyright holder in `netgear_sms_poller.py`,
  `netgear_sms_wrapper.sh` and `scripts/install.sh` were brought into one form, with the
  repository URL replacing the profile URL

### Known issue
This release dropped the `#!/usr/bin/env python3` line from `netgear_sms_poller.py`; the
copyright header replaced it on line 1. Fixed in `1.3.3`.

## [1.0.1] - 2025-12-30: Machine-readable license headers

### Added
- `SPDX-License-Identifier: MIT` and a copyright line in `netgear_sms_poller.py`,
  `netgear_sms_wrapper.sh` and `scripts/install.sh`, so a license scanner can attribute
  the files without reading `LICENSE`

## [1.0.0] - 2025-12-30: Initial public release

### Added
- Automatic SMS polling (every 5 minutes via systemd timer)
- Optional Telegram forwarding for 2FA/OTP codes
- Local JSON storage (monthly rotated files)
- State management (no duplicates, no lost messages)
- Python 3.10+ with async/await
- systemd security hardening (ProtectSystem=strict, PrivateTmp=yes)
- Complete API documentation
- Troubleshooting guide
- Setup documentation

[Unreleased]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.4...HEAD
[1.3.4]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.3...v1.3.4
[1.3.3]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.3.0
[1.2.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.2.1
[1.2.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.2.0
[1.1.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.1
[1.1.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.1.0
[1.0.4]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.4
[1.0.3]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.3
[1.0.2]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.2
[1.0.1]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.1
[1.0.0]: https://github.com/fidpa/netgear-lm1200-sms-gateway/releases/tag/v1.0.0
