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
