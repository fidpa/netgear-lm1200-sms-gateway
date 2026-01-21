# SMS Encryption Guide

## Overview

Netgear LM1200 SMS Gateway supports **optional** AES-256 encryption for SMS content stored on disk.

**Requirements**: `pip install cryptography>=42.0.0` (or `apt install python3-cryptography`)

**Note**: Gateway works perfectly without encryption. This is an opt-in security feature.

**Use Case**: 2FA/OTP codes contain sensitive data → encrypt at rest

**Algorithm**: Fernet (symmetric encryption, based on AES-128-CBC + HMAC-SHA256)

## Setup

### 1. Generate Encryption Key

```bash
cd /path/to/netgear-lm1200-sms-gateway
source venv/bin/activate
./src/netgear_sms_poller.py generate-key
```

Output:
```
Generated Fernet encryption key:
gAAAAABh5... (44 characters)

Save this key securely:
  sudo sh -c 'echo "gAAAAABh5..." > /etc/netgear-sms-gateway/.encryption.key'
  sudo chmod 600 /etc/netgear-sms-gateway/.encryption.key
```

### 2. Save Key Securely

```bash
# Copy key from output above
sudo sh -c 'echo "YOUR_KEY_HERE" > /etc/netgear-sms-gateway/.encryption.key'
sudo chmod 600 /etc/netgear-sms-gateway/.encryption.key
sudo chown <service-user>:<service-group> /etc/netgear-sms-gateway/.encryption.key
```

### 3. Enable Encryption

Edit `/etc/netgear-sms-gateway/config.env`:
```env
SMS_ENCRYPTION_ENABLED=true
```

### 4. Restart Service

```bash
sudo systemctl restart netgear-sms-poller.service
```

## Verification

Check state file:
```bash
sudo cat /var/lib/netgear-sms-gateway/sms-poller-state.json | jq .latest_sms.content
# Should show: "ENC:gAAAAABh5..." (encrypted)
```

Check Telegram forwarding still works (wrapper auto-decrypts).

## Key Management

### Backup Key

```bash
sudo cp /etc/netgear-sms-gateway/.encryption.key ~/backup-encryption-key.txt
chmod 600 ~/backup-encryption-key.txt
```

Store in password manager (Vaultwarden, 1Password, etc.)

### Rotate Key

1. Generate new key
2. Disable encryption temporarily
3. Wait for all new SMS to be received (plaintext)
4. Enable encryption with new key
5. Old encrypted SMS will remain encrypted (hybrid state)

**Note**: Key rotation doesn't re-encrypt existing SMS archives.

## Migration

### From Plaintext → Encrypted

No migration needed! Existing plaintext SMS remain readable.

**Hybrid State Support**:
- Old SMS: Plaintext
- New SMS: Encrypted (ENC: prefix)
- Wrapper auto-detects format

### From Encrypted → Plaintext

```bash
# Disable encryption
SMS_ENCRYPTION_ENABLED=false

# New SMS will be plaintext
# Old encrypted SMS remain encrypted (frozen state)
```

## Troubleshooting

### Error: "SMS_ENCRYPTION_ENABLED=true but no key found"

**Solution**: Key file missing or wrong path
```bash
ls -la /etc/netgear-sms-gateway/.encryption.key
# Should exist with chmod 600
```

### Error: "Decryption failed: Invalid key or corrupted data"

**Solution**: Wrong key or corrupted state file
```bash
# Verify key matches (re-generate if lost)
./src/netgear_sms_poller.py generate-key

# Emergency: Reset state (loses SMS history)
./src/netgear_sms_poller.py reset
```

## Security Considerations

**Key Storage**:
- ✅ Key file: chmod 600, service-user-owned
- ✅ systemd LoadCredential: `LoadCredential=encryption-key:/path/to/key`
- ❌ ENV var in service file: NOT recommended (visible in systemctl show)

**Backup Strategy**:
- Store key in password manager
- Test restore procedure regularly

**Encryption Scope**:
- ✅ SMS content (.content field)
- ❌ Phone numbers (.number field) - NOT encrypted (needed for deduplication)
- ❌ Timestamps (.time field) - NOT encrypted

**Limitations**:
- Encrypted SMS only protects at-rest data
- Telegram forwarding transmits plaintext (via HTTPS)
- Modem API uses HTTP (plaintext over wire)
