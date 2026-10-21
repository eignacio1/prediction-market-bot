# KXNFLPASSYDS (W81.3) — results so far (PARKED, Part B unmerged at time of writing)

- Frozen model: `models/passyds_strike_v1.json`, sha256 `1053c8433715baf1d732a3a773077755aa6b0895bd099b7d3856559595d4e0db`. No market price enters the model.
- Sanity gate (reported, not a verdict): train 2019–2023 REG, held out 2024–2025 (1047 QB-games, 5235 strike rows). Brier model 0.20021 vs QB-season-average baseline 0.21886 (delta −0.01864). See `sanity_report.json`.
- Snapshot read-back vs kickoff: NOT YET (job not installed on box at time of writing; first game to write: Thu 10-22 TNF NE @ CHI, `KXNFLPASSYDS-26OCT22NECHI`). Pre-kickoff depth n = 0. Fillability floor: n only until one full NFL week exists.
- Registry: cell is NOT_IMPLEMENTED; flips to SHADOW only after the first valid row.
