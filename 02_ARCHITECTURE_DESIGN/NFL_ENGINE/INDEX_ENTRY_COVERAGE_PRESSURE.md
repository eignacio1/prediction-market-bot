# Index entry: defensive coverage and pressure tendency × the QB's production against it — W82.3

Run: `12_EXPLORATORY/nfl_engine/coverage_gap/` (`part_a.py`, `part_b.py`; full numbers in `results.md`). Data: nflverse pbp + participation (2016–2025; coverage and pressure fill ≥0.996 from 2023) + FTN blitzers (2022+). No 2026 participation file exists (GG-730), so 2026 values cannot be recomputed point-in-time. Muse's 2026 values are not comparable to the bot's definitions.

**Stage reached: interpreted — trait confirmed; no gain beyond the frozen KXNFLPASSYDS model at current sample sizes.**

## 1. Split
Man vs zone (share of classified coverage), pressure (`was_pressure`), 5+ rusher blitz, each per defense-game over QB dropbacks; QB EPA/dropback vs man, zone, pressured and clean.

## 2. Rank against history
2025 defense-seasons ranked against 160+ team-seasons since 2018: top pressure rates CLE 0.349 (95th pct), DEN 0.345, TB 0.345; top man share DEN 0.446 (80th pct), PHI 0.436, CHI 0.417. Stability, split-half at six games: man share r 0.79 [0.74, 0.84], 5+ rushers 0.64 [0.57, 0.71], pressure 0.31 [0.20, 0.42]. All TRAIT. Year-to-year (league shift removed): 0.53 / 0.55 / 0.32.

## 3. Matchup cross
Defense deviation × QB response gap, both shrunk with fixed pseudo-counts, point-in-time. sd(d_man) 0.0046, sd(d_press) 0.0021 (small: the QB-response deviations shrink hard at 150 dropbacks per side).

## 4. Market map
KXNFLPASSYDS strike ladder (T1 pre-game) first; KXNFLTEAMTOTAL, KXNFLSPREAD and KXNFLTOTAL by way of team passing.

## 5. Application (residual of the frozen passyds_strike_v1, read-only)
n = 1,060 QB-games (559 games), 2024–25 held out. Slope of residual yards per sd of d: d_man −2.6 [−7.2, +1.5]; d_press −0.3 [−4.1, +3.7]. Not supported. Not tested against a Kalshi price.

## Operator question — how would a bet be placed pre-game?
1. Compute the defense's shrunk man/pressure deviation and the QB's response gap; the cross is d. 2. Convert d into a shift of the QB's expected passing yards (uncalibrated; measured effect today is zero). 3. Re-price the KXNFLPASSYDS ladder and compare with the market. 4. Size only through a registered cell (none; kelly_fraction 0).

## Mid-game (design only)
Coverage is a per-play fact; in-play it becomes a running tendency update. No free live participation feed exists; FTN and participation are post-game. Nothing built.

## Result
The operator's pattern ("man-heavy defense × QB who struggles against man") is now a measured, trait-gated feature with a tested path to the passing-yards residual; it does not yet move predictions. Muse side: no class VERIFIED; time to throw FAILED on level; coverage/pressure ungradeable until Muse supplies prior-season values or a play-level 2026 source (TO_MUSE R-014).
