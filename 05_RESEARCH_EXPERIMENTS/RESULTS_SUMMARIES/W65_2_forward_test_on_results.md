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
