# Session Handoff — 2026-06-01T19:00Z

**Trigger:** Context window near limit — operator-initiated session end  
**Last commit:** `710e8bf` (main) — pushed to GitHub

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 589/589 passing (VPS)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running
- **Paper bets:** 0/66 resolved — APR-0017 statistical floor; Finals G1 Jun 3 is the first live fire

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T-115: Evaluate ALL Kalshi thresholds per player, not just the closest | `closest = min(player_mkts, ...)` suppressed throughput 7–8×. p_est is player-level; each threshold is an independent signal. Full-loop restores design intent: ~25–40 bets/game T1 regular season. Finals: 175–280 bets across 7 games vs ~70 borderline single-threshold. | DECISION_LOG.md (2026-06-01 T-115 entry) | DS |
| T-091: P&L alert thresholds are percentage-based (5%/10%), not fixed dollar amounts | Fixed dollar thresholds ($50/$100) become meaningless after drawdown — same dollar loss represents a larger fraction of a smaller bankroll. Percentage-based thresholds scale correctly at all bankroll levels. | DECISION_LOG.md (2026-06-01 T-091 entry) | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-115 (KI-022) | ✅ `for mkt in player_mkts:` loop replaces `closest = min(player_mkts, ...)` in `run_paper_trade.py`. Features (`X`, `p_est`) computed once per player; each threshold independently evaluated through idempotency + C4 + PaperTrader. Restores ~25–40 bets/game regular season T1. Files: `src/prediction_market_bot/run_paper_trade.py` (core change at old line 290). Governance: DECISION_LOG, TODO_NEXT, KNOWN_ISSUES (KI-022 → RESOLVED), MEMORY_BANK all updated. 438/438 tests (local, sans scipy incompatible files). |
| T-091 (KI-012) | ✅ `check_portfolio_pnl()` added to `SystemMonitor`. Constants `PNL_L1_LOSS_PCT = 0.05` and `PNL_L2_LOSS_PCT = 0.10` in `c7_monitoring/monitor.py`. L1 (≥5% loss of initial bankroll) → C6 INFO `pnl_alert_l1_watch`; L2 (≥10%) → C6 WARNING `pnl_alert_l2_loss`. Wired into PIPE-03 (`run_paper_trade.py`) and PIPE-03R (`run_resolve.py`). 8 new tests in `tests/test_c7_monitor.py`. Mock fix in `tests/test_run_resolve.py` (`initial_bankroll_usd: 1000.0` added). Governance: DECISION_LOG, TODO_NEXT (T-091 ✅), KNOWN_ISSUES (KI-012 → RESOLVED), MEMORY_BANK all updated. |
| VPS deploy (T-115 + T-091) | ✅ `git pull` on VPS to commit `710e8bf`. 589/589 VPS tests pass. |
| T-091 governance (this session block) | ✅ DECISION_LOG, TODO_NEXT, KNOWN_ISSUES, MEMORY_BANK updated and committed `710e8bf`. |

---

## ONE THING PENDING

**Finals G1 Jun 3 — first live paper bet fire on the corrected system.**

State: VPS cron is running. `paper_portfolio.json` does NOT exist (clean slate; cron creates it on first fire). The 22:00 UTC PIPE-03 run on Jun 3 will be the first G6-eligible bet placement. After the game, run the T-109 procedure:

```bash
# Step 1 — resolve locally (VPS 403 blocks nba_api)
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

# Step 2 — pull pregame price files from VPS for EXP-017
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio

# Step 3 — once ≥66 resolved markets accumulated, re-run EXP-017 Part B
```

EXP-017 Part B is at n=2, DIRECTIONAL_POSITIVE. GG-004 is OPEN until ≥66 markets. This is the binding G6 constraint — not bet count.

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (clean slate — 0% drawdown)
- Open: None
- Closed/Resolved: 0 | G6 gate: 0/66 (APR-0017 statistical floor; + ≥5 game nights)
- `paper_portfolio.json`: DOES NOT EXIST on VPS — cron creates it at first fire (Finals G1 Jun 3)

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
2. No live capital until G6: APR-0017 — ≥66 resolved bets + ≥5 game nights + EXP-017 Part B CONFIRMED + Tier 1–3 evidence
3. VPS 403 blocks nba_api: resolution must run locally via `run_resolve_local.py`
4. `arb/` folder = REFERENCE ONLY until APR-0010 signed (ADR-0002)
5. Polymarket adapter built (T-077) but requires operator KYC + API key provisioning before activation
6. Local venv scipy incompatibility: 5 test files excluded with `--ignore` flags (KI-021 cleared — delta max 0.00106, zero direction flips; VPS runs 589/589)

---

## ⚙️ DECISION AUDIT

**Governance scan (Step 0):** 7 documents with `decisions_logged: false` — T-093 through T-099 registered. No documents with `decisions_logged: false` were created or modified this session.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `c7_monitoring/monitor.py` | n/a (code) | T-091 entry written | ✅ |
| `run_paper_trade.py` | n/a (code) | T-115 entry written | ✅ |
| `run_resolve.py` | n/a (code) | T-091 entry written | ✅ |
| `DECISION_LOG.md` | n/a | T-115 + T-091 entries added | ✅ |
| `KNOWN_ISSUES.md` | n/a | KI-012 + KI-022 RESOLVED | ✅ |
| `MEMORY_BANK.md` | n/a | KI-012 RESOLVED noted | ✅ |
| `TODO_NEXT.md` | n/a | T-091 + T-115 ✅ | ✅ |

---

## Open Governance Debt (T-093–T-099)

7 `decisions_logged: false` documents — all pre-registered with T-NNNs, all LOW priority, none modified this session:

| Task | Document | Unlogged decisions |
|------|----------|--------------------|
| T-093 | EXECUTION_ARCHITECTURE.md | 4 execution mode design, paper fill assumptions, idempotency key, decision cycle ordering |
| T-094 | MONITORING_DRIFT_PLAN.md | L1–L4 drift thresholds (Brier 0.255/0.265/0.275/0.280; win rate 54%/52%/48%), metric selection |
| T-095 | METHODOLOGY.md | PRF framework choices, ±0.02 edge threshold, A–H sequencing |
| T-096 | VENUE_REGISTRY.md | V-001–V-005 prioritization, activation roadmap sequencing, per-venue edge formulas |
| T-097 | RISK_APPETITE_CONSTRAINTS.md | Rationale for $500/bet, $1,000/day, 20% drawdown thresholds attributed to this doc |
| T-098 | QUALITATIVE_SIGNALS.md | L1/L2/L3 amplification architecture, qualitative governance rules |
| T-099 | ROADMAP_MILESTONES.md | G7–G9 gate criteria and phase sequencing |

*Resolve during dark period (Jun 22 – Oct 2026). Non-blocking for G6.*

---

## Open Known Issues (Active)

| KI | Severity | Status | Blocks |
|----|----------|--------|--------|
| KI-010 | LOW | OPEN — inter-series gap | Non-blocking |
| KI-011 | HIGH | OPEN — injury blindness (fake alpha) | T2 activation |
| KI-013 | MEDIUM | OPEN — model staleness 2026-27 | G6 quality |
| KI-018 | LOW | OPEN — max_daily_loss_usd inactive at current bankroll | Non-blocking (drawdown % operative) |
| KI-019 | MEDIUM | OPEN — Polymarket tag "nba" unconfirmed | T-077 activation |

---

## What Must Happen Next (Priority Order)

1. **Jun 3 Finals G1** — First live cron fire on corrected system. T-109 procedure after game.
2. **T-109 (standing)** — After EACH Finals game: local resolve → fetch pregame prices → accumulate EXP-017 data.
3. **T-077 (dark period)** — Polymarket API key provisioning (operator action).
4. **T-092 (dark period)** — Model retrain before 2026-27 season (ADR required; target Oct 2026).
5. **T-093–T-099 (dark period)** — Governance debt resolution (LOW, non-blocking).
6. **EXP-017 Part B re-run** — When ≥66 resolved markets accumulated. GG-004 closes.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260601_1900.md then run mandatory session-start protocol"
```
