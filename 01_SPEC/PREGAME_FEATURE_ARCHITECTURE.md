# Pre-Game Feature Architecture — Inventory, Target by Factor Class, Build Order

**Status:** SPEC — PROPOSES, does not authorize. Nothing here builds, trains, wires, schedules or sizes anything.
**Date:** 2026-09-30 · **Task:** T-591 (wave 40.x) · **Decisions logged:** n/a (no strategic decision made; findings for later registration are in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T591_pregame_feature_architecture.md`)
**Why this horizon first:** ADR-0068 (PROPOSED; landed on main as `ae49434`) D1/D5 — the longer the decision horizon, the deeper the tree may be; the widest horizon (pre-game, T1, 12–48h) is where matchup/sport/player/team/external/qualitative structure can actually be piped in and where evidence accrues at a countable rate (one resolved row per game, roughly independent across games). Build the deep tree here, then carry granularity inward. ADR-0068 is PROPOSED, so that authority is itself pending DS sign-off.
**Costing source (not re-derived):** `T586_absent_attribute_pricing.md` (attribute IDs N1–N10, M1–M9, tiers, backfill). **Model/feature inventory sources (not re-derived):** `T575_feature_space_audit_RESULTS.md`, `T588_evidence_boundary_2026-09-30.md`, `T554_nstar_wall_analysis.md`, `T581_exp027_epa_splits_results.md`. Every code citation below was read in this session from the T-591 worktree.

Conventions: **[Assumption]** = a claim with no source in the repo or a verified external document. **[UNVERIFIED]** = inherited from T-586 as unverified. **Judgement** = an ordinal rating by the author, not a measurement.

---

## 1. Present-tense inventory (what is consumed today)

Definition used: a feature is *consumed* only if a run path passes it into a `predict_proba`/model fit that can produce an order. "Available" and "stored" are weaker and are listed separately.

### 1.1 NFL (the only sport in season; ~14 weeks left)

Market families in the registry: `KXNFLGAME` (moneyline), `KXNFLSPREAD`, `KXNFLTOTAL`, `KXNFLTEAMTOTAL` (`c5_execution/market_type_registry.py:124-127`; run path series list `run_t1_nfl_game_market.py:125`).

| Feature | Stored where | History depth | Consumed by |
|---|---|---|---|
| `off_epa` (= passing_epa + rushing_epa, per team-game) → recency-weighted `off_epa`, `def_epa_allowed` (window 8, min_periods 3, decay 0.85) | `NFLTeamStatsStore` (`c1_signal_ingestion/nfl_team_stats_store.py:43-53,206-236`), populated from nflverse `stats_team_week` via `nfl_ingestion.py` | 2014–2025 coverage per T-581 §1; EXP-027 trains 2015–2024 (`scripts/exp027_hyp012_nfl_moneyline_backtest.py:81`) | **Moneyline only**: `nfl_exp027_adapter.EXP027NFLForecastModel` |
| `home_rest`, `away_rest` (nflverse pre-computed days) | Schedule payload, `nfl_ingestion.py` allowlist (10 schedule columns, `:120-130`) | Same file, all seasons | Moneyline only (same adapter) |
| Model vector = `[off_h, def_h, off_a, def_a, home_rest, away_rest]` (`FEATURES`, `exp027…backtest.py:85-89`); LR + Platt; re-fit at process start, not serialized | in-process | — | `EXP027NFLForecastModel` — **not wired to cron** (adapter docstring: scheduling not authorized) |
| `passing_epa`, `rushing_epa` splits, `get_pass_epa/get_rush_epa/get_def_pass_epa_allowed/get_def_rush_epa_allowed` | Store, opt-in `include_splits` (T-581) | 2014–2025 | **Nothing.** Offline candidate only; ADR-0066 recommends not accepting (Brier Δ −0.0007 [−0.0020, +0.0005]) |
| Everything else in nflverse `games.csv` / `stats_team_week` (weather, QB, coach, referee, sacks, penalties, pace inputs) | **Not stored** — dropped at the allowlist (`nfl_ingestion.py:120-154`) | — | Nothing (T-586 N1–N6) |

Per-family consumption today:

| NFL family | Real forecaster? | Run path | Countable evidence |
|---|---|---|---|
| Moneyline (KXNFLGAME) | Yes, but only when `EXP027NFLForecastModel` is injected into `run_t1_nfl_game_market.main(model=…)` | `run_t1_nfl_game_market.py` (default = `StubNFLForecastModel`, fixed_p 0.55, PROVENANCE says STUB, GG-255) | 22 open + 20 closed MODEL_EVIDENCE rows; 802 rows STUB (T-588) |
| Spread (KXNFLSPREAD) | **No.** Adapter refuses (`predict_proba` → None); only the stub could price it | same | 0 |
| Game total (KXNFLTOTAL) | **No** | same | 0 |
| Team total (KXNFLTEAMTOTAL) | **No** | same | 0 |
| Player prop | **No NFL player-prop cell exists in the registry** (only NFL_MONEYLINE/SPREAD/GAME_TOTAL/TEAM_TOTAL) | — | — |

Claimed-in-docs, consumed-by-no-run-path (NFL): (i) the EPA-split accessors (built, unwired); (ii) `get_opp_runs_scored`-style totals inputs have no NFL analogue at all — NFL totals/spread have no feature consumer of any kind; (iii) Kalshi NFL spread/total/team-total registry cells exist without any model that can populate them.

### 1.2 MLB

| Feature | Stored where | History depth | Consumed by |
|---|---|---|---|
| `ba_l10`, `ba_l10_shrunk` (empirical-Bayes, K=40, prior 0.2512, ADR-0047), `slg_l10`, `obp_l10`, `ops_l10`, `h_l10_mean`, `k_rate_l10`, `bb_rate_l10`, `hr_rate_l10`, `days_rest`, `b2b_flag`, `is_home_game`, `opp_runs_allowed_l10`, `opp_sp_era_l5`, `opp_sp_k9_l5`, `opp_sp_bb9_l5`, `opp_sp_is_known`, `park_factor_hits` | `exp_output/MLB/mlb_feature_matrix.csv` (45 columns; 132,184 batter-game rows, 2024-03-20 → 2026-07-17, measured this session); producers `c2_feature_store/mlb_features.py` (window 10, min_periods 3), `mlb_pitcher_stats_store.py` (`get_era_l5/k9_l5/bb9_l5`), `mlb_team_stats_store.py` (`get_opp_runs_allowed`) | ~2.3 seasons | **Player-prop hits (KXMLBHIT), T1 pregame:** `run_mlb_pregame.py` (LR+Platt, ~12 of these; T-575). `park_factor_hits` was dead until T-578, ADR-0064 still PROPOSED |
| `ba_l10`/`ba_l10_shrunk`, threshold, `h_so_far`, `ab_remaining` | live state | — | T4M-PROJ (in-play; out of scope here; only 4 inputs, T-575) |
| `get_opp_runs_scored()` | `mlb_team_stats_store.py:136` | — | **Nothing in a run path** (only `scripts/exp022_totals_backtest.py`, T-586) |
| Platoon (M1), bullpen (M4), lineup slot pregame (M5), weather (M6), umpire (M8), defence (M7) | not stored | — | Nothing |

| MLB family | Real forecaster? | Run path |
|---|---|---|
| Player prop hits | Yes (T1 pregame LR+Platt; T4M-PROJ in-play) | `run_mlb_pregame.py`; T4 engine |
| Moneyline / run line / game total / team total / F3-F5-F7 | **No.** Default `StubMLBGameMarketForecastModel` (no PROVENANCE → stamps UNKNOWN, T-588); "never ran live" per queue | `run_t1_mlb_game_market.py` |

### 1.3 NBA and NHL
NBA (dark/frozen): the only sport with the 47-feature PRF/PAM v4 qualitative layer (`c2_feature_store/qualitative_amplifier.py`, `qualitative_store.py`; T-575). Player-points only (`KXNBAPTS`). Not portable to NFL/MLB as written **[Assumption: I did not read the amplifier internals this wave; portability judgement rests on T-575's statement that it is wired to NBA only]**. NHL: registry cells exist (`NHL_MONEYLINE/PUCK_LINE/GAME_TOTAL`), **zero source files** (T-575).

### 1.4 Net
Real pre-game consumption today: **NFL moneyline 6 features (not on cron); MLB hit-prop ~12 features.** Every game-market family other than NFL moneyline is unpriced by any real model. This bounds section 3.

---

## 2. Target architecture by factor class

Common entry rule for all classes (keeps the existing math; no parallel scheme): a class contributes either (a) additional columns in the LR design matrix for the family it targets, each entered as **home-minus-away difference** (moneyline/spread) or **sum** (totals) to control feature count, then Platt-recalibrated exactly as ADR-0004; or (b) a pre-model adjustment to an expected-margin/expected-total that feeds a distributional probability. The edge test is unchanged: `model_p > market_implied_probability + vig`. **Market-derived fields (spread_line, total_line, moneyline odds) are never features** (circular; T-586 exclusion). A line may be used only as the *threshold* when converting a predicted margin/total to P(cover)/P(over). Sizing is outside this spec (ADR-0048 zeroed `kelly_fraction`; untouched).

Point-in-time rule (all classes): a feature may enter only if its value was publicly available before the decision time for that row (T1 = 12–48h pre-start); backfills must be built from as-of data, not final data. Injuries and inactive lists are the highest leakage risk.

Costs use T-586's tiers verbatim: *Payload field* < *Accessor on existing store* < *New accessor on new store* < *New C1 module* < *New external dependency*.

### 2.1 Team (strength)
- **Contents:** rolling offence/defence efficiency, recent form.
- **NFL features:** `off_epa`, `def_epa_allowed` (consumed today); N5 pace/PROE inputs from `stats_team_week`; N6 `def_sacks`, `def_qb_hits`, `sacks_suffered`, penalties. **MLB:** `slg_l10`/`ops_l10`/`hr_rate_l10`, `opp_runs_allowed_l10`; add M4 bullpen aggregates.
- **Source/tier/backfill:** N5 raw rates and N6 = Payload field, deep (same file; coverage start to confirm per T-586); PROE proper = new accessor on pbp. M4 = new accessor on existing store, deep aggregates.
- **Enters the estimate:** LR difference columns (NFL sides); sum columns for totals; for spread, margin regression below.

### 2.2 Player
- **Contents:** identity-level availability and quality, dominated in NFL by the starting QB.
- **Features:** N2 starting-QB identity and QB-change flag (`games.csv` `home_qb_id/away_qb_id`; Payload field; deep). Encoding: (i) `qb_change` binary = starter differs from team's previous-game starter; (ii) QB-specific rolling EPA/play needs a per-QB table **[Assumption: not in T-586's costing; requires a QB-level nflverse player-stats source, unpriced]** — until priced, only (i) is admitted. MLB: M3 opposing-pitcher quality beyond ERA/K9/BB9 (accessor on existing store), M1 platoon (batter side × pitcher hand; new accessor, terms UNVERIFIED), M5 lineup slot (pregame via existing `fetch_lineups`; history depth UNVERIFIED, Retrosheet M9 as backfill).
- **Enters the estimate:** `qb_change` as a signed difference column; adjusts the team-EPA columns which lag a swap. MLB: additional columns in the KXMLBHIT LR; platoon as `1[opposite-handed]`.

### 2.3 Matchup
- **Contents:** interactions, not levels: offence-vs-defence facet pairing.
- **Features:** NFL `off_pass_epa_h − def_pass_epa_allowed_a` and the rush analogue (accessors already exist, T-581) — tested and **no detectable improvement** (ADR-0066), so this class is *tested-null in its cheapest form*; N10 OL/DL (nextgen/PFR; New C1 module; 2016+/2018+); N9 formation/coverage (CC-BY-SA, new C1 module, **not available in-season for 2023+ participation**). MLB M1 platoon is the matchup feature.
- **Enters the estimate:** interaction columns in the LR. Because T-581 found null for the pass/rush split, no further NFL matchup class is proposed for this season's build.

### 2.4 External (venue, weather, travel, rest)
- **Features:** N1 `temp`, `wind`, `roof`, `surface` (Payload field, already downloaded and dropped; deep; backtestable). Encoding: `wind_eff = wind if roof ∈ {outdoors, open} else 0`, `temp_eff` analogous, plus `dome` binary. N7 travel (timezone shift, distance; new accessor; needs a stadium-coordinate table **[Assumption: table not in repo]**). Rest (consumed). MLB: `park_factor_hits` (built, ADR-0064 pending), M6 weather (new external dependency or payload if feed carries it; Open-Meteo free tier is non-commercial — do not use commercially, T-586).
- **Enters the estimate:** mainly **totals** (wind/cold shift expected total; T-586 says weak for sides). Totals model: `E[total] = a + b1·(off_h + def_a) + b2·(off_a + def_h) + c·wind_eff + d·temp_eff + e·pace`, fitted by OLS on 2015–2024; P(over line) = 1 − Φ((line − E[total]) / σ̂), σ̂ = residual SD from training data (**estimated, not assumed**). Weather adds to sides only as LR columns and is expected to be near-null.

### 2.5 Sport (structural priors)
- **Contents:** league-level constants that change by sport, not by game: home-field advantage, scoring scale, score variance, season-phase effects, overtime rules.
- **Features:** home advantage as the LR intercept plus `is_home`; NFL league-mean points and margin SD estimated from the training seasons; MLB run environment by season. Source: same `games.csv` scores (Payload; deep). Enters as fitted constants (intercept, σ̂), re-fit at model build only (frozen-model policy, Hard Rule 4).
- **Note:** this class is where "new sport = new C1 + C2 + C3" (CLAUDE.md) is concretely met; NHL has none of it.

### 2.6 Qualitative
- **Rule:** admitted only if it can be reduced to a bounded machine value with a stated encoding and an as-of timestamp. Free text, analyst opinion, "momentum", coach quotes and narrative are **kept out**.
- **Encodable today (source identified):**
  1. Injury-report status per key position group — nflverse `injuries` (since 2009; **New accessor on new store**, N8). Encoding: ordinal 0 = active/no designation, 1 = Questionable, 2 = Doubtful, 3 = Out, per starter slot (QB, and an aggregate count for OL/DL/WR/CB), recorded at the last report before decision time. Point-in-time discipline mandatory.
  2. QB change (2.2) is the highest-value qualitative fact and is already binary.
  3. Coach identity (N3; Payload) as a categorical only if regularised; T-586 rates the mechanism weak.
- **Not encoded (kept out):** the PRF "player quality / role-fit / form" judgement layer for NFL/MLB — no source or encoding exists outside NBA; I did not verify whether the NBA encoding could be re-sourced **[Assumption]**. Sentiment/news feeds have no identified source and no verified terms — omitted.
- **Enters the estimate:** as numeric LR columns, never as a post-hoc override of `model_p`.

---

## 3. Build order

### 3.1 Ranking method (stated before applying)
`score = information-gain rating / integration-cost points`.
- **Information-gain rating (1–3, Judgement, not measured):** 3 = plausibly moves moneyline/spread probabilities by a decision-relevant amount; 2 = moves totals or a subset; 1 = marginal or largely priced by existing features. Ratings follow T-586's mechanism notes, not new measurement. The one measured datum is T-581: splits (already-cheap, rating would have been 2) returned null, which lowers my prior for team-efficiency variants generally.
- **Integration cost points (from T-586's tiers, no parallel scheme):** Payload field = 1; accessor on existing store = 2; new accessor on new store = 3; new C1 module = 5; new external dependency = 8. Add +1 if point-in-time leakage risk is high (injuries, lineups). Backfill depth gates *testability*, not score.
- Tie-break: testability against the NFL remainder.

### 3.2 Applied — NFL (family: moneyline first, then totals)
| Rank | Attribute | Gain | Cost | Score | Testable in NFL remainder? |
|---|---|---|---|---|---|
| 1 | N2 QB change | 3 | 1 | 3.00 | Backtest yes (deep); forward rows: yes, see 3.5 |
| 2 | N1 weather (totals mainly) | 2 | 1 | 2.00 | Backtest yes; forward scoring needs a totals forecaster |
| 2 | N6 sack/pressure/penalty | 2 | 1 | 2.00 | Backtest yes |
| 2 | N5 pace/pass-rate raw | 2 | 1 | 2.00 | Backtest yes |
| 5 | N3/N4 coach, referee | 1 | 1 | 1.00 | Backtest yes (T-586 rates the mechanism weak) |
| 6 | N8 injuries | 2 | 3+1 = 4 | 0.50 | Backtest yes with as-of care; forward yes |
| 7 | N9/N10 scheme, NGS/PFR | 2 | 5 | 0.40 | N9 not in-season for 2023+; **waits** |
| 8 | N7 travel | 1 | 2+1 (stadium table unsourced) = 3 | 0.33 | Backtest yes once a table exists |

T-586's own ranking (N2, N1, N6, N5, N8, N7, N4/N3, N9/N10) is broadly consistent; this method places N3/N4 above N8/N7/N9/N10 because they are near-free, the one disagreement, and it rests on a Judgement gain of 1.

### 3.3 Applied — MLB (waits for March 2027 or a non-running season)
M1 platoon (gain 3, cost 2 → 1.50), M3 opposing-pitcher (3/2 → 1.50; data already ingested), M2 park factor (2/1, built; gated by ADR-0064), M5 lineup slot (2/2+1 → 0.67), M4 bullpen (2/2 → 1.00), M6 weather (1/8 → 0.13), M8 umpire (1/5 → 0.20), M7 defence (1/5 → 0.20). **Buildable offline now** (backfill on the 2024–2026 matrix or Retrosheet) but **not forward-testable until MLB resumes**; nothing in (b) is scored against live rows before then. Terms for MLB Stats API and Statcast are UNVERIFIED (T-586); do not commit to them.

### 3.4 (a) vs (b) split
- **(a) Buildable and testable against the remaining NFL season:** N2, N1, N6, N5 (all Payload-tier), then N8 — as offline backtests on 2015–2025 with the T-581 protocol (season holdout, rolling origin, bootstrap Δ CI), and as forward *shadow* rows on the NFL moneyline once a model is running. Spread/total forecasters would have to exist first; none does (section 1.1).
- **(b) Waits:** all MLB attributes (M1–M9); NFL N9/N10; N7 until a stadium table is sourced; any qualitative class beyond QB-change and injury status.

### 3.5 Can the NFL remainder clear n*? — No.
Arithmetic (sources: T-554 §cadence, T-588 census, T-581):
- NFL 2026: 272 regular-season games over 18 weeks (T-554). Weeks 1–4 are done (today 2026-09-29); ≈ 4 × 15–16 = 60–64 played. Remaining regular season ≈ 272 − ~62 ≈ **~210 games**, plus the postseason (~13 games) ≈ **~223 games**.
- Only NFL moneyline has a real model, and only when the adapter is injected (not scheduled). At T-554's observed clean rate 0.875: ≈ 0.875 × 223 ≈ **~195 new resolved, countable rows**; add the 20 already closed → **~215 by the end of the season**. Even at a 100% clean rate: ~243. **[Assumption: the 0.875 clean rate from one resolved week persists; the Week-1 sample was n=16.]**
- **EXP-027 n\* = 2,610.35** (T-554; variance-derived, APR-0024). **~215 / 2,610 ≈ 8%.** It does not clear, by roughly a factor of 12. T-554 already projects ≈ 11 NFL seasons at ~13.2 clean games/week; nothing buildable this season changes that cadence, because each game yields one row.
- Adding spread/total/team-total rows does not help: they have no forecaster, so under the evidence predicate they would be STUB or unattributed, not countable. Pre-registered multipliers (more contracts per game) are not a substitute; rows within a game are correlated **[Assumption, standard for same-event contracts]**.
- What the remainder *can* support: a Brier/ECE read. T-581's holdout at n=284 has a paired-Brier 95% half-width of ≈ 0.00125; scaling by 1/√n, at n≈215 the half-width is ≈ 0.0014 (derived here). **That is larger than every Brier difference measured so far** (−0.0007 for splits), so the remainder cannot resolve a candidate improvement of that size on forward data either; it can detect only a large effect. Backtest seasons (2015–2025) are the only place a candidate feature can be tested with adequate n, which is why section 3.4(a) is framed as offline backtests.
- **Decision-grade note for APR-0035 (open):** the NFL remainder is underpowered for the P&L gate by ~12×; only backtest-based feature evaluation is feasible this season, and the forward-evidence gate cannot close in 2026 on any feature set.

---

## 4. Encoding rules (summary)
1. Numeric only; ordinal categories mapped to integers with a stated table; missing = NaN, imputed by the training-set median (as `_impute` in `exp027…backtest.py:361`) plus a `*_is_known` indicator, following the `opp_sp_is_known` precedent.
2. Home-minus-away for sides, sum for totals; do not add raw home and away columns when a difference carries the signal.
3. As-of timestamping: every stored row carries the availability time; backfills reconstruct that time or exclude the feature.
4. Frozen model: features are fixed at build; no automated retraining (Hard Rule 4).
5. Provenance: every model carries `PROVENANCE`; a family without one stamps UNKNOWN and is not countable evidence (GG-317/318).
6. No market-derived field as a feature.

## 5. Open questions
1. NFL spread/total/team-total: who authorises a forecaster, and does a margin/total model warrant its own pre-registration? (Out of this spec's scope.)
2. Should APR-0035 be judged on a calibration/Brier gate rather than P&L n\*? (T-554 raises it; not decided here.)
3. QB-level quality (not just QB change): which nflverse source, and at what cost? Unpriced.
4. Stadium coordinate table for travel: which source? Unsourced.
5. nflverse licence mismatch (CC-BY-4.0 vs MIT in the code docstring) and CC-BY-SA for N9/N10 (T-586 §6) — needs an owner before N9/N10.
6. MLB Stats API and Statcast commercial terms: UNVERIFIED.
7. Whether "Kalshi's NFL closing archive covers 2026 only" (T-581 §4) limits market-relative testing of any new feature to ~50 games this season.

## 6. Assumptions (consolidated)
- A1: 0.875 clean rate persists (n=16 week).
- A2: Same-event contracts are correlated; extra contracts per game do not add independent evidence.
- A3: NBA PRF layer is not portable (internals unread this wave).
- A4: A stadium-coordinate table and a QB-level quality table are not in the repo and are unpriced.
- A5: Information-gain ratings are Judgement, not measurements; a single measured datum (T-581) is null for team-efficiency variants.
- A6: Weeks 1–4 have ~60–64 games played; the exact count should be read from the schedule, not this estimate.
