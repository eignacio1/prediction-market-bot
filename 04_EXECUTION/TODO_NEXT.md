# TODO Next — Prediction Market Trading Bot

**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-06-04 SESSION 29 — PDTP Finals G1 analysis written and committed (3abae30). VPS deploy complete (f32efa9 deployed, same-day fix live, T4 PID 205448 running). Finals Game 2 MC verify + portfolio reset decision remain open. EXP-017 DIRECTIONAL_NEGATIVE — path to G6 requires T-072 (opponent features + retrain) before further evidence accumulation.

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
| **Finals Game 2 MC verify** | **Run Monte Carlo before Finals Game 2 T1 cron (Jun 5)** | DS | **HIGH — before Jun 5 2:55 PM PDT** | `BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2`. Expect 30–45 bets. If low: check reserve floor, pagination, market availability. |
| **Portfolio reset decision** | **Evaluate reset to $1,500 ($1,000 T1 + $500 T4 pool) before Finals Game 2** | DS | MEDIUM | Current T1 bankroll ~$404.80. If EXP-017 root cause (opponent features) understood and strategy adjustment planned: reset gives cleaner signal for G2. If not: run G2 on reduced bankroll and treat as continued evidence accumulation. |
| **GG-004 next step** | **Add opponent defensive features to C2/C3 for EXP-017 re-run** | DS | HIGH — before G6 | T1 model overestimates win prob by 13.7pp vs. Kalshi. Root cause: no opponent quality in feature set. Path: (1) enable TeamStatsStore F-040 `opp_def_rating_l10_mean` in C2 v1.3.0; (2) retrain with new ADR; (3) re-run EXP-017 Part B on Finals G2+. Note: T-072 model refresh (dark period) is the natural vehicle for this — coordinate. |
| **T-131 — Fee-adjusted edge ADR** | **GG-009: taker fee absent from MIN_EDGE gate** | DS | HIGH — before G6 | See existing entry in SESSION 22/23 open items below. |
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
| **T-131 — Fee-adjusted edge ADR** | **Register and resolve GG-009: Kalshi taker fee not in MIN_EDGE gate** | DS | **HIGH — before G6** | GG-009 (2026-06-03 SESSION 23): taker fee = `0.07 × P × (1−P)`. At P=0.50: $0.0175/contract = 87% of MIN_EDGE=0.02. Three resolution options: (1) raise MIN_EDGE to 0.0375; (2) fee-adjusted edge gate `net_edge = gross_edge - 0.07×P×(1-P)`; (3) maker-first limit order policy (4× cheaper). Any option requires ADR. Write T-131 ADR before G6 EXP-017 re-run (EV figures are overstated without fee correction). |
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
