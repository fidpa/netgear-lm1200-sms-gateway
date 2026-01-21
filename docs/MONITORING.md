# Monitoring & Health Check Guide

## Health Check Endpoint

The SMS gateway provides a `health` CLI mode for monitoring integration.

**Exit Codes**:
- **0 (HEALTHY)**: Recent check, state valid
- **1 (DEGRADED)**: Stale state (>30min), minor issues
- **2 (DOWN)**: State missing/corrupt, modem unreachable

## Basic Usage

```bash
/usr/local/bin/netgear-sms-poller health
echo $?  # Check exit code
```

Output examples:
```
HEALTHY: Last check 45s ago, 127 SMS received
```

```
DEGRADED: Stale state (last check 1832s ago, threshold 1800s)
```

```
DOWN: State file missing
```

## Integration Examples

### Prometheus Node Exporter

Create `/usr/local/bin/sms-gateway-health-check.sh`:
```bash
#!/bin/bash
/usr/local/bin/netgear-sms-poller health
exit_code=$?
echo "sms_gateway_healthy{status=\"${exit_code}\"} 1" > /var/lib/node_exporter/textfile_collector/sms_gateway.prom
```

Add systemd timer (every 5 minutes):
```ini
[Unit]
Description=SMS Gateway Health Check

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

Query in Prometheus:
```promql
sms_gateway_healthy{status="0"} == 1  # Healthy
sms_gateway_healthy{status="1"} == 1  # Degraded
sms_gateway_healthy{status="2"} == 1  # Down
```

### Uptime Kuma

**HTTP Keyword Monitor**:
1. Create wrapper script that returns HTTP response:
```bash
#!/bin/bash
/usr/local/bin/netgear-sms-poller health
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "HTTP/1.1 200 OK"
    echo "Content-Type: text/plain"
    echo ""
    echo "HEALTHY"
else
    echo "HTTP/1.1 503 Service Unavailable"
    echo "Content-Type: text/plain"
    echo ""
    echo "DEGRADED or DOWN"
fi
```

2. Add to Uptime Kuma:
   - Type: HTTP(s) - Keyword
   - URL: http://localhost:8080/sms-gateway-health (via wrapper)
   - Keyword: HEALTHY

### systemd Watchdog (Future)

```ini
[Service]
WatchdogSec=300s
ExecStartPre=/usr/local/bin/netgear-sms-poller health
```

## Configuration

### Stale Threshold

Default: 30 minutes (1800 seconds)

Adjust in `/etc/netgear-sms-gateway/config.env`:
```env
HEALTH_CHECK_STALE_THRESHOLD=3600  # 1 hour
```

### Modem Ping (Optional)

Enable modem reachability check (adds 5s HTTP ping):
```env
HEALTH_CHECK_PING_MODEM=true
```

**Trade-off**:
- ✅ Detects modem offline faster
- ❌ Health check takes 5s instead of <1ms

## Alerting

### Prometheus Alert Rules

```yaml
groups:
  - name: sms_gateway
    rules:
      - alert: SMSGatewayDown
        expr: sms_gateway_healthy{status="2"} == 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "SMS Gateway is DOWN"

      - alert: SMSGatewayDegraded
        expr: sms_gateway_healthy{status="1"} == 1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "SMS Gateway is DEGRADED"
```

### Telegram Alerts

Via Alertmanager or custom script:
```bash
#!/bin/bash
if /usr/local/bin/netgear-sms-poller health | grep -q "DOWN"; then
    curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=🚨 SMS Gateway DOWN"
fi
```

## Troubleshooting

### False Positives (DEGRADED)

**Cause**: Timer execution delayed (systemd load)

**Solution**: Increase stale threshold:
```env
HEALTH_CHECK_STALE_THRESHOLD=2400  # 40 minutes
```

### Health Check Times Out

**Cause**: `HEALTH_CHECK_PING_MODEM=true` but modem unreachable

**Solution**: Disable modem ping:
```env
HEALTH_CHECK_PING_MODEM=false
```
