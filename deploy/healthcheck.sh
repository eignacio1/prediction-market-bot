#!/usr/bin/env bash
# ============================================================================
# healthcheck.sh -- daily VPS health check against TODAY'S invariants (W72.3 / GG-669).
#
# Rewrites the Phase-0 PIPE-02 script, which asserted files and flags from the NBA-era
# deployment and so was red for the wrong reasons. Contract: exit 0 when the box is healthy,
# exit 1 only on a real fault. [WARN] lines never fail the run -- drift worth a look, not a fault.
#
# Checks ([FAIL] = real fault):
#   1  venv python + OpenSSL 3 + sklearn/joblib import
#   2  MLB T1 model + meta exist
#   3  DEMO ONLY: .env BOT_ENV=paper, order base URL resolves to demo host, .env mode 600/400,
#      VENUE_API_KEY set
#   4  kelly_fraction 0.0 on T1_MULTI_DAY and T4M_PROJ (ADR-0048). A superseding ADR that
#      reactivates sizing must update this check -- red is the point, it forces the review
#   5  deploy/demo_fill.env present, not group/world-writable, unmodified vs git HEAD
#   6  services t4-mlb and pmbot-web-dashboard active (WARN on restarts)
#   7  required cron arms present in crontab (WARN: live cron scripts with no deploy/cron* mirror, GG-676)
#   8  deploy truth (scripts/ops/deploy_truth.py): failed deploy / stale pending restart / stale service code
#   9  Kalshi DEMO API reachable (read-only GET, 2 tries)
#  10  logs/ writable, disk < 90%
#  13  NHL in-play write recency (W129.7): FAIL when a live game has no row written
#  10b disk growth (W118.4): WARN when the 7-day growth reaches 90% within 14 days
#  11  demo-fill stall (W109.6): WARN when 0 demo orders in 24h while shadow arms logged rows
#
# Env overrides exist for tests/test_healthcheck.py only:
#   PMBOT_DIR PMBOT_PYTHON PMBOT_SYSTEMCTL PMBOT_CRONTAB_CMD PMBOT_SKIP_NET PMBOT_MIN_OPENSSL
# ============================================================================
set -uo pipefail

PROJ="${PMBOT_DIR:-/opt/prediction-market-bot}"
PYTHON="${PMBOT_PYTHON:-$PROJ/venv/bin/python}"
SYSTEMCTL="${PMBOT_SYSTEMCTL:-systemctl}"
CRONTAB_CMD="${PMBOT_CRONTAB_CMD:-crontab -l}"
ERRORS=0
WARNS=0

pass() { echo "[OK] $1"; }
fail() { echo "[FAIL] $1"; ERRORS=$((ERRORS+1)); }
warn() { echo "[WARN] $1"; WARNS=$((WARNS+1)); }

echo "=== VPS Health Check (W72.3) ==="
date -u '+%Y-%m-%dT%H:%M:%SZ'
echo ""

# 1. interpreter + OpenSSL 3 + model libs
if "$PYTHON" -c "import ssl, sys; assert ssl.OPENSSL_VERSION_INFO[0] >= int(sys.argv[1]), ssl.OPENSSL_VERSION" "${PMBOT_MIN_OPENSSL:-3}" 2>/dev/null; then
    pass "python + $("$PYTHON" -c 'import ssl; print(ssl.OPENSSL_VERSION)' 2>/dev/null)"
else
    fail "python at $PYTHON missing or OpenSSL < 3 (Kalshi TLS needs 3.x)"
fi
if "$PYTHON" -c "import sklearn, joblib" 2>/dev/null; then
    pass "sklearn + joblib import"
else
    fail "sklearn/joblib do not import (MLB T1 model cannot load)"
fi

# 2. the live T1 model
if [ -s "$PROJ/models/mlb_v1_model.joblib" ] && [ -s "$PROJ/models/mlb_v1_model_meta.json" ]; then
    pass "MLB T1 model + meta present"
else
    fail "models/mlb_v1_model.joblib or mlb_v1_model_meta.json missing/empty"
fi

# 3. demo only
ENVF="$PROJ/.env"
if [ -f "$ENVF" ]; then
    MODE="$("$PYTHON" -c "import os,sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777)[2:])" "$ENVF" 2>/dev/null || echo "?")"
    case "$MODE" in
        600|400) pass ".env mode $MODE" ;;
        *)       fail ".env mode $MODE (must be 600/400: it holds the API key id and key path)" ;;
    esac
    # GG-662: a lingering .env.bak* copy duplicates the secret outside the locked file (names only are printed)
    BAKS=""
    for f in "$PROJ"/.env.bak*; do [ -e "$f" ] && BAKS="$BAKS $(basename "$f")"; done
    if [ -n "$BAKS" ]; then fail ".env backup copy present:$BAKS (delete it)"; else pass "no .env.bak* copies"; fi
    # source in a subshell and print only derived flags: secrets never reach output
    BOT_ENV_VAL="$(set -a; . "$ENVF" >/dev/null 2>&1; echo "${BOT_ENV:-unset}")"
    KEY_SET="$(set -a; . "$ENVF" >/dev/null 2>&1; if [ -n "${VENUE_API_KEY:-}" ] && [ "${VENUE_API_KEY}" != "REPLACE_WITH_YOUR_KALSHI_READ_ONLY_KEY" ]; then echo yes; else echo no; fi)"
    if [ "$BOT_ENV_VAL" = "paper" ]; then
        pass "BOT_ENV=paper (demo only)"
    else
        fail "BOT_ENV=$BOT_ENV_VAL in .env (must be paper: no real capital before G6)"
    fi
    if [ "$KEY_SET" = "yes" ]; then pass "VENUE_API_KEY set"; else fail "VENUE_API_KEY unset/placeholder in .env"; fi
else
    fail ".env not found at $ENVF"
fi
ORDER_URL="$(BOT_ENV=paper PYTHONPATH="$PROJ/src" "$PYTHON" -c 'from prediction_market_bot.c5_execution.kalshi_client import _kalshi_base_url as u; print(u())' 2>/dev/null || echo "?")"
case "$ORDER_URL" in
    *demo*) pass "order base URL under BOT_ENV=paper is demo ($ORDER_URL)" ;;
    *)      fail "order base URL under BOT_ENV=paper is '$ORDER_URL', not the demo host" ;;
esac

# 4. kelly zero where ADR-0048 zeroed it
KELLY="$(PYTHONPATH="$PROJ/src" "$PYTHON" -c "
from prediction_market_bot.execution_bands import BAND_CONFIGS, ExecutionBand as B
print(' '.join(f'{b.name}={BAND_CONFIGS[b].kelly_fraction}' for b in (B.T1_MULTI_DAY, B.T4M_PROJ)))" 2>/dev/null || echo "?")"
if [ "$KELLY" = "T1_MULTI_DAY=0.0 T4M_PROJ=0.0" ]; then
    pass "kelly_fraction 0.0 on T1_MULTI_DAY and T4M_PROJ (ADR-0048)"
else
    fail "kelly_fraction is '$KELLY', expected T1_MULTI_DAY=0.0 T4M_PROJ=0.0 (ADR-0048); a reactivating ADR must update this check"
fi

# 5. the registered demo-fill config
DF="$PROJ/deploy/demo_fill.env"
if [ -f "$DF" ]; then
    DFW="$("$PYTHON" -c "import os,sys; print(os.stat(sys.argv[1]).st_mode & 0o022)" "$DF" 2>/dev/null || echo "?")"
    if [ "$DFW" = "0" ]; then pass "deploy/demo_fill.env not group/world-writable"; else fail "deploy/demo_fill.env group/world-writable (or unreadable mode)"; fi
    if git -C "$PROJ" diff --quiet -- deploy/demo_fill.env 2>/dev/null; then
        pass "deploy/demo_fill.env matches git HEAD"
    else
        fail "deploy/demo_fill.env differs from git HEAD (registered config edited on the box)"
    fi
else
    fail "deploy/demo_fill.env missing"
fi

# 6. services
for svc in t4-mlb pmbot-web-dashboard; do
    if [ "$("$SYSTEMCTL" is-active "$svc" 2>/dev/null)" = "active" ]; then
        NR="$("$SYSTEMCTL" show "$svc" -p NRestarts --value 2>/dev/null || echo 0)"
        if [ -n "${NR:-}" ] && [ "${NR:-0}" != "0" ]; then warn "$svc active but NRestarts=$NR"; else pass "$svc active, 0 restarts"; fi
    else
        fail "$svc is not active"
    fi
done

# 7. cron arms
# W117.3: ``echo | grep -q`` under ``set -o pipefail`` reports a PRESENT arm as MISSING once the crontab is bigger than the 64KB pipe
# buffer (grep -q exits at the first match, echo dies of SIGPIPE, the pipeline is non-zero). Here-strings have no pipe.
if CRON="$($CRONTAB_CMD 2>/dev/null)" && [ -n "$CRON" ]; then
    LIVE="$(echo "$CRON" | grep -v '^[[:space:]]*#')"
    for arm in vps_deploy.sh run_mlb_pregame.py run_resolve_mlb.py archive_market_prices.py healthcheck.sh; do
        if grep -q -- "$arm" <<<"$LIVE"; then pass "cron arm present: $arm"; else fail "cron arm MISSING from crontab: $arm"; fi
    done
    ORPHANS=""
    for tok in $(echo "$LIVE" | grep -oE '[A-Za-z0-9_]+\.py' | sort -u); do
        grep -rqsF --include='cron*' "$tok" "$PROJ/deploy" || ORPHANS="$ORPHANS $tok"
    done
    if [ -n "$ORPHANS" ]; then warn "cron-mirror drift (GG-676): live crontab scripts with no deploy/cron* mirror:$ORPHANS"; else pass "every live cron script has a deploy/cron* mirror"; fi
else
    warn "crontab not readable here; cron arms not checked"
fi

# 8. deploy truth
if DT="$("$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" check 2>&1)"; then
    if grep -q '^  ALARM' <<<"$DT"; then
        while IFS= read -r l; do fail "deploy truth: ${l#  }"; done < <(echo "$DT" | grep '^  ALARM')
    elif grep -q '^  UNKNOWN' <<<"$DT"; then
        warn "deploy truth has UNKNOWN lines: $(echo "$DT" | grep '^  UNKNOWN' | head -2 | tr '\n' ';')"
    else
        pass "deploy truth: no stale service code, failed deploy or stuck pending restart"
    fi
else
    warn "deploy truth check exited non-zero"
fi

# 9. Kalshi DEMO reachability (read-only GET)
if [ -n "${PMBOT_SKIP_NET:-}" ]; then
    warn "network check skipped (PMBOT_SKIP_NET)"
else
    NETOK=no
    for _ in 1 2; do
        if "$PYTHON" -c "
import urllib.request
urllib.request.urlopen('https://external-api.demo.kalshi.co/trade-api/v2/exchange/status', timeout=10).read()" 2>/dev/null; then NETOK=yes; break; fi
        sleep 3
    done
    if [ "$NETOK" = yes ]; then pass "Kalshi DEMO API reachable"; else fail "Kalshi DEMO API unreachable (2 tries)"; fi
fi

# 10. logs + disk
if [ -w "$PROJ/logs" ]; then pass "logs/ writable"; else fail "logs/ not writable"; fi
USE="${PMBOT_DISK_FAKE_PCT:-$(df -P "$PROJ" 2>/dev/null | awk 'NR==2{gsub("%","",$5); print $5}')}"   # override: tests only (W118.4)
if [ -n "${USE:-}" ]; then
    if [ "$USE" -ge 90 ]; then fail "disk ${USE}% used"; elif [ "$USE" -ge 80 ]; then warn "disk ${USE}% used"; else pass "disk ${USE}% used"; fi
fi

# 10b. disk growth (W118.4 / B-102): WARN when the 7-day growth puts the disk at 90% within 14 days; records one sample per run
if DG="$(cd "$PROJ" && PYTHONPATH="$PROJ/src" "$PYTHON" -m prediction_market_bot.disk_guard "$PROJ" --record 2>&1)"; then
    case "$DG" in
        WARN*) warn "disk growth: ${DG#WARN: }" ;;
        *) pass "disk growth: ${DG#OK: }" ;;
    esac
else
    warn "disk growth check errored: $(echo "$DG" | tail -1)"
fi

# 11. demo-fill stall (W109.6): the forward test sat 5 days with every switch off and nothing alarmed
if ST="$(cd "$PROJ" && PYTHONPATH="$PROJ/src" "$PYTHON" -m prediction_market_bot.pregame_shadow.demo_fill_stall "$PROJ" 2>&1)"; then
    case "$ST" in
        STALLED*) warn "demo-fill stall: ${ST#STALLED: }" ;;
        UNKNOWN*) warn "demo-fill stall check: ${ST#UNKNOWN: }" ;;
        *) pass "demo-fill: ${ST#OK: }" ;;
    esac
else
    warn "demo-fill stall check errored: $(echo "$ST" | tail -1)"
fi

# 12. MLB board alarms (W129.3 / GG-1957): not armed 7 days before opening day, or a 0-row run on a scheduled game day
if MB="$(cd "$PROJ" && PYTHONPATH="$PROJ/src:$PROJ/scripts" "$PYTHON" scripts/mlb_board_install.py healthcheck 2>&1)"; then
    while IFS= read -r l; do case "$l" in
        FAIL*) fail "${l#FAIL }" ;; WARN*) warn "${l#WARN }" ;; *) pass "${l#PASS }" ;; esac; done <<< "$MB"
else
    while IFS= read -r l; do case "$l" in
        FAIL*) fail "${l#FAIL }" ;; WARN*) warn "${l#WARN }" ;; *) pass "${l#PASS }" ;; esac; done <<< "$MB"
fi

# 13. NHL in-play write recency (W129.7): a live NHL game with no row written = FAIL (a 200 from the feed proves nothing, GG-163)
if [ -f "$PROJ/data/shadow/nhl_inplay/pass_log.jsonl" ]; then
    if NH="$(cd "$PROJ" && PYTHONPATH="$PROJ/src:$PROJ" "$PYTHON" scripts/nhl_inplay_shadow.py --health 2>&1)"; then
        case "$NH" in
            FAIL*) fail "nhl in-play: ${NH#FAIL: }" ;;
            *) pass "nhl in-play: ${NH#*: }" ;;
        esac
    else
        warn "nhl in-play health check errored: $(echo "$NH" | tail -1)"
    fi
fi

# 14. NFL in-play write recency (W130.1): a live NFL game with no row written = FAIL (a 200 from the feed proves nothing, GG-163)
if [ -f "$PROJ/data/shadow/nfl_inplay/pass_log.jsonl" ]; then
    if NF="$(cd "$PROJ" && PYTHONPATH="$PROJ/src:$PROJ" "$PYTHON" scripts/run_nfl_inplay_shadow.py --health 2>&1)"; then
        case "$NF" in
            FAIL*) fail "nfl in-play: ${NF#FAIL: }" ;;
            *) pass "nfl in-play: ${NF#*: }" ;;
        esac
    else
        warn "nfl in-play health check errored: $(echo "$NF" | tail -1)"
    fi
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "=== HEALTHY: 0 faults, $WARNS warning(s) ==="
    exit 0
else
    echo "=== UNHEALTHY: $ERRORS fault(s), $WARNS warning(s) ==="
    exit 1
fi
