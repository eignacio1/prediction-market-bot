# Session Handoff — 2026-05-30

**Trigger:** Operator — prepare handoff to new terminal window  
**Prior handoff:** SESSION_HANDOFF_20260529_EOD.md  

---

## Status

- **Phase:** 6/7 ACTIVE (G0–G5 all closed)
- **Tests:** 550/550 passing (533 original + 17 paper_trader tests)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (dual-window + resolve)
- **Paper bets:** 0 resolved / 6 open (Fox YES ×3, SGA NO ×3 — SAS vs OKC 2026-05-30)
- **Bankroll:** $762.16 (initial $1,000) — $237.84 in open stakes
- **Drawdown:** 23.78% (all from open stakes, ZERO realized losses)
- **Experiments:** 16/16 complete — all 9 hypotheses resolved

---

## Strategic Decisions This Session

| Decision | Canonical Reference |
|----------|-------------------|
| No new strategic decisions — pure bug-fix session | N/A |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T3 CT scan — 3 consecutive clean scans | ✅ Scans 3, 4, 5 all clean (carried from prior session) |
| Bug C fix — `current_drawdown_pct` not passed to `evaluate_forecast()` | ✅ `run_paper_trade.py` — drawdown now computed and passed; kill switch guard functional |
| Bug D fix — stale bankroll for Kelly on bet N+1 | ✅ `run_paper_trade.py` — RiskEngine reconstructed from fresh `trader.get_state()` after each approved bet |
| Feature vector ordering fix — PIPE-03 | ✅ `run_paper_trade.py` — single-pass `[row[c] if c in row.index else np.nan for c in feature_names]` |
| Feature vector ordering fix — PIPE-02 | ✅ `run_pregame.py` — same fix; `feat_cols + missing` pattern removed |
| Bug F fix — PRF temporal guard bypass | ✅ `c2_feature_store/qualitative_store.py` — `_DS01_PRF_RAW` nullified before `compute_prf_onehot()` |
| VPS deployment | ✅ All 3 files synced to `/opt/prediction-market-bot/src/prediction_market_bot/`; VPS grep confirmed |
| Test suite | ✅ 550/550 passing after all fixes |
| Portfolio state read (VPS) | ✅ Revealed two newly discovered bugs (G and H — see below) |

---

## CRITICAL: Newly Discovered Bugs (Do Not Deploy Further Fixes Without ADR/DS Review)

### Bug G — Idempotency Check Failure (HIGH)

**Symptom:** Fox YES 15+ and SGA NO 30+ each appear as 3 OPEN positions in the portfolio (placed at 17:40, 22:00, and 01:30 UTC on the same ticker). The idempotency check:
```python
_open_tickers = {p["kalshi_ticker"] for p in trader.get_state().get("open_positions", [])}
if closest.ticker in _open_tickers:
    continue
```
should have caught this after the first run. It did not. Root cause unknown — possible cron working-directory mismatch causing `_load_or_init()` to return fresh state, or ticker representation mismatch between stored and Kalshi API response.

**Impact:** 3× intended exposure on Fox (stakes: $56.55 + $56.12 + $41.39 = $154.07) and SGA (stakes: $7.18 + $42.00 + $34.58 = $83.77). Total at-risk: $237.84 instead of ~$80 expected. This inflates apparent drawdown and will inflate realized P&L or loss.

**Tickers:**
- Fox: `KXNBAPTS-26MAY30SASOKC-SASDFOX4-15` (all 3 same)
- SGA: `KXNBAPTS-26MAY30SASOKC-OKCSGILGEOUSALEXANDER2-30` (all 3 same)

**Registered:** KI-014

---

### Bug H — Drawdown Includes Open Position Stakes (HIGH, OPERATIONAL BLOCKER)

**Symptom:** `current_drawdown_pct` is computed as:
```python
max(0.0, 1.0 - bankroll / _initial_bankroll)
```
Where `bankroll = trader.get_state()["bankroll_usd"]` which DECREASES when positions are opened (stakes deducted). With $237.84 in open stakes, apparent drawdown = 23.78% > 20% kill switch threshold.

**Impact:** PIPE-03 will KILL_SWITCH at 22:00 UTC tonight (before any resolution). Paper bet accumulation for G6 is halted until drawdown recovers below 20%.

**Self-resolving path:** PIPE-03R runs at 06:00 UTC tomorrow (2026-05-31). If positions resolve and returns stakes + any wins, bankroll restores and drawdown drops. If all 6 positions lose, bankroll stays at $762.16 and drawdown remains 23.78% — PIPE-03 continues to halt.

**Fix direction:** Compute drawdown from realized losses only:
```python
# Option A (preferred):
realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))
current_drawdown_pct = realized_loss / _initial_bankroll

# Option B:
open_stakes = sum(p["size_usd"] for p in _state.get("open_positions", []))
effective_bankroll = bankroll + open_stakes
current_drawdown_pct = max(0.0, 1.0 - effective_bankroll / _initial_bankroll)
```
This is a Class A change (kill switch behavior) — requires DS sign-off before fix.

**Registered:** KI-015

---

## OPERATIONAL STATUS: PIPE-03 Tonight (22:00 UTC)

| Cron job | Expected outcome |
|----------|-----------------|
| 22:00 UTC PIPE-03 (early) | KILL_SWITCH — drawdown 23.78% > 20%; exits immediately |
| 01:30 UTC PIPE-03 (late) | KILL_SWITCH — same |
| 06:00 UTC PIPE-03R (resolve) | Attempts resolution of 6 open positions for game 2026-05-30 |
| After PIPE-03R | If ≥1 position wins (returns stake): bankroll partially recovers |

**If all 6 positions resolve as losses:** bankroll stays at $762.16, drawdown stays 23.78%, PIPE-03 continues to kill-switch — operator must fix Bug H before paper betting resumes.

**If positions recover bankroll above $800:** drawdown drops below 20%, PIPE-03 can bet again.

---

## Next Session Priority Queue

| Priority | Task | Notes |
|----------|------|-------|
| 1 | Check PIPE-03R results (06:00 UTC 2026-05-31) | `ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "cat /opt/prediction-market-bot/logs/paper_portfolio.json"` |
| 2 | Fix Bug H — drawdown includes open stakes | Class A change; requires DS sign-off; fix is small (Option A above) |
| 3 | Fix Bug G — idempotency check failure | Investigate cron working dir; add logging to show path and loaded state at startup |
| 4 | T-070 — Accumulate paper bets | Blocked by Bug H kill switch until fix or positions resolve favorably |
| 5 | T-077 — Polymarket KYC (operator) | polymarket.com → KYC → API key → .env → RUNBOOK |
| 6 | T-091 — C7 paper P&L monitoring alert | After Bug H fix; WARNING at -$50; L2 at -$100 |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude:
# "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260530.md,
#  confirm 550 tests pass, then proceed."
```

---

## Key Constraints (Do Not Forget)

1. **FEATURE_VERSION = 1.2.0** — NOT 1.3.0; falsified by EXP-012
2. **G6 gate = 30 resolved paper bets + positive P&L** — NOT 50; APR-0016 signed 2026-05-29
3. **No live capital until G6** — ADR-0005 pending; paper only
4. **T-072 model refresh is REQUIRED before 2026-27 paper trading** — KI-013
5. **Work wifi blocks Kalshi API** — use any other network
6. **NBA dark period ~2026-06-22 to ~2026-10** — use for build, not rest
7. **Band framework: T1 is the only ACTIVE execution band** — T2/T3 are SKELETON; T4/T5 BLOCKED
8. **$270.76 bankroll in MEMORY.md belongs to the OLD Kalshi NBA Trading System project** — NOT this project
9. **Bug G: idempotency check failure** — 3× exposure on Fox/SGA for 2026-05-30 game
10. **Bug H: drawdown includes open stakes** — PIPE-03 kill-switch tonight; self-resolving after PIPE-03R IF positions recover

---

## Active Cron on VPS (157.230.91.33)

```
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets — will KILL_SWITCH tonight due to Bug H)
01:30 UTC  — PIPE-03 late (paper bets — will KILL_SWITCH tonight due to Bug H)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
```

---

## Bug Fix Summary (This Session)

| Bug | File | Nature | Status |
|-----|------|--------|--------|
| C | `run_paper_trade.py` | `current_drawdown_pct` not passed to `evaluate_forecast()` | ✅ FIXED |
| D | `run_paper_trade.py` | Stale bankroll for Kelly on bet N+1 | ✅ FIXED |
| Feature ordering | `run_paper_trade.py` | Missing features appended to END of array | ✅ FIXED |
| Feature ordering | `run_pregame.py` | Same pattern | ✅ FIXED |
| F | `c2_feature_store/qualitative_store.py` | PRF raw cols not nullified before `compute_prf_onehot()` | ✅ FIXED |
| G | `run_paper_trade.py` | Idempotency check failure (3× open positions per ticker) | 🔲 OPEN — KI-014 |
| H | `run_paper_trade.py` | Drawdown includes open stakes (not realized losses only) | 🔲 OPEN — KI-015 |
