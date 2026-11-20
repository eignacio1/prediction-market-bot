# PREREG — NBA player-prop splits (W121.2, EXP-NBAPROPS-001)

**Last reviewed:** 2026-11-20. **Frozen before any outcome (`y`) or net figure is read for any prop row.**
Only schemas, row counts, series and timestamps were read (price archive `exp_output/PRICE_ARCHIVE/prices_2026-11-11..20.jsonl`,
series KXNBAPTS / KXNBAREB / KXNBAAST / KXNBA3PT, ~277k snapshot rows). Any change after the first scored row is a new
pre-registration, not an edit.

Binds to DOCTRINE §1 (a factor is applied when it is a tested split scored per leaf per arm: net after costs, held out,
game-clustered), ADR-0075, ADR-0077, EXP-039/040/047. "Does not beat the market" is a routing result, never a stop.
Shadow only: Kelly 0, no capital, orders follow v1.

## 1. Layer 1 — market state (from the price archive; PIT by construction: snapshots with run_ts <= row ts)
Per prop market (ticker = event-player-threshold), the row is the last snapshot at or before each band's decision time:
- **price**: yes_mid; **fav price bin** as in `leaf_key` (favourite side price bins).
- **move**: yes_mid(row) minus yes_mid of the earliest snapshot >= 6 h earlier, same ticker (None if none) -> down / flat / up with `FLAT_BAND`.
- **ladder gap**: yes_mid(threshold k) minus yes_mid(next higher threshold of the same player and stat) in the same snapshot;
  bins: tight (<0.06) / normal / wide (>0.20). Coherence check: a non-monotone ladder is flagged `ladder_incoherent` and not scored.
- **time to tip**: close of band T1 12–48 h / T2 4–8 h / T3 15–60 min before the event's start (start from event_ticker date + earliest game snapshot).
Bands: T1–T3 only. T4 points is dark and is not touched.

## 2. Layer 2 — four player-level splits (point in time)
Leaves are terciles (LOW,HIGH = 1/3, 2/3) of prior-completed-season (2025-26) archive values, same edges as `nba_depth`.
- **P1 `minutes_trend@player`** — player's last-10 vs season minutes per game from ESPN box scores strictly before the game date:
  up (>= +10%) / flat / down (<= -10%). Unknown if < 5 prior games this season.
- **P2 `zone_defence@player`** — for the stat's shot-zone mix (points/threes), the opponent's allowed FG%/3P% percentile from the
  2025-26 opponent shooting table (same file family as nba_depth S2); rebounds use opponent rebound-rate, assists opponent assist-allowed. Leaf: soft / mid / tough.
- **P3 `pace@total`** — reuse nba_depth S1 pace leaf (mean of both teams' 2025-26 pace percentile): high / mid / low.
- **P4 `rest@player`** — player's team days of rest and back-to-back from the schedule (prior games only): b2b / normal / rested (>= 3 d).
Coverage (rows joined / total) is stated per split in the results file. `unknown` is never scored.

## 3. Scoring (Part B)
Arms RIDE / FADE / MOMENTUM / NO_BET as `retro_route.arm_nets` (net of fee and the real half-spread). Leaf = (series, band, fav-price bin,
move bin) x split leaf. Fit on the earliest 70% of **games** (by date), scored on the latest 30%. Thin leaf (fit rows < 60 or fit games < 20) -> NO_BET.
Dedupe one row per ticker per band. **Kept** = not thin, arm != NO_BET, held-out games >= 10, held-out mean net > 0. Game-clustered bootstrap
(10,000 draws), BH q = 0.10 across all tested (split, leaf, series, band) cells; reported, and a kept split must also be BH-significant to be
called "earned" (kept-but-not-BH is logged `kept_unearned`). Every non-kept split is logged with its verdict (stump rule).
Settlement outcomes: public Kalshi settled-market GET (as `quant_w109_props/fetch_markets.py`); minutes/rest from ESPN box scores.

## 4. Candidate map
Only KEPT splits go to `leaf_maps/nba_props_v2.json`, registered as `router_candidates["nba_props"]` beside v1 under `PM_CANDIDATE_ARMS`.
v1 and the `router` block stay byte-identical (test). Router v2 (pooled) arms no leaf; the props map reads the same market-state leaf first.

## 5. Modal outcome (pre-registered)
Most prop leaves are thin or non-positive after the half-spread (props are wide-spread); expect 0–3 kept splits and D6 prop cells wired
only where a kept split or an armed leaf exists. A zero is a routing result ("ride / no bet in these leaves"), not a stop; hypotheses are
closed individually (EXP-id, parked for R&D).

## 6. Known limits (stated, not hidden)
- Model-p rows from the engine live on the box only; this scoring uses market state + outcomes, so MODEL_FADE is not scored here.
- The sports-intel-archive is not local; zone/pace profiles come from `nba_depth_splits/profiles.json` (already PIT-pinned at the sha above).
- "After deploy and one slate, run d6_read" cannot be done inside this session without future data; the handoff says so.
