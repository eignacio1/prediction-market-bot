#!/usr/bin/env bash
# Install MLB T4 systemd service + timer (replaces cron line).
# Run as root on VPS: bash /opt/prediction-market-bot/deploy/install_systemd_t4_mlb.sh
set -euo pipefail

PROJ=/opt/prediction-market-bot
SYSDIR=/etc/systemd/system

echo "=== Installing MLB T4 systemd service ==="

# Stop and disable any running instance before replacing unit files
if systemctl is-active --quiet t4-mlb.service 2>/dev/null; then
    echo "Stopping existing t4-mlb.service..."
    systemctl stop t4-mlb.service || true
fi

# Copy unit files
cp "$PROJ/deploy/t4-mlb.service" "$SYSDIR/t4-mlb.service"
cp "$PROJ/deploy/t4-mlb.timer"   "$SYSDIR/t4-mlb.timer"
echo "Unit files installed to $SYSDIR/"

# Reload systemd config
systemctl daemon-reload

# Enable: service starts on boot; timer fires at 13:00 UTC daily
systemctl enable t4-mlb.service t4-mlb.timer
echo "t4-mlb.service + t4-mlb.timer enabled"

# Start the timer (manages scheduled daily starts)
systemctl start t4-mlb.timer
echo "Timer started — next scheduled: $(systemctl show t4-mlb.timer -p NextElapseUSecRealtime --value)"

# Start the service NOW (don't wait until 13:00 UTC)
systemctl start t4-mlb.service
echo "t4-mlb.service started"

echo ""
echo "=== Status ==="
systemctl status t4-mlb.service --no-pager -l | head -20
echo ""
systemctl status t4-mlb.timer --no-pager | head -10

echo ""
echo "=== Operator commands ==="
echo "  Stop (no auto-restart): systemctl stop t4-mlb.service"
echo "  Restart manually:       systemctl restart t4-mlb.service"
echo "  Disable timer:          systemctl disable t4-mlb.timer && systemctl stop t4-mlb.timer"
echo "  View live log:          journalctl -u t4-mlb -f"
echo "  OR: tail -f $PROJ/logs/t4_mlb_live_cron.log"
