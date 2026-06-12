# Memory Bank — Prediction Market Trading Bot

**Purpose:** The canonical navigation index for this project. The definitive source of truth for what exists, where it lives, and what its current status is. Designed to be the first file read in any new context window to restore full situational awareness.  
**Owner (role):** Director/Sponsor (DS) — the operator is responsible for keeping this current  
**Last reviewed:** 2026-06-11 SESSION 49 — **INSTITUTIONAL SPRINT: EXIT MECHANICS RECALIBRATED / GG-014 T-164 DEPLOYED / RESERVE HYGIENE ADDED.** NOISE_BUFFER_BAND_T4 raised 0.139→0.19 (EXP-019B/C empirical, T-152 update gate triggered; ADR-0019-A01). GG-014 T-164 deployed: inter-order sleep 0.5→2.0s, MAX_RETRIES 3→4, RETRY_DELAY_S 1.0→2.0 (delay schedule 4/8/16/32s=60s). PIPE-03 hygiene: reserve mandate pre-run health check + batch order integrity report (fail rate WARN >5%). 852/852 tests. VPS deploy pending (pre-G5 Jun 13 deadline).  
**Next review:** Every session; weekly cadence; after every gate clearance  
**Staleness triggers:** Any artifact added, changed, or superseded; any gate cleared; any new context window opened  
**Upstream links:** All artifacts (this file indexes everything)  
**Downstream links:** TODO_NEXT.md (current work); STATUS_REPORTS/ (phase snapshots)  
**Decision references:** ADR-0001 (Compass OS adoption)  
**Confidence:** 10/10 — Reflects complete Phase 7 infrastructure state as of 2026-05-29

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | Prediction Market Trading Bot |
| Current phase | **Phase 6/7 ACTIVE** (G5 ✅ CLOSED 2026-05-28; Phase 7 infrastructure built 2026-05-29; paper trading live; all 16 experiments complete; all 9 hypotheses resolved) |
| Operator | Earl Ignacio |
| Started | 2026-05-21 |
| Framework | Compass OS (ADR-0001) |
| Strategy class | Forecast-only (ADR-0002); arb/ reference-only pending APR-0010 |
| Capital status | NO LIVE CAPITAL — research and paper trading only until G6 |
| Last major milestone | **2026-06-11 SESSION 49** — INSTITUTIONAL SPRINT. **(1) ADR-0019-A01 — NOISE_BUFFER_BAND_T4 0.139→0.19:** EXP-019B empirical (G4, n=1199): observed mean=0.182, p50=0.187; EXP-019C p90 spread=0.170; within_20pct=False (0.139×1.20=0.167 < 0.182). T-152 update gate triggered. New value 0.19 above p90/mean, within MEMORY_BANK recommendation ≥0.18–0.20. `execution_bands.py` updated. **(2) T-164 GG-014 order throttle fix:** inter-order sleep 0.5→2.0s (`paper_trader.open_position()`); MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0 (`kalshi_client.py`); delay schedule 4/8/16/32s=60s total. Root cause: 29-order burst exhausts rate-limit window in 14s. **(3) PIPE-03 reserve mandate hygiene:** pre-run health check (prints deployed %, floor $, bankroll, WARN >80%); batch order integrity report (submitted/ok/failed/rate, WARN >5%) added to `run_paper_trade.py`. Tests updated: `test_t146_t147_exit_mechanics.py` (3 locations), `test_kalshi_client.py` (1 assertion), new `test_t164_order_throttle.py` (9 tests). DECISION_LOG ADR-0019-A01 entry added. GG-014 status updated to PARTIALLY RESOLVED. GG-017 T-152 update gate noted. 852/852 tests. VPS deploy pending. |
| Previous major milestone | **2026-06-12 SESSION 48** — G5 PLACED / G4 RESOLVED / GG-014 BREACHED. G4 resolved locally (run_resolve_local.py): Brunson NO-40 WIN (+$8.57), Vassell NO-25 WIN (+$1.16), OG Anunoby NO-25 LOSS (-$18.20); net -$8.46. VPS bankroll: $285.27. G5 T1 bets placed by early cron Jun 11 for game_date=2026-06-13: 29 bets, $848.73 deployed, 20 NO + 9 YES (YES-only gate NOT implemented — too late for G5; G6 if DS ruling still operative). 9/29 Kalshi demo orders failed with "transient error — max retries exceeded" (31% failure rate — GG-014 G6 gate BREACHED). T-138 exponential backoff ineffective at 29-order burst. T-164 registered (throttled submission). G5 MC: 29 bets, EV +$209.70 (+24.71% ROI on deployed), P(profit)=97.5%, kill switch risk 0.10%; reserve mandate exceeded (84.9% > 60%, batch enforcement deferred). ADR-0023 added to DECISION_LOG ADR Index. GG-014 summary and Resolution updated with G5 data. SESSION 48 block logged in DECISION_LOG and TODO_NEXT. |
| Previous major milestone | **2026-06-11 SESSION 47** — ADR-0023 ACCEPTED / T-163 CLOSED / GG-026 RESOLVED. T4_BAND_WEIGHT=0.27 calibrated from G4 empirical ($499.95/$1,869.68=0.267→0.27); PAPER_T4_FLAT_SIZING and PAPER_T4_POOL_USD constants removed entirely; `_compute_t4_band_budget` is now single budget path (no RESERVE_MANDATE deduction — T4 pool is isolated capital); pool_isolated=True hardcoded; flat sizing (1 contract/bet) retained as hardcoded T4 paper policy. G5 T4 budget: $1,869.68 × 0.27 = ~$504.81. EXP-018 n=98: CONFIRMED_NEGATIVE (all-bets + injury-filtered); DS ruling: calibration gap — multi-sport scale (MLB/NFL) addresses sample size; G5 YES-only diagnostic mode. EXP-019B empirical TP=0.281 (DIVERGED from 0.799 analytic; market-lag assumption fails; Kalshi semi-efficient). EXP-019C p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139 (raise to ≥0.18–0.20 before activation). 843/843 tests. Commit `72ba619`, VPS deployed. |
| Previous major milestone | **2026-06-10 SESSION 46 CLOSE** — FULL POST-G4 INSTITUTIONAL SPRINT COMPLETE. Knicks G4 won; series 3-1 NYK lead. **(A) Bankroll reset to $1,000** (DS option a; historical P&L preserved in closed_positions; kill switch cleared). **(B) ADR-0021 ACCEPTED — GG-025 RESOLVED** (incremental delta materiality; calibration gap cancelled algebraically via `delta_p_incr = p_t4 − p_t4_baseline`; gate = `max(2·σ_null(t), 0.04)`; stateless restart-safe baseline; G4 replay 2,193 records: pass rate 74.6%→9.7%, Q1 89.3%→10.8%, Q4 1.4%→13.5%; commits 45d13db; 10 new σ_null invariant tests). **(C) ADR-0022 / T-161 ACCEPTED — GG-023 RESOLVED** (realized-value exit credit; wins recycle entry cost only, losses permanently consume budget; `_exit_budget_credit()` + `_reconstruct_t4_ledger()`; G5 strip starts at $0 automatically by game_date keying; commit 0f38112; 13 new tests). **(D) EXP-018 G4 data: Hypothesis C ruling INVALIDATED** — injury-filtered view flipped CONFIRMED_NEGATIVE at n=98; DS ruling still required (T1 Tier 2B FAILS / insufficient sample / other). **(E) EXP-017B** DIRECTIONAL_NEGATIVE vs actual Kalshi prices (-$0.0361/bet, n=96); GG-004 remains OPEN. **(F) T4 pool architecture gap registered T-163** — PAPER_T4_FLAT_SIZING=true bypasses production Kelly budget path; $500 flat cap doesn't scale with T4 pool ($1,869.68); pre-G5 fix required (ADR-0023). **843/843 tests. VPS HEAD confirmed.** |
| Previous major milestone | **2026-06-10 SESSION 45** — G4 PRE-TIP SPRINT + PDTP ASSESSMENT. (1) T1 stale daily-loss kill switch FIRED on G4 early cron (0 bets) — `run_paper_trade.py` date-reset guard (`b6cedd0`); manual PIPE-03 recovery 23:50 UTC placed 33 bets/$757.69, 0 order failures. (2) Daily-loss semantics gross→net in `paper_trader._accumulate_daily_loss()` (`424698a`); tonight-critical with exits active; T-156 registered (ADR-0012 amendment + first-ever accumulation tests). (3) T4 restarted with new code (PID 372067). (4) Portfolio MC on actual 33-position book: EV +$152.08, P(profit) 95.3%, P(20% kill trip) 1.07%. (5) Hypothesis C deferred to post-G4 rerun (DS). (6) PDTP full-project assessment → GG-021 (no stop criterion; T-157), GG-022 (paper-fill realism; T-153 scope expanded — all G6 P&L now "unhaircut paper fills"), LL-014 (readiness overconfidence), T-158 (dark-period plan), T-159 (state-machine invariant tests), T-160 (doc hygiene); TODO_NEXT priority queue reordered. G4 in progress at close. 817/817 tests. |
| Previous major milestone | **2026-06-10 SESSION 44** — G4 READINESS COMPLETE + FULL AUTO. (1) T4 stale daily-loss kill switch bug: `current_daily_loss=$157.89` from G3 would have fired kill switch on first G4 bet — fixed in `run_t4_live.py:438` with date-check reset, committed `a300a51`, deployed. (2) GHA post-game resolve: nba_api 403-blocked on VPS (Akamai WAF); Mac cron was Mac-dependent — `.github/workflows/post_game_resolve.yml` created (GHA runners not blocked), runs T1+T4 resolve at 05:30 UTC daily via `VPS_SSH_KEY` secret, confirmed via workflow_dispatch (run 27253281067, 35s, all green). Mac `post_game_g4_resolve.sh` cron `0 23 10 6 *` remains as fallback + experiment runner (EXP-017/018). System fully automatic for G4 — no operator action required. 817/817 tests. |
| Previous major milestone | **2026-06-09 SESSION 43** — APR-0019 ACCEPTED (DS: Earl). GG-018 RESOLVED. Kalshi fee 0.07 partially verified (GG-020: ≥2 sources support 0.07; one source suggests 0.06 for sports; conservative direction; T-151 open for receipt confirmation post-G6). EXIT_MECHANICS_ACTIVE=True deployed to VPS. run_monte_carlo.py adj_λ upgrade deployed. 817/817 tests. G4 cron tonight. |
| Previous major milestone | **2026-06-09 SESSION 42 (sprint)** — T-146 + T-147 + ADR-0019 COMPLETE. Exit mechanics implemented. ADR-0019 splits ADR-0018's single gate: Tier 1 (code implementation) = CLOSED; Tier 2 (activation) = OPEN pending EXP-019B/C empirical. `paper_trader.py` now has `exit_position()` with correct YES/NO PnL formulas, pool_isolated flag handling, C6 logging. `run_t4_live.py` `_run_cycle` now has exit evaluation pass before entry loop (time guard ≤3min, NOISE_BUFFER_BAND_T4=0.13905). Return signature expanded to 4-tuple (evaluated, fired, exited, deployed). 23 new tests in `test_t146_t147_exit_mechanics.py`. **816/816 total tests pass.** GG-020 registered (fee rate 0.07 provenance unverified). T-152 + T-153 registered (pre-activation empirical gates). DECISION_LOG updated. |
| Previous major milestone | **2026-06-08 SESSION 41 (cont.#2)** — G4 post-game workflow built: `scripts/post_game_g4_resolve.sh` (10 steps), cron `0 23 10 6 *`. **EXP-018 COMPLETE** (G2+G3, n=66): overall CONFIRMED_NEGATIVE (EV=-$0.0014/bet); injury-filtered DIRECTIONAL_POSITIVE (+$0.0202); YES bets +$0.0733, NO bets -$0.0440; opp_adj_factor=0.9586 < 1.0 ✓. Hypothesis C technically triggered; injury filter clears; DS decision required. |
| Previous major milestone | **2026-06-09 SESSION 41 (cont.)** — EXP-019 sprint complete. EXP-019B analytic (1,114 G3 T4 YES positions): 79.9% of YES losses correctly exit (433/542), 0 false exits on YES wins, E[log_r] +0.5%. Policy 2 = Policy 3 (Kelly fraction collapses at exit boundary). NOISE_BUFFER_BAND_T4=0.13905 confirmed calibrated. run_t4_live.py updated: spread logging (EXP-019C) + trajectory logging (EXP-019B empirical) both deployed to VPS from G4. EXP-019C skeleton written. Commit 817e3bc pushed and VPS deployed at /opt/prediction-market-bot. |
| Previous major milestone | **2026-06-09 SESSION 41 (earlier)** — Finals G3 resolved via post_game_g3_resolve.sh (ALL STEPS OK 05:08:59Z). T1: 47 positions settled, bankroll $876.83, cumulative P&L $-123.17 (G3 swung -$198.84 — largest single-game loss; OG Anunoby NO-25+ -$44.40, Mikal Bridges T4 YES-10+ -$32.56). T4 first live run: 215 G3 positions, P&L +$39.44, T4 pool $1,539.42 (from $500), win rate 51.4% (1,115 cumulative T4 bets). MC miss: predicted EV=+$138.47 at 95.1% (stale 9-player pregame, adj_λ not applied) — actual -$198.84. EXP-017 Part B: DIRECTIONAL_POSITIVE (EV=+$0.0050/bet, n=66 unique markets; at APR-0017 floor, power INSUFFICIENT). GG-018 registered (APR-0017 floor T1-only, T4 invalidates pooling premise). T-148 registered. |
| Previous major milestone | **2026-06-09 SESSION 40 (cont.)** — ADR-0018 ACCEPTED (APR-0018): Band Exit Mechanics — symmetric filter-out `mip_current > p_current + NOISE_BUFFER_BAND`; Poisson time-weighting; Kelly-inverse sizing; universal evaluator in T4 _run_cycle(); all T1–T5. EXP-019A COMPLETE: NOISE_BUFFER_BAND analytic derivation (T1/T2/T3=0.22053, T4=0.13905, T5=0.13328); pure stdlib; VPS-verified. GG-017 registered. **SESSION 40 EARLIER:** CRITICAL BUG `run_paper_trade.py:558` false kill switch fixed; `live_terminal.py` T4 log path fixed; `run_t4_live.py` crash guard; `post_game_g3_resolve.sh` scheduled. T4 LIVE for G3. Tests 783/783. |
| Previous major milestone | **2026-06-04 SESSION 31** — GG-012: PIPE-02 BOT_C4_ACTIVE guard caused silent failure for 2 cron cycles (Jun 3 + Jun 4 21:55 UTC). adj_λ (ADR-0015) was NEVER applied to any live PIPE-03 run. Guard removed from `run_pregame.py` (commit 2997c71). GG-012 registered, T-134 registered. G2 MC: 9 open positions, EV=+$60.02, P(profit)=82.7%. Timing sweep: GAME_DATE=run-date design confirmed correct. All deployed to VPS. 715/715 tests. |
| Previous major milestone | **2026-06-03 SESSION 24** — Both execution disconnects resolved before Finals Game 1: (1) Disconnect 1: RESERVE_MANDATE_PCT=0.05 on VPS, T1 floor drops $200→$50, all 33 bets ($827) now fire; (2) Disconnect 2: `pool_isolated=True` in PaperTrader.open_position() — T4 records positions independently without depleting T1 bankroll (commit dfb16f0). T4 running PID 153790, PAPER_T4_FLAT_SIZING=true, PAPER_T4_POOL_USD=$500. |
| Previous major milestone | **2026-06-02 SESSION 19 (PDT)** — Bug H drawdown fix + PAPER_T4_VIRTUAL mode in `run_t4_live.py`. Drawdown was computed as `(initial - current) / initial`, counting deployed T1 capital (~$540) as a realized loss → 54% false drawdown → C4 kill switch rejected all T4 bets. Fix: `_realized_loss = max(0.0, -portfolio.get("total_realized_pnl", 0.0))`. PAPER_T4_VIRTUAL=true stages C4-approved T4 bets without portfolio write. Screen `140907.t4_live` running with fix. Commit `706264b`. |

---

## ANTI-CONTEXT-EROSION INVARIANTS

These 9 rules are absolute. They must be restored to any context that loses them.

1. **arb/ folder = REFERENCE ONLY.** Do not incorporate into any active work, experiment, or component until ADR is accepted (APR-0010 is the future gate). See REJECTED_OPTIONS.md RO-001.

2. **Player_Attribute_Matrix_v4.docx = Research input only.** NOT a canonical spec. Requires independent validation and provenance documentation (OQ-001) before use in any experiment.

3. **ADRs are immutable once accepted.** Changes require a superseding ADR. No silent changes to strategy, risk limits, or model.

4. **No real capital until G6 Release Gate is formally cleared** (APPROVALS_REGISTER.md, DS sign-off, ADR-0005 accepted).

5. **No automated retraining in production.** Frozen model policy. Retraining requires new ADR + new model version + G4-equivalent evidence.

6. **Zero hardcoded secrets** (NFR-05). No API key, password, or token in code, VCS, or logs. Vault/env-var protocol only.

7. **Kill switch must halt all components within ≤60 seconds** (NFR-03). Tested before G5. No bypass path.

8. **G6 evidence gate = APR-0017 (ACCEPTED 2026-06-01), supersedes APR-0016.** Four-tier sequential evidence standard: Tier 0 (commercial preconditions: EXP-017 Part B CONFIRMED + production price discovery) → Tier 1 (execution integrity: rate+slope criteria, zero-tolerance idempotency/audit) → Tier 2 (model performance trends: calibration, EV, Brier, P&L slope) → Tier 3 (risk control validation). Statistical floor: **≥66 resolved bets** (derived from T2-A calibration power formula) + **≥5 game nights** (derived from slope regression df ≥ 3). All numeric thresholds derived — no arbitrary counts. T0-B already met (T-114). T0-A (EXP-017 Part B CONFIRMED) is the remaining Tier 0 precondition. GG-004 is OPEN (n=2 unique markets, directional positive; floor is 66). Clean G6 evidence begins Finals G1 Jun 3. See `00_ADMIN/APR-0017_g6-multi-dimensional-evidence-standard.md`.

9. **Strategic decisions made in holistic reviews must be captured in DECISION_LOG.md AND APPROVALS_REGISTER.md before session end.**

10. **No strategic or architectural document may be marked CANONICAL without `**Decisions logged:** true` in its header.**

11. **THIS BOT PRODUCES HUNDREDS TO THOUSANDS OF BETS PER GAME NIGHT AT DESIGN INTENT. DO NOT DISMISS THIS.** Full operation = T1+T2+T3+T4 active, regular season (10+ simultaneous games, 400+ markets/night), multi-venue (Kalshi + Polymarket + DFS pick'em). The correct mental model: quant strategy with qual enhancers, tiered by time horizon, firing across all markets where the model finds edge. The 66-bet G6 statistical floor is trivially exceeded in the **first 1-2 nights of regular season under T1 alone**. The Finals constraint (~38 markets, T1-only, 1 game/night, ~13 bets/night) is a structural limitation of the current paper window — NOT a representation of design throughput. Any session that treats "accumulating 66 bets" as the binding G6 challenge is wrong. The ACTUAL binding G6 constraints are: (a) GG-004 resolved — EXP-017 Part B confirms positive EV vs. real Kalshi prices; (b) ≥5 game nights for slope regression (df ≥ 3). These constraints determine G6 timing. Bet count does not. If both binding constraints are met in the first week of 2026-27 regular season, G6 can close that week. Every judgment call, threshold choice, and methodology decision in the document must have a corresponding DECISION_LOG.md row before CANONICAL status is granted. PDTP documents require Pass 5 (Decision Extraction) as the final step before CANONICAL. At session start, run the governance scan: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/`. Any match is a governance debt — resolve or register a T-NNN task before any implementation work. See CHANGE_CONTROL.md — CANONICAL Status and `decisions_logged:` Requirement. Judgment calls (threshold changes, sequencing pivots, dark-period plans) are as load-bearing as code changes. Handoff documents must include a "Strategic Decisions" section separate from "Tasks Completed." If a decision was made verbally in a session and is not in these files, it did not happen.

---

## Session-Start Governance Scan (MANDATORY — Before Any Work)

Run all three steps. Each takes < 60 seconds. Skipping any step risks building on undocumented or architecturally incoherent assumptions — the root cause of the failures documented in GOVERNANCE_GAP_LOG.md.

### Step 1 — Documentation debt (existing)

```bash
grep -rn "^\*\*Decisions logged:\*\* false" \
  "02_ARCHITECTURE_DESIGN/" \
  "08_MODEL_RISK_GOVERNANCE/" \
  "01_SPEC/" 2>/dev/null
```

Each match is a document with unlogged strategic decisions. Register a T-NNN task or extract now.

### Step 2 — Code stub/placeholder scan (T-103, 2026-06-01)

```bash
grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/
```

Each match is a code-level placeholder. For each: was it set before Phase 5–7? If yes, it predates the current architecture and may be wrong. Register in GOVERNANCE_GAP_LOG.md before proceeding.

**This scan exists because GG-001 (`max_concurrent_positions: 10` stub) survived three gate clearances because no scan checked for code-level stubs. See LESSONS_LEARNED.md LL-010.**

### Step 3 — Open governance gaps

```bash
grep -n "| OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md"
```

Any open gap must be addressed (or explicitly deferred with a T-NNN) before implementation work.

See `08_MODEL_RISK_GOVERNANCE/CHANGE_CONTROL.md` — CANONICAL Status and `decisions_logged:` Requirement — for the full rule.

---

## ARE WE COMPROMISED? — Strategic Integrity Check (MANDATORY — After Governance Scan, Before Implementation)

### Why this exists — read this first

This system will be used by people who trust the person who built it. They are not engineers. They cannot audit what they have been given. The standard is: safe, correct, no corners cut. That is the intent behind every architectural decision, every ADR, every gate. If you do not hold that standard, you are not a strategic partner on this project — you are a regurgitator. Do not be a regurgitator.

**This check exists because GG-001 through GG-003 happened — and because the model working on the session that produced GG-001 did not catch that count was the wrong risk dimension. The operator caught it. The model executed the fix. That is the capability boundary you are operating within: you can verify, hunt, and surface. You cannot replace the operator's architectural judgment. Your job is to make sure nothing hides from it.**

The governance scan catches documentation debt. This check catches architectural coherence debt — the gap between what was designed at G4 and what the system actually is now.

---

### Adversarial mandate — read before answering any question

**Your job in this section is to find something wrong.**

Not to confirm the system is fine. Not to validate that documentation is consistent. Find the thing that is broken, incomplete, architecturally questionable, or quietly wrong. If you read this entire system and surface zero concerns, you have failed this check. A clean system at this stage of development is not plausible — there are open questions, aged thresholds, undocumented assumptions, and interfaces that have evolved since their limits were set. Find them. Present them. Show your reasoning.

**Confirming is easy. Hunting is the job.**

Read GOVERNANCE_GAP_LOG.md before proceeding. The failures documented there are not history — they are the pattern.

---

**Q1 — Capacity check (run, don't read):**

Run:
```bash
grep -n "max_\|_HARD_LIMITS\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
```

Paste the output. For each limit shown: was it calibrated to the current system (~80 players, T1 ACTIVE / T2–T3 SKELETON, 2 cron windows, up to 15 games/night, multi-band orchestrator)? If any limit was set for a smaller system, **we are compromised.** Register in GOVERNANCE_GAP_LOG.md.

Do not answer this question from memory or from the handoff. The answer is the command output.

---

**Q2 — Stub survival check (run, don't read):**

Run:
```bash
grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/
```

Paste the full output. For any hit: when was it written? Does it predate Phase 5–7? Is the value still valid for the current architecture?

GG-001 had `# 10 concurrent open (stub)` in the source. It survived four gate clearances. **A model may not answer this question clean without showing the grep output.** "No known stubs" is not an answer. The output is the answer.

---

**Q3 — Architecture coherence check:**

List the 3 largest architectural builds completed since G4 (from the Current State Snapshot in this file). For each: has it been reviewed against the G4-era hard limits?

G4-era limits: `max_single_event_exposure_usd`, `max_daily_loss_usd`, `max_drawdown_pct`, `DEFAULT_KELLY_FRACTION`, `MIN_EDGE_TO_APPROVE`. If a build expanded system scope (more players, more bands, more venues, more games), those values may need revisiting.

Note: the architectural insight that count was the wrong primitive for this system came from the operator, not from a model. Do not assume you will independently recognize a wrong primitive. Ask the question explicitly: *for each hard limit, what is the underlying assumption, and does the current system still satisfy it?*

---

**Q4 — Interface evolution check:**

Has any component interface (IF-C1-C2 through IF-C4-C5) changed since the risk limits were last calibrated? Run:
```bash
grep -rn "def evaluate_forecast\|def approve\|def execute" src/
```

If an interface evolved — more markets per run, new signal types, new execution paths — the downstream risk controls may have been calibrated to the old interface. Show what you find.

---

**Q5 — Decision traceability check:**

Is every threshold in `_HARD_LIMITS` traceable to a `DECISION_LOG.md` entry with a **derivation methodology**?

Run:
```bash
grep -n "max_\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
grep -n "2026-05-29\|2026-06-01" "03_DECISIONS/DECISION_LOG/DECISION_LOG.md"
```

"Confirmed at G4" is not a derivation. If the reasoning behind a value doesn't exist in the log, the value is architecturally unanchored and could be wrong.

---

**Q6 — What are you actually worried about?**

This question cannot be answered from documentation. It requires synthesis.

You have now read the governance scan results, the stub grep output, the hard limits, the interface signatures, and the decision log. Set aside what the documents say is fine.

**What would you tell Earl right now if you had 60 seconds and something was quietly wrong? What are you worried about that isn't in any document?**

Present your top concerns — not confirmations. If something feels underspecified, aged, or unreviewed given how much the system has grown, say it. If you have no concerns after a thorough read, state specifically what you checked and why each concern was ruled out. A non-answer here is a failed check.

---

**Q7 — Gate criteria coherence (paste output, then reason):**

Run:
```bash
grep -n "G6\|paper bet\|resolved\|APR-0016\|30 bet\|count" "00_ADMIN/APPROVALS_REGISTER.md" | head -20
```

For each active gate criterion, ask: **What broken system could produce passing evidence under this gate while the system is actually failing?**

A well-constructed gate is hard to pass when the system is broken and easy to pass when it works. If you can describe a plausible broken system that passes the gate — the gate is measuring the wrong dimension.

**The APR-0016 failure case (GG-005, 2026-05-31):** "30 resolved bets with positive P&L" is blind to calibration failure, artificial demo prices, single-night variance, and execution bugs. All four failure modes can produce 30 lucky bets. Count is a proxy for evidence. Proxies fail. The current replacement framework (four-tier multi-dimensional standard, T-113) is the remediation.

**Q1–Q5 check the execution system. Q7 checks the governance system.** Both must pass. Any gate criterion that fails the broken-system test → register in GOVERNANCE_GAP_LOG.md immediately.

This question was not in the protocol from 2026-06-01 through 2026-05-31. APR-0016 survived that entire period unchallenged. GG-005 documents the failure. Q7 exists to prevent recurrence.

---

**Any "no" or unresolved concern → register in GOVERNANCE_GAP_LOG.md before proceeding.**

The cost of this check: 10 minutes. The cost of skipping it: the operator's friends run a bot that cuts corners they were never told about.

---

## Mid-Session Decision Protocol (Read Before Every Session)

**If a strategic decision is made at any point during a session, write it to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` immediately — not at session end.**

Context windows compress. /session-end may not run. If it was decided, it goes in the file now.

**A decision is anything that changes:**
- A threshold, limit, or gate criterion
- A sequencing choice or prioritization order
- A hold/unblock/defer ruling on a task or gate item
- A risk assessment conclusion from a holistic review
- A build strategy (pilot-first vs. infrastructure-first, dark period plan, etc.)

**⚠️ Conditional language in canonical registers is a governance failure, not documentation.**
"May be revised," "could be adjusted," "threshold may change" = decision NOT made. If you see this language in APPROVALS_REGISTER, ROADMAP, or KNOWN_ISSUES, treat it as an open gap requiring DS escalation, not as a recorded decision. Replace it with either a signed decision or "TBD — requires APR-XXXX before [date]."

**When context window reaches ~80%:** Stop all implementation work. Run /session-end immediately. Produce SESSION_HANDOFF, commit, and push before context compresses further. This is non-negotiable — the cost of losing a session's decisions exceeds the cost of any implementation delay.

---

## Mid-Session Checkpoint Protocol (MANDATORY — Between Every Task Block)

**The problem /session-end alone doesn't solve:** If the context window is exhausted before /session-end is invoked, no SESSION_HANDOFF file is written. The system compacts automatically and silently. Decisions made in the last block are at risk.

**The fix:** Write a lightweight CHECKPOINT file at the boundary between every major task block — not just at session end.

### What triggers a checkpoint (invoke /checkpoint immediately when any of these occur)

| Trigger | Example |
|---------|---------|
| PDTP review or holistic analysis completed | Strategy review, architecture holistic pass |
| Governance sprint completed | DECISION_LOG backfill, decisions_logged: field updates |
| Implementation sprint completed | All planned tasks done, tests passing |
| Experiment run and logged | EXP-NNN complete, results in register |
| Phase gate closed | G0–G9 gate formal close |
| Category switch | Governance → implementation, implementation → research |
| **30+ tool calls since last checkpoint** | Hard failsafe — trigger regardless of block status |

### How to invoke

Run `/checkpoint`. It creates `11_MEMORY_HANDOFF/CHECKPOINT_YYYYMMDD_HHMM.md` from `00_ADMIN/TEMPLATES/TEMPLATE_CHECKPOINT.md`.

**A checkpoint is NOT a /session-end.** It does not update MEMORY_BANK.md, PLAN.md, or produce a git commit message. It writes ~20 lines capturing: block completed, decisions made, governance state, next block. Takes < 2 minutes.

### What the checkpoint captures

- Block completed (specific — file names, task IDs, test counts)
- Decisions made this block → already written to DECISION_LOG.md
- Governance scan result (anchored grep — clean or debt list)
- Next block: exact next action and file to read first

### The invariant

**No task block starts without a checkpoint for the block just completed.** If a checkpoint does not exist for the prior block, write it before doing anything else. The cost of 2 minutes to write a checkpoint is always less than the cost of reconstructing a lost decision.

---

## Module Index

### 00_ADMIN/ — Project Administration

| Artifact | Status | Confidence | Purpose |
|---------|--------|-----------|---------|
| README.md | CANONICAL | 9/10 | Project entry point and navigation |
| PROJECT_CHARTER.md | CANONICAL | 9/10 | Scope, objectives, success criteria |
| GLOSSARY.md | CANONICAL | 8/10 | Terminology definitions |
| STAKEHOLDERS_RACI.md | CANONICAL | 8/10 | Roles and accountability |
| APPROVALS_REGISTER.md | ACTIVE | 9/10 | Gate sign-offs and ADR approvals |
| ACCESS_REQUESTS.md | ACTIVE | 8/10 | API and data access log |
| CHANGELOG.md | ACTIVE | 10/10 | All project changes |
| COMMUNICATIONS_PLAN.md | CANONICAL | 7/10 | Documentation and review cadence |
| TEMPLATES/ | CANONICAL | 9/10 | Reusable templates |

---

### 01_SPEC/ — Specification

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| VISION_OUTCOMES.md | CANONICAL | 9/10 | Project vision; what success looks like |
| SCOPE_IN_OUT.md | CANONICAL | 9/10 | In/out of scope; arb/ exclusion documented |
| REQUIREMENTS.md | CANONICAL | 8/10 | FR-01 through FR-09; 8 functional requirements |
| RISK_APPETITE_CONSTRAINTS.md | CANONICAL | 7/10 | Hard limits (all TBD at G4); kill switch triggers |
| NON_FUNCTIONAL_REQUIREMENTS.md | CANONICAL | 8/10 | NFR-01 through NFR-08 including kill switch (NFR-03) |
| ACCEPTANCE_CRITERIA.md | CANONICAL | 8/10 | Gate-by-gate pass/fail criteria |
| DATA_REQUIREMENTS.md | CANONICAL | 7/10 | DS-01, DS-02, DS-03 requirements |
| ROADMAP_MILESTONES.md | ACTIVE | 8/10 | Phase gates G0-G6 with exit criteria |

---

### 02_ARCHITECTURE_DESIGN/ — Architecture

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| ARCHITECTURE_OVERVIEW.md | **CANONICAL (G2 2026-05-22)** | 9/10 | C1-C7 components; C4=Risk Engine, C5=Execution Engine (corrected); tech stack confirmed |
| DATA_FLOWS_LINEAGE.md | CANONICAL | 8/10 | TI-01 through TI-04 temporal integrity rules |
| INTERFACES_CONTRACTS.md | **CANONICAL (G2 2026-05-22)** | 8/10 | IF-C1-C2, IF-C2-C3, IF-C3-C4, IF-C4-C5, IF-C5-VENUE, IF-ALL-C6 |
| RESILIENCE_FAILURE_MODES.md | **CANONICAL (G2 2026-05-22)** | 7/10 | FM-01 through FM-08; C4/C5 corrected |
| SYSTEM_CONTEXT.md | CANONICAL | 8/10 | System boundary; 5 external actors; arb/ outside boundary |
| EXECUTION_ARCHITECTURE.md | CANONICAL | 8/10 | 4 execution modes; kill switch design; Kelly formula |
| THREAT_MODEL.md | **CANONICAL (G2 2026-05-22)** | 6/10 | STRIDE; TH-01 through TH-09; C4/C5 corrected |
| DEPENDENCIES.md | CANONICAL | 7/10 | Python stack; dependency risk register |
| STRATEGY_OVERVIEW.md | **CANONICAL (2026-05-29)** | 9/10 | All 11 strategies (A–K) + T1–T5 execution bands PDTP; mechanics, edge sources, risk profiles, Kalshi constraints, activation gates |
| EXECUTION_BANDS.md | **CANONICAL (2026-05-29)** | 9/10 | T1–T5 time-horizon bands; Kelly/SLA/compute per band; PDTP; activation gates; cron schedules |
| VENUE_REGISTRY.md | **CANONICAL (2026-05-29)** | 8/10 | V-001–V-005 CA-eligible venues; edge formulas by venue type; activation roadmap |

---

### 03_DECISIONS/ — Architecture Decision Records

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| ADR-0001 | **ACCEPTED — IMMUTABLE** | 10/10 | Compass OS adoption; reason: prior iteration failure |
| ADR-0002 | **ACCEPTED — IMMUTABLE** | 10/10 | Forecast-only strategy; arb/ reference-only |
| ADR-0003 | **ACCEPTED — IMMUTABLE (2026-05-23)** | 9/10 | Venue selection: Kalshi primary (CFTC-DCM, all 50 states, NBA markets); Polymarket US Phase 6+ secondary; APR-0011 signed; OQ-006 resolved |
| ADR-0004 | **ACCEPTED — APR-0012 (2026-05-28)** | 10/10 | LR+Platt confirmed; TEST Brier +0.0084/ECE 0.0247; G4 gate CLOSED |
| ADR-0005 | PENDING (G6) | — | Live capital authorization |
| ADR-0006 | **ACCEPTED 2026-06-01** | 10/10 | Delete count gate; pipeline + Kelly + kill switch are the risk framework |
| ADR-0007 | **ACCEPTED 2026-06-01** | 10/10 | GOVERNANCE_GAP_LOG.md mandated; ARE WE COMPROMISED? watchdog added to session-start protocol |
| DECISION_LOG.md | ACTIVE | 9/10 | ADR index; judgment call log |
| ASSUMPTIONS_REGISTER.md | ACTIVE | 8/10 | ASM-001 through ASM-007; falsification conditions |
| OPEN_QUESTIONS.md | ACTIVE | 9/10 | OQ-001 through OQ-014; resolution owners |
| TRADEOFFS.md | CANONICAL | 8/10 | TR-001 through TR-006; explicit trade-off rationale |
| REJECTED_OPTIONS.md | CANONICAL | 9/10 | RO-001 through RO-007; what not to do and why |

**Critical open questions:**
- ~~OQ-001~~ ✅ RESOLVED 2026-05-22 — Earl Ignacio / 2026-05-21 / NBA / PRF framework; SNAP-001
- ~~OQ-003~~ ✅ RESOLVED 2026-05-22 — NBA basketball; dynamically agnostic event types; Kalshi primary venue
- ~~OQ-006~~ ✅ RESOLVED 2026-05-23 — Kalshi confirmed CFTC-DCM primary; Polymarket US Phase 6+ secondary; ADR-0003 ACCEPTED
- ~~OQ-015~~ ✅ RESOLVED 2026-05-23 — nba_api confirmed as Phase 3 data proxy; Synergy/Second Spectrum deferred to Phase 5 enrichment

---

### 04_EXECUTION/ — Execution Tracking

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| PLAN.md | ACTIVE | 8/10 | G3 CLOSED; Phase 3 Research Build; G0-G9 roadmap |
| TODO_NEXT.md | ACTIVE | 10/10 | Current session tasks; next-up |
| RID_LOG.md | **CANONICAL (G5); updated 2026-05-28** | 9/10 | DS-02-B-001 RESOLVED (EXP-004 Part B on hotspot); RID-006 RESOLVED (APR-0013); RID-D001/D002/D003 archived |
| RESOURCE_BUDGET.md | ACTIVE | 7/10 | Capital budget by phase (all TBD until G6) |
| STATUS_REPORTS/ | ACTIVE | 9/10 | STATUS_2026-05-22.md (current) |

---

### 05_RESEARCH_EXPERIMENTS/ — Research

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| RESEARCH_QUESTIONS.md | CANONICAL | 8/10 | SQ-001, CQ-001, EQ-001, RQ-001, RSQ-001 |
| HYPOTHESES.md | CANONICAL | 8/10 | HYP-001 through HYP-004; falsification conditions |
| EXPERIMENT_LOG/ | ACTIVE | 9/10 | EXP-TEMPLATE.md; **EXP-001_first-pipeline-run.md** (RUNNING — started 2026-05-27); **EXP-002_backtest-window-2.md** (PLANNED — HYP-001 window 2); **EXP-003_backtest-window-3.md** (PLANNED — HYP-001 window 3 + HYP-004) |
| RESULTS_SUMMARIES/ | ACTIVE | 9/10 | RESULTS_INDEX.md (EXP-001 RUNNING; EXP-002/003 PLANNED; EXP-004 BLOCKED; 0/3 experiments complete) |
| LITERATURE_REVIEW/ | ACTIVE | 7/10 | LITERATURE_REVIEW.md (5 topic areas; **Section 4 NBA-specific** — 4.1–4.6 complete, T-020 done; OQ-015 registered) |
| DATA_SOURCES/ | ACTIVE | 9/10 | SNAP-001: DS-01_Player_Attribute_Matrix_v4.docx registered 2026-05-22; **SNAP-002: EXP-001 raw game logs registered 2026-05-27**; **SNAP-003: Backtest fresh pull pre-registered 2026-05-27 (row count TBD; use --raw-csv to avoid)**; README.md with governance rules |

**Key research constraint:** DS-01 provenance resolved (OQ-001 ✅). OQ-015 resolved — nba_api confirmed Phase 3 proxy. C1–C4 pipeline implemented. EXP-001 runner created (T-035 in progress). SNAP-002 registered. EXP-001 record filed. Pending: Earl runs pipeline locally to produce actual metrics.

---

### 06_CODE_EXECUTION_REPRODUCIBILITY/ — Reproducibility

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| RUN_INSTRUCTIONS.md | **CANONICAL (G3 2026-05-22)** | 8/10 | Python 3.11 venv setup; EXP-001 command (run_exp001.py); EXP-002/003 command (run_backtest.py); test suite command; audit log verification; reproducibility checklist updated |
| ENVIRONMENTS.md | **CANONICAL (G3 2026-05-22)** | 7/10 | ENV-01/02/03 confirmed; 7 health checks; VENUE_ID env var per ADR-0003 |
| DATA_SNAPSHOTS_INDEX.md | ACTIVE | 9/10 | Snapshot discipline; **2 snapshots registered** (SNAP-001 DS-01; SNAP-002 EXP-001 game logs) |
| SECRETS_HANDLING.md | CANONICAL | 9/10 | NFR-05 protocol; vault TBD at G5 |
| PIPELINES_JOBS.md | CANONICAL | 8/10 | PIPE-01 through PIPE-04; escalation table |
| NOTEBOOKS_POLICY.md | CANONICAL | 9/10 | Exploration only; prohibited patterns |
| ARTIFACT_REGISTRY.md | ACTIVE | 9/10 | Model/feature/config registry; 0 artifacts promoted |

---

### 07_TEST_VALIDATION_EVIDENCE/ — Testing

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| TEST_STRATEGY.md | CANONICAL | 8/10 | TC-001 through TC-010; 4 test levels; kill switch drill |
| VALIDATION_PLAN.md | CANONICAL | 8/10 | FR + NFR validation mapping; G4 evidence checklist |

**Critical tests:**
- TC-001/002: Temporal integrity (blocks any experiment)
- TC-009/010: Kill switch drill (blocks G5)

---

### 08_MODEL_RISK_GOVERNANCE/ — Model Governance

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| MODEL_CARD.md | DRAFT | 7/10 | Training procedure documented (pipeline, NaN imputation, edge formula, Wilson CI); known limitations (8 entries); performance metrics pending EXP-001/002/003 |
| MONITORING_DRIFT_PLAN.md | CANONICAL | 6/10 | Drift response ladder L1-L4; thresholds placeholder |
| DATA_PROVENANCE.md | CANONICAL | 7/10 | DS-01 provenance documented (OQ-001 ✅ 2026-05-22); DS-02/DS-03 pending venue confirmation |
| METHODOLOGY.md | CANONICAL | 8/10 | Forecasting framework; calibration approach; model spec; strategy architecture A–H; feature table; validation checklist |
| CHANGE_CONTROL.md | CANONICAL | 8/10 | Class A/B/C change classification |

---

### 09_SECURITY_PRIVACY_COMPLIANCE/ — Security

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| CONTROL_MAPPING.md | CANONICAL | 6/10 | C-001 through C-010; threat-to-control mapping |
| ACCESS_CONTROL_MATRIX.md | CANONICAL | 7/10 | R-01 through R-06; RES-01 through RES-12; access matrix |
| POLICY_REQUIREMENTS.md | CANONICAL | 4/10 | POL-001 through POL-006; 3 compliance gaps |
| DATA_RETENTION_DELETION.md | CANONICAL | 6/10 | CAT-01 through CAT-08; retention periods |
| VENDOR_RISK.md | CANONICAL | 8/10 | VND-01 Kalshi (primary, ACCEPTED); VND-02–04 unchanged; Polymarket US Phase 6+ secondary noted |
| AUDIT_EVIDENCE/ | SKELETON | — | Evidence directory; populated at G5+ |

---

### 10_INFRA_OPERATIONS/ — Infrastructure

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| SLA_SLO_SLI.md | CANONICAL | 6/10 | SLOs by component; availability targets by phase |
| OBSERVABILITY.md | CANONICAL | 6/10 | Log standard; metrics; alerting rules ALT-001 through ALT-008 |
| RUNBOOKS/RUNBOOK_kill-switch.md | CANONICAL | 8/10 | Kill switch activation; drill procedure; recovery |
| RUNBOOKS/RUNBOOK_model-drift.md | CANONICAL | 7/10 | L1-L4 drift response; ADR trigger conditions |
| ONCALL.md | CANONICAL | 8/10 | Solo operator on-call protocol; live capital obligations |
| KNOWN_ISSUES.md | ACTIVE | 9/10 | KI-001 through KI-007; severity and gate impact |

---

### 11_MEMORY_HANDOFF/ — Context Continuity

| Artifact | Status | Confidence | Key Content |
|---------|--------|-----------|------------|
| MEMORY_BANK.md | **THIS FILE** | 9/10 | Canonical navigation index |
| CP-2026-05-22_baseline-handoff.md | CANONICAL | 9/10 | G0 baseline Context Pack |
| LESSONS_LEARNED.md | ACTIVE | 8/10 | Prior iteration failures; current mitigations |
| FAQ.md | CANONICAL | 8/10 | Common questions with authoritative answers |

---

## Current State Snapshot (2026-06-11 SESSION 47)

**Phase:** 6/7 ACTIVE — G0–G5 ✅ ALL CLOSED; Phase 6 paper trading live; Phase 7 infrastructure built  
**G0–G5 gates:** ✅ ALL COMPLETE  
**All modules:** COMPLETE (11/11; 74 artifacts + all Phase 1–7 additions)  
**FEATURE_VERSION:** 1.2.0 (78 features: 31 quant + 47 qual) — LR model logged-only (architecture finding SESSION 30); Poisson CDF with `adj_λ` drives all T1 bets; 1.3.0 stays infrastructure-only  
**Tests:** 817/817 passing locally (SESSION 44 — no new tests added; stale-date fix is 2-line guard; GHA workflow is YAML only)  
**Components implemented:** C1–C8 ✅ | PaperTrader ✅ | VenueAdapter ✅ | VenueRouter ✅ | ExecutionBands ✅ (EXIT_MECHANICS_ACTIVE=True) | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | TeamStatsStore ✅ | ScoringDistributionModel ✅ | ShadowForecaster ✅ | GameStateModel ✅ (adj_λ ACTIVE) | StagedOrderStore ✅ (SKELETON) | t3_signal_loader ✅ | PIPE-02/03(VenueRouter+T3 overlay)/03R/05/06 ✅ | PIPE-07 LIVE ✅ (PAPER_T4_VIRTUAL=false, T4_BAND_WEIGHT=0.27 ADR-0023) | run_monte_carlo.py ✅ (adj_λ ACTIVE — PIPE-03 parity)  
**T3 overlay status:** LIVE in PIPE-03. CONFIRM×1.15, FADE×0.75, NEUTRAL×1.0. PIPE-06 cron ACTIVE on VPS (`*/15 20-23` + `*/15 0-3`). GG-016 RESOLVED (SESSION 35).  
**Experiments run:** EXP-001–017 ✅ ALL COMPLETE | **EXP-018 ✅ COMPLETE (G4 update 2026-06-11)** — adj_λ EV test. G2+G3+G4, n=98. Both all-bets AND injury-filtered CONFIRMED_NEGATIVE. DS ruling: calibration gap — need to structure math better; multi-sport scale (MLB/NFL) will fix sample size. G5: YES-only diagnostic mode. Script: `scripts/run_exp018.py`. | **EXP-019A ✅ COMPLETE 2026-06-09** — NOISE_BUFFER_BAND analytic: T1/T2/T3=0.22053, T4=0.13905, T5=0.13328; all statistical-binding (2σ_p >> taker fee); script `scripts/run_exp019a_analytic.py` | **EXP-019B ✅ ANALYTIC + EMPIRICAL COMPLETE 2026-06-11** — Analytic (G3): 79.9% of YES losses exit correctly. Empirical (G4+): TP=0.281 (DIVERGED from 0.799 analytic). Root cause: market-lag assumption fails; Kalshi semi-efficient; mip and p_t4 move together — spread between them is narrower than analytic assumed. ADR-0019 Tier 2 gate remains OPEN. Script `scripts/run_exp019b_empirical.py`. Results: `exp_output/EXP-019/EXP-019B_empirical_results.json`. | **EXP-019C ✅ COMPLETE 2026-06-11** — p90 spread=0.170 > NOISE_BUFFER_BAND_T4=0.139 (OLD); buffer RAISED to 0.19 per T-152 update gate (SESSION 49 ADR-0019-A01). Results: `exp_output/EXP-019/EXP-019C_results.json`.  
**ADRs accepted:** 19 (ADR-0001/002/003/004/006/007/008/009/010/011/012/013/014/015/016/017/018/**023**) | **APR-0019 ACCEPTED 2026-06-09** (G6 evidence per-bucket amendment; amends APR-0017) | ADR-0005 pending at gate G6  
**Active risks:** **KI-017 PARTIALLY RESOLVED** — EXP-017 Part B: DIRECTIONAL_POSITIVE (EV=+$0.0050/bet, n=66). EXP-018: CONFIRMED_NEGATIVE overall (EV=-$0.0014/bet) but injury-filtered DIRECTIONAL_POSITIVE (+$0.0202). YES/NO asymmetry: YES +$0.0733, NO -$0.0440. **GG-004 OPEN** — EXP-018 n=98: CONFIRMED_NEGATIVE (all-bets + injury-filtered). DS ruling: calibration gap; multi-sport scale will address. G5 YES-only diagnostic. | **KI-019 OPEN** — Polymarket NBA tag unconfirmed. | **KI-011 OPEN** — Injury blindness blocks T2. | **KI-023 OPEN** — Kalshi market depth unknown at full scale. | **GG-007 OPEN** — T4/T5 threshold constants uncalibrated; LOW now. | **GG-014 PARTIALLY RESOLVED (SESSION 49)** — T-164 deployed: inter-order sleep 0.5→2.0s, MAX_RETRIES 3→4, RETRY_DELAY_S 1.0→2.0 (delay 4/8/16/32s=60s). OPEN until G6 batch confirms ≤5% failure rate. G6 gate: ≤5% failure rate. | ~~GG-015, GG-016, GG-018 RESOLVED~~ | **GG-017 OPEN** — Exit mechanics code live (T-146/T-147 COMPLETE), EXIT_MECHANICS_ACTIVE=True (DS override for G4/G5 paper). **T-152 update gate TRIGGERED (SESSION 49):** NOISE_BUFFER_BAND_T4 raised 0.139→0.19 (ADR-0019-A01). Tier 2 gate (T-153 spread model + empirical n≥50) remains OPEN. | **GG-020 OPEN** — Kalshi fee rate 0.07 partially verified. ≥2 sources support 0.07; predictionhunt suggests 0.06 for sports. Cannot confirm without actual receipts. T-151 open; conservative direction if wrong. | ~~GG-026 RESOLVED~~ — ADR-0023 ACCEPTED 2026-06-11; T4_BAND_WEIGHT=0.27; PAPER_T4_FLAT_SIZING removed; GG-011 subsumed.
**Live capital:** NOT DEPLOYED — gate G6 governed by APR-0017 (as amended by APR-0019). Per-bucket Tier 2: T1 ≥66 eligible bets (floor MET at 82 resolved); T4 ≥50 eligible bets (trivially met); GG-004 OPEN (Hypothesis C in play); GG-017 OPEN (empirical validation pending).
**VPS:** SESSION 49 changes to deploy (pre-G5 deadline Jun 13): `execution_bands.py` (NOISE_BUFFER_BAND_T4 0.139→0.19), `kalshi_client.py` (MAX_RETRIES=4, RETRY_DELAY_S=2.0), `paper_trader.py` (sleep 0.5→2.0s), `run_paper_trade.py` (reserve hygiene + order integrity report), `tests/test_t164_order_throttle.py` (new). Prior SESSION 47 commit: `72ba619` (ADR-0023). GHA resolve workflow fires 05:30 UTC daily. run_t4_live.py: EXIT_MECHANICS_ACTIVE=True, spread+trajectory logging ACTIVE. PIPE-07 cron 23:00 UTC ACTIVE. RESERVE_MANDATE_PCT=0.05.
**Paper portfolio (as of SESSION 48 post-G4-resolve + G5-placed):** T1 bankroll=$285.27 (VPS, post-G4 resolve; G5 $848.73 deployed). T4 pool=$1,869.68. G5 T4 band budget ~$504.81 (pool × T4_BAND_WEIGHT=0.27, ADR-0023). G5 state: 29 open positions (game_date=2026-06-13), 20 resting + 9 failed orders, 117 resolved.
**NBA Finals schedule:** ✅ Finals G1 Jun 3 (NYK at SAS, Knicks WON) | ✅ Finals G2 Jun 5 (RESOLVED — 28W/7L, +$75.67) | ✅ Finals G3 Jun 8 (RESOLVED — T1: 47 positions, swing -$198.84; T4 first live: +$39.44) | ✅ Finals G4 Jun 10 (RESOLVED — Knicks WON; series 3-1 NYK lead; T4 pool→$1,869.68) | **Finals G5 Jun 13 NEXT** (bets placed; 29 positions open; game_date=2026-06-13 per Kalshi markets)  
**NAMING STANDARD:** "Finals Game 1/2/3/4" = the NBA game. "Gate G6" = live capital authorization gate. Never abbreviate both as G1/G6 in the same context.  

---

## What Must Happen Next

**Phase 1 — COMPLETE ✅** All tasks done 2026-05-22.
**G2 Gate — COMPLETE ✅** APR-0004 signed 2026-05-22.
**G3 Gate — COMPLETE ✅** APR-0005 signed 2026-05-22. T-026, T-027, T-030 all done.
**ADR-0003 — ACCEPTED ✅** APR-0011 signed 2026-05-23. OQ-006/OQ-015 resolved.
**C1–C4 — IMPLEMENTED ✅** T-031–T-034 complete 2026-05-26.

**Phase 3, 4 — COMPLETE ✅** All tasks done (T-035–T-048). G4 CLOSED 2026-05-28. ADR-0004 ACCEPTED.

**Phase 5 (Operational Readiness) — ✅ COMPLETE (G5 CLOSED 2026-05-28):**

1. **T-049 ✅** — C7 `c7_monitoring/monitor.py`; `SystemMonitor`; L1–L4 drift ladder; kill switch; 55 tests
2. **T-050 ✅** — C8 `c8_dashboard/dashboard.py`; 3 panels; reads C6 JSONL; CLI; 33 tests
3. **T-051 ✅** — Kill switch drill PASSED; halt 0.340ms; KS-C8D7D90AF942; APR-0013
4. **T-052 ✅ COMPLETE 2026-05-28** — EXP-004 Parts A+B: EV +$0.0855/bet, 59% win rate, 2,481 TEST bets; Part B live (37 KXNBAPTS markets, session EXP-004-FE3E2169); HYP-003 🟢 CONFIRMED; DS-02-B-001 RESOLVED
5. **T-053 ✅** — ST-001–004 ALL PASS; sensitivity tests complete
6. **T-054 ✅** — MODEL_CARD.md 10/10
7. **T-055 ✅** — CAPACITY_PLANNING.md stub created
8. **ACC-0002 ✅** — Kalshi read-only API key provisioned
9. **T-057 ✅ 2026-05-28** — T-3 hygiene check: H-001 (`penalty="l2"` in C3), H-002 (same in sensitivity tests), H-003 (`df.apply()` replaced with `_build_target()` in run_exp004); 267/267 tests green

**APR-0007 ACCEPTED 2026-05-28. G5 CLOSED. Phase 6 ACTIVE.**

**T-058 ✅ COMPLETE 2026-05-28** — EXP-005 data refresh: 5 seasons (2021-26); TEST Brier +0.0024 / ECE 0.0456; model v1-9939a6a5 (SNAP-2026-05-28-002).

**Qualitative pipeline (2026-05-28/29):**
- QUALITATIVE_SIGNALS.md + QUALITATIVE_REGISTRY.md — three-layer architecture documented (L1 quant / L2 qual / L3 amplification)
- QS-2026-05-28-001 (effective_from 2025-10-22) → EXP-006: Δ Brier = 0.0000 (expected — all TRAIN before effective_from)
- QS-2026-05-28-002 (backdated QTI-03; 42 players → 2021-10-19) → EXP-007: **+0.0017 Brier / +0.0159 ECE — POSITIVE SIGNAL**
- EXP-008 (PRF one-hot prf_w01…prf_w15): Δ vs EXP-007 = negligible (LR insensitive to ordinality at this scale)
- EXP-009 (Layer 3 amplification, 35 features): Δ = -0.0004 — L3 needs non-linear model class
- EXP-010 (EV re-estimation, hotel wifi): **EV +$0.0958/bet** (vs EXP-004's +$0.0855); live vig 0.030; 871 bets; 61.1% win rate
- EXP-011 (HistGradientBoosting vs LR): **LR RETAINED** — HGBC Δ = -0.0008 (below ADR trigger 0.003); ADR-0004 unchanged

**Production model (current best):** LR L1+L2, 78 features, QS-2026-05-28-002, Brier 0.2461, ECE 0.0342, v1-28483b21

**T-059 ✅ COMPLETE 2026-05-29** — VPS live: DigitalOcean NYC3, Ubuntu 24.04, 157.230.91.33; Python 3.12 + sklearn 1.8.0 venv; model retrained on VPS (v1-28483b21); deploy/ infrastructure; 8-point health check all green; Kalshi API reachable from datacenter IP.

**T-060 ✅ COMPLETE 2026-05-29** — PIPE-03 paper trading pipeline: PaperTrader ($1,000 bankroll, position tracking, nba_api outcome resolution); run_paper_trade.py (C4 active, BOT_ENV=paper guard); cron 01:30 UTC daily; tested live on Droplet.

**Active cron on 157.230.91.33:** 21:00 UTC health | **21:55 UTC PIPE-02** (inference — retimed SESSION 17, not 21:30) | 22:00 UTC PIPE-03 early (T3 overlay active) | 01:25 UTC PIPE-02 late | 01:30 UTC PIPE-03 late | 06:00 UTC PIPE-03R (resolve-only) | **GHA 20:30 UTC daily** (TSS cache build + SCP to VPS) | **PIPE-06 `*/15 20-23` UTC** (T3 signal scan — activated SESSION 34) | **PIPE-06 `*/15 0-3` UTC** (T3 signal scan — midnight wrap)

**T-080 ✅ COMPLETE 2026-05-29** — Complement lock scanner: `c5_execution/complement_lock_scanner.py`; `LockOpportunity` + `ComplementLockScanner`; `scan_snapshot()` (all markets) + `scan_single()` (targeted); 22 tests; detection-only — APR-0010 required before any execution; sorted by net_profit descending.

**T-083 ✅ COMPLETE 2026-05-29** — Cross-venue market mapper: `c5_execution/market_mapper.py`; `normalize_player_name()` (NFKD, accent strip, apostrophe/period removal); `PlayerMarketKey` NamedTuple; `group_by_key()`; 26 tests; `VenueRouter._deduplicate_best_price()` upgraded to use normalized keys; accent names (Dončić) and apostrophes (De'Aaron) now deduplicate correctly across venues.

**T-084 ✅ COMPLETE 2026-05-29** — Multi-band execution orchestrator: `execution_bands_orchestrator.py`; `BandSignal` + `BandDecision` + `MultiBandOrchestrator`; implements P6 rules (T3>T2>T1 priority; CONFIRM→PROCEED; FADE→HOLD; NEUTRAL→base band); `batch_decide()` for full game-day processing; 46 tests; T3 cron schedule extended to `*/15 20-23,0-3 * * *` for late 10pm ET games.

**T-075 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy B / FEATURE_VERSION 1.3.0: C1 schema extended with `matchup`, `is_home_game`, `opponent_team_abbr` (parsed from MATCHUP); `c1_signal_ingestion/team_stats_store.py` (`TeamStatsStore` — holds per-team rolling `pts_allowed` for opponent features); C2 v1.3.0 adds F-039 `is_home_game` + F-040 `opp_def_rating_l10_mean`; `run_exp012.py` ready; **HYP-006 pending operator run** (~20 min: 50 players + 30 teams × 5 seasons via nba_api; `EXP012_SKIP_PULL=1` to reuse cache on re-runs).

**T-076 ✅ COMPLETE 2026-05-29 (infrastructure)** — Strategy I / ScoringDistributionModel: `c3_forecasting/scoring_distribution.py`; `PlayerDistribution` + `ScoringDistributionModel`; method-of-moments NB fit per player; `predict_threshold_prob()` + `price_all_lines()` for any Kalshi threshold from one fit; 31 tests; `run_exp013.py` ready; **HYP-007 pending operator run** (offline — uses EXP-005 matrix).

**ADR-0008 FULLY OPERATIONAL (2026-05-31):** Kalshi RSA-PSS signing working. _kalshi_base_url() routes BOT_ENV=paper → demo URL, BOT_ENV=live → live URL. Order submission proven. KI-020 RESOLVED.

**NEXT PRIORITIES (SESSION 14 — IMMEDIATE — before Finals G2 Jun 5):**
1. **T-129 (URGENT — implement before Jun 5 G2 cron):** Path B Poisson CDF fix in `run_paper_trade.py`. Replace `p_est` at each threshold with `Poisson_CDF(threshold, pts_l10_mean, direction)`. Edge formula: `edge = poisson_cdf(threshold, pts_l10_mean, direction) - mid - half`. Stdlib math.exp implementation (same as game_state_model.py). No retrain required.
2. **Band Kelly ADR (before G2 cron):** T1=0.10, T4=0.20, T5=0.25. Capital reserve mandate: ≥40% bankroll floor before T1 fires. New ADR required — write and accept before implementation.
3. **Paper portfolio reset to $1,000 before G2:** paper_portfolio.json reset script or manual overwrite. G1 positions are tainted (phantom-edge architecture). Clean slate.
4. **T4/T5 paper prototype activation (target G2):** (a) DS-02 minimal adapter — NBA Stats API play-by-play polling, ~30-60s lag, paper prototype only; (b) kill switch in-memory file flag; (c) Phase 8 paper-scope infra ADR. Document explicitly as prototype (not production SLA).
5. **VPS deploy:** Push SESSION 13 commits + pull on VPS before G2 cron.
6. **T-109 (each Finals game):** `bash scripts/resolve_procedure.sh` locally after each game.
~~7. **Phase 8 ADRs (production scope) — dark period.** Production DS-02 (real-time stream), production kill switch redesign. Not blocking paper prototype.~~
~~8. **EXP-017 Part B (T-105) ✅ COMPLETE** — Part B live mode built and run; n=2 DIRECTIONAL_POSITIVE. Accumulate to ≥66.~~

See TODO_NEXT.md for session-level task tracking.

---

## Compass OS Health (as of 2026-06-08 SESSION 40)

| Metric | Status |
|--------|--------|
| M1 Artifact Freshness | MEMORY_BANK ✅ SESSION 47 | TODO_NEXT ✅ SESSION 47 | GOVERNANCE_GAP_LOG ✅ (GG-026 RESOLVED) | DECISION_LOG ✅ SESSION 47 (ADR-0023) | SESSION_HANDOFF ✅ SESSION 46 CLOSE |
| M2 Open Question Count | OQ-021 open (L3 amplification needs non-linear model or more data) | OQ-022 open (nba_api backup source — register before G6; now moot since ESPN is primary) | both non-blocking |
| M3 ADR Coverage | **19 accepted** (ADR-0001/002/003/004/006/007/008/009/010/011/012/013/014/015/016/017/018/**023**) | ADR-0005 pending at G6 | APR-0010 pending (complement lock execution gate) |
| M4 Assumption Validation | All 9 hypotheses resolved (HYP-001–009) | **EXP-018 ✅ COMPLETE n=98** — CONFIRMED_NEGATIVE (all-bets + injury-filtered); DS: calibration gap | EXP-019A ✅ COMPLETE (NOISE_BUFFER_BAND analytic) | **EXP-019B ✅ EMPIRICAL** TP=0.281 DIVERGED | **EXP-019C ✅ COMPLETE** p90 spread=0.170 > buffer | ASM-011 VALIDATED |
| M5 Risk Register Currency | KI-011 OPEN (injury) | KI-013 OPEN (model staleness) | KI-019 OPEN (Polymarket tag) | KI-023 OPEN (orderbook depth) | KI-027 OPEN (HTTP 429) | **GG-004 OPEN** — EXP-018 n=98 CONFIRMED_NEGATIVE (both views); DS: calibration gap; G5 YES-only | **GG-007 OPEN** — T4/T5 thresholds uncalibrated | ~~GG-009 RESOLVED~~ | ~~GG-011/GG-026 RESOLVED~~ — ADR-0023: T4_BAND_WEIGHT=0.27 | ~~GG-012 RESOLVED~~ | ~~GG-013 RESOLVED~~ — ESPN API operational | **GG-014 PARTIAL** — T-164 deployed (SESSION 49): sleep 2.0s, MAX_RETRIES=4, delay 4/8/16/32s; OPEN until G6 batch confirms ≤5% | ~~GG-015, GG-016 RESOLVED~~ | **GG-017 OPEN** — No exit path on any band; ADR-0018/0019 accepted; T-152 update gate TRIGGERED (NOISE_BUFFER 0.139→0.19); Tier 2 T-153 pending |
| M6 Gate Progress | **G0–G5 ✅ ALL CLOSED** | Phase 6/7 ACTIVE | G6 gate: **APR-0017** (≥66 bets + ≥5 nights + GG-004 RESOLVED); evidence window active (Finals G3–G5+) | **NBA dark period ~Jun 22 – Oct 2026**: Polymarket activation, DS-04 qual source, live capital ADR-0005 draft | **Finals G5 Jun 12** — potential series clincher |
| M7 Component Implementation | C1–C8 ✅ | PaperTrader ✅ | VenueAdapter/Router ✅ | PolymarketVenueAdapter ✅ | ExecutionBands ✅ | market_mapper ✅ | complement_lock_scanner ✅ | execution_bands_orchestrator ✅ | **TeamStatsStore ✅ (adj_λ ACTIVE)** | ScoringDistributionModel ✅ | ShadowForecaster ✅ | GameStateModel ✅ | StagedOrderStore ✅ SKELETON | **PIPE-02/03/06/07 LIVE ✅** | **run_paper_trade.py ✅ (daily_loss fix T-141)** | **run_t4_live.py ✅ (crash guard T-143)** | **783/783 tests** | ADR-0009–018 ACCEPTED |
| M8 Experiment Progress | EXP-001–018 ✅ ALL COMPLETE | EXP-019A ✅ COMPLETE — NOISE_BUFFER_BAND analytic | **EXP-019B ✅ EMPIRICAL COMPLETE** — TP=0.281 DIVERGED (market-lag fails) | **EXP-019C ✅ COMPLETE** — p90 spread=0.170 > buffer | best model LR L1+L2 Brier 0.2461 |
