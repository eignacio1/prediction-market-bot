# W59.2 — Calibration correctness before the first look

Status: IN PROGRESS (Part A done; B, C, D pending). Counts only anywhere in this document; no cell has reached a look.

## Part A — Projection from the real schedule

**Defect.** `project_first_look` extrapolated a linear trailing-14-day settle rate. NFL plays one slate a week and the
season ends at week 18, so a daily rate misdates the look by up to a slate and cannot say "never reaches it".

**Fix.** The projection now walks the sport's remaining published schedule (one entry per scheduled regular-season game)
multiplied by the cell's measured coverage (settled games / scheduled games since the cell began logging), adds a
1-day settle lag, and reports `not reachable on the published schedule` instead of a date when the expected total falls short.
Schedule sources: NFL `data/schedules/nfl_2026.json` (snapshot of the nflverse 2026 schedule, 272 games, committed);
NHL `data/raw/nhl/schedule/2026.json` (VPS cache; 1,312 regular-season games); MLB: 2027 schedule not published, so no date is given.
Tests: `tests/test_calibration_engine.py` (weekly slate, slate-day landing + lag, unreachable, no schedule, tiny-sample coverage, reached).

**Corrected first-look dates (as of 2026-10-07, data copied read-only from the VPS):**

| Sport | Cells | Settled games | Old (linear) | Corrected |
|---|---|---|---|---|
| NFL | 12 (4 markets x T1-T3) | 15 each | trailing-rate date | **2026-11-02**, coverage 100% of 15 scheduled since logging began (208 games left; needs 45). Fragile: one week of coverage data |
| MLB | 12 | 0 judged (2-4 postseason, never scored) | n/a | none: judged games begin 2027-03-01 and the 2027 schedule is unpublished |
| NHL | 9 | 16-30 | trailing-rate date | **none: judged n 2,500 is not reachable.** Expected additional games 668 (T1) to 1,128 (T2) of 1,295 left; even at 100% coverage the season has 1,312 games |

## Part B — Release mechanics

**What the pre-registrations say (read, not assumed).** NFL (EXP-037): the first look scores exactly the earliest 60 settled
games per cell; B=2000, seed 20261002, game-cluster bootstrap. MLB: looks 150 / 600, 2027 regular season only. NHL (EXP-036):
judged n 2,500, PRELIMINARY below; B=10,000, per-game mean over strikes. **Not defined in any of them:** the ordering key for
"earliest", and the NHL seed.

**Defects found and fixed in the engine.**
1. *Unstable first-look set.* "Earliest" was ordered by first ledger timestamp, so a game that started earlier but settled late
   (postponement, straggler) would silently rewrite a look already read. Now ordered by `(start_time_utc, game_key)`, and a released
   look is written once to `exp_output/CALIBRATION/release_manifests/<cell>.look<k>.json` with a sha256 digest. Later runs score exactly
   the frozen games; a tampered manifest fails its digest and is not trusted; an existing manifest is never overwritten.
2. *NHL used the NFL bootstrap.* The engine ran B=2000 on raw strike rows for NHL; EXP-036 specifies B=10,000 on per-game means. Now a per-sport policy (`boot_b`, `per_game_mean`, `rules`). The NHL seed is unspecified in EXP-036; the engine keeps 20261002 and states it in the output (`bootstrap` block).
3. *No verdict.* The engine emitted deltas but not the pre-registered decision. `verdict()` now emits n, both deltas with CIs, E_net under both fees, and RULED_OUT / SHADOW / CANDIDATE-PENDING-CAPACITY (EXP-037) or RULED_OUT (a)/(b) / SHADOW-continue / CANDIDATE (EXP-036), only on a released look. It never changes a cell's registry status. A climatology delta <= 0 is flagged as a separate model failure.

**Proof on fixtures (`tests/test_calibration_engine.py`, 27 pass):** 59 games emit no score, verdict or release; 60 emit exactly the
verdict fields, equal to scoring those 60 directly; game 61 leaves the look unchanged; a late-settling earlier game changes an unfrozen
look but not a frozen one; manifest write-once and tamper-evident; verdict-rule cases; NHL policy parameters and rules.

**Synthetic first-look REPORT** (same renderer as the real one): `W59_2_first_look_REPORT_SYNTHETIC.md`. Regenerate with
`python3 scripts/calibration_engine.py --synthetic-report PATH`. The NHL synthetic cell uses B=400 for runtime (stated in the report).

**Gaps to register (not changed here; pre-registrations are not edited):** the "earliest 60" ordering key is undefined in EXP-037;
the NHL seed is unspecified in EXP-036; MLB settled rows have no `p_clim`, so the pre-registered climatology comparison is unavailable for MLB.
