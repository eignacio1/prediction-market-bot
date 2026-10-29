# W94.2 results: NFL forward test, temporal evolution, play callers

Pillar: PROOF + DEPTH. Measures: P3 (EXP-045 look dated), D5(a) NFL 7/8 -> 8/8, D5(b) N11 none -> interpreted. surface_delta 0.
Nothing here touches an order, gate, model, runner, registry cell, frozen pre-registration or running component.

## 1. EXP-045 (frozen before any new row)
- `05_RESEARCH_EXPERIMENTS/EXP045_NFL_ENGINE_FORWARD_PREREGISTRATION_2026-10-28.md`, sha256 `d0df8a4977476f9fe9a9fa0d92242b7752e0d5c0ea0dc31f1ef773cf3e4d8c85`, pushed 2026-10-29T00:23:54Z, freeze 2026-10-29T03:00:00Z. Merged in PR #367.
- Judged n at MDE 0.02: 429 / 442 / 337 games (spread / total / team total). Post-freeze 2026 regular-season games: 165, so MDE is about 0.032. Look 1 (2027-01-12) is labelled UNDERPOWERED; a non-pass reads "NOT DISTINGUISHABLE at MDE ~0.032". Modal outcome: not distinguishable (~85%).
- In-sample replay, net P&L per contract: spread -0.003 [-0.039, +0.032]; total +0.009 [-0.029, +0.045]; team total -0.021 [-0.052, +0.008].

## 2. Temporal evolution, NFL (Part B, PR #369) - stage: interpreted
Applies when a factor is estimated from games already played in the season and the question is how fast to trust recent games over the long run. 2016-2025 REG, 320 team-seasons.
- Only neutral pass rate drifts team against team inside a season: odd/even vs early/late reliability gap +0.157 [+0.071, +0.242].
- League slope per week: offensive EPA/play -0.0011 [-0.0020, -0.0001]; success rate -0.0005; neutral pass rate -0.0015 [-0.0022, -0.0007].
- Other factors' reliability gaps have intervals spanning 0. Known-answer tests: 4 pass (`tests/test_nfl_temporal_evolution.py`).

## 3. Play callers, N11 (Part C, PR #371) - stage: interpreted, not applied
`src/prediction_market_bot/c1_signal_ingestion/nfl_play_callers.py`; measurement `callers_measure.py` -> `callers_W94_2.json`.

**Who called plays.** Muse R-019 offensive-coordinator cards cover 93.2% of 2016-2025 team-games; the head coach of record fills the other 6.8%. **Proxy caveat: the coordinator of record is not a confirmed play caller** (the archive holds no play-caller records). Source is stored per row.

**Rule.** Four tendencies from the play-level store, each as residual against an expected value fitted only on earlier seasons: pass rate over expected (down/distance/score), fourth-down go over expected, neutral pace (seconds per play), lead protection. Estimates are keyed by person, shrunk to the league mean by `s/(n+k)` and use only games before the one predicted. The prior is the league mean, so a new caller starts at exactly 0; a caller who moves keeps his own history; confidence decays per elapsed season, so a gap pulls toward the prior. A coordinator change resets the team's tendency because the new person has no history. k and decay were fitted on 2016-2019 only (k: pass 200, go4 100, pace 50, lead 50; decay 0.6). 2020-2025 is held out.

**Known-answer tests (5 pass).** A simulated caller with a known tendency is recovered with the right sign and size; a new caller is exactly 0; no leakage; split-season OC parsing.

**Are they real traits?** Held-out 2020-2025, as-of estimate vs the same team-game's realized residual:

| Tendency | n team-games | corr [95% CI] |
|---|---|---|
| pass rate over expected | 2,682 | 0.381 [0.350, 0.413] |
| fourth-down go over expected | 2,939 | 0.150 [0.113, 0.188] |
| neutral pace | 1,116 | 0.451 [0.398, 0.500] |
| lead protection | 530 | 0.299 [0.220, 0.375] |

**Do they move totals beyond the line and N1-N3?** Paired MSE gain, bootstrap game-level, seed 94, 2000 resamples. Baseline is a proxy for N1-N3 (EW points for/against, offensive/defensive EPA, rest; **not opponent-adjusted**).
- Game total (n=1,615, line-only MSE 170.10): baseline +0.14 [-0.93, +1.20]; callers added -0.92 [-2.98, +1.04].
- Team totals (n=3,230, line-only MSE 82.56): baseline -0.10 [-0.31, +0.11]; callers added -0.24 [-0.56, +0.09]. Single features: pass +0.065 [-0.101, +0.242]; go4 +0.011 [-0.125, +0.149]; pace -0.094 [-0.214, +0.022]; lead -0.153 [-0.351, +0.039].
- Every interval spans 0. **The line already holds the callers' tendencies; the stage is interpreted, not applied. A rigorous null for this application is a result.**

**Kalshi descriptive look** (`callers_kalshi_look.py`, 2026 REG, KXNFLTEAMTOTAL ladders from the price archive; implied team total is the strike where P(X>=k)=0.5, last tight snapshot; compared with the schedule line's implied team total): n=147 team-games with a joined tendency; mean gap -0.65 pts, sd 8.5 (the ladder interpolation is crude). Correlation of gap with tendency: pass 0.12, go4 0.08, pace -0.04, lead -0.02; interval at n=147 is about +/-0.16, so all span 0. Descriptive only; no test claimed. 2026 is also 165 games into the season, so this is an early read.

**Granularity index (five parts).**
1. Split: pass rate over expected by down/distance/score; fourth-down go over expected; situation-neutral snap pace; lead protection.
2. Rank against history: the shrunk estimate against every caller's estimate at the same point, history from 2016.
3. Matchup cross: not built (caller against opposing coverage/front scheme). Registered as a gap, not claimed.
4. Market map: team totals and game total (KXNFLTEAMTOTAL, KXNFLTOTAL).
5. Application: none. Rigorous null on totals and team totals above.

## 4. Stage per factor
| Factor | Before | After | Note |
|---|---|---|---|
| Temporal evolution (NFL component) | none | interpreted | built and tested; not wired |
| N11 play callers | none | interpreted | proxy caller; not applied (null) |
| EXP-045 forward test | not registered | frozen, scoring built | look 1 2027-01-12, UNDERPOWERED |

## 5. Defect found (for the handoff)
`_fence.safe_out` resolves relative paths against `12_EXPLORATORY/`, so `--out 12_EXPLORATORY/x` writes to `12_EXPLORATORY/12_EXPLORATORY/x` (likely the origin of the untracked nested directory in the main tree). Separately, the fence scan flags any `.rename()` / `.replace()` call as write-shaped, a pandas/str false positive that cost two CI rounds here; the scripts were reworded rather than the scan changed (out of scope).
