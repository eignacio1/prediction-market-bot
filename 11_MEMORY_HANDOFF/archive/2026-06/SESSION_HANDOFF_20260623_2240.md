# Session Handoff — 2026-06-23T22:40Z

**Trigger:** Operator-initiated session-end
**Last commit:** `f014738` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live on VPS; dark period (NBA off-season, MLB Phase 3 infrastructure complete)
- **Tests:** 1609/1609 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (dark period; PIPE-02/03 idle until October)
- **Paper bets:** 158/30 resolved (G6 gate met on count; P&L gate FAILING — true drawdown 24.9%)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

None — session was implementation-only (closure/deploy of T-184 from prior compacted session).

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-184 governance closure | ✅ TODO_NEXT.md updated (SESSION 79 block), MEMORY_BANK.md updated, PLAN.md updated |
| Commit `f014738` | ✅ 5 files: `scripts/run_exp017_mlb.py` (new), `tests/test_t184_exp017_mlb.py` (new, 99 tests), DECISION_LOG.md, TODO_NEXT.md, MEMORY_BANK.md |
| Git push | ✅ origin/main at `f014738` |
| VPS deploy | ✅ `git pull` + `source venv/bin/activate && pip install -e . -q` → DEPLOY_OK |

---

## ONE THING PENDING

**T-117 / GG-006 — operator action, deadline 2026-06-30 (7 days).**

Earl must formally read:
- (a) Kalshi Participant Agreement
- (b) KXMLBHIT Terms & Conditions (PAL/Position Limit)

Log findings in DECISION_LOG. This is a prerequisite for ADR-0005 (G6 formal authorization). Model cannot do this. Infrastructure is complete and waiting.

---

## Current Paper Portfolio

- Bankroll: **$751.10** (24.9% drawdown from initial $1,000 NBA book)
- Open: 0 positions ($0.00 deployed)
- Closed/Resolved: 158 | G6 gate: 158/30 (count met; P&L gate FAILING — EXP-017 still GG-004 OPEN)
- MLB book: `logs/paper_portfolio_mlb.json` — fresh $1,000, 0 positions (Phase 3 starts August 2026)

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

**Dark period:** NBA crons active but no games until October 2026. MLB crons NOT yet added (Phase 3 starts August 2026 — requires separate MLB PIPE-02/03 cron setup before season).

---

## MLB Phase 3 Infrastructure — Complete

All four MLB C1–C4 build tasks done:

| Task | Status | Commit area |
|------|--------|-------------|
| T-181 MLB C1 ingestion | ✅ COMPLETE | mlb_ingestion.py, mlb_team_stats_store.py, mlb_pitcher_stats_store.py |
| T-182 MLB C2 features | ✅ COMPLETE | mlb_features.py, MLB_FEATURE_VERSION 1.0.0 |
| T-183 MLB C3 model training | ✅ COMPLETE | train_mlb_model.py, HOLDOUT_CUTOFF 2026-01-01 |
| T-184 EXP-017 MLB commercial validation | ✅ COMPLETE | run_exp017_mlb.py (99 tests) |

EXP-017 MLB execution: `python3 scripts/run_exp017_mlb.py` — returns INCONCLUSIVE until ≥20 positions accumulate in `logs/paper_portfolio_mlb.json`. Expected first data: August 2026. ADR-0024 Tier 1 check at n=150 (mid-August).

---

## Priority Queue — What's Next

| Pri | Task | What | Due |
|-----|------|------|-----|
| **P0 — OPERATOR ACTION** | **T-117 / GG-006** | Read Kalshi Participant Agreement + KXMLBHIT T&C; log in DECISION_LOG | **2026-06-30** |
| **P1** | **T-186** | F-042 playoff TeamGameLog pull + v2b NBA retrain. `opp_playoff_def_rating_l5_mean` was NaN everywhere in v2-065b9510 (deferred at training). Pull playoff TeamGameLog for 8-10 teams, repopulate F-042, retrain v2b | Pre-Oct 2026 |
| **P1** | **T-073** | DS-04 injury source for T2 activation (KI-011 — injury blindness) | July 2026 |
| **P1** | **T-077** | Polymarket KYC completion (operator action) | — |
| **P0 Oct** | **T-185** | v2 model deploy + paper trading restart + kill switch reset (8-step runbook; DS witnesses Step 7; NBA book reset A/B/C decision) | Oct 2026 |

---

## Open Governance Gaps

| Gap | Status | Note |
|-----|--------|------|
| GG-004 | OPEN | EXP-017 not yet run on adequate sample (MLB paper trading not started) |
| GG-006 | OPEN | T-117 operator action, deadline 2026-06-30 |
| GG-020 | OPEN (LOW) | Kalshi fee 0.07 — conservative direction; T-151 receipt verify post-G6 |
| GG-027 | OPEN (LOW) | PAM full integration across T2/T3/T5 (low severity until T2 activation) |

---

## Key Constraints to Remember

1. No live capital until G6 (30 resolved paper bets + positive P&L — APR-0016). Count met (158); P&L gate FAILING.
2. EXP-017 MLB commercial validation (GG-004) is the binding G6 blocker — no script execution until August 2026.
3. v2 model (`v2-065b9510`) NOT yet deployed to VPS — `FEATURE_VERSION 1.4.0` artifact exists locally; deploy via T-185 runbook at NBA 26-27 season start.
4. MLB PIPE-02/03 crons not yet configured on VPS — required before August MLB paper trading starts.
5. `arb/` folder = REFERENCE ONLY until APR-0010.

---

## ⚙️ DECISION AUDIT

**Step 1 scan:** Clean — no `decisions_logged: false` documents found.

| Document | decisions_logged | DECISION_LOG entries | Status |
|----------|-----------------|----------------------|--------|
| `scripts/run_exp017_mlb.py` | N/A (script, not ADR/spec) | SESSION 79 entry written | ✅ |
| `tests/test_t184_exp017_mlb.py` | N/A | — | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260623_2240.md, confirm 1609 tests"
```
