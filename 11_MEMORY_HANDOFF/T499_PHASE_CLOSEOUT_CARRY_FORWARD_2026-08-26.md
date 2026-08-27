# T-499 Phase close-out — carry-forward, 2026-08-26

**Window:** Terminal session, T-499 ("Phase close-out — reconcile plan, registry, gap log, carry-forward"), worktree `20260827T013319Z-t499-phase-closeout`, merged to `main` this session at `4ceb0ea` and pushed to `origin/main`.
**Do not trust any figure in this document without re-deriving it.** Every number below was correct at commit `4ceb0ea`, verified 2026-08-26. This project's own instruments have been wrong more often than the things they measure (see Part C) — that pattern applies to this document too the moment another commit lands.

---

## Part A/B recap — what actually changed this session (re-derive, don't recall)

- Four ADRs flipped PROPOSED → ACCEPTED per explicit operator sign-off: **ADR-0054, ADR-0055, ADR-0057, ADR-0058.** Conditions recorded verbatim in `00_ADMIN/APPROVALS_REGISTER.md`. Four DECISIONS OWED items recorded there — read that file directly; do not paraphrase the conditions from memory.
- Gap log restructure/archive-move completed and merged: live `GOVERNANCE_GAP_LOG.md` **OPEN=65**, header/status parity **78=78**, `gg_id_uniqueness_check.py` **clean**. `OPERATOR_CONSOLE.md` regenerated against this state: blocked=4, broken=6, accruing=68, total=78, severity debt 30/78.
- `MARKET_EXPANSION_ACTION_PLAN.md`: boxes 2.2/2.3 checked with T-487's real (branch-only, unmerged) INCONCLUSIVE—EXTEND ARCHIVE verdict; 2.4 marked N/A pending an undecided routing question (INCONCLUSIVE has no defined reroute in the plan, unlike FALSIFIED); 3.4 confirmed correctly unchecked with T-490/T-491 context attached.
- `SESSION_CLAIMS.md`: three "CLOSED — NOT MERGED" rows added for T-490, T-491, T-487 — the 6th, 7th, 8th documented instances of the GG-186 pattern (claimed/real work whose branch never reached `origin/main`). T-490 and T-491 remain deliberately unmerged (out of this session's scope — foreign branches, not this session's own work). **T-487 remains unmerged too** — its Poisson-fit backtest, `HYPOTHESES.md` update, and `T487_EXP022_GATE23_RESULT.md` exist only on `session/20260826T000515Z-t487-phase2-team-totals` (tip `0ef39ab`). If Phase 2 work resumes, merging or re-deriving T-487's branch is a prerequisite, not a formality — `origin/main`'s `HYPOTHESES.md` still shows HYP-010 as PRE-REGISTERED.
- True next-free GG number: **221** (GG-220 confirmed reserved-and-unused, matching GG-201/205/207/208/211/213/214/215/219).

---

## GG-203 status — read the live entry, not this summary

**PARTIALLY RESOLVED** as of T-492 (2026-08-25). Root cause diagnosed and is **external, not fixable in this repo**: Kalshi's demo-account order-write path (`POST /portfolio/events/orders`) rejects every schema-valid, auth-valid order account-wide and ticker-independent, with three rotating non-diagnostic 404/403 bodies (`market_not_found` → `HTTP403 Nevada-residents` → `user_not_found`) across 2026-08-15 through at least 2026-08-25. Reads succeed (balance, market GET); only order-writes fail. No code change applies. **Recommended next action is operator-level: contact Kalshi support, or check/regenerate the demo API key.** ~5,700+ approved-and-discarded T4M-PROJ positions accrued during the window; the loss is ongoing until Kalshi-side state changes. **Do not assume this is fixed** — re-check `audit_mlb_t4.jsonl` for a `kalshi_order_failed`-free day before treating T4M-PROJ as executing again.

---

## Four measured results — do not re-run these, re-verify by reading the artifact instead

1. **T-487 / EXP-022 (Phase 2 gate 2.3):** INCONCLUSIVE — EXTEND ARCHIVE. `clean_n=207` games vs `n*=94,260` (own mean/sd); mean P&L/bet (game-level) = −0.0026. Artifact: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T487_EXP022_GATE23_RESULT.md` (branch-only, see above).
2. **T-492 / GG-203:** Kalshi demo order-write path externally broken, diagnosed exhaustively (credential, env, ticker-construction, and paper-trader-leak hypotheses all ruled out with direct evidence). See live gap-log entry above.
3. **T-489:** halt-latency measurements (referenced by ADR-0059/0060 lineage on band-level kill-switch NFR-03 timing) — re-read the task's own artifact before citing a number; not re-derived this session.
4. **T-494 / GG-135 game-market ruin geometry:** re-derivation exists at `T494_GG135_GAME_MARKET_RUIN/results.json` (pulled into `main` via this session's merge, originating from a T-494-era commit on the branch this session's worktree also carried) — read the file directly for the current figures; not re-derived or re-verified by T-499.

---

## Part C — The Phase's own verdict

**This Phase spent itself on measurement integrity instead of coverage expansion, and that was the correct use of it.**

The mandate coming in was reconciliation: verify the plan, the registry, the gap log, the claims file all say what actually happened. Every item in that mandate, without exception, turned up a version of the same defect — a document asserting a state that direct re-derivation contradicted. None of the five examples below were hunted for; they surfaced as a side effect of doing the reconciliation honestly instead of trusting the nav files.

**The generalizable lesson: this project's instruments have now repeatedly been more wrong than the things they measure.** In descending cost, this session's instances:

1. **T-487's closure note was invisible to a normal grep.** Its "CLOSED"/"MERGED:NO" self-report exists only on an unmerged branch — nothing in `origin/main`'s `SESSION_CLAIMS.md` pointed at it. A narrower search (`git log --all --grep`) found it; the file-based check alone would have missed real, valuable experimental work entirely and reported the phase as further behind than it is. Cost: high — this is the same failure shape (claimed work absent from the shared record) that GG-186 already names seven times, discovered an eighth time by the exact process meant to close it out.
2. **Three GG-186 instances (T-490, T-491, T-487) surfaced specifically during this close-out sweep**, not during the sessions that produced the work. The claim-lifecycle assertion this project built to catch exactly this pattern did not catch it in real time — it caught it retrospectively, three tasks late, because the tasks themselves were correct to self-halt or work standalone and nobody ran the ancestor-check until now.
3. **`OPERATOR_CONSOLE.md`'s apparent staleness was a real branch divergence, not document rot.** Local `main` was six commits behind `origin/main` and one commit ahead, unpushed — the console file wasn't lying about the gap log; the gap log itself hadn't reached the branch the console was generated from. Cost: moderate — resolved this session by merging and pushing, but it means a generated-file "staleness" symptom needs a branch-ancestry check before it needs a regeneration.
4. **`ACTIVE_QUEUE.md` carried "✅ merged" markings for work that wasn't**, caught in time this session by the same ancestor-check discipline, before it propagated into this document.
5. **A prior session's regex false-negative on GG-210/GG-212** (documented in an earlier segment of this same task) hid two real reserved-and-returned GG numbers from a plain-text scan — the same shape again: a check that looks like it covers the case but doesn't, discovered only by re-deriving instead of trusting the check's own output.

Five instances, one pattern: **a document or a check reporting a state (merged, current, reserved-and-unused, stale) that direct re-derivation contradicted.** The fix each time was never to distrust the underlying work — the work was consistently real and consistently fine — it was to distrust the *instrument reporting on the work*. This Phase did not expand coverage by a single cell. It found, at minimum, five places where the project's own record of itself was wrong, and left the record corrected and the divergence between branches resolved. That is a legitimate and necessary use of a Phase, not a consolation for one that didn't ship a cell — a coverage-expansion session built on top of any one of these five uncorrected would have built on a false floor.

**Standing instruction for whoever reads this next:** the next Phase should not assume this document's own counts are still current. Re-run the OPEN count, the parity check, the uniqueness check, and a `git merge-base --is-ancestor` check against `origin/main` before trusting anything above — including this sentence.

---

## Untracked files noticed in the main tree, not part of this session's scope

`05_RESEARCH_EXPERIMENTS/STRATEGIC_REVIEW_2026-08-03_HANDOFF.md`, `11_MEMORY_HANDOFF/NEW_WINDOW_PASTE_IN.md`, `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-08-12.md`, `..._2026-08-16.md`, `..._2026-08-18.md`, `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_PDTP_2026-08-24.md`, `scripts/lib/__pycache__/`. None of these were touched, evaluated, or relied upon by T-499 — flagged for the operator's own housekeeping decision, not resolved here (out of this session's stated scope: nav files, `03_DECISIONS/` archive moves, `04_EXECUTION/`, `11_MEMORY_HANDOFF/` — the strategic-window documents in the last group are arguably in-scope by directory but were left untouched deliberately, since none of the reconciliation items named them).
