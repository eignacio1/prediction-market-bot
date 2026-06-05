# Governance Gap Log — Prediction Market Trading Bot

**Purpose:** Register every discovered governance process failure — decisions that should have been made and weren't, thresholds set as placeholders and never revisited, architectural assumptions that went undocumented. This is distinct from DECISION_LOG (records decisions *made*) and KNOWN_ISSUES (records runtime bugs). This records failures of the governance *system itself*.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-06-01  
**Next review:** Session start (mandatory scan); after every gate review; after any incident  
**Staleness triggers:** New gap discovered; existing gap resolved  
**Upstream links:** DECISION_LOG.md, KNOWN_ISSUES.md, LESSONS_LEARNED.md  
**Downstream links:** TODO_NEXT.md (remediation tasks), ADRs (resolution artifacts)  
**Decision references:** ADR-0007 (Governance Gap Logging — mandates this artifact)  
**Confidence:** 10/10 — Three gaps registered at artifact creation

---

## Why This Artifact Exists

The prior iteration failed to context rot → hallucination → contamination. The current iteration built extensive governance: ADRs, decision logs, gate reviews, session handoffs. Yet GG-001 through GG-003 still happened.

**The gap the prior system could not catch:** Decisions made correctly at an early phase that became *wrong* after the architecture grew past them — with nothing in the governance system to trigger a re-review.

Session-start scans caught `decisions_logged: false`. They did not catch "this value was set at G4 when we had 10 players and is now running on 80 players across 5 execution bands." The ARE WE COMPROMISED? check (MEMORY_BANK.md) was designed to catch this class of failure going forward.

---

## Active Gaps

### GG-001 — max_concurrent_positions: 10 stub survived G4→G5→G7 undetected

| Field | Detail |
|---|---|
| Gap ID | GG-001 |
| Category | Architectural placeholder survived gate review |
| What was missed | `_HARD_LIMITS["max_concurrent_positions"] = 10.0` was set at G4 as a stub with explicit `# TBD at G4 review` comment. The G4 gate review confirmed the *existence* of the check but never validated whether 10 was architecturally correct. Three subsequent phases (G5, G6, G7) were cleared without the value being revisited. |
| When it should have been caught | G4 Evidence Gate (2026-05-28) — when actual player cohort size, execution bands, and resolution lag were known |
| Phases it survived | G4 → G5 → G6 → G7 (3 gate clearances) |
| Why it survived | The governance scan checked `decisions_logged: false` in documentation headers. It did not check for `# stub` / `# placeholder` comments in source code. The gate review asked "does this work?" not "is this value correct for the architecture we just built?" |
| Impact | Count-based position gate was architecturally wrong for a multi-band, 80-player, multi-game quant execution system. Would have silently rejected valid bets in regular season on the first multi-game night. Active blocker during paper trading (9/10 positions filled, Finals G2 at risk). |
| Discovery | Operator manual review 2026-05-31 — noticed strategic incoherence between the limit and the execution architecture |
| Discovery method | Human eye test — NOT caught by any automated scan or governance artifact |
| Resolution | ADR-0006: delete count gate entirely; pipeline + Kelly + kill switch are the risk framework. Code fix: T-102 (2026-06-01). |
| Status | **RESOLVED 2026-06-01** — ADR-0006 accepted; `max_concurrent_positions` deleted from `_HARD_LIMITS`; CHECK 3 removed from `risk.py`; `current_open_positions` parameter removed from interface; 2 tests rewritten; VPS deploy pending |

---

### GG-002 — T1–T5 execution tier architecture required multiple sessions to implement correctly

| Field | Detail |
|---|---|
| Gap ID | GG-002 |
| Category | Incremental architecture without coherence checkpoints |
| What was missed | The T1–T5 time-horizon execution band framework was conceptually adopted as a governing architectural principle but was implemented piecemeal across multiple sessions without a coherence checkpoint confirming the risk framework had been updated to match. ExecutionBands (T-084), multi-band orchestrator (T-084), band-specific Kelly fractions, and dual-window cron were all built — but the risk framework they operate within (C4) retained a G4-era stub that was designed for a single-band, 10-player system. |
| When it should have been caught | At the end of any session that completed a major Phase 7 build (T-083, T-084) — when the scope of the execution architecture had clearly grown past the risk framework |
| Phases it survived | Phase 7 build (2026-05-29) through G7 run (2026-05-31) |
| Why it survived | No architectural coherence checkpoint existed. Session handoffs captured "tasks completed" but not "which G4 assumptions are now potentially stale given what we just built?" The mid-session checkpoint protocol (MEMORY_BANK.md) does not ask whether upstream risk limits are still valid for the components just deployed. |
| Impact | The system ran the first real game (NBA Finals G1, 2026-05-31) with an execution architecture designed for thousands of trades per season but a risk gate designed for 10 concurrent positions. The misalignment was structurally undetectable without operator review. |
| Discovery | Same session as GG-001 — operator identified the execution/risk coherence gap during GG-001 remediation discussion |
| Resolution | ADR-0006 (GG-001 resolution covers this). ARE WE COMPROMISED? check added to MEMORY_BANK.md session-start protocol to catch future coherence gaps. |
| Status | **RESOLVED 2026-06-01** — Root cause addressed by ADR-0006 + ARE WE COMPROMISED? watchdog |

---

### GG-003 — No automatic detection for "architecture outgrew its constraints"

| Field | Detail |
|---|---|
| Gap ID | GG-003 |
| Category | Systemic governance blind spot |
| What was missed | The governance system — ADRs, DECISION_LOG, gate reviews, session handoffs — was designed to prevent re-litigating resolved decisions and ensure new decisions were logged. It was not designed to detect the case where a correctly-made early decision becomes *wrong* because the system architecture grew past the assumptions that underpinned it. This is a distinct failure class from context rot (undocumented decisions) or scope creep (unauthorized changes). It is architectural coherence drift. |
| When it should have been caught | This is a structural gap — it predates any specific incident. The prior iteration failed to context rot; the mitigation (Compass OS) was thorough on decision documentation but created no mechanism to revisit early decisions when the architecture changed. |
| Impact | GG-001 and GG-002 are symptoms of this systemic gap. Any value in `_HARD_LIMITS`, any threshold in RISK_APPETITE_CONSTRAINTS.md, any ADR from G0–G4 is potentially stale if the architecture changed significantly after it was written. Without GG-003's mitigation, future versions of this gap will recur. |
| Discovery | 2026-06-01 operator escalation: "there is nothing in the system that would have caught this without manual review" |
| Resolution | ADR-0007: mandates GOVERNANCE_GAP_LOG.md as a required artifact. ARE WE COMPROMISED? check (MEMORY_BANK.md): 5-question strategic integrity check at session start. T-103: code stub scan added to session-start protocol. |
| Status | **RESOLVED 2026-06-01** — ADR-0007 accepted; watchdog protocol added to MEMORY_BANK.md |

---

### GG-004 — EV Validation Benchmark Was Never the Commercial Question

| Field | Detail |
|---|---|
| Gap ID | GG-004 |
| Category | Systemic research blind spot |
| What was missed | All 16 experiments in this project computed edge and EV using `mip = 0.50` as the market implied probability. The research process validated "does the model beat a coin flip?" — not "does the model beat an informed Kalshi market?" The commercial question the project is built to answer was never posed as an experiment. EXP-004 Part B and EXP-010 Part B used live prices but only as a 2-player spot check on a single day. This is not statistical validation. |
| When it should have been caught | G4 Evidence Gate (2026-05-28) — when the EV figure (+$0.0858/bet) was accepted as gate evidence. The gate question should have been "what is the benchmark for this EV figure?" It was not asked. |
| Phases it survived | G4 → G5 → G6 (all gate reviews) |
| Why it survived | Gate reviews asked "is the EV positive?" not "is the EV positive against the right benchmark?" The distinction between `mip=0.50` and `mip=kalshi_market_price` was not part of any experiment design checklist or gate criterion. No governance artifact asked: "what market are we competing against?" |
| Impact | The core commercial claim — model generates positive EV against real Kalshi prices — is unvalidated. Paper trading (Phase 6) is accumulating real-world evidence, but 30 bets is insufficient for statistical confidence and variance is high. If EXP-017 shows the model does NOT beat real prices, G6 gate cannot be cleared. |
| Discovery | 2026-06-01 — new terminal session review of run_exp010.py:164; operator escalation in session convergence |
| Discovery method | Code review by fresh model instance following CLAUDE.md session-start protocol. Human operator confirmed significance. |
| Resolution | EXP-017: backtest edge against actual historical Kalshi prices. OQ-023 registered. T-105 registered. |
| Status | OPEN — 2026-06-01; EXP-017 registered; blocks G6 confidence clearance |

---

### GG-005 — Gate criteria dimensional coherence was never audited by ARE WE COMPROMISED? (Q1–Q6)

| Field | Detail |
|---|---|
| Gap ID | GG-005 |
| Category | Systemic governance blind spot — wrong dimension, not wrong value |
| What was missed | ARE WE COMPROMISED? Q1–Q6 audits code artifacts: hard limits in risk.py, stubs in src/, interface signatures, decision traceability. No question asked: "for each active gate criterion, what broken system could produce passing evidence?" APR-0016 ("30 resolved bets with positive P&L") survived from 2026-05-29 to 2026-05-31 without any protocol step asking whether count was the right primary metric. The 2026-05-31 corrective entry fixed the throughput math (4 bets/day → 17-40+ bets/night) but missed the structural issue: count is categorically the wrong dimension regardless of the throughput number. |
| When it should have been caught | When APR-0016 was written (2026-05-29) — the same session that included a multi-band, 80-player execution architecture discussion. Or at the latest when ADR-0006 deleted the count gate from C4 (2026-06-01), making the dimensional incoherence explicit: if count is wrong in C4, count is wrong in G6. |
| Phases it survived | G6 paper trading phase (2026-05-29 through 2026-05-31) |
| Why it survived | Q1–Q5 audit code and numerical values. No question in the protocol asked: "Is the gate criterion measuring the right dimension?" The distinction between "wrong value" (e.g., 10 for max_concurrent_positions) and "wrong dimension" (e.g., count as a gate metric) was not part of any scan, template, or prompt. Count looks like a reasonable metric until you ask what broken system passes it. |
| Impact | APR-0016 would have allowed G6 live capital promotion based on one lucky game night's bets (30+ bets at Finals throughput). A miscalibrated model with execution bugs producing one lucky variance run would have cleared G6. No calibration evidence required. No commercial validation required. No execution integrity required. |
| Discovery | Operator review 2026-05-31. Earl identified that count is the wrong primary metric — the same conceptual insight that produced ADR-0006 (count wrong in C4) applied to G6. Human synthesis connected these two; no automated scan would have. |
| Discovery method | Human eye test — NOT caught by any protocol step |
| Resolution | Q7 added to ARE WE COMPROMISED? in CLAUDE.md and MEMORY_BANK.md. APR-0017 drafted 2026-06-01: 4-tier sequential evidence standard (Tier 0 commercial preconditions, Tier 1 execution integrity, Tier 2 model performance trends, Tier 3 risk control validation). Statistical floor ≥50 resolved bets + ≥5 game nights. Each criterion includes broken-system test. T0-B already met (T-114). |
| Status | **RESOLVED 2026-06-01** — APR-0017 v2 ACCEPTED (PO/DS sign-off 2026-06-01). Q7 protocol established. APR-0016 superseded. |

---

### GG-006 — Kalshi TOS Automated Trading Review Incomplete: Position Accountability Limits Not Reflected in risk.py

| Field | Detail |
|---|---|
| Gap ID | GG-006 |
| Category | Venue risk / regulatory compliance |
| What was missed | ADR-0003 reviewed Kalshi's regulatory status (CFTC-DCM regulated, all 50 states, NBA markets confirmed). It did not review Kalshi's operational terms for automated/algorithmic participants — specifically: (1) API Developer Agreement restrictions on automation, (2) rate limits and whether they permit hundreds of orders/game night, (3) CFTC/Kalshi Rulebook position accountability limits that may restrict per-event or per-market concentration. No governance artifact asked "does Kalshi permit a bot that places 100-300+ orders/night on NBA player prop markets?" before paper trading began. |
| When it should have been caught | ADR-0003 (2026-05-23) — venue selection ADR. When Kalshi was selected as primary venue, the operational terms for automated participants should have been part of the acceptance criteria. |
| Phases it survived | ADR-0003 acceptance (2026-05-23) through Sessions 1-8 (2026-06-01). All paper trading sessions ran without this check. |
| Why it survived | ADR-0003 framed Kalshi selection around regulatory status (CFTC-regulated = legitimate) and market availability (NBA player props exist). It did not frame the question as: "is our specific usage pattern — a bot placing hundreds of automated orders per game night — within Kalshi's operational terms?" THREAT_MODEL.md does not include TOS violation as a threat (TH-01 through TH-09). |
| Impact | If Kalshi's position accountability limits or participant conduct rules restrict automated bot volume and this is discovered post-live-capital deployment, cessation is immediate and retroactive. Paper trading is lower risk (no real capital); the urgency is highest at G6 live capital authorization. |
| Discovery | PDTP analysis 2026-06-01 (Session 8) — identified as an ungated HIGH-severity risk not in any document. Registered same session per protocol. |
| Discovery method | Strategic analysis — NOT caught by any automated scan |
| Partial resolution (2026-06-01) | TOS review partially completed via web search + API docs: (1) **Automated/bot trading: EXPLICITLY PERMITTED** — Kalshi provides API specifically for programmatic trading; no special tier, waitlist, or approval needed. Any account in good standing can generate API credentials and trade algorithmically. (2) **Rate limits compatible with throughput**: Basic tier = 100 write tokens/sec; each order costs 10 tokens = 10 orders/sec. 300 bets in a single PIPE-03 run takes ~30 seconds — well within limits. (3) **Prohibited conduct**: market manipulation, wash trading, spoofing, self-matching across accounts — behavioral restrictions, not automation restrictions. (4) **Self-trading requirement**: must use own account + own API keys; no pooling funds — Earl's use case is compliant. (5) **March 2026 restriction**: no bets by anyone directly involved in NBA operations — not applicable to Earl. (6) **Position accountability limits (Kalshi Rulebook): UNVERIFIED** — CFTC PDF was unreadable; rulebook section titled "Position Accountability" suggests per-event or per-market concentration limits exist. These are not reflected in `_HARD_LIMITS` in risk.py. |
| Rulebook review complete (2026-06-01) | DCM Rulebook v1.26 (82pp) and DCO Rulebook v1.4 (108pp) read in full. Key findings: (1) **Definitions**: "Position Accountability Level" = the level of LOSS above which Kalshi may impose disclosure/reduction obligations (SOFT threshold). "Position Limit" = the maximum LOSS allowed per position per Contract (HARD cap). Both are denominated in dollar-loss terms, not contract counts or notional size. (2) **Rule 5.18 (Position Accountability)**: All contracts have PALs; each PAL is specified in the contract's individual Terms and Conditions — NOT in the main rulebook body. Exceeding PAL → required disclosure to Kalshi Compliance; must reduce if instructed. (3) **Rule 5.19 (Position Limits)**: Hard cap per contract. Also specified in each contract's Terms and Conditions. First violation = warning letter; subsequent within 12 months = formal proceedings. Rule 5.19(h): "In no instance may a Trader's position exceed any applicable limit established by the CFTC." (4) **Rule 5.4(a)(a)/(d)**: Exchange-level order rate limiter explicitly anticipated; automated order submissions are standard operating mode. Automated participants must maintain "adequate controls to prevent excessive messaging." Our rate-limiting architecture satisfies this. (5) **Chapter 4 Market Makers**: Market Makers get 10× PAL and Position Limit exemptions. Earl is NOT a Market Maker — standard participant rules apply. (6) **DCO Rule 7.5 Fully Collateralized**: Members must maintain deposited funds to cover Maximum Downside Exposure at all times. Clearing house will not clear positions exceeding deposited funds. This means account balance ($683.41) IS the effective position ceiling before any regulatory PAL is relevant. (7) **CRITICAL FINDING**: The main DCM Rulebook 1.26 does NOT contain any numerical PAL or Position Limit values for any contract. The actual numbers are in each individual contract's Terms and Conditions on the Kalshi website. KXNBAPTS contract's Terms and Conditions page is the authoritative source. |
| Remaining open risk | Specific numerical PAL and Position Limit for KXNBAPTS (NBA player points) contracts — in per-contract Terms and Conditions on Kalshi website, not in main rulebook. Three structural factors substantially bound this risk at current paper trading scale: (1) Fully Collateralized rule: max exposure = deposited balance ($683.41); (2) risk.py `max_bet_usd: 500` cap; (3) quarter-Kelly at current bankroll produces typical bets of $10–80/market. Any reasonable per-participant PAL on an NBA player prop market will be far above $80. Risk is LOW now; grows materially with bankroll post-G6. |
| Resolution path | T-117 (HIGH — Week 1 dark period, by 2026-06-30): two formal document readings required — (1) **Kalshi Participant Agreement** (account-level TOS; prior review was informal web search; formal document must be read for ADR-0005 sign-off); (2) **KXNBAPTS contract Terms and Conditions** on Kalshi website for numerical PAL and Position Limit values. If limits above $500, no risk.py changes required. If limits below $500, add `max_position_usd_per_market` to `_HARD_LIMITS` via ADR. Both required before G6 ADR-0005 draft. |
| Status | SUBSTANTIALLY RESOLVED — pending T-117 (two formal document readings) — 2026-06-01 SESSION 11. Automated trading: CONFIRMED PERMITTED. Rate limits: CONFIRMED COMPATIBLE. Position accountability framework: FULLY UNDERSTOOD from rulebook review. KXNBAPTS numerical PAL/Position Limit: NOT IN MAIN RULEBOOK — in per-contract Terms. Participant Agreement: reviewed informally only — formal read required for ADR-0005. Must fully close before G6 live capital authorization (ADR-0005). Timeline: Week 1 dark period (by 2026-06-30). |

---

### GG-007 — T4/T5 Threshold Constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) Are Uncalibrated Skeleton Values

| Field | Detail |
|---|---|
| Gap ID | GG-007 |
| Category | Architectural placeholder — Phase 8 pre-activation gate |
| What was missed | `T4_MIN_DELTA_P = 0.08`, `T5_YES_CERTAINTY = 0.85`, `T5_NO_CERTAINTY = 0.15` were adopted as Phase 7 skeleton constants without empirical calibration against real in-play data. The SESSION 12 DECISION_LOG entry for T4_MIN_DELTA_P explicitly states: "must be calibrated against real in-play data before T4 ACTIVE designation — this value is a Phase 7 skeleton constant, not a validated production threshold." The governance gap is that no experiment is registered to perform this calibration, and no Phase 8 activation gate blocks on it. |
| When it should have been caught | Phase 8 infrastructure ADR — the third of the three Phase 8 blocker ADRs must include threshold calibration as a pre-activation gate |
| Phases it survived | Phase 7 skeleton (by design) — gap is forward-looking, not retroactive |
| Why it survived | Phase 7 correctly deferred calibration to Phase 8. Gap: no experiment was registered at Phase 7 build time to close it. Without a registered experiment, Phase 8 activation could proceed with the skeleton constants intact. |
| Impact | Uncalibrated `T4_MIN_DELTA_P` may be too loose (false fires on marginal signals) or too tight (misses genuine T4 edge). Uncalibrated T5 certainty bounds may trigger on near-certainty that isn't structurally certain given late-game variance. Either error direction produces realized EV below the model's estimate at live capital. |
| Discovery | ARE WE COMPROMISED? review of game_state_model.py — 2026-06-02 |
| Resolution | Register EXP-018 (T4_MIN_DELTA_P calibration against historical in-play score sequences) and EXP-019 (T5 certainty threshold calibration in final-3-minute game segments). Both must PASS before Phase 8 T4 activation ADR is signed. Threshold revision requires ADR amendment if materially different from skeleton values. T-128 registered. |
| Status | OPEN — LOW severity now (T4/T5 not active); HIGH severity pre-Phase 8 activation |

---

### GG-008 — All-threshold loop uses player-level p_model; `kalshi_threshold` absent from C3 feature vector — phantom edge on extreme thresholds

| Field | Detail |
|---|---|
| Gap ID | GG-008 |
| Category | Architectural misspecification — model feature gap |
| What was missed | `run_paper_trade.py` (T-115 implementation) computes `p_est` once per player from 78 player-level features. `kalshi_threshold` is NOT in the feature vector. The same `p_est` is then compared against market implied probability for EVERY Kalshi threshold listed for that player. For extreme thresholds (far from player's pts_l10_mean), the market prices them correctly via Poisson(pts_l10_mean) — e.g., KAT YES 25 ≈ 16.8¢ — but the model returns p_est ≈ 0.47–0.57 regardless of threshold, creating apparent edges of 30–50¢ that don't exist. Only positions within ±~3pt of pts_l10_mean have calibrated edge (ADR-0004 ECE=0.034 applies). All other threshold positions have phantom edge. |
| When it should have been caught | T-115 decision (2026-06-01) — when the all-threshold loop was designed. The loop was engineered for evidence volume throughput, but the feature alignment question ("does the model output a threshold-specific probability?") was not asked before enabling multi-threshold bet sizing. |
| Phases it survived | T-115 landed SESSION 11 (2026-06-01); survived through SESSION 13 (2026-06-02). First live evidence is Finals G1 (Jun 3, 2026) — portfolio already deployed. |
| Why it survived | ARE WE COMPROMISED? checks hard limits, stubs, interface evolution, and threshold traceability. It does not ask: "for every loop over market objects, does the model output a signal specific to the loop variable?" Feature-variable alignment was not a protocol check item. |
| Impact | Monte Carlo (50,000 runs, Poisson(pts_l10_mean) ground truth, Jun 3 Finals G1 portfolio of 25 positions / $911.53 staked): **expected P&L -$528 (-58%); win rate 6.4%; P50 -$634.** 24 of 25 positions have negative expected P&L under Poisson pricing. KAT YES 20 (threshold ≈ mean) is the only position with genuine positive EV (+$14). Phantom edge inflates paper stake on extreme threshold positions (e.g., KAT NO 10: $97 staked; Fox YES 25: $92 staked). G6 evidence quality is degraded while this misspecification is active. |
| Discovery | Monte Carlo pre-Finals portfolio assessment, SESSION 13 (2026-06-02). Back-solving from Kelly inverse formula confirmed p_est is player-level only. VPS `prod_model.joblib` feature names inspected: 78 features, `kalshi_threshold` absent from all. Poisson CDF cross-check: Kalshi market prices for extreme thresholds match Poisson(pts_l10_mean) closely; model prices diverge. |
| Resolution | T-129 registered. Two candidate fix paths (operator decision required): **(A)** Add `kalshi_threshold` (normalized) as a C3 feature → requires model retrain; blocked until T-072 (Oct 2026). **(B)** Replace `p_est` at each threshold with `Poisson_CDF(threshold, pts_l10_mean)` in the all-threshold loop — immediate fix, no retrain; architecturally correct for threshold-specific markets; edge = P(score ≥ threshold) - market_price. Path B is implementable before Finals G2 (Jun 5). T4's GameStateModel already uses this approach correctly. |
| Status | RESOLVED — 2026-06-02 SESSION 14. Path B implemented in `run_paper_trade.py` (T-129). `p_est` (player-level LR) replaced with `Poisson_CDF(threshold, pts_l10_mean)` per threshold in the all-threshold loop. `p_est` retained in `forecast_rec` as `p_estimate_lr` for C6 logging. `_poisson_cdf` imported from `game_state_model` (same function T4 uses). No retrain required. Path A (add threshold as feature + retrain) deferred to T-072 (Oct 2026). G1 portfolio (25 positions / $911.53) already tainted — wiped and reset to $1,000 before Finals G1 cron (Jun 3 22:00 UTC). GG-008 closed. |

---

### GG-009 — Taker Fee Absent From Edge Formula: MIN_EDGE=0.02 Does Not Cover Kalshi Taker Cost

| Field | Detail |
|---|---|
| Gap ID | GG-009 |
| Category | Architectural misspecification — fee not in edge gate |
| What was missed | `MIN_EDGE_TO_APPROVE = 0.02` in `risk.py` does not include Kalshi taker fees. Kalshi taker fee formula: `0.07 × P × (1−P)` per contract. At P=0.50 (typical market): taker fee = $0.0175/contract. At a bet sized at 1 contract ($0.50 stake), fee = $0.0175 = 87% of the total edge approved by MIN_EDGE=0.02. The bot may be systematically approving and placing bets where the net-of-fee EV is negative even when gross edge is positive. This applies immediately to paper T4 flat 1-contract bets (SESSION 23) and to T1 bets at small Kelly sizes. |
| When it should have been caught | EXP-017 Part A design (2026-06-01) — when edge formula was used to evaluate EV. Or any session that computed fee structure from Kalshi docs. |
| Phases it survived | G4 → G5 → paper trading phase → SESSION 22/23 |
| Why it survived | No governance artifact asked "does the edge gate account for transaction costs?" GG-004 asked whether EV is positive vs real prices — but not whether the fee structure is included in the edge gate itself. The Kalshi fee formula was first sourced in SESSION 22 (2026-06-03) via web search — fee was never in any prior design doc. |
| Impact | At $0.50 market, taker fee = $0.0175. MIN_EDGE = 0.02. Net fee-adjusted edge threshold = 0.0025 (12.5% of nominal edge). Bets at 50¢ market approved at MIN_EDGE=0.02 have an expected fee cost that is 87% of gross edge. This is architecturally serious: the bot may be betting with essentially zero or negative fee-adjusted edge at the current threshold. Maker orders (fee = 0.25× taker = $0.004375 at 50¢) are more favorable but require limit order infrastructure (not yet built). |
| Discovery | SESSION 22 (2026-06-03) — Kalshi operational constraints research. Fee formula sourced from Kalshi API docs: `fee = 0.07 × P × (1-P)` taker; `fee = 0.0175 × P × (1-P)` maker. Calculation: at P=0.50, taker fee = $0.0175 vs MIN_EDGE=0.02 gross. |
| Resolution | Three options: (1) **Raise MIN_EDGE**: set `MIN_EDGE = 0.02 + fee_at_50c = 0.0375` (a ~2× increase — materially reduces approved bets); (2) **Fee-adjusted edge gate**: `net_edge = gross_edge - fee(mip)` where `fee(mip) = 0.07 × mip × (1−mip)` — approved only if `net_edge >= MIN_EDGE`; (3) **Maker-first policy**: place as limit (maker) order at MIP, reducing fee 4×. Requires limit order infrastructure. **Resolution requires ADR** (changes to MIN_EDGE or edge formula are architectural). Register T-131. Block on before G6 (EXP-017 EV figures without fee correction are overstated). |
| Status | **RESOLVED — 2026-06-04 SESSION 30** — ADR-0016 ACCEPTED: `net_edge = gross_edge - 0.07 × mid × (1-mid)`; fee-negative bets rejected at edge gate; `fee_contaminated` position flag (SESSION 25) logically always False for new bets post-ADR-0016; GG-009 closed |

---

### GG-010 — T5 Band Budget Shares T4 Allocation: T4 Depletion Can Starve T5 Firing Window

| Field | Detail |
|---|---|
| Gap ID | GG-010 |
| Category | Architectural note — shared in-play budget; resolved by design intent |
| What was missed | `run_t4_live.py` passes the same `t4_band_budget` to both T4 and T5 RiskEngine calls. Concern was T4 depleting budget before T5's Q4 firing window. |
| When it should have been caught | ADR-0013 design. |
| Phases it survived | ADR-0013 ACCEPTED 2026-06-02 → SESSION 22/23 paper validation |
| Why it survived | T5 was SKELETON; the shared budget was implicit. |
| Impact | Under correct validity-math calibration: T5's arithmetic certainty gate is strict (p ≥ 0.85, final 3 min only) — T5 events are infrequent enough that T4 budget depletion before a T5 window is not a realistic scenario. If T4 IS depleting before T5 fires, the root cause is T4_MIN_DELTA_P miscalibration (T4 firing too aggressively), not a budget allocation design flaw. Fix is EXP-018 (T4_MIN_DELTA_P calibration), not a separate T5 budget. |
| Discovery | 2026-06-03 SESSION 23 — ADR-0014 T-130. |
| Resolution | **DS decision 2026-06-03 SESSION 23:** No dedicated band budgets. Bands are bucket filters with independent kill switches and specific validity math. Shared budget is correct; per-band kill switches prevent runaway. If T5 is starved, that indicates T4 validity math is miscalibrated — fix EXP-018, not the budget architecture. ADR-0014 Q2 resolved: Option A (shared, current) is design intent, not a fallback. |
| Status | RESOLVED — 2026-06-03 SESSION 23; DS decision: no dedicated band budgets; shared budget + per-band kill switches is the correct architecture |

---

### GG-011 — T4_BAND_WEIGHT Fractional-Allocation Formula Incompatible with High-Throughput T4

| Field | Detail |
|---|---|
| Gap ID | GG-011 |
| Category | Architectural — T4 sizing model unfit for high-throughput operation |
| What was missed | `T4_BAND_WEIGHT` assumes `t4_band_budget = bankroll × (1−RESERVE_MANDATE_PCT) × T4_BAND_WEIGHT`. At KELLY_T4=0.20 and ~1,434 evaluations/game with avg edge=0.305, uncapped Kelly deployment = $81,226 across one game — 87× any reasonable band budget. The budget exhausts after ~12 bets, leaving 1,400+ evaluations unfunded. The formula is valid only if T4 fires 10–20 bets/game (pre-ADR-0006 count-gate era), not at design-intent throughput. |
| When it should have been caught | ADR-0013 design (2026-06-02 SESSION 20) when T4_BAND_WEIGHT was first introduced as a stub. |
| Phases it survived | ADR-0013 ACCEPTED 2026-06-02 → G1 paper execution 2026-06-03 |
| Why it survived | G1 ran PAPER_T4_FLAT_SIZING=true which overrides the formula via PAPER_T4_POOL_USD. The stub was never exercised in production — paper mode bypasses it. Calibration script `run_t4_budget_sim.py` requires PAPER_T4_VIRTUAL=true data; G1 ran non-virtual so calibration was never attempted. |
| Impact | LOW now — paper mode overrides T4_BAND_WEIGHT via PAPER_T4_POOL_USD; stub not active in any current execution path. HIGH before T4 ACTIVE: live mode uses `_compute_t4_band_budget()` which applies the formula. If activated with current formula, T4 depletes its entire band budget in ~12 bets and goes dark for the remaining 1,400+ evaluations per game. |
| Discovery | 2026-06-04 SESSION 28 — G1 calibration attempt. Calibration script returned "No T4 VIRTUAL fires found." Manual analysis of audit_t4.jsonl: 1434 approved bets × avg approved_size=$56.64 = $81,226 uncapped Kelly deployment. |
| Resolution | **OPEN** — new ADR required to specify per-evaluation sizing for high-throughput T4. Options: (1) per-evaluation budget normalization: `bet_size = edge × KELLY_T4 × (band_budget / expected_bets_per_game)` — each bet gets a budget slice; (2) fixed per-contract sizing (current paper approach) extended to live; (3) dynamic budget refresh per quarter. None of these are validated. Gate: resolve before T4 ACTIVE designation. |
| Status | OPEN — 2026-06-04 SESSION 28; LOW severity now (paper mode bypasses formula); HIGH severity before T4 ACTIVE designation |

---

### GG-012 — PIPE-02 Silently Failed Due to BOT_C4_ACTIVE Guard: ADR-0015 adj_λ Never Applied to Live PIPE-03 Runs

| Field | Detail |
|---|---|
| Gap ID | GG-012 |
| Category | Pipeline integrity — silent failure, no alert, governance-invisible |
| What was missed | `run_pregame.py` contained a guard: `if os.environ.get("BOT_C4_ACTIVE"): sys.exit(1)`. The `.env` file on VPS has `BOT_C4_ACTIVE=true` (set for PIPE-03 live execution). The cron for PIPE-02 sources `.env` via `export $(grep -v '^#' .env | xargs)` before running, loading `BOT_C4_ACTIVE=true`. Result: PIPE-02 exits immediately at startup with "FATAL: BOT_C4_ACTIVE is set" — writes nothing to disk. The guard was written as a manual safety check (don't run PIPE-02 in a live shell where orders might fire). It should never have applied to the automated cron, which uses a separate `.env` sourcing step. |
| When it should have been caught | When ADR-0015 was deployed and `BOT_C4_ACTIVE=true` was already in `.env` — a sanity check of the cron environment should have caught this. Alternatively: when the G2 bet log shows `[TSS] Cache miss — building fresh team stats store... 0/30 teams loaded`, this should have triggered an alert. It did not because no PIPE-03 monitoring watches for TeamStatsStore size = 0. |
| Phases it survived | PIPE-02 failed at 21:55 UTC Jun 3 (G2 pregame attempt) and 21:55 UTC Jun 4 (G2 pregame retry). 2 consecutive cron cycles, 0 alerts. The paper_early_cron.log had the evidence (`0/30 teams loaded`) but no monitoring process read it. |
| Why it survived | (1) The guard was written for a different use context (manual interactive safety) and was never reviewed for cron compatibility. (2) No monitoring checks whether PIPE-02 succeeded before PIPE-03 fires. (3) No alert fires when TeamStatsStore loads 0 teams — PIPE-03 treats it as a graceful fallback (raw pts_mean), not an error. (4) PIPE-03's log line "Cache miss — building fresh... 0/30 teams" looks like a recoverable condition, not a signal that an upstream dependency entirely failed. |
| Impact | (1) **ADR-0015 adj_λ was never applied to any G2 bet.** All 9 G2 paper positions use unadjusted Poisson λ (raw `pts_l10_mean`). (2) **EXP-018 cannot validate ADR-0015 commercial correction.** G2 outcomes will tell us whether unadjusted Poisson beats market prices — not whether opponent adjustment improves over unadjusted. The experiment design is broken for this game. (3) **PIPE-02 late window (01:25 UTC Jun 5) will also fail** unless the fix is deployed before that window. |
| Discovery | 2026-06-04 SESSION 31 — timing sweep + MC investigation. `[TSS] Built fresh: 0/30 teams loaded` in paper_early_cron.log. Cross-referenced with pregame file listing: no `pregame_20260604.json`. Cross-referenced with pregame_cron.log: two FATAL exits at end. Cross-referenced `.env`: `BOT_C4_ACTIVE=true` at line 23. |
| Resolution | Removed `BOT_C4_ACTIVE` guard from `run_pregame.py __main__`. Updated docstring. PIPE-02 now runs unconditionally — it is read-only by design and should not be blocked by C4 activation state. 715/715 tests. T-134 registered for monitoring task: add alert when TeamStatsStore loads 0 teams in PIPE-03. EXP-018 analysis note: G2 bets are valid (positive directional edge at unadjusted λ) but do not test ADR-0015. ADR-0015 validation deferred to a future game night where PIPE-02 succeeds before PIPE-03 runs. |
| Status | RESOLVED — 2026-06-05 SESSION 32. PIPE-02 ran at 01:25 UTC Jun 5 (`pregame_20260605.json` confirmed). T-134 (monitoring alert for TSS size=0) remains OPEN under TODO_NEXT. TSS 0/30 continues but for a different root cause registered as GG-013 (NBA API blocked from VPS IP). EXP-018 evidence is baseline Poisson vs. market, not ADR-0015 validation. |

---

### GG-013 — NBA Stats API Blocked from VPS: ADR-0015 adj_λ Has Never Applied to Any Live Run

| Field | Detail |
|---|---|
| Gap ID | GG-013 |
| Category | Data source integrity — deployment environment incompatibility |
| What was missed | The NBA Stats API (stats.nba.com) is protected by Akamai CDN, which identifies and blocks requests from DigitalOcean datacenter IPs. All `TeamGameLog` requests from VPS 157.230.91.33 return an empty HTTP response body. `nba_api` raises `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` for every team. Result: `TeamStatsStore` loads 0/30 teams for every run. `opp_adjusted_lambda()` silently returns raw `pts_l10_mean` (line 202: `if opp_def is None: return pts_mean`). The fallback is correct behavior, but no alert fires and no audit event distinguishes "TSS empty because PIPE-02 failed" from "TSS empty because API is blocked." |
| When it should have been caught | When ADR-0015 was drafted and the VPS IP class was not checked against stats.nba.com access patterns. Alternatively: first PIPE-02 deployment (Jun 4 22:00 UTC) — the `[TSS] Team stats store: 0/30 teams loaded` message should have triggered investigation before running PIPE-03. |
| Phases it survived | All PIPE-02/PIPE-03 runs since Jun 4 22:00 UTC (first TSS build attempt). 0 successful team fetches across 90 attempts (3 TSS build cycles × 30 teams). |
| Why it survived | (1) GG-012 was the working hypothesis for TSS 0/30 — once the BOT_C4_ACTIVE fix was applied, it appeared the TSS issue would self-resolve. (2) No session verified TSS success after the fix. (3) The `team_stats_cache_{date}.json = {}` file was not checked until SESSION 32. (4) No monitoring alerts on TSS success/failure rate. |
| Impact | ADR-0015 (`adj_λ = pts_l10_mean × clip(opp_def_l10/113.0, 0.70, 1.30)`) has **never been applied to any live PIPE-03 bet** since deployment. All paper bets use unadjusted Poisson λ. EXP-018 (which was registered as "ADR-0015 validation") will actually measure unadjusted Poisson vs. market — a different question. ADR-0015's claimed improvement in EV cannot be validated until the API block is resolved. LOW severity now (paper period; unadjusted λ is the training baseline). HIGH severity pre-G6: ADR-0015 must be validated before live capital. |
| Discovery | 2026-06-05 SESSION 32 — `team_stats_cache_20260605.json = {}`. Audit log confirmed 90 fetch errors, 0 successes, all with error `"Expecting value: line 1 column 1 (char 0)"`. Manual VPS test: both `season_type="Regular Season"` and `season_type="Playoffs"` return `ok=False, rows=0` for SAS and all other teams. |
| Resolution | **RESOLVED — 2026-06-05 SESSION 32/33.** stats.nba.com blocked from both VPS (DigitalOcean ASN 14061, HTTP 403) AND GitHub Actions (Azure, connection timeout). nba_api approach abandoned. Switched to ESPN scoreboard API (site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard) — confirmed unblocked from all environments. 60-day lookback, 60 sequential calls, ~3s total. Adds ESPN→NBA abbreviation normalization (GS→GSW, NY→NYK, SA→SAS, NO→NOP, UTAH→UTA, WSH→WAS). End-to-end verified: GitHub Actions run 27021048445 completed in 25s, wrote 30 teams / 279 game-records, SCP'd `team_stats_cache_20260605.json` to VPS. File confirmed on VPS (22254 bytes, 14:33 UTC). NYK: 18 games, SAS: 22 games including Finals G1 (NYK 105, SAS 95). VPS_SSH_KEY secret pre-configured in prior run; no further one-time setup needed. |
| Status | **RESOLVED — 2026-06-05 SESSION 33.** Daily GHA cron at 20:30 UTC (T-137: moved from 00:30 UTC to align GAME_DATE with PIPE-02 early cron at 21:55 UTC — see GG-015). First game-day run will deliver pre-populated cache to VPS before PIPE-02 at 21:55 UTC. ADR-0015 adj_λ will apply to next game day's bets. |

---

### GG-014 — Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode

| Field | Detail |
|---|---|
| Gap ID | GG-014 |
| Category | Execution integrity — rate limit characterization missing |
| What was missed | Kalshi's order placement API rate limits were not characterized before PIPE-03 was activated for multi-market execution. With 25+ bets per game night executing within a ~2 second burst window, Kalshi's `/portfolio/orders` endpoint returns HTTP 429 (Too Many Requests) for roughly 50% of calls. Paper mode logs positions regardless (portfolio write is local; the Kalshi API call is best-effort for order confirmation), so paper P&L tracking is unaffected. No retry logic exists. At live capital, these would be real execution failures — the bot would have C4-approved edge and model signal but fail to deploy capital for ~50% of intended bets. |
| When it should have been caught | Before PIPE-03 first activation; the Kalshi API rate limits should have been verified against the expected burst sizing (~25 orders in ~2s) before any live-mode execution ran. |
| Phases it survived | All PIPE-03 runs since Jun 4 22:00 UTC. 12 of 25 G3 positions have `kalshi_order_status: "failed: HTTP 429"`. |
| Why it survived | (1) Paper mode masks the severity — portfolio state is correct regardless of API status. (2) No monitoring alert fires on 429 response patterns. (3) The first game nights had fewer concurrent markets (Finals structure: 1 game/night, ~25 bets) — at regular season scale (400+ markets/night) the failure rate would likely be higher. |
| Impact | LOW now (paper mode; P&L unaffected). HIGH pre-G6: live capital execution failures for ~50% of approved bets means approximately half the model's edge is never deployed. Risk-adjusted return would be materially lower than paper period suggests. Also possible: systematic bias if 429 failures are not random (e.g., later bets in the burst are more likely to fail, meaning low-threshold / high-probability bets fail more often). |
| Discovery | 2026-06-05 SESSION 32 — `paper_portfolio.json` review: 12/25 open positions have `kalshi_order_status: "failed: HTTP 429"`. |
| Resolution | **PARTIAL — 2026-06-05 SESSION 33 (T-136).** Option (1) implemented: `time.sleep(0.5)` added in `paper_trader.py` after each Kalshi order submission. Reduces burst rate from ~12 req/s to ~2 req/s. Effectiveness unverified until next game-night run (Finals G2, 00:30 UTC Jun 6). If 429s persist, next step is exponential backoff retry (option 2). Characterizing Kalshi's exact rate limit tier is TBD. Gate: must verify ≤5% execution failure rate before G6. |
| Status | PARTIAL — 2026-06-05 SESSION 33; sleep(0.5) fix deployed; effectiveness confirmed after Finals G2 cron run |

---

### GG-015 — GHA Cache Timing Gap: adj_λ Cache GAME_DATE Mismatch Between GHA Run and PIPE-02 Early Cron

| Field | Detail |
|---|---|
| Gap ID | GG-015 |
| Category | Architectural timing — deployment environment mismatch |
| What was missed | `GAME_DATE` in `run_pregame.py` is computed as `datetime.now(utc).strftime("%Y%m%d")`. At PIPE-02 early cron time (21:55 UTC, day N), GAME_DATE=N. The GHA workflow was scheduled at 00:30 UTC (day N+1), which also computes GAME_DATE=N+1. The GHA cache is `team_stats_cache_{N+1}.json`; PIPE-02 looks for `team_stats_cache_{N}.json`. **They never matched.** adj_λ was structurally unreachable for the early cron on every game day, even after GG-013 was resolved. |
| When it should have been caught | When the GHA workflow was initially scheduled (SESSION 32). The cron time was set to 00:30 UTC by convention without verifying GAME_DATE alignment with the VPS cron schedule. |
| Phases it survived | All GHA cache runs since workflow activation. The mismatch meant adj_λ would silently fall back to raw λ even after GG-013 was fixed — this would not have been caught without Q6 analysis. |
| Why it survived | No end-to-end test of GAME_DATE matching between GHA and VPS cron. GG-013 was the active hypothesis for TSS=0 failures; the timing gap was a second independent failure mode that would have been masked by GG-013 resolution. |
| Impact | LOW now (paper mode; adj_λ fallback is silent not wrong). MEDIUM pre-G6: ADR-0015 validation requires adj_λ to actually apply. If this gap persisted post-G6, live bets would use unadjusted λ with no alert, and any measured edge from adj_λ in paper experiments would not transfer to live. |
| Discovery | 2026-06-05 SESSION 33 — Q6 ARE WE COMPROMISED? analysis traced GAME_DATE computation in `run_pregame.py` against GHA cron timing. |
| Resolution | **RESOLVED — 2026-06-05 SESSION 33 (T-137).** GHA cron moved from `30 0 * * *` to `30 20 * * *` (20:30 UTC). At 20:30 UTC day N, GAME_DATE=N. PIPE-02 early cron at 21:55 UTC day N also computes GAME_DATE=N — same file. Trade-off: late cron at 01:25 UTC day N+1 (GAME_DATE=N+1) no longer has GHA cache. Acceptable for Finals (bankroll depleted by early cron before late cron fires). Needs revisit for regular season: two GHA runs/day or late-cron cache strategy. |
| Status | **RESOLVED — 2026-06-05 SESSION 33.** Cron timing fix committed. Regular-season two-run strategy deferred to T-072 scope. |

---

## Resolved Gaps

| Gap ID | Resolution Date | Resolution Summary |
|---|---|---|
| GG-001 | 2026-06-01 | ADR-0006: count gate deleted; pipeline + Kelly + kill switch are the risk framework |
| GG-002 | 2026-06-01 | ADR-0006 covers this; ARE WE COMPROMISED? watchdog added |
| GG-003 | 2026-06-01 | ADR-0007: GOVERNANCE_GAP_LOG.md mandated; ARE WE COMPROMISED? protocol added |
| GG-005 | 2026-06-01 | APR-0017 v2 ACCEPTED: all criteria expressed as rates/slopes with derived thresholds; Q7 protocol in CLAUDE.md |
| GG-008 | 2026-06-02 | T-129 Path B: `p_est` replaced with `Poisson_CDF(threshold, pts_l10_mean)` per threshold in `run_paper_trade.py`; tainted G1 portfolio wiped; clean slate on $1,000 for Finals G1 cron |
| GG-009 | 2026-06-04 | ADR-0016: `net_edge = gross_edge - 0.07 × mid × (1-mid)`; fee-negative bets rejected at gate; `fee_contaminated` always False for new bets post-ADR-0016 |
| GG-010 | 2026-06-03 | DS decision: no dedicated band budgets; shared budget + per-band kill switches is design intent. If T5 starved → root cause is T4_MIN_DELTA_P miscalibration → fix EXP-018, not budget architecture. ADR-0014 Q2 closed. |
| GG-012 | 2026-06-05 | PIPE-02 BOT_C4_ACTIVE guard removed (commit 2997c71). PIPE-02 now runs unconditionally — confirmed by pregame_20260605.json. TSS 0/30 continues for separate reason (GG-013). T-134 remains open. |
| GG-013 | 2026-06-05 | ESPN scoreboard API replaces nba_api (blocked by Akamai from VPS and GitHub Actions). 30 teams/279 records verified. GHA cron auto-delivers cache to VPS before PIPE-02. |
| GG-014 | 2026-06-05 | PARTIAL: time.sleep(0.5) added after each Kalshi order (T-136). Reduces burst from ~12 req/s to ~2 req/s. Effectiveness verified after Finals G2 cron. |
| GG-015 | 2026-06-05 | GHA cron moved 00:30→20:30 UTC (T-137). GAME_DATE now aligned between GHA and PIPE-02 early cron. Late-cron mismatch acceptable for Finals; regular-season two-run strategy deferred. |

---

## Gap Registration Template

When a new governance process failure is discovered:

```markdown
### GG-NNN — [Short title]

| Field | Detail |
|---|---|
| Gap ID | GG-NNN |
| Category | [Architectural placeholder / Incremental architecture / Systemic blind spot / other] |
| What was missed | [The specific decision, value, or check that was absent] |
| When it should have been caught | [Gate, phase, or trigger that should have flagged it] |
| Phases it survived | [G0→G1→...] |
| Why it survived | [Root cause of the governance failure — what scan/check/protocol did NOT catch it] |
| Impact | [What happened or could have happened as a result] |
| Discovery | [How and when it was found — especially if human eye test vs. automated] |
| Resolution | [ADR/APR/task that closes it] |
| Status | OPEN / IN PROGRESS / RESOLVED [date] |
```

---

## Invariant

**Every governance gap must be registered here before remediation work begins.** The act of registering a gap is itself load-bearing — it ensures that the process failure is documented independently of the fix, so that future sessions can distinguish "we fixed the bug" from "we fixed the system that allowed the bug."
