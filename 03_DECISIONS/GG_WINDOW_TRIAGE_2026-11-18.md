# Window triage for the gap burner — 2026-11-18 (SW-9)

**Last reviewed:** 2026-11-18. Operator 11-17 22:03 PT: the window has the project-wide context a terminal lacks, so it judged which
OPEN gaps are already fixed, whose premise is gone, and which are registered data limits rather than defects. Read from the 264 OPEN
titles at e7f35cf (11-18 06:05Z). **The gap burner applies this list**: it owns gap statuses. Per gap it spot-checks the evidence named
here (one grep, one file or one box result) and writes the status line with the reason below. Any line it cannot confirm in a minute
stays OPEN and goes on its report. Nothing here is deleted; every closure carries its reopen trigger.

## A — fixed, with evidence (14)
| GG | Evidence |
|---|---|
| GG-1935 | Daily breaker was a real-money cap on the demo path; caps separated (#504) and raised (#514, operator-approved 11-17). |
| GG-1939 | Router ERROR = KeyError market_ticker in LeafMap.row_for; fixed #503 / #507 (W116.3), d6_read 11-18 shows routed rows. |
| GG-1953 | NHL store shrunk 2,049 → 270 MB peak (#507) and installed 11-18 05:04Z (results/20261118T050412Z_nhl_event_store_install.md). |
| GG-1898 | NHL event store has its box job: same install, readback results/20261118T050414Z_nhl_event_store_readback.md. |
| GG-1944 | Depth at submit is logged on arm orders: #512 (W117.1). |
| GG-1942 | Arm-order book is advisory in the exposure gate: #508 merged, box deployed 11-18 (box HEAD 8f8b560d). |
| GG-611 | EXP-040 shadow logging wired: silent_arms_read 11-18 02:36Z "NBA player points minutes+injury challenger (EXP-040): rows written". |
| GG-1450 | EXP-044 / 044b installed: same read, "NBA engine v1 (EXP-044) / v2 (EXP-044b): rows written". |
| GG-1581 | OOM-killed T3 shadow cycles: flock lock added, OOM kills 142 / day → 0 (W95-100); budget_read 11-18 0 stale / down. |
| GG-406 | Shadow code auto-pulled: vps_deploy runs every 5 min; deploy_truth_read 11-18 shows services 0.0 h behind HEAD. |
| GG-538 | Pre-2026 Kalshi history is on the VPS, sha-verified (dashboard assets; GG-538 copy completed). |
| GG-740 | Answered by ADR-0074: runtime registry (95 live, 0 unreviewed), pattern sweep (Hard Rule 13). |
| GG-741 | Answered by ADR-0074: window error log (W1-W58), Pushback / Surface / Dependencies lines in every wave (Hard Rule 15). |
| GG-154 | CLAUDE.md "Right now" is generated from the code and checked every session (scripts/claude_md_now.py); box reads replace ssh. |

## D — premise gone (reason · reopen trigger)
**Legacy MLB books (T4M-PROJ, T1 MLB) — idle since the World Series; the router and arm orders replace them (ADR-0077); MLB 2027
opens on the 2026 look-back leaf map (W118.1).** Reopen any of these if T4M-PROJ or the T1 MLB book trades again:
GG-098, GG-105, GG-140, GG-150, GG-153, GG-189, GG-209, GG-296, GG-301, GG-304, GG-307, GG-320, GG-323, GG-344, GG-536, GG-747,
GG-1190, GG-1441, GG-1582, GG-168.
*Kept OPEN on purpose:* GG-164, GG-166, GG-170, GG-190, GG-196 (game_date corruption) — W118.1 reads 2026 MLB rows and must check them.

**Legacy in-play (T4 / T5) design items — no in-play arm runs; the doctrine builds pre-game first and an in-play tree must earn its
speed (ADR-0068, DOCTRINE).** Reopen when an in-play arm is proposed: GG-007, GG-038, GG-039, GG-040, GG-046, GG-066, GG-202.

**The old NBA book (frozen, adjudicated GG-034 / GG-037):** GG-037, GG-041, GG-630.

**Legacy NFL T1 paper book (stub model; superseded by shadow arms + arm orders):** GG-295, GG-316, GG-317, GG-562.

**Paper fills as evidence — superseded by fills-only counting (GG-527):** GG-157, GG-161.

**Superseded documents and tools:** GG-094 (premise "MLB is the sole ACTIVE pool" is gone; depth is tracked as D1-D6), GG-172
(MARKET_EXPANSION_ACTION_PLAN superseded by the rolling backlog and DOCTRINE.md), GG-345 (MLB probes moved to HEALTH_PROBES.md, run
in season only), GG-423 (Live Terminal rebuilt for in-season sports, #491), GG-349 and GG-417 (Cowork shared-tree sandbox no longer
used; windows run in isolated worktrees).

**By operator directive:** GG-174 (Polymarket tag — "No Polymarket build work"; reopen if Polymarket activates).

**Permanent historical fact, nothing to fix:** GG-156 (no MLB price archive before 2026-08-01).

## L — registered data limits, not defects → status `ACCEPTED UNCERTAINTY`
Doctrine: free sources only, ever (operator 11-17); "a factor only a paid source has is a registered gap". These stay registered (the
data-gap inventory the engines plan around) but are not open defects. Reopen if a free source appears.
GG-730, GG-731, GG-732, GG-733, GG-734, GG-775, GG-776, GG-777, GG-778, GG-779, GG-800, GG-801, GG-910, GG-911, GG-912, GG-1013,
GG-1060, GG-1061, GG-1062, GG-1031, GG-1090, GG-1251, GG-1261, GG-1302, GG-1895.

## Counts
A 14 · D 44 · L 25 → 83. OPEN 264 → ~181 before the burner's own A / B finds.
