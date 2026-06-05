# Session Handoff — 2026-06-05T11:50Z

**Trigger:** Operator-initiated session end
**Last commit:** `d91b30b` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 734/734 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — all crons running; PIPE-06 activated this session
- **Paper bets:** 25 open (Finals G2, tips 00:30 UTC Jun 6) — G6 gate: 0 resolved

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **T3 momentum overlay design: `t3_signal_loader.py` extracted as standalone module, not inline in run_paper_trade.py** | BOT_ENV module-level guard in run_paper_trade.py would block test imports if T3 loader were inline. Standalone module allows `from prediction_market_bot.t3_signal_loader import load_t3_signals` in tests without triggering BOT_ENV guard. | `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` SESSION 34 row | DS |
| **T3 non-contamination: return {} on absent/stale/error → pure T1 path guaranteed** | Any fragility in T3 signal loading must fail safe — not contaminate T1 bets. Empty dict forces every `.get(ticker, "NEUTRAL")` to return NEUTRAL, leaving `edge = t1_edge` unchanged. This is the invariant: T3 is additive, never destructive. | DECISION_LOG SESSION 34 row | DS |
| **PIPE-06 cron activated despite "verify Polymarket connectivity" gate note** | Original comment said "Run AFTER verifying Polymarket connectivity (T-077)." T-077 is about Polymarket operator KYC — irrelevant to T3 signal generation, which only requires Kalshi via VenueRouter. Gate note was vestigial. Kalshi is primary venue; T3 cron is safe to run now. | VPS crontab + SESSION_HANDOFF | DS |
| **T4 MC deferred until GG-011 ADR written** | T4_BAND_WEIGHT=0.10 is an unvalidated STUB (GG-011 OPEN). run_monte_carlo.py is scoped to T1 band. A T4 MC result derived from a stub weight would be misleading. Correct path: pull G1/G2 T4 virtual logs → derive weight empirically → write ADR → flip PAPER_T4_VIRTUAL=false for G3. | GG-011 in GOVERNANCE_GAP_LOG.md | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T3 momentum overlay — `t3_signal_loader.py`** | ✅ New standalone loader. `load_t3_signals(log_dir, game_date)` → `{ticker: signal}`. Returns `{}` on absent/stale (>900s)/malformed. Staleness guard matches PIPE-06 `*/15` interval. |
| **T3 momentum overlay — `run_paper_trade.py` (6 edits)** | ✅ Import, constants (CONFIRM=1.15, FADE=0.75), load site (after TSS, before player loop), per-market overlay (between `edge = gross_edge - kalshi_fee` and `direction`), `t1_edge` preserved in forecast_rec, BET print tag `[T3:SIGNAL]`. |
| **T3 integration tests — `tests/test_t3_integration.py`** | ✅ 19 tests: fresh/stale/boundary/missing/malformed/empty/multi-file/no-run_at/wrong-date / non-contamination (2) / multiplier arithmetic (7). 715→734 tests. |
| **PIPE-06 cron activated on VPS** | ✅ Both `# */15 20-23` and `# */15 0-3` uncommented via `sed`. Confirmed active in `crontab -l`. |
| **G2 Monte Carlo with T3** | ✅ EV=+$36.90, P(profit)=95.2%, P50=+$39.52. Bankroll=$256.34. N=10,000, seed=42. |
| **T4 MC assessed** | ✅ Not feasible until GG-011 ADR written. T4_BAND_WEIGHT=0.10 is STUB. |
| **RESERVE_MANDATE_PCT confirmed** | ✅ VPS has 0.05 → floor=$50. No BATCH HALT at $256.34. |
| **G2 readiness confirmed** | ✅ All crons active. PIPE-06 first fires 20:00 UTC. PIPE-02 at 21:55 UTC. PIPE-03 at 22:00 UTC with T3 overlay. Everything on auto. |

---

## ONE THING PENDING

**PIPE-06 has never run on this VPS — verify after 20:00 UTC Jun 5.**

After 20:00 UTC, SSH and check:
```bash
tail -50 /opt/prediction-market-bot/logs/t3_cron.log
ls /opt/prediction-market-bot/logs/t3_20260605_*.json 2>/dev/null
```

If PIPE-06 ran but found no T1 report (PIPE-02 hasn't run yet at 21:55 UTC), that's expected — it will write an empty report and exit gracefully. The critical check is: does `t3_20260605_2200.json` (or similar near-22:00 timestamp) exist and contain forecasts? If PIPE-03 at 22:00 UTC sees that file with `run_at` within 900s, T3 signals will be applied.

After G2 resolves (~06:00 UTC Jun 6), run EXP-018 analysis with T3 isolation:
```bash
# On VPS: check portfolio for t3_signal field
grep -c '"t3_signal": "CONFIRM"' /opt/prediction-market-bot/logs/paper_portfolio.json
grep -c '"t3_signal": "FADE"' /opt/prediction-market-bot/logs/paper_portfolio.json
grep -c '"t3_signal": "NEUTRAL"' /opt/prediction-market-bot/logs/paper_portfolio.json
```

---

## Current Paper Portfolio

- Bankroll: $256.34 (74.4% drawdown from initial $1,000 — reflects paper losses + reserve depletion)
- Open: 25 positions (Finals G2, game_date=2026-06-05, tips 00:30 UTC Jun 6)
- Closed/Resolved: 0 this season | G6 gate: 0/66 resolved bets
- Last portfolio write: 2026-06-05T01:30:49Z (SESSION 33 late cron)

---

## Active Cron on VPS (157.230.91.33)

```
20:00 UTC  — PIPE-06 T3 scan (*/15 20-23) — NEWLY ACTIVATED SESSION 34
21:00 UTC  — Health check
21:55 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, T3 overlay active)
00:00 UTC  — PIPE-06 T3 scan (*/15 0-3) — midnight wrap for late games
01:25 UTC  — PIPE-02 late (run_pregame.py)
01:30 UTC  — PIPE-03 late (paper bets, T3 overlay active)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
20:30 UTC daily — GHA TSS cache build + SCP to VPS
```

---

## Key Constraints to Remember

1. RESERVE_MANDATE_PCT=0.05 on VPS — floor=$50, not $200. Confirmed this session.
2. T3 multipliers defined in BOTH run_paper_trade.py AND run_t3_pretip.py — if PIPE-06 constants change, PIPE-03 must update (coupling risk flagged in DECISION_LOG).
3. T4 PAPER_T4_VIRTUAL=true — no capital deployed. PAPER_T4_FLAT_SIZING=true. GG-011 must resolve before flip to PAPER_T4_VIRTUAL=false.
4. adj_λ FIRST LIVE on Finals G3 (Jun 8) — not G2. G2 bets used unadjusted Poisson.

---

## Resume Command for Next Session

```
Start with MEMORY_BANK.md. After G2 resolves (~06:00 UTC Jun 6):
1. SSH to VPS, check t3_cron.log and paper_portfolio.json for T3 signal distribution
2. Run EXP-018 analysis: compare T1-only (t3_signal=NEUTRAL) vs T3-enhanced bets
3. Check GG-014: what was the HTTP 429 rate for G2 paper bets?
4. Pull T4 virtual logs from VPS → begin GG-011 ADR derivation for T4_BAND_WEIGHT
5. Verify GHA cache pre-populates VPS before G3 PIPE-02 (20:30 UTC Jun 8)
```

---

## ⚙️ DECISION AUDIT

- DECISION_LOG.md: SESSION 34 row written (T3 integration architectural decisions)
- APPROVALS_REGISTER.md: No new APR entries required this session
- GOVERNANCE_GAP_LOG.md: No new GG entries; GG-011 still OPEN (T4_BAND_WEIGHT); GG-014 PARTIAL
- TODO_NEXT.md: SESSION 34 completed block added; open items registered
- MEMORY_BANK.md: Current State Snapshot updated (SESSION 34)
