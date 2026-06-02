# Session Handoff — 2026-06-02T17:20Z

**Trigger:** Context window near limit — operator-initiated /session-end  
**Last commit:** `1d10b7e` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 692/692 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; G1 fires ~22:00 UTC tonight (Jun 2)
- **Paper bets:** 0/66 resolved — G6 gate (APR-0017); clean slate begins Finals G1 Jun 3

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| ADR-0010 ACCEPTED: Band Kelly hierarchy revised to T3=0.07 < T1=0.10 < T2=0.13 < T4=0.20 < T5=0.25 | Variance-scaling principle: k_band = k_ref × (σ_λ_ref / σ_λ_band). T4/T5 Poisson CDF has better signal than T1 LR (threshold-specific vs player-level) — higher Kelly is correct. Old T1=0.25 > T4=0.05 was architecturally backwards. | `03_DECISIONS/ADR-0010_band-kelly-hierarchy-revision.md` | DS |
| ADR-0011 ACCEPTED: Phase 8 T4/T5 paper prototype activated at paper scope only | NBA Stats API CDN polling (45s), file kill switch, screen/tmux. NOT real-time stream. EXP-018/019 gates before ACTIVE (live capital). Production blockers explicitly deferred. | `03_DECISIONS/ADR-0011_phase8-paper-scope-t4t5-activation.md` | DS |
| T4_MIN_DELTA_P=0.08 retained for paper prototype (phase-dependent) | Noise floor is 0.069 at min 44+ (threshold appropriate) but 0.10–0.15 at min 40–42 (too lenient). Retained at 0.08 to generate EXP-018 calibration data. Calibration deferred to EXP-018 before ACTIVE. | `DECISION_LOG.md` Session 14 entry | DS |
| T5 thresholds (0.85 / 0.15) grounded — no change | Poisson arithmetic: λ_rem ≈ 1.25 at ≤3 min; P(≥1 pt)=0.714, P(≥3 pts)=0.131. Economic floor: p_min = market + MIN_EDGE + VIG_HALF = 0.845 at market=0.80; 0.85 clears it. Both thresholds GROUNDED. | `DECISION_LOG.md` Session 14 entry | DS |
| GG-008 RESOLVED — Path B (Poisson CDF per threshold) implemented | LR p_est was player-level (no kalshi_threshold feature), same value applied to all threshold markets → phantom edge at extremes. Fix: Poisson_CDF(threshold, pts_l10_mean) per threshold. LR p_est retained as p_estimate_lr for C6 audit log. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-008 row | DS |
| Portfolio reset to $1,000 — clean G6 evidence counter starts Finals G1 | G1 portfolio tainted by GG-008 phantom edge (25 positions, $88.47 remaining). Old Kalshi demo orders stranded but inert. Clean slate required before counting bets toward G6. | `reset_paper_portfolio.py` + DECISION_LOG | DS |
| RESERVE_MANDATE_PCT=0.40 added to risk.py | ≥40% bankroll must remain uncommitted after T1 batch so T4/T5 have capital at game time (ADR-0010). Warning-only at paper scale; blocking at live capital. | `c4_risk_engine/risk.py` | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| ADR-0010 — band Kelly hierarchy | ✅ Written + accepted; `execution_bands.py`, `game_state_model.py` updated; 3 test invariants updated |
| ADR-0011 — Phase 8 paper-scope ADR | ✅ Written + accepted; explicit paper-only scope; production blockers documented |
| T-129 Path B — Poisson CDF fix | ✅ `run_paper_trade.py`: `p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, pts_mean)` per threshold; LR p_est → p_estimate_lr for C6 |
| DS-02 adapter — `ds02_nba_live.py` | ✅ `NBALiveFeed`, `LivePlayerState`, `kill_switch_armed()`, `_parse_game_clock()`, `run_loop()`, CLI |
| run_t4_inplay.py — kill switch wired | ✅ `_kill_switch_armed()` stub replaced; imports `kill_switch_armed` from ds02_nba_live |
| `reset_paper_portfolio.py` | ✅ Built; `--confirm` flag required; prints current state before overwrite |
| RESERVE_MANDATE_PCT=0.40 | ✅ Added to `risk.py` before `_HARD_LIMITS` |
| GG-008 — governance log updated | ✅ Status: OPEN → RESOLVED 2026-06-02 SESSION 14 |
| VPS deploy | ✅ `git pull` on VPS; both commits (d8340ba + 1d10b7e) confirmed; 692/692 tests on VPS |
| Portfolio reset on VPS | ✅ `$1,000 / 0 positions` confirmed; G6 counter: 0/66 |
| DECISION_LOG + ADR Index | ✅ ADR-0010 + ADR-0011 indexed; Session 14 decision entries written |
| Tests | ✅ 692/692 (no regression) |

---

## ONE THING PENDING

**G1 paper cron fires at ~22:00 UTC tonight (Jun 2) — first run with corrected architecture.**

Infrastructure is ready. The corrected PIPE-03 cron will use:
- Poisson CDF per threshold (T-129 Path B, GG-008 fix)
- ADR-0010 Kelly fractions (T1=0.10)
- Fresh $1,000 portfolio

After G1, run `T-109 resolve procedure` locally (VPS 403 blocks nba_api):
```bash
# 1. Resolution (run after game ends, locally)
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py

# 2. Sync pregame files from VPS for EXP-017
PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio

# 3. Check G1 paper trade log on VPS
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "tail -100 /opt/prediction-market-bot/logs/paper_early_cron.log"
```

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (reset 2026-06-02; 0% drawdown; 0 open bets)
- Open: none
- Closed/Resolved: 0 | G6 gate: 0/66 resolved (APR-0017 floor); 0/5 game nights

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
2. No live capital until G6 (≥66 resolved bets + ≥5 game nights + EXP-017 CONFIRMED — APR-0017)
3. GG-004 still OPEN — EXP-017 commercial validation (n=2 markets, directional positive; floor is 66)
4. arb/ folder = REFERENCE ONLY until APR-0010 signed
5. T4/T5 are paper-scope SKELETON — do not attempt to fire live orders without Phase 8 ACTIVE gate (EXP-018 + EXP-019 + production ADRs)
6. Kill switch arm: `touch logs/t4_kill_switch.flag`; disarm: `rm logs/t4_kill_switch.flag`

---

## ⚙️ DECISION AUDIT

**Step 1 scan result:** 7 pre-existing files with `decisions_logged: false` (T-093 through T-099, all registered in previous sessions). No new files modified this session have `decisions_logged: false`.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `ADR-0010_band-kelly-hierarchy-revision.md` | N/A (ADR format) | ✅ Session 14 entries in DECISION_LOG | ✅ |
| `ADR-0011_phase8-paper-scope-t4t5-activation.md` | N/A (ADR format) | ✅ Session 14 entries in DECISION_LOG | ✅ |
| `GOVERNANCE_GAP_LOG.md` | N/A | ✅ GG-008 resolved row added | ✅ |
| `run_paper_trade.py` | N/A (code) | ✅ T-129 decision logged | ✅ |
| `ds02_nba_live.py` | N/A (code) | ✅ DS-02 paper scope logged in ADR-0011 | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260602_1720.md.
# G1 paper cron fired last night — check VPS logs: tail -100 /opt/prediction-market-bot/logs/paper_early_cron.log
# Then run T-109 resolve procedure locally. 692/692 tests."
```
