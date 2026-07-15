# GG-105 Split — Worked Example (ADR-0044 demonstration, not yet applied live)

**Purpose:** ADR-0044 proposes splitting dense, multi-session governance-log entries into a short current-status line (kept live in `GOVERNANCE_GAP_LOG.md`) plus a linked, verbatim, permanent history file. This file demonstrates the split mechanically using GG-105 (T4M-PROJ anti-predictive/calibration-decay finding) as the worked example, because it is the single largest entry in the log (5 distinct session dates: T-333, T-341, T-344, T-359, T-361) and clears ADR-0044's split threshold by a wide margin.

**This is a demonstration only. `GOVERNANCE_GAP_LOG.md`'s live GG-105 entry was NOT edited this session** — at the time this was drafted, GG-105 had very recent, active same-day work (T-359/T-361, Window 2 escalation, per `SESSION_CLAIMS.md`), and this session had no way to push/serialize through `origin` to safely coordinate a live edit with whatever session is currently working that entry. Editing it directly carried real collision risk for no benefit over demonstrating the pattern here first. A future session should perform the live split once it has confirmed (via a fresh `git diff` / re-read, per Hard Rule 10) that GG-105 is not mid-edit by a concurrent session.

---

## BEFORE (current live state — reconstructed verbatim from `GOVERNANCE_GAP_LOG.md` as read this session)

> Status | OPEN (watch item, by design) — registered 2026-07-07. The core gap (aggregate metrics cited as milestones while variance-dominated) is reinforced by the aggregate sign-flipping +$15.23 (n=151) → −$44.76 (n=169) in 18 bets. YES underperformance is variance-consistent (Binomial P(≤0)=0.073 on the k=2 0/7 run; model under-predicts k=2 at threshold level). Pre-registered monitor: revisit YES only at n_YES ≥ 40 with Fisher p<0.05 AND an identified mechanism. Watch item — no quarantine, no stop-work. **Citation-hygiene verification pass, 2026-07-12 (T-349):** [...several hundred words of T-349 detail...] **T-341 confirmation (2026-07-11, separate worktree, C7-wiring task):** [...] **T-344 decomposition (2026-07-12, same-day continuation, fresh VPS pull, clean_n grown to n=412...):** [...] **T-359 (2026-07-15, Window 2 escalation...):** [...H1 dose-response sweep, H4 isolation attempt...] **T-361 (2026-07-15, Window 2 continuation) drafts the formal remediation proposal...**

*(Full text runs well over 1,500 words in a single table cell as of this session's read — truncated here; the complete original is preserved verbatim in `GOVERNANCE_GAP_LOG.md`'s git history and was not altered.)*

## AFTER (proposed — what the live entry would read once split)

> **Status:** OPEN (watch item, by design) — registered 2026-07-07. T4M-PROJ shows a real, reproducible anti-predictive/calibration-decay pattern (win rate decays across edge terciles; calibration slope excludes 1.0). Leading mechanism: model overconfidence from unshrunk `ba_l10`, not a sign-inversion or sizing artifact (both ruled out). Remediation proposed (APR-0025, empirical-Bayes shrinkage), awaiting DS sign-off as of 2026-07-15. **Full investigative history (T-333→T-361, 5 sessions): see `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG105_FULL_HISTORY.md`.**

That's the entire live-file footprint after the split — roughly 60 words instead of 1,500+, with zero information loss: the full 1,500+ words move, unedited, into the linked history file.

## What moves into the linked history file (`GG105_FULL_HISTORY.md`, to be created when this split is actually applied)

Everything currently inline: the full T-349 citation-hygiene pass, the T-341 C7-wiring confirmation, the T-344 four-mechanism decomposition (with the GG-113 vig-sign-bug cross-reference), the T-359 H1×H4 interaction-model dose-response sweep, and the T-361 APR-0025 remediation-proposal summary — verbatim, unedited, in full. Nothing summarized, nothing dropped. This is what ADR-0044 §2-3 requires: the move must be lossless and verified before the inline copy is replaced.

## Next action for whoever applies this live

1. Confirm via fresh `git diff`/read (Hard Rule 10) that `GOVERNANCE_GAP_LOG.md`'s GG-105 entry has not changed since this worked example was drafted (2026-07-15).
2. Copy the full current inline text verbatim into a new `GG105_FULL_HISTORY.md` in this same directory.
3. Diff the copy against the original to confirm byte-for-byte match before touching the live file.
4. Replace the inline GG-105 Status cell with the short pointer line (see AFTER above, updated to whatever the entry's true current state is at that time — do not just copy this file's wording verbatim without re-verifying it's still accurate).
5. State the verification explicitly in the `DECISION_LOG.md` row for that session, per ADR-0044 §3.
