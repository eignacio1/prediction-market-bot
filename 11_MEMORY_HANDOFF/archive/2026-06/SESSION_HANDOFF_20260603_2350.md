# Session Handoff — 2026-06-03T23:50Z

**Trigger:** Context window near limit (SESSION 22 compacted; SESSION 23 continuation)
**Last commit:** `00d0525` (main) — pushed to GitHub; VPS `git pull` confirmed

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; T4 nohup process started, **VERIFICATION REQUIRED** before Finals Game 1 tip (00:30 UTC Jun 4)
- **Paper bets:** 11 open (Finals Game 1) — G6 gate accumulating

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **Kelly in execution layer is wrong for T4 throughput validation** | Kelly scoped to `t4_band_budget=$60` at current bankroll caps T4 to ~60 actual bets before band exhaustion — not design throughput ~1,050. This is architecturally correct behavior for live sizing, but wrong for paper validation of execution layer throughput. Flat 1-contract sizing (at MIP) decouples bet COUNT from Kelly sizing. | DECISION_LOG.md SESSION 23 Notable Judgment Calls | DS/IO |
| **PAPER_T4_VIRTUAL=false default** | Virtual mode (no trader.open_position() call) was correct for architecture calibration but does not validate the execution layer. Actual paper positions must fire to validate throughput end-to-end. | `run_t4_live.py` line 252 | DS |
| **PAPER_T4_FLAT_SIZING=true default** | Flat 1-contract at MIP. When active: `approved_size = mip; approval = {**approval, "approved_size": approved_size}`. Both local variable AND approval dict updated. `trader.open_position()` uses the dict. | `run_t4_live.py` ~line 305 | DS |
| **PAPER_T4_POOL_USD=500.0** | ~1,050 × avg $0.50/contract = $525 ≈ $500 pool. When FLAT_SIZING=true, `t4_band_budget = PAPER_T4_POOL_USD` — bypasses ADR-0013 Kelly computation. ADR-0013 is NOT superseded; it governs when flat sizing is off. | `run_t4_live.py` main() | DS |
| **MIN_BET_T4_PAPER corrected $10.0 → $0.01** | $10 was a heuristic invented in SESSION 18, never sourced from Kalshi docs. Actual Kalshi minimum: 1 contract at market price = $0.01–$0.99. This affected both T4 and T1 paper floors. T1 floor at $1.0 is a paper-operational choice, not a Kalshi constraint. | `run_t4_live.py` line 251; `feedback_verify_external_claims.md` memory | DS |
| **GG-009 registered: taker fee not in MIN_EDGE** | Kalshi taker fee = 0.07×P×(1−P). At P=0.50: $0.0175/contract. MIN_EDGE=0.02. Fee = 87% of gross edge. All current EXP-017 EV estimates are overstated (fee not subtracted). Three resolution paths: raise MIN_EDGE, fee-adjusted gate, or maker-first policy. T-131 ADR required before G6. | `GOVERNANCE_GAP_LOG.md` GG-009 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Kalshi operational constraints research | ✅ Sourced from Kalshi docs: taker fee 0.07×P×(1−P), minimum $0.01/contract, 10k API/day rate limit, automated trading permitted |
| MIN_BET_T4_PAPER $10.0 → $0.01 | ✅ `run_t4_live.py` line 251 corrected |
| PAPER_T4_VIRTUAL default → false | ✅ `run_t4_live.py` line 252; actual bets now fire via `trader.open_position()` |
| PAPER_T4_FLAT_SIZING added | ✅ `run_t4_live.py` ~line 305; flat 1-contract at MIP; updates both `approved_size` local AND `approval` dict |
| PAPER_T4_POOL_USD=500.0 added | ✅ `run_t4_live.py` main(); band budget override when flat sizing active |
| MIN_BET_T1_PAPER added (SESSION 22) | ✅ `run_paper_trade.py` + `scripts/run_monte_carlo.py`; VPS `.env` updated |
| GG-009 registered | ✅ `GOVERNANCE_GAP_LOG.md` — taker fee absent from edge formula; T-131 ADR required |
| DECISION_LOG SESSION 23 entry | ✅ Notable Judgment Calls table updated with flat sizing architecture decision |
| VPS old screen killed | ✅ `149029.t4_live` (PAPER_T4_VIRTUAL=true old code) killed |
| VPS git pull + nohup start | ✅ `git pull` → commit `00d0525`; nohup process started — **verification status UNKNOWN (ENOSPC)** |
| TODO_NEXT.md updated | ✅ SESSION 22/23 completed + open items |
| MEMORY_BANK.md updated | ✅ Last reviewed, milestones, snapshot, Compass OS Health |
| PLAN.md updated | ✅ Last reviewed header |

---

## ONE THING PENDING (CRITICAL)

**Verify VPS T4 process is running the new code before Finals Game 1 tip at 00:30 UTC Jun 4 (8:30 PM EDT Jun 3).**

The nohup command was sent but output was lost to ENOSPC (Claude Code temp filesystem full). Result: UNKNOWN. The T4 process may or may not be running.

**Verify command:**
```bash
ssh root@157.230.91.33 'ps aux | grep run_t4 | grep -v grep && echo "---log---" && tail -10 /opt/prediction-market-bot/logs/t4_live.log'
```

**Expected output:** a running python process AND log lines containing `PAPER_T4_VIRTUAL=False, PAPER_T4_FLAT_SIZING=True, PAPER_T4_POOL_USD=500.0`.

**If NOT running:**
```bash
ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "source venv/bin/activate && BOT_ENV=paper BOT_C4_ACTIVE=true PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" & echo "PID: $!"'
```

---

## Current Paper Portfolio

- Bankroll: ~$459.47 (54% deployed in 11 open Finals Game 1 positions)
- Open: 4 filled Kalshi (KAT YES 20/15/10, Fox YES 10) | 3 canceled by Kalshi | 4 failed HTTP (Wembanyama/Castle)
- Closed/Resolved: 0 resolved this game yet — G6 gate: accumulating

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:55 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:25 UTC  — PIPE-02 second window (late games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
T4 live    — nohup (always-on poll loop, 45s cycles)
```

---

## Key Constraints to Remember

1. **VPS T4 must be verified running before Finals Game 1 tip.**
2. No live capital until G6 (≥66 resolved bets + ≥5 game nights + EXP-017 Part B CONFIRMED — APR-0017).
3. GG-009 is OPEN: all current EXP-017 EV figures are fee-overstated. T-131 ADR required before G6.
4. PAPER_T4_FLAT_SIZING=true is for paper throughput validation ONLY — not a production architecture decision.
5. ADR-0013 (Kelly budget scoping) is NOT superseded by flat sizing mode; it governs when flat sizing is off.

---

## ⚙️ DECISION AUDIT

**Step 1:** Governance scan — no `decisions_logged: false` documents were modified this session. Scan: CLEAN.

**Step 2:**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_t4_live.py` | N/A (code) | SESSION 23 entry written | ✅ |
| `GOVERNANCE_GAP_LOG.md` | N/A (governance register) | GG-009 entry written | ✅ |
| `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` | N/A (is the log) | SESSION 23 judgment calls entry | ✅ |

---

## TASK 2 (Not Yet Addressed — PENDING)

Decision tree rework per bucket (T-130): formally specify per-bucket decision tree mechanics — model inputs, probability estimate, Kelly variant, and sizing rule per T1–T5 band. Longer time horizon = more complex decision tree. T1: Kelly on full bankroll (validated). T4 paper: flat 1-contract. Future production T4: TBD by T-130 ADR. Required before T4 ACTIVE gate. This was the second task from SESSION 23 — tackle in next session after Finals Game 1 verification and post-game tasks.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260603_2350.md, then verify VPS T4 process is running before Finals Game 1 tip"
```

---

## NEXT SESSION PRIMER

First action: verify VPS T4 process (`ps aux | grep run_t4` on VPS) — unknown status due to ENOSPC blocking output verification. If not running, restart before 00:30 UTC Jun 4. After game: resolve positions, calibrate T4 throughput from `audit_t4.jsonl`. Then tackle T-130 decision tree rework per bucket.
