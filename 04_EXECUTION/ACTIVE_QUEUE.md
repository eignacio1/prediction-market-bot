# Active queue — the only prompt file to read

**Verified against:** `origin/main = 80984e8` (2026-09-16, Cowork strategic window) — *may be stale; the window cannot `git fetch`. Run `git fetch origin` first. A LANDED call is safe from a stale ref; a "not landed" call is not.*
**Live state, derived by import not grep (2026-09-16):** 92 cells · **22 execution bands** · **1 cell ACTIVE** (MLB player-prop hits × T4M-PROJ) · 88 NOT_IMPLEMENTED · 2 BLOCKED · 1 DARK · 128 gap-log entries, **89 OPEN**, next free **GG-285**.
**Unlanded:** `session/20260915T235119Z-why-no-bet-can-be-placed` (tip `73cd8eb`, 6 commits) — Wave 26's Floor-A fix and APR-0034. Landed in 27.1.
**Ignore:** `session/20260915T003401Z-nfl-capture-gap-0912` (tip `4985290`) reads NOT-LANDED but its content landed under new SHAs via merge `57beb30`. GG-276 is RESOLVED on main. Do not re-land it.
**IDs:** do not pre-assign. Claim at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
**Queue drift:** this file must be COMMITTED, not left as a working-tree edit — GG-260.

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Hard ceiling, operator directive 2026-09-15.
- **A block in the wave fires immediately, concurrently with every other block.** A sequencing note is not a fence. Work that must wait goes in "Queued next," not in the wave.
- **Deliverable 0 in every block: land any un-landed predecessor.** Wave 25 left two strays, Wave 26 left one. Every wave so far has left at least one.
- **A premise written in a block is a claim to verify, not a fact.** Two waves running, the briefing asserted something it had not derived — `ActiveEnterTimestamp` (T-548 corrected it) and "Weeks 1 and 2 have resolved" (GG-281; only Week 1 had). Both were caught by the terminal, neither by the window. Check the premise before acting on it and register the correction if it is wrong.
- **Push after each deliverable, not at close-out.** Budget the close-out separately.
- Verify a code fix by importing and calling the real function. Never re-implement its logic in a test harness.
- **Benchmark the real thing, not the unit test.**
- **A merge is not a deployment, and a deployment is not an activation** (GG-279). Prove the *running* process carries the change.
- Register-and-stop on any gap outside scope (Hard Rule 11).
- If a permission control refuses you, report the exact command and refusal text, then hand back.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–24 | ✅ CLOSED | see history |
| **25** | ✅ CLOSED | GG-271 ACTIVATED and proven (T-548) · GG-203 remediated to exhaustion, still broken (T-547) · NFL Saturday capture gap root-caused (T-545/GG-276) · NFL T1 opened 0 positions, GG-274 still OPEN (T-546). Fired 4-wide; 2 branches left unlanded. |
| **26** | ✅ **CLOSED, 2 OF 3 LANDED** | **Capture coverage closed properly** — GG-276 and GG-280 both RESOLVED, detector generalized to sport/dow-agnostic, Wave 25's strays landed (T-549) · **EXP-027 re-run: UNDERPOWERED, and the number is the story** (T-550/GG-281) · **Floor A was real and is fixed; Floor B is now APR-0034** (T-551/GG-282, unlanded). |
| **27** | ⬜ **ACTIVE** | Land Wave 26 and try to open a position · confront the n* wall · fix the two cohort defects |

### ✅ WAVE 26 — what actually happened

**The min-bet floor was a real own goal, and it is fixed.** T-551 confirmed both T1 game-market run scripts inherited `risk.py`'s live `$10` floor while setting an ADR-0050 `$1.00` measurement stake — a guaranteed refusal on every approved bet. Fixed in both scripts with tests, aligned to the paper floor their four sibling runners already pass. **This is the first time in this project's history that a refusal class was found to be self-inflicted rather than external.**

**Floor B became APR-0034** — *Should T4 MLB run with `kalshi_client=None` while GG-203 is unresolved?* Three options presented, none selected, plus what superseding ADR would be required under Hard Rule 3. It is on your desk.

**EXP-027 is UNDERPOWERED, and the gap is not close.** Verbatim re-run, zero code changes: `clean_n = 14` games against **`n* = 2,610.35`**. 2026 prospective: accuracy 0.5625, Brier 0.2290, ECE 0.1739, n=16 — against the 2025 out-of-sample baseline of 0.6056 / 0.2210 / 0.0661, n=284. The session correctly refused to read anything into a 16-game sample.

**The number nobody has said out loud:** at `mean=0.0321` and `sd=0.4992` per bet, `n*` is ~2,610 games. An NFL regular season is 272 games. **That gate is roughly ten NFL seasons away at the observed effect size.** It is not a "wait a few more weeks" situation, and no amount of Week 2, 3 and 4 data changes the order of magnitude. That is 27.2.

**Two cohort defects found while disclosing the capture gap, both register-and-stop.** GG-283: the backtest's Kalshi team-code alphabet has `WSH` but not `WAS`, and a live ticker uses `WAS` — `parse_event_teams` silently returns `None` and drops the game. GG-284: `2026_01_CLE_JAX` has zero archived KXNFLGAME rows on *any* date, not just 09-12. Both correctly left unfixed mid-run so the pre-registered cohort was not changed underneath the gate.

---

### ⬜ WAVE 27 — fire all three together, disjoint surfaces

| # | Block | Tier | Why |
|---|---|---|---|
| 27.1 | **Land Wave 26 + open and settle a position** | STANDARD | Floor A's fix may have unblocked the 24 refused evaluations. The loop has never closed once. |
| 27.2 | **The n\* wall — is the gate reachable at all?** | STANDARD | clean_n=14 against n\*=2,610. Ten seasons. Someone has to ask whether the gate statistic is the right one. |
| 27.3 | **GG-283 + GG-284 — two defects in the NFL cohort** | STANDARD | One game silently dropped by a team-code typo, one missing from the archive entirely. |

**Surfaces:** 27.1 owns the two T1 run scripts, the NFL portfolio and the settlement resolver. 27.2 owns `run_power_calc.py`, a new APR in `00_ADMIN/`, and read-only analysis. 27.3 owns the backtest's team-code table, the archiver and `PRICE_ARCHIVE/`. All three write the gap log and DECISION_LOG — self-serialising close-out applies.

---

# 27.1 — LAND WAVE 26 · OPEN AND SETTLE A POSITION · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "land-w26-open-and-settle"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

DELIVERABLE 0 -- LAND WAVE 26'S UNLANDED BRANCH FIRST.
  origin/session/20260915T235119Z-why-no-bet-can-be-placed  (tip 73cd8eb, 6 commits)
  Carries T-551/GG-282's Floor-A fix (min_bet_usd in both T1 game-market run scripts, with tests)
  and APR-0034. Everything below depends on that fix being on main.
  Confirm with `git merge-base --is-ancestor 73cd8eb origin/main` AFTER merging. A merge command
  exiting 0 is not the check.
  Then confirm the fix is actually present: grep min_bet_usd in both run scripts on main and paste it.

DELIVERABLE 1 -- RE-RUN THE OPEN ATTEMPT AND COMPARE THE REFUSAL BREAKDOWN.
  T-546 ran the real EXP-027 adapter (not the stub) against 1,185 live markets on 2026-09-15 and
  opened zero: 1,105 no_model_prediction, 52 no_live_quotes, 24 min_bet_floor, 4 no_edge.
  Re-run the same path with Floor A now fixed. Use the VPS venv and the `export $(grep -v '^#' .env
  | xargs)` pattern -- plain `source .env` does not export into the Python subprocess (T-546 lost two
  attempts to this).
  **Report the new refusal breakdown against those four numbers before doing anything else.** The
  min_bet_floor count is the measurement: if it went to zero, Floor A was the blocker for those 24.
  Confirm model_identity on every row is the EXP-027 string, not the stub.

DELIVERABLE 2 -- IF A POSITION OPENS, SETTLE IT END TO END. This closes GG-274.
  Fetch the final score with nfl_espn_results.py, on the VPS (GG-266: the Mac's Python cannot
  TLS-handshake with ESPN). Confirm FINAL, not in progress -- verify T-535's guard fires, do not
  assume. Cross-check the score against a second independent source and paste both.
  Dry-run the resolver against a COPY first. Per position: market type, derived actual_stat,
  threshold, YES/NO outcome, P&L. Hand-verify the arithmetic against the score -- moneyline is final
  margin vs threshold 0. On a tie the resolver must REFUSE via check_settlement_ambiguity() (GG-257).
  **Paste the full dry-run. Do not settle live until the arithmetic is verified line by line.**
  Then back up the live file, settle under the existing lock discipline, run it AGAIN, and prove the
  ledger is byte-identical on the second pass.

DELIVERABLE 3 -- IF IT STILL OPENS ZERO, THAT IS THE FINDING. REPORT IT PROPERLY.
  Name the dominant refusal class and what would have to change to clear it. Do not manufacture a
  position. Do not widen a threshold, loosen a gate, or switch to the stub model to get a row.
  no_model_prediction at ~93% means EXP-027's moneyline-only scope, not a defect -- say so plainly.

DELIVERABLE 4 -- ONE HONEST PARAGRAPH. If a position settled, it is one paper position on a model
  whose own gate returned UNDERPOWERED at clean_n=14 against n*=2,610. A win is not evidence of edge
  and a loss is not evidence against it. Write it so it cannot be misread as a signal.

DO NOT: submit a live order, or construct PaperTrader with a non-None kalshi_client.
DO NOT: modify settle_position() -- GG-257 is registered, not assigned here.
DO NOT: change min_bet_usd, kelly_fraction, MIN_BET_USD, or any _HARD_LIMITS value beyond what
  Deliverable 0 lands.
DO NOT: touch the backtest, its team-code table, the archiver or PRICE_ARCHIVE/ -- 27.3 owns those.
DO NOT: touch run_power_calc.py or draft any APR -- 27.2 owns that.
DO NOT: touch any MLB ledger or the T4 writer. DO NOT: restart any service. DO NOT: promote a cell.
DO NOT: add a cron entry for any T1 game-market run script.

SCOPE FENCE: the merge, the two T1 game-market run scripts if a proven defect blocks the run, a
settlement run + its backup, apply_resolved_nfl_game_markets.py only if a proven defect blocks it,
gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the ancestor check post-merge and the grepped min_bet_usd lines; the new refusal
breakdown against T-546's four numbers; whether a position opened; if so both independent scores, the
hand-verified dry-run table, the backup verification, realized P&L and the idempotency proof; GG-274's
disposition; your Deliverable 4 paragraph.
```

---

# 27.2 — THE n* WALL · IS THE GATE REACHABLE · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "n-star-wall-gate-reachability"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD. This is ANALYSIS and a decision request. Change no gate, no threshold, no parameter.

EXP-027's re-run (T-550, 2026-09-15) returned clean_n=14 against n*=2610.35, at
mean_pnl_per_bet=0.0321 and sd=0.4992. An NFL regular season is 272 games. Nobody has stated the
implication: at the observed effect size that gate is roughly ten NFL seasons from clearing, and
Weeks 2 through 18 do not change the order of magnitude.
APR-0024 sets the standard -- per-band `clean_n >= n*`, n* derived live from that band's own observed
mean and stdev of P&L per bet. That is the right shape for a low-variance signal. The question this
block asks is whether it is reachable for signals whose per-bet sd is ~15x their mean.

DELIVERABLE 1 -- COMPUTE THE WALL FOR EVERY CELL THAT HAS DATA. Do not stop at NFL moneyline.
  For each band/cell with a resolved cohort -- T4M-PROJ, T1, T2, and EXP-027's NFL moneyline -- run
  scripts/run_power_calc.py and report: observed mean, sd, sd/mean ratio, n*, current clean_n, and
  **n* expressed in seasons or months of real cadence at that cell's own measured bet rate.**
  That last column is the one that has never been computed. It is the whole point of this block.

DELIVERABLE 2 -- ASK WHETHER P&L-PER-BET IS THE RIGHT GATE STATISTIC.
  Calibration metrics converge far faster than P&L per bet, because they do not carry payoff
  variance. EXP-027's own 2025 baseline reports Brier 0.2210 and ECE 0.0661 at n=284 -- quantities
  that are already informative at a sample where n* on P&L is not remotely met.
  Establish, with the numbers: what n would be required for a Brier or ECE read at the same power,
  versus n* on P&L, for at least two cells. Show the calculation.
  **Do not propose replacing the gate.** Establish the size of the difference and let the APR carry it.

DELIVERABLE 3 -- STATE THE STRATEGIC CONSEQUENCE PLAINLY, IN ONE SECTION.
  If every cell's n* is years away, then G6 as currently written cannot close on P&L evidence within
  any practical horizon, and the coverage target (one cell of ~25 ACTIVE) compounds it.
  Say whether that is true, cell by cell, from Deliverable 1's table. If it is not true for some
  cell, name that cell -- it is the one worth prioritizing.

DELIVERABLE 4 -- DRAFT THE APR. DO NOT DECIDE IT.
  A decision request in 00_ADMIN/, numbered per convention, presenting options: keep the P&L gate and
  accept the horizon; add a calibration-based interim gate for cell promotion while P&L stays the
  gate for live capital; re-derive n* under a different power/alpha; or something else the analysis
  surfaces. Note what superseding ADR each would require (APR-0024 and ADR-0057 are in force;
  Hard Rule 3 applies). Recommend, do not select.

DO NOT: change n*, alpha, power, any gate threshold, or any pre-registered verdict.
DO NOT: relabel EXP-027's UNDERPOWERED verdict. It stands regardless of what this analysis finds.
DO NOT: touch kelly_fraction/sizing, promote a cell, submit an order, or settle a position.
DO NOT: touch the T1 run scripts, the settlement path or the NFL portfolio -- 27.1 owns those.
DO NOT: touch the backtest's team-code table, the archiver or PRICE_ARCHIVE/ -- 27.3 owns those.
DO NOT: restart any service.

SCOPE FENCE: read-only analysis, scripts/run_power_calc.py invocations, one new APR in 00_ADMIN/,
gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the per-cell table including n* in seasons/months at real cadence; the calibration-vs-P&L
sample-size comparison with its calculation shown; your Deliverable 3 statement cell by cell; the
APR's filename and its recommendation in two sentences.
```

---

# 27.3 — GG-283 + GG-284 · TWO DEFECTS IN THE NFL COHORT · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "gg283-gg284-nfl-cohort-defects"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

Both were found by T-550 while disclosing the GG-276 capture gap, and both were correctly left
unfixed so the pre-registered cohort was not changed mid-run.
  GG-283 -- exp027_hyp012_nfl_moneyline_backtest.py's Kalshi team-code alphabet contains "WSH" but
  not "WAS"; a live KXNFLGAME ticker uses "WAS", so parse_event_teams returns None and the game is
  dropped SILENTLY. 2026_01_WAS_PHI was lost this way despite healthy pregame snapshots 09-05 to 09-11.
  GG-284 -- 2026_01_CLE_JAX has zero archived KXNFLGAME rows on ANY date in the captured September
  window, not just 09-12, so GG-276 is ruled out as sole cause. Cause unconfirmed.
Together they cost 2 of 16 resolved games -- 12.5% of an already tiny cohort.

DELIVERABLE 1 -- AUDIT THE WHOLE ALPHABET, NOT JUST WAS.
  A silent None on one code means the mapping was never validated against live tickers. Pull the
  distinct team codes actually appearing in captured KXNFLGAME tickers across the whole archive and
  diff them against _NFL_TEAM_CODES. Report every mismatch in both directions.
  **Report the full diff before fixing anything.** If WAS is the only one, say so; if there are
  others, they matter more than WAS does.

DELIVERABLE 2 -- MAKE THE FAILURE LOUD, NOT JUST CORRECT.
  Fix the alphabet. Then make parse_event_teams unable to fail silently again: an unmapped code must
  surface -- a counter, a warning, a refusal -- not a None that reads as "no game here."
  A silent drop that shrinks a statistical cohort is the same failure class as GG-276's silent
  capture gap and GG-203's silent order failures. Tests for both the fix and the loudness.

DELIVERABLE 3 -- FIND OUT WHAT HAPPENED TO CLE_JAX.
  Zero rows on every date is not a cron-window gap. Check: did KXNFLGAME markets for that matchup
  exist on Kalshi at all; did the archiver query and get nothing; is it a series-naming or
  event-ticker variant the archiver does not match; or was it never listed.
  **Name the cause with evidence, or state explicitly that it could not be determined and why.**
  If it is a matching defect, fix it and prove the fix against the live exchange.

DELIVERABLE 4 -- STATE THE COHORT EFFECT. DO NOT RE-RUN THE GATE.
  Say how many games these fixes would restore to the EXP-027 cohort, and note that clean_n would go
  from 14 toward 16 against n*=2610 -- immaterial to the verdict.
  **Do not re-run the backtest and do not touch its pre-registered parameters.** Whether and when to
  re-run on a corrected cohort is a separate decision, not yours to take here.

DO NOT: change any pre-registered parameter, threshold, cohort rule or verdict label.
DO NOT: re-run the EXP-027 gate or relabel its UNDERPOWERED verdict.
DO NOT: backfill, reconstruct or synthesise archive rows (GG-156).
DO NOT: modify or re-time any existing capture window. Adding a missing series match is different --
  if you add one, prove it with an env -i cron dry-run, the T-537 pattern.
DO NOT: touch the T1 run scripts, settlement or the NFL portfolio -- 27.1 owns those.
DO NOT: touch run_power_calc.py or draft any APR -- 27.2 owns that.
DO NOT: touch kelly_fraction/sizing, promote a cell, submit an order, or settle a position.
DO NOT: restart any service.

SCOPE FENCE: the backtest's team-code table and parse_event_teams, the archiver's series matching,
tests, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the full live-ticker-vs-_NFL_TEAM_CODES diff; the fix and the loudness mechanism with
its tests; CLE_JAX's cause with evidence or an explicit could-not-determine; the cohort effect in
games; confirmation you did not re-run the gate.
```

---

## Queued next — not yet fired

**Wave 28 — depends on 27.** If 27.1 settles a position, GG-274 closes and the loop has run end to end for the first time; the next question is cadence, which means a cron entry and therefore your authorization. If 27.2's analysis shows the P&L gate is unreachable everywhere, the next question is the gate itself, and that is an ADR — which runs into unsigned **ADR-0063** either way.

**GG-279 — deploy-vs-activation still has no structural check.** The design sketched with it: compare each long-running service's `ActiveEnterTimestamp` against its source's most recent relevant commit. Worth one SHORT block once a slot frees; it prevents the exact class that cost GG-271 four days.

---

## Needs your decision

| Item | Plain English | What happens if it waits |
|---|---|---|
| **APR-0034** | New, from Wave 26. Should T4 MLB stop submitting demo orders while Kalshi's order path is broken? Three options, none selected. If the demo round-trip is optional, this is the one thing that could restart MLB accrual without Kalshi doing anything. | T4 MLB stays at zero. 33 days and counting since the last position entered. |
| **ADR-0063** | The emergency-stop / bet-sizing hierarchy. Drafted 2026-09-05, still unsigned, still absent from `APPROVALS_REGISTER.md`. | Blocks the kill-switch write side, and blocks any cell promotion that 27.1 or 27.2 might make reachable. Eleven days unsigned. |
| **GG-203 / Kalshi** | Your correspondence. Their "expected... periodically unstable" reply does not address a 100% failure rate over 33 days on a fresh key. | Nothing accrues in T4 MLB. APR-0034 is the only lever that does not depend on them. |
| **GG-262** | The live server's schedule for one MLB job doesn't match the repo. Cause unknown. | Same class as GG-271 and GG-276. Capture lines are now audited; this one is not. |

---

## DO NOT — standing

- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Bypass or disable a permission control — report what refused you and hand back.
- Re-investigate GG-203 in-repo. T-492 ruled out the code; T-547 rotated the key and filed with support.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time an existing price-capture window. Adding a missing day or series is different.
- Restart a production service without a scoped, written authorization. None is authorized in Wave 27.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the running process, not the file on disk, contains it.
- Manufacture a position, a row, or a cohort member to have something to measure.
