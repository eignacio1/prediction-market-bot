# DS-04: MLB T2 Batting Lineup Data Source Designation

**Designation:** DS-04  
**Sport:** MLB  
**Pipeline:** PIPE-05.5 (run_t2_mlb_sameday.py — T2 Same-Day Overlay)  
**Date designated:** 2026-06-25  
**Designated by:** Earl Ignacio (operator ruling, Session 87)  
**Status:** ACTIVE

---

## Source Description

**Source:** MLB Stats API — Schedule endpoint with `hydrate=lineups,team`

**Endpoint:** `https://statsapi.mlb.com/api/v1/schedule`  
**Parameters:** `sportId=1, date={GAME_DATE_ISO}, hydrate=lineups,team`

**Method:** `MLBIngestionClient.fetch_lineups(game_date, session_id)` in  
`src/prediction_market_bot/c1_signal_ingestion/mlb_ingestion.py`

---

## What This Source Provides

1. **Lineup confirmation** — Whether a player is in the confirmed batting lineup for today's game. Players not in the lineup (scratched, benched, DL) are filtered out of T2 evaluation. T1 (PIPE-05 at 03:00 UTC) has no confirmed lineup data; this is the primary T2 value add.

2. **Batting order position** — The player's slot in today's confirmed batting order (1-indexed; 1 = leadoff). Used to compute an AB-per-game adjustment:
   - Slots 1-2: ~4.1-4.2 expected ABs/game (top of order, most plate appearances)
   - Slots 3-4: ~3.9-4.0 ABs/game
   - Slot 5: ~3.7 ABs/game (≈ population average baseline)
   - Slots 6-7: ~3.4-3.6 ABs/game
   - Slots 8-9: ~3.1-3.2 ABs/game (bottom of order, fewest plate appearances)

3. **Game-level association** — `game_pk` links each player to their specific game, enabling per-game contamination guard (skip players in already-started games rather than halting all T2 bets when ANY game is live).

---

## Adjustment Methodology

T2 applies a Binomial slot adjustment to the T1 probability estimate (`p_t1`):

```
p_adj  = 1 - (1 - ba_l10)^ab_adj           [for H≥1]
p_base = 1 - (1 - ba_l10)^ab_default        [for H≥1]
ratio  = clip(p_adj / p_base, 0.85, 1.15)
p_t2   = clip(p_t1 × ratio, 0.01, 0.99)
```

For H≥2:
```
p_adj  = 1 - (1-BA)^n - n×BA×(1-BA)^(n-1)
```

`ba_l10` comes from the T1 pregame context (`pregame_mlb_YYYYMMDD.json`). The adjustment is capped at ±15% to prevent over-riding the model signal.

---

## Availability Constraints

1. **Current season only (2026):** MLB Stats API returns HTTP 406 for historical dates from DigitalOcean/Fastly CDN infrastructure. Lineups endpoint accessible for current season only. (Consistent with PIPE-05FX constraint documented in cron.conf.)

2. **Timing — lineups not always posted at 19:30 UTC (3:30 PM ET):** Lineups are typically posted 3-4 hours before first pitch. For evening games (7:05-7:10 PM ET = 23:05-23:10 UTC), lineups appear at approximately 15:30-16:00 ET = 19:30-20:00 UTC. The T2 cron at 19:30 UTC may catch lineups 30-60 minutes after posting for most games.
   - **Graceful handling:** If lineups not yet posted (empty response), `fetch_lineups` returns `ok=True, {}`. T2 proceeds without lineup filter — no bets blocked, no scratches applied.
   - **Afternoon games:** Games starting before 19:30 UTC may have already-live status. Per-game contamination guard catches these and skips those players specifically.

3. **`hydrate=lineups` response field:** Returns `lineups.homePlayers` and `lineups.awayPlayers` as ordered lists (index 0 = batting first). Order is the batting order. If the API changes this structure, `fetch_lineups` returns empty dict.

---

## Known Issues and Limitations

**KI-T2-MLB-001 — No injury report source:**  
MLB T2 does not have access to structured injury reports. A player may be "in the lineup" per the API at 19:30 UTC but be a late scratch due to injury reported after lineup submission. T2 cannot detect this. The T4 in-play band (PIPE-07-MLB) handles late scratches implicitly — a player who doesn't bat never accumulates hits, so T4's Bayesian update will naturally price them to 0.

**KI-T2-MLB-002 — SP change since PIPE-06pre:**  
PIPE-06pre runs at 16:30 UTC with `hydrate=probablePitcher`. If the starting pitcher changes between 16:30 UTC and 19:30 UTC (rare — typically only injury scratches), T2 does not detect this and uses the T1 probability that incorporated the original SP. Risk: LOW — SP changes this late in the day are infrequent. An SP identity check was evaluated and deferred (complexity vs. signal value insufficient before G6 validation).

**GG-004 (OPEN):** Commercial validation (EXP-017) not yet run. T2 inherits the same open commercial question as T1 — edge vs. actual Kalshi prices is unvalidated. T2 requires ≥500 closed positions (from T1 + T2 combined) to run EXP-017.

---

## Relationship to NBA DS-04

The NBA T2 band is blocked on DS-04 (qualitative source: structured injury reports). MLB T2 uses a different approach — quantitative lineup data from the MLB Stats API is the primary T2 source. MLB does not have structured injury reports comparable to the NBA. This designation is **DS-04 MLB** specifically; it does NOT unblock NBA T2, which still requires a qualitative injury source.

---

## Activation Gate

- [x] DS-04 MLB designated (this document)
- [x] `MLBIngestionClient.fetch_lineups()` implemented and in mlb_ingestion.py
- [x] `run_t2_mlb_sameday.py` built (PIPE-05.5-MLB)
- [x] Tests written (`tests/test_t191_mlb_t2.py`)
- [x] Cron entry added (`deploy/cron.conf` — 30 19 * * *)
- [ ] EXP-017 commercial validation — G6 blocker (GG-004 OPEN)
