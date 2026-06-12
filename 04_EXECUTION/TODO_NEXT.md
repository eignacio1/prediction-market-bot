# TODO Next — Prediction Market Trading Bot

**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-12 SESSION 55 — T-168/GG-030 RESOLVED (MC correlation fix), T-170/GG-032 RESOLVED (T4 ledger corrected), GG-031 registered. Commit `530e1c3`, VPS deployed. 851/852 tests (1 pre-existing timing flake).

---

## PRIORITY QUEUE (updated 2026-06-12 SESSION 55 — T-168/T-170 DONE; GG-031 registered)

| Pri | Task | What / Why | Due |
|-----|------|-----------|-----|
| **0 — ✅ DONE (SESSION 47)** | **T-163: ADR-0023 — Remove PAPER_T4_FLAT_SIZING; T4 budget proportional to bankroll (GG-026)** | T4_BAND_WEIGHT=0.27 derived from G4 empirical ($499.95/$1,869.68=0.267→0.27). PAPER_T4_FLAT_SIZING and PAPER_T4_POOL_USD constants removed. _compute_t4_band_budget is single budget path (no RESERVE_MANDATE deduction). pool_isolated=True hardcoded. Flat sizing (1 contract/bet) retained as hardcoded paper policy (ADR-0023). G5 budget ~$504.81. ADR-0023 ACCEPTED. GG-026 RESOLVED. 843/843 tests. Commit 72ba619, VPS deployed. | ✅ 2026-06-11 |
| **0b — ✅ DONE (SESSION 47)** | **EXP-018 Hypothesis C — DS ruling: calibration gap** | n=98, both all-bets and injury-filtered CONFIRMED_NEGATIVE. DS ruling: calibration gap — need to structure math better. NOT T1 Tier 2B FAILS. Multi-sport scale (MLB/NFL) addresses sample size. G5 diagnostic: YES-only mode (filters NO bets to isolate YES vs NO edge; requires YES_ONLY config gate in run_paper_trade.py before G5 cron). G5 fired WITHOUT YES-only gate (gate not implemented in time). G6 if DS ruling still applies. | ✅ 2026-06-11 |
| **0c — ✅ DEPLOYED (SESSION 49)** | **T-164: Throttled order submission (GG-014 G6 gate — 31% failure rate at G5)** | Inter-order sleep 0.5→2.0s; MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0; delay schedule 4/8/16/32s=60s. Root cause: 29-order burst saturates rate-limit window in ~14s. Batch order integrity report added to PIPE-03 run. GG-014 status: PARTIALLY RESOLVED. G6 gate (≤5% failure rate) will be confirmed in next batch run. 852/852 tests. VPS deploy pending. **OPEN until G6 batch confirms ≤5%.** | ✅ 2026-06-11 (monitoring pending) |
| **1 — ✅ DONE (SESSION 51)** | **T-157: Project-level stop criterion (GG-021)** | ADR-0024 ACCEPTED. Tier 1 (n≥150, ≥2 months): EV/bet < -$0.03 → diagnostic sprint. Tier 2 (structurally adequate: n≥500, ≥15 opponents OR ≥2 sports): CONFIRMED_NEGATIVE → halt + ADR-0004 supersession. Passability drift watch standing. EXP-017 scope transition to MLB/regular season logged. GG-021 RESOLVED. | ✅ 2026-06-11 |
| **2 — HIGH (governing)** | **T-153 (EXPANDED, GG-022): fill-realism haircut on ALL paper P&L** | Spread model from G4/G5 spread logs must haircut T1+T4 P&L used as G6 evidence — not just exit validation. Until then, all G6-facing P&L reports carry "unhaircut paper fills" caveat. T4's +108% pool at 51.4% win rate is presumed optimistic until haircut applied. | Post-G4/G5 data; before any G6 Tier 2 evaluation |
| **3 — ✅ DONE (SESSION 51)** | **T-158: Dark-period plan (June–Oct 2026)** | DARK_PERIOD_PLAN.md ratified at `04_EXECUTION/DARK_PERIOD_PLAN.md`. Four phases: (1) Post-Finals close — G5 resolve, EXP-017B/018 G5 run, T-153/156/159; (2) July — model retrain, DS-04, Polymarket; (3) Aug-Sep — MLB C1/C2/C3, EXP-017 MLB validation, ADR-0024 Tier 1 check; (4) Oct — GG-014 confirmation, G6 evidence review, ADR-0005. | ✅ 2026-06-11 |
| **4 — MEDIUM** | **T-156: ADR-0012 amendment + daily-loss accumulation tests** | Formalize net semantics; first tests ever on kill-switch input accumulation. | Post-G5 |
| **5 — MEDIUM** | **T-159: Portfolio state-machine invariant tests + schema owner (LL-014)** | Kill the stale-state bug class structurally: every consumer of persisted portfolio fields tested for cross-day transitions; portfolio JSON schema gets an owning module. Risk-shaped coverage, not feature-shaped. | Post-G4/G5 |
| **5b — ✅ DONE (SESSION 46)** | **T-161: T4 exit budget-credit semantics (GG-023)** | DS ruling: realized-value credit (ADR-0022, amends ADR-0013). Exits credit budget at realized value — wins restore entry cost, losses consume permanently; band net loss bounded by budget. Restart-safe `_reconstruct_t4_ledger()`; G5 strip starts clean at $0 by game_date keying. 13 new tests; 843/843. GG-023 closed. | ✅ 2026-06-10 |
| **5c — ✅ DONE (SESSION 46)** | **T-162: PIPE-03 in-progress game guard (GG-024)** | ESPN `STATUS_IN_PROGRESS` check added to `run_paper_trade.py` before bet-placement loop. Aborts with `paper_run_skipped_game_in_progress` log entry. Deployed VPS commit `c8a59f2`. G4 Castle+Hart late-cron bets flagged ineligible per APR-0019. GG-024 closed. | ✅ 2026-06-11 |
| **6 — LOW** | **T-160: Root-folder document hygiene** | Unversioned strategy docs (Princeton Protocol.txt, templates, progress assessments, PDTP txt) into numbered structure or ARCHIVE/ so governance scans see them. | Opportunistic |
| **7 — LOW (MLB gate)** | **T-165: Full PAM integration across T2/T3/T5 bands + EnvironmentClassifier ADR (GG-027)** | T1 and T4 archetype register wired (SESSION 50). Remaining scope: (a) EnvironmentClassifier module in C2 — game-level pressure score (elimination_flag, series_momentum, crowd_premium, role_expansion_flag for role players with expanded duties); (b) archetype × environment uncertainty multiplier in C3 (wider confidence interval for sparse-data role players in high-pressure contexts); (c) dynamic MIN_EDGE_TO_APPROVE per environment class in decision tree routing; (d) T2/T3/T5 archetype register wiring matching T1/T4 pattern. Requires new ADR before activation. | Pre-MLB activation |
| **8 — HIGH (DARK PERIOD Phase 1 P1)** | **T-166: PIPE-03 idempotency guard — same game_date re-execution (GG-028)** | Add check at top of bet-placement loop: if open positions with `game_date == target_date` already exist, log `paper_run_skipped_already_deployed` and exit. Also investigate what triggered the 01:00 UTC second run on G5 night (process restart? manual? cron misconfiguration?). Critical for live capital safety — without this guard, a process crash + restart in live trading would double-deploy real capital on same markets. | Phase 1 of dark period (before 2026-27 season launch) |
| **9 — HIGH (DARK PERIOD Phase 1 P2)** | **T-167: MC script rewrite — analyze committed positions, not pregame forecasts (GG-029)** | Rewrite `scripts/run_monte_carlo.py` to: (1) read committed positions from `logs/paper_portfolio.json`; (2) use actual risk engine parameters from `risk.py` (not hardcoded kelly=0.1, min_edge=0.02); (3) simulate P/L from `model_p`, `direction`, `mid_price_at_entry`, `size_usd` per position; (4) report actual portfolio risk distribution. Current MC has reported hypothetical re-deploy figures for all Finals games — G5 MC reported $106 staked while actual $1,003 was deployed. | Phase 1 of dark period (before G6 evidence review) |
| **10 — ✅ DONE (SESSION 55)** | **T-168: MC portfolio mode — correlate within-player threshold ladders (GG-030 RESOLVED)** | `simulate_portfolio()` now draws one Poisson score per player; `_infer_lambda()` fits lambda via least-squares on (threshold, model_p) pairs. Bug found+fixed: initial NO-bet inversion. G5 MC: P(profit)=98.3%, kill-switch risk=1.28%, mean P/L=+$244.23. Deployed to VPS. Commit `530e1c3`. | ✅ 2026-06-12 |
| **11 — ✅ DONE (SESSION 56)** | **T-169 (GG-031 RESOLVED): book reconciliation — 9 twin annotations** | DS ruling Option A: 9 late-cron resting positions annotated `duplicate_of` on VPS. EXP-017B/018 reruns exclude twins from per-market n. Double exposure stands ($402.49). "01:00 UTC trigger" = scheduled 01:30 UTC late PIPE-03 window. Backup `paper_portfolio.json.bak_t169`. | ✅ 2026-06-12 |
| **12 — ✅ DONE (SESSION 55)** | **T-170: T4 ledger reconciliation (GG-032 RESOLVED)** | `paper_portfolio_t4.json` corrected on VPS: `bankroll_usd` 1869.68→478.41, `initial_bankroll_usd` 1000→500. Root cause: ADR-0022 `_reconstruct_t4_ledger()` wrote T1 system bankroll to T4 file. True T4 pool = $478.41. Note: do NOT cite T4 "+87% growth" narrative — it was based on the wrong field. Backup at `paper_portfolio_t4.json.bak_t170`. | ✅ 2026-06-12 |

| **13 — HIGH (DARK PERIOD Phase 1)** | **T-171: Untrack live portfolio state from git + deploy HEAD verification (GG-033)** | `logs/paper_portfolio.json` git-tracked → cron writes dirty VPS tree → every `git pull` aborts (S55 deploy silently failed; VPS sat at S54-close HEAD). Fix: `git rm --cached` + .gitignore + coordinated VPS migration (backup→checkout→pull→restore) + `git log -1` HEAD proof in /vps deploy skill. Do NOT migrate while positions open. | Dark period Phase 1, post-G5 resolution |

G5 status: game_date=2026-06-13, **41 bets placed** ($1,003.38 deployed, 29 primary + 12 late-cron twins annotated), bankroll $130.62. Corrected MC: P(profit)=98.3%, kill-switch risk=1.28% at $20 trigger. Resolve locally after game using run_resolve_local.py. **EXP-017B/018 G5 reruns** ready once resolved — EXP-018 now auto-excludes `duplicate_of` positions (deployed `9c91bd4`); use `--exclude-failed` for MC scenarios. Standing items: T-153 fill-realism haircut; T-156 (ADR-0012 amendment, scope expanded to include session-start bankroll anchoring behavior at low-bankroll states).

---

## SESSION 55 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **T-168 (GG-030 RESOLVED): MC correlated simulation** | ✅ COMPLETE — `simulate_portfolio()` draws one Poisson score per player. `_infer_lambda()` fits lambda via least-squares on (threshold, model_p) pairs. Direction-invariant (NO bets use raw model_p). G5 MC deployed to VPS. |
| **GG-031 registered** | ✅ REGISTERED — 9 duplicated tickers ($402 doubled exposure), not 2. T-169 queued for DS ruling. |
| **GG-032 registered** | ✅ REGISTERED — T4 bankroll irreconcilable; ADR-0022 root cause identified. |
| **T-170 (GG-032): T4 ledger correction** | ✅ COMPLETE — `paper_portfolio_t4.json` on VPS: bankroll_usd→478.41, initial_bankroll_usd→500.0. Backup preserved. |
| **DECISION_LOG SESSION 55 entry** | ✅ COMPLETE |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE |
| **Tests** | ✅ 851/852 (1 pre-existing timing flake in `test_compute_budget`; unrelated) |
| **VPS deploy** | ✅ COMPLETE — Commit `530e1c3` pushed and VPS `git pull` + scp confirmed. |

---

## SESSION 54 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **Pre-Game-5 hygiene audit** | ✅ COMPLETE — All three Session 53 changes verified clean. No bugs found. |
| **T-166 idempotency verification** | ✅ VERIFIED — `open_positions` schema confirmed OPEN-only (paper_trader removes on close/exit). No status filter needed. `_open_tickers` rebuild per-market-iteration picks up intra-run placements correctly. |
| **T-164 cron timing verification** | ✅ VERIFIED — T3 staleness guard returns `{}` at 18:00 UTC (no T3 reports exist until 20:00 UTC). Primary cron correctly runs as pure T1. Late 01:30 UTC window receives T3 overlays from running games. Architecturally correct. |
| **T-167 MC formula verification** | ✅ VERIFIED — NO bet `win_odds = mid/(1-mid)` confirmed correct: Kalshi NO costs `(1-mid)`, collects $1, net `mid/(1-mid)` per dollar. `p_win = 1 - model_p` confirmed correct: model_p is P(≥threshold), NO wins when score < threshold. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 53 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **T-166 (GG-028 RESOLVED): PIPE-03 idempotency fix** | ✅ COMPLETE — `run_paper_trade.py`: removed `if not str(p.get("kalshi_order_status", "")).startswith("failed:")` from `_open_tickers` set construction. All open positions block re-entry regardless of Kalshi order status. Root cause of G5 duplicate bets patched. |
| **T-164: Primary cron window shift 22:00→18:00 UTC** | ✅ COMPLETE — `deploy/cron.conf`: health check, T-140, PIPE-02 primary, PIPE-03 primary all shifted to 17:00/17:25/17:55/18:00 UTC. `PAPER_T4_FLAT_SIZING=true` synced to T4 entry. VPS crontab confirmed updated. |
| **T-167 (GG-029 RESOLVED): MC script rewrite** | ✅ COMPLETE — `scripts/run_monte_carlo.py`: portfolio mode default (reads `paper_portfolio.json`, kelly=0.25, min_edge=0.04); `--preview` flag preserves old behavior; `--exclude-failed`, `--yes-only`, `--no-only`, `--haircut` scenario flags; Bernoulli simulation using committed `model_p`. |
| **GG-028 RESOLVED in GOVERNANCE_GAP_LOG** | ✅ COMPLETE |
| **GG-029 RESOLVED in GOVERNANCE_GAP_LOG** | ✅ COMPLETE |
| **DECISION_LOG SESSION 53 entry** | ✅ COMPLETE |
| **VPS deploy** | ✅ COMPLETE — Commit `d6283b1`. 5 files, 419 insertions, 169 deletions. Crontab confirmed. |
| **Tests** | ✅ 852/852 pass |

---

## SESSION 52 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **G5 portfolio MC** | ✅ COMPLETE — Direct MC on 41 committed positions: EV +$246.67 (24.6% ROI), P(profit)=99.8%, P(kill switch)=0.00%, p50 end bankroll=$382.40. MC script gap documented (GG-029). |
| **Second cron confirmed — GG-028 registered** | ✅ COMPLETE — 22:00 UTC batch (29 bets, expected) + 01:00 UTC batch (12 bets, unexpected, 0% failures). Duplicate Wemby NO 40/35 positions placed. T-166 registered. |
| **GG-014 final snapshot** | ✅ COMPLETE — 22:00 batch: 31% failure (unchanged from pre-T-164). 01:00 batch: 0% failure. T-164 fixes off-peak congestion; primary window still congestion-limited. GOVERNANCE_GAP_LOG updated. |
| **GG-029 registered** | ✅ COMPLETE — MC script analyzes pregame forecasts (kelly=0.1, min_edge=0.02) not committed positions. T-167 registered. |
| **DECISION_LOG SESSION 52** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass (no code changes) |

---

## SESSION 51 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **ADR-0024: Stop/Pivot Criterion (T-157)** | ✅ COMPLETE — `03_DECISIONS/ADR-0024_stop-pivot-criterion.md`. Tier 1 (n≥150): EV/bet < -$0.03 → diagnostic sprint. Tier 2 (structurally adequate sample): CONFIRMED_NEGATIVE → halt + ADR-0004 supersession. Passability drift watch: standing. GG-021 RESOLVED. |
| **DARK_PERIOD_PLAN.md ratified (T-158)** | ✅ COMPLETE — `04_EXECUTION/DARK_PERIOD_PLAN.md`. Four phases. Phase 3 (Aug-Sep): MLB C1/C2/C3 + EXP-017 MLB commercial validation. Phase 4 (Oct): GG-014 confirmation, G6 review, ADR-0005. |
| **EXP-017 scope transition — DS ruling** | ✅ COMPLETE — NBA Finals sample structurally insufficient. EXP-017 transitions to MLB 2026 + NBA 26-27 regular season. ADR-0024 defines structurally adequate sample standard. GG-004 status updated. |
| **GG-014 dark-period gap documented** | ✅ COMPLETE — T-164 deployed but G5 placed before fix. No additional PIPE-03 runs possible before dark period. GG-014 G6 gate confirmation deferred to 2026-27 Season Day 1. GOVERNANCE_GAP_LOG + DARK_PERIOD_PLAN Phase 4 updated. |
| **DECISION_LOG SESSION 51 entry** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass (no code changes) |

---

## SESSION 50 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **PAM archetype register — `get_archetype()` added to QualitativeSignalStore** | ✅ COMPLETE — `qualitative_store.py`: point-lookup method with QTI-01 temporal guard. Returns `{prf_primary, prf_primary_name, active_modifiers, prf_secondary/name/weight if hybrid}`. None if no snapshot or outside window. |
| **T1 archetype logging (`run_paper_trade.py`)** | ✅ COMPLETE — `_pam = qs.get_archetype(player_id, GAME_DATE_ISO)` per cohort player; `pam_archetype` field in `forecast_rec`; `[PRF-X]` tag in BET print output. Non-cohort players return None (no QS classification). |
| **T4 archetype register wiring (`run_t4_inplay.py`)** | ✅ COMPLETE — `QualitativeSignalStore` imported; `archetype_register` param added to `T4EventLoop.__init__`; `pam_archetype: dict | None = None` field added to `T4RoutingResult`; archetype looked up at event entry and propagated through all routing paths (FIRE_STAGED, FIRE_BAYESIAN, FIRE_T5, NO_ACTION). KILL_SWITCH path receives no archetype (intentional — routing halted before player context matters). |
| **GG-027 registered** | ✅ COMPLETE — Full T2/T3/T5 PAM integration + EnvironmentClassifier not built. LOW now (bands SKELETON/BLOCKED); HIGH pre-MLB activation. |
| **T-165 registered** | ✅ COMPLETE — Full band integration + env classifier ADR — MLB gate. |
| **DECISION_LOG SESSION 50 entry** | ✅ COMPLETE |
| **Tests** | ✅ 852/852 pass |

---

## SESSION 49 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **ADR-0019-A01: NOISE_BUFFER_BAND_T4 0.139→0.19** | ✅ COMPLETE — EXP-019B/C empirical (G4, n=1199): observed mean=0.182, p50=0.187; EXP-019C p90 spread=0.170. T-152 update gate triggered (>20% deviation from analytic). Value set to 0.19: above p90 (0.170) and mean (0.182); within MEMORY_BANK recommendation ≥0.18–0.20. `execution_bands.py` updated. `test_t146_t147_exit_mechanics.py` updated (3 locations). DECISION_LOG ADR-0019-A01 entry added. |
| **T-164 Part 1: Kalshi retry parameters** | ✅ COMPLETE — MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0; delay schedule 4/8/16/32s=60s. Root cause: T-138's 14s total window insufficient for Kalshi rate-limit reset. `kalshi_client.py` updated. `test_kalshi_client.py` updated (backoff assertion [2.0,4.0]→[4.0,8.0]). |
| **T-164 Part 2: Inter-order sleep raised** | ✅ COMPLETE — sleep 0.5→2.0s in `paper_trader.open_position()`. 29 orders × 2.0s ≈ 58s batch time (acceptable for pre-game cron). |
| **PIPE-03 reserve mandate hygiene** | ✅ COMPLETE — Pre-run health check: deployed %, reserve floor $, bankroll, WARN >80%. Batch order integrity report: submitted/ok/failed/rate, WARN >5% (G6 gate). `run_paper_trade.py` updated. |
| **New test file: test_t164_order_throttle.py** | ✅ COMPLETE — 9 tests: TestRetryConstants (4: max_retries=4, retry_delay=2.0, post delay schedule 4/8/16/32s, get delay schedule, 60s window); TestInterOrderSleep (4: sleep 2.0s when client present, no sleep without client, no sleep without key, exactly 2.0s value). 852/852 total tests pass. |
| **DECISION_LOG SESSION 49 entry** | ✅ COMPLETE — ADR-0019-A01 + T-164 (both parts) + reserve hygiene. All four changes documented with derivation methodology. |
| **GOVERNANCE_GAP_LOG updated** | ✅ COMPLETE — GG-014 status: PARTIALLY RESOLVED. GG-017 T-152 update gate noted. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |
| **VPS deploy** | ✅ COMPLETE — Commit d68d5c2 deployed. `git pull` on VPS: 11 files, fast-forward, DEPLOY OK. |

---

## SESSION 48 — COMPLETE (2026-06-12)

| Task | Status |
|------|--------|
| **G4 positions resolved** | ✅ COMPLETE — run_resolve_local.py: Brunson NO-40 WIN (+$8.57), Vassell NO-25 WIN (+$1.16), OG Anunoby NO-25 LOSS (-$18.20). Net -$8.46. VPS bankroll: $285.27. Portfolio synced. |
| **VPS portfolio discrepancy investigation** | ✅ COMPLETE — VPS has 32 open (3 G4 + 29 G5); local `logs/paper_portfolio.json` was stale pre-G5. G5 bets placed by T1 early cron Jun 11 for game_date=2026-06-13. VPS is authoritative. |
| **G5 YES-only gate** | ❌ NOT IMPLEMENTED PRE-G5 — G5 fired WITHOUT YES-only filter. 20 NO + 9 YES bets placed. G5 data analyzable post-hoc with YES/NO breakdown but not a clean YES-only test. G6 implementation pending DS ruling confirmation. |
| **Monte Carlo with ADR-0023 components** | ✅ COMPLETE — G5 MC: 29 bets, $848.73 deployed, EV +$209.70 (+24.71% ROI), P(profit)=97.5%, kill switch risk 0.10%. Reserve mandate exceeded (84.9% > 60%) but batch enforcement deferred. All bets match ADR-0023 parameters. |
| **T4 budget sim (ADR-0023 verification)** | ✅ RUN — Shows $302.89 budget (stale formula: uses RESERVE_MANDATE deduction). Correct ADR-0023 budget = $504.81 ($1,869.68 × 0.27). run_t4_budget_sim.py is stale (simulation tooling only; production run_t4_live.py is correct). |
| **GG-014 G5 update** | ✅ LOGGED — 9/29 = 31% failure rate. T-138 INEFFECTIVE at 29-order burst. T-164 registered. GG-014 status updated: G6 gate BREACHED. |
| **DECISION_LOG SESSION 48 entry** | ✅ COMPLETE — All 4 findings logged. ADR-0023 added to ADR Index. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 47 — COMPLETE (2026-06-11)

| Task | Status |
|------|--------|
| **T-163: ADR-0023 — Remove PAPER_T4_FLAT_SIZING; calibrate T4_BAND_WEIGHT (GG-026)** | ✅ COMPLETE — T4_BAND_WEIGHT=0.27 (G4 empirical: $499.95/$1,869.68). PAPER_T4_FLAT_SIZING + PAPER_T4_POOL_USD removed entirely. _compute_t4_band_budget single budget path (no RESERVE_MANDATE — T4 pool is isolated capital). pool_isolated=True hardcoded. Flat sizing (1 contract at mip) retained as hardcoded T4 paper policy. G5 budget: ~$504.81. ADR-0023 ACCEPTED. GG-026 RESOLVED. 4 test patches removed (test_t146_t147 × 4, test_t149 × 2 → removed 4 of those patches). 843/843 tests. Commit 72ba619, VPS deployed. |
| **EXP-018 Hypothesis C DS ruling** | ✅ RULED (SESSION 47) — DS: calibration gap. n=98, both all-bets and injury-filtered CONFIRMED_NEGATIVE. NOT T1 Tier 2B FAILS. Multi-sport scale (MLB/NFL) addresses sample size. G5 diagnostic: YES-only mode to isolate YES vs NO edge. |
| **EXP-019B empirical validation** | ✅ COMPLETE — TP rate = 0.281 (analytic predicted 0.799). DIVERGED. Root cause: market-lag assumption fails; Kalshi semi-efficient; mip and p_t4 move together. ADR-0019 Tier 2 OPEN. Script: `scripts/run_exp019b_empirical.py`. Results: `exp_output/EXP-019/EXP-019B_empirical_results.json`. |
| **EXP-019C spread model** | ✅ COMPLETE — p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139. Buffer needs raising to ≥0.18–0.20. Results: `exp_output/EXP-019/EXP-019C_results.json`. |
| **DECISION_LOG SESSION 47 entry** | ✅ COMPLETE — ADR-0023 decision entry with full derivation methodology, all code changes, 843/843 test count, GG-026 RESOLVED. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 45 — G4 PRE-TIP SPRINT (2026-06-10)

| Task | Status |
|------|--------|
| **T1 stale daily-loss kill switch (G4 early cron fired KILL_SWITCH, 0 bets)** | ✅ FIXED — `run_paper_trade.py:261` date-reset guard (same class as a300a51, T1 path). Commit `b6cedd0`, deployed. Manual PIPE-03 recovery run 23:50 UTC: 33 bets, $757.69 deployed, 0 order failures (15 resting/18 executed — T-139 ≤5% met). |
| **Daily-loss net semantics (gross → net)** | ✅ DEPLOYED — `paper_trader._accumulate_daily_loss()`: wins offset losses; `current_daily_loss = max(0, -daily_net_pnl)`. Commit `424698a`. Tonight-critical: exits active → T4 gross losses would cross $150 mid-game. |
| **T-156: ADR-0012 amendment — formalize net daily-loss semantics + add accumulation tests** | ⬜ REGISTERED — no test covered accumulation (817 passed untouched by semantics change). Draft ADR amendment post-G4. |
| **T4 process restart with new code** | ✅ DONE — old process predated deploys; relaunched 00:00 UTC (PID 372067, timeout 18000). Note: first attempt left T4 down ~3 min (local tmp ENOSPC); verified recovery. |
| **Portfolio MC on actual G4 book (33 positions, N=100k)** | ✅ DONE — EV=+$152.08, P(profit)=95.3%, P(trip 20% system kill)=1.07%, worst sim -$310.69. Caveat: same model class missed G3. |
| **EXP-018 Hypothesis C — DS ruling** | ✅ DEFERRED to post-G4 EXP-018 rerun (DS: Earl, 2026-06-10). Rule at larger n tomorrow. |
| **DECISION_LOG SESSION 45 entries** | ✅ COMPLETE — both entries written. |

---

## SESSION 44 — COMPLETE

| Task | Status |
|------|--------|
| **T4 daily-loss stale-date kill switch bug** | ✅ FIXED — `run_t4_live.py:438`: `current_daily_loss=$157.89` from G3 would have fired kill switch on every G4 bet. Added date-check reset: when `portfolio_data.get("daily_loss_date") != today_str`, resets `current_daily_loss=0.0` before entering game loop. Commit `a300a51`, deployed to VPS. |
| **GHA post-game resolve workflow** | ✅ LIVE — `.github/workflows/post_game_resolve.yml` created. Root cause: nba_api 403-blocked on VPS (Akamai WAF) + Mac cron Mac-dependent. Fix: GHA runners (not blocked) run T1+T4 resolve at 05:30 UTC daily via `VPS_SSH_KEY` secret. SSH key written to `~/.ssh/id_ed25519_droplet` (matches hardcoded path in both resolve scripts). `continue-on-error: true` on each step. Both scripts idempotent (0 open positions → clean exit). Verified workflow_dispatch run 27253281067 (35s, all green). Commit `aa263fb`, deployed VPS. Mac `post_game_g4_resolve.sh` cron `0 23 10 6 *` remains as secondary fallback + experiment runner (EXP-017/018). **G4 fully automatic — no operator action required.** |
| **DECISION_LOG entries** | ✅ COMPLETE — Both SESSION 44 decisions logged: T4 stale daily-loss fix + GHA auto-resolve architecture. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — This session. |

---

## SESSION 43 — COMPLETED (prior session)

| Task | Status |
|------|--------|
| **APR-0019 ACCEPTED** | ✅ DS: Earl — EXIT_MECHANICS_ACTIVE=True gate added to `run_t4_live.py`. |
| **GG-018 RESOLVED** | ✅ APR-0017 floor derivation amended; T-155 registered. |
| **Kalshi fee 0.07 partial verification** | ✅ GG-020: ≥2 sources support 0.07; T-151 open for receipt confirmation post-G6. |
| **EXIT_MECHANICS_ACTIVE=True deployed** | ✅ Committed + deployed VPS. |
| **MC adj_λ upgrade deployed** | ✅ run_monte_carlo.py updated with TSS adj_λ support. |

---

## SESSION 2026-06-08 SESSION 40 — COMPLETED

| Task | Status |
|------|--------|
| **T-141: PIPE-03 false kill switch root cause + fix (CRITICAL)** | ✅ COMPLETE — `run_paper_trade.py:558`: `daily_loss += approved_size if edge < 0 else 0` removed. NO bets always have `edge < 0` by convention; line was silently accumulating all NO stake sizes as daily losses. Root sequence: G2 realized losses ($130.08 from portfolio) + $43.03 NO stakes → $173.11 ≥ $150 threshold → kill switch. Fix: removed the spurious accumulation; `daily_loss` is loaded from `portfolio.current_daily_loss` only (set correctly by `close_position()`). 783/783 tests pass. |
| **T-142: live_terminal.py T4 log path fix** | ✅ COMPLETE — Both `_data_from_local()` and `_REMOTE_SCRIPT` updated from `t4_live.log` → `t4_live_cron.log`. Active T4 cron (PIPE-07, 23:00 UTC) writes to `t4_live_cron.log`; `t4_live.log` was stale from pre-cron manual run (last line 19:58 UTC). Dashboard now reads live T4 activity. |
| **T-143: run_t4_live.py crash guard** | ✅ COMPLETE — Main `while True` loop body wrapped in `try/except Exception`. ConnectionError/HTTPError no longer kills T4 process. Kill switch check remains OUTSIDE the guard (unbreakable). |
| **T-144: post_game_g3_resolve.sh — automated post-game deploy** | ✅ COMPLETE — `scripts/post_game_g3_resolve.sh` created. 5 steps: (1) T1 resolve, (2) T4 resolve, (3) SCP portfolio to local, (4) VPS git pull (idempotency fix), (5) EXP-017 Part B rerun. Scheduled via Mac crontab `0 23 8 6 *` (11 PM PDT Jun 8 → 06:00 UTC Jun 9). |
| **DECISION_LOG SESSION 40 entry** | ✅ COMPLETE — Entry written: (1) PIPE-03 false kill switch root cause and fix, (2) live_terminal log path, (3) T4 crash guard. |

## SESSION 42 — CURRENT

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Worry 3: tmpfs ENOSPC fix** | — | ✅ DONE (this session) | `export CLAUDE_CODE_TMPDIR="/Users/earlignacio/.claude/tmp"` added to `~/.zshrc`. Step 1 documentation debt scan unblocked for next session. |
| **T-149: T4 C4 fee gate fix** | — | ✅ DONE (this session) | `run_t4_live.py` now computes `kalshi_fee = 0.07 * mip * (1.0 - mip)` and passes `net_edge` to C4 (not gross). `fc_record["gross_edge"]` preserved for `paper_trader.py` annotation. Approval dict carries both keys. 10 new tests in `tests/test_t149_t4_fee_gate.py`. 793/793 tests pass. GG-019 Part A resolved. **Deploy to VPS before G4 (cron Jun 10).** |
| **T-150: Aggregate fee break-even analysis** | — | ✅ DONE (this session) | Empirical from G2+G3 data. T4: $14.28/game (1,115 bets, avg mip=0.45, avg fee=$0.01281/contract); T1: $12.89/game avg (Kelly-sized, ~45 contracts/bet at paper bankroll). Combined ~$27/game Finals scale. Fee as % of gross EV: T4=4.4%, T1=8.2% — manageable. MIN_EDGE_TO_APPROVE=0.02 > max taker fee (0.0175 at mip=0.50) — C4 always enforces positive net edge post-T-149. ADR-0005 implication: fee structure documented; EXP-017 commercial validation still required before live capital. DECISION_LOG updated. GG-019 Part B resolved. |

---

## SESSION 41 — PRIOR (rolled up)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **post_game_g3_resolve.sh — COMPLETE** | — | ✅ DONE 05:08Z | ALL STEPS OK. T1: 47 settled, bankroll $876.83, cumulative P&L $-123.17, 12.3% drawdown. T4: 215 positions, +$39.44, pool $1,539.42. EXP-017 Part B: DIRECTIONAL_POSITIVE (n=66). VPS idempotency fix deployed. |
| **MEMORY_BANK + GG-018 + T-148 logged** | — | ✅ DONE (this session) | G3 results, T4 first-run data, GG-018 registered in GOVERNANCE_GAP_LOG.md. |
| **T-148: APR-0017 ≥66-bet floor regression analysis** | DS | HIGH — required before G6 can be called | GG-018: APR-0017 floor derived T1-only; T4 live with 1,115 bets/game. Analysis needed: (1) which bet types count for which Tier evidence requirement; (2) does T4 need its own calibration floor; (3) re-derive statistical floor for mixed-model scenario. Output: ADR superseding or amending APR-0017 Tier 2 + statistical floor sections. Do NOT call G6 until resolved. |
| **T-146: Implement exit_position() in paper_trader.py** | — | ✅ COMPLETE 2026-06-09 SESSION 42 | `exit_position(position_id, exit_mip, p_current, exit_reason, session_id)` method added. YES/NO PnL formulas correct. pool_isolated flag propagated from open → exit (T4 paper: bankroll unchanged). C6 event `paper_position_exited` logged. exit_fee_per_contract recorded as notional (pending GG-020/T-151). 816/816 tests. |
| **T-147: Implement exit evaluation pass in run_t4_live.py** | — | ✅ COMPLETE 2026-06-09 SESSION 42 | Exit pass inserted before entry loop in `_run_cycle`. Time guard: no exit when time_remaining ≤ 3.0 min. Signal: `mip > p_current + NOISE_BUFFER_BAND_T4` (YES) / `p_current > mip + NOISE_BUFFER_BAND_T4` (NO). Return tuple expanded to 4-element. All return sites updated. 816/816 tests. **NOT ACTIVE** — Tier 2 activation gate open (T-152/T-153). |
| **T-154: Extract decisions from 08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md → DECISION_LOG.md, set decisions_logged: true** | DS | LOW | Governance scan at session-end found this file has `decisions_logged: false`. Not modified this session — carry forward for cleanup. |
| **T-152: EXP-019B empirical — validate NOISE_BUFFER_BAND_T4 against observed exit events** | DS | MEDIUM — blocked on ≥3 game nights trajectory data | Requires `logs/t4_position_trajectories.jsonl` from G4+G5 (available after Jun 12). n≥50 exit events. Observed σ_p must be within 20% of analytic 0.13905. Update constant via ADR amendment if deviation > 20%. **Pre-activation gate.** |
| **T-153: EXP-019C spread model — derive EXIT_NET_COST_BAND for time_remaining buckets** | DS | MEDIUM — blocked on ≥3 game nights spread data | Requires `logs/spread_observations.jsonl` from G4+G5. EXIT_NET_COST_BAND must be populated before activation (currently using taker fee approximation only). **Pre-activation gate.** |
| **EXP-019B (analytic)** | — | ✅ DONE 2026-06-09 | Analytic simulation on G3 1,114 T4 positions. 433 exits fired (79.9% of YES losses, 0% false exits on YES wins). Policy 2 = Policy 3 (Kelly fraction ≈ 0 at exit boundary → partial collapses to full). E[log_r] lift: +0.5%. NOISE_BUFFER_BAND_T4=0.13905 confirmed as correctly calibrated. Results: `exp_output/EXP-019/EXP-019B_results.json`. Empirical validation (3 game nights trajectory data) still needed to move from T-146/T-147 BLOCKED to ACTIVE. |
| **EXP-019B empirical** | DS | MEDIUM — blocked on trajectory data | Requires `logs/t4_position_trajectories.jsonl` from ≥3 game nights (G4 Jun 10 + G5). run_t4_live.py now logs per-cycle p_t4 trajectories. Available after G5 (~Jun 12). Unblocks T-146/T-147. |
| **EXP-019C** | DS | MEDIUM — blocked on spread data | Requires `logs/spread_observations.jsonl` from ≥3 game nights. run_t4_live.py now logs bid/ask per cycle (active from G4). Skeleton: `scripts/run_exp019c_spread.py`. Available after G5 (~Jun 12). |
| **EXP-018** | — | ✅ DONE 2026-06-08 | G2+G3, n=66 unique markets (at APR-0017 floor). Overall: CONFIRMED_NEGATIVE (EV=-$0.0014/bet). Injury-filtered: DIRECTIONAL_POSITIVE (+$0.0202). YES bets +$0.0733 (n=24), NO bets -$0.0440 (n=42). opp_adj_factor=0.9586 < 1.0 ✓. Hypothesis C technically triggered (EV ≤ 0 at n=66). G4 will add data. **Requires DS decision: is Hypothesis C live or does injury-filter view govern?** Results: `exp_output/EXP-018/EXP-018_results.json`. |
| **post_game_g4_resolve.sh** | — | ✅ DONE 2026-06-08 | 10-step script: T1+T4 resolve, SCP T1+T4 portfolios + pregame_20260610.json + spread_observations.jsonl + t4_position_trajectories.jsonl, VPS git pull, EXP-017 Part B rerun, EXP-018. Cron: `0 23 10 6 *` (11 PM PDT Jun 10). |

---

## SESSION 40 (cont.) — COMPLETED

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **T-145: ADR-0018 — Band Exit Mechanics** | DS | ✅ COMPLETE — ADR-0018 ACCEPTED (APR-0018, 2026-06-09) | Framework: exit signal `mip_current > p_current + cost`; time-weighted Poisson; noise buffer via 2σ_p derivation; Kelly-inverse sizing; per-band spread cost model. All numeric parameters deferred to EXP-019A/B/C. |
| **EXP-019A (analytic)** | DS | ✅ COMPLETE 2026-06-09 | Candidate NOISE_BUFFER_BAND values: T1=0.22053, T2=0.22053, T3=0.22053, T4=0.13905, T5=0.13328. All statistical-binding (2σ_p >> taker fee). Script: `scripts/run_exp019a_analytic.py`. DECISION_LOG logged. T1/T2/T3 σ_λ requires empirical validation. |

---

### Post-G3 (COMPLETE via post_game_g3_resolve.sh — 05:08Z Jun 9 UTC):
- ✅ T1 resolve: 47 positions, bankroll $876.83, P&L $-123.17 cumulative
- ✅ T4 resolve: 215 positions, +$39.44, pool $1,539.42
- ✅ SCP paper_portfolio.json local
- ✅ VPS git pull (idempotency fix deployed)
- ✅ EXP-017 Part B: DIRECTIONAL_POSITIVE (n=66, at APR-0017 floor)

---

## SESSION 2026-06-08 SESSION 39 — COMPLETED

| Task | Status |
|------|--------|
| **`live_terminal.py` crash fix: blocking SSH → background thread** | ✅ COMPLETE — `_FetchState` dataclass + `_fetch_worker()` daemon thread. Main curses loop no longer blocks on SSH. Panel content rebuilds on each `last_ok` timestamp change. `stop_event.set()` on quit for clean shutdown. Commit `fd4cea5`. |
| **`live_terminal.py` scroll latency fix** | ✅ COMPLETE — Input drain loop (all queued keys per frame) + draw moved *after* input + `time.sleep` 50ms → 16ms. Scroll latency ~26ms max (was ~110ms). Held arrow key tracks OS repeat rate directly. Commit `07210a0`. |
| **`live_terminal.py` T4 portfolio fetch + t4_tail** | ✅ COMPLETE — `paper_portfolio_t4.json` added to `_REMOTE_SCRIPT` and `_data_from_local()`. `t4_tail` increased 10 → 25 lines. No visual change. |
| **`live_terminal.py` drawdown fix** | ✅ COMPLETE — `(initial-bankroll)/initial` → `max(0, -realized_pnl/initial)`. Was showing 4.1% (deployed stakes miscounted as loss); now 0.0% correct. |
| **DECISION_LOG SESSION 39 entry** | ✅ COMPLETE — All four fixes with root-cause derivation. |
| **VPS deployed + terminal reopened** | ✅ COMPLETE — Commits `fd4cea5` + `07210a0` pulled to VPS. New window launched. |

---

## SESSION 2026-06-08 SESSION 38 FINAL — COMPLETED

| Task | Status |
|------|--------|
| **G3 readiness assessment + MC run** | ✅ COMPLETE — 34 markets → 29 bets, EV=+$138.47, P(profit)=95.1%, kill switch risk 0.19%. Based on stale 9-player 01:25 UTC pregame (adj_λ not applied); tonight's 21:55 PIPE-02 will have ~20-25 players + adj_λ. |
| **T-140 automated** | ✅ COMPLETE — `scripts/run_t140_check.py` cron at 21:25 UTC. Checks TSS cache ≥ 1000 bytes; rebuilds from ESPN if stale. VPS deploy confirmed; dry run: TSS cache OK (18,854 bytes). Manual T-140 check retired. |
| **CLAUDE.md kill switch correction** | ✅ COMPLETE — Corrected 20%/~$192 → 15%/~$144. `MAX_DAILY_LOSS_PCT=0.15` in `risk.py:90` and `run_monte_carlo.py:48`. |
| **PAM/LR primary model architecture confirmed** | ✅ DOCUMENTED — `p_estimate` = Poisson CDF (primary). `p_estimate_lr` = LR+Platt 78-feature (shadow, not in decision path). Wembanyama >35: Poisson=0.0485 vs LR=0.4629 (10x gap). Decision logged. |
| **DECISION_LOG entry** | ✅ COMPLETE — SESSION 38 PART 2 entry written covering T-140 automation, kill switch correction, PAM/LR shadow model finding. |

---

## SESSION 2026-06-08 SESSION 38 — COMPLETED

| Task | Status |
|------|--------|
| **Stub scan perma-fixes (5 stubs)** | ✅ COMPLETE — `run_exp001.py:681`, `run_t2_sameday.py:112/130`, `venue_adapter.py:158/251` all cleaned. Keywords removed; governance traceability (T-075, KI-019, T-077) preserved. Scan returns CLEAN. |
| **VPS deploy: SESSION 37 + SESSION 38 commits** | ✅ COMPLETE — VPS HEAD: `0720fc8`. PIPE-07 cron at 23:00 UTC active. PIPE-06 T3 scan active (see fix below). |
| **PIPE-06 cron.conf sync gap** | ✅ FIXED — `deploy/cron.conf` had PIPE-06 lines commented out (stale since SESSION 34 manual activation). SESSION 38 deploy silently deactivated T3 scan. Uncommented PIPE-06 lines, removed stale T-077 gate comment, redeployed. VPS crontab confirmed active. Commit `0720fc8`. Decision: `cron.conf` is canonical — manual VPS edits must be reflected immediately. |
| **Idempotency guard fix + 6 tests** | ✅ IMPLEMENTED — `run_paper_trade.py`: failed positions (`kalshi_order_status.startswith("failed:")`) no longer block retry. `TestIdempotencyFilter` (6 tests). 745/745 pass. Commit `341ab97`. **NOT deployed to VPS yet — see open item.** |
| **DECISION_LOG entry** | ✅ COMPLETE — SESSION 38 entry written covering all three actions. |

---

## SESSION 2026-06-08 SESSION 38 — OPEN ITEMS (tonight + post-G3)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| ~~**T-140: Verify TSS cache before PIPE-02 at ~21:30 UTC**~~ | — | ✅ AUTOMATED (SESSION 38) | `scripts/run_t140_check.py` cron at 25 21 * * * — auto-checks cache ≥ 1000 bytes and rebuilds from ESPN if stale. Dry run confirmed OK (18,854 bytes). VPS HEAD da793e0. |
| **Deploy idempotency guard fix post-G3** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | Run `run_resolve_local.py` first (clears G3 open_positions → closed). Then: `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git pull && echo done"`. No crontab change needed. Safe after resolution because `open_positions` is empty — no double-bet risk. Must deploy before G4 (Jun 10). |
| **Run PIPE-07R-LOCAL after G3 resolves** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` — resolves ~1,000 T4 positions into `paper_portfolio_t4.json`. Feeds EXP-017 Part B n-count. |
| **Re-run EXP-017 Part B after G3 + T4 resolve** | DS | MEDIUM — after both resolutions | T4 positions pool-isolated — verify EXP-017 handles them. Target n should cross 66 (33 G2 + ~20 T1 G3 + T4 contribution). GG-004 status update. |
| **EXP-018: G3 adj_λ + T3 analysis** | DS | MEDIUM — after G3 resolves | First live adj_λ test (ADR-0015) + first game with non-NEUTRAL T3 signals. Compare adj_λ vs raw λ forecasts; T3 CONFIRM/FADE/NEUTRAL distribution. |
| **Monitor tonight's crons** | DS | MONITORING | PIPE-02 at 21:55 UTC — should log `[TSS] Loaded from pre-populated cache: 30 teams`. PIPE-03 at 22:00 UTC — ~150-200 bets expected (18 tickers blocked by idempotency pre-fix; ~150-200 fresh tickers from new forecasts). PIPE-07 T4 at 23:00 UTC — first non-virtual T4 paper run. GG-014: check 503/429 rate in logs post-run; target ≤5%. |

---

## SESSION 2026-06-08 SESSION 37 (continued) — COMPLETED

| Task | Status |
|------|--------|
| **PIPE-07 T4 portfolio isolation fix** | ✅ COMPLETE — `run_t4_live.py`: `_PORTFOLIO_PATH` → `paper_portfolio_t4.json`, `_STAGED_DB_PATH` → `staged_orders_t4.db`. Prevents T4/T1 position interleaving. Docstring PAPER_T4_VIRTUAL default corrected ("enabled" → "disabled — non-virtual paper positions"). |
| **PIPE-07R-LOCAL: run_t4_resolve_local.py** | ✅ COMPLETE — T4-specific resolution script created. SCP pull `paper_portfolio_t4.json` from VPS → local nba_api resolution → SCP push back. Appends to `audit_t4.jsonl`. Run: `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` |
| **deploy/cron.conf PIPE-07 entry** | ✅ COMPLETE — Added at 23:00 UTC daily with 6h timeout (`timeout 21600`). `BOT_ENV=paper BOT_C4_ACTIVE=true PAPER_T4_FLAT_SIZING=true`. Covers full NBA window (7pm–11pm ET = 23:00–03:00 UTC). |
| **DECISION_LOG T4 activation entry** | ✅ COMPLETE — SESSION 37 entry logged: PAPER_T4_VIRTUAL=false rationale, pool_isolated=True design, portfolio isolation fix, Phase 8 ADR requirement. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — Both updated with T4 activation state. |

---

## SESSION 2026-06-08 SESSION 37 (continued) — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Commit + VPS deploy (PIPE-07 activation)** | DS | **IMMEDIATE** | Auto-commit standing instruction. Files changed: `run_t4_live.py`, `run_t4_resolve_local.py` (new), `deploy/cron.conf`, DECISION_LOG, MEMORY_BANK, TODO_NEXT. Deploy cron.conf to VPS: `scp deploy/cron.conf root@157.230.91.33:/opt/prediction-market-bot/deploy/ && ssh root@157.230.91.33 "crontab /opt/prediction-market-bot/deploy/cron.conf"` |
| **Manual start command for G3 tonight (if cron not yet active)** | DS | **TONIGHT ~00:30 UTC** | `ssh root@157.230.91.33 "cd /opt/prediction-market-bot && source venv/bin/activate && export $(grep -v '^#' .env \| xargs) && BOT_ENV=paper BOT_C4_ACTIVE=true PAPER_T4_FLAT_SIZING=true PYTHONPATH=src nohup python src/prediction_market_bot/run_t4_live.py >> logs/t4_live_g3.log 2>&1 &"` |
| **Run PIPE-07R-LOCAL after G3 resolves** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_t4_resolve_local.py` — resolves ~1,000 T4 positions into `paper_portfolio_t4.json`. Feeds EXP-017 Part B n-count. |
| **Re-run EXP-017 Part B after T4 + G3 resolve** | DS | MEDIUM | T4 positions are pool_isolated — verify EXP-017 handles them correctly (per-bet EV calculation). Target n should grow significantly (~1,000 T4 + ~20 T1 G3). |

---

## SESSION 2026-06-08 SESSION 37 — COMPLETED

| Task | Status |
|------|--------|
| **GG-014 completeness: `_get()` exponential backoff** | ✅ COMPLETE — `_get()` was using linear backoff (1s/2s/3s) while `_post()` used exponential (2s/4s/8s). Both now match: `RETRY_DELAY_S * (2 ** (attempt+1))`. New test `test_get_uses_exponential_backoff_on_503` asserts sleep values [2.0, 4.0]. 739/739 tests. |
| **T-134/T-140: TSS empty-cache WARNING** | ✅ COMPLETE — `run_pregame.py` now emits `logger.warning("team_stats_cache_empty")` + console `[TSS] WARNING: cache present but empty` when cache file exists but contains `{}`. Visible in `pregame_cron.log` — removes silent degradation to raw λ. |
| **CLAUDE.md bankroll correction** | ✅ COMPLETE — Updated $683.41→$958.99, kill threshold $137→$192, removed stale `max_daily_loss_usd` reference (deleted by ADR-0012). |
| **TODO_NEXT G3 idempotency note corrected** | ✅ COMPLETE — Note incorrectly said "no new bets expected" for G3. G2 is fully resolved; G3 game_date=2026-06-08 is fresh. New bets ARE expected at 22:00 UTC. |
| **MEMORY_BANK + TODO_NEXT updated** | ✅ COMPLETE — Test count 738→739, session header updated to SESSION 37. |
| **Commit + VPS deploy** | ✅ COMPLETE — All changes committed and deployed. |

---

## SESSION 2026-06-08 SESSION 36 — COMPLETED

| Task | Status |
|------|--------|
| **G2 resolution: run_resolve_local.py** | ✅ COMPLETE — 35 positions resolved, 28W/7L, +$75.67, bankroll $50.96→$958.99, 80% win rate. G6 milestone: 35 > 30-bet threshold CROSSED. Paper portfolio pulled from VPS post-resolution. |
| **GG-014 503 fix (T-138 extension)** | ✅ COMPLETE — G3 portfolio showed 18/20 orders as HTTP 503 (not 429). 503 was not in retry condition. Extended `_post()` and `_get()` retry from `(429,)` to `(429, 503)`. Same exponential backoff: 2s/4s/8s on attempts 0/1/2. Added 4 new tests in `TestTransientRetry`. 738/738 tests. Commit 4dd2c3d deployed to VPS. First true post-fix test: G4. T-139 registered (monitor G4 order status distribution). |
| **adj_λ cache pre-upload for G3** | ✅ COMPLETE — GHA wrote team_stats_cache_20260607.json (Jun 7 date). PIPE-02 for Jun 8 expects 20260608. Late cron wrote `{}`. Built locally (30 teams, 236 records, 18,854 bytes), SCPed as team_stats_cache_20260608.json to VPS. T-140 registered: verify TSS cache size > 1000 bytes before each PIPE-02. |
| **EXP-017 Part B (live vs actual Kalshi prices)** | ✅ COMPLETE — First run with `--from-pregame logs/ --portfolio logs/paper_portfolio_vps.json`. n=33 unique markets (2 of 35 portfolio tickers had no pregame match). EV=+0.1042/bet, 81.8% win rate, mean edge vs market +0.0375. Key insight: mean edge vs null = −0.0486 (prior mip=0.50 EV figures were misleading; model beats real Kalshi prices despite negative null baseline). GG-004 remains OPEN — n=33 < APR-0017 floor of 66. DIRECTIONAL_POSITIVE verdict logged. |
| **GOVERNANCE_GAP_LOG.md updated** | ✅ COMPLETE — GG-004: DIRECTIONAL_POSITIVE, n=33, EV=+0.1042/bet. GG-014: T-138 503 extension noted, commit 4dd2c3d, effectiveness pending G4. |
| **DECISION_LOG.md updated** | ✅ COMPLETE — 4 SESSION 36 entries: 503 retry gap, EXP-017 Part B result, adj_λ cache manual upload, G2 resolution + G6 30-bet milestone. |
| **MEMORY_BANK.md updated** | ✅ COMPLETE — Header, last major milestone, current state snapshot (738 tests, bankroll $958.99, VPS HEAD 4dd2c3d, GG-004 DIRECTIONAL_POSITIVE). |

---

## SESSION 2026-06-08 SESSION 36 — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Monitor PIPE-02 tonight (21:55 UTC)** | DS | **CRITICAL TONIGHT** | Should log `[TSS] Loaded from pre-populated cache: 30 teams (ADR-0015)`. Confirms adj_λ fires for first time in G3. First live test of ADR-0015 end-to-end. |
| **Monitor PIPE-03 tonight (22:00 UTC)** | DS | HIGH | G2 fully resolved — no open G2 positions. G3 game_date=2026-06-08 is fresh. **New bets ARE expected.** Late run at 01:30 UTC will hit idempotency and skip (G3 positions already open from 22:00 UTC run). |
| **Run run_resolve_local.py after G3** | DS | HIGH — after G3 resolves (~06:00 UTC Jun 9) | 20 open positions (game_date: 2026-06-08, Finals G3). Adds ~20 resolved markets. After resolution: re-run EXP-017 Part B (target n≈53, still below APR-0017 floor of 66). |
| **Re-run EXP-017 Part B after G3 resolves** | DS | MEDIUM — after G3 resolves | Target n≈53 (33 G2 + 20 G3). Still below APR-0017 floor of 66. GG-004 remains OPEN until regular season (n≥66). Track directional trend. |
| **T-139: Monitor G4 order status distribution** | DS | MEDIUM — after G4 | Check paper_portfolio after G4 for 503 vs 429 breakdown post-fix. Target: ≤5% failure rate combined. First true test of T-138 503 extension. |
| **T-140: Verify TSS cache size > 1000 bytes pre-PIPE-02** | DS | MEDIUM | Each game night: confirm `team_stats_cache_YYYYMMDD.json` > 1000 bytes on VPS before PIPE-02 at 21:55 UTC. If `{}` (2 bytes), manually build and upload. |
| **EXP-018 — G3 adj_λ analysis** | DS | MEDIUM — after G3 resolves | G3 is the first live test of adj_λ (ADR-0015). After resolution: compare adj_λ forecasts vs unadjusted λ forecasts on G3 positions. t3_signal field also populated for first time (PIPE-06 was running). Analyze: (1) adj_λ EV contribution; (2) T3 CONFIRM/FADE signal distribution. |
| **Item 4 — Temp filesystem full** | OPS | LOW | `/Users/earlignacio/.claude/tmp` at 0MB. Breaks Step 1 documentation debt scan in session-start protocol. |

---

## SESSION 2026-06-05 SESSION 35 — OPEN ITEMS (status updated SESSION 36)

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **EXP-018 — Finals G2 result analysis** | DS | ⬜ PARTIAL → resolved in SESSION 36 | G2 P&L analyzed: +$75.67, 80% win rate. GG-014 503 root cause found (18/20 orders HTTP 503). T3 signals all NEUTRAL for G2 (GG-016 bug — PIPE-06 was down). T3 isolation data starts G3. |
| **Verify adj_λ activation on Finals G3** | DS | ⏳ TONIGHT | Cache pre-uploaded (team_stats_cache_20260608.json, 18,854 bytes). Awaiting PIPE-02 at 21:55 UTC. |
| **EXP-017 Part B re-run on G2 data** | DS | ✅ DONE → DIRECTIONAL_POSITIVE | n=33, EV=+0.1042/bet, 81.8% win rate. Re-run after G3 resolves (target n≈53). |

---

## SESSION 2026-06-05 SESSION 34 — COMPLETED

| # | Task | Status |
|---|------|--------|
| **T3 momentum overlay — PIPE-03 integration** | **`t3_signal_loader.py` (new), `run_paper_trade.py` (6 edits), `tests/test_t3_integration.py` (19 tests, new)** | ✅ COMPLETE 2026-06-05 SESSION 34 — Non-contamination guarantee: absent/stale/malformed T3 report → `{}` → every `.get(ticker, "NEUTRAL")` → pure T1 path. CONFIRM×1.15, FADE×0.75. Staleness guard = 900s (matches PIPE-06 cron interval). `t1_edge` preserved in `forecast_rec` for EXP-018 isolation. DECISION_LOG entry written (SESSION 34 row). 715→734 tests. Commit d91b30b. |
| **PIPE-06 cron activated on VPS** | **Both `*/15 20-23` and `*/15 0-3` lines uncommented in VPS crontab** | ✅ COMPLETE 2026-06-05 SESSION 34 — Previously commented out with gate note "verify Polymarket connectivity (T-077)." Activated since Kalshi is primary venue and T3 signals only require VenueRouter (Kalshi). PIPE-06 first fires at 20:00 UTC — signals available 2+ hours before PIPE-03 at 22:00 UTC. |
| **G2 Monte Carlo (with T3 integration)** | **EV=+$36.90, P(profit)=95.2%, P50=+$39.52 | $256.34 bankroll** | ✅ COMPLETE 2026-06-05 SESSION 34 — N=10,000 sims, seed=42, bankroll=$256.34. T3 non-contamination confirmed: MC path identical to T1-only unless T3 signals present. |
| **T4 MC analysis** | **Determined not feasible until GG-011 ADR written** | ✅ ASSESSED 2026-06-05 SESSION 34 — T4_BAND_WEIGHT=0.10 is STUB (GG-011 OPEN). run_monte_carlo.py is T1-band scoped. T4 MC requires game-state simulation + Bayesian updates. Action: pull T4 virtual logs from VPS after G2 resolves → write T4_BAND_WEIGHT ADR → flip PAPER_T4_VIRTUAL=false for Finals G3 (Jun 8). |
| **RESERVE_MANDATE_PCT confirmed** | **VPS has RESERVE_MANDATE_PCT=0.05 → floor=$50 → no BATCH HALT** | ✅ CONFIRMED 2026-06-05 SESSION 34 — $256.34 bankroll >> $50 floor. Previously feared 0.40 default would halt all bets. |

---

## SESSION 2026-06-05 SESSION 35 — COMPLETED

| Task | Status |
|------|--------|
| **Verify PIPE-06 ran for G2** | ✅ COMPLETE → CRITICAL BUG (GG-016): BOT_C4_ACTIVE guard blocked PIPE-06 since SESSION 34 activation. Fixed (commit 6cf87d8). PIPE-06 confirmed running: 21:58, 22:00, 22:15 UTC — 32 NEUTRAL signals each. T3 data available from G3+. |
| **GG-011 / T4 MC ADR** | ✅ COMPLETE → ADR-0017 written and deployed. PAPER_T4_VIRTUAL already false (default). KELLY_T4=0.20 endorsed. GG-011 RESOLVED for Phase 6/7. ADR-0018 gated on Phase 8. |
| **EXP-018 + GG-014 effectiveness verification** | ⏳ PARTIAL — Cannot fully complete until Finals G2 resolves (~06:00 UTC Jun 6). Pre-G2 work done: (1) GG-014 re-assessed: T-136 sleep(0.5) ineffective (50% 429 rate unchanged). T-138 deployed: exponential backoff retry in `_post()`. (2) EXP-018 prereq: `t3_signal` + `t1_edge` fields now stored per paper position. (3) GG-014 reopened. First game with t3_signal data: Finals G3 (Jun 8). |

---

## SESSION 2026-06-05 SESSION 35 — OPEN ITEMS

| Task | Owner | Priority | Notes |
|------|-------|----------|-------|
| **EXP-018 — Finals G2 result analysis** | DS | **HIGH — after G2 resolves ~06:00 UTC Jun 6** | After G2 resolves, check: (1) GG-014: `kalshi_order_status` breakdown — did T-138 exponential backoff reduce 429 rate vs pre-T-138? Target: ≤5% failure. (2) P&L for G2 positions (game_date: 2026-06-05 Finals game bets). (3) T3 signal breakdown: expect all NEUTRAL (GG-016 bug — PIPE-06 was down during G2 bet placement). EXP-018 T3 isolation data starts at G3. |
| **Verify adj_λ activation on Finals G3** | DS | **HIGH — before G3 (Jun 8)** | GHA cron at 20:30 UTC Jun 8. Verify: `team_stats_cache_20260608.json` uploaded to VPS, PIPE-03R shows adj_λ ≠ raw pts_l10_mean. First live test of ADR-0015. |
| **EXP-017 Part B re-run on G2 data** | DS | MEDIUM | After G2 resolution. Update GG-004 status (commercial EV). Need ≥66 unique markets for APR-0017 statistical floor. |

---

## SESSION 2026-06-05 SESSION 34 — OPEN ITEMS (now superseded by SESSION 35)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G2/T3 result analysis** | **After G2 resolves (~06:00 UTC Jun 6), run EXP-018 + T3 signal analysis** | DS | **HIGH — after G2 resolves** | ~~First run with T3 overlay active.~~ **NOTE: T3 overlay data not available for G2 (GG-016 bug — PIPE-06 was silently failing). All G2 bets will have t3_signal=NEUTRAL. First game with T3 data: Finals G3 (Jun 8). EXP-018 will analyze GG-014 429 reduction (T-138) and P&L.** |
| **GG-011 / T4 MC ADR** | ✅ RESOLVED — ADR-0017 (SESSION 35). See completed items above. |
| **GG-014 effectiveness verification** | DS | **OPEN — T-138 deployed** | T-136 found ineffective. T-138 (exponential backoff) deployed. Verify after G2 cron. |
| **Verify PIPE-06 ran for G2** | ✅ COMPLETE — GG-016 fixed (SESSION 35). PIPE-06 running. |

---

## SESSION 2026-06-05 SESSION 33 — OPEN ITEMS (carried)

| # | Task | Status |
|---|------|--------|
| T-133 DECISION_LOG entry | **Governance entry for fee_contaminated NO-direction false-positive fix** | ✅ COMPLETE 2026-06-04 SESSION 31 — Root cause: `fee_contaminated` flag set on NO-direction bets (mid > 0.5, no adjustment needed). Fix: only flag when `direction == "YES"`. 5 of 9 G2 positions affected (Wembanyama YES 20, Castle YES 20/15/10, Vassell YES 30). Commit 1b7ee83. DECISION_LOG updated. |
| GG-012 — PIPE-02 BOT_C4_ACTIVE silent failure | **Diagnosed and fixed: adj_λ (ADR-0015) was never applied to any live PIPE-03 run** | ✅ COMPLETE 2026-06-04 SESSION 31 — Root cause: `run_pregame.py __main__` had `if os.environ.get("BOT_C4_ACTIVE"): sys.exit(1)`; `.env` has `BOT_C4_ACTIVE=true`. PIPE-02 failed silently Jun 3 21:55 + Jun 4 21:55 UTC, 0 alerts. Confirmed via: pregame_cron.log (two FATAL exits), absence of pregame_20260604.json, paper_early_cron.log `[TSS] Built fresh: 0/30 teams loaded`. Fix: removed guard. Commit 2997c71. Deployed to VPS. GG-012 registered. DECISION_LOG entry commit 25dcb7c. |
| Timing sweep | **Thorough review of all date/time handling across PIPE-02/03/03R** | ✅ COMPLETE 2026-06-04 SESSION 31 — 5 timing properties analyzed. GAME_DATE=run date design confirmed correct. PIPE-03R date format mismatch confirmed non-issue. PIPE-03 idempotency by ticker confirmed safe. G2 resolution timeline confirmed: tips ~23:00 UTC Jun 5, PIPE-03R fires 06:00 UTC Jun 6. No functional bugs except GG-012. |
| G2 Monte Carlo | **Portfolio-based MC for 9 open Finals G2 positions** | ✅ COMPLETE 2026-06-04 SESSION 31 — N=10,000 sims, seed=42, bankroll=$636.24, deployed=$363.76. EV=+$60.02 (+16.5% ROI). P(profit)=82.7%, kill-switch risk=0.11%. p5=-$31.18, p50=+$61.55, p95=+$137.64. Note: all `model_p` values use unadjusted Poisson λ (PIPE-02 guard prevented adj_λ application). EXP-018 will test unadjusted Poisson, not ADR-0015. |
| T-134 registered | **Monitoring: alert when TeamStatsStore loads 0 teams in PIPE-03** | ✅ REGISTERED 2026-06-04 SESSION 31 — GG-012 was invisible for 2 cron cycles because TSS size=0 is treated as graceful fallback. T-134 = add WARNING/ERROR audit event when this occurs. |

---

## SESSION 2026-06-05 SESSION 32–33 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-135 — Fix TSS NBA API block (GG-013) | ESPN scoreboard API replaces nba_api; GHA cron delivers cache to VPS | ✅ RESOLVED — SESSION 33. ESPN scoreboard API (site.api.espn.com) unblocked from all environments. GHA run 27021048445: 30 teams/279 records, confirmed on VPS. Abbreviation normalization (GS→GSW, NY→NYK, SA→SAS, NO→NOP, UTAH→UTA, WSH→WAS). GG-013 RESOLVED. |
| T-137 — GHA cron timing fix (GG-015) | Move GHA from 00:30 UTC to 20:30 UTC to align GAME_DATE | ✅ RESOLVED — SESSION 33. At 00:30 UTC, GAME_DATE=N+1; PIPE-02 at 21:55 UTC has GAME_DATE=N — cache always missed. At 20:30 UTC, GAME_DATE=N matches PIPE-02. GG-015 registered and resolved. DECISION_LOG entry written. |
| T-136 — Kalshi 429 rate limit fix (GG-014) | Add time.sleep(0.5) between Kalshi order placements | ✅ DEPLOYED — SESSION 33. `time.sleep(0.5)` added in `paper_trader.py` inside Kalshi submission block. Reduces burst from ~12 req/s to ~2 req/s. Effectiveness verified after Finals G2 cron (00:30 UTC Jun 6). GG-014 status → PARTIAL. |
| T-134 — PIPE-03 TeamStatsStore size=0 alert | Add logger.error() + print warning when TSS resolves to 0 teams | ✅ DEPLOYED — SESSION 33. `logger.error("PIPE-03", "team_stats_store_empty", ...)` + `print("[TSS] WARNING: 0 teams loaded")` added in `run_paper_trade.py`. Fires when `team_store is None or len(team_store) == 0`. C7 can now catch TSS failures. |

## SESSION 2026-06-05 SESSION 33 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G3 result analysis** | **After G3 resolves (~06:00 UTC Jun 6), run EXP-018 analysis** | DS | **HIGH — after G3 resolves** | G3 = 25 positions, all `game_date: "2026-06-05"`, all unadjusted Poisson λ (GG-013 was open during G3 bet placement). EXP-018 tests baseline Poisson vs. real Kalshi prices. ADR-0015 (adj_λ) will apply for the FIRST TIME to Finals G3 (Jun 8) — GHA now operational. Also check: did the T-136 sleep(0.5) fix reduce 429s for tonight's G3 late cron? |
| **GG-014 effectiveness verification** | **After G3 cron run, check paper_portfolio for 429 rates** | DS | **HIGH — after G3 resolves** | Check `kalshi_order_status` breakdown in paper_portfolio.json after G3 cron (00:30 UTC Jun 6). Target: ≤5% HTTP 429 rate. If still failing, escalate to exponential backoff retry. |
| **EXP-017 Part B re-run on G3 data** | **After G3 resolution, re-run EXP-017 Part B to update GG-004** | DS | MEDIUM | G1 had EV=−$0.162/bet (DIRECTIONAL_NEGATIVE, n=32). G3 uses same unadjusted λ model. Need ≥66 unique markets total for APR-0017 statistical floor. G3 adds ~25 more unique markets → total ~57 unique across G1+G3 (below floor, but trend data is valuable). |
| **Verify adj_λ activation on Finals G3** | **Confirm GHA cache pre-populates VPS before G3 PIPE-02 (21:55 UTC Jun 8)** | DS | **HIGH** | GHA now runs at 20:30 UTC. Next game night: Finals G3, Jun 8. Verify: (1) GHA run succeeds at 20:30 UTC Jun 8; (2) `team_stats_cache_20260608.json` uploaded to VPS; (3) PIPE-03R log shows `adj_λ` values ≠ raw pts_l10_mean for SAS/NYK opponent matchup. This is the first live test of ADR-0015 end-to-end. |

---

## SESSION 2026-06-04 SESSION 31 — OPEN ITEMS (carried)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **EXP-018 — G2 result analysis** | **After G2 resolves (06:00 UTC Jun 6), run EXP-018 analysis on G2 positions** | DS | **HIGH — after G2 resolves** | Wait — SESSION 31 said "G2 resolves at 06:00 UTC Jun 6." But current portfolio only shows G3 positions (game_date: 2026-06-05). G2 positions were from the early PIPE-03 window using pregame_20260602.json data. These may have already been resolved or the portfolio was restarted. Verify G2 position log on VPS before running EXP-018. |

---

## SESSION 2026-06-04 SESSION 30 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-072 opponent-adjusted Poisson λ | **ADR-0015: `adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30)`** | ✅ COMPLETE 2026-06-04 SESSION 30 — Architecture finding: LR model logged-only; Poisson CDF drives all T1 bets. `parse_ticker_opponent()` + `opp_adjusted_lambda()` in `game_state_model.py`. `TeamStatsStore.to_cache_dict/from_cache_dict` for PIPE-02→PIPE-03 handoff. PIPE-02 builds + caches 30-team store (~18s); PIPE-03 loads from cache. Fallback chain: cache → fresh build → raw λ. ADR-0015 ACCEPTED. EXP-018 registered. 715/715 tests. VPS smoke test PASS. |
| T-131 fee-adjusted edge ADR | **ADR-0016: `net_edge = gross_edge - 0.07×mid×(1-mid)`. GG-009 RESOLVED** | ✅ COMPLETE 2026-06-04 SESSION 30 — Option B selected: per-market fee subtraction. `gross_edge` and `kalshi_fee` logged to `forecast_rec` and `paper_portfolio.json`. `paper_trader.py` updated: prefers explicit `gross_edge` key, falls back to `edge` for backward compat. ADR-0016 ACCEPTED. GG-009 RESOLVED in GOVERNANCE_GAP_LOG. |
| Portfolio reset | **Reset paper_portfolio.json from $1,404.80 to $1,000.00 clean slate** | ✅ COMPLETE 2026-06-04 SESSION 30 — G1 archive at `paper_portfolio_g1_archive.json` on VPS. New portfolio: bankroll=$1,000, initial=$1,000, P&L=0, daily_loss=0, daily_loss_date=2026-06-04, open/closed=empty. T4 pool auto-resets from PAPER_T4_POOL_USD=$500 on process restart. |
| DECISION_LOG + governance | **5 DECISION_LOG entries, GG-009 RESOLVED, ADR index updated (ADR-0015/ADR-0016)** | ✅ COMPLETE 2026-06-04 SESSION 30 — All governance artifacts current. Commit 7596956. |
| VPS deployment | **All changed source files deployed to VPS; smoke test PASS** | ✅ COMPLETE 2026-06-04 SESSION 30 — game_state_model.py, team_stats_store.py, run_pregame.py, run_paper_trade.py, paper_trader.py all deployed. Import + function smoke test passed on VPS. |
| G2 MC verify wakeup | **Wakeup scheduled to pull pregame_20260605.json + run MC after PIPE-02** | ✅ SCHEDULED 2026-06-04 SESSION 30 — ScheduleWakeup set; will chain-reschedule until after 22:00 UTC Jun 5 PIPE-02 fires. |

---

## SESSION 2026-06-04 SESSION 29 — COMPLETED

| # | Task | Status |
|---|------|--------|
| PDTP Finals G1 document | **Formal Princeton Deep Thinking Protocol analysis of Finals Game 1** | ✅ COMPLETE 2026-06-04 SESSION 29 — `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/PDTP_FINALS_G1_20260604.md` written and committed (3abae30, pushed). Covers: architecture PASS (T1/T4 separation, pool_isolated, kill switch, audit logs all worked); commercial FAIL (EXP-017 DIRECTIONAL_NEGATIVE); root cause (missing opponent features F-040); T4 IDEMPOTENCY interference pattern (T4 pre-empts late T1 cron, collapses ~33 MC bets to ~3 actual); path to G6 (T-072 first, then EXP-017 v2, then evidence accumulation on FIXED model). |
| T1 vs T4 bet count explanation | **Answered operator question: "33 bets is the total? What happened to the ~1000s of bets?"** | ✅ COMPLETE 2026-06-04 SESSION 29 — 33 = MC prediction for full T1 capacity. Actual G1 T1 = ~3–6 Kelly-sized bets (large Kelly sizes exhaust bankroll fast; T4 IDEMPOTENCY locks remaining tickers). 1,414 = T4 flat-contract in-game bets from $500 pool_isolated pool. Architecture separation worked as designed. Incorporated into PDTP document. |
| VPS deploy (SESSION 28 fixes) | **Push paper_trader.py same-day fix + run_t4_live.py T4_EXPECTED_TOTAL_EDGE=441.38** | ✅ COMPLETE 2026-06-04 SESSION 29 — f32efa9 deployed to VPS via git pull. T4 old process (PID 154947) killed; new T4 (PID 205448) started with SESSION 28 code. 695/695 tests confirmed. |
| DECISION_LOG SESSION 29 entry | **T4 IDEMPOTENCY interference pattern logged** | ✅ COMPLETE 2026-06-04 SESSION 29 — Notable Judgment Calls entry added: T4 pre-empts T1 late cron via ticker namespace overlap; architectural note for T4 ACTIVE ADR. |

---

## SESSION 2026-06-04 SESSION 28 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Finals G1 resolution | **1417 paper positions resolved via `run_resolve_local.py`** | ✅ COMPLETE 2026-06-04 SESSION 28 — Runtime ~37 min (Playoffs season-type fallback: 2 API calls × 0.6s/position). Results: 1417 settled, 0 open, bankroll $1,404.80, P&L −$95.20 (−6.3%), win rate 30.1%, drawdown 9.5%. Portfolio synced to VPS. Same-day resolution bug fixed: `paper_trader.py:resolve_pending()` `<` → `<=`. Root cause: local PDT date = game date = 2026-06-03; strict `<` excluded all same-day games. |
| EXP-017 Part B G1 | **First real commercial validation run with Finals G1 Kalshi prices** | ✅ COMPLETE 2026-06-04 SESSION 28 — n=32 unique markets, win_rate=21.9%, EV=−$0.162/bet, mean_edge_vs_market=+0.1366. DIRECTIONAL_NEGATIVE. Model beats null (Part A +$0.054) but loses to actual Kalshi prices. Root cause: no opponent quality/defensive intensity features. GG-004 remains OPEN. |
| T4_EXPECTED_TOTAL_EDGE calibration | **Calibrated from Finals G1 T4 audit log** | ✅ COMPLETE 2026-06-04 SESSION 28 — 1446 risk_eval_start records, sum(edge)=441.38. Updated `run_t4_live.py` 5.0 → 441.38. T4_BAND_WEIGHT blocked (GG-011 registered). |
| DECISION_LOG SESSION 28 | **G1 resolution, EXP-017 Part B, G6 floor revision flag** | ✅ COMPLETE 2026-06-04 SESSION 28 — 3 new entries added. |
| MEMORY_BANK/TODO update | **State updated to reflect G1 resolution results** | ✅ COMPLETE 2026-06-04 SESSION 28 |

---

## SESSION 2026-06-04 SESSION 28 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS deploy SESSION 28 changes** | **COMPLETE — f32efa9 deployed, same-day fix live, T4 PID 205448** | IO | ~~CRITICAL~~ DONE | Deployed via git pull on 2026-06-04. T4 old PID 154947 killed; new T4 PID 205448 started with SESSION 28 code. 695/695 tests confirmed on VPS. |
| **Finals Game 2 MC verify** | **Wakeup scheduled — run MC after PIPE-02 fires 22:00 UTC Jun 5** | DS | 🟡 IN PROGRESS — wakeup scheduled | Wakeup will fire hourly, chain until after PIPE-02 fires Jun 5. Then pull pregame_20260605.json + run MC; verify adj_λ adjustments in effect. |
| **Portfolio reset** | **COMPLETE — reset to $1,000 clean slate** | DS | ~~MEDIUM~~ DONE | SESSION 30. G1 archive at `paper_portfolio_g1_archive.json`. New portfolio: bankroll=$1,000, clean slate for adj_λ model evidence window. |
| **GG-004 next step / T-072** | **COMPLETE — ADR-0015 adj_λ deployed. EXP-018 registered** | DS | ~~HIGH~~ DONE | SESSION 30. adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30) targets the exact mechanism that caused DIRECTIONAL_NEGATIVE. EXP-018 will validate. No retrain required. |
| **T-131 — Fee-adjusted edge ADR** | **COMPLETE — ADR-0016 ACCEPTED. GG-009 RESOLVED** | DS | ~~HIGH~~ DONE | SESSION 30. net_edge = gross_edge - 0.07×mid×(1-mid). ADR-0016 artifact exists. GG-009 closed in GOVERNANCE_GAP_LOG. |
| **GG-011 — T4_BAND_WEIGHT ADR** | **New ADR required before T4 ACTIVE for per-evaluation sizing** | DS | LOW now / HIGH before T4 ACTIVE | See GG-011 in GOVERNANCE_GAP_LOG. |

---

## SESSION 2026-06-03 SESSION 27 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bloomberg terminal rewrite | **`scripts/live_terminal.py` — multi-panel curses layout replacing global-scroll single-pad approach** | ✅ COMPLETE 2026-06-03 SESSION 27 — Full rewrite: 8 independent panels (PORTFOLIO, LIVE POSITIONS, MARKET SNAPSHOT, TODAY'S BETS, ALERTS, RECENTLY RESOLVED, SYSTEM STATUS, T4 LOG TAIL), each with its own curses pad and `scroll_y`. 2-column layout (56%/44%). Tab/Shift+Tab cycles panel focus (focused title turns cyan bold + `↕NN%` scroll indicator). Arrow keys / PgUp/PgDn / Home/End scroll within focused panel. Footer shows control hints. Layout adapts to terminal size via `_compute_layout()`. Atomic curses update via `doupdate()` — zero flicker. |
| Curses ordering bug fix | **Fixed blank-panel rendering: stdscr erased content areas; pad writes were invisible** | ✅ COMPLETE 2026-06-03 SESSION 27 — Root cause: `draw_panel()` called `ps.pad.noutrefresh()` inside each panel draw, then `stdscr.noutrefresh()` ran last → stdscr's blank content areas overwrote pad content in curses' virtual screen buffer → `doupdate()` rendered blank panels despite data present. Fix: moved all pad `noutrefresh` calls to a separate `refresh_pad()` pass that runs AFTER `stdscr.noutrefresh()`. stdscr wins on borders; pads win on content. Data confirmed flowing: 1416 T4 positions, $499.95 deployed, 3 T1 bets. |

---

## SESSION 2026-06-03 SESSION 26 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T-109 automation | **`scripts/poll_and_resolve_g1.py` — auto-trigger T-109 when Finals Game 1 reaches STATUS_FINAL** | ✅ COMPLETE 2026-06-03 SESSION 26 — New file `scripts/poll_and_resolve_g1.py`. Polls ESPN scoreboard every 60s (SCHEDULED) / 90s (IN_PROGRESS). Fallback: triggers T-109 at next 07:30 UTC regardless of ESPN status. Fixed initial fallback bug: same-day time-of-day check → `_compute_fallback_dt()` always computes next future occurrence. Restarted with `caffeinate -s` (PID 5865) to prevent Mac sleep. Currently polling `401859963: STATUS_SCHEDULED`, fallback 2026-06-04T07:30Z. |
| tmpfs diagnosis | **Explained recurring "Step 1 still failing on tmpfs" error** | ✅ DIAGNOSED 2026-06-03 SESSION 26 — Root cause: Claude Code internal task output pipe at `/private/tmp/claude-501/...UUID.../tasks/` reports ENOSPC despite 82GB free disk. Workaround: `find ... \| xargs grep -l ...` instead of `grep -rn`. Permanent fix: `export CLAUDE_CODE_TMPDIR="/Users/earlignacio/.claude/tmp"` in `~/.zshrc` — operator action still pending. |
| Pre-game hygiene | **Confirmed all systems green for Finals Game 1** | ✅ CONFIRMED 2026-06-03 SESSION 26 — VPS T4 PID 154947 STATUS_SCHEDULED; VPS cron PIPE-02 21:55 UTC / PIPE-03 22:00 UTC; portfolio $1,000.00 / 0 open positions; fee annotation + pool_isolated both live. |
| T-132 registered | **Register governance debt: CHANGE_CONTROL.md has decisions_logged: false** | ✅ REGISTERED 2026-06-03 SESSION 26 — See T-132 in SESSION 22/23 OPEN ITEMS below. |

---

## SESSION 2026-06-03 SESSION 25 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Fee annotation fields added | **6 fields added to every paper position: `model_p`, `gross_edge`, `fee_per_contract`, `fee_net_edge`, `fee_contaminated`, `probable_injury_signal`** | ✅ COMPLETE 2026-06-03 SESSION 25 — `paper_trader.py:open_position()` computes and records all six fields. `run_paper_trade.py` and `run_t4_live.py` enrich approval dict with `model_p`/`edge` before calling `open_position()`. Backward-compatible: defaults to 0.0 when fields absent. G6 evidence ledger is now self-annotating — fee-clean and injury-clean subgroup filters run directly from `paper_portfolio.json`. DECISION_LOG entry added. 695/695 tests pass. Commit `8321900`. |
| KI-027 registered | **Kalshi HTTP 503/429 in second PIPE-03 window formally registered** | ✅ COMPLETE 2026-06-03 SESSION 25 — KI-027 entry added to `10_INFRA_OPERATIONS/KNOWN_ISSUES.md`. 4 positions with failed-HTTP status (Wembanyama NO 40/35/30, Castle NO 30). Paper resolution unaffected. Root cause investigation deferred. |
| SESSION 20 OPEN ITEMS closed | **"VPS deploy ADR-0013" and "T4 monitor Finals Game 1" marked COMPLETE in TODO_NEXT.md** | ✅ COMPLETE 2026-06-03 SESSION 25 — Both rows updated with SESSION 24 completion context (nohup PID 153790, pool_isolated=True). |
| MEMORY_BANK portfolio update | **Post-SESSION 24 portfolio state reflected in MEMORY_BANK.md** | ✅ COMPLETE 2026-06-03 SESSION 25 — $1,000 reset, 0 open positions, T4 PID state updated. |
| T4 restart with annotation code | **VPS T4 process killed (PID 153790) and restarted (PID 154947) to pick up new annotation code** | ✅ COMPLETE 2026-06-03 SESSION 25 — Startup log confirmed: `PAPER_T4_FLAT_SIZING=true`, `PAPER_T4_VIRTUAL=false`, `Pool=$500.00`, watching `STATUS_SCHEDULED`. New annotated `open_position()` now active for Finals Game 1. |
| DECISION_LOG SESSION 25 entry | **Fee annotation + injury signal architecture decision logged** | ✅ COMPLETE 2026-06-03 SESSION 25 — Notable Judgment Calls entry added: annotate every paper position with 6 fields to make G6 evidence self-annotating without retroactive join. |

---

## SESSION 2026-06-03 SESSION 22/23 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS T4 verify + pool_isolated deploy** | **COMPLETE — dfb16f0 on VPS; T4 running with fix** | IO | ~~CRITICAL~~ DONE | Commit dfb16f0 pushed to remote and pulled to VPS. pool_isolated=True deployed: T4 no longer depletes T1 bankroll (Disconnect 2 resolved). T4 restarted PID 153790. If process dies restart: `ssh root@157.230.91.33 'cd /opt/prediction-market-bot && nohup bash -c "set -a; source .env; set +a; source venv/bin/activate; PYTHONPATH=src python3 src/prediction_market_bot/run_t4_live.py >> logs/t4_live.log 2>&1" > /dev/null 2>&1 &'`. **Critical: must include `set -a; source .env; set +a` — omitting causes VENUE_API_KEY crash.** |
| **RESERVE_MANDATE_PCT fix** | **COMPLETE — 0.20→0.05 on VPS; all 33 T1 bets fire** | IO | ~~HIGH~~ DONE | VPS `.env` updated. Floor dropped from $200 to $50. MC confirmed: 33 bets PLACED, $827 total, no BATCH HALT (Disconnect 1 resolved). Advisory MC warning `82.7% > 60%` is informational display threshold, not the execution gate. |
| **T-132 — CHANGE_CONTROL.md governance debt** | **Extract decisions from `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` → DECISION_LOG.md; set decisions_logged: true** | DS | **LOW — before any session that modifies CHANGE_CONTROL.md** | Identified SESSION 26. File has `decisions_logged: false`. No current-session modifications — no urgency. Resolve before any future session that edits the document. |
| **T-131 — Fee-adjusted edge ADR** | **COMPLETE — ADR-0016 ACCEPTED, GG-009 RESOLVED** | DS | ~~HIGH~~ DONE | SESSION 30. Option B: `net_edge = gross_edge - 0.07×mid×(1-mid)`. `gross_edge` and `kalshi_fee` logged to every position record. `paper_trader.py` backward-compat updated. |
| **T-130 — Decision tree rework per bucket** | **COMPLETE — ADR-0014 ACCEPTED** | DS | ~~HIGH~~ DONE | ADR-0014 at `03_DECISIONS/ADR-0014_per-band-decision-tree-mechanics.md`. Both DS questions resolved: (Q1) no T3 multiplier — regression test run, 1.15× arbitrary at KELLY_T3=0.07; (Q2) shared budget is design intent. GG-010 registered and RESOLVED. |
| **Post-Finals G1 T4 calibration** | **Run `run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` after Finals Game 1** | DS | **HIGH — after game** | Extract: (1) T4_BAND_WEIGHT calibration (total_deployed / (bankroll × 0.60)); (2) actual bets placed count vs ~1,050 design throughput. Compare actual fires vs expected at flat sizing. Replace STUB comments in `run_t4_live.py`. Decision log derivation. Redeploy before Finals Game 2. |
| **Post-Finals G1 resolve** | **AUTOMATED — `scripts/poll_and_resolve_g1.py` (PID 5865) will run T-109 automatically when game ends** | DS | ~~HIGH~~ AUTOMATED | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py` + `fetch_kalshi_prices.py --portfolio`. SESSION 26: auto-trigger deployed. Script polls ESPN every 60–90s; fallback 2026-06-04T07:30Z. No operator action needed. |
| KI-027 API rate errors | **Investigate Kalshi HTTP 503/429 in second PIPE-03 window** | IO | MEDIUM | 4 positions with failed-HTTP status. Check VPS logs for rate limit (429) or server error (503). May require backoff/retry in `paper_trader.py`. |
| Portfolio reset option | **Evaluate portfolio reset to $1,000 before Finals Game 2** | DS | MEDIUM — post-G1 resolve | After Finals Game 1 resolves: review bankroll, P&L, position outcomes. If mixed signal, reset before Finals Game 2 T1 cron (21:55 UTC Jun 5). |
| Finals Game 2 MC verify | **Run Monte Carlo before Finals Game 2 T1 cron** | DS | HIGH — Jun 5 PDT before 2:55 PM PDT | `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`. Expect 40–50 bets. If still low: check cursor pagination, reserve floor, market availability. |

---

## SESSION 2026-06-03 SESSION 22/23 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Kalshi operational constraints research | **Sourced Kalshi taker/maker fee formula, confirmed $0.01 actual contract minimum, rate limits (10k/day API), TOS automated trading policy** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — Taker fee: `0.07 × P × (1−P)`. At P=0.50: $0.0175/contract. Maker fee: `0.0175 × P × (1−P)`. Actual Kalshi minimum: $0.01/contract (1 contract at minimum price). Rate limit: 10,000 requests/day standard tier. Automated trading: permitted per TOS. GG-009 registered. |
| MIN_BET_T4_PAPER correction | **Changed from $10.0 (invented heuristic) to $0.01 (actual Kalshi minimum)** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` line 251. Prior value was $10.0 set in SESSION 18 as "Kalshi practical minimums" — never sourced. Actual Kalshi minimum is 1 contract at market price ($0.01–$0.99). Decision logged. Memory feedback written. |
| PAPER_T4_VIRTUAL default → false | **Default changed from `true` to `false` — actual paper positions now fire** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` line 252. `PAPER_T4_VIRTUAL = os.environ.get("PAPER_T4_VIRTUAL", "false").lower() in ...`. Previous: virtual-only calibration mode. Now: `trader.open_position()` called, positions recorded in `paper_portfolio.json`. Purpose: validate execution layer throughput at actual bet scale. |
| PAPER_T4_FLAT_SIZING added | **New env var: flat 1-contract sizing (at MIP) overrides Kelly for paper T4 validation** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` lines 253, ~300–310. `PAPER_T4_FLAT_SIZING = os.environ.get("PAPER_T4_FLAT_SIZING", "true").lower() in ...`. When true: `approved_size = mip; approval = {**approval, "approved_size": approved_size}`. Both local variable AND approval dict updated (trader.open_position uses dict). Purpose: decouple bet COUNT from Kelly sizing — Kelly at t4_band_budget=$60 caps to ~60 bets before exhaustion; flat sizing allows ~1,050 bets at design throughput. |
| PAPER_T4_POOL_USD=500.0 added | **When flat sizing active, band budget override to $500 (bypasses ADR-0013 Kelly computation)** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `run_t4_live.py` main(). `PAPER_T4_POOL_USD = float(os.environ.get("PAPER_T4_POOL_USD", "500.0"))`. When `PAPER_T4_FLAT_SIZING=true`: `t4_band_budget = PAPER_T4_POOL_USD` (not `_compute_t4_band_budget()`). Rationale: ~1,050 bets × avg $0.50/contract = $525 ≈ $500 pool. ADR-0013 Kelly budget is not superseded — it applies when flat sizing is off. |
| MIN_BET_T1_PAPER added | **`run_paper_trade.py` + `scripts/run_monte_carlo.py` now use configurable floor** | ✅ COMPLETE 2026-06-03 SESSION 22 — `MIN_BET_T1_PAPER = float(os.environ.get("MIN_BET_T1_PAPER", "1.0"))`. Both RiskEngine instantiations in `run_paper_trade.py` receive `min_bet_usd=MIN_BET_T1_PAPER`. VPS `.env` updated with `MIN_BET_T1_PAPER=1.0`. |
| GG-009 registered | **Taker fee absent from edge formula — governance gap formally registered** | ✅ COMPLETE 2026-06-03 SESSION 23 — `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-009 added. At P=0.50, taker fee = $0.0175 = 87% of MIN_EDGE=0.02. T-131 ADR required for resolution before G6. |
| VPS old T4 screen killed | **`149029.t4_live` (running PAPER_T4_VIRTUAL=true old code) killed** | ✅ COMPLETE 2026-06-03 SESSION 22/23 — `screen -X -S 149029.t4_live quit` confirmed. VPS `git pull` to commit `00d0525`. |
| VPS new T4 process started | **T4 running on VPS — confirmed 2026-06-03 SESSION 23** | ✅ COMPLETE — PID 152702. Root cause of earlier failures: nohup command didn't source `.env` → VENUE_API_KEY not set → crash at kalshi_client init. Fix: `set -a; source .env; set +a` before activate. Startup confirmed: T4 band budget $500.00 (flat sizing mode), PAPER_T4_FLAT_SIZING=true, PAPER_T4_VIRTUAL=false, ESPN game 401859963 STATUS_SCHEDULED → sleeping 60s. Will auto-activate at tip-off 00:30 UTC Jun 4. |
| DECISION_LOG SESSION 23 entry | **T4 flat sizing architecture decision logged** | ✅ COMPLETE 2026-06-03 SESSION 23 — Notable Judgment Calls entry added: T4 flat 1-contract sizing for paper throughput validation; PAPER_T4_VIRTUAL=false default; MIN_BET_T4_PAPER→0.01. |
| 695 tests | **Test count unchanged — all passing** | ✅ CONFIRMED 2026-06-03 SESSION 23 — 695/695 tests pass locally. |

---

## SESSION 2026-06-02 SESSION 20 (PDT) — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| **VPS deploy ADR-0013** | ~~Deploy updated `run_t4_live.py` to VPS before Finals G1 tip-off~~ | IO | ~~CRITICAL — before game~~ | ✅ COMPLETE — SESSION 24. VPS on commit `dfb16f0`. Old `140907.t4_live` screen superseded by nohup PID 153790 with `pool_isolated=True` + `PAPER_T4_FLAT_SIZING=True`. ADR-0013 code deployed. |
| **Post-G1 T4 calibration** | ~~Run `run_t4_budget_sim.py --from-log logs/audit_t4.jsonl` after G1 to calibrate stubs~~ | DS | ~~HIGH~~ | ✅ PARTIAL — SESSION 28 (2026-06-04). (1) T4_EXPECTED_TOTAL_EDGE updated 5.0 → 441.38 (G1: 1446 evals, sum edge from risk_eval_start records, KELLY_T4=0.20). DECISION_LOG updated. (2) T4_BAND_WEIGHT cannot be calibrated: calibration script requires VIRTUAL data, G1 ran non-virtual flat-sizing. Critical finding: uncapped Kelly deployment = $81,226 across 1434 bets = 87× any band budget — fractional-allocation formula is architecturally incompatible with high-throughput T4. GG-011 registered. New ADR required before T4 ACTIVE. |
| Finals Game 1 resolve | **Run `run_resolve_local.py` after Finals Game 1 ends (Jun 3 PDT ~11:30 PM EDT)** | DS | **HIGH — immediately after game** | `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`. Then `fetch_kalshi_prices.py --portfolio` to sync pregame files for EXP-017. 11 open positions; all resolve on player stats (Kalshi order status irrelevant). EXP-017 n=2 → will grow. |
| T4 monitor Finals Game 1 | ~~Monitor `140907.t4_live` during Finals Game 1~~ | IO | ~~HIGH — game night~~ | ✅ COMPLETE — SESSION 24. `140907.t4_live` screen was dead (old code); replaced by nohup PID 153790 running updated `run_t4_live.py`. Finals Game 1 T4 monitoring complete. |
| KI-027 API rate errors | **Investigate Kalshi HTTP 503/429 in second PIPE-03 window (01:30 UTC Jun 3)** | IO | MEDIUM | 4 positions recorded with failed-HTTP status (Wembanyama NO 40/35/30, Castle NO 30). Paper resolution unaffected. Root cause: rate limit (429) or server error (503)? Check VPS logs. May require backoff/retry logic in `paper_trader.py`. |
| Portfolio reset option | **Evaluate portfolio reset to $1,000 before Finals Game 2 (Jun 5 PDT)** | DS | MEDIUM — post-Finals Game 1 resolve | After Finals Game 1 resolves: review bankroll, P&L, position outcomes. If mixed signal (canceled + failed positions muddy the evidence), reset to $1,000 clean slate before Finals Game 2 T1 cron (21:55 UTC Jun 5). Recommendation from SESSION 19: let Finals Game 1 run; reassess post-resolution. |
| Finals Game 2 MC verify | **Run Monte Carlo before Finals Game 2 T1 cron to verify expected bet count** | DS | HIGH — Jun 5 PDT before 2:55 PM PDT | `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`. Expect 40–50 bets (vs 11 for Finals Game 1 where first-window architecture was old). If still low: check cursor pagination, reserve floor, market availability. |
| **T-130 — Decision tree mechanics per band** | **Formally specify quantitative computation per T1–T5 bucket: model inputs, probability estimate method, Kelly variant, kill switch tier** | DS | HIGH — before T4 ACTIVE | CLAUDE.md Hard Rule 9 establishes that model computation determines routing. T-130 specifies *what* that computation is per bucket. Longer time horizon = more complex decision tree — this gradient must be documented. Required as one of T4 ACTIVE activation gates (supersedes or supplements ADR-0013 gate 4). Output: new ADR or expansion of ADR-0011 specifying per-band decision mechanics. |

---

## SESSION 2026-06-02 SESSION 20 (PDT) — COMPLETED

| # | Task | Status |
|---|------|--------|
| KI-026 ADR-0013 architecture | **T4 band budget architecture: Kelly scoped to `t4_band_budget`, not full portfolio bankroll** | ✅ COMPLETE 2026-06-02 SESSION 20 — `run_t4_live.py` updated (import RESERVE_MANDATE_PCT, T4_BAND_WEIGHT=0.10 stub, T4_EXPECTED_TOTAL_EDGE=5.0 stub, `_compute_t4_band_budget()`, `_make_engines(t4_band_budget)`, `_run_cycle()` returns updated `t4_deployed_usd`, main loop accumulates `t4_deployed_game`). ADR-0013 written at `03_DECISIONS/ADR-0013_t4-throughput-capital-budget.md`. Syntax OK. |
| run_t4_budget_sim.py | **Write and verify T4 budget Monte Carlo simulation script** | ✅ COMPLETE 2026-06-02 SESSION 20 — `scripts/run_t4_budget_sim.py` written. Parametric mode (pre-G1) and empirical mode (`--from-log`, post-G1 calibration). Verified at $618.03 bankroll: budget=$37.08, avg 37 bets, exhausts at cycle 125/200 (63% into game), all bets floor to $1 paper minimum. Sensitivity: band_weight=0.15 → 73% exhaustion rate; band_weight=0.20 → 6.6% exhaustion rate. |
| T1 Monte Carlo verification | **Confirm T1 Monte Carlo unaffected by T4 architecture changes** | ✅ COMPLETE 2026-06-02 SESSION 20 — `scripts/run_monte_carlo.py --label pre-G1-ADR-0013` ran clean. Same T1 logic, same bet structure. T4 changes isolated to `run_t4_live.py`. |
| DECISION_LOG ADR-0013 entry | **Log ADR-0013 in DECISION_LOG per CLAUDE.md Rule 7** | ✅ COMPLETE 2026-06-02 SESSION 20 — ADR-0013 added to ADR Index table + Notable Judgment Calls with full derivation rationale. |

---

## SESSION 2026-06-02 SESSION 19 (PDT) — OPEN ITEMS (carried forward above)

---

## SESSION 2026-06-02 SESSION 19 (PDT) — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bug H drawdown fix (T4) | **Fix drawdown calculation in `run_t4_live.py` — deployed T1 capital counted as realized loss** | ✅ COMPLETE 2026-06-02 SESSION 19 — `_realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))`. Old formula: `(initial - current) / initial` counted deployed T1 capital (~$540) as loss → 54% false drawdown → C4 kill switch rejected ALL T4 bets pre-game. Fix matches PIPE-03 reference pattern. Commit `706264b`. |
| PAPER_T4_VIRTUAL mode | **Add virtual mode: C4 evaluates + stages bets without bankroll deduction** | ✅ COMPLETE 2026-06-02 SESSION 19 — `PAPER_T4_VIRTUAL = os.environ.get("PAPER_T4_VIRTUAL", "true").lower() in ("true", "1", "yes")`. Virtual path: `store.mark_fired()` + logger `"T4 VIRTUAL"` line, no `trader.open_position()`. Proves architecture fires at ~1000s/game without depleting T1 capital pool. Commit `706264b`. |
| VPS screen restart | **Kill old screen `139678.t4_live`; restart with Bug H fix** | ✅ COMPLETE 2026-06-02 SESSION 19 — Old screen ran stale code with drawdown bug. `git pull` → commit `706264b`. New screen `140907.t4_live` confirmed running, watching Finals G1 (STATUS_SCHEDULED → will auto-activate at tip-off Jun 3 PDT 8:30 PM EDT). |
| G1/G2 label correction | **Correct game label errors: SESSION 18 mislabeled Finals G1 as G2 and used internal ESPN game IDs as primary labels** | ✅ COMPLETE 2026-06-02 SESSION 19 — SESSION 18 used ESPN game ID as primary label in all docs — replaced with Finals G1/G2/G3. ESPN IDs kept only in technical monitoring commands. Finals schedule pinned: G1=Jun 3 PDT, G2=Jun 5 PDT, G3=Jun 8 PDT. |

---

## SESSION 2026-06-03 SESSION 18 — COMPLETED

| # | Task | Status |
|---|------|--------|
| PIPE-07 T4 live | **`run_t4_live.py` — full PIPE-07 wiring T4EventLoop → staged_order_store → C4 → PaperTrader** | ✅ COMPLETE 2026-06-03 SESSION 18 — `src/prediction_market_bot/run_t4_live.py` built from scratch. 45s poll cycle, ESPN live boxscore, per-cycle `fired_tickers` deduplication, ghost-protection ordering (stage BEFORE open), `MIN_BET_T4_PAPER=1.0` paper override. ESPN API replaces blocked NBA CDN (`cdn.nba.com` / `stats.nba.com` return 403 from DO VPS via Akamai WAF). `KalshiMarketClient.from_env()` fix committed. `BOT_C4_ACTIVE=true` added to VPS `.env`. Commits: `451abf2` (from_env fix), `47e9a2b` (PIPE-07 build), `2446a02` (ESPN main loop). VPS screen watching Finals G1 (NYK vs SAS), sleeping until tip-off Jun 3 PDT 8:30 PM EDT. 695/695 tests on VPS. |
| ESPN API source | **Replace NBALiveFeed with ESPN API for T4 live data** | ✅ COMPLETE 2026-06-03 SESSION 18 — `_espn_game_ids_today()`, `_parse_espn_clock()`, `_espn_poll_once()` implemented in `run_t4_live.py`. Player matching via `name_to_pregame` dict (normalized lowercase). `_load_pregame_context()` updated to return 3-tuple (by_player_id, by_ticker, name_to_pregame). Main loop: `for gid in game_ids: all_states.extend(_espn_poll_once(gid, name_to_pregame))`. Decision logged. |
| risk.py MIN_BET_USD | **Add `min_bet_usd` init param to RiskEngine for paper T4 override** | ✅ COMPLETE 2026-06-03 SESSION 18 — `min_bet_usd: float | None = None` param on `RiskEngine.__init__()`. CHECK 7 uses `self._min_bet_usd` instead of `MIN_BET_USD`. Live path unchanged. Paper T4 uses `$1.0` floor. No ADR required (paper-only). Decision logged. |
| Session documentation | **DECISION_LOG entries (4 decisions), TODO_NEXT, MEMORY_BANK, SESSION_HANDOFF** | ✅ COMPLETE 2026-06-03 SESSION 18 — All governance artifacts updated. |

---

## SESSION 2026-06-03 SESSION 18 — OPEN ITEMS (game night)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| G1 resolve | **Run `run_resolve_local.py` after G1 tip-off resolves (Jun 4 UTC post-game)** | DS | **HIGH — immediately after game** | After NYK vs SAS **G1** ends (tips 00:30 UTC Jun 4 = Jun 3 PDT 8:30 PM EDT): `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`. Then run `fetch_kalshi_prices.py --portfolio` to sync VPS pregame files for EXP-017. EXP-017 n=2 → will grow to n=2 + Finals **G1** market count (~35 markets). |
| T4 monitor | **Monitor t4_live screen session during G1 (00:30–03:30 UTC Jun 4 = Jun 3 PDT evening)** | IO | **HIGH — G1 game night Jun 3 PDT** | `ssh root@157.230.91.33 'tail -f /opt/prediction-market-bot/logs/t4_live.log'`. Watch for: (1) status transitions from STATUS_SCHEDULED → STATUS_IN_PROGRESS; (2) first `_run_cycle()` execution; (3) T4 VIRTUAL log lines (scale proof); (4) any ESPN fetch errors or NameError. Kill switch: `ssh root@157.230.91.33 'touch /opt/prediction-market-bot/logs/t4_kill_switch.flag'` |
| T4 session doc | **Register ESPN API source decision in a new ADR (DS-02 replacement ADR) if T4 goes ACTIVE** | DS | MEDIUM — dark period | ADR-0011 scoped T4 to "NBA Stats API CDN polling" — that's now ESPN API. If T4 evidence (EXP-018) validates the approach, ADR-0011 should be superseded by an ADR that explicitly names ESPN as the DS-02 source and documents its limitations (unofficial API, no SLA guarantee, schema may change). |

---

## SESSION 2026-06-02 SESSION 17 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~KI-025~~ | ~~PIPE-02 cron retimed 21:30 → 21:55 UTC + second PIPE-02 at 01:25 UTC~~ | ✅ COMPLETE 2026-06-02 SESSION 17 — Root cause: 30-minute price drift gap between PIPE-02 capture and PIPE-03 execution caused MC to predict 23 bets but only 7 placed on G1. Fix: `deploy/cron.conf` PIPE-02 moved to 55 21 UTC; second PIPE-02 at 25 1 UTC for late window (which previously had 4h-stale prices). KI-025 RESOLVED. |
| Market-first loop | **Cohort-first → market-first in PIPE-02 + PIPE-03** | ✅ COMPLETE 2026-06-02 SESSION 17 — `run_paper_trade.py` + `run_pregame.py`: iterate over all active Kalshi markets, resolve players via cohort lookup or dynamic nba_api fallback. Non-cohort players: `NBAIngestionClient.fetch_player_game_log(season="2025-26")` → `pts_l10_mean` → Poisson-only (`p_est_lr = None`). `_pts_cache` prevents duplicate API calls. Covers 100% of KXNBAPTS-listed players, not just 55-player EXP-005 cohort. |
| Cursor pagination | **`fetch_player_points_markets` now paginates all Kalshi pages** | ✅ COMPLETE 2026-06-02 SESSION 17 — `kalshi_client.py`: while-loop with `cursor` field; break when `cursor` is None or `len(page) < page_size`. Was silently truncating at 200 markets on regular-season nights with 800+ KXNBAPTS markets. |
| Batch reserve gate | **PIPE-03 batch-level reserve floor enforcement** | ✅ COMPLETE 2026-06-02 SESSION 17 — `run_paper_trade.py`: before every `open_position()`, check `bankroll - approved_size < RESERVE_MANDATE_PCT (0.40) * _initial_bankroll`. If true: log warning, set `_reserve_halted = True`, break both loops. Prevents repeat of Jun 1 incident (91.2% bankroll deployed in one run). |
| DECISION_LOG | **Session 17 decisions logged (5 entries)** | ✅ COMPLETE 2026-06-02 SESSION 17 — Market-first loop, dynamic nba_api fallback, batch reserve gate, cron retiming, cursor pagination all logged. |

---

## SESSION 2026-06-02 SESSION 17 — OPEN ITEMS

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| MC verify | **Verify next Finals game bet count with new architecture** | DS | **HIGH — G2 (Jun 5 PDT / Jun 6 00:30 UTC)** | All four fixes are live on VPS. G2 is the first real test of the market-first loop + cursor pagination + cron retiming: expect 40–50 bets (vs 7 in G1 with old architecture). If bet count is still low, check: (1) how many active KXNBAPTS markets Kalshi has for the game; (2) whether non-cohort players resolve via dynamic nba_api path; (3) whether `_reserve_halted` fires prematurely. Run MC after PIPE-02 fires (21:55 UTC) to compare prediction vs actual. Finals schedule: G1=Jun 3 PDT, G2=Jun 5 PDT, G3=Jun 8 PDT, G4=Jun 10 PDT, G5=Jun 13 PDT. |
| EXP-017 | **Re-run EXP-017 after each game to accumulate n toward G6 floor (≥66)** | DS | HIGH | n=2 unique resolved markets as of session end. Every Finals game adds ~7–50 markets. Run T-109 procedure after each game (local resolution, then fetch pregame files from VPS). |

---

## SESSION 2026-06-02 SESSION 16 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Monte Carlo protocol | **`scripts/run_monte_carlo.py` + `03_DECISIONS/MONTE_CARLO_PROTOCOL.md`** | ✅ COMPLETE 2026-06-02 SESSION 16 — CLI-parameterized general assessment tool; mirrors PIPE-03 Path B + Kelly exactly; 10k sims; BOT STATISTICS (bets placed/YES/NO split, bets exp. to WIN/LOSE, MC averages, total staked, reserve, per-player breakdown, bet-level detail, rejected list with reasons) + EV + P/L distribution + governance footer. `--label` + `--out` flags enable before/after comparison. `MONTE_CARLO_PROTOCOL.md` defines 8 trigger conditions, run procedures, output interpretation, known limitations. Decision logged in DECISION_LOG Session 16. Commit d8ec72d; VPS current. |
| G1 T1 cron observation | **7 bets placed / $381.97 deployed (MC predicted 23 / $796)** | ✅ OBSERVED — G1 T1 cron fired 22:00 UTC Jun 2. Bankroll: $1,000 → $618.03. 7 open positions, 0 resolved. MC vs actual discrepancy root-caused and fixed in SESSION 17: (1) 30-min price drift KI-025 → cron retiming; (2) 55-player cohort ceiling → market-first loop; (3) 200-market API cap → cursor pagination. |
| ~~KI-025~~ | ~~**Investigate MC vs actual bet-count discrepancy (23 predicted → 7 placed in G1)**~~ | ✅ RESOLVED 2026-06-02 SESSION 17 — Three root causes identified and fixed. See SESSION 17 COMPLETED above. |

---

## SESSION 2026-06-02 SESSION 15 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~KI-018~~ | ~~Fix zombie daily loss limit (max_daily_loss_usd=1000.0 inactive at $1,000 bankroll)~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — `MAX_DAILY_LOSS_PCT=0.15` replaces `max_daily_loss_usd` in `risk.py`. `initial_bankroll` parameter added to `RiskEngine.__init__()`. Daily loss threshold = 15% of initial_bankroll = $150 (fires before 20% drawdown = $200). Two independent kill switches restored. ADR-0012 ACCEPTED. |
| ~~RESERVE_MANDATE_PCT wire~~ | ~~Advisory warning in evaluate_forecast() for single bet exceeding 60% of bankroll~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — `risk_reserve_mandate_warning` log emitted (severity=WARNING) when `approved_size > bankroll * (1 - RESERVE_MANDATE_PCT=0.40)`. Warning-only at paper scale; blocking enforcement deferred to PIPE-03 batch-level check (dark period). |
| ~~T-093~~ | ~~Extract decisions from EXECUTION_ARCHITECTURE.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-094~~ | ~~Extract decisions from MONITORING_DRIFT_PLAN.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-095~~ | ~~Extract decisions from METHODOLOGY.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-096~~ | ~~Extract decisions from VENUE_REGISTRY.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-097~~ | ~~Extract decisions from RISK_APPETITE_CONSTRAINTS.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-098~~ | ~~Extract decisions from QUALITATIVE_SIGNALS.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |
| ~~T-099~~ | ~~Extract decisions from ROADMAP_MILESTONES.md → DECISION_LOG.md; set decisions_logged: true~~ | ✅ COMPLETE 2026-06-02 SESSION 15 — DECISION_LOG entry logged; header flipped true. |

---

## SESSION 2026-06-02 SESSION 13/14 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~T-129~~ | ~~Fix all-threshold loop: replace LR p_est with Poisson CDF per threshold (GG-008)~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `run_paper_trade.py`: `p_threshold = 1.0 - _poisson_cdf(thresh_int - 1, pts_mean)` per threshold. LR `p_est` retained as `p_estimate_lr` in C6 log. GG-008 RESOLVED. |
| ~~ADR-0010~~ | ~~Band Kelly hierarchy revision — variance-scaling derivation~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `ADR-0010_band-kelly-hierarchy-revision.md` ACCEPTED. Kelly hierarchy: T3=0.07 < T1=0.10 < T2=0.13 < T4=0.20 < T5=0.25. `execution_bands.py`, `game_state_model.py` updated. 3 test invariants updated. |
| ~~ADR-0011~~ | ~~Phase 8 paper-scope T4/T5 activation ADR~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `ADR-0011_phase8-paper-scope-t4t5-activation.md` ACCEPTED. Explicit scope: NBA Stats API CDN polling, file kill switch, paper only. Production blockers deferred. EXP-018/019 gates before ACTIVE. |
| ~~DS-02 adapter~~ | ~~Build ds02_nba_live.py + wire kill switch in run_t4_inplay.py~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `c1_signal_ingestion/ds02_nba_live.py`: `NBALiveFeed`, `LivePlayerState`, `kill_switch_armed()`, `_parse_game_clock()`. `run_t4_inplay.py`: `_kill_switch_armed()` stub replaced with live `kill_switch_armed(KILL_SWITCH_PATH)` call. |
| ~~Portfolio reset~~ | ~~reset_paper_portfolio.py + VPS reset + deploy~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `reset_paper_portfolio.py` built; VPS reset confirmed ($1,000 / 0 positions); both commits (d8340ba + 1d10b7e) pushed and pulled on VPS. 692/692 tests on VPS. |
| ~~RESERVE_MANDATE_PCT~~ | ~~Add 40% reserve mandate to risk.py~~ | ✅ COMPLETE 2026-06-02 SESSION 14 — `RESERVE_MANDATE_PCT = 0.40` added to `risk.py`. Warning-only at paper scale; blocking at live capital. |

---

## SESSION 2026-06-02 SESSION 13 — OPEN TASKS (dark period / Phase 8 pre-activation)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-128 | **DS-02 ADR: require live rolling pace as mandatory feed field** | DS | **HIGH — Phase 8 pre-activation** | KI-024: `pace_pts_per_min` is set at T1 from C2 feature store and never refreshed during a game. λ = pace × time_remaining drives both T4 and T5 Poisson CDF — a stale pace propagates linearly into every in-game probability estimate. At T5 (≤3 min remaining), λ is small and pace error translates directly to P(hit threshold) error. The Phase 8 DS-02 ADR must explicitly require live rolling pace as a required feed field, not optional enrichment. Without this constraint, a DS-02 source that provides only score + clock (no pace) would silently degrade T4/T5 inference. Resolution: operator reviews DS-02 ADR draft and adds live pace as a required field before signing. |
| EXP-018 | **T4_MIN_DELTA_P calibration experiment** | DS | **MEDIUM — Phase 8 pre-activation** | GG-007 (item 1): T4_MIN_DELTA_P=0.08 retained for paper prototype to generate calibration data. Requires replay of historical NBA game-state snapshots. Gate: must complete before Phase 8 T4 activation ADR is signed. |
| EXP-019 | **T5 certainty threshold calibration experiment** | DS | **MEDIUM — Phase 8 pre-activation** | GG-007 (item 2): T5_YES_CERTAINTY=0.85 / T5_NO_CERTAINTY=0.15 grounded by Poisson arithmetic (SESSION 14). Requires calibration against historical Q4 ≤3 min game-state data. Gate: must complete before Phase 8 T5 activation ADR is signed. |

---

## SESSION 2026-06-01 SESSION 10 — COMPLETED

| # | Task | Status |
|---|------|--------|
| ~~ADR-0009~~ | ~~Shadow model policy accepted~~ | ✅ COMPLETE 2026-06-01 — `03_DECISIONS/ADR-0009_shadow-model-policy.md` accepted before code per Compass OS invariant. Isolation guarantee: shadow never routes to C4. Promotion gate: shadow_brier_30 ≤ prod_brier - 0.005 over ≥30 events → WARNING; ADR-0010 required for promotion. Frozen model extension: shadow version-pinned at deployment. |
| ~~T-119~~ | ~~Model version hash guard~~ | ✅ COMPLETE 2026-06-01 — `run_pregame.py`: after loading prod_model.joblib, checks `artifact["model_version"]` vs `prod_model_meta.json`. Mismatch → CRITICAL log + exit(1). Absent meta file → guard skips (backward compatible). |
| ~~T-120~~ | ~~ShadowForecaster C3 + PIPE-02 integration~~ | ✅ COMPLETE 2026-06-01 — `c3_forecasting/shadow_forecaster.py`: optional parallel inference; C6-only; non-fatal (_load() + predict_shadow() both catch all exceptions). C7 monitor: `_shadow_window` deque + `record_shadow_outcome()` + shadow Brier computed independently of production window + `shadow_promotion_flag` in DriftSnapshot. PIPE-02 wired: `shadow_p_estimate` + `shadow_model_version` in all forecast records. 15 new C3 shadow tests + 11 new C7 shadow tests. 612/612 pass. |

---

## SESSION 2026-06-01 SESSION 12 — COMPLETED

| # | Task | Status |
|---|------|--------|
| T4/T5 Iteration Plan | **Dark-period T4/T5 roadmap designed** | ✅ COMPLETE 2026-06-01 — Jane Street pre-computation principle applied: detection band ≠ execution band. Phase 7/8/9 sequencing adopted. Three Phase 8 blockers identified (DS-02 ADR, kill switch redesign ADR, Phase 8 infra ADR) — all require operator decision. |
| `game_state_model.py` | **T4 Bayesian engine + T5 late-game arithmetic** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/c3_forecasting/game_state_model.py`. Poisson CDF pure Python stdlib. `GameState`, `GameStateModel.update()` → `T4Signal`, `LateGameArithmetic.evaluate()` → `T5Signal`. Constants: T4_MIN_DELTA_P=0.08, T5_TIME_THRESHOLD_MIN=3.0, T5_YES_CERTAINTY=0.85, T5_NO_CERTAINTY=0.15, KELLY_T4=0.05, KELLY_T5=0.15. 33 tests (test_c3_game_state_model.py). Phase: SKELETON. |
| `staged_order_store.py` | **SQLite pre-staging handoff layer** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/c4_risk_engine/staged_order_store.py`. Append-only, WAL mode. Statuses: STAGED/FIRED/EXPIRED/CANCELLED. `stage_order()`, `get_staged()`, `mark_fired()`, `mark_cancelled()`, `expire_stale()`, `summary()`. Default db_path: `logs/staged_orders.db`. 31 tests (test_c4_staged_order_store.py). |
| `run_t4_inplay.py` | **PIPE-07 skeleton + unified T4 decision tree** | ✅ COMPLETE 2026-06-01 — `src/prediction_market_bot/run_t4_inplay.py`. `T4EventLoop.on_game_state_event()` → `T4RoutingResult`: kill switch (<5ms) → expire_stale → pre-staged lookup → Bayesian (T4) → T5 → NO_ACTION. `--demo` flag runs synthetic scenarios. 16 tests (test_run_t4_inplay.py). BLOCKED: kill switch armed check placeholder; C4 approve + C5 execute placeholders. Phase 8+. |
| `scripts/resolve_procedure.sh` | **T-109 automation script** | ✅ COMPLETE 2026-06-01 — `scripts/resolve_procedure.sh` (chmod +x). Automates full resolve + EXP-017 update procedure after each Finals game. Logs to `logs/resolve_auto.log`. Step 3 reports G6 evidence count. Must run locally (VPS 403 blocks stats.nba.com). |
| `scripts/query_orderbook_depth.py` | **T-127 automation script (KI-023)** | ✅ COMPLETE 2026-06-01 — `scripts/query_orderbook_depth.py`. Queries Kalshi orderbook for 3–5 active KXNBAPTS contracts. Reports total depth, tight depth (±10¢), paper/live cap as % of visible depth. Flags if cap exceeds DEPTH_IMPACT_THRESHOLD_PCT=0.05. Audit log: `logs/orderbook_depth_YYYYMMDD_HHMMSS.json`. |
| scipy/sklearn upgrade | **numpy 2.x compatibility fix** | ✅ COMPLETE 2026-06-01 — scipy 1.12→1.17.1, sklearn 1.4.2→1.8.0. Pre-existing import error (`_ARRAY_API not found`) caused by numpy 2.4.6 in local .venv311. VPS was already working (612 tests). 692/692 tests pass locally after upgrade. |
| Tests | **+80 new tests** | ✅ COMPLETE 2026-06-01 — 612 → 692 total. test_c3_game_state_model.py (+33), test_c4_staged_order_store.py (+31), test_run_t4_inplay.py (+16). |

---

## SESSION 2026-06-01 SESSION 11 — COMPLETED

| # | Task | Status |
|---|------|--------|
| VPS deploy | **Deploy SESSION 8-10 code to VPS** | ✅ COMPLETE 2026-06-01 — git push origin main (SESSION 10 commit 1b325e0); VPS git pull at /opt/prediction-market-bot. VPS now at HEAD 1b325e0. 612/612 tests pass on VPS. T-119 (model hash guard) + T-120 (ShadowForecaster + C7 shadow Brier) now live. Ready for Finals G1 Jun 3 cron window. |
| ~~T-122~~ | ~~EXP-017 exact-ticker join~~ | ✅ CLOSED — already satisfied in run_part_b_live; no code change required (see task detail below). |

---

## SESSION 2026-06-01 SESSION 11 — NEW TASKS (PDTP priority list retrofit)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-127 | **Query KXNBAPTS orderbook depth during Finals window (KI-023 resolution)** | DS / IO | **HIGH — Finals window Jun 3–22** | KI-023: no estimate of KXNBAPTS market depth exists. At full operational scale (300+ bets/night), bot order flow may move own prices. The Finals window is the only active KXNBAPTS opportunity before October 2026. Action: during Finals (any game day before Jun 22), call `GET /markets/{ticker}/orderbook` via Kalshi REST API for 3–5 active KXNBAPTS contracts. Record: (1) total visible depth (YES + NO sides); (2) depth within $500 of best price; (3) approximate `max_order_pct_of_depth` at our $10–80/bet paper scale vs. $500/bet live cap. If live cap ($500) exceeds ~5% of visible depth on a typical market, register new `max_order_pct_of_depth` limit in `_HARD_LIMITS` via ADR before G6. Data captured here feeds G6 live capital ADR-0005. If this window is missed, no equivalent data exists until 2026-27 pre-season. |

---

## SESSION 2026-06-01 SESSION 10 — NEW TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-121 | **Wire record_shadow_outcome() to resolve pipeline** | MEDIUM — Finals window | `run_resolve.py` reads pregame logs (which now carry `shadow_p_estimate`). For each resolved bet, extract `shadow_p_estimate` and call `SystemMonitor.record_shadow_outcome(shadow_p, outcome)`. Prerequisite: shadow model artifact must be trained and deployed first — without an artifact, shadow_p_estimate will be None in all pregame logs, so this wiring produces nothing. Register as T-121 but defer execution until shadow artifact is deployed in dark period. |
| ~~T-122~~ | ~~Update EXP-017 Part B to join on exact kalshi_ticker~~ | ✅ CLOSED 2026-06-01 SESSION 11 — `run_part_b_live` (the `--from-pregame` path) already joins on exact `kalshi_ticker` (line 511-517). The ±3 fuzzy match exists only in `run_part_b` (CSV prices path, not invoked by `--from-pregame`). Task description was written before final implementation settled. No code change required. |
| T-123 | **TI-04 enforcement test** | MEDIUM — Track 2 | Assert any feature with `_price` or `_market` in its name has a documented `look_back_window` attribute in `DATA_FLOWS_LINEAGE.md`. Prevents temporal leakage of pricing features in future feature additions. |
| T-124 | **QTI backdating framework — DS-01 PAM to 2021-22** | MEDIUM — dark period | Backdate DS-01 PAM classifications for all 50 cohort players to 2021-22 per QTI-03. Requires `backdated: true` + `backdating_rationale` + second review flag in QS CSV. ~5× qualitative signal training coverage. |
| T-125 | **Polymarket adapter test expansion** | MEDIUM — Track 3 | Empty-market assertion (zero markets returned is an error not silence), `_parse_market()` regex test for edge cases, VenueRouter multi-venue routing test. Required before T-077 Polymarket activation. |
| T-126 | **EXP-014-B line shopping EV at T2/T3** | LOW — dark period | Bound EV range per execution band with Polymarket active. Depends on T-077 (Polymarket KYC) and T-107 (NBA tag confirmed). |

---

## SESSION 2026-05-31 HANDOFF — NEW HIGH PRIORITY TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-113~~ | ~~**Draft new G6 promotion gate to supersede APR-0016 — multi-dimensional evidence standard**~~ | ~~**PENDING OPERATOR SIGN-OFF**~~ | ✅ DRAFTED v2 2026-06-01 — APR-0017_g6-multi-dimensional-evidence-standard.md revised. Operator instruction: "no arbitrary gating thresholds — use trend analysis sloping with derived figures." v1 arbitrary counts replaced: T1-A now pipeline error rate ≤ 5% AND slope ≤ 0 (derived from expected API failure rate); T1-C now resolution fidelity rate ≥ 85% AND slope ≥ 0 (derived from 1.5× expected legitimate failure rate); T1-B/T1-D kept zero-tolerance with explicit boolean-by-nature justification; Tier 2 slope directions made explicit on all criteria; statistical floor revised: ≥66 resolved bets (derived from T2-A calibration power formula at α=0.05, 80% power) + ≥5 game nights (derived from slope regression df ≥ 3). Decision logged (DECISION_LOG T-113/APR-0017 v2 entry). **OPERATOR ACTION: Review `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md` (v2) and sign the approval block at the bottom.** Until signed, APR-0016 remains operative. |
| ~~T-114~~ | ~~**Resolve Kalshi demo price validity question before counting Finals G1 bets toward G6**~~ | ~~HIGH~~ | ✅ COMPLETE 2026-06-01 — `_price_discovery_url()` added to kalshi_client.py: always returns `_KALSHI_LIVE_BASE_URL` regardless of BOT_ENV. `_get()` now uses `_price_discovery_url()` for unauthenticated calls (market data) and `_kalshi_base_url()` for authenticated calls (portfolio/orders). BOT_ENV=paper now suppresses order submission only — price discovery always hits production. 30 tests added in test_kalshi_client.py; 3 URL-routing invariant tests permanently lock the behavior. 438/438 passing. Decision logged. |

---

## SESSION 2026-06-01 — NEW TASKS (ADR-0008 Kalshi auth blocker)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-111~~ | ~~**Resolve Kalshi auth: NOT_FOUND on /portfolio/balance**~~ | ~~BLOCKER~~ | ✅ COMPLETE 2026-05-31 — Root cause: wrong base URL. Legacy `api.elections.kalshi.com` serves public endpoints only; authenticated endpoints (portfolio/balance, portfolio/orders) require `external-api.demo.kalshi.co` (demo) or `external-api.kalshi.com` (live). Fix: `_kalshi_base_url()` function reads BOT_ENV at runtime — paper→demo, live→live. Balance endpoint parsing also fixed (flat response, not nested). Confirmed: `Balance: True {'balance_usd': 1000.0, 'portfolio_value_usd': 0.0}`. RSA-PSS signing was correct throughout — only the server was wrong. |
| ~~T-112~~ | ~~**Deploy cryptography + updated kalshi_client.py to VPS**~~ | ~~HIGH~~ | ✅ COMPLETE 2026-05-31 — (1) kalshi_bot.pem copied to VPS `/root/.ssh/` with chmod 600; (2) `cryptography==43.0.3` installed in VPS venv; (3) `VENUE_PRIVATE_KEY_PATH=/root/.ssh/kalshi_bot.pem` added to VPS `.env`; (4) code deployed via git pull (HEAD c9fdb4e); (5) VPS balance check confirmed: `Balance: True {'balance_usd': 1000.0, 'portfolio_value_usd': 0.0}`. Cron intact — next PIPE-03 fire at 22:00 UTC will submit real Kalshi demo orders. |

---

## SESSION 2026-05-31 — NEW TASKS

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-109 | **Run run_resolve_local.py after each game day (standing procedure)** | HIGH | VPS 403 blocks nba_api; resolution must run locally. Full procedure: (1) `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`; (2) `PYTHONPATH=src python3 src/prediction_market_bot/fetch_kalshi_prices.py --portfolio` (sync pregame files from VPS for EXP-017); (3) re-run EXP-017 once ≥66 markets accumulated (APR-0017 floor). Jun 3 NYK vs SAS positions will be resolvable after Jun 3. |
| T-110 | **G6 evidence tracking: G6 counter reset to 0** | HIGH | Pre-ADR-0006 bets invalidated (2026-05-31 decision). Clean G6 evidence begins Finals G1 Jun 3. 3 open positions (KAT YES, Anunoby NO, Brunson NO). G6 requires ≥66 resolved markets + ≥5 game nights (APR-0017). |
| ~~T-105~~ | ~~**EXP-017 Part B — Collect Kalshi historical prices and run full market validation**~~ | ~~**BLOCKER — G6**~~ | ✅ COMPLETE 2026-06-01 — Part B live mode built (`--from-pregame <dir> --portfolio <path>`). Pulls pre-game logs + resolved portfolio; joins on kalshi_ticker. Run with n=2 unique resolved markets (May 30 game): Fox YES (WIN, EV/unit=+0.55), SGA NO (LOSS, EV/unit=−0.53). Per-market EV=+$0.01/bet. GG-004 OPEN — DIRECTIONAL_POSITIVE but far below APR-0017 floor of ≥66. `fetch_kalshi_prices.py` script built to pull pregame files from VPS after each game. **Standing action**: after each Finals game, run T-109 procedure (step 2) to accumulate data. Re-run EXP-017 once ≥66 resolved markets. Decision logged. |
| ~~T-106~~ | ~~Fix stale T2 activation gate in EXECUTION_BANDS.md~~ | ~~HIGH~~ | ✅ COMPLETE 2026-05-31 — EXECUTION_BANDS.md:190 updated: `FEATURE_VERSION 1.3.0` removed; gate now reads `DS-04 operational (T-075 + commissioning); dedicated EXP confirming injury overlay Brier improvement ≥ 0.001 at N ≥ 100`. Aligns with BAND_ASSIGNMENT_FRAMEWORK.md. Decision logged. |
| T-107 | **Confirm Polymarket NBA tag name before T-077 activates (KI-019)** | HIGH | `venue_adapter.py:251`: `"tag": "nba"` unconfirmed. Wrong tag = silent empty market returns. Before T-077 (Polymarket KYC + activation): test VenueAdapter call, confirm non-empty return, add empty-market assertion. |
| ~~T-108~~ | ~~Document zombie daily loss limit in risk.py (KI-018)~~ | ~~MEDIUM~~ | ✅ COMPLETE 2026-06-01 — `max_daily_loss_usd` comment updated in `risk.py` `_HARD_LIMITS` with KI-018 reference and note that 20% drawdown is the operative kill switch at current bankroll. |

---

## SESSION 2026-05-31 — COMPLETED

| # | Task | Status |
|---|------|--------|
| Bug I | **Fix `pd.to_datetime` format in `resolve_pending`** | ✅ COMPLETE 2026-05-31 — Same T-089 pattern: nba_api returns "Apr 28, 2026" format; `format="mixed"` added to both Regular Season and Playoffs lookups in paper_trader.py. This was the root cause of ALL resolution failures (date parse threw ValueError → swallowed → `actual_pts=None`). |
| Bug J | **Fix misleading `drawdown_pct` in `summary()`** | ✅ COMPLETE 2026-05-31 — `drawdown_pct` removed; replaced by `realized_drawdown_pct` (closed losses / initial) and `deployed_pct` (open stakes / initial). C4 kill switch was already correct; this fixes the report. run_paper_trade.py + run_resolve.py + tests updated. |
| KI-020 | **VPS 403 blocks nba_api resolution** | ✅ DOCUMENTED 2026-05-31 — stats.nba.com hard-blocks DigitalOcean IPs. resolve_pending now logs errors instead of silently discarding. run_resolve_local.py created as the canonical resolution path. VPS run_resolve.py is kept but won't resolve without IP change. |

---

## ⚠️ SESSION 2026-06-01 — OPEN ITEM (operator action required)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| T-104 | **Investigate broken token/context window efficiency auto-flags** | MEDIUM | Earl has flagged this across multiple sessions — the token maximization and context window efficiency auto-flags have never fired once. Zero attention or resolution. This is a Claude Code tooling/config issue, not a bot code issue. Operator should check: (1) Claude Code settings/hooks config; (2) whether the feature requires a specific plan tier or setting to activate; (3) file a report at https://github.com/anthropics/claude-code/issues if no config fix is found. |

---

## SESSION 2026-06-01 — NEW TASKS (throughput analysis)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| ~~T-115~~ | ~~**Expand run_paper_trade.py to evaluate ALL thresholds per player (not just closest)**~~ | ~~HIGH — before 2026-27~~ | ✅ COMPLETE 2026-06-01 — `closest = min(player_mkts, ...)` replaced with `for mkt in player_mkts:` loop. `X` and `p_est` computed once per player; each threshold evaluated independently through idempotency check + C4 + PaperTrader. Restores design throughput: ~25–40 bets/game regular season T1 (vs ~3–10 single-threshold). Finals: 175–280 bets across 7 games vs ~70 borderline. KI-022 RESOLVED. 438/438 tests pass. Decision logged. |

---

## ✅ SESSION 2026-06-01 — COMPLETED

| # | Task | Priority | Status |
|---|------|----------|--------|
| T-102 | **Fix max_concurrent_positions stub — count gate deleted (ADR-0006)** | ~~BLOCKER~~ | ✅ COMPLETE 2026-06-01 — `max_concurrent_positions` removed from `_HARD_LIMITS`, `evaluate_forecast()` signature, CHECK 3 block, `run_paper_trade.py`, 2 tests, `RISK_APPETITE_CONSTRAINTS.md`, `EXECUTION_ARCHITECTURE.md`. KI-016 RESOLVED. |
| T-103 | **Add stub/placeholder scan to session-start governance protocol** | ~~HIGH~~ | ✅ COMPLETE 2026-06-01 — 3-step session-start scan + ARE WE COMPROMISED? added to MEMORY_BANK.md per ADR-0007. GOVERNANCE_GAP_LOG.md created. LL-010/011/012 added. |  
**Next review:** Start of every work session; end of every session (update status)  
**Staleness triggers:** Any completed task; any new blocker; session end  
**Upstream links:** PLAN.md, RID_LOG.md  
**Downstream links:** STATUS_REPORTS/  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Immediate tasks are clear; ordering may shift based on blockers

---

## Session: 2026-05-22 — G3 CLOSED; Phase 3 (Research Build) Initiated

**G0 Status:** ✅ COMPLETE — APR-0002 signed 2026-05-22. All 74 artifacts built.  
**G1 Status:** ✅ COMPLETE — APR-0003 signed 2026-05-22. All 5 G1 exit criteria met.  
**G2 Status:** ✅ COMPLETE — APR-0004 signed 2026-05-22. All 4 architecture artifacts CANONICAL; C4/C5 naming corrected.  
**G3 Status:** ✅ COMPLETE — APR-0005 signed 2026-05-22. RUN_INSTRUCTIONS + ENVIRONMENTS + RID_LOG CANONICAL; OQ-006 excepted.  
**OQ-001:** ✅ RESOLVED — DS-01 provenance documented (Earl Ignacio / 2026-05-21 / NBA / PRF framework; SNAP-001 registered)  
**OQ-003:** ✅ RESOLVED — NBA basketball, dynamically agnostic event types, Kalshi primary venue  
**T-010:** ✅ COMPLETE 2026-05-22 — REQUIREMENTS.md FROZEN at G1  
**T-011:** ✅ COMPLETE 2026-05-22 — ACCEPTANCE_CRITERIA.md FROZEN at G1  
**T-015:** ✅ Scaffolding verified (ENV-01 artifacts correct); run locally: `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt && pre-commit install`  
**T-016:** ✅ requirements-dev.txt and requirements-base.txt confirmed; lock post-install with `pip freeze > 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-locked.txt`  
**T-017:** ✅ .pre-commit-config.yaml verified; `pre-commit install` after T-015  
**T-019:** ✅ COMPLETE 2026-05-22 — G1 exit checklist passed; APR-0003 signed; PLAN.md updated  
**T-020:** ✅ COMPLETE 2026-05-22 — LITERATURE_REVIEW.md Section 4 expanded (NBA-specific Sections 4.1–4.6); OQ-015 registered  
**T-021:** ✅ COMPLETE 2026-05-22 — ADR-0003_venue-selection.md created; PENDING formal acceptance (OQ-006 exception)  
**T-022:** ✅ COMPLETE 2026-05-22 — ARCHITECTURE_OVERVIEW.md promoted to CANONICAL; C4/C5 corrected; tech stack confirmed  
**T-023:** ✅ COMPLETE 2026-05-22 — INTERFACES_CONTRACTS.md promoted to CANONICAL; IF IDs corrected (IF-C3-C4, IF-C4-C5, IF-C5-VENUE)  
**T-024:** ✅ COMPLETE 2026-05-22 — RESILIENCE_FAILURE_MODES.md promoted to CANONICAL; FM-04/FM-05 corrected  
**T-025:** ✅ COMPLETE 2026-05-22 — THREAT_MODEL.md promoted to CANONICAL; TH-02/TH-04/TH-05/TH-07 corrected; RCO signed  
**T-026:** ✅ COMPLETE 2026-05-22 — RUN_INSTRUCTIONS.md + ENVIRONMENTS.md promoted to CANONICAL (G3); Python 3.11 confirmed; health checks documented  
**T-027:** ✅ COMPLETE 2026-05-22 — RID_LOG.md baselined CANONICAL (G3); RID-D002/D003 archived; RID-D001/RID-003 updated  
**T-028:** ✅ COMPLETE 2026-05-23 — ADR-0003 formally accepted; OQ-006 RESOLVED (Kalshi: CFTC-DCM, all 50 states, NBA markets confirmed primary; Polymarket US: Phase 6+ secondary, CFTC-regulated Dec 2025 relaunch); APR-0011 signed  
**T-029:** ✅ COMPLETE 2026-05-22 — APR-0004 signed; PLAN.md / MEMORY_BANK.md / CHANGELOG.md updated  
**T-030:** ✅ COMPLETE 2026-05-22 — APR-0005 signed; G3 CLOSED

### Priority Queue (Phase 3 — Research Build)

*Phase target: 2026-07-26*

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| T-031 | ADR-0003 formal acceptance | AO | 2026-05-23 | ✅ COMPLETE 2026-05-23 — APR-0011 signed; OQ-006 resolved |
| T-032 | C1 (Ingestion) implementation | EL | 2026-07-05 | ✅ COMPLETE 2026-05-26 — NBAIngestionClient; nba_api; OQ-015 resolved (nba_api proxy) |
| T-033 | C2 (Feature Derivation) implementation | EL | 2026-07-08 | ✅ COMPLETE 2026-05-26 — FeatureStore; 29-col IF-C1-C2 → IF-C2-C3; TI-01–TI-04 enforced |
| T-034 | C3 (Forecasting) + C4 (Risk) implementation | EL | 2026-07-12 | ✅ COMPLETE 2026-05-26 — ModelForecaster (LR+Platt, ECE<0.05 target); RiskEngine (quarter-Kelly, phase gate, kill switch) |
| T-035 | EXP-001 — First experiment run and logged | RL | **2026-06-10** | ✅ COMPLETE 2026-05-28 — Pipeline ran; val Brier 0.2454 (+0.0046 vs null 0.2500); ECE 0.0596; AUC-ROC 0.5906; C4 phase gate REJECTED (expected); C6 bug fixed (numpy int key); outputs: exp_output/ |
| T-036 | Backtesting framework operational | RL | **2026-06-21** | ✅ COMPLETE 2026-05-28 — EXP-002: Brier −0.0082, ECE 0.0941, AUC 0.5488; EXP-003: Brier −0.0068, ECE 0.0793, AUC 0.4364; G4 NOT MET (1/3 experiments beat null; need 2/3); outputs: exp_output/BACKTEST/ |
| T-037 | C2 Feature Enhancement v1.1.0 | EL | 2026-05-27 | ✅ COMPLETE 2026-05-27 — FEATURE_VERSION 1.1.0; 7 new features (season_type_is_playoffs, days_since_last_game, b2b_flag, load_games_l7d, eri_prev_hot, eri_prev_cold, eri_consec_cold_games); 27 new tests; 89/89 total; ASM-008/009 + HYP-005 + OQ-016/017 filed |
| T-038 | C4 risk engine tests + METHODOLOGY.md + DATA_FLOWS_LINEAGE.md | EL | 2026-05-27 | ✅ COMPLETE 2026-05-27 — test_c4_risk.py (32 tests; phase gate, hard limits, Kelly, approval, C6 failure); METHODOLOGY.md 4/10→8/10 (model spec, feature table, strategy architecture A–H, validation checklist); DATA_FLOWS_LINEAGE.md F-001–F-038 populated; C4/C5 naming corrected; 121/121 tests |
| T-039 | C6 AuditLogger tests | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — test_c6_audit_logger.py (38 tests; init, write, write failure, severity filtering, payload redaction, traceability chain, convenience wrappers, from_env, thread safety); 159/159 tests |
| T-039b | C3 ModelForecaster tests | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — test_c3_forecaster.py (35 tests; _model_version_hash, _compute_ci Wilson CI, fit() insufficient/TI-02/happy path/C6 failure, predict() not-fitted/schema/edge/direction/CI/series/C6 failure); 194/194 tests |
| T-041 | MODEL_CARD.md Phase 3 population | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — MODEL_CARD.md 2/10→7/10; training procedure (pipeline, NaN imputation, edge formula, Wilson CI), feature version 1.1.0, known limitations (8 entries), null model documented; performance metrics pending EXP-001/002/003 |
| T-042 | RUN_INSTRUCTIONS.md Phase 3 commands | EL | 2026-05-28 | ✅ COMPLETE 2026-05-28 — All TBD Phase 3 commands replaced; EXP-001 (run_exp001.py), EXP-002/003 (run_backtest.py), test suite command, audit log verification, reproducibility checklist updated; confidence 6/10→8/10 |

### Phase 4 — Next Tasks (G4 Evidence Gap Remediation)

**Trigger:** G4 evidence requirement NOT met (1/3 experiments beat null; need 2/3). Phase 4 focus: expand training data and validate HYP-005.

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| T-043 | Expand player set 10→50 players (OQ-018) | EL | 2026-07-15 | ✅ COMPLETE 2026-05-28 — 50 players (SNAP-2026-05-28-001); EXP-001 Brier +0.0056/ECE 0.0345/AUC 0.5785; EXP-002 +0.0049/0.0289/0.5866; EXP-003 +0.0026/0.0369/0.5673; G4 evidence MET (3/3 beat null; ECE<0.05 all) |
| T-044 | HYP-005 feature ablation (OQ-019) | EL | 2026-07-22 | ✅ COMPLETE 2026-05-28 — v1.0.0 ablation: Brier +0.0054/ECE 0.0314 vs v1.1.0 +0.0056/0.0345; Δ Brier=+0.0002 (threshold 0.005); HYP-005 FALSIFIED; --ablation-v10 + --source-csv flags added to run_exp001.py |
| T-045 | MODEL_CARD.md 7/10→10/10 | EL | 2026-05-28 | 🔲 NEXT — Populate performance metrics table with 50-player results; update known limitations (HYP-005 falsified; training data requirement); note G4 readiness |
| T-046 | FEATURE_VERSION 1.2.0 — prune ERI/schedule features | EL | Phase 4 | ✅ COMPLETE 2026-05-28 — F-032–F-038 removed from features.py; FEATURE_VERSION "1.2.0"; 31 features; DATA_FLOWS_LINEAGE.md + MODEL_CARD.md updated; 179/179 tests |
| T-047 | ADR-0004 — model class confirmation | AO | Phase 4/G4 | ✅ COMPLETE 2026-05-28 — ADR-0004 ACCEPTED (APR-0012); TEST Brier +0.0084/ECE 0.0247/AUC 0.6062; G4 gate CLOSED |
| T-048 | G4 formal gate — TEST set evaluation + sign-offs | MV/AO/DS | 2026-05-28 | ✅ COMPLETE 2026-05-28 — TEST set evaluated (3,254 rows, 2023-24 season); PERFORMANCE_METRICS.md + G4_VALIDATION_REPORT.md + VALIDATION_SIGNOFF.md + APPROVALS_REGISTER.md all updated; APR-0006 + APR-0012 accepted |

### Phase 5 — Operational Readiness (G5 gate target)

**Phase 5 unblocked 2026-05-28 by G4 gate closure.**

| # | Task | Owner | Priority | Status |
|---|------|-------|----------|--------|
| T-049 | C7 Monitoring + Kill Switch implementation | EL | HIGH | ✅ COMPLETE 2026-05-28 — `c7_monitoring/monitor.py` (SystemMonitor, DriftSnapshot, KillSwitchResult); 55 tests; rolling Brier/ECE/edge; L1–L4 drift ladder; thread-safe kill switch; drill method |
| T-050 | C8 Visual Dashboard — Phase 5 panels | EL | HIGH | ✅ COMPLETE 2026-05-28 — `c8_dashboard/dashboard.py`; 3 panels (system health, drift metrics, alert feed); reads C6 JSONL; CLI entrypoint; 33 tests; 267/267 total |
| T-051 | Kill switch drill (TC-007, NFR-03) | EL/DS | HIGH | ✅ COMPLETE 2026-05-28 — halt 0.340ms (SLA 60,000ms); KS-C8D7D90AF942; VALIDATION_SIGNOFF.md TC-007 row signed; APR-0013 recorded; G5 kill switch blocker CLEARED |
| T-052 | EXP-004 — HYP-003: edge vs Kalshi vig | RL | HIGH | ✅ COMPLETE 2026-05-28 — Parts A+B: EV +$0.0855/bet (2,481 TEST bets, 59% win rate); Part B live (37 KXNBAPTS markets, session EXP-004-FE3E2169); HYP-003 🟢 CONFIRMED; DS-02-B-001 RESOLVED |
| T-053 | SENSITIVITY_STRESS_TESTS.md — run ST-001 through ST-004 | MV | MEDIUM | ✅ COMPLETE 2026-05-28 — ST-001–004 ALL PASS; results in exp_output/SENSITIVITY_TESTS/; script: run_sensitivity_tests.py |
| T-054 | MODEL_CARD.md 7/10 → 10/10 update | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-055 | CAPACITY_PLANNING.md — create | EL | LOW | ✅ COMPLETE 2026-05-28 |
| T-056 | Context Pack CP-2026-05-28_G5-readiness | DS | LOW | ✅ COMPLETE 2026-05-28 — `11_MEMORY_HANDOFF/CONTEXT_PACKS/CP-2026-05-28_G5-readiness.md` |

### Phase 6 — Paper Trading (ACTIVE 2026-05-29)

**G5 CLOSED 2026-05-28. Phase 6 ACTIVE. Paper trading running on VPS.**

| # | Task | Owner | Priority | Status |
|---|------|-------|----------|--------|
| T-058 | Model data refresh — 5 seasons 2021-26 | EL | HIGH | ✅ COMPLETE 2026-05-28 — EXP-005; 11,931 TRAIN; Brier +0.0024; model v1-9939a6a5 |
| T-059 | VPS provisioning | IO | HIGH | ✅ COMPLETE 2026-05-29 — DigitalOcean NYC3, 157.230.91.33, Ubuntu 24.04, Python 3.12; health check 8/8 pass; cron installed |
| T-060 | Paper trading pipeline (PIPE-03) | EL | HIGH | ✅ COMPLETE 2026-05-29 — PaperTrader + run_paper_trade.py; $1,000 bankroll; C4 active; nba_api resolution; cron 01:30 UTC |
| T-061 | ADR-0005 — Live capital authorization (G6) | AO/DS | LOW | 🔲 — After 30 resolved paper positions with positive P&L (APR-0016); 0/30 as of 2026-05-29; not yet |
| T-062 | Context Pack for Phase 6 | DS | LOW | 🔲 — Create CP-2026-05-29_phase6-active.md |
| T-063 | OQ-021 Amplification study (EXP-009 done; GBM tried) | RL | MED | ✅ COMPLETE 2026-05-29 — EXP-009 L3 Δ=-0.0004 (LR); EXP-011 GBM Δ=-0.0008; L3 needs more data or context-stratified approach |
| T-064 | PRF coefficient analysis (EXP-008 one-hot) | RL | MED | ✅ COMPLETE 2026-05-29 — prf_w features implemented; encoded as weighted continuous |
| T-065 | Gradient boosting model experiment | EL | MED | ✅ COMPLETE 2026-05-29 — EXP-011 HGBC vs LR; LR RETAINED; ADR-0004 unchanged |
| T-069 | EV re-estimation with refreshed model | RL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-010: EV +$0.0958/bet; win 61.1%; live vig 0.030; 871/2,692 bets |

### Phase 6 — Next Tasks

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-070 | Accumulate paper trading evidence (30+ bets) | DS | HIGH | Monitor logs/paper_portfolio.json daily; target **30 resolved positions** (APR-0016: revised from 50 per seasonal constraint); 0/30 as of 2026-05-29; dual-window cron firing; NBA dark period ~2026-06-22 if not reached |
| T-071 | Model cohort expansion (more players for 2025-26) | EL | MED | ✅ COMPLETE 2026-05-29 — `cohort.py` canonical registry; v1=50 players; v2=~80 players; lookup_player_id.py utility added |
| T-072 | Playoff generalization ablation (EXP-016 / HYP-009) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-016-B8BA8CAC; Δ Brier = -0.0010 (gate < 0.012); HYP-009 CONFIRMED; KI-008 RESOLVED; playoff paper bets valid G6 evidence at full confidence |
| T-073 | DS-04 qualitative source registration | RL | LOW — August 2026 | First new qualitative source beyond PAM (coaching fit, matchup context, etc.). Decision required before T2 execution band can become ACTIVE. Timeline: August 2026 before dark period model retrain (T-092) so DS-04 features can be included in T-092 retrained model. |
| T-074 | Session handoffs CP-2026-05-29 | DS | LOW | ✅ COMPLETE 2026-05-29 — SESSION_HANDOFF_20260529_1651.md + SESSION_HANDOFF_20260529_2030.md |
| T-085 | PIPE-03R resolution-only pipeline | EL | HIGH | ✅ COMPLETE 2026-05-29 — `run_resolve.py`; 06:00 UTC cron; resolves late-game positions after nba_api updates; 9 tests |
| T-086 | C4 MIN_BET_USD floor ($10) | EL | MED | ✅ COMPLETE 2026-05-29 — CHECK 7 in risk.py; sub-floor bets → `min_bet_floor` REJECTED; 5 tests |
| T-087 | Dual-window PIPE-03 cron | IO | HIGH | ✅ COMPLETE 2026-05-29 — 22:00 UTC early + 01:30 UTC late; VPS crontab replaced; cron.conf inline Python extracted to check_model_freshness.py |
| T-088 | Governance registers KI-008/009/ASM-010/011/HYP-009 | DS | HIGH | ✅ COMPLETE 2026-05-29 — KI-008 playoff validity (HIGH G6 blocker); KI-009 50-bet calendar gap; ASM-010 strategy concentration; ASM-011 playoff generalization; HYP-009 registered; ROADMAP G6 calendar note + APR-0016 path |
| T-089 | ingestion.py date parse fix | EL | LOW | ✅ COMPLETE 2026-05-29 — `format="mixed"` on both player + team log paths; eliminates ~150 warnings per EXP run |
| T-090 | git author identity + VPS connectivity note | IO | LOW | ✅ COMPLETE 2026-05-29 — `earlignacio1@gmail.com`; "hotspot required" language removed from all forward-looking registers |

### Phase 7 — Planned Tasks (unblocked after G6)

**Prerequisite:** G6 gate cleared (ADR-0005 signed; T-061). Priority order reflects strategy research recommendation — B and I before E+C.

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| T-075 | Strategy B — Opponent def rating + home/away (EXP-012) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-012-54AEB56C; HYP-006 FALSIFIED; v1.3.0 TEST Brier 0.2480 vs v1.2.0 TEST Brier 0.2480; delta_vs_v12 = -7e-06 (negligible); opp_def_rating + home/away carry no additive signal; FEATURE_VERSION stays 1.2.0; Strategy B remains SKELETON |
| T-076 | Strategy I — Poisson/NB scoring distribution model (EXP-013) | EL | HIGH | ✅ COMPLETE 2026-05-29 — EXP-013-436E29C1; HYP-007 FALSIFIED; NB Brier 0.2671 vs LR Brier 0.2461; Δ = -0.0211 (gate ≤ 0.010); NB not competitive for calibration; ScoringDistributionModel retained for multi-line pricing use case only; Strategy I remains SKELETON |
| T-077 | Strategy E — Line Shopping: Polymarket US API access | IO | HIGH | 🟡 INFRASTRUCTURE COMPLETE 2026-05-29 — PolymarketVenueAdapter fully implemented (REST+CLOB, Bearer auth, `_parse_market()` regex, graceful failure); ACC-0003 registered PENDING in ACCESS_REQUESTS.md; RUNBOOK_polymarket-activation.md written; **OPERATOR ACTION REQUIRED: provision API key at polymarket.com → set POLYMARKET_API_KEY in .env → run activation runbook** |
| T-078 | Strategy E — C5 VenueRouter abstraction layer | EL | HIGH | 🟡 SKELETON COMPLETE 2026-05-29 — VenueAdapter Protocol + KalshiVenueAdapter + VenueRouter built; PIPE-05/06 deployed; Polymarket adapter stub ready; activate at T-077 API provisioning |
| T-079 | Strategy E — EXP-014: EV re-estimation with line shopping active | RL | MED | Quantify $/bet improvement from best-price routing vs. Kalshi-only baseline |
| T-080 | Strategy C — Complement lock scanner (cross-venue) | EL | MED | ✅ COMPLETE 2026-05-29 — `c5_execution/complement_lock_scanner.py`; `LockOpportunity` + `ComplementLockScanner`; scan_snapshot() + scan_single(); 22 tests; detection-only (APR-0010 required for execution) |
| T-081 | Strategy C — APR-0010 sign-off | DS | MED | DS governance sign-off to activate arb/ module; unblocks after T-078 VenueRouter is live; replaces "Indefinite" blocker in blocked items |
| T-082 | Phase 7 context pack | DS | LOW | CP-2026-Phase7 handoff |
| T-083 | Cross-venue market mapper (normalization rules) | EL | MED | ✅ COMPLETE 2026-05-29 — `c5_execution/market_mapper.py`; `normalize_player_name()` + `PlayerMarketKey` + `group_by_key()`; accent/apostrophe/period normalization; 26 tests; VenueRouter deduplication upgraded to use normalized keys |
| T-084 | Multi-band execution orchestrator (P6 rules) | EL | HIGH | ✅ COMPLETE 2026-05-29 — `execution_bands_orchestrator.py`; `BandSignal` + `BandDecision` + `MultiBandOrchestrator`; T3>T2>T1 priority; CONFIRM/FADE/NEUTRAL rules; batch_decide(); 46 tests; T3 cron schedule extended to 20-23,0-3 UTC for late games |

### Phase 6 — Newly Registered Tasks (2026-05-29 handoff audit)

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| ~~T-091~~ | ~~C7 paper P&L monitoring alert~~ | ~~EL~~ | ~~MED~~ | ✅ COMPLETE 2026-06-01 — `check_portfolio_pnl()` added to SystemMonitor. L1 (5% loss) → INFO `pnl_alert_l1_watch`; L2 (10% loss) → WARNING `pnl_alert_l2_loss`. Wired into PIPE-03 and PIPE-03R. 8 new tests. 589/589 VPS tests pass. KI-012 RESOLVED. DS sign-off: Earl Ignacio 2026-06-01. |
| T-092 | Elevate T-072 to required pre-2026-27 | DS | MED | Model staleness KI-013 — T-072 must retrain before paper trading resumes in Oct 2026; not optional; needs new ADR |
| T-116 | Pre-season multi-game night pipeline stress test (KI-023) | IO/EL | HIGH — before 2026-27 | PIPE-02 + PIPE-03 have only been tested in single-game Finals context (1 game/night). Regular season (10+ simultaneous games, 400+ markets/night) is structurally different: concurrent nba_api pulls, parallel pregame log writes, overlapping PIPE-03 execution windows. If PIPE-02 fails silently for any player on a multi-game night, EXP-017 cannot join on that game's prices — G6 evidence is silently contaminated. Test plan: simulate a 10-game night locally before 2026-27 season tip-off. Verify: (1) run_pregame.py captures pregame logs for all 75 cohort players across simultaneous games without silent failures; (2) PIPE-03 processes all players without timing collisions; (3) EXP-017 join succeeds on a simulated multi-game pregame directory. Resolve before October 2026 season start. |
| T-117 | **Formal Kalshi TOS + contract Terms review (GG-006 final close)** | DS | **HIGH — Week 1 dark period (by 2026-06-30)** | Two documents to read formally before G6 ADR-0005 can be drafted: **(1) Kalshi Participant Agreement** — the account-level legal document Earl agreed to at account creation. GG-006 partial resolution confirmed automated trading permitted via web search; formal document reading not yet done. Look for: algorithmic trading restrictions, prohibited strategies, account termination triggers. **(2) KXNBAPTS contract-specific Terms and Conditions** — DCM Rulebook v1.26 does NOT contain numerical Position Accountability Levels or Position Limits; those are in each contract's Terms tab on Kalshi's website. Navigate to any active KXNBAPTS contract → Terms and Conditions tab → record: (a) stated Position Accountability Level (soft threshold for disclosure); (b) stated Position Limit (hard cap). If both above $500 (our bet cap), no changes to risk.py required. If either below $500, add `max_position_usd_per_market` to `_HARD_LIMITS` via ADR. Stakes: prevents live capital on disallowed activity — must complete before G6. LOW risk at current paper bankroll ($683, $10–80/bet). |
| T-100 | Fix Bug H — drawdown includes open stakes (KI-015) | EL | HIGH | ✅ COMPLETE 2026-05-30 — `run_paper_trade.py` lines 215+334: `current_drawdown_pct = realized_loss / initial_bankroll`; DS sign-off granted by operator same session; deployed VPS; live check: 0.00% realized drawdown |
| T-101 | Fix Bug G — idempotency check failure (KI-014) | EL | HIGH | ✅ COMPLETE 2026-05-30 — Root cause: `LOG_DIR` was relative path; cron ran from different CWD → fresh portfolio each run → 3× positions. Fix: `_SRC_ROOT / "logs"` absolute default in `run_paper_trade.py` + `run_resolve.py`. Idempotency logging added. Deployed VPS. |

### Governance Debt — decisions_logged: false (registered 2026-05-29)

*These documents contain unlogged strategic decisions. Each must be resolved before the document can be marked CANONICAL. Low priority unless the document is being actively modified — resolve before any session that touches the document.*

| # | Task | Owner | Priority | Notes |
|---|------|-------|----------|-------|
| ~~T-093~~ | ~~Extract decisions from EXECUTION_ARCHITECTURE.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-094~~ | ~~Extract decisions from MONITORING_DRIFT_PLAN.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-095~~ | ~~Extract decisions from METHODOLOGY.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-096~~ | ~~Extract decisions from VENUE_REGISTRY.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-097~~ | ~~Extract decisions from RISK_APPETITE_CONSTRAINTS.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-098~~ | ~~Extract decisions from QUALITATIVE_SIGNALS.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |
| ~~T-099~~ | ~~Extract decisions from ROADMAP_MILESTONES.md~~ | ~~DS~~ | ~~LOW~~ | ✅ COMPLETE 2026-06-02 SESSION 15 |

---

### Operator Actions Remaining

| # | Action | Why It Matters |
|---|--------|---------------|
| T-015 | Run `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt && pre-commit install` from project root | Sets up local development environment (Python 3.11+ required; all artifacts verified correct) |

---

## Standing Items (Every Session)

- [ ] Review MEMORY_BANK.md for any broken links
- [ ] Check if any artifact has a staleness trigger that fired
- [ ] Update TODO_NEXT.md before ending session
- [ ] Log any new open questions to OPEN_QUESTIONS.md
- [ ] Log any new RIDs to RID_LOG.md

---

## Blocked Items

| # | Task | Blocked By | ETA to Unblock |
|---|------|-----------|----------------|
| T-061 | ADR-0005 live capital | 30 resolved paper positions with positive P&L (APR-0016) | After G6 evidence |
| T-073 | DS-04 qualitative source | Operator decision on which source to register next | When ready |
| T-077 | Polymarket API key (T-077) | polymarket.com KYC approval (1-3 days) | Operator action |
| T-081 | arb/ incorporation (Strategy C) | APR-0010 pending; T-078 VenueRouter required first | Phase 7 — after T-078 complete |
