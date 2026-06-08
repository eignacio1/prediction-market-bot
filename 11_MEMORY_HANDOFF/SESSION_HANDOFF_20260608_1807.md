# Session Handoff — 2026-06-08T18:07Z

**Trigger:** Session end / context window management  
**Last commit:** `b9a00b3` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 739/739 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-07 newly added at 23:00 UTC)
- **Paper bets:** 35/30 resolved (**G6 30-bet threshold CROSSED**) — G6 still requires ≥66 EXP-017 Part B + ≥5 game nights

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| PIPE-07 T4 activated in non-virtual paper mode (PAPER_T4_VIRTUAL=false) for Finals G3 | VIRTUAL mode only writes to audit log — feeds no EXP-017 Part B evidence. Non-virtual at flat sizing (~1,000 bets/game) feeds EXP-017 n-count directly. G1 VIRTUAL run already calibrated T4 architecture; another VIRTUAL run adds zero new commercial signal. | DECISION_LOG SESSION 37 row | DS |
| T4 portfolio uses separate file: `paper_portfolio_t4.json` + `staged_orders_t4.db` | Original code wrote to `paper_portfolio.json` (same as T1 VPS portfolio). T4 and T1 positions would interleave on same game night, corrupting T1 bankroll tracking. | DECISION_LOG SESSION 37 row; `run_t4_live.py` lines 294–295 | DS |
| PIPE-07 cron set at 23:00 UTC daily (not 00:00 UTC) | 23:00 UTC = 7pm ET: covers early NBA tip-offs. 00:00 UTC = 8pm ET: would miss 7pm tip-offs. 6h timeout (05:00 UTC) covers late games. | `deploy/cron.conf` PIPE-07 comment block | DS |

---

## Tasks Completed This Session

### SESSION 37 (earlier — G3 pre-game hardening, commit 97d5f06)

| Item | Result |
|------|--------|
| GG-014 completeness: `_get()` exponential backoff | ✅ `_get()` was linear (1s/2s/3s); corrected to exponential (2s/4s/8s) matching `_post()`. New test `test_get_uses_exponential_backoff_on_503`. |
| T-134/T-140: TSS empty-cache WARNING | ✅ `run_pregame.py` emits `logger.warning("team_stats_cache_empty")` + console print when cache = `{}`. |
| CLAUDE.md bankroll correction | ✅ Updated $683.41→$958.99, kill threshold $137→$192, ADR-0012 note. |
| MEMORY_BANK + TODO_NEXT | ✅ Updated to SESSION 37 pre-game state. |

### SESSION 37 (continued — PIPE-07 activation, commit b9a00b3)

| Item | Result |
|------|--------|
| **T4 portfolio isolation fix** | ✅ `run_t4_live.py` `_PORTFOLIO_PATH` → `paper_portfolio_t4.json`; `_STAGED_DB_PATH` → `staged_orders_t4.db`. Docstring PAPER_T4_VIRTUAL "enabled"→"disabled". |
| **PIPE-07R-LOCAL: `run_t4_resolve_local.py`** | ✅ New script. SCP pull `paper_portfolio_t4.json` from VPS → local nba_api resolve → SCP push + audit append. |
| **`deploy/cron.conf` PIPE-07 entry** | ✅ Added at 23:00 UTC daily, 6h timeout, `PAPER_T4_FLAT_SIZING=true`. |
| **DECISION_LOG** | ✅ SESSION 37 T4 activation entry written (portfolio isolation, mode rationale, Phase 8 ADR requirement). |
| **MEMORY_BANK + TODO_NEXT + PLAN.md** | ✅ All updated. |
| **Hygiene check** | ✅ 739/739. Governance scan CLEAN. |
| **Commit b9a00b3 + VPS deploy** | ✅ git push + VPS git pull + crontab installed. |

**Test count:** 739/739 (unchanged from session start — no new code requiring tests)

---

## ONE THING PENDING

**G3 is in progress tonight.** PIPE-03 (T1 bets) fires at 22:00 UTC. PIPE-07 (T4 in-play) fires at 23:00 UTC (or start manually at tip-off ~00:30 UTC).

After the game resolves (~06:00 UTC June 9), **run both resolution scripts in sequence:**

```bash
# T1 positions (~20 open, game_date 2026-06-08)
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

# T4 positions (~1,000 expected, paper_portfolio_t4.json on VPS)
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py
```

Then re-run EXP-017 Part B. With ~1,000 T4 positions + ~20 T1 G3 positions, n should cross APR-0017 floor of 66 (note: T4 positions are `pool_isolated=True` — verify EXP-017 handles them in per-bet EV calculation).

---

## Current Paper Portfolio

- **Bankroll:** $958.99 (4.1% drawdown from $1,000 initial)
- **Open (T1):** 20 positions, game_date 2026-06-08 (Finals G3) — 2 resting (Wembanyama 35/30), 18 failed HTTP 503 (pre-GG-014 fix; G4+ should be clean)
- **Open (T4):** Will be populated tonight by PIPE-07 into `paper_portfolio_t4.json`
- **Closed/Resolved:** 35 T1 positions | G6 gate: 35/30 ✅ (threshold crossed; G6 still requires n≥66 EXP-017 + ≥5 nights)

---

## Active Cron on VPS (157.230.91.33) — POST SESSION 37

```
21:00 UTC      — Health check
21:55 UTC      — PIPE-02 pre-game inference (early window)
22:00 UTC      — PIPE-03 paper bets (early window, 7pm ET games)
23:00 UTC      — PIPE-07 T4 in-play (NEW — runs until 05:00 UTC / 6h timeout)
01:25 UTC      — PIPE-02 pre-game inference (late window)
01:30 UTC      — PIPE-03 paper bets (late window, 9pm+ ET games)
06:00 UTC      — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon  — Model freshness check
```

Manual T4 start for G3 (if starting before cron at 23:00 UTC):
```bash
ssh root@157.230.91.33 "cd /opt/prediction-market-bot && source venv/bin/activate && export $(grep -v '^#' .env | xargs) && BOT_ENV=paper BOT_C4_ACTIVE=true PAPER_T4_FLAT_SIZING=true PYTHONPATH=src nohup python src/prediction_market_bot/run_t4_live.py >> logs/t4_live_g3.log 2>&1 &"
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (n≥66 EXP-017 Part B + ≥5 game nights + positive P&L — APR-0017/APR-0016)
3. T4 portfolio is fully isolated from T1 — `paper_portfolio_t4.json` on VPS; resolve with `run_t4_resolve_local.py`
4. GG-004 OPEN: EXP-017 Part B n=33 < 66 floor. DIRECTIONAL_POSITIVE (EV=+0.1042/bet) but not confirmed.
5. VPS Akamai block: stats.nba.com blocked from VPS (GG-013). All resolution must run locally. ESPN (T4 data source) NOT blocked.
6. T4 positions have `pool_isolated=True` — bankroll not deducted at open; T1 bankroll $958.99 is accurate T1 capital.

---

## ⚙️ DECISION AUDIT

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_t4_live.py` | N/A (source file) | SESSION 37 T4 activation entry | ✅ |
| `deploy/cron.conf` | N/A (config file) | SESSION 37 T4 activation entry | ✅ |
| `run_t4_resolve_local.py` | N/A (new script) | SESSION 37 T4 activation entry | ✅ |

Governance scan: **CLEAN** — 0 documents with `**Decisions logged:** false`.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260608_1807.md,
# confirm 739 tests. G3 ran last night — run resolve scripts and re-run EXP-017 Part B."
```
