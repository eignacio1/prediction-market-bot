# Known Issues — Prediction Market Trading Bot

**Purpose:** Track known issues, limitations, and technical debt that are acknowledged but not yet resolved. Distinguishes between issues that are acceptable risks versus those that must be resolved before specific gate clearances.  
**Owner (role):** Infrastructure Operator (IO) + Model Owner (MO)  
**Last reviewed:** 2026-05-22  
**Next review:** Weekly cadence during active development; update when issue resolved or new issue discovered  
**Staleness triggers:** Issue resolved; new issue discovered; blocking condition changes  
**Upstream links:** RID_LOG.md, OPEN_QUESTIONS.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** TODO_NEXT.md, RUNBOOKS/  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Current known issues accurately reflect Phase 0/1 state

---

## Active Known Issues

### KI-001 — DS-01 Provenance Unknown

| Field | Detail |
|-------|--------|
| Issue ID | KI-001 |
| Severity | HIGH |
| Category | Data governance |
| Description | Player_Attribute_Matrix_v4.docx source, creator, and creation date are unknown. The file exists as an artifact from a prior iteration but its provenance has not been documented. |
| Impact | Cannot use DS-01 in any experiment until OQ-001 is resolved |
| Workaround | None — must be resolved before Phase 3 work begins |
| Blocks gate | G1 exit; any experiment using DS-01 |
| Resolution path | Document source, creator, creation date; validate schema; register as snapshot (DATA_PROVENANCE.md action list) |
| Open question | OQ-001 |
| Status | OPEN — Phase 0 |

---

### KI-002 — Venue Not Selected

| Field | Detail |
|-------|--------|
| Issue ID | KI-002 |
| Severity | HIGH |
| Category | Architecture dependency |
| Description | The prediction market venue (Kalshi, Polymarket, or other) has not been selected. This blocks API client development, market data schema definition, and execution architecture finalization. |
| Impact | Blocks: DS-02/DS-03 schema, C5 implementation, HYP-003 testing, DEPENDENCIES.md vendor SDK, POLICY_REQUIREMENTS.md POL-001/POL-003 |
| Workaround | Research phase can proceed with DS-01 only; venue-dependent work deferred |
| Blocks gate | G3 (Architecture Complete) |
| Resolution path | ADR-0003: venue selection decision with TOS review |
| Open question | OQ-006 |
| Status | OPEN — deferred to G2/G3 |

---

### KI-003 — Secrets Vault Solution Undefined

| Field | Detail |
|-------|--------|
| Issue ID | KI-003 |
| Severity | MEDIUM (LOW at Phase 1-4; HIGH at Phase 5+) |
| Category | Security infrastructure |
| Description | No secrets vault solution has been selected. python-dotenv is acceptable for research-only phases but not for paper/live trading. |
| Impact | Cannot provision live API credentials safely until vault is in place |
| Workaround | python-dotenv (.env file, gitignored) for Phase 1-4 only |
| Blocks gate | G5 (Paper Trading Authorization) |
| Resolution path | Evaluate candidates (HashiCorp Vault, AWS Secrets Manager, macOS Keychain); select and document at G5 |
| Open question | OQ-009 |
| Status | OPEN — acceptable for current phase |

---

### KI-004 — C7 Monitoring Implementation Not Designed

| Field | Detail |
|-------|--------|
| Issue ID | KI-004 |
| Severity | MEDIUM (Phase 5+ blocker) |
| Category | Infrastructure |
| Description | The monitoring component (C7) design is specified at the interface level but the implementation approach (library, framework, alert delivery mechanism) has not been selected. |
| Impact | Cannot implement real-time drift detection or automated alerting |
| Workaround | Manual metric computation during Phase 3-4 experiments |
| Blocks gate | G5 (C7 must be active before paper trading) |
| Resolution path | Resolve OQ-010; implement C7 during Phase 4 |
| Open question | OQ-010 |
| Status | OPEN — deferred to Phase 4 |

---

### KI-005 — Kill Switch Not Implemented or Tested

| Field | Detail |
|-------|--------|
| Issue ID | KI-005 |
| Severity | MEDIUM (Phase 5+ blocker) |
| Category | Safety / NFR-03 |
| Description | The kill switch is designed (EXECUTION_ARCHITECTURE.md, RUNBOOK_kill-switch.md) but not implemented or tested. The drill (TC-009, TC-010) cannot be run until implementation is complete. |
| Impact | Cannot clear G5 gate; must not go to paper trading without tested kill switch |
| Workaround | None — kill switch implementation is required |
| Blocks gate | G5 (kill switch drill required) |
| Resolution path | Implement kill switch in Phase 4; drill in Phase 5 preparation |
| Open question | None — this is a known implementation task |
| Status | OPEN — implementation deferred to Phase 4 |

---

### KI-006 — Model Class Not Selected

| Field | Detail |
|-------|--------|
| Issue ID | KI-006 |
| Severity | LOW (Phase 3 task) |
| Category | Research |
| Description | Model class (logistic regression, XGBoost, or other) has not been selected. This is expected at Phase 0 — the selection is deferred to G3 after evidence from Phase 3 experiments. |
| Impact | MODEL_CARD.md model overview is template-only; METHODOLOGY.md model class is TBD |
| Workaround | N/A — this is the intended research process |
| Blocks gate | G4 (model must be selected and evidenced) |
| Resolution path | Phase 3 experiments evaluate candidates; ADR-0003 finalizes selection |
| Open question | OQ-007 (technology stack) |
| Status | OPEN — expected; not a problem at this phase |

---

### KI-007 — arb/ Folder Excluded from All Active Work

| Field | Detail |
|-------|--------|
| Issue ID | KI-007 |
| Severity | LOW (by design) |
| Category | Governance |
| Description | The arb/ folder from the prior iteration is explicitly excluded from all active development and experiments. It is reference-only for holistic future planning. Incorporating it requires a new ADR. |
| Impact | Any arbitrage strategy ideas from arb/ cannot be acted upon without ADR |
| Workaround | N/A — this is an intentional governance constraint, not a workaround situation |
| Blocks gate | Nothing currently; APR-0010 is the future gate |
| Resolution path | Future ADR if evidence at G4 suggests arbitrage is viable |
| Open question | None — constraint is intentional |
| Status | ACKNOWLEDGED BY DESIGN — see REJECTED_OPTIONS.md RO-001 |

---

### KI-008 — Production Model Untested on Playoff Data

| Field | Detail |
|-------|--------|
| Issue ID | KI-008 |
| Severity | HIGH |
| Category | Model validity / data distribution |
| Description | The production model (v1-28483b21, LR+Platt, 78 features) was trained and validated exclusively on regular season game logs (2021-26). All experiments EXP-001 through EXP-015 used `SEASON_TYPE_REGULAR`. Paper trading began 2026-05-29 during the NBA Western Conference Finals — a fundamentally different distribution: compressed rotations, elevated defensive intensity, no back-to-back scheduling, and high-stakes rest patterns not present in regular season data. |
| Impact | Paper trading bets placed during playoffs may not reflect the model's validated EV (+$0.0958/bet, EXP-010). If the model is miscalibrated for playoff conditions, paper P&L is not reliable G6 evidence. |
| Workaround | EXP-016 (T-072) quantifies the Brier degradation on held-out playoff rows. If Δ Brier < 0.012 (HYP-009 gate), paper results remain valid. If falsified, playoff-era paper bets must be annotated as lower-confidence G6 evidence. |
| Blocks gate | G6 — paper evidence reliability is partially dependent on playoff/regular distinction |
| Resolution path | 1. Run EXP-016 to get Δ Brier verdict (HYP-009). 2. If falsified, register playoff bets separately in paper portfolio and apply a confidence discount. 3. T-072: after 2025-26 Finals, retrain model with playoff data and evaluate Brier delta (ADR required). |
| Open question | None — resolved |
| Registered | 2026-05-29 |
| Status | ✅ RESOLVED (2026-05-29, EXP-016) — HYP-009 CONFIRMED; Δ Brier = -0.0010; playoff paper bets are valid G6 evidence at full confidence; T-072 post-Finals refresh is optional enrichment only |

---

### KI-009 — G6 Bet Gate Calendar Constraint (RESOLVED via APR-0016)

| Field | Detail |
|-------|--------|
| Issue ID | KI-009 |
| Severity | MEDIUM |
| Category | Project timeline |
| Description | The original G6 gate required 50+ resolved paper bets. Paper trading commenced 2026-05-29 with the NBA Western Conference Finals in progress. At ~4 bets per game day (dual-window PIPE-03), and ~10-15 remaining playoff games before Finals end (~2026-06-22), reaching 50 was borderline impossible within the season. |
| Impact | Managed via APR-0016: threshold revised to 30 resolved bets. If not reached by Finals end, accumulation window extends to first 30 days of 2026-27 regular season (October 2026). |
| Workaround | APR-0016 applied. Dark period (~2026-06-22 to ~2026-10) used for pre-season infrastructure build. |
| Blocks gate | G6 — resolved; 30-bet target is achievable within playoff window |
| Resolution path | ✅ RESOLVED — APR-0016 ACCEPTED 2026-05-29. Threshold = 30 resolved bets + positive Brier-consistent EV. |
| Open question | None |
| Registered | 2026-05-29 |
| Status | ✅ RESOLVED — APR-0016 accepted; threshold = 30 bets |

---

### KI-010 — Inter-Series Gap: Zero Bet Window Before NBA Finals

| Field | Detail |
|-------|--------|
| Issue ID | KI-010 |
| Severity | MEDIUM |
| Category | Paper trading / bet accumulation |
| Description | After the Western Conference Finals end and before the NBA Finals begin, there is typically a 3–7 day gap with no NBA games and therefore no Kalshi markets. PIPE-03 fires but finds zero markets; zero bets are placed. This gap is silent — cron runs successfully, logs show 0 bets, but the G6 bet count does not advance. |
| Impact | Reduces effective accumulation days by 3–7 within an already tight window (~15 remaining playoff games before Finals end ~2026-06-22). With G6 gate at 30 bets, losing a week to an inter-series gap is material. |
| Workaround | None — this is a structural property of the NBA schedule. Monitor paper_portfolio.json bet count against days remaining before ~2026-06-22. If Finals gap observed, re-project reachability. |
| Blocks gate | G6 indirectly — if gap reduces total bets below 30 before season end |
| Resolution path | If 30 bets not reached before Finals end: APR-0016 extension window activates (first 30 days of 2026-27 regular season, October 2026). No code change needed — just time. |
| Open question | None |
| Registered | 2026-05-29 |
| Status | OPEN — monitoring |

---

### KI-011 — Key Player Injury Eliminates Market Category Mid-Paper Run

| Field | Detail |
|-------|--------|
| Issue ID | KI-011 |
| Severity | MEDIUM |
| Category | Paper trading / portfolio integrity |
| Description | The current paper trading cohort (~80 players) concentrates on high-usage players who generate KXNBAPTS markets. If a key player (e.g., SGA, Fox, Jokić) suffers a game-ending or season-ending injury, Kalshi may stop listing markets for that player entirely. Existing open positions would need to be resolved (nba_api will show DNP). Future bets for that player become impossible. |
| Impact | Reduces the effective betting universe mid-paper run. If multiple players are injured simultaneously (not uncommon in playoffs), the pipeline may find 0 eligible markets per session and bet accumulation stalls without obvious error. |
| Workaround | run_resolve.py (PIPE-03R) will handle resolution via nba_api DNP detection. Bet accumulation gap is unmitigated — it is an inherent risk of a concentrated player cohort during playoffs. |
| Blocks gate | G6 indirectly — stalls bet accumulation |
| Resolution path | Monitor paper_portfolio.json for consecutive sessions with 0 bets placed (cron runs successfully but 0 markets eligible). If confirmed, expand cohort or adjust to team-level markets if available. |
| Open question | None |
| Registered | 2026-05-29 |
| Status | OPEN — monitoring |

---

### KI-012 — Negative Paper P&L Disqualifies G6 Without Monitoring Threshold

| Field | Detail |
|-------|--------|
| Issue ID | KI-012 |
| Severity | MEDIUM |
| Category | G6 gate / paper trading integrity |
| Description | The G6 gate requires 30 resolved paper bets with **positive P&L**. The P&L condition is binary — either positive or not. Currently there is no monitoring threshold or early-warning alert for P&L approaching zero. The paper portfolio could trend negative over 10-15 bets without any automated signal, only to disqualify G6 evidence after the full 30 bets. The model's EV is +$0.0958/bet (EXP-010), but variance over 30 bets is sufficient to produce a negative P&L run. |
| Impact | If P&L is negative at bet 30, all 30 bets become lower-quality G6 evidence requiring annotation. This delays G6 by an entire NBA season if it occurs near Finals end. |
| Workaround | Manually check `logs/paper_portfolio.json` on VPS after each session. Watch the `total_pnl` field. If total P&L goes negative before bet 15, flag to DS — may indicate model degradation requiring investigation before completing the paper run. |
| Blocks gate | G6 directly if P&L is negative at 30 bets |
| Resolution path | (1) Add a P&L monitoring alert to C7 SystemMonitor: if paper `total_pnl` < -$50 (5% of bankroll), emit WARNING. (2) If total_pnl < -$100, emit L2 drift alert. (3) DS review before continuing paper run. This is a buildable enhancement (T-091). |
| Open question | What is the appropriate early-warning threshold? Suggest -$50 (5% bankroll) as L1 and -$100 (10%) as L2. Requires DS sign-off. |
| Registered | 2026-05-29 |
| Status | OPEN — no monitoring threshold set; manual check required |

---

### KI-013 — Model Staleness: v1-28483b21 Trained Through 2026-05; 5+ Months Stale at 2026-27 Season Open

| Field | Detail |
|-------|--------|
| Issue ID | KI-013 |
| Severity | MEDIUM |
| Category | Model risk / temporal validity |
| Description | The production model v1-28483b21 was trained on data through the 2025-26 regular season and playoffs (via EXP-005 + EXP-016 data). The NBA dark period runs ~2026-06-22 to ~2026-10. If G6 is not cleared before Finals end and paper trading continues into the 2026-27 regular season, the model will be used on 2026-27 player data while trained exclusively on 2021-26 data. Player form, team composition, and injury history all change over a summer. Rolling features (pts_l10_mean) will re-populate correctly from live nba_api data, but the model's calibration baseline (Platt scaling, decision boundary) reflects 2021-26 distributions. |
| Impact | Model may be miscalibrated for the first 2–4 weeks of the 2026-27 season. Paper bets placed during this period carry elevated uncertainty. G6 evidence from this window should be annotated as "early 2026-27, pre-retrain." |
| Workaround | T-072 (model refresh with 2026-27 data) is designated as the solution but is currently "optional post-Finals enrichment." This is too weak a designation given the calibration risk. |
| Blocks gate | G6 indirectly — paper evidence quality is lower during the stale window |
| Resolution path | (1) Elevate T-072 from "optional" to "required before paper trading resumes in 2026-27." (2) After 2026-27 preseason begins (~October 2026), pull fresh nba_api data and retrain with new ADR. (3) Model refresh requires G4-equivalent evidence before promotion. Timeline: target retrain by 2026-10-15 (before regular season tip-off). |
| Open question | Does model staleness require a new ADR, or is it covered by the existing "model retraining requires ADR" rule in ADR-0004? Answer: yes, covered — any retrain needs new ADR per ADR-0004. |
| Registered | 2026-05-29 |
| Status | OPEN — T-072 must be elevated before dark period ends |

---

## Resolved Issues

*Populated as issues are resolved.*

| Issue ID | Resolution Date | Resolution Summary |
|----------|----------------|-------------------|
| KI-008 | 2026-05-29 | EXP-016 run; HYP-009 CONFIRMED; Δ Brier = -0.0010 (gate < 0.012); playoff paper bets = full G6 evidence |
| KI-009 | 2026-05-29 | APR-0016 signed; G6 threshold revised 50 → 30 resolved bets; seasonal constraint formally acknowledged |

---

## Issue Triage Criteria

Issues are classified on two dimensions:

**Severity:**
- HIGH: Blocks a gate or makes a component unsafe to use
- MEDIUM: Must be resolved before a future phase; currently manageable with workaround
- LOW: Acknowledged limitation; acceptable for current state; no active blocker

**Resolution urgency:**
- G1 blocker: Must resolve before G1 exit
- G2 blocker: Must resolve before G2 exit
- G3 blocker: Must resolve before G3 exit
- G5 blocker: Must resolve before paper trading
- G6 blocker: Must resolve before live capital
- Non-blocking: Acknowledged; resolution opportunistic
