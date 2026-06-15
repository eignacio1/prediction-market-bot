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
| Resolution | EXP-017: backtest edge against actual historical Kalshi prices. OQ-023 registered. T-105 registered. **Part B (Live) run 2026-06-08 SESSION 36:** n=33 unique resolved markets (G2 Finals, 2026-06-05). EV=+0.1042/bet vs actual Kalshi prices. Win rate 81.8%. Mean edge vs market: +0.0375 (vs null 0.50: -0.0486). Verdict: DIRECTIONAL_POSITIVE. Statistical power INSUFFICIENT — n=33 < APR-0017 floor of 66. GG-004 remains OPEN until ≥66 unique markets resolved. |
| Status | OPEN — **scope transitioned to regular season/MLB. DS ruling 2026-06-11 SESSION 51:** NBA Finals sample (n ≈ 96, single series, ~20-30 players, T1-only, Finals context) is structurally insufficient for commercial conclusions — structural limitation, not statistical. Historical EXP-017B data retained: G2 EV=+$0.1042/bet (n=33, DIRECTIONAL_POSITIVE); G4 EV=-$0.0361/bet (n=96, DIRECTIONAL_NEGATIVE). Both inconclusive at Finals scale. Commercial validation now targets: (1) MLB 2026 season (August-September dark period, per DARK_PERIOD_PLAN.md Phase 3); (2) NBA 26-27 regular season (October+). ADR-0024 defines structurally adequate sample: n ≥ 500 unique markets, ≥ 15 distinct opponents, OR ≥ 2 sports each with n ≥ 150. GG-004 remains OPEN until EXP-017 CONFIRMED_POSITIVE on adequate sample. This oversight (Finals window as commercial validation measure) acknowledged in ADR-0024. |

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
| Resolution | Register EXP-020 (T4_MIN_DELTA_P calibration against historical in-play score sequences) and EXP-021 (T5 certainty threshold calibration in final-3-minute game segments). Both must PASS before Phase 8 T4 activation ADR is signed. Threshold revision requires ADR amendment if materially different from skeleton values. T-128 registered. **ID renumber 2026-06-12 SESSION 56:** this entry originally reserved EXP-018/EXP-019, but those IDs were subsequently consumed by unrelated experiments (EXP-018 = adj_λ EV test, `scripts/run_exp018.py`; EXP-019A/B/C = NOISE_BUFFER_BAND calibration). The GG-007 calibration experiments are renumbered EXP-020/EXP-021. No experiment work existed under the old IDs for this gap — the renumber is purely registrational. |
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
| Resolution | **RESOLVED for Phase 6/7 — ADR-0017 ACCEPTED 2026-06-05 SESSION 35.** ADR-0017 documents the formula incompatibility, confirms PAPER_T4_FLAT_SIZING=true as the correct paper architecture (bypasses T4_BAND_WEIGHT entirely), clarifies PAPER_T4_VIRTUAL was already false, and reconciles KELLY_T4=0.20 as the operative paper value. Phase 8 (T4 ACTIVE) per-bet sizing formula deferred to ADR-0018 with specific inputs defined. T4_BAND_WEIGHT=0.10 stub updated comment to reference ADR-0017. |
| Status | **RESOLVED for Phase 6/7 — 2026-06-05 SESSION 35 (ADR-0017).** HIGH severity obligation transferred to ADR-0018 pre-condition list before T4 ACTIVE designation. |

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
| Resolution | **PARTIAL — 2026-06-05 SESSION 33 (T-136).** sleep(0.5) deployed but ineffective (pre-T-136: 43.75% 429 rate, post-T-136: 50% 429 rate). **T-138 deployed 2026-06-08 SESSION 36:** exponential backoff retry (3 retries at 2s/4s/8s) added to `kalshi_client._post()/_get()` for **both 429 AND 503**. Root cause discovery: G3 night showed 18/20 orders as HTTP 503 (not 429) — 503 was not retried at all. Commit 4dd2c3d, 738/738 tests. **G3 effectiveness:** 2/20 orders resting (Wembanyama 35 NO, 30 NO); 18 were pre-fix 503s in portfolio. **G4 (3 orders, all succeeded):** kill switch triggered early; only 3 bets placed; 0/3 failures — inconclusive (too few orders to test burst behavior). **G5 (29 orders): T-138 INEFFECTIVE.** 9/29 = **31% failure rate** — "transient error — max retries (3) exceeded" for all 9. Failures clustered in latter orders of 29-order burst: Wembanyama NO×2 ($182.87), Brunson NO×4 ($57.55), KAT YES×1 ($22.97), Hart YES×2 ($13.88). Pattern: first ~20 orders succeed (resting), last ~9 hit persistent rate limits. Diagnosis: exponential backoff window (2+4+8=14s total) is too short for Kalshi's burst rate limit window at 29-order scale. Paper positions tracked regardless (paper P&L unaffected). G6 gate ≤5% BREACHED. **T-164 registered (SESSION 48):** investigate root cause (429 vs 503 classification; actual rate limit window); implement throttled order submission (inter-order sleep or batch sizing) before G6 live capital. |
| Status | **PARTIALLY RESOLVED — 2026-06-11 SESSION 49 (T-164).** Inter-order sleep 0.5→2.0s; MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0 (schedule 4/8/16/32s = 60s window). Batch order integrity report added to PIPE-03. OPEN until G6 batch confirms ≤5% failure rate in production. |

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

### GG-016 — PIPE-06 BOT_C4_ACTIVE Guard: T3 Signal Scan Silently Dead Since Activation

| Field | Detail |
|---|---|
| Gap ID | GG-016 |
| Category | Architectural guard copy-paste error — same root cause as GG-012 |
| What was missed | `run_t3_pretip.py` contained a `BOT_C4_ACTIVE` guard (lines 253-256) that exited with `FATAL: BOT_C4_ACTIVE is set. PIPE-06 does not place orders.` The VPS `.env` has `BOT_C4_ACTIVE=true`. PIPE-06 exited fatally on every cron tick since SESSION 34 activation — T3 signals were never generated. PIPE-03 correctly fell back to T1-only via the non-contamination guarantee, so no incorrect bets were placed, but the T3 overlay was silently dead despite being marked "LIVE" in the session handoff. |
| When it should have been caught | When SESSION 34 activated PIPE-06 cron. The cron was commented out with a gate note before SESSION 34 — the gate note was about Polymarket connectivity, not BOT_C4_ACTIVE. The guard was in the script from initial authoring and should have been removed before activation. |
| Phases it survived | SESSION 34 PIPE-06 cron activation (2026-06-05) through SESSION 35 protocol check (2026-06-05). All PIPE-06 cron ticks since activation: every 15 minutes 20:00–23:00 UTC and 00:00–03:00 UTC on Jun 5. |
| Why it survived | (1) The non-contamination guarantee worked — PIPE-03 saw no stale/empty T3 report and defaulted to T1-only silently. (2) SESSION 34 handoff stated "T3 overlay LIVE" based on the code path being in place, not on verifying PIPE-06 actually produced signals. (3) No automated alert fires when `t3_cron.log` contains only FATAL lines. (4) The TODO_NEXT "Verify PIPE-06 ran for G2" item was the intended catch, but was not actioned before this session. |
| Impact | LOW (paper mode; PIPE-03 non-contamination guarantee prevented incorrect T3-adjusted bets). The Finals G2 bets placed by PIPE-03 are pure T1 — same as if T3 had never been activated. EXP-018 T3 isolation field (`t3_signal`) will show all NEUTRAL. The CONFIRM/FADE analysis in EXP-018 will have no T3 signal data from G2. |
| Discovery | 2026-06-05 SESSION 35 — Q6 ARE WE COMPROMISED? check: "Verify PIPE-06 ran for G2" → `tail -80 /opt/prediction-market-bot/logs/t3_cron.log` showed only FATAL lines. |
| Resolution | **RESOLVED — 2026-06-05 SESSION 35.** Guard removed from `run_t3_pretip.py` (`__main__` block now calls `main()` directly). Docstring updated: "BOT_C4_ACTIVE may be set (read-only scan — no orders placed)." Committed 6cf87d8. Deployed to VPS. Manual run at 21:58 UTC confirmed: 32 forecasts evaluated, 0 CONFIRM, 0 FADE, 32 NEUTRAL. T3 cron now functional. PIPE-03 early at 22:00 UTC will load fresh `t3_20260605_2158.json` (within 900s staleness window). 19/19 T3 integration tests pass. |
| Status | **RESOLVED — 2026-06-05 SESSION 35.** GG-016 registered and closed. Root cause pattern (BOT_C4_ACTIVE guard incorrectly applied to non-order-placing scripts) now documented as a known copy-paste failure mode. |

---

### GG-017 — No Exit Path on Any Execution Band: System Holds All Positions to Expiry Regardless of Signal Reversal

| Field | Detail |
|---|---|
| Gap ID | GG-017 |
| Category | Architectural gap — missing symmetric filter-out across all bands |
| What was missed | Every execution band (T1–T5) has filter-IN logic (Poisson CDF entry signal, MIN_EDGE gate, Kelly sizing) but NO filter-OUT logic. When in-game Bayesian evidence reverses against an open position — e.g., `p_t4` drops sharply after a player injury or foul trouble — the system holds the position to market expiry with no mechanism to exit. Prediction markets are bilateral instruments: SELL YES and BUY NO are both valid exit mechanisms. A system that can only enter is not exploiting the full strategy space. The architectural principle is: each band's decision tree should be symmetric — filter-IN when edge is positive, filter-OUT when edge reverses. |
| When it should have been caught | ADR-0014 (T-130, 2026-06-03 SESSION 23) — when per-band decision trees were formalized. Entry logic was specified for all bands; exit logic was not addressed. |
| Phases it survived | ADR-0014 through SESSION 40 (2026-06-09). Exposed by G3 post-game analysis: Bridges 2 pts (heavily bet YES positions held to expiry with no exit mechanism despite real-time scoring data showing miss trajectory). |
| Why it survived | ADR-0014 scoped decision trees to entry mechanics only. Exit mechanics were not framed as a missing component — the prior mental model treated prediction markets like binary futures (hold to settlement). The bilateral nature of Kalshi contracts (BUY and SELL both supported) was understood at the venue layer but not integrated into band decision tree design. |
| Impact | MEDIUM. Current paper mode impact: open YES positions on underperforming players held to expiry → full loss on stake rather than partial recovery via exit. Commercial impact grows with capital scale and T4 throughput (~1,000 evaluations/game). At live capital, inability to exit a 300-position T4 book when signals reverse is a material risk that no kill switch addresses (kill switches halt new entries, not existing positions). |
| Discovery | 2026-06-09 SESSION 40 — post-G3 game analysis. Bridges 2 pts (Knicks lost, SAS won 115-111). Operator question: "Wouldn't the T-4 bucket trade those Bridges contracts out?" Answer: no mechanism exists. |
| Resolution path | ADR-0018 required before any implementation. Scope: exit trigger (Bayesian reversal threshold), exit instrument (SELL YES vs BUY NO selection), exit sizing (Kelly on inverse probability), qual enhancer (T3 FADE amplifies exit), time gate (no exits in final N minutes), cost model (E[holding loss] > spread cost). Implementation targets: `paper_trader.py:exit_position()`, `VenueAdapter` sell order type, `run_t4_live.py:_run_cycle()` exit evaluation path. |
| Status | **RESOLVED 2026-06-12 SESSION 59** — Both Tier 2 gate conditions met: (1) T-152 COMPLETE — n=244 exit events empirically validated (≥50 floor met comfortably); NOISE_BUFFER_BAND_T4 raised 0.139→0.19 per update gate; ADR-0019-A01 logged. (2) T-153 COMPLETE — `scripts/run_t153_haircut.py` executed; spread model derived from G4 in-play data (n=5,166); haircut is HIGH materiality ($86–$136 combined T1+T4, G1–G4). ADR-0019 Tier 2 formally CLOSED. Spread model confirms exit cost model (GG-022 haircut data shows p90 spread = 0.17, comfortably below updated NOISE_BUFFER_BAND_T4 = 0.19, validating the exit trigger threshold). |

---

### GG-018 — APR-0017 ≥66-Bet Floor Derived Under T1-Only Assumptions; T4 Integration Invalidates Evidence Pooling Premise

| Field | Detail |
|---|---|
| Gap ID | GG-018 |
| Discovered | 2026-06-09 SESSION 41 — Finals G3 resolution revealed T4 produced 1,115 resolved bets in a single game while APR-0017 was written for T1-only |
| What was missed | APR-0017 states explicitly: "The 66-bet floor was derived assuming the Finals paper window (1 game/night, ~38 markets, T1-only)." The derivation is a T2-A calibration power formula (α=0.05, 80% power, ±15pp deviation detection) for the pregame Poisson model. T4 uses a structurally different model: live Bayesian GameStateModel + adj_λ, firing ~1,115 evaluations per game. The statistical evidence generated by T4 bets cannot be pooled with T1 bets toward the same calibration floor without a governance ruling: (1) T4 and T1 have different error distributions (T4 is live inference under partial information vs T1's static pregame Poisson); (2) the T2-A calibration formula's β/α parameters were derived for T1's specific ECE distribution; (3) pooling conflates evidence from two different prediction problems into a single floor that was designed for one. |
| When it should have been caught | When T4 was activated as LIVE paper mode (PAPER_T4_VIRTUAL=false, SESSION 24 2026-06-03). APR-0017 was accepted 2026-06-01; T4 live activation was 2026-06-03. The 48-hour gap meant the evidence standard was finalized before T4 was understood to produce high-volume evidence of a different type. |
| Why it survived | Paper mode is T1-primary; T4 was virtual for G1 (PAPER_T4_VIRTUAL=true) and not generating real resolved bets. The evidence pooling question wasn't visible until T4 produced real data (G3, 1,115 bets). The MEMORY_BANK GG-011 entry addresses the band budget formula incompatibility; it does not address the calibration evidence structure question. |
| Impact | MEDIUM now (paper mode — G6 is not yet being called). HIGH before G6: if T4 bets are pooled with T1 toward the APR-0017 floor, the 82+1,115 = 1,197 resolved bets wildly exceed the floor without ever validating the T1 pregame model to the T2-A calibration standard. G6 could be called on evidence that is statistically adequate for T4 but does not address T1 calibration at all. Conversely, if T4 bets are excluded, T1 has 82 bets (barely at the floor, at marginal power). |
| Resolution path | ADR required (superseding or amending APR-0017) to: (1) define which bet types count toward each Tier evidence requirement; (2) confirm T1-only for Tier 2 calibration or expand scope with explicit rationale; (3) define T4-specific calibration evidence standard given its different model architecture; (4) re-derive statistical floor for any mixed-model G6 evidence scenario. T-148 registered for regression analysis as input to the ADR. |
| Status | **RESOLVED 2026-06-09 SESSION 43** — APR-0019 ACCEPTED (DS: Earl Ignacio). Per-bucket calibration floors, Tier 2 independence, eligible bets definition, and YES/NO direction monitoring all formally adopted. GG-018 closed. |

---

### GG-019 — T4 C4 Approval Gate Uses Gross Edge: Fee Not Subtracted Before MIN_EDGE Check; Aggregate Fee Drag Undocumented

| Field | Detail |
|---|---|
| Gap ID | GG-019 |
| Discovered | 2026-06-09 SESSION 42 — operator institutional hygiene sprint; spot-check of fee handling in logs and codebase |
| Category | Architectural gap — fee subtraction asymmetry between T1 and T4; aggregate cost undocumented |
| What was missed | **Part A — Code gap:** `run_t4_live.py` computes `edge = p_est - mip` (gross, no fee) and passes it to C4 via `fc_record["edge"]`. C4 gates on `MIN_EDGE_TO_APPROVE = 0.02` against this gross value. T1 (`run_paper_trade.py:461–463`) subtracts `kalshi_fee = 0.07 × mid × (1−mid)` BEFORE C4 (`edge = gross_edge - kalshi_fee`). Result: T4 approves bets with gross_edge in [0.02, 0.0375] at P=0.50 that T1's fee-adjusted gate would reject. At P=0.50 midpoint: fee = $0.0175; bets approved at gross_edge=0.02 have net-of-fee edge = $0.0025 — 87% of gross edge consumed by fees. C4 thinks it's approving at MIN_EDGE=0.02; actual net edge is 8× lower. Note: `paper_trader.py` DOES annotate `fee_per_contract` and `fee_net_edge` on T4 positions post-approval — so the data for post-hoc analysis is present in `paper_portfolio_t4.json`. The error is in the approval gate, not the annotation. **Part B — Architecture/governance gap:** Aggregate fee drag at designed T4 throughput (~1,115 bets/game, G3 data): 1,115 × $0.0175 ≈ $19.51/game in fees. `T4_EXPECTED_TOTAL_EDGE = 441.38` (calibrated G1) is gross — net-of-fee expected total edge is lower by ~$25 (1,446 evals × avg fee). This aggregate fee cost is in zero governance documents: not in ADR-0016 (which covers per-bet fee formula but not aggregate impact), not in CAPACITY_PLANNING.md, not in the APR-0017 EV analysis, not in RESOURCE_BUDGET.md, not in any capital plan draft. At live capital, ~$19/game in T4 fees + ~$2/game in T1 fees at Finals scale is a real cash outflow that changes break-even calculations for live trading. |
| When it should have been caught | ADR-0016 acceptance (2026-06-04 SESSION 30) — when fee subtraction was added to T1, T4's `run_t4_live.py` should have received the same treatment. The ADR says "fee-negative bets rejected at gate" but the gate was only implemented in `run_paper_trade.py`. The GOVERNANCE_GAP_LOG.md GG-009 resolution entry states `fee_contaminated always False for new bets post-ADR-0016` — that is correct for T1 but NOT verified for T4. |
| Phases it survived | ADR-0016 accepted 2026-06-04 → T4 activated live 2026-06-03 (T4 predates ADR-0016) → G1/G2/G3 paper execution → EXP-018 analysis |
| Why it survived | ADR-0016 was written as a T1 fix; T4's edge computation is structurally different (gross = p_t4 - mip, no signed gross_edge key) so the parallel was not checked. ARE WE COMPROMISED? protocol checks `MIN_EDGE_TO_APPROVE` values in risk.py but does not verify that every execution path subtracts fees before that gate. No test asserts fee subtraction in T4 path. |
| Impact | **Part A (paper mode):** T4 paper bets with gross_edge 0.020–0.0375 at P≈0.50 have been placed with near-zero or negative net edge. At 1,115 bets/game and unknown distribution of edge values, some fraction of T4 paper bets are fee-negative. Paper P&L does not track Kalshi fees as a real cash cost (paper fees are notional), so T4 paper P&L is overstated by aggregate fee drag (~$19/game at G3 throughput). G6 evidence from T4 paper does not account for this cost. **Part B (live capital):** At live capital, ~$19/game T4 + ~$2/game T1 in fees at Finals scale → ~$21/Finals-game cost that must be covered by gross edge. At regular season scale (10+ games/night, T1 + T4), aggregate daily fee drag at designed throughput is a material input to break-even analysis that has never been computed. This must be in ADR-0005 (live capital authorization). |
| Resolution path | **Part A:** Fix T4 edge computation to subtract fee before C4: in `run_t4_live.py` before `fc_record`, add `kalshi_fee = 0.07 × mip × (1-mip)` and set `fc_record["edge"] = edge - kalshi_fee`, `fc_record["gross_edge"] = edge`. Requires T-NNN + new tests. **Part B:** Compute aggregate fee budget at designed throughput and add to ADR-0005 break-even analysis: (a) T4 flat-sizing: n_bets × avg_fee = throughput × 0.07 × E[mid × (1-mid)]; (b) T1 Kelly-sizing: derive from approved bet distribution; (c) total at regular-season scale. Neither fix requires an ADR independently, but Part B must be resolved before ADR-0005 can be accepted. Register T-149 (code fix) and T-150 (break-even analysis). |
| Status | **RESOLVED — 2026-06-09 SESSION 42.** T-149 (T4 fee gate code fix) deployed; T-150 (aggregate fee break-even analysis) complete. Net-of-fee edge now in C4 gate for T4. Aggregate fee drag documented in DECISION_LOG SESSION 42 entry. |

---

### GG-020 — Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts

| Field | Detail |
|---|---|
| Gap ID | GG-020 |
| Discovered | 2026-06-09 SESSION 42 — operator question on fee rate provenance during institutional hygiene sprint |
| Category | Governance provenance gap — documentation-sourced constant, no empirical verification |
| What was missed | `ADR-0016` establishes `fee(P) = 0.07 × P × (1−P)` as the Kalshi taker fee formula. `GG-009` discovery note states "Fee formula sourced from Kalshi API docs" — verbal assertion only. No URL is cited in ADR-0016 or GG-009. No documentation version is recorded. No verification against an actual Kalshi transaction receipt has been performed. Verification is structurally impossible in paper trading (no real orders are placed, no real fees charged). The 0.07 rate was taken from documentation at face value in SESSION 22 (2026-06-03) and embedded directly into ADR-0016, `run_paper_trade.py`, `run_pregame.py`, `run_t4_live.py`, `paper_trader.py`, and all fee-adjusted edge computations. |
| What is NOT a validation | `complement_lock_scanner.py:DEFAULT_FEE_PER_CONTRACT = 0.030` (labeled "EXP-010 confirmed Kalshi vig") is the bid-ask spread — a different cost metric. EXP-010 confirming the vig does NOT validate the taker fee rate. These are distinct quantities. |
| When it should have been caught | ADR-0016 acceptance (2026-06-04 SESSION 30) — when the fee formula was formally adopted, a source citation and verification plan should have been part of the acceptance criteria. |
| Impact | LOW now (paper mode; fee is notional; direction of impact well-understood). MEDIUM pre-G6: ADR-0005 break-even analysis depends on the fee drag numbers from T-150, which are computed using 0.07. If Kalshi's actual taker fee differs — e.g., 0.05 or 0.10 — all fee-adjusted edge computations, the T-149 C4 gate threshold, and T-150 break-even estimates are wrong by a proportional factor. At Finals throughput (~$27/game combined T1+T4 fee drag from T-150 analysis), a 30% error in the fee rate = ~$8/game error in the break-even model. |
| Discovery method | Operator question: "Is that 0.07 an arbitrary number? Did you log it as the metric for the fees based on scrubbing through the entire Kalshi database?" — SESSION 42 audit of fee rate provenance revealed no URL, no version, no receipt verification anywhere in the governance artifacts. |
| Resolution path | **Before ADR-0005 (live capital authorization):** (1) Locate the current Kalshi API documentation fee schedule and verify `fee = 0.07 × P × (1−P)` taker. Record URL and access date in ADR-0016 amendment. (2) Place one real live trade post-G6 authorization and verify the fee charged on the receipt matches the formula. If the rate differs, supersede ADR-0016 with corrected constant and rerun T-150 break-even analysis. (3) Both verifications must be complete before ADR-0005 is accepted. Register T-151 (operator action: read current Kalshi fee documentation and record URL + rate in governance artifact). |
| Status | OPEN — **partial verification 2026-06-09 SESSION 43.** Independent investigation conducted: (1) marketmath.io states "Fee per contract = 7% × p × (1−p)" across all contract types; (2) initial search summary confirms 0.07 multiplier for most categories. One conflicting source (predictionhunt.com) suggests sports markets use ~0.06 — explicitly states it cannot confirm the exact multiplier for NBA player props. Kalshi API does not expose fee rates in market data. Kalshi fee schedule PDF rate-limited (HTTP 429). No actual transaction receipts available (paper trading only). Net verdict: **0.07 is supported by ≥2 independent sources; one source suggests possible 0.06 for sports; neither definitively confirmed for NBA player props without actual receipts.** T-151 status: investigation conducted; receipt verification still required post-G6. If 0.06 is correct instead of 0.07: direction of error is conservative (we over-deduct fees → reject profitable bets at margin; EV evidence understated). GG-020 remains OPEN until first live receipt verified post-G6 ADR-0005. |

---

### GG-021 — No Project-Level Stop Criterion: No Documented Evidence Standard for Concluding the Edge Does Not Exist

| Field | Detail |
|---|---|
| Gap ID | GG-021 |
| Discovered | 2026-06-10 SESSION 45 — PDTP full-project self-assessment (operator-directed), blind-spot pass |
| Category | Governance asymmetry — all gates govern *advancing*; nothing governs *stopping* |
| What was missed | The governance system defines what evidence authorizes forward motion (G6: positive P&L, EXP-017 Part B CONFIRMED, ≥66 bets, ≥5 nights, DS sign-off) but defines nowhere what evidence would force the conclusion that the model has no commercial edge and the project should halt or pivot. Current paper record (cumulative P&L −$123.17 / 82 bets; EXP-018 overall CONFIRMED_NEGATIVE) is being correctly scoped as "underpowered, adverse window" — but without a pre-committed falsification standard, *any* negative result can be scoped away indefinitely. The default trajectory of a well-governed project with no stop criterion is to remain well-governed forever. |
| When it should have been caught | APR-0017 acceptance (2026-06-01) — a multi-tier evidence standard for GO should have included the symmetric NO-GO tier. |
| Impact | LOW during paper trading (no capital at risk). HIGH at first regular-season evaluation: deciding what failure looks like *after* seeing the data invites motivated reasoning at exactly the moment live capital is on the table. |
| Discovery method | PDTP Pass 4 blind-spot scan: "Top 3 that could flip the decision" — item 1. |
| Resolution path | T-157: draft stop/pivot criterion as OPEN_QUESTIONS entry now; DS decides and ratifies via ADR **before 2026-27 regular season data begins** (cold decision, warm data prohibited). Must specify: metric (e.g., EXP-017B CONFIRMED_NEGATIVE at adequate power), sample floor, and the action (halt, model-class pivot per ADR-0004 supersession, or scope retreat). Companion watch item: G6 criteria have been superseded once (APR-0016→0017); each future revision must be checked for passability drift — revision direction logged in DECISION_LOG. |
| Status | **RESOLVED — ADR-0024 ACCEPTED 2026-06-11 SESSION 51.** Stop/pivot criterion ratified cold. Tier 1 (n ≥ 150, ≥ 2 months): EV/bet < -$0.03 → diagnostic sprint. Tier 2 (structurally adequate sample = n ≥ 500, ≥ 15 opponents, OR ≥ 2 sports × n ≥ 150): CONFIRMED_NEGATIVE (p < 0.05) → halt paper trading + ADR-0004 supersession review. Scope retreat option: if failing subset is isolated, reduced-scope ADR acceptable. Passability drift watch: standing — every G6 criteria revision must log direction and justification. EXP-017 scope transition to MLB/regular season logged as ADR-0024 consequence. GG-021 CLOSED. |

---

### GG-022 — Paper-Fill Realism: All Paper P&L Used as G6 Evidence Assumes Fills Without Spread Crossing

| Field | Detail |
|---|---|
| Gap ID | GG-022 |
| Discovered | 2026-06-10 SESSION 45 — PDTP self-assessment, contradiction scan |
| Category | Evidence integrity — G6 Tier 1/2 inputs systematically biased in the favorable direction |
| What was missed | Paper fills execute at observed market prices without modeling bid-ask spread crossing, queue position, or market impact. This biases ALL paper P&L upward — T1 and T4 — and that P&L is the core G6 Tier 2 evidence (P&L slope) and the G6 headline criterion (positive cumulative P&L). The contradiction that surfaced it: T4 pool grew $500→$1,539.42 (+108%) at a 51.4% win rate across 1,115 bets while EXP-018 ruled the same underlying λ model CONFIRMED_NEGATIVE on EV — paper-fill optimism is the most parsimonious reconciliation. T4 is worst-exposed (fires into thin in-play books where the fill assumption is least realistic), but T1 resting orders carry the same assumption in milder form. T-153 (spread model) exists but is scoped to ADR-0019 Tier 2 exit validation — not to G6 evidence integrity generally. |
| When it should have been caught | APR-0017 acceptance — paper-fill realism is a precondition for treating paper P&L as gate evidence. |
| Impact | MEDIUM now; HIGH at G6 evaluation: if spread costs consume the measured edge, the G6 gate could clear on evidence that does not survive contact with real execution. Direction of error is systematically anti-conservative — the dangerous direction. |
| Discovery method | PDTP Pass 3 contradiction scan: T4 paper profit vs. EXP-018 negative EV cannot both be face-value true. |
| Resolution path | Expand T-153 scope: spread model must produce a fill-realism haircut applied to *all* paper P&L lines reported as G6 evidence (T1 + T4), not only exit-mechanics validation. G4/G5 spread logging (deployed SESSION 41) is the data source. Until the haircut exists, every G6-facing P&L report must carry the caveat "unhaircut paper fills." APR-0017 amendment required if haircut materially changes Tier 2 thresholds. |
| Status | PARTIALLY RESOLVED 2026-06-12 SESSION 59 — `scripts/run_t153_haircut.py` implemented and executed. Results (G1–G4 data, G5 still open): T1 haircut $53.50–$83.09 (p50/mean); T4 haircut $32.80–$52.71; combined $86.31–$135.81 (HIGH materiality). Paper P&L already negative (T1 −$242.75, T4 −$21.59); adjusted combined P&L ranges from −$350.65 to −$400.15. T1 caveat: resting orders may be maker fills (zero spread cost) — upper bound. **APR-0017 amendment still required (DS ruling needed)** before G6 Tier 2 thresholds can be recalibrated to haircut-adjusted P&L. GG-022 remains OPEN pending DS ruling on APR-0017 amendment scope. Rerun script after G5 resolution for final G1–G5 figures. |

---

### GG-023 — T4 Entry Budget Is Monotonic: Exits Free Economic Capital but Never Replenish Entry Capacity

| Field | Detail |
|---|---|
| Gap ID | GG-023 |
| Discovered | 2026-06-11 SESSION 46 (UTC; 2026-06-10 PDT) — live observation during Finals G4, mid-Q2 |
| Category | Incremental architecture — exit mechanics (ADR-0018/0019) bolted onto a budget design (ADR-0013) that predates them |
| What was missed | `t4_deployed_usd` in `run_t4_live.py` accumulates monotonically (`+= approved_size` at fire, lines 672/709) and is never decremented by the exit pass. When a position exits, its stake is economically freed (PnL realized, position closed in the T4 portfolio) but the entry-budget counter still counts it as deployed. Observed live in G4: T4 fired 1,199 bets and hit $499.95/$500.00 (100%) **before halftime**; 29 exits then fired correctly and freed capital, but `budget_used` stayed pinned at $499.95 — every subsequent cycle logged `fired=0`. The entire second half, where live Bayesian updates carry the densest signal, had zero entry capacity. |
| When it should have been caught | ADR-0019 acceptance / SESSION 43 DS activation override — activating exits changed the meaning of "deployed" from a one-way commitment to a revolving quantity, and the budget accounting was not re-examined against that change. |
| Phases it survived | Designed pre-exit (ADR-0013); survived ADR-0018, ADR-0019, T-146/T-147 implementation review, and SESSION 43 activation. |
| Why it survived | No test or review question asked "what does an exit do to the budget counter?" Exit tests (test_t146_t147_exit_mechanics.py) validate PnL formulas and signal logic, not budget interaction. The budget-exhaustion halt is *designed* behavior (band-level kill: ADR-0013, GG-010 resolution), which made the observation pattern-match to "working as intended." |
| Impact | MEDIUM now (paper only; T4 pool isolated). Distinct from and NOT relitigating GG-010 (DS ruled shared budget + per-band kills is design intent — that ruling concerned cross-band allocation; this gap concerns within-band accounting after exits). Capacity cost is measurable from G4 logs: T4 was entry-dead from ~Q2 onward with ~24+ min of game remaining. Also degrades T-152 empirical exit-event collection: no new entries in the second half means no second-half exit events. Direction of error is conservative (under-deployment, never over-deployment) — but it silently halves the very evidence window the DS override was created to collect. |
| Discovery | Live log read during G4 (session cycle summaries: `fired=0` every cycle post-01:21 UTC with budget pinned at $499.95 after 29 exits), confirmed against source. Human-directed registration (operator: Earl). |
| Resolution | T-161: DS decision + ADR-0013 amendment (or new ADR) on exit-credit semantics. Options to be evaluated with G4/G5 data: (a) credit full exited stake back to entry budget (revolving budget); (b) keep monotonic — budget = gross commitment cap per game (status quo, document explicitly); (c) credit exited stake only up to realized value (no credit for losing exits). Interaction to check: daily-loss net semantics (`424698a`) and kill-switch inputs must stay coherent with whichever option is chosen. No remediation direction chosen at registration — deliberately left to DS cold review post-G4. |
| Status | RESOLVED — 2026-06-10 SESSION 46, ADR-0022 (T-161 DS ruling: option (c) realized-value credit). Exits credit budget at realized value via `_exit_budget_credit()` (entry cost on a win — no capacity expansion; entry cost + pnl on a loss — losses permanently consume budget). Aggregate band net loss now bounded by t4_band_budget. Restart-safe: `_reconstruct_t4_ledger()` rebuilds the ledger from portfolio state (open pool_isolated exposure + per-exit realized losses, keyed to game_date) — G5 starts at $0.00 deployed automatically. Daily-loss net semantics (424698a) verified independent and coherent. 13 new tests (test_t161_budget_credit.py); 843/843 passing. |

---

### GG-024 — PIPE-03 Late Cron Places T1 Bets on Games Already in Progress

| Field | Detail |
|---|---|
| Gap ID | GG-024 |
| Discovered | 2026-06-11 SESSION 46 — audit log review, Phase A post-G4 resolve |
| Category | Architectural gap — PIPE-03 has no in-progress game guard on bet placement |
| What was missed | PIPE-03 (T1 pipeline) checks GAME_DATE but does not check whether the target game has already started before placing new positions. The late cron fires at 01:30 UTC; Finals G4 tipped at 00:30 UTC (~60 min into the game). Audit shows `paper_order_opened` × 2 at 01:31:22 and 01:31:27 UTC for Stephon Castle and Josh Hart — both placed mid-Q2 with live game in progress. These bets used pre-game model estimates (Poisson CDF on pre-game `pts_l10_mean`) against market prices that had already repriced to reflect 60 min of live play. The T1 model has no informational advantage at that point; the market's live price is more informative than the T1 forecast. |
| When it should have been caught | PIPE-03 cron design review (SESSION 10–12) — when the late cron window was established, the overlap with game-in-progress time was not explicitly ruled out. |
| Phases it survived | Every game night since the late cron was activated. G1–G3 likely fired the same way but were not audited at this granularity. |
| Why it survived | The concern was always about the early cron (pre-tip timing), not the late cron. The late cron was designed as a "same-day with T3 overlay" backup window; the guard discussion focused on date alignment (GG-015), not game-start state. |
| Impact | MEDIUM. Bets placed on in-progress games are anti-informed: market has live signal, model does not. In paper trading this is a data quality issue (degrades EXP-017B/EXP-018 evidence — bets placed at a systematic disadvantage). In live trading this would be financially harmful. Also creates ambiguity in G6 evidence: "eligible bets" definition (APR-0019) should exclude mid-game placements. |
| Discovery | Audit log: `player_stats_fetch_failed` × 66 (01:30:10–01:30:56 UTC) then `paper_order_opened` × 2 at 01:31:22/01:31:27 UTC; confirmed `paper_order_opened` payloads show `player_name: Stephon Castle` and `player_name: Josh Hart`; ESPN poll confirmed Q2/clock=~25min at that timestamp. |
| Resolution | T-162: Add game-start guard to PIPE-03 — before the bet-placement loop, check ESPN game status (already polled by T4). If `STATUS_IN_PROGRESS` or past scheduled tip time: skip placement, log `paper_run_skipped_game_in_progress`. Fix is low-complexity (single check against ESPN game state or tip-time comparison). G6 evidence audit: flag any bets placed mid-game as ineligible per APR-0019. |
| Status | RESOLVED — T-162 implemented 2026-06-11 SESSION 46. ESPN `STATUS_IN_PROGRESS` guard added to `run_paper_trade.py` before bet-placement loop (commit `c8a59f2`). Deployed to VPS. 817/817 tests pass. G4 late-cron bets (Castle + Hart) flagged ineligible per APR-0019. |

---

### GG-025 — T4 delta_p Mixes Calibration Gap with Live Signal (Architectural)

| Field | Detail |
|---|---|
| Gap ID | GG-025 |
| Status | RESOLVED (2026-06-10, ADR-0021) |
| Severity | MEDIUM |
| Discovered | 2026-06-10 (SESSION 46) |
| Registered by | ADR-0020 derivation analysis |

**The gap:** `delta_p = p_t4 - p_t1` where p_t4 is raw Poisson and p_t1 is Platt-scaled. At game start (t=48, 0 pts scored), the baseline calibration gap is mean=0.376, σ=0.165 — a systematic model difference, not a live game-state signal. ADR-0020 raises T4_MIN_DELTA_P to 0.50 as a band-aid (above mean+1σ noise floor), but this does not address Q3/Q4 scenarios where the Kalshi market has converged to p_t4, causing |delta_p| to fall to 0.01-0.04. A massive Q4 reversal would not trigger T4 even with budget available because the market has already priced in the game state.

**Correct fix:** Compute incremental delta_p = p_t4_current - p_t4_t0 (change from game-start p_t4, not from p_t1). This isolates live game-state signal from calibration bias. Estimated threshold for incremental version: mean+2σ ≈ 0.48 (G4 trajectory data, n=36 tickers).

**Remediation:** New ADR required. Architectural change — involves storing per-ticker game-start p_t4 and updating GameStateModel.update() and T4EventLoop. Post-G6 scope.

**Resolution (2026-06-10, SESSION 46):** DS overrode the post-G6 deferral ("the architecture needs the correct fix"). ADR-0021 implemented same session. Improvement on the registered fix: no stored game-start snapshot needed — `p_t4_baseline = p_exceeds_threshold(0, threshold, pace×48)` is deterministic from pregame pace, making the fix stateless and restart-safe (G4 mid-game process death would have corrupted a stored-snapshot design). Gate is `|delta_p_incr| ≥ max(2·σ_null(t), 0.04)` where σ_null is the exact Poisson null envelope — no fitted constants. G4 replay (n=2,193): materiality pass rate 74.6% → 9.7%; Q1 false-fire flood eliminated (89.3% → 10.8%) while Q4 sensitivity increased (1.4% → 13.5%), confirming calibration bias is cancelled rather than signal suppressed. T4_MIN_DELTA_P removed; ADR-0020 D2 superseded.

---

### GG-026 — T4 Band Budget Architecture: PAPER_T4_FLAT_SIZING Bypasses Production Kelly Budget Path

| Field | Detail |
|---|---|
| Gap ID | GG-026 |
| Discovered | 2026-06-10 SESSION 46 CLOSE — DS review: "I don't want arbitrary capital restraint (ie $500) — no bandaid fixes" |
| Category | Architectural shortcut outliving its original scope |
| What was missed | `PAPER_T4_FLAT_SIZING=true` (default) hardcodes `t4_band_budget = PAPER_T4_POOL_USD` ($500 flat) and bypasses the production path `_compute_t4_band_budget(portfolio)` = `deployable × T4_BAND_WEIGHT`. The flat $500 was the correct pool size when first set (SESSION 24, G1 launch). By G4/G5, the T4 pool has grown to $1,869.68 through paper wins — the flat cap is now 26.7% of the actual pool and no longer represents a principled fraction of capital. Additionally, `T4_BAND_WEIGHT = 0.10` is explicitly marked "Phase 8 placeholder — inactive in PAPER_T4_FLAT_SIZING=true mode" — it was never calibrated. If the flag were removed today, the production path would give $186.97 band budget ($1,869.68 × 0.10) — less than the flat cap, not more. The transition from flat to proportional is undocumented, unplanned, and the calibration constant is a stub. |
| When it should have been caught | ADR-0011/ADR-0017 acceptance — when PAPER_T4_FLAT_SIZING was introduced as a "paper architecture" shortcut, a sunset condition (pool growth trigger, or G-gate) should have been specified. GG-011 resolution (2026-06-05) explicitly confirmed the bypass as paper architecture; no calibration review was triggered. |
| Phases it survived | G1 launch (pool=$500, flat cap=$500 — coincidentally correct); G2, G3, G4 (pool grew 3.7×, cap unchanged). |
| Impact | MEDIUM now. The cap is effectively underspecified: $500 is neither the current pool size nor a calibrated fraction of it. At G5 with ADR-0021 active (fire volume ~10% of G4's), budget exhaustion should be rare regardless of cap level — but the cap will grow increasingly mismatched as the pool continues to grow. Direction of error is conservative (under-deployment) but arbitrary — the cap has no principled relationship to the system's capital position. |
| Resolution path | T-163: ADR-0023 — remove PAPER_T4_FLAT_SIZING flag; activate `_compute_t4_band_budget(portfolio)` production path; calibrate T4_BAND_WEIGHT from Kelly math (expected concurrent positions × Kelly fraction × expected edge → target utilization fraction). Derivation must be grounded in G1–G4 trajectory data — no arbitrary constant. T4_BAND_WEIGHT update per ADR-0023; `pool_isolated` flag wiring retained. |
| Status | RESOLVED 2026-06-11 SESSION 47 — ADR-0023 ACCEPTED; T4_BAND_WEIGHT=0.27 (G4 empirical: $499.95/$1,869.68); PAPER_T4_FLAT_SIZING and PAPER_T4_POOL_USD removed; `_compute_t4_band_budget` is now the single budget path; pool_isolated=True hardcoded; 843/843 tests. |

---

### GG-027 — PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Environment Classifier Not Built

| Field | Detail |
|---|---|
| Gap ID | GG-027 |
| Discovered | 2026-06-11 SESSION 50 — operator architectural direction: pressure-context categorization for decision tree filters |
| Category | Architectural capability gap — registered feature not yet integrated across full band stack |
| What was missed | The Player Archetype Matrix (PAM v4) is operationalized in C2 (`QualitativeSignalStore`) and the prod model uses 47 PAM features (prf_w01–15, mod_01–32). However: (1) T2/T3/T5 bands have no PAM wiring — `run_t2_sameday.py`, `run_t3_pretip.py`, and T5 LateGameArithmetic operate without archetype context; (2) T4 `T4EventLoop` received archetype register wiring in SESSION 50 but the archetype does not yet affect the routing math (passed through to audit log only); (3) the "pressure-context environment classifier" described by the operator — game-environment categorical modifiers (high-pressure Finals/elimination context, expanded-role context for role players, crowd/psychological context) — is entirely unbuilt as of SESSION 50; (4) QS snapshot age: classifications dated 2026-05-28 have not been updated for Finals-specific role changes (e.g. Alvarado Q4 expanded role in G4). |
| When it should have been caught | ADR-0019 (exit mechanics) acceptance — when PAM features were confirmed live in the model, a task for full band integration should have been registered. The operator's architectural direction toward environment-context categorization makes the gap more visible. |
| Impact | LOW now — T2/T3/T5 are SKELETON/BLOCKED; T4 routing is correct without archetype math (ADR-0021 handles materiality). HIGH pre-MLB activation — regular season requires full band coverage; environment classifier is architecturally essential for the "Wemby 10 RBG ≠ Zubac 10 RBG" disambiguation at scale. |
| Resolution path | T-165: Full PAM integration across T2/T3/T5 bands + environment classifier ADR — MLB activation gate. Scope: (a) EnvironmentClassifier in C2 (game-level pressure score: elimination_flag, series_momentum, crowd_premium, role_expansion_flag for role players); (b) archetype × environment interaction in C3 (uncertainty multiplier on model_p for sparse-data role players in high-pressure contexts); (c) dynamic MIN_EDGE_TO_APPROVE in decision tree routing per environment class; (d) T2/T3/T5 archetype register wiring matching T1/T4 pattern. |
| Status | OPEN — T-165 registered. Low severity until T2/T3/T5 approach active status. |

---

### GG-028 — PIPE-03 No Idempotency Guard: Second Cron Execution Places Duplicate Positions for Same game_date

| Field | Detail |
|---|---|
| Gap ID | GG-028 |
| Discovered | 2026-06-12 SESSION 52 — G5 portfolio audit: 41 open positions vs expected 29; two batch timestamps confirmed (22:00 UTC 29 bets, 01:00 UTC 12 bets) |
| Category | Operational gap — pipeline has no guard against re-execution for an already-deployed game_date |
| What was missed | PIPE-03 (`run_paper_trade.py`) has no check for existing open positions before running the bet-placement loop. If the script runs twice for the same game_date, it evaluates all markets afresh and places any new bets that pass the edge filter — including markets where positions already exist from the first run. G5 result: the 22:00 UTC batch placed 29 bets; a second run at 01:00 UTC placed 12 more bets, including duplicate Wemby NO ≥40 and NO ≥35 positions (the two that failed in the first batch — the pipeline saw no "resting" order and re-deployed them). Total T1 deployment: $1,003.38 from a $1,000 bankroll reset, pushing reserve to 13% (below RESERVE_MANDATE 15%). T-162's game-in-progress guard (added SESSION 46) guards against in-progress games only — it does not guard against same-game_date re-execution when the game has not yet started. |
| When it should have been caught | GG-024 resolution — when T-162's in-progress guard was added, idempotency for pre-game re-execution should have been addressed in the same pass. |
| Phases it survived | G5 paper trading only; no live capital impact. Likely occurred in other finals games but was not audited at this granularity. |
| Why it survived | GG-024 focused on mid-game placement (game in progress). The idempotency case (game not yet started, positions already open for this game_date) was not explicitly addressed. The second cron may have been triggered by PIPE-03 restart or manual rerun — cause unknown. |
| Impact | MEDIUM. In paper mode: extra bets, reserve mandate breach (~13% vs 15% target), data quality degradation (duplicate positions inflate sample n). In live trading: this would double-deploy real capital on the same market, potentially violating per-event exposure caps. A PIPE-03 accidental rerun (process crash + restart) in live trading would cause material unintended exposure. |
| Resolution path | T-166: Add idempotency guard to `run_paper_trade.py` — before the bet-placement loop, check portfolio for existing open positions with `game_date == target_date`. If any exist: log `paper_run_skipped_already_deployed: {n} positions exist for {game_date}` and exit. Also: investigate what triggered the 01:00 UTC second run (process restart? manual? cron misconfiguration?). |
| Status | **RESOLVED 2026-06-11 SESSION 53** — T-166 implemented. `_open_tickers` set in `run_paper_trade.py` now includes ALL open positions regardless of `kalshi_order_status`. Commit: SESSION 53. Root cause of "failed = transient" design confirmed: the exclusion was intended as a Kalshi-connectivity retry mechanism, but a recorded paper position represents a committed local allocation — bankroll already decremented, position already in `open_positions`. The second cron is connectivity redundancy, not a re-evaluation window. |

---

### GG-029 — MC Script Analyzes Pregame Forecasts, Not Committed Positions: Wrong Source and Wrong Parameters

| Field | Detail |
|---|---|
| Gap ID | GG-029 |
| Discovered | 2026-06-12 SESSION 52 — MC script reported $106.21 staked; actual portfolio had $1,003.38 deployed; source confirmed as `pregame_20260612.json`, not `paper_portfolio.json` |
| Category | Tooling gap — risk analysis tool not connected to actual system state |
| What was missed | `scripts/run_monte_carlo.py` reads from `pregame_YYYYMMDD.json` (the model's forecast output) rather than `logs/paper_portfolio.json` (the actual committed positions). It then re-applies Kelly sizing with hardcoded parameters: `kelly=0.1, min_edge=0.02, max_exposure=500.0` — none of which match the actual risk engine (`DEFAULT_KELLY_FRACTION=0.25, MIN_EDGE_TO_APPROVE=0.04`). Result: every MC run throughout the Finals has simulated a hypothetical re-deploy of the residual bankroll, not the actual risk exposure of committed positions. G5 example: MC reported $106.21 staked from $130.62 bankroll (81% utilization) while the actual portfolio had $1,003.38 deployed. The kill switch risk and P/L distribution the MC reported were for a different portfolio than the one that will resolve. |
| When it should have been caught | MC script introduction (SESSION ~30?) — the source data and parameter alignment were never validated against the actual risk engine configuration. |
| Phases it survived | All Finals games (G1–G5). Every MC report produced this session analyzed a hypothetical portfolio. |
| Impact | MEDIUM. The MC is a governance and operator-communication tool — Earl uses its output to assess risk before game day. If the tool is analyzing a different portfolio than the one deployed, all MC-based risk assessments are systematically disconnected from actual exposure. P/L distribution tails, kill switch risk probabilities, and player concentration figures are all wrong. Actual G5 portfolio analysis (run manually SESSION 52): EV=+$246.67, P(profit)=99.8%, P(kill switch)=0.00%, p50 end bankroll=$382. |
| Resolution path | T-167: Rewrite `run_monte_carlo.py` to: (1) read from `logs/paper_portfolio.json` as primary source; (2) use risk engine constants from `risk.py` (not hardcoded); (3) simulate actual win/loss outcomes for each committed position using stored `model_p`, `direction`, `mid_price_at_entry`, `size_usd`; (4) report actual P/L distribution, not hypothetical re-deploy. Keep `pregame_YYYYMMDD.json` as an optional "pre-deploy preview" mode for analysis before committing. |
| Status | **RESOLVED 2026-06-11 SESSION 53** — T-167 implemented. `run_monte_carlo.py` rewritten: portfolio mode (default) reads `paper_portfolio.json`, simulates committed positions via Bernoulli draws using `model_p`/`direction`/`mid_price_at_entry`/`size_usd`. Preview mode (`--preview`) retains pregame JSON behavior. Constants corrected to production values (`kelly=0.25`, `min_edge=0.04`). Scenario flags added: `--exclude-failed`, `--yes-only`, `--no-only`, `--haircut`. Commit: SESSION 53. |

---

### GG-030 — Portfolio MC Draws Positions as Independent Bernoullis: Within-Player Threshold-Ladder Correlation Ignored

| Field | Detail |
|---|---|
| Gap ID | GG-030 |
| Discovered | 2026-06-12 SESSION 55 — pre-Game-5 protocol review of `run_monte_carlo.py` portfolio mode (T-167 rewrite) |
| Category | Tooling gap — risk model structurally understates correlated tail risk |
| What was missed | Portfolio mode (`run_monte_carlo.py:144`) simulates each committed position as an **independent** Bernoulli draw (`rng.random(n_sims) < p_win` with a fresh draw per position). But the G5 book holds threshold *ladders* on single players — e.g., Brunson NO 25/30/35/40 (×2 each after GG-028 duplicates) and Wembanyama NO 35/40 (×2). In reality these rungs are perfectly correlated: one 40-point game loses every rung simultaneously. The script's own caveat text (line 297–298) acknowledges this, but the headline numbers reported to the operator (G5: P(profit)=99.8%, P(kill switch)=0.00%) come from the uncorrelated path. Notably, the legacy `--preview` mode does this *correctly* — it draws one Poisson score per player and compares it against all thresholds (line 424–438) — so the T-167 rewrite regressed correlation structure while fixing position sourcing. Compounding: the draws use the model's own `model_p` as ground truth, so the MC cannot see model miscalibration — the exact failure mode EXP-017B (DIRECTIONAL_NEGATIVE vs real prices) and the G3 MC miss (predicted +$138 @ 95.1%; actual -$199) point at. |
| When it should have been caught | T-167 implementation review (SESSION 53) / SESSION 54 hygiene audit — the audit verified per-position formulas but not the joint distribution. |
| Phases it survived | G5 risk reporting (SESSION 52 manual analysis used the same independent-draw structure). |
| Why it survived | Hygiene audit checked formula correctness per position, not portfolio-level dependence. The caveat in the report footer made the limitation feel "documented" without changing the headline numbers. |
| Impact | MEDIUM-HIGH for operator communication. With $323 on Wembanyama NO rungs and ~$102 on Brunson NO rungs (each rung duplicated), a single star eruption in an elimination game realizes losses approaching the $200 kill-switch trigger (20% of $1,000) — yet the MC reports P(kill switch)=0.00%. The reported risk profile of the G5 book is materially understated in the left tail. No live capital impact (paper). |
| Discovery | Human-prompted adversarial review (SESSION 55 Q6), grep of simulation structure vs live book composition. |
| Resolution | T-168: portfolio mode should draw one latent outcome per player (Poisson score, as preview mode already does) and resolve all of that player's positions against it; treat duplicated tickers as summed exposure. Re-run G5 MC and re-report tail/kill-switch figures. |
| Status | RESOLVED 2026-06-12 — T-168 SESSION 55: `simulate_portfolio()` now draws one Poisson score per player via `_infer_lambda()` (least-squares fit on threshold/model_p pairs); direction-invariant (NO bets use raw model_p, not 1−model_p); NO-bet inversion bug found and fixed in same session. G5 MC re-run: P(profit)=98.3%, kill-switch risk=1.28%, mean P&L=+$244.23. Commit `530e1c3`. |

---

### GG-031 — GG-028 Blast Radius Understated: 9 Duplicated Tickers ($402.49, 40% of G5 Deployment), Not 2

| Field | Detail |
|---|---|
| Gap ID | GG-031 |
| Discovered | 2026-06-12 SESSION 55 — direct audit of VPS `paper_portfolio.json` open positions: `Counter((ticker, direction))` |
| Category | Incident scoping gap — resolved-gap record documents partial blast radius |
| What was missed | GG-028's record states the 01:30 UTC batch placed "duplicate Wemby NO ≥40 and NO ≥35 positions." The actual count: **all 9 tickers whose 22:00 UTC orders failed were re-bet at 01:30 UTC** — Wemby NO-40/-35, Brunson NO-40/-35/-30/-25, Hart YES-15/-10, KAT YES-10. Every duplicated pair shows one `failed: transient` position (22:0x UTC) and one `resting` position (01:30 UTC). Total stake in duplicated tickers: $402.49 of $1,003.38 deployed (40%). Also resolved as side-finding: the "unexplained" 01:00 UTC second run flagged in GG-028's resolution path is simply the scheduled 01:30 UTC late PIPE-03 window in `cron.conf` — `entered_at` timestamps match exactly. No mystery trigger exists; the investigation item can close. |
| When it should have been caught | SESSION 52 portfolio audit (it identified 2 of 9) and SESSION 53 T-166 close-out (fix was verified, but the existing book was not re-audited under the fix's logic). |
| Phases it survived | G5 book as currently committed; will flow into G5 resolution P&L and any G6-facing evidence unless annotated. |
| Why it survived | The SESSION 52 audit spotted the largest duplicates (Wemby) by eye; no systematic ticker-level duplicate scan was run. T-166 fixed the mechanism prospectively without retrospectively reconciling the already-committed book. |
| Impact | MEDIUM. (1) G5 P&L will double-count 9 markets — G6 evidence (already Finals-excluded per ADR-0024, but logged) and EXP-017B/018 G5 inputs need dedupe-or-annotate. (2) Doubles tail exposure on exactly the positions GG-030 shows the MC can't see. (3) Bankroll accounting carries both stakes ($130.62 remaining). |
| Discovery | SESSION 55 protocol — direct VPS book audit. |
| Resolution | T-169: decide DS treatment of the 9 failed-order twins (annotate as `duplicate_of` and exclude from per-market experiment n; or accept as committed allocations with documented double exposure); update GG-028 resolution summary; close the "01:00 UTC trigger" investigation as RESOLVED (scheduled late window). |
| Status | RESOLVED 2026-06-12 SESSION 56 — DS ruling: Option A. 9 late-cron (01:30 UTC) resting positions annotated with `duplicate_of: <original_position_id>` (original = failed 22:00 UTC attempt). EXP-017B/018 reruns must filter `duplicate_of` positions from per-market n. G5 P&L still resolves all 41 positions (double exposure stands as committed). Backup at `paper_portfolio.json.bak_t169`. "01:00 UTC mystery trigger" confirmed RESOLVED — scheduled 01:30 UTC late PIPE-03 window in `cron.conf`; no mystery trigger. |

---

### GG-032 — T4 Portfolio Accounting Incoherence: bankroll +$869.68 vs total_realized_pnl −$21.59

| Field | Detail |
|---|---|
| Gap ID | GG-032 |
| Discovered | 2026-06-12 SESSION 55 — VPS `paper_portfolio_t4.json` top-level field audit |
| Category | Data integrity gap — headline T4 performance metric cannot be reconciled from the file that stores it |
| What was missed | `paper_portfolio_t4.json` shows `bankroll_usd=1869.68`, `initial_bankroll_usd=1000.0`, `total_realized_pnl=-21.59`. These cannot all be true under bankroll = initial + realized P&L: the implied gap is ~$891. Probable contributors: the pool actually started at $500 (PAPER_T4_POOL_USD era) while `initial_bankroll_usd` recorded 1000; the SESSION 46 reset touched realized P&L epochs differently from bankroll; and/or pool-isolated open/close paths credit `bankroll_usd` asymmetrically from `total_realized_pnl`. Whatever the mix, the widely-cited "T4 pool +87% / +108% growth at 51.4% win rate" narrative and the file's own realized P&L (negative since reset) tell opposite stories. |
| When it should have been caught | SESSION 46 bankroll reset (epoch boundary not applied consistently to T4 file) or T-148/APR-0019 T4 evidence separation work. |
| Phases it survived | G3–G5 T4 reporting; MEMORY_BANK milestone entries cite pool growth figures. |
| Why it survived | T4 pool figures were read as a single number (bankroll_usd) without reconciling against initial + realized; pool_isolated semantics made cross-checking against T1 conventions feel inapplicable. |
| Impact | MEDIUM. T4's G6-facing evidence (APR-0019 T4 floor ≥50) depends on knowing whether T4 is actually up ~$870 or down ~$22 since its epoch start. Until reconciled, no T4 performance claim should be cited. Fill-realism haircut (T-153/GG-022) compounds the uncertainty in the same direction. |
| Discovery | SESSION 55 protocol — field-level file audit. |
| Resolution | T-170: reconstruct T4 ledger from `closed_positions` (2,315 records) + C6 audit log; determine true epoch-consistent P&L; correct either `bankroll_usd`, `total_realized_pnl`, or `initial_bankroll_usd`; document which figure feeds APR-0019 Tier 2 T4 evidence. |
| Status | RESOLVED 2026-06-12 — T-170 SESSION 55: `paper_portfolio_t4.json` corrected on VPS — `bankroll_usd` 1869.68→**478.41**, `initial_bankroll_usd` 1000→**500.0**. Root cause: ADR-0022 `_reconstruct_t4_ledger()` wrote T1 system bankroll into T4 file. True T4 pool = $500 initial + (-$21.59 realized P&L) = **$478.41**. Backup at `paper_portfolio_t4.json.bak_t170`. Do not cite "+87% growth" T4 narrative — based on wrong field. |

---

### GG-033 — Live Portfolio State Tracked in Git: Deploy Pipeline Silently Broken Since SESSION 55

| Field | Detail |
|---|---|
| Gap ID | GG-033 |
| Discovered | 2026-06-12 SESSION 56 — VPS `git pull --ff-only` aborted on dirty tree during EXP-018 filter deploy |
| Category | Deploy integrity gap — live mutable state in VCS blocks deploys and risks state destruction |
| What was missed | `logs/paper_portfolio.json` is git-tracked. Every cron write dirties the VPS working tree, so every `git pull` aborts. SESSION 55's deploy record ("git pull + scp confirmed") was inaccurate: the pull failed on this same conflict, and the scp of `run_monte_carlo.py` masked it. Result: VPS sat at `cea8a19` (SESSION 54 close) through SESSION 55–56 while MEMORY_BANK recorded it as current — the T-168 MC fix existed on the VPS only as an uncommitted working-tree file. Verified identical to the committed version this session (no drift), but nothing guaranteed that. |
| When it should have been caught | SESSION 55 deploy verification — "DEPLOY OK" was asserted without `git log -1` confirmation on the VPS. |
| Phases it survived | SESSION 55 (T-168 deploy), SESSION 56 (T-169 sprint) until this session's pull attempt. |
| Why it survived | scp side-channel made the working tree look current; no deploy step verified VPS HEAD == origin/main. |
| Impact | HIGH for live-capital era, MEDIUM now. (1) Two failure modes: deploys silently no-op (stale risk code in production), or a future `git checkout .`/`git reset --hard` on the VPS destroys the live book — open positions, annotations, bankroll. (2) Local repo copy of the portfolio is stale ($1,000/3-open vs VPS $130.62/41-open), so the session-start governance hook prints misleading portfolio state. |
| Discovery | SESSION 56 — pull abort during EXP-018 dedupe filter deploy. |
| Resolution | T-171: (1) `git rm --cached logs/paper_portfolio.json` (and `paper_portfolio_t4.json` if tracked) + add to `.gitignore`; (2) coordinated VPS migration: backup live file outside repo → checkout → pull (file removed from tree) → restore → verify untracked; (3) add `git log -1` HEAD verification to the /vps deploy skill so "deployed" claims require commit-hash proof; (4) decide what the session-start hook PORTFOLIO line should read once local copy is gone (VPS fetch or label as N/A). Schedule for dark period — do NOT perform the untracking migration while 41 positions are open and crons are writing. |
| Status | OPEN — T-171 registered 2026-06-12; migration deferred to dark period Phase 1 (post-G5 resolution) |

---

### GG-034 — Realized-P&L Accumulator Desynced From Ledger: Drawdown Kill Switch Blind to True −25% Loss

| Field | Detail |
|---|---|
| Gap ID | GG-034 |
| Discovered | 2026-06-13 SESSION 62 — ARE WE COMPROMISED? Q6, reconciling session-start portfolio readout |
| Category | Lying-monitor / ledger-reconciliation gap — self-reported health diverges from append-only ground truth (matches the standing audit thesis) |
| What was missed | The live VPS book `logs/paper_portfolio.json` stores `total_realized_pnl = −$8.46`, but the sum of its own 117 closed-position `pnl` fields is **−$251.21**. The C6 append-only audit log (`audit.jsonl`, `paper_position_resolved` events) independently confirms **−$251.21** for exactly those 117 position_ids, with **zero double-resolutions** — so the ledger is correct and the scalar accumulator is the corrupted value. Gap = **$242.75**. True realized drawdown is **25.1%** of the $1,000 initial bankroll, which **exceeds the 20% `max_drawdown_pct` kill switch** (`risk.py:105`). The drawdown kill switch reads the corrupted scalar (`run_paper_trade.py:274` → `current_drawdown_pct` → `risk.py:418`), as do the C7 monitor (`monitor.py:537`), the C8 dashboard (`dashboard.py:181`), and the G6 positive-P&L gate. All four health surfaces read the lying number; none derive P&L from the ledger. **The same class of desync exists in the T4 book** (`paper_portfolio_t4.json`: stored −$21.59 vs Σ closed pnl −$47.25) — systemic, not a one-off. Per-game-date truth: 06-05 +$75.67 (35 bets, = the last consistent snapshot, matches the stale local `paper_portfolio_vps.json`), 06-08 −$198.84 (47), 06-10 −$128.04 (35). The −$8.46 scalar matches no clean subset → not a single reset; consistent with concurrent-writer clobbering. |
| Root cause | `total_realized_pnl` is a redundant scalar accumulator of a value fully derivable from `Σ closed_positions.pnl`. It is incremented in-memory by `PaperTrader` (`paper_trader.py:528`, `:377`) under an **in-process lock only** (`:188`), with **no cross-process lock**. Multiple runners write the same JSON file load→mutate→save: `run_paper_trade.py`, `run_resolve.py`, `run_t4_live.py`, `run_t4_resolve_local.py`. A runner holding a stale in-memory copy saves it back and clobbers increments from another runner (last-write-wins), so the scalar drifts while the appended `closed_positions` list and the append-only audit log stay correct. Bankroll is also independently inconsistent: entry debits full `size_usd` (`paper_trader.py:199,226`) and resolve credits `size+pnl` (`:527`), so `bankroll = init − Σ(open size_usd) + Σ(closed pnl)` implies Σ closed pnl = **+$134.00**, a third number disagreeing with both −$8.46 and −$251.21 — so `bankroll_usd` cannot be trusted either. |
| When it should have been caught | Any session reading the portfolio summary since 2026-06-08 (first divergent resolution batch). The session-start governance hook prints `total_realized_pnl` verbatim as "P&L $-8.46 / drawdown 0.8%" with no ledger cross-check. GG-030/GG-032/GG-033 each corrected portfolio *values* in prior sessions but never reconciled the accumulator against the ledger, so the mechanism survived every patch. |
| Phases it survived | G4→G5 (2026-06-08 onward); through SESSION 56–61 portfolio-state work; surfaced SESSION 62. |
| Why it survived | No invariant check that `total_realized_pnl == Σ closed_positions.pnl` on load or save. All health surfaces (kill switch, monitor, dashboard, G6 gate) trust the cached scalar instead of deriving from the ledger. The reported 0.8% drawdown looked healthy and far from the 20% switch, so nothing prompted a reconciliation. |
| Impact | **HIGH.** (1) **Drawdown kill switch is blind** — true 25.1% drawdown is past the 20% halt threshold but the switch reads 0.85% and never fires on this. CRITICAL for live-capital era; HIGH now even on paper because every risk decision since 06-08 sized against a false bankroll/drawdown. (2) **G6 readiness is measured on a false number** — G6 requires positive resolved P&L; book shows ≈breakeven (−$8.46) while truth is −$251.21 (−25%). The commercial/gate picture is materially worse than recorded in MEMORY_BANK. (3) `bankroll_usd` itself does not reconcile, so Kelly sizing inputs are suspect. (4) Same desync confirmed in the T4 book. |
| Discovery | SESSION 62 Q6 — cross-checked stored scalar vs Σ closed pnl vs C6 audit log vs cash identity; three of four mutually disagree, audit log corroborates the ledger at −$251.21. |
| Resolution | NOT YET FIXED (operator approved root-cause + registration only; no writes to the live book pending fix approval). Proposed direction for a dedicated session: (1) make `total_realized_pnl` a **derived property** (`sum(p["pnl"] for p in closed_positions)`) rather than a maintained accumulator, OR add a load-time reconciliation assert that halts on `|accumulator − Σledger| > $0.01`; (2) recompute and correct the live `bankroll_usd` from the audit log as ground truth (init − Σ open entry-costs + Σ closed pnl), with backup preserved; (3) point the kill switch / monitor / dashboard / G6 gate at the ledger-derived figure; (4) add a cross-process file lock (or single-writer invariant) so concurrent runners cannot clobber state; (5) apply the same fix + correction to the T4 book; (6) re-evaluate whether the true −25% drawdown retroactively triggers a halt / DS review. Coordinate with T-171 (untracking + migration) since both touch the live book during the dark period. |
| Status | OPEN (CODE-COMPLETE in `paper_trader.py`, NOT DEPLOYED, 2026-06-14 SESSION 63 — T-174 WS1 full). **Reporting layer fixed:** `total_realized_pnl` is ledger-derived (accumulator increments removed; `_save()` recomputes from Σ closed `pnl`+`exit_pnl`); `reconcile()` logs a `portfolio_pnl_desync` C6 event and adopts the ledger value on load (in-memory only); `summary()` derives drawdown from the ledger — un-blinds the kill switch. **Source layer fixed (second half):** cross-process `fcntl` file lock + `_reload_locked()` re-read under lock on all three mutating paths (stops the list-clobbering at its root); `resolve_pending` double-resolution guard; `bankroll_usd` now ledger-derived via `_ledger_bankroll()` (initial + Σ closed non-isolated pnl − Σ open non-isolated stake), imperative bankroll mutations removed; the latent `resolve_pending` isolated-credit bug (credited bankroll ignoring `pool_isolated`) is fixed by the derivation. 13 tests in `tests/test_t174_pnl_reconciliation.py` (incl. the exact GG-034 scenario + concurrency/clobber + isolated-bankroll cases); 2 `TestSummary` tests rewritten off the condemned scalar-trust contract; **936/936 pass.** **NO live-book writes this session — the corrupted VPS book is untouched, so the kill switch is still blind IN PRODUCTION until this code is deployed AND the book is corrected.** STILL OPEN pending (WS3/deploy): **live VPS book correction (operator OK required — surfaces true −25%, trips kill switch)**; **DS ruling on retroactive halt**; true G6 baseline recompute; T4-book application; T-171 coordination; commit/push/deploy. Linked: GG-030, GG-032, GG-033; T-171; T-174. |

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
| GG-028 | 2026-06-11 | T-166: `_open_tickers` set includes ALL open positions regardless of Kalshi order status. Second cron now correctly blocked from re-deploying failed positions. |
| GG-029 | 2026-06-11 | T-167: MC script rewritten — portfolio mode default; constants corrected; scenario flags added. |
| GG-030 | 2026-06-12 | T-168: `simulate_portfolio()` draws one Poisson score per player (`_infer_lambda()` least-squares); direction-invariant; NO-bet inversion fixed. G5 MC: P(profit)=98.3%, kill-switch risk=1.28%. Commit `530e1c3`. |
| GG-032 | 2026-06-12 | T-170: `paper_portfolio_t4.json` on VPS corrected — bankroll_usd→478.41, initial_bankroll_usd→500.0. True T4 pool=$478.41. Backup preserved. |
| GG-031 | 2026-06-12 | T-169: DS ruling Option A — 9 late-cron twins annotated `duplicate_of` on VPS. EXP reruns exclude duplicates from per-market n. Double exposure stands. "01:00 UTC trigger" confirmed as scheduled 01:30 UTC late window. |
| GG-014 | 2026-06-11 | **PARTIALLY RESOLVED — T-164 deployed (SESSION 49).** Root cause: 29-order burst exhausts rate-limit window; T-138 backoff window (14s total) < rate-limit reset window. Fix: inter-order sleep 0.5→2.0s; MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0 (delay schedule 4/8/16/32s = 60s total). Batch order integrity report added to PIPE-03 run (fail rate logged + WARN >5%). **G5 FINAL SNAPSHOT (SESSION 52, 2026-06-12):** 22:00 UTC batch (29 bets): 9/29 failed = **31% failure rate** — identical to pre-T-164 rate; T-164 did not reduce failures at peak API congestion window. 01:00 UTC batch (12 bets): 0/12 failed = 0% — T-164 is effective when API is uncongested (off-peak). Interpretation: failures are congestion-driven (server-side Kalshi rate limiting at ~22:00 UTC betting rush), not rate-limiting caused by the bot's own request cadence. T-164's 2.0s inter-order sleep addresses self-generated rate pressure but not server-side congestion. Fix path may require moving the primary cron earlier (e.g., 18:00 UTC) or requesting a higher rate limit tier. **DARK PERIOD NOTE (SESSION 51, 2026-06-11):** G6 gate (≤5% failure rate) confirmation deferred to 2026-27 Season Day 1 paper batch — registered as Phase 4 P0 gate in DARK_PERIOD_PLAN.md. Status: OPEN; next viable confirmation window: October 2026. **TONIGHT'S KNOWN RISK (SESSION 62, 2026-06-13, NYK@SAS):** This is the designated execution risk for tonight's unattended run. Order-failure rate over the last 6 betting nights: 06-06 46%, 06-09 0%, 06-10 0%, 06-11 22%, 06-12 0% — congestion-driven, concentrated in the 22:00–23:00 UTC burst window (T4 cron fires 23:00). It is a server-side coin-flip; no safe mitigation available before tip-off. **Failure mode is graceful**: failed orders are logged (`kalshi_order_failed`) and skipped, the run continues — not a crash, not state corruption. Accepted as the residual risk for tonight per operator decision (ride). Verified NOT at risk tonight: idempotency (06-13 18:00 cron correctly skipped already-open Brunson position), T4 in-progress guard (polling ESPN game status as designed), infra (disk 15%, Kalshi API HTTP 200, code current). Healthcheck reports 3 FAILs tonight, all confirmed false positives (Kalshi API up despite FAIL; BOT_C4_ACTIVE harmless for paper/T4 path; OpenSSL system-python check irrelevant to working venv) — T-173 lying-monitor thread. |
| GG-015 | 2026-06-05 | GHA cron moved 00:30→20:30 UTC (T-137). GAME_DATE now aligned between GHA and PIPE-02 early cron. Late-cron mismatch acceptable for Finals; regular-season two-run strategy deferred. |
| GG-011 | 2026-06-05 | ADR-0017 ACCEPTED. PAPER_T4_FLAT_SIZING=true confirmed as paper architecture (bypasses formula). Phase 8 per-bet sizing deferred to ADR-0018. T4_BAND_WEIGHT stub comment updated. |
| GG-016 | 2026-06-05 | BOT_C4_ACTIVE guard removed from run_t3_pretip.py (commit 6cf87d8). PIPE-06 now runs cleanly. T3 signals confirmed at 21:58 UTC Jun 5 — 32 NEUTRAL, cron functional. |
| GG-018 | 2026-06-09 | APR-0019 ACCEPTED (DS: Earl Ignacio). Per-bucket T1/T4 evidence separation; T1 floor ≥66, T4 floor ≥50 (new derivation); Tier 2 evaluated independently; eligible bets defined; YES/NO direction monitoring registered. APPROVALS_REGISTER.md updated. |
| GG-019 | 2026-06-09 | T-149 deployed (T4 fee gate now subtracts kalshi_fee before C4 evaluation). T-150 complete (aggregate fee drag: T4 $14.28/game, T1 $12.89/game, combined ~$27/game at Finals scale; documented in DECISION_LOG SESSION 42). GG-020 registered as new gap: fee rate source citation + receipt verification required pre-ADR-0005. |
| GG-025 | 2026-06-10 | ADR-0021: materiality gated on `delta_p_incr = p_t4 − p_t4_baseline` (calibration gap cancels algebraically) vs exact Poisson null envelope `max(2σ_null(t), 0.04)`. Stateless/restart-safe; zero fitted constants. G4 replay: pass rate 74.6%→9.7%, Q1 89.3%→10.8%, Q4 1.4%→13.5%. T4_MIN_DELTA_P removed; ADR-0020 D2 superseded. |
| GG-023 | 2026-06-10 | ADR-0022 (T-161 ruling: realized-value credit). Exits credit budget at realized value — wins restore entry cost (no expansion), losses consume permanently; band net loss bounded by budget. Restart-safe ledger reconstruction from portfolio state; G5 strip starts clean at $0 deployed by game_date keying. 843/843 tests. |

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
