#!/usr/bin/env bash
# Pre-flight health check for VPS PIPE-02 deployment.
# Run before enabling cron, and optionally daily before game time.

set -uo pipefail

PROJ="/opt/prediction-market-bot"
PYTHON="$PROJ/venv/bin/python"
ERRORS=0

pass() { echo "[OK] $1"; }
fail() { echo "[FAIL] $1"; ERRORS=$((ERRORS+1)); }
warn() { echo "[WARN] $1"; }

echo "=== PIPE-02 Health Check ==="
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""

# 1. Python 3.11 with OpenSSL 3.x
if $PYTHON -c "import ssl; v=ssl.OPENSSL_VERSION; assert '3.' in v, v" 2>/dev/null; then
    OPENSSL_VER=$($PYTHON -c "import ssl; print(ssl.OPENSSL_VERSION)")
    pass "Python 3.11 | $OPENSSL_VER"
else
    fail "Python 3.11 with OpenSSL 3.x not found (required for Kalshi TLS)"
fi

# 2. sklearn version matches training
SKLEARN_VER=$($PYTHON -c "import sklearn; print(sklearn.__version__)" 2>/dev/null || echo "missing")
if [ "$SKLEARN_VER" = "1.4.2" ]; then
    pass "sklearn 1.4.2 (matches training environment)"
else
    warn "sklearn $SKLEARN_VER (training was 1.4.2 — version mismatch may cause warnings)"
fi

# 3. Model file
if [ -f "$PROJ/models/prod_model.joblib" ]; then
    SIZE=$(du -h "$PROJ/models/prod_model.joblib" | cut -f1)
    TRAINED_AT=$($PYTHON -c "
import json; m=json.load(open('$PROJ/models/prod_model_meta.json'))
print(m.get('trained_at','unknown'))" 2>/dev/null || echo "unknown")
    pass "Model present ($SIZE, trained $TRAINED_AT)"
else
    fail "Model not found: $PROJ/models/prod_model.joblib"
fi

# 4. Feature matrix
if [ -f "$PROJ/exp_output/EXP-005/EXP-005_feature_matrix.csv" ]; then
    ROWS=$(wc -l < "$PROJ/exp_output/EXP-005/EXP-005_feature_matrix.csv")
    pass "Feature matrix present ($ROWS rows)"
else
    fail "Feature matrix missing: $PROJ/exp_output/EXP-005/EXP-005_feature_matrix.csv"
fi

# 5. QS snapshot
if [ -f "$PROJ/qualitative_data/pam_v4/QS-2026-05-28-002_classifications.csv" ]; then
    pass "QS snapshot present (QS-2026-05-28-002)"
else
    fail "QS snapshot missing"
fi

# 6. .env + VENUE_API_KEY
if [ -f "$PROJ/.env" ]; then
    # GG-662: the venue key lives here; mode must be 600, and no .env.bak* copies may linger.
    ENV_MODE=$(stat -c '%a' "$PROJ/.env" 2>/dev/null || stat -f '%Lp' "$PROJ/.env")
    if [ "$ENV_MODE" = "600" ]; then pass ".env mode 600"; else fail ".env mode $ENV_MODE (expected 600)"; fi
    if ls "$PROJ"/.env.bak* >/dev/null 2>&1; then fail ".env backup copy present ($(ls "$PROJ"/.env.bak* | tr '\n' ' '))"; else pass "no .env.bak* copies"; fi
    source "$PROJ/.env" 2>/dev/null || true
    if [ -n "${VENUE_API_KEY:-}" ] && [ "$VENUE_API_KEY" != "REPLACE_WITH_YOUR_KALSHI_READ_ONLY_KEY" ]; then
        pass "VENUE_API_KEY set (${#VENUE_API_KEY} chars)"
    else
        fail "VENUE_API_KEY not configured in .env"
    fi
    if [ "${BOT_ENV:-}" = "paper" ]; then
        pass "BOT_ENV=paper"
    else
        fail "BOT_ENV=${BOT_ENV:-unset} (expected: paper)"
    fi
    if [ -n "${BOT_C4_ACTIVE:-}" ]; then
        fail "BOT_C4_ACTIVE is set — must be unset in ENV-02"
    else
        pass "BOT_C4_ACTIVE not set (correct)"
    fi
else
    fail ".env not found at $PROJ/.env"
fi

# 7. Kalshi API connectivity
echo ""
echo "[DS-02] Testing Kalshi API connectivity..."
CONNECTIVITY=$($PYTHON -c "
import sys, os
sys.path.insert(0, '$PROJ/src')
os.environ.setdefault('VENUE_API_KEY', os.popen('grep VENUE_API_KEY $PROJ/.env | cut -d= -f2').read().strip())
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
try:
    c = KalshiMarketClient.from_env()
    ok, s = c.check_connectivity()
    print('CONNECTED' if ok else f'FAILED:{s}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null)

if [ "$CONNECTIVITY" = "CONNECTED" ]; then
    pass "Kalshi API reachable (exchange active)"
else
    fail "Kalshi API: $CONNECTIVITY"
fi

# 8. Log directory writable
if [ -w "${LOG_DIR:-$PROJ/logs}" ]; then
    pass "Log directory writable (${LOG_DIR:-$PROJ/logs})"
else
    fail "Log directory not writable"
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "=== All checks passed — VPS ready for PIPE-02 cron ==="
    exit 0
else
    echo "=== $ERRORS check(s) FAILED — fix before enabling cron ==="
    exit 1
fi
