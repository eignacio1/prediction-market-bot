# SEATS — what each sport's engine conditions on (ADR-0075 §2, W75.3)

One TOML per sport: `nfl.toml`, `nba.toml` (populated, v0 drafts), `mlb.toml`, `nhl.toml` (stubs: every registered cell, no factors).
`NFL_SEAT.md` / `NBA_SEAT.md` are rendered from the TOML by `scripts/render_seat.py`; edit the TOML, re-render.

**These are v0 drafts.** A football or basketball eye will correct them. They exist so the correction has something to land on.

## Schema
- `[[factor]]`: `id`, `factor_class` (FACTOR_TAXONOMY id for NFL; local `NBA-n` for NBA), `name`, `source` (free source + field, or the GAP), `engine_slot` (an `INTERFACE.md` slot, or `none`), `stage`, `evidence`.
- `[[cell]]`: one per registered (market family x band): `market`, `band`, `status` (copied from `market_type_registry.py`), `serving_model`, `factors` (factor ids the cell's model conditions on today), `evidence`.
- **stage**: `aggregated` (in a store) < `interpreted` (turned into a feature or tested) < `applied` (conditioned on by a model that logs forecasts); `none` = not built. Set only from `evidence`, a path that exists on main. If you cannot cite a file, the stage is `none`.

## Rules
- Every registered cell of a populated sport has a seat entry (test: `tests/test_seat_interface.py`).
- Every `evidence` path exists (same test). A pending or in-flight file is never evidence.
- `scripts/distance_to_optimum.py` reads D5(b) (factor counts by stage) from these files.
