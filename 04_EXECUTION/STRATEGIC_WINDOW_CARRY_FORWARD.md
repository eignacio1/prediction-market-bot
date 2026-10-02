# Strategic Window — Carry Forward

**Written:** 2026-10-01, at the close of the window that ran Waves 38 → 44.
**Verified against:** `origin/main = d8d5850`. Every figure below was derived by running a command
against tracked files, not recalled. Where something is judgment rather than state, it says so.

> **This file is the operating context for the strategic window.** It is not a status report. It
> carries the things that exist nowhere else in the repo: why the arc bent where it did, what has
> already been disproved, and the traps that cost the last window real time.

---

## 1. The role

The strategic window is **eyes, not hands**. It does not execute build work. It:

1. Derives true state from tracked files at `origin/main` — never from a terminal's prose summary.
2. Writes complete paste-in prompt blocks into `04_EXECUTION/ACTIVE_QUEUE.md`.
3. Verifies the previous wave against tracked files before writing the next.
4. Routes findings, verdicts and decisions to the operator. It does not hand him commands to run.

**Operator's standing framing, in his words:** *"I'm eyes and ears on the project not the plumbing —
that's for you and the terminals to do."* Sandbox / paper / demo actions are plumbing: handle them, do
not escalate. **Only actions touching real capital are his.**

---

## 2. Wave construction — the rules, and why each exists

- **Three blocks per wave. Never four.** Operator directive 2026-09-15. A sequencing note is not a
  fence; blocks fire concurrently.
- **Each block carries its workstream to a measured verdict.** Operator directive 2026-09-30, given
  because the window had been splitting one job across three waves — build an instrument in one wave,
  wire it in another. *"These terminal windows can take on and should take on more work."* Blocks are
  now LARGE and stop only at a real governance boundary: an operator decision on capital/sizing/pool
  contents, a model change needing its gate, an unaccepted ADR, or a permission control. **Caution is
  not a boundary.**
- **Disjoint file surfaces, stated explicitly in the queue.** Exactly one block per wave owns
  `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md`; the others write findings into their results summary
  for later registration.
- **Deliverable 0 in every block:** land un-landed predecessors, sync the shared tree, paste
  before/after SHAs. **The landing step is the recurring failure mode**, not the work itself.
- **Pre-register before measuring, and push the pre-registration as its own commit.** This is the
  single most valuable habit the project has. It is why EXP-028's void-flag, EXP-029's HARMFUL and
  EXP-032's NEAR could not be quietly relabelled afterwards.
- **Write the stop condition into the arc, in advance.** Every wave since 39 has pre-registered what
  result would stop or redirect the arc. Three have fired. None were argued with after the fact.
- **Invariants on the queue file:** exactly three fenced blocks (`grep -c '^```'` returns 6), and
  **ASCII only inside fences**. A fourth fence means something is wrong — stop.
- Closed prompts move **verbatim** to `ACTIVE_QUEUE_ARCHIVE.md` *before* the queue rotates. Wave 33's
  prompts were once deleted without archiving; don't repeat it.

---

## 3. Traps that cost the last window real time

- **This window cannot `git fetch` and cannot push.** `origin/main` is frozen at the last terminal's
  fetch. Never report "did not land" — report *"not visible at my ref `<SHA>`, which may be stale."*
- **Derive from `origin/main`, not from local `main`.** The shared worktree is routinely dozens of
  commits behind. I once read `rev-list --left-right` backwards and reported the tree as *ahead* when
  it was 28 *behind*. Check the direction.
- **`device_commit_files` silently no-ops on its first call, often.** It returns `{"written":[...]}`
  and the file is unchanged. **Always commit, then `md5sum` on the device against the staged file, and
  re-commit if they differ.** This is in no documentation and it will bite.
- **The absolute `devicePath` form sometimes fails where `~/...` succeeds.** Prefer `~/Documents/...`.
- Files written to `/mnt/user-data/outputs/` with `Write` or `Edit` appear in the chat automatically;
  a file placed there by `cp` needs `SendUserFile`.

---

## 4. State at handoff

| Fact | Value |
|---|---|
| `origin/main` | **d8d5850** (2026-10-01) |
| Highest GG / T / ADR | **GG-326** · **T-603** · **ADR-0069** |
| Live gap entries | **138** · **119 OPEN** |
| Unaccepted ADRs | **0067** (append-only log), **0068** (band doctrine), **0069** (game-key correlation group) — all PROPOSED |
| Cells | 92 · 22 bands · **1 ACTIVE** (T4M-PROJ), and it is formally MISFILED |
| Countable evidence | **42 rows**; **1,694 recoverable** on operator sign-off |
| Capital at risk | **$0.** `kelly_fraction = 0.0` on every live band since July. Demo venue only. |
| Price archive | ~2.12 M rows · 14 families · 2026-08-01 → 10-01 |
| Live terminal | Landed byte-faithful, tested. **VPS still serves the old page** — restart unauthorized. |

---

## 5. The empirical record — read this before proposing anything

**This is the most valuable section in the file.** Every line is a pre-registered result. Do not
re-ask a question that is already answered here, and do not re-cut data to rescue one.

### Proven

- A 16-feature pre-game tree beats **climatology** by ΔBrier **+0.0052** [.00438,.00601] over 1,414
  games, and beats the one-line shrunk-BA rule by **+0.0036**. Depth earns its complexity. (EXP-028)
- MLB T4M-PROJ provenance reconstructs to **13 cited windows**, formula source hash identical across
  all 12 commits, and **verifies offline 13/13** from an in-repo snapshot. (T-592, T-595)
- The archive's books are **exactly complementary** — `no_ask = 1 − yes_bid`, zero residual on all
  2.125 M rows. YES and NO cost the same; they differ only in *availability*. (EXP-032)
- **H is a strong function of time.** The half-spread falls an order of magnitude as the start
  approaches: KXMLBF7 20c → 1c, KXMLBTEAMTOTAL 4c → 0.5c. (EXP-032)

### Disproven

- **T4 latency thesis** — NOT SUPPORTED at the current feature set. (T-569)
- **NFL EPA splits** — no detectable difference; every interval spans zero. (ADR-0066)
- **Pre-game model vs the market** — **HARMFUL.** ΔBrier −0.00393, CI [−.00629,−.00152], 215 games.
  The corrected placebo (backward +.00494 vs forward +.00484, **ratio 1.02**) showed the model's skill
  is time-symmetric persistence — player role and playing time — which a liquid market prices first.
  (EXP-029)
- **T4 structural depth** — T4's other 27 logged fields: −0.0063 [−.0203,+.0091], every C setting
  worse, power floor met at 40/40 games. (EXP-030)
- **Cross-family market selection** — **ZERO CANDIDATES** across 14 families. Several *clear* their
  null (KXMLBTEAMTOTAL, all five F-series) but E < 0 because H eats the gap. (EXP-031)
- **Execution-cost rescue** — **no family's E crosses zero under any policy the archive evidences.**
  (EXP-032)
- **Multi-leg coherence** — **0 of 24 cells survive.** Holm-adjusted p = 1.0 in every cell. (EXP-033)
- **`exchange_index` propagation** — tested and disproved. (T-558)

### The structural finding, and it is the project's most important

EXP-032 answered *why* the board is closed, not just *that* it is:

> **H falls as the start approaches — and B falls with it.** The mispricing EXP-031 measured at the
> earliest quote has largely converged by the time the toll is cheap. Correcting the cost side removes
> the H-kill, and then B-at-entry kills the same families instead.

The edge and the cost **decay together**. That is a property of the venue's price formation, not of
any model. KXMLBHIT under the cheap-entry policy is the closest thing to a survivor — **+0.0042, CI
[−.0006,+.0101], B earned at entry** — explicitly labelled **NEAR** and **not promoted**, because the
CI spans zero and it is day-fragile.

And capacity closes it independently: the depth sample's **p25 within 5c is $0.00** for KXMLBTEAMTOTAL.
No stake in this project's range is supported, at any size.

### Still unknown — not assumed either way

- **89 of 92 cells** have no measured cadence, so C5 cannot rule on them.
- Whether **another venue** prices more loosely. Never examined. Only Kalshi has been measured.
- Whether **pre-kickoff NFL state** carries signal — captured once, never modelled.
- Whether the **2,229 non-clean** T4M-PROJ rows are recoverable. Never attempted.
- Drift / convergence for **F3, F5, F5SPREAD, F5TOTAL** — UNMEASURED, because their markets close
  1.0–1.7h after start and failed EXP-032's pre-registered 2.0h clock floor. **The floor was not edited
  after the fact** (GG-327). That is the discipline working; it also leaves a real gap.

---

## 6. The arc, and the stop condition that just fired

Wave 44's arc pre-registered this:

> *"If 44.1 shows no family's E crosses zero under any evidenced policy AND 44.2 finds nothing
> surviving its toll and correction, then this venue is efficient net of cost across every structure
> the project can currently measure, and the next decision is venue or asset-class selection — not
> another model, another feature, or another band."*

**Both halves came true.** EXP-032: no crossing under any evidenced policy. EXP-033: 0 of 24.

**So the next decision is not a modelling decision.** This is judgment, not state, and it is the
operator's call — but the window should not write a Wave 45 that quietly re-asks a settled question.
The live options, in the order the evidence supports them:

1. **Venue selection.** Every measurement to date is about one exchange. Whether a different venue,
   or a different asset class, prices more loosely is entirely unexamined. This is the option the stop
   condition points at.
2. **Capacity-first.** Even the NEAR result dies on depth. 44.3 built a depth writer that reaches
   statistical adequacy in about a week — one week of capture would convert "unmeasurable" into
   "measured", cheaply, and would settle whether anything here is sizeable at all.
3. **The unmeasured four.** F3/F5/F5SPREAD/F5TOTAL fell out of EXP-032 on a clock-gate technicality.
   Re-running them under a correctly specified clock is cheap and closes a known hole — but note this
   is *not* re-cutting: the gate failed on a stated rule, it was not edited to rescue a result.
4. **The operator's own roadmap.** He has described the eventual arm as *"big hitters, low-probability
   parlays, sharp-money low win rate lines"* and the north star as that level of granularity at every
   arm. ADR-0069 now exists as the correlation-group draft. EXP-033 found no coherence violations in
   the structures the archive holds — but the archive holds *this venue's* structures only.

**What the window must not do:** propose another feature set, another band, or another model for these
families. Four pre-registered experiments have closed that door and the standing rules forbid re-cutting
to reopen it.

---

## 7. Open operator decisions, carried forward

None of these block a wave. All have been carried for multiple waves.

| Item | State |
|---|---|
| **Dashboard service restart** | Terminal landed byte-faithful (59,130 bytes, mutation-checked, 31/31 tests, `/api/data` 0.21–0.56 s). Needs a line naming `pmbot-web-dashboard`. **The VPS still serves the old page.** |
| **Settlement + depth capture schedules** | Writers built, back-captured, reconciled (1 discrepancy: a timing difference, neither source preferred). Cron lines DRAFTED as comments, not installed. |
| **NFL pre-kickoff capture** | Runner built, 11/11 tests, hand-run twice, cron drafted. **Its urgency was disproved** — see §8. |
| **Provenance allowlist — 1,694 rows** | Verifies offline 13/13. Two residual risks are the operator's: **L1** VPS working-tree state at each process start; **L2** provenance of each day's `ba_l10_shrunk` input. |
| **APR-0035** | Both sides of its arithmetic now exist. Open **eight weeks**. |
| **ADR-0067 / 0068 / 0069** | All PROPOSED. 0068 is already being *enforced* (C5 produced GG-320 and the T3 verdict) by a criterion that has not been accepted. |
| **39.3 triage — 6 NOTED** | One sign-off pass archives six entries. Cheapest window recovery available. |
| **T4M-PROJ and T3 disposition** | Both MISFILED under C5. T3 additionally has **no order path at all** — read-only scan, JSON report. Change-control entries drafted by 42.3. |
| **ADR-0063** | Approved in chat 2026-09-18; file still reads PROPOSED, no register row. Pure record-keeping. |
| **ADR-0064 / 0065 / 0066 · APR-0034 / 0036 · 9 unmerged branches · registry corrections** | Unchanged. |

---

## 8. Judgment that is not in the repo

**The last window got two things wrong, both the same way: asserting from a secondary source without
checking the primary.** Both were caught. Both are worth inheriting.

1. **"The band doctrine isn't in the record."** Asserted after checking one ADR. It was in
   `EXECUTION_BANDS.md` the whole time. What was *actually* wrong was subtler and more useful: the
   doctrine licensed a stripped decision tree on **assumed** speed rather than measured speed, and
   `CLAUDE.md` stated the complexity gradient **backwards**. That became ADR-0068 and criterion C5.
2. **The NFL "weekly clock."** Wave 43's queue said each week without a pre-kickoff capture was
   permanently lost, with urgency attached. It came from T-597's report, passed forward unchecked.
   **43.3 disproved it**: `nflverse/nfldata` is git-versioned at ~10-minute commits (1,116 commits read,
   92 sampled, 0 mismatching cells), and referee/temp/wind are *null before kickoff and populated only
   after* — they were never perishable pre-kickoff fields. **Nothing is unrecoverable.**

The rule that caught it is already in every block: *a premise written in a block is a claim to verify,
not a fact — including every number in this file.* **Keep writing that line, and mean it about your own
queue.** The second error cost a terminal part of its budget disproving the window.

**Three things the terminals did right that are worth protecting as culture:**

- **T-594 void-flagged its own results** rather than relax a pre-registered criterion its permutation
  control had failed, and diagnosed the control as mis-specified instead of claiming a pass.
- **T-597 refused to enable the NFL capture**, judging that with no existing schedule to configure
  inside, enabling *was* scheduling — then said so explicitly rather than acting.
- **T-603 flagged its own deviation** (a pre-registered bootstrap it did not implement) in a result
  where nothing survived and no CI was needed.

A project that reports its own failures to follow its own rules is worth more than one that always
looks clean.

**Compaction note.** The outgoing window compacted once, around Wave 38. Everything before that was its
own summary, and both errors above trace to building on summaries. **If this window compacts, treat
pre-compaction recollection as a lead to verify, never as a citation.**

---

## 9. Standing DO NOT — carry verbatim into every block

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228). Re-capturing a raw source from its own upstream is a different act — say which one you are doing.
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding — and do not assume the rest of the board behaves like the cells that happened to be measurable.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization.
- Add a cron entry without explicit operator authorization, including for read-only capture writers.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`; **re-verify after any release or retry** (GG-322 — two blocks once ran as the same T-592).
- Report a live fix RESOLVED without proving the RUNNING process contains it, not the file on disk.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Assume a fill the data cannot evidence.
- Revive `exchange_index` propagation — T-558 tested and disproved it.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.

---

## 10. First actions for the incoming window

1. Derive state from `origin/main` — refs, gap counts, max GG/T/ADR — **in one command**, and diff
   against §4 above. Report any drift rather than assuming this file is current.
2. Read, in full, the three Wave 44 results summaries. They are the live frontier:
   `EXP032_RESULTS_execution_cost_surface_2026-10-01.md`,
   `EXP033_RESULTS_multileg_coherence_2026-10-01.md`,
   `T602_archive_self_sufficiency.md`.
3. **Do not write Wave 45 until the operator has chosen a direction.** The stop condition fired; the
   decision in front of him is venue / asset-class selection versus capacity-first versus closing the
   four unmeasured families. Present the options with their evidence and let him pick.
4. Two dashboards sit in the project root: **`Visual Dashboard.html`** (analytical — what the project
   has established) and **`Live Terminal.html`** (operational — the bot transpiring). Both are static
   snapshots as of 2026-10-01 and should be regenerated when a wave closes.
