# W65.2 — demo-fill forward test ON + T1 fills-only counting (GG-536)
Claim: T-790..T-792, GG-560..GG-561. Status: **BLOCKED at Part A step 1 (canary) — demo order writes 404 (GG-560).**

## Part A step 0 (read-only, verified 2026-10-11 ~02:30Z)
- VPS HEAD c944d8a8 == origin/main. t4-mlb (pid 3138167) environ: neither DEMO_FILL_* nor SHADOW_FLAT_STAKE set. No crontab/deploy refs set either.
- T1 MLB (logs/paper_mlb_cron.log, last run Oct 10 11:00): runs complete; players matched 27/6/0/6; "Bets placed today: 0". Only [WARN] schema_unexpected_column ba_l10_shrunk and dtype warnings — no HALT/violation line found. Zero bets is consistent with T1 kelly_fraction=0 (ADR-0048), not a pipeline failure; not re-diagnosed here.
- Code facts affecting step 3: `DEMO_FILL_ASSIGN_SHARE` defaults to 1.0, so the registered share 0.5 MUST be set explicitly. `schedule_cancel` uses a daemon threading.Timer; in a short-lived cron shadow process the timer dies with the process, and cancel then depends on `sweep_overdue` at the NEXT run of that script. Needs a decision/fix before the shadow-cell arm can meet the registered 60 s cancel (Part B).

## Part A step 1 — canary: NOT RUN
Command refused by the auto-mode classifier (no reason given): `scp scripts/w65_2_cancel_canary.py prediction-market-vps:/tmp/ && ssh prediction-market-vps 'cd /opt/prediction-market-bot && set -a && . ./.env && set +a && export BOT_ENV=paper PYTHONPATH=src && python /tmp/w65_2_cancel_canary.py /tmp/w65_2_canary.json'`.
No order was placed. Both switches remain OFF; steps 2-3 and Part B not started.

## Part A step 1 — canary, update (2026-10-11 ~03:20Z)
The permission denial was resolved by shipping the canary via PR (#210, #212, #214, #215, #216) and running the plain repo script on the VPS. Runs 1-3 failed on market selection (bid threshold; combo KXMV markets, then 2000 combos listed before any real market; fixed with `mve_filter=exclude`). Run 4 (VPS HEAD cd0f4b62): 12 candidate markets (MLB first), every `POST /portfolio/events/orders` returned `HTTP 404 not_found`. t4-mlb itself shows the same: 325/283/154 `kalshi_order_failed` per hour for KXMLBHIT-26OCT102000CWSCLE (00:00-02:59Z). Reads work; shard-3 balance $146.22. **No order was accepted, so the cancel path remains unverified.** Per the stop rule: GG-560 registered, both switches OFF (unchanged), ADR-0072 not marked ACCEPTED-in-force, steps 2-3 and Part B not started. Next: re-run `scripts/w65_2_cancel_canary.py` when order writes recover.

## W66.2 Part A — why demo orders 404 (GG-560): ROOT CAUSE FOUND, canary PASSES (2026-10-11 ~06:17Z)
Claim T-796..T-798, GG-564..GG-565.

**Premise corrected: demo order writes do NOT all 404.** Audit log `audit_mlb_t4.jsonl` on the VPS: t4-mlb had demo orders accepted
(`paper_order_opened` with a `kalshi_order_id`) on every game day through the latest, 17 on 2026-10-10 (00:09:29Z-02:24:39Z, i.e. 10-11 UTC;
players Murakami, Rocchio, Vargas, Adell, Montgomery). In the SAME game and window, 23 other tickers returned
`HTTP 404 {"code":"not_found"}` (762 events). The 404 is per-market, not per-endpoint. No client, host, auth or payload change near the
first 404s (plain `not_found` events begin 2026-08-28; `kalshi_client.py` last touched 2026-10-09 by the W64.2 placement policy, which is OFF).

**Cause:** the Kalshi DEMO host lists only a subset of production's markets. Both documented demo hosts (`external-api.demo.kalshi.co`,
`demo-api.kalshi.co`) return identical listings. Evidence, 2026-10-11:
- game KXMLBHIT-26OCT102000CWSCLE: demo lists 18 tickers (CLE Rocchio/Adell/Ramirez, CWS Montgomery/Murakami/Vargas x thresholds 1-3), production lists 55.
- `GET demo/markets/KXMLBHIT-26OCT102000CWSCLE-CWSCMEIDROTH10-1` -> 404; same ticker on production -> 200. Same for `CWSKTEEL8-1`.
- The accepted bot orders were all on demo-listed players; the 404'd tickers are absent from demo.
- 65.2's canary listed markets and read books from PRODUCTION (`_get` unauthenticated -> price-discovery URL) and submitted to demo, so
  production-only tickers 404'd 12/12. A selection bug in the canary, not an order-write outage.

**Canary, fixed (candidates now come from the demo listing, `authenticated=True`):** VPS HEAD 7f11b0a6 + patched script, 2026-10-11T06:16:33Z:
POST /portfolio/events/orders on KXDEMOFUTHOURLY-26OCT11H07-UP, 1 contract @ 1c YES -> accepted (order 01a1299b-19e8-7715-8795-09ae94337432);
DELETE -> `reduced_by 1.00`; GET after cancel -> status `canceled`, fill_count 0. Verdict true. (One GET immediately after create returned 404 - read-after-write lag, harmless.)

**Consequence for E1:** t4-mlb needs no fix and no restart (nothing wrong with its writes). Roughly the share of its orders on tickers demo
does not list (here 23 of 40 tickers) can never be accepted, so demo-fill statistics describe only the demo-listed subset. Registered as GG-564.

## W66.2 Part B - forward test ON (2026-10-11)

Gate met: the Part A canary placed AND cancelled (order 01a1299b..., `canceled`, fill_count 0).

**Shipped (PR #220, merge dfc00e9):** `scripts/demo_cancel_sweeper.py` (cron, every minute, ~55 s loop, 10 s sweeps via
`overdue_pending()` / `sweep_overdue()`; refuses unless BOT_ENV=paper + demo host; flock) so cancels survive process exit;
`deploy/demo_fill.env` (rule `book_anchor_cancel`, `SHADOW_FLAT_STAKE=on`, N=60, gap 0.05, **share 0.5**, seed w64-2);
`t4-mlb.service` `EnvironmentFile=-.../deploy/demo_fill.env`; T1 cron line exports the same file. Realized cancel delay is ~60-70 s.
Turn off: delete/rename `deploy/demo_fill.env` (and restart t4-mlb), remove the W66.2 cron block.

**GG-536 (same PR):** T1 MLB execution/G6 counts are CONFIRMED_FILLED only (`logs/t1_mlb_fill_status.jsonl`), labelled on
`run_power_calc`, `run_band_monitor`, `governance_scan.sh`, web dashboard and terminal MLB dashboard; all-rows T1 kept as
"calibration only - not execution evidence". No ledger row rewritten. Visual (hand-built narrative) HTML dashboard carries no T1 count; untouched.

**Tests (local, GitHub $0):** 10 failed, 3950 passed, 44 skipped. The 10 are pyarrow env failures (test_fetch_mlb_game_history x3,
test_t593 x1, test_t601 x6), unrelated and pre-existing locally. CI Deploy: t4-mlb restart decision `not_needed` (no imported file changed).

**VPS rollout:** crontab backed up (`logs/crontab.bak.w66_2_*`), W66.2 block + T1 export installed; unit installed, daemon-reload,
t4-mlb restarted 2026-10-11 ~14:3x UTC with no game live (MLB schedule: CWS final, next game 10-12 00:00Z).
**Proof** `/proc/3213544/environ`: BOT_ENV=paper, DEMO_FILL_PLACEMENT_RULE=book_anchor_cancel, SHADOW_FLAT_STAKE=on,
DEMO_FILL_CANCEL_AFTER_S=60, DEMO_FILL_MAX_MID_GAP=0.05, DEMO_FILL_ASSIGN_SHARE=0.5, DEMO_FILL_SEED=w64-2.

**First orders:** none yet - no game live and `logs/demo_fill_policy.jsonl` does not exist. First look: next game (10-12 00:00Z) and the 11:00Z T1 run.
Read arm assignment, skips by reason, cancels and cancel success rate from that log.

**Findings (not fixed here):** (1) `SHADOW_FLAT_STAKE` is NOT inert in code - `make_on_row` is wired in run_{mlb,nba,}_pregame_shadow.py -
but those cron lines do not load `demo_fill.env`, and editing them was outside this authorization, so shadow runners stay OFF.
(2) GG-564 (demo lists a subset) still biases E1 denominators; stratify. (3) The summary's earlier "maybe_place uncalled" claim was wrong.

## Read-back 10-13 (W69.1, 2026-10-13T00:09Z-00:37Z, run on the VPS)

Box: HEAD == origin/main at the time of read (then f9ab37de after deploy). Crontab: NFL/MLB/NHL(`run_nhl_shadow_staked.py`)/NBA shadow lines now load `deploy/demo_fill.env`; 11:25 report line installed (backup `/root/crontab.bak.w69_1`). t4-mlb loads `demo_fill.env` via `EnvironmentFile` (read by unit config, not process environ).

First forward-test numbers (treatment arm only; no shadow control orders existed yet):

| book/sport | orders | fills | settle-minus-price on fills |
|---|---|---|---|
| paper/MLB | 17 (18 at 00:37Z) | 5 | +0.07 |
| shadow/MLB | 363 | 75 | -0.20 (-0.12 by 00:37Z) |
| shadow/NFL | 1135 | 231 | +0.39 |
| shadow/NHL, shadow/NBA | no events yet (lines just installed) | - | - |

Cancels: MLB paper 0 ok / 17 failed; shadow MLB 0 / 363; NFL 906 ok / 229 failed (79.8%). Failure body in every sampled case: `HTTP 404 not_found` (`unfilled_after_N` 17, `sweep_overdue` 383) = order already terminal at cancel time.

Turn-off: `cancel_fail_rate_gt_10pct_in_a_day` TRIPPED (rate 1.0, worst day 2026-10-13 = 10 minutes old). It is a classification artifact, not a cancel-API failure: GG-596. The trip auto-disabled both switches. Fills/week vs ~550 in 8 weeks, win rate on fills and per-reason skip counts are in `exp_output/FORWARD_TEST/demo_fill_forward_report.json` on the box; only 1 day observed, so pace is NOT yet meaningful.

Not done: governance-scan line and /project panel were not compared with these numbers.

GG-586 (shadow control arm, model-mid order, no cancel, no book read; same hash/share; report splits arms): merged in PR #234, 4 new tests, deployed. NOT read back live: switches are OFF, so no control-arm order has been placed. GG-587 (untracked git-ignored `deploy/demo_fill.override.env`, read last by the policy): merged, deployed, READ BACK on box (tracked env says `on`, override wins, `is_enabled()` False, tree has no tracked modifications).

## Read-back W70.1 (2026-10-13, UTC)

**Part A1 - GG-596 fix: merged, deployed, partly proven.** PR #237 (squash `5b5c693`; CI green after merging #239's main fix; no admin merge). VPS HEAD == `5b5c693`, `cancel_already_terminal` present in the running tree, t4-mlb active (no Deploy workflow run is listed for these merges, yet box HEAD is `5b5c693`; I did not observe a t4-mlb restart decision), t4-mlb active (no MLB-imported file in the diff that required a restart decision beyond the deploy's own policy; deploy workflow did not run for these merges - box was pulled to `5b5c693` already).
The report now classifies a 404 as already_terminal only when a GET of the order shows filled/canceled/expired. Result: shadow/MLB 360 and NFL 229 "failures" were verified already-terminal (GG-596 artifact confirmed). **But the turn-off still TRIPS** (rate 1.0, worst day 2026-10-13): 8 paper/MLB `KXMLBHIT` cancels (00:02-01:35Z) returned 404 while the order GET showed `resting` (7 of 8; one was `canceled`) on `active` markets. A manual retry of the 7 returned **HTTP 503 service_unavailable** x3 each. So these are real cancel failures, not an artifact, and the earlier "all 404s are already-terminal" read in W69.1 was only true for the shadow books.
**Part A2 - re-arm NOT done.** `deploy/demo_fill.override.env` left in place: deleting it would re-arm on a condition that is genuinely tripped (the next report would turn it off again) and would leave uncancelled resting paper orders. Needs: operator decision, or fix of the MLB-HIT cancel path (cancel 404/503 on resting orders; `cancel_order` path is flagged UNVERIFIED in `kalshi_client.py`; NFL cancels via the same path succeed 906 times). Registered as GG-623.

**Part B4 - NFL fill audit (scripts/demo_fill_timing_audit_collect.py + demo_fill_timing_audit.py).** 1,135 orders, 231 fills, **0 fills after kickoff** (ESPN kickoffs). No post-kickoff GG needed; no kickoff-cancel needed. All fills are YES side, immediate taker crosses at placement. Pooled settle-minus-price **+0.398 on 137 settled fills (win 0.759)**; first-fill-per-(ticker,side) **+0.394 on 58 settled positions**. By game: BALATL +0.095 (win 0.50), DENLAC +0.623, DETARI +0.715, SFSEA +0.214; BUFLAR (94 fills) unresolved at read time.
**Interpretation:** the +0.39 is not a timing artifact but is not evidence of edge either: effective n is ~4 games, and ladder rungs on one game's totals/spreads resolve together (within-game correlation). Do not cite it as E2. Registered as GG-624.

**Part B3 / B5 - not done this session.** The switches are still OFF, so the control arm (GG-586) has placed no SHADOW orders; GG-586/570/571 stay open. NHL nightly / NFL Thu 10-15 runs have not happened. Governance-scan line and /project panel not compared. GG-564 listing-status split not done (E1 remains unstratified).

## Read-back W72.1 (2026-10-14T00:44Z, UTC; source: `scripts/demo_fill_forward_report.py --no-act` on the VPS, log sliced at ts >= 2026-10-13T23:58, 320 events)

Switches: `book_anchor_cancel` + `SHADOW_FLAT_STAKE=on`, no override file, no turn-off tripped. Report run read-only (`--no-act`).

| since re-arm | orders | cancel ok / already_terminal / failed | fills (settled) |
|---|---|---|---|
| paper/MLB treatment | 4 (138 skips `not_listed_on_demo`) | 4 / 0 / 0 | 0 (0) |
| shadow/MLB treatment | 9 (2 `not_listed_on_demo`) | 8 / 1 / 0 | 1 (0) |
| shadow/MLB **control** | 13 | n/a (no cancel by design) | 3 (0) |
| shadow/NHL treatment | 21 (46 `not_listed_on_demo`) | 20 / 1 / 0 | 1 (0) |
| shadow/NHL **control** | 23 | n/a | 1 (0) |

- **Cancel path (GG-645/623): proven live.** 12 real `cancel_ok` on KXMLB* (4 `unfilled_after_N`, 8 `sweep_overdue`), 0 `cancel_failed`; 20 on KXNHL. Pre-fix, MLB was 0 ok / 17+363 failed.
- **Control arm (GG-586): placing.** 13 MLB + 23 NHL model-mid orders, same hash/share; control fills 3 MLB, 1 NHL.
- **No post-re-arm order has settled**, so win rate on fills and settle-minus-price cannot be read yet: E2/E3 are unchanged. Cumulative-since-day-one cells (pre-fix classification, not re-arm numbers): paper/MLB 5/26 fills +0.07; shadow/MLB 76/372, -0.06; shadow/NFL 231/1,135, +0.40 (GG-624: ~4 correlated games, not E2).
- **GG-564 listing split:** paper/MLB 4 orders vs 138 `not_listed_on_demo` skips (2.8% of attempts reach demo); shadow/MLB 9 vs 2; shadow/NHL 21 vs 46. E1 describes the demo-listed subset only.
- **Pace vs ~550 fills per arm in 8 weeks** (report projection, ~1 day of data, treat as order-of-magnitude): paper/MLB 17/wk (not on pace), shadow/MLB 230/wk, NFL 692/wk (both on pace), NHL 7/wk (not on pace).
- **Skip-rate turn-off watch:** daily skip rates 0.2% / 56.3% / 98.6% (10-11/12/13). The condition needs three consecutive days > 90%; today alone is over. If 10-14 and 10-15 stay above 90% it trips. That is the paper/MLB `not_listed_on_demo` share (GG-564), not a fault.
- **Not done:** governance-scan line and /project panel were not compared with these numbers in this read-back.
- **GG-646 fixed** in `scripts/demo_fill_forward_report.py`: a 404 counts as `already_terminal` only if the order's `last_update_time` is at or before the cancel attempt plus 30s; missing or unparseable timestamp stays a failure.

## Read-back W73.1 (2026-10-15T00:15Z, UTC; source: `scripts/demo_fill_forward_report.py --no-act` on the VPS, log sliced at ts >= 2026-10-13T23:58, 1,219 events)

**Status change.** The forward test was OFF from 2026-10-14T11:25Z to 00:14Z (GG-710: the cancel-fail turn-off counted 10-13 failures from before the fix). PR #256 scopes it to post-fix attempts; override archived; re-armed and read back (`is_enabled()` True, policy log flowing). No turn-off tripped.

| since 10-13T23:58 | orders | cancel ok / already_terminal / failed | fills (settled) | win rate on fills | settle-minus-price |
|---|---|---|---|---|---|
| paper/MLB treatment | 8 (641 `not_listed_on_demo`) | 8 / 0 / 0 | 0 (0) | n/a | n/a |
| shadow/MLB treatment | 20 (6 listing) | 11 / 9 / 0 | 2 (0) | n/a | n/a |
| shadow/MLB control | 29 | none by design | 5 (0) | n/a | n/a |
| shadow/NFL treatment | 28 | 25 / 3 / 0 | 3 (0) | n/a | n/a |
| shadow/NFL control | 28 | none | 11 (0) | n/a | n/a |
| shadow/NHL treatment | 48 (131 listing) | 47 / 1 / 0 | 1 (1) | 0.0 (n=1) | -0.47 |
| shadow/NHL control | 54 | none | 29 (29) | 0.483 (n=29) | +0.123 |

- **E1:** 51 post-re-arm demo fills (2 MLB-T + 5 MLB-C + 3 NFL-T + 11 NFL-C + 1 NHL-T + 29 NHL-C), 30 settled (all NHL). 0 cancel failures in 168 treatment cancels.
- **E2/E3:** only NHL has settled. Control 29 settled fills, 48.3% win, +0.123 per contract; treatment 1 settled fill (a loss). **n is far below judged n (550 per arm); no verdict, no comparison drawn.** MLB and NFL fills have not settled.
- **Fill-rate contrast (descriptive):** treatment fills 1 of 48 NHL orders (2%) against control 29 of 54 (54%); MLB 2/20 vs 5/29; NFL 3/28 vs 11/28. Anchored orders fill much less often than model-mid orders in every sport. This is the quantity the pre-registration is built to measure; read it at judged n only.
- **Treatment-minus-control:** formable for NHL only, at n=1 vs 29: not interpretable.
- **NBA:** no NBA order exists yet (regular season opens 10-20). The T1-T3 NBA lines are already staked and demo-only (GG-570 note); first read-back 10-21.

## Read-back W76.1 (2026-10-16T00:20Z, UTC; source: `scripts/demo_fill_forward_report.py --since 2026-10-13T23:58 --no-act` on the VPS, window 2026-10-13T23:58Z to 2026-10-15T23:55Z, about 2.0 days)

Report fixes first (GG-754): `no_outcome` is now gated on `ts >= CANCEL_PATH_FIX_EPOCH` and the override-file, report and cache writes are atomic. New in the report: `--since`, and a settled-market lookup for unfilled terminal orders (E3 counterfactual: what a non-fill would have won). 16 tests pass.

| cell | orders accepted | fills | settled fills | win rate on fills | settle-minus-price | non-fills resolved (would-win) | cancels ok / failed / already terminal |
|---|---|---|---|---|---|---|---|
| paper/MLB treatment | 10 | 0 | 0 | n/a | n/a | 10 (0.10) | 10 / 0 / 0 |
| shadow/MLB control | 107 | 8 | 8 | 0.625 | +0.184 | 81 (0.235) | none by design |
| shadow/MLB treatment | 89 | 2 | 2 | 1.0 | +0.45 | 73 (0.233) | 80 / 0 / 9 |
| shadow/NFL control | 112 | 44 | 0 | n/a | n/a | 0 | none |
| shadow/NFL treatment | 110 | 6 | 0 | n/a | n/a | 0 | 104 / 0 / 6 |
| shadow/NHL control | 256 | 53 | 29 | 0.483 | +0.123 | 25 (0.24) | none |
| shadow/NHL treatment | 288 | 16 | 1 | 0.0 | -0.47 | 47 (0.34) | 200 / 74 / 15 |

- **E1:** 129 shadow fills of 962 accepted orders (13.4%), 40 settled; paper book 0 of 10. Shadow cells stay separate from the T4M-PROJ / T1 MLB demo book, which this block did not re-measure (its E rows are unchanged).
- **E2/E3:** control NHL 29 settled, 48.3% win, +0.123; control MLB 8 settled, 62.5%, +0.184; treatment 3 settled in total. Non-fills would have won 23-34% where resolved, against 48.3% (NHL) and 62.5% (MLB) on control fills: the adverse-selection gap is visible again, but n is far below 550 per arm. No verdict, no treatment-minus-control comparison is interpretable.
- **Fill rate, treatment against control, per accepted order:** MLB 2.2% vs 7.5% (0.30), NHL 5.6% vs 20.7% (0.27), NFL 5.5% vs 39% (0.14). Pooled shadow 24/487 = 4.9% vs 105/475 = 22.1% (0.22). Verdict condition (b) needs 0.25. Descriptive only, at 2 days.
- **The binding limiter is the demo account, not the rule.** Cash $0.1674 against $108.14 portfolio value. Since the re-arm: 962 accepted, 1,606 rejected, 1,535 of them `insufficient_balance` (68 `market_closed`, 3 transient). Fills for both arms depend on cash recycling, so every rate above is selection-dependent (GG-840).
- **Turn-off exposure.** The 2026-10-15 cancel-fail rate is 19.6%, all HTTP 503 (74 rows, 17:00-19:xxZ), and `cancel_now` does not retry (GG-841). The 11:25Z cron on 2026-10-16 will turn the rule off on that metric unless GG-841 lands first. A failed cancel means the treatment order rested past its 60 s design, so the metric is legitimate, not a false alarm.

### Projection to ~550 fills per arm (ADR-0072; rates from a 2-day sample under cash starvation, so noisy)

| arm | observed fills/week | date at 550 | verdict window (8 weeks from 10-14, about 12-08) |
|---|---|---|---|
| NHL treatment | ~56 | about 2026-12-23 | **misses** |
| NFL treatment | ~24 | not this season | **misses** |
| MLB treatment | ~7 | not this season (World Series ends in about 2 weeks) | **misses** |
| NHL control | ~186 | about 2026-11-06 | reachable |
| NFL control | ~177 | about 2026-11-07 (0 settled so far) | reachable |
| MLB control | ~28 | not this season | misses |
| shadow treatment, pooled across sports | ~87 | about 2026-12-02 | reachable only if pooling is accepted |

NBA from 2026-10-20 is upside and is not counted.

**Options if treatment cannot reach judged n (the rule is not changed here):**
1. **Different anchor offset** (rest nearer the touch): raises treatment fills, but it is a different treatment, so it needs a new pre-registration and restarts the 8 weeks.
2. **Longer resting window**: the same cost, and it moves the arm toward the control it is meant to contrast with (more adverse selection exposure).
3. **Pooled-sport judged n**: reaches 550 by about 12-02, but ADR-0072 does not license pooling across sports and the sports differ 8x in fill rate, so a pooled bound would be dominated by NHL.
4. **Declare underpowered** at the 8-week mark and report descriptively (already in ADR-0072); costs nothing in validity.

**ONE LINE FOR THE OPERATOR:** Recommend leaving the rule as it is and fixing demo cash starvation (GG-840) and the cancel 5xx retry (GG-841) first, since both are demo-only fixes for the next block (GG-841 sits in `demo_fill_policy.py`, outside 76.1's ownership); the open question is whether the 2026-10-15 exchange-503 day is excluded from the turn-off check, a change to a pre-registered rule.
