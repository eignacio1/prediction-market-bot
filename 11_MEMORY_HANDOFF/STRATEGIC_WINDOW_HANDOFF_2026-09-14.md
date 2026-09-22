# Strategic window handoff — outgoing window (Waves 20–24) → incoming

**Written:** 2026-09-14 · **Verified against:** `origin/main = 417663f`

---

## FIRST — before you trust anything below, including this line

1. **`git fetch origin`.** Every SHA and "not landed" claim in this document was derived from a ref that may already be stale. The outgoing window could not fetch — no network from its environment — and falsely reported completed work as unlanded at least once because of it.
2. Read `00_ADMIN/APPROVALS_REGISTER.md` **directly**. Do not accept this document's summary of what is approved.
3. Run the Princeton Protocol (`00_ADMIN/Princeton Protocol.txt`) in full — all four passes — then re-derive the state block yourself.
4. **Do not trust any figure in this handoff, including its own.** That instruction was given to this window at T-499 and it was correct; three of this window's six errors would have been caught earlier if it had applied the same standard to its own working memory.

---

## Your role

You are the **strategic window**. You do not execute build work. You write complete paste-in terminal prompts, the operator (Earl, sole operator and reviewer) pastes them into terminal sessions, and you verify results **against tracked files in git — never against a terminal's prose summary**.

Operator preferences, learned the hard way:
- Plain English. No jargon walls. He is a solo operator and cannot afford to decode your output.
- Prompt blocks go **in `04_EXECUTION/ACTIVE_QUEUE.md`**, not pasted into chat. He references them against closed waves.
- Blocks must be **fenced, complete, paste-in ready** — worktree line, `WORK FROM origin/main`, TIER, deliverables, DO NOTs, SCOPE FENCE, close-out, REPORT BACK. Prose bullet lists are not usable.
- Don't hand him work he has to fire later. Blocks are for now.
- He will tell you when you're wrong. He has been right every time.

---

## ⚠️ BLOCK 1 FOR YOU — GG-271 is fixed on a branch that never merged

This is the most important thing in this document.

**T-542 completed the fix.** Branch `origin/session/20260911T152320Z-gg271-bound-t4-rejected-positions`, 7 commits: a 2000-entry ring buffer (`MAX_REJECTED_POSITIONS`), a migration script, a fixed read race in the backup/verify path, 97 lines of tests, and a completed live VPS migration. The gap is marked RESOLVED **on that branch**.

**The branch is not on `origin/main`.** GG-271 still reads OPEN on main. That is the thirteenth-plus recurrence of the landing-failure pattern (GG-186) in this project.

**And the consequence is already measurable.** The live T4 portfolio cache (`logs/.vps_portfolio_cache_mlb_t4.json`, mtime 2026-09-14 23:45Z) is **15MB with 7,505 `rejected_positions` entries** — well past the 2,000 cap. The data migration ran, but because the *code* never reached main, the VPS is still running the unbounded writer and the file has regrown ~7,500 entries in three days.

At that rate it returns to the 33MB that OOM-killed the dashboard in roughly two weeks. **Land that branch first.** Verify against the live file afterwards, not against the merge succeeding.

*(Caveat, applied to my own claim: this was read at `origin/main = 417663f` and from a local cache file. Fetch and re-verify before acting.)*

---

## Verified state

| | |
|---|---|
| Cells | 92 · 18 execution bands · 5 sizing tiers |
| NFL capture | **Live and verified.** Week 1 opener recorded: 17,367 KXNFL price rows 09-09, plus depth. Day-3 (Wed UTC) window added; `--depth-sample-per-family 1` on all six NFL lines, VPS-deployed and confirmed via `crontab -l`. |
| Dashboard | Restored. Four stacked faults resolved (GG-269/270/272/273). Per-row model provenance now rendered (GG-267, T-544). |
| Six-step NFL trace | Market fetch ✅ · C1 ingestion ✅ · C2/C3 model 🟡 (LR exists, gate UNDERPOWERED) · C4 sizing ✅ · C5 run script ✅ paper-only, no cron · Settlement ✅ built, **never exercised** |
| Positions ever opened | **Zero.** T-543's gate stopped correctly rather than manufacturing one. |

---

## Open gaps — honest dispositions

| Gap | What it is | Status |
|---|---|---|
| **GG-271** | Unbounded `rejected_positions`; root cause of the dashboard outage. **Fixed on an unmerged branch; file regrowing.** | OPEN on main |
| **GG-274** | The NFL T1 settlement path has never run end-to-end, because no position has ever been opened to settle. | OPEN |
| **GG-257** | Kalshi splits a tied NFL moneyline $0.50/$0.50; `settle_position()`'s boolean model can't express it. Correctly refuses rather than guessing. ~1 tie/season. | OPEN, LOW |
| **GG-262** | Live VPS crontab's `run_mlb_pregame.py` schedule diverges from the repo. Cause unknown. Means the repo is not a reliable picture of the server. | OPEN, LOW |
| **GG-266** | Operator's Mac Python (3.9.6/LibreSSL) can't TLS-handshake with ESPN. All local live-network tests silently skip. VPS unaffected. | OPEN, LOW |
| **GG-256** | `claim_session.sh` allowed a duplicate T-number claim (two sessions claimed T-526 one second apart). | OPEN, LOW |
| **GG-260** | `ACTIVE_QUEUE.md` drifts as an uncommitted working-tree edit, invisible to worktree sessions. Recurrence of what T-505 fixed in Wave 10. **Every block needs a Deliverable 0 that installs and commits it.** | OPEN |
| **GG-255** | T1 game-market run scripts now exist for NFL and MLB. No cron for either — manual invocation only. | LIKELY RESOLVED |

---

## Operator-only — neither you nor a terminal can move these

| Item | Plain English | Consequence |
|---|---|---|
| **GG-203** | ~30 days. Every real order submission to Kalshi fails, 1:1 with approvals. Account/API-key problem, not code. Support ticket or demo-key regeneration. | **Nothing can ever trade, no matter what gets built.** Largest item on the board. |
| **ADR-0063** | Five-tier kill-switch / Kelly alignment hierarchy. Drafted 2026-09-05, still unsigned. | Blocks the kill-switch write side and everything gated behind it. |

---

## What Wave 25 should probably be

Your call after you re-derive, but the evidence points here:

1. **Land the GG-271 branch** (above). Non-negotiable, and verify against the live file.
2. **Open one real paper position, then settle it.** GG-274 exists because the settlement path has never run. The loop has never closed once, end to end, on a real game. Until it does, "it works" is untested.
3. **The NFL forecasting layer.** EXP-027's LR is real and calibrated (accuracy 0.6056, Brier 0.2210, ECE 0.0661, out-of-sample n=284) but its own pre-registered gate returned **UNDERPOWERED** — it scored zero 2026 games because the season hadn't started. It re-scores automatically as games resolve; several weeks of results now exist. Re-running it is cheap and is the first real read on whether there is edge.

---

## Failure patterns this window actually hit — assume you will too

Six errors, and **five were the same one: asserting a fact about a file without opening it.**

- Summarized an ADR's recommendation three times without reading it. It said the opposite.
- Cited a naming convention from memory that had been superseded by an amendment.
- Re-implemented a function's logic in a test harness instead of importing it; missed two branches and reported a false finding.
- Generalized a landing theory from n=1; the next block failed identically.
- Reported completed work as "did not land" from a frozen `origin/main`.
- Reused a live experiment ID (`EXP-026`/`HYP-011`) that already belonged to a different MLB experiment. The terminal caught it and rerouted.

**Every one was caught by a terminal or the operator, never by the window itself.** Cheap output and careful output are indistinguishable at the moment of production. The rules that follow from this are in `assert-from-memory-failure-mode.md` in project memory; the operative ones:

- Never cite a document you have not opened in your current window.
- Import and call the real function. Never re-implement it to test it.
- Never write "did not land" — write "not visible at my ref `<SHA>`, which may be stale."
- Mark every claim's source: "verified at `file.py:954`" vs "from my working picture, unverified." The operator can only calibrate trust in you if those look different.
- **Benchmark the deployed thing, not the unit test.** GG-272 and GG-273 were caught only because a deliverable measured the live pipeline instead of trusting green tests.

---

## DO NOT — standing, carry forward verbatim

- Touch sizing or any `kelly_fraction` without an ADR, including T1. ADR-0058 authorizes measurement stake at 0.0 and no sizing change.
- Promote `assert_ledger_invariants.py` to `--strict`. Alarm-only is a standing operator decision.
- Bypass or disable a permission control — report the exact command and refusal text, hand back. Five waves were lost to workaround attempts; the diagnostic is worth more.
- Re-investigate GG-203 in-repo. The ruled-out list is exhaustive.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- **Recommend against a sport or market family on one finding.** Operator doctrine 2026-08-21, reaffirmed 2026-08-27: MLB, NBA, NFL and NHL are all being built; which cells calibrate edge is discovered per-cell, never decided in advance.
- Modify or re-time the MLB price capture (feeds T-488, T-494, Phase 2).
- Restart a production service without a scoped written authorization. The 2026-08-29 grant was scoped to the 11.1 repair only and does not extend.
- Pre-assign T-/GG- numbers. Claim at run time, verify uniqueness across `git log --all`.
