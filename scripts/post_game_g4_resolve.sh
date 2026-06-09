#!/bin/bash
# post_game_g4_resolve.sh — Automated post-G4 resolution + experiment run
# Scheduled: 11:00 PM PDT Jun 10 (06:00 UTC Jun 11) via Mac crontab
# Cron entry: 0 23 10 6 * /bin/bash "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets/scripts/post_game_g4_resolve.sh"
#
# Steps (each runs independently — failures logged, not fatal):
#   1.  Resolve T1 positions locally   (nba_api + SCP sync to VPS)
#   2.  Resolve T4 positions locally   (nba_api + SCP sync to VPS)
#   3.  SCP T1 portfolio     → local logs/   (EXP-017 / EXP-018 source)
#   4.  SCP T4 portfolio     → local logs/   (EXP-019B empirical cross-check)
#   5.  SCP pregame G4 file  → local logs/   (EXP-018 opp_adj_lambda join)
#   6.  SCP spread_observations.jsonl → local logs/   (EXP-019C)
#   7.  SCP t4_position_trajectories.jsonl → local logs/   (EXP-019B empirical)
#   8.  VPS git pull  (deploy all post-G3 commits: EXP-018, T4 logging, etc.)
#   9.  EXP-017 Part B rerun  (GG-004 evidence update, n=G2+G3+G4)
#   10. EXP-018  (adj_λ EV test, ADR-0015)

PROJ="/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
VPS="root@157.230.91.33"
SSH_KEY="$HOME/.ssh/id_ed25519_droplet"
PYTHON="$PROJ/.venv311/bin/python3"
LOG="$PROJ/logs/post_game_g4_resolve.log"
VPS_BOT="/opt/prediction-market-bot"

cd "$PROJ" || exit 1

{
    echo ""
    echo "======================================================"
    echo "POST-GAME G4 RESOLVE — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "======================================================"

    FAILURES=0

    # Step 1 — T1 resolve
    echo ""
    echo "[1/10] Resolving T1 positions..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_resolve_local.py; then
        echo "[1/10] OK"
    else
        echo "[1/10] FAILED — continuing"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 2 — T4 resolve
    echo ""
    echo "[2/10] Resolving T4 positions..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_t4_resolve_local.py; then
        echo "[2/10] OK"
    else
        echo "[2/10] FAILED — continuing"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 3 — SCP T1 portfolio → local
    echo ""
    echo "[3/10] Syncing resolved T1 portfolio to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:${VPS_BOT}/logs/paper_portfolio.json" \
            "$PROJ/logs/paper_portfolio.json"; then
        echo "[3/10] OK — $(wc -c < "$PROJ/logs/paper_portfolio.json") bytes"
    else
        echo "[3/10] FAILED — EXP-017/EXP-018 will use pre-resolve local portfolio"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 4 — SCP T4 portfolio → local
    echo ""
    echo "[4/10] Syncing resolved T4 portfolio to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:${VPS_BOT}/logs/paper_portfolio_t4.json" \
            "$PROJ/logs/paper_portfolio_t4.json"; then
        echo "[4/10] OK — $(wc -c < "$PROJ/logs/paper_portfolio_t4.json") bytes"
    else
        echo "[4/10] FAILED — T4 portfolio not synced locally"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 5 — SCP pregame G4 file → local  (EXP-018 needs opp_adj_lambda for G4 players)
    echo ""
    echo "[5/10] Syncing G4 pregame file to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:${VPS_BOT}/logs/pregame_20260610.json" \
            "$PROJ/logs/pregame_20260610.json"; then
        echo "[5/10] OK — $(wc -c < "$PROJ/logs/pregame_20260610.json") bytes"
    else
        echo "[5/10] FAILED — EXP-018 opp_adj_factor will be missing G4 data"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 6 — SCP spread_observations.jsonl → local  (EXP-019C)
    echo ""
    echo "[6/10] Syncing T4 spread observations to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:${VPS_BOT}/logs/spread_observations.jsonl" \
            "$PROJ/logs/spread_observations.jsonl"; then
        echo "[6/10] OK — $(wc -l < "$PROJ/logs/spread_observations.jsonl") lines"
    else
        echo "[6/10] FAILED — EXP-019C requires this file; may not exist until T4 fires G4"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 7 — SCP t4_position_trajectories.jsonl → local  (EXP-019B empirical)
    echo ""
    echo "[7/10] Syncing T4 position trajectories to local logs/..."
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "${VPS}:${VPS_BOT}/logs/t4_position_trajectories.jsonl" \
            "$PROJ/logs/t4_position_trajectories.jsonl"; then
        echo "[7/10] OK — $(wc -l < "$PROJ/logs/t4_position_trajectories.jsonl") lines"
    else
        echo "[7/10] FAILED — EXP-019B empirical requires this file"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 8 — VPS git pull
    echo ""
    echo "[8/10] Deploying post-G3 commits to VPS (git pull)..."
    if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
            "$VPS" \
            "cd ${VPS_BOT} && git pull && git log --oneline -3"; then
        echo "[8/10] OK"
    else
        echo "[8/10] FAILED — VPS not on latest; deploy manually before G5"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 9 — EXP-017 Part B rerun  (GG-004 update, n=G2+G3+G4)
    echo ""
    echo "[9/10] Running EXP-017 Part B (GG-004 evidence update)..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            src/prediction_market_bot/run_exp017.py \
            --from-pregame logs/ \
            --portfolio logs/paper_portfolio.json; then
        echo "[9/10] OK"
    else
        echo "[9/10] FAILED"
        FAILURES=$((FAILURES + 1))
    fi

    # Step 10 — EXP-018  (adj_λ EV test, ADR-0015, GG-004)
    echo ""
    echo "[10/10] Running EXP-018 (opp-adjusted λ EV test)..."
    if BOT_ENV=paper PYTHONPATH=src "$PYTHON" \
            scripts/run_exp018.py; then
        echo "[10/10] OK"
    else
        echo "[10/10] FAILED"
        FAILURES=$((FAILURES + 1))
    fi

    echo ""
    echo "======================================================"
    if [ "$FAILURES" -eq 0 ]; then
        echo "RESULT: ALL STEPS OK — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    else
        echo "RESULT: $FAILURES/10 STEPS FAILED — review log before G5"
    fi
    echo "======================================================"

} >> "$LOG" 2>&1
