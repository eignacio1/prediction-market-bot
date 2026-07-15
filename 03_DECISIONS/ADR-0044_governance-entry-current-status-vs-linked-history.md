# ADR-0044 — Governance-Entry Splitting: Current-Status Line + Linked Immutable History (ACCEPTED)

**Status:** ACCEPTED — operator directive Earl Ignacio, 2026-07-15, given directly in-session in response to an efficiency/fidelity review (no code/capital change; a documentation-process ADR). **Not yet pushed to `origin/main`** — this session had no network route to GitHub (sandboxed environment), so the file exists locally in the working tree only. The next session with real push access must `git add`/commit/push this file and register it in `SESSION_CLAIMS.md`/`TODO_NEXT.md` per the normal protocol; until then, treat this ADR as adopted-but-not-yet-synced.
**Date:** 2026-07-15
**Operator:** Earl Ignacio
**Scope:** Governs how individual entries within `GOVERNANCE_GAP_LOG.md`, `MEMORY_BANK.md`'s Current State Snapshot / Last-reviewed chain, and (optionally) dense `DECISION_LOG.md` rows are structured going forward. Extends ADR-0041's Tier 1 principle ("never truncated, destructively rewritten, or replaced by a summary on disk") down to the level of a *single entry*, not just a whole file. Does not change any C1–C8 production code path, retention policy, or capital/gate logic.

---

## Context

Two independent, converging pieces of evidence triggered this ADR in the same session:

1. **An efficiency review** (this session, prior to this ADR) quantified that `GOVERNANCE_GAP_LOG.md` (2,088 lines) and `TODO_NEXT.md` (2,145 lines) are each growing ~40-50 lines/day, and that a single governance-gap entry (GG-105, the T4M-PROJ anti-predictive/calibration-decay finding) has grown into a multi-thousand-word nested narrative spanning five sub-investigations (T-333→T-344→T-359→T-361) stacked inline in one table cell. A session (or the operator) trying to answer "is this open, and does it matter today" has to read the entire investigative history to find out.
2. **`.claude/hooks/session_guard.sh`, run live during this same session**, independently flagged the identical pattern already active in `MEMORY_BANK.md`: 4 stacked "Current State Snapshot" headers and 20 stacked "Last reviewed" headers, each carrying full prior-session prose forward instead of being archived, in direct violation of an existing rule (T-334, "one authoritative entry, older ones archived") that the tooling already knows about but that has not been enforced.

ADR-0041 already established the correct principle for whole files (Tier 1 governance lineage is never destructively rewritten or replaced by a summary, but a session may load a diff/pointer instead of the full file). What ADR-0041 did not address is the case where the problem isn't file-level bulk — the *file* can be read via delta — but entry-level bulk: one row, one snapshot header, growing without bound because every session appends its full narrative to the same cell instead of the same *file*. `session_delta.sh` cannot help here, because the entry itself, not just the file, is what has become too dense to safely skim.

## Decision

**Every governance-log entry that accumulates a multi-session investigative history must carry exactly one live, short current-status line, with the full history moved verbatim to a linked, permanent, append-only memo file.**

Concretely:

1. **Current-status line (stays in the live file — `GOVERNANCE_GAP_LOG.md` row, or `MEMORY_BANK.md`'s single authoritative Current State Snapshot / Last-reviewed header):** one to three sentences. States: is this OPEN/RESOLVED/WATCH-ITEM right now, what is the one-line reason, and a link to the full-detail file. Nothing else. This is the line a session or the operator reads to know "do I need to care about this today."
2. **Linked history file (new, permanent, append-only):** the full investigative narrative — every session's findings, every dose-response sweep, every superseded hypothesis — moved verbatim, in full, losing zero content. Lives under `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/` (matching the existing convention already used ad hoc for some findings, e.g. `T344_GG105_DECOMPOSITION_MEMO.md`) or `11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md` for MEMORY_BANK snapshot/review-chain entries specifically (matching `session_guard.sh`'s own T-334 fix instruction). This file is itself Tier 1 under ADR-0041 — never truncated, never summarized-in-place, append-only going forward.
3. **The move must be lossless and verifiable.** Before replacing an inline entry with a pointer, the full original text must exist byte-for-byte in the linked file first. A session doing this migration diffs the extracted content against the original before deleting the inline copy, and states the verification explicitly in its `DECISION_LOG.md` row (not just "moved it").
4. **Trigger for when to split:** an entry crosses this threshold once it has accumulated narrative from **3 or more distinct session dates**, or exceeds roughly **500 words inline** — whichever comes first. Below that, leave it inline; splitting a short, single-session entry adds indirection for no benefit.
5. **This does not relax Hard Rule 10.** A session must still re-read/re-diff the current-status line fresh from `HEAD` before writing to it. The linked history file being append-only and permanent does not make the pointer line trustworthy-by-default.
6. **Does not apply retroactively by default.** This ADR governs entries going forward and any entry a session happens to be actively working. It does not mandate a one-time mass-migration of all existing dense entries in the same pass — that would itself be a large, collision-prone edit to files multiple concurrent sessions are actively writing to. Migrate opportunistically: the next time a session is already touching a given dense entry for substantive reasons, split it as part of that touch.

## Non-Goals

- This is not a change to retention policy. Nothing is deleted; volume moves, it does not shrink.
- This is not a replacement for `session_delta.sh` / ADR-0041 — it operates one level below file-granularity.
- This does not apply to short entries. Most `GOVERNANCE_GAP_LOG.md` rows are already one to two sentences and need no change.

## Consequences

- `GOVERNANCE_GAP_LOG.md` and `MEMORY_BANK.md` stop growing unbounded per-entry; growth becomes bounded by number-of-open-items, not number-of-sessions-that-ever-touched-an-item.
- A session (or the operator) can determine "what's actually open and does it matter" from the live file alone, without reading multi-thousand-word inline histories.
- Slightly more files to navigate (one linked memo per split entry) — an acceptable, disclosed tradeoff; this is what Recommendation #1 of the efficiency review explicitly called for.
- The `MEMORY_BANK.md` 4-snapshot / 20-review hygiene violation flagged live by `session_guard.sh` this session (T-334) is a ready-made, already-scoped first application of this ADR, but was **not** applied in this same session — `MEMORY_BANK.md` had uncommitted changes from a concurrent session at the time this ADR was drafted, and editing it risked colliding with that live work. Left as the immediate next action for whichever session picks this up next (see `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG105_SPLIT_WORKED_EXAMPLE.md`, drafted this same session, for a demonstration of the mechanics using GG-105 as a worked, non-live example instead).

## Validation

- Verified this ADR's proposed mechanics do not contradict ADR-0041 by direct re-read of ADR-0041's Tier 1 language before drafting (quoted above) — the "verbatim move to a linked permanent file, pointer left behind" pattern is explicitly compatible with "never truncated, destructively rewritten, or replaced by a summary on disk," since nothing is summarized or destroyed, only relocated.
- Confirmed the trigger threshold (§4) against GG-105 as a test case: 5 distinct session dates (T-333 through T-361) and well over 500 words — clears the bar by a wide margin, making it a correctly-scoped pilot candidate (demonstrated in the worked example, not applied live — see Consequences).

## Assumptions

- Assumes a future session with real network access will complete the push/PR/merge and formal `SESSION_CLAIMS.md`/`TODO_NEXT.md` registration this session could not perform.
- Assumes "3 sessions or 500 words" is a reasonable, not precisely-tuned, threshold — revisit if it proves too aggressive (splitting things not worth splitting) or too lax (dense entries still slipping through) after a few real applications.
