# Session Handoff — 2026-06-02 SESSION 19 (PDT)

**Session end:** 2026-06-02 ~21:00 PDT  
**Operator:** Earl Ignacio  
**Git HEAD:** 80544c0  
**Next session priority:** Finals Game 1 monitoring + post-game resolve

---

## What Happened This Session

### Completed
1. **Bug H drawdown fix in `run_t4_live.py`** — T4 was computing `drawdown = (initial - current) / initial`, counting deployed T1 capital (~$540) as a realized loss. This produced ~54% false drawdown before the game started, triggering C4's kill switch and silently rejecting every T4 bet. Fix: `_realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))`. Same two-line pattern as PIPE-03. Commit `706264b`.

2. **PAPER_T4_VIRTUAL=true mode** — added as default (`os.environ.get("PAPER_T4_VIRTUAL", "true")`). C4 evaluates + stages bets; logs "T4 VIRTUAL" line; does NOT call `trader.open_position()`. Purpose: prove the architecture fires at evaluation scale without depleting T1 capital pool. Commit `706264b`.

3. **VPS screen restarted** — old `139678.t4_live` (running stale code with Bug H) killed. New `140907.t4_live` running with commit `706264b`. Confirmed: STATUS_SCHEDULED → sleeping 60s per cycle. Will auto-activate at Finals Game 1 tip-off.

4. **Game labels corrected** — SESSION 18 mislabeled the upcoming Finals game as "G2." ESPN confirmed: it is **Finals Game 1** (NYK at SAS, Jun 3 PDT 8:30 PM EDT). Finals schedule pinned: Finals Game 1 Jun 3 PDT / Finals Game 2 Jun 5 PDT / Finals Game 3 Jun 8 PDT. ESPN internal IDs purged from all human-readable documentation.

5. **NAMING STANDARD ADOPTED** — "Finals Game 1" = the NBA game. "Gate G6" = live capital authorization gate. Never abbreviated the same way in the same context.

6. **DECISION_LOG updated** — 5 new judgment call entries for SESSION 19.

7. **VPS portfolio state pulled** — see below.

### New Issues Discovered

**KI-026 (NEW) — T4 per-bet sizing for continuous in-play firing is unresolved**  
Design intent: ~1000 evaluation cycles/game WITHIN the capital ceiling. At T4 Kelly=0.20 and $600 bankroll, each approved bet is ~$120 — 5 bets depletes capital. High-frequency T4 execution requires a fundamentally different per-bet sizing model (tiny fraction, not quarter-Kelly). No experiment or ADR currently addresses this. PAPER_T4_VIRTUAL=true is correct interim mode. Must be resolved via ADR before T4 ACTIVE. EXP-018 calibrates T4_MIN_DELTA_P (separate question).

**KI-027 (NEW) — Kalshi HTTP 503/429 errors in second PIPE-03 window**  
Second cron (01:30 UTC Jun 3) placed 4 positions that all failed at Kalshi API (HTTP 503 or 429). Paper resolution is unaffected (resolves on player stats). Root cause unknown — may need backoff/retry in `paper_trader.py`. Check VPS logs.

---

## VPS Portfolio State (Finals Game 1)

Pulled at 20:45 PDT Jun 2. Game tips ~11 hours from now.

```
Bankroll: $459.47 / $1,000 initial
Open positions: 11
```

| Player | Ticker suffix | Direction | Size | Kalshi status |
|--------|--------------|-----------|------|---------------|
| KAT | YES 20 | YES | $30.37 | resting ✅ |
| KAT | YES 15 | YES | $70.37 | resting ✅ |
| KAT | YES 10 | YES | $86.73 | resting ✅ |
| Fox | NO 25 | NO | $72.61 | canceled ⚠️ |
| Fox | NO 20 | NO | $40.42 | canceled ⚠️ |
| Fox | YES 10 | YES | $39.41 | resting ✅ |
| Anunoby | NO 25 | NO | $42.05 | canceled ⚠️ |
| Wembanyama | NO 40 | NO | $57.40 | failed 503 ❌ |
| Wembanyama | NO 35 | NO | $41.74 | failed 503 ❌ |
| Wembanyama | NO 30 | NO | $21.89 | failed 429 ❌ |
| Castle | NO 30 | NO | $37.53 | failed 429 ❌ |

**4 real Kalshi positions** (resting); **3 canceled by Kalshi**; **4 failed HTTP API**.  
All 11 will resolve via `run_resolve_local.py` on player stats — Kalshi order status is irrelevant to paper resolution.  
Architecture: all 11 placed under Path B (Poisson CDF) corrected system.

---

## Strategic Decisions This Session

1. **T4 per-bet sizing for high-frequency in-play is an open architectural gap** — must be named, registered, and resolved via ADR before T4 ACTIVE. PAPER_T4_VIRTUAL=true is the correct interim mode.

2. **Do not reset portfolio before Finals Game 1** — the 11 positions are valid Path B evidence. Run the game, resolve after, let EXP-017 n accumulate. Evaluate reset option before Finals Game 2 if results are unclear.

3. **Finals schedule is locked** — Finals Game 1 Jun 3 PDT, Finals Game 2 Jun 5 PDT, Finals Game 3 Jun 8 PDT.

4. **G1/gate G6 disambiguation is now a standing rule** — always spell out in full.

---

## What the Next Session Must Do

**BEFORE GAME (Jun 3 PDT, anytime before 8:30 PM EDT):**
- Check T4 screen: `ssh root@157.230.91.33 'screen -ls'` — confirm `140907.t4_live` alive
- Optional: tail the log to confirm STATUS_SCHEDULED polling continues

**DURING GAME (00:30–03:30 UTC Jun 4 = Jun 3 PDT 8:30 PM–midnight EDT):**
- `ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'`
- Watch for STATUS_IN_PROGRESS transition + "T4 VIRTUAL" lines
- Kill switch if needed: `ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'`

**AFTER GAME (Jun 4 UTC early morning):**
- `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`
- `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio`
- EXP-017 n grows from 2 → 2 + Finals Game 1 market count
- Evaluate portfolio reset option for Finals Game 2

**OPEN ARCHITECTURAL ITEM (any session):**
- Register KI-026 as a formal task with registered experiment/ADR path: T4 per-bet sizing model for continuous in-play firing within capital ceiling

---

## VPS Quick Reference

```bash
# Check screens
ssh root@157.230.91.33 'screen -ls'

# T4 live log
ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'

# Kill switch
ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'

# Portfolio
ssh root@157.230.91.33 'cat /opt/prediction-market-bot/logs/paper_portfolio.json'

# Resolve after game
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && BOT_ENV=paper PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python src/prediction_market_bot/run_resolve_local.py'
```

---

## Governance Scan (run at next session start)

- Step 1 doc debt: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/`
- Step 2 stub scan: per CLAUDE.md protocol
- Step 3 open gaps: `grep -n "| OPEN" 03_DECISIONS/GOVERNANCE_GAP_LOG.md`
- GG-004 is the binding gate G6 blocker. EXP-017 n grows after Finals Game 1 resolves.
