# Code Hygiene Audit — B74-A Session 1 (2026-10-15 UTC)

**VERDICT: SOUND WITH ISSUES — improved since 10-13.** No path places a real-money order; the data is clean (0 integrity violations across 106,012 rows in 81 ledger files copied read-only from the box); the crash-safety and deploy fixes from 10-13 (GG-661/663/664/665/666/667/668/672) are fixed **and running** (read back over ssh). The CRITICAL from 10-13 (GG-660) is gone from the live tree. What keeps this from plain SOUND: the kill switch is three unconnected switches and the main T1 order path has none (GG-745); four NFL positions have stayed open 4–7 days past the game (GG-746); the runtime registry cannot see the box and is still 75/75 unreviewed (GG-753); deploy has no rollback (GG-752); and the cron mirror, log rotation and fee-formula duplication are open or worse. Change since 10-13: 1 CRITICAL → 0, 3 HIGH fixed and running, 2 new HIGH found, 18 old GGs mostly closed, 21 new GGs (GG-745..765).

## Plain-English summary (5 lines)
1. Nothing can place real money today and the logged data is internally clean; the 10-13 crash-safety, restart and permission fixes are live on the box.
2. The kill switch is split: `touch` the wrong flag file and the main order placer never notices, and the NFL/T1 path has no check at all (GG-745).
3. Four NFL moneyline positions are still open days after their games ended, so the NFL book is not closing the loop (GG-746).
4. The runtime map exists but only reads the repo, never the box, and no entry has been human-reviewed yet (GG-753, Session 2).
5. Smaller debt: fee math inlined in 9 places, no deploy rollback, no log rotation, 162 type errors in the order code. Nothing was fixed in this session (Hard Rule 11).

Purpose: PLUMBING (each finding names the pillar it would corrupt). Branch `session/20261015T003528Z-b74a-s1-hygiene-audit`, claim T-975..979 / GG-745..774. Read-only on code; ssh read-only; audit tools in a throwaway Python 3.11 venv (`.audit_venv`, git-excluded, not in pyproject). Tree at origin/main a812dbd (includes W73.2 Part B, #258).

## Findings (ranked)

### HIGH
- **GG-745 kill switch is not one switch** — `run_t4_mlb_live.py:290` watches only `t4_mlb_kill_switch.flag`; `run_t4_live` another; `shadow_flat_stake.maybe_place:55` globs `*kill_switch*.flag`; C7 `is_kill_switch_active` writes no flag; `paper_trader.py:685` has no `halt_reason()`. No flag has ever been touched on the box. Pillar EXECUTION/PROOF. Fix: one shared check inside `submit_order`, C7 writes the flag, monthly canary.
- **GG-746 four NFL positions open 4–7 days after the game** — POS-BC7EBF8BB9, POS-5606773C7E (CIN-MIA 10-11), POS-0EED4809E1, POS-515DEC8556 (TB-DAL 10-08). Pillar EXECUTION/PROOF. Fix: read the NFL resolve path, close or explain, alarm on position age past game end.

### MEDIUM
- **GG-747** T4 portfolio 4,309 closed vs 4,275 resolved (34 gap). PROOF.
- **GG-748** four scripts rewrite the live T4 ledger non-atomically (`correct_t4_game_dates.py:133`, `gg271_bound_t4_rejected_positions.py:149`, `replay_harness_t427.py:210`, `tag_locked_pairs_t4_mlb.py:116`); `CellLedger.append` has no cross-process lock. PROOF.
- **GG-749** measurement-path failures swallowed or counted-not-alarmed (`run_t4_mlb_live.py:413-419`, `runner.py:68-72, 88-91`, `calibration_engine.py:311-317, 379-404`, T2 slot default 3.7, `stage_order` log-and-continue). PROOF/DEPTH/EXECUTION.
- **GG-750** t4-mlb loop has no consecutive-failure escalation (`:2037-2220`, GG-163 pattern); Kalshi client init failure silently makes orders `local_only` (`:1930-1934`). EXECUTION.
- **GG-751** settlement `return None` is indistinguishable from "not final yet" (`nfl_settlement.py:41`, `nba_settlement.py:44`, `mlb_settlement.py:32-53`, `nfl_espn_results.py:78`). PROOF.
- **GG-752** `vps_deploy.sh` has no rollback; `dirty_tree_abort` still exits 1; `deploy/demo_fill.env` tracked and tool-rewritten; no alarm on `deploy_status.json`. EXECUTION.
- **GG-753** `runtime_registry.py:66-101` never reads the box. Live `45 22 * * * run_mlb_pregame.py` is unregistered; the registry's `run_mlb_pregame_shadow.py --bands T1 --refresh` entry is not installed. Script also crashes on python3.9. PLUMBING.
- **GG-754** `demo_fill_forward_report.py:~207-211` `no_outcome` not epoch-gated (one pre-fix orphan re-trips the turn-off forever); `:306` (the override kill-switch file) and `:369` plain `write_text`. EXECUTION.
- **GG-755** fee formula at 9 src sites in 8 files plus `pregame_shadow/fees.py` (INFERRED 0.035 coefficient), ~17 script copies, no devig helper (GG-673 was 7). EXECUTION (E2).
- **GG-756** NFL engine not sport-agnostic and code ≠ INTERFACE.md (`engine.py:14-38,77`); rating layer is the frozen ridge, so D4 = scaffold only. DEPTH.
- **GG-757** `12_EXPLORATORY/nfl_engine/test_engine.py` is outside `testpaths` (`pyproject.toml:77`); invariants never run on push. PROOF.

### LOW
- **GG-758** silent-arm coverage coarse (postseason folded into `mlb_shadow`; MLB T2/T3 no arm; runs only in the full scan). **GG-759** three stale comments (`market_type_registry.py:~945`, `t4_fill_status.py:362`, `gg271…:~83`). **GG-760** mypy 162 errors on c4/c5/pregame_shadow, 5 on the order path. **GG-761** layering inversions and NBA sport defaults (GG-674 unchanged; c4/c6 clean). **GG-762** `mlb_game_pregame_features.py:88` timezone-fragile. **GG-763** NFL ties y=0.5, T4M-PROJ cross-path 187/2,080, 317 legacy null outcomes, GG-690/691 unchanged. **GG-764** read-side holes (`assert_ledger_invariants.py:145`, `validators.py:379`, `run_t4_mlb_live.py:1175`, GG-675). **GG-765** ADR-0070..0074 absent from APPROVALS_REGISTER; APR-0007/0016 dangling.

## Part A — mechanical sweep (diffed against 10-13)

| Check | Result | vs 10-13 |
|---|---|---|
| ruff (default) | see `.audit_out/ruff_default.txt`; swallow sites S110/S112/E722 = 21 | was 23 |
| ruff on NFL files | 27 errors, all style (UP045 37 lines, I001, C408, F401 4); none logic | new scope |
| bandit | collected; nothing on an order path flagged as new | not re-triaged line by line |
| pip-audit | 66 frozen venv pins: **no known vulnerabilities**. Base `requirements-base.txt` still unpinned (`nba_api>=`, `cryptography>=`) and pip-audit refuses it | GG-677 still open |
| secrets grep (NFR-05) | only dummy key `tests/test_gg303_order_id_write_defect.py:28`; `BEGIN .*PRIVATE KEY`: no files | clean |
| vulture ≥80 | all unused imports/variables, none on order/risk/ledger paths | clean |
| radon top 10 | collected (`.audit_out/radon.txt`) | — |
| mypy c4/c5/pregame_shadow | 162 errors (90 type-arg, 17 arg-type, 15 no-any-return, 14 no-untyped-def, 13 no-untyped-call, 6 assignment, 3 operator, 2 return-value); order-path: `kalshi_client.py:954/1024/1045`, `paper_trader.py:129/672/676`, `demo_fill_policy.py:215` | GG-760 |
| mypy NFL files (+transitive) | 98 errors in 17 files: 32 type-arg, 25 no-untyped-def, 13 arg-type | GG-760 |
| Step 2 stub scan | CLEAN — no stubs found | clean |
| `assert_ledger_invariants` on box copies | 81 files, 106,012 rows, **0 violations** (data present, not a vacuous 0) | clean |
| `gg_id_uniqueness_check` | OK, no duplicate ids (after adding GG-745..765) | clean |
| `check_register_parity` | `!!` ADR-0070..0074 absent; APR-0007/0016 dangling | GG-765 |
| `runtime_registry.py check` / `surface` | 76 mirrored / 76 registry; 75 unreviewed; 75 live, 21 no alarm | GG-742/743 + GG-753 |

### Test suite
- Result: **4132 passed, 1 failed, 44 skipped** in 17m38s (Python 3.11.15; audit venv resolved pandas 3.0.6 / numpy 2.4.6, **off the `pyproject.toml` pins** pandas<2.3, numpy<2.0 - all Part A numbers carry that caveat).
- Failure: `tests/test_generate_mlb_features.py:540` `TestPostseasonOptIn.test_default_output_unchanged` - golden SHA mismatch. Cause unverified (likely off-pin CSV serialization). Registered **GG-766** (LOW); not fixed (audit only).
- Skips (44): integration MLB smoke tests (missing feature CSV / model pkl / `VENUE_API_KEY`), live-network tests (GG-428), frozen NBA dataset, one GNU-date test.
- Coverage (line, total 60%): c4_risk_engine 92.0% (risk.py 91); c5_execution 86.1% (paper_trader 95, demo_fill_policy 96, shadow_flat_stake 84, kalshi_client 72); pregame_shadow 82.7% (ledger.py 97.8); atomic_io 83; c6_audit_logger 100; c7 91.5; `run_t4_mlb_live.py` 67. NFL engine: forecaster 62.0, model 87.7, settlement 95.1, **event_store 0.0% (161 stmts, no test touches it)** - folded into GG-757.

## Baseline table (GG-660..677, 690, 691)

| GG | Status now | Evidence |
|---|---|---|
| 660 `/vps` provisioning | fixed on disk only | file moved to `_archive`; header not read |
| 661 stale t4-mlb after deploy | fixed and running | t4-mlb started 02:53Z after last src commit; pending-restart retry fired |
| 662 `.env` mode | fixed and running | 600, `.bak` gone; owner is an orphan uid |
| 663/664 paper_trader atomic/save | fixed and running | read on disk and via deploy |
| 665 kelly from forecast | fixed and running | positive kelly remains only on non-operational bands |
| 666 live host guard | fixed and running | |
| 667 kill switch on shadow | fixed for shadow stake only | see GG-745 |
| 668 deploy failures | partly | no rollback, `dirty_tree_abort` remains → GG-752 |
| 669 healthcheck red | open | stale invariants |
| 670 log rotation | open | logs ~2G |
| 671 `date.today()` | not re-checked | |
| 672 shadow ledger torn line | fixed and running | |
| 673 fee formula | open, worse (9 sites) | GG-755 |
| 674 NBA defaults | open, unchanged | GG-761 |
| 675 demo-fill audit drops | open / not re-read | GG-764 |
| 676 cron drift | open | 22:45 live vs 18:45 mirror; 70 live vs 66 mirror → GG-753 |
| 677 hygiene/deps/root | partly open | unpinned base deps, root services, dormant `t4-mlb.timer` |
| 680 atomic writers | partly | missed writers → GG-748, GG-754 |
| 690/691 | present | 3,495 null market_type; 16 CANCELLED → GG-763 |

## Review methods run / not available
Part B ran as six parallel read-only lanes (L1 Orders, L2 Ledgers+data, L3 Failure handling, L4 Deployment, L5 Architecture, L6 Process/ADR-0074). **Ran:** `/hygiene` (read-only items 3, 4, 6 only: secret scan clean except two docstring examples in `run_exp004.py`/`run_exp010.py`; `BOT_C4_ACTIVE` is set in-process at `run_t1_nfl_game_market.py:63` and `run_t1_mlb_game_market.py:79`, after the paper-env guard, which the skill's "never set programmatically" expectation does not allow for; `BAND_CONFIGS` has 22 bands, positive kelly only on non-operational `T4`/`T5`/`T4-*` legacy bands and BLOCKED `T4M-ARITH` 0.1 / `T4M-FLOW` 0.08, zero on T1-T3, `T4M-PROJ`, NFL/NHL; VenueAdapter protocol OK). The skill itself is stale (329-test baseline, `prod_model.joblib` no longer exists, NBA-only wording): see GG-677. Items 1, 2, 5, 7-9 not run (item 1 superseded by the full suite below; 7 has no model file; 8/9 would edit files).
**Loaded as generic templates and applied through the six lanes, not as separate runs:** `engineering:code-review`, `engineering:architecture`, `engineering:deploy-checklist`, `engineering:testing-strategy`, `engineering:tech-debt`, `data:validate-data` (the last applied to the ledger-invariant evidence: row counts, nulls, dedup, tz).
**Failed to run:** `/security-review`: its own pre-command `git diff --name-only origin/HEAD...` errored with `fatal: ambiguous argument 'origin/HEAD...': unknown revision or path not in the working tree`; the worktree has no `origin/HEAD` and I did not alter git config to work around it. Security coverage instead came from bandit, pip-audit, the secrets grep and lane L1/L4.
**Not available:** `/deploy-audit` (`Unknown skill`; `.claude/commands/deploy-audit.md` exists on disk but is not a registered skill).
**Not run on purpose:** `/pregame` is NBA-era, needs `VENUE_API_KEY` and a live Kalshi call, and its checks assume `prod_model_meta.json`; skipped (read-only audit, no secrets on this machine).

## Not checked
- Anything on the box beyond read-only ssh (no crontab edit, no restart); Kalshi DEMO API not queried.
- W73.2 Part B event-store code (#258) and W73.3 got only the ruff/mypy pass above, no lane read.
- `.claude/commands/vps.md` header and GG-660 file move not read; GG-671, GG-675 pagination (897-915), GG-669, GG-670 not re-measured.
- Bandit findings not triaged line by line; radon not mapped to every order path.
- Non-demo behaviour of `BOT_ENV` per cron line (GG-666 per-line prefix).
- Python 3.12 (VPS) behaviour: audit venv is 3.11.

## Punch list (MEDIUM blocks)
1. **Kill switch unification** (GG-745): shared `halt_reason()` in `submit_order`, C7 writes flag, canary test. EXECUTION.
2. **NFL book closes** (GG-746, 751, 763a): read resolver, close/explain 4 positions, typed settlement result, age alarm. EXECUTION/PROOF.
3. **Registry sees the box** (GG-753, 742, 743; Session 2): `check --box`, review 75 entries, alarms.
4. **Ledger writers atomic + lock** (GG-748, 764, 747): route through `atomic_io`, flock `append`, reconcile 34 rows.
5. **Alarm the swallows** (GG-749, 750): counters and alarms on each listed site.
6. **Deploy rollback + cron mirror + log rotation** (GG-752, 676, 670, 669).
7. **One fee module** (GG-755/673) with a sweep test.
8. **Demo-fill report epoch gate + atomic writes** (GG-754).
9. **NFL engine to tests/, sport-neutral core** (GG-756, 757).
10. **Type ratchet and register parity** (GG-760, 765, 759, 758, 761, 762).
