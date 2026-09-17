# Active queue — the only prompt file to read

**Verified against:** `origin/main = 89c7d1f` (2026-09-17, Cowork strategic window) — *may be stale; the window cannot `git fetch`. Run `git fetch origin` first. A LANDED call is safe from a stale ref; a "not landed" call is not.*
**Live state, derived by import not grep (2026-09-17):** 92 cells · **22 execution bands** · **1 cell ACTIVE** · 88 NOT_IMPLEMENTED · 2 BLOCKED · 1 DARK · 131 gap-log entries, **91 OPEN**, next free **GG-288**.
**42 NFL T1 paper positions are open** — the first in this project's history. None settleable until 2026-09-20.
**This file on `origin/main` is three waves stale** (its header still reads `a1c5ed9`, 2026-09-11). Waves 25-27 ran from blocks the operator pasted, not from the committed file. 28.2 fixes that.
**IDs:** do not pre-assign. Claim at run time (GG-236); verify uniqueness across `git log --all` (GG-256).

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Hard ceiling, operator directive 2026-09-15.
- **A block in the wave fires immediately, concurrently with every other block.** A sequencing note is not a fence. Work that must wait goes in "Queued next."
- **Deliverable 0 in every block: land any un-landed predecessor.**
- **Check the sequencing of your own deliverables against venue mechanics before starting (GG-287).** Wave 27 asked one session to open a position and settle it in the same pass. That is structurally impossible here — Kalshi only quotes live markets for unplayed games, so a freshly opened position is always for a future game. The session was right to refuse rather than manufacture one.
- **A premise written in a block is a claim to verify, not a fact.** Three waves running, a briefing asserted something it had not derived.
- **Push after each deliverable, not at close-out.**
- Verify a code fix by importing and calling the real function. **Benchmark the real thing, not the unit test.**
- **A merge is not a deployment, and a deployment is not an activation** (GG-279).
- Register-and-stop on any gap outside scope (Hard Rule 11).
- If a permission control refuses you, report the exact command and refusal text, then hand back.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–25 | ✅ CLOSED | see history |
| **26** | ✅ CLOSED | Capture coverage closed (GG-276/GG-280) · EXP-027 UNDERPOWERED · **Floor A found and fixed** (GG-282). |
| **27** | ✅ **CLOSED, 2 OF 3 LANDED** | **42 NFL T1 positions opened — first ever** (T-556) · **the n\* wall quantified, APR-0035 drafted** (T-554/GG-285) · **GG-203 narrowed to exchange sharding** (T-556 addendum) · GG-283/284 complete but unlanded (T-555). |
| **28** | ⬜ **ACTIVE** | Fix the 33-day order blockade · land the strays and install the close-out fix · rehearse the first settlement |

### ✅ WAVE 27 — what actually happened

**Floor A was the whole story for those 24 refusals, and the pipeline works.** T-556 re-ran the identical open-attempt against 1,175 live markets with the real EXP-027 model: `min_bet_floor` went **24 → 0**, and **42 positions opened**. Refusal breakdown now 1,121 `no_model_prediction` (moneyline-only scope), 40 `no_live_quotes`, 10 `no_edge`, 4 `insufficient_edge`. Every row carried the real EXP-027 provenance string, never the stub. `kalshi_order_id: null`, `kalshi_order_status: "local_only"` — nothing touched the venue.

**GG-274 still could not close, and the reason is my fault, not the session's.** All 42 positions are for unplayed games (18 on 09-20, 2 on 09-21, 2 on 09-24, 18 on 09-27, 2 on 09-28). Kalshi only quotes live markets for games that have not finished, so a fresh open-attempt can only ever produce future positions. The block asked for open-and-settle in one session; that is structurally impossible. Registered as **GG-287**. The session refused to manufacture a settleable position, which was the correct call.

**The n\* wall has numbers now (GG-285, APR-0035).** T4M-PROJ: `clean_n=765`, mean $0.05193/bet, sd $1.4628 (ratio 28.2x), `n*=8,587`, ~198 clean bets/week ⇒ **~43 weeks, 1.6–1.7 MLB seasons**. NFL moneyline: `clean_n=14`, `n*=2,610` ⇒ **~197 weeks of game-time, ~11 NFL seasons, ~11 calendar years**. T1/T2/T3 have `clean_n<2` — no variance estimate exists at all, which is worse than a distant wall. APR-0035 is on the operator's desk.

**GG-203 is no longer a mystery — it is a sharding problem.** See 28.1.

---

### ⬜ WAVE 28 — fire all three together, disjoint surfaces

| # | Block | Tier | Why |
|---|---|---|---|
| 28.1 | **GG-203 — exchange sharding** | STANDARD | 33 days of zero accrual, now with a named mechanism and an outside developer's matching fix. |
| 28.2 | **Land the strays, install the close-out fix** | STANDARD | T-555 is stray, the session-end fix never landed, and this queue file on main is three waves old. |
| 28.3 | **Rehearse the settlement, do not settle** | STANDARD | 42 real positions settle from 09-20 through a resolver that has never run once. |

**Surfaces:** 28.1 owns `kalshi_client.py` and the Kalshi demo account. 28.2 owns the merges, `.claude/commands/`, `scripts/` and `ACTIVE_QUEUE.md`. 28.3 owns a COPY of the NFL portfolio and read-only reads of the resolver.

---

# 28.1 — GG-203 · EXCHANGE SHARDING · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg203-exchange-sharding"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

*** THIS OVERRIDES THE STANDING "DO NOT RE-INVESTIGATE GG-203 IN-REPO" RULE, NARROWLY, AGAIN. ***
T-492's ruled-out list stays closed and is NOT to be re-run. T-556's addendum already ruled out the
base URL (exact match) and the request schema (all six required fields sent; no event_ticker field
exists; 404 is not even a documented response for this endpoint). This block acts on what T-556's
addendum pointed AT, with external corroboration it did not have.

THE MECHANISM, from Kalshi's own docs (https://docs.kalshi.com/getting_started/exchange_sharding):
  - Kalshi split trading across multiple matching engines. Shard 0 is default; shard 3 is Sports.
  - `exchange_index` names a market's shard and is "the authoritative source of truth" for routing.
    KXMLBHIT returns `exchange_index: 3` on BOTH demo and production (T-556, 2026-09-17T05:13:20Z).
  - **Balances are PER-SHARD.** A user must have collateral allocated to a specific shard before
    placing orders there, moved via the Intra Account Transfer API and verified with Get Balance.
  - `grep -c exchange_index src/prediction_market_bot/c5_execution/kalshi_client.py` returns **0**.
    The bot has never sent or read this field.
  - An independent developer hit the identical symptom and fixed it exactly this way:
    https://github.com/BradSherwood24/degeneracy_v3/pull/9 -- orders rejected `market_not_found`
    because they omitted `exchange_index` and defaulted to shard 0; fix was explicit propagation.
  This explains the whole rotating error set -- `market_not_found` (absent on shard 0),
  `user_not_found`/"Exchange user not found", `insufficient_shard_balance` (no collateral on shard
  3) are three faces of one problem -- and why a fresh API key changed nothing.

DELIVERABLE 1 -- PROVE OR KILL THE HYPOTHESIS WITH ONE DIAGNOSTIC ORDER. Do not change the bot yet.
  In an isolated throwaway script on the VPS, against DEMO only, submit one order for a currently
  open KXMLBHIT market TWICE: once exactly as the bot sends it today, and once identical except
  with `exchange_index` set to that market's own value from its market-data record.
  Paste both full request bodies and both full responses.
  **If the second succeeds, GG-203's 33-day cause is established.** If both fail, paste the codes
  and go to Deliverable 2 -- do not start guessing at other fields.

DELIVERABLE 2 -- READ THE PER-SHARD BALANCE BEFORE CONCLUDING ANYTHING.
  Call Get Balance and report the allocation across shards, not just the aggregate. T-492's
  `balance_dollars: 399.4321` may be shard 0 only.
  If shard 3 shows zero, that is the second half of the cause and no client-side field fixes it --
  the account needs collateral moved to shard 3 via the Intra Account Transfer API. Report what the
  API requires. **Do not move funds yourself**; that is an operator action on his account. Mock
  demo funds are not real money, but it is still his account and his decision.

DELIVERABLE 3 -- IMPLEMENT PROPAGATION ONLY IF DELIVERABLE 1 PROVED IT.
  Read the market's own `exchange_index` from market data and pass it through to `submit_order()`.
  Follow the outside fix's shape: capture it per ticker at discovery, carry it on the order, and
  **refuse to dispatch an order whose exchange_index is unknown** rather than silently defaulting
  to 0 -- a silent default is what caused this.
  Tests: an order carries the market's exchange_index; an unknown exchange_index refuses rather
  than defaults. Do not touch sizing, kelly_fraction, or any _HARD_LIMITS value.

DELIVERABLE 4 -- FIX THE AUTHENTICATION ASYMMETRY T-556 FOUND, OR REGISTER IT.
  Market discovery (`fetch_player_points_markets`, the three `_get(f"/markets/{ticker}")` sites)
  defaults `authenticated=False` and therefore resolves to PRODUCTION regardless of `BOT_ENV`,
  while order writes go to demo. Production market data feeding demo order writes is wrong on its
  face and could hand the order path a production `exchange_index`.
  If fixing it is one clear change inside this block's fence, make it with a test. If it is larger,
  register a gap and stop -- do not let it expand this session.

DO NOT: submit any order against PRODUCTION or with real funds, at any point, for any reason.
DO NOT: move funds between shards or subaccounts. Report what is required; the operator acts.
DO NOT: rotate the API key again. T-547 already did; it changed nothing.
DO NOT: re-run anything on T-492's ruled-out list, or re-check the base URL or the request schema.
DO NOT: touch kelly_fraction/sizing, promote a cell, or settle a position.
DO NOT: touch the NFL portfolio or the resolver -- 28.3 owns those.
DO NOT: touch .claude/commands/, scripts/close_session_claim.sh or ACTIVE_QUEUE.md -- 28.2 owns those.

SCOPE FENCE: kalshi_client.py, an isolated diagnostic script, tests, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: both diagnostic request bodies and both full responses; the per-shard balance
breakdown; what the Intra Account Transfer API needs if shard 3 is unfunded; the propagation change
and its two tests if you made it; GG-203's disposition -- RESOLVED only if a real order succeeded.
```

---

# 28.2 — LAND THE STRAYS · INSTALL THE CLOSE-OUT FIX · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "land-strays-install-closeout-fix"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

DELIVERABLE 1 -- LAND T-555 (Wave 27's stray).
  origin/session/20260917T001723Z-gg283-gg284-nfl-cohort-defects  (tip 865e74c, 9 commits)
  GG-283 (WAS/WSH team-code alphabet) and GG-284 (CLE_JAX zero rows). Complete, pushed, unmerged.
  Confirm with `git merge-base --is-ancestor 865e74c origin/main` AFTER merging, and paste both
  gap statuses as they then read on main.

DELIVERABLE 2 -- INSTALL THE CLOSE-OUT FIX. IT NEVER LANDED.
  Two commits sit on the operator's LOCAL main tree, unpushed:
    44b7fb5  Wave 27 queue          580e9c9  session-end closure-row + stray-sweep fix
  PR #138 squash-merged WITHOUT them -- `git ls-tree origin/main scripts/` shows neither
  `close_session_claim.sh` nor `sweep_stray_branches.sh`, and session-end.md on main has no Step 9.
  Cherry-pick BOTH onto your branch (do NOT cd into the shared main tree -- GG-101):
    git fetch origin && git cherry-pick 44b7fb5 580e9c9 && git push
  If either conflicts, STOP and report. Then confirm on main after merge:
    git ls-tree origin/main scripts/ | grep -E "close_session|sweep_stray"
    git show origin/main:.claude/commands/session-end.md | grep -c "Step 9 -- Stray-branch sweep"

DELIVERABLE 3 -- THE FIX HAS ALREADY HALF-FAILED ONCE. DIAGNOSE THAT BEFORE TRUSTING IT.
  A T-554 session ran `close_session_claim.sh` and its commit is sitting UNPUSHED on local main:
    1431cdd  Session close: T-554 -- MERGED: NO
  The script committed the row and could not push it. That is the script's documented failure path
  and it reported honestly -- but the row still did not reach origin/main, which is the entire
  point of the script.
  Establish why: local main was ~66 commits behind, so the rebase-retry loop had to reconcile a
  large divergence. Determine whether the loop failed, timed out, or was never completed.
  **Fix the script so a far-behind local main cannot silently swallow the row** -- e.g. push the
  row from a detached ref rather than from whatever `HEAD` happens to be, or fetch-and-rebase
  before the first push attempt rather than only after a rejection.
  Then exercise it yourself at close-out and verify the row on origin/main.

DELIVERABLE 4 -- RECONCILE ACTIVE_QUEUE.md.
  The copy on main is three waves stale (header reads `a1c5ed9`, 2026-09-11). Deliverable 2's
  cherry-pick brings Wave 27's; the operator will supply Wave 28's. Confirm what is on main after
  your merge and say plainly which wave it reflects. Do not hand-author queue content yourself.

DO NOT: merge any branch older than 2026-09-15 without asking. The sweep will list ~10 older
  strays; they are the operator's routing decision, not yours (Hard Rule 11).
DO NOT: touch kalshi_client.py or the Kalshi account -- 28.1 owns those.
DO NOT: touch the NFL portfolio or the resolver -- 28.3 owns those.
DO NOT: touch kelly_fraction/sizing, promote a cell, submit an order, or settle a position.
DO NOT: restart any service.

SCOPE FENCE: the merges, .claude/commands/session-end.md, scripts/close_session_claim.sh,
scripts/sweep_stray_branches.sh, ACTIVE_QUEUE.md, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the ancestor check for 865e74c and both gap statuses; the ls-tree and Step 9 greps
proving the fix is on main; your diagnosis of the T-554 push failure and what you changed; your own
closure row verified visible on origin/main; which wave ACTIVE_QUEUE.md now reflects.
```

---

# 28.3 — REHEARSE THE FIRST SETTLEMENT · DO NOT SETTLE · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "rehearse-first-settlement"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

42 real NFL T1 paper positions are open (T-556). Their games run 2026-09-20 through 09-28. Today
is before the earliest, so **nothing is settleable and you must not settle anything.** The
settlement path -- `settle_position()`, the idempotency guard, the not-yet-final guard,
`check_settlement_ambiguity()`/GG-257 -- has never executed against a real position in this
project's history. The first time it does, it will write to a ledger that feeds G6 evidence.
This block makes that first run boring. It is a rehearsal, against a COPY, start to finish.

DELIVERABLE 1 -- INVENTORY WHAT IS ACTUALLY OPEN, FROM THE REAL FILE, READ-ONLY.
  Per position: ticker, market type, threshold, direction, size, entry price, game_date,
  model_identity. Confirm all 42 carry the real EXP-027 provenance string and none the stub.
  Confirm `kalshi_order_id: null` / `kalshi_order_status: "local_only"` on every one.
  Report the game_date histogram. If it disagrees with T-556's (18/2/2/18/2 across 09-20, 09-21,
  09-24, 09-27, 09-28), say so -- something changed and that matters more than this block.

DELIVERABLE 2 -- PROVE THE NOT-YET-FINAL GUARD FIRES. THIS IS THE ONE THAT PROTECTS YOU.
  Copy the portfolio. Run the resolver against the COPY, today, with games unplayed.
  It must REFUSE every position. Paste the refusal output.
  A resolver that settles an unplayed game would corrupt the ledger silently -- verify the guard
  by running it, not by reading it. If it does NOT refuse, stop everything and report: that is a
  live defect and the most important finding available this wave.

DELIVERABLE 3 -- REHEARSE A REAL SETTLEMENT ON SYNTHETIC FINALS, STILL AGAINST THE COPY.
  Construct plausible final scores for the 09-20 games (clearly labelled synthetic, never written
  anywhere near the live ledger). Run the resolver against the copy.
  Per position: derived actual_stat, threshold, YES/NO outcome, P&L -- hand-verify the arithmetic.
  Moneyline is final margin vs threshold 0. Include one deliberate tie: `check_settlement_ambiguity()`
  must REFUSE, not guess (GG-257).
  Then run it a second time and prove the copy is byte-identical -- idempotency, verified not assumed.

DELIVERABLE 4 -- WRITE THE RUNBOOK FOR THE REAL SESSION.
  A short ordered checklist the 09-21 session follows: fetch finals on the VPS (GG-266 -- the Mac
  cannot TLS to ESPN), cross-check against a second source, back up and verify the backup, dry-run
  against a copy, hand-verify, settle live under the lock, re-run for idempotency, report P&L.
  Name every failure mode you hit in rehearsal and how you got past it. The point is that the real
  session discovers nothing new.

DO NOT: settle, modify, or write to the live portfolio file. Everything happens on a copy.
DO NOT: modify settle_position() or apply_resolved_nfl_game_markets.py unless a PROVEN defect
  blocks the rehearsal -- and if one does, that is a finding to report, not a fix to rush.
DO NOT: fabricate a final score anywhere outside the clearly-labelled rehearsal copy.
DO NOT: open, close or adjust any position. DO NOT: touch any MLB ledger or the T4 writer.
DO NOT: touch kalshi_client.py or the Kalshi account -- 28.1 owns those.
DO NOT: touch .claude/commands/ or scripts/close_session_claim.sh -- 28.2 owns those.
DO NOT: touch kelly_fraction/sizing or promote a cell.

SCOPE FENCE: a copy of the NFL portfolio, read-only reads of the resolver, a runbook document
under 04_EXECUTION/, tests only if a proven defect needs one, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the 42-position inventory and game_date histogram; the not-yet-final refusal output;
the full rehearsal table with hand-verified arithmetic including the tie case; the idempotency
proof; and the runbook.
```

---

## Queued next — not yet fired

**Wave 29 — settle for real.** Fires after 2026-09-20 concludes. Follows 28.3's runbook against the
real 42-position ledger. Closes GG-274 and, with it, GG-287. This is the first end-to-end close in
the project's history — treat it as the milestone it is, and do not let a win or loss on 18 games be
read as evidence of edge.

**MLB T1 game markets have never been run live.** Floor A was fixed in `run_t1_mlb_game_market.py`
too, and that path uses `kalshi_client=None`, so GG-203 does not block it. Worth a block once the
model question is settled — its default is `StubMLBGameMarketForecastModel`, and opening positions
from a stub is worth nothing. Establish whether EXP-026/HYP-011's MLB moneyline work produced a real
forecaster before scheduling it.

**GG-279 — deploy-vs-activation still has no structural check.** Compare each long-running service's
`ActiveEnterTimestamp` against its source's most recent relevant commit. One SHORT block.

---

## Needs your decision

| Item | Plain English | What happens if it waits |
|---|---|---|
| **APR-0035** | New, from Wave 27. The P&L gate is 1.6 MLB seasons away for T4M-PROJ and ~11 NFL seasons away for NFL moneyline, at measured effect sizes. Calibration metrics would be informative far sooner. Options presented, none selected. | G6 cannot close on P&L evidence in any practical horizon. This is now the biggest strategic question on the board. |
| **APR-0034** | Should T4 MLB stop submitting demo orders while Kalshi's order path is broken? | **28.1 may make this moot** — if the sharding fix works, MLB accrual restarts and the question dissolves. Hold it until 28.1 reports. |
| **ADR-0063** | Emergency-stop / bet-sizing hierarchy. Drafted 2026-09-05, unsigned, absent from `APPROVALS_REGISTER.md`. | Twelve days. Blocks the kill-switch write side and any cell promotion. |
| **Shard funding** | If 28.1 finds shard 3 unfunded, moving mock demo collateral there is an action on your account, not the session's. | Even a correct client-side fix will not place an order without it. |

---

## DO NOT — standing

- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Bypass or disable a permission control — report what refused you and hand back.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time an existing price-capture window. Adding a missing day or series is different.
- Restart a production service without a scoped, written authorization. None is authorized in Wave 28.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the running process, not the file on disk, contains it.
- Manufacture a position, a row, a cohort member, or a final score to have something to measure.
- Submit an order against the production Kalshi account or with real funds. Demo only, always.
