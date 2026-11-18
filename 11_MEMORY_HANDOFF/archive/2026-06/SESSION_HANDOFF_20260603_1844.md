# Session Handoff — 2026-06-03T18:44Z

**Trigger:** Operator-initiated — session-end protocol
**Last commit:** `8321900` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing locally and on VPS
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; T4 PID 154947 active
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017; clean evidence window begins Finals Game 1 Jun 3 PDT)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Add 6 annotation fields to every paper position record: `model_p`, `gross_edge`, `fee_per_contract`, `fee_net_edge`, `fee_contaminated`, `probable_injury_signal` | GG-009 (taker fee absent from MIN_EDGE gate) + KI-011 (injury blindness) would require retroactive annotation at G6; self-annotating ledger prevents the join problem regardless of final bet count bucket | `DECISION_LOG.md` [SESSION 25 entry]; `paper_trader.py:open_position()` | DS |
| Enrich approval dict in calling scripts (not in C4 or paper_trader signatures) | C4's `evaluate_forecast()` return dict intentionally omits `model_p`/`edge` (C4 returns sizing/direction only); adding them to approval dict in `run_paper_trade.py` and `run_t4_live.py` before `open_position()` is backward-compatible and preserves the C4 interface contract | `run_paper_trade.py` (pre-`open_position()` enrichment); `run_t4_live.py` (after flat sizing block) | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| KI-027 registered in KNOWN_ISSUES.md | ✅ New OPEN MEDIUM entry: Kalshi HTTP 503/429 in second PIPE-03 window (01:30 UTC Jun 3); 4 positions with failed-HTTP status (Wembanyama NO 40/35/30, Castle NO 30) |
| SESSION 20 items closed in TODO_NEXT.md | ✅ "VPS deploy ADR-0013" + "T4 monitor Finals Game 1" both marked COMPLETE with SESSION 24 context |
| MEMORY_BANK.md portfolio section updated | ✅ Reflects $1,000 reset, 0 positions, T4 PID 153790→154947 |
| Fee annotation + injury signal code | ✅ 6 fields added to `paper_trader.py:open_position()`; `run_paper_trade.py` + `run_t4_live.py` enriched; 695/695 tests pass; commit `8321900` |
| T4 restarted on VPS | ✅ PID 153790 killed; PID 154947 started with annotated code; startup confirmed correct config |
| DECISION_LOG SESSION 25 entry | ✅ Full derivation rationale logged |
| TODO_NEXT.md SESSION 25 section | ✅ All completed items listed |
| MEMORY_BANK.md full update | ✅ Last reviewed, VPS HEAD, T4 PID, portfolio status, active risks all updated to SESSION 25 |
| PLAN.md Last reviewed update | ✅ Updated to SESSION 25 |
| SESSION_HANDOFF file created | ✅ This file |

---

## ONE THING PENDING

**T4 fired at 00:30 UTC Jun 4 (Finals Game 1 tip-off) — results unknown.** The annotated PID 154947 was live when the game started. First check of the session:

```bash
ssh root@157.230.91.33 'tail -100 /opt/prediction-market-bot/logs/t4_live.log'
```

Then run T1 + T4 resolution:
```bash
# Local:
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```

T4 calibration follows: `scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` — extracts actual T4 fires vs. ~1,050 design throughput and calibrates `T4_BAND_WEIGHT` + `T4_EXPECTED_TOTAL_EDGE` stubs before Finals Game 2.

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (reset before Finals Game 1; ~$827 deployed in T1 bets)
- Open: ~33 T1 bets (22:00 UTC Jun 3 PIPE-03 cron) + unknown T4 bets (00:30–03:30 UTC Jun 4)
- Resolved: 0 | G6 gate: 0/66
- All positions carry: `fee_contaminated`, `probable_injury_signal`, `fee_net_edge`, `model_p` fields

---

## Active Cron on VPS (157.230.91.33)

```
21:55 UTC  — PIPE-02 inference (run_pregame.py) [retimed from 21:30 — KI-025]
22:00 UTC  — PIPE-03 early (paper bets, T1)
01:25 UTC  — PIPE-02 late refresh
01:30 UTC  — PIPE-03 late (paper bets, T1)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
T4 live    — nohup PID 154947 (polls ESPN continuously; fires at STATUS_IN_PROGRESS)
```

T4 restart if dead:
```bash
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "set -a; source .env; set +a; source venv/bin/activate; PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" > /dev/null 2>&1 &'
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (APR-0017: ≥66 resolved bets + ≥5 game nights + EXP-017 Part B CONFIRMED; GG-004 OPEN)
3. GG-009 OPEN: all current EV figures are fee-overstated. T-131 ADR required before G6. Mitigation: `fee_contaminated` flag in every position.
4. T-131 ADR target: before Finals Game 2 (Jun 5 PDT) — not before G6
5. EXP-017 Part B re-run needed after T-131 fee correction (EV will be lower; currently n=2)

---

## ⚙️ DECISION AUDIT

**Governance scan:** No matches — `grep -rl "decisions logged.*false"` returned empty output. Clean.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `paper_trader.py` | n/a (code) | SESSION 25 entry added | ✅ |
| `run_paper_trade.py` | n/a (code) | SESSION 25 entry covers both | ✅ |
| `run_t4_live.py` | n/a (code) | SESSION 25 entry covers | ✅ |
| `KNOWN_ISSUES.md` | n/a (operational) | KI-027 registered | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_1844.md"
# First action: ssh root@157.230.91.33 'tail -100 /opt/prediction-market-bot/logs/t4_live.log'
# Then: run_resolve_local.py for Finals Game 1 T1 positions
# Then: scripts/run_t4_budget_sim.py --from-log logs/audit_t4.jsonl
# Before Finals Game 2 (Jun 5): write T-131 ADR (fee-adjusted MIN_EDGE)
```
