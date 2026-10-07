# W57.3 — Truthful books on the Live Terminal (results)

Date: 2026-10-06 · Branch `w57-books-truth` · Tier STANDARD · Deliverable: Live Terminal placements truth + NFL paper-book finding.

## D1 — Paper ledger survey (VPS, read-only)
- T1 MLB and T4M-PROJ books are written by their live pipelines. T4M-PROJ portfolio: 0 open, 4,168 closed at survey time.
- **NFL game-market book: unmaintained.** No write in ~162h; 824 open positions, ~820 with past game dates. `deploy/cron.conf` has no NFL writer or resolver. The only resolver is manual (`scripts/apply_resolved_nfl_game_markets.py`, dry-run default). The writer script named in the brief does not exist in the repo. Registered **GG-490** (OPEN). No position was resolved or edited.

## D2 — Placements on the Live Terminal
- New `placements` field in `/api/data` → `decisions` (newest 30 T4M-PROJ open+closed positions: time, market, player, side, price, `size_usd`, status, outcome, P&L, label "flat-stake · ADR-0050 · paper"). New panel above the decision stream.
- **Premise correction:** the stake is not a constant $1. Recorded `size_usd` ranges 0.05–1.00 (e.g. $0.05 NO placements at price 0.005). The panel shows the recorded value.
- Mode tile and fire-rule text no longer imply nothing is placed.
- Blank-market evaluation rows are now hidden and counted in the stream header (`blank_dropped`). In the sampled local tail the count was 0, so the fix is defensive, not demonstrated on live data.
- Phone status bar: wraps and hides low-priority items under 700px. Measured page scrollWidth at 390px viewport: **774px before → 390px after**.

## D3 — C4 tile
Root cause: the systemd unit runs `/usr/bin/python3`, which lacks `jsonlines`; `jsonlines` is already declared as a dependency, the unit just doesn't use the venv. Fix: `_hard_limits()` tries the import, else reads `risk.py` literals with stdlib `ast`. No dependency change (pandas in the dashboard process was rejected as an OOM risk, GG-118). Registered and resolved as **GG-491**. Local verification: limit 0.20 read under `python -I`. Live-tile check is below.

## Evidence
Screenshots in `w57_3_screens/` (`index.before/after.png`, `phone.before/after.png`) — local dashboards on a read-only copy of the VPS portfolios and a 3,000-row cycle-log tail, old code from main vs this branch. Tests: `tests/test_w57_3_books_truth.py` (6) plus the existing dashboard suites. Embed (`Live Terminal.html`) re-synced from `_HTML`; byte-fidelity tests pass.

## Deploy / post-deploy
See the section appended after merge.

## Deploy / post-deploy (appended after merge)
- PR #172, CI green (`test` 6m43s), squash-merged as `00f8b59`. Deploy run 37553561725: success.
- **t4-mlb was NOT restarted** — GG-432 policy: `not_needed -- no file imported by t4-mlb changed in this push` (t4-mlb still on its 2026-10-05 07:57 start, NRestarts=0). `pmbot-web-dashboard` restarted 00:45:57 UTC, NRestarts=0.
- Running terminal (`/api/data` on the VPS under system python): 30 placements, latest the Chisholm YES $1.00 CLOSED LOSS row; **5 blank-market evaluation rows hidden** (the live blank-row defect, real), 0 blank rows rendered; both books report the 0.20 drawdown limit from the stdlib read, so the C4 source read works under system python.
- Not independently eyeballed in a browser against the live URL; verified via the live API and the local browser check on a copy of live data.
