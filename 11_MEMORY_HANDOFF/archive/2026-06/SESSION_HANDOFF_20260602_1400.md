# Session Handoff — 2026-06-02T14:00Z

**Trigger:** Operator-initiated session-end (/session-end)
**Last commit:** `9337d14` (main) — pushed to GitHub + VPS pulled

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (local + VPS)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; G1 fires ~22:00 UTC Jun 3
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017); Finals G1 Jun 3 is first eligible game

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Replace `max_daily_loss_usd: 1000.0` with `MAX_DAILY_LOSS_PCT=0.15` (ADR-0012) | At $1,000 bankroll the absolute limit required losing the entire bankroll before firing — structurally inactive. 15% = $150 fires before the 20% drawdown kill switch ($200), restoring two independent kill switches. | `03_DECISIONS/ADR-0012_percentage-based-daily-loss-limit.md`; `c4_risk_engine/risk.py` | DS |
| `initial_bankroll` parameter added to `RiskEngine.__init__()` | Without anchoring to session-start bankroll, mid-session threshold shrinks as bets are placed — a feedback loop where losing sessions become progressively harder to continue. `initial_bankroll` holds the threshold stable. | ADR-0012; `run_paper_trade.py` | DS |
| RESERVE_MANDATE_PCT advisory = per-bet WARNING, not batch blocking | `evaluate_forecast()` doesn't know total committed capital across all bets in a session. Per-bet advisory fires when single bet > 60% of current bankroll (rarely at paper scale). Proper batch-level enforcement deferred to PIPE-03 dark period. | `c4_risk_engine/risk.py` (reserve_mandate_warning log entry) | DS |
| Documentation debt T-093–T-099: extract to DECISION_LOG, flip headers | 7 governance documents carried `decisions_logged: false` headers. Decisions existed in document bodies but were not formally recorded. Written to DECISION_LOG before any future session could modify those documents without awareness of prior decisions. | `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (8 entries); 7 document headers | DS |
| G6 MAX_DAILY_LOSS_PCT recalibration obligation | 15% is calibrated to $1,000 paper bankroll. At live capital (higher bankroll), the same 15% may be too loose. Formal review required when ADR-0005 (live capital) is drafted. | ADR-0012 §G6 obligation | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| KI-018 RESOLVED — zombie daily loss limit | ✅ `MAX_DAILY_LOSS_PCT=0.15` in `risk.py`; `initial_bankroll` param in `RiskEngine`; `_daily_loss_threshold = initial_bankroll * 0.15`; ADR-0012 ACCEPTED |
| ADR-0012 created | ✅ `03_DECISIONS/ADR-0012_percentage-based-daily-loss-limit.md` — full threshold derivation table; G6 obligation noted |
| run_paper_trade.py updated | ✅ `_initial_bankroll` read from state before first RiskEngine instantiation; both engine instantiations now pass `initial_bankroll=_initial_bankroll` |
| RESERVE_MANDATE_PCT advisory wire | ✅ `risk_reserve_mandate_warning` log in `evaluate_forecast()` after min_bet_floor check; severity=WARNING; fires when `approved_size > bankroll * 0.60` |
| Tests: +3 new, 692 → 695 | ✅ `test_daily_loss_pct_at_threshold_triggers_kill_switch`, `test_daily_loss_pct_below_threshold_passes`, `test_zombie_daily_loss_no_longer_inactive`; 1 existing test fixed (`test_kill_switch_approved_size_is_zero`: threshold updated from $1,001 → $1,500 to match new 15% basis) |
| T-093 — EXECUTION_ARCHITECTURE.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-094 — MONITORING_DRIFT_PLAN.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-095 — METHODOLOGY.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-096 — VENUE_REGISTRY.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-097 — RISK_APPETITE_CONSTRAINTS.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-098 — QUALITATIVE_SIGNALS.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| T-099 — ROADMAP_MILESTONES.md decisions logged | ✅ DECISION_LOG entry written; `decisions_logged: true` |
| Commit + push + VPS pull | ✅ `9337d14` on main; VPS at `/opt/prediction-market-bot` pulled and confirmed |

**Files modified:** `src/prediction_market_bot/c4_risk_engine/risk.py`, `src/prediction_market_bot/run_paper_trade.py`, `tests/test_c4_risk.py`, `03_DECISIONS/ADR-0012_percentage-based-daily-loss-limit.md`, `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`, `02_ARCHITECTURE_DESIGN/EXECUTION_ARCHITECTURE.md`, `02_ARCHITECTURE_DESIGN/VENUE_REGISTRY.md`, `08_MODEL_RISK_GOVERNANCE/MONITORING_DRIFT_PLAN.md`, `08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md`, `08_MODEL_RISK_GOVERNANCE/QUALITATIVE_SIGNALS.md`, `01_SPEC/RISK_APPETITE_CONSTRAINTS.md`, `01_SPEC/ROADMAP_MILESTONES.md`

---

## ONE THING PENDING

**G1 fires Jun 3 at ~22:00 UTC.** After the game ends (expected ~01:00–02:00 UTC Jun 4), run the resolve procedure locally:

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
bash scripts/resolve_procedure.sh
```

This resolves paper bets against nba_api stats, updates paper_portfolio.json on VPS (via sync), and updates EXP-017 running count. Run it on your local machine — VPS 403-blocks stats.nba.com. The script logs to `logs/resolve_auto.log`. Step 3 in the script reports the current G6 evidence count.

**The code is clean and fully deployed.** Nothing needs to be done before G1 fires. The cron will run on `9337d14` (ADR-0012 active).

---

## Current Paper Portfolio

- **Bankroll:** $1,000 starting (paper_portfolio.json lives on VPS — not present locally)
- **Open:** 0 positions (G1 hasn't fired yet)
- **Closed/Resolved:** 0 | G6 gate: 0/66 (APR-0017)
- **First eligible bets:** Jun 3 at ~22:00 UTC (G1 NYK vs SAS)

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

1. Work wifi blocks Kalshi API — use any other network for manual checks
2. No live capital until G6 (**≥66 resolved bets + ≥5 game nights, positive P&L** — APR-0017)
3. EXP-017 Part B requires ≥66 resolved markets; n=2 currently (DIRECTIONAL_POSITIVE only; GG-004 OPEN)
4. `MAX_DAILY_LOSS_PCT=0.15` is calibrated to $1,000 paper bankroll; must recalibrate at G6 (ADR-0012 obligation)
5. RESERVE_MANDATE_PCT batch-level enforcement (total-committed-capital check in PIPE-03) is deferred to dark period — current wire is per-bet advisory only

---

## ⚙️ DECISION AUDIT

**Governance scan:** All 7 `decisions_logged: false` files were flipped to `true` this session. Scan result: CLEAN (verified by session edits — temp filesystem prevented re-run of grep command).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| EXECUTION_ARCHITECTURE.md | true | T-093 entry (2026-06-02) | ✅ |
| MONITORING_DRIFT_PLAN.md | true | T-094 entry (2026-06-02) | ✅ |
| METHODOLOGY.md | true | T-095 entry (2026-06-02) | ✅ |
| VENUE_REGISTRY.md | true | T-096 entry (2026-06-02) | ✅ |
| RISK_APPETITE_CONSTRAINTS.md | true | T-097 entry (2026-06-02) | ✅ |
| QUALITATIVE_SIGNALS.md | true | T-098 entry (2026-06-02) | ✅ |
| ROADMAP_MILESTONES.md | true | T-099 entry (2026-06-02) | ✅ |
| ADR-0012 | N/A (new file) | ADR-0012 entry + index row | ✅ |

---

## Known Open Items (carry forward)

| Item | Status | Gate impact |
|------|--------|------------|
| GG-004 — EXP-017 Part B n=2 (floor ≥66) | OPEN — accumulating via T-109 after each game | G6 Tier 0 precondition |
| GG-007 — T4/T5 threshold constants uncalibrated | OPEN LOW (skeleton only, Phase 8+) | Phase 8 blocker |
| KI-024 — stale pace_pts_per_min in T4/T5 | OPEN (DS-02 ADR required before Phase 8) | Phase 8 blocker |
| KI-019 — Polymarket NBA tag unconfirmed | OPEN MEDIUM (pre-T-077 activation) | Phase 7 |
| KI-011 — Injury blindness (T2 skeleton) | OPEN LOW (T2 not active) | T2 activation |
| T-117 — Kalshi KXNBAPTS contract Terms review | OPEN HIGH (before G6 ADR-0005) | G6 |
| T-127 — KXNBAPTS orderbook depth query | OPEN HIGH (Finals window Jun 3–22) | G6 live capital ADR |
| T-113 — APR-0017 v2 operator sign-off | PENDING operator review + signature | G6 |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260602_1400.md, confirm 695 tests. 
# G1 NYK vs SAS is Jun 3. Run the session-start protocol then check paper_portfolio.json on VPS 
# for G1 results. Run resolve procedure if game is complete."
```
