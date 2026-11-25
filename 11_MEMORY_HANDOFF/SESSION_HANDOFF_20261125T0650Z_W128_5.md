# SESSION_HANDOFF W128.5 (TRUNCATED: operator shut down the machine; see commit range)

<!-- session-meta
task_id: W128.5
one_line_summary: Data offload scrapers built (not run), TRIAGE written, gate PASS, box peak RSS/runtime measured; mlb_boxscore re-probe pending
vision_pillar: DEPTH (D4) / PLUMBING
gap_measure: D4 families fetched by server: 0 -> 4 built (moneypuck, nhl_officials, nhl_goalie_logs, savant); mlb_boxscore pending
gap_delta: built, not run; nothing fetched until install approved
surface_delta: +1 install built, not run
pattern_sweep: Accept/Accept-Encoding header set in Http.open (single request path)
-->

## Strategic decisions this session
None. Implementation-only.

## What changed
- PR #584: scripts/data_offload.py, data_offload_install.py, deploy/cron.data_offload (paused registry entry), box tasks, retention target, 21 tests.
- PR #587: standard Accept header (statsapi answered the box 406 without it).
- 12_EXPLORATORY/data_offload/TRIAGE.md: SCRIPT / MUSE / ALREADY by QUEUE table.

## Per-scraper, measured on the box (systemd-run MemoryMax cap, rc=0)
| Family | Req | Bytes | Sec | Peak RSS | Result |
|---|---|---|---|---|---|
| nhl_goalie_logs | 25 | 22,841 | 24.1 | 26.0 MB | ok |
| nhl_officials | 25 | 5,185 | 23.7 | 26.9 MB | ok |
| moneypuck | 16 | 5,594,685 | 30.8 | 26.0 MB | ok (byte cap) |
| savant | 25 | 369,353 | 72.4 | 26.0 MB | ok |
| mlb_boxscore | 3 | 0 | 14.5 | 25.9 MB | HTTP 406 on the box, before AND after the Accept fix (re-probe 20261125T063734Z). Stays MUSE |

Cap 150 MB, one at a time (flock), window 09-15 UTC, 12 MB/night cap.

## Refusals (MUSE, no bypass)
nba_stats 403, nba_cdn 403, pfr 403. umpscorecards and kofsports return 200 but are not built.

## Terms
MoneyPuck: free for non-commercial use, must credit MoneyPuck.com. NHL domains: Content-Signal ai-train=no (we do not train AI).

## Gate
PASS. disk 68.0%, +12.0 MB/day upper bound (backfill nights), projected 30d 69.4% (ceiling 80%).

## operator decisions
- approve data_offload_install (gate PASS, 12 MB/day upper bound). NOT run. Confirm the MoneyPuck non-commercial/credit terms are acceptable.

## Part C (for the window's Monday message; not Muse-contacted)
Retire as "moved to bot cron" only after install approved AND first nightly run succeeds:
MoneyPuck C-922..C-1101, C-1378..C-1751, C-2138, C-3516..C-4347; NHL officials C-3399..C-3515; NHL goalie logs C-4348..C-4763; Savant boards per TRIAGE row. C-5128..C-5487 (mlb_boxscore) are NOT retired: 406 persists on the box.
MUSE-only, by value: (1) NFL personnel/tendencies C-4764..C-5019 (check nflverse overlap first), (2) browser-only NBA tables, (3) umpscorecards/kofsports (reachable, unbuilt), (4) snapshots/judgment work. R/B/snapshot labels were not in the QUEUE table I read; map them in the Monday message.

## One thing pending
mlb_boxscore re-probe read: still 406 from the box. C-5128..C-5487 stay with Muse (do not retire). Optional: ask whether statsapi blocks the box IP; no bypass.

## Resume
git fetch origin; read the result file above. ACTIVE_QUEUE row not updated. Session claim not closed; run scripts/close_session_claim.sh "W128.5" "<summary>" and generate_session_artifacts.py on this file.
