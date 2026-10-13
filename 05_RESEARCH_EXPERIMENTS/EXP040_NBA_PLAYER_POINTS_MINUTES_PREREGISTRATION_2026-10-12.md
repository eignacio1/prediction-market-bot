# EXP-040 — NBA player points ≥15, projected-minutes + injury challenger — PRE-REGISTRATION (ACCEPTED)
**Accepted by operator:** 2026-10-13T00:15:02Z (message "Accept"). Judged ONLY on rows dated after this timestamp. Origin: PROPOSED EXP-040-P in `12_EXPLORATORY/W69_3_nba_points_minutes_results.md`.

* **Challenger:** `minutes_inj` arm of `12_EXPLORATORY/20261012_nba_points_minutes/features.py`; **strike 15 only** (strikes 10/20/25 not registered; strike 25 showed harm, must never be emitted).
* **Fit:** frozen once, train 2023–2024, calibrate 2025 (plan recipe, ridge λ=100, NB dispersion MLE, Platt), artifact sha recorded at freeze; no retraining (Hard Rule 4). **Artifact is NOT yet built** — freezing it and wiring shadow logging beside EXP-039 is the next task; no row counts toward this registration until the artifact sha exists and predates the row.
* **Judged against the MARKET** (Kalshi KXNBAPTS ≥15 mid, de-vigged), not vs frozen EXP-039. First look at n=300 player-games for the cell; game-cluster bootstrap, B=2000, seed 20261009 (as EXP-039).
* **Expected modal outcome (stated now):** edge vs market negative to zero; the market prices late scratches this model cannot see (snapshot ≥4h pre-tip). A null is informative.
* **Known limits:** challenger gain over frozen model ≤0.001 Brier; 2026 injury-report coverage 34% (GG-610 reserved, unregistered); starter flag is a min-rank proxy; no archived market history, so no historical market comparison exists.
