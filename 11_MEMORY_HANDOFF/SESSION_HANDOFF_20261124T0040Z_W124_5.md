# Session handoff - W124.5 H-DEPTH-PAM-3 run (2026-11-24 00:40 UTC)

<!-- session-meta
task_id: W124.5
tier: MICRO
timestamp: 2026-11-24T00:40:00Z
commit: 05aeb8a
one_line_summary: W124.5 H-DEPTH-PAM-3 judged run on NBA props: SUPPORTED (pooled D +0.00201, 4/4 stats); PR 555 test green
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) class 3 NBA player level, D3
gap_delta: D5(b) class 3 NBA: absent -> interpreted; D3 +1 challenger (12_EXPLORATORY/pam_stability/RESULT.md @ 05aeb8a)
pattern_sweep: grep write_text( in 12_EXPLORATORY/ -> only run_pam3.py bypassed _fence.safe_out, fixed 12b54cc
surface_delta: 0
-->

COMMON_RULES_W124 first line, quoted: "# Wave 124 common rules".

## Result
- Verdict **SUPPORTED** (PREREG 16fcd204d5e41995c761d8e3d27b71c121024620 + PREREG_ADDENDUM_1, committed 743a7e1 before any judged row was read).
- Pooled D (log-loss control - challenger) +0.00201, 90% game-clustered [+0.00184, +0.00219]; 4 of 4 stats positive, all BH q 0.10.
- Gain by prior games: 4-10 +0.0103, 11-30 +0.0013, 31+ +0.0001. ~92% is the shrunk rate; shrunk minutes add little.
- Gross calibration only (no price, spread or fee). A tighter interval is not an edge.
- Modal outcome: 3 of 4 parts matched; assists was not among the largest (threes was).
- Routing consequence: licenses an EXP-047 challenger with its own pre-registration in a later wave; not applied until the router scores it per leaf on net after costs.
- Files: 12_EXPLORATORY/pam_stability/{RESULT.md,results.json,run_pam3.py,PREREG_ADDENDUM_1.md,trait_reliability_draft.json}; tests/test_pam3_known_answer.py.

## Part A data (regular season, minutes > 0 rows; store exp_output/NBA_EVENTS, git-ignored)
2016 26071 | 2017 26135 | 2018 26099 | 2019 26095 | 2020 22387 | 2021 23053 | 2022 26035 | 2023 25892 | 2024 26393 | 2025 26302.
Columns: minutes (MM:SS parsed), points, rebounds_total, assists, three_pointers_made, blocks, steals, free_throws_made, free_throws_attempted,
person_id, team_id, game_id, season_type_id; game_date from the schedule table. 2026 downloaded by the store CLI, never loaded.

## Measure moved
DEPTH D5(b) class 3, NBA player level: absent -> interpreted (reliability table + supported test). D3: +1 challenger (shrunk-mean props mu), pre-registration still to write.
Source: 12_EXPLORATORY/pam_stability/RESULT.md. D6 / execution / proof unchanged.

## Notes the next window needs
- local_helpers: `game_bootstrap` in run_pam3.py (numpy, same algorithm as quant.inference.cluster_bootstrap, which is a per-row loop, ~1e9 ops here). Library `mde_paired` and the BH idea are used; BH is a 4-line local copy on one-sided bootstrap p-values.
- PREREG gaps filled in the addendum before the run (A1-A9). A4: "raw rate x raw minutes" is identical to the control, reported as an identity check plus two partial arms.
- Dev smoke on training seasons only (train 2016-20, check 2021-22) was run to test the loader; nothing was tuned from it. results.json got two metadata keys (prereg_sha, addendum) after the run; no numbers edited.
- CI: `guard` job (Docs Guard, gaps-by-arm index --check) is red on main at every recent commit, not from this PR. Regeneration belongs to whoever owns the gap log. Registered as a defect outside scope; no GG written (needs the gap-log owner).
- ACTIVE_QUEUE 124.5 row updated inside the PR, not as a separate docs-only push.

directive_conflicts: none found (read-only research code, no live path).
surface_delta: 0 (no cron, service, workflow or box change; one test file, one exploratory script).
pattern_sweep: exploratory-write fence checked (tests/test_exploratory_isolation.py caught a bare write_text; fixed to safe_out); grep of 12_EXPLORATORY for other write_text uses outside this block not done (out of scope).
Hard limits / Kelly: untouched. No real capital.

## Close-out
- Strategic decisions: none (verdict only; no threshold or doctrine change).
- One thing pending: operator go-ahead to merge PR 555. `test` green; `guard` red on `generate_gap_arm_index.py --check`, which fails on main too (pre-existing, not this PR).
- Resume: read 12_EXPLORATORY/pam_stability/RESULT.md; next is a pre-registered EXP-047 challenger (shrunk mu) in a later wave.
