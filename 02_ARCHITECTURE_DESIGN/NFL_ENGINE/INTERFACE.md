# NFL Engine — interface (ADR-0073 stage 1)

**Status:** DRAFT v0, 2026-10-14 (W73.3, T-950). EXPLORATORY scaffold; no production wiring. **Decisions logged:** n/a (no strategic decision; records the contract 73.2 builds to).
**Pillar:** DEPTH · **Measure:** D4 (NFL: whole board priced from one engine — scaffold stage).

## 1. Contract in one line
`GameInputs` (ratings as of kickoff + context) → `simulate(inputs, n, seed)` → `GameSample` (n joint draws of the game) → every market price is a pure function of the sample. **No market has its own model.**

## 2. Inputs — `GameInputs` (everything known strictly before kickoff; TI-01: source dated < as_of)
| Field | v0 source (today) | Richer source (73.2 / Wave 74 fills it) |
|---|---|---|
| `as_of` (tz-aware UTC) | game date | actual pre-kickoff timestamp (band-aware) |
| `home`, `away` | schedule | — |
| `off_pass`, `off_rush` (per team) | **v0: single `off` rating (off EPA/play, EB-shrunk, recency-weighted)** | pass / rush EPA split, adjusted for opponent |
| `def_pass`, `def_rush` (per team) | **v0: single `def` rating** | pass / rush defense, coverage (man/zone), pressure |
| `st` (special teams) | not in v0 (None) | ST EPA, kicker FG% |
| `qb` (starter id + shrunk EPA) | `qb_epa` from the W64.1 recipe (projected starter, k=6) | QB vs coverage, availability from point-in-time injury report |
| `pace` | league constant | team seconds/play, neutral-situation pace |
| `ctx.home`, `ctx.rest_h`, `ctx.rest_a` | schedule | — |
| `ctx.roof`, `ctx.wind`, `ctx.temp` ("weather slot") | **None in v0** | point-in-time forecast at as_of |
| `ctx.officials`, `coach` | None | penalty-rate / 4th-down aggression tendencies |

A field that is `None` means "league average", never a silent drop; the sample records which slots were populated (`GameSample.provenance`).

## 3. Layers (the part that does not change as inputs get richer)
1. **Rating → rates.** `rates(inputs) -> TeamRates{mu_points, n_poss, p_td, p_fg}` per team. v0: mean points from a ridge on the existing features (so the scaffold is compared on EQUAL inputs with the frozen models); later: built bottom-up from unit-level matchup ratings. This is the only layer 73.2 / Wave 74 should need to extend.
2. **Event simulator.** Possession-level Monte Carlo: shared game pace → possessions per team → each possession ends TD / FG / no score → regulation tie goes to an OT module. Output is **integer scores per draw**, so key numbers (3, 7, 10, 14) and ties emerge instead of being assumed away. Drive-level events (possessions, TD/FG counts) are retained in the sample — that is what props and live conditioning will read.
3. **Pricing.** Pure functions of a `GameSample`.

## 4. Output — `GameSample`
Arrays of length `n`: `home_pts`, `away_pts`, `n_poss_h`, `n_poss_a`, `td_h`, `td_a`, `fg_h`, `fg_a`, `went_ot`; plus `provenance` (inputs digest, model id, seed, n). Same seed + same inputs ⇒ identical sample (deterministic).

## 5. Pricing API (all derived from one sample — consistency is by construction and asserted in tests)
- `p_moneyline_home(s)` = P(margin>0) + ½·P(margin=0)
- `p_spread_home_covers(s, k)` = P(margin > k) (half-point k)
- `p_total_over(s, k)`, `p_team_total_over(s, side, k)`
- `p_joint(s, event_a, event_b)` — parlay legs from the **same draws** (the only correlation source; this is ADR-0073 point 3's route into the parlay class)
- later (not v0): player props from the `td/fg` counts + a player-allocation layer.
Invariants asserted per sample: `home_pts+away_pts == total` exactly; ladders monotone in k; `P(ML)=P(cover −0.5)+½P(tie)` exactly; P(team-total pair) sums to game total in every draw.

## 6. What 73.2's data layer must supply
A function `build_inputs(game_id, as_of) -> GameInputs` returning populated fields from the right-hand column of §2, point-in-time, with the populated-slot map. The simulator and pricing do not change when 73.2 lands; only `rates()` consumes new fields, and each new field is a pre-registered, tested addition that must beat the previous engine version on rolling origin (ADR-0073 point 5).

## 7. Honest limits of v0
- Possession-level, not play-level: no play-by-play is ingested here. Per-possession scoring probabilities are scaled from team mean points, so v0 cannot yet *explain* a mean, only reshape the distribution around it.
- Shape parameters (FG:TD ratio, pace dispersion) are league-wide, fitted on training seasons only; see `12_EXPLORATORY/nfl_engine/PLAN.md`.
- The frozen per-family model is **already one coherent bivariate Gaussian** (`pregame_shadow/nfl_model.py`: all four families read from one distribution). The scaffold's claim is therefore not "consistency the per-family models lack" but *shape* (discrete scores, key numbers) and *extensibility* (props/parlays/live from one sample). Results report exactly that.
