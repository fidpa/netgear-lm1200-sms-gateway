# Upgrade Guide: v1.0.x → v1.1.0

## ⚡ TL;DR
v1.1.0 introduces hash-based SMS deduplication. Upgrade is **automatic** and **backward compatible**.

## 🎯 What's New

### Hash-based Deduplication
- **Problem**: Modem ID resets (e.g., after reboot) caused duplicate SMS
- **Solution**: Hash-based tracking via `number + time + content`
- **Impact**: No more duplicates, even after ID reset

### ID Reset Detection
- New `max_sms_id_seen` field tracks highest ID ever seen
- Detects and logs ID resets automatically
- Continues processing without data loss

## 🚀 Upgrade Process

### Automatic Migration (Recommended)

1. **Stop service**:
   ```bash
   sudo systemctl stop netgear-sms-poller.timer
   sudo systemctl stop netgear-sms-poller.service
   ```

2. **Update code**:
   ```bash
   cd /path/to/netgear-lm1200-sms-gateway
   git pull origin main
   git checkout v1.1.0
   ```

3. **Update systemd service** (if needed):
   ```bash
   sudo cp systemd/netgear-sms-poller.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

4. **Start service**:
   ```bash
   sudo systemctl start netgear-sms-poller.timer
   ```

5. **Verify migration**:
   ```bash
   journalctl -u netgear-sms-poller.service -n 20
   # Look for: "Migrated state: added processed_hashes field"
   # Look for: "Migrated state: added max_sms_id_seen field"
   ```

### State File Changes

**Before (v1.0.x)**:
```json
{
  "last_processed_sms_id": 42,
  "last_check": 1737475200.0,
  "total_sms_received": 5,
  "last_sms_timestamp": 1737475000.0,
  "latest_sms": { ... }
}
```

**After (v1.1.0)**:
```json
{
  "last_processed_sms_id": 42,
  "max_sms_id_seen": 42,
  "last_check": 1737475200.0,
  "total_sms_received": 5,
  "last_sms_timestamp": 1737475000.0,
  "latest_sms": { ... },
  "processed_hashes": ["abc123...", "def456..."]
}
```

## 🔄 Rollback (if needed)

If you encounter issues with v1.1.0, you can rollback:

```bash
sudo systemctl stop netgear-sms-poller.timer
cd /path/to/netgear-lm1200-sms-gateway
git checkout v1.0.4

# Restore service
sudo cp systemd/netgear-sms-poller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start netgear-sms-poller.timer
```

**Note**: v1.1.0 state files are backward compatible. v1.0.x will ignore `processed_hashes` and `max_sms_id_seen` fields.

## 🐛 Troubleshooting

### Migration not applied

**Symptom**: No "Migrated state" log entries

**Fix**: Check Python version (requires 3.10+)
```bash
python3 --version  # Should be ≥ 3.10
```

### Duplicate SMS after upgrade

**Symptom**: Receiving duplicate SMS notifications

**Cause**: State file not loading correctly

**Fix**: Verify state file permissions
```bash
sudo ls -la /var/lib/netgear-sms-gateway/sms-poller-state.json
# Should be readable by service user
```

### Exit code 1 errors

**Symptom**: Service fails with exit code 1

**Cause**: State save failures (new in v1.1.0)

**Fix**: Check StateDirectory permissions
```bash
sudo journalctl -u netgear-sms-poller.service | grep "Failed to save state"
```

## 📚 Additional Resources

- [CHANGELOG.md](../CHANGELOG.md) - Full list of changes
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
