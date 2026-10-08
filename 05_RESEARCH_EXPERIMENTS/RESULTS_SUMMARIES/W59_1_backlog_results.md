# W59.1 — Gap backlog results (2026-10-08)

**Status: DONE.** Parts A, B, C, D done. Part C (GG-498): PR #183 (squash 58dc28c, CI green, merged by me) made `deploy/cron.conf` match the live crontab; T-601/T-602 uninstalled drafts moved to `deploy/cron.drafts.conf`; GG-498 RESOLVED and archived. At close the live log has 158 headers = 158 status lines, OPEN 136 (the rise from 131 is other sessions registering new gaps; the 131 re-verified entries were not reopened); uniqueness check passes.

## OPEN before -> after
176 -> 131 (45 retired to the archive). Parity 153 headers = 153 status lines; `gg_id_uniqueness_check.py` passes.

## Verification statement (corrected)
An earlier pass of this block annotated ~90 entries "Not re-verified this session; entry stands as written". That was corner-cutting and was reversed: every remaining OPEN entry was re-checked with this-session evidence (repo at origin/main, tests, VPS read-only logs/ledgers) and now carries a dated W59.1 current state plus smallest next action. Four read-only runners handled the last 32 in parallel; two V5 entries (GG-216, GG-228) had wrong evidence and were corrected in V6. Evidence strength varies: several OPEN entries are confirmed "still true" by code reading only, and some remain only partly verified (GG-299, GG-326, GG-408, GG-416 list what was not checked).

## Findings worth the operator's attention
- GG-228's live body had been overwritten by a copy of GG-226's body (pre-dated this session); restored verbatim from f9891f4. The hazard (Monday 14:20 UTC rebuild of the T4 resolved ledger, `deploy/cron.conf:315`) is real.
- T4M-PROJ epoch-12 P&L is negative overall (-0.0481/bet, n=1898); the 08-04..08-07 outage bucket (+0.2751/bet, n=153) is still anomalous (GG-196).
- 4169 of 4181 closed T4 positions carry `kalshi_order_status="submitted"`, which is never re-polled (GG-300/304).

## Still-open items by what they block
Scores/G6: GG-300, GG-301, GG-204, GG-320, GG-296, GG-285, GG-196.
Data integrity: GG-166/GG-170, GG-189, GG-333, GG-323 (state fields exist on only ~5% of cycle-log rows, forward-only).
Ops/safety: GG-441, GG-038, GG-347 (unattributed t4-mlb restarts), GG-344, GG-498, GG-046.

## Needs an operator decision
2. GG-285: a practicable P&L gate.
3. GG-289: how classifier-flagged self-modifying scripts get approved.
4. GG-441 and GG-320 (as previously recorded in their entries).

## Noted, not fixed (register-and-stop)
Stale "Gaps by Arm" index at top of the log; session-start hook count (176/365) is stale (GG-426); odd severity tokens ("ADR-0052", "ledger") on two OPEN entries.
