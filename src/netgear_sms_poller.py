#!/usr/bin/env python3
"""
Netgear LM1200 SMS Poller (Authenticated API Version)

Polls LM1200 modem for incoming SMS messages and forwards them via Telegram.
Stores SMS locally in monthly-rotated JSON files for backup/history.

Version: 1.0.0 - Initial Release

Use Case: Automatically forward 2FA/OTP codes via Telegram

Features:
 - Authenticated API access (aiohttp + CookieJar)
 - State management (last_processed_sms_id tracking)
 - Monthly-rotated JSON storage (/var/lib/netgear-sms-gateway/sms-inbox-YYYY-MM.json)
 - Telegram forwarding via Bash wrapper (exit code 2 signals new SMS)
 - Signal handling (SIGTERM/SIGINT)
 - Python 3.10+ type hints

Returns (check mode):
 - Exit code 0: No new SMS
 - Exit code 1: Error (authentication failed, API error)
 - Exit code 2: New SMS forwarded (triggers Telegram alert in wrapper)
 - Exit code 130: SIGINT (KeyboardInterrupt)

CLI Modes:
 - check: Standard polling mode (called by timer)
 - status: Display current state (last processed ID, total count)
 - reset: Reset state (emergency use)
 - list: List all SMS in modem inbox (debug)

Repository: https://github.com/fidpa/netgear-lm1200-sms-gateway
Created: 2025-12-30
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simple format, bash wrapper adds prefixes
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration (environment variables)
NETGEAR_IP = os.environ.get("NETGEAR_IP", "192.168.0.201")
NETGEAR_PASSWORD = os.environ.get("NETGEAR_ADMIN_PASSWORD", "")
API_URL = f"http://{NETGEAR_IP}/api/model.json"
LOGIN_URL = f"http://{NETGEAR_IP}/Forms/config"

# State management (configurable paths)
STATE_DIR = os.getenv("SMS_STATE_DIR", "/var/lib/netgear-sms-gateway")
STATE_FILE = Path(STATE_DIR) / "sms-poller-state.json"
SMS_STORAGE_DIR = Path(STATE_DIR)

# Global shutdown flag
shutdown_requested = False

@dataclass
class SMSMessage:
    """
    Represents a single SMS message.

    Attributes:
        id: Unique SMS ID from modem
        number: Sender phone number
        time: Timestamp string from modem
        content: SMS message text
        read: Whether SMS was marked as read
    """
    id: int
    number: str
    time: str
    content: str
    read: bool

@dataclass
class SMSPollerState:
    """
    Persistent state for SMS poller.

    Attributes:
        last_processed_sms_id: ID of last processed SMS (track new messages)
        last_check: Unix timestamp of last check
        total_sms_received: Total count of SMS received
        last_sms_timestamp: Unix timestamp of last SMS received
        latest_sms: Latest SMS for Telegram forwarding (dict format)
    """
    last_processed_sms_id: int = 0
    last_check: float = 0.0
    total_sms_received: int = 0
    last_sms_timestamp: float = 0.0
    latest_sms: dict[str, str] = field(default_factory=dict)

    def update_with_new_sms(self, sms: SMSMessage) -> None:
        """Update state with newly received SMS."""
        self.last_processed_sms_id = max(self.last_processed_sms_id, sms.id)
        self.last_check = time.time()
        self.total_sms_received += 1
        self.last_sms_timestamp = time.time()
        # Store latest SMS for Telegram forwarding
        self.latest_sms = {
            "number": sms.number,
            "time": sms.time,
            "content": sms.content
        }

    def mark_check(self) -> None:
        """Mark check timestamp (no new SMS)."""
        self.last_check = time.time()

def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    global shutdown_requested
    logger.warning("Shutdown signal received")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def get_api_data(session: aiohttp.ClientSession) -> dict:
    """
    Fetch data from /api/model.json endpoint.

    Args:
        session: aiohttp ClientSession

    Returns:
        dict: JSON data from API

    Raises:
        Exception: On HTTP error or invalid response
    """
    async with session.get(API_URL, allow_redirects=True, timeout=10) as response:
        if response.status == 200:
            # LM1200 returns JSON with text/plain content-type, parse manually
            text = await response.text()
            return json.loads(text)
        else:
            raise Exception(f"HTTP {response.status}: {await response.text()}")

async def login(session: aiohttp.ClientSession) -> bool:
    """
    Login to modem and create authenticated session.

    Args:
        session: aiohttp ClientSession with CookieJar

    Returns:
        bool: True if login successful

    Raises:
        Exception: On login failure
    """
    if not NETGEAR_PASSWORD:
        raise Exception("NETGEAR_ADMIN_PASSWORD not set")

    # Get security token from API
    data = await get_api_data(session)
    token = data.get('session', {}).get('secToken', '')

    if not token:
        raise Exception("No security token found in API response")

    # Login via Forms/config (creates session cookie)
    login_data = {
        'session.password': NETGEAR_PASSWORD,
        'token': token
    }

    async with session.post(LOGIN_URL, data=login_data,
                           allow_redirects=False, timeout=10) as response:
        # Accept 200, 204 (No Content - success), or 302 (redirect)
        if response.status not in [200, 204, 302]:
            response_text = await response.text()
            raise Exception(f"Login failed with HTTP {response.status}: {response_text[:200]}")

        return True

async def fetch_sms_list(session: aiohttp.ClientSession) -> list[SMSMessage]:
    """
    Fetch SMS list from authenticated API.

    Args:
        session: Authenticated aiohttp ClientSession

    Returns:
        list[SMSMessage]: List of SMS messages from modem

    Notes:
        SMS data is in ['sms']['msgs'] from /api/model.json
        Format: [{"id": "1", "sender": "+49...", "rxTime": "...", "text": "...", "read": false}, ...]
    """
    try:
        # Get authenticated API data
        data = await get_api_data(session)

        # Extract SMS list
        sms_data = data.get('sms', {}).get('msgs', [])

        if not sms_data:
            logger.info("No SMS in modem inbox")
            return []

        # Parse SMS messages
        sms_list = []
        for msg in sms_data:
            try:
                sms = SMSMessage(
                    id=int(msg.get('id', 0)),
                    number=msg.get('sender', ''),      # API uses 'sender', not 'number'
                    time=msg.get('rxTime', ''),        # API uses 'rxTime', not 'time'
                    content=msg.get('text', ''),       # API uses 'text', not 'content'
                    read=bool(msg.get('read', False))
                )
                sms_list.append(sms)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse SMS message: {e}")
                continue

        logger.info(f"Found {len(sms_list)} SMS in modem inbox")
        return sms_list

    except KeyError as e:
        logger.error(f"SMS data not found in API response: {e}")
        return []

def save_sms_to_json(sms_list: list[SMSMessage]) -> bool:
    """
    Save SMS to monthly-rotated JSON file.

    Args:
        sms_list: List of SMS messages to save

    Returns:
        bool: True if save successful

    Notes:
        Format: /var/lib/netgear-sms-gateway/sms-inbox-YYYY-MM.json
        Appends to existing file (keeps history)
    """
    if not sms_list:
        return True

    try:
        # Get current month for filename
        current_month = datetime.now().strftime('%Y-%m')
        sms_file = SMS_STORAGE_DIR / f"sms-inbox-{current_month}.json"

        # Ensure storage directory exists
        SMS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing SMS (if file exists)
        existing_sms = []
        if sms_file.exists():
            try:
                existing_sms = json.loads(sms_file.read_text())
            except json.JSONDecodeError:
                logger.warning(f"Corrupted SMS file {sms_file}, starting fresh")
                existing_sms = []

        # Convert SMSMessage to dict
        new_sms = [asdict(sms) for sms in sms_list]

        # Merge (avoid duplicates by ID)
        existing_ids = {msg['id'] for msg in existing_sms}
        for sms in new_sms:
            if sms['id'] not in existing_ids:
                existing_sms.append(sms)

        # Atomic write (temp file + rename)
        temp_file = sms_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(existing_sms, indent=2, ensure_ascii=False))
        temp_file.replace(sms_file)

        logger.info(f"Saved {len(new_sms)} new SMS to {sms_file}")
        return True

    except OSError as e:
        logger.error(f"Failed to save SMS to JSON: {e}")
        return False

def load_state() -> SMSPollerState:
    """
    Load SMS poller state from JSON file.

    Returns:
        SMSPollerState: Loaded state or default if file doesn't exist

    Notes:
        Falls back to default state if file doesn't exist or is corrupted.
        Ensures state directory exists.
    """
    # Ensure state directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE.exists():
        logger.info("No state file found, initializing new state")
        return SMSPollerState()

    try:
        data = json.loads(STATE_FILE.read_text())
        # Convert dict to dataclass (handles missing fields gracefully)
        state = SMSPollerState(**{k: v for k, v in data.items() if k in SMSPollerState.__dataclass_fields__})
        logger.debug(f"Loaded state: last_processed_sms_id={state.last_processed_sms_id}, total={state.total_sms_received}")
        return state
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to load state file: {e}, using defaults")
        return SMSPollerState()

def save_state(state: SMSPollerState) -> bool:
    """
    Save SMS poller state to JSON file (atomic write).

    Args:
        state: SMSPollerState to save

    Returns:
        bool: True if save successful

    Notes:
        Uses atomic write pattern (temp file + rename) to prevent corruption.
        Creates parent directory if needed.
    """
    try:
        # Ensure state directory exists
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write pattern: write to temp, then rename
        temp_file = STATE_FILE.with_suffix('.tmp')
        temp_file.write_text(json.dumps(asdict(state), indent=2))
        temp_file.replace(STATE_FILE)

        logger.debug(f"State saved: last_processed_sms_id={state.last_processed_sms_id}")
        return True
    except OSError as e:
        logger.error(f"Failed to save state: {e}")
        return False

async def poll_sms() -> int:
    """
    Poll modem for new SMS and process them.

    Returns:
        Exit code:
            0: No new SMS
            1: Error (authentication failed, API error)
            2: New SMS forwarded (triggers Telegram alert in wrapper)

    Flow:
        1. Login to modem (authenticated session)
        2. Fetch SMS list from API
        3. Load current state (last_processed_sms_id)
        4. Filter NEW SMS (id > last_processed_sms_id)
        5. Save new SMS to monthly JSON file
        6. Update state with latest SMS
        7. Return exit code (2 if new SMS, 0 if none)
    """
    # Load current state
    state = load_state()

    logger.info(f"Last processed SMS ID: {state.last_processed_sms_id}")

    # Use CookieJar for session management (needed for authentication)
    jar = aiohttp.CookieJar(unsafe=True)

    try:
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            # Login to get authenticated session
            logger.info("Logging in to modem...")
            await login(session)
            logger.info("Login successful")

            # Fetch SMS list
            sms_list = await fetch_sms_list(session)

            if not sms_list:
                # No SMS in inbox
                state.mark_check()
                save_state(state)
                logger.info("No SMS in modem inbox")
                return 0

            # Filter NEW SMS (id > last_processed_sms_id)
            new_sms = [sms for sms in sms_list if sms.id > state.last_processed_sms_id]

            if not new_sms:
                # No new SMS since last check
                state.mark_check()
                save_state(state)
                logger.info(f"No new SMS (all {len(sms_list)} already processed)")
                return 0

            # Process new SMS
            logger.info(f"Found {len(new_sms)} new SMS")

            # Save to monthly JSON file
            save_sms_to_json(new_sms)

            # Update state with latest SMS (for Telegram forwarding)
            # Process in order, update state with the LAST one
            for sms in new_sms:
                logger.info(f"  SMS #{sms.id} from {sms.number}: {sms.content[:50]}...")
                state.update_with_new_sms(sms)

            # Save updated state
            save_state(state)

            logger.info(f"Processed {len(new_sms)} new SMS, last_id={state.last_processed_sms_id}")

            # Exit code 2 signals "new SMS" to Bash wrapper
            return 2

    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to poll SMS: {e}")
        return 1

def show_status() -> int:
    """
    Display current SMS poller state.

    Returns:
        Exit code: Always 0
    """
    state = load_state()

    print("Netgear LM1200 SMS Poller Status")
    print(f"{'='*40}")
    print(f"Last Processed SMS ID: {state.last_processed_sms_id}")
    print(f"Total SMS Received: {state.total_sms_received}")

    if state.last_check > 0:
        last_check_str = datetime.fromtimestamp(state.last_check).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_check_str = "Never"
    print(f"Last Check: {last_check_str}")

    if state.last_sms_timestamp > 0:
        last_sms_str = datetime.fromtimestamp(state.last_sms_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_sms_str = "Never"
    print(f"Last SMS: {last_sms_str}")

    if state.latest_sms:
        print(f"\nLatest SMS:")
        print(f"  From: {state.latest_sms.get('number', 'N/A')}")
        print(f"  Time: {state.latest_sms.get('time', 'N/A')}")
        print(f"  Text: {state.latest_sms.get('content', 'N/A')[:50]}...")

    return 0

def reset_state() -> int:
    """
    Reset SMS poller state (emergency use).

    Returns:
        Exit code: 0 if success, 1 if failed
    """
    state = SMSPollerState()
    if save_state(state):
        logger.info("State reset successfully")
        print("State reset: last_processed_sms_id=0")
        return 0
    else:
        logger.error("Failed to reset state")
        return 1

async def list_sms() -> int:
    """
    List all SMS in modem inbox (debug mode).

    Returns:
        Exit code: 0 if success, 1 if failed
    """
    jar = aiohttp.CookieJar(unsafe=True)

    try:
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            # Login
            await login(session)
            logger.info("Login successful")

            # Fetch SMS
            sms_list = await fetch_sms_list(session)

            if not sms_list:
                print("No SMS in modem inbox")
                return 0

            print(f"\nSMS Inbox ({len(sms_list)} messages):")
            print(f"{'='*60}")

            for sms in sms_list:
                print(f"ID: {sms.id}")
                print(f"From: {sms.number}")
                print(f"Time: {sms.time}")
                print(f"Read: {'Yes' if sms.read else 'No'}")
                print(f"Text: {sms.content}")
                print(f"{'-'*60}")

            return 0

    except Exception as e:
        logger.error(f"Failed to list SMS: {e}")
        return 1

def main() -> int:
    """
    Main entry point with CLI argument parsing.

    Returns:
        Exit code (0=no_new_sms, 1=error, 2=new_sms_forwarded, 130=SIGINT)
    """
    parser = argparse.ArgumentParser(
        description="Netgear LM1200 SMS Poller",
        epilog="""
Examples:
  %(prog)s check                  # Poll for new SMS (standard mode)
  %(prog)s status                 # Show current state
  %(prog)s reset                  # Reset state (emergency)
  %(prog)s list                   # List all SMS in modem inbox
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'action',
        choices=['check', 'status', 'reset', 'list'],
        nargs='?',
        default='check',
        help='Action to perform (default: check)'
    )

    args = parser.parse_args()

    try:
        # Handle actions
        if args.action == 'check':
            return asyncio.run(poll_sms())
        elif args.action == 'status':
            return show_status()
        elif args.action == 'reset':
            return reset_state()
        elif args.action == 'list':
            return asyncio.run(list_sms())
        else:
            logger.error(f"Unknown action: {args.action}")
            return 1

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"FATAL: Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
