# Session Handoff — 2026-06-02T09:10Z

**Trigger:** Context window near limit — operator-initiated session end
**Last commit:** `e0488bc` (main) — [GG-008] Register all-threshold loop model misspecification — pushed pre-session-end; additional DECISION_LOG + MEMORY_BANK + TODO updates committed at session close

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 692/692 passing locally (VPS at 692/692 — SESSION 12 push confirmed earlier)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; Finals G1 (NYK vs SAS) Jun 3 positions PLACED (25 OPEN, $911.53 deployed, $88.47 remaining)
- **Paper bets:** 0/66 resolved (G6 gate — APR-0017) — Finals G1 Jun 3 is first live game; G1 portfolio tainted (see GG-008 below; reset before G2)
- **Kalshi demo:** $1,000.36 — 25 resting orders (unfilled; collateral posts at fill)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **GG-008 registered** — all-threshold loop uses player-level p_est (no `kalshi_threshold` in 78-feature vector); same p_est applied to all Kalshi threshold prices → phantom edge on extreme thresholds | Monte Carlo 50k runs: expected P&L -$528 (-58%) on $911.53 Finals G1 portfolio; 6.4% win rate; only KAT YES 20 has genuine edge | `GOVERNANCE_GAP_LOG.md` GG-008; `DECISION_LOG.md` SESSION 13 | DS |
| **Path B approved** — replace `p_est` at each threshold with `Poisson_CDF(threshold, pts_l10_mean, direction)` in `run_paper_trade.py` all-threshold loop; implement before Finals G2 (Jun 5) | Architecturally correct for threshold-specific markets; no retrain required; T4 GameStateModel already uses this pattern correctly | `DECISION_LOG.md` SESSION 13; T-129 in TODO_NEXT.md | DS |
| **T4/T5 paper prototype activation approved** — target Finals G2 (Jun 5); DS-02 = NBA Stats API polling (~30-60s lag, NOT real-time); kill switch = in-memory file flag (NOT C7); Phase 8 ADR = paper scope only | Finals window is the only live T4/T5 evidence before October 2026; can't validate the in-game architecture without data from this window | `DECISION_LOG.md` SESSION 13 | DS |
| **Band Kelly hierarchy restructuring direction** — T1=0.10 (pre-game seeding), T4=0.20 (primary in-play Poisson), T5=0.25 (near-certain arithmetic); capital reserve mandate ≥40% bankroll before T1 fires | T1 LR model is player-level, not threshold-specific; T4 Poisson IS threshold-specific → T4 is the higher-quality signal; inverted hierarchy misallocates capital | `DECISION_LOG.md` SESSION 13; Band Kelly ADR PENDING | DS |
| **Paper portfolio reset to $1,000 before Finals G2** | G1 portfolio was placed on pre-Path-B system (phantom-edge architecture); tainted evidence; clean G6 evidence starts from the corrected system | `DECISION_LOG.md` SESSION 13 | DS |
| **Dark period reframe: NBA offseason → MLB/NFL C1/C2/C3 buildout** | Prior framing treated dark period as infrastructure cleanup; corrected: dark period is the multi-sport expansion window; NBA Finals is the evidence accumulation window (≥5 games remaining) | `DECISION_LOG.md` SESSION 13 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| GG-007 registered (T4/T5 skeleton thresholds uncalibrated) | ✅ `GOVERNANCE_GAP_LOG.md` GG-007; EXP-018/EXP-019/T-128 queued |
| KI-024 registered (stale pace_pts_per_min in T4/T5) | ✅ `KNOWN_ISSUES.md` KI-024; T-128 DS-02 ADR must require live pace |
| SESSION 13 docstring corrections (Bayesian→Poisson framing) | ✅ `game_state_model.py` + `run_t4_inplay.py` committed (873627f) |
| GG-008 registered (all-threshold loop model misspecification) | ✅ `GOVERNANCE_GAP_LOG.md` GG-008; T-129 queued (e0488bc) |
| 6 strategic decisions logged to DECISION_LOG.md | ✅ Path B, T4/T5 prototype activation, band Kelly direction, portfolio reset, dark period reframe |
| Monte Carlo analysis (50k runs, Poisson ground truth) | ✅ Expected P&L -$528 (-58%); root cause confirmed (no threshold in feature vector); assessment delivered to operator |
| Pre-Finals G1 portfolio assessment complete | ✅ Kalshi demo $1,000.36; paper $88.47 remaining; 0 new bets tomorrow (idempotency); T4/T5 $0 (SKELETON) |

---

## ONE THING PENDING

**T-129 (Path B Poisson CDF fix) + Band Kelly ADR + portfolio reset + T4/T5 prototype activation — ALL must complete before Finals G2 cron (Jun 5, ~22:00 UTC).**

Precise current state:
- Path B: code not yet written. Implement `poisson_cdf(threshold, mu)` helper in `run_paper_trade.py` (same stdlib math.exp pattern as `game_state_model.py:_poisson_cdf()`). Replace lines 295-296: `p_est = float(pipeline.predict_proba(X)[0, 1])` stays for shadow model reference; edge computation at each threshold should use Poisson CDF, not p_est.
- Band Kelly ADR: not yet written. Must be written and accepted (DS sign-off) before changing DEFAULT_KELLY_FRACTION or the band-specific Kelly fractions in `risk.py`.
- Portfolio reset: `logs/paper_portfolio.json` on VPS needs overwrite to clean `{"bankroll_usd": 1000.0, "initial_bankroll_usd": 1000.0, "open_positions": [], "closed_positions": [], "total_realized_pnl": 0.0}`.
- T4/T5 prototype: DS-02 NBA Stats adapter not yet built. Kill switch flag not yet wired. Phase 8 paper-scope ADR not yet written.

**Sequencing constraint:** Band Kelly ADR must be accepted BEFORE Path B is deployed (Path B changes which bets fire; Kelly determines how much; both must be consistent at deployment). ADR first, then Path B code.

---

## Current Paper Portfolio

- Bankroll: $88.47 (91.2% deployed — 25 OPEN positions from Jun 1 T1 cron)
- Open: 25 positions — all NYK vs SAS Finals G1 Jun 3; all `kalshi_order_status: "resting"` (limit orders, fills at game time)
- Closed/Resolved: 0 | G6 gate: 0/66
- **Reset decision:** Wipe to $1,000 before Finals G2 (Jun 5). G1 positions are architecturally tainted.

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

Finals G1 tip-off Jun 3 ~8:30pm ET = 00:30 UTC Jun 4. T1 cron already fired (Jun 1); idempotency suppresses re-entry. T2/T3/T4/T5 SKELETON — no execution.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. **GG-008 is OPEN HIGH** — Path B must deploy before Finals G2 cron (Jun 5 ~22:00 UTC)
3. **Band Kelly ADR must be signed before Path B deploys** — ADR first, then code
4. **T4/T5 activation = paper prototype, NOT production SLA** — DS-02 polling (~30-60s), in-memory kill switch, paper-scope ADR. Must be documented explicitly in the Phase 8 infra ADR.
5. **Paper portfolio reset to $1,000 before G2** — G1 bets are tainted; don't mix evidence
6. **Dark period = MLB/NFL buildout** — use Finals window for NBA G6 evidence; dark period is for new sport C1/C2/C3 modules

---

## ⚙️ DECISION AUDIT

**Step 1 result:** 7 pre-existing `decisions_logged: false` documents (T-093–T-099 registered — no new debt this session)

| Document | Decisions logged | DECISION_LOG entries written | Status |
|----------|-----------------|------------------------------|--------|
| `GOVERNANCE_GAP_LOG.md` | n/a (registries exempt) | GG-007, GG-008 registered | ✅ |
| `KNOWN_ISSUES.md` | n/a | KI-024 registered | ✅ |
| `DECISION_LOG.md` | n/a | 6 SESSION 13 entries added | ✅ |
| `TODO_NEXT.md` | n/a | T-128, T-129, EXP-018, EXP-019 added | ✅ |
| `game_state_model.py` | n/a | docstring corrections (no new decisions) | ✅ |
| `run_t4_inplay.py` | n/a | docstring corrections (no new decisions) | ✅ |

---

## Open Governance Gaps (SESSION 13 state)

| Gap | Severity | Status |
|-----|----------|--------|
| GG-004 | HIGH (G6 blocker) | OPEN — EXP-017 n=2, need ≥66 |
| GG-007 | LOW now / HIGH at Phase 8 | OPEN — EXP-018/EXP-019 required before T4/T5 production activation |
| GG-008 | HIGH | OPEN — Path B approved; implement before G2 |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260602_0910.md.
# Immediate task: write Band Kelly ADR (T1=0.10, T4=0.20, T5=0.25, 40% reserve), get DS sign-off,
# then implement T-129 Path B Poisson CDF fix in run_paper_trade.py, then build
# DS-02 NBA Stats polling adapter for T4/T5 paper prototype. All before Jun 5 22:00 UTC."
```
