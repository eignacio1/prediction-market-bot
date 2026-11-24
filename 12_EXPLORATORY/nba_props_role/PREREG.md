# PREREG — EXP-047-C1: the lineup-cross usage shift reaches NBA player props (W125.4)

**Last reviewed:** 2026-11-23. **Frozen before any outcome is read.** Only schemas (player_box columns, injury file shape),
file counts and date ranges were read. Any change after the first scored row is a new pre-registration, not an edit.
Binds to DOCTRINE §1, ADR-0075, ADR-0077, COMMON_RULES_W125. Shadow only: Kelly 0, no capital, orders follow v1.
Measure moved: DEPTH D1 (personnel/availability on the NBA props arm) and D5(b) NBA-10 consumers. Backlog B-116, GG-2003.

## 1. Hypothesis (one test, closed individually if it loses)
EXP-047 prices every player at his plain average. When a rotation teammate is listed **Out** at the pre-tip cutoff, his minutes
and usage go to the others. Challenger **EXP-047-C1** takes EXP-047's inputs and redistributes the Out players' expected
minutes and usage to teammates, then prices P(stat >= k) on the ladder. A loss closes this hypothesis only
("hypothesis closed (EXP-047-C1, parked for R&D)"); no cell, market or arm closes.

## 2. The rule — one place, shared with the game-line path
`nba_engine/usage_redistribution.py` holds the single rule. Premise gap, stated: NBA-10 (W110.2) does not redistribute
anything today; it computes team-level `usage_missing = sum(share x (1 - p_play))` and `creator_out` and feeds engine_v3 margin/total
shifts. There is no redistribution rule to copy, so this block defines the parameter-free one:
for a team with usage weights w_i and play probabilities p_i, **active players absorb proportionally**,
`f = sum(w) / sum(w * p)  (= 1/(1 - V), V = sum(w(1-p))/sum(w))`, active weight becomes `w_i * p_i * f`. Team total is preserved.
`usage_missing` is refactored onto the same module (V's numerator), **bit-identical** on the game path (test).
- Props path: p_i = 0 if status is Out, else 1 (Questionable/Probable/Doubtful keep p = 1; no status-rate fit is applied here).
- Applied to the minutes-weighted expectation `mu` of each player for all four stats by the same f (one rule, no per-stat fit).
- No Out in the rotation => f = 1 and the output equals EXP-047's **to the bit** (test). No new fitting on judged data.

## 3. Population, ladder, outcome
- Data: `NBA_EVENTS/raw/player_box` (minutes, points, rebounds_total, assists, three_pointers_made); injury reports
  (`20261012_nba_points_minutes/inj`, `20261013_nba_games_availability/inj2026`; 654 files, 2022-10-18..2026-04-14). Seasons 2022-23..2025-26.
- Pre-tip cutoff: last snapshot slot (11:30/13:30/15:30/17:30/19:30 ET) at least 4 h before earliest tip (`nba_point_in_time`).
  Out = status "Out" at that slot. Games with no usable snapshot are dropped from both arms.
- Rotation and priors: EXP-047's (top 10 by prior minutes, as-of strictly earlier games). A scored player is in the prior rotation,
  not listed Out, and played (minutes > 0). DNP-after-active rows are excluded from both arms identically and their count is reported.
- Fixed ladder (declared now, not Kalshi's, because Kalshi prop markets exist only from 2026-27): points {10,15,20,25,30};
  rebounds {4,6,8,10,12}; assists {2,4,6,8,10}; threes {1,2,3,4}. Outcome = 1[stat >= k] from the box score.
- Both arms use EXP-047's draw count and sha-keyed seeds (game, team, stat), so the only difference is the rule.
- **Split by date:** fit window 2022-23..2023-24 is diagnostics only (reliability P(played | listed Out), counts per bucket);
  nothing in it changes C1. **Judge: games on or after 2024-10-01** (2024-25, 2025-26).

## 4. Verdict rule
Primary population: judged player-rows on teams with V > 0 (at least one prior-rotation teammate Out). Unaffected rows are
identical by construction and are reported only as a count.
Per stat: paired mean log-loss difference d = LL(C1) - LL(EXP-047) over (player, k) rows, **game-clustered bootstrap, 10,000 draws,
95% interval**. Stat verdict: *improves* if upper < 0, *worse* if lower > 0, else *indeterminate*. BH q = 0.10 across the four stats.
**C1 verdict:** SUPPORTED if at least one stat improves (BH-significant) and none is worse; REFUTED if any stat is worse and none improves;
otherwise INDETERMINATE. Cuts reported, not gating: by stat and by vacated-usage bucket V < 0.10 / 0.10-0.25 / >= 0.25 (edges fixed now).
Brier reported second. Net after costs is scored forward only (Section 6), because the retrospective ladder has no prices.

## 5. Modal outcome (stated in advance)
Points improves modestly in the V >= 0.25 bucket (creator out); rebounds and assists are indeterminate; threes indeterminate.
Verdict most likely INDETERMINATE overall or SUPPORTED on points only. A refutation on any stat is possible and would be reported plainly.

## 6. Forward and activation
Logged beside EXP-047 on 2026-27 rows as candidate map `nba_props_role` (own model id and SHA-256, same seeds), behind
`PM_PROPS_C1` (default **off**). The router scores it per leaf on net after costs (ADR-0077). Activation is a dated proposal line in the
queue for the operator; this block does not turn it on. Hard Rule 14 surface check is in the handoff.

## 7. Known limits
- Out is a pre-tip report; late scratches and "Questionable who sits" are not modelled (p = 1), which biases C1 toward under-shifting.
- A synthetic ladder is not the market's ladder; log-loss here measures calibration against outcomes, not edge against prices.
- Survivors-only (players who played) selects toward the easier rows; stated, same for both arms.
