# W55.1 — #159 landed; 26 stuck MLB positions booked from Kalshi settlement (ADR-0071)

**Date:** 2026-10-05 · **Claim:** T-676..T-679, GG-475..GG-476 · **Result:** DONE

## Deploy (D1)
- PR #159 (head 2421c0a, CI green, was a *draft* — marked ready) squash-merged as `49bf44c`.
- Deploy run 37280539639 success. GG-432 decision: `restart -- t4-mlb imports changed: paper_trader.py; no MLB game in progress`.
- VPS HEAD at check = `08332fe` (docs-only descendant; `49bf44c` is an ancestor).

## Backups (D2)
| file | sha256 (orig == backup) | backup |
|---|---|---|
| paper_portfolio_mlb.json | 19a1cf7771ab…831a1 | `.bak.20261005T075734Z` |
| paper_portfolio_mlb_t4.json | 338ef55ecd0c…598f0 | `.bak.20261005T075734Z` |
T4 moved afterward (t4-mlb live), so a second pair was taken immediately before the write: `.bak.20261005T225954Z` (T1 sha 19a1cf77…, T4 sha 9e9183aa…).

## Dry run (D3) — pre-registered expectation met
First attempt looked like "0 resolved" — that was a dry-run artifact (dry-run `continue`s before settle; the audit note "fetch_actual_hits returned None" is stale text) plus lost stdout. Re-run with captured output on ledger copies:
- 26 `DRY-RUN settles` (17 T1, 9 T4); 16 `scalar` (cancelled); xcheck_hits=None for all (statsapi 406 still open, cross-check only per ADR-0071).
- Real run on a second copy: T1 realized P&L −124.44 → **12.44%**; T4 −134.47 → **13.45%**. Both < 20%.

## Live write (D4)
Cron command line, same env, ~23:00 UTC 2026-10-05. Diff vs `.bak.20261005T225954Z`:
- T1: 17 open→closed, 16 `outcome=CANCELLED, cancelled=True`; bankroll 733.75→875.56; P&L −106.01→−124.44; 0 other changes.
- T4: 9 open→closed; P&L −128.99→−134.47; 2 new opens from live t4-mlb (expected); 0 pre-existing positions altered.
- Rejected lists identical.

## Live Terminal (D5)
`/api/data` (localhost:8050): T1 `last_updated 2026-10-05T23:05Z`, 0 open, P&L −124.44, freshness `ok` — no FROZEN. Checked via API, not the rendered page. The 0.106/0.129 drawdown strings in the payload are older audit-event copies, not the portfolio block.

## Caveats
- "0 cancelled counted toward G6": verified only the `cancelled` flag on all 16; the G6 counter itself was not re-run here.
- The resolver wrote ledgers while t4-mlb was running (same as the cron does); no corruption seen in the diff.
- Stats API 406 (GG-453/GG-470) still open — cross-check is dark.
