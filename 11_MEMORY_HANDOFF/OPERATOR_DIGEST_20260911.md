
## T-538/GG-255 — MLB game-market run script (2026-09-11)

Built the MLB half of the nine-cell game-market coverage target: a script evaluating moneyline, run line, game total, team total, and partial-game markets for MLB, ported directly from the already-proven NFL design.

Verified against live MLB market data with zero regressions, and confirmed the script refuses to act in five edge cases (kill switch active, no model, unparsed markets, ambiguous settlement, and — importantly — it can never touch either live MLB paper-trading ledger).

No capital moved, no live positions opened — paper-only infrastructure. A concurrent session's dashboard fix landed on main mid-session; picked up cleanly via rebase, no code conflicts, only a routine decision-log merge.

Branch is pushed; merge into main is next.

## T-541 — Dashboard "blind panel" incident (2026-09-11)

The dashboard showed a red "cannot fetch data" error on every panel, with all baseball panels stuck on "Loading." Fixed and confirmed working live.

Three stacked problems. First, the backend was crash-looping because reading one data file used far more memory than needed — most of it was data the dashboard never displays. Second, once fixed, requests got slow from an inefficient file-scanning method. Third, even after both fixes, a separate server setting was still capping how much processing power the dashboard was allowed to use. All three are fixed and deployed.

Confirmed with five real live requests: all succeeded in under a second with real baseball data. No other system (betting crons, data archiver) was touched.

## T-542/GG-271 — Bounding the rejected-orders file (2026-09-11)

This traces back to the same dashboard-outage chain as T-541: the T4 MLB portfolio file on the VPS was growing without limit because every rejected Kalshi order got appended to a list that never got trimmed — it had reached 39MB and 25,000+ entries. This session measured the problem, confirmed who reads and writes that data, and put a cap on it (most recent 2,000 rejections kept, older ones preserved in a separate backup file, nothing discarded).

The live file on the VPS was migrated down to 7.3MB with the trading service never restarted and open positions verified byte-for-byte unchanged before and after. Along the way, the migration script itself was caught reading a mid-write file and getting torn data, so it was rebuilt to do all its work inside the same lock the live trader already uses — a real bug caught before it could cause a second incident.

Dashboard response time is confirmed back under a second. GG-271 is marked resolved. The only remaining step is merging this session's branch into main, which needs a PR review since it touches trading code.
## T-544/GG-267 — Per-row NFL model provenance (2026-09-11)

Until now, a bet placed by the real trained model and a bet placed by the temporary stand-in model looked identical in the trading records — no way to tell which one made which decision. Fixed: every new bet now carries a label naming exactly which model produced it, shown on the dashboard next to each position. Older bets that predate this change safely show "unknown" instead of guessing or crashing.

Verified with a full new test set (8/8 passing) plus the entire existing test suite (88/88, zero regressions). One known gap: the dashboard's visual rendering wasn't checked in an actual browser this session, only through its underlying data — disclosed rather than hidden, and judged not to need a separate write-up.

Branch is pushed; opening a merge request into the main line is the next decision, not yet made.
## T-543/GG-274 — NFL Week 1 settlement gate check (2026-09-11)

Task was to settle the NFL opener shadow run end-to-end — but only after checking whether that shadow run actually opened any positions to settle. It hadn't been checked.

Checked two independent ways: the file that would hold those positions doesn't exist on the server, and a fresh read of that run's own log confirms it evaluated 827 markets and opened zero. Both checks agree with each other and with what was already on record.

Per your instruction, zero positions is a complete answer, not a problem to work around — stopped here. No score fetched, nothing settled, nothing touched on either live ledger. Whether the settlement path actually works against a real position stays open until a future shadow run opens one that survives to a finished game.
