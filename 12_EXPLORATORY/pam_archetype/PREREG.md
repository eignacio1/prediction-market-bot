# H-DEPTH-PAM-5 — matchup cross (player archetype × opponent archetype) vs EXP-047-S (PRE-REGISTRATION)

**Written:** 2026-11-25 (W130.4), committed before any 2026-27 prop row exists in this arm's ledger. **Status:** PRE-REGISTERED.
**Doctrine:** HYPOTHESIS_DOCTRINE.md Part I binds. **Purpose (Hard Rule 12):** DEPTH D5(b) NBA PAM classification, D3 (+1 pre-registered test).
Operator, 2026-11-24: "obviously Zubac's 10 rebounds aren't the same as Wembys 10 rebounds".

## 1. Claim
For NBA player props (points, rebounds, assists, threes), multiplying EXP-047-S's expected stat by a **frozen factor per
(player's PIT top archetype × opponent anchor flag)** gives better-calibrated P(stat ≥ k) than S alone. S is the control.
A result scores an *input* against outcomes. The factor is applied in the tree only when scored per leaf on net after costs per arm
(ADR-0077); log-loss is never the verdict on a cell.

## 2. Seasons already read (verified 2026-11-25 against the preregs/results in the repo)
Every NBA season through 2025-26 has been read: **C2** 2023-24; **PAM-3** 2022-23, 2023-24, 2024-25; **C1** 2024-25 and 2025-26;
**EXP-047-S** 2025-26; the event store seasons 2016-2022 were S's training. None is fresh. **Judged data = forward 2026-27 rows only**
(season 2027 label), logged by the PAM5 arm. Training for the factor table may use seasons ≤ 2025-26 (already read, so allowed as training).

## 3. Definitions
- Player archetype: top weight of the PIT mass record (`qualitative_data/pam_pit/nba/records.jsonl`, `nba_pit_archetype.py`) in force
  on the game date with `known_at` ≤ game date; no record → "unclassified". PRF-10 and PRF-13 have no score (no tracking data).
- Opponent anchor: any of the opponent's top-10-by-prior-minutes players has PRF-9 weight ≥ 0.5 at that date.
- Cell = (player archetype, anchor ∈ {anchor, none}). Cells with < 200 training rows pool into the player's archetype-only row.
- Logged per row in `reasons`: ("player_arch", id, weight), ("opp_anchor", flag). p_yes in the ledger = S's, unchanged.

## 4. Factor table (frozen before the first 2026-27 row)
Per stat s and cell c: `f = (Σ actual + k0·1·Σ S_mu... )` — specifically `f_sc = (A + K) / (M + K)` with A = Σ actual stat, M = Σ S expected stat over
training rows in the cell and K = 40 pseudo-games × the cell's mean S expected stat (shrinks to 1). Fit on training seasons only
(2022-23 .. 2025-26), by `scripts/pam_pit_factor_table.py` (SW-10 builds it; committed as `12_EXPLORATORY/pam_archetype/factors_frozen.json`
with its sha256 **before** the first PAM5 row of 2026-27 is scored). Challenger mean = f_sc × S mean; same engine draws and strike code.
**If the table is not committed before 2026-27 game 1 of the season's scoring, H-DEPTH-PAM-5 is not judged for 2026-27 (stated, not waived).**

## 5. Metric, power and rule
Primary: D = LL(S) − LL(cross), mean over (player-game, stat, threshold) rows, ladders as in PAM-3 §3, 90% game-clustered bootstrap
(2,000 resamples, seed 20261125). Power from `quant/inference.mde_paired`, using S's own per-game sd of D (0.00718, EXP-047-S RESULT):
**judged n = 1,100 games → MDE (80%, one-sided .05) = 0.000538**. A full regular season is 1,230 games, ~1,130 usable (S dropped 43 of 1,230),
so the first judgement is the **end of 2026-27**; no earlier look is a verdict. The sd for a cross-vs-S difference is expected to be at or below S-vs-C2's.
- **SUPPORTED:** D interval wholly above zero **and** D > 0 in ≥ 3 of 4 stats.
- **NOT SUPPORTED:** D point estimate ≤ 0, or fewer than 3 of 4 stats positive → "hypothesis closed (H-DEPTH-PAM-5, parked for R&D)".
- **UNDERPOWERED:** D > 0 with interval including 0; state n needed via `mde_paired`.
- Secondary (reported, never the verdict): per-stat D with BH q 0.10; D by cell; D on rebounds alone (the Zubac / Wembanyama case); Brier.

## 6. Modal outcome
**NOT SUPPORTED or UNDERPOWERED (about 65%).** Cells split ~10 archetypes × 2 flags × 4 stats over one season; S already gained mostly from
low-game players (D ≈ 0 at 31+ games). SUPPORTED (about 35%) needs the cross to matter for bigs' rebounds, where it is most plausible.

## 7. Forward logging (built in W130.4)
`PM_PROPS_PAM5` (default on, `off` is the off-switch) in `scripts/run_nba_engine_props_shadow.py`; ledger `PREGAME_SHADOW_EXP047_PAM5`; shadow beside S, no orders.
