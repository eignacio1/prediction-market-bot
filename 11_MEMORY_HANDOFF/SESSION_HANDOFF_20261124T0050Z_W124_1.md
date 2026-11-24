# Handoff W124.1 — variance tools and the power ledger (Sonnet)
PR #557 merged (2668336). Test job green on the rebased head.

MEASURE MOVED: PROOF P3 — hypotheses with a dated judgeable look, 2 → 9 of 18 covered (power_ledger.json). H-EXEC-2 gets a date only if H-MEAS-1 licenses CLV (R is the 15:00Z game-morning line, not the close, so CLV here is descriptive).

## Built
- src/prediction_market_bot/quant/variance.py: clustered_mean, icc, design_effect, mde_clustered, games_needed, clv, control_variate (theta from first 2/3 of dates), paired_within_cluster, partial_pool (DerSimonian-Laird). tests/test_quant_variance.py: 9 known-answer tests.
- 12_EXPLORATORY/edge_location/power_ledger/: power_ledger.py (CLI --out/--md/--meas/--asof, re-runnable weekly, writes via _fence.safe_out), POWER_LEDGER.md (has RESULT section), power_ledger.json, build_dataset.py, measure_variance_tools.py. tests/test_power_ledger.py.
- HYPOTHESIS_DOCTRINE Part II: "judgeable ~<date>" appended to Consequence cells of measured rows only.

## Measured (archive proxy, 4,566 rows, 372 games; gross / cost / net side by side)
- CLV gross +0.0253 [0.0213, 0.0293], cost 0.0948, net -0.0695 [-0.0730, -0.0660]. Descriptive only.
- design effect: icc 0.114, deff 4.28, n_eff 1,067.
- control variate: theta -0.1136, variance reduction 0.075 (1,021 judged rows / 129 games).
- paired GAME-vs-SPREAD: -0.0061 [-0.0086, -0.0036], 188 games, variance reduction 0.0105.
- partial pool: tau 0.009, I2 0.96.

## Dated looks
NBA props ~2027-01-28 (234 games) · NFL props ~2028-02-09 (next season) · NBA confirmations 2027-01-02 · NFL inactives 2026-12-01 · EXP-W119.3 2027-02-14 · NBA depth best leaf ~2027-05-22. Cited: EXP-045 2027-01-12, EXP-044 2027-02-15, PAM-3 2026-11-23. Undated with reasons: H-ROUTER-2, EXP-W117.1, NBA S3/S5, NHL-1, EXP-NBAPROPS-001, NFL-1. MLB-2027 is relative to opening day (not in repo).

## Caveats
Proxy sds for props (MLB|prop_hit 0.114, cost 0.0322) and the NBA depth leaf (read from two stated numbers as a 90% interval). Props/NFL have 0% game-day 15Z coverage, so no CLV or ICC measured for them. No mixed pre/post-2026-11-06T01:03:42Z demo-fill data used. W123 held-out third not re-read.

## Deploy / t4-mlb decision
No deploy.yml run fired for 2668336 (last deploy run 2026-10-16), and MLB is idle until 2027, so no t4-mlb restart and no live-game conflict. Decision: none needed.

## CI note
Docs Guard (`generate_gap_arm_index.py --check`) fails on main itself at c9c1549, before this PR; not caused by 124.1 and out of scope (Rule 11). Registered as a finding for the window, not fixed here.

pattern_sweep: grepped src/ scripts/ tests/ 12_EXPLORATORY for other SE/MDE helpers duplicating quant/variance.py; extended quant/ rather than adding a parallel module. All 12_EXPLORATORY writes use _fence.safe_out.
surface_delta: 0 live components (a library, tests, an offline CLI; no cron, service or box change).
directive_conflicts: none found.
vision_pillar: PROOF (P3). gap_measure: P3 hypotheses with dated look. gap_delta: 2 → 9 of 18.
git note: `git fetch` printed "cannot lock ref refs/remotes/origin/main" (stale local ref); `git show origin/main:` still worked and a later fetch succeeded.
