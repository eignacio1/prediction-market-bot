# SESSION HANDOFF — T-570 (SHORT)

<!-- session-meta
task_id: T-570
tier: SHORT
timestamp: 2026-09-23T00:00:00Z
commit: 08b0acc
one_line_summary: T-570: retirement mechanism (warn-only) -- archive-mover, governance_scan assertion, operator console Section 0, branch/register reverse checks. No GG log/DECISION_LOG writes -- for 33.2 to register.
gg_touched: none (findings below are FOR 33.2 to register, not registered by this session)
adr_touched: none
plan_deliverable_moved: no
-->

**Date:** 2026-09-23
**Branch:** `session/20260923T234404Z-retirement-mechanism` (not yet merged — awaiting 33.2's concurrent GG-log/DECISION_LOG writes to land first, per this session's explicit ownership boundary)
**Tier:** SHORT — one deliverable ("make retirement a machine step instead of a person remembering"), delivered as four sub-parts per the task brief.

## What happened

Artifact *creation* in this repo (session claims, gap registration) is mechanical and enforced by tooling. Artifact *retirement* (archiving resolved gaps, deleting merged branches, closing register rows, closing session claims) was manual and unenforced — this session built the missing half, warn-only throughout, and touched nothing outside the stated scope fence (`scripts/retire_resolved_gaps.py`, `scripts/generate_operator_console.py`, `scripts/sweep_stray_branches.sh`, `scripts/check_register_parity.py`, `.claude/hooks/governance_scan.sh`, their tests).

**Deliverable 1 — `scripts/retire_resolved_gaps.py`** (commit `4b70985`). Moves RESOLVED/CLOSED-AS-ARTIFACT entries verbatim from `GOVERNANCE_GAP_LOG.md` to the archive. Dry-run by default; `--apply` required to write. **Proven on copies only this session — never run with `--apply` against the live log.** Report-back: entry-by-entry "would move" list and stay-token list were produced against a copy in a prior turn; the live log was never touched (`git status` throughout confirms no live-log diff from this session).

**Deliverable 2 — warn-only retirement-debt assertion in `.claude/hooks/governance_scan.sh`** (commits `bd577da`, `e7f8d9d`). Asserts the live log has zero resolved-class statuses; prints a warning, never fails the scan (`|| true`, matching the existing alarm-only pattern used elsewhere in the same hook). Run today against the live log: non-zero (24 unarchived resolved gaps found — see Deliverable 3 below), confirmed printing as a warning, exit code unaffected.

**Deliverable 3 — `scripts/generate_operator_console.py` Section 0** (commit `08b0acc`, this turn). `classify()` now checks resolved-class status first, before blocked/broken/accruing routing, so a resolved gap is never double-counted into another bucket. New "## 0. Overdue for retirement" section rolls up, against real repo data as of this session:

| Sub-finding | Count | Source |
|---|---|---|
| Unarchived resolved gaps | 24 | live `GOVERNANCE_GAP_LOG.md`, resolved-class entries not yet archived |
| Merged-but-undeleted local branches | 39 | `git for-each-ref` ancestors of `origin/main` |
| Prunable worktree metadata | 0 | `git worktree prune -n` |
| ADRs/APRs missing register accountability | 15 | `check_register_parity.py` rules 1, 2, 5 (12 ADRs + APR-0034/0035/0036) |
| Session claims with no closure row | 132 (noisy — see caveat) | `SESSION_CLAIMS.md`, "CLOSED"-prefix heuristic |

Full run: `Wrote 03_DECISIONS/OPERATOR_CONSOLE.md: retirement_debt=210 blocked=4 broken=6 accruing=104 total=138`. 19 new tests in `tests/test_generate_operator_console.py`; full related suite (`test_check_register_parity.py` + `test_generate_operator_console.py` + `test_retire_resolved_gaps.py` + `test_sweep_stray_branches.py` + `test_governance_scan_retirement_debt.py`) = **62 passed**.

**Deliverable 4a — `scripts/sweep_stray_branches.sh`** (commit `4874db4`). Extended with a landed-local-branch cleanup section: reports (default) or deletes (`--execute`, `git branch -d` only, never `-D`) local branches that are ancestors of `origin/main`. Never touches an unmerged branch, never touches the currently-checked-out branch, never force-deletes.

**Deliverable 4b — `scripts/check_register_parity.py` Rule 5** (commit `ec57dec`). Closes the one-directional gap in the existing register-parity check: previously only checked that a resolved ADR was *mentioned* somewhere in the register; Rule 5 now requires it to have its *own dedicated row*. Run against real data: **12 ACCEPTED ADRs currently fail Rule 5** (ADR-0001, 0003, 0010, 0015, 0018, 0024, 0026, 0027, 0028, 0032, 0045, 0046) — reported as findings for governance triage, not silently backfilled into `REGISTER_PARITY_EXEMPTIONS.txt` (adding an exemption is an adjudication this script does not make for itself).

## Findings for 33.2 to register (this session does not write GG-log/DECISION_LOG)

1. **24 unarchived resolved gaps** sitting in the live `GOVERNANCE_GAP_LOG.md` — candidates for a first real `retire_resolved_gaps.py --apply` run once an operator or 33.2 authorizes it (still deferred per this session's explicit instruction not to execute the archive move).
2. **12 ACCEPTED ADRs with no dedicated register row** (listed above) — a real, verified parity gap (Rule 5), not yet an exemption. Worth a GG entry distinct from the original GG-126 class, since GG-126 covered write-back drift, not this "mentioned but never given an own row" shape.
3. **15 total ADR/APR register-accountability findings**, including APR-0034/0035/0036 — these are `DECISION REQUEST` status, not `ACCEPTED`; they appear because Rule 1 requires *every* APR to have a row unconditionally, regardless of status. (Correcting a mislabel discovered this session: an earlier draft of this rollup's section header read "ACCEPTED/resolved ADRs or APRs with no register row," which was inaccurate for the APR half — fixed before commit.)
4. **Department directory count is 13, not 12.** `ls -d [0-9][0-9]_*` confirms `09_INTEGRATION_PATCHES` and `09_SECURITY_PRIVACY_COMPLIANCE` share the `09_` prefix. The originating task assumed 12; the generated Section 0 output now states this correction explicitly. Any other document in this repo that still says "twelve departments" is stale and should be corrected the next time it's touched (CLAUDE.md-style in-place-fix-and-log norm), but that correction is out of this session's scope fence.
5. **`SESSION_CLAIMS.md` closure-detection convention is not retroactively consistent.** The "starts with the literal word CLOSED" heuristic (used both by this session's new `unclosed_session_claims()` and implicitly assumed elsewhere) only reliably holds for recent rows. Concrete counterexample: T-224's closure row (dated 2026-07-18) reads "...T-224 close (...)" — closed, but not detected by the strict prefix match. This is why Section 0 reports 132 "unclosed" claims with an explicit caveat rather than presenting that number as trustworthy. **Not fixed this session** (broadening the heuristic risks new false negatives and is a rabbit hole beyond a SHORT-tier deliverable) — flagging as a candidate follow-on task if 33.2 or the operator wants the count tightened, e.g. normalizing older rows or widening the detection pattern with a reviewed regex.

## Not done (out of scope, Hard Rule 11)

- No archive move executed against the live `GOVERNANCE_GAP_LOG.md` — by explicit instruction, deferred to a later wave/operator call.
- No GG-log or DECISION_LOG.md writes — 33.2's ownership this wave.
- No fix to the `SESSION_CLAIMS.md` closure-detection heuristic itself (finding #5 above) — register-and-stop only, consistent with Hard Rule 11's "one session = one deliverable."
- No backfill of `REGISTER_PARITY_EXEMPTIONS.txt` for the 12 ADRs found by Rule 5 — that adjudication belongs to governance triage, not this script.

## Next session

- 33.2 (or a follow-on) should register the findings above as GG entries once its own concurrent GG-log/DECISION_LOG writes land, to avoid a merge collision on those files.
- First real `retire_resolved_gaps.py --apply` run against the live log is a distinct, deliberate follow-on — not automatic just because this session proved the tool works on copies.
- Branch is pushed (`session/20260923T234404Z-retirement-mechanism` @ `08b0acc`) and ready to merge to `main` once 33.2's concurrent work is reconciled.
