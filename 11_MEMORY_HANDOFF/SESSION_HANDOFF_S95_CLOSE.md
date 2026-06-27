# SESSION HANDOFF — S95 CLOSE

**Date:** 2026-06-27
**Session:** 95
**Operator:** Earl Ignacio
**Context at close:** ~80%+ — handoff triggered

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live on VPS 157.230.91.33
- **Tests:** 2110/2110 passing (7 skipped, 2 warnings — harmless)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — all 7 MLB crons active + T4 systemd service running
- **Paper bets — MLB T4:** 80 fires ($19.84 deployed) at session close; NONE resolved yet (resolves tonight when games end)
- **Paper bets — NBA:** 158 resolved / G6 gate; drawdown −24.9% / P&L −$248.90 (gate NOT cleared — positive P&L required)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| ESPN stat group filter bug fixed — T4 had 0 evaluations/cycle since launch | Silent filter excluded all athletes from live game stat groups; zero evaluations = zero fires = zero P&L data. Found by comparing logged eval counts vs expected throughput. | DECISION_LOG SESSION 95 entry; commit `302ce84` | EL |
| T4 MLB → systemd 3-layer defense | VPS restart or T4 crash after 13:00 UTC left T4 dead for remainder of day under old cron. Systemd `Restart=on-failure` + startup self-heal eliminates this failure mode. | `deploy/t4-mlb.service`, `deploy/t4-mlb.timer`; DECISION_LOG SESSION 95 | EL |
| T4 MLB Kalshi demo wiring (ADR-0008 parity with T1) | T4 PaperTrader was initialized without `kalshi_client` → all orders `local_only`, never flowing to Kalshi demo order book. T1 had this wired; T4 did not. | DECISION_LOG SESSION 95; commit `635d4af` | EL |
| T4 MC sim structural error corrected (60×) | Sim treated per-cycle slots as session total (234 vs 29,700). Corrected: ~1,169 evals/game validates CLAUDE.md spec of ~1,000/game. | DECISION_LOG SESSION 95 | EL |
| T1 MLB "0 players matched" flagged — T-205 registered | PIPE-05 ran at 11:00 UTC with 149 Kalshi markets + 69 pregame players, matched 0. This means T1 may be dark every day it runs. Needs root cause before tomorrow 11:00 UTC. | T-205 in TODO_NEXT.md | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| PIPE-08 midnight-wrap bugfixes | ✅ T1 + T2 date-rollover guards corrected; commit `2d54029` |
| T4 MLB startup self-heal | ✅ On startup: if UTC time > PIPE-08 optimal start, immediately load today's games; commit `982ef4f` |
| ESPN stat group filter bug | ✅ FIXED — T4 now evaluates correctly; 1,154 evals / 50 fires in first 23 cycles post-fix; commit `302ce84` |
| T4 MLB → systemd | ✅ DEPLOYED — `t4-mlb.service` + `t4-mlb.timer` created + deployed; old cron retired; date-rollover refresh in main loop; commit `9f5b869` |
| T4 MLB Kalshi demo wiring | ✅ COMPLETE — `PaperTrader(kalshi_client=kalshi if _signing_ready else None)`; routes to `external-api.demo.kalshi.co`; commit `635d4af` |
| T4 MC sim corrected + P_WIN sensitivity | ✅ 60× error found and corrected; architecture validates at ~1,169 evals/game; sensitivity table at P_WIN 0.27–0.70 produced |
| ARE WE COMPROMISED? protocol | ✅ RUN — All Q1–Q6 complete; ESPN filter bug was the critical finding; T1 matching flagged |
| Full hygiene test suite (×3 runs) | ✅ 2110/2110 passing each run |
| VPS confirmed live | ✅ T4 systemd active; 80 fires, $19.84 deployed |

---

## ONE THING PENDING

**T-205: T1 MLB "0 players matched" bug must be investigated BEFORE tomorrow's 11:00 UTC PIPE-05 run.**

State: PIPE-05 ran at 11:00 UTC today with 149 Kalshi markets fetched and 69 pregame players loaded. Zero matches. Suspected cause: player name normalization mismatch between pregame JSON keys (from ESPN/MLB Stats API names) and Kalshi market ticker/name format.

To investigate:
1. `ssh prediction-market-vps "cat /opt/prediction-market-bot/logs/paper_mlb_cron.log | grep -E '2026-06-27|player|match|market' | head -50"`
2. Compare a sample Kalshi market name (`KXMLBHIT-26JUN271310HOUDET-*`) vs pregame player name format
3. Check `market_mapper.py` name normalization function
4. Compare against T4's name matching (T4 successfully matches — what's different?)

If the bug is a simple name normalization mismatch: fix in `run_mlb_paper_trade.py`'s market-matching logic and redeploy before 11:00 UTC tomorrow.

---

## Current Paper Portfolio

- **NBA (main book):** $751.10 bankroll | 0 open | 158 resolved | −$248.90 P&L (24.9% drawdown) | G6 gate: P&L condition FAILING
- **MLB T4:** $1,000 bankroll | 80 open (resolving tonight) | 0 resolved | $19.84 deployed
- **MLB T1/T2:** 0 open (T1 fired but matched 0 players; T2 runs at 19:30 UTC)

---

## Active Cron on VPS (157.230.91.33)

```
MLB:
  0  8  * * *    PIPE-08 schedule validation (08:00 UTC)
  0 11  * * *    PIPE-05 T1 MLB paper bets (11:00 UTC) — ⚠️ MATCHED 0 PLAYERS TODAY
  30 16 * * *    PIPE-06pre MLB pregame context (16:30 UTC)
  30 19 * * *    PIPE-05.5 T2 MLB lineup overlay (19:30 UTC)
  30 22 * * *    PIPE-05FX MLB feature refresh (22:30 UTC)
  30  6 * * *    PIPE-05R MLB resolution (06:30 UTC)
  */15 20-23, */15 0-3 UTC  PIPE-07.3 T3 MLB pre-tip scan

T4 MLB:
  systemd t4-mlb.service — RUNNING (Restart=on-failure; WantedBy=multi-user.target)
  systemd t4-mlb.timer   — ACTIVE (daily 13:00 UTC trigger; Persistent=true)
```

---

## Deployment State

| Item | State |
|------|-------|
| VPS | 157.230.91.33 / `/opt/prediction-market-bot` |
| git HEAD | `635d4af` (5 commits this session) |
| T4 service | systemd `t4-mlb.service` ACTIVE; `Restart=on-failure` confirmed |
| T4 timer | `t4-mlb.timer` ACTIVE; fires 13:00 UTC daily |
| T4 live | 80 fires, $19.84 deployed, 1,154+ evals/session |
| T1 status | ⚠️ 0 players matched June 27 — T-205 investigation required |
| Test suite | 2110 passing / 7 skipped |

---

## Key Constraints to Remember

1. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016). G6 P&L gate is currently FAILING (−$248.90).
2. T-205 HIGH priority — T1 MLB may be completely dark due to player name matching bug.
3. First MLB T4 resolutions come via PIPE-05R at 06:30 UTC June 28 — this is the first empirical read on T4 binomial model win rate (GG-046).
4. T4 "multi-bet concentration": same player-threshold pair can accumulate many bets per game (Bayesian design). Normal. Will need per-outcome cap when sizing scales to live capital.

---

## ⚙️ DECISION AUDIT

Governance scan: CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged | DECISION_LOG entries | Status |
|----------|-----------------|---------------------|--------|
| No architecture docs modified this session | N/A | 4 entries written (SESSION 95 ESPN filter, systemd migration, Kalshi wiring, MC sim correction) | ✅ |

---

## Open Governance Gaps (condensed)

| Gap | Description | Priority |
|-----|-------------|----------|
| GG-004 | Commercial validation (EXP-017) — no demonstrated alpha vs Kalshi | G6 blocker |
| GG-007 | NBA Phase 8 ADR-0029 skeleton constants | LOW (Phase 8 pre-activation) |
| GG-020 | Kalshi fee 0.07 unverified for MLB player props — post-G6 receipt check | LOW |
| GG-038 | T4 kill switch ≤5s SLA (Phase 8 prereq) | Phase 8 blocked |
| GG-039 | T4 price cache / staleness (Phase 8 prereq) | Phase 8 blocked |
| GG-040 | T4 real-time data sources (Phase 8 prereq) | Phase 8 blocked |
| GG-043 | MLB Kelly fraction 0.10 inherited from NBA — needs MLB-specific derivation | LOW |
| GG-044 | C7 drift baselines are NBA G4 values | LOW (calib monitor not enabled) |
| GG-045 | Kalshi market depth capital ceiling unanalyzed | LOW now, HIGH at G8–G9 |
| GG-046 | T4 commercial validation — independent alpha hypothesis untested | LOW (paper phase) |

---

## Artifacts Modified This Session

| File | Change |
|------|--------|
| `src/prediction_market_bot/run_t4_mlb_live.py` | ESPN filter fix; startup self-heal; date-rollover refresh; Kalshi client wiring |
| `deploy/cron.conf` | T4 MLB cron line commented out (REPLACED BY SYSTEMD) |
| `deploy/t4-mlb.service` | CREATED — systemd service unit |
| `deploy/t4-mlb.timer` | CREATED — systemd timer unit |
| `deploy/install_systemd_t4_mlb.sh` | CREATED — install script |
| `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` | 4 SESSION 95 entries added |
| `04_EXECUTION/TODO_NEXT.md` | SESSION 95 COMPLETE block + T-205 + T-206 registered |
| `11_MEMORY_HANDOFF/MEMORY_BANK.md` | Last reviewed updated |
| `04_EXECUTION/PLAN.md` | Last reviewed updated |
| `11_MEMORY_HANDOFF/SESSION_HANDOFF_S95_CLOSE.md` | CREATED (this file) |

---

## Priority Queue for Next Session

1. **T-205 (HIGH):** Investigate T1 MLB "0 players matched" — check `logs/paper_mlb_cron.log`, compare player name formats, fix market_mapper name normalization before 11:00 UTC tomorrow
2. **Monitor PIPE-05R at 06:30 UTC June 28** — first MLB T4 position resolutions; compute win rate vs mip distribution; first empirical T4 calibration signal
3. **Monitor T1 MLB tomorrow 11:00 UTC** — did T-205 fix hold? Any T1 bets fire?
4. **Watch T4 tonight** — games continue; budget currently at 7% ($19.84/$270); expect 300+ more fires before games end

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_S95_CLOSE.md, 
# then investigate T-205 (T1 MLB 0 players matched — check logs/paper_mlb_cron.log on VPS)"
```
