# Data Snapshots Index — Prediction Market Trading Bot

> **STATUS BANNER (2026-10-20, W80.4): NOT VERIFIED against the running system.** Written May 2026; index not maintained since May 2026; current data lives under `exp_output/` and `logs/` per `RUNTIME_MAP.md`. Where this file disagrees with those sources, they win. Registered LIVING in `00_ADMIN/DOC_REGISTRY.toml` with no verification date.

**Purpose:** The authoritative registry of all data snapshots used in experiments. Every dataset that enters the pipeline must be registered here before use. Immutability guarantee: once registered, a snapshot is never modified.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-06-14 (SNAP-2026-06-14-001 registered — T-174 canonical NBA Finals clean bet dataset)  
**Next review:** Before each experiment run; updated as new snapshots are registered  
**Staleness triggers:** New snapshot registered; snapshot used in new experiment; data source schema change  
**Upstream links:** DATA_FLOWS_LINEAGE.md, DATA_REQUIREMENTS.md  
**Downstream links:** EXPERIMENT_LOG/ (all experiment records must cite Snapshot IDs)  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — SNAP-001 registered (DS-01 framework document); SNAP-002 registered (DS-02 EXP-001 raw game logs); SNAP-003 pre-registered (DS-02 backtest fresh pull — row count TBD)

---

## Snapshot Discipline

Per DATA_FLOWS_LINEAGE.md:

1. **Assign Snapshot ID** before any experiment references the dataset
2. **Register here** with all required fields
3. **Cite in experiment record** — every EXPERIMENT_LOG entry must list all Snapshot IDs used
4. **Immutability** — once registered, a snapshot is NEVER modified. Corrections create a new snapshot with a lineage note pointing to the corrected snapshot.

**Format:** `SNAP-YYYY-MM-DD-NNN` where NNN is a zero-padded sequence for that date (001, 002, ...)

---

## Active Snapshot Registry

| Snapshot ID | Dataset | Source | Version | Ingestion Date | File Path | Row Count | Schema Version | Lineage Note | Used In |
|-------------|---------|--------|---------|----------------|-----------|-----------|---------------|--------------|---------|
| SNAP-2026-05-22-001 | Player_Attribute_Matrix_v4.docx | DS-01 (Earl Ignacio) | v4.0 | 2026-05-22 | 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/DS-01_Player_Attribute_Matrix_v4.docx | N/A — framework document (not tabular rows) | v4.0-weighted-hybrid | First registration; OQ-001 resolved same date; provenance in DATA_PROVENANCE.md | No experiments yet (Phase 3+) |
| SNAP-2026-05-27-001 | NBA Game Logs (10 players × 3 seasons) | DS-02 (nba_api) | nba_api v0.9.x | 2026-05-27 | exp_output/EXP-001/SNAP-2026-05-27-001_raw_game_logs.csv | TBD — populated after ingestion run | IF-C1-C2 v1.0 (29-column schema) | Raw game logs for EXP-001 first pipeline run; C1 NBAIngestionClient output; seasons 2021-22/2022-23/2023-24 Regular Season; 10 target players (LeBron 2544, KD 201142, Curry 201939, Giannis 203507, Jokic 203999, Embiid 203954, Lillard 203081, Luka 1629029, Tatum 1628369, Butler 202710) | EXP-001; EXP-002 (via --raw-csv); EXP-003 (via --raw-csv) |
| SNAP-2026-05-27-002 | NBA Game Logs (10 players × 3 seasons) — Backtest fresh pull | DS-02 (nba_api) | nba_api v0.9.x | TBD — populated if run_backtest.py is run without --raw-csv | exp_output/BACKTEST/SNAP-2026-05-27-002_raw_game_logs.csv | TBD — populated after ingestion run | IF-C1-C2 v1.0 (29-column schema) | Fresh C1 pull for backtesting (T-036); same cohort as SNAP-2026-05-27-001 (10 players × 3 seasons 2021-22/2022-23/2023-24 Regular Season). Use SNAP-2026-05-27-001 via --raw-csv to avoid a second pull. | EXP-002; EXP-003 (if fresh pull used) |

| SNAP-2026-05-28-001 | NBA Game Logs (50 players × 3 seasons) | DS-02 (nba_api) | nba_api v0.9.x | 2026-05-28 | exp_output/EXP-001/SNAP-2026-05-28-001_raw_game_logs.csv | TBD — populated after T-043 run | IF-C1-C2 v1.0 (29-column schema) | T-043 expansion: 50 players (original 10 + 40 additions); same seasons 2021-22/2022-23/2023-24 Regular Season. Registered before run per snapshot discipline. | EXP-001 (T-043); EXP-002/003 rerun (Phase 4) |
| SNAP-2026-06-14-001 | NBA Finals 2026 Clean Bet Dataset (canonical NBA T1+T4 paper track record) | DS-02 derived (PaperTrader ledger + C6 audit log) | bet_record_contract v1.0 | 2026-06-14 | data/nba_finals_clean_dataset.csv | 158 bets (117 CLOSED + 41 OPEN G5) | bet_record_contract v1.0 (28 canonical fields) | **T-174 WS2/WS3 canonical NBA close-out record.** Built by `scripts/build_clean_dataset.py` from the corrected PaperTrader ledger; contamination is LABELED not dropped (`duplicate_twin`/`fee_contaminated`/`kalshi_order_failed`/`order_local_only` + `is_clean` flag). Reconciles to true realized P&L **−$251.21 (−25.1%)** headline; **clean-only −$302.98 (−30.3%)** — contaminated bets netted +$51.76. **sha256 `bf5652c3edd88a93b4b3060ac2541a19418eeba2b29d1156e14b645c178314b8`.** Summary JSON `data/nba_finals_clean_dataset_summary.json` sha256 `eee43a7236f5652f22e64749bba7cdf819aae03aacfde655e9e76ecfb9095cd7`. CSV gitignored (data CSV convention); registered by hash. **41 G5 rows remain OPEN — see GG-036; re-freeze as a new snapshot if G5 resolves.** | G6 baseline ratification (2026-06-14); EXP-017-style commercial validation (post-season audit) |
| SNAP-2026-07-02-001 | T4-MLB production per-cycle raw context log (GG-067 fix output) | DS-02 derived (`run_t4_mlb_live.py::_run_cycle()` production cycle-log write, live since SESSION 110) | t4_mlb_cycle_log schema v1 (ts/cycle_id/session_id/game_date/ticker/player_name/player_id/threshold/p_t4/mip/vig/gross_edge/net_edge/ba_l10/h_so_far/ab_so_far/ab_remaining/inning/batting_slot) | 2026-07-02T19:44Z (pulled from VPS) | exp_output/EXP-ARITH-MLB-01/SNAP-2026-07-02-001_t4_mlb_cycle_log.jsonl | 1,201 raw cycles, single game_date (2026-07-02), 2 games (PIT@PHI, CIN@MIL) | t4_mlb_cycle_log v1 | First snapshot of the GG-067 production logging fix; frozen via `scp` from `/opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl` at the point of use. **Both source games were still IN PROGRESS (not FINAL) at freeze time** — `fetch_actual_hits` resolution will return 0 or near-0 resolved bets against this snapshot; this is an expected early-cycle snapshot for validating the EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 runners' graceful no/low-data path against real production output, not a data-sufficient run. **sha256 `c817d983f260facecc58fd4b28fd9af4a2fc9e127a300cb4eddb1f70dff75f59`.** Re-freeze a later snapshot once multiple FINAL game-days have accumulated before treating any EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 verdict as data-sufficient. **Correction (2026-07-02, same day):** the real EXP-ARITH-MLB-01 run against this snapshot resolved 7 bets at confidence_gate=0.70, not the 0 this note predicted — traced to [[GG-069]] (`fetch_actual_hits` has no FINAL-status gate; it returns live/partial MLB Stats API `gameLog` hit totals for in-progress games). Those 7 resolved records are known-invalid (resolved against confirmed-incomplete box scores), not evidence the games had actually finished. | EXP-ARITH-MLB-01 (T4M-ARITH); EXP-FLOW-MLB-01 (T4M-FLOW) — both BLOCKED pending sufficient resolved N |

| SNAP-2026-07-11-001 | MLB paper portfolio snapshot (T1 regression-anchor fixture, T-336/N-01) | DS-02 derived (live VPS `.vps_portfolio_cache_mlb.json` pull, frozen at point of use) | bet_record schema as written by `PaperTrader`/`load_pool_by_band` | 2026-07-11T11:08Z (pulled from VPS, frozen this session) | tests/fixtures/SNAP-2026-07-11-001_t1_regression_anchor_mlb_portfolio.json | 232 closed_positions (T1=230, T2=2) | matches `load_pool_by_band`/`to_mlb_positions` input contract (no schema change from live cache) | **T-336 fix for GG-live-data-regression-anchor:** `tests/test_band_monitor.py::TestT1RegressionAnchor` previously asserted an exact Fisher p-value against the live, growing `.vps_portfolio_cache_mlb.json` — as the real book accumulated volume (n=167→230 T1 positions) the exact float drifted (0.246→0.359) while the underlying verdict (INCONCLUSIVE, not anti-predictive) stayed stable, breaking the anchor on every session that pulled a fresher cache. This snapshot freezes the book at n=230 T1 positions so the anchor is reproducible; the test now asserts verdict + a tolerance range, not an exact float, so future re-freezes don't require hand-tuning a new magic number. **sha256 `47938bd44ff762a37d557c2551a633e0eafd0a92a1e9050fbfdb114b9a85924d`.** Computed against this fixture: `fisher_pvalue=0.359`, verdict=INCONCLUSIVE, calibration `b_ci=[0.614, 1.314]` (includes 1, `b_excludes_1=False`). | `tests/test_band_monitor.py::TestT1RegressionAnchor` |

**Alias:** SNAP-001 (shorthand for SNAP-2026-05-22-001; internal references)  
**Alias:** SNAP-002 (shorthand for SNAP-2026-05-27-001; EXP-001 10-player raw game logs)  
**Alias:** SNAP-003 (shorthand for SNAP-2026-05-27-002; backtest fresh pull — optional)  
**Alias:** SNAP-004 (shorthand for SNAP-2026-05-28-001; T-043 50-player raw game logs)  
**Alias:** SNAP-005 (shorthand for SNAP-2026-06-14-001; canonical NBA Finals clean bet dataset)  
**Alias:** SNAP-006 (shorthand for SNAP-2026-07-02-001; T4-MLB production cycle-log first snapshot)  
**Alias:** SNAP-007 (shorthand for SNAP-2026-07-11-001; T1 regression-anchor MLB portfolio fixture)

---

## Registration Procedure

When registering a new snapshot:

1. Assign Snapshot ID: `SNAP-[today's date]-[next sequence number]`
2. Complete all fields in the registry table above
3. Record file hash for integrity verification
4. Update DATA_SNAPSHOTS_INDEX.md (this file)
5. Reference Snapshot ID in the experiment record before running

**Required fields (all mandatory):**
- Snapshot ID
- Dataset name
- Source (DS-01, DS-02, DS-03, or custom)
- Version of source schema
- Ingestion date and time (UTC)
- File path (relative to SNAPSHOT_DIR)
- Row count (verify after ingestion)
- Schema version

---

## Snapshot Integrity Checks

Per the reproducibility requirement (NFR-01):

```bash
# Verify snapshot file has not been modified since registration
# [Command TBD at Phase 3]
python scripts/verify_snapshot_integrity.py --snapshot-id SNAP-YYYY-MM-DD-NNN
```

If hash mismatch detected: do NOT use the snapshot; open an issue in RID_LOG.md; create a corrected snapshot with a lineage note.

---

## Snapshot Lineage

When a correction is needed:

| Original Snapshot | Corrected Snapshot | Reason | Date |
|------------------|-------------------|--------|------|
| — | — | — | — |
