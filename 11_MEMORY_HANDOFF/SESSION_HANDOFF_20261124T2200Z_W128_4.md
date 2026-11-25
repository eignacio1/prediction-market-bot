# Session handoff - W128.4 H-DEPTH-PAM-3 (2026-11-24)

<!-- session-meta
task_id: W128.4
tier: MICRO
one_line_summary: Landed PR #555 (rebased, CI-gated); H-DEPTH-PAM-3 SUPPORTED (judged run was W124.5's, not re-read); Part B routing words written
gg_touched: GG-2004
vision_pillar: PROOF, DEPTH
gap_measure: P2, D5(b) PAM class 3 NBA
gap_delta: P2 +1 verdict; D5(b) class 3 NBA absent -> interpreted (12_EXPLORATORY/pam_stability/RESULT.md)
pattern_sweep: none (no code changed beyond the PR's own)
surface_delta: 0
-->

COMMON_RULES_W128 first line, quoted: "# Wave 128 common rules".

## Premise conflict (operator chose: land as-is, no rerun)
Block said the judged seasons were never read and Part 0 was code + known-answer test only. PR #555's branch already held the W124.5 judged run
(RESULT.md, results.json, trait_reliability_draft.json). PREREG says run once, so no rerun. Operator picked "land as-is, no rerun" in chat 2026-11-24.

## Result
- PREREG frozen at 16fcd204 (file untouched). Verdict SUPPORTED: pooled D +0.00201 [+0.00184, +0.00219], 4 of 4 stats, BH q 0.10 all.
- Gain 0.0103 at 4-10 prior games, 0.0001 at 31+. Gross calibration, no costs. Not an edge claim.
- Modal outcome: 3 of 4 parts matched (assists not among the largest).
- Part B: trait_reliability_draft.json stands; C2 taking shrunk rates is a later pre-registration.

## Rebase notes
Conflicts in HYPOTHESIS_DOCTRINE.md (kept main's EXP-047-C1/C2 rows plus the PAM-3 SUPPORTED row), ACTIVE_QUEUE.md (main's side), and generated nav files (main's side).

## Pending
- CI on the PR head; Docs Guard (`guard`) was red on main before this PR. Merge only on green of the current head.
