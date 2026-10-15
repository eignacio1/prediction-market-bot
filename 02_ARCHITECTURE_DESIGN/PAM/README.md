# PAM: Player Attribute Matrix (ADR-0075 §3)

One sport-agnostic record, one append-only store, one read path `pam_as_of(sport, player_id, as_of)`. See `CORE_SCHEMA.md`. Operator, 2026-10-14: "we're gonna start piping in the PAM into the NFL, NBA, MLB and NHL (starting with NFL and NBA) - this is going to be a portion of our Syndicate32 bridging - it needs to stay dynamic enough that we can port it easily and do mass application but we'll keep it substantive for when it matters most."

## What exists (2026-10-14, W75.1)

| Sport | Core | Taxonomy | Mass tier | Deep tier | Stage |
|---|---|---|---|---|---|
| NBA | yes | `qualitative_data/pam/nba/taxonomy.json` (15 PRF, 32 modifiers, from the v4 docx) | none | 100 records (2 snapshots x 50, lossless port of the v4 CSVs; 002 supersedes 001) | aggregated |
| NFL | yes | `NFL_TAXONOMY.md` (9 groups); built group: WR (`qualitative_data/pam/nfl/taxonomy.json`) | WR, 2023-2025: 247 records | none (method proposed, `DEEP_TIER.md`) | aggregated (WR); interpreted/applied: none |
| MLB | core only | none | none | none | none |
| NHL | core only | none | none | none | none |

Nothing is applied: no engine reads PAM yet and no experiment script was rewired (they still read the old NBA CSVs).

## Layout
`src/prediction_market_bot/pam/` (schema, store, `nba_port`, `nfl_wr_mass`) · `scripts/pam_nfl_wr_mass.py` (offline run) · `qualitative_data/pam/<sport>/{taxonomy.json,records.jsonl}` · tests `tests/test_pam_core.py`, `tests/test_pam_nfl_wr.py` · WR run output `NFL_WR_MASS_REPORT.txt`.

## D5 line
**D5(a) cluster designs: NFL 0 -> 1 (core + 9-group taxonomy + WR mass classifier, aggregated), NBA 0 -> 1 (v4 ported losslessly into the core, deep tier), 2026-10-14, W75.1.** Gaps registered: GG-775..GG-779.
