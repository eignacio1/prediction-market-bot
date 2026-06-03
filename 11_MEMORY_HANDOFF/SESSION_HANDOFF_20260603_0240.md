# Session Handoff — 2026-06-03T02:40Z

**Trigger:** Operator-initiated session end (game night — G2 tip-off in ~22 hours)  
**Last commit:** `2446a02` (main) — pushed to GitHub + pulled to VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (VPS)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; T4 screen `139678.t4_live` LIVE
- **Paper bets:** 0 resolved in new G6 window (clean slate since G1 portfolio wipe) — G6 gate: accumulating

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| ESPN API as primary T4 live data source (permanent) | NBA CDN (`cdn.nba.com`, `stats.nba.com`) blocked on VPS by Akamai WAF — returns Access Denied for all cloud IPs. ESPN API (`site.api.espn.com`) confirmed unblocked. Verified against completed SAS vs OKC game. | DECISION_LOG.md 2026-06-03 SESSION 18 / PIPE-07 entry | DS |
| `min_bet_usd` param on RiskEngine (paper T4 uses $1.0 floor) | $10 live floor suppresses all paper T4 bets at current bankroll scale — defeats evidence accumulation purpose without protecting real capital. Paper-only init param; live path unchanged; no ADR required. | DECISION_LOG.md 2026-06-03 SESSION 18 / risk.py entry | DS |
| Ghost protection ordering: stage BEFORE open in T4 cycle | SQLite WAL ACID write (`stage_order`) before JSON write (`open_position`) ensures orphan detection if JSON write fails. Reverse ordering leaves no trace. | DECISION_LOG.md 2026-06-03 SESSION 18 / PIPE-07 entry | DS |
| Per-cycle idempotency only: `fired_tickers` resets each 45s cycle | T4 re-entry of same ticker in next cycle after price move is intentional — it's a new signal, not a duplicate. Cross-cycle dedup would defeat continuous in-play polling. | DECISION_LOG.md 2026-06-03 SESSION 18 / PIPE-07 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| `KalshiMarketClient.from_env()` fix | ✅ `run_t4_live.py` was calling `KalshiMarketClient()` directly — missing required `api_key_id` arg. Fixed to `from_env()` classmethod. Commit `451abf2`. |
| `run_t4_live.py` — PIPE-07 full implementation | ✅ New file: 45s poll cycle; T4EventLoop → staged_order_store (SQLite WAL) → C4 RiskEngine → PaperTrader; ESPN live feed; `fired_tickers` per-cycle dedup; ghost protection; `MIN_BET_T4_PAPER=1.0`; `BOT_C4_ACTIVE` guard; `KILL_SWITCH_PATH`; session/cycle logging. Commit `47e9a2b`. |
| ESPN API integration — replace blocked NBALiveFeed | ✅ `_espn_game_ids_today()`: scoreboard discovery (in-progress first). `_parse_espn_clock()`: `period + displayClock → minutes_remaining`. `_espn_poll_once()`: boxscore → `list[LivePlayerState]`. `_load_pregame_context()` updated to return `name_to_pregame` as 3rd value. `main()` updated: removed `live_feeds`, `_refresh_feeds()`, `cohort_ids`; replaced with ESPN polling loop. Commit `2446a02`. |
| VPS deployment — screen session restart | ✅ `BOT_C4_ACTIVE=true` added to `/opt/prediction-market-bot/.env`. Old screen `136196.t4_live` killed. New screen `139678.t4_live` started with venv + .env. Confirmed running: `Loaded 9 player(s), 35 market(s)`; game `401859963` found; `STATUS_SCHEDULED` → sleeping 60s. Will auto-poll when game goes `IN_PROGRESS`. |
| 4 DECISION_LOG entries | ✅ ESPN source decision, MIN_BET_USD override, ghost protection ordering, per-cycle idempotency. |

---

## ONE THING PENDING

**T4 is armed and will fire automatically at G2 tip-off (~00:30 UTC June 4). The next immediate action is monitoring.**

After the game: run `run_resolve_local.py` to settle T4 positions and accumulate EXP-017 data.

**Exact monitoring command:**
```bash
ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'
```

Watch for status transition: `STATUS_SCHEDULED → STATUS_IN_PROGRESS`. Once in progress, `_run_cycle()` executes every 45s. FIRE_BAYESIAN and FIRE_T5 events will appear in the log.

**Kill switch (if needed):**
```bash
ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'
```

Remove with: `rm /opt/prediction-market-bot/logs/t4_kill_switch.flag`

**Post-game resolution procedure (T-109):**
```bash
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```

Then sync VPS pregame files for EXP-017:
```bash
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio
```

---

## Current Paper Portfolio

- Bankroll: Unknown (VPS `paper_portfolio.json` — check after G1 T1 cron fires tonight)
- T1 cron fires at 21:55 UTC tonight (Jun 3) for G2
- T4 fires in-play from 00:30 UTC June 4
- G6 gate: 0 resolved positions in current clean window

---

## Active Cron on VPS (157.230.91.33)

```
21:55 UTC  — PIPE-02 inference (run_pregame.py) — G2 pregame
22:00 UTC  — PIPE-03 early (paper bets, T1 — early games)
01:25 UTC  — PIPE-02 second window (late-game price refresh)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check

T4 SCREEN (continuous): screen 139678.t4_live
  — 45s poll; ESPN API; STATUS_SCHEDULED → IN_PROGRESS → polling active
```

---

## Key T4 Architecture (for next session)

`run_t4_live.py` flow per cycle:
1. `_espn_poll_once(gid, name_to_pregame)` → `list[LivePlayerState]`
2. `_run_cycle(live_states, pregame_by_player_id, ...)` — per player × per market:
   a. Build `GameStateEvent(pts_so_far, time_remaining_min, pace_pts_per_min, p_t1, threshold)`
   b. `loop.on_game_state_event(event)` → `T4RoutingResult(action, ...)`
   c. If `FIRE_BAYESIAN` or `FIRE_T5`: build fc_record, call `engine.evaluate_forecast()`
   d. If `APPROVED`: `store.stage_order()` → `trader.open_position()` → `store.mark_fired()`
3. Log cycle summary: evaluated / fired / rejected counts

**ESPN constants that matter:**
- Scoreboard URL: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`
- Summary URL: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary`
- Status: `STATUS_SCHEDULED`, `STATUS_IN_PROGRESS`, `STATUS_FINAL`
- PTS index: `labels.index("PTS")` (typically index 1); MIN at index 0

**ADR-0011 note:** ADR-0011 scoped T4 to "NBA Stats API CDN polling" — that source is now ESPN. If T4 produces evidence (EXP-018/019), supersede ADR-0011 with an ADR naming ESPN explicitly and documenting schema-change risk.

---

## Open Governance Items (Unchanged from Prior Sessions)

| Gap | Status |
|-----|--------|
| GG-004 | OPEN — EXP-017 n=2 unique markets; floor ≥66; accumulating each Finals game |
| GG-006 | SUBSTANTIALLY RESOLVED — T-117 (formal TOS + KXNBAPTS PAL read) pending; due Week 1 dark period (by 2026-06-30) |
| GG-007 | OPEN — T4_MIN_DELTA_P + T5 certainty thresholds uncalibrated; LOW now, HIGH pre-Phase 8 ACTIVE |

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (APR-0017: ≥66 resolved bets + ≥5 game nights + EXP-017 positive EV vs real prices)
3. ESPN API is unofficial — schema changes without notice; if T4 stops getting states, check ESPN format first
4. `BOT_C4_ACTIVE=true` must be in VPS `.env` for `run_t4_live.py` to run
5. Kill switch: `touch logs/t4_kill_switch.flag` halts T4 within one cycle (~45s); remove file to resume

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `**Decisions logged:** false` documents found in `02_ARCHITECTURE_DESIGN/`, `08_MODEL_RISK_GOVERNANCE/`, `01_SPEC/`.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_t4_live.py` (new file) | N/A — source file | 4 entries written 2026-06-03 | ✅ |
| `risk.py` (min_bet_usd param) | N/A — source file | 1 entry written 2026-06-03 | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_0240.md.
# G2 tip-off was 00:30 UTC June 4. Check T4 screen logs and paper_portfolio.json.
# Run T-109 resolution procedure if game is complete."
```
