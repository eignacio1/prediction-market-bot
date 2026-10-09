# 12_EXPLORATORY — Charter

**Created:** 2026-10-09 (Wave 61.3, T-753, GG-533). **Status:** in force. Amend only by a dated addendum at the bottom.

## Purpose
Build **challengers** for pre-registered cells, so that when a first look says NO (NFL first look ≈ 2026-11-02; Waves 38-44 found no
edge net of cost across 14 families) a candidate already exists, built on data the judged cells never see, ready to be pre-registered.
Nothing here is evidence about any cell. Nothing here is a verdict.

## Rules (binding; enforced by `tests/test_exploratory_isolation.py` where a static scan can enforce them)
1. **Reads only** archives, copies and **past seasons** (data dated before the relevant model's freeze / before the pre-registration it would challenge).
2. **NEVER reads shadow rows or any result of a sealed cell.** Reading a sealed cell's score below its judged n is a look; looks are pre-registered and counted.
   Forbidden read targets include the pregame-shadow ledgers, `*_T[123].jsonl`, settled-row files, first-look reports, `logs/`, paper ledgers.
3. **NEVER writes** to `logs/`, shadow or paper ledgers, the market-type registry, `03_DECISIONS/`, any `*PREREGISTRATION*` file, `models/`, or a
   calibration-engine release. **All writes go through `_fence.safe_out()`**, which refuses any path outside `12_EXPLORATORY/`.
4. **NEVER imports** order, position, promotion or registry-mutation code: `paper_trader`, `kalshi_client` (order/submit), `promote_cell_status` /
   `set_measurement`, `pregame_shadow.ledger|runner|calibration_engine`, `execution_bands_orchestrator`, `run_*`, `t4_*`. Frozen models may be
   **loaded as read-only artifacts from their JSON** (e.g. `exp_output/NFL/nfl_pregame_v1.json`), not via the production runner.
5. No network write (POST/PUT/DELETE/PATCH), no subprocess, no `os.system`. Read-only GETs against the Kalshi DEMO API only, if ever needed.
6. Every output file and table is labelled **EXPLORATORY** and is never cited as a verdict, in any document, by any session.
7. **Graduation:** a finding becomes evidence only through a **new dated pre-registration the operator accepts**, judged on data dated **after** that
   pre-registration. A challenger pre-registration drafted here is `PROPOSED` until the operator accepts it; it is not accepted by being drafted.
8. No order, position, fill, stake size or `kelly_fraction` change originates here (ADR-0048 sizing zero stands).

## Layout
- `_fence.py` — `safe_out()`; the only sanctioned write path.
- `W61_3_exploratory_track_results.md` — results doc, updated per part.
- Studies live in subdirectories named `<yyyymmdd>_<slug>/`; each writes only inside itself.
