# PREREG — EXP-047-C2: stat-specific absorption of an Out player's usage on NBA props (W126.2)

**Last reviewed:** 2026-11-24. **Frozen before any stat outcome is read.** Read so far: schemas, file counts, date ranges, the C1
PREREG / RESULT / code. Any change after the first fitted or scored row is a new pre-registration, not an edit.
Binds to DOCTRINE §1, ADR-0075, ADR-0077, HYPOTHESIS_DOCTRINE, COMMON_RULES_W126. Shadow only: Kelly 0, no capital, orders follow v1.
Measure moved: DEPTH D1 (personnel on the NBA props arm) and D3 (+1 challenger). Backlog B-116, GG-2003.

## 0. Premise correction (stated, not hidden)
The block text says C1 "moved every stat with one points-share rule". The code did not: `NBAEnginePropsC1._mu` redistributes each stat's
**own** per-player mean (`redistribute(base[s], p)` for s in points / rebounds / assists / threes), so rebounds already moved by rebound
share. What C1 assumed is **full absorption**: every vacated unit of the stat lands on active teammates (team total preserved).
That is right for points (the team's points are fixed by the simulated game, so shares renormalise) and is the untested part for the
other three. C2 therefore tests one thing: a **fitted absorption fraction per stat**. Points is C1's path, unchanged (see 2).

## 1. Hypothesis (one test; closed individually if it loses)
**EXP-047-C2**: pricing NBA props with a per-stat absorption fraction lambda_s fitted on a fit season (rebounds, assists, three-point
**attempts**) plus C1's full-absorption rule for points prices NBA props better than EXP-047's plain trailing average, on a season no
earlier test scored. A loss closes this hypothesis only ("hypothesis closed (EXP-047-C2, parked for R&D)"); no cell, market or arm closes.

## 2. The rule — one place (`nba_engine/usage_redistribution.py`)
For a team with prior-mean weights w_i of a stat, play probability p_i (0 if listed Out at the pre-tip cutoff, else 1; same as C1),
f = sum(w) / sum(w p) (the C1 factor), lambda in [0, 1]:
**w_i' = w_i p_i (1 + lambda (f - 1))**. Active total becomes W_act + lambda * (vacated). lambda = 1 is C1 (taken through C1's own
`redistribute`, so it is equal to the bit); lambda = 0 is "Out players dropped, nothing absorbed". Nobody Out: input returned unchanged, bit for bit.
- **points:** lambda = 1 (not fitted). The points total is the simulated team score, so any lambda gives the same shares; C2 points == C1 points.
- **rebounds, assists:** own-stat mean weights, lambda_reb, lambda_ast fitted (3).
- **threes:** the weight is the player's mean three-point **attempts** (3PA). Attempts are absorbed by the rule above with lambda_3pa;
  makes are re-derived per player at his own prior make rate r_i = mean 3PM / mean 3PA: mu3_i' = r_i * 3PA_i'. (3PA = 0 or nobody Out -> unchanged.)
- The game-line path is untouched: `missing_usage` / `usage_missing` / `creator_out` stay bit-identical (existing test) and `redistribute` is not edited.

## 3. Fit (fit season only; frozen before the judged season is scored)
Fit season: **2022-23** (season label 2023) — the only season the fit may read. For each fit-season team-game with a usable pre-tip report
(same cutoff as C1: last slot at least 240 min before earliest tip), >= 5 prior-rotation players (EXP-047 roster) and V > 0:
W_act = sum of prior means of rotation players not listed Out who played; A = their actual stat total; e = A - W_act; vac = sum of prior
means of listed-Out rotation players. b0 = mean e over fit-season team-games with nobody Out (baseline drift, so pace noise is not absorbed).
**lambda_s = clip( sum[(e - b0) * vac] / sum[vac^2], 0, 1 )** over V > 0 games (origin OLS slope), rounded to 2 decimals, then frozen in
`FIT_C2.json` (committed before 2023-24 is scored) and hashed into the model SHA. Stat basis: rebounds, assists, 3PA. The C1 data are
**descriptive background only**: nothing from the 2024-25 / 2025-26 judge window of C1 is read, fitted or scored here.

## 4. Judged populations
1. **Retrospective: season 2023-24 (regular season, game dates 2023-08-01 .. 2024-07-31).** Why it is unread: C1 built rows for the fit window
   but scored only games on/after 2024-10-01; its only reads of 2022-23 / 2023-24 were counts (P(played | listed Out)). W93.1 used 2023-24
   to estimate play rates and scored game margins, never player-prop stats. No test has scored a prop price on it.
   Same ladder as C1 (points {10,15,20,25,30}; rebounds {4,6,8,10,12}; assists {2,4,6,8,10}; threes {1,2,3,4}), same EXP-047 priors
   (as-of strictly earlier games, within season), same draw counts and sha-keyed seeds, same exclusions (DNP-after-active dropped from all
   arms). Reported as a count: games with no pre-tip report.
2. **Forward: 2026-27 rows from the date of the commit that freezes this file**, logged as candidate map `nba_props_c2` beside EXP-047
   (and C1), scored by the router per leaf on net after costs per arm (ADR-0077). The retrospective ladder has no prices, so net is forward only.

## 5. Verdict rule (set before outcomes)
Population: judged player-rows on teams with V > 0. Per stat, paired mean log-loss difference d = LL(C2) - LL(EXP-047) over (player, k) rows,
**game-clustered bootstrap, 10,000 draws, 95% interval**; improves if upper < 0, worse if lower > 0, else indeterminate; BH q = 0.10 across
four stats. **Verdict:** SUPPORTED if at least one stat improves (BH-significant) and none is worse; REFUTED if any stat is worse and none improves;
otherwise INDETERMINATE. Secondary, reported not gating: C2 vs C1 per stat on the same rows; the V buckets (< 0.10, 0.10-0.25, >= 0.25 on the
points basis, as C1); Brier; gross, round-cost and net stay forward-only. Gross / cost / net side by side applies when the router scores
the forward rows (Section 4.2).

## 6. Modal outcome (stated in advance)
Points improves again (same rule as C1, new season; replication). The fitted lambdas come out below 1 for rebounds and assists (about
0.4-0.8) and nearer 1 for 3PA. C2 closes most of C1's loss on those three stats: rebounds and assists indeterminate or slightly worse,
threes indeterminate. Verdict most likely SUPPORTED on points only, with INDETERMINATE the close second. A stat that stays worse
(rebounds is the likeliest, because position/role matters and no position data enters) would make the verdict REFUTED, and is
reported plainly. If lambda_s clips to 1 or 0 for a stat, that is a finding about the stat, not a failure.

## 7. Forward and activation
Candidate map logged behind `PM_PROPS_C2` (default **off**), own model id and SHA-256, same seeds. Activation is a dated proposal line
(Hard Rule 14 surface check in the handoff); the window activates shadow logging (plumbing). Nothing is installed; no frozen PREREG,
hash, leaf map, cron line or kelly_fraction changes.

## 8. Known limits
- Out is a pre-tip report; late scratches are not modelled (p = 1). Position/role is not an input, so a big out does not feed other bigs first.
- Priors reset each season (within-season, as C1's retro), so the first games of 2023-24 drop out of both arms identically.
- Log-loss against realised outcomes on a fixed ladder is calibration, not an edge claim against prices.
- One fit season (2022-23) gives noisy lambdas; the fit reports their bootstrap interval, but the frozen value is the point estimate.
