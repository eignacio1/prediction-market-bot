#!/usr/bin/env bash
# VPS one-time setup script — Ubuntu 22.04 LTS
# Installs Python 3.11, project dependencies, and directory structure.
# Run as root on a fresh droplet.

set -euo pipefail

echo "=== Prediction Market Bot — VPS Setup ==="
echo "OS: $(lsb_release -ds 2>/dev/null || echo 'unknown')"
echo ""

# ---------------------------------------------------------------------------
# System packages
# ---------------------------------------------------------------------------
echo "[1/5] Installing system packages..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    python3.11 python3.11-pip python3.11-venv \
    git curl wget ca-certificates \
    build-essential libssl-dev \
    2>&1 | grep -E '(Get:|Unpacking|Setting up|done)'

# Verify OpenSSL version (must be 3.x for Kalshi TLS)
python3.11 -c "import ssl; print('[OK] OpenSSL:', ssl.OPENSSL_VERSION)"

# ---------------------------------------------------------------------------
# Project directory
# ---------------------------------------------------------------------------
echo "[2/5] Creating project directory..."
mkdir -p /opt/prediction-market-bot/{logs,models,exp_output/EXP-005,qualitative_data/pam_v4}
chmod 750 /opt/prediction-market-bot

# ---------------------------------------------------------------------------
# Python packages
# ---------------------------------------------------------------------------
echo "[3/5] Installing Python packages..."
pip3.11 install --quiet --upgrade pip
pip3.11 install --quiet \
    "scikit-learn==1.4.2" \
    "pandas>=2.0" \
    "numpy>=1.24,<2.0" \
    "requests>=2.31" \
    "jsonlines>=4.0" \
    "joblib>=1.3" \
    "nba_api>=1.3"

# Verify sklearn version matches training environment
python3.11 -c "
import sklearn
assert sklearn.__version__ == '1.4.2', f'sklearn version mismatch: {sklearn.__version__}'
print('[OK] sklearn 1.4.2 confirmed')
"

# ---------------------------------------------------------------------------
# Log rotation
# ---------------------------------------------------------------------------
echo "[4/5] Setting up log rotation..."
cat > /etc/logrotate.d/pred-market-bot << 'EOF'
/opt/prediction-market-bot/logs/*.jsonl {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
}
/opt/prediction-market-bot/logs/pregame_*.json {
    daily
    rotate 90
    compress
    missingok
    notifempty
}
EOF

# ---------------------------------------------------------------------------
# Environment file (operator must fill in secrets)
# ---------------------------------------------------------------------------
echo "[5/5] Creating environment template..."
if [ ! -f /opt/prediction-market-bot/.env ]; then
    cat > /opt/prediction-market-bot/.env << 'EOF'
# ENV-02 — Paper Trading Environment
# SECURITY: chmod 600 this file. Never commit. Never log.
BOT_ENV=paper
LOG_DIR=/opt/prediction-market-bot/logs
VENUE_API_KEY=REPLACE_WITH_YOUR_KALSHI_READ_ONLY_KEY
# BOT_C4_ACTIVE must NOT be set in ENV-02
EOF
    chmod 600 /opt/prediction-market-bot/.env
    echo "  .env template created — fill in VENUE_API_KEY before running"
fi

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Deploy code: git clone <repo> /opt/prediction-market-bot"
echo "  2. Deploy model: scp models/prod_model.joblib <VPS>:/opt/prediction-market-bot/models/"
echo "  3. Fill in .env: nano /opt/prediction-market-bot/.env"
echo "  4. Run health check: bash /opt/prediction-market-bot/deploy/healthcheck.sh"
echo "  5. Install cron: crontab /opt/prediction-market-bot/deploy/cron.conf"
