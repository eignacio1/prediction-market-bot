# Execution Plan — Prediction Market Trading Bot

**Purpose:** The authoritative, actionable delivery plan. Maps work to phases, owners, and milestones. Updated at each gate and weekly during active phases.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-07-03 SESSION 116 (session-end) — **T-225 RESOLVED: no deliverables-table impact (dedup policy redesign is not a milestone-tracked line item, same treatment as T-220/T-221/T-222/T-223).** T4 MLB one-shot-per-ticker dedup redesigned to allow per-ticker re-entry keyed on `(h_so_far, ab_remaining)` state change, per Earl's explicit design ruling. 11 new tests, full suite 2293 passed / 7 skipped / 1 pre-existing unrelated (up from 2282). Committed `2331264`, pushed, VPS deployed, `t4-mlb` restarted clean. GG-076 closed; T-229 now unblocked, T-228 remains open. See MEMORY_BANK.md and TODO_NEXT.md SESSION 116 entries for full detail.** *(Previous, SESSION 115 (session-end):)* **Diagnostic/governance-only session, no deliverables-table impact (same treatment as T-220/T-221/T-222/T-223).** GG-076's T-226 (Kalshi KXMLBHIT coverage — real ceiling ~60-70% of games/day, pagination confirmed correct, no bug) and T-227 (mid-window T4 restart — both clean deploy-triggered systemd restarts, GG-072 explicitly ruled out) both RESOLVED via the mandatory sequential process (investigate -> document -> commit -> deploy -> verify -> report back), committed `f0f9bdc` and `d215b4a`, both auto-deployed clean. T-225 (one-shot-per-ticker dedup policy redesign) confirmed the dominant remaining lever on GG-076's throughput gap, awaiting a DS/design decision before any code changes — not resolved this session. T-228 (vig/liquidity floor filter) and T-229 (Hard-Rule-9 arithmetic reconciliation, blocked on T-225) remain open. No code changes to `src/`, no test count change (2282/7/1 unchanged). See MEMORY_BANK.md and TODO_NEXT.md SESSION 115 entries for full detail.** *(Previous, SESSION 114 CONTINUATION, session-end:)* **Governance/reconciliation-only session, no deliverables-table impact (documentation closeout is not a milestone-tracked line item, same treatment as T-220/T-221/T-222/T-223).** Closed out the 4 session-opening worries with institutional-depth root-cause analysis: (1) T1 MLB PIPE-05's 2026-07-02 zero-bet day root-caused to the same GG-068 HALT-severity DataContractViolation bug that hit PIPE-06pre (fixed same-day) but PIPE-05 was never independently cross-checked/recovered — that betting day is permanently, irrecoverably lost (Kalshi markets long closed). **GG-072 registered OPEN, T-224 assigned** (process fix: any future incident response to a shared contract/validation-module HALT must enumerate and re-verify every pipeline gated by that contract, not just the one whose failure prompted the fix). (2) GG-063 (Kalshi v1→v2 order endpoint migration, T-217) reconciled against GG-064 and confirmed LIKELY RESOLVED. (3) The 07-01 "all 50 T1 bets were NO" pattern investigated and closed as a non-bug (structural artifact, not a calibration failure). (4) The `data_contracts_state.json` "13989x row count" cardinality-drift WARN traced to a one-time bootstrap artifact (fired once, VPS baseline self-corrected after the GG-068 fix) — not a recurring bug and not its own gap. That investigation surfaced the real issue: `data_contracts_state.json` was git-tracked, which combined with two stray dead files and an uncovered `exp_output/MLB/` cache directory to keep the VPS working tree permanently dirty, causing **GG-073: a 100% historical failure rate (~31 consecutive failures since deploy.yml's creation 2026-06-12) in the deploy workflow's dirty-tree guard. GG-073 fully RESOLVED this continuation** (`.gitignore` updated to cover `data/data_contracts_state.json` and `exp_output/MLB/`; stray dead files removed); **T-224b registered OPEN** as the sole GG-073 follow-up. Mid-session, self-discovered and corrected a GG-072/GG-073 mislabeling that had propagated into this session's own drafts of `TODO_NEXT.md`/`MEMORY_BANK.md` (GG-072 is Worry #1, not Worry #4) — corrected in place across 5 locations, logged in `DECISION_LOG.md`'s Notable Judgment Calls table per Hard Rule 7. Also reconciled a concurrent parallel session's already-complete T4 MLB throughput root-cause diagnosis (GG-076, T-225 through T-229) found landed in the shared working tree. No code changes to `src/` beyond `.gitignore`, no test count change (2282/7/1 unchanged). See MEMORY_BANK.md and TODO_NEXT.md SESSION 114 CONTINUATION entries for full detail.** *(Previous, SESSION 113 CONTINUATION, session-end:)* **Forward-MC/GG-071/T-223: no deliverables-table impact (governance registration + artifact work, not a milestone-tracked line item, same treatment as T-220/T-221/T-222).** Forward-time compounding Monte Carlo built for T1/T4M-PROJ/Combined bankroll projection (1mo/6mo/1yr), simulating forward paths from real observed win rate/payout multiple/bet cadence as calibration inputs (not resolving currently-open positions), enforcing `MAX_SINGLE_EVENT_EXPOSURE`/`MAX_DAILY_LOSS_PCT`/`max_drawdown_pct` path-by-path. Redeployed Artifact: https://claude.ai/code/artifact/9318e2d4-588a-4624-81c0-73b98a3a37c9. Finding: T1's real positive edge nonetheless yields 46.45% 1yr probability of permanent kill-switch breach under proportional compounding — operator confirmed correct, directed future-look flag rather than immediate fix. GG-071 registered OPEN; T-223 registered (C4 stake-sizing ruin-risk review). No code changes to `src/`, no test count change (2282/7/1 unchanged). See MEMORY_BANK.md and TODO_NEXT.md SESSION 113 CONTINUATION entries for full detail.** *(Previous, same-day SESSION 113, session-end:)* **T-222/GG-070: no deliverables-table impact (edge_logger wiring + hook fix are tooling/process fixes, not milestone-tracked line items, same treatment as T-220/T-221).** T-222 (T-213 Phase 2): `edge_logger` wired into `run_t4_mlb_live.py`, giving T4 MLB the same PIPELINE_BROKEN/NO_EDGE/RISK_REJECTED/ACTIVE edge-decision classification T1 already has (T-213 Phase 1). T-213 Phases 3-5 (T2 wiring, EXP-harness wiring, cross-band rollup) remain open/unassigned. GG-070 RESOLVED: session-start governance hook was printing NBA's frozen ledger unlabeled as generic "PORTFOLIO (VPS LIVE BOOK)" — fixed to print both `MLB (ACTIVE)` / `NBA (DARK/FROZEN — historical, not live risk)` labeled ledgers every session; elevated to MEMORY_BANK.md ANTI-CONTEXT-EROSION INVARIANT #12. EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 re-run clean INCONCLUSIVE against fresh snapshot `SNAP-2026-07-02-002`. Full suite 2282/7/1 (1 pre-existing unrelated). Committed `f98dda3`, pushed, VPS deployed + `t4-mlb` restarted, confirmed active. See MEMORY_BANK.md and TODO_NEXT.md SESSION 113 entries for full detail.** *(Previous S110 CONTINUATION #2, session-end:)* **T-219 follow-up: no deliverables-table impact (backtest-runner build is not a milestone-tracked line item). GG-067 registered+resolved (false data-source claims in EXP-ARITH-MLB-01.md/EXP-FLOW-MLB-01.md corrected). Production per-cycle raw-context logging added to `run_t4_mlb_live.py` (`logs/t4_mlb_cycle_log.jsonl`, `game_date` field). `scripts/run_exp_arith_mlb_01.py` backtest runner built (36/36 tests) — grid-sweeps T4M-ARITH's `entry_window`/`confidence_gate` against the new cycle log, ADR-0024 tiers + T-177/GG-037 Fisher's-exact monotonicity guard applied. Result: BLOCKED, not run — cycle log had zero records at deploy time (logging feature went live with this session's own deploy; no game in progress at that hour). `T4M-ARITH` correctly remains `status="BLOCKED"` — code/infra ready, data doesn't exist yet. T4M-FLOW backtest runner NOT built (deprioritized behind ARITH per explicit session-opening instruction) — next open T4 sub-band code task once F-FLOW-01 score_diff/inning wiring exists. Full suite 2235/7/1 (1 pre-existing unrelated failure). Committed `b924f1d`/`e91734c`/`9cb08b1`, pushed, VPS synced (explicit `systemctl restart t4-mlb` for the live-path code change, then plain `git pull` for the docs-only closeout commit). See MEMORY_BANK.md and TODO_NEXT.md SESSION 110 entries for full detail.** *(Previous S109 CONTINUATION, session-end:)* **T-219 COMPLETE: MLB-native T4 sub-band architecture (ADR-0039) implemented per Earl's scoped DS sign-off (T4M-PROJ/T4M-ARITH/T4M-FLOW+BLOWOUT only). No deliverables-table impact (T-219 is not a milestone-tracked line item in this table). T4M-PROJ relabeled ACTIVE (zero live-path logic change); T4M-ARITH/T4M-FLOW built and tested but structurally BLOCKED, gated on EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 (both drafted this session, PLANNED — methodology only, not run). 17 new tests; full suite 2192 passed / 7 skipped / 1 pre-existing unrelated failure. Committed `4fdedc4`, pushed, VPS pulled to `4fdedc4` (no restart — docstring-only live-path change). T-220 registered (extra-innings `_AB_BY_SLOT` bug, LOW). See MEMORY_BANK.md SESSION 109 session-end entry for full detail.** *(Previous S108 CONTINUATION session-end:)* **Governance-only closeout, no deliverables-table impact. T-217/GG-063 VPS-deployed (`976d238`). T-218/ADR-0039 (MLB T4 sub-band scoping) drafted, Status corrected to DRAFT pending Earl's sign-off. GG-066 registered (no MLB real-time event feed). GG-053/GG-062 RESOLVED by parallel session (commit `f81edb0`, confirmed): staleness spike reattributed to a GG-062 process-duplication recurrence, fixed via flock singleton lock (T-216). Reconciled parallel-session commits `ef60c9c`/`3551aa3`; own governance-doc changes committed as `b001441`, pushed, VPS-deployed (docs-only). See MEMORY_BANK.md SESSION 108 session-end entry for full detail.** *(Previous S107 PAUSED:)* **Implementation session, no deliverables-table impact (T-212/T-213 are not milestone-tracked line items in this table). T-212 Phase 1 (GG-059, Data Quality Contracts) code-complete, 17-test regression unresolved (full-suite confirmed: 17 failed, 2145 passed, 6 skipped — 11 fixture-expansion fixes + 6 dead-code-assertion tests in test_t193_mlb_freshness_guard.py needing retirement). T-213 Phase 1 (GG-060, C4 Edge Accounting) not started. Nothing committed yet — see MEMORY_BANK.md and TODO_NEXT.md SESSION 107 entries for full detail. Resume next session.** *(Previous S106 CLOSE:)* **Governance-only session, no code changes, no deliverables-table impact. GG-058 fixed (T4 MLB UTC-midnight rollover), T1 MLB 50-bet anomaly investigated and closed (not a bug), GG-057 (C8 dashboard governance trail) resolved retroactively. GG-063 discovered (100% MLB Kalshi order failures, HTTP 410) → T-217 registered, now operator-flagged MUST-FIX for next session. T-211 (MLB T4 sub-bands, vacated SESSION 105/ADR-0037) elevated to HIGH PRIORITY for next session — needs new task number + ADR before any code. Commits `76e5c39` (+ prior `aaf1a9f`, `d1d36d8`), VPS deployed. See MEMORY_BANK.md SESSION 106 entry for full detail.** *(Previous S105:)* **Governance-only session, no code changes, no deliverables-table impact. ADR-0037 ACCEPTED: corrects ADR-0036 (NBA/MLB conflation — `t4_execution_engine.py` is the NBA T4 engine, not MLB). T-211 vacated before any code was written. GG-061 registered; GG-038/GG-039/GG-040 reverted OPEN. Commit `6a9fd66`, VPS deployed. See MEMORY_BANK.md SESSION 105 entry for full detail.** *(Previous S103:)* **GG-052 RESOLVED: T4 MLB `cycle_start_at` captured before Kalshi paginated fetch (60–130s) → freshness window expired before `_run_cycle()`. Fix: `cycle_start_at = snapshot_fetched_at` (after fetch). Commit `bbaf86a`. SESSION 102: T2 crash fix, YES-ONLY gate rescinded, ADR-0035 ACCEPTED. Tests: 2109/2109. VPS HEAD `bbaf86a`.** *(Previous S101:)* **ADR-0034 Layer 3 Semantic Contracts fully integrated and deployed. 5 patches (PIPE-05, T4 MLB `_run_cycle()`, C7 monitor, `__init__.py`). 25 new tests. 2151/2151 tests. Commit `501c4ca`. VPS active.** *(Previous S99:)* **T-208 COMPLETE: GG-050 T4 MLB re-betting bug fixed. EXP-T4-01 RETRACTED (n=73 INCONCLUSIVE). GG-046 REOPENED. T4 portfolio reset. 2113/2113 tests. Commit `840025f`. VPS active.** *(Previous S95:)* **T4 MLB HARDENED + LIVE. ESPN stat group filter bug fixed (T4 had 0 evaluations since launch). 3-layer T4 defense deployed (PIPE-08 + startup self-heal + systemd). T4 MLB Kalshi demo wired (ADR-0008 parity). PIPE-08 midnight-wrap bugfixes. Tests 2083→2110 (+27). T4 live: 80 fires, $19.84 deployed at session close. T1 "0 players matched" bug flagged (T-205). T-205 + T-206 registered.** *(Previous S94:)* **FULL MLB ARM LIVE. T-200 through T-204 ALL COMPLETE. MLB T4 iteration plan CLOSED. ADR-0033 ACCEPTED (provisional edge threshold). All 7 MLB crons active on VPS. First MLB T4 live evaluations tonight (22:00 UTC). First MLB T1 bets June 27 (11:00 UTC). GG-045 + GG-046 registered. 2083/2083 tests.** *(Previous S92:)* **T-200 + T-201 COMPLETE. MLB T4 ab_remaining inning-aware fix + dual-pool resolution. 2070/2070 tests. MLB T4 iteration plan active (T-202 dry-run mode next).** *(Previous S90:)* 2026-06-27 SESSION 90 CLOSE — **MLB-G1 gate CLOSED. T-194 through T-199 COMPLETE. ADR-0032 ACCEPTED. 6 MLB crons enabled. 2044/2044 tests. MLB paper trading arm live.** *(Previous S87:)* **T-191 COMPLETE: MLB arm institutional completion. T2 built (PIPE-05.5), DS-04 MLB designated, T4 bugs fixed (NFR-03, stat group filter, dead constant), T1 timing fixed (03:00 UTC same-day), T3 cron gate breach resolved. 1947/1947 tests. VPS HEAD `2f13a35`. All 7 MLB cron entries active. Next: monitor accumulation, EXP-017 MLB when ≥150 closed positions (Tier 1) or ≥500 (Tier 2).** *(Previous S86:)* **T-190 COMPLETE: full MLB arm built (pregame + T3 + T4). 1918/1918 tests. Next: VPS deploy + MLB cron activation.** *(Previous S85:)* **MLB arm audit: CLAUDE.md T4 corrected, MLB cron PAUSED, T-190 registered (3-step: pregame + T3 + T4 MLB). MLB accumulation suspended until all 3 components built and tested. 1819/1819 tests unchanged.** *(Previous S84:)* **T-189 COMPLETE: PIPE-05 three-concern remediation (GAME_DATE=tomorrow, ensure_persisted(), hydrate fix, cache bust scope). 1819/1819 tests. MLB portfolio $1,000 fresh start. PIPE-05 ready for June 25 slate.** *(Previous S83:)* **T-188 COMPLETE: MLB curses TUI dashboard. MLB accumulation LIVE as of 2026-06-24 (PIPE-05 first run tonight 23:30 UTC). 1790/1790 tests. VPS HEAD 42bce66.** T-187E (PIPE-05R resolve), T-187F (PIPE-05C calibration monitor, Mondays 14:10 UTC), T-187G (live SP overlay), T-187H (t=3 shadow gate re-evaluation — VALID NEGATIVE, GG-042 DEFERRED structural). 1790/1790 tests. VPS HEAD 6447fea. *(Previous S81:)* T-187B COMPLETE: per-threshold MLB LR+Platt models. Shadow gate PASS on VPS. PIPE-05 + per-threshold model live. 1704/1704 tests. T-187E/F/G remain.** *(Previous S80:)* **T-117 COMPLETE + GG-006 CLOSED + T-186 COMPLETE (valid negative). Kalshi Participant Agreement read — no automation restrictions; ADR-0005 pre-requisite satisfied. MLB paper book: fresh $1,000. T-186: PLUS_MINUS absent from nba_api.TeamGameLog (F-040/F-042 dead since EXP-005); cross-reference fix applied; v2b Brier +0.000130 < 0.001 → shadow gate FAIL → deploy v2-065b9510 October 2026. 1650/1650 tests. Commit 89d795c, VPS HEAD confirmed. T-187 REGISTERED: `scripts/run_mlb_paper_trade.py` (P0, before August 2026).** *(Previous S75:)* **T-181 COMPLETE: MLB C1 data ingestion module (3 new source files, 80 tests, 1373/1373 green). MLB Stats API data source decision logged. IF-C1-C2 MLB contract established. Next: T-182 (MLB C2 feature set, P0).** *(Previous S74:)* Governance-only. MLB $1K fresh paper book decision. Phase 3 task registration: T-181/T-182/T-183/T-184/T-186. T-185 v2 deploy runbook. ADR-0031 Known Limitations added. DARK_PERIOD_PLAN updated. 1293 tests unchanged. *(Previous S72:)* **Governance-only. ADR-0028 ACCEPTED (DS sign-off Earl Ignacio); T-148 DONE; GG-022 RESOLVED; GG-041 registered (T-127 KI-023 Finals window miss; deferred Phase 4 Oct 2026). 1280 tests unchanged.** *(Previous S68:)* **T-180 PHASE 2 COMPLETE: the T4 routing engine built (substance of ADR-0029 Tier A; resolves S67 Q6 flag). `t4_price_cache.py` (GG-039 architecture; `T4PriceCache`/`STALENESS_WINDOW_S`/`T4Phase8BlockedError`; polling deferred to Phase 8) + `t4_execution_engine.py` (`GamePhase`, `Layer1EvaluationEngine` event-dispatch, `Layer2ExecutionQueue` heapq EXIT-priority + 3 drop conditions, 8 BLOCKED evaluator stubs, `T4CorrAdjuster._assert_downward_only` Principle-6, `_PHASE8_ACTIVE=False`) + `tests/test_t4_engine.py` (+109). VERIFIED 1108/1108 green; all execution paths provably blocked. T4 STILL DARK (gated GG-038/039/040); evaluator math still empty stubs — remaining T-180 / Phase 8. Engine commit + no-op VPS deploy this session.** *(Previous, SESSION 67:)* **ADR-0029 ACCEPTED (Tier A frozen, DS sign-off Earl Ignacio; Tier B provisional). T-180 SCAFFOLD landed: `execution_bands.py` split — `T4_IN_PLAY` kept as aggregate parent, 10 sub-bands added beneath via `T4_SUBBANDS`/`is_t4_subband()`/`t4_parent()`; `T4SubBandSpec`+`T4_SUBBAND_REGISTRY` (all BLOCKED) encode Tier B in code + `validate_t4_subbands()` invariant; PROJ/ARITH Kelly ≤0.167; Strategy K not redefined (ADR-0030 overlap OPEN). 999/999 tests.** *(Previous, SESSION 66:)* **T-179 ADR-0029 drafted (PENDING DS SIGN-OFF): T4 11-sub-band architecture; GG-038/039/040 registered; code changes blocked pending sign-off; 988/988 tests; no VPS deploy.** *(Previous, SESSION 65:)* **T-148 ADR-0028 rework complete (PENDING DS SIGN-OFF): G6 is T1-only; T4 Activation Gate created as Phase 8 placeholder; T-179 registered.** *(Previous, SESSION 64:)* Pre-MLB governance sprint complete: GG-036 + GG-035 + GG-037(calibration half) RESOLVED; full-DB assessment done. VPS HEAD `897ff4d`; 988/988 tests. GG-036: re-froze 158-bet NBA Finals dataset, G5 resolved (NOT fabricated). GG-035 (ADR-0026/APR-0020): C4 two-tier portfolio free-cash invariant shipped. GG-037 (ADR-0027/APR-0021): C3 temperature calibration on production Poisson prob (NOT Platt); NBA T=2.05 OOS, MLB fail-safe identity. **Recalibration DISPROVED miscalibration — edge anti-predictive post-calibration; GG-037 alpha half + GG-004 stay OPEN; no demonstrated alpha vs Kalshi.** New tasks: T-175 (ADR-0026 caller coverage), T-176 (MLB T derivation, dark period), T-177 (edge-inversion/no-alpha, G6 blocker), T-178 (market_mapper MLB pre-flight). Paper book remains halted at drawdown kill switch (25.12%). MLB C1 data-source selection still pending operator/DS. *(Previous, SESSION 63:)* T-174 + T-171 DEPLOYED + live book corrected; GG-034 + GG-033 RESOLVED (VPS HEAD `52607f2`); G6 baseline RATIFIED negative — Tier 0/EXP-017 (GG-004) still the binding G6 blocker.  
**Next review:** Weekly; update on any milestone slip > 3 days; update at each gate  
**Staleness triggers:** Milestone complete; milestone slips; scope change; resource change  
**Upstream links:** ROADMAP_MILESTONES.md, REQUIREMENTS.md, ARCHITECTURE_OVERVIEW.md  
**Downstream links:** TODO_NEXT.md, RID_LOG.md, STATUS_REPORTS/  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Confidence:** 8/10 — G4 CLOSED 2026-05-28; Phase 5 Operational Readiness active; later phases planned at lower fidelity

---

## Phase 0 — Directory Scaffolding + Governance Spine ✅ COMPLETE

**Gate:** G0 Intent | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0002 signed 2026-05-22

### Phase 0 Work Plan

| # | Task | Owner | Due | Status | Blocker |
|---|------|-------|-----|--------|---------|
| 0.1 | Full directory skeleton | DS | 2026-05-21 | ✅ Done | — |
| 0.2 | 00_ADMIN complete (all 9 files + templates) | DS/PO | 2026-05-22 | ✅ Done | — |
| 0.3 | 01_SPEC complete (all 8 artifacts) | PO | 2026-05-22 | ✅ Done | — |
| 0.4 | 02_ARCHITECTURE_DESIGN complete | AO | 2026-05-22 | ✅ Done | — |
| 0.5 | 03_DECISIONS complete (ADR-0001, ADR-0002, registers) | DS | 2026-05-22 | ✅ Done | — |
| 0.6 | 04_EXECUTION complete (PLAN, TODO, RID) | EL | 2026-05-22 | ✅ Done | — |
| 0.7 | 05_RESEARCH_EXPERIMENTS complete | RL | 2026-05-22 | ✅ Done | — |
| 0.8 | 06_CODE_EXECUTION_REPRODUCIBILITY complete | AO | 2026-05-22 | ✅ Done | — |
| 0.9 | 07–10 modules complete | Multiple | 2026-05-22 | ✅ Done | — |
| 0.10 | 11_MEMORY_HANDOFF: MEMORY_BANK.md + baseline CP | DS | 2026-05-22 | ✅ Done | — |
| 0.11 | First DIR; health report | DS | 2026-05-22 | ✅ Done | — |
| 0.12 | G0 exit checklist complete | DS/PO | 2026-05-22 | ✅ Done | — |

### G0 Exit Criteria

- [x] Charter frozen (PROJECT_CHARTER.md — FROZEN status)
- [x] All 00_ADMIN artifacts in CANONICAL or FROZEN state
- [x] MEMORY_BANK.md initialized with all canonical links
- [x] Baseline Context Pack produced (CP-2026-05-22_baseline-handoff.md)
- [x] First DIR completed — M1 all artifacts stamped 2026-05-22 ✅
- [x] ADR-0001 and ADR-0002 accepted; APR-0002 signed 2026-05-22

---

## Phase 1 — Spec + Research Framing ✅ COMPLETE

**Gate:** G1 Spec | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0003 signed 2026-05-22

### Phase 1 Work Plan

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| 1.1 | REQUIREMENTS.md frozen (all FR/NFR complete) | PO | 2026-05-31 | ✅ Done — FROZEN 2026-05-22 (T-010) |
| 1.2 | ACCEPTANCE_CRITERIA.md frozen | EO | 2026-06-01 | ✅ Done — FROZEN 2026-05-22 (T-011) |
| 1.3 | RESEARCH_QUESTIONS.md confirmed CANONICAL | RL | 2026-06-01 | ✅ Done (written at G0) |
| 1.4 | HYPOTHESES.md confirmed CANONICAL | RL | 2026-06-03 | ✅ Done (written at G0) |
| 1.5 | Player_Attribute_Matrix staged in 05_RESEARCH/ with snapshot header | RL | 2026-06-03 | ✅ Done — SNAP-001 registered 2026-05-22 |
| 1.6 | ADR-0002 confirmed (APR-0002 signed) | DS | 2026-05-22 | ✅ Done |
| 1.7 | ASSUMPTIONS_REGISTER.md populated (≥5 assumptions) | RL/AO | 2026-06-05 | ✅ Done (7 at G0) |
| 1.8 | OQ-001 resolved (Player_Attribute_Matrix provenance) | RL | 2026-06-03 | ✅ Done — resolved 2026-05-22; DATA_PROVENANCE.md updated |
| 1.9 | OQ-003 resolved (target market category) | RL/PO | 2026-06-01 | ✅ Done — NBA, dynamically agnostic, Kalshi primary; resolved 2026-05-22 |
| 1.10 | G1 exit checklist | PO/DS | 2026-06-07 | ✅ Done — all 5 criteria met; APR-0003 signed 2026-05-22 |

### G1 Exit Criteria

- [x] Requirements are testable (all FR/NFR have measurable acceptance criteria — REQUIREMENTS.md FROZEN)
- [x] Priorities are explicit (P0/P1/P2 designations confirmed — REQUIREMENTS.md FROZEN)
- [x] ASSUMPTIONS_REGISTER.md has ≥5 research assumptions (ASM-001 through ASM-007)
- [x] Target market category confirmed (OQ-003 resolved 2026-05-22 — NBA, dynamically agnostic, Kalshi primary)
- [x] Player_Attribute_Matrix provenance documented (OQ-001 resolved 2026-05-22 — DATA_PROVENANCE.md; SNAP-001)

---

## Phase 2 — Architecture + Infrastructure Design ✅ COMPLETE

**Gates:** G2 Architecture | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0004 signed 2026-05-22

### Phase 2 Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| ARCHITECTURE_OVERVIEW.md reviewed + promoted | AO | 2026-06-11 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| INTERFACES_CONTRACTS.md reviewed + promoted | AO | 2026-06-13 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| RESILIENCE_FAILURE_MODES.md reviewed + promoted | AO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| THREAT_MODEL.md reviewed + promoted; RCO sign-off | AO/RCO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| G2 gate signed (APR-0004) | AO | 2026-06-15 | G2 | ✅ Done — 2026-05-22 |

### G2 Exit Criteria

- [x] All core architecture artifacts CANONICAL (ARCHITECTURE_OVERVIEW, INTERFACES_CONTRACTS, RESILIENCE_FAILURE_MODES, THREAT_MODEL)
- [x] C4/C5 naming consistent across all architecture artifacts (C4=Risk Engine, C5=Execution Engine)
- [x] Interface contracts versioned and downstream-acknowledged
- [x] Technology stack confirmed (Python 3.11, JSON Lines logging, pip/pyproject.toml)
- [x] APR-0004 signed 2026-05-22

---

## Phase 2 (G3) — Execution Infrastructure Design ✅ COMPLETE

**Gate:** G3 Execution | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0005 signed 2026-05-22

### Phase 2/G3 Key Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| RUN_INSTRUCTIONS.md + ENVIRONMENTS.md reviewed + promoted | EL | 2026-06-17 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-026) |
| DEPENDENCY_LOCKS/ confirmed | EL | 2026-06-17 | G3 | ✅ Done — confirmed at G3 |
| PLAN.md + RID_LOG.md baselined | EL | 2026-06-19 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-027) |
| ADR-0003 formal acceptance (pending OQ-006) | AO | 2026-06-21 | G3 | ⚠️ Excepted — OQ-006 operator action; gate closed with exception |
| G3 gate signed (APR-0005) | EL/DS | 2026-06-21 | G3 | ✅ Done — 2026-05-22 |

### G3 Exit Criteria

- [x] RUN_INSTRUCTIONS.md CANONICAL — environment setup and pipeline run commands documented (Python 3.11, venv, requirements-dev.txt, pre-commit)
- [x] ENVIRONMENTS.md CANONICAL — ENV-01/02/03 defined; environment variables confirmed; health checks documented
- [x] RID_LOG.md baselined at G3 — RID-D002/D003 archived (OQ-001/003 resolved); RID-D001 updated (ADR-0003 skeleton); RID-003 partially mitigated
- [x] PLAN.md baselined for Phase 3 entry
- [⚠️] ADR-0003 formal acceptance — skeleton CANONICAL PENDING; OQ-006 excepted per standing operator authorization; must resolve before Phase 3 data integration

---

## Phases 3–4 — ✅ COMPLETE (2026-05-22 – 2026-05-28)

**Phase 3 (Research Build):** G3 CLOSED 2026-05-22 — C1–C6 implemented; ADR-0003 accepted  
**Phase 4 (Evidence Capture):** G4 CLOSED 2026-05-28 — TEST Brier +0.0084/ECE 0.0247; ADR-0004 ACCEPTED (APR-0012)

| Deliverable | Owner | Status |
|------------|-------|--------|
| ADR-0003 formal acceptance | AO | ✅ 2026-05-23 — APR-0011 |
| C1–C6 implementation | EL | ✅ 2026-05-26 — T-032/033/034 |
| EXP-001/002/003 (50-player, SNAP-2026-05-28-001) | RL | ✅ 2026-05-28 — T-043; G4 criteria MET |
| FEATURE_VERSION 1.2.0 (31 features, HYP-005 falsified) | EL | ✅ 2026-05-28 — T-046 |
| ADR-0004 (LR+Platt model class confirmation) | AO | ✅ 2026-05-28 — T-047; APR-0012 ACCEPTED |
| G4 TEST set evaluation | MV | ✅ 2026-05-28 — T-048; Brier +0.0084/ECE 0.0247/AUC 0.6062 |

## Phase 5 — Operational Readiness ✅ COMPLETE

**Gate:** G5 Operational | **Closed:** 2026-05-28 | **Status:** ✅ APR-0007 ACCEPTED

| Deliverable | Owner | Status |
|------------|-------|--------|
| C7 Monitoring + Kill Switch (T-049) | EL | ✅ 0.340ms drill; APR-0013 |
| C8 Visual Dashboard (T-050) | EL | ✅ 3 panels; CLI |
| Kill switch drill TC-007 (T-051) | EL/DS | ✅ KS-C8D7D90AF942 |
| EXP-004 HYP-003 Parts A+B (T-052) | RL | ✅ EV +$0.0855/bet; CONFIRMED |
| Sensitivity tests ST-001–004 (T-053) | MV | ✅ All PASS |

---

## Current Phase: Phase 6 — Paper Trading

**Gate:** G6 Release (live capital) | **Started:** 2026-05-29 | **Status:** 🟢 Active

### Phase 6 Key Deliverables

| Deliverable | Owner | Priority | Status |
|------------|-------|----------|--------|
| Model data refresh 5 seasons (T-058) | EL | HIGH | ✅ 2026-05-28 — EXP-005; Brier +0.0024; v1-9939a6a5 |
| Qualitative pipeline (QS + EXP-006–008) | RL | HIGH | ✅ 2026-05-28/29 — EXP-007 +0.0017 Brier CONFIRMED |
| Gradient boosting experiment (T-065/EXP-011) | EL | MED | ✅ 2026-05-29 — LR RETAINED; ADR-0004 unchanged |
| EV re-estimation (T-069/EXP-010) | RL | HIGH | ✅ 2026-05-29 — +$0.0958/bet; 61.1% win rate |
| VPS provisioning (T-059) | IO | HIGH | ✅ 2026-05-29 — 157.230.91.33; cron active |
| Paper trading pipeline PIPE-03 (T-060) | EL | HIGH | ✅ 2026-05-29 — $1,000 bankroll; running |
| Accumulate paper evidence ≥66 bets / ≥5 nights (T-110, APR-0017) | DS | HIGH | 🟡 IN PROGRESS — T1: 114+29(G5 open)/66 bets ✓; G5 closes 5/5 game nights ✓; GG-004 OPEN (EXP-017B DIRECTIONAL_NEGATIVE, -$0.0361/bet vs Kalshi prices); GG-014 BREACHED (9/29=31% G5 order failures, T-164 registered); VPS bankroll $285.27; ADR-0023 deployed |
| PIPE-07 T4 in-play paper trading (PIPE-07) | EL | HIGH | ✅ 2026-06-08 SESSION 37 — portfolio isolation fix, cron.conf 23:00 UTC, PIPE-07R-LOCAL script |
| ADR-0005 live capital authorization (T-061) | AO/DS | LOW | 🔲 After paper evidence |

---

## Phases 3–9 — High-Level Plan

| Phase | Key Work | Gate | Target |
|-------|----------|------|--------|
| 3 Research Build | C1–C3 pipeline; first experiment; backtesting framework | — | **2026-06-21** (compressed — NBA playoffs end) |
| 4 Validation | G4 evidence collection; model card; drift thresholds confirmed | G4 | 2026-08-23 |
| 5 Operational Readiness | C7 wired; kill switch drilled; secrets vault; G5 ops gate | G5 | 2026-09-13 |
| 6 Paper Trading | Full simulated cycle; N events; paper results collected | — | 2026-10-25 |
| 7 Promotion Gate | Paper evidence reviewed; G6 readiness checklist | G6 | 2026-12-06 |
| 8 Live Capital | Real orders; drawdown tracking; governance in steady state | — | 2027-Q1 |
| 9 Self-Service Governance | Automated DIR; quarterly retrieval drills; continuous ops | — | From Phase 8 |

---

## Planning Assumptions

1. Single operator (Earl Ignacio) across all roles
2. Timeline contingent on Player_Attribute_Matrix validation (if falsified at Phase 3, G4 date shifts)
3. Venue selection (ADR-0003) could shift Phase 3 start by 1–2 weeks
4. All dates assume no major operational incident requiring remediation
