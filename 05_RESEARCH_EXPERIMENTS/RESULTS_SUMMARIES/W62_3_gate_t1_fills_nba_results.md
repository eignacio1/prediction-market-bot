# W62.3 - stand-down gate loaded, T1 MLB fill audit, NBA flip dry run

Status: Part A DONE (this file); Part B: see below. Claim: T-756..T-758, GG-536..GG-537.

## Part A

### 1. t4-mlb restart (authorized once, ACTIVE_QUEUE "Needs your decision" 2026-10-08 ~18:25 PT)
Preconditions checked at 2026-10-09T06:14Z: Stats API schedule - 10-09 no games, the 10-08 game Final, next first pitch
2026-10-11T00:00Z (~41h out); T4 cycle log last row 03:26:09Z (168 min idle); service up since 2026-10-07 06:13Z.
One `systemctl restart t4-mlb` at 06:14:46Z. (My SSH session dropped with exit 255 right after; I did not repeat it.)

Proof the RUNNING process contains the gate:
- new MainPID 3104947, `ActiveEnterTimestamp` 2026-10-09 06:14:48Z, `NRestarts=0`, service active.
- VPS HEAD c9e2315 (#194, includes #193); `run_t4_mlb_live.py` on disk defines `stake_stood_down` (line 239) and calls it at
  line 1646; the file was last modified 2026-10-09 00:56:47Z, i.e. BEFORE the 06:14:48Z process start, so the new process
  imported it.
- Not yet observed: a stood-down row in a live cycle. The next live game (~10-11 00:00Z) is the first behavioral check;
  the service is idle until then (no cycle-log rows is expected, not an outage).
GG-527 -> RESOLVED on this evidence.

### 2. Does T1 MLB send orders to the demo venue? Yes.
Placement path: `run_mlb_paper_trade.py` (PIPE-05, cron 11:00Z) -> `PaperTrader.open_position` ->
`KalshiMarketClient.submit_order` whenever a signing key is present (`paper_trader.py:644-650`). Same code path as T4.
Ledger `logs/paper_portfolio_mlb.json`: 485 closed positions (T1 483, T2 2), game dates 2026-06-30..07-29; 431 carry a
`kalshi_order_id` / status `submitted`; 52 `failed: HTTP 410` and 2 `local_only` carry none. Example: POS-D33B57A9D4
(KXMLBHIT-26JUL261410HOUCWS-HOUCWALKER8-1, NO, $9.53) has an order id.

Classified with `t4_fill_status` generalized to be book-agnostic (`--book t1_mlb`, own sidecar
`logs/t1_mlb_fill_status.jsonl`, append-only, no ledger rewrite; rows with no order id and a failed/local_only status are
CONFIRMED_NOT_FILLED `no_order_accepted_by_venue`). Venue fills history was complete (2,578 fills, reaching back past
the oldest position), so nothing is UNVERIFIABLE.

| class | closed | settled WIN/LOSS | games | P&L total | P&L / bet | win rate | 95% CI on P&L/bet (game-clustered bootstrap) |
|---|---|---|---|---|---|---|---|
| all rows (calibration only - not execution evidence) | 485 | 469 | 173 | -$113.17 | -$0.241 | 48.0% | -1.365 .. +0.915 |
| CONFIRMED_FILLED (execution evidence) | 85 | 83 | 57 | -$124.73 | -$1.503 | 28.9% | -3.666 .. +0.631 |
| CONFIRMED_NOT_FILLED | 400 | 386 | 159 | +$11.56 | +$0.030 | 52.1% | -1.251 .. +1.332 |
| UNVERIFIABLE | 0 | 0 | - | - | - | - | - |

By how: 85 matched by order_id; 346 inside the fills horizon with no match; 54 never accepted by the venue.
Clusters are Kalshi events (one game); 4,000 resamples, seed 20261009. The 16 settled-not-WIN/LOSS closed rows (outcome not WIN/LOSS)
are excluded from the P&L table.

### 3. Verdict
The T1 MLB book can claim a calibration record (469 settled paper bets, -$113 and CI spanning zero) but not execution
evidence: only 83 settled bets (17.7%) were actually filled, and those lost $124.73 at a 28.9% win rate, while the 386
bets that never traded earned +$11.56 - the book's headline result is dominated by orders the venue never filled, and
the filled subset's CI (-3.67..+0.63) is too wide to claim either profit or loss. Descriptively, win rate on fills (28.9%)
is far below non-fills (52.1%) - the same selection pattern as T4M-PROJ; not tested here.

No T1 counting, status or ledger was changed (GG-527's decision covers T4M-PROJ only). Registered GG-536 for the operator's call.
Caveat: P&L above is the ledger's P&L (priced at the model's recorded entry), not re-priced at actual fill prices.


## Part B (NBA) — results

**t4-mlb deploy decision (PR #196):** `not_needed` (no t4-mlb-imported file changed). Real T1 sidecar written on the VPS (GET only): `logs/t1_mlb_fill_status.jsonl`, 485 rows = 85 CONFIRMED_FILLED / 400 CONFIRMED_NOT_FILLED, matching the audit.

**Step 4 — `scripts/w59_3_nba_flip_check.py` run 2026-10-09:** all 12 cells `NO-ROWS ... 0 rows, 0 valid -> leave NOT_IMPLEMENTED`, exit 1 (not ready, as expected). Valid-row output proven by fixture, `tests/test_w59_3_nba_flip_check.py` (writes only to tmp): a cell with one valid row prints `FLIP-OK  NBA_MONEYLINE/T1_MULTI_DAY: 1/3 valid rows -> promote_cell_status(MarketType.NBA_MONEYLINE, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW, superseding_reference="EXP-038")`, exit 0; bad sha / p_yes=1 / null mid / excluded rows are rejected.

**Step 5 — `scripts/remove_nba_preseason_cron.py`:** removes only the `# BEGIN/END EXP-038 NBA PRESEASON` block, backs up first, mirrors `deploy/cron.conf` + deletes `deploy/cron.nba_shadow_preseason`, dry-run by default, live `--apply` refused before 2026-10-21 10:00 UTC. Tested on a copy of the real VPS crontab (551 -> 543 lines; exactly the 8 block lines gone) and by `tests/test_remove_nba_preseason_cron.py`. NOT run on the live crontab.

**Step 6 — first-look release for NBA:** no break. `tests/test_w62_3_nba_release_rehearsal.py` proves seal@149 -> release@150 (manifest, REPORT, dashboard verdict), preseason rows excluded, look150 frozen across later games, look400 manifest at 400. Runbook section added to `04_EXECUTION/NFL_FIRST_LOOK_RUNBOOK.md`. No source change was needed.
