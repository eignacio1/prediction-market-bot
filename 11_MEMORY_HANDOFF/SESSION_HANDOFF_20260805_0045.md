# Session Handoff — 2026-08-05T00:45Z

**Trigger:** Operator-initiated (full task scope given at session start)
**Last commit:** `446468a` (branch `session/20260805T000103Z-t1-adjudication-stuck-positions`) — pending push + merge to `main`

---

## Status

- **Phase:** 6/7 ACTIVE (unchanged)
- **Tests:** not re-run this session (memos only, zero `src/` change — no reason to expect drift from the last-known 2799 passed / 8 known-failed / 29 skipped baseline)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; not modified this session (read-only SSH probes only, into `resolve_mlb_cron.log` and direct MLB Stats API test queries via the VPS's own venv)
- **Paper bets:** T1/MAIN unchanged this session — bankroll $683.91 / initial $1,000 / realized P&L -$121.85 / 22 open positions ($194.24 locked), all pre-existing state, no trades or capital action taken

---

## STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Adjudicated GG-153's Option (a): the pre-epoch-10 T1 cohort (n=202, epochs 5-8) IS recoverable but its own mean P&L/bet is negative (-$0.6289, 45.54% win rate) — no finite n* exists for a negative-mean sample | Direct computation against the live ledger, replicating `run_exp017b_decomp_mlb.py`'s `load_records()` filter exactly. Directionally consistent with GG-037's prior "no demonstrated T1 alpha" verdict — a second independent read, not a new finding | `GG153_T1_ADJUDICATION_MEMO.md`, GG-153, GG-037 | Earl (decision pending) |
| Computed GG-153 Option (b)'s stake at ~$1/bet if a `fixed_stake_usd` bypass is extended to T1 | 10% of T1's historical $9.99/bet mean stake, applying GG-135's own frontier finding (10%-of-current Kelly-equivalent sizing → 1yr P(kill)=1.2%) directly rather than picking a number | `GG153_T1_ADJUDICATION_MEMO.md`, GG-135 | Earl (decision pending) |
| Did NOT self-adjudicate GG-153 to a closed/resolved status | The memo's explicit purpose is operator decision input ("Earl decides in <10 min"), not an autonomous resolution — closing it myself would exceed the scope fence even though a documentation-only status edit was technically permitted | `GG153_T1_ADJUDICATION_MEMO.md` | Claude (deferred to Earl) |
| Corrected two causal claims in `OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md` § Task 1 regarding the 22 stuck T1/T2 positions | (1) `run_resolve_mlb.py`'s `pending` list is not `aged_open`-filtered — retries genuinely happen daily, not blocked by `mark_aged_open()`'s idempotency as the prior doc implied. (2) A cron-window-correlated MLB Stats API 406 failure pattern (~68% fetch failure rate, concentrated at 06:30 UTC) is a second, previously undocumented root-cause mechanism, evidenced directly: 3 of Julio Rodríguez's 4 stuck dates have valid data available right now via off-window query, yet never resolved in 5+ weeks of daily cron attempts | `T416_STUCK_POSITIONS_DIAGNOSIS.md`, GG-161 | DS/Ops |
| Registered GG-161 for the corrected causal finding | New, operationally significant finding distinct from the prior session's Task 1 entry — tracked separately so the correction is independently discoverable | `GOVERNANCE_GAP_LOG.md` GG-161 | Unstaffed |
| Recommended a genuine terminal state for positions that fail all three resolution sources past an age ceiling, instead of indefinite `aged_open` limbo | `aged_open` today never returns capital regardless of how permanent the underlying data gap is (~9 of 10 stuck players show genuine gameLog data absence, not a transient failure) | `T416_STUCK_POSITIONS_DIAGNOSIS.md` | Earl (design decision pending) |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Transcribe 3 missing SESSION_CLAIMS.md closure rows (T-413/T-414/T-415) | ✅ Done and committed before this turn (see prior commits on this branch) |
| GG-153 T1 adjudication decision memo — all 3 options answered with computation | ✅ `05_RESEARCH_EXPERIMENTS/GG153_T1_ADJUDICATION_MEMO.md` |
| T-416 stuck-positions root-cause diagnosis | ✅ `05_RESEARCH_EXPERIMENTS/T416_STUCK_POSITIONS_DIAGNOSIS.md` |
| Register GG-161 | ✅ `GOVERNANCE_GAP_LOG.md`, OPEN, unstaffed |
| Q2/Q3/Q6 adversarial review (Q1/Q4/Q5 already done pre-compaction) | ✅ Q2 stub scan re-run CLEAN; Q3/Q6 folded into this session's final report to the operator rather than a separate write-up (no new architecture-coherence concern found beyond what's already in GG-161) |
| DECISION_LOG.md entry | ✅ 2026-08-05 T-418 row |
| SESSION_CLAIMS.md closure row | ✅ This file's commit range |

---

## ONE THING PENDING

GG-153 itself remains OPEN — this session deliberately did not resolve it, since the memo's purpose is decision input for Earl, not an autonomous close. Earl's choice among (a)/(b)/(c) (or some combination) is the next action on T1. Separately, GG-161's recommended next step — re-attempting resolution for Julio Rodríguez's 3 recoverable stuck positions outside the 06:30 UTC cron window, and designing a terminal state for the genuinely-unresolvable remainder — is unstaffed; no T-NNN assigned yet.

---

## Current Paper Portfolio

T1/MAIN: bankroll $683.91, initial $1,000, realized P&L -$121.85, 22 open positions ($194.24 locked, all `aged_open: True`, `game_date` 2026-07-01→2026-07-29). Not modified this session — reported for reconciliation context only; see `MEMORY_BANK.md` Current State Snapshot for the authoritative live figure at the time it's next pulled.

---

## Active Cron on VPS (157.230.91.33)

Unchanged this session. `run_resolve_mlb.py` confirmed still running daily at `30 6 * * *` UTC via `/opt/prediction-market-bot/venv/bin/python` (requests==2.34.2) — read-only confirmation only, no crontab edit.

---

## Key Constraints to Remember

1. No live capital until G6 (30 resolved paper bets + positive P&L, DS sign-off)
2. GG-153's Option (a) computation is a materially worse finding than "13 days short of mature" — the recoverable cohort's mean P&L/bet is negative. Do not cite it as evidence of unresolved sample-adequacy; it is evidence of a negative read, pending Earl's adjudication of what that means for T1's status
3. GG-161's Mechanism 2 (cron-window API unreliability) may extend beyond these 22 legacy positions — worth checking whether normal-cadence resolution (of non-aged, current positions) is also silently affected by the same 06:30 UTC failure pattern; this was not checked this session and is a live open question, not yet a GG entry of its own
4. Scope fence honored throughout: zero `src/` change, no sizing/epoch/ADR change; no T1 modelling reopened (four candidate classes already exhausted per GG-037, not revisited)

---

## Report back to operator

**Branch:** `session/20260805T000103Z-t1-adjudication-stuck-positions`
**Commit range:** includes the SESSION_CLAIMS transcription commits from before this turn, through `bffece0` (memos + GG-161), `4748af4` (DECISION_LOG), `446468a` (SESSION_CLAIMS closure), plus this handoff file's commit.

**Is the pre-reset T1 cohort recoverable?** Yes — n=202 is physically intact and computable — but unfavorably: its mean P&L/bet is negative (-$0.6289/bet, 45.54% win rate), so no finite n* exists and recoverable does not mean usable for a positive adjudication.

**Root cause of the 22 stuck positions — one cause or many?** Two distinct, overlapping mechanisms, not 22 independent causes and not one uniform cause: genuine gameLog data absence for ~9 of 10 players' specific stuck dates (permanent, not fixable by retrying), plus a newly-identified cron-window-correlated MLB Stats API 406 failure pattern that plausibly explains why Julio Rodríguez's 3 currently-recoverable dates have never resolved despite 5+ weeks of daily attempts.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260805_0045.md, then read
# 05_RESEARCH_EXPERIMENTS/GG153_T1_ADJUDICATION_MEMO.md for Earl's pending T1 decision"
```
