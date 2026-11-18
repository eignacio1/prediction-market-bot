# Session Handoff — 2026-05-29T20:30Z
**Trigger:** Context window near limit — operator-initiated clean cutoff  
**Last commit:** `6917479` (main) — pushed to GitHub + VPS

---

## Status
- **Phase:** 6/7 ACTIVE (G0–G5 all closed)
- **Tests:** 533/533 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (new dual-window schedule live)

---

## This Session Completed (Phase 3 Sprint + Full Hygiene)

### Phase 3 — VPS Deployment
| Item | Result |
|------|--------|
| GitHub repo created | ✅ `github.com/eignacio1/prediction-market-bot` (private) |
| VPS git pull | ✅ Synced to `6917479`; deploy key configured |
| PIPE-03 VenueRouter verified | ✅ 41 markets, 2 bets placed (Fox YES, SGA NO), kalshi_only |
| EXP-012 HYP-006 | ✅ FALSIFIED — opp def rating Δ Brier = 0.0000 |

### Full Hygiene Sprint
| Item | Result |
|------|--------|
| ingestion.py date parse warning | ✅ Fixed — `format="mixed"` on both player+team paths |
| C4 MIN_BET_USD=$10 floor | ✅ Added as CHECK 7; sub-floor → REJECTED `min_bet_floor` |
| run_resolve.py (PIPE-03R) | ✅ Created — resolution-only; 06:00 UTC cron; 9 tests |
| run_exp016.py (T-072 / HYP-009) | ✅ Created — playoff ablation; **RUN PENDING** |
| cron dual-window | ✅ Deployed — 22:00 UTC early + 01:30 UTC late + 06:00 UTC resolve |
| VPS crontab | ✅ Replaced; inline Python → `deploy/check_model_freshness.py` |
| KI-008 (playoff validity) | ✅ Registered — HIGH, G6 blocker |
| KI-009 (50-bet gate calendar) | ✅ Registered — MEDIUM, APR-0016 path |
| ASM-010 (strategy concentration) | ✅ Registered |
| ASM-011 (playoff generalization) | ✅ Registered — UNVALIDATED |
| HYP-009 | ✅ Registered in HYPOTHESES.md |
| ROADMAP G6 calendar constraint | ✅ Documented + APR-0016 extension path |
| git author identity | ✅ Fixed — `earlignacio1@gmail.com` |
| Connectivity assumption | ✅ Corrected — work wifi blocked; all other networks fine |

---

## ONE THING PENDING: EXP-016 (HYP-009)

**Playoff data already pulled and cached** (1,805 rows across 4 seasons). Bug fixed (game_date_dt Timestamp in feature set). Run with cache in a fresh terminal:

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
EXP016_SKIP_PULL=1 PYTHONPATH=src python3 src/prediction_market_bot/run_exp016.py
```

- Cache already at: `exp_output/EXP-016/EXP-016_playoff_matrix.csv`
- Skip the 15 min data pull — use `EXP016_SKIP_PULL=1`
- Output: `exp_output/EXP-016/EXP-016_results.json`
- Verdict: HYP-009 CONFIRMED (Δ < 0.012) or FALSIFIED

**After EXP-016 runs**, next session should:
1. Record verdict in HYPOTHESES.md (change `⏳ PENDING` to result)
2. Update ASM-011 status
3. Update KI-008 resolution path if CONFIRMED
4. Commit + push + VPS pull
5. Write new session handoff

---

## Current Paper Portfolio (as of this session)
- Bankroll: $936.27 (6.4% drawdown from 2 open bets)
- Open: Fox YES 15+ pts ($56.55) | SGA NO 30+ pts ($7.18)
- Closed: 0 | Resolved bets: 0
- G6 gate: 0/50 resolved bets

---

## Active Cron on VPS (157.230.91.33)
```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints to Remember
1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (50+ resolved paper bets + positive P&L)
3. Playoff model validity unconfirmed until EXP-016 runs
4. G6 gate is calendar-constrained: NBA Finals end ~2026-06-22; APR-0016 extends window if needed
5. Strategy A is the only active signal — B/I falsified; C/E/F/J/K all infrastructure-blocked

---

## Resume Command
```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260529_2030.md, confirm 533 tests"
```
