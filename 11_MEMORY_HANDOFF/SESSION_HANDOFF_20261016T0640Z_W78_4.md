# SESSION_HANDOFF W78.4 — NBA event-level data layer (PARTIAL; PR #278)

<!-- session-meta
task_id: W78.4
tier: STANDARD
timestamp: 2026-10-16T06:40:00Z
commit: f9e79c6
one_line_summary: W78.4 PARTIAL: NBA event store (123 files, PIT contract, checks, manifest) built; FACTOR_TAXONOMY.md and GG-895..899 not written.
gg_touched: GG-895..899 (claimed, not registered)
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D4/D1
gap_delta: D4 NBA none -> event-level data layer with PIT contract (manifest 2026-10-16T06:01:34Z); D1 NBA factor mapping NOT moved (Part A undone).
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

## Strategic Decisions This Session
See DECISION_LOG 2026-10-15 23:30 PT. No order/stake/kelly/pre-registration change.

## Pending (next session)
1. Wait for PR #278 CI green; read Deploy job summary; merge.
2. Write `02_ARCHITECTURE_DESIGN/NBA_ENGINE/FACTOR_TAXONOMY.md` (13 classes: free source, field, first season, PIT availability, ADR-0075 stage). Seat NBA B1-B4 are "applied"; PAM NBA "aggregated".
3. Register GG-895..899 in GOVERNANCE_GAP_LOG: historical injuries, officials assignment timestamps, coaches (season-static), travel/venue geometry, PAM/qualitative. No purchases.
4. Propose weekly rebuild next wave (no running component added here).
Findings: ~5.5% of games (preseason/all-star) imputed, no box/officials; lineups key ~5.2% repeats; stats.nba.com unreachable.
