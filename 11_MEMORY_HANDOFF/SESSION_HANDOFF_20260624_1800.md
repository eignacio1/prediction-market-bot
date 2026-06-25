# Session Handoff — 2026-06-24T18:00Z

**Trigger:** Context window near limit  
**Last commit:** (pending — commit immediately after this file is written)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 1918/1918 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — MLB cron PAUSED (all 5 MLB lines commented out, per S85)
- **Paper bets:** MLB: 0 open, 0 closed ($1,000 fresh bankroll). NBA: dark (off-season).

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

*None — session was implementation-only.*

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| None | Implementation-only session | — | — |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-190 Step 3: `src/prediction_market_bot/run_t4_mlb_live.py`** | ✅ COMPLETE — PIPE-07 MLB, ~420 lines. Binomial hit-count model. 45s poll loop. ESPN MLB scoreboard + summary APIs. Isolated portfolio `paper_portfolio_mlb_t4.json`. T4_BAND_WEIGHT=0.27. Kill switch `logs/t4_mlb_kill_switch.flag`. Ghost protection via StagedOrderStore. BOT_ENV=paper + BOT_C4_ACTIVE=true guards at import. |
| **`tests/test_run_t4_mlb_live.py`** | ✅ COMPLETE — 55 tests (10 classes). All passing. Suite 1819→**1918/1918**. |
| **`deploy/cron.conf` PIPE-07 MLB block** | ✅ COMPLETE — 22:00 UTC cron line added (paused). PIPE-05 PAUSED comment updated. |
| **T-190 OVERALL** | ✅ COMPLETE — all 3 steps done across S85/S86. |
| **Session-end artifacts** | ✅ COMPLETE — TODO_NEXT, MEMORY_BANK, PLAN, DECISION_LOG, SESSION_HANDOFF all updated. |

---

## ONE THING PENDING

**Deploy to VPS and activate MLB accumulation.** The MLB arm is fully built and tested locally (1918/1918 passing). The single remaining action is:

```bash
# Step 1 — copy new files to VPS
scp src/prediction_market_bot/run_t4_mlb_live.py prediction-market-vps:/opt/prediction-market-bot/src/prediction_market_bot/
scp tests/test_run_t4_mlb_live.py prediction-market-vps:/opt/prediction-market-bot/tests/
scp deploy/cron.conf prediction-market-vps:/opt/prediction-market-bot/deploy/

# Step 2 — run T4 MLB tests on VPS
ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python3 -m pytest tests/test_run_t4_mlb_live.py -q"

# Step 3 — if tests pass, uncomment all 5 MLB cron lines in deploy/cron.conf and reinstall
# Lines to uncomment: PIPE-06pre (30 16), PIPE-05 (30 23), PIPE-05R (30 6), PIPE-05FX (30 22), PIPE-07 MLB (0 22)
ssh prediction-market-vps "crontab /opt/prediction-market-bot/deploy/cron.conf"
```

Also confirm: `run_mlb_pregame.py` and `run_t3_mlb_pretip.py` are already on VPS from S85/S86 (scp'd previously). If uncertain, scp them too.

---

## Current Paper Portfolio

- NBA: halted (off-season). Bankroll ~$130.62 (25.12% drawdown, kill switch active).
- MLB T1: $1,000.00, 0 open, 0 closed. Ready for accumulation once cron re-enabled.
- MLB T4: `paper_portfolio_mlb_t4.json` does not exist yet (created on first run of `run_t4_mlb_live.py`).

---

## Active Cron on VPS (157.230.91.33)

```
17:00 UTC  — Health check
17:25 UTC  — TSS cache pre-flight (T-140)
17:55 UTC  — PIPE-02 NBA pre-game inference
01:25 UTC  — PIPE-02 NBA late window
18:00 UTC  — PIPE-03 NBA paper trading (early)
01:30 UTC  — PIPE-03 NBA paper trading (late)
06:00 UTC  — PIPE-03R NBA resolve
20:00–03:00 UTC */15 — PIPE-06 NBA T3 pre-tip scan
23:00 UTC  — PIPE-07 NBA T4 in-play (dark, off-season)
14:00 UTC Mon — Model freshness check

MLB (ALL PAUSED — S85):
  30 16 * * * — PIPE-06pre MLB pregame (run_mlb_pregame.py)
  30 23 * * * — PIPE-05 MLB paper bets (run_mlb_paper_trade.py)
  30  6 * * * — PIPE-05R MLB resolution (run_resolve_mlb.py)
  30 22 * * * — PIPE-05FX MLB feature refresh
   0 22 * * * — PIPE-07 MLB T4 in-play (run_t4_mlb_live.py)
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
3. MLB T1 + T4 portfolios are independent JSON files — do NOT write T1 bets to `paper_portfolio_mlb_t4.json`
4. `run_t4_mlb_live.py` requires BOT_ENV=paper AND BOT_C4_ACTIVE=true — will sys.exit(1) if not set
5. GG-004 (EXP-017 MLB commercial validation) remains OPEN — blocked until ≥20 closed MLB positions

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_t4_mlb_live.py` | n/a (new source file) | SESSION 86 entry written | ✅ |
| `deploy/cron.conf` | n/a | SESSION 86 entry covers | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_1800.md.
# T-190 COMPLETE (1918/1918 tests). Next action: deploy MLB arm to VPS and activate MLB accumulation.
# scp run_t4_mlb_live.py + test + cron.conf → VPS, run 55 tests, uncomment 5 MLB cron lines, reinstall crontab."
```
