# Code Hygiene Audit — W71.H1 (2026-10-13)

**VERDICT: SOUND WITH ISSUES** for a forensics pass to trust the logged data. The shadow arms append-only and the point-in-time feature builders I read are clean. Three things the forensics pass must know: (1) the paper ledger writer is not crash-safe (GG-663), (2) the only ACTIVE cell, t4-mlb, is running code older than main (GG-661), (3) one repo command (`/vps`) is dangerous if run (GG-660). Not run on the box, not edited.

## Plain-English summary (5 lines)
1. I found no path that places a real-money order today; protection is entry-point guards, not a hard rule in the order code (GG-666).
2. The logged data is mostly trustworthy, but the main paper ledger is written non-atomically and swallows read errors, so a crash can silently reset or lose rows (GG-663).
3. The live T4 process is running pre-GG-623 code because deploys skip restarts during live games and never retry (GG-661).
4. `.claude/commands/vps.md` is a May-2026 setup script. Running it today would append the cron mirror to the live crontab (every job twice), overwrite the model and pin old deps. Correction to the brief: it appends and duplicates, it does not replace the crontab. Harm is the same class (GG-660).
5. Several smaller issues (log growth, UTC dates, fee math copied in 20 places, an always-red healthcheck) are sized as MEDIUM blocks below. 18 GGs registered: GG-660..GG-677. Nothing was fixed.

Purpose: PLUMBING. Branch `session/20261013T235411Z-w71-h1-hygiene-audit`. Read-only on code; read-only ssh (one `git fetch` on the box updated remote-tracking refs only, as `vps_deploy.sh` does every 5 min).

## Findings (ranked)

### CRITICAL
- **GG-660 `/vps` provisioning command.** `.claude/commands/vps.md` (149 lines, last commit 2026-05-31). Step 7 `crontab -l > /tmp/existing_cron; cat deploy/cron.conf >> /tmp/existing_cron; crontab /tmp/existing_cron` appends the mirror: ~62 live jobs (incl. `vps_deploy.sh`) would run twice, shadow arms write every row twice. Step 4 `scp models/prod_model.joblib ...` overwrites the box model; step 3 pins `scikit-learn==1.8.0` + unpinned `nba_api>=1.5.0`. Pillar: BREADTH/PROOF/EXECUTION. Fix: archive with a DO-NOT-RUN header; replace with a read-only deploy-audit command.

### HIGH
- **GG-661** t4-mlb (pid 3223742, started 2026-10-11 16:35Z) stale: deploys at 00:33, 01:48, 23:53Z on 10-13 returned `skip_live_game` for demo_fill_policy / market_type_registry / kalshi_client (GG-623 fix). No pending-restart marker. Pillar EXECUTION. Fix: marker + restart at first no-live-game tick + age alarm.
- **GG-662** box `.env` and `.env.bak.20260915T055650Z` are mode 644 (owner foreign uid) and hold VENUE_API_KEY. Low exposure (single listener sshd), invariant violated. Fix: chmod 600, delete .bak, healthcheck assert.
- **GG-663** `c5_execution/paper_trader.py:346` `write_text` (no tmp+`os.replace`); `:200-210` and `:318-327` `except Exception: pass` then fresh state / stale overwrite. Atomic pattern exists in scripts/backfill_logic_epoch.py:127. Pillar EXECUTION/PROOF (E1/E2 source file). Fix: atomic write, quarantine corrupt file, halt.

### MEDIUM
- **GG-664** paper_trader.py:360,975,1064,1152,1206 ignore `_save()` return.
- **GG-665** risk.py:166 takes `kelly_fraction` from the forecast dict (default 0.25), not from BAND_CONFIGS (ADR-0048 zero not enforced here).
- **GG-666** `kalshi_client._post`/`submit_order` (553-575, 1048-1157) assert no host; `BOT_ENV=live` reaches prod. Per-cron-line `BOT_ENV` prefix unverified (cron.conf:110, 496-567).
- **GG-667** NFR-03 kill switch not wired to shadow runners or `shadow_flat_stake.maybe_place` (bypasses C4); t4-mlb poll 45 s.
- **GG-668** `vps_deploy.sh` failures are log-only; 3 `dirty_tree_abort` ticks on 10-13 (tracked `deploy/demo_fill.env` rewritten by a tool); no rollback; gate = 13 tests.
- **GG-669** `healthcheck.sh` is red daily (133x BOT_C4_ACTIVE, 23x Python 3.11) against stale Phase-0 invariants.
- **GG-670** no log rotation; logs 1.9G, exp_output 2.6G, journal 1.1G, disk 51%.
- **GG-671** `date.today()` used where UTC is documented (run_t4_mlb_live.py:1921,1969; paper_trader.py:150; etc.); correct only because VPS is UTC. Related GG-170.
- **GG-672** shadow `ledger._load` raises on one torn line; per-process dedup; `runner.py:90` swallow.
- **GG-673** fee formula inlined at 7 src sites + ~12 scripts copies.
- **GG-674** NBA-default sport params in venue layer; C7 baselines NBA/MLB only; NBA registry cells flip from a data file read at import; c3 imports pregame_shadow.contract.
- **GG-675** demo_fill_policy drops audit rows on OSError and never retries `cancel_failed`; kalshi pagination returns partial board as ok=True (897-915).

### LOW
- **GG-676** cron mirror vs live: `run_mlb_pregame.py` 22:45 live vs 18:45 mirror; 69/70 lines match; crontab installed by hand.
- **GG-677** /hygiene command stale; unpinned base deps; root-run services; dead t4-mlb.timer; legacy `run_t4_live.py` NBA cron outside the restart policy; swallow sites in verdict scripts (`nhl_shadow_eval.py:166`, `distance_to_optimum.py:47`, `run_mlb_dashboard.py:199` bare except).

## Part A — mechanical sweep (numbers)
Interpreter note: local default Python 3.9.6 cannot install the pinned dev deps; the suite was run under Python 3.11 (`/usr/local/bin/python3.11`). VPS is 3.12.

| Item | Result | Source |
|---|---|---|
| ruff default/F,E9,B,S | see raw outputs in session scratchpad; S110/S112/E722 = 23 hits, 1 bare except | `ruff check src scripts deploy --select S110,S112,E722` |
| bandit >= medium | 6 HIGH, all **false positives**: `hashlib.sha1` used as a non-security ID/blob hash (scripts/train_mlb_model.py:134, train_model_v2.py:143, train_model_v2b.py:127, verify_provenance_snapshot.py:66 (git blob id), c3_forecasting/forecaster.py:122, train_and_save_model.py:80). Fix hygiene: `usedforsecurity=False`. | hand triage |
| pip-audit | **Not run on requirements-base.txt**: `nba_api>=1.5.0` unpinned, pip-audit refuses (finding GG-677). | error output |
| secrets grep | CLEAN. Only 2 doc-comment matches (`run_exp010.py:25`, `run_exp004.py:12`, shell usage text). | /hygiene check 3 |
| prod Kalshi URL from order write | Not reachable from any configured entry point; library permits it (GG-666). | L1 read |
| vulture >= 80 | run; dead-code list in scratchpad, not triaged (no order-path hits found) | vulture |
| scripts/ one-offs (t4xx/w6x/run_t*_diag) | 17 files, none referenced from deploy/.github/tests; newest `w65_2_cancel_canary.py` 2026-10-13, oldest `run_t344_vig_sign_diag.py` 2026-07-12. Candidates to archive, none harmful. | git log + grep |
| radon C+ | 115 functions grade C or worse. Top 10: run_paper_trade.main 97 (F, legacy NBA entry), run_mlb_paper_trade.main 65 (F, **order path**), run_pregame.main 59 (F), run_exp001.run_experiment 44 (F, experiment), **c4_risk_engine/risk.py `_evaluate_forecast_impl` 44 (F, RISK path)**, **run_t4_mlb_live `_run_cycle` 43 (F, ORDER path)**, run_t2_mlb_sameday.main 41 (F, order), run_t4_mlb_live.main 39 (E, order), run_t4_live._run_cycle 39 (E, order), run_exp005.run_experiment 38 (E). Risk gate and the live T4 cycle are the two untestable-by-eye hotspots. | `radon cc src -n C` |
| mypy c4/c5/pregame_shadow | run; output in scratchpad, not triaged in full | mypy |
| pytest + coverage | see "Test suite" below | |
| /hygiene | Run (see below). The command itself is stale (GG-677). | |
| Step-2 stub scan | CLEAN — no stubs found (governance hook output this session) | hook |
| assert_ledger_invariants.py | "0 violations" is **not a clean result**: all 3 ledger sources were SOURCE_UNAVAILABLE in the worktree. Not checked. | script output |
| gg_id_uniqueness_check | OK — no duplicate GG ids (re-run after registration) | script |
| check_register_parity.py | run in Part A earlier; see scratchpad | script |

/hygiene results (read-only items): secret scan clean; BOT_C4_ACTIVE is set programmatically after a `BOT_ENV=paper` check in 5 entry points (run_t1_mlb_game_market.py:79, run_t1_nfl_game_market.py:63, run_mlb_paper_trade.py:85, run_t2_mlb_sameday.py:61, run_paper_trade.py:60) — by design, but check 4's wording ("never set programmatically") is stale; ExecutionBand has 22 members, active = T1,T2,T3,T4M-PROJ, VenueAdapter protocol satisfied; item 2 failed (`FeatureStore.FEATURE_VERSION` absent); item 7 failed (models/ gitignored, no prod_model.joblib in the worktree). MEMORY_BANK/TODO checks not done (not this block's scope).

## Test suite
**Not complete at time of push.** Under Python 3.11 with pytest-cov the suite was ~3% done after ~3 min (many tests skip; first 200 results: 0 failures). Full pass/fail, skips/xfails, coverage for c4/c5/pregame_shadow/ledger code and assertion-free tests are carried to **H2** (command: `PYTHONPATH=src pytest tests -q -rsx --cov=src/prediction_market_bot --cov-report=term` in `.audit-venv311`). Treat test health as NOT VERIFIED by this audit.

## Part B — judgment lanes
- **L1 Orders:** answers in GG-663..667, 675. Q: can code place a real-money order? Not from a configured entry point; the library does not forbid it. kelly_fraction 0 held in BAND_CONFIGS, not enforced at the risk gate. Kill switch 60 s: only t4-mlb has a file flag.
- **L2 Ledgers + data:** GG-663, 671, 672. Positives: shadow ledger append-only, no 'w' writes in the package; audit log append-only with a per-process lock (cross-process interleave unverified, likely fine for small lines). Look-ahead: NBA, MLB game and NFL builders read are point-in-time (strict `<` as_of, TI-01). Replay caveat: UTC `as_of` vs local game date may admit a same-evening Final in backtests. No smoking-gun leak found.
- **L3 Failure handling:** 23 swallow sites (S110/S112/E722); none silent on the order path except those in GG-663/664/675. No `|| true` in cron.conf. Retries bounded. t4-mlb main loop logs and loops forever on a persistent exception (no escalation).
- **L4 Config + VPS:** GG-662, 669, 670, 677. No separate demo/prod key variable names; **operator should confirm the `.env` key is demo.**
- **L5 Architecture:** C4 and C6 are sport-agnostic in code; C7/C8/venue layer are not (GG-674). Every SHADOW/ACTIVE cell has a runner; NBA 12 cells are NOT_IMPLEMENTED until the 10-20 flip though runner and silent specs exist. No MLB-postseason silent spec found. No c1..c8 import cycle.
- **L6 Deployment:** GG-660, 661, 668, 676. Box HEAD b9812c8 == origin/main minus one docs commit. Deploy lock (flock) and fail-closed gate with import-shadow check are good. Last 20 deploy decisions: 14 docs_only/deployed OK, 0 gate_red/verify_failed/policy_failed, but the 3 skip_live_game restarts above. Unit files for t4-mlb match repo. Deploy checklist: secrets perms FAIL, healthcheck FAIL, rollback missing, running-SHA verification missing.

## Review methods: ran / not available
Ran: ruff, bandit, vulture, radon, mypy, pytest-cov (3.11), secrets grep, 4 read-only lane reviews by subagent (L1+L3, L2, L4+L6, L5), /hygiene, repo checks. Skill map: `/hygiene` ran. The skills `data:validate-data`, `/security-review`, `engineering:code-review`, `engineering:deploy-checklist`, `/pregame` diagnostics, `engineering:architecture`, `engineering:system-design`, `engineering:tech-debt`, `engineering:testing-strategy` were **not invoked as skills** in this block; I covered their ground by direct review (deploy-checklist pass is in the L4/L6 lane; tech-debt ranking is the punch list below). `/vps` deliberately not run.

## Not checked
- Feature builders: `nfl_qb_features`, `nba_player_features`, `nba_minutes_features`, NHL features, `c2_feature_store/mlb_features.py` (the likeliest look-ahead spot for ba_l10 rolling windows).
- `deploy/*.sh` beyond grep; `venue_router`; `complement_lock_scanner`; `game_market_settlement`.
- Devig duplication (not exhaustively searched).
- Per-line `BOT_ENV` prefix on all cron lines.
- Live ledger invariants (no local data; the script's 0 is a no-data result). `data:validate-data` on judged ledgers (shadow arms, T4 resolved, forward-test report) therefore not done.
- Whether the box `.env` key is demo or prod.
- vulture and mypy findings not triaged line by line; ruff default output not triaged beyond S/E722.
- pip-audit (see above).

## Punch list (MEDIUM blocks for next wave, ranked by tech-debt value)
1. **M-A Ledger safety** (GG-663, 664, 672): shared `atomic_write_json`, quarantine-on-corrupt, check `_save`, tolerant shadow `_load`. Tests: crash-mid-write, torn trailing line. Smallest, highest value.
2. **M-B Deploy truthfulness** (GG-661, 668, 676, 669): pending-restart marker, status-file alarm, untrack tool-written env file, rollback script, healthcheck rewrite, running-SHA verify.
3. **M-C Retire /vps** (GG-660, 677): archive + read-only deploy-audit command; chmod 600 `.env` (GG-662) as a one-line operator action.
4. **M-D Order-path guards** (GG-665, 666, 667, 675): clamp kelly to BAND_CONFIGS, prod-host assertion, shared kill-switch helper, cancel retry.
5. **M-E Single sources** (GG-671, 673, 674): `utc_today()`, `fees.py`, required `sport`, baselines keyed by (sport, band).
6. **M-F Ops** (GG-670): logrotate + disk alarm.
7. **H2 remainder** (this audit): the Not-checked list above, led by `mlb_features.py` look-ahead and a ledger-invariants run against read-only copies pulled from the VPS.
Testing-strategy gaps: `risk.py::_evaluate_forecast_impl` (complexity 44) and `run_t4_mlb_live._run_cycle` (43) are the order/risk hotspots; coverage numbers below should be read against them.

## Operator decisions
1. Confirm `.env` VENUE_API_KEY is a demo key.
2. Manual `systemctl restart t4-mlb` in an idle window to pick up the GG-623 cancel fix (not done here).
3. Approve M-C: retire `/vps`.

## H2 remainder (W72.3 Part B, 2026-10-14)
Read-only copies of the VPS ledgers were pulled into the worktree `logs/vps_ro/` (gitignored, never committed): 3 paper portfolios (MLB T1, MLB T4, NFL game market), T4 resolved ledger, T4 outcome store, PREGAME_SHADOW / _NFLQB / _PRESEASON, `data/shadow`, and the W65.2 forward-test report.

**Ledger invariants** (`assert_ledger_invariants.py`, alarm-only): 16 violations in 48 runs, all one assertion (L, T1, enum). All 16 are `outcome=CANCELLED`, a stale enum, not corruption (GG-691). 24 band/cell assertion pairs were NOT EVALUATED because 3,495 records have no market_type (GG-690). Assertions G and K are clean on the 3,311 tagged T4M-PROJ rows. Nothing was run against GG-170's assertion A epoch-12 rate here; not a new finding.

**Data validation** (96,199 JSONL rows over 80 shadow/ledger files, plus 5,622 closed portfolio positions): 0 duplicate rows, 0 unparseable lines, 0 duplicate position_id or (player, ticker, entered_at), 0 resolved_at before entered_at, 0 closed positions lacking resolved_at, 0 out-of-range model_p or entry mid price, 0 tz-naive timestamps, 0 WIN/LOSS rows whose pnl sign disagrees. Limit: the shadow-file price and timestamp checks matched by field name; where a file used other names they were skipped, so "0" there means none found among known names, not proven absent.

**Point-in-time features** (`tests/test_point_in_time_features.py`, 7 tests, pass): corrupting a game's own row and every later row leaves MLB rolling features (`_compute_rolling_batter_features`, games 3/10/24) bit-identical; shuffled input is re-sorted, not leaked; NFL `team_rates`, `projected_starter`, `qb_epa` and league means ignore rows dated on/after the as-of date. Positive controls (perturbing a prior game) move the features, so the tests cannot pass vacuously. Not tested: same-date doubleheaders for MLB (sorted by game_date only, so order within a date is unspecified).

**Verdict re-stated:** no look-ahead found in either feature path; no data corruption found in the judged ledgers. Two data-quality gaps registered (GG-690, GG-691), none fixed here.
