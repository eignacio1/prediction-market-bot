# T-574 Results — Governance Tooling (Wave 34, session 34.1)

**Session:** `session/20260924T045227Z-resolved-filter` · **Date:** 2026-09-24 · **Tier:** SHORT
**Deliverable:** four bounded governance-tooling fixes — `classify()`, CLAUDE.md Step 3 correction, `retire_resolved_gaps.py` gating, GG-279 structural check.
**Scope:** `scripts/`, `.claude/hooks/`, `tests/`, CLAUDE.md Step 3 only. No write to `GOVERNANCE_GAP_LOG.md` or `DECISION_LOG.md` — both owned exclusively by concurrent session 34.2 (T-573) this wave. Gap candidates found below are recorded here only, for 34.2 to register.

---

## 1. Deliverable 1 — `classify()` in `generate_operator_console.py`

**Already fully satisfied by prior task T-570 (2026-09-23).** Verified by reading the code (`is_resolved_class()`, resolved-first priority routing in `classify()`) and running the existing test suite — no changes made. See `tests/test_retire_resolved_gaps.py` for the classifier's own test coverage (prefix-match on `RESOLVED`/`CLOSED-AS-ARTIFACT`, adversarial near-misses on `PARTIALLY RESOLVED` prose containing "fixed and verified").

**Operator console counts, before and after this session (unchanged, since no classify() code changed):**

```
Wrote 03_DECISIONS/OPERATOR_CONSOLE.md: retirement_debt=214 blocked=4 broken=6 accruing=106 total=140
SEVERITY DEBT: 32/140 live entries UNSPECIFIED (see GG-165)
```

Of the 214 retirement-debt items, **24** are unarchived resolved-class gaps (`Unarchived resolved gaps (24)` in Section 0). Full breakdown live: 4 blocked / 6 broken / 106 accruing / 140 total live entries — same before and after, since Deliverables 1 and 3 required no code change.

**Resolved-class status-string variants actually found in the live `GOVERNANCE_GAP_LOG.md` (2026-09-24, from the 24-entry unarchived-resolved list rendered in Section 0):**
- `RESOLVED` (bare)
- `RESOLVED (2026-09-09/10)`, `RESOLVED (2026-09-11)`, `RESOLVED (2026-09-07)`, `RESOLVED (2026-09-15, T-549)`, `RESOLVED (2026-09-22, T-564)` — dated, with/without a T-number
- `RESOLVED 2026-08-28 (T-502)` — date-before-parenthetical variant
- `RESOLVED (2026-09-11, code+migration) · ACTIVATED (2026-09-15, confirmed live in running process)` — compound suffix (the GG-271/GG-279 entry itself — see § 4 below)
- `CLOSED-AS-ARTIFACT` did not appear in this particular 24-entry sample but is covered by `test_retire_resolved_gaps.py`'s fixtures, including a `CLOSED-AS-ARTIFACT · superseded by ADR-0060, see GG-300` compound-suffix case.

All of the above classify correctly as resolved-class under `is_resolved_class()`'s prefix-match rule (starts with `RESOLVED` or `CLOSED-AS-ARTIFACT`, regardless of trailing narrative).

---

## 2. Deliverable 2 — CLAUDE.md Step 3 correction

**DONE, committed, and pushed** (`56178c3`, pushed to `origin/session/20260924T045227Z-resolved-filter` at the start of this segment).

Corrected the false "structurally impossible" claim about `classify()`/the operator console never mis-sorting a resolved entry, citing the measured distribution above (24 unarchived resolved-class entries still live, correctly classified) as the actual current evidence rather than an unverified assertion.

---

## 3. Deliverable 3 — `retire_resolved_gaps.py` gated execution

**Already fully satisfied by prior task T-570.** Verified by reading the script and its test suite — no changes made. The existing `--apply` flag, required `--out-src`/`--out-archive` pair (refuses with exit code 2 and no write if either is missing when `--apply` is passed), and dry-run-by-default behavior already satisfy every stated requirement (dry-run default, explicit apply flag, archive-destination assertion).

**Idempotency proof** (`tests/test_retire_resolved_gaps.py::test_apply_move_is_idempotent_on_second_pass`): running `plan_move` + `apply_move` a second time against the output of the first pass produces zero entries to move, zero warnings, and byte-identical `new_src`/`new_archive` output — confirmed passing in this session's test runs (`37 passed` for the targeted suite; see § 6).

**Per the explicit instruction for this deliverable: `retire_resolved_gaps.py` was NOT run against the live `GOVERNANCE_GAP_LOG.md` in this session** — all proof above is against synthetic fixtures (`SYNTHETIC_LOG`/`SYNTHETIC_ARCHIVE` in the test file) or `tmp_path`-based CLI tests. 34.2 owns the live governance log this wave; the 24 unarchived resolved-class entries identified in § 1 remain live and unarchived, ready for 34.2 to action with this tool once their concurrent work on the log concludes.

---

## 4. Deliverable 4 — GG-279 structural check

GG-279 (OPEN, MEDIUM): a code fix can land in git, even fully migrate on-disk state, and still not be active in a long-running service's process memory until that service is restarted (`t4-mlb` and `pmbot-web-dashboard.service` do not hot-reload). GG-271 recurred for ~77h in exactly this way — the fix was merged and the live data file migrated, but the running process kept executing pre-fix bytecode. GG-279's own Resolution field explicitly defers the live check: "a structural fix... is registered here and left for a future session to design and build."

**Fit within SHORT scope: partially — the comparison primitive fit, the live wiring did not, by GG-279's own design.**

Added `scripts/assert_service_activation.py`: a pure function `landed_but_not_activated(service_start, commit_timestamps)` returning the subset of given commit timestamps strictly newer than a given service-start timestamp (i.e., landed in git after the process's own last start — not yet active in that process's memory), plus an alarm-only CLI matching `assert_ledger_invariants.py`'s (Q7) convention (exit 0 always; findings go to stderr). 5 tests in `tests/test_assert_service_activation.py`, covering the GG-271 timeline itself, before/at/after boundary cases, empty input, and naive-vs-offset timestamp handling. All passing.

**Deliberately not built** (out of SHORT scope, and explicitly deferred by GG-279's own text, not just by this session's tier limit): SSH/`systemctl` enumeration of live services, and the source-path-per-service mapping that decides which git commits are "relevant" to a given service (e.g., which files under `src/` matter for `t4-mlb` vs. `pmbot-web-dashboard.service`). Both are real design decisions — GG-279 itself does not specify this mapping — not wiring that could be added mechanically within a SHORT-tier session.

**Gap candidate for 34.2 (or a future T-NNN) to register:** GG-279 remains OPEN. This session's primitive is a necessary but not sufficient piece of its structural fix — the follow-up task is to (a) define the source-path-per-service mapping and (b) wire `assert_service_activation.py`'s `landed_but_not_activated()` into a live check (likely Step 4, per GG-279's own suggestion) that pulls real `ActiveEnterTimestamp` values via SSH/`systemctl show` and real commit timestamps via `git log -1 --format=%cI -- <paths>` for each mapped service.

---

## 5. Deliverable 0(f) — visible debt in Section 0's roll-up

Added two new read-only detectors to `generate_operator_console.py`'s Section 0, following the existing detector-function pattern exactly:

- **`shared_tree_behind_origin()`** — how many commits the shared `main`-tree checkout (distinct from isolated per-session worktrees) sits behind `origin/main`. Verified live: correctly reports the primary checkout at `/Users/earlignacio/Documents/Claude/Projects/Prediction Markets` as 1 commit behind `origin/main` at time of this session's regeneration (expected — this session's commits haven't been pulled into the shared tree, which is exactly the condition the detector exists to surface for a session that skips the launch-isolated default).
- **`closed_wave_fences()`** — pasteable code fences left under a `## ... Wave N ...` header for a wave the Sequencing track already marks `CLOSED`, in violation of `ACTIVE_QUEUE.md`'s own stated archival rule. Verified live: correctly reports 0 findings post-Wave-33-recovery (the defect this detector was built to catch, found by hand during Deliverable 0, is already fixed).

Committed as `c849eae`, pushed. 7 new tests in `tests/test_generate_operator_console.py`, all passing.

**Note:** `03_DECISIONS/OPERATOR_CONSOLE.md` was regenerated to verify both detectors live (output confirmed above), then its diff was discarded via `git checkout --` per T-533 precedent — it's a hook-generated file, the regeneration itself reflects the generator script's diff (already committed), and no `classify()` logic changed.

---

## 6. Full test verification

Targeted suite (`test_generate_operator_console.py` + `test_retire_resolved_gaps.py` + `test_assert_service_activation.py`): all passing across this session's runs (37 + 5 = 42 tests touching this session's changes). A full-repo `pytest tests/ -q` run was also launched to confirm no unrelated regressions; see this session's close-out note for its result if it completed before session-end, otherwise treat as unconfirmed-but-not-blocking (targeted coverage of every file this session touched is complete and green).

---

## 7. Gap candidates for 34.2 to register (NOT written to `GOVERNANCE_GAP_LOG.md` by this session)

**(a) `SemanticFloorViolation` grep has no recency window — same defect class as the already-fixed `staleness_halts`/GG-085.**
CLAUDE.md Step 4 (line ~266): `grep -c "SemanticFloorViolation" /opt/prediction-market-bot/logs/paper_mlb_cron.log` is a raw cumulative count against a log file that is not rotated per-session — it has no time window, so one historical hit makes the check report a nonzero count indefinitely, exactly the shape of defect GG-085 already found and fixed for `payload.staleness_halts` (CLAUDE.md's own Step 4 text documents that fix and explicitly contrasts a "cumulative counter" with a "recency-windowed" check for the staleness case, but never applied the same correction to this line). The one hit found in a prior segment of this session was dated 2026-07-10 — roughly 2.5 months stale relative to this session's date (2026-09-24) — not a live signal. Suggested fix shape: mirror the `tail -500 ... | grep -c` recency-windowed pattern already used for T4 MLB staleness, applied to `paper_mlb_cron.log`.

**(b) `ACTIVE_QUEUE.md` queue-archival discipline lapse, Wave 33.**
During Deliverable 0 (shared-tree landing, before this worktree was created), Wave 33's pasteable prompt blocks were found dropped from `ACTIVE_QUEUE.md` without being moved to `ACTIVE_QUEUE_ARCHIVE.md` first, in violation of the file's own stated rule. Recovered in this session's predecessor commit (`4a00b8e`, "Recover Wave 33 archived prompts, land Wave 34 queue state"). This gap is now **structurally caught going forward** by Deliverable 0(f)'s `closed_wave_fences()` detector (§ 5) — flagging it here only as the originating incident, for 34.2's discretion on whether a GG entry is still warranted given the structural fix is already live.

**(c) Informational, not a gap:** Deliverables 1 and 3's core asks were found already fully satisfied by prior task T-570 (2026-09-23) — `is_resolved_class()`, `classify()`'s resolved-first routing, and `retire_resolved_gaps.py`'s gated `--apply` CLI all pre-date this session. Noted here so no future session re-attempts this work believing it outstanding.

---

## 8. Commits this session

- `56178c3` — CLAUDE.md Step 3 correction (Deliverable 2)
- `c849eae` — `shared_tree_behind_origin()` + `closed_wave_fences()` detectors (Deliverable 0(f))
- `43d1c69` — `assert_service_activation.py` comparison primitive (Deliverable 4)

All pushed to `origin/session/20260924T045227Z-resolved-filter` immediately after each commit, per this session's explicit instruction.

---

## 9. Addendum — self-inflicted false "CLOSED" row, found and corrected same-session (2026-09-25T01:16–2026-09-25T01:2x)

While closing out via `close_session_claim.sh`, running it directly from my own branch would have replicated T-572's already-documented "pushes whole unreviewed branch" defect (§7(gap candidate re: close_session_claim.sh push-whole-branch), so I instead ran it from a clean `git worktree add --detach origin/main`. That avoided the branch-push defect but introduced a different one: the script's `git merge-base --is-ancestor HEAD origin/main` check was tautologically true (HEAD *was* origin/main's own tip in that detached context), so it wrote a false `CLOSED — merge confirmed` row for T-574 even though PR #149 (containing all actual T-574 work) was still open/unmerged.

**Corrected same-session:** appended a follow-up row to `SESSION_CLAIMS.md` on `origin/main` (commit `6419ec3`) stating the true state (`MERGED: NO`, PR #149 open) and flagging the mechanism.

**Gap candidate (d) for 34.2 to register:** `close_session_claim.sh`'s ancestor-check is spoofable whenever it is run from a checkout whose HEAD already equals `origin/main` — including the exact detached-worktree pattern used here to avoid gap candidate's other defect (whole-branch push). The two defects compound: there is currently no safe way to run this script when the caller's real branch is unmerged. Suggested fix: require an explicit `--branch-sha <sha>` argument compared against `origin/main`, rather than trusting ambient `HEAD`.
