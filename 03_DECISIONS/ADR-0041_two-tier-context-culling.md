# ADR-0041 — Two-Tier Context Culling (ACCEPTED)

**Status:** ACCEPTED — operator directive Earl Ignacio 2026-07-09, issued as the explicit gate for Window A (context/token optimization infra) before any culling tooling is built.
**Date:** 2026-07-09
**Session:** Window A (isolated worktree `session/20260709T000753Z-ctx-optimization`)
**Operator:** Earl Ignacio
**Scope:** Governs what a Claude Code session may exclude from its loaded conversational context when working in this repository, and what it may never exclude. Applies to session-start retrieval (A3), cron/audit summarization (A4), and any future context-economy tooling. Does not change any C1–C8 production code path, retention policy, or file-deletion behavior — this ADR is about what enters a session's *context window*, not what exists on disk.

---

## Context

This project generates a large and growing volume of governance text: `DECISION_LOG.md`, `GOVERNANCE_GAP_LOG.md`, `SESSION_CLAIMS.md`, session handoffs, ADRs, and dense operational traces (`paper_mlb_cron.log`, `audit_mlb_t4.jsonl`, T4 cycle logs). Every session-start protocol (CLAUDE.md) reads several of these in full. As the project has matured (169+ resolved MLB positions, 100+ governance gaps, 40+ ADRs), the token cost of loading this material in full has grown to the point where it materially competes with the budget available for the actual work of a session — while, at the same time, several of this project's worst historical failures (GG-082 narrative conflation, GG-101 working-tree collision, the T-233/T-223 mislabeling) were caused by a session trusting an *already-loaded* narrative instead of re-reading the authoritative file, not by reading too much.

Any context-economy effort therefore has to solve two problems at once without trading one for the other:

1. Reduce the token cost of routine session-start and mid-session retrieval.
2. Never weaken the re-read-before-trust discipline (Hard Rule 10) that governance lineage depends on.

A naive approach — summarize everything, or truncate old entries — would fix (1) and reopen exactly the failure class (1) exists alongside: a stale or lossy summary standing in for the authoritative record. This ADR exists to draw the line explicitly before any tooling is built against it.

---

## Decision

Adopt a **two-tier context-culling model**. The tier a given piece of information belongs to is determined by what it *is*, not by its age or size.

### Tier 1 — Governance lineage: never culled, never summarized-in-place

Includes: `DECISION_LOG.md`, `GOVERNANCE_GAP_LOG.md`, all ADRs, `SESSION_CLAIMS.md`, `TODO_NEXT.md`, `MEMORY_BANK.md`, session handoff files, and the C6 audit JSONL logs (`logs/audit*.jsonl`, `logs/audit_mlb_t4.jsonl`).

Rules:
- These files are never truncated, destructively rewritten, or replaced by a summary **on disk**. Full history stays intact per existing retention policy (ENV-01/02 2yr, ENV-03 5yr, C6 append-only).
- A session MAY choose to load a *diff since last checkpoint* instead of the full file into its own context window (this is what A3's `session_delta.sh` operationalizes) — but the diff is computed against the real file at `HEAD`, not against a cached or remembered version.
- **Hard Rule 10 (re-read-before-trust) is reaffirmed without modification for these files.** Whether a session retrieved one of these files via a full read or via a delta script, it must re-read or re-diff the file fresh from `HEAD` immediately before writing to it. A delta script that makes retrieval cheaper does not make the pre-write freshness check optional — if anything, a delta-based workflow increases the risk of acting on a narrative that has since drifted (a delta bounds what changed *since the checkpoint*, not what changed since the delta was generated), so the check is load-bearing here specifically.
- No tooling built under this ADR may delete, compact, or destructively summarize a Tier 1 file's on-disk content. "Culling" for Tier 1 means "don't load the whole thing into context by default" — never "don't keep the whole thing."

### Tier 2 — Computation and derived artifacts: may be culled from context (never from disk without separate retention sign-off)

Includes: per-cycle T4 audit detail beyond the recency window Step 4 already checks, cron trace lines older than the current review window, experiment intermediate outputs (`exp_output/**` working files, not the final results JSON), and any full-file dump used only to reconstruct state that a fresh delta or summary script can regenerate on demand.

Rules:
- May be summarized, compacted, or excluded from what a session loads into its context window. A4's cron-aggregator summary is the canonical example: the executive summary is what a session reads; the raw trace stays on disk, untouched, for anyone who needs to go back to source.
- Culling here means "don't pull the raw form into the conversation" — it does not authorize deleting the underlying file or shortening existing retention windows. Any actual retention-policy change (deleting data before ENV-01/02/03 floors) requires its own ADR, not this one.
- A Tier 2 summary must be traceable back to its source file (path + line range or query used to produce it) so a session can always drop back to raw data if the summary looks wrong.

### The dependency this ADR gates

A2 (audit/log writer), A3 (session-delta script), and A4 (cron aggregator) are all downstream of this decision: A2 writes Tier 1 records without ever requiring the caller to re-read the log body back (receipt-only return); A3 computes a Tier 1 diff instead of a full-file load, but the diff is always taken against live `HEAD`; A4 produces a Tier 2 summary and explicitly never touches Tier 1 files. None of the three may be built or used before this ADR is accepted, per the gate the operator set for Window A.

---

## Consequences

**Positive:** Routine session-start and mid-session retrieval should cost meaningfully fewer tokens (measured in A5), freeing budget for actual analysis and implementation work in a session.

**Risk:** A delta or summary could omit a decision-relevant change if the checkpoint used to compute it is stale, or if a summarization heuristic misses something a human would have caught reading the full file. Mitigation: A3's own gate requires spot-checking, on one real handoff, that the delta captures every decision-relevant change versus the full file before the workflow is trusted going forward — this is not assumed to hold, it is tested once before being relied on. If a future session finds a delta or summary that hid a real change, that is a Tier-2-tooling bug to fix, not grounds to relax Tier 1's re-read-before-trust rule.

**Non-goal:** This ADR does not reduce what is written to disk, does not shorten retention, and does not change any C1–C8 runtime behavior. It is scoped entirely to what a Claude Code session loads into its own conversational context.

---

## Related

- Hard Rule 7 (log every strategic decision immediately) — this ADR's own registration follows that rule.
- Hard Rule 10 / GG-082 / GG-101 — the re-read-before-trust discipline this ADR explicitly reaffirms and refuses to weaken.
- T-300 (registered same session) — implementation task for A2–A5 under this ADR's gate.
