# Data Snapshots Index — Prediction Market Trading Bot

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

**Alias:** SNAP-001 (shorthand for SNAP-2026-05-22-001; internal references)  
**Alias:** SNAP-002 (shorthand for SNAP-2026-05-27-001; EXP-001 10-player raw game logs)  
**Alias:** SNAP-003 (shorthand for SNAP-2026-05-27-002; backtest fresh pull — optional)  
**Alias:** SNAP-004 (shorthand for SNAP-2026-05-28-001; T-043 50-player raw game logs)  
**Alias:** SNAP-005 (shorthand for SNAP-2026-06-14-001; canonical NBA Finals clean bet dataset)

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
