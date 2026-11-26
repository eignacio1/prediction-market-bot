# Handoff W130.4 — PIT NBA archetypes from the event store (SW-9 last wave)
**Branch:** session/20261126T020341Z-w130-4-pam-pit-archetypes · **Model:** Sonnet 5.5

## Built
- `pam/nba_pit_profile.py`: per-player production profile as of a date (games strictly before), per 100 possessions: usage/creation, shot zones, OREB/DREB split, chances vs conversion, share of rebounds on floor, stl/blk, rim-deterrence proxy. pbp rebounds match box 97.2% of 2026 player-games.
- `pam/nba_pit_archetype.py`: mixture on PRF-1..15, fixed signed scores, fit (mean/sd) on 2022-25 only. 2,413 mass records, 469 players, 7 monthly snapshots of 2026, in `qualitative_data/pam_pit/nba/`.
- Agreement vs the 100 deep records (descriptive): top-1 34.8%, deep top present in PIT mixture 71.7%. Weak: PRF-4 over-assigned, PRF-2 collapses into PRF-1. RESULTS.md has the table and Zubac (PRF-12 .51/PRF-7 .49) vs Wembanyama (PRF-9 1.0).
- H-DEPTH-PAM-5 PREREG.md; PAM5 forward shadow arm (`PM_PROPS_PAM5`, default on) logs the cell beside S, S probability unchanged. Registry row + RUNTIME_MAP done.

## Not built (named)
- PRF-10 and PRF-13 (no tracking data); contested rebounds, height, post-up, transition. Opponent size = PRF-9 anchor proxy.
- **Factor table** (`scripts/pam_pit_factor_table.py` → `factors_frozen.json`) is NOT written. It must be committed with its sha256 before 2026-27 scoring or H-DEPTH-PAM-5 is not judged (PREREG §4).
- Season 2027 absent from the event store, so nothing is scorable yet.

directive_conflicts: none
operator decisions: none needed. Installs unchanged (cron is still PAUSED pending nba_engine_props_shadow_install).
surface_delta: +1 shadow arm inside an existing runner (ledger PREGAME_SHADOW_EXP047_PAM5), +0 crons.
pattern_sweep: grep of src/ scripts/ tests/ for other classifiers reading deep-tier labels at fit time: none found in this wave's code.
MEASURE MOVED: D5(b) NBA PAM classification: players with a PIT archetype 0 → 469 (2026 snapshots; source qualitative_data/pam_pit/nba/records.jsonl). D3 +1 (H-DEPTH-PAM-5).
Next (SW-10): write and freeze the factor table; extend the build to the 2027 season when the store lands; tune PRF-4/PRF-2 scores only on training-season structure, not on the deep tier.
