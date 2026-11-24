# Session handoff — W124.4 dense capture (Sonnet) — 20261124T0029Z
Common rules read first: origin fetched; line 1 of COMMON_RULES_W124.md = "# Wave 124 common rules". Branch session/20261124T002053Z-w124-4-dense-capture.

## Result in one line
Built and tested dense capture (props from listing, 5-min game snapshots, forward trade prints) with a budget gate. **The gate REFUSES on the box's current disk**, so the install needs retention headroom first. Install NOT run.

## Part A — measured (box numbers are disk_read 2026-11-19 05:27Z, the latest result; no fresh box read this session)
- Disk 24G, 74% used, 6.1G free. disk_guard growth -1.00 pct/day over 6 d (flat/shrinking; counted as 0 by the gate).
- PRICE_ARCHIVE 2.6 GB plain, 60-110 MB/day; retention gzips it after 14 d (disk_retention_install is still paused).
- Existing prop cron covers hours 17-05Z only; hours 06-16Z have no props (cause of the H1 and NHL prop gap).
- Rate limit: no number in the repo. Kalshi Basic read tier is 200 tokens/s, 10 per default request = 20 req/s (DERIVED, not a Kalshi-stated req/s; GET /account/limits is the authority). Half = 10 req/s = 600 req/min.

## Part B — dry run, live public API, 2026-11-24 00:25Z (evening ET, NBA+NHL slate = peak run)
| mode | rows | gz bytes/run | requests/run | seconds | runs/day |
|---|---|---|---|---|---|
| props | 3,849 | 118,859 | 38 | 14.6 | 33 (hours 06-16Z) |
| games | 1,044 | 34,167 | 20 | 6.5 | 288 |
| prints | 14,644 (of 103,012 scanned) | 505,150 | 104 | 42.6 | 288 |
- Upper bound (every run at peak size): **159 MB/day** (prints 145, games 10, props 4). Realistic is lower (prints scale with the slate); not measured.
- Requests: 25.7/min average; worst case all three bursting at once 8.1 req/s = 487/min, under the 600/min half-limit.

## Part C — the gate (scripts/archive_dense_install.py gate())
Refuses unless disk after 30 d < 80% and burst rate < half the limit. At 74% now and 0 existing growth: projected **93.9%** at the upper bound (even at half of it ~84%). **It refuses today.** I did not loosen it.
To pass: disk_retention_install first (compress the 2.6 GB archive), or cut prints (145 MB/day is 91% of the load), or more disk.

## Part D / E — files
scripts/archive_dense_capture.py, scripts/archive_dense_install.py, deploy/cron.archive_dense (3 NEW lines, none edited), 3 paused RUNTIME_REGISTRY entries, box_tasks archive_dense_install/_readback/_uninstall/_dryrun, tests/test_w124_4_dense_capture.py (11 tests), writers set in tests/test_box_tasks.py extended. Output: exp_output/PRICE_ARCHIVE_DENSE/{props,games}/ and exp_output/TRADE_PRINTS/ as .jsonl.gz (gzip members, read by io_jsonl). Already compressed, so retention has nothing to do until a POLICY entry is added.

## Limits (state them in any read of this data)
- Kalshi occurrence_datetime is about game END. Start is estimated as occurrence minus 2.5 h (NBA/NHL) or 3.25 h (NFL), +/- ~30 min; raw occurrence_datetime is on every row.
- Games with a 06-16Z start (rare) are only on the games line; props there are on the props line.
- Prints keep only tickers dated today ET; a late game dated tomorrow ET is missed until midnight ET.

## Expected gain once installed (not before; MEASURE MOVED: PROOF P3, none until installed)
- H1: props games per week with a full listing-to-start series; today the 06-16Z gap loses every early-listed prop.
- H4: game snapshot spacing 19-30 min -> 5 min in the 3 h before start.
- H3: forward trade prints for all NBA/NFL/NHL tickers of the day (about 14.6k per 6 min at peak) instead of 11-10 onward only for a sample.

operator decisions:
- [ ] Approve `archive_dense_install` (3 lines in deploy/cron.archive_dense) — only AFTER disk_retention_install has run or you accept dropping prints; as built it will refuse and change nothing.

surface_delta: +3 cron components (paused, not live). pattern_sweep: box_tasks writers set, registry, cron mirror, disk_retention POLICY (checked; no entry added). directive_conflicts: none found. vision_pillar: PROOF P3. gap_measure: none until installed. Words: hypotheses H1/H3/H4 stay open for R&D; nothing closed.
