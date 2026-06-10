# Session Handoff — 2026-06-09T21:00Z

**Trigger:** Context window limit (session-end protocol)
**Last commit:** `fd1caea` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 817/817 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-07 23:00 UTC ACTIVE, PIPE-06 active, PIPE-02 21:55 UTC, PIPE-03 22:00 UTC)
- **Paper bets:** 82 T1 resolved (G6 T1 floor MET) | 1,115 T4 resolved (G6 T4 floor MET)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| APR-0019 ACCEPTED — per-bucket G6 evidence separation | APR-0017's unified 66-bet floor was derived for T1-only (pregame Poisson). T4 generates 1,115 bets/game via a structurally different live Bayesian model. Pooling T1+T4 toward a shared calibration floor conflates two distinct inference problems. GG-018 registered this as a governance gap. APR-0019 resolves it with derived per-bucket floors (T1 ≥66, T4 ≥50) and mandates independent Tier 2 evaluation per active bucket. | `00_ADMIN/APR-0019_g6-evidence-per-bucket-amendment.md` (ACCEPTED) | DS |
| GG-018 RESOLVED | APR-0019 acceptance closes GG-018 — the governance gap that blocked a G6 call due to ungoverned T4 evidence pooling. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | DS |
| Kalshi fee rate 0.07: conservative/verified for now | Independent investigation: marketmath.io + direct API query support 0.07. predictionhunt suggests 0.06 for sports (unconfirmed for NBA player props specifically). Kalshi fee schedule PDF returned HTTP 429. Cannot definitively confirm without actual trade receipts. Error direction if 0.07 is wrong = conservative (over-deducting = system slightly more conservative than necessary). T-151 open for post-G6 receipt verification. 0.07 retained in all production code. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-020 updated) | DS |
| EXIT_MECHANICS_ACTIVE=True DS override for G4/G5 | EXP-019B analytic validated 79.9% correct exits and 0 false exits. Empirical data (T-152) can ONLY be collected by running exits. T4 pool is isolated (no real capital risk). GG-017 Tier 2 gate remains OPEN pending T-152/T-153 completion. DS override allows data collection without claiming the gate is formally cleared. | `src/prediction_market_bot/execution_bands.py:EXIT_MECHANICS_ACTIVE` | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Commit uncommitted SESSION 43 work (run_t4_live.py gate + MC adj_λ + APR-0019 draft) | ✅ Commit `24bd442` — 817/817 tests |
| Push + VPS deploy `24bd442` | ✅ VPS HEAD updated |
| APR-0019 formal DS sign-off | ✅ Status line updated to ACCEPTED; sign-off block updated with date and role |
| APPROVALS_REGISTER.md — APR-0019 row added | ✅ Row inserted with full evidence summary |
| GG-018 RESOLVED in GOVERNANCE_GAP_LOG.md | ✅ Status block updated; added to Resolved Gaps table |
| Kalshi fee rate 0.07 independent verification | ✅ Web search + Kalshi API queries; findings logged to GG-020 |
| DECISION_LOG entries: APR-0019 acceptance + GG-020 fee investigation | ✅ Two new entries inserted |
| Commit + push governance artifacts | ✅ Commit `fd1caea` — all governance files updated |
| VPS deploy `fd1caea` | ✅ VPS deployed |
| TODO_NEXT.md updated (Last reviewed header) | ✅ SESSION 43 context |
| MEMORY_BANK.md updated | ✅ Header, milestone, Current State Snapshot all updated |
| PLAN.md updated | ✅ Last reviewed date |

---

## ONE THING PENDING

**G4 tonight (Jun 10) is the first data collection night for T-152 and T-153.**

- PIPE-07 cron at 23:00 UTC (Jun 10) will run with `EXIT_MECHANICS_ACTIVE=True` — exits will fire in paper mode for the first time.
- `logs/t4_position_trajectories.jsonl` will begin populating trajectory data (required for T-152 / EXP-019B empirical).
- `logs/spread_observations.jsonl` will begin populating bid/ask data (required for T-153 / EXP-019C).
- `post_game_g4_resolve.sh` cron runs at 06:00 UTC Jun 11: T1+T4 resolve, SCP portfolios + pregame + spread + trajectory JSONs to local, EXP-017 Part B rerun, EXP-018 rerun.

After G4 resolves, the next session should: (1) check post_game_g4_resolve.sh completed successfully, (2) check exit events in T4 portfolio, (3) note updated EXP-018 n-count (G4 adds ~50+ more T1 bets to Hypothesis C analysis).

**GG-004 remains the primary G6 blocker**: EXP-018 Hypothesis C was technically triggered at n=66. G4 data expands the sample. DS must decide whether the injury-filter view governs before calling G6.

---

## Current Paper Portfolio

- T1 Bankroll: $876.83 (12.3% drawdown from $1,000) | 0 open | 82 resolved
- T4 Pool: $1,539.42 | 0 open | 1,115 resolved (51.4% win rate, G3 P&L +$39.44)
- G6 T1 floor: ≥66 eligible bets — **MET** (82 resolved; some injury-excluded; eligible n=60 per EXP-018)
- G6 T4 floor: ≥50 eligible bets — **MET** (1,115 resolved)

---

## Active Cron on VPS (157.230.91.33)

```
21:25 UTC  — run_t140_check.py (TSS cache size check; rebuilds from ESPN if stale)
21:55 UTC  — PIPE-02 inference (run_pregame.py, adj_λ via TeamStatsStore)
22:00 UTC  — PIPE-03 early (paper bets, T1 + T3 overlay)
01:25 UTC  — PIPE-02 late
01:30 UTC  — PIPE-03 late
06:00 UTC  — PIPE-03R resolve-only
*/15 20-23 UTC  — PIPE-06 T3 signal scan
*/15 0-3 UTC    — PIPE-06 T3 signal scan (midnight wrap)
23:00 UTC  — PIPE-07 T4 live (run_t4_live.py, EXIT_MECHANICS_ACTIVE=True)
0 23 10 6 * — post_game_g4_resolve.sh (11 PM PDT Jun 10 = 06:00 UTC Jun 11)
GHA 20:30 UTC daily — TSS cache build + SCP to VPS
```

---

## Key Constraints to Remember

1. No live capital until G6 (APR-0017 amended by APR-0019): T1 Tier 2 + T4 Tier 2 must both pass independently; GG-004 (Hypothesis C) must be resolved; GG-017 (empirical exit mechanics) must be cleared.
2. GG-004 OPEN: EXP-018 Hypothesis C technically triggered at n=66. DS must decide whether injury-filter view governs before calling G6. Do NOT call G6 until DS decision logged.
3. T-151 OPEN: Kalshi fee rate 0.07 unverified against actual receipts. T-151 requires post-G6 live trade to verify. Cannot be closed in paper mode.
4. EXIT_MECHANICS_ACTIVE=True: This is a DS override for data collection (G4/G5). GG-017 Tier 2 gate is still OPEN. Do not represent exit mechanics as formally activated.

---

## ⚙️ DECISION AUDIT

Step 0 governance scan: **CLEAN** — no `decisions_logged: false` documents found in 02_ARCHITECTURE_DESIGN/, 08_MODEL_RISK_GOVERNANCE/, 01_SPEC/.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `00_ADMIN/APR-0019_g6-evidence-per-bucket-amendment.md` | N/A (new APR file, no `decisions_logged` field) | `[SESSION 43 / APR-0019]` written | ✅ |
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | N/A | `[SESSION 43 / GG-020]` written | ✅ |
| `00_ADMIN/APPROVALS_REGISTER.md` | N/A | APR-0019 row added | ✅ |
| `src/prediction_market_bot/execution_bands.py` | N/A | DS override rationale in inline comment | ✅ |
| T-154 (CHANGE_CONTROL.md decisions_logged: false) | false — carry-forward from SESSION 26 | Not modified this session — T-154 registered | ✅ deferred |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260609_2100.md"
# Then: Check post_game_g4_resolve.sh output — did all 10 steps complete?
# Then: Check T4 exit events in paper_portfolio_t4.json — did exits fire?
# Then: Run EXP-018 with G4 data and check if Hypothesis C picture changes
```
