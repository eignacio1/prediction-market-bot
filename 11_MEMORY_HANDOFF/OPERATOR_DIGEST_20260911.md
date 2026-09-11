
## T-538/GG-255 — MLB game-market run script (2026-09-11)

Built the MLB half of the nine-cell game-market coverage target: a script evaluating moneyline, run line, game total, team total, and partial-game markets for MLB, ported directly from the already-proven NFL design.

Verified against live MLB market data with zero regressions, and confirmed the script refuses to act in five edge cases (kill switch active, no model, unparsed markets, ambiguous settlement, and — importantly — it can never touch either live MLB paper-trading ledger).

No capital moved, no live positions opened — paper-only infrastructure. A concurrent session's dashboard fix landed on main mid-session; picked up cleanly via rebase, no code conflicts, only a routine decision-log merge.

Branch is pushed; merge into main is next.

## T-541 — Dashboard "blind panel" incident (2026-09-11)

The dashboard showed a red "cannot fetch data" error on every panel, with all baseball panels stuck on "Loading." Fixed and confirmed working live.

Three stacked problems. First, the backend was crash-looping because reading one data file used far more memory than needed — most of it was data the dashboard never displays. Second, once fixed, requests got slow from an inefficient file-scanning method. Third, even after both fixes, a separate server setting was still capping how much processing power the dashboard was allowed to use. All three are fixed and deployed.

Confirmed with five real live requests: all succeeded in under a second with real baseball data. No other system (betting crons, data archiver) was touched.
