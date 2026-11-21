# PAM attribute classes — five classes from the fantasy hotline test (design note)

**Last reviewed:** 2026-11-21 (SW-9). **Purpose (Hard Rule 12):** DEPTH — D5(b) factor classes by stage, D1 factor classes per live
pre-game model. Feeds the PAM (DS-01) bridge into the per-sport engines (ADR-0073 §, ADR-0075 §3).
**Origin:** operator-run test outside the bot. A per-game z-score model (2025-26 per-game stats, top-156 baseline) was set against the
operator's judgment on 9-cat fantasy rosters over five weeks. The model missed every call that depended on context, and caught only one
stable stat-composition fact. **This is design motivation, not evidence for any cell.** The correlations quoted below (block rate r 0.90,
steal rate r 0.69, FT% r 0.81, usage vs steal rate r −0.05) come from the operator's test. They are not measured on our store; the class-3
pre-registration re-measures them on training seasons only.

## 1. What PAM is today (read from the repo 2026-11-21, not from memory)

| Piece | Where | What it holds |
|---|---|---|
| DS-01 spec | `01_SPEC/DATA_REQUIREMENTS.md` § DS-01 | v4 .docx, research input only, "NOT canonical spec" |
| v4 column schema (legacy) | `qualitative_data/pam_v4/SCHEMA.md` | archetype ids (F-100..102), 32 binary modifiers (F-150..181), effective_from / until, backdating |
| Core schema + store (ADR-0075 §3) | `src/prediction_market_bot/pam/schema.py`, `store.py` | `PamRecord`: archetype mix (weighted), modifiers, effective_from / until, `recorded_at` (knowledge time), tier mass / deep, classifier, `confidence`, `supersedes`, `extra`. Append-only JSONL, one read path `as_of(..., known_at=)` |
| NBA taxonomy | `qualitative_data/pam/nba/taxonomy.json` | 15 archetypes (PRF-1..15), 32 modifiers (M-1..32) |
| NBA records | `qualitative_data/pam/nba/records.jsonl` | 100 deep-tier records, all `recorded_at` 2026-05-28 (hindsight for 2025-26) |
| NBA mass tier | `qualitative_data/pam/nba/mass_tier_pit_2026.csv` (19,499 rows), `mass_tier_counts.json` | per player-game, factors met strictly before the game |
| NFL | `qualitative_data/pam/nfl/records.jsonl` (247), taxonomies | WR mass tier (`pam/nfl_wr_mass.py`) |
| MLB, NHL | `taxonomy_v4depth.json` only | no records |
| Consumers | `02_ARCHITECTURE_DESIGN/SEATS/nba.toml` NBA-PAM-1..4; no engine imports `PamStore` (only `scripts/pam_nfl_wr_mass.py`) | PAM-1 / PAM-2 are tree paths in W110.2 (`d_/s_pam_creator`, `d_/s_pam_mod`), **hindsight only** per the seat file |

**The structural finding:** a `PamRecord` is a *classification* — an archetype held over a date range. Four of the five classes are
*state* that changes game to game (who is out, current usage, current minutes). They should not be squeezed into classification records.
They belong in a point-in-time **player state** table that PAM classifications sit beside, with the same `known_at` discipline.

## 2. The five classes against what exists

Stage words per ADR-0075 / ADR-0077: absent · aggregated · interpreted · **applied** (a tested split in the multi-arm tree, scored per leaf
on net after costs per arm). "In PAM" and "in the engine" are reported separately: several of these exist in the NBA engine but not in PAM.

| # | Class | In PAM | In the NBA engine / seat file | Point-in-time source | Free data source |
|---|---|---|---|---|---|
| 1 | **Role state** (usage, primary option, teammates out, as of decision time) | **absent.** PRF-1/2 encode usage *tier* at season level; no as-of usage, no "primary option on the floor tonight", no teammates-out field | **Game families: applied** — NBA-10 lineup cross (usage redistribution when a rotation player is out; W110.2 held-out spread Brier −0.00409, team total −0.00173, n 2,268 games). NBA-5 own status + teammates out: **interpreted**. NBA-11 absorber profile: **interpreted**. **Player props (EXP-047): absent** — `nba_engine_props_forecaster.roster()` uses the unweighted mean of every prior game on this team, and `props.py` states "it does not model who plays" | injury report at the pre-tip cutoff (W93.1 path); box scores strictly before the game | sportsdataverse NBA event store (box, lineups, possessions, `_as_of` on every row); NBA official injury reports; ESPN injury snapshot |
| 2 | **Availability distribution** (multi-season GP, injury type, recurrence) | **aggregated at best.** M-19 "Injury-Managed / Load-Sensitive" is a binary flag; not among the scored modifiers (NBA-PAM-2 lists M-2,3,4,5,6,13,14,18,24,29) | **interpreted, single game only** — `player_availability.fit_play_rates`: P(plays \| report status), shrunk to pooled (Out 0.0008, Questionable 0.514, n 23k). No multi-season games-played distribution, no injury-type recurrence | games-played per season from box scores as of a date; injury-report body part and status history | event store box scores 2016-2026 (GP per season); injury reports 2023-26 already pulled (W93.1); Muse archive for injury text; Kalshi itself nothing |
| 3 | **Trait stability / shrinkage** (weight each skill by how well it repeats) | **absent** — no per-trait reliability anywhere in the schema | **Team level: applied** (`nba_engine/ratings.py` shrinks team ratings to last season with K pseudo-games; NBA-13 officials shrunk). **Player level: absent** — EXP-047 `mu` is a raw mean with `MIN_PRIOR_GAMES = 4`, so four games of threes carry full weight | per-stat reliability fitted on training seasons only; player's own base rate as of the game | event store box scores 2016-2026 |
| 4 | **Role security** (P(keeps minutes when teammates return / rotation changes)) | **absent** | **absent.** NBA-11 (who absorbs a missing creator's shots) is the same machinery run forwards; nobody runs it backwards (who loses minutes when the creator returns) | minutes share with full roster vs current; which rotation teammates are out now and their expected return | event store box + lineups (on-court stints); injury reports for "out" lists |
| 5 | **Scarcity / redundancy** (how many independent sources contribute to an outcome) | **absent** | **partly applied where markets need it:** player points sum exactly to team points (`player_layer.draw_split`), same-game correlation measured and priced for game × points legs (W110, `quant/sgp.py`, `nba_engine/joint.py`); wrong for same-player cross-stat (W110). Contributor concentration as a variance term: **absent** | team stat shares as of the game | event store box scores |

**Pushback recorded with the mapping (the strongest reason not to build this as written):**
- **Class 5 is mostly a fantasy concept.** "Scarce stable contributors are worth more than their raw value" is a roster-construction
  statement: in fantasy you are scored on category ranks across a roster. A Kalshi market prices one leg at a time; there is no scarcity
  premium to capture. The parts that *do* carry over are (a) the dependence between legs for parlays (already built, partly wrong for
  same-player cross-stat), and (b) concentration as a variance input: a team whose rebounds come from one player has a wider
  team-rebound distribution when he sits. Only (b) is new.
- **Class 1 is already applied for game families.** What is missing is the same signal reaching player props and PAM. The cheapest move is
  to feed NBA-10's usage redistribution into EXP-047's `mu`, not to build a new class.
- **Class 2's market value is in props and availability-driven lines, at the margin.** The single-game P(plays) already exists; the
  multi-season distribution matters mostly for players returning from a recurring injury, which is a small population per night.

## 3. Minimum schema additions (no ingestion built here)

Principle: classifications stay in `PamRecord`; state goes in a new point-in-time table read through the same `as_of(..., known_at=)`
contract. Every row carries `as_of_ts` (UTC, the decision time it describes), `known_at` (when it could have been known), `source`, and
`version`. No field is written that a pre-tip reader could not have known.

**A. `player_state` (new; one row per sport, player, game, decision time) — carries classes 1 and 4**
| Field | Type | Class | Meaning |
|---|---|---|---|
| `sport, player_id, game_id, team` | key | — | team as of the game (a trade changes it) |
| `as_of_ts`, `known_at`, `source`, `version` | ts / str | — | point-in-time contract |
| `usage_rate_shrunk` | float | 1 | usage over prior games on this team, shrunk to the player's prior (class 3 rule) |
| `usage_rank_available` | int | 1 | rank of the player's usage among teammates expected to play tonight (1 = primary option) |
| `teammates_out` | list[player_id] | 1 | rotation teammates listed Out / Doubtful at the cutoff |
| `vacated_usage_share` | float | 1 | share of team usage held by `teammates_out` (NBA-10's input, reused) |
| `minutes_expected` | float | 1 / 4 | expected minutes tonight given who plays |
| `minutes_share_full_roster` | float | 4 | the player's minutes share in games when the full rotation played |
| `role_security` | float 0–1 | 4 | P(minutes ≥ 80% of current when the listed teammates return), fitted on history |
| `return_window` | list[(player_id, expected_games_out)] | 4 | when the displacing teammates are expected back (injury report / Muse) |

**B. `availability_profile` (new; one row per sport, player, as-of date) — class 2**
| Field | Type | Meaning |
|---|---|---|
| `gp_by_season` | map season → (gp, team_games) | last 3–5 seasons |
| `missed_by_body_part` | map part → games missed (prior seasons, injury reports) | |
| `recurrence_flags` | list[part] | a body part with ≥ 2 separate absences in the window |
| `expected_games_dist` | (alpha, beta) | beta-binomial on remaining games, shrunk to the age × position pool |
| `as_of`, `known_at`, `source`, `version` | | point-in-time contract |
M-19 stays as the human deep-tier flag; this table is its data-derived mass tier.

**C. `trait_reliability` (new; one row per sport, stat definition, fit version — league level, not per player) — class 3**
| Field | Type | Meaning |
|---|---|---|
| `stat`, `rate_def` | str | e.g. threes per 36, steals per 100 possessions, FT% |
| `r_year_to_year`, `r_split_half` | float + interval | measured on training seasons |
| `k_stabilize` | float | pseudo-games (or attempts) of prior that a sample is shrunk toward; k = n(1−r)/r at the fitted n |
| `prior_rule` | str | player's own previous-season rate, else archetype (PRF) mean, else league mean |
| `fit_seasons`, `version` | | |
Read path: `shrunk_rate(player, stat, as_of) = (n·x̄ + k·prior) / (n + k)`. Nothing is stored per player beyond the base rates it reads.

**D. Class 5 — no PAM field.** A team-level, as-of `contributor_hhi[stat]` (Herfindahl of player shares) computed in the engine, used
only as a variance input for team totals and props. Parlay dependence stays in `quant/sgp.py` / `nba_engine/joint.py`.

**E. `PamRecord` itself:** unchanged. `confidence` (exists, unused in every NBA record) should be filled for deep-tier records when the
deep-tier method is set with the operator (ADR-0075 §3).

## 4. Order of work (proposed, not scheduled)

1. **Class 3 first** — it is the cheapest, has the largest n (ten seasons of box scores), and gives the shrinkage rule classes 1 and 4
   reuse. Pre-registered: `12_EXPLORATORY/pam_stability/PREREG.md` (H-DEPTH-PAM-3).
2. **Class 1 into props** — feed NBA-10's vacated-usage redistribution into EXP-047's `mu` as a challenger (its own pre-registration;
   the forecaster's constants are frozen and hashed).
3. **Class 4** — the reverse of NBA-11: minutes lost when a creator returns; fitted on lineups.
4. **Class 2** — `availability_profile` from GP history + injury reports; first use is the props eligibility filter.
5. **Class 5** — concentration as a variance term; only if 1–4 leave the team-total / prop dispersion visibly misfit.

A class reaches **applied** only when it is a tested split in the multi-arm tree, scored per leaf on net after costs per arm (ADR-0077).
A better-calibrated input is a stronger *interpreted* factor; it is not applied until the router scores it.

## 5. Registered
- GG-2003: player props (EXP-047) have no role-state input — `mu` ignores who is out tonight while game families use NBA-10.
- GG-2004: no player-level shrinkage anywhere in the NBA props path (`MIN_PRIOR_GAMES = 4`, raw mean).
- GG-2005: PAM has no point-in-time state table; four of five classes are state, not classification.
- Backlog B-115 (class 3 test), B-116 (class 1 into props), B-117 (player_state + availability_profile + trait_reliability schema).
