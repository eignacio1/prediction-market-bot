# W96.3 results: B-003 (backlog on the dashboard) and B-004 (demo orders that cannot pay, GG-1481)

Sources: box read-only reads 2026-10-30 ~16:00Z (`logs/demo_fill_policy.jsonl`, first row 2026-10-11T16:38Z; bridge results `04_EXECUTION/BOX_TASKS/results/20261030T1600Z_w96_3_*`).

## Part A: B-003, the backlog on /visual: DONE (read back)
- PR #382 (`edda7ff`), CI green on the post-rebase head. Panel `#backlog` rendered from `ROLLING_BACKLOG.json`; `scripts/rolling_backlog.py` writes `ROLLING_BACKLOG.md` from the same JSON (`--check` fails on a stale .md or invalid JSON). A bad or missing JSON shows a visible error card.
- Box read-back (`dashboard_pages_read`, 2026-10-30T16:00:31Z): `backlog sections on /visual: 1` (was 0 before the deploy). `/visual` 200, 340,788 B. Dashboard `NRestarts=0`, `MemoryCurrent=62,951,424` against `MemoryMax=134,217,728` (55.1 MB before the merge; +7.9 MB, 47% of the cap).
- MEASURE MOVED: backlog on /visual 0 → 1.

## Part B: B-004, GG-1481 demo `insufficient_balance`
### What the data says (shadow books, `shadow_order` rows, ok=false)
| day (UTC) | placed ok | insufficient_balance |
|---|---|---|
| 10-12 | 650 | 4 |
| 10-14 | 207 | 25 |
| 10-15 | 755 | 1455 |
| 10-16 | 681 | 402 |
| 10-17 | 4192 | 233 |
| 10-18 | 7271 | 0 |
| 10-19 | 2451 | 312 |
| 10-20 | 7363 | 0 |
| 10-21 | 12621 | 0 |
| 10-22 | 7791 | 120 |
| 10-23 | 11790 | 341 |
| 10-24 | 12253 | 310 |
| 10-25 | 12876 | 75 |
| 10-26 | 8835 | 0 |
| 10-27 | 5449 | 255 |
| 10-28 | 7209 | 202 |
| 10-29 | 4542 | 9 |
| 10-30 (to ~15:38Z) | 2439 | 0 |

- **Since when:** first refusal 2026-10-12T23:13Z; last 2026-10-29T00:16Z. **Zero in the ~39 h since**, with 4,542 + 2,439 orders still placed. The balance read at 10-30 was $3,287.58 cash (W95.3); a top-up happened 10-16T05:40Z. 10-15 (1,455) preceded the top-up and was the worst day.
- **Which books:** shadow books on the shared demo account (NFL, NHL, NBA, MLB game-market shadow arms) and the paper T4 MLB book ($0.50 stakes; W95.3: 2,000 rejected on game dates 10-26/27/28, audit `kalshi_order_failed` 2,214 on 10-27 → 10-29, 00–04Z, all `insufficient_balance`). Paper T4 has placed no orders since: `audit_mlb_t4.jsonl` last written 10-29 03:13Z (cause of the silence not checked; likely no games).
- **Fills per day:** the shadow log has no fill event; the closest proxy is `cancel_already_terminal` with `order_status=executed` (an order that filled before its 60 s cancel): 10-14: 6, 10-15: 16, 10-16: 25, 10-17: 222, 10-18: 556, 10-19: 172, 10-20: 184, 10-21: 564, 10-22: 525, 10-23: 740, 10-24: 652, 10-25: 836, 10-26: 495, 10-27: 225, 10-28: 378, 10-29: 177, 10-30: 93. No shadow-arm breakdown is derivable from this log. Paper T4 fills: 5 of 32 orders, all before the top-up (W95.3), 0 since.
- **Balance over time:** NOT AVAILABLE. No balance series existed before this block; that is the gap GG-1481 named. It exists from the next refused order onward.

### Cause: not proven, not a code fault, and not currently occurring
- Refusals cluster at evening peaks (16–19Z, 23Z, 00Z, 06Z) and stopped after 10-29T00:16Z without any code change, which fits cash reserved by resting 60 s-cancel shadow orders on the one shared demo account (daily placed stakes of $5–11k against ~$3.3k cash), easing as volume fell. Still a hypothesis: nothing logged balance at the refusal.
- The W77.1 cash guard (`cash_skip_reason`) logged 0 `insufficient_demo_cash` skips, so it never saw a low balance at decision time.
- The only code-side remedy (reserve in-flight resting exposure in the guard) changes order gating, which this block may not touch. Not done.

### What was done
- PR #384 (`32ce531`, CI green on head `c8399c1`): `refusal_context()` in `demo_fill_policy.py` and the `kalshi_order_failed` payload in `paper_trader.py` now carry `size_usd`, `demo_balance_usd`, `demo_portfolio_value_usd`, `demo_balance_age_s`, `open_exposure_usd`, `open_positions_n`. Logging only: never raises, own 15 s balance cache (one GET per burst), no change to orders. 4 new tests; 111 passed with the existing fill-policy and paper-trader suites.
- Funds: The bot has no deposit call and I did not verify that Kalshi's demo API offers one; no top-up was needed ($3,287.58 cash, refusals stopped). Nothing added.
- Operator step (one line, demo, plumbing): if refusals return, top up the demo account by logging in at Kalshi demo; nothing else is needed from the operator today.

### Read-back still owed
The new fields reach the box with the next t4-mlb restart (`paper_trader.py` is imported by t4-mlb). The first `kalshi_order_failed` row carrying `demo_balance_usd` can only appear on the next refused order (next evening game window with refusals). That read, and the verdict on the cause, belong to the first block after it appears.

## Deploy read-back for Part B (box, 2026-10-30)
- Gate passed; box deployed `f6fb0463` (contains `32ce531`). `deploy_truth_read` 16:08Z: t4-mlb runs box HEAD code (started 16:06:33Z); decision logged: `restart -- t4-mlb imports changed: demo_fill_policy.py, paper_trader.py; no MLB game in progress`.
- Dashboard right after that restart (16:08Z): `/api/data` and `/visual` timed out at 60 s and memory read 123.6 MB of 134 MB. Re-read directly at 16:27Z (dashboard restarted again by a later deploy): `/visual` 200 in 0.88 s, `NRestarts=0`, memory 2.9 MB (fresh), box load average 3.7–5 on a 961 MB single box. Read as cold-start under load, not caused by the backlog panel, but the 92%-of-cap reading right after a restart is worth a look (not registered as a defect: one observation, recovered).
