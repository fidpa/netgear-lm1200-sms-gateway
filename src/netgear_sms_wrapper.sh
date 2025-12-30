#!/bin/bash
# Copyright (c) 2025 Marc Allgeier (fidpa)
# SPDX-License-Identifier: MIT
# https://github.com/fidpa/netgear-lm1200-sms-gateway
#
# Netgear LM1200 SMS Poller - Telegram Forwarding Wrapper
# Delegates SMS polling to Python, handles Telegram alerts
#
# Version: 1.0.2 - Public Release
#
# Changelog:
#  - v1.0.2 (30.12.2025): Source-Code Header standardization
#  - v1.0.0 (30.12.2025): Public release
#    - Python handles: SMS fetch, state management, JSON storage
#    - Bash handles: Telegram forwarding (optional)
#    - Exit-code-based communication (0=no_new_sms, 1=error, 2=new_sms)
#    - Inlined alerts.sh and logging.sh (self-contained)
#
# Repository: https://github.com/fidpa/netgear-lm1200-sms-gateway
# Created: 2025-12-30

set -uo pipefail  # No -e: Use explicit error handling instead

# Symlink-robust path resolution
SCRIPT_DIR=""
if ! SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"; then
    echo "FATAL: Failed to determine script directory" >&2
    exit 1
fi
readonly SCRIPT_DIR

SCRIPT_NAME=""
if ! SCRIPT_NAME="$(basename "$0" .sh)"; then
    echo "FATAL: Failed to determine script name" >&2
    exit 1
fi
readonly SCRIPT_NAME

readonly SCRIPT_VERSION="1.0.0"

# Python script in same directory (uses venv)
readonly PYTHON_SCRIPT="${SCRIPT_DIR}/netgear_sms_poller.py"
readonly PYTHON_VENV="${SCRIPT_DIR}/venv/bin/python"

# State directory (configurable via environment)
readonly STATE_DIR="${SMS_STATE_DIR:-/var/lib/netgear-sms-gateway}"
readonly STATE_FILE="${STATE_DIR}/sms-poller-state.json"

# ============================================================================
# Inline Logging Functions (replaces logging.sh dependency)
# ============================================================================

log_info() { echo "[INFO] $*"; }
log_error() { echo "[ERROR] $*" >&2; }
log_warning() { echo "[WARN] $*" >&2; }
log_success() { echo "[OK] $*"; }

# ============================================================================
# Inline Telegram Alert Function (replaces alerts.sh dependency)
# ============================================================================

send_telegram_alert() {
    local alert_type="$1"
    local message="$2"

    # Skip if Telegram not configured
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]]; then
        log_info "Telegram not configured (skipping alert)"
        return 0
    fi

    # Simple rate limiting (default: 5 minutes)
    local rate_limit_seconds="${RATE_LIMIT_SECONDS:-300}"
    local rate_limit_file="${STATE_DIR}/.last_alert_${alert_type}"

    if [[ -f "$rate_limit_file" ]]; then
        local last_alert
        last_alert=$(cat "$rate_limit_file" 2>/dev/null || echo "0")
        local now
        now=$(date +%s)

        if (( now - last_alert < rate_limit_seconds )); then
            log_info "Telegram alert skipped (rate limit: ${rate_limit_seconds}s)"
            return 0
        fi
    fi

    # Send via Telegram Bot API
    local telegram_url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
    local telegram_prefix="${TELEGRAM_PREFIX:-[SMS Gateway]}"
    local full_message="${telegram_prefix} ${message}"

    if curl -s -X POST "$telegram_url" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=${full_message}" \
        -d "parse_mode=HTML" >/dev/null 2>&1; then

        # Update rate limit timestamp
        echo "$(date +%s)" > "$rate_limit_file"
        log_info "Telegram alert sent [TYPE=${alert_type}]"
    else
        log_warning "Failed to send Telegram alert"
    fi
}

# ============================================================================
# Configuration Loading
# ============================================================================

# Load credentials from config file (if exists)
CONFIG_FILE="${CONFIG_FILE:-/etc/netgear-sms-gateway/config.env}"
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    log_info "Loaded configuration from ${CONFIG_FILE}"
else
    log_warning "Config file not found: ${CONFIG_FILE}"
fi

# Check if password is configured
if [[ -z "${NETGEAR_ADMIN_PASSWORD:-}" ]]; then
    log_error "NETGEAR_ADMIN_PASSWORD not set in ${CONFIG_FILE}"
    exit 1
fi

# Export password for Python script
export NETGEAR_ADMIN_PASSWORD

# Export other environment variables for Python
export NETGEAR_IP="${NETGEAR_IP:-192.168.0.201}"
export SMS_STATE_DIR="${STATE_DIR}"

# ============================================================================
# Signal Handlers
# ============================================================================

cleanup() {
    log_info "Shutting down"
    # NO exit here - let signal handler return
}

trap cleanup SIGTERM SIGINT

# ============================================================================
# Main SMS Poller Logic
# ============================================================================

main() {
    log_info "=== Netgear LM1200 SMS Poller Check ==="

    # Run Python SMS poller
    # Python returns: 0=no_new_sms, 1=error, 2=new_sms_forwarded
    local sms_output
    sms_output=$("$PYTHON_VENV" "$PYTHON_SCRIPT" check 2>&1)
    local sms_exit=$?

    # Log Python script output
    echo "$sms_output" | while IFS= read -r line; do
        log_info "Python: $line"
    done

    # Handle exit codes from Python
    case $sms_exit in
        0)
            # No new SMS
            log_info "No new SMS received"
            return 0
            ;;

        1)
            # Error (authentication failed, API error, etc.)
            log_error "SMS poller failed"
            send_telegram_alert "sms_poller_error" "❌ SMS Poller Error: API access failed"
            return 1
            ;;

        2)
            # New SMS received - forward via Telegram
            log_success "New SMS received, forwarding via Telegram"

            # Read latest SMS from state file
            if [[ ! -f "$STATE_FILE" ]]; then
                log_error "State file not found: $STATE_FILE"
                send_telegram_alert "sms_state_error" "❌ SMS received, but state file missing!"
                return 1
            fi

            # Extract SMS details from state file
            local sms_number sms_time sms_content
            if ! sms_number=$(jq -r '.latest_sms.number // "Unknown"' "$STATE_FILE" 2>/dev/null); then
                log_error "Failed to extract SMS number from state file"
                return 1
            fi

            if ! sms_time=$(jq -r '.latest_sms.time // "Unknown"' "$STATE_FILE" 2>/dev/null); then
                log_error "Failed to extract SMS time from state file"
                return 1
            fi

            if ! sms_content=$(jq -r '.latest_sms.content // ""' "$STATE_FILE" 2>/dev/null); then
                log_error "Failed to extract SMS content from state file"
                return 1
            fi

            # Format Telegram message
            # Use multiline format for better readability
            local telegram_message
            telegram_message="📱 New SMS

From: ${sms_number}
Time: ${sms_time}

${sms_content}"

            # Send via Telegram (rate-limited)
            send_telegram_alert "new_sms" "$telegram_message"

            log_success "SMS forwarded via Telegram: From ${sms_number}"
            return 0
            ;;

        130)
            # SIGINT (Ctrl+C)
            log_warning "SMS poller interrupted by user"
            return 130
            ;;

        *)
            # Unexpected exit code
            log_error "Unexpected exit code from Python: $sms_exit"
            send_telegram_alert "sms_unexpected_error" "❌ SMS Poller: Unexpected error (Exit Code: $sms_exit)"
            return 1
            ;;
    esac
}

# Run main function if script is executed directly
[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
