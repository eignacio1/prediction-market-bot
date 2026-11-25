# Session handoff — W128.1 (NHL depth: goalie, referee, availability) — 2026-11-24
**PR:** #585 (branch w128-1-nhl-depth). **Backlog:** B-122. **Prereg:** `12_EXPLORATORY/nhl_depth/PREREG.md` (99f0aa1, before any outcome join). **Result:** `RESULT.md`.

**MEASURE MOVED — D5(b) NHL factor classes by stage:** before = officials, coaches/scratches, availability, qualitative at `none`; goalie quality on post-game starter. After = **unchanged at `none`** for all four. Built, shadow-only, unjudged: goalie@game and officials@game inputs behind `PM_NHL_DEPTH=on` (default off). Availability abstains (no point-in-time feed). No stage moved because no split reached a tested verdict; I did not edit SEATS/nhl.toml.

- vision_pillar: DEPTH D5(b). gap_measure: NHL factor classes at a tested verdict = 0 → 0. gap_delta: 0 (inputs and filter built; judging needs ~370+ games).
- Built: `filters/nhl_depth.py` (leaves, PIT check, Muse loader), `shadow_route.py` candidate `nhl_depth` (logs `split_leaves` beside nhl_v2, `split_applied=False`), `tests/test_w128_1_nhl_depth.py` (9 tests: planted backup start moves leaf; no Muse data / snapshot after row / marker rows → abstain).
- Part C: 99 games 11-10..11-23 joined to Muse goalie snapshots: 7 both_expected, 39 any_backup, 53 unknown. **The 39 is a sparse-history artefact**, not a finding: expected starter is derived from Muse-confirmed starts only. Fix = prior starters from the box NHL event store. Not read as a leaf.
- Deviation from prereg: the referee crew prior and cuts are not yet computed at logging time (leaf `unknown`); scoring supplies them offline once settled totals exist.
- pattern_sweep: marker rows without `game_id` (fetch failure, NO_GAMES) exist in Muse files (11-13, 11-15, 11-20); the loader skips them. Checked `src/ scripts/ tests/`: no other Muse reader.
- surface_delta: +1 candidate key in `router_candidates` (off by default), +1 module, 0 services/crons. No RUNTIME_REGISTRY change.
- directive_conflicts: none. Kelly 0, shadow only, orders follow v1.
- operator decisions: none needed. Turning `PM_NHL_DEPTH=on` on the box is a plumbing step for the next window (needs `NHL_MUSE_DIR` populated by a pinned-SHA fetch task, which does not exist yet).
- Next: (1) box task to fetch Muse NHL snapshots at the pin; (2) prior starters from the NHL event store; (3) re-count leaves; (4) first look at ~370 games.
- Environment notes: local `.venv` missing; used a scratch venv. The NHL API returns 403 without a browser User-Agent.
