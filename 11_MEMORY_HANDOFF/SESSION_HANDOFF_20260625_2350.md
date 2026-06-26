# Session Handoff — 2026-06-25T23:50Z (SESSION 88)

**Trigger:** Context window near limit
**Last commit:** pending (commit at end of this session)

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live on VPS (MLB arm PAUSED pending Phase MLB-G1)
- **Tests:** 1947/1947 passing (no new tests this session — integration tests are not in standard suite)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — NBA cron running, ALL MLB crons PAUSED (Phase MLB-G1)
- **Paper bets:** 0 MLB resolved — MLB arm paused. NBA arm G6 baseline: −$251.21/−25.1% drawdown, kill switch active
- **MLB bankroll:** $1,000 fresh pool, 0 open, 0 closed — preserved while paused

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **Phase MLB-G1 gate established** — MLB arm will not fire a single bet until integration tests, freshness guards, resolution age-out, kill switch drill, and governance docs are all complete | MLB was deployed in 2 sessions (S86–S87) without the gate rigor the NBA arm received. The 0-bet observation on June 25 (T1 firing at 03:00 UTC when Kalshi shows only previous-day markets) revealed the arm was never validated before activation. Earl directive: build it right, no corners cut. | `SESSION_HANDOFF_20260625_2350.md` + `deploy/cron.conf` (all 9 MLB lines PAUSED) | DS |
| **All 9 MLB crons paused on VPS** | Hard pause while Phase MLB-G1 builds. Nine lines in deploy/cron.conf updated with "PAUSED — Phase MLB-G1" comments. Deployed and verified on VPS: zero active MLB cron lines. | `deploy/cron.conf` (VPS deployed) | DS |
| **MLB T1 cron timing: 03:00 UTC is wrong; must move to 11:00 UTC on re-enable** | At 03:00 UTC, Kalshi KXMLBHIT markets show only the previous calendar day's games (June 25 ET games). June 26 ET games are not yet published. Fix is 11:00 UTC (confirmed publication by VPS log evidence ~01:58 UTC, but safer margin is 11:00 UTC). Already documented in paused cron.conf comment. Source code comment in run_mlb_paper_trade.py still references 03:00 UTC and must be updated when cron is re-enabled (T-196). | `deploy/cron.conf` paused comment | DS |
| **Integration test suite created for Phase MLB-G1** (T-192) | Real API tests (no mocks) covering: MLB Stats API (5 endpoints), ESPN (6 endpoints), Kalshi KXMLBHIT (7 structure/validity tests), player name matching (≥90% gate), full pipeline dry-run (6 stages: feature load → cohort build → market filter → name match → feature vector assembly → model scoring → C4 check). These are the MLB-G1 gate tests. | `tests/integration/` (4 files) | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **Pause all 9 MLB crons on VPS** | ✅ All 9 MLB cron lines in deploy/cron.conf commented out with "PAUSED — Phase MLB-G1". Deployed to VPS. Verified: zero active MLB cron lines. |
| **T-192: Phase MLB-G1 integration test suite** | ✅ `tests/integration/__init__.py`, `tests/integration/conftest.py`, `tests/integration/test_mlb_api_connectivity.py`, `tests/integration/test_mlb_name_matching.py`, `tests/integration/test_mlb_pipeline_smoke.py`. Session-scoped fixtures, real API calls, marked `pytest.mark.integration`. ≥90% name match gate, 5s latency SLA, T4 10s SLA, freshness 7-day gate, C4 dry-run. |

---

## Phase MLB-G1 — Remaining Tasks

These tasks must ALL be complete before any MLB cron re-enables:

| T-NNN | Task | Priority |
|-------|------|----------|
| **T-193** | Feature CSV freshness guard: add to `run_mlb_paper_trade.py` (>3 days → WARNING log; >7 days → sys.exit(1)) + C7 alert | P0 |
| **T-194** | Resolution age-out: positions open >48h that can't resolve → `aged_open` status + C7 alert. Currently they stay open indefinitely (silent). | P0 |
| **T-195** | Silent fallback audit: every `except Exception` in MLB pipeline files that `continue`s silently must either be converted to a C7 alert or documented as "silent-by-design" with a reason. Key files: `run_mlb_paper_trade.py` (SP overlay, lineup fetch, contamination guard), `run_mlb_pregame.py`, `run_t2_mlb_sameday.py`. | P0 |
| **T-196** | Fix T1 MLB cron timing comment in `run_mlb_paper_trade.py` (still says 03:00 UTC in source). On re-enable: set to 11:00 UTC. | P1 |
| **T-197** | MLB kill switch drill: equivalent of TC-007/APR-0013 from NBA. Touch `logs/paper_mlb_kill_switch.flag` and verify all MLB crons halt within 60s. Register APR. | P0 |
| **T-198** | Register Phase MLB-G1 gaps in governance: (1) GG for Kelly fraction (MLB inherits NBA T1_KELLY=0.10; MLB AUC=0.589 vs NBA ~0.63 — not calibrated); (2) GG for C7 drift baseline (MLB uses NBA Brier/ECE baselines — wrong sport); (3) ADR for Phase MLB-G1 gate definition. | P1 |
| **T-199** | MLB-G1 gate close: run all integration tests, confirm all T-193–T-198 complete, re-enable MLB crons (11:00 UTC T1, others at original times), deploy to VPS, reinstall crontab. | GATE |

---

## ONE THING PENDING

**Phase MLB-G1 is not complete. MLB arm is fully paused.** The integration test suite (T-192) is written but not yet run against real APIs. Next session should: (1) run `pytest tests/integration/ -v -m integration` locally or from VPS, (2) build T-193 freshness guard, (3) work through T-194 through T-198 in order.

The integration tests are at `tests/integration/` and use session-scoped fixtures — run time is ~30–60s (one Kalshi snapshot, one feature CSV load, shared across all tests).

---

## Current Paper Portfolio

- **MLB bankroll:** $1,000 (fresh pool, 0 open, 0 closed — PAUSED)
- **NBA bankroll:** ~$707.78 (−$251.21/−25.1% drawdown, kill switch ACTIVE, NBA off-season — 0 active games)
- **G6 gate:** 0/30 resolved MLB paper bets (NBA arm blew through G6 baseline negative)

---

## Active Cron on VPS (157.230.91.33)

```
NBA crons:   ACTIVE (dark — off-season, 0 games)
MLB crons:   ALL PAUSED — Phase MLB-G1
```

MLB cron lines to re-enable (in deploy/cron.conf) when MLB-G1 gate closes:
- T3 pretip ×2 (PIPE-06pre + PIPE-06pre-late)
- T1 PIPE-05 → **must move to 11:00 UTC** (was 03:00 UTC — wrong)
- T2 PIPE-05.5 (19:30 UTC)
- T4 PIPE-07 (22:00 UTC)
- PIPE-05R resolve (06:30 UTC)
- PIPE-05FX feature refresh
- Calibration monitor

---

## Key Constraints to Remember

1. MLB arm is PAUSED — no bets until Phase MLB-G1 gate is closed
2. MLB T1 cron must run at **11:00 UTC** (not 03:00 UTC) — Kalshi doesn't publish same-day markets until ~01:58 UTC, and 03:00 UTC was showing prior-day games
3. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
4. `normalize_player_name` is in `c5_execution/market_mapper.py:47` — not in mlb_ingestion.py
5. Integration tests require `.env` (Kalshi credentials) and feature CSV at `exp_output/MLB/mlb_feature_matrix.csv`

---

## ⚙️ DECISION AUDIT

**Governance scan result:** CLEAN — no `decisions_logged: false` documents modified this session.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `tests/integration/*` (new test files) | N/A — test files have no decisions_logged field | N/A | ✅ No entries needed |
| `deploy/cron.conf` (MLB paused) | N/A | Phase MLB-G1 strategic decision → this SESSION_HANDOFF + DECISION_LOG | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260625_2350.md, then continue Phase MLB-G1 with T-193 (freshness guard)"
```
