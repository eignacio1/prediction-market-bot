# Session Handoff — 2026-06-02T19:00Z (estimated)

**Trigger:** Context window near limit — operator-initiated /session-end  
**Last commit:** `d8ec72d` (main) — pushed to GitHub + VPS pulled  
**Session:** SESSION 16

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (VPS confirmed)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running
- **Paper bets:** 7 open / 0 resolved — G6 gate (APR-0017): 0 resolved / 0 game nights complete

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Monte Carlo pre-game assessment established as MANDATORY protocol for all C3/C4 strategic changes | Operator mandate: any ADR, parameter change, or model update affecting C3/C4 must have before/after MC comparison before next PIPE-03. Quantifies P/L impact, bet count, kill switch risk, reserve mandate. | `03_DECISIONS/MONTE_CARLO_PROTOCOL.md` + DECISION_LOG Session 16 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| `scripts/run_monte_carlo.py` | ✅ Written + committed + VPS deployed. CLI-parameterized; mirrors PIPE-03 Path B + Kelly exactly; 10k sims; BOT STATISTICS section (bets placed/YES/NO, exp. wins/losses, MC averages, per-player breakdown, rejected with reasons); EV; P/L distribution; governance footer. `--kelly`, `--min-edge`, `--max-exposure`, `--label`, `--out` flags. |
| `03_DECISIONS/MONTE_CARLO_PROTOCOL.md` | ✅ Written + committed. 8 trigger conditions; standard + before/after + VPS run patterns; output interpretation table; expected effect table; 5 known limitations (GG-004, independence, sequential bankroll depletion, T1-only). |
| DECISION_LOG Session 16 entry | ✅ Written — protocol establishment, baseline stats, architecture findings. |
| Code hygiene | ✅ Unused `Dict` import removed from `run_monte_carlo.py`. All other patterns verified correct. |
| VPS deploy | ✅ 695/695 tests on VPS after pull. |

---

## ⚠️ CRITICAL FINDING: MC vs Actual Discrepancy (KI-025)

**MC prediction (from pregame_20260603.json at 21:30 UTC):** 23 bets / $796.29 deployed  
**Actual PIPE-03 execution (22:00 UTC):** 7 bets / $381.97 deployed  
**Current bankroll:** $618.03 / open positions: 7

**Implication:** 16 bets the MC showed as having edge above MIN_EDGE were NOT placed. The 30-minute gap between PIPE-02 pregame capture and PIPE-03 execution is the primary suspect — if Kalshi prices moved toward the model's estimate in that window, edge drops below MIN_EDGE=0.02.

**Why this matters:** 
1. The MC is calibrated to PIPE-02 snapshot prices. If prices systematically move toward the model in the 30-minute window, the MC over-estimates bet count. This is a known limitation not yet documented in MONTE_CARLO_PROTOCOL.md.
2. If the MC consistently over-predicts, the protocol's usefulness as a predictive tool is undermined.
3. Alternatively, if prices move AWAY from the model (market agrees with us), edge increases — more bets than predicted.

**Investigation for next session:**
```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 \
  "tail -300 /opt/prediction-market-bot/logs/paper_early_cron.log"
```
Look for: edge values at execution time vs. pregame snapshot; which markets had edge below MIN_EDGE at execution; idempotency skips.

**If hypothesis confirmed (price drift):** Add caveat to MONTE_CARLO_PROTOCOL.md § Known Limitations: "MC uses pregame snapshot prices from PIPE-02 (21:30 UTC). Kalshi prices may move before PIPE-03 execution (22:00 UTC). If markets systematically move toward the model estimate in this window, MC over-predicts bet count."

---

## Current Paper Portfolio (post-G1 T1 cron)

- Bankroll: $618.03 (7 open bets deployed; 0% realized drawdown)
- Open: 7 positions — G1 (Jun 3 2026, NYK vs SAS)
- Closed/Resolved: 0 | G6 gate: 0/66 resolved (APR-0017 floor); 0/5 game nights

---

## Next Steps (priority order)

### IMMEDIATE (before G1 game resolves, ~01:00-02:00 UTC Jun 4)
1. **Investigate KI-025** — check `paper_early_cron.log` for actual edge values at execution time vs. pregame snapshot; confirm which markets dropped below MIN_EDGE between 21:30 and 22:00 UTC.

### AFTER G1 RESOLVES (~01:00-02:00 UTC Jun 4)
2. **T-109 resolve procedure** — run locally (VPS 403 blocks nba_api):
   ```bash
   BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
   ```
3. **Run EXP-017 Part B** with resolved positions (accumulates toward GG-004 / APR-0017):
   ```bash
   PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py \
     --from-pregame logs/ --portfolio logs/paper_portfolio.json
   ```
4. **Run MC after G1 resolve** to see G2 pregame assessment baseline.

### HIGH PRIORITY (before G2, Jun 5)
5. **T-117** — Kalshi KXNBAPTS contract Terms review (GG-006 final close). Log into Kalshi → any active KXNBAPTS contract → Terms and Conditions tab → record PAL and Position Limit numbers. Must complete before G6 ADR-0005.
6. **T-127** — KXNBAPTS orderbook depth query during Finals window. Run `scripts/query_orderbook_depth.py`. KI-023 resolution. Window closes Jun 22.
7. **KI-025 add to MONTE_CARLO_PROTOCOL.md** if price-drift hypothesis confirmed — add as Known Limitation #6.

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check (⚠ two known false-negatives: Python 3.11 check vs 3.12 venv; Kalshi ping broken)
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py — 403 blocks nba_api on VPS; use T-109 locally)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints

1. **arb/ folder = REFERENCE ONLY** — APR-0010 required; no active integration
2. **No live capital until G6** (≥66 resolved bets + ≥5 game nights + EXP-017 Part B CONFIRMED — APR-0017)
3. **GG-004 OPEN** — EXP-017 Part B n=2 directional positive; floor is 66 unique markets
4. **T4/T5 paper-scope SKELETON** — do not fire live orders without Phase 8 ACTIVE gate (EXP-018/019)
5. **Work wifi blocks Kalshi API** — use mobile hotspot or any other network
6. **Monte Carlo MANDATORY** before next ADR affecting C3/C4 (MONTE_CARLO_PROTOCOL.md trigger table)
7. **G1 game is Jun 3 (8:30pm ET / 00:30 UTC Jun 4)** — resolve locally after game ends

---

## ⚙️ DECISION AUDIT

**Step 1 scan (documentation debt):** All 7 files flipped to `decisions_logged: true` in SESSION 15. No new files this session have `decisions_logged: false`.

| Document | Status |
|----------|--------|
| `scripts/run_monte_carlo.py` | N/A (code); DECISION_LOG Session 16 entry written ✅ |
| `03_DECISIONS/MONTE_CARLO_PROTOCOL.md` | N/A (protocol doc); DECISION_LOG Session 16 entry written ✅ |

---

## Monte Carlo Baseline (SESSION 16)

From pregame_20260603.json at $1,000 bankroll, T1_KELLY=0.10:
- **Markets evaluated:** (varies by pregame file)
- **MC prediction:** 23 bets / $796.29 deployed / EV +$136.89 / kill switch risk 0.13%
- **Actual PIPE-03 result:** 7 bets / $381.97 deployed
- **Discrepancy ratio:** 7/23 = 30% of predicted — flag for KI-025 investigation

For future ADR assessments, run baseline BEFORE applying changes:
```bash
PYTHONPATH=src python3 scripts/run_monte_carlo.py --label "before-ADR-XXXX" --out logs/mc_before.txt
```

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read MEMORY_BANK.md and SESSION_HANDOFF_20260602_1900.md.
# G1 game resolves tonight (~01:00 UTC Jun 4). First task: investigate KI-025
# (check paper_early_cron.log for actual edge at execution vs. MC prediction).
# Then run T-109 resolve procedure locally after game ends.
# 695/695 tests. Commit: d8ec72d."
```
