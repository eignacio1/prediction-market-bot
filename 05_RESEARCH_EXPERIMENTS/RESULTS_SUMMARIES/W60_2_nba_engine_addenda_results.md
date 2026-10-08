# W60.2 — NBA into the calibration engine + pre-registration addenda

Claim: T-743..T-746, GG-529..GG-530 (W60 numbering collided twice on claim; first free range taken).

## Part A — NBA policy in the engine (EXP-038)
`pregame_shadow/calibration_engine.py` `PREREG["NBA"]`: looks 150 / 400, mode sealed_until_look, bootstrap B=2000, seed 20261006
(EXP-038 §3; differs from the engine default 20261002), game-cluster bootstrap (scoring.py), climatology on (settle writes `p_clim`),
decision rules = EXP-038 §5 (`rules="exp038"`: §5.1 RULED_OUT, §5.2 SHADOW then UNRESOLVED after the second look, §5.3 CANDIDATE-PENDING-CAPACITY).
Preseason: `settled_schema.counts_toward_judged_n` (excluded_from_judged_n=true or season_phase=preseason) gates `eligible()` for every sport;
`PREGAME_SHADOW_PRESEASON` is never discovered. The 12 EXP-038 §1 cells are listed from day one (`EXPECTED_CELLS`) so counts show before the first row.
Dashboard Calibration section gains NBA; 0-row cells read "awaiting first regular-season rows".

**Left undefined by EXP-038 — listed, not invented** (emitted per cell as `undefined_rules`):
1. Second look "or 2027-01-31, whichever first": no rule for which games / what n at the date. Only the n=400 second look is released. Registered GG-529.
2. "judged on whatever n they reach" (§1) vs §4 "no scoring before judged n": a cell below 150 stays sealed.
3. Ordering key for "earliest N": inherited from EXP-037 §2 via the EXP-037 addendum (Part B), not restated in EXP-038.

Tests (`tests/test_calibration_engine.py`): policy values; sealed at 149 (no score, no verdict); release at exactly 150; 151 leaves the look
byte-identical (games and scores); preseason never counted (flag, label, mixed); UNRESOLVED only after the second look; 12 cells listed with zero rows.

Part A shipped: PR #186 (squash d58623b), CI green. Deploy: t4-mlb restart decision `not_needed` (no file imported by t4-mlb changed). VPS manual run of the engine lists 12 NBA cells, each SEALED 0 of 150 (GG-513 RESOLVED; the scheduled daily run's first NBA listing is still to be seen).

## Part B — addenda (authority: operator 2026-10-07 19:03 PT)
Appended, original text untouched: EXP-037 NFL + MLB ordering key (start_time_utc, game_key) [GG-510]; EXP-036 seed 20261002 [GG-511]; EXP-036 goalie amendment, W59.3 Part B text verbatim; EXP-037 MLB climatology unavailable [GG-512]. GG-510/511/512 RESOLVED; GG-514 ACCEPTED UNCERTAINTY (NHL PRELIMINARY in 2026-27). One DECISION_LOG entry written.
Engine check (no code change): ordering = `_games_in_order` -> (start_time_utc else ts_utc, game_key); NHL seed = `scoring.BOOT_SEED` 20261002, B=10,000 per-game means.
**GG-401 stays OPEN.** (1) Judgeable under the amendment: yes by the amended text. (2) Live T3 job: `nhl_shadow_eval.py` passes no starter_provider, so the model uses the projected last-start goalie (confirmed=False), but the 2,246 live T3 rows on the VPS carry no `confirmed`/`starter_source` field (it exists only inside the hashed feature row). The "flagged confirmed=False" condition is therefore not met on the rows -> GG-530 (new rows only fix, not done here).
Registered: GG-529 (EXP-038 date-triggered second look undefined), GG-530.
