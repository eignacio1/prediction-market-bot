#!/bin/bash
# post_game_g3_resolve.sh — Automated post-G3 resolution + deploy
# Scheduled: 11:00 PM PDT Jun 8 (06:00 UTC Jun 9) via Mac crontab
#
# Steps (each runs independently — failures logged, not fatal):
#   1. Resolve T1 positions locally (nba_api + SCP sync to VPS)
#   2. Resolve T4 positions locally (nba_api + SCP sync to VPS)
#   3. Sync resolved T1 portfolio to local logs/ (for EXP-017)
#   4. Deploy idempotency fix to VPS (git pull)
#   5. Run EXP-017 Part B (GG-004 evidence update)

PROJ="/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
VPS="root@157.230.91.33"
SSH_KEY="$HOME/.ssh/id_ed25519_droplet"
PYTHON="$PROJ/.venv311/bin/python3"
LOG="$PROJ/logs/post_game_g3_resolve.log"

cd "$PROJ" || exit 1

{
    echo ""
    echo "======================================================"
    echo "POST-GAME G3 RESOLVE — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "======================================================"

    FAILURES=0

    # Step 1 — T1 resolve
    echo ""
    echo "[1/5] Resolving T1 positions..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_resolve_local.py; then
        echo "[1/5] OK"
    else
        echo "[1/5] FAILED — continuing"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 2 — T4 resolve
    echo ""
    echo "[2/5] Resolving T4 positions..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_t4_resolve_local.py; then
        echo "[2/5] OK"
    else
        echo "[2/5] FAILED — continuing"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 3 — Sync resolved T1 portfolio to local logs/ (EXP-017 reads it)
    echo ""
    echo "[3/5] Syncing resolved portfolio to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:/opt/prediction-market-bot/logs/paper_portfolio.json" \
            "$PROJ/logs/paper_portfolio.json"; then
        echo "[3/5] OK — $(wc -c < "$PROJ/logs/paper_portfolio.json") bytes"
    else
        echo "[3/5] FAILED — EXP-017 will use pre-resolve local portfolio"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 4 — Deploy idempotency fix to VPS
    echo ""
    echo "[4/5] Deploying idempotency fix to VPS (git pull)..."
    if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "$VPS" \
            "cd /opt/prediction-market-bot && git pull && git log --oneline -3"; then
        echo "[4/5] OK"
    else
        echo "[4/5] FAILED — idempotency fix not deployed; deploy manually before G4"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 5 — EXP-017 Part B
    echo ""
    echo "[5/5] Running EXP-017 Part B (GG-004 update)..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_exp017.py \
            --from-pregame logs/ \
            --portfolio logs/paper_portfolio.json; then
        echo "[5/5] OK"
    else
        echo "[5/5] FAILED"
        FAILURES=$((FAILURES + 1))
    fi

    echo ""
    echo "======================================================"
    if [ "$FAILURES" -eq 0 ]; then
        echo "RESULT: ALL STEPS OK — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    else
        echo "RESULT: $FAILURES/5 STEPS FAILED — review log before G4"
    fi
    echo "======================================================"

} >> "$LOG" 2>&1
