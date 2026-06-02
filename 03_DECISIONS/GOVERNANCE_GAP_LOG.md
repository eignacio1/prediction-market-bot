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
| Status | OPEN — HIGH severity for G6 evidence quality; paper only at current scale; immediate fix available (Path B pending DS decision) |

---

## Resolved Gaps

| Gap ID | Resolution Date | Resolution Summary |
|---|---|---|
| GG-001 | 2026-06-01 | ADR-0006: count gate deleted; pipeline + Kelly + kill switch are the risk framework |
| GG-002 | 2026-06-01 | ADR-0006 covers this; ARE WE COMPROMISED? watchdog added |
| GG-003 | 2026-06-01 | ADR-0007: GOVERNANCE_GAP_LOG.md mandated; ARE WE COMPROMISED? protocol added |
| GG-005 | 2026-06-01 | APR-0017 v2 ACCEPTED: all criteria expressed as rates/slopes with derived thresholds; Q7 protocol in CLAUDE.md |

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
