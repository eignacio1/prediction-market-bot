# Active queue — the only prompt file to read

**Verified against:** `origin/main = a1c5ed9` (2026-09-11) — *may be stale; `git fetch origin` before trusting any "not landed" call here.*
**Live state:** 92 cells · 18 execution bands · 5 sizing tiers · Week 1 NFL capture live and verified · dashboard restored
**IDs:** do not pre-assign. Claim at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
**Queue drift:** this file must be COMMITTED, not left as a working-tree edit — GG-260.

---

## Read this first (standing)

- Fire one wave at a time. Three concurrent maximum, disjoint file surfaces.
- **Deliverable 0 in every block: land any un-landed predecessor.**
- **Push after each deliverable, not at close-out.** Budget the close-out separately.
- Verify a code fix by importing and calling the real function. Never re-implement its logic in a test harness.
- **Benchmark the real thing, not the unit test.** GG-272 and GG-273 were both caught only because a deliverable measured the deployed pipeline instead of trusting a passing test.
- Register-and-stop on any gap outside scope (Hard Rule 11). Do not fix it incidentally.
- If a permission control refuses you, report the exact command and refusal text, then hand back.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10–19 | ✅ CLOSED | see history |
| **20** | ✅ CLOSED | Moneyline reframe. Settlement derivation + NFL result fetcher + resolver (T-527); GG-252 parser fix — NFL game markets went 0→64/404/304/55 parsed, MLB props held 286/286; NFL C1 ingestion (T-526). |
| **21** | ✅ CLOSED | Landed Wave 20; capture-fidelity audit (T-528, verdict GO); **day-3 Wednesday cron gap found and closed** (GG-261); NFL depth capture enabled and VPS-deployed (GG-259); T1 NFL run script landed (T-530). |
| **22** | ✅ CLOSED | NFL shadow run + EXP-027 LR adapter + NFL dashboard panel (T-534/GG-263); settlement resolver hardened with idempotency (T-535); depth-capture preflight proved the cron path clean before it fired (T-537/GG-265). |
| **23** | ✅ CLOSED | **Dashboard outage root-caused four levels deep** — see below. T1 MLB game-market run script + additive MLB parsing (T-538/GG-255 → LIKELY RESOLVED). |
| **24** | ⬜ **ACTIVE** | Stop the outage recurring · close the provenance gap · settle the first real game |

### ✅ WAVE 23 — what the dashboard outage actually was

The "Cannot fetch data / check SSH tunnel" error was none of those things. Four distinct faults, each hidden behind the last:

| Gap | What it was | Status |
|---|---|---|
| **GG-270** | `/api/data` did an unbounded `json.load()` of a 33MB file, OOM-killing the service in a restart loop. Blanked MLB *and* NFL panels behind a false "SSH tunnel" message. | RESOLVED |
| **GG-269** | The service was in an active OOM crash-loop that `systemctl is-active` does **not** reliably reveal — the health check that reported "active" was lying. | RESOLVED |
| **GG-272** | GG-270's own fix introduced a 2.2–4.6s latency regression, two separate causes. Caught only because a deliverable benchmarked the live pipeline instead of trusting green unit tests. | RESOLVED |
| **GG-273** | systemd `CPUQuota=10%` throttled the now-fixed 0.39s request into ~3.8–4.15s wall time, making a correct fix look broken. Proved with `cpu.stat`: 38 of 38 accounting periods throttled, ~3.38s of the 3.79s was pure throttling. | RESOLVED |
| **GG-271** | **The root cause, still open.** The T4 MLB writer appends to an unbounded `rejected_positions` array — 24k+ entries, ~33MB and growing. Registered-and-stopped as out of scope. | **OPEN** |

**This is why Wave 24 opens with GG-271.** Everything above was treating symptoms of a file that is still growing.

### ⬜ WAVE 24 — fire 3-wide, disjoint surfaces

| # | Block | Tier | Why |
|---|---|---|---|
| 24.1 | **GG-271** — bound the `rejected_positions` array | STANDARD | The outage's root cause. Still growing. Will take the dashboard down again. |
| 24.2 | **GG-267** — per-row model provenance | SHORT | Did not run in Wave 23. The panel can't distinguish a stub row from a real forecast. |
| 24.3 | **Settle the Week 1 opener** | STANDARD | First real end-to-end close: market → forecast → size → position → settlement. |

---

# 24.1 — GG-271 · BOUND THE T4 LEDGER · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "gg271-bound-t4-rejected-positions"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD.

GG-271: the T4 MLB writer appends an unbounded `rejected_positions` array to
logs/paper_portfolio_mlb_t4.json -- 24k+ entries / ~33MB observed 2026-09-10. This is the ROOT CAUSE
of the GG-269/270/272/273 outage chain that blanked the operator's dashboard for two days. Those four
are resolved; this one is not, and the file is still growing.

*** THIS FILE IS LIVE PRODUCTION STATE FOR THE ONLY BAND CURRENTLY TRADING. ***
GG-034's file-lock invariant governs every mutation. GG-224 showed a clobber happening ON the
protected path. Treat every write as dangerous.

DELIVERABLE 1 -- MEASURE AND LOCATE BEFORE CHANGING ANYTHING.
  Current size, entry count, growth rate per day, and oldest/newest entry timestamps.
  Find every writer that appends to `rejected_positions` -- grep the whole repo, do not assume it is
  one site. Quote each with file and line.
  Establish what actually READS it. If nothing reads it, say so plainly -- that changes the right fix
  from "rotate" to "stop writing it".
  **Report findings before writing code.**

DELIVERABLE 2 -- DECIDE THE FIX ON THE EVIDENCE, AND SAY WHY.
  Options, in rough order of preference:
   (a) stop writing rejections into the portfolio file at all; they belong in the audit log, which is
       already append-only and rotated
   (b) bound the array (ring buffer / last N) with N justified by what actually reads it
   (c) rotate the file
  **Do not implement more than one.** Whatever you pick, the portfolio file must stay a portfolio
  file -- position state -- not an event log.
  If rejections carry information nothing else preserves, say that explicitly; it changes the answer.

DELIVERABLE 3 -- IMPLEMENT UNDER THE LOCK, AND MIGRATE SAFELY.
  Every mutation goes through PaperTrader's existing `with self._lock, self._file_lock():
  self._reload_locked(); ...; self._save()` pattern. Do not hand-roll fcntl. Do not add a second
  lock discipline.
  Migrating the existing 33MB file: back it up first, verify the backup loads and its open positions
  match the original exactly, then migrate. **If the position set differs by even one entry, restore
  and stop.**
  **Do not restart the T4 service to do this.** The 2026-08-29 restart pre-authorization was scoped
  to the 11.1 repair and does not extend here. If a restart is genuinely required, stop and report
  that it is -- do not take it.

DELIVERABLE 4 -- PROVE IT HOLDS. A test that simulates sustained rejection volume and asserts the file
  stays bounded. Then re-measure the live file post-migration: size, open-position count (must be
  unchanged), and /api/data latency (must stay under 2s).

DO NOT: restart any service. DO NOT: touch kelly_fraction/sizing, promote a cell, submit a live order,
  or settle a position. DO NOT: touch deploy/cron.conf or the archiver.
DO NOT: touch scripts/web_dashboard.py or any NFL path -- other blocks own those this wave.
DO NOT: promote assert_ledger_invariants.py to --strict.
DO NOT: delete any historical rejection data without first writing it somewhere durable.

SCOPE FENCE: the T4 writer path, paper_trader.py if the lock path genuinely requires it, a migration
script under scripts/, tests, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: size/count/growth-rate/timestamps; every writer with file+line; what reads it; which
option you chose and why; the backup verification; post-migration size and open-position count
(before vs after); the bounded-growth test; live /api/data latency; GG-271 disposition.
```

---

# 24.2 — GG-267 · PER-ROW MODEL PROVENANCE · SHORT

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "gg267-per-row-model-provenance"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: SHORT. This was scoped in Wave 23 and did not run. GG-267 is still OPEN.

GG-267: the NFL position/audit data model has no per-row model-identity field. The dashboard's
provenance label is section-wide, so a row produced by the EXP-027 LR and a row produced by
StubNFLForecastModel are indistinguishable once written. The operator is beginning to read this panel
to make decisions. This project's signature failure is an instrument that drifts from the thing it
measures -- close this before the panel is trusted, not after.

DELIVERABLE 1 -- Read run_t1_nfl_game_market.py's position/audit write path and
  nfl_exp027_adapter.py in full. Quote the current row schema and the adapter's PROVENANCE class
  attribute.

DELIVERABLE 2 -- Add a per-row model-identity field, written at position-open AND at every audit
  event: the model identity (adapter PROVENANCE string, or an explicit stub marker) plus enough to
  distinguish runs.
  **It must be impossible to write a row without one.** No default that could silently label a stub
  row as the LR. If the model cannot state its identity, the row records UNKNOWN explicitly.
  Backward compatible: rows already on disk load fine and read UNKNOWN -- a reader never assumes.

DELIVERABLE 3 -- Render it. scripts/web_dashboard.py is free this wave (Wave 23's dashboard work is
  closed) -- surface the per-row label in the NFL panel so the operator can see, per row, which model
  produced it. Keep it additive; **do not alter any MLB panel, path, or key.**
  Verify by loading the page and confirming both the NFL per-row labels and all MLB panels render.
  Re-check /api/data stays under 2s after your change -- GG-272's lesson.

DELIVERABLE 4 -- Tests: a stub row and an LR row are distinguishable on disk; a legacy row with no
  field loads and reads UNKNOWN; no code path can write a row with the field absent or empty.

DO NOT: re-fit, retrain or instantiate the EXP-027 model to read its identity -- use the class
  attribute; its docstring warns instantiation re-fits.
DO NOT: touch logs/paper_portfolio_mlb_t4.json or the T4 writer (24.1 owns those).
DO NOT: touch kelly_fraction/sizing, deploy/cron.conf, settle_position(), or any MLB run path.
DO NOT: submit a live order or settle any position.

SCOPE FENCE: run_t1_nfl_game_market.py, nfl_exp027_adapter.py, scripts/web_dashboard.py (NFL panel
only), tests, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the quoted current schema and PROVENANCE attribute; the field and where it is enforced;
how the panel renders it; post-change /api/data latency; the three test results; confirmation MLB
panels are unchanged.
```

---

# 24.3 — SETTLE THE WEEK 1 OPENER · STANDARD

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "settle-week1-opener-first-real-close"
Claim your own IDs at run time (GG-236); verify uniqueness across `git log --all` (GG-256).
Gap-log entry as your FIRST pushed commit.
*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***

TIER: STANDARD. The Week 1 opener kicked off 2026-09-10T00:20Z and is final. T-534 ran a paper
shadow against it with the EXP-027 LR; T-535 built and hardened the resolver. **Nothing has ever
been settled through this path.** This block closes the first full loop end-to-end:
market -> forecast -> size -> position -> settlement.

*** GATE *** `git fetch origin`, then establish and REPORT, before doing anything else:
  - Does logs/paper_portfolio_t1_nfl_game_market.json exist on the VPS, and does it contain any
    positions from T-534's shadow run? Paste the position count.
  - **If there are ZERO positions, STOP.** That is a complete and valid answer: report why T-534
    opened none (check its audit log for refusal codes) and hand back. Do not manufacture a position
    to have something to settle. Do not re-run the shadow against a finished game.

DELIVERABLE 1 -- FETCH THE REAL RESULT. Use nfl_espn_results.py to get the opener's final score.
  Confirm the game is FINAL, not in-progress -- T-535 built a not-yet-final guard; verify it fires
  correctly rather than trusting it.
  Cross-check the final score against a second independent source and paste both. A settlement run
  on a wrong score is worse than no settlement.
  **GG-266 warning:** the local dev machine's Python (3.9.6/LibreSSL) cannot TLS-handshake with
  ESPN. If you hit that, run this step on the VPS and say so.

DELIVERABLE 2 -- DRY RUN FIRST, AGAINST A COPY. Copy the portfolio file; run the resolver against
  the COPY. For every position report: market type, derived actual_stat, threshold, YES/NO outcome,
  and P&L. Verify each derivation by hand against the final score -- moneyline is final point margin
  vs threshold 0; spread is margin vs the line; totals are combined or team score vs the line.
  If the game was a tie, the resolver must REFUSE via check_settlement_ambiguity() per GG-257.
  **Paste the full dry-run output. Do not proceed to Deliverable 3 until the arithmetic is verified
  line by line.**

DELIVERABLE 3 -- SETTLE FOR REAL. Only after Deliverable 2 verifies clean.
  Back up the live portfolio file first and confirm the backup loads.
  Run the resolver against the live file, under the existing lock discipline.
  Then run it AGAIN and prove idempotency -- the ledger must be byte-identical after the second pass
  (T-535 built this; verify it, do not assume it).
  Report the resulting realized P&L and the final ledger state.

DELIVERABLE 4 -- SAY WHAT IT MEANS, HONESTLY. One paragraph: what this result does and does not tell
  us. **It is one game on a model whose own pre-registered gate came back UNDERPOWERED (EXP-027).**
  A win here is not evidence of edge and a loss is not evidence against it. Write it so the operator
  cannot mistake a single settled paper position for a signal.

DO NOT: place any new position. DO NOT: submit a live order. DO NOT: modify settle_position() --
  GG-257 is registered, not assigned here.
DO NOT: touch logs/paper_portfolio_mlb_t4.json or the T4 writer (24.1 owns those).
DO NOT: touch scripts/web_dashboard.py (24.2 owns it). DO NOT: touch any MLB ledger.
DO NOT: touch kelly_fraction/sizing, deploy/cron.conf, or promote any cell.
DO NOT: adjust, retrain or re-fit the model based on this outcome. One game changes nothing.

SCOPE FENCE: a settlement run + its backup, apply_resolved_nfl_game_markets.py only if a proven
defect blocks the run, gap-log + DECISION_LOG.
Self-serialising close-out: rebase onto origin/main before writing GOVERNANCE_GAP_LOG.md/DECISION_LOG.md.

REPORT BACK: the gate result (position count -- and if zero, why); both independent final scores;
the full dry-run table with hand-verified arithmetic; the backup verification; realized P&L; the
idempotency proof; and your Deliverable 4 paragraph.
```

---

## Needs your decision

| Item | Plain English | What happens if it waits |
|---|---|---|
| **GG-203** | 26 days. Every attempt to place a real order with the exchange fails. It is an account/key problem, not a code problem — a support ticket or a new demo key. | Nothing can ever trade for real, no matter how much gets built. Biggest item on the board and only you can move it. |
| **ADR-0063** | The written rule for how the emergency-stop levels line up with bet sizing. Drafted 09-05, still unsigned. | Blocks the write side of the kill switch and everything in Wave 25. |
| **GG-262** | The live server's schedule for one MLB job doesn't match what's in the repo. Nobody knows why. | Low risk today, but it means the repo is not a reliable picture of what the server is running. |
| **GG-266** | Your Mac's Python is too old to talk to ESPN over HTTPS. | Local test runs silently skip all live-network tests. VPS is unaffected. |

---

## DO NOT — standing

- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Bypass or disable a permission control — report what refused you and hand back.
- Re-investigate GG-203 in-repo; the ruled-out list is exhaustive.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time the MLB price capture.
- Restart a production service without a scoped, written authorization.
- Pre-assign T-/GG- numbers. Claim at run time.
