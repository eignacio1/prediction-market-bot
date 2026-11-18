# Session Handoff — 2026-07-11T23:36Z

**Trigger:** Operator-initiated (`/session-end`) — Window 2 "Convert tooling into a decision" (T-338/N-03, T-339/N-04, T-340/N-05) complete
**Last commit:** `c790618` (branch `session/20260711T225312Z-window2-n03-n05-cleann-gate`) — NOT YET pushed to GitHub/VPS (see One Thing Pending)

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** unchanged this session (no `src/` changes — governance/tooling docs only)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (not modified this session)
- **Paper bets:** MLB T1 clean_n=81, MLB T4M-PROJ clean_n=338 (raw counts higher — see logic_epoch); G6 30-bet floor still cleared on `clean_n` for both bands. Sample-*adequacy* status now tracked separately via `n*` (see below) — this does NOT change the G6 30-bet floor itself, only the separate ADR-0024/GG-004 commercial-validation adequacy question.

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Replace flat 30/150/500 sample-adequacy heuristic with per-band variance-derived `n*` (95% power, α=0.05, one-sided), computed live via `scripts/run_power_calc.py` (T-323) | ADR-0024's Tier 1/2 thresholds assume a single `σ_EV≈$0.25/bet` across all bands — measured live data shows T1's real stdev is $9.14/bet (n* = 2,322, ~15.5× the flat 150 floor) and T4M-PROJ's is $0.41/bet (n* = 787, ~1.6× the flat 500 floor). A uniform threshold is wrong in both directions simultaneously. | `00_ADMIN/APR-0024_g6-sample-adequacy-n-star-rebase.md` (drafted, PENDING DS sign-off); memo: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md` | DS (pending) |
| APR-0024 explicitly does NOT supersede ADR-0024 itself — prose-only amendment to CLAUDE.md/MEMORY_BANK gate language; whether to formally supersede ADR-0024's own Tier 1/2 thresholds is left as an open DS decision at sign-off | Hard Rule 3 (ADRs immutable, need superseding ADR); avoids pre-deciding a DS-level governance-hierarchy question in an APR draft | `APR-0024...md` § Scope, Review Checklist item 5 | DS (pending) |
| GG-004's existing n=151 DIRECTIONAL_POSITIVE Tier-1 verdict (2026-07-06) is NOT retracted by APR-0024 — it governs go-forward gate language only | Historical evidentiary finding under the prior heuristic should not be silently invalidated by a later methodology change | APR-0024 § "What Does NOT Change" | — |
| T-340/GG-105 Component A calendar gate checked and confirmed NOT YET MET; re-check target ~2026-07-19/20 (both bands' cadence spans <14 days as of 2026-07-11, so `n*` ETAs are flagged `cadence_immature` and provisional) | `run_power_calc.py`'s own `MATURE_CADENCE_SPAN_DAYS=14.0` threshold not yet crossed | `04_EXECUTION/TODO_NEXT.md` (T-340 entry), `MEMORY_BANK.md` Window 2 entry | — |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-338 (N-03) | ✅ Published live `clean_n` vs `n*` per band (T1: 81/2,322; T4M-PROJ: 338/787; T2/T3: insufficient data); wired into `.claude/hooks/governance_scan.sh` "SAMPLE ADEQUACY" block so every session sees it automatically. Memo: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md`. |
| T-339 (N-04) | ✅ Drafted APR-0024 (`00_ADMIN/APR-0024_g6-sample-adequacy-n-star-rebase.md`), status PENDING DS sign-off. Registered in `00_ADMIN/APPROVALS_REGISTER.md`. |
| T-340 (N-05) | ✅ Checked GG-105 Component A calendar gate — not yet met (cadence <14 days); logged with re-check ETA ~2026-07-19/20. |
| Nav-file session-end sync | ✅ `04_EXECUTION/TODO_NEXT.md`, `11_MEMORY_HANDOFF/MEMORY_BANK.md`, `04_EXECUTION/PLAN.md`, `00_ADMIN/APPROVALS_REGISTER.md` — all updated, committed as `c790618`. |

---

## ONE THING PENDING

**Push the session branch and open a PR.** Branch `session/20260711T225312Z-window2-n03-n05-cleann-gate` has 3 unpushed commits (`168a71e`, `bf5b1dd`, `c790618`) sitting only in the local worktree at `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260711T225312Z-window2-n03-n05-cleann-gate`. This has not been pushed yet this session — no push/PR command has been run. Next session (or the operator) should either push + open a PR for merge to `main`, or explicitly instruct otherwise. No VPS deploy is needed for this branch (governance/docs only, no `src/` changes).

---

## Current Paper Portfolio

- See governance hook output for live bankroll figures (MLB ACTIVE / NBA DARK) — not re-pulled fresh in this handoff since this session made no live-book/capital changes.
- MLB T1: clean_n=81 (raw_n higher, see `logic_epoch.py`) | MLB T4M-PROJ: clean_n=338 | Both clear G6's 30-bet floor.
- Sample-*adequacy* (separate from the 30-bet floor): T1 needs 2,322 (~15.8wk ETA at current cadence, provisional); T4M-PROJ needs 787 (~0.9wk ETA, provisional). Neither band currently meets `clean_n ≥ n*`.

---

## Active Cron on VPS (157.230.91.33)

Unchanged this session — not touched. See prior handoffs for the current schedule.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network.
2. No live capital until G6 (30 resolved paper bets + positive P&L — APR-0016).
3. **GG-110 is OPEN/uninvestigated, owned by a concurrent session this window — was NOT touched.** Do not pick it up without confirming that session's status first.
4. APR-0024 is PENDING — do not treat its proposed `n*` language as adopted gate criteria until DS signs off.

---

## ⚙️ DECISION AUDIT

**Step 1 result:** Not re-run this session (no `02_ARCHITECTURE_DESIGN/`, `08_MODEL_RISK_GOVERNANCE/`, or `01_SPEC/` files were touched — governance/tooling docs only, outside that scan's scope).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| APR-0024_g6-sample-adequacy-n-star-rebase.md | N/A (APR, not a `decisions_logged` doc) | Logged pre-excerpt in `DECISION_LOG.md` (T-339) | ✅ |

Sprint is not being closed here — this is a task-window close within an ongoing phase.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260711T225312Z-window2-n03-n05-cleann-gate"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260711_2336_WINDOW2.md.
# One thing pending: push branch session/20260711T225312Z-window2-n03-n05-cleann-gate and open a PR
# (3 unpushed commits: 168a71e, bf5b1dd, c790618). GG-110 remains out of scope — owned by a
# concurrent session."
```
