# T-600 — Live Terminal landing (Wave 43.2)

Branch `session/20261001T012448Z-live-terminal-landing`. Commits: D1 `58cfe4d`, D2 `772a562`.
No GOVERNANCE_GAP_LOG.md / DECISION_LOG.md writes (43.1 owns them).

## D0 — predecessors / sync
Nothing to land. Only unmerged dashboard-adjacent branch (`...nfl-capture-gap-0912`) adds a cron.conf entry: out of scope, untouched.
origin/main before: `633e1b5`; after (T-600 claim commit): `d27d60e` (origin/main kept moving from concurrent claims; now `4fd17f7`).
Claim: T-599 was refused (concurrent session held it); re-checked and claimed T-600; uniqueness verified (1 in claims, 1 in git log) per GG-322.

## D1 — byte-faithfulness (proven)
`_HTML` in `scripts/web_dashboard.py` is a verbatim raw-string embed of `Live Terminal.html`.
- Source file is the source of truth; D2 wiring edits were made to the page, then re-embedded (embedding is fixed, never the page to fit it).
- Proof levels: in-process equality; pytest over real HTTP (`/` and `/index.html`, plus Content-Length); real `web_dashboard.py` subprocess, `curl /` then `cmp` against the source -> BYTE-IDENTICAL after D2 as well (59,130 bytes served).
- Test: `tests/test_web_dashboard_terminal.py::TestTerminalByteFidelity`. Mutation-checked: a one-byte change after `</html>` -> 3 failures; restored -> pass. (A first mutation attempt matched nothing and proved nothing; redone.)
- DEMO fallback and NOT CONNECTED banner survive (test-guarded).

## D2 — additive /api/data keys (all existing keys unchanged; each via safe())
| key | what | tests (tests/test_web_dashboard_terminal.py) |
|---|---|---|
| `rejected_counts` | `{mlb, mlb_t4, nfl}` int, `None` = unknown. Streaming bracket-depth count, 1 line in memory (<=1 MiB), (mtime,size) cached. Arrays never enter payload. | `TestRejectedCounts` (6): per-pool counts incl. 2000 ring-buffer cap and tricky strings; missing file -> None not 0; array not last key; over-long line -> None; cache invalidation; failure isolation |
| `t4_cycle_tail` | last 200 rows (~92 KB) of `.vps_t4_mlb_cycle_log_cache.jsonl`, falling back to `t4_mlb_cycle_log.jsonl` (the VPS-native name). Backward-chunked `_read_tail_lines`. | `TestCycleTail` (4): bounded+ordered; fallback/empty; spy asserts only bounded <=64 KiB reads; failure isolation |
| `process` | `{started_at, sha}`; both captured at import so sha = code the process loaded, not what is on disk | `TestProcessInfo` (4): shapes; fixed-at-import; resolver degrades to "unknown"; additive-only key-set assertion |

Terminal wiring: status bar `SHA <7-char>` (tooltip: full sha + start time) and `T4 <cyc/min> · last <age>` cycle-rate readout; footer shows rejected counts; CONTRACT comment and DEMO payload extended. Degrades to "—" against an older server. `TestTerminalWiring` guards it. Page JS parse-checked (JXA `new Function`). 31/31 tests pass in the two dashboard test files.

## D3 — local verification (real subprocess, like Reload Dashboard.command)
Realistic dir: main-tree `.vps_*` caches (t4 portfolio 8.9 MB, mlb portfolio 0.6 MB, cycle log 28.9 MB) + a SYNTHETIC 50 MB `audit_mlb_t4.jsonl` (the real 433 MB audit is not local; tail read is size-independent). Not VPS-measured.
- `GET /` -> 200, ~0.001 s, 59,130 B.
- `GET /api/data` -> 200; 0.561 s first (cold count), 0.225 s, 0.209 s; 5.74 MB payload. Well under 5 s.
- Costliest keys: `rejected_counts` cold 0.40 s (cache hit ~0 s), `t4_portfolio` 0.126 s; everything else <0.01 s.

## D4 — restart: SKIPPED
No authorization line naming `pmbot-web-dashboard` under "Needs your decision" (ACTIVE_QUEUE.md row 445 still says it needs one; re-checked at end of session). Nothing restarted/reloaded/reconfigured on the VPS. Stopped at pushed, tested commit `772a562`. There is NO running sha to report: the VPS process is still the old one and shows the old page until restarted. Once authorized, verify from the running process: GET `/` vs file on disk, `/api/data` for `rejected_counts`/`t4_cycle_tail`/`process`, and compare `process.sha` to the deployed commit.

## GAPS FOUND -- FOR REGISTRATION
1. `portfolio` (MLB T1) and `nfl_portfolio` still carry `rejected_positions` in the payload (16 entries locally; bounded by the 2000 ring buffer, but contradicts "rejected array stays dropped"). Only `t4_portfolio` drops it. Pre-existing; left unchanged (existing keys must not change).
2. Step 4: `CONTAMINATION_HALT` count = 161,952 in `audit_mlb_t4.jsonl` — expected-at-game-end per CLAUDE.md, but the magnitude was not diagnosed.
3. Step 4: `SemanticFloorViolation` count = 1, and one 0-player T1 run among the last 6 — not diagnosed (out of scope).
4. Q7 `assert_ledger_invariants.py` is vacuous in a fresh worktree (`logs/.vps_*` caches absent -> SOURCE_UNAVAILABLE, 0 violations is meaningless there).
5. Compass OS Health line in governance output is 5,159 chars (noise).
6. Claim race: T-599 collided with a concurrent session (GG-162 class; T- numbers protected, handled by retry).
7. `process.started_at` is module-import time, not kernel process start; sub-second difference, noted for accuracy.
8. `rejected_counts` relies on the writer's indent=2 layout for bounded line length; a compact-written file yields `None` (safe, but loses the count).
