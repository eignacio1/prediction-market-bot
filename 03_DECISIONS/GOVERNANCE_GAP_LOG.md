# Governance Gap Log — Prediction Market Trading Bot

**Purpose:** Register every discovered governance process failure — decisions that should have been made and weren't, thresholds set as placeholders and never revisited, architectural assumptions that went undocumented. This is distinct from DECISION_LOG (records decisions *made*) and KNOWN_ISSUES (records runtime bugs). This records failures of the governance *system itself*.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-07-02 (SESSION 112 — GG-069 RESOLVED under T-221: FINAL-status gate added to `fetch_actual_hits`/`_fetch_mlb_hits`)  
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

## Gaps by Arm

**Generated, not hand-maintained (W60.3, 2026-10-08):** see `03_DECISIONS/GOVERNANCE_GAP_ARM_INDEX.md`, produced from the live entries by `python3 scripts/generate_gap_arm_index.py`. The T-374 hand-written index (frozen at 126 gaps, 2026-07-20) was replaced; its arm classification is preserved as the seed in `GOVERNANCE_GAP_ARM_SEED.txt`, and gaps registered since are keyword-assigned and marked `(auto)` until reviewed.

---
## Active Gaps


> **Restructure banner (2026-08-05, T-420):** this file was split by status.
> OPEN and IN PROGRESS gaps stay here, in structured form (`**Status:** ... · **Severity:** ...`
> immediately under each header, full original record preserved verbatim inside the
> `<details>` fold below it). RESOLVED and CLOSED-AS-ARTIFACT gaps moved **verbatim**,
> in full, to `GOVERNANCE_GAP_LOG_ARCHIVE.md` — nothing was summarized, reworded,
> re-scoped, or re-severitied in either direction. The "Gaps by Arm" index below is
> unchanged and still lists all gaps regardless of where their full record now lives.
> Severity is UNSPECIFIED wherever the original text carried no explicit severity
> signal — no severity was invented. See DECISION_LOG.md 2026-08-05 for the full
> rationale and the pre/post OPEN-count assertion that gated this merge.

### GG-004 — EV Validation Benchmark Was Never the Commercial Question

**Status:** OPEN · **Severity:** HIGH

**Update (W85.3, 2026-10-22):** `c4_risk_engine/exposure_gate.py` computes realized loss + open + settled-unresolved stake per book and system-wide, persists atomically, fails closed on missing/corrupt state; wired into T1 MLB only. Remaining: GG-1082. Status stays OPEN.

**Current state (2026-10-08, W59.1):** Sample-adequacy gate still the G6 blocker; governed per band by APR-0024 n*. Not re-derived this session. **Next:** Re-run run_power_calc.py at next governance scan.

<details>
<summary>Full record ▸</summary>


**Full history moved 2026-07-15 (ADR-0044 split, verified lossless via diff) to `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG004_ev_validation_benchmark_history.md`.** That file is the authoritative record of all 7 session-dated updates (2026-06-01 through 2026-07-12). Condensed current status below.

| Field | Detail |
|---|---|
| Gap ID | GG-004 |
| Arm | MLB |
| Category | Systemic research blind spot |
| Current status (2026-07-15) | Commercial question (does the model beat real Kalshi prices, not a `mip=0.50` coin-flip null?) remains formally OPEN. Latest MLB read (2026-07-08): n=169 unique resolved T1 positions, aggregate P&L **sign-flipped negative (−$44.76)** from the 2026-07-06 n=151 read (+$15.23, the first Tier-1-reached DIRECTIONAL_POSITIVE verdict). Edge-monotonicity guard: INCONCLUSIVE (Fisher p=0.2468), not anti-predictive. Under APR-0024's superseding `clean_n ≥ n*` standard (accepted 2026-07-12), neither T1 (clean_n=81/n*=2,322) nor T4M-PROJ (clean_n=338/n*=787) clears its own bar. GG-004 remains OPEN under either framework. |
| Disposition (this pass, 2026-07-15) | **(c) Reaffirmed as an intentional long-lived watch item.** This is not a unilateral verdict change — the n=169 negative read and the APR-0024 non-clearance both already stand as logged. Re-check trigger: next `run_exp017_mlb.py`/`run_t177_edge_monitor.py` re-run once either band's `clean_n` materially closes on its `n*` floor (T1 ETA ~15.8 weeks, T4M-PROJ ETA ~0.9 weeks per CLAUDE.md's 2026-07-11 cadence pull) — re-derive both ETAs at that check, they were provisional and cadence-immature when logged. |
| Full detail | See linked history file above for the complete Category/What-was-missed/Discovery/Resolution narrative across all 7 session dates. |

</details>

---

### GG-007 — T4/T5 Threshold Constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) Are Uncalibrated Skeleton Values

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** NBA is DARK per operator directive (resume ~1 month before 2026-27 tip-off); no new evidence this session. Constants unchanged. **Next:** Calibrate before any NBA T4 activation.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-007 |
| Arm | NBA |
| Category | Architectural placeholder — Phase 8 pre-activation gate |
| What was missed | `T4_MIN_DELTA_P = 0.08`, `T5_YES_CERTAINTY = 0.85`, `T5_NO_CERTAINTY = 0.15` were adopted as Phase 7 skeleton constants without empirical calibration against real in-play data. The SESSION 12 DECISION_LOG entry for T4_MIN_DELTA_P explicitly states: "must be calibrated against real in-play data before T4 ACTIVE designation — this value is a Phase 7 skeleton constant, not a validated production threshold." The governance gap is that no experiment is registered to perform this calibration, and no Phase 8 activation gate blocks on it. |
| When it should have been caught | Phase 8 infrastructure ADR — the third of the three Phase 8 blocker ADRs must include threshold calibration as a pre-activation gate |
| Phases it survived | Phase 7 skeleton (by design) — gap is forward-looking, not retroactive |
| Why it survived | Phase 7 correctly deferred calibration to Phase 8. Gap: no experiment was registered at Phase 7 build time to close it. Without a registered experiment, Phase 8 activation could proceed with the skeleton constants intact. |
| Impact | Uncalibrated `T4_MIN_DELTA_P` may be too loose (false fires on marginal signals) or too tight (misses genuine T4 edge). Uncalibrated T5 certainty bounds may trigger on near-certainty that isn't structurally certain given late-game variance. Either error direction produces realized EV below the model's estimate at live capital. |
| Discovery | ARE WE COMPROMISED? review of game_state_model.py — 2026-06-02 |
| Resolution | Register EXP-020 (T4_MIN_DELTA_P calibration against historical in-play score sequences) and EXP-021 (T5 certainty threshold calibration in final-3-minute game segments). Both must PASS before Phase 8 T4 activation ADR is signed. Threshold revision requires ADR amendment if materially different from skeleton values. T-128 registered. **ID renumber 2026-06-12 SESSION 56:** this entry originally reserved EXP-018/EXP-019, but those IDs were subsequently consumed by unrelated experiments (EXP-018 = adj_λ EV test, `scripts/run_exp018.py`; EXP-019A/B/C = NOISE_BUFFER_BAND calibration). The GG-007 calibration experiments are renumbered EXP-020/EXP-021. No experiment work existed under the old IDs for this gap — the renumber is purely registrational. |
| Status | OPEN — LOW severity now (T4/T5 not active); HIGH severity pre-Phase 8 activation. **Reaffirmed watch item, 2026-07-15 (T-368 odd-gap burn-down session):** re-read in full; premise unchanged — NBA T4/T5 remain tabled per standing operator directive, EXP-020/EXP-021 still unrun, no Phase 8 activation ADR exists. Not resolvable now (calibration requires live in-play data collection, which requires NBA reactivation) and not an escalation candidate (no Earl decision is being blocked today). **Re-check trigger: any session that drafts a Phase 8 T4/T5 activation ADR, or NBA reactivation per the ~1-month-pre-2026-27-season directive — whichever comes first.** |

</details>

---

### GG-014 — Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode

**Status:** PARTIALLY RESOLVED · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-014 |
| Arm | Core |
| Category | Execution integrity — rate limit characterization missing |
| What was missed | Kalshi's order placement API rate limits were not characterized before PIPE-03 was activated for multi-market execution. With 25+ bets per game night executing within a ~2 second burst window, Kalshi's `/portfolio/orders` endpoint returns HTTP 429 (Too Many Requests) for roughly 50% of calls. Paper mode logs positions regardless (portfolio write is local; the Kalshi API call is best-effort for order confirmation), so paper P&L tracking is unaffected. No retry logic exists. At live capital, these would be real execution failures — the bot would have C4-approved edge and model signal but fail to deploy capital for ~50% of intended bets. |
| When it should have been caught | Before PIPE-03 first activation; the Kalshi API rate limits should have been verified against the expected burst sizing (~25 orders in ~2s) before any live-mode execution ran. |
| Phases it survived | All PIPE-03 runs since Jun 4 22:00 UTC. 12 of 25 G3 positions have `kalshi_order_status: "failed: HTTP 429"`. |
| Why it survived | (1) Paper mode masks the severity — portfolio state is correct regardless of API status. (2) No monitoring alert fires on 429 response patterns. (3) The first game nights had fewer concurrent markets (Finals structure: 1 game/night, ~25 bets) — at regular season scale (400+ markets/night) the failure rate would likely be higher. |
| Impact | LOW now (paper mode; P&L unaffected). HIGH pre-G6: live capital execution failures for ~50% of approved bets means approximately half the model's edge is never deployed. Risk-adjusted return would be materially lower than paper period suggests. Also possible: systematic bias if 429 failures are not random (e.g., later bets in the burst are more likely to fail, meaning low-threshold / high-probability bets fail more often). |
| Discovery | 2026-06-05 SESSION 32 — `paper_portfolio.json` review: 12/25 open positions have `kalshi_order_status: "failed: HTTP 429"`. |
| Resolution | **PARTIAL — 2026-06-05 SESSION 33 (T-136).** sleep(0.5) deployed but ineffective (pre-T-136: 43.75% 429 rate, post-T-136: 50% 429 rate). **T-138 deployed 2026-06-08 SESSION 36:** exponential backoff retry (3 retries at 2s/4s/8s) added to `kalshi_client._post()/_get()` for **both 429 AND 503**. Root cause discovery: G3 night showed 18/20 orders as HTTP 503 (not 429) — 503 was not retried at all. Commit 4dd2c3d, 738/738 tests. **G3 effectiveness:** 2/20 orders resting (Wembanyama 35 NO, 30 NO); 18 were pre-fix 503s in portfolio. **G4 (3 orders, all succeeded):** kill switch triggered early; only 3 bets placed; 0/3 failures — inconclusive (too few orders to test burst behavior). **G5 (29 orders): T-138 INEFFECTIVE.** 9/29 = **31% failure rate** — "transient error — max retries (3) exceeded" for all 9. Failures clustered in latter orders of 29-order burst: Wembanyama NO×2 ($182.87), Brunson NO×4 ($57.55), KAT YES×1 ($22.97), Hart YES×2 ($13.88). Pattern: first ~20 orders succeed (resting), last ~9 hit persistent rate limits. Diagnosis: exponential backoff window (2+4+8=14s total) is too short for Kalshi's burst rate limit window at 29-order scale. Paper positions tracked regardless (paper P&L unaffected). G6 gate ≤5% BREACHED. **T-164 registered (SESSION 48):** investigate root cause (429 vs 503 classification; actual rate limit window); implement throttled order submission (inter-order sleep or batch sizing) before G6 live capital. |
| Status | **PARTIALLY RESOLVED — 2026-06-11 SESSION 49 (T-164).** Inter-order sleep 0.5→2.0s; MAX_RETRIES 3→4; RETRY_DELAY_S 1.0→2.0 (schedule 4/8/16/32s = 60s window). Batch order integrity report added to PIPE-03. OPEN until G6 batch confirms ≤5% failure rate in production. |

</details>

---

### GG-020 — Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts

**Status:** ACCEPTED UNCERTAINTY · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-020 |
| Arm | Core |
| Discovered | 2026-06-09 SESSION 42 — operator question on fee rate provenance during institutional hygiene sprint |
| Category | Governance provenance gap — documentation-sourced constant, no empirical verification |
| What was missed | `ADR-0016` establishes `fee(P) = 0.07 × P × (1−P)` as the Kalshi taker fee formula. `GG-009` discovery note states "Fee formula sourced from Kalshi API docs" — verbal assertion only. No URL is cited in ADR-0016 or GG-009. No documentation version is recorded. No verification against an actual Kalshi transaction receipt has been performed. Verification is structurally impossible in paper trading (no real orders are placed, no real fees charged). The 0.07 rate was taken from documentation at face value in SESSION 22 (2026-06-03) and embedded directly into ADR-0016, `run_paper_trade.py`, `run_pregame.py`, `run_t4_live.py`, `paper_trader.py`, and all fee-adjusted edge computations. |
| What is NOT a validation | `complement_lock_scanner.py:DEFAULT_FEE_PER_CONTRACT = 0.030` (labeled "EXP-010 confirmed Kalshi vig") is the bid-ask spread — a different cost metric. EXP-010 confirming the vig does NOT validate the taker fee rate. These are distinct quantities. |
| When it should have been caught | ADR-0016 acceptance (2026-06-04 SESSION 30) — when the fee formula was formally adopted, a source citation and verification plan should have been part of the acceptance criteria. |
| Impact | LOW now (paper mode; fee is notional; direction of impact well-understood). MEDIUM pre-G6: ADR-0005 break-even analysis depends on the fee drag numbers from T-150, which are computed using 0.07. If Kalshi's actual taker fee differs — e.g., 0.05 or 0.10 — all fee-adjusted edge computations, the T-149 C4 gate threshold, and T-150 break-even estimates are wrong by a proportional factor. At Finals throughput (~$27/game combined T1+T4 fee drag from T-150 analysis), a 30% error in the fee rate = ~$8/game error in the break-even model. |
| Discovery method | Operator question: "Is that 0.07 an arbitrary number? Did you log it as the metric for the fees based on scrubbing through the entire Kalshi database?" — SESSION 42 audit of fee rate provenance revealed no URL, no version, no receipt verification anywhere in the governance artifacts. |
| Resolution path | **Before ADR-0005 (live capital authorization):** (1) Locate the current Kalshi API documentation fee schedule and verify `fee = 0.07 × P × (1−P)` taker. Record URL and access date in ADR-0016 amendment. (2) Place one real live trade post-G6 authorization and verify the fee charged on the receipt matches the formula. If the rate differs, supersede ADR-0016 with corrected constant and rerun T-150 break-even analysis. (3) Both verifications must be complete before ADR-0005 is accepted. Register T-151 (operator action: read current Kalshi fee documentation and record URL + rate in governance artifact). |
| Status | **ACCEPTED UNCERTAINTY (pre-G6) — 2026-07-16, GG-easy-sweep session, T-374 scope, per Earl's explicit session directive to "resolve GG-020 fee verification one way or the other."** One final verification attempt made this session: `WebSearch` for the Kalshi fee schedule/API docs returned "session limit reached" before any results; `WebFetch` against `kalshi.com/docs/kalshi-fee-schedule.pdf` returned HTTP 429 (identical failure mode to SESSION 43's attempt on the same URL, 37 days earlier); a follow-up `WebFetch` against the redirected `docs.kalshi.com` API-fees reference page also hit the session limit before returning content. All three external-verification channels available in this environment are exhausted for this session. This is not a new data point beyond SESSION 43's partial verification (below) — it confirms the same URL is still gated and no new source was reachable. **Rather than reaffirm OPEN indefinitely a fourth time (2026-06-09, 2026-07-04-ish, 2026-07-15, now), this is being formally closed out for the pre-G6 period as an accepted, labeled uncertainty:** the 0.07 rate is supported by ≥2 independent sources (marketmath.io's stated "7% × p × (1−p)"; SESSION 43's initial search summary), one conflicting source (predictionhunt.com) suggests ~0.06 for sports markets specifically but does not confirm it, and no actual Kalshi transaction receipt has ever been available to check against (paper trading only — structurally impossible pre-G6). The error direction, if 0.06 is correct, is conservative (over-deduct fees → reject profitable bets at the margin; EV evidence is understated, not overstated) — this bounds the downside of proceeding on 0.07 without further re-litigation. **Disposition: pre-G6, treat 0.07 as an accepted working constant with known, bounded, conservative-direction uncertainty — not a blocker requiring further verification attempts before G6.** T-151 (first live receipt check) remains the sole re-open/re-verify trigger and is unchanged, gated on post-G6/ADR-0005 real capital. Historical partial verification (2026-06-09 SESSION 43, unchanged): marketmath.io states "Fee per contract = 7% × p × (1−p)" across all contract types; Kalshi API does not expose fee rates in market data; Kalshi fee schedule PDF was rate-limited then too. |

</details>

---

### GG-027 — PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Environment Classifier Not Built

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** NBA is DARK per operator directive (resume ~1 month before 2026-27 tip-off); no new evidence this session. **Next:** Revisit at NBA preseason.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-027 |
| Arm | NBA |
| Discovered | 2026-06-11 SESSION 50 — operator architectural direction: pressure-context categorization for decision tree filters |
| Category | Architectural capability gap — registered feature not yet integrated across full band stack |
| What was missed | The Player Archetype Matrix (PAM v4) is operationalized in C2 (`QualitativeSignalStore`) and the prod model uses 47 PAM features (prf_w01–15, mod_01–32). However: (1) T2/T3/T5 bands have no PAM wiring — `run_t2_sameday.py`, `run_t3_pretip.py`, and T5 LateGameArithmetic operate without archetype context; (2) T4 `T4EventLoop` received archetype register wiring in SESSION 50 but the archetype does not yet affect the routing math (passed through to audit log only); (3) the "pressure-context environment classifier" described by the operator — game-environment categorical modifiers (high-pressure Finals/elimination context, expanded-role context for role players, crowd/psychological context) — is entirely unbuilt as of SESSION 50; (4) QS snapshot age: classifications dated 2026-05-28 have not been updated for Finals-specific role changes (e.g. Alvarado Q4 expanded role in G4). |
| When it should have been caught | ADR-0019 (exit mechanics) acceptance — when PAM features were confirmed live in the model, a task for full band integration should have been registered. The operator's architectural direction toward environment-context categorization makes the gap more visible. |
| Impact | LOW now — T2/T3/T5 are SKELETON/BLOCKED; T4 routing is correct without archetype math (ADR-0021 handles materiality). HIGH pre-MLB activation — regular season requires full band coverage; environment classifier is architecturally essential for the "Wemby 10 RBG ≠ Zubac 10 RBG" disambiguation at scale. |
| Resolution path | T-165: Full PAM integration across T2/T3/T5 bands + environment classifier ADR — MLB activation gate. Scope: (a) EnvironmentClassifier in C2 (game-level pressure score: elimination_flag, series_momentum, crowd_premium, role_expansion_flag for role players); (b) archetype × environment interaction in C3 (uncertainty multiplier on model_p for sparse-data role players in high-pressure contexts); (c) dynamic MIN_EDGE_TO_APPROVE in decision tree routing per environment class; (d) T2/T3/T5 archetype register wiring matching T1/T4 pattern. |
| Status | OPEN — **re-scoped 2026-07-06 SESSION 123.** This entry, its "What was missed" text, and T-165 all describe NBA's bands (`run_t2_sameday.py`, `run_t3_pretip.py`) and NBA's PAM v4 taxonomy — GG-027 stays confined to that scope and stays dormant while NBA is tabled (see NBA-deferred directive). **Attempting to action this for MLB (T2/T3 MLB — `run_t2_mlb_sameday.py`, `run_t3_mlb_pretip.py`) this session surfaced that the premise "wire PAM into T2/T3 MLB" does not hold**: direct inspection confirms PAM v4 is NBA-only end-to-end — `qualitative_data/pam_v4/SCHEMA.md` requires `player_id` to be an `nba_api` ID, the only two classification snapshots on disk (`QS-2026-05-28-001/002`) are NBA players, the PRF-1–15 archetype taxonomy is sourced from `Player_Attribute_Matrix_v4.docx` (a basketball role taxonomy — GG-027's own "Wemby ≠ Zubac" example is NBA-specific), and no MLB file anywhere (including the already-Tier-1-validated T1/T4M-PROJ MLB bands) references `prf_w0*`/`mod_0*`/`DS01_FEATURE_NAMES`. There is no MLB archetype system to wire in — building one is a from-scratch DS-source project (taxonomy design, player classification, an ADR per the environment-classifier requirement already in this entry's Resolution path, and a decision on how a frozen, already-validated MLB model consumes a brand-new feature set under Hard Rule 4), not a same-sprint wiring fix. That MLB-side work is tracked separately as **T-243** (registered 2026-07-06, unscoped/unsized — do not treat as "in progress"). GG-027/T-165 remain exactly as originally scoped: NBA-only, dormant until NBA bands approach active status. **Reaffirmed watch item, 2026-07-15 (T-368 odd-gap burn-down session):** confirmed still NBA-only in scope, still dormant per NBA-tabled directive; T-243 (MLB-side, separate/unscoped) confirmed still not started — not conflating the two per this entry's own 2026-07-06 correction. Not resolvable now (from-scratch DS taxonomy project blocked on NBA reactivation) and not an escalation candidate. **Re-check trigger: NBA reactivation (per standing operator directive, ~1 month before 2026-27 season) — at that point both GG-027/T-165 (NBA wiring) and whether T-243 (MLB archetype system) should be picked up become live questions again.** |

</details>

---

### GG-037 — Calibration Collapse + Inverted Edge Realization: the Model's Edge Signal Is Anti-Predictive

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Alpha half still unexplained per entry; MLB-side analogue is GG-105. **Next:** Fold NBA retest into NBA preseason work.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-037 |
| Arm | NBA |
| Status | **OPEN (alpha half) — ADR-0044 split applied 2026-07-15 (T-368 odd-gap burn-down session).** Calibration half RESOLVED via ADR-0027 (temperature scaling, NBA T=2.05). Alpha half remains OPEN: post-calibration residual edge on the n=158 NBA Finals dataset is still anti-predictive (edge>0 wr 0.356 vs edge≤0 wr 0.747) — this is a real, not-yet-explained finding, not just overconfidence. Original deferral trigger was "EXP-017 at scale (MLB dark period + NBA regular season)." **Reaffirmed, not resolved, 2026-07-15:** EXP-017 MLB has since run and cleared ADR-0024 Tier 1 (n=151, DIRECTIONAL_POSITIVE per CLAUDE.md) — a materially relevant new data point in the *opposite* direction from GG-037's NBA finding, but MLB and NBA are separate pools/theses (CLAUDE.md's dual-ledger framing) and the NBA regular-season leg of the original deferral is still untested (NBA tabled). Whether EXP-017 MLB's positive result should be read as satisfying GG-037's deferral condition is a model-validity call this session is not authorized to make unilaterally (Hard Rule 3) — left for Earl. Not an escalation candidate today (no immediate decision is blocked); reaffirmed as a watch item. **Re-check trigger: NBA regular-season data becomes available (NBA reactivation), OR EXP-017 MLB clears Tier 2 (n≥500) — whichever comes first.** **Full investigative history (2026-06-16 SESSION 64 through 2026-06-22 SESSION 68): see `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG037_FULL_HISTORY.md`** (verbatim, lossless move verified 2026-07-15). Linked: ADR-0027, [[GG-004]], ADR-0024, ADR-0004/ADR-0015 (amended), GG-008. |

</details>

---

### GG-038 — T4 Kill Switch SLA: 60s NFR-03 Is 12× Too Slow for Continuous T4 Evaluation

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** ADR-0060 (NFR-03 band-level kill-switch latency remedy) ACCEPTED 2026-09-03; implementation not verified this session, so not closed. **Next:** Verify band-level kill switch latency measurement against ADR-0060 acceptance criteria.
**Actively-Broken:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-038 |
| Arm | NBA |
| Category | Architectural gap — safety SLA insufficient for new execution regime |
| What was missed | NFR-03 specifies kill switch ≤60 seconds. At Kalshi's 60 calls/min execution rate, 60 seconds = up to 60 additional bets submitted between kill trigger and halt. For monolithic T4 with a small pre-scheduled bet set, this was acceptable. For continuous T4 evaluation potentially approving multiple bets per second, 60 seconds of uncontrolled execution after a kill trigger represents unacceptable capital exposure. |
| When it should have been caught | When ADR-0029 T4 sub-band architecture was first designed — the moment continuous evaluation was proposed, the kill switch SLA should have been immediately re-examined. |
| Phases it survived | T4 is BLOCKED (Phase 8+), so no live harm has occurred. |
| Why it survived | NFR-03 was designed for a batch-bet system (T1: ~10–20 bets per night). The T4 continuous evaluation architecture is new (SESSION 66). |
| Impact | **HIGH pre-Phase 8.** Without a T4-specific fast-halt mechanism (≤5s), a kill trigger during a live T4 evaluation burst could result in 60+ bets submitted before halt — the exact scenario the kill switch exists to prevent. |
| Discovery | SESSION 66 — ADR-0029 hygiene check. Surfaced during three-layer T4 architecture design. |
| Resolution | New ADR amending NFR-03 for T4 band + C7 implementation of two-tier fast-halt mechanism: (1) T4-specific halt in ≤5s; (2) system-level halt preserves current 60s SLA for T1/T2/T3. Both tiers must operate independently. |
| Status | **OPEN — SESSION 105 CORRECTION: paper-trading exemption RETRACTED.** ADR-0036's exemption was true as a fact (T4FastHalt exists in `t4_live_runner.py`, SESSION 71) but conflated the NBA T4 engine with MLB — `t4_live_runner.py`/`t4_price_cache.py`/`t4_execution_engine.py` are the NBA sub-band stack (ADR-0029), not MLB; MLB T4 (`run_t4_mlb_live.py`) has no sub-band architecture and does not consume this code at all. See ADR-0037 (correction). No paper-trading exemption currently applies to any live MLB work. **Remains OPEN.** Formal production validation of T4FastHalt (as an NBA-scope item) is tabled per the NBA work-tabling directive until ~1 month before 2026-27 tip-off. Linked: ADR-0029, ADR-0036, ADR-0037, GG-061, NFR-03. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed as watch item, no change** — this is an NBA-scoped architectural gap (NBA T4 sub-band stack) with zero live exposure while NBA is tabled; nothing has changed since SESSION 105's correction. Re-check trigger unchanged: NBA reactivation window (~1 month before 2026-27 tip-off), same trigger as [[GG-040]]. |

**Addendum (2026-08-26, T-489, MEASUREMENT ONLY — scope mismatch flagged, not silently absorbed):** GG-038's own `Arm` field says NBA; T-489's task brief asked for MLB/T4M-PROJ figures. Both arms now have real, measured numbers below rather than the design-time estimate above — do not conflate the two arms' figures when reading this gap.

Test harnesses: `tests/test_gg038_t4_mlb_halt_latency.py`, `tests/test_gg038_system_halt_latency.py`, `tests/test_gg038_non_coupling.py` (branch `session/20260826T045856Z-t489-gg038-killswitch-sla`). Three real, distinct mechanisms exist, not one: (1) MLB T4 band-level filesystem flag (`run_t4_mlb_live.KILL_SWITCH_PATH`, checked via `kill_switch_armed()`), checked at top-of-loop and per-game, **never inside `_run_cycle()` and never during the unconditional 45s post-cycle `time.sleep`**; (2) system-level `c7_monitoring.monitor.SystemMonitor.trigger_kill_switch()`; (3) `RiskEngine.evaluate_forecast()`'s per-evaluation `approval_status == "KILL_SWITCH"` on drawdown breach, which both T1 and T4 MLB receive (both pass `current_drawdown_pct` in) but only T1 branches on.

**TASK 1 — MLB T4 band-level detection latency (n=200 simulated trials, fake clock driving the real check topology + primitives):** min=0.014s p50=22.285s p90=42.720s p99=50.855s max=51.236s. 0% of simulated trials exceed 60s — **structural PASS against NFR-03**, but this is a synthetic lower bound only (POLL_INTERVAL_S=45s + measured `_run_cycle()` duration, no network I/O modeled). **Empirical cross-check against 48 real cycles pulled live from the VPS same-day (`t4_mlb_cycle_log.jsonl`, 2026-08-26): real cycle-start-to-cycle-start gap min=51.47s p50=66.96s p90=74.67s max=81.19s — every real percentile from p50 up ALREADY EXCEEDS the 60s bar.** The gap between the synthetic 45-52s structural bound and the real 51-81s measured gap is attributed to unmodeled network I/O (ESPN/Kalshi fetch) inside the real loop; this is a real, measured discrepancy, not test error — **the honest verdict is FAIL against NFR-03 using the only number that reflects the real production system (p50=66.96s, p90=74.67s, max=81.19s all >60s)**, not the PASS the synthetic harness alone would suggest.

**TASK 2 — System-level halt latency (n=150 real, non-simulated trials of `SystemMonitor.trigger_kill_switch()`):** min=0.0250ms p50=0.0270ms p90=0.0320ms max=0.0490ms against `KILL_SWITCH_SLA_MS=60000` — trivially **PASS**, sub-millisecond. **Caveat that makes the PASS not mean what it sounds like: zero MLB pipelines read `is_kill_switch_active`.** `run_t4_mlb_live.py` does not import `c7_monitoring.monitor` at all; `run_mlb_paper_trade.py` imports `SystemMonitor` only for post-hoc `.check_portfolio_pnl()` reporting. A fast flag-set has zero enforcement effect on either live MLB process today. Confirmed also: `risk.py`'s two `trigger_kill_switch()` references (lines 224/227) are inside a class docstring usage example, not executable code — `risk.py` never calls the real mechanism.

**TASK 3 — Non-coupling, verified by construction (3 tests, all passing):** (a) tripping the MLB band-level flag leaves `SystemMonitor` untouched — true, but an accident of the two mechanisms sharing no code path, not a designed guarantee. (b) tripping the system-level switch has no assertable effect on either MLB module (neither exposes the symbol a consumer would need) — **"the system switch halts everything" does NOT currently hold for the MLB books.** (c) asymmetric handling of the risk-engine `KILL_SWITCH` status, confirmed via `inspect.getsource()`: `run_mlb_paper_trade.py` (T1) branches on the literal string `"KILL_SWITCH"` and self-halts remaining evaluations for that cron run; `run_t4_mlb_live.py` (T4) has zero such branch anywhere in its source and treats a KILL_SWITCH approval identically to an ordinary REJECTED one — skip this ticker, keep looping. Currently low-dollar-stakes only because ADR-0048 zeroed T4M_PROJ's `kelly_fraction` to 0.0 — the architectural gap is real regardless of current sizing.

**TASK 4 — evaluations inside the measured window:** real production rate ≈8.33 (player,threshold) evaluations/cycle (400 rows / 48 cycles, live VPS pull, 2026-08-26). At that rate: structural-harness p50 (22.29s) ≈2.8 evals, p90 (42.72s) ≈5.3 evals, max (51.24s) ≈6.4 evals in-flight during detection; using the more trustworthy real empirical cycle-gap instead, p50 (66.96s) ≈8.3 evals (≈1 full cycle), p90 (74.67s) ≈9.3 evals, max (81.19s) ≈10.1 evals. **The task brief's own "~76 bets/day" figure does not trace to any sourced measurement in this repo** — grepped; the only hits are the task brief text itself (`04_EXECUTION/ACTIVE_QUEUE.md:524`) and an unrelated "76s" runtime estimate in an unrelated DECISION_LOG entry — so it is not used above. Governing caveat: ADR-0048 has `T4M_PROJ.kelly_fraction = 0.0`, so every one of these in-window evaluations currently carries zero live capital exposure regardless of measured latency, pending edge-conditional reactivation.

**TASK 5 / T1 kill-path assessment (auxiliary, per T-493 T1 reopening):** T1's real requirement is two-part: (a) does a trip block the next cron run, and (b) can existing open exposure be force-closed before natural resolution. **(a) SATISFIED** — `run_mlb_paper_trade.py` recomputes `current_drawdown_pct` fresh from persisted ledger state (`trader.get_state()`) every process invocation, so a real ≥20% drawdown reasserts `KILL_SWITCH` on the very next run's first evaluation; the halt is not a one-run-only, in-memory-only signal. **(b) ABSENT — registered separately as GG-209, not built here per task instruction.** See GG-209 below.

</details>

---

### GG-039 — T4 Price Cache / Staleness Check Architecture

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** NBA is DARK per operator directive (resume ~1 month before 2026-27 tip-off); no new evidence this session. **Next:** Revisit at NBA preseason.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-039 |
| Arm | NBA |
| Category | Architectural gap — missing component required for Layer 2 staleness arbitration |
| What was missed | ADR-0029's Layer 2 execution queue requires current Kalshi market prices to run the staleness check on each dequeued bet. The existing venue constraint for T4 specifies `max_api_calls_per_decision = 0` — zero live API calls at execution time. These two requirements are in direct tension: the staleness check needs current prices but cannot call the API at execution time. |
| When it should have been caught | When the staleness-arbitration execution queue was designed in T-179 (SESSION 66). This gap is intrinsic to the architecture — it cannot be discovered before the architecture is specified. |
| Phases it survived | T4 is BLOCKED. No live harm. |
| Why it survived | The gap is created by the architecture specified in this session. It has not had time to "survive" any phase. |
| Impact | **MEDIUM — design gap only; no live capital risk until Phase 8.** If unresolved, the staleness check cannot function as designed and the execution queue would either need to drop all bets without a price check (unsafe) or use stale prices from trade time (defeats the purpose). |
| Discovery | SESSION 66 — ADR-0029 hygiene check. |
| Resolution | Design and implement a separate read-only price polling loop: polls Kalshi market prices for all open markets at a cadence ≤ the shortest expected edge window across active T4 sub-bands; writes to an in-memory price cache; operates independently of the execution rate limit budget (not counted as execution API calls). Cache staleness windows per sub-band defined in ADR-0029. Full architectural design requires a separate ADR. |
| Status | **OPEN — SESSION 105 CORRECTION: paper-trading exemption RETRACTED.** `fetch_player_points_markets()` (the function this exemption cited) is an NBA-only function — points props, not MLB hits. ADR-0036 conflated the NBA T4 engine (ADR-0029, `t4_live_runner.py`/`t4_execution_engine.py`) with MLB; no MLB sub-band system exists for this exemption to apply to. See ADR-0037 (correction). **Remains OPEN.** MLB's actual T4 runner (`run_t4_mlb_live.py`) has no sub-band price-cache dependency of this kind — it is a separate, flat-tree implementation. Linked: ADR-0029, ADR-0036, ADR-0037, GG-061. **Reaffirmed watch item, 2026-07-15 (T-368 odd-gap burn-down session):** re-confirmed scope is NBA T4 sub-band architecture only (ADR-0029); MLB's flat T4M-PROJ engine still has no analogous dependency and remains unaffected. Not resolvable now (design work is gated on NBA T4 sub-band reactivation, which is dark) and not an escalation candidate. **Re-check trigger: any session that resumes NBA T4 sub-band (ADR-0029) work, or drafts the Phase 8 T4 activation ADR referenced in GG-007.** |

</details>

---

### GG-040 — T4 Real-Time Data Sources: Required Feeds Not in Current C1 Architecture

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** NBA is DARK per operator directive (resume ~1 month before 2026-27 tip-off); no new evidence this session. MLB analogue is GG-066. **Next:** Revisit at NBA preseason.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-040 |
| Arm | NBA |
| Category | Architectural gap — data source prerequisite for T4 sub-band activation |
| What was missed | T4 sub-bands require data feeds that do not exist in the current C1 implementation. Current C1 uses ESPN scoreboard API for box scores with multi-minute latency — insufficient for T4-EVENT (requires ≤2s event detection) and T4-LINEUP (requires ≤5s substitution detection). T4-MICRO requires real-time order book feed. T4-SENTIMENT requires Kalshi tick-level price history. None of these are built. |
| When it should have been caught | During T4 Phase 8 planning. The gap exists because T4 is BLOCKED and no Phase 8 data source planning has been done. |
| Phases it survived | T4 BLOCKED — no live harm. |
| Why it survived | T4 Phase 8 data source requirements were never formally inventoried. ADR-0029 is the first document to specify them concretely. |
| Impact | **HIGH pre-Phase 8; LOW now.** Without Phase 8 data sources, T4-EVENT, T4-LINEUP, T4-MICRO, and T4-SENTIMENT cannot function as designed. T4-STAGED and T4-PROJ can function with enhanced versions of current C1 data. |
| Discovery | SESSION 66 — ADR-0029 design analysis. |
| Resolution | Phase 8 C1 rebuild to add: (1) Live box score feed with ≤2s event detection latency (T4-EVENT, T4-ARITH); (2) Live play-by-play / lineups API with ≤5s substitution detection (T4-LINEUP); (3) Kalshi tick-level market price feed (T4-MICRO, T4-SENTIMENT). Each requires vendor evaluation and C1 module design. Full data source ADR required before Phase 8. |
| Status | **OPEN — SESSION 105 CORRECTION: "PARTIALLY RESOLVED" status RETRACTED.** ADR-0036's sub-band data-sufficiency table described T4-PROJ/ARITH/FLOW/BLOWOUT inputs in MLB vocabulary ("batter stats," "innings," "batting slot") but was actually evaluated against `t4_execution_engine.py` — the NBA sub-band engine, which operates on `pts_so_far`/`quarter`, not MLB fields. No MLB sub-band architecture exists in the codebase for this table to describe; the ruling does not correspond to any real code. See ADR-0037 (correction). **Reverts to OPEN, fully unresolved**, pending either (a) a genuine MLB sub-band build with its own data-sufficiency analysis, or (b) confirmation that the NBA ruling stands on its own NBA-scoped merits once NBA work resumes (~1 month before 2026-27 tip-off). Linked: ADR-0029, ADR-0036, ADR-0037, GG-038, GG-039, GG-061. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed as watch item, no change** — same NBA-tabled class as [[GG-038]]; no genuine MLB sub-band build has been authorized or started (Tier B roster, incl. T4M-EVENT/LINEUP, remains scoping-only per CLAUDE.md, requiring fresh DS sign-off before implementation). Re-check trigger unchanged: NBA reactivation window, or a future DS-authorized MLB sub-band build (whichever comes first). |

</details>

---

### GG-041 — KXNBAPTS Orderbook Depth Data: Finals Window Missed; ADR-0005 Limit Empirical Basis Absent

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** NBA is DARK per operator directive (resume ~1 month before 2026-27 tip-off); no new evidence this session. Finals window is past; data cannot be recovered retroactively. **Next:** Capture depth in next NBA season via archiver depth sampling.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-041 |
| Arm | NBA |
| Discovered | SESSION 72 — 2026-06-22; T-127 execution attempt found no active KXNBAPTS markets |
| Category | Data collection miss — evidence required for ADR-0005 hard limit not captured during the only available window |
| What was missed | Live KXNBAPTS orderbook depth data was not captured during the 2026 NBA Finals window (Jun 3–22). T-127 required querying `GET /markets/{ticker}/orderbook` during an active Finals game day to set an empirical `max_order_pct_of_depth` limit for ADR-0005. The one logged run (`logs/orderbook_depth_20260602_151325.json`, 2026-06-02) queried before Finals markets opened — all 5 markets showed `combined_depth_usd: 0`. No subsequent script run was triggered during any Finals game day. VPS has zero orderbook depth logs. All KXNBAPTS markets finalized 2026-06-14 (after G5 on 2026-06-13). |
| When it should have been caught | Any Finals game day Jun 3–13 during active market hours. T-127 was registered as HIGH priority with explicit "if this window is missed, no equivalent data exists until 2026-27 pre-season" warning. |
| Phases survived | G5 |
| Why it survived | T-127 script automation was registered as COMPLETE (script built); but script execution during an active game day was not automated or calendared. The single pre-Finals run returned zeros and was not flagged as "wrong window." No VPS cron for orderbook depth polling was set up. |
| Impact | **LOW now (dark period, no live capital).** ADR-0005 (`max_order_pct_of_depth` hard limit in `_HARD_LIMITS`) cannot be set on empirical Finals orderbook data. The limit must use a conservative placeholder or be deferred to 2026-27 regular season Day 1 data collection. Impact is LOW because no live capital is at risk until G6; the limit is a G6 prerequisite, not a paper-trading constraint. |
| Discovery | SESSION 72 — `python3 scripts/query_orderbook_depth.py` returned "No active KXNBAPTS markets found." Confirmed via VPS run and direct Kalshi API orderbook query (empty `yes_dollars`/`no_dollars` arrays on finalized markets). |
| Resolution | Re-run `scripts/query_orderbook_depth.py` on 2026-27 regular season Day 1 (target October 2026, Phase 4). Capture live depth for 3–5 active KXNBAPTS contracts during a regular-season game window. Use result to set `max_order_pct_of_depth` in ADR-0005. Until then: ADR-0005 must not specify an empirical `max_order_pct_of_depth` value; any placeholder must be labeled provisional pending Phase 4 data. |
| Status | **OPEN.** Deferred to Phase 4 (October 2026 — 2026-27 regular season Day 1). LOW urgency. Linked: T-127, KI-023, ADR-0005. **Reaffirmed watch item, 2026-07-15 (T-368 odd-gap burn-down session):** confirmed Phase 4 has not arrived and no interim data collection window occurred. Not resolvable now (data collection requires a live NBA game day, currently off-season/tabled) and not an escalation candidate. **Re-check trigger: 2026-27 NBA regular season Day 1 (target October 2026) — same trigger as originally specified, restated as current.** |

---

| Gap ID | GG-042 |
| Arm | MLB |
| Discovered | SESSION 81 — 2026-06-24; T-187B per-threshold model diagnostic |
| Category | Active scope exclusion — threshold with inadequate Brier signal deferred pending feature injection |
| What was missed | MLB KXMLBHIT threshold t=3 (3+ hits per game) excluded from `THRESHOLDS` in `train_mlb_model.py` and `_MODEL_THRESHOLDS` in `run_mlb_paper_trade.py`. Exclusion rationale: at t=3, base rate=3.9% and AUC=0.61 produce a Brier improvement of only +0.0002 (shadow gate requires ≥0.001). Even if Brier passed, t=3 bets would almost never fire — model predicts ~3.9% while Kalshi asks ~8¢, always negative edge. The t=3 market exists on Kalshi (threshold 4 in Kalshi ticker format: `KXMLBHIT-...-4`) but the bot will skip it with a C6 log entry on every run. |
| When it should have been caught | Before T-183 architecture was committed. The pooled-model approach masked per-threshold base-rate divergence; the ECE failure on the pooled model forced the per-threshold redesign that revealed t=3 inadequacy. |
| Phases survived | N/A — pre-paper-trading discovery; no capital at risk. |
| Why it survived | T-183 (initial training) used a pooled model which never triggered per-threshold Brier checks; the ECE failure on the first real training run (T-187B setup) forced the diagnostic. |
| Impact | **LOW — paper trading only.** t=3 markets are skipped silently; no bets are placed. No capital risk. EXP-017 commercial validation accumulates t=1 and t=2 bets only, which is the statistically meaningful sample. t=3 exclusion does not affect G6 evidence review. |
| Discovery | SESSION 81 — T-187B per-threshold diagnostic: separate pipeline fit per threshold revealed t=3 Brier delta=+0.0002 < 0.001 gate. Confirmed that even at AUC=0.61, the low base rate (3.9%) means correct t=3 predictions contribute near-zero Brier improvement in absolute terms. |
| Resolution | **T-187H (2026-06-24, SESSION 82) — shadow gate re-evaluation COMPLETE. VALID NEGATIVE — structural failure confirmed.** T-187G's live SP overlay prerequisite was met. SP coverage verified: 99.9% of t=3 positive events (h≥3) already had `opp_sp_is_known=1` in training data. T-187G addresses inference-time SP staleness only — it does not change training data. Shadow gate re-evaluation: Brier delta=+0.0002 (FAIL — identical to T-187B), ECE=0.0037 (PASS), AUC=0.6141. Score distribution: p50=0.037 (≈ base rate); only 1.9% of holdout predictions exceed 0.08 (≈ Kalshi market price). Root cause is structural: at 3.9% base rate, AUC=0.61 cannot produce absolute Brier delta ≥0.001. Further reconsideration requires architectural improvement (non-linear model, richer pitcher-batter matchup features, or lower Kalshi market price ≤5–6%) — not SP data quality improvement. `THRESHOLDS = [1, 2]` and `_EXCLUDED_THRESHOLDS = [3]` remain unchanged. |
| Status | **DEFERRED — structural.** T-187H (2026-06-24 SESSION 82) confirmed the failure is base-rate structural, not a data quality issue resolvable by better SP coverage. t=3 deferred indefinitely pending architectural improvement. LOW urgency. Linked: T-187B, T-187G, T-187H, GG-004. |

</details>

---

### GG-045 — Maximum Effective Bankroll Constrained by Kalshi Market Depth: Capital Ceiling Unanalyzed

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** CLAUDE.md now says depth is volatile (GG-155/T-411, 10-100x intraday); no fixed ceiling can be documented. Operator-blocked. **Next:** Operator decision on a live-depth sizing gate.
**Blocked-On-Operator:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-045 |
| Arm | Core |
| Category | Systemic blind spot — scaling ceiling absent from governance documentation |
| What was missed | Kelly criterion assumes infinite market depth. Kalshi KXMLBHIT player prop markets are thin (estimated $500–$2,000 per market). At $1K bankroll with 25% Kelly fraction, position sizes are $50–$250 — within market depth. At $10K+ bankroll, full Kelly sizing would start moving prices against the bot, degrading edge before the position fills. The maximum effective bankroll this strategy can deploy is constrained by Kalshi market depth, independent of bankroll math or Kelly fraction calibration. This ceiling has never been analyzed or documented. Current paper-trading bankroll ($1,000 reset) is well below any likely ceiling. The gap becomes binding during G8–G9 (multi-sport, large capital deployment). |
| When it should have been caught | Before G6 go/no-go on live capital. Current $1K paper makes it non-urgent, but the live capital threshold (G6: 30 resolved bets, positive P&L) does not include market depth analysis as a gate condition. If live capital is authorized and then scaled, the ceiling could be hit without warning. |
| Phases it survived | G0–G5 (bankroll small enough that depth is not binding at any point in the paper period) |
| Why it survived | Kelly sizing math is correct at current bankroll. Market depth was never explicitly modeled — the system treats Kalshi markets as having infinite liquidity, which is correct at $1K but not at scale. |
| Impact | LOW now ($1K paper). MEDIUM at G6 live capital ($1K–$5K depending on market). HIGH at G8–G9 (multi-sport deployment, $10K+). If unaddressed, live capital deployment could hit the depth ceiling without a mechanism to detect it — positions partially fill at degraded prices, effective edge disappears, but C4 continues sizing at full Kelly. |
| Discovery | SESSION 94 (2026-06-26) — strategic read-through of project by external analyst; surfaced in four-point structural assessment of project architecture. |
| Resolution | Pre-G8: empirical analysis of Kalshi KXMLBHIT order book depth per market; derive maximum effective stake per market as a function of market depth; add depth-aware position size cap to C4 (overrides Kelly when market is thin). Alternatively: accept the ceiling as a known hard limit, document the maximum deployable bankroll explicitly, and commit to never exceeding it without a depth re-analysis. |
| Status | **OPEN.** LOW urgency (current bankroll $1,000). Must be addressed before G8 live capital scaling beyond estimated market depth ceiling. **Reaffirmed watch item, 2026-07-15 (T-368 odd-gap burn-down session):** re-read in full; premise unchanged, current paper bankroll still well under any plausible depth ceiling, G8 not imminent. The underlying "$500-$2,000 per market estimated" figure is itself flagged as an estimate both here and in CLAUDE.md — independently re-verifying that estimate was judged out of scope for this pass (not a decision only Earl can make, but a data-collection task, not a burn-down verdict). Not resolvable now (empirical order-book depth analysis is pre-G8 scoped work, not urgent at current scale) and not an escalation candidate. **Re-check trigger: pre-G8 gate review, or bankroll approaching an order of magnitude above current ($5K+), whichever comes first.** **Empirical groundwork started 2026-07-17 (T-377, isolated worktree `session/20260717T051845Z-gg045-depth-analysis`):** built `scripts/query_orderbook_depth_mlb.py` (MLB-scoped, mirrors NBA-scoped `scripts/query_orderbook_depth.py` from T-127/KI-023 without modifying it) and ran it live against production Kalshi against 30 open KXMLBHIT markets spanning 5+ distinct games (STL@AZ, WSH@ATH, SF@SEA, BAL@HOU, and others in the 2026-07-17 slate). **Result: `combined_depth_usd = $0.00` on all 30 markets sampled — zero orderbook depth pregame.** Sample was pulled at 2026-07-17T05:27 UTC, ~12 hours before the day's first scheduled first pitch (17:35 UTC) and ~4.5h after the prior live game (PHI@NYM) had already gone final — i.e., no MLB game was live anywhere at sample time (confirmed via ESPN scoreboard). This replicates the exact GG-041 dead-end (NBA KXNBAPTS depth pull run pre-market, before Finals markets opened, also returned all-zero depth) — strong second-instance evidence that Kalshi player-prop orderbooks across both sports genuinely have no resting liquidity until close to/during the live game window, not a series-specific or one-off anomaly. **This is a real, load-bearing operational constraint for resolving GG-045, not a null result:** any future depth pull for this gap MUST be timed during an actual live game window (ticker's game in "in" state per ESPN/Kalshi, not "pre") or it will silently reproduce this all-zero read. Full multi-market live-window pull is the concrete next step (raw audit: `logs/orderbook_depth_mlb_20260717_052732.json` in the T-377 worktree) — not yet executed this session; deferred to a live-window re-run (see DECISION_LOG.md 2026-07-17 entry, T-377).** **Update 2026-07-17 (same day, separate action) — APR-0029 (this gap's D1/D2 decision request) signed off by Earl Ignacio (DS):** D2 ADOPTED (the live-window timing constraint above is now a standing operational rule, not just documented preference); D1 (depth-aware `max_stake` cap formula) APPROVED IN PRINCIPLE but NOT authorized for implementation until real live-window depth data exists; D3 (`DEPTH_IMPACT_PCT` calibration) remains explicitly deferred. No code change resulted. The core empirical gap (a real live-window depth pull) remains open — see `00_ADMIN/APR-0029_gg045-kalshi-depth-capital-ceiling-decision-request.md` (updated). **Update 2026-07-18T05:25 UTC (Terminal C) — first post-APR-0029 live-window attempt: WINDOW MISSED, no pull executed (D2-compliant no-run).** A dedicated terminal was tasked with running `query_orderbook_depth_mlb.py` during the 2026-07-17 slate's live windows — the first slate since D2's sign-off. At execution time (2026-07-18T05:22 UTC / 22:22 PT), the ESPN MLB scoreboard showed all 15 events of the 2026-07-17 slate in `post` state: 14 Final (including the latest-ending West-coast games SF@SEA, DET@LAA, STL@ARI) and PIT@CLE Postponed — zero games in state. Per D2 (standing rule: depth pulls only during confirmed-live windows), the pull was deliberately NOT run: a post-final read would produce a third invalid all-zero/closed-market artifact (after GG-041's NBA pregame read and T-377's MLB pregame read) with no diagnostic value, and no log artifact was produced by design. **Consequence: GG-045's empirical prerequisite remains unmet — D1's depth-aware stake-cap implementation in `risk.py` stays blocked on live-window data.** Next opportunity: the 2026-07-18 slate (first pitches ~17:00–23:00 UTC; a pull in the ~00:00–03:00 UTC 07-19 band would capture the maximum number of concurrently-live games). **Operational lesson from this miss: the live-window pull cannot be scheduled as an end-of-night terminal task — West-coast games end ~04:30–05:00 UTC and the window was already closed by 05:22 UTC.** Either (a) a session must be launched while games are verifiably in state (check ESPN scoreboard for `state == "in"` FIRST, before any protocol overhead), or (b) a scheduled/cron-triggered pull gated on live-game state should be registered as its own task — option (b) would need a fresh task registration and is not authorized by this note. **Update 2026-07-19/20/21 (T-393, worktree `session/20260718T052953Z-gg045-live-depth-pull`) — samples 2-3 collected, empirical prerequisite for APR-0029 D1 now MET, memo complete.** Terminal C (same worktree) collected sample 2 (2026-07-19 20:33Z, 10 games live, 521 markets, 521/521 nonzero) and built a laptop-independent VPS `systemd-run` one-shot for sample 3, then crashed before retrieval/write-back. A resuming session confirmed the worktree/branch were fully intact (not lost, contrary to the crashed session's own last self-report) and completed the remaining work: the VPS one-shot's scheduled 23:05Z run fired correctly but matched 0 markets — root-caused as structural (individual KXMLBHIT batter markets close progressively per-player, not at final out, so a lone late-game target naturally empties out), not a bug, and documented as such rather than silently discarded. A second, valid, previously-undocumented local pull Terminal C had made before crashing (2026-07-20 01:25Z, LAD@NYY G2 Bot 7th, 57/57 nonzero, D2-compliant) was found, verified, and adopted as sample 3. **Combined findings across all 3 samples (full detail + all figures: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T393_GG045_LIVE_WINDOW_DEPTH_MEMO.md`):** median tradeable combined depth runs $66-$195 (the $500-$2,000 estimate describes the upper quartile, not the range — floor is 2.5-7× too high as a central tendency); liquidity is structurally one-sided (YES-bid book near-empty, median committed USD $0.16-0.29 at best YES bid) and the bot's dominant bet direction (94% NO for T1, 72% NO for T4M-PROJ) consumes the thin side; the $500 `max_single_event_exposure_usd` hard cap fails the script's 5%-impact test in 100% of tradeable markets across all 3 samples and is whole-book NO-fillable in only 2%; Kelly-driven degradation on the measured NO-side book begins between ~$500 (thinnest sampled single-game window) and ~$2,400 (peak 10-game-overlap window) T1 bankroll — the current paper bankroll is at or within one order of magnitude of that range depending on which window type governs. **APR-0029 D1 (depth-aware max_stake cap) remains an OPEN OPERATOR DECISION — this update does not implement it, only supplies the data D1 was waiting on**, per Hard Rule 3/APR-0029's own terms. Raw artifacts (samples 1-3 + the empty VPS run) copied to main-tree `logs/` (gitignored). See DECISION_LOG.md 2026-07-21 (T-393) for the full write-back entry. |

</details>

---

### GG-046 — T4 Commercial Validation: Independent Alpha Hypothesis Untested and Unregistered

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** T4 independent validation still unregistered/unfinished; T-569 latency test returned NOT SUPPORTED per CLAUDE.md. Operator-blocked. **Next:** Operator decision on T4 validation track.
**Blocked-On-Operator:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-046 |
| Arm | MLB |
| Category | Systemic blind spot — T4 has a distinct alpha hypothesis with no validation experiment registered |
| What was missed | T4's alpha hypothesis ("market is slow to update to live game state; bot can get there first") is structurally distinct from T1's hypothesis ("calibrated historical model beats pregame market pricing"). EXP-017 tests T1's commercial case. No experiment is registered to test T4's commercial case. The governance framework (GG-004, EXP-017 design, ADR-0024 validation gates) was designed entirely around T1-style hypothesis testing. If T4 wins on a different information edge (market microstructure / reaction speed), T1 failure does not imply T4 failure. Conversely, T1 success does not validate T4. |
| When it should have been caught | Before T4 (MLB) was enabled for paper trading. ADR-0033 authorized T4 paper positions; T4's independent commercial validation was not a prerequisite. |
| Phases it survived | All phases — T4 and T1 were conceptually treated as parts of the same strategy without articulating the structural distinction in governance documentation. |
| Why it survived | The structural distinction (T1 = forecasting accuracy, T4 = market microstructure) was never explicitly documented. T4 was treated as a signal extension of T1 rather than an independent alpha source requiring its own validation track. |
| Impact | LOW in paper phase (no live capital). MEDIUM post-G6 if live capital is authorized based on T1 EXP-017 evidence and T4 is scaled alongside it — T4 could have negative expected value independently of T1. The kill switch and Kelly sizing provide protection, but a misclassified alpha thesis can bleed slowly without triggering either mechanism. |
| Discovery | SESSION 94 (2026-06-26) — strategic read-through surfaced the structural distinction between T1 (forecasting accuracy) and T4 (market microstructure / information speed). |
| Resolution | Define a T4 commercial validation experiment (EXP-T4-01) analogous to EXP-017: compare T4 model_p against live Kalshi market price at the moment each evaluation fired; compute net_edge over resolved bets; apply ADR-0024 Tier 1/2 thresholds independently. Requires ≥500 resolved T4 bets at unique markets (ADR-0024 Tier 2). Gate: T4 should not receive live capital allocation until independently validated by EXP-T4-01. Bug GG-050 must be fixed and T4 portfolio reset before clean data accumulates. |
| Status | **OPEN — SESSION 99 CORRECTION.** EXP-T4-01 SESSION 98 analysis RETRACTED: GG-050 bug (per-cycle `fired_tickers` reset) inflated n from 73 true unique markets to 1274 (17.5× overcounting). Corrected findings (73 independent markets, 2 game nights): win rate 37.0%, P&L −$0.18, EV −$0.0025/market (INCONCLUSIVE). n=73 does NOT satisfy ADR-0024 Tier 2 (need ≥500). Model calibration severely overconfident at model_p extremes. One positive signal: edge monotonicity correct (Q1→Q4 monotonically ordered win rates). Current T4 portfolio data is contaminated — must reset after GG-050 fix deployed. GG-046 OPEN until EXP-T4-01 re-run on ≥500 clean unique markets. See DECISION_LOG SESSION 98/99. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed, no change.** EXP-T4-01 still has not been re-run. Current T4M-PROJ clean_n=338 (2026-07-11 pull) is closer to but still short of the legacy ADR-0024 Tier 2 floor (500) and also short of APR-0024's variance-derived `n*=787` for this band — under either framework the independent T4 alpha hypothesis remains untested at adequate sample. Re-check trigger: next EXP-T4-01 re-run once T4M-PROJ clean_n clears 500 (legacy) or 787 (APR-0024 n*), whichever framework is in use at that time. **Fresh re-pull (2026-07-16, T-375) — ⚠️ LEGACY TIER 2 FLOOR CROSSED, flagged not acted on.** Live VPS pull via `build_t4_resolved_ledger.py`: T4M-PROJ **raw_n=910** resolved positions (win=532, loss=378, win_rate=58.5%, total P&L +$22.38) — this clears the legacy ADR-0024 Tier 2 floor (raw_n≥500) for the first time. **However, `clean_n=0` for T4M-PROJ (and every other band: T1 clean_n=0, T2 clean_n=0) as of this pull**, because `CURRENT_LOGIC_EPOCH` advanced 5→6 via GG-123/ADR-0028's D2 action (commit `cc887e8`, 2026-07-16T00:13:46Z, landed by an unrelated concurrent T2-vig-fix session just hours before this pull) — `logic_epoch.py`'s counter is deliberately global, not per-band (confirmed via its own module docstring), so a T2-scoped fix resets every band's `clean_n` to 0 regardless of which band's write-path it actually touched. **This is expected, documented epoch-cascade behavior (consistent with the GG-113/GG-119/GG-122 cascade already on record above), not a T4M-PROJ regression.** Net effect: APR-0024's governing `n*` standard cannot currently be evaluated for T4M-PROJ (`run_power_calc.py` returns `INSUFFICIENT_DATA`, needs clean_n≥2 to even estimate variance) — the 787 figure from 2026-07-11 is stale and cannot be refreshed until clean data re-accumulates under epoch 6. **Per this task's explicit instruction: this crossing is flagged here, not acted on. EXP-T4-01 has NOT been re-run. That is a decision for Earl to make and register separately** — open questions for that decision include whether to re-run against `raw_n` (legacy framework, now satisfied) despite APR-0024 having superseded raw-count heuristics as the *governing* standard, or wait for clean_n to re-accumulate under epoch 6 so a same-framework (APR-0024 n*) re-run is possible. An automated check (`.claude/hooks/governance_scan.sh`, T-375) now flags this crossing on every session's mandatory scan output going forward, so this stops depending on a human remembering to re-pull. **EXP-T4-01 built and run for the first time (2026-07-16, T-375/GG-060 Phase 4)** — `scripts/run_exp_t4_01_mlb.py` (thin wrapper over a new shared `scripts/exp_retrospective_core.py`, extracted from `run_exp017_mlb.py` and verified byte-identical against a pre-refactor baseline). Run against the same raw_n=910/456-unique T4M-PROJ pull above: overall verdict **DIRECTIONAL_POSITIVE** (EV=+$0.0294/bet, win_rate=0.564, P&L +$13.42) — consistent with the raw-count picture. **⚠️ But the edge-monotonicity guard (T-177/GG-037 anti-predictive pattern) returned ANTI-PREDICTIVE at Fisher p=0.0280 (significant at alpha=0.10)**: tercile win rates by fee-net-edge are T1(low)=0.671, T2=0.566, T3(high)=0.454 — higher model-computed edge is winning *less* often, structurally the same shape that closed NBA's alpha case negatively (GG-037/GG-004). **This is a raw_n result, not clean_n** (T4M-PROJ clean_n=0 per the epoch-6 cascade documented above) — a first-look diagnostic on a contaminated-epoch cohort, not a clean APR-0024 verdict. Flagged here and in DECISION_LOG.md (T-375 Phase 4 entry, 2026-07-16) for Earl's review; no band pause or kill-switch action taken unilaterally, per this project's capability-boundary standard. Recommend re-running EXP-T4-01 once clean_n re-accumulates under epoch 6 to confirm or rule out the pattern on uncontaminated data before treating it as a governance-grade signal. **Update 2026-07-20 (T-390) — epoch-8 clean cohort has reached clean_n=30, verdict NO_POSITIVE_EFFECT, flagged not acted on.** `scripts/run_power_calc.py` (`.claude/hooks/governance_scan.sh`'s SAMPLE ADEQUACY section) now reports T4M-PROJ at `clean_n=30, raw_n=1267`, mean P&L/bet **−$0.1746** (stdev $0.3826) under `CURRENT_LOGIC_EPOCH=8` (boundary 2026-07-18T18:07:19Z, per T-387). `NO_POSITIVE_EFFECT` is the script's own status for "clean_n≥MIN_N but observed mean ≤ 0 — no finite n* exists to size a confirmatory sample until the point estimate itself turns positive," per `run_power_calc.py`'s own reason string. Two things this is NOT: (1) not a G6 verdict — G6's 30-bet criterion requires positive P&L, and clean_n happening to equal 30 here is coincidental to that gate threshold, not a gate crossing (APR-0024 is the governing per-band standard, and it has no finite n* to report while the point estimate is negative); (2) not yet interpretable — `cadence_span_days=0.00387` (~5.6 minutes) is flagged `cadence_immature=True` by the script itself, meaning these 30 resolved bets are bunched extremely tightly in time (consistent with T4's high-frequency per-cycle evaluation design, CLAUDE.md Hard Rule 9) and this is a first-look point estimate on a tiny post-epoch-8 window, not a stable measurement. Flagged here and in `DECISION_LOG.md` (2026-07-20, T-390) for Earl's review; no band pause or kill-switch action taken unilaterally. Recommend re-checking once clean_n grows materially past 30 and cadence_span_days is no longer immature before treating the negative sign as a governance-grade signal — do not conflate with GG-105's separate anti-predictive-tercile investigation, which is a different (though related) diagnostic on a different cohort framing. **Update 2026-07-20 (T-392) — explicit re-check threshold registered and wired into code, closing the open-ended "flagged, no action" gap named above.** Per Earl's explicit instruction not to leave this as an open-ended flag, `scripts/run_power_calc.py`'s `mu<=0` branch (`NO_POSITIVE_EFFECT`) now computes a concrete `neg_sign_governance_grade` boolean gated on two thresholds, both required: **(1) `clean_n >= NEG_SIGN_CONFIRM_N` (150)** — reusing the project's own legacy ADR-0024 Tier 1 single-sport floor as the clean_n confirmation floor, since no finite variance-derived `n*` exists to derive a bespoke number when the point estimate itself has the wrong sign (the `n*` formula assumes sizing toward *detecting* a positive effect); and **(2) `cadence_span_days >= MATURE_CADENCE_SPAN_DAYS` (14)** — the pre-existing constant already used elsewhere in this script to flag time-bunched cohorts (precedent: GG-080's "n=2 game-days, not a stable long-run estimate" caution). Both conditions must clear before a negative sign is treated as governance-grade rather than a first-look artifact of a small/immature cohort; today's reading (clean_n=30, cadence_span_days≈0.004) clears neither. This is now surfaced automatically, not dependent on a human re-deriving it: `run_power_calc.py`'s `_fmt_band()` output tags every `NO_POSITIVE_EFFECT` band `[GOVERNANCE-GRADE]` or `[pre-confirmation]`, and `.claude/hooks/governance_scan.sh`'s existing GG-046 alert block (T-375) gained a third check (`neg_sign_crossed`) alongside its two positive-direction checks (legacy Tier 2 raw_n≥500, APR-0024 n* met) — when the negative-sign thresholds clear and neither positive-direction check has already fired, the scan prints a dedicated "GG-046 NEGATIVE-SIGN ALERT" block on every session's mandatory scan, naming the exact clean_n/cadence values that crossed and directing the session to register Earl's decision before any band action. Verified working end-to-end 2026-07-20: `python3 scripts/run_power_calc.py` and a full `bash .claude/hooks/governance_scan.sh` run both execute cleanly against live T4M-PROJ data (clean_n=30, raw_n=1267 — the raw_n Tier-2 floor is already crossed and correctly takes priority in the alert's if/elif ordering, so the negative-sign branch is dormant-but-verified-functional rather than exercised by current data). This does not change GG-046's OPEN status or resolve the underlying commercial question — it only ensures the negative-sign finding cannot silently sit as "flagged, no action" past its own re-check point. See `scripts/run_power_calc.py` (`NEG_SIGN_CONFIRM_N`, `neg_sign_governance_grade`), `.claude/hooks/governance_scan.sh` (GG-046 section), DECISION_LOG.md 2026-07-20. **Update 2026-07-30/31 (ADR-0050) — T4M-PROJ reactivated at a flat $1.00 measurement stake, sizing-only, to resume clean-cohort accrual for this gap.** T4M-PROJ had been at `kelly_fraction=0` since ADR-0048 (R1, 2026-07-29), meaning every evaluation clearing the post-ADR-0049 signed-edge gate still rejected downstream with `kelly_size_zero` — zero bets placed, zero new resolved data for GG-046 to measure, independent of whatever the underlying edge sign turns out to be. `risk.py::evaluate_forecast()` gained an optional `fixed_stake_usd` bypass (default `None`, inert for every other caller); `run_t4_mlb_live.py` now passes `T4_MEASUREMENT_STAKE_USD=1.00`. This is explicitly **not** a claim that GG-105's edge is resolved or that the ANTI-PREDICTIVE/NO_POSITIVE_EFFECT findings above are overturned — the stake exists solely to accrue a clean, gate-fixed (post-ADR-0049) T4M-PROJ cohort large enough to eventually re-run `run_power_calc.py`/EXP-T4-01 against. `logic_epoch` bumped 10→11, `bands_affected={"T4M-PROJ"}` only (MAIN's T1/T2/T3 clean_n floors stay at epoch 10, unaffected). Exit criteria (ADR-0050 §6): regress to B2-frontier edge-conditional sizing once T4M-PROJ's own `n*` is reached and clears power-calc, or revert `T4_MEASUREMENT_STAKE_USD` to $0 if the edge fails that check. DS sign-off: operator, 2026-07-30. GG-046 remains **OPEN** — this is instrumentation to eventually close it, not a resolution. See ADR-0050, DECISION_LOG.md 2026-07-30, commits `b7ff281`/`c9c8263`. **Update 2026-07-30/31 (ADR-0050 §8 addendum) — instrumentation corrected before any data accrued; a second, independent blocking bug found and fixed.** Operator direct source-inspection against `HEAD=00201fe` found the fixed-stake plumbing above (commit `b7ff281`) was correctly wired (no fix needed) but flagged two required corrections applied before this cohort starts: **(1)** an unrelated, more severe bug in `StagedOrderStore.stage_order()` — it rejected `kelly_fraction=0.0` (every T4M-PROJ call's exact value) with `ValueError`, silently caught by `run_t4_mlb_live.py`'s try/except before `trader.open_position()` was ever reached, meaning T4M-PROJ would have recorded zero paper positions regardless of the fixed-stake fix — fixed (bound loosened to `0.0 <= kelly_fraction <= 1.0`, commit `cafcf74`), registered and RESOLVED as GG-147 (see DECISION_LOG.md 2026-07-30/31); **(2)** flat-DOLLAR sizing without a contract cap would have let sub-$0.10 entries (23% of the epoch-8 gate-valid cohort) become 100:1+ longshot positions, ~15x the per-bet variance of capped sizing on the same bets — capped at `min($1.00, 10 contracts × entry_price)`, `T4_MEASUREMENT_MAX_CONTRACTS=10` (operator-overridable). Pre-registered price-stratum rule fixed in code before data accrual: LOW `<$0.10` reported as a named secondary stratum, MID/HIGH `≥$0.10` pooled for the headline verdict, per ADR-0050 §8(C). **Evidentiary caveat for the eventual regression (ADR-0050 §8(g)):** the prior +10.99%/+27.58% ROI readings associated with the post-GG-142 gate are in-sample (the threshold was chosen with knowledge of that data) and must not be treated as a validated prior when this flat-stake cohort is regression-analyzed — this cohort is the first genuinely out-of-sample read of that gate. Full project test suite now run clean apart from 8 pre-existing, unrelated failures traced to ADR-0048 (registered separately as GG-146). See ADR-0050 §8, DECISION_LOG.md 2026-07-30/31, commit `cafcf74`. |

---

### GG-056 — NBA Main Pool Dormant at 24.9% Drawdown; No Reactivation Plan Before October Resume

**Status:** PLAN ACCEPTED · **Severity:** MEDIUM

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-056 |
| Arm | NBA |
| Discovered | 2026-07-01 SESSION 104 — session-start protocol Q1/Q6 cross-check: `risk.py` `max_drawdown_pct = 0.20` (kill-switch trigger) vs. live NBA main-pool realized drawdown of 24.9% (bankroll $751.10 / $1,000 initial, realized P&L -$248.90, per GG-036 ratified baseline). |
| Category | Systemic blind spot — same failure shape as GG-049 (a pipeline that produces nothing looks identical to "no games," not "kill switch engaged"). |
| What was missed | The kill switch is working correctly: `current_drawdown_pct` is computed live per-pool in `run_paper_trade.py` and passed into `evaluate_forecast()`, which correctly halts at >= 0.20. NBA is currently off-season (0 games), so this hasn't manifested as an operational failure — no bets are being evaluated at all. But there is no decision on record for what happens when NBA resumes in October 2026 with the pool still 4.9 points above the kill-switch threshold: the very first live `evaluate_forecast()` call will trip `drawdown_limit_breached` and reject every subsequent bet indefinitely, with no reset mechanism currently defined. |
| When it should have been caught | Should have been flagged as a forward-looking action item when the G5/GG-036 baseline was ratified (-$248.90/-24.9%, SESSION ~66-67) or when the dark-period build plan was adopted, since both predate knowledge that NBA would sit dormant across an off-season while already past its own kill-switch threshold. |
| Impact | MEDIUM. If unaddressed, October's first NBA cron run will silently place 0 bets and, absent Step 4 of the session-start protocol (or a specific check of the kill-switch reason code), will look identical to "no games scheduled yet" rather than "kill switch permanently engaged." |
| Resolution path | Decide, before NBA 26-27 season open (or explicitly defer via a registered T-NNN): (a) NBA resumes on the current drawdown baseline and stays dark until a G6-scoped bankroll/limit revision, or (b) the drawdown baseline / initial_bankroll is formally reset for the new season via ADR, consistent with the standing G6 obligation to formally revise all hard limits (CLAUDE.md Q1, DECISION_LOG 2026-05-29 retroactive entries). |
| Status | **PLAN ACCEPTED (ADR-0035) — EXECUTION PENDING, ~1 month pre-2026-27-season.** Decision made, implementing ADR already exists and is accepted; only the operational reset itself (scheduled for game-day-minus-~1-month, October 2026) remains outstanding. **Disposition (2026-07-15, GG-burndown-even pass): (b) escalated.** Drafted `00_ADMIN/APR-0027_nba-drawdown-reactivation-decision.md` (PENDING) presenting the two documented options (stay dark until G6-scoped limit revision, vs. formally reset the NBA drawdown baseline via ADR) for Earl to choose between before the NBA reactivation window (~1 month before 2026-27 season). Flagged the GG-049/GG-060-style silent-failure risk if left undecided. Not self-resolved per Hard Rule 3 — this decides a kill-switch reset policy. **Update 2026-07-17 — Option B selected (Earl Ignacio, DS sign-off):** formally reset the NBA drawdown baseline/`initial_bankroll` via a dedicated ADR before the reactivation window, preserving the -24.9%/-$248.90 figure on record as historical/adjudicated fact. This 2026-07-17 entry registered **T-383** to draft that implementing ADR, believing none existed yet. **Correction 2026-07-22 (T-383/GG-056 close-out, Window B):** the implementing ADR already existed — `03_DECISIONS/ADR-0035_nba-paper-portfolio-reset-2026-27.md`, drafted and **ACCEPTED 2026-06-30 SESSION 102** (17 days before this GG-056 entry's own 2026-07-17 update, and the same session that ratified this gap's -$248.90/-24.9% baseline in the first place). ADR-0035 fully implements Option B: resets `paper_portfolio.json` to a clean $1,000.00 baseline at 2026-27 season start, preserves the 158-bet 2025-26 record in `paper_portfolio.json.bak_s102_pre_2627` as a distinct historical EXP-017 cohort, and includes a pre-activation checklist gated on the October 2026 reactivation window. The only real defect was that ADR-0035's own Status header had gone stale (still read "DRAFT" despite its filled Sign-off table and despite `DECISION_LOG.md:53` already recording ACCEPTED) and neither this GG-056 entry nor APR-0027 ever cross-referenced it — a missing-cross-link failure, not a missing-decision failure. Both are now fixed: ADR-0035's Status header corrected in place, and this entry + APR-0027's Disposition Record now point to it. **T-383 closed via this cross-reference, not by drafting a new ADR-0048** — see `DECISION_LOG.md` 2026-07-22. Remaining open item is unchanged from Option B's original scope: execute ADR-0035's reset checklist ~1 month before 2026-27 season tip-off (not yet due — no time pressure). See `00_ADMIN/APR-0027_nba-drawdown-reactivation-decision.md` (updated), `03_DECISIONS/ADR-0035_nba-paper-portfolio-reset-2026-27.md`, and `DECISION_LOG.md` 2026-07-17/2026-07-22. |

</details>

---

### GG-060 — Silent Success Indistinguishability: Zero Bets from "No Edge" Looks Identical to Zero Bets from Pipeline Failure

**Status:** IN PROGRESS · **Severity:** MEDIUM
**Actively-Broken:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-060 |
| Arm | MLB |
| Discovered | 2026-06-30 SESSION 104 — Opus strategic review identified the inverse of GG-049: a run that evaluates markets and finds no edge is currently indistinguishable in the log from a run where the pipeline silently died. |
| Category | Systemic blind spot — diagnostic oracle gap. Inverse of GG-049. |
| What was missed | C4 risk.py logs bet approvals (positions opened, sizes, Kelly fractions). It does not log evaluations that were rejected due to insufficient edge (`model_p ≤ market_implied_p + vig`), rejected due to risk controls (drawdown limit, exposure cap, size floor), or evaluated and simply found to have no positive edge signal. The result: a cron run that produces zero bets could mean: (A) pipeline died at some layer (GG-049 pattern), (B) C4 correctly evaluated N markets and found 0 with positive edge signal, (C) C4 found positive edge signals but rejected them (drawdown limit breached, exposure cap hit, size too small). Currently, case (B) and case (C) are indistinguishable from each other and from case (A) without manually reading `paper_portfolio_mlb.json` or the audit log at a per-event level. There is no structured per-evaluation log record, no run-level edge opportunity summary, and no mechanism to detect when zero-edge nights cluster (which would indicate model drift or market regime shift). The Semantic Floor Guard (ADR-0034) partially mitigates case (A) for the C1→C2 layer but does not address cases (B) or (C), and provides no edge accounting at the C4 layer. |
| When it should have been caught | When C4 risk.py was designed — every risk control that rejects a bet should emit a structured rejection record, not just a decision to not call `open_position()`. |
| Impact | **MEDIUM ongoing.** Zero-bet runs from "no edge tonight" go undetected as a legitimate outcome vs. a silent failure. Model drift (market getting more efficient over time relative to the model) will not be caught until it shows up as sustained P&L underperformance — which requires resolved bets to diagnose, a 24–48 hour lag at minimum. No experiment (EXP-017, EXP-T4-01) can distinguish "we found edge and captured it" from "we found edge but risk controls blocked it" from the current log structure. |
| Discovery | Opus strategic review — SESSION 104. |
| Resolution | Phased: (1) Per-evaluation C4 decision audit log (every market: model_p, market_implied_p, vig, edge_signal True/False, decision: APPROVED/REJECTED_NO_EDGE/REJECTED_SIZE/REJECTED_DRAWDOWN/REJECTED_EXPOSURE). (2) Run-level edge opportunity report (markets evaluated, edge signals found, bets placed, rejection reasons). (3) Silent Success detector: flag runs where edge_signals == 0 for ≥50 evaluations (market is pricing efficiently relative to model — not a failure, but a signal). (4) Edge signal rate trend (rolling 7-day): detects sustained drift within 24–48h. (5) EXP-017/EXP-T4-01 retrospective template using edge accounting data. Registered as T-213. |
| Status | **IN PROGRESS.** 2026-07-02 SESSION 108: Phase 1 (resolution items 1-3 — per-evaluation edge-decision JSONL sink, `summarize_edge_run()` PIPELINE_BROKEN/NO_EDGE/RISK_REJECTED/ACTIVE classifier, `silent_success_flag` at the ≥50-evaluation threshold) is code-complete, tested (16 new tests, `test_c4_risk.py` 50→66 passing), and wired live into T1 MLB (`run_mlb_paper_trade.py`). Full DECISION_LOG entry: SESSION 108 / T-213 Phase 1 row. **Correction (2026-07-16, T-375): the 2026-07-15 burndown pass's claim that T4 wiring "remains OPEN" was stale and wrong** — `git blame` on `run_t4_mlb_live.py` shows `edge_logger` was already constructed and wired into `RiskEngine(...)` in commit `8d2f1dda` (2026-07-02 13:27:33 -0700, same session as T1), confirmed live on VPS (`audit_mlb_t4_edge_decisions.jsonl`, 12,620 lines as of 2026-07-12). The 07-15 pass reaffirmed "no change" without re-verifying this sub-item — a Hard-Rule-10 stale-narrative failure. **T2 wiring genuinely was missing (confirmed via grep, zero hits) and was closed this session (T-375, commits `6ad60d5`/`9c2cf51`)**: `edge_logger` added to `run_t2_mlb_sameday.py`, wired into both `RiskEngine(...)` construction sites, validated mechanically (synthetic call using T2's real forecast_rec schema and Kelly params produced a correctly-classified `RISK_REJECTED` record via `summarize_edge_run()`) since T2 has not yet produced a live non-PASS day to source real production data from. T1 and T4 wiring were additionally validated against real VPS production JSONL samples (`audit_mlb_edge_decisions.jsonl`, `audit_mlb_t4_edge_decisions.jsonl`) run locally through `summarize_edge_run()` — both returned plausible `ACTIVE` states. **New caveat found during T2 wiring, documented in-code (`run_t2_mlb_sameday.py`) rather than silently fixed:** T2 applies its own `EDGE_YES` pre-filter before calling `engine.evaluate_forecast()` — only non-PASS forecasts reach C4, so a legitimate all-PASS T2 day (observed in real 2026-07-16 production output, 4/4 PASS) will report `total_evaluations=0`, which `summarize_edge_run()` classifies as `PIPELINE_BROKEN` — a false positive specific to T2 that T1/T4 do not share. Widening the sink to also cover T2's pre-filter PASS population is left as an open scope decision for the operator, not resolved unilaterally. **Phase 2 (7-day edge-rate trend, `scripts/edge_rate_trend.py`) and Phase 4 (EXP-017/EXP-T4-01 retrospective template) both DONE this session (2026-07-16, T-375).** Phase 4: extracted the shared band-agnostic analytical core (`scripts/exp_retrospective_core.py`) from `run_exp017_mlb.py`, verified byte-identical against a pre-refactor real-data baseline, then built `scripts/run_exp_t4_01_mlb.py` and ran it for the first time ever against real T4M-PROJ data (raw_n=910/456 unique) — see the corresponding GG-046 entry above for the DIRECTIONAL_POSITIVE/ANTI-PREDICTIVE finding this produced and its raw_n caveat, and DECISION_LOG.md's T-375/GG-060 Phase 4 entry for full detail. **All four GG-060 resolution items (1–4) plus the Phase 4 retrospective template are now complete.** Linked: GG-049, GG-046, GG-037, T-213, T-375. Re-check trigger: next EXP-017/EXP-T4-01 re-run once clean_n data re-accumulates under logic epoch 6. |

</details>

---

### GG-064 — Kalshi DEMO Market `open_time` Lags LIVE for Same Ticker (Discovered During GG-063 Verification, Unconfirmed as Structural)

**Status:** LIKELY RESOLVED · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-064 |
| Arm | MLB |
| Discovered | 2026-07-01 SESSION 108 — while empirically verifying the GG-063/T-217 v1→v2 order-endpoint migration fix via a manual test order against Kalshi DEMO. |
| Category | Unconfirmed — possible DEMO/LIVE environment desync, or simply a testing-window artifact (no live MLB games "today" to test against). Not yet distinguished. |
| What was missed | Comparing `GET /markets/{ticker}` for the same live-sourced KXMLBHIT ticker against both DEMO and LIVE base URLs showed: DEMO `status=initialized`, `open_time=2026-07-02T05:12:39Z` (not yet reached); LIVE `status=active`, `open_time=2026-07-02T04:12:00Z` (already active) — a ~1hr `open_time` discrepancy for the identical ticker, with DEMO consistently lagging LIVE. All 60 currently-open KXMLBHIT markets at test time were for 2026-07-02 games (test was run 2026-07-01, no live in-progress MLB games existed to test against same-day). Every one of 15 test orders submitted against DEMO in this window returned `409 market_closed` — could not be distinguished between (a) a genuine DEMO/LIVE market-activation-timing lag that would also affect real T1/T4 MLB cron runs scheduled close to `open_time`, or (b) an artifact of testing against next-day markets outside any live game window, which is the more likely explanation given no MLB games were in progress at test time. |
| When it should have been caught | N/A — this is a fresh observation from this session's manual verification, not a process failure with a prior missed catch point. Flagging now specifically so it isn't silently absorbed into "GG-063 resolved" when it is a distinct, unconfirmed question. |
| Impact | **UNKNOWN, likely LOW.** Zero capital risk (paper mode). If structural (DEMO genuinely lags LIVE `open_time` by ~1hr for every market), the next T1/T4 MLB cron run scheduled near a game's `open_time` could see spurious `409 market_closed` on DEMO even though the market is live/active in production pricing — this would look identical to GG-063's original symptom (order rejected) but with a different, fully expected root cause once understood. If purely a testing-window artifact, no action is needed. |
| Resolution path | Do not attempt further synthetic testing to resolve this — the correct test is a real T1/T4 MLB cron run against a genuinely in-progress game, where DEMO and LIVE market state can be compared under realistic conditions. Monitor the next scheduled MLB cron run's `kalshi_order_status` distribution: if `409`/`market_closed`-class failures persist against markets confirmed `active` on LIVE, escalate to a structural DEMO/LIVE desync finding; if orders succeed normally, close as a testing-artifact false alarm. |
| Status | **LIKELY RESOLVED 2026-07-03 (SESSION 114) — testing-artifact false alarm, per this gap's own resolution path.** The real-world cron-run observation this gap called for has since occurred: T4 MLB's live orders against genuinely in-progress games show `kalshi_order_status="submitted"` for 23 orders on 2026-07-02 and 10 orders on 2026-07-03, with zero `409`/`market_closed` failures against markets confirmed active. Verified via code read of `submit_order()` in `kalshi_client.py` that `status="submitted"` can only be set on the `ok=True` branch — i.e., only after a genuine successful (200/201-equivalent) HTTP response from Kalshi's v2 endpoint, not a client-side default — so this evidence satisfies the "orders succeed normally → close as testing-artifact false alarm" branch of this gap's own resolution path. **One nuance keeping this at LIKELY RESOLVED rather than fully CLOSED:** all confirming evidence is from T4 (live, in-progress-game orders); T1/PIPE-05 has not itself placed an order since the GG-063/T-217 fix deployed, because it independently HALTed on 2026-07-02 (see [[GG-072]]) and the betting day was unrecoverable. Close fully once T1 places and confirms at least one post-fix order with the same clean `submitted` status. Not conflated with GG-063 (RESOLVED) — that gap's specific claim (v1 endpoint deprecation) remains conclusively fixed regardless of this outcome. |

</details>

---

### GG-066 — MLB C1 Has No Real-Time/Sub-Poll-Interval Event Feed (Blocks Event-Driven T4 Sub-Bands)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** MLB still polls ESPN at POLL_INTERVAL_S=45 (run_t4_mlb_live.py:151); no sub-poll event feed exists. **Next:** Needs a C1 feed decision; blocks event-driven T4 sub-bands.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-066 |
| Arm | MLB |
| Category | Architectural placeholder / data-availability gap (same class as NBA's GG-040, discovered independently for MLB). |
| What was missed | ADR-0039 (T-218, SESSION 108) scoped an MLB-native T4 sub-band taxonomy and, in doing so, confirmed by direct code read of `run_t4_mlb_live.py` that MLB's only live data source is a 45-second poll of the ESPN MLB summary endpoint (`_espn_poll_once_mlb`, `POLL_INTERVAL_S = 45`) that diffs `h_so_far`/`ab_so_far` between cycles. There is no play-by-play, no live event stream, and no sub-45s detection latency anywhere in current MLB C1. |
| When it should have been caught | This was never claimed to be otherwise — it is a newly surfaced scoping finding, not a regression. Registered proactively as part of ADR-0039's design work rather than being discovered as a live failure. |
| Phases it survived | N/A — this is the first ADR/task to formally scope event-driven MLB T4 sub-bands, so there was no prior point at which this gap could have been flagged as blocking. |
| Why it survived | Not applicable in the "should have been caught" sense; flagged as a direct consequence of ADR-0039's Tier B design work applying GG-061's process fix (verify actual data availability before proposing a sub-band that assumes it). |
| Impact | Blocks T4M-EVENT, T4M-LINEUP, and real-time firing of T4M-ARITH (all three degrade to "same signal as T4M-PROJ, one 45s cycle later" without this). Does not block T4M-BOUNDARY, T4M-ARITH's poll-driven firing, T4M-STAGED, T4M-CORR, or T4M-EXIT, none of which require sub-poll-interval detection. Zero capital risk — no sub-band gated by this has been built or activated. |
| Discovery | 2026-07-02 SESSION 108, during ADR-0039 scoping (T-218), by direct read of `run_t4_mlb_live.py`'s ESPN polling implementation. |
| Resolution | Not resolved. Requires evaluating real-time or near-real-time MLB event sources (e.g., MLB Stats API live game feed `v1.1/game/{gamePk}/feed/live`, which offers finer-grained play-by-play than the ESPN summary endpoint currently used) as a new C1 MLB data source, scoped under its own task once T4M-EVENT/T4M-LINEUP/T4M-PITCHER implementation is prioritized. Out of scope for T-218 (scoping-only). |
| Status | OPEN — registered, no task assigned yet. Zero capital risk; blocks three of ten proposed MLB T4 sub-bands from ADR-0039, does not block T-218 itself or G6. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed as watch item, no change** — no genuine MLB sub-band build has been authorized or started; the ADR-0039 Tier B roster (T4M-EVENT/LINEUP/PITCHER) remains scoping-only per CLAUDE.md, requiring fresh DS sign-off before implementation. Re-check trigger unchanged: whenever T4M-EVENT/LINEUP/PITCHER implementation is prioritized/authorized by Earl. |

</details>

---

### GG-078 — T4 MLB's Real ~341-Bet/Day Cadence Means Kill-Switch Fate Is Decided Within ~15 Days Regardless of True Edge Sign; Long-Horizon Projections for T4 Are Not Meaningful at Any Stake Cap

**Status:** WATCH ITEM · **Severity:** LOW

Re-filed 2026-10-21 under the operator's observation rule. Reopens if: T4M-PROJ kelly_fraction becomes nonzero (ADR-0048 reactivation).

**Current state (2026-10-08, W59.1):** T4M-PROJ kelly_fraction is 0.0 (ADR-0048), so the kill-switch-fate concern is moot while sizing is zero; reopens on reactivation. **Next:** Re-run mc_empirical_bootstrap.py before any reactivation.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-078 |
| Arm | MLB |
| Category | Modeling/simulation scope gap, discovered while extending [[GG-071]]'s forward-compounding Monte Carlo (T-233) to include the T4 leg per direct operator correction — the original T-233 pass modeled T1 only. |
| What was missed | The T-233 Monte Carlo initially covered T1 (26 bets/active-day, verified real inputs) only, on the judgment call that T4's 13 resolved positions were too thin to calibrate a reliable win rate. Operator correctly flagged this as the wrong call to make unilaterally — T4 is real, live, cron-active, and per CLAUDE.md's own throughput design fires roughly 13x more often than T1 (~341 bets/day derived from ~50-55 bets/game × ~6-7/9 games/day, vs. T1's real observed 21-26/day). Omitting it left the simulation silent on the dominant-volume leg of the actual system. |
| When it should have been caught | Should have been part of the original T-233 scope, not a follow-up correction — CLAUDE.md's own Hard Rule 9 explicitly states the T4 throughput design is a first-class architectural fact ("Design throughput is thousands of bet evaluations per game... any implementation that only makes sense at low throughput is architecturally wrong"), which should have prompted including T4's real cadence from the start rather than excluding it for data-thinness reasons. |
| Phases it survived | One full artifact rebuild cycle (T-233's v1/v2 passes) before being caught by direct operator review. |
| Why it survived | Reasonable-sounding but ultimately wrong risk-averse judgment call: T4's 13 resolved bets genuinely can't support a reliable win-rate estimate, and the instinct to exclude a thinly-evidenced input rather than fabricate one is generally sound practice — but applied here, it silently dropped an entire leg of the real system instead of including it with explicit, labeled uncertainty (the correct handling of a low-n input, per this project's own "mark unsupported as Assumption" discipline). |
| Impact | Running T4 at its real derived cadence under two explicit win-rate scenarios (46.34% breakeven — statistically consistent with T4's real +$1.59-on-13-bets result; 53.06% T1-comparable — an explicit unproven upper case) produced a structural finding independent of which scenario is closer to truth: **T4's outcome is almost entirely decided within the first ~15 days, regardless of edge sign.** At breakeven, 29% of the 100,000 simulated paths hit the 20% drawdown kill switch on day 1 alone, 96.5% by day 5, ~100% by day 15 — a driftless (zero-edge) random walk at ~341 bets/day will hit any fixed drawdown barrier almost immediately; this is a real mathematical property of high-frequency zero-edge processes under a hard stop, not a simulation artifact. At T1-comparable edge, breach probability plateaus at 15.4% by day ~15 (vs. T1's own day-~150 plateau) — same $500-stake-cap-escape mechanism as T1, compressed ~10x by the higher frequency — and the surviving-path median explodes to $8,851,815 by day 365, an even less credible number than the T1-only $484,087 finding this whole exercise started from. **This means no tuning of individual constants (stake cap, starting bankroll, which legs are included) fixes the "ludicrous long-horizon number" problem — it is structural to projecting any persistent edge forward at real observed frequency for a full year with no capital/liquidity ceiling.** The corollary for capital planning: if T4 truly has near-zero edge, the drawdown kill switch will reveal that fact fast (within ~2 weeks) and cap the loss at roughly -11.6% of T4's $1,000 book before going fully dark for the remainder of any period modeled — a real, actionable, and previously undocumented characterization of T4's near-term risk profile. |
| Discovery | 2026-07-03, T-233 v3 pass, direct operator feedback: "Why is the MC still not scripted properly to include the full bot... Where is T-4? ~1000s of bets PER GAME not even PER DAY is still not being simulated?" |
| Resolution | OPEN. T4 leg added to the Monte Carlo (`mc_t4_leg.py`) with both scenarios; new artifact `t1-t4-mlb-mc-combined` presents the combined finding. Not resolved: (a) T4's true edge remains unknown pending T4M-ARITH/FLOW's own gating experiments (EXP-ARITH-MLB-01/EXP-FLOW-MLB-01, both currently INCONCLUSIVE at n=0 resolved per prior sessions); (b) no capital/liquidity-ceiling model has been built for either leg — the recommended fix (a shorter, ~30-60 day trustworthy planning horizon, or a real market-depth-constrained model per GG-045) has not been implemented, only recommended in the artifact. |
| **2026-07-12 reconciliation (T-350)** | [[T-342]] (2026-07-11) added a `stake_mode="flat"` path to `mc_forward_projection.py --from-ledger` to model T4M-PROJ's *observed* near-constant-dollar stake behavior (~$0.57/bet, not visibly scaling with bankroll over a short ~6-day window). Running that flat-mode report live against the real clean_n=412 ledger (T-350, 2026-07-12) found its risk shape is **structurally different** from this gap's original finding: FLOOR-scenario (breakeven) P(kill) accumulates gradually across the full year — 0.00% at 30d, 4.18% at 182d, 17.92% at 365d — rather than being decided within ~15 days. This is expected, not a contradiction: this gap's "~15-day decision" finding was derived under T4's real Kelly-**proportional** sizing (`mc_t4_leg.py`, ~341 bets/day theoretical cadence, since superseded ~9-19x downward by [[GG-080]]'s empirical measurement), where compounding stake-vs-bankroll dynamics under a hard drawdown barrier force fast resolution. A **flat** dollar stake never grows with bankroll, so it does not inherit that early-decision property — it spreads ruin risk gradually across the full horizon instead. Critically, T4M-PROJ's live code is still Kelly-proportional (`KELLY_T4=0.10`) — the flat-stake behavior is an *empirical regime property* of a tiny, tightly-clustered edge over a short observed window (per T-342's own DECISION_LOG framing), not a coded guarantee. If real stakes begin visibly compounding with bankroll as more data accrues, this gap's original fast-decision dynamic is the operative risk model for T4M-PROJ again, not the flat-mode gradual one. A GG-078 cross-reference caveat was added directly to `build_ledger_report()`'s T4M-PROJ/flat-mode output (alongside the existing GG-105 caveat) so this distinction is visible in every report run, not just in this log. This reconciliation does not resolve either open item from the original finding (T4's true edge is still unknown; no capital/liquidity-ceiling model exists) — it clarifies that the flat-mode long-horizon numbers describe a distinct, conditional sizing regime, not a refutation or supersession of the original ~15-day finding. |
| Status | OPEN — finding registered and evidenced; no code/architecture change made or required by this finding alone. The 2026-07-12 reconciliation (above) confirms the original ~15-day proportional-sizing finding stands unmodified for T4's real live sizing mechanic; it does not transfer to T-342's flat-mode hypothetical, which is now explicitly caveated in the tool's own output. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed as watch item, no change** — both regimes (proportional fast-decision, flat gradual) remain live possibilities depending on how T4M-PROJ's real stake behavior evolves; no new data this pass. Re-check trigger: if T4M-PROJ stake behavior shifts from flat to visibly compounding with bankroll, or when EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 resolve. |

</details>

---

### GG-091 — `mypy --strict` Full-Tree Baseline: 365 Pre-Existing Errors in 57 Files, Not Yet Remediated

**Status:** PARTIAL RESOLVE · **Severity:** MEDIUM
**Actively-Broken:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-091 |
| Arm | Core |
| Discovered | 2026-07-06 SESSION 123, as a direct byproduct of closing GG-065. GG-065 had only ever been run against 2 files (`risk.py`, `run_mlb_paper_trade.py`); once `py.typed` markers existed repo-wide and `pandas-stubs` was installed, running `mypy --strict src` for the first time against the *entire* tree surfaced the true baseline. |
| Category | Architectural placeholder — same underlying control (strict static typing) as GG-065, but the prior gap's scope never extended past 2 of 89 checked source files. |
| What was missed | `mypy --strict src` (after GG-065's fixes) reports 365 errors in 57 files. Breakdown by rough category: (a) missing third-party stubs — `sklearn.*` (no py.typed upstream, affects `run_exp009.py`, `run_exp011.py`), `joblib` (affects `run_paper_trade.py`, `run_mlb_pregame.py` — same no-stub situation already `# type: ignore`'d in `run_mlb_paper_trade.py` this session); (b) bare `dict`/`list` generic-argument omissions, the same pattern fixed in `run_mlb_paper_trade.py`, recurring across `run_t4_live.py`, `run_exp009.py`, `run_exp011.py`, `run_backtest.py`, `run_mlb_pregame.py`, `run_paper_trade.py`, `t4_live_runner.py`; (c) `requests.get(params=...)` int/str mismatch in `run_t4_live.py:103` (identical root cause to the one fixed in `run_mlb_paper_trade.py` — same fix applies); (d) `pd.Series` `__setitem__` overload mismatches assigning `pd.NA` in `run_exp009.py`, `run_exp011.py`, `run_paper_trade.py` (real pandas-stubs-driven type-narrowing findings, not obviously safe to batch-fix); (e) **two errors of genuine interest in live/active-adjacent code**: `t4_mlb_execution_engine.py:198,295` — `EvaluationSignal(kelly_fraction=...)` is typed to accept `float` but is being passed a `float | None`, meaning either the type hint is wrong or a `None` can silently reach a Kelly-sizing field at runtime, worth a real look rather than a blind `# type: ignore`; (f) `run_t4_live.py:620-652` — several `T4Signal | T5Signal | None` union-attribute accesses assume a narrower type than declared (dark/frozen NBA code, lower urgency); (g) misc one-offs (`no-any-return`, `var-annotated`, `attr-defined` on `LockOpportunity.buy_yes_venue`/`buy_no_venue` vs. actual `yes_venue`/`no_venue` fields in `run_paper_trade.py:773-774` — this one in particular looks like a real latent bug in dark NBA code, not just a typing nit, and deserves its own look before being dismissed as dead-code debt). |
| When it should have been caught | Should be caught now that GG-065 exists and this baseline is quantified — the risk is this list going stale the same way the 29-error 2-file baseline did between SESSION 108 and SESSION 123. |
| Phases it survived | N/A — newly discovered, not a re-survival. |
| Why it survived | GG-065's own investigation was scoped to 2 files; nothing forced a full-tree run until `py.typed` markers made cross-module resolution actually possible. |
| Impact | LOW-MEDIUM overall, but NOT uniformly low: `t4_mlb_execution_engine.py` (item e) and `run_paper_trade.py`'s `LockOpportunity` attribute mismatch (item g) are worth individual triage — a wrong attribute name that mypy would have caught (`buy_yes_venue` vs. `yes_venue`) surviving in code at all, even dark code, is exactly the class of thing this project's strict-typing control exists to catch. Most of the remaining ~350 errors are mechanical (missing generics, missing stubs) and genuinely low-risk. |
| Discovery | Automated (mypy), triggered by GG-065 close-out work, not by any session-start protocol step (mypy is still not wired into Steps 1-4). |
| Resolution path | Not yet started. Recommend: (1) triage item (e) `t4_mlb_execution_engine.py` kelly_fraction Optional-vs-float mismatch first — it touches the live ACTIVE T4M-PROJ engine; (2) triage item (g) `run_paper_trade.py` `LockOpportunity` attribute mismatch next — confirm whether `buy_yes_venue`/`buy_no_venue` are ever actually reachable at runtime (dead code) or a real bug in dormant NBA arb logic; (3) batch-fix the mechanical categories (b), (c) — same fix pattern already proven safe in `run_mlb_paper_trade.py`; (4) either add stub packages or `# type: ignore[import-untyped]` with justification for (a); (5) individually review each `pd.Series.__setitem__`/`pd.NA` case in (d) rather than blanket-suppressing. Do not batch all 365 into one commit — several of these (e, g) are exactly the kind of finding that deserves its own focused session, not a rushed sweep. Consider wiring `mypy --strict src` (allowing a known-error baseline count, ratcheting down) into the session-start protocol once the count is near zero, so a new regression is caught immediately rather than accumulating silently again. |
| Status | **PARTIAL RESOLVE 2026-07-15 (T-368 odd-gap burn-down session).** Item (e) triaged and ruled OUT as a real bug: at both call sites (`t4_mlb_execution_engine.py:198,295`), the `kelly_fraction` value fed to `EvaluationSignal` comes from `T4_MLB_SUBBAND_REGISTRY[...].provisional_kelly`, which for `T4M_ARITH` (0.10) and `T4M_FLOW` (0.08) is a concrete float at both live call sites, never `None` — the `Optional[float]` declaration on the registry field is broader than what's actually passed here, so this is a type-hint-too-broad finding, not a runtime hazard. Item (g) triaged and CONFIRMED as a real bug, and FIXED: `class LockOpportunity` (`c5_execution/complement_lock_scanner.py:49-69`) has fields `yes_venue`/`no_venue` — no `buy_`-prefixed variants ever existed. `run_paper_trade.py:774-775` was reading `opp.buy_yes_venue`/`opp.buy_no_venue`, which would raise `AttributeError` at runtime the first time a lock opportunity was actually detected and logged (this is cross-venue arb/ detection-only code per ADR-0002/APR-0010 gating, not NBA-specific as originally guessed — reachable whenever the complement-lock scanner fires, independent of sport). Corrected to `opp.yes_venue`/`opp.no_venue`. Verified via `grep -rn "buy_yes_venue\|buy_no_venue" src/ tests/` (only the two now-corrected JSON payload keys remain) and an AST parse check. Remaining ~363 mechanical errors (categories a-d, f) are unchanged and reaffirmed as an OPEN backlog — no task assigned; re-check trigger = next dedicated typing-debt session. Zero capital risk either way — T4M-ARITH/T4M-FLOW remain registry-BLOCKED pending their own EXP verdicts, and the arb/ lock scanner is detection-only pending APR-0010. |
| Status (update 2) | **BASELINE RE-RUN + CATEGORIZED, ZERO FIXES APPLIED THIS PASS — 2026-07-16 (T-376, isolated worktree `20260716T053339Z-gg091-mypy-remediation`), parked early on an approaching session/usage limit.** (1) Re-ran `mypy --strict src` fresh against the full tree: **369 errors in 58 files** — drifted from the 365/57 figure logged 2026-07-06, a net +4/+1 despite the item-(g) `LockOpportunity` fix landing since then (not root-caused this session; plausible explanation is ordinary upstream drift in other sessions' commits touching typed code, not investigated further — flag for whoever picks this up next). Full raw output preserved only in this session's `/tmp/mypy_full_output.txt`, not committed (regenerate via the same command if needed). (2) Categorized the 369 by mypy error code: `type-arg` + `no-untyped-def` + `var-annotated` + `unused-ignore` = 179 total, of which **174 fall outside the four reserved live-money-adjacent files** (`c4_risk_engine/*`, `run_mlb_paper_trade.py`, `paper_trader.py`, `logic_epoch.py` — those four together account for the other 5: 4 in `c4_risk_engine/staged_order_store.py`, 1 in `c5_execution/paper_trader.py`). This 174-error/42-file set is the objectively lowest-risk tier (pure annotation additions — bare `dict`/`list` missing generic args, missing function annotations, one stale `# type: ignore`), no logic changes required. Remaining categories, all still fully OPEN and un-triaged this pass: `import-untyped`≈88, `arg-type`≈23, `no-any-return`≈20, `call-overload`≈20, `union-attr`≈19 (mostly item-(f), dark NBA `run_t4_live.py`), `assignment`≈11, `attr-defined`≈4, `misc`≈2, `return-value`≈1, `operator`≈1, `no-untyped-call`≈1. Per-file breakdown of the 174-error target set (highest first): `run_schedule_validator_mlb.py`(15), `run_t4_mlb_live.py`(14), `c5_execution/kalshi_client.py`(12), `t4_execution_engine.py`(9), `run_t4_live.py`(9), `c1_signal_ingestion/mlb_ingestion.py`(7), `run_mlb_pregame.py`(6), `run_exp016.py`(6), `run_exp015.py`(6), `run_t4_inplay.py`(5), `run_t2_mlb_sameday.py`(5), `run_exp017.py`(5), `c5_execution/venue_adapter.py`(5), `analytics/calibration_diagnostics.py`(5), plus 28 more files with 1-4 errors each (full list reproducible via the mypy filter command in the resolution-path note below). (3) Captured a full baseline `pytest -q` run **before touching any source** (required to exist so a future session can verify zero regressions after fixing): **2722 passed, 28 skipped, 1 pre-existing unrelated warning (date-format inference in `test_t193_mlb_freshness_guard.py:153`), 163.47s** — this is the exact target a future session must reproduce unchanged. (4) **Zero source files edited this session.** All work was read-only (mypy runs, categorization, baseline capture) — a session/usage-limit warning arrived immediately after categorization completed and before the first file edit began, so this session parked here rather than starting a 42-file sweep it could not finish and verify within its remaining budget, per this gap's own standing instruction ("Do not batch all 365 into one commit... deserves its own focused session, not a rushed sweep") and this session's explicit brief ("do not attempt to finish all 365 in one session"). Resolution path for the next session: reproduce the 174-error/42-file target list via `mypy --strict src`, filter to `[type-arg]`/`[no-untyped-def]`/`[var-annotated]`/`[unused-ignore]`, exclude lines matching `c4_risk_engine|paper_trader\.py|run_mlb_paper_trade\.py|logic_epoch\.py`, fix mechanically file-by-file (add generic params / annotations / remove the one stale ignore, no logic changes), re-run `mypy --strict` and full `pytest -q` and confirm the pytest result matches 2722 passed/28 skipped exactly, then update this gap again with real X-of-174 progress. Categories `import-untyped`(≈88) and `union-attr`(≈19, mostly dark NBA) remain unscoped for a future pass after the annotation tier is done. |
| Status (update 3) | **SUPERSEDES update 2 — that entry is now stale/incorrect ("ZERO FIXES APPLIED... parked early") and is left in place only for the historical record of the mid-session pause; do not trust its "zero fixes" claim.** The user countermanded the park instruction mid-turn ("tokens are back... proceed") and the 174-error/42-file target tier identified in update 2 was fixed in full this same session (T-376). **Mechanical fixes:** 156 `type-arg` sites (bare `dict`/`list`/`set` → `dict[str, Any]`/`list[Any]`/`set[Any]`) fixed via a line-targeted regex script against the exact `(file, line)` tuples from mypy's own output; 18 remaining `no-untyped-def`(13)/`var-annotated`(3)/`unused-ignore`(2) fixed individually by hand after reading each site's surrounding context (e.g. `run_t4_mlb_live.py`'s `status_fn` parameter typed `Callable[[str], str]` only after confirming `_espn_game_status`'s actual signature; `run_exp011.py`'s `_eval(model, X, y, ...)` typed `Any` for all three only after checking every call site's actual argument types). **Self-inflicted incident, caught and fixed before verification completed:** the supporting "ensure `Any` is importable" script had a real bug — for the 24 files with no pre-existing top-level typing import, it scanned the *entire file* (not just the top-level import block) for the last `import`/`from` line and inserted `from typing import Any` there with no indentation or docstring awareness. This corrupted 4 of those 24 files: `run_exp010.py`, `run_pregame.py`, `run_paper_trade.py` each got the bare import line inserted mid-body at column 0 inside an indented `try:`/`if:` block, breaking Python's block structure (`mypy --strict` aborted the *entire* tree check with `Expected 'except' or 'finally' block [syntax]` the moment it hit the first one — the true post-fix error count was unknowable until this was found and fixed); `run_exp001.py` got it inserted inside a docstring, which didn't break syntax but meant `Any` was never actually imported, silently producing 3 new `[name-defined]` errors once mypy could reach that far. All 4 fixed by moving the import to each file's real top-level import block and removing the stray line. Caught via `ast.parse()` against every `.py` file in `src/` (0 syntax errors found post-fix, up from 3 broken files pre-fix) plus a full mypy re-run confirming 0 `[name-defined]` errors; the other 20 of the 24 "INSERTED" files were individually confirmed to have exactly one correctly-placed top-level `from typing import Any` line (`grep -c "^from typing import Any$"` == 1 each) — no further defects of this kind found. **Verification (both required before/after comparisons hold):** `mypy --strict src` now completes a full, uninterrupted run (previously aborted on the syntax error) — **203 errors in 46 files**, down from the 369/58 baseline (166 fewer errors, 12 fewer files); every remaining `[type-arg]`/`[no-untyped-def]`/`[var-annotated]`/`[unused-ignore]` hit is confirmed confined to the two reserved files (`c4_risk_engine/staged_order_store.py`×4, `c5_execution/paper_trader.py`×1) that were correctly left untouched per this task's brief. `pytest -q` full suite: **2722 passed, 28 skipped, 1 warning** — identical to the pre-fix baseline (same pre-existing `test_t193_mlb_freshness_guard.py:153` UserWarning), confirming zero behavioral regressions from the annotation-only changes. **Remaining OPEN backlog (unchanged from update 2's categorization, none touched this pass):** `import-untyped`≈88, `arg-type`≈24, `call-overload`≈21, `no-any-return`≈20, `union-attr`≈19 (mostly dark NBA `run_t4_live.py`), `assignment`≈15, `attr-defined`≈4, `misc`≈2, `return-value`≈1, `operator`≈1 — total 203, next session's target. This is genuine multi-session remediation progress (369→203 errors, 58→46 files), not a close-out; GG-091 remains OPEN. |

</details>

---

### GG-094 — MLB Has No Qualitative/PRF-Analogue Feature Layer Despite Being the Sole ACTIVE Pool

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** mlb_features.py still has 0 references to qualitative/PRF (grep this session). **Next:** Design MLB qualitative layer; tied to pre-game deep-tree directive (ADR-0068).

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-094 |
| Arm | MLB |
| Category | Incremental architecture — a methodology component CLAUDE.md itself names as a T1 alpha input does not exist for the only currently-active sport. |
| What was missed | CLAUDE.md's own T1 alpha description names "PRF qualitative factors" (player quality, role-fit, form) as a model input alongside quantitative rolling stats. Direct grep confirms `src/prediction_market_bot/c2_feature_store/mlb_features.py` has zero references to `qualitative`, `PRF`, or `prf_w0*` (0 hits) — MLB's C2 feature layer is quantitative-only. `qualitative_store.py`/`qualitative_amplifier.py` (the modules that do carry PRF content) are NBA-only, consistent with GG-027/T-243's separate finding that the PAM v4 taxonomy is NBA-native end-to-end (player_id requires `nba_api` IDs). MLB's 151 resolved T1 positions and its DIRECTIONAL_POSITIVE EXP-017 result were produced entirely without this component. |
| When it should have been caught | MLB's Phase 3 buildout (the point MLB became the active pool) — CLAUDE.md's T1 description was written with NBA's PRF-equipped architecture in mind and was never re-scoped when MLB became the sole active sport with a quantitative-only C2. |
| Phases it survived | MLB Phase 3 buildout through today — the entirety of MLB's live paper-trading history (49→151 resolved positions) has run on a T1 implementation missing a component its own governing document names as core to the thesis. |
| Why it survived | Two separate audits (GG-027/T-243's PAM-v4-is-NBA-only finding, and this GG-074 pass) had to independently re-derive the same underlying fact from different entry points — MLB's feature parity with NBA was never directly checked end-to-end in one pass until now. |
| Impact | MEDIUM-HIGH, methodology-level. This does not invalidate MLB's DIRECTIONAL_POSITIVE EXP-017 result (n=151, EV=+$0.1009/bet) — the result is real and was produced by whatever MLB's T1 actually is — but it means CLAUDE.md's own written description of "the T1 thesis" overstates what MLB's live model actually uses as inputs. A reader relying on CLAUDE.md's T1 description to explain MLB's edge would be wrong about the mechanism. This is a documentation/scope-accuracy risk now; it becomes a methodology decision later if/when MLB PRF work (T-243) is ever scoped. |
| Discovery | 2026-07-06, GG-074 background audit agent (`a301d6be8aec05d3f`), via direct code inspection; independently re-confirmed by the calling session (`grep -c` → 0) before registering. Consistent with, and cross-links to, GG-027/T-243 (registered same session, different discovery path). |
| Resolution | Not a same-session fix — building an MLB-native qualitative/PRF-analogue layer is a from-scratch DS-source project per T-243's own scoping (taxonomy design, player classification, an ADR, and a Hard-Rule-4-compliant decision on how a frozen already-validated MLB model would consume a new feature set). This gap's own resolution is documentation-only for now: `QUALITATIVE_SIGNALS.md`/`MLB_BUILDOUT_SCAFFOLD_PLAN.md` corrected in place to state MLB has no qualitative layer, rather than implying one exists. CLAUDE.md's T1 description should be read as NBA-accurate/MLB-inaccurate until T-243 is scoped and actioned. |
| Status | OPEN — doc corrected 2026-07-06; underlying methodology gap tracked via T-243 (unscoped/unsized), not expected to close soon. Zero capital risk in the sense that MLB's real, positive result stands regardless — risk is purely in how the mechanism is described. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed as watch item, no change** — T-243 remains unscoped/unsized; no new evidence this pass. Re-check trigger unchanged: when T-243 is prioritized/scoped by operator directive (parallel to [[GG-066]]'s disposition). |

</details>

---

### GG-098 — MLB T1 Aggregate EV Metrics Are Cited as Milestones While Still Variance-Dominated (Small-n Subset Structure Masked; Aggregate Sign-Flipped n=151→169)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Aggregate-vs-direction decomposition concern stands; not re-run. **Next:** Re-run EXP-017B decomposition on current clean cohort.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-098 |
| Arm | MLB |
| Category | Systemic blind spot — a headline commercial-validation metric (EXP-017 Tier-1 +$0.1009/bet) that is not internally decomposed can mask a losing sub-strategy inside a "positive" aggregate. |
| What was missed | EXP-017 reported a single aggregate EV/bet and a monotonicity guard, but never split the book by bet DIRECTION. Decomposition (EXP-017B) shows all positive edge is NO-side (n=140, +8.71%/staked, +$125.50) while the YES sub-book (n=11) is −62.11%/staked (−$110.27), erasing ~88% of NO profit. The aggregate +$0.1009/bet is bootstrap-insignificant (95% CI [−$1.86,+$2.13], P(EV>0)=53%). |
| When it should have been caught | At the EXP-017 Tier-1 read (2026-07-06). A Tier verdict on an aggregate should have been paired with a direction/threshold/edge-bucket decomposition before being cited as evidence of edge. |
| Phases it survived | MLB paper-trading G6 pursuit (49→151 resolved). The EXP-017 script has a monotonicity guard (GG-037/T-177 class) but no direction split. |
| Why it survived | No internal-validity companion existed for EXP-017; the aggregate + monotonicity guard were treated as sufficient. EXP-017B/C/D were built this session to fill that gap. |
| Impact | MEDIUM. Does NOT invalidate the Tier-1 milestone, but materially qualifies it: the edge is NO-only, non-monotonic in realized profit, tail-concentrated, and aggregate-insignificant. EXP-017C shows the model is nonetheless well-calibrated (slope CI includes 1) — so the shortfall vs expected is variance, not miscalibration. Risk is over-crediting the aggregate when reasoning about G6/live readiness. |
| Discovery | 2026-07-07, edge-strategy decomposition session (EXP-017B/C/D), via direct decomposition of the live cached book (`logs/.vps_portfolio_cache_mlb.json`, n=151). Headline reproduced to 4 dp before decomposing. |
| Resolution | (1) EXP-017B/C/D registered as the standing internal-validity companion to EXP-017 (re-run as n grows). (2) ADR-0042 — **corrected 2026-07-07**: the original proposal to quarantine YES was REJECTED by the operator as over-calibration on n≈11; ADR now monitors YES and keeps collecting. (3) A/B harness given a `MIN_REMOVED_N`=30 guard so category-removal filters return `UNDERPOWERED_REMOVAL` not DEFENSIBLE on tiny removed sets. (4) T-250 reframed to monitor-and-investigate-at-higher-n; T-251 re-runs the decomposition as n grows. Does NOT close GG-004. |
| Status | OPEN (watch item, by design) — registered 2026-07-07. The core gap (aggregate metrics cited as milestones while variance-dominated) is reinforced by the aggregate sign-flipping +$15.23 (n=151) → −$44.76 (n=169) in 18 bets. YES underperformance is variance-consistent (Binomial P(≤0)=0.073 on the k=2 0/7 run; model under-predicts k=2 at threshold level). Pre-registered monitor: revisit YES only at n_YES ≥ 40 with Fisher p<0.05 AND an identified mechanism. Watch item — no quarantine, no stop-work. **Citation-hygiene verification pass, 2026-07-12 (T-349):** audited every "milestone"/EV-citation surface for an unhedged claim — `CLAUDE.md` § "commercial validation gap", `07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-03/EVIDENCE.md`, `exp_output/EXP-017B-DECOMP/FINDINGS.md`, `MEMORY_BANK.md` — all four already carry the direction-split/bootstrap-insignificance/"milestone not proof" caveats this gap calls for; none found requiring correction. This gap stays OPEN as its own pre-registered watch item (the n_YES≥40 trigger above), not because a doc-hygiene action remains outstanding. **Disposition (2026-07-15, GG-burndown-even pass): (c) reaffirmed, no change needed** — this gap's design is already exemplary (pre-registered numeric trigger, prior citation-hygiene pass found nothing to fix). Confirmed the current pre-registered trigger (n_YES≥40, Fisher p<0.05, identified mechanism) still stands unmodified. **Update 2026-07-17 — ADR-0042 D2 ACCEPTED (Earl Ignacio, DS sign-off):** the A/B harness holdout-gate is now formally binding on all future strategy-enhancer activation (it was already being followed informally per T-252, but had not cleared ADR-0042's own sign-off gate until today). Flagged at sign-off that this ADR's own cited P&L figures (n=151/n=169 above) are stale relative to the current book (T1 has since moved through GG-119/ADR-0045's epoch reset) — does not change this gap's own status or trigger. |

</details>

---

### GG-105 — T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship between its own computed edge and realized win rate, on clean data (Workstream B / T-322/T-323/T-324 discovery)

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Remediation in progress per entry (ADR-0047 shrinkage live since epoch 8); T4M-PROJ now clean_n=1898 so anti-predictive tercile can be retested. **Next:** Re-run tercile test on clean cohort.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-105 |
| Arm | MLB |
| Status | **OPEN — remediation in progress, 2026-07-17 (T-382, ADR-0047/APR-0025, worktree `20260717T201405Z-apr0025-gg105-ba-l10-shrinkage`). Do not read this as resolved.** DS sign-off (operator, Earl Ignacio, 2026-07-17) accepted APR-0025's empirical-Bayes shrinkage remediation with three parameters resolved: K=40 (shrinkage strength, conservative default not a data-fit optimum), real per-player `ab_sum` (not the flat `AB_WINDOW=37` constant) as the observed-sample-size term, and ship-shrinkage-alone-now/defer-H2 (pregame `p_t1` blending, a second hypothesis, explicitly not tested or implemented under this fix). Implemented this session: `ba_l10_shrunk` column in `mlb_features.py` (`MLB_FEATURE_VERSION` 1.0.0→1.1.0, additive), surfaced audit-only in `run_mlb_pregame.py`, and wired to actually drive T4M-PROJ's live Binomial calc in `run_t4_mlb_live.py` (`p_hits_gte_threshold(..., ba_l10=ba_l10_shrunk, ...)` — the behavioral fix). Full ADR: `03_DECISIONS/ADR-0047_gg105-ba_l10-shrinkage.md`. Test suite green (271/271 in the three touched files, including a new `_run_cycle()`-level test proving the shrunk value — not raw `ba_l10` — drives the logged `p_t4`; full-suite regression run pending/see DECISION_LOG.md for result). **This ADR implements the remediation; it does not itself constitute proof the anti-predictive pattern is resolved.** GG-105 stays OPEN until a fresh tercile-monotonicity re-measurement runs against a clean, post-fix epoch cohort — that re-measurement requires sufficient post-fix `clean_n` to accumulate first (see GG-124 below) and is not yet scheduled. H2 remains deferred, not dropped — needs its own follow-on task/ID when picked up. Prior history (through 2026-07-16, T-378) preserved below for context. — **Addendum 2026-07-16 (T-378, "Terminal 2" GG-105 investigation session); verdict unchanged, mechanism narrowed.** T4M-PROJ's computed edge is robustly anti-predictive (tercile win rate declines monotonically as edge magnitude rises) across every diagnostic run against it (game-state segmentation, sizing-artifact check, edge-formula/vig audit, a formal H1×H4 interaction model, and — new this pass — a retrospective NBA-ADR-0027-style temperature-scaling what-if) — game-state noise, sizing artifacts, analysis-tooling vig omission, **and now global temperature scaling**, have all been ruled out as fixes/causes. **New 2026-07-16 finding: temperature scaling (the exact T=2.05 remediation NBA used in ADR-0027) does NOT flatten the anti-predictive tercile pattern — it makes it substantially worse (Fisher p 0.0212→0.0000, tercile spread ~22.5pp→~41pp) even as it improves aggregate calibration slope/ECE, a real dissociation between aggregate model_p calibration and edge-tercile rank-ordering.** This rules out the simplest, most-precedented remediation candidate and sharpens the case for APR-0025's per-feature shrinkage approach over a global rescale. Leading mechanism remains model miscalibration/overconfidence, with H1 (unshrunk `ba_l10` as a noisy per-AB Bernoulli parameter) showing a clean, monotonic dose-response under empirical-Bayes shrinkage (T-359) — still the only remediation candidate tested so far that moves both the Fisher p-value and tercile winrate gap in the correct direction. **Full investigative history (2026-07-10 through 2026-07-16: T-322/T-323/T-324, T-329, T-332, T-333, T-340, T-341, T-344, T-345, T-359, T-361, T-378): see `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG105_FULL_HISTORY.md`** (verbatim, lossless move verified 2026-07-15; 2026-07-16 addendum appended). **Separately, this session also discovered and registered [[GG-124]]** — `run_band_monitor.py`'s official `clean_n` filter currently returns 0/UNDERPOWERED for T4M-PROJ (and all other active bands) due to three rapid-fire logic-epoch boundary bumps; this session's diagnostics used the relaxed `logic_epoch==3` cohort (n=666) instead, per the data-cohort caveat documented in `scripts/run_t373_gg105_temp_scaling_whatif.py`. **Addendum 2026-07-18 (T-385) — activation-timing correction + epoch 7 registered.** The ADR-0047 fix did NOT go behaviorally live at merge/deploy: `run_t4_mlb_live.py` falls back to raw `ba_l10` when the pregame JSON lacks `ba_l10_shrunk`, and the 2026-07-17 pregame regeneration (PIPE-06pre, 22:15 UTC) predated the merge (`f961fba`, 2026-07-18 00:33 UTC) — verified directly: zero `ba_l10_shrunk` fields in `pregame_mlb_20260717.json`, and zero T4 evaluation cycles ran between the post-deploy `t4-mlb` restart (01:17 UTC) and game-night end (last audit eval 00:34 UTC), so the entire Jul-17 game night is cleanly pre-fix with no mixed cohort. Behavioral activation = the first post-deploy pregame regeneration, 2026-07-18 at the PIPE-08-set PIPE-06pre time in [14:00, 22:15] UTC. **`CURRENT_LOGIC_EPOCH` advanced 6→7 (`logic_epoch.py`, boundary anchored 2026-07-18T14:00Z — the earliest-possible regeneration time, analyzed to zero behavioral misclassification since T4M-PROJ cannot open a bet pre-regeneration and no other band's write path changed), DS sign-off Earl Ignacio 2026-07-18.** Consequence for this gap: the post-fix tercile re-measurement cohort is the epoch-7 `clean_n`, accruing from 2026-07-18 games onward. Pending same-day verification: `pregame_mlb_20260718.json` contains `ba_l10_shrunk`, and `audit_mlb_t4.jsonl` logs distinct raw-vs-shrunk values once games go live — if that verification fails, the epoch-7 boundary is mis-anchored and must be corrected before any epoch-7 bets resolve (contingency documented in `logic_epoch.py`). See DECISION_LOG.md 2026-07-18. **Addendum 2026-07-19 (T-387): the epoch-7 contingency FIRED — verification failed, remediated same-day, epoch advanced 7→8.** The 2026-07-18 15:55 UTC pregame regeneration emitted `ba_l10_shrunk: null` for all 62 players: `run_mlb_pregame.py` sources the field from `exp_output/MLB/mlb_feature_matrix.csv`, and the VPS CSV had last been regenerated by PIPE-05FX (22:30 UTC nightly cron) at 22:35 UTC Jul-17 — two hours *before* the ADR-0047 merge — so the column didn't exist and every lookup returned NaN→null. `run_t4_mlb_live.py`'s fallback therefore kept T4M-PROJ on raw `ba_l10` through the Jul-18 afternoon slate (~200 paper orders) while stamping every bet epoch 7 — exactly the mis-stamping the contingency named, and some of those bets resolved before correction landed. Remediation (operator-selected "fix tonight + epoch 8" over self-heal-tomorrow and re-stamp-surgery alternatives, 2026-07-18): manual PIPE-05FX re-run (CSV regenerated with the column, 18:04 UTC), manual PIPE-06pre re-run (`pregame_mlb_20260718.json` repopulated with real values), `t4-mlb` restart 18:06:52 UTC. **Behavioral activation verified directly: first cycle row with distinct raw-vs-shrunk values at 2026-07-18T18:07:19Z; `pregame_mlb_20260719.json` (15:55 UTC cron run, post-fix CSV) has zero nulls; `t4_mlb_cycle_log.jsonl` shows 3,004 shrunk-bearing rows, 2,835 with `ba_l10 != ba_l10_shrunk` — the ADR-0047 verification that was pending above is now PASSED, but at 18:07Z Jul-18, not 14:00Z.** Because the stamped-7 cohort irreversibly mixes pre-fix fallback bets with genuinely shrunk-behavioral ones, `CURRENT_LOGIC_EPOCH` advanced 7→8 (boundary 2026-07-18T18:07:19Z, same resolving commit `f961fba`) — the GG-105 post-fix tercile re-measurement cohort is now the **epoch-8** `clean_n`, accruing from bets stamped after the epoch-8 deploy (2026-07-19). Note the shrunk values themselves have driven live T4M-PROJ evaluation continuously since 18:07Z Jul-18; only the clean-cohort accounting restarts later. See DECISION_LOG.md 2026-07-19 (T-387). **Addendum 2026-07-20 (T-392) — H2 draft APR registered (this is the "follow-on task/ID" the entry above said H2 was waiting for; nothing else about GG-105's status changes).** `00_ADMIN/APR-0030_gg105-h2-pt1-blended-shrinkage-prior.md` (DRAFT, PENDING in `APPROVALS_REGISTER.md`, not submitted for DS sign-off) proposes testing whether blending T1's own pregame `p_t1` estimate into `ba_l10_shrunk`'s shrinkage prior — currently a player-agnostic population mean (`PRIOR=0.2512`, per ADR-0047) — narrows the residual anti-predictive gap that APR-0025's own T-359 sweep found persists at every tested shrinkage strength up to K=160. The draft proposes a diagnostic sweep only (methodology and open questions documented in the APR itself, including the nontrivial `p_t1`→per-AB-rate conversion step and the architectural tension of coupling T1 and T4 signals for the first time); it does not run that sweep, select a blend weight, or authorize any code change. This does not supersede or change the standing GG-105 remediation status: GG-105 stays OPEN pending the H1-alone post-epoch-8 tercile re-measurement (still blocked on `clean_n` accrual per GG-124), which should be checked before H2 is prioritized — if H1 alone has already closed the residual gap, H2 becomes moot. See DECISION_LOG.md 2026-07-20 (T-392). **Addendum 2026-07-24 (A2/A3, isolated worktree session/20260724T144459Z-a2-refit):** two standalone remediation candidates tested via the D1 what-if harness against MAIN's real resolved ledger (n=273 matched cohort) — A2 (LR+Platt refit on A1's `ba_l10_shrunk_a1_candidate` feature alone) and A3 (isotonic recalibration alone, same feature, superseding ADR-0004's sigmoid choice for this candidate only). **Both FAIL** the edge-tercile-monotonicity criterion — direction stays inverted/non-monotonic, same qualitative shape as the pre-fix baseline (t1 highest win rate, t2 lowest, t3 partial recovery). Both PASS calibration-slope-CI and Brier/ECE vs. ADR-0046 baselines. Neither candidate is promoted; no epoch bump; no live model change. T-384 (GG-105 H2, blend pregame `p_t1` into the shrinkage prior, APR-0030 DRAFT/PENDING) remains the next registered, DS-gated candidate — not yet actioned. See DECISION_LOG.md 2026-07-24 (A2/A3 rows), `04_EXECUTION/ITERATION_MC_PROGRESS.md` (A2 DONE line). **Addendum 2026-07-28 (this session, C1/GG-004 stabilization-freeze worktree) — escalation from "recalibrate" to "feature/model-class rework", GG-140 registered.** A2 (LR+Platt) and A3 (isotonic) join the 2026-07-16 temperature-scaling result as three separate monotonic-transform candidates that all failed the identical edge-tercile-monotonicity criterion while passing calibration-slope-CI/Brier/ECE. This is not coincidence: temperature scaling, Platt scaling, and isotonic regression are all strictly monotonic transforms of the model score, and a monotonic transform cannot alter rank ordering — only magnitude. If the underlying ranking is inverted (as GG-105's tercile pattern shows), no member of this transform class can fix it, by construction. See **[[GG-140]]** for the full structural finding. **Practical consequence: recalibration is closed off as a remediation path for GG-105.** The only remaining levers are (a) new rank-ordering features — T-384/APR-0030's H2 (blend pregame `p_t1` into the shrinkage prior) qualifies, since it changes the feature/ranking, not just the output transform — or (b) a non-monotonic model-class change superseding ADR-0004's LR+Platt pipeline. GG-105 stays OPEN; this addendum narrows, not closes, the remaining candidate space. **Addendum 2026-07-28 (Window B3, `03_DECISIONS/ADR-0048_edge-conditional-variance-aware-sizing.md`, PROPOSED):** since A2/A3 both FAILED with no further contingency in scope, and Platt/isotonic are both monotonic transforms unable to repair an inverted rank ordering, GG-105 is now explicitly load-bearing on the sizing side too, not just the modeling side — ADR-0048 sets `kelly_fraction=0` as the default operating point for every band whose edge signal depends on this defect (T1_MULTI_DAY, T2_SAME_DAY, T3_PRE_TIP, and — author's judgment call, flagged for override — T4M_PROJ, since GG-105 originated there) until this gap resolves. ADR-0048 is a sizing-side mitigation for the *consequence* of GG-105 (unvalidated edge sized as if real); it does not attempt to resolve GG-105 itself and does not change this gap's status or remediation path (still T-384/H2, DS-gated, not yet actioned). |

</details>

---

### GG-121 — 2026-07-11 T1 MLB `SemanticFloorViolation` (games_fetched=16, matched_players=0) surfaced by GG-049's own heartbeat but never logged

**Status:** WATCH ITEM · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-121 |
| Arm | MLB |
| Category | Detection-worked-but-no-close-loop — the GG-049 heartbeat mechanism fired correctly and the finding was then never registered anywhere |
| What was missed | CLAUDE.md Step 4's semantic-oracle check (`grep -c "SemanticFloorViolation" .../paper_mlb_cron.log`) is designed to surface exactly this failure mode (GG-049: pipeline runs, produces zero evaluations). It did its job: `paper_mlb_cron.log` line 1229 logs `[PIPE-05] CRITICAL semantic_floor_violation: SemanticFloorViolation: PIPE-05 MLB — games_fetched=16 but matched_players=0`, dated 2026-07-11 (`PT-MLB-2CD75D5F`). Nobody appears to have registered this specific incident in `GOVERNANCE_GAP_LOG.md` or `DECISION_LOG.md` at the time — this session (2026-07-15 Step 4 re-run) is the first to find it, 4 days after the fact. |
| When it should have been caught | Whichever session ran CLAUDE.md Step 4 first after 2026-07-11's cron run (session-start protocol runs Step 4 every session — this should have surfaced same-day or next-day, not 4 days later). |
| Phases it survived | At least one intervening session-start Step 4 run (unclear exactly how many, since no session logged catching it) between 2026-07-11 and 2026-07-15. |
| Why it survived | The check greps a cumulative log for a nonzero count and instructs "investigate immediately" but has no artifact requirement forcing that investigation's outcome to be written down anywhere — a session can run the grep, see a `1`, informally decide "single historical blip, log looks healthy around it," and move on without a durable record. That is what appears to have happened here. |
| Impact | LOW for this specific incident — confirmed single occurrence (`grep -c` on the full log = 1, only date-hit = 20260711), immediately surrounded by healthy runs before and after (per this session's Step 4 primary output: 18/0(anomalous)/24/23/19/29 bets across 6 recent runs, with player-match counts 35/29/26/0(same anomalous row)/37/36 — one bad run, not a trend), and 4 days stale with no recurrence. Not a live signal requiring action. The real gap is procedural: the heartbeat can fire, get manually waved off, and leave no trace — which is the exact "self-reported health > reality" failure pattern this project's own audit directive was built to catch. One dark evaluation cycle on one game-day is a small, bounded miss; a detection mechanism that can silently no-op an unknown number of times is not. |
| Discovery | 2026-07-15, this session (odd-gap burn-down, T-368), CLAUDE.md Step 4 VPS operational health check + its `SemanticFloorViolation` semantic-oracle follow-up. Confirmed root incident via `grep -n -B3 -A3` context read; confirmed single-occurrence, single-date via `grep -c` and date-extraction against the full log. Confirmed not already registered via `grep -in "SemanticFloorViolation|matched_players=0|2026-07-11" GOVERNANCE_GAP_LOG.md` (zero prior hits) — distinct from GG-049 (the mechanism that detected this) and GG-118/GG-120 (unrelated). |
| Resolution | Not a code fix — this entry *is* the resolution for the specific 2026-07-11 incident (closing the loop GG-049's detection opened but nobody recorded). No live/recurring failure to fix; single incident, 4 days stale, no recurrence. The procedural gap (heartbeat hits can be silently dismissed) is registered as a watch item below rather than fixed outright, since fixing it (e.g. forcing an artifact per nonzero hit) is a process-design change this odd-gap session did not scope or size, and none of the touched thresholds/models/gates are implicated (Hard Rule 3 does not apply — this is a logging-discipline gap, not a threshold/model/gate decision). |
| Status | **WATCH ITEM — reaffirmed 2026-07-15.** Re-check trigger: any session whose Step 4 `SemanticFloorViolation` grep returns a count that increased since this entry's 2026-07-15 reading (currently 1, all-time, single date 2026-07-11) must treat it as a fresh incident requiring the same investigation this entry performed, and must register the outcome here (or in a new GG-NNN) rather than waving it off informally — that is the specific behavior this gap exists to prevent recurring. No DS sign-off required to close further recurrences of this exact pattern (logging discipline, not a threshold change); a genuinely new incident (different date, nonzero recent `game_state_fresh`-style staleness, or a live player-mismatch) should still get its own fresh gap number rather than being folded into this one. |

</details>

---

### GG-127 — 00_ADMIN/README.md (designated nav hub, ADR-0001) went ~7 weeks with zero updates while the project moved through multiple phase transitions

**Status:** IN PROGRESS · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-127 |
| Arm | Core |
| Category | Documentation-integrity — same class as GG-108/GG-122/GG-126 (a real state change happened; the document meant to reflect it was never updated), but on the nav hub itself rather than a decision/status log. |
| What was missed | `00_ADMIN/README.md` is this project's designated "Navigation hub and canonical entry point... Start here" per its own header and ADR-0001 (Compass OS adoption). Its own governing workflow (`00_ADMIN/Project Directory Compass OS Workflow.txt`) prescribes a weekly Directory Integrity Review (DIR) specifically to prevent exactly this. Git confirms the file was last touched 2026-05-28 and its `Last reviewed` header field read 2026-05-21 — while the project moved from Phase 0 (all gates "Not Started") to Phase 6/7 ACTIVE with MLB paper trading live, G6 in progress, and Tier 1 commercial validation cleared (GG-004). Its "Where to Find Things" table and Canonical Artifacts table were both frozen at baseline. A second, related instance: `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` (Last reviewed 2026-05-31) carried a stale-content caveat that told readers to check `CLAUDE.md` for the live band registry instead of maintaining its own — which is a structural contributor to why `CLAUDE.md` had accumulated decaying state (band-status inventory, commercial-validation n-count history) that this same session also relocated. |
| When it should have been caught | Any of the ~7 weeks of sessions between 2026-05-21 and 2026-07-19 that ran CLAUDE.md's mandatory session-start protocol — none of Steps 0-4 or Q1-Q6 check the nav hub's own freshness, only code stubs, governance gaps, and VPS pipeline health. |
| Phases it survived | Multiple phase transitions (Phase 0 → Phase 6/7 ACTIVE), multiple gate closures (G0-G5), the entire MLB buildout, dozens of sessions per `SESSION_CLAIMS.md`/`MEMORY_BANK.md` density over the same window. |
| Why it survived | No automated check compared this file's own `Last reviewed` date against a freshness threshold. The weekly DIR cadence this file's own "Update Cadence + Owners" table documents was never wired to any enforcement mechanism — it existed as prose intent only, the same gap class GG-074 found for grounding-docs generally (`01_SPEC/`, `02_ARCHITECTURE_DESIGN/`, etc.), but GG-074's monthly grounding-docs review, adopted 2026-07-06, apparently never swept `00_ADMIN/README.md` itself in the ~6 weeks since (or did and found nothing, which is equally concerning given the actual staleness found here). |
| Impact | MEDIUM — no capital/gate impact (this is a navigation document, not a state-of-record for gate evidence), but real operator-trust impact: a new reader following this project's own stated onboarding path ("Start here") would have been told the project was in Phase 0 with zero gates closed, a materially false picture of a system with live paper trading and an in-progress G6 gate. Discovered during a Cowork session responding to an operator question about CLAUDE.md bloat and nav-hub discoverability — not caught by any internal process. |
| Discovery | 2026-07-19, Cowork session, prompted by an operator question about whether a new user could find things like "Compass Health," the latest strategic update, the mathematical overview, or continuous testing results. Verified via direct file read + `git log` on `00_ADMIN/README.md`, not assumed. |
| Resolution | Same session: `00_ADMIN/README.md` revived (current phase/gate table, expanded "Where to Find Things" table including the four items the operator asked about by example, Canonical Artifacts table replaced with a pointer to `MEMORY_BANK.md` rather than a second hand-maintained index, new "Compass Health" section stating this finding honestly). `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` revived alongside it with a new "Live Registry" section (moved verbatim from `CLAUDE.md`, which now points here instead of the reverse). `CLAUDE.md`'s decaying-state sections (band-status inventory, commercial-validation n-count history) condensed to one-line pointers to their proper homes — vision/intent/hard-rules/session-start-protocol sections explicitly left untouched per operator instruction mid-session. **Structural fix:** `.claude/hooks/governance_scan.sh` gained a nav-hub staleness check — parses `00_ADMIN/README.md`'s `Last reviewed` date on every session start, ALERTs if >14 days old (2x the nominal weekly DIR cadence), mirroring the existing register-parity check's pattern. This makes the failure visible again; it does not by itself restore the weekly DIR cadence itself, which remains documented intent only — see Status below. |
| Status | **IN PROGRESS.** The specific instance (both files' staleness) is RESOLVED as of 2026-07-19. The structural detection gap (no freshness check existed) is RESOLVED via the new governance_scan.sh check. **The root cause — the weekly DIR cadence itself is not actually running, only documented — is NOT resolved** and is explicitly flagged as such in the revived `00_ADMIN/README.md`'s own Update Cadence table. A future session (or the operator directly) should decide whether to actually run a DIR pass on a real cadence, extend GG-074's monthly grounding-docs sweep to explicitly include `00_ADMIN/README.md` and `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` by name, or accept the 14-day ALERT as sufficient backstop without a scheduled human review. **Note on session provenance:** this session ran without VPS/git-push access (Cowork sandbox, not a full Claude Code session with `scripts/claim_session.sh`/worktree tooling) — GG-127 and the provisional task ID T-389 were assigned as next-free against the last-known state of `GOVERNANCE_GAP_LOG.md`/`TODO_NEXT.md` but were **not claimed via the concurrent-session claim system** and were **not pushed to `origin`**. The next session with push access should verify GG-127/T-389 are still next-free before treating them as final, per this project's own documented ID-collision precedent (SESSION_CLAIMS.md has multiple recorded renumbering events for exactly this reason). **Provenance closed 2026-07-19 (follow-on Claude Code session, push access available):** all 8 touched files (CLAUDE.md, EXECUTION_BANDS.md, GG004_ev_validation_benchmark_history.md, README.md, governance_scan.sh, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, TODO_NEXT.md) confirmed committed and pushed — `git log`/`git status` show working tree clean, local HEAD (`45225ea`) matching `origin/main` exactly. `bash .claude/hooks/governance_scan.sh` run for real: NAV-HUB STALENESS (GG-127) section prints cleanly (exit 0), reports `README.md` 0 days old. ID-collision re-check against `SESSION_CLAIMS.md`/`TODO_NEXT.md`/`GOVERNANCE_GAP_LOG.md`: GG-127 correctly follows GG-126 (last claimed 2026-07-18, Terminal B); T-389 correctly follows T-388 (registered in commit `24b508a`, 13:56:42-07:00 — before this task's `c4f2139`/`45225ea` commits at 14:54:31-07:00); no other session claimed either ID (zero hits for "GG-127" or "T-389" anywhere in `SESSION_CLAIMS.md`). **No renumbering needed — both IDs are final as originally assigned.** Retroactive claim row added to `SESSION_CLAIMS.md` for this verification pass. **This closes only the ID-provenance/push-verification caveat — the root-cause item (weekly DIR cadence not actually enforced) remains OPEN, unchanged, per this entry's own Status field above.** |

</details>

---

### GG-133 — CHANGELOG.md has not been updated since 2026-05-30 despite ~2 months of major changes, violating its own staleness trigger

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** 00_ADMIN/CHANGELOG.md latest entry now 2026-08-23 (was 2026-05-30), but ~6 weeks stale again. **Next:** Add entries for Waves since 2026-08-23.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-133 |
| Arm | Core |
| Category | Documentation-hygiene — grounding-doc staleness, discovered during GG-074's first-ever monthly review run. |
| What was missed | `00_ADMIN/CHANGELOG.md`'s own header states it is "Updated continuously; reviewed weekly at DIR" with staleness trigger "Any major change without a corresponding entry." Its most recent entry is dated 2026-05-30. Since then, this project has shipped its dual-ledger MLB/NBA split (ADR-0035/ADR-0037), the T4 MLB build and multiple sub-band activations, EXP-017 and the APR-0024 variance-derived n* standard superseding the flat 30/150/500 heuristic, ADR-0026/APR-0020 (two-tier free-cash invariant), ADR-0040 (Kelly de-rating from ruin-risk MC study), the VPS web dashboard (GG-057), and dozens of other DECISION_LOG-logged changes — none of which produced a CHANGELOG.md entry. |
| When it should have been caught | At any weekly DIR-equivalent review, or by this project's own GG-074 monthly grounding-docs staleness process — except GG-074 itself was adopted 2026-07-06 and never run until this session, so no process ever checked this. |
| Phases it survived | 2026-05-30 through 2026-07-23 (~8 weeks), spanning the entirety of Phase 6/7 ACTIVE's major architecture growth. |
| Why it survived | `DECISION_LOG.md` became the de facto operative record for Hard Rule 7 ("every strategic decision goes into DECISION_LOG.md immediately") and appears to have silently superseded CHANGELOG.md's role as the human-readable timeline view — but no decision was ever made to retire or supersede CHANGELOG.md, so it sits as a grounding doc making a false "updated continuously" claim. |
| Impact | LOW — no capital/gate/trading-logic impact; this is a navigational/orientation doc, not a state-of-record. Risk is a new session or the operator trusting CHANGELOG.md's dated entries as a complete timeline when in fact two months of major architecture history are absent from it. |
| Discovery | 2026-07-23, this session, while executing GG-074's monthly grounding-docs staleness review for the first time (operator-directed). |
| Resolution | Not fixed this pass — backfilling ~8 weeks of major-change entries is a substantial dedicated task, out of scope for a header-staleness review. Header updated to record this finding rather than silently bumping the date (see file). Two viable paths for a future session: (a) backfill the missing entries from `DECISION_LOG.md`'s existing record, or (b) formally decide CHANGELOG.md is superseded by DECISION_LOG.md and either retire it or repurpose it as a lighter-weight index. Recommend registering a T-NNN to make that decision explicitly rather than letting the file drift further. |
| Status | OPEN. |

</details>

---

### GG-134 — `mc_empirical_bootstrap.py`'s forward-risk projection has four unmodeled scope gaps not disclosed as limitations at commit time

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Four MC scope gaps not re-checked. **Next:** Add limitations section to the MC report.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-134 |
| Arm | Core |
| Category | Incremental architecture — new forward-risk MC engine (`scripts/mc_empirical_bootstrap.py`, committed this session, `05_RESEARCH_EXPERIMENTS/MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`) models only book-level aggregates, not the band/pool structure CLAUDE.md's dual-ledger and multi-band architecture actually has. |
| What was missed | Four coverage gaps in the engine's forward projection, none disclosed as a stated limitation in the report before this registration: (a) **kill switches are book-level only** — the 20% peak-drawdown and 15% daily breaker are applied to each book's aggregate bankroll, with no per-band budget or per-band kill modeled, even though CLAUDE.md Hard Rule 9 and `execution_bands.py` describe per-bucket/per-band routing and (per this project's stated design) band-level kill switches are meant to operate independently of the system-level one; (b) **MAIN pools T1/T2/T3 into one undifferentiated cohort** — the engine's `cohort_fracs()` filters by `logic_epoch` only, not by band, so T1's pregame-calibration edge and T2/T3's distinct decision trees are blended into a single mean/variance pair, which could mask a profitable band being dragged down by a losing one or vice versa; (c) **blocked sub-bands and the dark NBA book are entirely absent** — T4M-ARITH and T4M-FLOW (built but blocked) and NBA (DARK/FROZEN per operator directive) have no representation in the simulation, so the engine's book-level "MAIN" and "T4" figures describe only the currently-active pools, not the system's full pool inventory; (d) the **survivable-edge frontier** (minimum per-bet edge needed to hold 1yr P(kill) below a target, given real variance/cadence/Kelly fraction) that would turn the report's ruin-geometry finding into an actionable sizing/ADR change has not been built into this engine — this is explicitly Window B2's scope (`ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md` §Window B, claimed `SESSION_CLAIMS.md` 2026-07-23T23:39:20Z), not re-registered here as a new gap. |
| When it should have been caught | At commit review, before the engine's report language ("Books modeled independently (dual-ledger)") could be read as a complete description of the system's pool structure by a future session trusting the report at face value. |
| Phases it survived | N/A — caught same-session, at first commit, before any downstream session relied on the report's book-level figures as if they covered per-band or full-pool-inventory risk. |
| Why it survived | The report is honest and clearly scoped to MAIN/T4 as the two *active* books, and its own Assumptions section discloses the CLT-in-log-space approximation — but it does not separately flag that "book" here means "everything active pooled," not "every band separately," nor that blocked/dark pools are out of scope entirely. A reader could reasonably infer full coverage from "dual-ledger" framing alone. |
| Impact | LOW-MEDIUM — no capital/gate impact today (G6 gate not cleared, no live capital). Risk is forward-looking: if this engine becomes "the standard forward-risk gate" (per the iteration plan's D2 item) without these scope boundaries being explicit, a future sizing/ADR decision could be made on book-level aggregate risk while a specific band's or blocked sub-band's true risk profile diverges materially from its book's pooled average. |
| Discovery | 2026-07-23, this session, during pre-commit review of `mc_empirical_bootstrap.py` ("confirm it's sound, not just present" per operator instruction). |
| Resolution | Not fixed this pass — registered as known scope, not remediated. (a)/(b)/(c) are candidates for a future extension of this engine (per-band cohort splitting, per-band kill modeling, explicit pool-inventory table) if/when it is formally adopted as the standard gate (Window D2). (d) is explicitly out of this gap's scope — already claimed and in progress under Window B2; do not duplicate. |
| Status | OPEN. |

</details>

---

### GG-136 — No standing archival cadence exists for `04_EXECUTION/TODO_NEXT.md`'s own `## T-NNN` task sections (same class as GG-127)

**Status:** IN PROGRESS · **Severity:** UNSPECIFIED

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-136 |
| Arm | Core |
| Category | Documentation-hygiene — same class as GG-127 (a file whose own stated purpose implies bounded, current content had been allowed to accumulate unbounded historical content, with no automated check or enforced cadence catching the drift). |
| What was missed | `TODO_NEXT.md`'s own header states: "**Purpose:** The immediate action list for the current work session. Only contains tasks executable in the next 1–3 sessions. Longer-horizon tasks belong in PLAN.md." Despite this, by 2026-07-23 the file had grown to 2,422 lines carrying 40 `## T-NNN` sections, 34 of which were marked ✅ DONE/RESOLVED/COMPLETE — some dating back to 2026-07-10/11 (T-325 through T-332), i.e. roughly two weeks of completed-task history sitting in a file whose own purpose line commits to a 1-3 session horizon. Unlike `MEMORY_BANK.md`'s `## Current State Snapshot` chain (which T-334/ADR-0044 gave a standing consolidation pattern and an automated WARN check, `check_memory_bank_snapshots.sh`), `TODO_NEXT.md`'s `## T-NNN` section list had no equivalent: no script checks its length or DONE-section count, and no prior session had registered a recurring cadence for pruning it — the only precedent was a single passing reference inside T-334's own scope description, never generalized into a repeatable process for this file specifically. |
| When it should have been caught | Any session running the mandatory CLAUDE.md session-start protocol, none of whose Steps 0-4 or Q1-Q6 checks inspect `TODO_NEXT.md`'s own line count, section count, or DONE-section ratio against its stated purpose. |
| Phases it survived | At minimum every session from 2026-07-10/11 (oldest surviving DONE section, T-325/T-326/T-327) through 2026-07-23 (this session) — on the order of two weeks and dozens of sessions, spanning Phase 6/7 ACTIVE. |
| Why it survived | No automated freshness/size check exists for this file, analogous to the nav-hub staleness check GG-127 added for `00_ADMIN/README.md` or the chain-length check T-334 added for `MEMORY_BANK.md`. Growth was gradual (one or two new DONE sections per session) and each individual addition looked locally reasonable — the drift was only visible in aggregate, and nothing forced an aggregate view. |
| Impact | LOW-MEDIUM — no capital/gate/trading-logic impact; this is a documentation-scannability issue in a file read at the start of every session. Real cost: a file meant to give a fast "what's actionable right now" view instead required scanning past 34 completed sections (roughly 425 of the file's 2,422 lines) to find the 6 genuinely open items, directly undermining the file's own stated purpose and slowing every session's orientation pass. |
| Discovery | 2026-07-23, this session (T-396, isolated worktree `session/20260723T003916Z-todo-next-archive`), operator-directed: Earl noted the file's line/section count and its own stale purpose line, and pointed to the T-334/`MEMORY_BANK_ARCHIVE.md` lossless-move pattern as an applicable precedent not yet extended to this file. |
| Resolution | Same session: the 34 confirmed DONE/RESOLVED/COMPLETE `## T-NNN` sections (T-325 through T-395, excluding T-333/T-376/T-379/T-384/T-390/T-394 which each retain a genuinely open component or explicit OPEN/PARTIAL/pending status) moved verbatim — programmatically extracted and diff-verified byte-for-byte, not paraphrased — into a new `## TODO_NEXT Task Archive` section in `11_MEMORY_HANDOFF/MEMORY_BANK_ARCHIVE.md`, with a one-line pointer left in `TODO_NEXT.md` in their place. This resolves the specific instance. **No structural/automated cadence was built this session** (unlike GG-127's nav-hub check or T-334's `check_memory_bank_snapshots.sh`) — this gap's root cause (no enforced pruning cadence for this file) remains open pending a future session deciding whether to extend `check_memory_bank_snapshots.sh` (or a new script) to also flag `TODO_NEXT.md` DONE-section accumulation past some threshold. |
| Status | **IN PROGRESS.** The specific instance (34 stale DONE sections) is RESOLVED as of 2026-07-23. The structural gap — no automated check or enforced cadence exists to catch this file recurring to the same state — is NOT resolved. A future session should decide whether to extend `check_memory_bank_snapshots.sh`'s pattern to this file (e.g. WARN if `## T-NNN` sections marked DONE/RESOLVED/COMPLETE exceed some count or age threshold) or accept periodic manual sweeps as sufficient. |
| Numbering note | Originally registered in-session (isolated worktree `session/20260723T003916Z-todo-next-archive`) as GG-133. On first merge attempt against `main`, GG-133 was found already taken by an independent, concurrently-merged session's CHANGELOG-staleness finding, and GG-134 also already taken (`mc_empirical_bootstrap.py` scope-gaps finding) — renumbered to GG-135. Before that merge could land, `origin/main` advanced again with a second independent concurrent registration (Window B1/B2's MAIN-book ruin-geometry finding, directly below) that also collided on GG-135 and landed first — renumbered a second time, to the true next-free ID verified fresh against `origin/main` post-second-merge, **GG-136**. |

</details>

---

### GG-137 — A1's holdout-Brier-optimal K=400 shrinkage candidate gives only ~7% weight to actual player data; may trade calibration for discrimination

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Depends on GG-105 outcome; not re-checked. **Next:** Revisit after GG-105 retest.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-137 (renumbered a second time at Window D's merge, 2026-07-24 — the ID this entry landed on via PR #53, GG-136, was itself already taken on `main` by an unrelated, earlier-registered entry: T-396's `TODO_NEXT.md` archival-cadence gap, above at GG-136, which predates this entry in `main`'s history but whose presence was evidently missed when this entry's own "next-free" check ran at its original merge time. Window D caught the resulting duplicate-GG-136 state on `main` while resolving its own, separate GG-136 collision against this same entry, and renumbered this entry to the true next-free ID, GG-137, verified against the full merged range GG-124–GG-136.) |
| Arm | Window A |
| Category | Modeling — metric/objective mismatch risk, discovered during the CLAUDE.md session-start protocol's Q6 adversarial pass, run retroactively after A1's implementation work. |
| What was missed | A1 (`ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md`) tuned a new candidate shrinkage constant, `ba_l10_shrunk_a1_candidate`, by grid-searching K to minimize per-at-bat weighted Brier score on a TEST holdout, per APR-0025's formula `(h_sum + K*PRIOR)/(ab_sum + K)`. The selected value, K=400, was accepted and shipped (flagged off) without checking what it implies for the feature's cross-sectional discrimination. Direct computation against the same holdout (median rolling L10 `ab_sum` ≈ 33 at-bats) shows K=400 gives the actual player-specific data a median weight of only **7.6%** — 92.4% of the shrunk value is the population prior (`GG105_SHRINKAGE_PRIOR=0.2512`), versus the live ADR-0047 K=40's median weight of **45.2%**. Brier score alone cannot distinguish "well-calibrated and discriminating" from "well-calibrated because it predicts near the population mean for almost everyone" — with a ~30-at-bat sample and real per-player batting-average spread this small relative to per-at-bat variance, the latter is Brier-optimal but is close to a degenerate, nearly-constant feature. T1's entire alpha thesis (CLAUDE.md § Alpha taxonomy) is that a model differentiates players by recent form/rolling stats better than the market — a feature that has been shrunk to ~93% prior-weight has very little cross-sectional spread left to differentiate players with, which could reproduce or worsen the same "no demonstrated alpha" finding as GG-037/GG-004, just via a different mechanism (flattened features instead of miscalibration). |
| When it should have been caught | Within A1 itself, before shipping the K=400 finding as the tuning script's `SELECTED K`, by also reporting/checking a discrimination or sharpness metric (e.g., feature variance/IQR post-shrinkage, or holdout AUC/log-loss decomposition into calibration + refinement) alongside Brier. |
| Phases it survived | Not deployed to any live epoch (A1 explicitly flagged off, per task constraint) — so no production impact yet. Survived only within this session's own A1 implementation, until caught retroactively by the Q6 adversarial check the same session should have run before declaring A1 complete. |
| Why it survived | The tuning script (`scripts/tune_a1_shrinkage_k.py`) optimizes a single scalar objective (Brier) chosen to match the downstream consumer's *loss function*, which was the right call for calibration but is silent on discrimination/sharpness — a known general failure mode of pure proper-scoring-rule optimization under high per-sample noise (shrink hard enough and Brier improves right up to the fully-degenerate "always predict the prior" limit). Nothing in A1's task description or APR-0025 asked for a discrimination check, and the session's own adversarial Q1-Q6 pass was itself skipped mid-session (token-constrained close) and only run after the fact. |
| Impact | LOW today (flagged off, not live) but HIGH if A2 or a future ADR promotes K=400 (or anything near the K≈300–750 plateau) into production without first checking whether the resulting feature still discriminates — this is exactly the kind of finding Window D's offline replay harness (A2's blocker) needs to check for, not just re-derive the same Brier-minimizing K. |
| Discovery | 2026-07-23, this session, direct computation: `test['ab_sum']/(test['ab_sum']+K)` on the same TEST holdout used for A1's tuning — median weight 0.0762 at K=400 vs. 0.4521 at K=40. |
| Resolution | Not fixed this pass — A1's scope was landing the flagged candidate + holdout Brier tuning, not building a discrimination metric. Recommend Window D's replay harness score every candidate K on BOTH holdout Brier and a discrimination/sharpness measure (e.g., post-shrinkage feature stdev, or resolved-bet edge-detection rate) before any A2 refit treats a Brier-only optimum as the right K. Flag explicitly to the operator before this candidate is ever considered for promotion. |
| Status | OPEN. |

</details>

---

### GG-140 — GG-105 remediation exhausted the entire class of monotonic-transform recalibration candidates without a structural check ruling that class out first (temperature scaling, LR+Platt refit, isotonic — all tested serially, all failed the same way)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Depends on GG-105 outcome; not re-checked. **Next:** Revisit after GG-105 retest.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-140 |
| Arm | MLB |
| Category | Architectural placeholder — a remediation search space was never bounded by its own mathematical limits before three separate sessions spent real time testing candidates inside it |
| What was missed | GG-105's anti-predictive tercile pattern (T4M-PROJ's computed edge is inversely, monotonically related to realized win rate) has now been attacked with three distinct recalibration techniques across three sessions: global temperature scaling (2026-07-16, NBA-ADR-0027-style, T-378 — made the pattern *worse*, Fisher p 0.0212→0.0000), LR+Platt refit on A1's shrunk `ba_l10` feature alone (A2, 2026-07-24), and isotonic recalibration on the same feature (A3, 2026-07-24, the sigmoid-superseding contingency). All three failed the identical criterion — edge-tercile monotonicity stays inverted, same qualitative shape as the pre-fix baseline — while all three *passed* calibration-slope-CI and Brier/ECE. What was never checked before spending three sessions' worth of work: temperature scaling, Platt scaling, and isotonic regression are all **strictly monotonic transforms of the model's output score**. A monotonic transform cannot change which bets rank above which other bets — it can only rescale/reshape the probability magnitude assigned to an already-fixed rank ordering. If the *ranking itself* is wrong (higher raw edge score does not correspond to higher realized win rate), no monotonic post-hoc transform can fix it by construction — a proof-level fact, not an empirical one, and it was available before any of the three sessions ran their experiments. |
| When it should have been caught | Before A2/A3 were scoped (2026-07-24), and arguably before the 2026-07-16 temperature-scaling test — GG-105's own repeated finding that calibration metrics (slope/Brier/ECE) improve or stay fine while tercile monotonicity stays broken is itself the empirical signature of a rank-ordering defect, not a calibration-magnitude defect, and should have prompted checking the transform class's mathematical ceiling before spending a second (temperature) let alone third/fourth (Platt, isotonic) session testing more instances of the same disqualified class. |
| Phases it survived | Three full remediation attempts (2026-07-16 T-378 temperature scaling; 2026-07-24 A2 LR+Platt refit; 2026-07-24 A3 isotonic contingency), each independently scoped, built, run, and scored via the D1 what-if harness — each rediscovering the same negative result rather than the search space being bounded up front. GG-105's own entry narrates the "dissociation between aggregate model_p calibration and edge-tercile rank-ordering" after the *first* (temperature) failure but did not generalize that dissociation into "therefore no monotonic transform can close this gap" until this entry. |
| Why it survived | GG-105's remediation history treated each new candidate (temperature → Platt → isotonic) as a distinct untested hypothesis worth a dedicated build-and-score cycle, rather than first asking whether the candidate belongs to a class that is mathematically incapable of fixing a rank-order defect. No step in the A2/A3 scoping (see DECISION_LOG.md 2026-07-24 "Window A / A2 scoping" row) asked this question before committing to the build. |
| Impact | MEDIUM — no capital or data-correctness impact (all three tests were correctly gated by the D1 harness/calibration-gate protocol and none were promoted to live), but real session-time cost across three separate remediation cycles chasing candidates from a class that was disqualifiable by inspection. Forward-looking impact is the more important one: **this closes off recalibration (in the Platt/isotonic/temperature-scaling sense) entirely as a remediation path for GG-105.** The only remaining levers are (a) new features that change the underlying rank ordering (e.g. GG-105's own still-untested H2, blending pregame `p_t1` into the shrinkage prior per APR-0030 DRAFT — this is a *feature* change, not a recalibration transform, so it is not excluded by this finding) or (b) a non-monotonic model-class change (e.g. a tree-based model, or any architecture whose score is not a monotonic function of the current LR+Platt pipeline's linear predictor). |
| Discovery | 2026-07-28, this session (C1/GG-004 stabilization-freeze worktree) — while checking `ITERATION_MC_PROGRESS.md`'s precondition for the C1 freeze (`A2 DONE ... gate=FAIL`), the pattern across A2/A3/2026-07-16-temperature-scaling (three monotonic transforms, three identical-shape failures) was recognized as a structural, provable fact rather than three independent empirical negatives. |
| Resolution | Not a code fix — a search-space finding. GG-105's own entry (`GOVERNANCE_GAP_LOG.md`, this file) is escalated from "recalibrate the existing model" to "feature/model-class rework"; see that entry's addendum below. No further monotonic-transform candidate should be scoped against GG-105 without first checking whether it changes rank ordering, not just magnitude. |
| Status | **OPEN — this is a standing constraint on GG-105's remaining candidate space, not a task with its own close condition.** Closes structurally once GG-105 itself resolves via a rank-order-changing remediation (H2 feature blend, or a model-class change), or is formally reclassified as unresolvable. |

</details>

---

### GG-150 — Cross-book (T1 vs T4) opposite-direction conflicts are alarmed, not blocked; a blocking control is an unstaffed gap

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Alarm-only by design; no blocking control built. **Next:** Operator decision on a blocking control.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-150 |
| Arm | MLB (T1 + T4M-PROJ, cross-book) |
| Category | Architectural placeholder — a deliberate scope boundary, not a defect, registered so it is not silently forgotten. |
| What was missed | GG-149's audit found 35 tickers carrying opposite directions across the T1 and T4 books (T1 holding YES while T4 holds NO on the same ticker, or vice versa). ADR-0023 pool-isolates T1 and T4 as separate processes with separate portfolio files and no shared coordination mechanism, so this session implemented a read-only, best-effort, alarm-only check (`t4_t1_cross_book_direction_conflict`, WARNING severity) rather than a blocking one — building real cross-process blocking would require a coordination mechanism (lock, shared ledger, or merged execution path) that does not exist today and was explicitly out of scope for this task. |
| When it should have been caught | N/A — this is a forward-registered scope boundary from the same session that fixed GG-149, not a missed catch. |
| Phases it survived | N/A. |
| Why it survived | N/A — deliberately deferred, not a governance failure. |
| Impact | LOW today (alarm-only is sufficient to make the condition visible; T1 and T4 are separate bankroll pools per ADR-0023/GG-070, so a cross-book wash is not a same-account wash trade in the same regulatory sense as GG-149's intra-book case) but will need revisiting if T1 and T4 are ever unified into one execution path or one venue account. |
| Discovery | 2026-07-31, session `session/20260731T020022Z-t4-reactivate`, alongside GG-149. |
| Resolution | Unstaffed. Requires a decision on whether/how to build real cross-process coordination (new ADR, since it touches ADR-0023's pool-isolation design) before any blocking behavior is implemented. |
| Status | OPEN — unstaffed, no T-NNN assigned. |

</details>

---

### GG-151 — `merge=union` does not guarantee dedup: identical content reaching both merge sides via different commit paths can be duplicated, not deduplicated

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** merge=union still applies to SESSION_CLAIMS.md (.gitattributes); dedup guarantee not added. **Next:** Add a post-merge duplicate-row check.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-151 |
| Category | Systemic blind spot — a documented safety mechanism (GG-082/GG-101/GG-103's `merge=union` protection for append-only logs) has a failure mode CLAUDE.md never states. |
| What was missed | While completing the merge of PR #62 (`session/20260731T020022Z-t4-reactivate` into `main`), two files configured with `merge=union` in `.gitattributes` — `04_EXECUTION/SESSION_CLAIMS.md` and `04_EXECUTION/ITERATION_MC_PROGRESS.md` — both ended up with a literal duplicate row (the R3/T4-reactivation closure entry) after the merge, rather than the clean union-append the driver is documented to guarantee. Root cause: the same real event (R3/T4M-PROJ reactivation) had been logged via two different commit-history paths that both survived into the merge (one from an earlier rebase state, one from the branch's current tip); `merge=union` unions line-ranges, and when both ranges independently contain the byte-identical text, it inserts both rather than recognizing them as the same content. |
| When it should have been caught | At GG-103 (2026-07-15), when `merge=union` was adopted for these files specifically to solve concurrent-append collisions — that fix assumed union-of-appends is always safe; it was never tested against the case of the *same* append surviving on both sides via divergent history. |
| Phases it survived | N/A — first occurrence found the same session it was introduced into the merge (2026-07-31). |
| Why it survived | `merge=union` is a line-level text union, not a semantic dedup — nothing in the mechanism or in CLAUDE.md's description of it checks for content-identity across the unioned ranges. |
| Impact | LOW this instance (caught by manual repo-wide duplicate grep during merge verification, fixed via 2 targeted Edits, no data lost — the duplicate was a closure-row narrative, not a numeric ledger figure). MEDIUM in general: any append-only log relying on `merge=union` as its collision-safety mechanism (SESSION_CLAIMS.md, .last_session_checkpoint, ITERATION_MC_PROGRESS.md) can silently accumulate duplicate rows on any merge where the same event was logged via two commit paths — a session that doesn't specifically grep for duplicates post-merge would ship them. |
| Discovery | 2026-07-31, session `session/20260731T020022Z-t4-reactivate`'s merge-completion pass, via targeted `grep -c`/`grep -n` duplicate-content checks run as part of merge verification (not part of any existing automated check). |
| Resolution | RESOLVED for this instance — both duplicate rows manually removed, re-verified via repo-wide grep post-fix. **Not resolved as a mechanism** — no automated post-merge duplicate-row check exists yet for `merge=union`-configured files. Candidate fix: add a lightweight check (e.g. to `session_guard.sh` or a merge-completion step) that greps each `merge=union` file for exact-duplicate paragraphs/rows after any merge into `main`. Unstaffed — no T-NNN assigned. |
| Status | OPEN — mechanism-level gap unstaffed; this instance's data-level defect is resolved. |

</details>

---

### GG-153 — T1's clean cohort is permanently frozen at clean_n=0 by the interaction of ADR-0048's zeroing and the epoch-10 ALL_BANDS reset; cannot self-heal under the current regime

**Status:** OPEN · **Severity:** MEDIUM

**W89.6 2026-10-26 (operator-approved disposition):** ADR-0057 was already ACCEPTED 2026-08-26 (T-499); only its section 4 (T1 fate A/B/C) remains deferred. Not retired: the operator reopened T1 on the game-market axis 2026-08-25 (ADR-0058), so retiring T1 (option A) would contradict that. Practical state is option C (dark, excluded from G6 count). Decision still the operator's.

**Current state (2026-10-08, W59.1):** T1 and T4M-PROJ kelly_fraction still 0.0 (execution_bands.py lines 156/167); VPS verdict shows T1 clean_n=0. Operator-blocked. **Next:** Operator decision on edge-conditional reactivation (ADR-0048 table).
**Blocked-On-Operator:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-153 |
| Category | Architectural placeholder — a governance-grade sample-adequacy mechanism (`run_power_calc.py`'s `clean_n`/`n*`/`cadence_span_days` gate, APR-0024) assumes clean data keeps accruing; nothing in the design accounts for a band whose sizing has been set to zero. |
| What was missed | ADR-0048 (2026-07-29, R1) set `T1_MULTI_DAY.kelly_fraction = 0.0`, so every T1 evaluation that clears CHECK 3/4b is rejected downstream with `kelly_size_zero` — no new resolved bets. Separately, epoch 10 (GG-142 gate fix, `bands_affected={ALL_BANDS}`, landed 2026-07-29/30 per `logic_epoch.py`) reset every band's `clean_epoch_floor`, including T1's (previously floor=5 since GG-119/ADR-0045, 2026-07-15). Because T1 cannot place any new bet post-zeroing, `clean_n` at floor=10 is stuck at 0 and structurally cannot increase — verified live via this session's `governance_scan.sh` SAMPLE ADEQUACY pull (2026-07-31): `[T1] clean_n=0 insufficient_data`. This corrects a framing that circulated this session ("T1's clean cadence span is frozen at 13 days... adjudicate against the frozen n=202 cohort") — that figure was a transient reading taken between epoch-9's zeroing and epoch-10's reset, and no longer describes the live state. The verified current state is worse than "13 days short of mature": it is `clean_n=0`, permanently, not slowly accruing. |
| When it should have been caught | At R1 (ADR-0048, 2026-07-29) or R2 (epoch-10/GG-142, 2026-07-29/30) — both landed in the same 24-48h window and neither checked whether the combination would leave any zeroed band's `clean_n` permanently unrecoverable. |
| Phases it survived | Introduced 2026-07-29/30 (R1 + R2 combined effect); not surfaced until this session's Q1-Q6 pass, 2026-07-31. |
| Why it survived | `run_power_calc.py`/`governance_scan.sh` correctly report `clean_n=0 insufficient_data`, but that output is visually identical whether a band is slowly accruing toward `n*` or structurally blocked from ever accruing again — nothing distinguishes "still counting" from "can never count." |
| Impact | MEDIUM. T1 (MAIN's primary pregame-calibration band, the T1 alpha thesis CLAUDE.md's alpha taxonomy treats as independent from T4) can never reach APR-0024's `n*`/`MATURE_CADENCE_SPAN_DAYS` governance-grade thresholds while ADR-0048 stands — meaning ADR-0048's own implicit exit path for T1 (clear power-calc, as ADR-0050 did for T4M-PROJ) is circular: clearing power-calc requires new clean bets, which requires nonzero Kelly, which is exactly what ADR-0048 zeroed. No capital-at-risk impact today (T1 already at kelly=0), but the band cannot earn its way back to reactivation under the current regime, and nothing had flagged that circularity until now. |
| Discovery | 2026-07-31, Phase 0-B session, Q1-Q6 pass, S.4 verification — task brief cited a "13 days / n=202" figure; a live governance-scan pull during this session's adversarial review found `clean_n=0` instead, prompting the trace through `logic_epoch.py`/`execution_bands.py`/DECISION_LOG that produced this entry. |
| Resolution | Not yet implemented — needs an explicit operator decision, not a wait. Candidate options: (a) adjudicate against the last clean cohort read before the epoch-10 reset, if recoverable, rather than waiting on a clock that cannot advance; (b) extend ADR-0050's fixed-stake bypass mechanism (`fixed_stake_usd`) to T1 as well, sized depth-/ruin-risk-safe, to resume clean accrual without reversing ADR-0048's ruin-risk zeroing — same shape as the live T4M-PROJ precedent; (c) explicitly document T1 as permanently unmeasurable under the current regime rather than leaving it as an open TODO implying eventual self-resolution. Unstaffed, no T-NNN assigned. |
| Status | OPEN — unstaffed, no T-NNN assigned. Not a G6 blocker today (T1 already zeroed, no capital at risk); blocks any future T1 reactivation decision. |

</details>

---

### GG-154 — Session-start protocol cannot verify CLAUDE.md's architectural claims against live source, and Step 4 silently no-ops without SSH access

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Session-start greps remain hardcoded snapshots; not re-verified. **Next:** Replace hardcoded greps with checked-in assertions.
**Actively-Broken:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-154 |
| Category | Systemic blind spot — third instance of the same failure class: GG-144's dead Q4 grep (`def approve`/`def execute`, matched nothing, ever), the `market_mapper` registry CLAUDE.md once described that was never built, and now this. |
| What was missed | Two related gaps. (1) The mandatory session-start protocol's Step 1/2/3/Q1/Q4/Q5 greps are hardcoded snapshots of specific line numbers, function names, and file paths; nothing automatically re-verifies they still return non-trivial matches against current source, so drift is silent until a session happens to notice (GG-144's precedent). (2) Step 4 (VPS operational health check) requires live SSH access to `prediction-market-vps` and has no documented fallback or explicit skip-acknowledgment when SSH is unavailable (sandboxed/offline session) — a session lacking SSH produces zero operational-health signal, with no visible marker distinguishing "Step 4 ran clean" from "Step 4 never ran." |
| When it should have been caught | At each protocol step's original authorship, or at GG-144's 2026-07-29 remediation, which fixed the specific dead greps found at the time but added no structural check against the next one. |
| Phases it survived | Present since the session-start protocol's original authorship; GG-144 fixed one instance without addressing the underlying class. |
| Why it survived | CLAUDE.md's protocol is documentation, not code — nothing enforces its embedded commands stay live against a moving source tree, and nothing flags a silently-skipped step as distinct from a step that ran and passed. |
| Impact | MEDIUM. Every future protocol/source drift (a renamed function, a moved file, a config that no longer matches a hardcoded assumption) depends on human/model attention during a live session to catch, same as GG-144, rather than structural enforcement; any session without SSH access produces a transcript that reads as complete while missing a mandated check, with no visible flag. |
| Discovery | 2026-07-31, Phase 0-B session, mandatory Q1-Q6 pass — named directly in this session's task brief as S.5/S.6. |
| Resolution | Not yet implemented. Candidate shape: (a) a lightweight check (script or CI step) that runs each of CLAUDE.md's Step 1-3/Q1/Q4/Q5 grep commands against current source and fails/warns on zero matches, catching the GG-144 class structurally rather than per-instance; (b) Step 4 should explicitly print "SSH UNAVAILABLE — Step 4 SKIPPED, no VPS health signal this session" on failure rather than producing silent empty output, so the gap is visible in every transcript. Unstaffed, no T-NNN assigned. |
| Status | OPEN — unstaffed, no T-NNN assigned. |

</details>

---

### GG-156 — No forward price archive existed for any MLB market family before 2026-08-01; Phase 2's market-comparison gate had no input source and the same absence limits GG-142 counterfactual analysis

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Triage lead cited only 'verified in prior pass' with no checkable evidence; not closed on say-so. **Next:** Confirm exp_output/PRICE_ARCHIVE has continuous forward files per MLB family, then close.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-156 |
| Category | Missing data infrastructure — a downstream gate (`MARKET_EXPANSION_ACTION_PLAN.md` 2.7/2.8) depended on an input source that was never built, and the gap was invisible because nothing failed loudly — the gate simply could not have been attempted. |
| What was missed | As of 2026-08-01, no component in this system persisted forward Kalshi price history for any market family. `t4_price_cache.py` is in-memory only (dies with the process); `fetch_kalshi_prices.py` is an scp-pull utility, not an archiver. The only price history anywhere was `mid_price_at_entry`/`vig_at_entry` embedded in ledger rows — prices at the instant the bot bet — which is selection-biased to bets actually placed on a single family (`KXMLBHIT`). Phase 2's action-plan gate (2.7/2.8, "score the team-level model offline against historical Kalshi prices") requires exactly the data that never existed for `KXMLBGAME`/`KXMLBSPREAD`/`KXMLBTOTAL`, and — separately — the same selection-bias absence means GG-142's gate-valid-filter result cannot be evaluated against bets the filter would have rejected but the bot did not place; there is no price record for markets not bet on. |
| When it should have been caught | When Phase 2's action-plan gate (2.7/2.8) was first written — the gate names "historical Kalshi prices" as an input without any script or process producing that input existing at the time, an unstated dependency that should have been flagged when the gate was drafted, not discovered when someone went to run it. |
| Phases it survived | Present since Phase 2's gate language was authored; survived Phase 0-A/0-B/0-C session work (2026-07-30 through 2026-08-01) because none of that work touched price persistence — it was market-listing and depth-orderbook sampling, a different data need. |
| Why it survived | No component in C1-C8 is responsible for price archival as a distinct concern — C6 (Audit Logger) logs bot actions/decisions, not passive market state for markets never acted on. The gap sat between explicit ownership boundaries. |
| Impact | MEDIUM-HIGH and partially irreversible. MLB's regular season ends in early October (~9 weeks from 2026-08-01); any day this does not run is a day of forward price data permanently lost for Phase 2's gate and for GG-142 counterfactual work — it cannot be backfilled after the fact for a market that has already resolved/closed. Not a G6 blocker (G6 does not depend on Phase 2), but every day of delay narrows the eventual n for both downstream uses. |
| Discovery | 2026-08-01, Phase 0-E session (T-410), while investigating what Phase 2's action-plan gate would actually run against. |
| Resolution | `scripts/archive_market_prices.py` deployed this session — read-only, append-only, one JSONL/UTC day, capturing top-of-book snapshots (`yes_bid`/`yes_ask`/`no_bid`/`no_ask`/`last_price`/volume/open_interest/liquidity + derived `yes_mid`/`half_spread`) for all 10 MLB families (`KXMLBGAME`, `KXMLBSPREAD`, `KXMLBTOTAL`, `KXMLBTEAMTOTAL`, `KXMLBF3`, `KXMLBF5`, `KXMLBF7`, `KXMLBF5SPREAD`, `KXMLBF5TOTAL`, `KXMLBHIT` as control). Cron installed on the VPS (`*/20 22-23,0-5 * * *`, matching T4M-PROJ's live window) via `deploy/cron.conf` + live crontab, first scheduled fire confirmed. Note: the first manual verification run (2026-08-01T22:55Z) shipped with a field-name bug (`SNAPSHOT_FIELDS` used plain names; the live `/markets` response uses `*_dollars`/`*_fp` keys) that silently dropped every quote field — caught by inspecting `yes_mid` population (0/2162) before trusting the run, fixed same-session (commit `6b687bf`), re-verified 100% `yes_mid` population with non-degenerate values across all 2170 rows on the corrected run. The broken first-run file was preserved as `prices_2026-08-01.jsonl.BROKEN_FIRSTRUN` rather than deleted. This does not retroactively resolve the pre-2026-08-01 data gap — history before this date remains permanently unrecoverable for all families except the selection-biased `KXMLBHIT` ledger rows. |
| Status | OPEN — archiver live and producing correct data going forward; the historical gap for dates before 2026-08-01 is permanently unresolvable and is the residual open concern this entry tracks. No T-NNN beyond T-410 (this session). |

</details>

---

### GG-157 — `paper_trader.py` has zero orderbook/depth/fill validation; every paper fill (including the live epoch-12 flat-$1 cohort) is assumed at mid, and GG-155/T-411 shows that assumption sits against a quantity that swings 10-100x intraday

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** paper_trader.py still has no depth/fill validation (1 incidental keyword hit, no orderbook check). **Next:** Add depth-aware fill check or document mid-fill as an assumption in results.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-157 |
| Category | Unvalidated execution assumption — the fill model underlying every paper position was never checked against the orderbook data it is meant to represent. |
| What was missed | `grep -n "orderbook\|depth\|liquidity\|available_size" src/prediction_market_bot/c5_execution/paper_trader.py` returns zero matches (confirmed 2026-08-04, T-412). `paper_trader.py` fills every simulated position at the quoted mid price with no reference to top-of-book size, depth within any cent band, or whether the intended stake could actually clear the book at that price. This was a defensible simplifying assumption when depth was believed to be a stable $500-$2,000/market figure (the since-corrected GG-155 claim) — it stops being defensible now that T-411's direct time-series measurement shows the same market's depth swinging 14x in 14 minutes on a single series and 67x between two consecutive `TEAM_TOTAL` reads. A fill model with no depth awareness cannot distinguish a moment when the book could absorb the position from a moment when it could not, and every paper P&L figure this system has produced inherits that blind spot. |
| When it should have been caught | When `paper_trader.py`'s fill logic was first written, execution-quality validation against the real book should have been an explicit design question, not an implicit "mid is close enough" assumption. It surfaced now because GG-155/T-411 (Phase 0-H) is the first work in this project to treat depth as a measured, time-varying quantity rather than a static architectural fact — the gap in `paper_trader.py` was invisible as long as depth itself was treated as a documentable constant. |
| Phases it survived | Present since `paper_trader.py`'s fill logic was authored, predating this session; survived every prior gate review (G0-G5) and the ongoing G6 accumulation (2,759 resolved paper positions as of this session, including the live epoch-12 flat-$1 cohort) without being flagged, since no prior session had a live depth time series to check the fill assumption against. |
| Why it survived | No component in C1-C8 validates a simulated fill against the real orderbook at execution time; C5 (Execution Engine)'s paper path was built to prove the forecasting/sizing pipeline, not to model market microstructure, and that scope boundary was never revisited once T4-band live trading (with its 45-90s in-play evaluation cadence) made fill-at-a-thin-and-volatile-book a live concern rather than a theoretical one. |
| Impact | HIGH as a G6 precondition, not a current blocker (no live capital is at risk pre-G6). Every one of the 2,759 resolved paper positions — including the epoch-12 flat-$1 live cohort the G6 gate is currently being evaluated against — assumes a fill that was never checked against available book size. If real depth at the moments those bets were placed was materially below what a mid-price fill assumes (T-411's 14x/67x swings make this plausible for at least some fraction of them), realized paper P&L is systematically optimistic relative to what live execution would have produced, and the G6 "30 resolved paper bets with positive P&L" gate could be evaluated against a fill model that does not hold up against the real venue. |
| Discovery | 2026-08-04, Phase 0-H session (T-412), while scoping Task 5 of the session's work order — a direct grep confirming the operator's stated concern before registering it, per this project's verify-before-acting standard. |
| Resolution | Registration only, per explicit session scope — `paper_trader.py` was not modified this session. Registered as a **G6 precondition**: no live-capital authorization should proceed while the fill model remains unvalidated against production orderbook depth, regardless of how many resolved paper bets or how positive the recorded P&L. Recommended next step (unstaffed, no T-NNN assigned beyond this registration): once `exp_output/PRICE_ARCHIVE/depth_*.jsonl` has accumulated enough observations (Task 2, this session — targeting 200+/family/week), cross-reference resolved paper-bet timestamps against the nearest depth sample for the same market and quantify how often the assumed mid-price fill would have exceeded available within-5c depth. |
| **2026-08-06 update (T-428)** | Ran the cross-reference the "Recommended next step" above called for. **Result: zero usable overlap.** Epoch-12 (the live flat-$1 T4M-PROJ cohort) runs 2026-07-31T19:38Z–2026-08-04T03:28Z; depth capture started 2026-08-04T00:46:22Z. Only 14/187 epoch-12 positions (10 unique tickers) were entered after capture began; exact-ticker matches against all depth samples captured to date (3 days, 69 cron fires, 247 unique tickers) = **0**. Root cause: the archiver samples 2 tickers/family/run against a live universe of ~425 concurrent `KXMLBHIT` tickers in a single hour — well under 3% coverage per pass — so incidental overlap with any specific bet ticker is near-nil by design, not bad luck. Separately, the archiver's ~20-min cadence is 10-20x coarser than the window (14 min) in which T-411 already measured depth swinging 10-100x, so even a ticker-match would not reliably represent book state at entry. **Conclusion carried forward to Task 3 of the same session:** closing GG-157 structurally requires depth captured by the bot itself at decision time (ticker-targeted, within its own 45-90s T4 cadence) — a denser/full-universe cron archiver helps but cannot substitute for co-located, decision-time capture. This is now a stated **Phase 3/4 design requirement** (add an orderbook read to `run_t4_mlb_live.py`'s live evaluation path, logged per position), not a Phase 0/1 measurement task. See `05_RESEARCH_EXPERIMENTS/T428_GG157_FILL_FEASIBILITY_2026-08-06.md` for full detail. No `src/` change this session; scope fence held. |
| **2026-08-26 update (T-488)** | With 23 days of depth accumulation since the 2026-08-06 exact-ticker attempt (which found 0 usable overlap), re-ran the cross-reference as a **family-level, nearest-in-time join** instead of exact-ticker — deliberately weaker than the Phase 3/4 decision-time capture this gap already calls for, but the first version of this measurement to produce a nonzero result. Props (PLAYER_PROP/KXMLBHIT): 605/765 epoch-12 T4M-PROJ traded positions joinable (160 predate 2026-08-04 depth coverage, permanently unvalidatable per GG-156); measured haircut mean $0.0101/median $0.0100 per contract, 0% depth-exhausted. Resolved cohort (n=559): mean P&L/bet $0.2864 → $0.2518 after haircut (−12.1%, still positive — directional edge survives), but n* (APR-0024 methodology, `run_power_calc.z_for`, sample stdev ddof=1) rises 437 → 560 against the same n=559 — **the cohort flips from comfortably clearing its own sample-adequacy target (559 ≥ 437) to falling one bet short of it (559 < 560)** once a measured fill cost replaces the mid-price assumption. Also ran a new, auxiliary synthetic measurement (no real positions exist yet to join) for the T1 game-market reopening (T-493): $1.00 ADR-0050 flat-stake haircut priced against each family's own depth-observation mid — GAME_WINNER (KXMLBGAME) mean $0.0340/median $0.0350; GAME_TOTAL (KXMLBTOTAL) mean $0.0307/p90 $0.0800/max $0.4200; RUN_LINE (KXMLBSPREAD) mean $0.0515/p90 $0.1500/max $0.4050 — 3-5x props' median haircut and up to ~$0.42/contract in the tail, confirming game markets carry materially worse fill geometry than props at the depth level, not just at the point-estimate level already on record in CLAUDE.md. D1 (ADR-0055 epoch-12 ledger repair) confirmed **PROPOSED, not accepted** — all figures above are scoped to the uncorrected ledger. Full detail, method, and caveats: `exp_output/T488_GG157_FILL_HAIRCUT/SUMMARY.md`; script: `scripts/gg157_fill_haircut_analysis.py`; machine-readable: `exp_output/T488_GG157_FILL_HAIRCUT/results.json`. This measurement **narrows** GG-157 (first nonzero result, extends coverage to game markets) but does **not close** it — family-level/nearest-in-time is still explicitly weaker than the ticker-targeted, decision-time capture the 2026-08-06 update already identified as structurally required; that Phase 3/4 build remains unstaffed. GG-208 was reserved for this session and is returned unused — this is a continuation of the existing OPEN gap, not a new distinct defect. No `src/` change this session; scope fence held (`scripts/`, `exp_output/` only). |
| **2026-08-31 update (T-507)** | Named follow-on to the 2026-08-26 (T-488) row above, per ADR-0055's own register entry stating T-488's figures were computed on the *uncorrected* epoch-12 ledger and must be re-run once the repair landed. T-503 executed and durability-verified the repair (Addendum B: 532 closed + 76 rejected epoch-12 rows repaired; ledger invariant violations 630→22; cross-path agreement 52.0%/68.4%→100.0%/100.0%). **Method: T-488's script re-run unmodified against the post-repair ledger** (`scripts/t507_gg157_haircut_rerun.py`, an invocation-only copy of `gg157_fill_haircut_analysis.py` — output path and one status-label string changed, zero logic changes; ran clean, no method substitution needed). Depth archive re-synced from VPS (29 files, 459M, 2026-08-04–2026-08-31) via the same GG-158 rsync mechanism. Props haircut distribution: **unchanged** (n=605 joinable, mean $0.0101/median $0.0100/0% depth-exhausted) — expected, since haircut-per-contract is a function of book depth, not ledger correctness. Game-market synthetic figures (Task 4): **unchanged within measurement noise** (GAME_WINNER/GAME_TOTAL/RUN_LINE means, medians, tails all closely match the 2026-08-26 figures; minor drift only from 6 additional days of archive accumulation) — confirms this portion is correctly unaffected by the ledger repair, as expected by construction (no ledger join). **The resolved-cohort P&L/n* figures move materially.** T-488's exact original cohort (n=559, isolated via each position's `resolved_at` timestamp to reconstruct positions resolved on/before 2026-08-26 — a supplementary diagnostic step, not a redesign of T-488's method) shows: mean P&L/bet BEFORE haircut $0.2864 (OLD, corrupted rows included) → **$0.0712** (NEW, repaired) — a genuine 75.1% drop (~3+ standard errors, not noise); AFTER haircut $0.2518 (OLD) → **$0.0366** (NEW) — an 85.5% drop. Direction stays positive but the margin is now thin. n* (same n=559): BEFORE-haircut n* 437→**4775** (was comfortably met with 122 to spare, now NOT met by a wide margin); AFTER-haircut n* 560→**18058** (OLD was "short by 1 bet," explicitly flagged by T-488 as noise — **NEW is not a 1-bet margin, it is not remotely close, and must not be read the same way**). Running T-488's method exactly as instructed, with no cohort-window restriction (n=605, today's full joinable set — includes 46 positions that organically resolved in the 5 days since T-488's run, mean P&L on those 46 alone = **−$0.1551**, i.e. negative): mean P&L/bet BEFORE haircut $0.0540, AFTER haircut $0.0191 — both still positive, both far thinner than either the OLD or the apples-to-apples-repaired figures. Full detail: `exp_output/T507_GG157_HAIRCUT_RERUN/results.json`; script: `scripts/t507_gg157_haircut_rerun.py`; tree SHA: `24fa323b047cacf099ae06e34a3f0b96e9a97beb` (worktree `session/20260901T002657Z-t507-gg157-haircut-rerun-post-repair`, rebased onto `origin/main` at close-out with `origin/main` confirmed an ancestor of HEAD). **Three required statements: (1) directional edge still survives the haircut — yes, mean P&L/bet stays positive in every cut of this data (apples-to-apples repaired, and full current re-run). (2) Figures that moved by more than their own uncertainty — yes: the apples-to-apples P&L/bet and both n* figures moved far beyond noise (see above); the props haircut distribution and game-market synthetic figures did NOT move materially. (3) Prior conclusion now wrong — T-488's own headline framing ("cohort falls 1 bet short of n*, likely noise, will clear on the next resolved position") is now wrong and must not be repeated: post-repair, the same cohort is short of its own n* by thousands of bets, not one, at current cadence. T-488's directional-edge-survives conclusion is NOT wrong — it still holds, just on a much thinner and now clearly sample-inadequate margin.** GG-157's structural weakness (family-level nearest-in-time join, not ticker-targeted/decision-time) is inherited unchanged from T-488, not fixed here, as instructed. No `src/` change, no `kelly_fraction`/ledger/service touch, no clean-vs-corrupted comparison run, no cell promotion, no gate-status change this session; scope fence held (`scripts/` invocation-only copy, `exp_output/`, `05_RESEARCH_EXPERIMENTS/` — no writes to the latter this session). |
| Status | OPEN — GG-157 now HAS a post-repair measurement (2026-08-31, T-507, above), superseding the 2026-08-26 uncorrected-ledger figures for any G6 sample-adequacy reasoning. What still blocks it: (1) the structural Phase 3/4 decision-time/ticker-targeted capture requirement from the 2026-08-06 update remains unstaffed and unchanged — this re-run measures the same family-level proxy, not the real fix. (2) The G6 sample-adequacy gap widened dramatically post-repair, not narrowed: the apples-to-apples n=559 cohort's post-haircut n* is now 18058 against an actual n=559 (was 560 vs 559, a 1-bet noise-level gap pre-repair) — this is a large, real, not-noise finding that must inform any G6 timeline discussion going forward. Not a current hard blocker on today's paper-trading accumulation continuing, but a hard precondition, now measured and materially worse than previously believed, before G6's "positive P&L" finding can be trusted as a live-capital signal. |

</details>

---

### GG-158 — Price archive had zero off-VPS copies for 3+ sessions despite repeated "verified"/"deployed" reports; same failure class as GG-144's unanchored grep

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Triage lead cited only 'verified in prior pass'; off-VPS copy not independently confirmed this session. **Next:** Verify an off-VPS archive copy job exists and is recent, then close.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-158 |
| Category | Check that reports success without testing the thing it claims to test — same class as GG-144 (unanchored OPEN-gap grep) and the original GG-155 sampler bug. |
| What was missed | `exp_output/PRICE_ARCHIVE/` was empty in the local/git tree while GG-156 (2026-08-01), the T-411 session (2026-08-03), and T-412 (2026-08-04) each reported the archiver "verified"/"deployed to the live VPS"/"confirmed running." Every report was true about VPS-side behavior (confirmed again this session via fresh SSH: `prices_2026-08-01.jsonl` through `prices_2026-08-04.jsonl`, 72,737 lines total, growing) but none of the three checked or established a second copy anywhere off that single VPS disk. Unlike `logs/` (a runtime cache, regenerable), `exp_output/PRICE_ARCHIVE/`'s season-long price/depth series is **not backfillable** once a game date passes — a VPS disk failure between 2026-08-01 and this session would have been a permanent, silent loss of the one artifact this project's entire Phase 0-E/0-G/0-H effort was built to produce. |
| When it should have been caught | The moment any session described the archiver as "verified" or "deployed" — "producing correctly on the VPS" and "backed up off the VPS" are different claims, and the log entries (GG-156, T-411/T-412 SESSION_CLAIMS rows) used language that reads as the latter while only ever having checked the former. |
| Phases it survived | Present since the archiver's original deploy (T-410, 2026-08-01); survived GG-156's own resolution write-up, the T-411 mid-slate depth session, and T-412's Phase 0-H close-out (which explicitly re-confirmed VPS-side growth via fresh SSH but still did not add a sync step) — three consecutive sessions touching this exact file. |
| Why it survived | No component in this project's session-start protocol or governance scan checked for a local/backed-up copy of `exp_output/PRICE_ARCHIVE/` — Step 4's operational health check greps cron logs and systemd state, not artifact redundancy, so an artifact can be "healthy" (cron firing, file growing) and simultaneously have zero backup with nothing in the mandatory scan surfacing that gap. |
| Impact | Was HIGH and time-sensitive (MLB season data, unbackfillable) until this session; now MEDIUM (a local rsync backup exists but is laptop-resident, not itself redundant, and only refreshes when a session runs `governance_scan.sh`). |
| Discovery | 2026-08-04, this session, operator-directed cleanup task explicitly framed against the GG-144 pattern. |
| Resolution | `.claude/hooks/governance_scan.sh` gained an age-gated (900s TTL) `rsync` pull-back of `exp_output/PRICE_ARCHIVE/` from the VPS to the local tree, mirroring the existing `logs/.vps_portfolio_cache_*.json` pattern — fires automatically every session via the existing UserPromptSubmit hook, no new manual step. `.gitignore` gained `exp_output/PRICE_ARCHIVE/` (the directory was previously untracked only by omission, not by rule — a `git add -A` in a shared-tree session could have committed tens of MB/day of price data into repo history). Verified end-to-end this session: local line counts (72,737 price rows + 156 depth rows) match the VPS byte-for-byte post-rsync, confirmed via `wc -l` on both sides. |
| Status | OPEN — the sync mechanism is real and verified, but it is still a single laptop's local disk, refreshed only when a session runs; a true off-VPS *and* off-laptop backup (e.g. cloud/object storage) is not in scope for this MICRO fix and remains a follow-on if the operator wants stronger redundancy than "runs every session." |

</details>

---

### GG-160 — Four `file:line` citations across three Phase 0/1 docs had drifted from source with nothing catching it; no mechanism exists that resolves a doc's code citations against current source

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** No file:line citation checker exists (scripts has none). **Next:** Build a citation resolver or accept as doc risk.

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-160 |
| Category | Doc citing source that moved underneath it — same shape of failure as GG-144 (unanchored regex silently missing entries) and GG-155 (a tool's own output silently wrong): the check that would catch drift was never built, so the drift accumulated invisibly across normal edits to the cited source files. |
| What was missed | A verification pass (2026-08-03) checked ten `file:line` claims across Phase 0/1 docs against source; four were wrong. (1) `MARKET_EXPANSION_ACTION_PLAN.md:125` cited a test-suite baseline (2,757 passed/17 known-failed/28 skipped) that predated GG-146's partial fix — true baseline at time of check was 2,799/8/29. (2) `MARKET_UNIVERSE_SURVEY_SPEC.md:6` cited `kalshi_client.py:115` for `SERIES_MLB_PLAYER_HITS`; the constant is at line 135. (3) `SEGMENTED_POOL_ARCHITECTURE.md:35` cited "53 of 83 files" for player/threshold-shaped tests; current measurement is 55 of 89. (4) `SEGMENTED_POOL_ARCHITECTURE.md:28` said `kalshi_client.py` has "one series constant"; it has two (`SERIES_PLAYER_POINTS` L133, `SERIES_MLB_PLAYER_HITS` L135) and the doc's own Phase 1 registry plan has to absorb both. All four were fixed this session (T-415); see `MARKET_EXPANSION_ACTION_PLAN.md`, `MARKET_UNIVERSE_SURVEY_SPEC.md`, `SEGMENTED_POOL_ARCHITECTURE.md` diffs. |
| When it should have been caught | At whatever commit first moved the cited line, added the second constant, or advanced the baseline — each of these was an ordinary, correct edit to the underlying source; the failure is that nothing re-checked the docs that had cited the old state. |
| Phases it survived | (1) survived from `PROJECT_ASSESSMENT_2026-07-30.md` through at least three corroborating 2026-08-02 sources (`PLAN.md:7`, `TODO_NEXT.md:11`, `SESSION_CLAIMS.md:171`) that all copied the same stale figure forward instead of re-deriving it. (2)-(4) survived since `SEGMENTED_POOL_ARCHITECTURE.md`/`MARKET_UNIVERSE_SURVEY_SPEC.md` were authored (2026-07-30) through every subsequent session that touched `kalshi_client.py` or `tests/`. |
| Why it survived | No component in this project's session-start protocol, governance scan, or CI checks a doc's `file:line`/count citations against current source. The stub scan (Step 2) and gap-log regex (Step 3) both check for a specific known pattern; neither, nor anything else, generically resolves "this doc says X lives at Y" against the repo as it exists today. A citation reads as authoritative prose, not as an assertion with a truth value someone should re-check — so it propagates by copy (as (1) shows, three separate files re-stated the same wrong number rather than re-deriving it). |
| Impact | MEDIUM, compounding. A wrong baseline is the highest-consequence instance of this class: `MARKET_EXPANSION_ACTION_PLAN.md` 1.7 is a **gate** ("full suite green" against the baseline) — comparing a real 2,799/8/29 result against a stale 2,757/17/28 baseline would either flag 35 new passes as suspicious noise or read 9 fewer failures as an improvement, when the actual delta is fully explained by T-412's 7 new tests plus GG-146's independent fix. The other three are lower-consequence (a reader who follows a wrong line number the short distance to the right one loses a few seconds) but are the same defect and the same reason they weren't caught. |
| Discovery | 2026-08-03/2026-08-04, operator-directed verification pass cross-checking ten citations against source, T-415. |
| Resolution | The four citations fixed this session. Per operator instruction this entry proposes, but does not build, a general mechanism: a CI/pre-commit check that extracts `` `path/to/file.py:NNN` `` (and, where present, the named symbol immediately preceding it) from every `0X_*.md` doc, greps the named symbol in the target file, and fails if the symbol's real line doesn't match the cited one — or, for citations with no adjacent symbol name (e.g. the baseline-count case), flags any `file:line` pointing at a line count / test count / other derived-not-fixed value for periodic re-derivation rather than pattern-matching it (those need a re-run, not a grep). Cheapest version: extend `governance_scan.sh` (already the home for the anchored-regex and stub-scan checks) with one more anchored regex pass over `0[0-9]_*/**/*.md`, reusing the exact `select:… / grep -n` idiom already used for Steps 1-3 rather than inventing new tooling. Not built this session — proposal only, per explicit scope fence (no src/ change, doc-fix task). |
| Status | OPEN — unstaffed, no T-NNN beyond T-415's discovery/registration. Re-check trigger: next session that edits `governance_scan.sh`, or the next documentation-remediation pass, whichever comes first. |

</details>

---

### GG-161 — 22 stuck T1/T2 aged_open positions: OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md's "not an API-outage signal" claim is contradicted by direct evidence; retries genuinely happen daily but a cron-window-correlated 406 failure mode was never surfaced

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** VPS paper_mlb_cron.log still shows MLB schedule API 406 Not Acceptable on self-heal queries (2026-10-05 01:31Z, 2026-10-07 06:13Z); failure mode persists, not yet correlated to cron windows. **Next:** Correlate the 406 timestamps against cron windows and add a retry/UA fix to the self-heal query.
**Actively-Broken:** YES

<details>
<summary>Full record ▸</summary>


| Field | Detail |
|---|---|
| Gap ID | GG-161 |
| Category | Confidently wrong causal claim in a prior finding, propagated without SSH-verified re-testing — same shape as GG-159/GG-160: a document asserted a mechanism ("not an API-outage signal"; idempotency blocks retries) that reads as settled but was never tested against the live cron's actual execution window. |
| What was missed | `10_INFRA_OPERATIONS/OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md` § Task 1 states the 22 stuck positions' resolution failure "is not an API-outage signal; it is a standing data-resolution failure," and separately implies `mark_aged_open()`'s idempotent early-return is why `last_updated` never advances. Direct testing this session (T-418) found both claims incomplete. (1) `run_resolve_mlb.py`'s `pending` list (`run_resolve_mlb.py:411-433`) is filtered only by `game_date < today`, not by `aged_open` status — `fetch_actual_hits()` genuinely is re-attempted for every stuck position, every day; the idempotency only suppresses re-tagging on the failure branch, not the retry itself. (2) `resolve_mlb_cron.log` shows a ~68% fetch failure rate (8,345 "giving up" 406s vs. 3,921 successes) concentrated in the cron's 06:30 UTC execution window; the same query (same player_id, date, venv, requests version) returns clean 200s when run interactively outside that window. For Julio Rodríguez specifically, 3 of his 4 stuck dates have valid gameLog data available right now via direct query, yet have never resolved across 5+ weeks of daily cron attempts — evidence the block is window-correlated API unreliability, not absent data, for that subset. |
| When it should have been caught | The moment `OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md`'s Task 1 was written (2026-08-04) — its own causal claims were assertable but not tested against `run_resolve_mlb.py`'s actual source or against a direct off-cron-window API probe; SSH access existed for that session for other tasks but was not used to verify this specific mechanism. |
| Phases it survived | One session (the 2026-08-04 ops-health pass itself) before this session's independent re-derivation, per direct operator instruction to confirm the diagnosis independently rather than accept it as given. |
| Why it survived | No component of the standard session-start protocol probes a specific dead-position resolution failure at this granularity — Step 4's operational health check looks for zero-bet days and staleness halts, not per-position fetch-failure patterns correlated with time-of-day. The ops-health document's claim was plausible on its face (idempotency + "standing failure") and nothing forced a re-test against the live code path or a direct off-window API call. |
| Impact | MEDIUM. Does not change the bottom line that all 22 positions are stuck and $194.24 remains locked — but it changes the fix path. Treating this purely as "permanent data absence needing a terminal state" (the prior framing) would miss that ~3 of the 22 (Julio Rodríguez's non-4th-date positions) may be resolvable today simply by re-running resolution outside the 06:30 UTC window, without needing any terminal-state mechanism at all. Conflating the two mechanisms risks writing off recoverable positions as permanently unresolvable. |
| Discovery | 2026-08-05, T-418 session, direct instruction to independently confirm the ops-health doc's Task 1 diagnosis rather than restate it. Full analysis: `05_RESEARCH_EXPERIMENTS/T416_STUCK_POSITIONS_DIAGNOSIS.md`. |
| Resolution | Registration and causal-correction only, per this session's scope fence (memos only, no `src/` change). `T416_STUCK_POSITIONS_DIAGNOSIS.md` recommends (a) attempting resolution for Julio Rodríguez's 3 recoverable dates outside the cron's execution window before writing them off, and (b) a genuinely terminal state (not indefinite `aged_open` limbo) for positions that fail all three resolution sources past some age ceiling (14-30 days suggested) — neither implemented this session. |
| **T-422 amendment (2026-08-05/06)** | The "cron-window-correlated" framing above (Mechanism 2) is corrected, not just extended: direct VPS-vs-unblocked-network A/B testing found (a) `_is_game_final()`'s `schedule?gamePk=X` query shape 406s deterministically from the VPS's datacenter IP while the equivalent `schedule?sportId=1&date=X` shape returns 200 — this, not general API unreliability, was blocking Julio Rodríguez's 3 recoverable dates; and (b) even after routing around (a), a full 22-position batch run from the VPS degrades the *primary* `gameLog` call itself to 100% 406 partway through — this is GG-084's already-documented escalating Fastly-CDN block reproduced verbatim, not a new mechanism, and it is volume/session-correlated to any batch run from that IP, not literally time-of-day-correlated (it only looked that way because the cron only ever runs once, as one batch, at 06:30 UTC). An out-of-band two-phase repair (fetch from an unblocked network, apply via pure-local `settle_position()` calls on the VPS — `scripts/repair_stuck_mlb_positions.py` and `scripts/apply_resolved_hits.py`) resolved and settled **5 of 22** live (all 4 Julio Rodríguez dates + 1 José Ramírez date), net +$15.84 booked, backed up first to `paper_portfolio_mlb.pre_repair_20260806T000501Z.json`. The remaining **17 are now confirmed** (re-fetched from the unblocked network, ruling out the IP-block as a confound) permanently unresolvable — `reason=no_split_for_date` across MLB-R, MLB-P, and ESPN for all 17. Full writeup: `05_RESEARCH_EXPERIMENTS/T416_STUCK_POSITIONS_DIAGNOSIS.md` § "T-422 update". Terminal-state design for the 17 drafted as ADR-0051 (DRAFT, not accepted) — proposes the state itself, not the code to implement it, per this session's scope fence. Convergent finding with **GG-163** (Window G, T-421, unmerged at time of writing): that entry independently found `run_resolve_mlb.py`'s ESPN-fallback path shares GG-163's UA-keyed 403 block — same root cause class (a hardcoded HTTP client identity/query-shape triggering a CDN-side block), different endpoints, found independently by two concurrent sessions on the same day. |
| Status | OPEN — real fix (query-shape correction in `_is_game_final()`, and a durable answer to GG-084's batch-volume escalation, e.g. rate-limiting or chunking the daily resolution run) still lives in `src/` and is explicitly deferred to Phase 1 per this session's hard scope fence, not staffed to a T-NNN yet. The out-of-band repair is a one-time manual recovery of the 5 recoverable positions, not a standing fix — the next daily 06:30 UTC cron run will hit the same unfixed `_is_game_final()` bug and the same GG-084 batch escalation for any future stuck positions. Re-check trigger unchanged: next session that touches `run_resolve_mlb.py` or the aged_open/terminal-state design (now with ADR-0051 as a concrete starting point for the latter). |

</details>

---

### GG-162 — GG-NNN numbers picked mid-session have no atomic reservation, unlike T-/ADR- ranges claimed at session start; two concurrent sessions independently registered GG-159 on 2026-08-04

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** claim_session.sh reserves T-/GG-/ADR- ranges at claim time and check_id_collision (GG-236) runs on retry, but mid-session GG numbers still have no reservation; W58.2 hit this again (GG-495/497 collision). **Next:** Reserve GG numbers atomically at registration.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-162 |
| Category | Systemic blind spot — concurrent-session ID collision, same failure family as GG-082/GG-101/GG-107/T-247, but in a sub-case that family's fix never covered. |
| What was missed | `scripts/claim_session.sh` + `scripts/lib/check_id_collision.sh` atomically reserve a T-/GG-/ADR- range through `origin` — but only when the range is known and passed at session-claim time (Step 0). A governance gap discovered organically mid-session is not known in advance; the session picks its number by locally grepping the log's current highest `GG-NNN` and incrementing, with no equivalent commit-and-push-through-origin reservation for that pick. Two sessions running concurrently can compute the same "next free" number from their own pre-push local view and both write it. |
| When it should have been caught | During the GG-082/GG-101/GG-107 concurrent-session hardening work (worktree isolation, `claim_session.sh` atomicity, `check_id_collision.sh`) — that effort closed the T-247 double-claim race for *session-start* ID claims but did not extend the same atomicity to GG-numbers assigned during a session, which is a structurally different moment (the ID isn't known until the finding is). |
| Phases it survived | All of GG-082, GG-101, GG-107's remediation, plus every session since (2026-07-07 through 2026-08-04) until it actually collided. |
| Why it survived | No scan step checks for a duplicate `### GG-NNN` header across concurrently-diverged local branches before merge; the collision is only visible once both sessions' commits land on `origin/main` and a human or a `grep -c` on the header pattern notices two entries claiming the same number. |
| Impact | LOW, confirmed self-healing so far. On 2026-08-04, session T-413 (VC6 vig-cascade) and session T-415 (citation repair) independently registered `GG-159` for two unrelated findings. T-415 caught the collision on merge and manually renumbered its own entry to `GG-160` (see `04_EXECUTION/TODO_NEXT.md` T-415 entry: "renumbered from a since-resolved GG-159 collision with the concurrent VC6 session"; `04_EXECUTION/SESSION_CLAIMS.md` T-413/T-415 closure rows). No content was lost or overwritten — the union-merge semantics on `SESSION_CLAIMS.md`/append-only entry structure meant both entries survived and only the *number* needed correcting. Would become MEDIUM+ if a future collision silently overwrote content instead of being caught as a visible duplicate header. |
| Discovery | Operator, scoping T-420 (2026-08-05): "Wave 1 hit two ID collisions in three windows (GG-159 claimed twice; T-415 registered twice)." Investigated as T-420 Task #5. The T-415/T-419 half of that report was separately traced to `check_id_collision.sh` correctly refusing this session's (T-420's) attempt to claim an already-claimed `T-419` at session start — that is the collision guard working as designed, not a defect, and is not part of this gap. Only the GG-159 double-registration is a genuine gap. |
| Resolution | Not built this session — explicit operator instruction: "do not build a locking mechanism speculatively." If pursued, the natural fix mirrors the existing `claim_session.sh` pattern: a small helper that reserves a `GG-NNN` number by committing and pushing a one-line placeholder through `origin` (with the same rebase-and-retry loop `claim_session.sh` already uses) at the moment a gap is discovered, before its full write-up begins — applying the proven T-/ADR- mechanism to the mid-session case it doesn't currently cover. Left for the operator to prioritize; no T-NNN assigned. |
| Status | OPEN — registration only, unstaffed. |

</details>

---

### GG-164 — T4 MLB cycle log's `game_date` field is wrong on 70% of all rows (45,217/64,396): stamped from UTC wall-clock "today" at write time, not the game's actual date; `(player_id, game_date, threshold)` is not a valid join key without correction, and doubleheaders break it further

**Status:** OPEN · **Severity:** MEDIUM · **Assertion:** PENDING(T-432, assertion A) — RESOLVED is not eligible until this lands (ADR-0052); this entry's original "Why it survived" field asserted an unverified negative ("isn't used as a resolution join key anywhere") that GG-166 directly contradicted — the motivating case for ADR-0052

**Current state (2026-10-08, W59.1):** Assertion A still PENDING per entry; related repair work tracked in GG-166/GG-170/GG-185. **Next:** Land T-432 assertion A.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-164 |
| Category | Data-quality / write-path field-labeling bug, distinct root cause from the already-RESOLVED GG-058 (UTC-midnight rollover dropping in-progress games) but in the same general area of the code — same class of "UTC calendar-day boundary interacting badly with an Eastern-evening game schedule," different mechanism (field mislabeling, not row-dropping). |
| What was missed | T-421's join-key verification step (task explicitly required checking `(player_id, game_date, threshold)` uniqueness before relying on it, rather than assuming it) found 194/2,132 distinct keys (9.1%) collide when using the row's raw `game_date` field. Root-caused by comparing against the date embedded in each row's own `ticker` (Kalshi's `KXMLBHIT-{YYMONDD}{HHMM}{teams}-{player}{jersey}-{threshold}` format, which reliably encodes the true game date): 45,119 rows have `game_date` exactly one day *ahead* of the ticker's date, plus 98 rows two days ahead — 45,217/64,396 rows total (70.2%) are mislabeled. Sampled rows show the pattern is not a narrow midnight edge case: e.g. `ts=2026-07-03T00:01:16Z`, `ticker=KXMLBHIT-26JUL021940TBKC-...` (game=Jul 2), `game_date field=2026-07-03` — the field reflects the UTC calendar date *at evaluation-cycle write time*, not the game's actual date. Since most MLB games start 18:00-20:00 ET (22:00-01:00 UTC) and run ~3h, the majority of any given game's ~60-90s evaluation cycles land after 00:00 UTC, so `game_date` is off-by-one for most rows of most games by construction — not an occasional artifact. Recomputing the join key with the ticker-derived date instead cuts collisions to 4/2,017 (0.2%), and those 4 are a second, independent, correctly-flagged-by-the-task cause: genuine doubleheaders (`...TBBOSG1...` / `...TBBOSG2...` in the ticker, TB@BOS 2026-07-17) sharing player/date/threshold across two real games — the task brief's own stated concern, confirmed real. |
| When it should have been caught | Whenever `game_date` was first stamped onto a cycle-log row from wall-clock UTC rather than parsed from the game's own scheduling data — not determinable from this session's read-only access without finding the write-site in `run_t4_mlb_live.py` (out of scope to locate/fix here). |
| Phases it survived | Untouched through T4 MLB's entire live-measurement history (2026-07-02 onward) — nothing in the T1-focused rollover fix (GG-058/T-215) or any later T4 session checked this field's correctness against the ticker it's stored alongside on every row. |
| Why it survived | The field is plausible-looking (a valid ISO date, usually close to correct) and nothing consumes it in a way that would surface a one-day skew as visibly wrong — it isn't used as a resolution join key anywhere in the existing pipeline (T4 does not currently join cycle-log rows back to outcomes at all, which is precisely the gap T-421 exists to fill). |
| Impact | Any future code — this session's or otherwise — that joins/groups T4 MLB cycle-log rows by the literal `game_date` field will silently merge cycles from two different games (pre-midnight tail of one game, most of the next day's game) for the same player/threshold, corrupting per-game outcome resolution and any calibration/Brier analysis built on it. T-421's outcome-join store works around this by deriving the game date from the ticker instead of trusting the row field, and documents the workaround in its design doc rather than silently using the broken field. |
| Discovery | This session (T-421, decoupled-outcome-store), 2026-08-05, during the task-mandated join-key uniqueness verification step (explicitly required: "Verify this is actually unique before relying on it... State what you find; do not assume") — found by cross-checking the row's `game_date` field against its own `ticker`'s embedded date rather than trusting the field at face value. |
| Resolution | Not built this session — out of T-421's hard scope fence (no changes to `run_t4_mlb_live.py`'s write path). Workaround (not a fix) applied in the new read-only outcome-join store: derive game date from `ticker` via regex, never from the raw `game_date` field. A real fix would locate and correct whatever produces the `game_date` field at write time (likely a `datetime.utcnow().date()` call that should instead parse the game's own start time/date) — left for the operator to prioritize and staff. |
| Status | OPEN — new, unstaffed, MEDIUM. |

**T-431 addendum note (2026-08-11):** per `04_EXECUTION/ACTIVE_QUEUE.md` (T-431 prompt block), this gap's write-site was fixed by T-429, but that alone does not close it. GG-164 stays OPEN pending BOTH (1) the historical backfill of the 45,217 already-mislabeled cycle-log rows, and (2) T-433's executable-assertion requirement (ADR-0007 amendment: no gap may be marked RESOLVED without a checked assertion, not a prose claim) — this is the same class of failure T-433 exists to prevent: GG-164's own record does not yet have such an assertion. Do not close this on the write-site fix alone.

</details>

---

### GG-165 — 38/46 live gap entries carry no explicit Severity (UNSPECIFIED); full backfill deliberately deferred out of T-423's XS scope

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Severity backfill still partial; this block set no new severities. **Next:** Backfill UNSPECIFIED severities in a dedicated pass.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-165 |
| Category | Systemic blind spot — same family as the classifier defect this session's T-423 fixed (GG-144-style: the signal that should route attention lives one layer up, in narrative, not in a structured field a generator can read). |
| What was missed | `**Severity:**` has been a structured field on every entry since the T-420 restructure, but populating it was never made a requirement of registering a gap — of 46 live entries, 38 (83%) carry `UNSPECIFIED`, 6 `MEDIUM`, 2 `LOW`, 0 `HIGH`/`CRITICAL` before this session. `scripts/generate_operator_console.py` sorts every bucket by severity then ID; with 83% of entries unranked, that sort order was close to meaningless outside the handful of entries someone had bothered to set. |
| When it should have been caught | At the T-420 restructure (2026-08-05) when the `**Status:** ... · **Severity:** ...` line was introduced — the migration script (`split_ggl.py`) defaulted every entry to `UNSPECIFIED` rather than requiring a value, and no follow-up backfill task was registered at that time. |
| Phases it survived | The T-420 restructure itself, plus every governance scan since (the scan prints severity counts in its `OPERATOR CONSOLE` block but never flagged the 83%-empty rate as a debt in its own right until this session). |
| Why it survived | No check compares populated-vs-UNSPECIFIED count against a threshold; the raw count was visible in scan output but never surfaced as an actionable line, so it read as background noise rather than a gap. |
| Impact | LOW directly (severity is a sort/attention aid, not a gating value — nothing in C4-C8 or the gate criteria reads it). MEDIUM indirectly: `OPERATOR_CONSOLE.md`'s within-bucket severity ordering is unreliable for any entry not explicitly set, which is most of them; an operator scanning top-to-bottom for "worst first" gets a partially arbitrary order. |
| Discovery | T-423 (2026-08-06), while fixing the console's blocked/broken classifier (regex-over-prose → explicit fields). Operator explicitly scoped severity work to sections 1/2 only for this session ("Do NOT backfill all 46 by hand this session — that is a multi-hour judgment exercise") and asked this gap be registered for the remaining 36. |
| Resolution | Not built this session, by explicit instruction. `generate_operator_console.py` now prints a `SEVERITY DEBT` line to stderr and a `> **Severity debt:**` callout at the top of `OPERATOR_CONSOLE.md` whenever `unspecified_n > 0`, so the debt stays visible on every scan rather than being silently absorbed. The remaining backfill (36 of 46, all outside sections 1/2 as of this session) is future work — no T-NNN assigned. |
| Status | OPEN — registration only, unstaffed. |
| Note | Originally registered as GG-163 in this session's own local history; renumbered to GG-165 on merge with `origin/main` after discovering `origin/main`'s concurrent T-421/T-422 sessions had independently claimed GG-163 (ESPN 403 blindness) and GG-164 (`game_date` field bug) for unrelated findings — same collision class as GG-159/GG-162, resolved the same way T-415 resolved its own GG-159 collision (renumber the newcomer, per `04_EXECUTION/SESSION_CLAIMS.md`/`TODO_NEXT.md` precedent). |

</details>

---

### GG-166 — `run_resolve_mlb.py` consumes the same corrupted `game_date` field GG-164 documented, and silently resolves T4M-PROJ positions against the wrong day's box score for ~44% of the epoch-12 clean cohort — corrupting live paper-trading WIN/LOSS/pnl, not just a future-risk join key

**Status:** OPEN — code fixed, ledger `game_date` corrected, GG-170 authority settled and 1,127/1,220 (92.4%) of the stale outcome/pnl population re-derived (T-437, 2026-08-11/12); 93 positions still outstanding pending outcome-store coverage; T4M-PROJ power-calc baseline now flips TARGET MET → NOT MET post-correction · **Severity:** CRITICAL · **Assertion:** PENDING(T-432, assertion A) — shared with GG-164 (same defect, write-site vs. read-site); B2's per-resolution `game_date_ticker_mismatch` refusal is a point check at resolution time, not a standing suite-level invariant, so this remains PENDING not LANDED (ADR-0052); also the concrete G6 precondition example (ADR-0052 §2.3) — Kelly sizing and the drawdown kill switch both read this same ledger

**Current state (2026-10-08, W59.1):** Entry's own status: code fixed, 93 positions outstanding pending outcome-store coverage; not re-derived this session. **Next:** Finish outcome-store coverage for remaining 93.

**T-429 (2026-08-07) update — full blast radius measured, code hardened both sides, `game_date` field corrected in place; `actual_hits`/`outcome`/`pnl` re-derivation for closed positions explicitly NOT done this session:**

- **B1 (write-site fix, `run_t4_mlb_live.py`):** the `date.today()` UTC-wall-clock stamp at position-open is replaced with a ticker-derived date, closing the corruption at its source for all future positions.
- **B2 (read-site hardening, `run_resolve_mlb.py`):** `_resolve_pool()` now independently re-derives the game date from each position's own `kalshi_ticker` (same anchored regex T-421 validated at 100% reliability across 2,021 tickers) and **refuses to resolve** — logs `game_date_ticker_mismatch` via `AuditLogger.warning` and skips — any position where the stored `game_date` disagrees with the ticker. This turns future instances of this bug into a loud, visible refusal instead of a silent wrong-day resolution.
- **B2a:** checked T-416's 17 remaining stuck T1/MAIN `aged_open` positions against this same ticker-vs-`game_date` test — **0/17 mismatches**. T-416's positions are unrelated to GG-166 (genuine data absence, not date corruption); T1/MAIN's daily-batch write path does not share T4's long-running-session UTC-midnight-rollover mechanism.
- **B3 (true blast radius, superseding the "~44% of epoch-12" estimate above):** measured ticker-vs-`game_date` mismatch across **every** `logic_epoch` in the full T4M-PROJ ledger (2,193 closed + 223 open positions), not just the 156-position epoch-12 clean cohort this entry originally scoped to:

  ```
  epoch=1:  total=122 mismatch=79  (64.8%)
  epoch=2:  total=122 mismatch=0   (0.0%)   ← only clean epoch
  epoch=3:  total=666 mismatch=247 (37.1%)
  epoch=6:  total=143 mismatch=49  (34.3%)
  epoch=7:  total=184 mismatch=49  (26.6%)
  epoch=8:  total=799 mismatch=689 (86.2%)
  epoch=12: total=157 mismatch=107 (68.2%)
  OVERALL:  total=2193 mismatch=1220 (55.63%)
  open_positions: 223/223 (100%) mismatched
  ```

  This is far larger than the original 44%/epoch-12-only estimate. **Every epoch's historical P&L/win-rate figure except epoch 2 is now known to rest on a ledger with material, non-random date corruption** — this is not confined to the clean cohort or to epoch-12.
- **Ledger correction applied (not a full "re-resolve"):** `scripts/correct_t4_game_dates.py` (new, network-free, dry-run-by-default, mirrors `scripts/repair_stuck_mlb_positions.py`'s pattern) corrected the `game_date` field in place for all 1,220 closed + 223 open mismatched positions on the VPS ledger, after a verified backup (`paper_portfolio_mlb_t4.pre_gg166_correction_20260807T052850Z.json`). Closed positions were additionally flagged `game_date_corrected_but_outcome_stale: True` — **their `actual_hits`/`outcome`/`pnl` were deliberately NOT re-derived.** Re-deriving true outcomes for ~1,220 already-resolved positions requires live re-fetches against the MLB Stats API/ESPN, which GG-084 (T-416/T-422) showed escalates to a 100% Fastly-CDN block partway through any sequential batch from the VPS's own datacenter IP. The known-safe mitigation is the two-phase fetch-off-VPS/apply-on-VPS split T-422 used for the 5-position T1/MAIN repair — not attempted here; this is the single largest piece of GG-166 remediation still outstanding.
- **B4 (recompute clean_n/mean/stdev/n\*, `logs/t4_mlb_resolved_ledger.jsonl` rebuilt via `scripts/build_t4_resolved_ledger.py` from the now-`game_date`-corrected portfolio, then `scripts/run_power_calc.py` re-run):** result is **numerically IDENTICAL to the pre-correction baseline** — `clean_n=157, mean_pnl/bet=$+0.3793, stdev_pnl/bet=$1.8821, n*=267` (raw_n=2193, win_rate=0.570 across the full rebuilt ledger). This is expected, not a null result: `clean_n`/mean/stdev are computed from `outcome`/`pnl`, which this session's fix did not touch — only `game_date` was corrected. **The actionable finding is structural, not numeric: the current clean_n=157 cohort (epoch 12) is exactly the epoch-12 population in the B3 table above, meaning 107/157 (68.2%) of the positions backing today's live `n*=267` governance target carry a `game_date` that was wrong at resolution time.** The power-calc baseline itself must be treated as unverified, not merely "unchanged," until those 107 positions' outcomes are re-derived.
- **Not done earlier this session (now complete): epoch decision, Step 4 write-recency detector, downstream-doc flagging — see below for what is still open.**

- **B5 (2026-08-07, later same day, T-429 continuation) — cross-check vs. T-421's decoupled outcome store, run to completion. Confirms the `game_date` fix is working; discovers a second, distinct, similarly-sized disagreement source that GG-166's original diagnosis does not explain.**

  The T-421 outcome-store backfill (`scripts/build_t4_outcome_store.py`, parallelized this session with a `--workers` flag — I/O-bound HTTP fetches, no correctness change) was run to completion **off the VPS** (local network — GG-084's Fastly-CDN block is specific to the VPS's datacenter IP, not to the script itself; verified via direct `curl`/`ssh` A/B before running): **1,943/2,021 tickers resolved (96.1%), 78 permanently unresolved** after exhausting all three sources (MLB_R, MLB_P, ESPN) twice each with null results — a documented, expected terminal state, not a bug.

  `logs/t4_mlb_resolved_ledger.jsonl` was rebuilt fresh (`scripts/build_t4_resolved_ledger.py --pull`, read-only ssh `cat` of the live VPS portfolio) against the now-corrected portfolio: raw_n=2,416 resolved positions, clean_n (epoch≥12)=187. Re-running T-426's own unmodified Task 1 script (`scripts/run_t426_shadow_power_calc.py`) against this corrected ledger + the completed store gives:

  ```
  clean_n (epoch>=12) = 187, all 187 matched a resolved store row (0 unmatched, 0 unresolved-in-store)
  hits_agree=118  hits_disagree=69   (36.9%)
  outcome_agree=140 outcome_disagree=47 (25.1%)
  ```

  **First check — does the original root cause (ticker-date vs. recorded `game_date` mismatch) still explain this?** No. Direct check of every one of the 187 clean-cohort rows: **187/187 (100%) now have `game_date == ticker-derived date`** — B1's write-site fix has fully eliminated the date-corruption mechanism for this cohort; zero mismatches remain (versus 107/157, 68.2%, before the fix). This is confirmation the B1/B2 fix works as designed.

  **But the disagreement did not go away — it persists at a similar magnitude (36.9%/25.1% now vs. 44.2%/30.1% pre-fix) with the date-mismatch mechanism ruled out.** This is a second, distinct, currently-unexplained disagreement source. What was checked and ruled out this session: (a) not concentrated on one bad data day — disagreement rate is roughly even across all four dates in the cohort (41%, 37%, 29%, 26% for 07-31/08-01/08-02/08-03 respectively); (b) not a doubleheader/game-number ambiguity — zero player+game_date pairs in the clean cohort have more than one distinct ticker start-time/team-pair combination, so there is no same-day second-game collision to misattribute. Root cause **not yet identified**. One structural observation not yet investigated: the ledger's original resolution ran ~2026-08-02 (per `resolved_at`), while the store's independent re-fetch ran 2026-08-07 — a 5-day gap during which the same MLB Stats API endpoint was queried twice for the same, already-final game. Whether the API can return a different `actual_hits` value for a closed game on a later query (e.g. official scorer correction, box-score revision) is an open question, not a confirmed explanation.

  **This is registered here, under GG-166, rather than as a new gap, because it was discovered by GG-166's own B5 follow-on and directly bears on the same governance question (is the T4M-PROJ clean_n=187 cohort trustworthy for GG-004/APR-0024?) — but it is explicitly a different mechanism than GG-166's diagnosed root cause and should not be assumed fixed by the `game_date` correction.** Net effect: the T4M-PROJ power-calc baseline remains unverified — not because the original bug persists (it doesn't, confirmed above), but because an independent, undiagnosed ~26-37% disagreement rate between the ledger's own resolution and an independently-sourced re-fetch is still present in the current clean cohort. Recommend continuing to treat GG-166 as a G6/GG-004 blocker until this second source is root-caused. Not staffed further this session — flagged for the operator to prioritize, per this project's capability-boundary standard (surface, don't unilaterally chase into `src/` changes beyond this task's fence).

  **T-431 update (2026-08-10/11) — root-caused, registered separately as GG-170 (OPEN, CRITICAL):** the "5-day gap / box-score revision" structural observation noted above was the right instinct but not quite the mechanism. Three independent live-API ground-truth queries (Jackson Merrill, Freddie Freeman, Yordan Alvarez) confirmed the MLB Stats API's `gameLog` `date`-to-split labeling is transiently unstable near real-time: a delayed/retried resolution querying the identical `(player_id, game_date)` pair can return `game_date`+1's true hit total instead of `game_date`'s, with no error signal — explaining the pre-existing 44/44-vs-0/44 earliest-resolved-matches/latest-resolved-mismatches pattern. This is registered as **GG-170**, not folded into this entry, because it is a distinct external-data-source mechanism (API-side date-label instability) rather than an escalation of GG-166's own write-time `date.today()` bug (which remains fixed and confirmed dead — 0/187 mismatches). See GG-170 for full detail. Task 2 (re-deriving the ~1,220 `game_date_corrected_but_outcome_stale` positions, described below) was investigated but not executed this session — its target file (`paper_portfolio_mlb_t4.json`) is VPS-only, not present in this worktree, and that population is very likely dominated by this entry's already-fixed write-time mechanism rather than GG-170's newly-found API-timing mechanism; conflating the two in one re-derivation pass would risk mis-attributing outcomes, so it is left for a dedicated, VPS-coordinated follow-on.

- **Still not done (tracked as follow-on):** re-deriving true outcomes for the ~1,220 positions flagged `game_date_corrected_but_outcome_stale: True` (requires the two-phase fetch-off-VPS/apply-on-VPS write-back pattern, since unlike B5's read-only cross-check this would write to the live ledger) — separate, larger, and out of B5's scope; and root-causing the new B5 disagreement source described above.

- **T-437 (2026-08-11/12) update — the follow-on above is now done. GG-170 authority settled at n=69, the two mechanisms separated, ledger re-derived, and the power-calc baseline flips.**

  **Task 1 — GG-170 authority, n≥50 (actual n=69, the full date-clean disagreement pool):** fresh live re-fetches (MLB Stats API primary / ESPN fallback), run days after the original disagreements, against every (`player_id`, `game_date`) pair in Set A (date-clean, i.e. ticker-matched `game_date`, where ledger `actual_hits` disagreed with the T-421 store). Result: **69/69 STORE, 0/69 LEDGER, 0/69 NEITHER.** The store is authoritative — confirmed at n=69, not the earlier n=3 spot-check. No third mechanism found (the "matches neither" bucket, the condition that would have blocked Task 2/3, was empty).

  **Task 1 also surfaces a materially worse timing picture than GG-170's original framing.** All 69 sampled disagreements were *originally* resolved ~54.7–54.9h after `game_date` (a tight cluster, consistent with `_resolve_pool()`'s `>48h` aged-open grace-period retry picking them up on the first eligible cron pass) — and were **still wrong at that point**. They only became reliable somewhere between then and the store's build date (2026-08-07, T-421) or this session's re-fetch (2026-08-11) — i.e. the MLB Stats API's `gameLog` date-label instability GG-170 diagnosed is not a narrow "near-real-time" window; it was still actively wrong at +2 days for this entire sample. See GG-170 for the full timing writeup and T-437's proposed mitigation (design-only, not built).

  **Task 2 — mechanism separation over the full 1,220-position stale population** (GG-166's write-time bug vs. GG-170's read-time API instability vs. neither), using the store as ground truth:

  ```
  GG166 (store hits != ledger hits — GG-166's wrong-day query is a sufficient explanation): 757 (62.0%)
  NEITHER (store hits == ledger hits — wrong-day query coincidentally landed on the right total): 370 (30.3%)
  UNRESOLVED (no resolved store row — needs a future live fetch, not attempted this session): 93 (7.6%)
  ```

  Framing note: this uses a GG166/NEITHER/UNRESOLVED split rather than a literal GG-166/GG-170/neither three-way split, because GG-170's specific mechanism (instability on an otherwise-*correct*-date query) does not apply to a population that, by construction, queried the *wrong* date at original resolution — GG-166's wrong-day query is already a sufficient explanation for every GG166-tagged disagreement, with no need to additionally invoke GG-170. GG-170 as its own mechanism is fully characterized by Task 1's n=69 date-clean sample instead.

  **Task 3 — re-derivation, applied to the live VPS ledger.** `scripts/t437_task3_rederive_outcomes.py --apply`, gated behind the same advisory `fcntl.flock` discipline `PaperTrader._file_lock()` uses (to avoid racing the live T4 process), backed up automatically (`paper_portfolio_mlb_t4.pre_t437_rederivation_20260812T001532Z.json`) before write. 757 GG166 positions had `actual_hits`/`outcome`/`pnl` overwritten from the store (old values preserved under `_pre_t437_rederivation` per-position for audit); 370 NEITHER positions had only the `game_date_corrected_but_outcome_stale` flag cleared (no value change); 93 UNRESOLVED positions were left fully untouched, flag still set. Net applied P&L delta: **-$109.9643**.

  Before/after power-calc, same clean_n=453 population (epoch≥12 — grown from the earlier clean_n=157/187 snapshots via ordinary trading volume since; not itself part of this correction), pre- vs. post-correction outcome data:

  ```
  BEFORE (pre-t437, using the automatic backup): clean_n=453, n*=328  → TARGET MET
    mean_pnl/bet=$+0.3113  stdev_pnl/bet=$1.7126
  AFTER  (post-t437, live ledger):               clean_n=453, n*=839  → TARGET NOT MET (needs 386 more clean bets)
    mean_pnl/bet=$+0.1772  stdev_pnl/bet=$1.5593
  ```

  **This is a G6-relevant governance finding, not just a data cleanup: correcting the GG-166 write-time date bug's downstream outcome corruption flips T4M-PROJ's own commercial-validation gate from TARGET MET to target NOT met, and roughly halves the measured mean edge per bet.** The prior TARGET MET reading (and every `n*`/mean/stdev figure derived from `logs/t4_mlb_resolved_ledger.jsonl` before this correction) was computed on a ledger where 68.2%+ of the epoch-12 clean cohort carried a wrong `game_date` and, for 62% of that stale-flagged subset, a directly wrong outcome/pnl. Do not cite the pre-T-437 `clean_n=157/187, n*=267/...` figures as current; they are superseded by this correction the same way the earlier B4/B5 snapshots were superseded by population growth.

  **Residual, not corrected this session:** 93 UNRESOLVED positions remain flagged `game_date_corrected_but_outcome_stale: True` with unchanged (potentially wrong) outcome/pnl — the T-421 store has no resolved row for them. A future session should extend the outcome store (two-phase off-VPS-fetch/on-VPS-apply, GG-084) to cover these 93 specifically, then re-run `t437_task3_rederive_outcomes.py --apply` (it already skips anything the store can't resolve, so it is safe to re-run once the store grows).

  **Proposed mitigation (design-only, per T-437's explicit scope — not built):** GG-170's window of unreliability is now evidence-bound at ≥55 hours post-`game_date` (69/69 wrong at that point) and known-reliable by ≥7 days (T-421 store) / ≥11 days (this session's re-fetch), with no sampled data points in between to narrow it further. Recommend `run_resolve_mlb.py` treat any resolution attempt as provisional until a second independent re-fetch, taken no sooner than 7 days after the first, agrees with it — i.e. a reconcile-on-reread design rather than a single trust-after-N-hours wait, since the true stabilization point within the 2–7 day window is not established by this dataset and a fixed-N wait risks being either too short (data) or unnecessarily long (a single conservative N=7d for every position, most of which likely stabilize earlier).

  Scripts (`t437_task1_settle_check.py`, `t437_task2_classify.py`, `t437_task3_rederive_outcomes.py`) live in `scripts/`, committed on `session/20260811T235604Z-t437-outcome-authority`.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-166 |
| Category | Data-integrity bug with a direct P&L consequence — escalation of GG-164, not a duplicate. GG-164 characterized `game_date` as a mislabeled field with no active consumer ("it isn't used as a resolution join key anywhere in the existing pipeline"); this entry shows that claim is false for the ledger's own `game_date` field on position records, which IS consumed as a resolution join key, with a measured, non-hypothetical P&L impact. |
| What was missed | T-426 (this session), building a decoupled outcome-measurement store independent of the paper-trading ledger, ran an agreement check between the store's ticker-derived `actual_hits` and the ledger's own recorded `actual_hits` for the T4M-PROJ epoch-12 clean cohort (156 matched, store-resolved positions). Found 69/156 (44.2%) hit-value disagreements and 47/156 (30.1%) outcome (WIN/LOSS) disagreements — far above noise. Root-caused by checking each disagreement's ledger `game_date` field against the true game date embedded in that position's own `kalshi_ticker` (Kalshi's `KXMLBHIT-{YYMONDD}...` format): **100% of the 69 hit-disagreements coincide exactly with a mismatched `game_date` (69/69); 0% of date-matched positions disagree (0/87).** Mechanism confirmed in code: `run_t4_mlb_live.py:1519` stamps `game_date = date.today().isoformat()` (UTC wall-clock at write time — the exact GG-164 bug pattern) onto the position record at bet-entry, and `run_resolve_mlb.py`'s `_fetch_mlb_hits()` (lines ~436-441, 214-221) later queries the MLB Stats API using that position-level `game_date` field as an exact-match key against `split.get("date")` in the player's season gameLog. When the (wrong) recorded date happens to also be a game day for that player's team — common, since MLB teams play near-daily — the API silently returns a valid split from a **different game**, producing wrong `actual_hits`, wrong `outcome`, and wrong `pnl` with no error, no warning, and no visible signal that resolution used the wrong day. |
| When it should have been caught | At GG-164's own discovery (2026-08-05, T-421) — that entry's "Why it survived" field asserted the field had no consuming join, which was not verified against `run_resolve_mlb.py` before being written. A one-file grep (`grep -n game_date src/prediction_market_bot/run_resolve_mlb.py`) at that time would have found the same consumption path this session found. |
| Phases it survived | Every T4M-PROJ resolution run since `run_t4_mlb_live.py`'s position-open write path began stamping `game_date` this way — i.e., plausibly the entire T4 MLB paper-trading history, not just epoch-12. This session only checked the epoch-12 clean cohort (156 positions); the raw (non-clean-filtered) resolved-position count is 2,193 per the same `run_power_calc.py` baseline this session used, so the affected population may be much larger than 69. |
| Why it survived | Same root cause as GG-164: the field is plausible-looking (a valid ISO date, close to correct) and a wrong-game resolution produces a normal-looking WIN/LOSS/pnl record with no error signal — nothing in the pipeline cross-checks a resolved position's outcome against an independent source. This session's decoupled outcome store is the first artifact in the project with an independent enough data path to surface the mismatch at all. |
| Impact | **Directly affects G6 gate evidence.** T4M-PROJ's current governance baseline (`exp_output/T323-POWER-CALC/power_calc_results.json`, re-run this session): `clean_n=157, mean_pnl/bet=$+0.3793, stdev_pnl/bet=$1.8821`. If ~44% of that clean_n's underlying positions have wrong outcome/pnl (consistent with the measured 44.2% rate in the 156-position matched subset), the mean/stdev feeding `n*` and the go/no-go P&L sign are both unreliable as currently computed. This is squarely inside GG-004/APR-0024's commercial-validation gate — a governance-grade verdict must not be drawn from the current ledger until this is fixed and the affected positions are re-resolved. Per T-426's explicit scope fence, none of this session's numbers (shadow `mu`/`sigma`, Task 2/3 figures) are being reported as governance-grade for the same reason — this gap is the reason, not merely correlated with it. |
| Discovery | T-426 (2026-08-06), Task 1 (agreement check) of the decoupled-outcome-store shadow power-calc, immediately upon finding a 44%/30% disagreement rate against a value (`hits_agree`/`hits_disagree`) the task brief expected to be a near-total-agreement sanity check. |
| Resolution | Not built this session — out of T-426's hard scope fence (read-only, no `src/` changes). The correct fix has two parts, both left for the operator to staff: (1) fix `run_t4_mlb_live.py`'s write-time `game_date` stamp to parse the game's actual scheduled date rather than `date.today()` (this also fixes GG-164 at the source, since both appear to derive from the same variable); (2) re-resolve every already-resolved T4M-PROJ position (and check other bands using the same `run_resolve_mlb.py` path) against the corrected date or the ticker-derived date directly, and recompute `clean_n`/mean/stdev/`n*` from the corrected ledger before treating the current power-calc baseline as valid. Until (2) is done, GG-004's live n-count/clean_n status should be read as unverified, not merely pending-more-data. |
| Status | OPEN — new, unstaffed, CRITICAL. Recommend treating as a G6 blocker alongside GG-004 until resolved. |

</details>

---

### GG-167 — `deploy.yml`'s dirty-tree guard only inspects tracked files; an untracked-file collision on the VPS silently blocked `git pull --ff-only` during GG-163's deploy, sibling gap shape to the already-resolved GG-130

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** deploy.yml line 153 still uses --untracked-files=no, so the untracked-collision blind spot persists. **Next:** Add an untracked-collision check before git pull --ff-only.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-167 |
| Category | Deploy-safety blind spot — sibling of GG-130 (RESOLVED, archived), same general area (`deploy.yml`'s dirty-tree guard around `REGEN_ROOTS`) but a structurally distinct failure mode: GG-130 was about **tracked** files drifting from what the guard expected; this is about **untracked** files on the VPS colliding with paths a `git pull --ff-only` needs to create/overwrite. |
| What was missed | During this session's (T-429) VPS deploy of the GG-163 ESPN-UA fix, `git pull --ff-only` (cddf027→5e8f047) failed outright — not on tracked-file drift (which GG-130's guard would have caught and auto-healed/hard-failed on) but on two **untracked** files already present at the exact paths the incoming commit range introduced: `scripts/apply_resolved_hits.py` and `scripts/repair_stuck_mlb_positions.py`. Git refuses a fast-forward merge when it would overwrite untracked local files, and `deploy.yml`'s guard has no check for this at all — it only ever inspects tracked files under `REGEN_ROOTS`, so an untracked collision anywhere in the pull's path range is invisible to it until the pull itself fails. |
| When it should have been caught | At GG-130's original design/fix (its RESOLVED date, see archive) — a `git pull --ff-only` can be blocked by untracked-file collisions independent of any tracked-file drift, and nothing in that fix's threat model considered files that exist on the VPS but were never committed there (e.g., ad hoc repair/investigation scripts written directly on the VPS during an incident, never committed, then later added to the repo under the same filename from a different session). |
| Phases it survived | GG-130's entire fix lifecycle (RESOLVED, archived) plus every deploy since — this is the first deploy session to hit an untracked-path collision against the guard rather than a tracked-drift case, so the gap in coverage was latent, not previously exercised. |
| Why it survived | `deploy.yml`'s guard was scoped, by design, to `REGEN_ROOTS` tracked-file drift (GG-130's actual failure mode) — untracked files were out of that fix's stated scope, not an oversight within it, but the absence was never separately registered as its own residual gap once GG-130 closed. |
| Impact | LOW as measured this session: the collision was caught manually (the pull failed loudly, not silently), diagnosed, and resolved safely by backing up (not deleting) the two colliding files to `/root/vps_untracked_backup_20260807/` before retrying the pull — no work was lost. The residual risk is procedural: without a structural check, recovering from this collision depends on whoever is deploying noticing the `git pull` failure message and choosing backup-and-retry over a more destructive shortcut (e.g. `git clean -fd`, which Hard Rule 10 already prohibits unscoped but which a rushed deploy could still reach for). |
| Discovery | T-429 (2026-08-07), during the GG-163 fix's VPS deploy — `git pull --ff-only` failed with git's standard "untracked working tree files would be overwritten by merge" error, listing both colliding paths explicitly. |
| Resolution | Not built this session — deploy-tooling change (`deploy.yml`), out of this task's scope fence (may change `run_t4_mlb_live.py`, `run_resolve_mlb.py`, plus the Step-4 write-recency detector only). Manual workaround applied and documented in GG-163's Recovery-proof note: backup untracked colliding files to a timestamped directory on the VPS, then retry the pull. A real fix would extend `deploy.yml`'s guard to `git status --porcelain` for untracked entries under the paths a pending pull would touch (e.g. `git diff --name-only HEAD..origin/main` intersected against `git ls-files --others --exclude-standard`), failing loudly with the same backup-and-retry procedure automated rather than manual — left for the operator to prioritize and staff. |
| Status | OPEN — new, unstaffed, LOW. |

</details>

---

### GG-168 — Step 4's T4 cycle-log write-recency probe (GG-163/T-429) has no exemption for "daily T4 budget exhausted" — a legitimate zero-new-rows state indistinguishable from a real outage by the probe's own logic

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Step 4 probe in CLAUDE.md still has no budget-exhausted exemption (re-read this session). **Next:** Add budget-exhausted exemption to the probe.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-168 |
| Category | Systemic blind spot — same probe family as GG-163, but a false-positive-shaped gap in the fix rather than a recurrence of the original outage. |
| What was missed | Running the Step 4 T4 cycle-log write-recency probe this session (T-434, 2026-08-10) found `t4_mlb_cycle_log.jsonl`'s last row 21.0h stale (`2026-08-10T02:33:03Z` vs. now `2026-08-10T23:34:44Z`) while T1 MLB confirmed live-market player matches — on its face, exactly the alarm condition CLAUDE.md's probe describes ("age_hours in the high single digits or more while games were live ... is a signal failure — investigate immediately"). Direct SSH inspection showed this is **not** a GG-163 recurrence: `t4_mlb_live_cron.log` shows zero 403/forbidden lines in the last 200 entries, ESPN discovery succeeding, and the process actively polling two genuinely live games with real batter state (`game=401816469 inning=2`, `game=401816470 inning=1`, 14 batters each). The per-cycle stat line reads `eval=0 fired=0` with `T4_budget: $270.00/$270.00 (100%)` — the daily T4 budget cap is fully deployed, and evaluation appears to short-circuit before a cycle-log row is written once the cap is hit, even with live, evaluable batter state present. The probe's documented exemption list ("off-day, off-season, or a pregame stretch with no live batter state") does not include this case, so a session following the protocol literally would flag a false alarm — or, in the opposite direction, a genuine future silent-discovery failure occurring on a day when budget also happens to be exhausted would be wrongly written off as "just the budget-cap case" without verification. |
| When it should have been caught | At GG-163/T-429's original fix (2026-08-07) — the write-recency probe was designed and verified against the ESPN-403 failure mode specifically; the budget-exhaustion code path (whatever gates cycle-log writes on `T4_budget` state) was not considered as a second legitimate source of a stale-looking log when that probe was written. |
| Phases it survived | Unexercised until this session — T-429's fix session ended before any live game day drove the T4 budget to 100%, so this interaction was never hit. |
| Why it survived | The probe checks wall-clock age and cross-references only T1's player-match count and season/off-day status; it has no visibility into T4's own per-cycle `eval`/`fired` counters or `T4_budget` state, which live only in `t4_mlb_live_cron.log`'s cycle-summary lines, not in any file Step 4 currently reads. |
| Impact | MEDIUM, procedural: as observed this session, the underlying behavior may be entirely correct (daily budget cap doing its job at end-of-day) — but the protocol as written cannot currently distinguish that from a silent failure without an operator manually tailing `t4_mlb_live_cron.log` and reading the cycle-summary line, which Step 4 does not currently instruct anyone to do. Whether budget-exhausted cycles *should* still write an (non-firing) evaluation row to `t4_mlb_cycle_log.jsonl` — i.e., whether `eval=0` while live batter state exists is itself correct behavior or a separate bug in the evaluation gate ordering — was not determined this session; that question is unstaffed. |
| Discovery | T-434 (2026-08-10), MICRO-scoped protocol-sizing session, while running CLAUDE.md Step 4 verbatim as part of the mandatory session-start protocol — register-and-stop per Hard Rule 11, this task's deliverable is unrelated (three protocol files, session-scope trigger thresholds). |
| Resolution | Not built this session — out of scope. Two independent follow-ups for a future staffed session: (1) confirm whether `eval=0`/no cycle-log row on budget-exhausted cycles is intended design or a gap-ordering bug in the evaluation code path itself; (2) extend Step 4's write-recency probe to also read the latest `T4_budget` cycle-summary line from `t4_mlb_live_cron.log` so "budget exhausted, correctly idle" is a third recognized exemption alongside off-day/off-season/pregame, rather than an unhandled case that looks identical to a real outage. |
| Status | OPEN — new, unstaffed, MEDIUM. |

</details>

---

### GG-170 — MLB Stats API `gameLog` date-label is transiently unstable in near-real-time; a delayed/retried resolution query can bind to `game_date+1`'s true hit total instead of `game_date`'s, root-causing the second B5 disagreement source GG-166 left unexplained

**Status:** OPEN · **Severity:** CRITICAL

**Current state (2026-10-08, W59.1):** CRITICAL external-source instability; no fix evidence this session. **Next:** Pin resolution query to dated gameLog and cross-check totals.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-170 |
| Category | External data-source instability, not a code bug — sibling to GG-166 (same governance impact, T4M-PROJ clean_n trustworthiness) but a structurally distinct mechanism: GG-166 was our own write-time date-stamping bug (fixed, confirmed dead, 0/187 mismatches); this is the MLB Stats API itself returning an ambiguous/incorrect `date`-labeled split on a later query for an already-resolved game. |
| What was missed | T-431 (this session) tested GG-166's B5 follow-on question — a 36.9%/25.1% (hits/outcome) disagreement rate between the ledger's own resolution and T-421's independently-sourced outcome store, persisting at similar magnitude even after GG-166's `game_date` fix was confirmed 100% effective (0/187 mismatches in the current clean cohort). Direct code re-read of `run_resolve_mlb.py` ruled out any arithmetic/date-handling bug on our side: `_fetch_mlb_hits()` performs a pure exact-string-match, `split.get("date","") == game_date`, against the first matching split in the MLB Stats API's own `gameLog` response — no date offset, no timezone conversion, no our-side computation of any kind. Three independent live-API ground-truth queries this session (Jackson Merrill id=701538, Freddie Freeman id=518692, plus an earlier Yordan Alvarez check) confirmed: for each of these players' disagreeing ledger positions, the ledger's `actual_hits` value exactly matches the true hit total for **`game_date`+1**, while the store's (later-refetched, from a local non-VPS machine) value exactly matches the true hit total for `game_date` itself — i.e., the same `(player_id, game_date)` query pair, issued at two different times, returned two different hit totals, one of which is objectively wrong for the requested date. This is consistent with, and gives a causal mechanism for, the pre-existing deterministic pattern already established before this session: across all 44 tickers in the full ledger with >1 distinct `actual_hits` value sharing a ticker, the EARLIEST-resolved position matches the independently-sourced store 44/44 times, and the LATEST-resolved position matches it 0/44 times — i.e. resolving sooner after the game is safe, resolving later (a delayed or retried resolution against the identical join key) risks silently binding to the wrong day's split. |
| When it should have been caught | Could not reasonably have been caught before GG-166's B5 cross-check existed — this requires an independently-sourced, differently-timed re-fetch to detect at all, since our own code performs no incorrect operation; the API itself is the source of the discrepancy. GG-166's B1 fix (ticker-derived `game_date`, correct at write time) does not protect against this, since the mechanism doesn't require an incorrect `game_date` — it happens even when `game_date` is already correct, purely as a function of *when* the resolution query is issued. |
| Phases it survived | Plausibly the entire T4M-PROJ resolution history — any resolution that ran later than the game's near-real-time window (a delayed cron run, a retry after a transient failure, a backfill) is a candidate instance, independent of the epoch/game_date-corruption timeline GG-166 already measured. Not yet measured across the full ledger this session — only the 187-position epoch-12 clean cohort GG-166/B5 already isolated. |
| Why it survived | Nothing in the pipeline cross-checks a resolved position's `actual_hits` against a second, independently-timed source — GG-166's B5 outcome-store cross-check is the first artifact in the project with an independent enough data path to surface this at all, and even then only because T-431 traced the *remaining* disagreement (after ruling out the already-fixed `game_date` mechanism) back to API-side timing rather than assuming it was already explained. |
| Impact | Same governance surface as GG-166: directly bears on whether the T4M-PROJ `clean_n=187` cohort (and the `n*`/mean/stdev feeding GG-004/APR-0024) is trustworthy. Unlike GG-166's mechanism (which is now understood, fixed at the write site, and bounded to positions with a corrected-but-stale `game_date`), this mechanism has no known fix yet — a resolution can be individually correct in every way our code controls (right `game_date`, right join, right gating on `abstractGameState=="Final"`) and still resolve to the wrong day's outcome, purely as a function of query timing against an external API whose date-labeling is not guaranteed stable near real-time. Recommend continuing to treat T4M-PROJ's power-calc baseline as unverified pending a mitigation (e.g., a mandatory minimum resolution delay past game-final, or a second-source cross-check before accepting a resolution as final) — this is a live, unresolved architectural gap in `run_resolve_mlb.py`'s resolution timing, not a one-time data-correction task like GG-166's `game_date` fix was. |
| Discovery | T-431 (2026-08-10/11), Task 1 of this session's charter (root-cause the B5 disagreement GG-166 left unexplained), via direct live MLB Stats API ground-truth queries against three players' disagreeing positions, cross-referenced against the pre-existing 44/44-vs-0/44 earliest/latest deterministic pattern. |
| Resolution | Not built this session — out of T-431's scope fence (`scripts/` and the ledger only, with backup; no changes to `run_resolve_mlb.py` or any production pipeline file). A real fix requires a staffed follow-on to design and implement a mitigation in `run_resolve_mlb.py`'s resolution timing/gating logic (candidates: enforce a minimum delay after `abstractGameState=="Final"` before accepting a resolution as terminal; or add a second, differently-timed confirmatory fetch before writing `actual_hits`/`outcome`/`pnl`) — left for the operator to prioritize and staff. Separately, and NOT attempted this session per the HARD STOP condition governing Task 2/3: re-deriving outcomes for the ~1,220 `game_date_corrected_but_outcome_stale`-flagged positions (GG-166's own follow-on) targets a different, VPS-only file (`paper_portfolio_mlb_t4.json`, not present in this worktree) and is very likely dominated by GG-166's already-understood, already-fixed mechanism rather than this session's newly-found API-timing mechanism — the two should not be conflated when that re-derivation work is eventually staffed. |
| Status | OPEN — new, unstaffed, CRITICAL. Recommend treating as a G6/GG-004 blocker alongside GG-166 until a mitigation is designed. |

</details>

**2026-08-17 update (T-458):** Mitigation built. (1) A new `_verify_official_date()` cross-check in `run_resolve_mlb.py`'s `_fetch_mlb_hits()` queries the MLB Stats API's `/api/v1/schedule?gamePk=` endpoint for the split's `gamePk`'s authoritative `officialDate` and refuses the resolution (returns `None`, fail-closed on both a confirmed mismatch and an inconclusive lookup) unless it exactly confirms the requested `game_date` — a second, independent signal beyond the `gameLog` split's own `date` label this gap found untrustworthy near real-time. (2) No new settle-window code was needed: a refusal here falls through the existing Postseason→ESPN fallback chain and, failing those, the pre-existing 48h aged-open retry window — reusing infrastructure that already never silently drops or guesses a value. (3) Backfill of already-corrupted epoch-12 rows was scoped, not executed (out of session scope): 532 closed T4M-PROJ epoch-12 positions carry the mismatch; 0 of 532 are currently re-derivable from the T-421 outcome store, not from a matching-key defect (ruled out) but because the store's own data coverage ends 2026-08-03, before the affected range (2026-08-07 onward) begins — all 532 are theoretically re-derivable via a direct re-query using the ticker's true date, reusing `fetch_actual_hits()` (now guarded by this fix), but building that backfill is a follow-on. (4) `assert_ledger_invariants.py` now prints a loud `[GG-170 RECURRENCE]` stderr banner and appends a `recurrence_alarm` JSONL report line whenever assertion A's violations include the *current* max `logic_epoch` for a band — confirmed firing against real data (`654 NEW ticker/game_date mismatches` for T4M-PROJ epoch 12), exit code unchanged (still 0, `--strict` not promoted). Independently re-verified the operator's cited epoch-12 figure while doing this: the correct closed-only violation rate is **532/719 = 74.0%**, not the cited 654/719 = 91.0% (654 is an all-status-combined count — 532 closed + 46 open + 76 rejected — not closed-only); 74.0% is still up from CLAUDE.md Q7's 69.9% (2026-08-11), supporting the "still accruing" direction of the claim even though the specific figure needed correction. Full detail: `DECISION_LOG.md` 2026-08-17, T-458. **A separate, unexplained anomaly surfaced during this verification — all 532 corrupted closed rows resolved strictly after the sibling GG-166 guard's confirmed deployment, which should have refused them — registered as [[GG-185]] rather than chased in this session (Hard Rule 11).**

---

### GG-172 — `MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 are written entirely in market-type terms and contain zero boxes addressing band activation, even though the operator's coverage directive is explicitly "all five bands" and three of five bands have essentially no trading history

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** MARKET_EXPANSION_ACTION_PLAN.md still states at l.14 the band dimension is unowned and the GG-172 ID is only 'reserved'; no band-activation boxes added. **Next:** Add band-activation boxes to Phases 1-4.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-172 |
| Category | Systemic blind spot — an entire dimension of the operator's own stated directive is absent from the plan meant to execute it, and nothing in the plan's structure would surface the omission to a session working it box by box. |
| What was missed | `02_ARCHITECTURE_DESIGN/COVERAGE_TARGET_MATRIX.md` states the operator's directive plainly: cover moneyline, spread/run line, totals, and team totals **across all five execution bands**. `04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 (verified directly this session, lines 152-207) build exactly one axis of that: market-type registry generalization (Phase 1), a team-level forecasting model gated on NB/Poisson EXP-013/2.x falsification tests (Phase 2), per-family segmented pools/ledgers/kill switches/oracles (Phase 3), and per-family shadow-mode activation (Phase 4). **No box in any of the four phases proposes activating T2, T3, or T5, or reactivating T1.** Verified directly against `src/prediction_market_bot/execution_bands.py` (`BAND_CONFIGS`) and `exp_output/T323-POWER-CALC-AFTER/power_calc_results.json` rather than trusting a pasted figure: T1 `kelly_fraction=0.0` (ADR-0048), `clean_n=0`, `raw_n=466` — zeroed on ruin-geometry grounds (GG-135), reactivation is an unstaffed operator decision (GG-153); T2 `kelly_fraction=0.0`, `raw_n=2` — effectively never traded; T3 `kelly_fraction=0.0`, `raw_n=0` — never traded at all; T5 `phase_active="Phase 8"`, never built or traded for either sport, gated on EXP-018 which is `Status: PENDING` (registered 2026-06-04, no paper data yet). Even a fully executed Phases 1-4 therefore delivers, at best, coverage of 4-5 market types × **one** band (T4) — not the five-band directive the coverage matrix states. |
| When it should have been caught | When `COVERAGE_TARGET_MATRIX.md` was written and cross-read against the existing phase plan — the matrix's own "How the phases map to the matrix" section already states this in its own text ("The band dimension is currently unowned... That is a gap in the phase plan itself and should be registered") but nothing had formally registered it in `GOVERNANCE_GAP_LOG.md` until this session. |
| Phases it survived | Phase 0 (market survey/ticker confirmation/depth measurement, ✅ per the matrix) through the current pre-Phase-1 state. Multiple sessions worked Phase 1 boxes in this window (T-427 replay-determinism audit, T-436 depth re-check, T-439 market-type registry, T-440 replay-harness rerun) without the band-dimension gap being registered, because none of those tasks' scope required reading the plan against the coverage matrix as a whole — each worked one box in isolation. |
| Why it survived | The phase plan's own structure is organized entirely around the market-type axis (registry → model → segmented pools → activation); there is no "band" heading or box anywhere in Phases 1-4 that would prompt a reader tracking box-by-box completion to ask "which band does this activate." A plan can be 100% internally consistent and fully executable while silently covering only one axis of a two-axis directive — nothing about reading the plan in isolation reveals the missing axis; it only becomes visible by holding the plan next to the matrix, which is exactly what this session's required-reading order (matrix before plan) was designed to force. |
| Impact | If Phases 1-4 execute to full completion exactly as scoped today, the deliverable is 4 (or 5, including the existing player-prop cell) market types × T4 only. The operator's "all five bands" directive remains unaddressed: T1 needs an explicit operator decision to reactivate (GG-153, currently unstaffed) or stays permanently dead per this session's instruction; T2/T3 have no plan box proposing how to generate the volume they currently lack (raw_n=2 and raw_n=0 respectively); T5 has no build at all and its gating experiment (EXP-018) has not run. A team executing this plan faithfully to Phase 4 completion would reasonably believe "coverage" had been delivered while 4 of 5 bands remain untouched — a strategic-scope miss, not a data or code defect, which is why Severity is set HIGH rather than CRITICAL: nothing here risks live capital or corrupts data, but it is a real gap between the operator's stated goal and what the funded plan actually produces. |
| Discovery | T-441 (2026-08-12), tasked explicitly with reading `COVERAGE_TARGET_MATRIX.md` against `MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 and registering any band-dimension gap found; all cited figures (T1/T2/T3/T5 `kelly_fraction`/`raw_n`/`clean_n`/`phase_active`) verified directly against `execution_bands.py`, `power_calc_results.json`, and the EXP-018 experiment log rather than accepted from the task brief as given. |
| Resolution | Still not resolved by this entry — GG-172 remains OPEN. `03_DECISIONS/ADR-0053_market-type-band-composition.md` was amended and marked **ACCEPTED** (as amended) by T-448 (2026-08-14), reconciled against T-439's shipped `market_type_registry.py` (see the ADR's §6 for the reconciliation and accepted delta). That acceptance is the composition-design response to this gap — it gives the codebase a first-class (market_type, band) cell object with clean_n/n*, kill-switch, and RULED_OUT/SHADOW status fields to build toward — **but it is not this gap's closure.** ADR-0053 accepted six delta items (ledger `market_type` field, per-cell clean_n/n*, per-cell kill-switch state, SHADOW status, RULED_OUT promotion guard, and naming — not building — the cross-family correlation group); none of those items are band-activation boxes, and ADR-0053 explicitly declines to add any to `MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4. The actual gap this entry names — no plan box proposes reactivating T1, generating T2/T3 volume, or building T5 — is unchanged and remains an open operator decision, tracked in the coverage matrix's own "Open questions for the operator" §2. |
| Status | OPEN. |

</details>

---

### GG-174 — `PolymarketVenueAdapter._parse_market()`'s CLOB query hardcodes `"tag": "nba"` (KI-019), unconfirmed against Polymarket's real tag taxonomy, and silently returns an empty market set for any other value

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** venue_adapter.py:350 still hardcodes "tag": "nba" (KI-019); path dormant until Polymarket KYC. **Next:** Confirm Polymarket tag taxonomy before activation.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-174 |
| Category | Architectural placeholder — an unverified literal sitting on a dormant, not-yet-activated code path. |
| What was missed | `src/prediction_market_bot/c5_execution/venue_adapter.py:257`, inside `PolymarketVenueAdapter`'s CLOB query params: `"tag": "nba",  # KI-019 — Polymarket NBA tag unconfirmed until T-077`. The value has never been confirmed against Polymarket's actual tag taxonomy. If it is wrong, the query returns an empty market set with no error — `ok=True`, zero markets — which is indistinguishable from "no NBA markets currently open" at every calling layer above it. |
| When it should have been caught | Before Polymarket activation (T-077, gated on operator KYC) — this is pre-existing, known (KI-019), and was already dormant/flagged before this session; re-surfaced here per T-442's explicit instruction to register rather than fix any out-of-scope finding touched during Box 1.2 (VenueAdapter generalization). |
| Phases it survived | Dormant since Polymarket's `VenueAdapter` implementation was first written — Polymarket is Secondary/KYC-gated per CLAUDE.md's venue map and has never been live-activated, so this literal has never been exercised against real traffic. |
| Why it survived | No test exercises `PolymarketVenueAdapter` against a live or recorded Polymarket response; the class exists as infrastructure-built-ahead-of-activation. A silent empty-result failure mode has no signal to trip until the venue is actually turned on. |
| Impact | None today (T4M-PROJ/Kalshi is the only live venue; Polymarket is inert). At T-077 activation, if the tag is wrong, `PolymarketVenueAdapter.fetch_player_points_markets()` / the new general `fetch_markets()` (T-442, Box 1.2) will silently report zero available markets rather than erroring — a silent-empty-result footgun, not a crash, so it could pass casual smoke-testing at activation time undetected. |
| Discovery | T-442 (2026-08-13), Box 1.2 (VenueAdapter generalization) — found while reading `venue_adapter.py` in full to generalize `fetch_player_points_markets()` off "player points" onto the market-type registry. Out of T-442's declared scope (abstraction repair only); registered and not touched, per Hard Rule 11 and the task's explicit instruction. |
| Resolution | Not resolved by this entry — registration only. Fix belongs to T-077 (Polymarket KYC/activation): confirm the real tag value against Polymarket's live CLOB API before or at activation, replacing the hardcoded literal. |
| Status | OPEN. |

</details>

---

### GG-177 — `session_end_prep.sh`'s Step 0 SESSION_CLAIMS.md lookup matches on the worktree branch's timestamp, but `claim_session.sh` stamps its row at actual claim-command time — the two are seconds-to-minutes apart, so the exact-string match fails on effectively every session even when the claim genuinely exists

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** session_end_prep.sh:136 still does an exact-string match on the claim timestamp (grep -F). **Next:** Match on claim-row branch name instead of timestamp.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-177 |
| Category | Tooling false-negative — a session-health check whose match key is structurally guaranteed to miss real data. |
| What was missed | `scripts/session_end_prep.sh` (Step 0, section 6) derives its match key by extracting the `<timestamp>` component from the current branch name (`session/<timestamp>-<slug>`, set once at worktree creation by `new_session_worktree.sh`) and does an exact `grep -F` for that ISO string against `SESSION_CLAIMS.md`. But `claim_session.sh` runs as a separate, later command and stamps its own row with the wall-clock time *at claim-command execution*, not the branch-creation time — confirmed directly on T-448: branch timestamp `20260814T144527Z` vs. the actual claim row's timestamp `2026-08-14T14:45:50Z`, a 23-second gap. Any real gap between worktree creation and running `claim_session.sh` (the normal case — session-start protocol runs the guard and other Step 0 checks in between) makes the exact match fail, even though the claim row genuinely exists and is correctly attributed to this session by every other means (branch name, T-/GG- range, focus text). |
| When it should have been caught | Whenever `session_end_prep.sh` and `claim_session.sh` were both authored/changed and their timestamp-sourcing conventions diverged — no test or cross-check verifies the two scripts agree on what "this session's timestamp" means. |
| Phases it survived | Unknown how many sessions this has silently produced a false "not found" on since `session_end_prep.sh`'s Step 0 section 6 was introduced — this session (T-448) is the first one observed to have chased it down rather than reading the printed caveat and moving on. |
| Why it survived | The script's own output already hedges ("confirm claim_session.sh was run at start" — advisory phrasing, not an alarm), so a false negative reads as a mild reminder rather than a bug, and nothing forces a session to verify the claim row exists by other means (e.g. `git log` for the claim commit) before accepting the script's "not found." |
| Impact | Low — purely a false-negative in a health-check message, not a data-loss or concurrency risk (the actual GG-101/GG-082 protections — atomic append, worktree isolation, `check_id_collision.sh` — are unaffected). Could cause a future session to wrongly conclude `claim_session.sh` was skipped and re-run it, producing a harmless duplicate claim row for the same session rather than any destructive action. |
| Discovery | T-448 close-out (`/session-end`, 2026-08-14), while working through Step 0's mandatory pending-task list — the summary carried into this window flagged the mismatch as unresolved; directly reading `scripts/session_end_prep.sh` lines 126-148 confirmed the mechanism (branch-name timestamp vs. claim-command timestamp) rather than assuming the claim was actually missing. Confirmed via `grep` that the T-448 claim row exists in `SESSION_CLAIMS.md` (line 236) with the correct T-448/STANDARD content, ruling out an actually-skipped claim. |
| Resolution | Not resolved by this entry — registration only, per Hard Rule 11 (T-448's declared deliverable is ADR-0053 amendment/acceptance plus session-end close-out; fixing a separate script's matching logic is a distinct deliverable). Fix (when picked up): either have `claim_session.sh` accept and echo back the branch's own timestamp component so the two scripts share one source of truth, or loosen `session_end_prep.sh`'s match to a same-session-window heuristic (e.g. match on branch slug text, or any claim row within N minutes of branch creation) instead of exact string equality. |
| Status | OPEN. |

</details>

---

### GG-183 — Per-cell kill-switch state (ADR-0053 §2.3/§6.3 item 4) has a store and a resolution helper but is not wired into C4/C7's live kill-switch check

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Deliberate scoped deferral; no wiring of CellKillSwitchState into C4/C7 found. **Next:** Wire when a second cell goes live.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-183 |
| Category | Incremental architecture — a deliberate seam, not a defect, but must be tracked so it is not mistaken for a finished control. |
| What was missed | Nothing was missed; this is a scoped deferral. T-453 added `CellKillSwitchState`/`resolve_kill_switch_state()`/`halt_cell()` to `market_type_registry.py` per ADR-0053 §2.3, but explicitly did not rewire `risk.py`/C4/C7's live drawdown-based kill-switch check to resolve per-cell state before halting. Today one cell (T4M-PROJ) places live bets, so the gap has zero live consequence; it becomes load-bearing the moment a second cell goes ACTIVE, since C4's current check is implicitly band-scoped and would halt/not-halt across cells indiscriminately. |
| When it should have been caught | N/A — named as out of scope at task-assignment time (T-453's DO-NOT list: "DO NOT REWIRE C4/C7'S LIVE KILL-SWITCH PATH... Leave a seam, register the wiring as its own task"). |
| Phases it survived | N/A. |
| Why it survived | Explicit scope fence, not a governance failure. |
| Impact | None while only one cell is ACTIVE. Becomes real risk-control gap the moment a second `(MarketType, ExecutionBand)` cell is promoted to ACTIVE without this wiring landing first. |
| Discovery | Self-identified during T-453 (2026-08-15) per the task's own instruction to register the wiring as its own task. |
| Resolution | Not started. Future task: make C4/C7 resolve `(market_type, band)` for an incoming bet via `resolve_kill_switch_state()` before checking halt state, and call `halt_cell()` from whatever path currently trips the drawdown kill switch. |
| Status | OPEN |

</details>

---

### GG-184 — `open_position()`'s `market_type` parameter defaults silently; 100% of live call sites rely on the default rather than passing it explicitly

**Status:** PARTIALLY RESOLVED · **Severity:** LOW

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-184 |
| Category | Incremental architecture — a deliberate deferral, not a defect found in-session. |
| What was missed | Nothing was missed at write time; this is a scoped deferral. T-456 (ADR-0053 delta item 2) grepped every call site of `open_position(` in `src/` and `scripts/` and found zero of the 7 production call sites (`run_mlb_paper_trade.py`, `run_t4_mlb_live.py`, `run_t2_mlb_sameday.py`, `run_t4_live.py`, `run_paper_trade.py`, `t4_live_runner.py`, `scripts/replay_harness_t427.py`) pass `market_type=` explicitly — all rely on `paper_trader.py`'s `market_type or MarketType.MLB_PLAYER_PROP_HITS` silent default. Today this is harmless because the entire live ledger is single-market-type (T-456's empirical cross-validation: 100% `KXMLBHIT` across every band and pool), but the default becomes a silent mislabeling risk the moment a second market type goes live and any call site is missed when adding its explicit tag. |
| When it should have been caught | N/A — named out of scope at T-456 task-assignment time; making the parameter required touches 6+ call-site files, bigger than T-456's single-deliverable scope (Hard Rule 11). |
| Phases it survived | N/A. |
| Why it survived | Explicit scope fence, not a governance failure — T-456 implemented the non-fatal in-scope mitigation instead (a `market_type_defaulted` warning log fires whenever a caller passes `market_type=None`, so any future defaulting is visible in the audit trail without changing call-site behavior). |
| Impact | None today (single-market-type ledger). Becomes a real mislabeling risk once a second `MarketType` goes ACTIVE and any of the 7 call sites is not updated to pass it explicitly — the position would silently record the wrong cell. |
| Discovery | Self-identified during T-456 (2026-08-16) via exhaustive call-site grep. |
| Resolution | **2026-09-01 (T-509, ADR-0054(a) §8 item 4):** 1 of 7 call sites fixed — `scripts/replay_harness_t427.py`'s `replay_one()` now passes `market_type=` explicitly instead of relying on the silent default, with a regression test that fails against the old behavior. The fix stopped at this one call site per T-509's explicit scope fence (operator instruction: "STOP and report if [going further] would require changing a shared signature"); `open_position()`'s parameter itself is still optional/defaulted, so the other 6 call sites (`run_mlb_paper_trade.py`, `run_t4_mlb_live.py`, `run_t2_mlb_sameday.py`, `run_t4_live.py`, `run_paper_trade.py`, `t4_live_runner.py`) are unchanged and this gap is not closed. Remaining future task, unchanged: make `market_type` a required (non-defaulted) parameter on `open_position()`, update the other 6 call sites to pass it explicitly, remove the default and its warning log. |
| Status | OPEN |

</details>

---

### GG-185 — 532 closed T4M-PROJ epoch-12 positions carry a ticker-vs-`game_date` mismatch despite the GG-166 guard, which should have refused every one of them, being confirmed deployed and unconditional at their `resolved_at` time

**Status:** PARTIALLY RESOLVED · **Severity:** CRITICAL

**Strategic-review contradiction, 2026-08-19 (re-derived from `logs/t4_mlb_resolved_ledger.jsonl`, 2,948 rows, by recomputing the ticker-embedded date and comparing with the stored `game_date`):** the mismatch rate is a STEP FUNCTION, not a gradient, and the deploy gap is CONSTANT across both sides of the step. Per-epoch mismatch: epoch 1 = 0/124, epoch 2 = 0/122, epoch 3 = 0/699, epoch 6 = 0/158, epoch 7 = 0/184, epoch 8 = 0/942, epoch 12 = 532/719 (74.0%). Within epoch 12, by `game_date`: 2026-07-31 = 78 clean / 0 mismatched; 08-01 = 75/0; 08-02 = 7/0; 08-03 = 27/0; 08-04 through 08-07 = ZERO rows in either column (this is the GG-163 ESPN-403 outage, 2026-08-04T23:41Z, 43.5h+, independently visible in the ledger); 08-08 = 0/144; 08-09 = 0/121; 08-10 = 0/1; 08-11 = 0/139; 08-12 = 0/118; 08-13 = 0/6; 08-14 = 0/3. `resolved_at` windows: clean 2026-08-01 → 2026-08-07, mismatched 2026-08-09 → 2026-08-15. The guard was undeployed for BOTH cohorts, so guard absence explains why the defect was not DETECTED; it cannot explain why the defect STARTED, because a constant cannot produce a step change. The trigger is something in the post-GG-163-outage restart path that brought T4 back on 2026-08-08 and bound `game_date` differently than the pre-outage path did. Root-causing that restart path is registered as its own task (see Block D / T-471). Do not re-close this gap on the deploy-gap explanation alone.

**T-465 update (2026-08-18):** Root cause confirmed with direct evidence — NOT a logic bug, NOT a second write path, NOT a TOCTOU race (T-458 had ruled out "deploy lag" as a candidate but without checking the VPS's actual pull history; this session checked it directly and it is the answer). Commit `58b2eb6` (the GG-166 guard) was pushed to `origin/main` at 2026-08-07T05:37:38Z, ~11min after the VPS's last pre-gap pull (`687bf9e`, 05:26:27Z same day). The VPS then did not pull again until 2026-08-15T19:44:27Z — an 8.5-day deploy gap, confirmed via full VPS `git reflog` (569 entries, no cherry-picked date window). `git show 687bf9e:src/prediction_market_bot/run_resolve_mlb.py` contains 0 occurrences of `game_date_ticker_mismatch`; `git show 687bf9e:src/prediction_market_bot/run_t4_mlb_live.py` contains 0 occurrences of `_ticker_to_game_date`. The guard was never running during the gap — not bypassed, absent. 100% of the 532 closed positions' `resolved_at` timestamps fall strictly before the gap closed (532 before / 0 after), which is complete and sufficient explanation; "unconditional guard deployed" in this entry's own title was itself the wrong premise — it was deployed to `origin/main`, never to the VPS, until 2026-08-15. **Reconciliation with GG-170: same root cause, not two.** GG-185 does not have an independent mechanism — it is the resolve-path manifestation of the same corruption GG-170 tracks, gated by silent deploy cadence rather than by data-source instability alone. Fix (the actual bypass, not a second guard): `.claude/hooks/governance_scan.sh` gained a "VPS DEPLOY DRIFT (GG-185/T-465)" structural probe (auto-run every session via the governance hook) that diffs VPS deployed HEAD against `origin/main` and alarms loudly if any undeployed commit is >24h old — this makes deploy-currency itself a checked invariant instead of an unstated assumption. Assertion A (`assert_ledger_invariants.py`, `aid="A"`, `assert_A_ticker_date`) already fails loudly for new-epoch violations via a pre-existing `[GG-170 RECURRENCE]` stderr alarm (tagged GG-170/T-458 in code) without altering exit code (`--strict` remains off) — no change needed there. New out-of-scope findings split to **GG-189** (renumbered from GG-187 2026-08-19/T-468 to resolve an ID collision with T-466's GG-187; register-and-stop, Hard Rule 11): 46 stuck-open T4M-PROJ epoch-12 positions (100% mismatch rate, correctly refused by the now-current guard since 2026-08-16 but nothing corrects them yet — live capital, Kelly-relevant per ADR-0052 sec 2.3), 76 rejected-position epoch-12 mismatches (no capital impact, data hygiene only), and `t4_mlb_outcome_store.jsonl`'s coverage ceiling (ends 2026-08-03, zero coverage of the 2026-08-07–08-15 corruption window — blocks any backfill of the 532 closed positions).

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-185 |
| Category | Guard-bypass anomaly of unknown mechanism — sibling to GG-166/GG-170 (same T4M-PROJ epoch-12 ledger-trust surface) but distinct from both: GG-166 is the write-time `game_date` bug (fixed); GG-170 is the MLB Stats API's `gameLog` date-label instability (mitigated this session, T-458). This gap is neither — it is that the pre-existing, confirmed-deployed GG-166 read-time guard (`run_resolve_mlb.py` lines 474-502, `58b2eb6`, 2026-08-06) is not preventing the exact condition it checks for, in positions resolved strictly after its own deployment. |
| What was missed | T-458 (this session), while independently verifying the user's cited "654/719 = 91.0%" epoch-12 figure ahead of building GG-170's mitigation, found the correct closed-only rate is 532/719 = 74.0% (654 is an all-status-combined count: 532 closed + 46 open + 76 rejected). All 532 closed T4M-PROJ epoch-12 positions with a ticker-vs-`game_date` mismatch have `resolved_at` timestamps strictly after the GG-166 guard's confirmed VPS deployment (`git log` on the VPS shows `run_resolve_mlb.py` unchanged since `58b2eb6`, 2026-08-06 22:37:38 -0700) — meaning the guard was live and should have refused every one of these 532 resolutions, and did not. |
| When it should have been caught | Should have been caught by GG-166's own post-deployment monitoring, if any existed — it did not. Found only incidentally, as a side effect of T-458's independent figure-verification step for an unrelated task (GG-170 mitigation), not by any structural check. |
| Phases it survived | All resolutions since `58b2eb6` (2026-08-06) through at least 2026-08-17 (session date) — an unknown but non-trivial window, not yet bounded. |
| Why it survived | No monitoring or assertion currently checks whether the GG-166 guard's refusal condition is actually firing when its precondition is met; `assert_ledger_invariants.py`'s assertion A measures the mismatch's existence, not whether a guard that should prevent it is working. T-458 ruled out three candidate explanations (deploy lag; a second, unguarded path to `settle_position()` — confirmed `settle_position()` has a single caller; a ticker-regex parse failure on a spot-checked example, `KXMLBHIT-26AUG071940MINMIL-MINRLEWIS23-2`, which parses correctly to `2026-08-07`) without reaching a definitive root cause, and stopped further investigation per Hard Rule 11 (one session = one deliverable; T-458's deliverable was GG-170's mitigation, not this anomaly) and the session's explicit scope fence. |
| Impact | Directly bears on T4M-PROJ epoch-12 `clean_n` trustworthiness (GG-004/APR-0024) — the same governance surface as GG-166 and GG-170. Also means GG-166's guard cannot currently be trusted to be doing what its own governance-log entry claims it does for resolutions after its deployment date; that claim needs re-verification once this gap's root cause is found. Does not touch sizing, `kelly_fraction`, or the drawdown kill switch (out of T-458's scope; not evaluated for downstream effect here). |
| Discovery | T-458 (2026-08-17), incidental to independently verifying the operator's cited epoch-12 violation-rate figure before building GG-170's mitigation. |
| Resolution | Not started. Candidate next steps for a staffed follow-on: (1) instrument or trace `_resolve_pool()`'s GG-166 guard block directly against a handful of the 532 known-bad tickers to see whether the guard is being reached, evaluated, and behaving as its code reads, or whether some upstream state (e.g. the position's stored `game_date` already matching a *different*, also-wrong value by the time the guard runs) makes the guard's own check pass incorrectly; (2) check whether the ~1,220 `game_date_corrected_but_outcome_stale`-flagged positions from GG-166's own unstaffed follow-on migration interact with or explain this set — T-458 could not reconcile this cleanly with the guard's unconditional check logic in the time available and did not pursue it further. |
| Status | PARTIALLY RESOLVED 2026-08-19 (T-468) — the 2026-08-18 (T-465) root-cause claim below is necessary but not sufficient; see the strategic-review contradiction block above the table (step-function mismatch onset vs. constant deploy gap — root-causing the actual trigger is T-471). Original T-465 note: 8.5-day VPS deploy gap (2026-08-07T05:26:27Z–2026-08-15T19:44:27Z) meant the guard was never deployed to production during the window that produced these 532 rows, not a logic bypass. `governance_scan.sh` VPS-deploy-drift probe landed and is independently valuable regardless of this downgrade. Remaining populations (46 stuck-open, 76 rejected, outcome-store coverage gap) split to GG-189 (renumbered from GG-187, see GG-189 for why). |

</details>

---

### GG-186 — SESSION_CLAIMS.md closure rows for T-458 and T-460 asserted "CLOSED" from local branch/commit state alone, with no check that either branch had actually reached `origin/main` — 4th occurrence of the same pattern (T-456 x2, T-458, T-460)

**Status:** PARTIALLY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-186 |
| 2026-08-25 recurrence (T-486) | The "structurally impossible" claim in Resolution below is falsified: T-485 (2026-08-24/25) wrote a `SESSION_CLAIMS.md` CLOSED row for `session/20260824T233621Z-t485-adr0057-g6-rescope` (tip `ba09980`/`64b8956`) asserting merge-landing, but `git merge-base --is-ancestor` from T-486's session confirmed the branch was NOT an ancestor of `origin/main` at that time — the branch and its PR #113 sat unmerged until T-486 resolved conflicts and landed it (merge commit `9f3b78ba1653a21744733e4deb678b5347470a45`). This is a 5th occurrence of the underlying pattern, not a new gap — the mechanism described in Resolution (generator-side merge-check gating the literal string "CLOSED") evidently was not exercised, bypassed, or hand-authored around in T-485's session; root cause not re-investigated here per Hard Rule 11 (out of T-486's declared scope). Re-open investigation is warranted before this can be called RESOLVED again — logged here per explicit task instruction rather than as a new GG number. |
| Category | Systemic blind spot — session-end's closure-row generator had no dependency on merge-landing at all; it read purely from the session's own `session-meta` block (local task_id/commit/summary), which is true regardless of whether that commit ever reached `origin/main`. |
| What was missed | `scripts/generate_session_artifacts.py`'s `generate_claims_closure_row()` wrote `CLOSED — ... (commit \`<local-sha>\`)` unconditionally, and — structurally worse — it runs at session-end Step 6-gen, which executes *before* Step 8 (push + merge). So even a fully correct session following the documented step order writes a "CLOSED" row before the merge that closure claims has happened. A window that then skipped, deferred, or failed Step 8 left a permanently-false "CLOSED" row with nothing to ever contradict it. |
| When it should have been caught | Should have been caught by Step 0c of the next session's session-start protocol (reading recent `SESSION_CLAIMS.md` rows) — but a false "CLOSED" row is indistinguishable from a true one by inspection; the check that would catch it (does this commit exist in `origin/main`'s history?) was never run by anything. |
| Phases it survived | Every session-end since T-430 (2026-08-07) introduced the generated closure row — at minimum T-456 (twice), T-458, T-460 (2026-08-17), confirmed via this session's (T-462) direct verification: `git fetch` + `gh pr list` showed both T-458 (PR #83) and T-460 (PR #82) were in fact merged by session end (23:50:37Z and 23:46:51Z respectively), so this specific pair turned out to be a false alarm raised by a strategic review that ran before the merges landed — but the false alarm was only resolvable by manually re-deriving PR/merge-base state by hand, which is exactly the check that should have been automatic and wasn't. T-456's two prior occurrences (referenced in this session's task brief, not independently re-verified here per Hard Rule 11 scope) are the confirmed genuine cases. |
| Why it survived | The closure-row mechanism (T-430/GG-101/GG-082's write-once fix) solved the "closure row gets skipped by hand" problem but never asked "is the thing this row claims actually true." No executable assertion connected "wrote CLOSED" to "reached origin/main" — the two facts could drift apart freely, and did, repeatedly, because nothing made drift visible. |
| Impact | Every prior "CLOSED" row in `SESSION_CLAIMS.md` was self-reported with no verification backing it, which is exactly the failure mode Hard Rule 10/GG-101/GG-082 were built to prevent for git-state collisions generally — this is the same failure mode applied to status reporting instead of file writes. Downstream: the next session's Step 0c ("check for other live sessions") and any audit trusting `SESSION_CLAIMS.md` as ground truth for "is this task's work safe to build on" could act on a false premise. This session (T-462) burned real verification effort (SSH-free git/gh reconciliation) specifically because the row-vs-reality gap is not machine-checkable today. |
| Discovery | T-462 (2026-08-18), tasked directly with confirming or refuting a strategic review's claim that T-458/T-460 were unmerged; found the specific claim false (both were merged) but the *general* mechanism gap real and unaddressed — this GG registers the mechanism, not the specific (already-resolved-by-the-time-of-review) false alarm. |
| Resolution | Landed same session (T-462, this branch): (1) `scripts/session_end_timer.sh merge-check` — new subcommand, the named executable assertion (ADR-0052) running `git fetch origin main` + `git merge-base --is-ancestor HEAD origin/main`, printing `MERGE_CHECK: YES/NO`. (2) `generate_session_artifacts.py`'s `generate_claims_closure_row()` now calls the same check live and writes `CLOSED` only when it passes; otherwise writes `MERGED: NO — branch \`<name>\` awaiting merge — ...` — so a false "CLOSED" row can no longer be produced by the generator at all, only a true one or an honest "not yet." (3) `.claude/commands/session-end.md` Step 8 gained a mandatory "Step 8-confirm" sub-step: after the merge lands, re-run `merge-check` and append a second, confirming `CLOSED` row (append-only, matching `SESSION_CLAIMS.md`'s `merge=union` convention) — a window that skips this leaves the honest "MERGED: NO" row as its last word, which is visible to the next session's Step 0c scan instead of a silent false positive. **What makes a 5th occurrence structurally impossible, not merely less likely:** the string "CLOSED" can now only be written by code that just ran a live git check and got a passing result — there is no code path left that writes "CLOSED" from session-local state alone. A session would have to bypass the generator entirely (hand-author the row) to reproduce this gap, which is itself a violation of the write-once discipline (T-430) that predates and is independent of this fix. |
| Status | RESOLVED 2026-08-18 (T-462) — `session_end_timer.sh merge-check` + `generate_session_artifacts.py` truth-check + `session-end.md` Step 8-confirm, this branch. Not yet exercised by a real subsequent session-end (this session is doc/script-only, MICRO fast-path per Step 8) — first live use will be the next STANDARD session-end that runs Step 8-confirm for real; if it surfaces friction, amend in place rather than re-opening a duplicate gap. |
| 2026-08-27/28 resolution, instances #6/#7 (T-501) | T-499's 2026-08-27 sweep (`04_EXECUTION/ACTIVE_QUEUE.md` rows 7.2/8.2) had confirmed T-490 (`session/20260826T043303Z-t490-sport-axis-power-calc`, tip `9e95194`/superseded by `075c4ce`) and T-491 (`session/20260826T045905Z-t491-gg172-band-axis`, tip `554b67b`) as CLOSED-without-merge — the 6th and 7th occurrences of this gap's underlying pattern, left unlanded pending an explicit operator fast-forward-or-lapse call. That call was made 2026-08-27 (LAND BOTH). T-501 verified both docs-only (no `src/`, `scripts/`, `kelly_fraction`), merged them sequentially into a landing branch (`git merge --no-ff`, T-490 first then T-491), resolved the predicted append-order conflict in `DECISION_LOG.md`/`PLAN.md`/`TODO_NEXT.md`/`MEMORY_BANK.md` by keeping both branches' content (never dropping either), pushed, and fast-forward-landed onto `origin/main` (`3017ea5..b702256`). Post-push `git merge-base --is-ancestor` confirmed both tips are now ancestors of `origin/main`: T-490 (`075c4ce`) exit 0, T-491 (`554b67b`) exit 0. Instances #6 and #7 are RESOLVED. Root cause of the recurrence itself remains uninvestigated (out of T-501's declared scope, per Hard Rule 11) — a 9th instance (a stale "merged" claim on this same queue's own 6.1/T-487 row) was found by T-499 the same day and is being landed separately (T-500); this GG stays PARTIALLY RESOLVED, not RESOLVED, until the pattern's root cause is addressed rather than each instance being landed by hand. |
| 2026-09-01 Step 8-confirm live proof, first genuinely-blocked case (T-506) | T-504's session-end correctly used the GG-186-fixed generator: it wrote `MERGED: NO — branch ... awaiting merge` in `SESSION_CLAIMS.md` for `session/20260829T190245Z-t504-t4-subbuckets-game-markets` (PR #125) rather than a false `CLOSED`, because `gh pr merge` was in fact blocked. T-506 diagnosed the block as two independent things: (1) GitHub's own `mergeStateStatus: DIRTY`/`mergeable: CONFLICTING` — a true positive, origin/main had advanced past PR #125's branch tip; (2) Claude Code's auto-mode permission classifier, which blocked a `--force-with-lease` push needed to update the PR branch after a rebase fix — also a true positive on its own terms (force-push is a destructive op requiring explicit authorization), resolved by asking the operator, who authorized it. After the operator-authorized force-push, `gh pr view 125` showed `mergeStateStatus: CLEAN`/`mergeable: MERGEABLE`; `gh pr merge 125 --merge` succeeded (merge commit `7116c0d0b276e54ba346cd47bc40fa7b053f47dc`). Step 8-confirm then ran in the direction this GG's Resolution specifies — is the *landed work* an ancestor of `origin/main`, not the reverse (the direction Wave 11 got backwards, per the T-506 task brief) — `git merge-base --is-ancestor 86e1503 origin/main` → **exit 0**. This is the first live case where the Step 8-confirm mechanism (built 2026-08-18, T-462) caught a branch that was genuinely, non-trivially blocked (not merely delayed by a session boundary) and confirmed its eventual real landing correctly. No new occurrence of the underlying pattern (false CLOSED claim) — the mechanism worked as designed. Root cause of the broader recurrence (why sessions keep reaching for local-state-only closure claims in the first place) remains uninvestigated and out of T-506's declared scope (Hard Rule 11); GG-186 stays PARTIALLY RESOLVED. |
| 2026-09-01 landing of T-506's own remaining unmerged tail (T-511) | T-506's own branch (`session/20260901T002700Z-t506-land-t504-register-regex`) had itself been left unlanded past its own session boundary — the D1 merge onto `origin/main` (row above) covered only D1 (landing T-504's PR #125); D2 (APR-0033 register row / GG-227), D3 (negation-guard regression tests / GG-222 closure), and a documentation miscount-correction commit remained committed to the branch but never pushed onto `origin/main` itself, i.e. a further instance of this GG's underlying pattern — real work sitting on a session branch with no automatic guarantee it reaches `origin/main`. T-511 (this session) merged the branch's tip (`14ef94f`) into its own worktree branch (merge commit `0224437`, resolving one real content conflict in `DECISION_LOG.md` by combining both sides' independently-appended entries — no content dropped from either) and fast-forward-pushed directly onto `origin/main` (`538d5cd..0224437`). Step 8-confirm direction, run post-push: `git merge-base --is-ancestor 14ef94f origin/main` → **exit 0**. `check_register_parity.py` re-run from the pushed tree: still CLEAN (71 docs, 27 legacy-exempt, zero mismatches). `gg_id_uniqueness_check.py` re-run: OK, no duplicates. This instance is not evidence against the Step 8-confirm mechanism itself (it worked correctly when run) — it is evidence that a branch can sit fully committed and still not reach `origin/main` for an entire session's length with nothing surfacing it automatically until a later session's Step 0c happens to notice via `git branch -a`. GG-186 stays PARTIALLY RESOLVED; root cause (why landing is not itself an automatic, non-optional last step of every session-end) remains unaddressed and out of T-511's declared scope (Hard Rule 11). |
| 2026-09-03 landing of T-509 (ADR-0054(a) cell-awareness), verified before-and-after (T-514) | T-509 (`session/20260901T052401Z-t509-adr0054a-cell-awareness`, tip `bacd705`) sat unlanded since 2026-09-01 — a further instance of work committed to a session branch with no guarantee it reaches `origin/main`. T-514 (this session) checked landing status BEFORE acting, per this GG's own documented Step 8-confirm direction: `git merge-base --is-ancestor session/20260901T052401Z-t509-adr0054a-cell-awareness origin/main` → **exit 1** (not landed). Merged the branch's tip into this session's worktree branch (clean merge, `04_EXECUTION/SESSION_CLAIMS.md` the only auto-merged file, zero conflicts, `logic_epoch.py` confirmed untouched per the T-513/14.3 concurrent-ownership fence). Ran the full suite on the merged branch before pushing, per explicit task instruction not to land red work: `python3 -m pytest -q` → `3001 passed, 28 skipped, 2 warnings in 136.53s` — green, matching T-509's own previously-reported figure exactly. Checked for a blocking check/classifier before pushing: no `.git/hooks/` pre-push hook exists in this repo; `gh api repos/eignacio1/prediction-market-bot/branches/main/protection` → 403 (no branch protection available on this private, non-GitHub-Pro repo); no open PR existed for T-509 to be blocked by. Confirmed fast-forward safety (`git merge-base --is-ancestor origin/main HEAD` passed) and pushed directly: `git push origin HEAD:main` → `48c5eee..4723550`. Step 8-confirm direction, run post-push exactly as documented: `git merge-base --is-ancestor session/20260901T052401Z-t509-adr0054a-cell-awareness origin/main; echo exit=$?` → **exit=0**. This instance is further evidence the Step 8-confirm mechanism itself works correctly whenever actually run (T-509's own session apparently never ran it) — the recurring failure is still that landing is not a forced, automatic last step, so a fully green, fully committed branch can sit for a full session-length or more with nothing surfacing it until a later session's Step 0c/explicit task brief happens to check. GG-186 stays PARTIALLY RESOLVED; root cause unaddressed and out of T-514's declared scope (Hard Rule 11). |

</details>

---

### GG-187 — T2's gross-edge formula is known but epoch-conditional; unsafe to backfill into assert_ledger_invariants.py's flat multiplier

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** assert_ledger_invariants.py:109 still has only T1 and T4M-PROJ in GROSS_EDGE_VIG_MULTIPLIER; T2 reports NO_FORMULA. **Next:** Add epoch-conditional T2 formula.

<details><summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-187 |
| Category | Incremental architecture — a mechanism (`GROSS_EDGE_VIG_MULTIPLIER`) built flat/epoch-independent for T1 and T4M-PROJ does not extend safely to a band whose formula actually changed mid-ledger. |
| What was missed | `scripts/assert_ledger_invariants.py`'s assertion G (`assert_G_gross_edge_formula`) reports `NO_FORMULA` for band T2 — T2 has no entry in `GROSS_EDGE_VIG_MULTIPLIER`, so its gross-edge values are never checked against any formula. Unlike T1 and UNTAGGED (no known formula at all) or T4M-PROJ (stable formula, full coverage), T2's formula IS known and documented: APR-0028 (ACCEPTED, DS sign-off, T-373/GG-123) specifies full-vig pre-fix (`gross_edge = p_calibrated - mid - vig`) through `CURRENT_LOGIC_EPOCH` < 6, and half-vig post-fix (`gross_edge = p_calibrated - mid - vig*0.5`, matching T1's convention) from epoch 6 forward (commit `cc887e8`). |
| When it should have been caught | At the time APR-0028's fix landed (epoch bumped to 6, T-373/GG-123) — the epoch-conditional nature of the formula should have been carried into the ledger-assertion suite in the same change that fixed the underlying bug, not left as a downstream gap for a later coverage audit to find. |
| Phases it survived | Written pre-G6 (paper trading), survived APR-0028's own fix commit, survived the 2026-08-11 Q7/GG-166 ledger-integrity remediation pass (T-432/BLOCK B) that built assertion G itself, and survived until T-466's coverage audit (2026-08-18) made NO_FORMULA counts visible per-band for the first time. |
| Why it survived | `GROSS_EDGE_VIG_MULTIPLIER` is a flat `{band: float}` dict with no epoch dimension — the pattern that exists elsewhere in the same script for epoch-scoping (e.g. `ADR_0050_FLOOR`, `FEE_NET_EDGE_CLEAN_FLOOR`, both used as `logic_epoch >= floor` gates) was never applied to assertion G. T2's only 2 resolved ledger records (`POS-83946C4309`, `POS-A89B4E8868`, both `logic_epoch: 2`, entered 2026-07-05) are both pre-fix, so any naive flat backfill (`GROSS_EDGE_VIG_MULTIPLIER["T2"] = 1.0`) would score as clean against currently-existing data while being silently wrong — and would start firing false alarms — the moment T2 accrues its first post-epoch-6 resolved record, since that record would legitimately use the half-vig formula the flat entry doesn't know about. NO_FORMULA's own silent-pass framing (see this GG's sibling finding under T-466) meant the absence produced no signal either way until coverage was made structurally visible. |
| Impact | T2 currently has zero formula-level protection on gross_edge, same as before this finding — this GG does not change that; it registers why a naive fix was rejected rather than applied. A wrong (flat) assertion would have been strictly worse than the current honest gap: it would pass today, then generate false-positive alarms against genuinely-correct post-epoch-6 T2 records, training the reader to distrust or silence real alarms from this assertion. T2's current live registry status does not include any ACTIVE cell (confirm at time of any future T2 promotion), so this gap does not currently block the new ACTIVE-status formula-coverage gate landed this session (T-466) — but it will block a T2 promotion to ACTIVE the moment one is attempted, by design. |
| Discovery | T-466 (2026-08-18), tasked with making NO_FORMULA visible and gating ACTIVE status on formula coverage; investigated T1/T2 backfill feasibility per the task's explicit instruction to register rather than guess a formula, read APR-0028 in full, and directly verified both of T2's resolved records against the pre-fix formula by exact arithmetic. |
| Resolution | Not yet resolved. Two viable paths, neither built this session (explicitly out of scope — the task's DO NOT list bars changing any existing assertion's logic): (1) wait for T2 to accrue resolved records at `logic_epoch >= 6`, then backfill `GROSS_EDGE_VIG_MULTIPLIER["T2"] = 0.5` once there is real post-fix data to validate against (the pre-fix epoch-2 records would then need either exclusion or a floor, matching the `ADR_0050_FLOOR` pattern); or (2) build proper epoch-conditional support into assertion G generally (a `{band: [(epoch_floor, multiplier), ...]}` structure or similar), which is a shared-logic change affecting T1 and T4M-PROJ's code path too and should be scoped and reviewed as its own change, not folded into a coverage-visibility task. |
| Status | OPEN 2026-08-18 (T-466) — registered, not resolved. Blocks any future promotion of a T2 cell to `CellStatus.ACTIVE` under the gate landed this session (`market_type_registry.py::__post_init__`), by design — T2 is not in `BANDS_WITH_FORMULA_ASSERTIONS`. |

</details>

---

### GG-188 — T-463 (team runs-scored outcome store for archived `KXMLBTOTAL` game-events, Phase 2 unblock) was claimed and never implemented, closed, or explained; Phase 2 remains blocked exactly where HYP010's Finding 5 left it

**Status:** PARTIALLY RESOLVED · **Severity:** MEDIUM

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-188 |
| Category | Systemic blind spot — `SESSION_CLAIMS.md` has no mechanism that flags a claim row with no matching CLOSED row; a claim can be silently abandoned mid-session with zero signal. |
| What was missed | `SESSION_CLAIMS.md` (2026-08-18T04:46:53Z) records a claim: "T-463: team runs-scored outcome store for archived KXMLBTOTAL game-events (ingestion only, Phase 2 unblock) + market Brier by-product." The very next commit (`9bb9999`) and claim row belong to T-464, an unrelated CI task. No commit, file, test, or DECISION_LOG/GOVERNANCE_GAP_LOG entry for T-463 exists anywhere in `origin/main` history. T-467 (this session) verified directly: `grep -rn "T-463"` against `DECISION_LOG.md` and `GOVERNANCE_GAP_LOG.md` returns zero hits; no file matching `*outcome_store*`/`*runs_scored*`/`*KXMLBTOTAL*` postdating the claim timestamp exists; `mlb_team_stats_store.py` (the only `runs_scored`-adjacent file in the repo) predates T-463 by three sessions (T-181, `87ffa2a`). |
| When it should have been caught | At the next session-start after 2026-08-18T04:46:53Z — `session_guard.sh`'s "other sessions' recent claims" check surfaces open claim rows but does not distinguish an open claim with in-progress work from one that was silently dropped; nothing in Step 0 flags a claim with no CLOSED row after a full session-claim-cycle has elapsed. |
| Phases it survived | From claim time (2026-08-18T04:46:53Z) through T-464, T-465, and T-466's full sessions (2026-08-18 through 2026-08-19T00:17Z) — three subsequent sessions' worth of `session_guard.sh` runs, none of which flagged it. |
| Why it survived | `session_guard.sh`'s claim-tail check is a visibility aid (prints recent rows for human/model judgment), not an assertion — there is no automated check that every claim row is eventually followed by a CLOSED row for the same T-number within some bound. The gap was only found because T-467 was explicitly tasked (04_EXECUTION/ACTIVE_QUEUE.md Block J) with verifying T-463's landing before proceeding, per the operator's own note that "a strategic window could not confirm it." |
| Impact | Phase 2 (`04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md` § Phase 2, gate 2.3) remains exactly as blocked as HYP010's Finding 5 (`05_RESEARCH_EXPERIMENTS/HYP010_PHASE2_PREREGISTRATION_2026-08-15.md`, 2026-08-15) found it: no team run-total outcome source exists, all 64,969 archived `KXMLBTOTAL` price-archive rows remain `status: "active"` with no settlement captured, and the 214 archived game-events cannot be scored. No live-capital or sizing impact — Phase 2 is offline-only and has not reached any C4 sizing path. This session (T-467) does not build the fix; per its own scope fence (ADR-0054 is Phase 3, independent of Phase 2) it registers this and stops. |
| Discovery | T-467 (2026-08-19), Step 1 of its mandated task: verify T-463's landing before starting Phase 3's ADR-0054, per `04_EXECUTION/ACTIVE_QUEUE.md` Block J instruction to "say so plainly and STOP" if unlanded. |
| Resolution | Built and verified — 414-line `scripts/build_t4_totals_outcome_store.py` at `8541840`, plus a 239-row / 224-resolved output artifact produced 2026-08-18T05:04:59Z, landed by T-469 (2026-08-19, PR #91). GG-188's own evidence was not wrong, it was scoped wrong: it searched tracked files on `origin/main` at investigation time, and the deliverable lived on an unmerged branch (`session/20260818T044631Z-phase2-team-outcomes`) plus a gitignored log — both now confirmed by T-469 (`git merge-base --is-ancestor 8541840 origin/main`, direct row-count of the output JSONL) before landing. The remaining Phase 2 work is a gate-2.3 run against the 224 resolved game-events, not a rebuild. Separately, the same blind spot this entry's Category names produced a SECOND instance in the same ~30-hour window: T-465 (claimed 2026-08-18T23:38:45Z, work on branch `session/20260818T233821Z-gg185-guard-failure`) also sat without a CLOSED row for multiple session-claim cycles before reconciling — the category is not a one-off, and the automated claim-vs-CLOSED assertion (Block I, `04_EXECUTION/ACTIVE_QUEUE.md`) remains the actual fix. Consider whether `session_guard.sh` should warn on claim rows with no CLOSED row after N hours/sessions — not built here, out of this session's one-deliverable scope (Hard Rule 11). |
| Status | PARTIALLY RESOLVED — T-463's specific deliverable is landed and verified (PR #91, ancestor-confirmed on `origin/main`); Phase 2 gate 2.3 has not yet run against the 224 resolved game-events. The Category's systemic blind spot (claim row with no CLOSED row produces no signal) remains OPEN as a general finding — now evidenced twice (T-463, T-465) — and stays open until Block I ships the automated assertion. |

</details>

---

### GG-189 — T-465 register-and-stop: 46 stuck-open T4M-PROJ epoch-12 positions, 76 rejected-position mismatches, and outcome-store coverage gap block any GG-185/GG-170 backfill

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Three residual populations blocking backfill; not re-derived this session. **Next:** Clear the 46 stuck-open positions first.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-189 |
| Category | Three residual populations surfaced while root-causing GG-185 (T-465), out of that session's single-deliverable scope (Hard Rule 11) — registered, not fixed. |
| What was missed | (1) **46 stuck-open T4M-PROJ epoch-12 positions**, ticker-vs-`game_date` mismatch rate 100% (46/46) — since the deploy gap closed 2026-08-15T19:44:27Z, the now-current GG-166 guard correctly refuses to resolve these on every resolve-cron pass (138 logged `game_date_ticker_mismatch` warnings starting 2026-08-16), but nothing corrects their stored `game_date` in place, so they are permanently stuck open. Live capital exposure — Kelly/kill-switch relevant per ADR-0052 sec 2.3. (2) **76 rejected-position epoch-12 mismatches** — same defect family, no capital ever committed, data-hygiene only. (3) **`t4_mlb_outcome_store.jsonl` coverage ceiling** — date range 2026-07-02 through 2026-08-03 only; zero coverage of 2026-08-07–08-15, the exact window that produced GG-185's 532 corrupted closed rows, so 0/532 are currently re-derivable from it. |
| When it should have been caught | Should have been visible the first time the resolve cron began refusing the 46 (2026-08-16); no monitor currently distinguishes "guard correctly refusing, position stuck" from ordinary pending-resolution latency. |
| Phases it survived | 2026-08-16 through session date (2026-08-18), ~2 days for the stuck-open population; unknown, unbounded duration for the outcome-store coverage gap (present since the store's introduction, T-421). |
| Why it survived | No assertion checks "is this open position's guard-refusal condition permanent" vs. transient; no assertion checks outcome-store coverage against the ledger's active date range. |
| Impact | (1) is the highest-priority item — live paper capital sitting in positions that cannot resolve until fixed, directly read by C4 Kelly sizing and the drawdown kill switch (ADR-0052 sec 2.3). (2) and (3) are lower severity (no capital / blocks a not-yet-attempted backfill respectively). |
| Discovery | T-465 (2026-08-18), while root-causing GG-185; see that entry for full derivation. |
| Resolution | Not started — register-and-stop per Hard Rule 11. Candidate follow-on T-NNNs (not sized or claimed this session): (a) correct the 46 stuck-open positions' `game_date` in place using the same pattern as GG-166's 2026-08-07 one-shot backfill script (`scripts/correct_t4_game_dates.py`), then let the normal resolve cron pick them up — no outcome re-derivation required, comparatively low-risk/high-value; (b) extend `t4_mlb_outcome_store.jsonl` coverage into 2026-08-07–08-15 — prerequisite for any backfill of GG-185's 532 closed rows; (c) correct the 76 rejected-position mismatches, low priority. |
| Status | OPEN — unstaffed. (a) should be prioritized given live-capital/Kelly relevance. Renumbered from GG-187 to GG-189 on 2026-08-19 (T-468) to resolve an ID collision with T-466's GG-187 (T2 gross-edge formula), which landed on main first (GG-162 concurrent-claim collision, both sessions claimed within 12 seconds of each other) — content unchanged, only the Gap ID and header number were reassigned. |

</details>

---

### GG-192 — C4 tracks exposure at exactly two granularities (single bet-evaluation, whole portfolio) with nothing in between; a per-game correlation-group cap is a new grouping dimension, not a reuse of existing plumbing

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Per-game correlation-group cap still unbuilt (ADR-0054 s5.1 governs). **Next:** Build per-game exposure granularity in C4.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-192 |
| Category | Risk-engine architecture — a governance-surface gap. The substance was already found and stated in `ADR-0054` §5.1 (T-467, 2026-08-19) but existed only inside a PROPOSED document; this entry gives it a standing governance-log presence independent of that ADR's eventual status. |
| What was missed | Confirmed by direct grep of `src/prediction_market_bot/c4_risk_engine/risk.py`: `max_single_event_exposure_usd` (`_HARD_LIMITS`, line 135) resolves per call / per bet-evaluation — effectively per-ticker (CHECK 6, lines 736-737). Zero `game_key`/`correlat`/`per_game` hits anywhere in `risk.py` — no game-level or family-level grouping exists in `_compute_kelly_size()` or any CHECK. The only other exposure figure C4 consumes, `current_open_exposure_usd`, is supplied by `paper_trader.py::exposure_snapshot()` (~line 250) as a portfolio-wide sum across *all* open non-isolated positions, regardless of game or family. So exposure is tracked at exactly two granularities — single-event ($500) and whole-portfolio (ADR-0026 cap) — with nothing in between. Three correlated families on one game (e.g. `KXMLBTOTAL`/`KXMLBTEAMTOTAL`/`KXMLBHIT` on the same matchup) can each independently clear the edge gate and each independently clear the $500 single-event cap, producing ~$1,500 of exposure to one game outcome against a stated $500 per-event cap — the cap's intent is defeated by construction, not by a bug in its enforcement. |
| When it should have been caught | Design time for the per-event exposure cap (`_HARD_LIMITS`, dated 2026-05-29 per Q5/CLAUDE.md) — the cap was sized and named for a single-cell system and never revisited as a second grouping axis (family/game correlation) became a live architectural concern. |
| Phases it survived | Present since `_HARD_LIMITS`'s introduction; only surfaced as a named concern 2026-08-17 when the operator signed off ADR-0054 item (c) (correlated-exposure cap, GG-135 solvency framing). |
| Why it survived | `max_single_event_exposure_usd`'s name reads as if it already covers "one event," and at one ACTIVE cell (T4M-PROJ × MLB_PLAYER_PROP_HITS) there has never been a second correlated family live simultaneously to expose the gap empirically — no observed loss or near-miss triggered a review. The finding lived only inside `ADR-0054` §5.1, a PROPOSED document; nothing in the routine governance-scan surface (this log, `risk.py` itself) stated it independently, so if that ADR were superseded or narrowed before acceptance, the finding would leave no trace. |
| Impact | No live consequence today — one ACTIVE cell means no correlated grouping can currently occur. Becomes unsound the moment a second cell (a second market_type on an already-live band, e.g. MLB moneyline/totals) is promoted ACTIVE: correlated legs on the same game would silently stack past the intended per-event ceiling. Directly relevant to solvency (GG-135 framing), not edge. |
| Discovery | T-475 (2026-08-21), verifying `ADR-0054` §5.1's claim directly via `grep -n max_single_event_exposure_usd risk.py`, `grep -nic "game_key\|correlat\|per_event" risk.py` (zero hits), and `paper_trader.py::exposure_snapshot()` (portfolio-wide sum, confirmed). |
| Resolution | Not started — register-and-stop per Hard Rule 11 (out of T-475's one-deliverable scope, which was the ADR-0054 §5.2 amendment). `ADR-0054` §5.3-§5.4 already specifies the control shape (aggregate cap per game key, sized down not rejected, $1,000 provisional) as PROPOSED design; wiring it into `risk.py`/CHECK 6 is a Phase 3 box 3.7 follow-on, not performed here. |
| Status | OPEN — unstaffed. |

</details>

---

### GG-196 — Outage-window (08-04..08-07) sub-bucket of the repaired epoch-12 cohort shows anomalous P&L nearly matching the pre-repair corruption artifact

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** 2026-10-07 recompute from VPS t4_mlb_resolved_ledger.jsonl (4127 rows; T4M-PROJ epoch-12 WIN/LOSS n=1898): outage bucket game_date 08-04..08-07 n=153 mean pnl/bet +0.2751 (win 49.7%) vs pre-outage n=187 +0.0163 and post-outage n=1558 -0.0875; anomaly persists after repair, outcome-store accuracy for that window still unaudited. **Next:** Spot-check ~20 outage-window rows' outcome/actual_hits against box scores/Kalshi settlement (ADR-0071) to test the outcome-store reliability hypothesis.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-196 |
| Category | Measurement integrity — a sub-population inside a just-repaired dataset still looks anomalous even after the known corruption (GG-166-class date/outcome mismatch) is corrected. |
| What was missed | `ADR-0055` (T-477, 2026-08-20) pre-registered a dry-run repair of the 532 corrupted `logic_epoch`-12 closed positions and, per its own §5 pre-registered suspicion threshold (+0.15/bet), found that while the **pooled** repaired cohort (n=719, mean +0.0652/bet) does not cross it, the **outage/transition sub-bucket** (`game_date` 2026-08-04..08-07, n=144) does: mean +0.3037/bet, SE 0.1382, win rate 50.7% — nearly identical to the pre-repair corrupted-population artifact figure (+0.3085/bet) that this whole repair exists to correct away from, and well above both the pre-outage clean anchor (+0.0163) and the post-outage bucket (+0.0002). |
| When it should have been caught | This session (T-477), which is why it is being registered now rather than left for a later session to rediscover. |
| Phases it survived | N/A — newly surfaced by this session's dry-run; not a previously-known gap. |
| Why it survived | The repair rule (ADR-0055 §2) corrects `game_date` and re-derives `outcome`/`pnl` from the T-421 decoupled outcome store, but assumes the outcome store itself is uniformly reliable across all dates. The 08-04..08-07 window is exactly the GG-163 ESPN-403 outage window, and its outcome-store coverage was the most recently and narrowly backfilled part of T-470's 2026-08-20 extension — plausible that the store's own resolution accuracy is not uniform across that specific window, which the repair's assertions (STEP 2, all passed) do not test for. |
| Impact | Medium — does not affect live capital or sizing directly (this repair is a dry run only, nothing has been written to the production ledger), but if the in-place repair (D1) is authorized before this is investigated, a real bias could be baked into the corrected ledger under the appearance of a clean fix. Also directly affects how much weight epoch 12's edge question (separate from this repair, per ADR-0055 §6) should give to games played during that window. |
| Discovery | T-477 (2026-08-20), `scripts/t477_dryrun_epoch12_repair.py` STEP-3 regime-boundary split, computed per ADR-0055 §4's pre-registered (not post-hoc) date-boundary definition. |
| Resolution | Not started — register-and-stop per Hard Rule 11 (out of T-477's one-deliverable scope, which was pre-registration + dry-run, not investigation of an anomaly the dry-run surfaces). Candidate follow-on: audit the outcome store's `t4_mlb_outcome_store.jsonl` records specifically for `game_date` 2026-08-04 through 08-07 against a fresh independent source, before D1 (ADR-0055 §7) is decided. |
| Status | OPEN — unstaffed. |

</details>

---

### GG-190 — T-471: the step-function onset of GG-185's game_date corruption (0/77 mismatched under commit `cbd09ae`, 532/532 under `687bf9e`) is not explained by any source-code, deploy, or environment difference found between the two commits — root cause NOT found, evidence bounded and next steps specified

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Root cause NOT found per entry; no new evidence this session. **Next:** Run the entry's specified next steps.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-190 |
| Category | Unresolved anomaly — sibling to GG-166/GG-170/GG-185 (same T4M-PROJ epoch-12 ledger-trust surface). GG-185's 2026-08-19 strategic review found the 8.5-day VPS deploy gap (T-465's root cause) cannot alone explain a step function, since guard-absence is constant across both the clean and corrupted cohorts. T-471 was tasked with finding the actual write-time trigger. It was not found within session budget; this entry records what was ruled out and what remains untested. |
| What was missed | The precise mechanism by which two runtime windows — `cbd09ae` (deployed 2026-08-02T00:07:26Z, confirmed running through its last stop 2026-08-07T05:06:04Z) and `687bf9e` (deployed 2026-08-07T05:26:30Z, confirmed running continuously with no restart through at least 2026-08-10) — produce categorically different midnight-crosser correctness under `git diff --stat`-confirmed byte-identical `game_date` write-path code (`run_t4_mlb_live.py`'s unconditional, unguarded UTC-rollover reassignment at the in-loop `if today != _eval_date:` block, flowing unscoped into `_run_cycle(..., game_date=game_date, ...)` and thence into `trader.open_position(..., game_date=game_date, ...)`; `paper_trader.py` fully unchanged between the two commits). Precisely time-boxed query against `logs/t4_mlb_resolved_ledger.jsonl` (2,948 rows): `cbd09ae` window = 77 midnight-crossing positions, 77/77 correctly ticker-matched (including writes 1-3+ hours after that day's rollover fired, e.g. 2026-08-04T03:28:17 for a 2026-08-03 game); `687bf9e` window = 532 midnight-crossing positions, 0/532 correctly matched. `t4_mlb_live_cron.log` confirms the rollover fired with comparable carry-over magnitude (1-15 live games carried over) in BOTH windows (08-02, 08-03, 08-04 under `cbd09ae`; 08-08 through 08-15 under `687bf9e`), ruling out "a carry-over event occurred" as the sole discriminator. |
| When it should have been caught | Should have been caught by GG-185's own T-465 root-cause pass (2026-08-18), which stopped at "guard was undeployed" without checking whether the underlying corruption mechanism itself was constant or variable across the deploy boundary — a gap the 2026-08-19 strategic review (recorded in GG-185's entry above) surfaced but did not close, tasking T-471 (this entry) to close it. |
| Phases it survived | The full `687bf9e` deployment window, 2026-08-07T05:26:30Z through at least 2026-08-15T19:44:27Z (when `58b2eb6`'s guard finally landed) — undetected as a *mechanism* question (as opposed to GG-185's already-known *symptom*) for T-465's entire investigation and this session's investigation up to the point of write-up. |
| Why it survived | No test or assertion compares write-path behavior across deploy boundaries when source code is unchanged — `assert_ledger_invariants.py`'s assertion A detects the mismatch's existence but has no mechanism to explain a rate change under identical code. The paradox only becomes visible when crosser rows are time-boxed precisely to actual VPS deploy timestamps (established via `journalctl`) rather than loosely bucketed by calendar date — an earlier pass in this same session used loose bucketing and produced a misleading result by inadvertently pooling in a third, older, pre-GG-081/082 code era (the July TBJCAMINERO13 double-fire window, which predates and motivated `_game_date_window()`'s creation and is not comparable to either `cbd09ae` or `687bf9e`). |
| Impact | Same as GG-185: directly bears on T4M-PROJ epoch-12 `clean_n` trustworthiness (GG-004/APR-0024). Additionally: because the corruption's actual runtime trigger is unidentified, there is no assurance that redeploying `58b2eb6`'s guard alone prevents recurrence if the same unknown runtime condition reoccurs — the guard refuses mismatched writes but does not explain why they occur, so a monitoring gap remains even with the guard live. |
| Discovery | T-471 (2026-08-19/2026-08-20 session), tasked directly with root-causing GG-185's step-function trigger. Investigation ruled out, with direct evidence: (1) VPS system timezone/clock (`timedatectl` confirms `Etc/UTC`, matches `date.today()`); (2) a `t4-mlb.service` systemd restart at the corruption onset (`journalctl` shows zero restart events between the `687bf9e` deploy, 2026-08-07T05:26:30Z, and at least 2026-08-10 — the process ran continuously through the entire 08-08 onset); (3) `paper_trader.py` source differences (`git diff --stat cbd09ae 687bf9e -- src/` shows the file untouched — only `run_t4_mlb_live.py` [ESPN UA header, 5 insertions/1 deletion, `_run_cycle`'s body included since it is confirmed to live in this same file with no other diff] and `run_resolve_mlb.py` changed between the two commits); (4) `run_resolve_mlb.py`'s ESPN User-Agent fix as a contributor (confirmed the resolve path only reads and carries forward the already-stored open-time `game_date` value — `pos.get("game_date", "")` — and does not independently derive or overwrite it; the GG-166 mismatch-refusal guard did not exist in either commit). None of these four explains the observed 0%-vs-100% step. The two untested leads, not pursued due to STANDARD-tier/one-deliverable session budget: (a) diffing `paper_portfolio_mlb_t4.pre_gg166_correction_20260807T052850Z.json` (a portfolio-state backup on the VPS, timestamped ~2 minutes after the `687bf9e` deploy — its filename suggests an anticipated game_date correction was already in view at that moment) against contemporaneous live portfolio state, to check for a persisted-runtime-state trigger rather than a source-code one; (b) directly instrumenting (in a future, code-permitted session) the live value of `game_date` immediately before `trader.open_position()` for one corrupted `687bf9e`-era write and one correct `cbd09ae`-era write, to catch the discriminating state directly rather than by source inference. |
| Resolution | Not started — root cause not found. This is an explicit, bounded negative result per this task's own stated allowance. Candidate next steps for a staffed follow-on, in priority order: (1) diff the `pre_gg166_correction_20260807T052850Z.json` portfolio backup against live state at that timestamp; (2) instrument `game_date`'s value at the `trader.open_position()` call site for a live comparison pair (requires a code change — out of scope for a read-only investigation session); (3) if neither surfaces a mechanism, escalate to treating this as accepted residual risk on the guard (`58b2eb6`, deployed and confirmed unconditional since 2026-08-16) rather than a fully explained incident. |
| Status | OPEN — unstaffed. Does NOT resolve GG-185; GG-185 remains PARTIALLY RESOLVED (T-465's deploy-gap finding stands as a necessary-but-insufficient explanation, per that entry's own 2026-08-19 strategic-review note) since this session did not find the actual trigger, only bounded what it is not. |

</details>

</details>

---

### GG-202 — T4's 45s poll cadence was tuned against MLB/NBA's near-continuous state progression; NFL's drive-level, dead-period-clustered structure breaks that assumption, and NFL game markets sit at the efficient end of the venue's own gradient

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** POLL_INTERVAL_S is still 45 for MLB (run_t4_mlb_live.py:151); NFL not live. **Next:** Decide NFL cadence before any NFL T4 work.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-202 |
| Category | Architecture / unverified cross-sport assumption — a hardcoded constant carries an implicit design premise that does not hold for the new sport. |
| What was missed | `POLL_INTERVAL_S = 45` is hardcoded identically in `src/prediction_market_bot/run_t4_mlb_live.py:151` and `src/prediction_market_bot/run_t4_live.py:259` (NBA), with `_FRESHNESS_WINDOW_S = 2.0 * POLL_INTERVAL_S` (90s) as the staleness-detection window in the MLB runner. Both were tuned against a game structure where the live state advances in a roughly continuous stream (MLB: pitch-by-pitch/at-bat progression within each half-inning; NBA: possession-by-possession scoring). NFL's structure is fundamentally bursty instead: plays cluster in ~25-40s snap-to-whistle windows separated by long dead periods (the play clock, two-minute warnings, timeouts, ~12+ minute halftime, quarter breaks) — a live NFL broadcast averages on the order of ~11 minutes of actual ball-in-play time across a ~3-hour game. A fixed 45s poll against this structure has two compounding failure modes: (1) most cycles land inside a dead period and evaluate against unchanged state — wasted evaluations, not a correctness bug but a throughput/architecture mismatch; (2) a state-changing play (a big gain, a turnover, a score) resolves in seconds, so the market has a multi-second-to-tens-of-seconds window to reprice before the next poll even lands, and 45s does not obviously beat that. Separately, and compounding rather than duplicating this: `CLAUDE.md`'s own "Market efficiency gradient" section states the T4 latency thesis is designed to exploit *inefficient* markets (thin MLB mid-week books), and explicitly names NFL/NBA-Finals-caliber markets as the *maximally* efficient, most-attended end of that same gradient — professional in-game win-probability feeds and sportsbooks are known to reprice within seconds of a scoring play in exactly this market class. Both concerns point the same direction: the 45s constant is not just unvalidated for NFL, it is unvalidated in the specific direction that would matter if the thesis is wrong for NFL. |
| When it should have been caught | Before any NFL T4 sub-band work is proposed or budgeted — this is a precondition on T4 activation for NFL, not a post-hoc tuning question. |
| Phases it survived | N/A — first NFL-facing session (T-474); the constant itself has never been sport-parameterized or revisited since its MLB/NBA introduction. |
| Why it survived | `POLL_INTERVAL_S` was set once per sport's live runner at build time from whatever cadence "felt right" for that sport's live-state granularity (not derived from a measured distributional analysis of state-change inter-arrival times in either case, as far as this session found); no cross-sport review process exists that would re-examine a sport-specific tuning constant when a new sport is added, because until this session no second sport had ever been added to T4 post-MLB. |
| Impact | Medium as currently scoped: no NFL T4 sub-band registry exists yet (ADR-0056 D2 names the future `T4NFL-` prefix but this session does not build it — Hard Rule 11), no NFL cell is above `NOT_IMPLEMENTED`, and `kelly_fraction` is 0.0 throughout, so nothing trades on this today. The impact is entirely forward-looking: if NFL T4 work is picked up later without addressing this, the sub-band would launch on an unvalidated and plausibly-wrong cadence assumption, in the one market class where CLAUDE.md's own efficiency-gradient section already predicts the weakest edge. |
| Discovery | T-474 (2026-08-21 session, NFL skeleton spike), Step 3 — explicit task instruction to probe the T4 cadence assumption against NFL's structure and register a gap if warranted; probe-only per Hard Rule 11 (no C1/C2/C3, no sub-band registry, no constant changed in this session). |
| Resolution | Not resolved. Two independent things would need to happen before NFL T4 is a reasonable proposal: (1) a measured (not assumed) distribution of NFL live-state-change inter-arrival times, analogous to what T-235/GG-080 did for MLB's per-game-day cycle throughput, to determine whether a fixed poll interval is even the right primitive for a bursty sport (an event-driven trigger on play-end, if obtainable from the data source, may fit better than any fixed interval); (2) an explicit operator read on whether NFL game markets' pricing speed leaves any latency window for a 45s-or-faster poller to exploit at all, given CLAUDE.md's own efficiency-gradient framing already predicts this is hostile territory. Until both are addressed, NFL T4 activation should be treated as blocked on this gap, not merely unbuilt. |
| Status | OPEN 2026-08-21 (T-474). |

</details>

---

### GG-203 — T4M-PROJ has approved zero bets to execution since 2026-08-15T00:06:20Z: every Kalshi order submission has failed, 1:1 with approvals, for 10 consecutive days, while every liveness signal in Step 4 short of the order-outcome audit trail reports healthy

**Status:** PARTIALLY RESOLVED (T-568 — first confirmed real fill) · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-203 |
| Category | Systemic blind spot — a live, correctly-evaluating process whose execution layer fails 100% of the time is invisible to every existing health probe except a manual read of the order-outcome audit trail itself. |
| What was missed | `logs/t4_mlb_resolved_ledger.jsonl` on the VPS (2948 rows) has no `entered_at` date past 2026-08-14 — the last row: `entered_at=2026-08-14T02:51:19.567Z`, `resolved_at=2026-08-15T06:38:14.727Z`, player Mike Trout, `POS-138C49EB9B`. A direct grep for `entered_at` dates 2026-08-15 through 2026-08-24 returns zero matches. Meanwhile `t4_mlb_cycle_log.jsonl` is writing in real time (last row at the moment of this check: `2026-08-24T23:28:13.939437+00:00`, age_hours=0) and `audit_mlb_t4.jsonl` is likewise writing in real time (last row `2026-08-24T23:28:13.945Z`, 353,531 total rows, growing daily: 758–32,214 rows/day through 08-24). `systemctl is-active t4-mlb` reports `active`; `NRestarts=0`. The process is alive, polling, and evaluating — it is not a GG-163-style silent death. The actual defect: since **2026-08-15T00:06:20.592Z** (first occurrence), every `risk_eval_approved` event in `audit_mlb_t4.jsonl` is followed by a `kalshi_order_failed` event, and the daily counts match exactly (08-15: 372/372, 08-16: 692/692, 08-17: 281/281, 08-18: 445/444, 08-19: 1056/1057, 08-20: 534/534, 08-21: 180/180, 08-22: 420/420, 08-23: 1212/1212, 08-24: 30/30 as of this check) — a 100% order-submission failure rate sustained for 10 days. Two distinct HTTP 404 error bodies observed: `{"error":{"code":"market_not_found","message":"market not found"}}` (first occurrence, 08-15T00:06:20Z, ticker `KXMLBHIT-26AUG141910SDCLE-SDJMERRILL3-1`) and `{"error":{"code":"user_not_found","message":"user not found"}}` (most recent occurrence at time of this check, 08-24T23:28:11Z, ticker `KXMLBHIT-26AUG241840TBDET-TBJCAMINERO13-1`) — both from `component: "C5-PAPER"`. Two different 404 reasons across the window suggests this may not be a single static misconfiguration but something shifting (credential/session state, or a market-lookup path that fails differently depending on ticker). `t4_position_trajectories.jsonl` is separately and far more severely stale — `mtime=Jun 24 21:11`, last 3 rows are synthetic `NBA_TEST_*`/`NBA_EXIT_TEST_*` rows from 2026-06-24, not MLB data at all; this file appears to have been abandoned as a live write target roughly two months before the order-failure incident began and is unrelated to it. |
| When it should have been caught | Immediately — CLAUDE.md Hard Rule 9 states design throughput is hundreds of evaluation rows per game-day; a 100% execution-layer failure rate producing zero net bets for 10 days against that expected throughput should have been caught by the next session-start Step 4 after 2026-08-15, but Step 4 had not been run for real in an unknown number of sessions (Cowork sessions cannot SSH — GG-154) until this session. |
| Phases it survived | Unknown number of sessions between 2026-08-15 and 2026-08-24 (this session) — Step 4 could not run under Cowork (GG-154), and no other check in the session-start protocol inspects order-execution outcomes; Step 4's own GG-163 probe (`t4_mlb_cycle_log.jsonl` write-recency) and the `systemctl is-active`/`NRestarts` checks all report healthy throughout this exact window, because none of them look past "is the process alive and cycling" into "is the process's output actually landing." |
| Why it survived | Every existing Step 4 probe checks *process liveness* (systemd state, restart count, cycle-log write-recency, staleness-halt recency) or *upstream data freshness* (`game_state_fresh`) — none of them check the *execution outcome* of an approved trade. A process can poll correctly, evaluate correctly, approve a position correctly, and still fail 100% of the time at the final `kalshi_order_failed` step while every upstream signal reports green. This is a structurally different blind spot from GG-163 (dead process) — it is a live process with a dead execution path. |
| Impact | High: T4M-PROJ — the sole ACTIVE-band MLB sub-band per CLAUDE.md's coverage framing — has contributed zero new resolved bets to the G6 sample-adequacy count for 10 consecutive days during active MLB season, with 5222+ approved-but-failed positions in that window representing signal the model found and the execution layer discarded. Any commercial-validation read (GG-004/APR-0024 n*) taken during this window undercounts real throughput and is measuring a broken pipe, not the strategy. |
| Discovery | T-482 (2026-08-24 session), running Step 4 for real for the first time since an unknown number of Cowork-only sessions (GG-154), per explicit operator instruction to determine whether T4M-PROJ has entered a bet since 2026-08-14; register-and-stop per Hard Rule 11 — root cause of the `market_not_found`/`user_not_found` 404s (credential rotation? market-discovery/ticker-resolution bug? Kalshi-side account state change?) is NOT diagnosed in this session. |
| Resolution | **T-492 (2026-08-25) — cause diagnosed, no in-repo fix applies.** Full by-day classification of every `kalshi_order_failed` payload in `audit_mlb_t4.jsonl` from first occurrence through 2026-08-25 (raw counts, `payload.error` string substring-matched): `08-15 {market_not_found:370, transient-retry-exceeded:2}` · `08-16 {market_not_found:691, ConnectionError:1}` · `08-17 {market_not_found:36, transient-retry-exceeded:1, HTTP403-Nevada-residents:244}` · `08-18 {HTTP403-Nevada-residents:331, market_not_found:103, transient-retry-exceeded:10}` · `08-19 {transient-retry-exceeded:47, market_not_found:1010}` · `08-20 {market_not_found:234, transient-retry-exceeded:3, user_not_found:297}` **← crossover day** · `08-21 {user_not_found:180}` · `08-22 {user_not_found:420}` · `08-23 {user_not_found:1212}` · `08-24 {user_not_found:33}` · `08-25 {user_not_found:489}`. This surfaces a THIRD, previously-undocumented error class not in the original record: `HTTP 403 Nevada_residents_are_not_currently_allowed_to_open_positions_in_Sports,_Elections_and_Entertainment`, concentrated 08-17/08-18 only (a Kalshi-side geo/compliance flag, transient) — bracketed on both sides by `market_not_found`, not correlated with any code deploy on our end. TASK 2 (credential/env hypothesis): `.env` and `VENUE_PRIVATE_KEY_PATH` (`/root/.ssh/kalshi_bot.pem`) both carry `mtime=Jul 14`, unchanged across the entire incident window — ruled out. `BOT_ENV=paper` confirmed live via `systemctl cat t4-mlb.service` and `.env`; GG-152's fail-loud fix verified intact (unrecognized `BOT_ENV` raises, unset defaults safely to demo) — ruled out. A live authenticated `GET /portfolio/balance` against demo with the deployed credentials succeeded (`balance_dollars: 399.4321`) — rules out a broken/deactivated account for read scope. TASK 3 (ticker/market resolution): the most recent actual failing ticker (`KXMLBHIT-26AUG242140PITSD-PITOCRUZ15-1`, failed `user_not_found` at 08-25T04:03:31Z) was fetched directly from demo via `GET /markets/{ticker}` and confirmed to exist, `status: active`, real live pricing — the market is real and open; `market_not_found`/`user_not_found` do not mean "market absent." T-472/GG-191 (deployed 2026-08-19T22:12:55-07:00, service didn't reload it until the 2026-08-20 window) was checked for a second ticker malformation on top of the refusal-only grammar: ruled out as a *cause* — the exact ticker Kalshi itself confirms is malformed-free (GET succeeds on it), and the file list touched by `994b4d3` never includes `kalshi_client.py`. TASK 4 (C5-PAPER live-path leak): ruled out — read `paper_trader.py`'s `open_position()` order-submission block directly; a failed Kalshi order is routed to `rejected_positions`, never `open_positions`, no capital/exposure impact, function returns early. The "submit to Kalshi demo per ADR-0008" comment confirms this is a deliberate demo-side validation step, not a live-capital leak. No register-and-stop needed for this sub-question. **Root cause, reproduced live just now:** the demo account can authenticate (`balance` GET succeeds) and read markets (`GET /markets/{ticker}` succeeds on real, open, active markets), but `POST /portfolio/events/orders` fails on **every** order attempted in this session — not just the historically-failing ticker, but a freshly-fetched, currently-open, non-MLB, unrelated-series ticker too (`KXMVECROSSCATEGORY-...`) — ruling out both a single-ticker and an MLB/KXMLBHIT-series-specific cause; this is account-wide on the order-write path specifically. A differential body-schema test (varying `side` across `bid/ask/yes/no/buy/sell` with and without `self_trade_prevention_type`) reproduced Kalshi's real Go-struct validation messages (`"CreateOrderV2Request.SelfTradePreventionType" required`, then `"side must be bid or ask"`) — confirming the production request body in `kalshi_client.py::submit_order()` is schema-correct (bid/ask mapping, required-field set) and passes all of Kalshi's own field validation; it fails at a downstream lookup stage regardless of side value, count, price, or ticker. Five identical repeated submissions against the same ticker returned the identical `not_found` code every time (not per-call noise), but different tickers/eras returned three genuinely different 404 bodies (`market_not_found` / `user_not_found` / generic `not_found`) for requests that are otherwise structurally identical and equally valid — this is Kalshi-side inconsistency in which internal service intercepts an otherwise-valid, schema-correct, auth-correct order first, not a defect traceable to this repo's ticker construction, environment routing, or credentials. **In one sentence: the Kalshi demo-sandbox order-write path (`POST /portfolio/events/orders`) is rejecting every schema-valid, auth-valid order this account submits, account-wide and ticker-independent, with three different non-diagnostic 404 codes across the window — an external Kalshi-side demo-account/order-service fault, not a bug in `kalshi_client.py`, `paper_trader.py`, ticker derivation, or deploy config.** No code change was made — none is indicated; the scope fence's "fix only if unambiguous and doesn't touch sizing" does not apply because there is nothing to fix on our side. **Recommended next action (operator-level, outside this session's scope):** contact Kalshi support with this reproduction (account/API-key ID, the three 404 bodies, and the fact that reads succeed but writes don't) and/or check the Kalshi demo dashboard directly for the account's order/trading-permission state; consider whether the demo API key needs regeneration. Re-run T4's own order path once Kalshi confirms a fix — do not assume resolved from our side alone. **Accrual lost: 10 full days (2026-08-15 through 2026-08-24) of zero T4M-PROJ execution, ~5,700+ approved-and-discarded positions across that window (source: `risk_eval_approved` vs `kalshi_order_failed` daily parity already recorded above), continuing into 08-25 as of this check** — this is external and not something an in-repo fix can stop; the loss continues until Kalshi-side account state is corrected. |
| Status | PARTIALLY RESOLVED 2026-08-25 (T-492) — root cause diagnosed unambiguously (external, Kalshi-side demo-account order-write fault); no in-repo code change applicable or made; remediation is operator-level (Kalshi support / demo API key), outside this repo's control. Re-open verification once Kalshi confirms account-side fix and orders resume succeeding. |
| T-547 addendum (2026-09-15, opened) | **Operator-authorized remediation begins.** Cost since T-492's diagnosis, measured 2026-09-15: last position entered 2026-08-14T03:33:45Z — 32 days at zero — while `rejected_positions` runs to 2026-09-15T00:06:27Z at ~1,600/day. Operator (Earl Ignacio) explicitly authorized account-side action: regenerate the demo API key, redeploy via the existing vault/env path only, restart t4-mlb for credential reload only, and open a Kalshi support request if that fails. Scope: one scoped t4-mlb restart, credential reload only — no other service restart, no sizing/kelly_fraction/settlement change, `kalshi_client.py`/`paper_trader.py`/ticker construction untouched per T-492's own ruled-out findings. Ordered plan: (1) confirm still broken today before changing anything; (2) read Kalshi demo dashboard account/permission/flag state before rotating anything; (3) rotate+deploy+reload only if (2) shows no account-level block; (4) escalate to Kalshi support with the reproduction in hand if (3) still fails; (5) build an alarm-only detector (`risk_eval_approved` vs `kalshi_order_failed` parity) wired into `.claude/hooks/governance_scan.sh` so a repeat of this exact blind spot is never silent again. Gated on Wave 25 block 25.1 (GG-271 ring-buffer activation) closing first, since both blocks restart t4-mlb — confirmed CLOSED on `origin/main` (T-548/GG-279, 2026-09-15T05:11:02Z) before this session proceeded. Security constraint carried forward from the operator's task instruction and honored throughout: no key or secret material is printed, echoed, logged, committed, or pasted anywhere, in whole or in part, including this log — vault/env only (Hard Rule 5). |
| Kalshi response received (2026-09-15, T-547) | **Kalshi support replied to D4's email. Full text: "Hi Earl, This behavior is expected in the demo environment. The demo can have data consistency gaps, and some order-write paths may fail even when reads (balance, market data) work normally. Because demo is a testing sandbox, it's periodically updated and may be temporarily unstable. When that happens, order placement can return errors even for newly created API keys, while other requests continue to succeed. Please let me know if this helps or if you have any further questions."** Preliminary read (full assessment and reply-back deferred to operator, not completed in this session): this is generic sandbox-instability boilerplate and does not engage with the specific reproduction sent in D4 — it does not explain (a) a 100% failure rate, (b) sustained continuously for 32 days (2026-08-15 through 2026-09-15), (c) reproduced identically, on the very first attempt, on a brand-new API key created minutes before testing (D3's key-rotation result, below), or (d) reads succeeding perfectly throughout while every write fails with one of four rotating non-diagnostic 404/error bodies. "Periodically unstable" does not describe a sustained, deterministic, 100%-reproducible-on-fresh-credentials fault. **D4 remains FILED, not CLOSED** — this reply does not constitute a fix or an adequate explanation; GG-203 remains IN PROGRESS. Operator elected to handle further correspondence with Kalshi directly, outside this session (2026-09-15). |
| D5 result (2026-09-15, T-547) | **Alarm-only order-write parity detector built and verified against known historical data.** `scripts/gg203_order_write_detector.py` (committed `01dcbc5`) compares `risk_eval_approved` against `kalshi_order_failed` counts per UTC day via SSH against the VPS's own `audit_mlb_t4.jsonl` (never pulled locally), alarming at ≥90% same-day failure rate — the exact GG-203 blind spot (100% write-layer failure while every liveness probe reported healthy) made structural instead of dependent on a session noticing by hand. Two implementation bugs found and fixed during build: (1) SSH argv-joining — passing the remote Python source as a separate `subprocess.run` argv item let SSH's own space-join of trailing arguments mangle a multi-line script into invalid remote shell commands; fixed by building one `shlex.quote()`-wrapped command string locally. (2) Wrong timestamp field name — the script initially filtered on `row.get('ts', '')`, which is only correct for the separate `t4_mlb_cycle_log.jsonl` file; `audit_mlb_t4.jsonl`'s actual field is `"timestamp"`, confirmed via direct inspection. Verified post-fix against two known dates: `--date 2026-08-20` (a documented incident day) correctly returns `risk_eval_approved=534 kalshi_order_failed=534 failure_rate=100.0%` and fires `*** GG-203-CLASS ALARM ***`; `--date 2026-08-01` (pre-incident, healthy) correctly returns `approved=85 failed=1 failure_rate=1.2%`, OK, no alarm. Wired into `.claude/hooks/governance_scan.sh` (committed `f4607d6`) as a new alarm-only section mirroring the existing ledger-invariants pattern — always exits 0, output surfaced on every session start, does not gate the hook. **D5 disposition: COMPLETE.** All five T-547 deliverables (D1-D5) are now done; GG-203 itself remains IN PROGRESS, not RESOLVED, pending a genuine Kalshi-side account fix and a real order actually succeeding — see the "Kalshi response received" row above for the current state of that escalation. |
| D4 result (2026-09-15, T-547) | **Support escalation filed via email (Kalshi's in-dashboard support-messenger button was non-functional; operator confirmed via direct testing).** Ticket text referenced the decisive fresh-key reproduction from the D3 key-rotation result below: new key `f3328cd1-c503-44a6-b97a-d4ef36912cce`, created minutes before testing, succeeds on `GET /portfolio/balance` and `GET /markets/{ticker}` but fails on its first-ever `POST /portfolio/events/orders` with the identical `insufficient_shard_balance`/"Exchange user not found... Exchange Sharding documentation" body the old, month-old key produced throughout the incident — ruling out credential age/corruption and pointing at an account-level exchange-user/sharding provisioning fault on Kalshi's side. Operator sent the email directly (not through this session's tooling — no external send capability was used or available); no ticket ID was issued since this went out as a plain email rather than through a ticketing system that returns one. **D4 disposition: FILED, awaiting Kalshi response.** GG-203 remains IN PROGRESS — not RESOLVED — until Kalshi confirms an account-side fix and a real order actually succeeds. Proceeding to D5 (alarm-only detector) per the T-547 addendum's ordered plan. |
| D3 key-rotation result (2026-09-15, T-547) | **Genuine key rotation performed — still fails, identically. Old key deleted by operator; superseded, do not use.** After the restart-only D3 attempt above still failed, the operator requested and performed a real key rotation. A brand-new 2048-bit RSA key pair was generated directly on the VPS via `openssl genrsa`/`openssl rsa -pubout` (private key never left the server, never printed/logged/pasted — Hard Rule 5 honored). Only the public key (non-secret) was relayed to the operator, who pasted it into Kalshi's "Create API key" dialog and created a new key, permissions Read all data + Full access, new key ID `f3328cd1-c503-44a6-b97a-d4ef36912cce` (identifier only, non-secret, per D4's own instruction). `.env` on the VPS updated: `VENUE_API_KEY` set to the new ID, `VENUE_PRIVATE_KEY_PATH` repointed to the new private key file; `.env` backed up before edit. `systemctl restart t4-mlb` executed to load it: `ActiveEnterTimestamp` moved `2026-09-15T05:45:01Z` → `2026-09-15T05:57:08Z`, new `MainPID=2547028` — genuine restart confirmed. D1's three calls re-run against the brand-new key: (1) `GET /portfolio/balance` → `ok=True` (`balance_usd: 397.44`) — succeeds. (2) `GET /markets/{ticker}` on a freshly-opened `KXMLBHIT` ticker (`KXMLBHIT-26SEP151840LADCIN-LADMBETTS50-4`, created `2026-09-15T05:32:19Z`, i.e. after the *previous* restart — a market this new key pair has never touched before) → `ok=True`, full detail returned — succeeds. (3) `POST /portfolio/events/orders` on that same ticker → `ok=False status=error error=HTTP 404: {"error":{"code":"insufficient_shard_balance","message":"insufficient shard balance","details":"Exchange user not found. For Predictions: reference documentation Exchange Sharding documentation."}}` — fails, with the exact same error body seen historically on the *old* key (first documented in D1's 09-12 through 09-15 classification, above). **This is the decisive result: a completely fresh API key/key-pair, created minutes ago, with full read+trade permissions, fails on its very first order attempt with the identical "Exchange user not found / Exchange Sharding" error the old key produced for weeks.** This conclusively rules out any explanation tied to the specific key material, credential age, or key corruption — the fault is tied to the Kalshi-side account/exchange-user record itself, not to any artifact under this repo's control. **The old key (`ff1a9c1b-3c1d-4617-8c60-9d78b0408259`) has been deleted by the operator on Kalshi's side and is no longer valid — do not reference it as active in any future session; the live key is `f3328cd1-c503-44a6-b97a-d4ef36912cce`.** Proceeding to D4 (Kalshi support escalation) with this strengthened evidence. |
| D2/D3 result (2026-09-15, T-547) | **D2 — no account-level block found; D3 — rotation/restart did NOT fix it, proceeding to D4.** D2: operator manually reviewed the Kalshi demo dashboard (Chrome was malware-infected per operator disclosure this session — all dashboard access routed through a trusted Safari session instead, no browser automation used). Account status: active, no deactivation/suspension banner, full profile intact (name/email/phone/address). Trading history/PnL present (2026 total PnL with fees: −$2,371.03 — real resolved trading activity, not a fresh/unused account). Tax documents (1099-INT/MISC/DA) present for 2024-2025 — further evidence of an established, non-restricted account. API keys on file: exactly one, "prediction markets bot", scope Read/Trade, created 2026-07-13 (predates the 2026-08-15 incident start by a month — this is the same key that has been failing throughout the entire incident window), key ID `ff1a9c1b-3c1d-4617-8c60-9d78b0408259` (identifier only, never a secret value, safe to record per D4's own instruction). No explicit geo/compliance-flag page was located (no standalone "identity verification/compliance status" UI was found under Account & Security, Documents, or Settings) — operator time-boxed further manual dashboard exploration; no Nevada-residents-style banner or restriction was observed anywhere reviewed, including when attempting to view live markets. Judgment call: no gross account-level suspension found, so proceeded to D3 rather than continuing an open-ended manual dashboard search — noted as a residual gap: a subtle account/compliance flag of the 2026-08-17/18 Nevada type would not necessarily surface as a banner, and cannot be affirmatively ruled out from dashboard review alone. D3: rather than generate a brand-new API key (the existing key already predates and spans the entire incident with no code/env change on our side per T-492's own credential-hypothesis ruleout), proceeded directly to the restart step, since a fresh key would not distinguish an account-side fault from a credential-side one any more cleanly than reusing the existing one — this is a narrowing of the original D3 plan (skipped literal key regeneration), justified by T-492 having already ruled out the credential/env hypothesis directly (`.env`/`VENUE_PRIVATE_KEY_PATH` both `mtime=Jul 14`, unchanged across the entire incident). `systemctl restart t4-mlb` executed: `ActiveEnterTimestamp` moved `2026-09-15T00:12:01Z` → `2026-09-15T05:45:01Z`, new `MainPID`, `ActiveState=active`/`SubState=running` confirmed post-restart. D1's three calls re-run immediately after: (1) `GET /portfolio/balance` → `ok=True` (`balance_usd: 397.44`) — succeeds. (2) `GET /markets/{ticker}` on a freshly-opened `KXMLBHIT` ticker (`KXMLBHIT-26SEP151840LADCIN-LADMBETTS50-4`, "Mookie Betts: 4+ hits?", `open_time: 2026-09-15T05:41:00Z` — opened after the restart, ruling out any pre-restart cache) → `ok=True`, full detail returned — succeeds. (3) `POST /portfolio/events/orders` on that same freshly-opened ticker → `ok=False status=error error=HTTP 404: {"error":{"code":"not_found","message":"not found"}}` — fails, identical generic-404 shape to one of D1's two results today. Restart changed nothing. **D3 disposition: FAILED — the fault survives a credential reload on a market that didn't even exist before the restart, closing off any remaining "stale process/cached session" explanation. Proceeding to D4 (Kalshi support escalation).** No sizing/kelly_fraction/settlement/ticker-construction code touched; only action taken was `systemctl restart t4-mlb` (in-scope per T-547 addendum) plus the read-only VPS-side probe script (created/run/deleted from `/tmp`, never committed). No key or secret material was printed, logged, committed, or pasted at any point in D2 or D3. |
| D1 result (2026-09-15, T-547) | **CONFIRMED STILL BROKEN TODAY — proceeding to D2, not stopping.** Three live calls run via SSH on the VPS (`.env`/`venv` already loaded there; no credential ever left the VPS, no secret printed) after independently re-verifying `BOT_ENV=='paper'` first: (1) `GET /portfolio/balance` → `ok=True`, `{balance_usd: 399.43, portfolio_value_usd: 0.0, balance_dollars: "399.4321"}` — succeeds. (2) `GET /markets/{ticker}` on two independently fetched, currently-open tickers (`KXMVECROSSCATEGORY-SHARD1-S2026C5317179888-67A3A80645E`, a non-MLB multivariate-shard market, and `KXMLBHIT-26SEP152140MIAAZ-MIAKSTOWERS28-3`, "Kyle Stowers: 3+ hits?") → both `ok=True`, full market detail returned, `status: "active"` — succeeds on both, ruling out ticker-family-specific staleness. (3) `POST /portfolio/events/orders` on each of those same two tickers (`side="yes"`, verified against `submit_order()`'s own docstring/signature before calling — not a malformed request) → both `ok=False status=error error=HTTP 404: {"error":{"code":"not_found","message":"not found"}}` — fails identically on two structurally unrelated ticker types (cross-category multivariate shard vs. single-leg MLB player prop), reconfirming account-wide/ticker-independent per T-492. Last-3-day `kalshi_order_failed` classification from `audit_mlb_t4.jsonl` (`event_type` field, not `event`; corrected script after an initial empty-result run against the wrong field name): **09-12: 2,955** (`insufficient_shard_balance`×2,953, `transient-retry-exceeded`×2) · **09-13: 1,584** (`insufficient_shard_balance`×1,584) · **09-14: 529** (`insufficient_shard_balance`×529) · **09-15 partial, through 04:46:35Z, last row in file: 1,081** (`insufficient_shard_balance`×1,081) — all 6,149 failures in this window are on `KXMLBHIT` tickers exclusively (single-family sample; today's own live probe above independently confirms the fault is not limited to that family). Full historical body (n=6,147 of 6,149, first-seen 2026-09-12T00:01:51.202Z): `{"error":{"code":"insufficient_shard_balance","message":"insufficient shard balance","details":"Exchange user not found. For Predictions: reference documentation Exchange Sharding documentation."}}` — a fourth distinct 404 body, beyond the three T-492 already logged (`market_not_found`, `user_not_found`, generic `not_found` reproduced live today), reconfirming Kalshi-side **rotating non-diagnostic bodies** rather than a fixed, debuggable error. Orders did **not** start succeeding — this remains a remediation, not a verification-of-fix. Proceeding to D2 (read account state before rotating anything). |
| T-556 operator-addendum diagnosis (2026-09-17, DIAGNOSIS ONLY, no code/config/credential change made) | **Kalshi support formally declined API support (2026-09-15, pointed to docs + Discord #dev), closing the support route and narrowly overriding the standing "do not re-investigate GG-203" rule for one session, one new line of inquiry: published V2 API semantics, which T-492 never had. T-492's ruled-out list (credentials, env routing, ticker construction, paper-trader live-path leak) was NOT re-run.** **ADDENDUM-1 (base URL):** `kalshi_client.py`'s `_KALSHI_DEMO_BASE_URL` constant reads `"https://external-api.demo.kalshi.co/trade-api/v2"`, character-for-character identical to the canonical string the operator cited from the docs — **ruled out**, not a superseded/stale host. **ADDENDUM-2 (schema diff, from the live spec pulled fresh via `curl https://docs.kalshi.com/openapi.yaml` on the VPS, not the truncated WebFetch read):** `CreateOrderV2Request`'s full `required:` list is `ticker, side, count, price, time_in_force, self_trade_prevention_type` — `submit_order()`'s actual request body sends all six; **no required field is missing.** There is **no `event_ticker` field anywhere in the schema** — the operator's "separate event-ticker field" concern is moot, not a defect; the bot's sole use of the market `ticker` field is spec-correct. Unsent *optional* fields: `expiration_time`, `post_only`, `cancel_order_on_pause`, `reduce_only`, `subaccount`, `order_group_id`, `exchange_index`. Documented response set for `CreateOrderV2` is `201, 400, 401, 403, 409, 429, 500, 503` — **404 is not a documented possible response for this endpoint at all**, confirmed twice independently against the pulled spec; every failure GG-203 has ever logged (`market_not_found`, `user_not_found`, generic `not_found`, `insufficient_shard_balance`) is a 404-class code outside the endpoint's own documented contract. **ADDENDUM-3 (balance-works/user_not_found reconciliation):** `GET /portfolio/balance` and `POST /portfolio/events/orders` are both authenticated calls and both route through the same `_kalshi_base_url()` (`BOT_ENV`-gated, i.e. both demo) — no host asymmetry between the read that works and the write that fails; the real asymmetry in this codebase is that market-*discovery* (`fetch_player_points_markets`, the three `_get(f"/markets/{ticker}")` call sites) defaults `authenticated=False` and therefore always resolves to production regardless of `BOT_ENV`, so the ticker/price data feeding every order write is production-sourced while the write itself is demo-routed — a real architectural asymmetry, not previously on T-492's list, though not obviously the failure mechanism by itself. The "ticker/market doesn't exist on demo" sub-theory was tested directly: `GET /trade-api/v2/markets?series_ticker=KXMLBHIT&status=open` run separately against `external-api.demo.kalshi.co` and `external-api.kalshi.com` (2026-09-17T05:13:20Z) both returned the same `event_ticker` (`KXMLBHIT-26SEP172138MINLAA`) as genuinely distinct per-host market instances (different `created_time`, different live pricing) with **identical `exchange_index: 3` on both hosts** — **this refutes "ticker doesn't exist on demo"** and confirms the shard index itself matches between environments for this series. Revised leading hypothesis, replacing "the bot is missing a required field" (which the schema itself contradicts — `exchange_index` is optional and documented to auto-route when `ticker` is provided, which it always is): either Kalshi's documented ticker-based auto-routing is not resolving correctly for this specific account, or there is an account-level exchange-user/shard-provisioning fault upstream of anything a client-side field could fix — consistent with, and sharpening, the `insufficient_shard_balance`/"Exchange user not found... Exchange Sharding documentation" error already on record (D1/D4, 2026-09-15). **ADDENDUM-4 (Discord #dev draft, NOT posted — for the operator to post):** *"Hi #dev — Kalshi support pointed me here. Account [redacted], demo environment. `POST /portfolio/events/orders` has failed 100% of orders for 33+ days (since 2026-08-15), while `GET /portfolio/balance` and `GET /markets/{ticker}` succeed throughout, including on freshly-opened tickers and a brand-new API key tested minutes after creation. Failures rotate through four non-diagnostic bodies over time: `market_not_found`, `user_not_found`, generic `not_found`, and (since 09-12) `insufficient_shard_balance` — 'Exchange user not found. For Predictions: reference documentation Exchange Sharding documentation.' Per the V2 OpenAPI spec, `CreateOrderV2`'s documented response codes are 201/400/401/403/409/429/500/503 — 404 isn't among them, so these don't look like documented validation failures. Our request body includes all six required fields (ticker, side, count, price, time_in_force, self_trade_prevention_type) and omits `exchange_index`, which the spec says should auto-route when `ticker` is provided. Demo and prod both show `exchange_index: 3` for the same series (KXMLBHIT), so the shard assignment looks consistent, not obviously mismatched. Is there a known issue with exchange-user/shard provisioning on demo accounts, or a case where ticker-based auto-routing doesn't resolve? Happy to share the account/key ID and full failure log in DM."* **No code, base URL, request body, or credential was changed in this session; no order was submitted against production or with real funds; the API key was not rotated again.** Recommended next step, explicitly not undertaken here: a future, separately-authorized fix-block should either (a) post the Discord draft above and await a Kalshi-side account/shard fix, or (b) test explicit non-default `exchange_index` values against demo as a diagnostic (not a presumed fix) in an isolated, non-production script — outside this diagnosis-only addendum's scope. |
| T-558 block opened (2026-09-17, DIAGNOSIS + CONDITIONAL FIX, operator-authorized narrow override of "do not re-investigate GG-203 in-repo," again) | **Acts on option (b) from T-556's own "recommended next step" row above, now with external corroboration T-556 did not have: an independent developer (BradSherwood24/degeneracy_v3, PR #9) hit the identical `market_not_found` symptom on Kalshi and fixed it by explicitly propagating `exchange_index` on order submission after finding it defaults to shard 0 when omitted -- the same field T-556's ADDENDUM-3 flagged as unsent-but-optional in this repo's own request body (`grep -c exchange_index src/prediction_market_bot/c5_execution/kalshi_client.py` = 0, not yet independently re-run this block per the ruled-out-list prohibition but consistent with T-556's own reading of `submit_order()`).** Working hypothesis: Kalshi's documented ticker-based shard auto-routing is not resolving for this account, `exchange_index` needs explicit client-side propagation, and/or shard-3 (Sports) collateral is unallocated separately from the shard-0 aggregate T-492's `balance_dollars: 399.4321` reported -- three faces of one root cause explaining the full rotating error set (`market_not_found` -> `user_not_found` -> `insufficient_shard_balance`, all read as "no exchange-user/balance record found under the shard actually being routed to"). Plan, in order: **D1** -- one isolated throwaway diagnostic script, VPS-side, demo-only, submits one order for a currently-open KXMLBHIT market twice (as-is today, then with the market's own `exchange_index` added) and captures both full request/response bodies; no bot code changed yet. **D2** -- read Get Balance's per-shard breakdown (not just aggregate) before concluding anything; if shard 3 is zero, report what the Intra Account Transfer API requires without moving funds (operator action only). **D3** -- implement `exchange_index` propagation in `kalshi_client.py` only if D1's second order succeeds where the first failed; capture-at-discovery, carry-on-order, refuse-to-dispatch-on-unknown (no silent default to 0), two tests. **D4** -- fix or register the `authenticated=False`-defaults-to-production market-discovery/demo-order-write asymmetry T-556's ADDENDUM-3 already surfaced but did not itself resolve. T-492's ruled-out list (base URL, request-schema required fields, credential/env routing, ticker construction, paper-trader live-path leak) is NOT re-run in this block. No order will be submitted against production or with real funds at any point; no funds will be moved between shards; the API key will not be rotated again. This row is the gap-log entry committed and pushed first, per this block's own instructions, before any diagnostic script is written. |
| T-558 D1/D2/D4 results (2026-09-17, DIAGNOSIS COMPLETE, no order succeeded, no code changed) | **D1 (VPS, demo only, isolated throwaway script, deleted after use) -- DECISIVE, but not the hypothesis expected:** one currently-open KXMLBHIT market (`KXMLBHIT-26SEP182140NYYAZ-AZNARENADO28-3`) was submitted twice via `POST /portfolio/events/orders` against demo, reusing the bot's own `_auth_headers`/`_kalshi_base_url()` (BOT_ENV=paper) so signing/routing exactly matched production code paths. (a) exactly as `submit_order()` builds it today (no `exchange_index`) -> `ok=False`, `HTTP 404 insufficient_shard_balance` / "Exchange user not found. For Predictions: reference documentation Exchange Sharding documentation." (b) identical body plus `exchange_index: 3` (read live from the market's own raw `/markets/{ticker}` record, which does carry the field -- confirmed present in the raw JSON: `market_raw['exchange_index'] == 3`) -> **same error, byte-for-byte identical body.** **Adding `exchange_index` made zero difference -- this kills the degeneracy_v3-style "client must propagate exchange_index" hypothesis specifically.** D3 is therefore explicitly NOT undertaken, per this block's own stated conditionality ("implement propagation only if D1 proves it"). **D2 (read-only, same script pattern) -- root cause CONFIRMED:** `GET /portfolio/balance` on demo returns a `balance_breakdown` array T-492/T-556 never read (both only read the top-level `balance_dollars` aggregate): shard 0 = `397.4368`, shard 1 = `0.0000`, shard 2 = `0.0000`, **shard 3 (Sports, where KXMLBHIT lives) = `0.0000`.** Confirmed the `exchange_index` query param does filter the top-level `balance`/`balance_dollars` fields (returns `0`/`0.0000` when `exchange_index=3` is requested, `397.4368` when `exchange_index=0`) while `balance_breakdown` always returns the full per-shard array regardless -- this is a genuine per-shard structure, not a query artifact. T-492's `balance_dollars: 399.4321` (and T-556's re-read, `399.43`) was shard-0-only the entire time, exactly as this block's working hypothesis speculated; the account has simply never had collateral allocated to shard 3. This fully explains the `insufficient_shard_balance` body's own text ("Exchange user not found" under that shard) and, by extension, the earlier `market_not_found`/`user_not_found` rotation as different renderings of the same missing-shard-user condition. **Intra Account Transfer API requirements (documentation read only, https://docs.kalshi.com/api-reference/portfolio/intra-account-transfer -- no funds moved, no call made):** `POST /portfolio/intra_exchange_instance_transfer`. Required body fields: `source` and `destination` (enum `ExchangeInstance`: `event_contract` or `margined`), `amount` (int64, centicents). Optional: `source_exchange_shard` / `destination_exchange_shard` (int, 0-100, default 0 -- this is the field that would need to be set to move collateral from shard 0 to shard 3), `source_subaccount` / `destination_subaccount` (default 0, only relevant for event-contract-to-event-contract transfers). Response on success: `{"transfer_id": "string"}`. Same three-header RSA auth as every other authenticated call -- no new credential needed. The exchange-sharding doc's own funding workflow (fetched separately) additionally describes user-level transfer -> subaccount provisioning via Create Subaccount with `exchange_index` -> Transfer Between Subaccounts with `exchange_index`, and states plainly: "Programmatic traders must preallocate collateral on a given exchange shard before order placement" -- this is a funding/provisioning action, not a code defect, and sits outside this session's authorization (no fund movement). **This is the actionable operator step: call `intra_exchange_instance_transfer` with `destination_exchange_shard=3` for some amount of the demo balance, then re-run a single real order.** **D4 (auth asymmetry disposition) -- CLOSED, no fix, confirmed intentional, specific risk already ruled out:** all three `_get(f"/markets/{ticker}")`/`_get("/markets", ...)` call sites (lines 882, 952, 975 of `kalshi_client.py`, inside `fetch_player_points_markets`/`fetch_market_detail`) omit `authenticated=True` and therefore resolve to `_price_discovery_url()` (always production) by identical, consistent design -- this is not a partial or inconsistent asymmetry across call sites. The module's own docstring documents this as a deliberate T-114 (2026-06-01) decision: "paper mode suppresses order submission only... using demo prices for edge calculations produces edge = model_p - fake_price which is meaningless." The one concrete downstream risk this asymmetry could plausibly cause for GG-203 specifically -- a demo/production `exchange_index` mismatch feeding a wrong shard value into an order -- was already empirically tested and ruled out by T-556's ADDENDUM-3 (`exchange_index: 3` identical on both hosts for KXMLBHIT) and is independently reconfirmed by this block's own D1 read of the same field. **No code change made for D4; nothing new registered -- this closes the open thread T-556's ADDENDUM-3 left without a disposition.** **GG-203 disposition: NOT RESOLVED (no order has actually succeeded, per this block's own closing bar) but root cause is now mechanistically confirmed and fully outside this session's authorization to fix -- shard-3 collateral is unallocated on the demo account, and only the operator, via `intra_exchange_instance_transfer`, can allocate it. No production order was submitted, no funds were moved, no API key was rotated. Both throwaway diagnostic scripts were deleted from the VPS after use; nothing was left running or committed.** |
| T-560 shard-3 re-verification (2026-09-18) -- GATE STOPPED, no deliverables attempted, no change from T-558 | **Task premise: operator stated they had approved allocating demo collateral to shard 3 and "may have already done it" -- this block's own instructions made re-reading the live per-shard balance the mandatory first gate, with an explicit STOP-if-still-zero clause: "That is a complete and correct outcome for this block."** One isolated throwaway diagnostic script (`/tmp/gg203_t560_balance_check.py`, VPS-side, demo-only, deleted immediately after use) called `KalshiMarketClient.from_env()._get('/portfolio/balance', authenticated=True)` directly -- the same call T-558's D2 used, not a new code path. Live result, 2026-09-18: `balance_breakdown = [{exchange_index: 0, balance: "397.4368"}, {exchange_index: 1, balance: "0.0000"}, {exchange_index: 2, balance: "0.0000"}, {exchange_index: 3, balance: "0.0000"}]`. **Shard 3 (Sports, where every KXMLBHIT market lives) remains `$0.0000` -- unchanged from T-558's 2026-09-17 reading.** The operator's approved allocation has not yet been executed on Kalshi's side (or has not yet settled/reflected in a balance read as of this check). Per the block's own gate, this session stopped here: no diagnostic order was attempted, `gg203_order_write_detector.py` was not run against a live pipeline-resume question, the 35-day outage-cost/clean_n-accrual quantification (Deliverable 3) was not performed, and GG-203 was neither closed nor re-scoped. No funds were moved, no order was submitted (real or demo), no service was restarted, no API key was rotated, `exchange_index` client-side propagation was not revisited (T-558 already disproved it), and `kelly_fraction`/sizing/promotion were not touched. **GG-203 disposition: unchanged from T-558 -- NOT RESOLVED, root cause mechanistically confirmed (shard-3 collateral unallocated), remediation remains a pending operator-side `intra_exchange_instance_transfer` action outside this session's authorization.** Re-run the same balance check before any future GG-203 remediation attempt; do not assume the operator's stated allocation is live without re-verifying, since this session directly demonstrated it was not yet reflected as of this check. |
| T-568 first confirmed real fill (2026-09-23) -- PARTIAL PROGRESS, not a systemic fix | **Shard 3 was found funded (`$199.1094`) at the start of this block, independent of any action this session took -- someone (presumed operator) allocated collateral between T-560 (2026-09-18, `$0.0000`) and now.** Per this wave's Deliverable 3, queried the running `t4-mlb` systemd service's own live audit trail (no restart, no manual order) for a service-produced approval-to-fill trail rather than assuming one. Found and fully traced: `risk_eval_approved` (`RISK-84D31C9DF4C2`, forecast `T4-MLB-C0160-1f8973-SSTEWART27-2`, 2026-09-22T23:58:31.508Z, `approved_size=1.0`, `sizing_mode="fixed_measurement"`, `kelly_fraction=0.0` -- ADR-0050/ADR-0048 both confirmed live and correctly applied) -> `paper_order_opened` (`kalshi_order_id=01a0cb8e-8c40-79ed-b7e7-647dbc8d5e6d`, 6 contracts, mid_price 0.145, `kalshi_order_status="submitted"`) -> **confirmed real fill via `GET /portfolio/fills` (authoritative endpoint, not the `submitted`-status audit event, which only means "Kalshi accepted," not "filled")**: `fill_id=0723e5b4-49b9-98d0-48ff-6e94e913cfa9`, 6 contracts @ $0.14 yes_price, fee $0.0506, 2026-09-22T23:58:32.126714Z, taker, `exchange_index=3` -> ledger row `POS-466189FABE` present in `paper_portfolio_mlb_t4.json`'s `open_positions` (band `T4M-PROJ`, `logic_epoch=12`, `status="OPEN"`, not yet in `t4_mlb_resolved_ledger.jsonl`). **This is the first confirmed, service-produced (not hand-built/manual) real Kalshi fill for T4M-PROJ since GG-203 opened -- GG-203's Deliverable-3-level closing bar (`t4-mlb` itself converting an approval into a fill`) is met for the first time.** **This does NOT resolve GG-203 at scale.** A full audit of shard-3 fills across the account's entire history (`GET /portfolio/fills`, paginated, all 2,498 fills, filtered to `exchange_index==3`) found this is the *only* shard-3 fill ever recorded -- and a systematic query of Kalshi's real order status for all 140 positions the local ledger shows as `open_positions` (all dated 2026-09-22) found **139 of 140 are `status: "canceled"` with `fill_count_fp: "0.00"` at Kalshi -- only this one position actually executed.** The underlying reliability of order matching/execution at the now-funded shard-3 balance is not established: whether the 139 cancellations reflect normal thin-book non-matching (one sampled canceled order was a resting `limit` bid that sat ~2h41m unmatched before cancellation, consistent with this) or a residual collateral/matching defect is not diagnosed in this session -- register-and-stop per Hard Rule 11; see GG-297. No service was restarted, no code was touched, no sizing/`kelly_fraction` was changed. **GG-203 disposition: PARTIALLY RESOLVED -- existence proof obtained (the pipeline CAN produce a real fill end-to-end when shard-3 collateral is present), but 1-of-140 (0.7%) same-day fill rate means systemic reliability at scale remains unproven and is not this session's finding to make.** |

</details>

---

### GG-206 — `t4_mlb_totals_outcome_store.jsonl` (and its sibling `t4_mlb_outcome_store.jsonl`) are gitignored under a rule documented for CAT-04 audit logs, but the files are CAT-03 resolution data with no backup/sync path — single-laptop-copy risk for an irreplaceable, StatsAPI-cost dataset

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** outcome_store files still caught by .gitignore (lines 96/151); no backup path found. **Next:** Add off-box backup or un-ignore the stores.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-206 |
| Category | Systemic blind spot / data-classification mismatch — a directory-level `.gitignore` rule was written and documented for one data category (CAT-04 audit logs) but also silently catches a different category (CAT-03 outcome/resolution data) that `DATA_RETENTION_DELETION.md` does not authorize excluding from durable storage, and no other backup mechanism exists for it. |
| What was missed | `.gitignore:149` excludes `logs/` with the comment "never commit audit logs — retained per DATA_RETENTION_DELETION.md". `t4_mlb_totals_outcome_store.jsonl` (built T-463, 2026-08-17) and its sibling `t4_mlb_outcome_store.jsonl` (built T-421, extended T-470) are not audit logs — `DATA_RETENTION_DELETION.md` classifies "Event resolution data from venue" as CAT-03, a distinct category whose own rule ("MUST be stored separately from feature store at all times", TI-03) says nothing about excluding it from version control or backup. Both files are effectively irreplaceable (each row costs a live MLB StatsAPI call); T-463's own commit message states "Output store is gitignored (logs/), not committed here" as a fact, without examining durability. Unlike `.vps_portfolio_cache_*.json` / `exp_output/PRICE_ARCHIVE/`, which `.claude/hooks/governance_scan.sh` actively rsync-pulls from the VPS every session, these two outcome stores are generated locally and, until this session, existed as a single copy on a single laptop with no sync mechanism in either direction. |
| When it should have been caught | At T-463's own build time (2026-08-17), or at T-421 when the sibling store was first built — either commit stated the gitignore fact without checking whether the stated audit-log rationale actually covered this data category. |
| Phases it survived | T-421 (hit store built) → T-463 (totals store built) → T-469/T-470 (both landed/extended without addressing durability) → T-484 (this session), four sessions across roughly two weeks. |
| Why it survived | `.gitignore`'s comment is a plausible-sounding blanket rationale that reads as covering everything under `logs/`, so nothing prompted a closer read of `DATA_RETENTION_DELETION.md`'s actual category boundaries. Compounding: `scripts/assert_ledger_invariants.py` (Q7) silently degrades to `SOURCE_UNAVAILABLE` skip-with-zero-violations when its source files (this store included) are absent — confirmed directly this session: run from a freshly isolated worktree (Hard Rule 10's default launch mode), Q7 reported "0 total violations across 0 band-scoped assertion runs" because none of its three source files exist in a fresh worktree at all. Q7 is alarm-only by design (exits 0 regardless of findings), so this silent skip means the mandatory session-start protocol can report a clean Q7 pass while checking nothing, on every worktree-isolated session — an unexamined side effect of the GG-101 isolation fix on this specific check. |
| Impact | Medium. Had the laptop disk failed or the file been accidentally deleted before this session, 307 resolved rows (each backed by a real StatsAPI call) would have been unrecoverable without re-querying the API from scratch, and any work depending on Q7's cross-path check would have been silently unvalidated in the meantime. Now mitigated for this one file via a VPS copy (see Resolution); the sibling `t4_mlb_outcome_store.jsonl` and any future outcome store built the same way remain exposed, and Q7's worktree blind spot is unaddressed. |
| Discovery | T-484 (2026-08-24), tasked with closing the "single uncommitted copy of an irreplaceable dataset" failure mode for this one file. Checking whether a documented reason for leaving it untracked actually applied surfaced the CAT-03/CAT-04 mismatch; running the mandatory Q7 step from an isolated worktree (this session's own protocol run) directly demonstrated the silent-skip consequence. |
| Resolution | Partially resolved, by two independent concurrent paths. This session (T-484) copied the file (329 rows) to the VPS at `/opt/prediction-market-bot/logs/t4_mlb_totals_outcome_store.jsonl`, sha256-verified both directions. Concurrently and independently, T-482 (same day, commit `83a6c48`, merged into `origin/main` ahead of this session's PR) force-added this same file to git tracking despite `.gitignore:149` still excluding `logs/` — confirmed via `git check-ignore` returning empty for the file post-merge while the sibling `t4_mlb_outcome_store.jsonl` still shows as ignored. Post-merge content is identical (sha256 `7e577e33e3e4cb21f8c0653ffcc85bc8af17de362edc5fe4a42850a470ee4a09` in both the git blob and the working-tree file), so the two resolution paths did not conflict, only overlap. Net effect: for this one file, both the "commit it" and "copy it to the VPS" halves of the original task's own disjunction ended up satisfied, by two different sessions, neither aware of the other's choice at authoring time. Two things remain open: (1) the underlying `.gitignore:149` rule itself is untouched — this file is tracked only via an ad hoc force-add with no `!` exception recorded, so a future `git add -A`-style operation gives no signal either way, and the sibling `t4_mlb_outcome_store.jsonl` remains laptop-only with neither a VPS copy nor a git commit; a standing rule (explicit gitignore carve-out, or a rsync pull/push pattern like `PRICE_ARCHIVE`'s) is still undecided; (2) Q7's silent `SOURCE_UNAVAILABLE` skip in isolated worktrees — either give Q7 the same VPS pull-back `governance_scan.sh` already does for the portfolio caches, or make the skip visibly loud rather than folding into "0 violations" in the summary line. |
| Status | OPEN 2026-08-24 (T-484; partial-resolution note added post-merge with T-482/GG-203, same session). |

</details>

---

### GG-204 — ADR-0028's G6 closure condition is unclosable as written: it is scoped to T1, and T1 is permanently `clean_n=0`

**Status:** RESOLVED · **Severity:** HIGH

**RESOLVED 2026-10-28 (W91.1 Part C, T-1343).** ADR-0076 section 2 (ACCEPTED 2026-10-27 17:30 PT by the operator, "Yes I accept") redefines G6 per (book, sport) and supersedes the T1-scoped closure condition of ADR-0028 that this gap found unclosable. ADR-0028 stays immutable; a "partially superseded" line was appended.

**W89.6 2026-10-26 (operator-approved disposition):** ADR-0057 sections 1-2 (cell-scoped G6 re-expression) were ACCEPTED 2026-08-26, so the closure-condition contradiction is addressed; GG-204 stays OPEN only until the operator confirms it can close on that acceptance or names the remaining owed decision (how many cells must clear, APPROVALS_REGISTER).

**Current state (2026-10-08, W59.1):** ADR-0028 is immutable and T1 is clean_n=0 (kelly_fraction 0.0 per ADR-0048); contradiction stands. Operator decision. **Next:** Superseding ADR for the G6 closure condition.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-204 |
| Category | Architectural placeholder / stale gate condition — an ACCEPTED, immutable ADR encodes a closure condition against a band that a later, also-ACCEPTED ADR (ADR-0048) structurally zeroed out, and no session flagged the resulting contradiction until this one. |
| What was missed | ADR-0028 §"Updated G6 Closure Condition" scopes G6 items 2, 3, and 4 to T1 bets (item 4 specifically to YES-direction eligible T1 bets). ADR-0048 (`kelly_fraction=0.0` for T1_MULTI_DAY, per GG-105/GG-135) and epoch-10's ALL_BANDS reset (clearing T1's clean-epoch floor) jointly mean T1 cannot place a bet and cannot accrue `clean_n` under the current logic epoch — confirmed live via `scripts/run_power_calc.py`: `[T1] clean_n=0 (raw_n=466)`. ADR-0028 also names T4 out-of-scope/BLOCKED for G6, but T4M-PROJ is the only ACTIVE cell currently accruing evidence (`clean_n=719` vs. `n*=608` — nominally TARGET MET, though GG-046/GG-170's live ticker/game_date corruption, reconfirmed recurring at the *current* epoch by this session's own Q7 run, means the repaired figure per ADR-0055 is `n*=5,580`, not met). Since ADRs are immutable (Hard Rule 3), no session could simply edit ADR-0028 to fix this — the contradiction could only be surfaced and a superseding decision requested. |
| When it should have been caught | At ADR-0048's own acceptance (T1_MULTI_DAY zeroed) or at epoch-10's ALL_BANDS reset — either event should have prompted a check of whether any ACCEPTED ADR's closure condition still had a live path to satisfaction. Neither did. |
| Phases it survived | ADR-0028 (accepted) → ADR-0048 (accepted, zeroed T1 Kelly) → epoch-10 reset (cleared T1 clean-epoch floor) → multiple subsequent sessions treating G6 progress as a live, trackable quantity — all without anyone checking whether the gate's own text still had a satisfiable path. |
| Why it survived | Each of ADR-0028, ADR-0048, and the epoch-10 reset was independently correct and independently reviewed in isolation; the contradiction only exists in the conjunction of the three, and no protocol step cross-checks an ACCEPTED ADR's closure condition against a *different* ACCEPTED ADR's downstream effect on the same band. Q1/Q5 grep for hard-limit values and their DECISION_LOG derivation, not for gate-condition satisfiability. |
| Impact | High. G6 (the gate to live capital) has had no satisfiable closure path since epoch-10 at the latest, and nothing in the routine session-start protocol would have surfaced this on its own — it required a session explicitly tasked with checking ADR-0028 against ADR-0048/GG-153/`execution_bands.py`/`logic_epoch.py` together. Any session reasoning about "G6 progress" using T1 figures during this window was reasoning about a gate that could not close. |
| Discovery | T-485 (2026-08-24), tasked by the operator with verifying this exact finding before drafting a decision request. Confirmed via direct read of ADR-0028/ADR-0048/GG-153, `execution_bands.py`'s `kelly_fraction=0.0` for `T1_MULTI_DAY`, `logic_epoch.py`'s `ALL_BANDS` reset semantics, and a live `scripts/run_power_calc.py` run showing `T1 clean_n=0`. |
| Resolution | ADR-0057 (drafted this session, Status PROPOSED — not yet ACCEPTED) requests re-expressing G6 against ADR-0053's per-`(market_type, band)` cell registry (`clean_n ≥ n*` per cell, under APR-0024) instead of per-band T1, while explicitly not resolving T1's fate (retire / revive via ADR gated on GG-105 / leave dark and exclude from gate — presented as an open operator decision with no recommendation) and not touching `execution_bands.py`, `risk.py`, or any `kelly_fraction`. GG-204 stays OPEN until ADR-0057 (or a successor) is ACCEPTED and T1's fate is operator-decided. |
| Status | OPEN 2026-08-24 (T-485). Blocked-On-Operator: YES — ADR-0057's acceptance and T1's fate (§4 of that ADR) are both operator decisions this session explicitly does not make. |

</details>

---

### GG-216 — Venue registry tracked "CA eligibility" but never account-level geo/IP jurisdiction; a Kalshi-side account classification flip is a live-capital blocker with no structural check

**Status:** WATCH ITEM · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Operator disposition: defer to the G6 checklist as a live-capital precondition (account-level geo/IP classification check). Irrelevant while no real capital; MEDIUM -> LOW until G6 is approached.

**Current state (2026-10-08, W59.1):** Partially addressed: VENUE_REGISTRY.md § Jurisdiction / Account Geo-Compliance Tracking was added 2026-08-26 (T-496) and tracks the VPS egress IP 157.230.91.33 and the Nevada_resident 403 trigger (GG-203); the premise that nothing tracked account geo is no longer true, but no structural pre-live check exists. **Next:** Add an account-geo check to the pre-live checklist.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-216 |
| Category | Systemic blind spot — a real, distinct compliance vector (Kalshi's own account-level geo/residency classification of the deployment's egress IP) had no field, check, or document anywhere in the governance system, despite the venue registry's stated purpose being to track exactly this class of constraint. |
| What was missed | `02_ARCHITECTURE_DESIGN/VENUE_REGISTRY.md` tracks "CA eligible" per venue (the operator's California residency vs. state betting law) and ADR-0003 frames "jurisdiction" the same way — both exclusively about the operator's home state. Neither tracks, nor has ever tracked, the separate risk that Kalshi's own geo-IP/account-compliance service can classify the *deployment's* egress IP under a different state's restrictions (observed: a "Nevada residents are not currently allowed to open positions in Sports, Elections and Entertainment" 403, GG-203) — a classification that, if it became stable rather than transient, would silently block the exact market class (Sports/Elections/Entertainment) this bot trades, and would most likely surface at go-live rather than in paper testing. ADR-0005 (the reserved slot for "Live Capital Authorization") does not exist as a written document, so there is also no future gate positioned to catch this before live capital is authorized. |
| When it should have been caught | When GG-203's Nevada-403 was first logged (2026-08-17/18) — the error message itself names a jurisdiction-classification mechanism distinct from CA-residency eligibility, and nothing prompted a check of whether that mechanism was tracked anywhere. More structurally, at VENUE_REGISTRY.md's original authoring (2026-05-29) or any of its three subsequent reviews (2026-07-02, 2026-07-31) — the document's own stated purpose ("regulatory basis, CA eligibility... activation status") never explicitly scoped in or out account-level geo classification as a tracked constraint. |
| Phases it survived | Initial venue registry build (2026-05-29) → two subsequent reviews (2026-07-02, 2026-07-31) → GG-203's discovery and diagnosis (T-492, 2026-08-24) — each treated the Nevada-403 purely as one of three rotating order-failure error codes to root-cause, correctly out of scope for that investigation, without a separate session ever asking whether the underlying constraint class was tracked anywhere. |
| Why it survived | The CA-eligibility framing in both VENUE_REGISTRY.md and ADR-0003 is intuitive and was never wrong on its own terms — it correctly answers "can Earl legally use this venue." It simply never had a counterpart answering "can this specific deployment's network egress point legally transact on this venue," and no session-start check (Q1–Q7) is scoped to catch an absent document field, only present-but-stale ones. |
| Impact | Medium as assessed today — this session's evidence (unanimous New Jersey geolocation across 3 independent providers, stable droplet identity since 2026-05-29, GG-203's rotating-error-code context) supports the 08-17/18 Nevada-403 as a transient Kalshi-side fault, not a live IP-based misclassification. But the underlying monitoring gap is real and forward-looking: nothing today would catch a *future* stable jurisdiction misclassification before it surfaces at go-live, on a venue where the account would already be restricted from exactly the market class this bot trades. |
| Discovery | T-496 (2026-08-26), tasked by the operator with distinguishing "Kalshi geo-service glitched for 48h" from "the VPS's egress IP sits in a Kalshi-classified-Nevada block and the classification flips" following GG-203's Nevada-403 finding. |
| Resolution | Not resolved by this session (analysis/documentation-tier task, no code or infrastructure change authorized). `02_ARCHITECTURE_DESIGN/VENUE_REGISTRY.md` § "Jurisdiction / Account Geo-Compliance Tracking" (added T-496, 2026-08-26) now documents the finding, evidence, and this residual gap explicitly, so a future session has somewhere to check rather than rediscovering the absence. No monitoring mechanism (e.g., a periodic geo-classification re-check against the live egress IP, or an ADR-0005 gate condition) has been built — that remains open, unstaffed work, and is explicitly an operator decision on priority, not a session's call. |
| Status | OPEN 2026-08-26 (T-496). |

</details>

---

### GG-209 — MLB T1 has no force-close/flatten mechanism for open positions; a kill-switch trip or operator halt can only stop new bets, not exit existing exposure early

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** No force-close wiring found for T1; PaperTrader.exit_position exists but is not called from the T1 pipeline. **Next:** Wire exit_position into kill-switch handling.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-209 |
| Arm | MLB, T1_MULTI_DAY |
| Category | Architectural gap — a real, working primitive exists but is not wired into the pipeline that would need it. |
| What was missed | `PaperTrader.exit_position()` (`c5_execution/paper_trader.py:661`) is a real, generic, sport-agnostic early-exit method (ADR-0018/0019 band exit mechanics — sells at current market mid price before expiry, full-exit only per EXP-019B). It is proven, working code: it is the only `exit_position(` call site in the entire `src/` tree, called live by NBA's `run_t4_live.py:543`. **Zero MLB script calls it.** MLB T1 positions close via exactly one path: `run_resolve_mlb.py`'s `_resolve_pool()` → `trader.settle_position()`, gated on `game_date < today` (position must be from a game that has already happened) and a successful actual-outcome fetch from the MLB Stats API/ESPN. If neither condition holds — game in progress, or a kill switch/operator halt trips mid-day — there is no code path, script, or CLI entrypoint that force-closes an MLB position early. The only other position-mutating path, `mark_aged_open()`, tags a position after 48h of failed API fetches; it does not close it or assign P&L. |
| When it should have been caught | When T1's kill-switch self-halt (`"KILL_SWITCH"` branch in `run_mlb_paper_trade.py`) was built — a halt that stops new bets but cannot touch existing exposure is only half the mechanism NFR-03/Hard Rule 6 ("halt all components") implies. |
| Phases it survived | T1 MLB is ACTIVE (Phase 6/7); this gap has been live and unexercised since T1 MLB went live, and remains live now that T-493/ADR-0058 proposes reopening T1 on the game-market axis with real cell promotion, which increases the population of positions this gap would apply to. |
| Why it survived | T1's kill path was validated against "does a trip block the next cron run" (it does — see GG-038's 2026-08-26 addendum, Task 5a), which reads as sufficient if you don't separately ask "can we act on positions already open." Never tested end-to-end because triggering it requires a real ≥20% drawdown, which has not occurred on the live T1 MLB book. |
| Impact | Medium, not high: T1 MLB's own structure bounds the exposure window — positions resolve naturally within roughly a day (game-day settlement), and `kelly_fraction` sizing already caps single-event exposure (`max_single_event_exposure_usd=500.0`, `risk.py` `_HARD_LIMITS`). So a kill-switch trip mid-day leaves already-open positions to ride out to natural resolution rather than being stuck open indefinitely — but "ride out to natural resolution with no way to cut losses early" is exactly the exposure a kill switch exists to prevent, and the gap gets more consequential as T1's real-money stakes or open-position count grow (T-493's game-market reopening is a stated example of exactly that). |
| Discovery | T-489 (2026-08-26), Task 5(b) of the GG-038 kill-switch SLA measurement task — investigating "can existing T1 exposure be force-closed" surfaced the call-site grep above. |
| Resolution | Not resolved; not built here per this task's explicit scope fence and instruction to register-and-stop rather than build a fix. A fix would wire `run_mlb_paper_trade.py` (or a new operator-invoked script) to call the existing `PaperTrader.exit_position()` for all open MLB positions on kill-switch trip, sourcing a live `exit_mip`/`p_current` per position at trip time — this is new pipeline logic, not a threshold change, and needs its own design/ADR pass, not a same-session patch. |
| Status | OPEN 2026-08-26 (T-489). |

</details>

---

### GG-224 — Live systemd services holding an in-memory ledger copy silently revert external file-level repairs on their next flush cycle

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** ADR-0061 (external-repair safety contract) ACCEPTED 2026-09-03; no service-side enforcement verified this session. **Next:** Verify t4-mlb honors the ADR-0061 contract.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-224 |
| Category | Architectural placeholder (no external-repair-safety contract exists for any service-owned ledger file) |
| What was missed | `t4-mlb.service` (`run_t4_mlb_live.py`) holds its entire portfolio object in memory and periodically flushes that in-memory copy back to `logs/paper_portfolio_mlb_t4.json` via a read-modify-write pattern against its OWN in-memory state — it does not re-read the file from disk before each flush. An external repair script (T-502's `t502_repair_d2_stuck_open.py`) that writes directly to that file, using a fully correct verified-backup + optimistic-concurrency + atomic-write pattern, is still silently overwritten by the service's next scheduled flush, because the danger window is AFTER the external write completes, not before it — no purely external, read-before-write safeguard can detect or prevent this class of clobber. Observed flush cadence this session: ~22s and ~72s after a fresh service restart. |
| When it should have been caught | At initial design of any long-running service that owns a shared, externally-repairable ledger file — the read-modify-write-against-memory pattern should have either re-read from disk before each flush, or the file should have carried a service-generation/version marker that an external writer could use to detect an in-flight staleness race. Neither existed. |
| Phases it survived | Unknown — this is the pattern's first direct empirical demonstration; no prior repair script (including `correct_t4_game_dates.py`/GG-166/T-429) is known to have run this repair-under-load scenario against a concurrently-flushing service and observed the revert. |
| Why it survived | No prior repair session combined (a) targeting a file owned by a currently-running, in-memory-caching service, and (b) verifying repair durability across multiple post-write intervals long enough to observe a flush cycle. T-502 is the first to do both, because its own repair-verification discipline (re-checking `repair_ref` presence after the write, not just trusting the write's own exit code) surfaced the revert. |
| Impact | MEDIUM. Any future external repair to `paper_portfolio_mlb_t4.json` (or any other file with an analogous owning service) that does not coordinate a service restart/reload immediately post-write will appear to succeed (correct backup, correct write, correct exit code) and then silently revert within roughly one flush interval — a false-positive "repair complete" that a session could report without ever detecting the revert, had it not specifically re-verified persistence across multiple post-write intervals as this session did. |
| Discovery | 2026-08-28, T-502, during execution of the ADR-0055 D2 repair — the first repair attempt (dry-run-equivalent full `--apply` run) appeared to succeed but was found reverted to zero `repair_ref`-carrying rows on a subsequent check. |
| Resolution | Worked around this session via explicit operator authorization (`AskUserQuestion`, operator selected "Restart t4-mlb.service after write (Recommended)"): re-ran the repair script, then immediately ran `systemctl restart t4-mlb.service` so the freshly started process loads the corrected file from disk on startup rather than flushing stale in-memory state over it. Verified durable through two independent subsequent flush cycles post-restart (`last_updated` advancing at 00:43:05Z and 00:44:17Z, both preserving all 46 `repair_ref` stamps, `logic_epoch={12}` throughout, service `NRestarts=0` — a clean single restart, not a crash-loop). This is a session-scoped workaround, not a systemic fix. **Open follow-on, unstaffed, out of this session's scope fence:** modify `run_t4_mlb_live.py` (or the owning service pattern generally) to re-read ledger state from disk immediately before each flush, or to detect an external mtime/hash change since its last read and merge/abort accordingly, so future external repairs do not require a coordinated restart. Minor related doc-debt noted but NOT fixed (out of scope): `04_EXECUTION/LEDGER_INVARIANT_SUITE.md`'s documented cache-refresh command (`scp` against a VPS-side dotfile path) does not match the actually-working fetch pattern (`ssh ... cat ... > local.tmp` then atomic move, as used in `.claude/hooks/governance_scan.sh` and by this session) — the documented command targets a path that does not exist on the VPS. |
| Status | OPEN. Workaround applied and verified for this session's specific repair; the general hazard (any future external write to a service-owned ledger file) remains unaddressed pending a code change to the owning service(s). |

</details>

---

### GG-234 — Task assignment named `T-508 / GG-231` for new work; both IDs were already consumed by unrelated, already-closed sessions by the time the assigned session actually started

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Process gap, same family as GG-256: claim_session.sh collision check exists but assignments authored against a stale SESSION_CLAIMS snapshot are not validated. **Next:** Fold into GG-256 fix; close when that lands.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-234 |
| Category | Process gap — task-assignment ID staleness, distinct from GG-162 (no atomic GG-number reservation at claim time) and GG-199 (duplicate-ID detection blind spot). This is neither a race nor a duplicate — it is a prompt authored against a snapshot of `SESSION_CLAIMS.md` that had already gone stale by the time the assigned session launched. |
| What was found | This session's task prompt explicitly assigned `T-508 / GG-231` and instructed "Take GG-231 and push it first." At session start (`scripts/claim_session.sh "T-508: ..." "T-508 / GG-231"`), both IDs collided: GG-231 was already claimed and CLOSED by T-507 (2026-09-01T05:07:10Z closure row, same log), and T-508 was already reserved in `04_EXECUTION/TODO_NEXT.md` line 22 for a wholly unrelated task ("Fix GG-230: MEMORY_BANK.md Compass OS Health line length"). A first retry at `T-510 / GG-233` also collided seconds later against a genuinely concurrent session claiming those same IDs for a third, different task (NFL/NHL T4 ADR). Landed on `T-511 / GG-234` on the second retry. |
| When it should have been caught | Before the task prompt was handed to this session — whoever drafted the `T-508 / GG-231` assignment was working from a `SESSION_CLAIMS.md`/`TODO_NEXT.md` snapshot that predated T-507's and T-508's actual registration as different work. |
| Phases it survived | N/A — this is a single-session, single-instance finding, not a multi-phase survival. |
| Why it survived | Task prompts naming specific `T-`/`GG-` numbers are authored outside the session that will execute them (by the operator or a prior planning pass) and are not re-validated against live `SESSION_CLAIMS.md`/`TODO_NEXT.md` state at hand-off time. `claim_session.sh`'s collision check does catch this at claim time (as it did here, working exactly as designed) — the gap is that the *assignment itself* embeds numbers that can go stale between drafting and execution, forcing an in-session renumber rather than the assignment being correct on arrival. |
| Impact | LOW as realized — `claim_session.sh` caught both collisions cleanly, no number was double-registered, and this session renumbered to `T-511 / GG-234` before any deliverable work began, per this same task's own instruction ("a number is claimed when it is pushed, not when it is read"). Would be higher-impact if a session did not re-verify collisions live and instead wrote directly into `GOVERNANCE_GAP_LOG.md`/`DECISION_LOG.md` under the assigned-but-stale number, silently colliding with T-507's or T-508's real content. |
| Discovery | 2026-09-01, T-511 (this session), at the mandatory Step 0 claim step, before any deliverable work — `claim_session.sh` refused the assigned IDs twice in direct succession. |
| Resolution | Not a code fix — this entry documents the finding per Hard Rule 11 (register on discovery) and per this session's own explicit instruction to push a gap-log entry first. No process change proposed here; `claim_session.sh`'s live collision check is the correct mitigation and worked as intended both times. A future task-assignment workflow could re-run a fresh `claim_session.sh` dry-check immediately before drafting a prompt's ID line, but that is a planning-side process change outside this session's scope fence (`GOVERNANCE_GAP_LOG.md`/`DECISION_LOG.md`/T-506 landing/`APPROVALS_REGISTER.md`/`check_register_parity.py`/`11_MEMORY_HANDOFF/`). |
| Status | OPEN. |

</details>

---

### GG-230 — `MEMORY_BANK.md`'s "Compass OS Health" single-line field is 5159 chars, 1.7x the script's own 3000-char anti-blob threshold, flagged and never registered

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** MEMORY_BANK.md Compass OS Health line is 5158 chars (was 5159); threshold 3000. **Next:** Split the line.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-230 |
| Category | Process gap — a finding surfaced by an existing automated check was never converted into a governance gap entry, so it sat unactioned outside any tracked backlog |
| What was missed | `scripts/check_memory_bank_snapshots.sh`'s Check 4 (`check_line_length`, `LENGTH_THRESHOLD=3000`, added under T-334 specifically to catch "the count stays 1 but the line itself becomes the blob" regression) currently reports the `## Compass OS Health` line in `11_MEMORY_HANDOFF/MEMORY_BANK.md` (line 1100) at **5159 chars** — confirmed live this session by direct execution: `bash scripts/check_memory_bank_snapshots.sh` → `Compass OS Health line length: 5159 chars (line 1100)` → `VIOLATION=1`, 72% over the script's own 3000-char threshold. This is exactly the pre-T-334 inline-blob failure mode the check exists to catch (header count stays at 1 while the single line silently regrows) — the check is working correctly and reporting a live violation, but the violation itself was never registered anywhere actionable. |
| When it should have been caught | `SESSION_HANDOFF_20260817_2338.md` (T-460, 2026-08-17) already names this exact finding verbatim: "Also unregistered: the `Compass OS Health` 5159-char line-length concern `session_guard.sh` flagged at session start — needs a GG next session." That session-end note was itself the point this should have been registered; it was not, and no session in the 14 days since (2026-08-17 → 2026-08-31) picked it up. |
| Phases it survived | At least 14 days / an unknown number of intervening sessions between the 2026-08-17 T-460 handoff note and this 2026-08-31 T-507 discovery — the line length is unchanged (5159 chars then and now, per the handoff note's own figure matching this session's live measurement exactly), so no session in between edited the field, and none registered the already-flagged concern either. |
| Why it survived | A session-end handoff note naming an unregistered finding is not itself a tracked backlog item — nothing re-surfaces a "needs a GG next session" line from a dated handoff file unless a future session happens to read that specific file and notices the sentence. There is no standing check that cross-references stated handoff carryover items against the governance gap log to confirm they were actually registered. |
| Impact | LOW as currently realized — no observed downstream corruption from this specific field; the risk is the one T-334/the script's own header comment describes: an unpruned single-line blob field can silently regrow indefinitely (embedded "Prior pointer —" / "(Previous, as of ...)" phrases) without header-count checks ever detecting it, since header count alone stays at 1. |
| Discovery | 2026-08-31, T-507 (this session), during the out-of-scope-finding-verification step required by Hard Rule 11 before registering anything found outside T-507's own scope. Found by reading `SESSION_HANDOFF_20260817_2338.md` (grepped from a vague pre-compaction memory of "a Compass OS Health line-length finding"), then independently re-verified by direct measurement (`awk` line-length scan + running `check_memory_bank_snapshots.sh` itself) rather than trusting the handoff note's figure at face value — both measurements agree exactly (5159 chars, line 1100). |
| Resolution | Not resolved in this session — per Hard Rule 11 ("Register and stop on discovery... Do not fix it in-session"), T-507's scope fence is `exp_output/`, `05_RESEARCH_EXPERIMENTS/`, and T-488's analysis script; `MEMORY_BANK.md` is out of scope. The actual fix (per the script's own guidance: check for embedded "Prior pointer —" / "(Previous, as of ...)" phrases in the Compass OS Health field and cut over to a dated archive header in `MEMORY_BANK_ARCHIVE.md`'s "Compass OS Health chain" section per T-334's established pattern) is a small, well-specified follow-on for a future session to pick up directly. |
| Status | OPEN. |

</details>

---

### GG-487 — MLB shadow settlement y is derived from games-cache final scores, never cross-checked against Kalshi's own settlement

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** src/prediction_market_bot/pregame_shadow/mlb_settlement.py derives y only from Final games-cache scores via join_row(); no Kalshi market-result comparison exists (git grep finds none in pregame_shadow/scripts). VPS mlb_pregame_shadow_settle.log 2026-10-07 shows 21/4/12/28 settled per cell all derived this way. **Next:** Write a read-only script comparing settled/ y with Kalshi market `result` for the same tickers and report disagreement rate.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-487 |
| Category | Data integrity |
| What was found | W57.2 settles MLB shadow rows from Stats API final scores (per the W57 block). GG-472/GG-440 named Kalshi's own settlement as the authoritative source. Edge cases (suspended/shortened games, ticker grammar drift) could make derived y differ from Kalshi's. |
| Why it matters | A wrong y poisons the cell's judged-n scoring later (cf. GG-166). Cheap to check now, expensive after scoring. |
| Disposition | Registered only (operator, 2026-10-07: proceed with cross-check rec). Build a read-only comparison of settled/ y vs Kalshi market `result` for the same tickers; report disagreement rate. Not built this session (Hard Rule 11). |
| Source | W57.2 |

</details>

### GG-730 — nflverse pbp_participation has no 2026 file: current-season coverage, pressure and personnel unavailable

**Status:** OPEN · **Severity:** MEDIUM

W73.2 Part A (2026-10-14). The `pbp_participation` release (read 2026-10-14) lists 2016-2025 and `_old_2023` only. It is the only free source of `defense_man_zone_type`, `defense_coverage_type`, `was_pressure`, `time_to_throw`, `offense/defense_personnel`. 2026 features for coverage/pressure/personnel cannot be built from it; FTN 2026 (blitzers, rushers, motion) and pbp-derived features partly substitute. Re-check the release at each data-layer build; close when a 2026 file appears.

### GG-731 — No free table of NFL offensive/defensive coordinators or the actual play caller

**Status:** OPEN · **Severity:** LOW

W73.2 Part A (2026-10-14). Syndicate32 shows play callers as a matchup factor. nflverse `games` has `home_coach`/`away_coach` (head coach) only. Registered as a GAP, not bought (ADR-0073 point 4).

### GG-732 — nflverse injuries and officials carry no publication timestamp

**Status:** OPEN · **Severity:** MEDIUM

W73.2 Part A (2026-10-14). `injuries_*` is keyed by (season, week, team, gsis_id) with no report time; `officials` has no assignment time. Point-in-time use is by a conservative week rule (FACTOR_TAXONOMY GAP-3), enforced and tested in the W73.2 store. A true as-of timestamp needs our own dated snapshots going forward.

W73.2 Part B (2026-10-15). Measured: `injuries` 2015-2024 DO carry `date_modified` (fill 100%; 2009 0.4%); 2025-26 files do not; `officials` never. The column is stored but not used - its meaning (last edit of the week's report vs. each line) is unverified, so the contract stays on the conservative week rule. Verifying it would let 2015-2024 week-of injuries be used for Thursday games.

### GG-733 — nflverse games.parquet lines are closing values in a rolling, overwritten file, not as-of-kickoff snapshots

**Status:** OPEN · **Severity:** MEDIUM

W73.2 Part A (2026-10-14). `games.parquet` (schedules tag) updates in place (2026-10-14T23:36Z). `spread_line`, `total_line`, moneylines are final values: usable as a market comparison, never as a model input. W73.2 snapshots the file per build so 2026 lines become point-in-time from now on.

W73.2 Part B (2026-10-15). Mitigation is live: each weekly `nfl_event_store` build uploads its `games.parquet` snapshot to the rolling release `nfl-games-snapshots`. Lines before 2026-10-15 cannot be recovered as-of; only snapshots from the first Actions run forward are point-in-time.

### GG-734 — No free historical weather FORECAST archive confirmed; stored temp/wind are at-game values

**Status:** OPEN · **Severity:** LOW

W73.2 Part A (2026-10-14). `games.temp`/`wind` (fill 0.74 in 2018, 0.38 in 2022, 0.67 in 2025; roofed games null) and `pbp.weather` are recorded at game time, not forecasts available before kickoff. Treated as a labelled leakage-risk feature until a forecast source is verified. Candidate sources are unverified.

### GG-740 — Slice failure: no single owned map of the running system; fixes landed in one place while the same defect survived elsewhere

**Status:** OPEN · **Severity:** HIGH

Registered 2026-10-14 by the strategic window (ADR-0074). Hundreds of short sessions each saw a slice of the system; nobody owned what runs end to end, and fixes were not swept for the same defect elsewhere. Evidence: GG-122 -> GG-144 (same broken grep fixed in the hook, left in CLAUDE.md Step 3 for 13 days); GG-532 and GG-163 (silent arm / silent T4 found by hand); GG-661 (stale code running after skipped restarts); GG-203 (only evidence cell dark 38 days). **Done 2026-10-14 (window):** `02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml` + `scripts/runtime_registry.py` + `tests/test_runtime_registry.py` (CI fails on an unregistered cron line, service or workflow; 76 components registered, 75 live); `RUNTIME_MAP.md` generated; Hard Rule 13 + `pattern_sweep:` handoff key (required after 2026-10-15T12:00Z, `generate_session_artifacts.py`, tests). **Open until:** a terminal (a) wires registry check, surface counts and live columns (running code SHA, last write, alarm state) into the governance scan, and (b) reviews all 75 auto-classified entries against the live crontab (`reviewed = true`). Pillar: PLUMBING (protects every pillar).

### GG-741 — Strategic windows were unaccountable: no pushback against surface outrunning reliability, plumbing escalated, notes not read, colliding blocks

**Status:** OPEN · **Severity:** HIGH

Registered 2026-10-14 (ADR-0074). Twelve window errors seeded in `04_EXECUTION/WINDOW_ERROR_LOG.md` (W1-W12, plus two historical slice failures). **Done 2026-10-14 (window):** the log with a pattern tally; Hard Rules 14-15 in CLAUDE.md (surface budget; error log read first; notes-first; Pushback / Surface / Dependencies lines in every wave; operator routing limited to pre-registration, frozen artifact/book, real capital, strategy); `/strategic-handoff` step 0 + Surface row + wave format; window paste-in updated. **Open until:** two consecutive waves are issued in the new format and the next window handoff reads and extends the log. Pillar: PLUMBING.

### GG-747 — T4 portfolio has 4,309 closed rows vs 4,275 in the resolved ledger (gap of 34)

**Status:** OPEN · **Severity:** MEDIUM

B74-A L2, 2026-10-14. Last T4 entry 2026-10-14T02:29Z. Unexplained difference of 34 between the portfolio's closed rows and the resolved T4 ledger. Pillar: PROOF (P&L per filled bet is read from one of these). Proposed fix: diff the two by position id, classify the 34 (legacy, cancelled, duplicate), and add the reconciliation as a Q7 assertion.

### GG-748 — Live-ledger writers outside atomic_io: four scripts and CellLedger.append

**Status:** OPEN · **Severity:** MEDIUM

B74-A L2. `scripts/correct_t4_game_dates.py:133`, `gg271_bound_t4_rejected_positions.py:149`, `replay_harness_t427.py:210`, `tag_locked_pairs_t4_mlb.py:116` rewrite the live T4 ledger with `open("w")` + `json.dump` (backup copy only, no lock, no atomic replace). `pregame_shadow/ledger.py` `CellLedger.append` has no cross-process lock and its dedup key set is cached per process, so two overlapping runners can double-write (0 duplicates found today, latent). Regenerable reports/caches also non-atomic (`nfl_ingestion.py:543/550`, `generate_mlb_features.py`, `run_add_players.py:136`). Pillar: PROOF. Proposed fix: route through `atomic_io` + `_file_lock`, refuse to run while t4-mlb is active, flock around `append`. Extends GG-680.

### GG-749 — Measurement-path failures are swallowed or counted but never alarmed

**Status:** OPEN · **Severity:** MEDIUM

B74-A L3. (a) `run_t4_mlb_live.py:413-419` `_append_dryrun_record` swallows a write failure with a warning, so cycle-log rows go missing non-randomly. (b) `pregame_shadow/runner.py:68-72` a forecaster `None` (about 13 branches in `nfl_forecaster.py:38-122`) is counted, never alarmed: selection bias in what gets scored. (c) `calibration_engine.py:311-317, 379-404` swallow errors and undercount P3. (d) `runner.py:88-91` swallows an `on_row` observer failure (E1 if it is the demo-fill hook). (e) `run_t4_mlb_live.py:~590-596` T2 batting slot silently defaults to 3.7 with no flag in the cycle log. (f) `:1735-1737` `stage_order` failure is log-and-continue with no counter. Pillar: PROOF, DEPTH, EXECUTION. Proposed fix: an `alarm()` plus a per-cycle counter on each; flag defaulted inputs in the row.

### GG-750 — t4-mlb main loop never escalates repeated failure; Kalshi client init failure silently makes orders local_only

**Status:** OPEN · **Severity:** MEDIUM

B74-A L3. `run_t4_mlb_live.py:2037-2220` logs and loops forever; ESPN discovery failure returns `[]` (the GG-163 pattern, blind to `systemctl is-active`). `:1930-1934` a Kalshi client init failure makes orders `local_only` with no alarm, which GG-527 says is not execution evidence. Pillar: EXECUTION (E1). Proposed fix: consecutive-failure counter with alarm and a non-zero exit after N, and an alarm when the client falls back to local_only.

### GG-752 — vps_deploy.sh has no rollback; deploy_status.json alarm and heal_dirty_tree coverage unverified

**Status:** OPEN · **Severity:** MEDIUM

B74-A L4. GG-661 and GG-668 are otherwise fixed and read back as running (t4-mlb started 02:53Z, after the last src commit; pending-restart retry fired). Still open: no rollback after `gate_red`/`verify_failed` (tree stays at the pulled SHA); `dirty_tree_abort` still exits 1 (3 historical, last 10-13 00:28Z) and tracked `deploy/demo_fill.env` is tool-rewritten (heal_dirty_tree L100-130 not read); nothing confirmed to alarm on `deploy_status.json`. Pillar: EXECUTION. Proposed fix: record previous SHA and revert on verify_failed; confirm heal covers demo_fill.env (or untrack it); wire `deploy_truth.py check` into the governance scan.

### GG-754 — demo_fill_forward_report: no_outcome check not epoch-gated; two plain write_text writers

**Status:** OPEN · **Severity:** MEDIUM

B74-A L6. `scripts/demo_fill_forward_report.py:~207-211` counts `no_outcome` cancels over all history and `checks["scheduled_cancel_no_outcome_15m"]` trips on `count > 0`: one pre-fix orphan re-trips the turn-off forever (same class as the #256 stale-history fix, not swept). Per-cell `cancels`/`cancel_success_rate` also include pre-fix rows. `:306` writes `deploy/demo_fill.override.env` (the kill-switch file the policy reads last) and `:369` the cache with plain `write_text`. Pillar: EXECUTION. Proposed fix: gate on `ts >= CANCEL_PATH_FIX_EPOCH` with a test; move both writers to `atomic_io`.

### GG-755 — Fee formula inlined at 9 src sites plus a second fee model (GG-673 grew from 7)

**Status:** OPEN · **Severity:** MEDIUM

B74-A L5. `0.07*p*(1-p)` at `run_mlb_paper_trade.py:915`, `run_paper_trade.py:589`, `run_t4_mlb_live.py:1459`, `run_pregame.py:370`, `run_mlb_pregame.py:434`, `run_t2_mlb_sameday.py:450`, `run_t4_live.py:666`, `c5_execution/paper_trader.py:521,813`; `pregame_shadow/fees.py` is a separate source (`fee_kmult` uses an INFERRED 0.035 coefficient) imported only by the shadow runner and scoring. About 17 more copies in scripts. No devig helper exists in src. Pillar: EXECUTION (E2). Proposed fix: one `c5_execution/fees.py`, import everywhere, a test that fails on a new inline copy (Hard Rule 13 sweep).

### GG-756 — NFL engine interface is not sport-agnostic and the code does not match INTERFACE.md

**Status:** OPEN · **Severity:** MEDIUM

B74-A L5 (HEAD before W73.2 Part B merged). ADR-0073 point 6 calls NFL the template for all four sports, yet `GameSample` in INTERFACE.md §4 carries `td_h/td_a/fg_h/fg_a` and `12_EXPLORATORY/nfl_engine/engine.py:14-38` hard-codes TD/FG scoring; no `SportEngine` Protocol. `GameInputs`/`build_inputs` exist only in the doc; `engine.py:77` has a different `simulate` signature. The rating layer is the frozen ridge, so D4 is scaffold only. Pillar: DEPTH (D4). Proposed fix: split a sport-neutral `GameSample` core and add a Protocol before the NBA engine copies the shape; say "scaffold" in D4.

### GG-757 — NFL engine invariants are not run by CI

**Status:** OPEN · **Severity:** MEDIUM

B74-A L5. `12_EXPLORATORY/nfl_engine/test_engine.py` is outside `pyproject.toml:77` `testpaths=["tests"]`; no `__init__.py`; `study.py:24-30` uses sys.path/importlib hacks. The invariants INTERFACE §5 calls asserted (ML identity, monotone ladders, total = home + away) never run on push. Pillar: PROOF. Proposed fix: move into `tests/` or extend `testpaths`.

### GG-758 — Silent-arm coverage is coarse (MLB postseason folded into mlb_shadow; T2/T3 have no arm)

**Status:** OPEN · **Severity:** LOW

B74-A L5. `pregame_shadow/silent_arms.py` SPECS has 10 arms; postseason is folded into `mlb_shadow` (`_mlb_starts` includes R/F/D/L/W, globs `MLB_*.jsonl`), so a dead postseason runner is masked by regular-season rows. MLB player-hits T2/T3 (registry SHADOW) have no arm; `t1_mlb` reads only `audit_mlb.jsonl` with a 30h window. Runs only in `governance_scan_full.sh:769`. Pillar: PROOF/BREADTH. Proposed fix: per-band file filters, a postseason spec keyed on game_type, run in the light scan.

### GG-759 — Stale comments that now state the wrong thing

**Status:** OPEN · **Severity:** LOW

B74-A L1. `c5_execution/market_type_registry.py:~945` says SHADOW = no orders, but shadow cells place demo orders when `SHADOW_FLAT_STAKE=on` (ADR-0072). `t4_fill_status.py:362` says BOT_ENV is blank in the VPS `.env`; it is `paper` (`.env:8`). `gg271_bound_t4_rejected_positions.py` near L83 is stale. Pillar: PLUMBING. Proposed fix: correct the three comments.

### GG-760 — Type debt: mypy 162 errors on c4/c5/pregame_shadow, including unsound unions in kalshi_client and paper_trader

**Status:** OPEN · **Severity:** LOW

B74-A Part A, 2026-10-14 (`mypy --ignore-missing-imports`, 3.11). 162 lines: 90 type-arg, 17 arg-type, 15 no-any-return, 14 no-untyped-def, 13 no-untyped-call, 6 assignment, 3 operator, 2 return-value. Worth a look: `kalshi_client.py:954,1024,1045` (`PlayerMarket | GameMarket` appended/returned as one type), `paper_trader.py:129` (`str | None` key), `:672/:676` (`str | int | float | Any | None` passed where `str` is required, on the order path), `demo_fill_policy.py:215`. None triaged as a live bug. Pillar: PLUMBING. Proposed fix: fix the 5 order-path ones first, then add mypy on c4/c5 to CI at the current count as a ratchet.

### GG-761 — Layering inversions and sport literals outside C4/C6 (GG-674 unchanged)

**Status:** OPEN · **Severity:** LOW

B74-A L5. `c3_forecasting -> pregame_shadow` (`nhl_pregame.py:43`, lazy), `pregame_shadow -> c5_execution` (analytics). `venue_router.py:132`, `venue_adapter.py:105,173,375,510` default `sport="NBA"`; `venue_adapter.py:350` hard-codes `"tag":"nba"` (KI-019); C7 baselines NBA/MLB only; C8 42 sport mentions. C4 and C6 hold zero. No import cycle among c1..c8. Pillar: PLUMBING. Proposed fix: make `sport` a required argument; move shared contract out of pregame_shadow.

### GG-762 — MLB game feature builder is timezone-fragile on as_of

**Status:** OPEN · **Severity:** LOW

B74-A L2. `mlb_game_pregame_features.py:88` uses `as_of.date().isoformat()` and `as_of.year` with no UTC normalization (strict `bisect_left`, so no look-ahead for UTC input). NFL normalizes with `astimezone(UTC)`. A naive or non-UTC as_of would shift the cutoff day. Pillar: PROOF. Proposed fix: require tz-aware and normalize.

### GG-763 — Data observations for PROOF: NFL ties scored y=0.5, thin T4M-PROJ cross-path coverage, legacy null outcomes

**Status:** OPEN · **Severity:** LOW

B74-A L2 (106,012 rows across 81 files, 0 integrity violations). (a) NFL moneyline settled files carry y=0.5 (2 rows per file): confirm scoring and calibration treat 0.5 as a tie. (b) T4M-PROJ epoch-12 cross-path outcome check covers 187 of 2,080 rows, so "0 disagreement" is thin. (c) 317 legacy `paper_portfolio_t4` closed rows have outcome None. (d) GG-690/691 baseline unchanged: 3,495 null market_type in the MLB portfolio (plus 158 + 485 + 2,895 legacy) and 16 CANCELLED rows. Pillar: PROOF. Proposed fix: assert each in the ledger-invariants script with a stated expected count.

**W75.5 part (a) done:** the pre-registration is explicit (moneyline tie = y=0.5) and the shadow settlement code matches; now covered by a test through `typed_join`. The paper path's tie refusal (GG-257) is a separate, intentional mechanism. Parts (b)-(d) remain OPEN.

### GG-764 — Read-side holes: assert_ledger_invariants crashes on a corrupt file; validators reset state on decode error

**Status:** OPEN · **Severity:** LOW

B74-A L2. `scripts/assert_ledger_invariants.py:145` `load_json` has no try (one corrupt ledger crashes the scan, which is alarm-only). `validators.py:379` `_load_state` returns `{}` on JSONDecodeError, silently resetting the previous-row-count check. `run_t4_mlb_live.py:1175` fails open on a corrupt T1 portfolio. `demo_fill_policy.py` `append_log` swallows OSError (GG-675 still open; the 897-915 pagination was not re-read). Pillar: PROOF. Proposed fix: catch per file and report CORRUPT; alarm on state reset.

### GG-766 — Golden-SHA test `test_default_output_unchanged` fails off the pinned pandas; suite is not env-proof

**Status:** OPEN · **Severity:** LOW

B74-A Part A, 2026-10-14: `tests/test_generate_mlb_features.py:540` (`TestPostseasonOptIn.test_default_output_unchanged`) failed its byte-level `_GOLDEN_DEFAULT_SHA` assertion (got 2103375a..., expected 7ea0e376...) in the audit venv, which resolved pandas 3.0.6 / numpy 2.4.6 against `pyproject.toml` pins `pandas>=2.2.0,<2.3`, `numpy<2.0`. Likely cause (UNVERIFIED): CSV float/quoting serialization differs off-pin. Not re-run on the pinned set, so it is not shown to be a product defect. Pillar risk: PLUMBING (a golden-hash test that depends on library serialization will false-alarm or, worse, be re-goldened blindly). Fix: re-run under the pinned pandas; if it passes, make the audit venv install honor the pins and note it in the audit runbook; if it fails, re-derive the golden from the pre-change script. Also caveat: every Part A number in HYGIENE_AUDIT_20261015 came from an off-pin env.

### GG-775 — No free receiver/defender alignment or routes-run denominator (slot vs wide, TE/RB role)

**Status:** OPEN · **Severity:** LOW

W75.1 Part B (2026-10-14). WR-SLOT, TE-IN, RB-REC, CB-SLOT archetypes need pre-snap alignment and routes run per player. nflverse participation gives `route` only on the targeted play and no alignment. Source would be NGS/PFF tracking (not free).

### GG-776 — No free OL block-level win rates or blocker attribution

**Status:** OPEN · **Severity:** LOW

W75.1 Part B (2026-10-14). OL-PASS and OL-RUN archetypes need per-blocker pass-block/run-block outcomes. pbp attributes sacks/pressure to the team and defender only. Source would be PFF-type grading (not free). OL stays team-level proxy only.

### GG-777 — No free defender coverage assignment (who covered whom, man vs zone per defender)

**Status:** OPEN · **Severity:** LOW

W75.1 Part B (2026-10-14). CB-SHD, CB-ZN, S-DEEP, LB-COV need per-defender assignment. participation has play-level `defense_man_zone_type` only; PFR def counts targets allowed to the covering defender but not alignment or scheme. Mass CB classification therefore deferred; WR chosen instead.

### GG-778 — No free DL/EDGE pass-rush snap counts or alignment

**Status:** OPEN · **Severity:** LOW

W75.1 Part B (2026-10-14). DL-RUSH rates need a pass-rush-snap denominator and alignment (wide-9 / 3-tech). snaps give total defensive snaps, not rush snaps; alignment not free.

### GG-779 — No free tracking-derived separation / speed / route quality

**Status:** OPEN · **Severity:** LOW

W75.1 Part B (2026-10-14). Separation, yards per route run and top speed need NGS/Sportradar tracking. Cross-cutting for WR/TE/CB. Registered as a GAP, not bought (ADR-0073 point 4).

### GG-891 — KXNBATEAMTOTAL never listed: the 3 NBA_TEAM_TOTAL cells cannot get rows

**Status:** OPEN · **Severity:** LOW

**2026-10-20 (W80.2) - premise stale:** `KXNBATEAMTOTAL` IS listed (public GET: `KXNBATEAMTOTAL-26OCT21INDNOP-NOP137`, active) and `NBA_TEAM_TOTAL_T1.jsonl` holds 374 valid rows, flip check FLIP-OK 374/374 (box preflight 20261020T0005Z). The 9-of-12 ceiling is 12-of-12. Stays OPEN only until the 12:40Z autoflip records the TEAM_TOTAL T1 flip; close on that evidence.

W78.3 read-only GET 2026-10-15: KXNBAGAME 56, KXNBASPREAD 200, KXNBATOTAL 200 open markets; KXNBATEAMTOTAL 0. B1 ceiling for NBA game cells is 9 of 12 until Kalshi lists it. Also KXNBAPTS returned 0 open markets on 2026-10-15 (the points series may list closer to tip or under another series ticker) — verify on 10-20 before treating the points arm as healthy.

### GG-892 — nba_shadow silent arm masked by player-points rows (NBA_*.jsonl glob)

**Status:** OPEN · **Severity:** MEDIUM

W78.3: `silent_arms.load_inputs` globbed `NBA_*.jsonl` for the game arm, which also matches `NBA_NBA_PLAYER_POINTS_*`; live points rows would hide a dead game arm. Fixed in PR #275 with a test; pending deploy at write time. Sweep of the other arms' globs (MLB_/NFL_/NHL_) found no sibling families sharing a prefix. Close after deploy read-back.

### GG-910 — NBA engine: no point-in-time injury history before 2026-09-08

**Status:** OPEN · **Severity:** MEDIUM

W79.3 FACTOR_TAXONOMY N10/GAP-1. The ESPN injuries endpoint serves the current list only; the store has daily snapshots from 2026-09-08 (2 files). Games before that cannot be given an as-of injury state, so availability cannot be backtested on this store. Pillar: DEPTH (D5b NBA availability). Proposed fix: take the snapshot daily (not weekly) from now; no purchase. Legacy availability studies (NBA-T3) used other sources and are not rebuilt here.

### GG-911 — NBA engine: officials crew has no assignment timestamp

**Status:** OPEN · **Severity:** LOW

W79.3 GAP-2. `officials` lists the crew for finished games; nothing says when the crew was public, so crew cannot be used pre-tip without an assumption. Pillar: DEPTH. Proposed fix: capture the NBA official assignment page (posted game day) as a dated snapshot going forward.

### GG-912 — NBA engine: coaches are season-level with no tenure dates

**Status:** OPEN · **Severity:** LOW

W79.3 GAP-3. `coaches` has no start/end dates; mid-season firings and interims are invisible and the point-in-time contract refuses the table (`season_static`). Pillar: DEPTH. Proposed fix: derive head coach per game from game-level sources if a free one exists, else snapshot from now.

### GG-913 — NBA engine: no travel / venue geometry (coordinates, time zones, miles)

**Status:** OPEN · **Severity:** MEDIUM

W79.3 GAP-4. Only venue city and state are loaded; no coordinates or time zones. Rest (N3) is built and interpreted without distance. Pillar: DEPTH (travel is a named granularity-bar factor). Proposed fix: a hand-built 30-arena coordinate table (free, small), plus rest-in-time-zone-hours; then test incremental to rest.

### GG-914 — NBA engine: PAM and structured qualitative factors not piped into the NBA engine

**Status:** OPEN · **Severity:** MEDIUM

W79.3 GAP-5 / N13. PAM (DS-01, NBA v4 port) exists but no NBA engine reads it; structured qualitative has no free historical feed. Operator directive 2026-10-14 pipes PAM into NFL and NBA engines first. Pillar: DEPTH (D2 qualitative count 0). Proposed fix: a PAM-to-engine adapter as a separate block; unaffected by this wave.

### GG-915 — SURFACE BUDGET counted import-blind "behind HEAD" hours (false RED on unrelated merges)

**Status:** IN PROGRESS · **Severity:** MEDIUM

W79.1 / W80P.1. `scripts/runtime_registry.py` `probe_local` counted every `src/`/`scripts/` commit since a service's running SHA, so any unrelated merge turned the SURFACE BUDGET RED after 6 h ("t4-mlb running 03ad6df9, 8.33h behind box HEAD", 2026-10-16), while the deploy restart policy (GG-432) correctly declines to restart t4-mlb for files it does not import. Two definitions of "behind" disagreed; Hard Rule 14 then blocked new components on a false red. Fix (W80P.1 PR): one shared definition `scripts/ops/deploy_truth.py::unapplied_changes` (restart policy's import closure for t4-mlb, src/ + web_dashboard for the dashboard), called by both the deploy-truth check and the budget probe; CLAUDE.md Hard Rule 14 text aligned; 6 regression tests. Stays IN PROGRESS until a session with box access reads `scripts/runtime_registry.py live` GREEN (or RED only on a real import change) after the merge deploys — this cloud session had no ssh.

### GG-920 — SURFACE BUDGET read a stale t4-mlb as current (running SHA estimated from commit dates) → false GREEN

**Status:** IN PROGRESS · **Severity:** HIGH

W80R.1, 2026-10-16. The budget probe (`runtime_registry.probe_local`) picked the running SHA with `git rev-list -1 --before=<ActiveEnterTimestamp> HEAD`, which selects commits *dated* before the start even when they were pulled after it. On the box at 15:56Z `deploy_truth` (exact SHA from `logs/vps_deploy_decisions.jsonl`) read **ALARM t4-mlb runs dc84fa6c; 2 imported files changed (demo_fill_policy.py, paper_trader.py), 11.0h old**, while the budget read t4-mlb 0.0h behind and GREEN. The W80P.1 capture was installed through the bridge on that false GREEN (Hard Rule 14 breach, unintended). Same defect class as GG-915 (two definitions of one fact); W80P.1's sweep unified "which files" but not "which SHA". Fix (W80R.1 PR): the probe uses `deploy_truth.sha_at` + `unapplied_changes`; `capture_uninstall` bridge task removes the capture until the red clears; regression test. Open item: the real red — t4-mlb running code 11h behind on two files it imports — needs an idle-window restart (standing authorization 2026-10-08) by the window; why GG-432's restart did not fire for those files is not yet diagnosed.

### GG-1000 — PFR advanced passing is not capturable by a plain GET (Cloudflare 403); the source card says CAPTURABLE

**Status:** OPEN · **Severity:** LOW

W83.1 (2026-10-22). `https://www.pro-football-reference.com/years/2026/passing.htm` returns a Cloudflare 403 to an anonymous GET from both the operator's Mac and the box. The Muse source card's CAPTURABLE verdict (commented-out table in raw HTML) holds only for a browser fetch. Not captured; a headless browser on the box is outside W83.1's permissions. Action: Muse re-labels the card browser-only (TO_MUSE entry 2026-10-21 W83.1); close when a free non-browser route is found or the card is re-labelled and the one-off schedule is set.

### GG-1001 — A newly registered cron is RED against the surface budget until its first write, so its own installer refuses to install it

**Status:** OPEN · **Severity:** LOW

W83.1 (2026-10-22). `source_capture_install.py` refused: the registry entry for the not-yet-installed cron reported `STALE ... no write found` (its log did not exist), and the installer gates on budget GREEN. Worked around legitimately by running the job once (`--log`) before the install. Same shape as the W82.1 passyds refusal. Fix: a first-run bootstrap step in the install protocol, or a registry `not_installed_yet` state that is not counted STALE. Pattern sweep: `thin_capture_install.py` and `passyds_install.py` have the same gate.

### GG-1260 — NBA game-level Kalshi price history is not stored: the W88.3 pull of 1,228 games was kept only as aggregates, so no NBA factor's share priced can be measured

**Status:** OPEN · **Severity:** MEDIUM

W89.3, 2026-10-27. The unpriced-share screen (`12_EXPLORATORY/unpriced_screen/results_W89.md`) covered NFL only. NBA has no stored per-game close, and the pace/availability/lineup terms are not stored point-in-time either. Rebuild with `12_EXPLORATORY/market_history/fetch_game_hourly.py` (public GETs, free) and save the per-game table. Next undone part of W89.3.

### GG-1261 — NFL venue (N13) and weather (N14) have no out-of-sample per-game points term, so their share priced cannot be screened

**Status:** OPEN · **Severity:** LOW

W89.3, 2026-10-27. `20261011_nfl_totals_venue_weather` tests fixed league strikes, not a per-game term against the line. A rolling-origin ridge contribution in points, from schedule roof/surface/temp/wind, would let the screen run. Free data.

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

---

### GG-232 — ADR-0054(a) staffing gap: three named-not-staffed follow-ons (replay-harness `market_type=`, cell-unaware ledger/monitor tooling) sat unstaffed from sign-off to this entry

**Status:** IN PROGRESS · **Severity:** MEDIUM

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-232 |
| Category | Process gap — an ADR sign-off elevated three §8 follow-ons from "named" to "required STAFFED," and no session picked them up between sign-off and this one |
| What was missed | `ADR-0054` §8 named eight follow-on tasks as "not staffed here." §9's 2026-08-26 sign-off on item (a) elevated three of them (§8 items 1, 2, 4) to required STAFFED follow-ons, with item 4 (`replay_harness_t427.py`'s silent `market_type` default, GG-184) flagged PRIORITY because it "produces confidently wrong output rather than a visible error." No task claimed any of the three between the 2026-08-26 sign-off and this entry (2026-09-01, T-509) — five days where the priority item's silent-default failure mode remained live and undetected-by-design in the replay harness. |
| When it should have been caught | Immediately at ADR-0054(a) sign-off (2026-08-26) — a signed condition that elevates named tasks to required-staffed should itself produce the staffing (a claim row / GG entry), not merely a sentence in the ADR. |
| Phases it survived | 2026-08-26 (sign-off) → 2026-09-01 (this entry): 5 days, at least one intervening session's worth of ADR-0054-adjacent work (item (c) and other §8 items were not separately gap-logged either) without a GG entry making the staffing gap itself visible in the tracked backlog. |
| Why it survived | Sign-off conditions recorded inside an ADR's own prose are not cross-referenced against `GOVERNANCE_GAP_LOG.md` by any automated check — the same class of gap as GG-230 (a flagged finding sitting in a document nothing re-surfaces). Nothing forces a signed "must be staffed" condition to immediately spawn its own tracked entry. |
| Impact | MEDIUM. Item 4's silent `market_type` default (GG-184) is confirmed live in `scripts/replay_harness_t427.py::replay_one()` as of this session's investigation — every replayed position was silently attributed to `MLB_PLAYER_PROP_HITS` regardless of its true market type, producing passing-looking replay diffs that never actually verified the field. Items 1/2 (band-scoped, not cell-scoped tooling) under-report coverage against the current 78-cell `(MarketType, ExecutionBand)` registry without raising any alarm, since both tools were built before the registry moved past a single-market-type shape. |
| Discovery | 2026-09-01, T-509 (this session), assigned directly to staff all three items per the operator's task brief; the absence of any prior GG/T claim for these three items across the 2026-08-26→2026-09-01 window was confirmed by grep against `SESSION_CLAIMS.md` and this log before starting implementation. |
| Resolution | This session (T-509) stages the fix directly — see `DECISION_LOG.md` 2026-09-01 for the three items' before/after detail. Registering this entry first (per the operator's explicit "write and push as first commit" instruction) so the staffing gap is documented independently of the fix, matching this log's own stated invariant. **2026-09-01 update:** all three §8 items now implemented, tested, and committed on `session/20260901T052401Z-t509-adr0054a-cell-awareness`: item 4 (`8e3182d`) makes `replay_harness_t427.py` pass `market_type=` explicitly to `open_position()`, with a test that fails on the old silent-default behavior; item 2 (`386c6a0`) makes `run_band_monitor.py` cell-aware; item 1 (`066bc8b`) makes `assert_ledger_invariants.py` cell-aware (see `DECISION_LOG.md` 2026-09-01 for the full before/after violation-count comparison against real pulled VPS data). Full suite green: 3001 passed / 28 skipped / 0 failed post-rebase onto `origin/main`. Branch pushed. Awaiting merge to `main`. |
| Status | IN PROGRESS — implementation complete and pushed to the session branch; will move to RESOLVED once merged to `main` by a subsequent session (this session's scope did not include merging). |

</details>

---

### GG-243 — T-number collision: "T-518" independently claimed by two unrelated tasks (TODO_NEXT.md's EXP-026 entry vs. this session's ADR-0060/0061/0062 re-recording)

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Same family as GG-256: claim_session.sh has pre-claim check but no atomic reservation. **Next:** Close with GG-256.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-243 |
| Category | `claim_session.sh` T-number collision — the exact failure mode Hard Rule 10/GG-082's atomic-claim mechanism exists to prevent, observed anyway. |
| What was found | `04_EXECUTION/TODO_NEXT.md` line 16 has a `## T-518 — Execute EXP-026 (HYP-011 moneyline-first LR track)` entry, registered 2026-09-03 by T-517, OPEN/unstaffed. This session (worktree `session/20260904T000244Z-rerecord-adr-signoffs`) independently claimed T-518 for a wholly unrelated deliverable — re-recording ADR-0060/0061/0062 operator sign-offs after T-512/PR #126 was stranded (GG-240) — and closed it under that same number (`04_EXECUTION/SESSION_CLAIMS.md` row, 2026-09-03T21:45:00Z). Both claims are real, both reference genuine work; the number was simply assigned to two different tasks. |
| When it should have been caught | At claim time, by `scripts/claim_session.sh`'s atomic reservation — the same mechanism that prevented the 2026-07-07 T-247 race this script was built to fix. |
| Phases it survived | Not caught by this session's own Step 0c (read last ~24h of SESSION_CLAIMS.md) — the EXP-026 T-518 registration was a TODO_NEXT.md entry, not a same-day SESSION_CLAIMS row, so a claims-log-only reconciliation check would not surface it; only cross-referencing TODO_NEXT.md's own task headers against the claimed number catches it, which is not currently part of the claim-time check. |
| Why it survived | `claim_session.sh` appends to `SESSION_CLAIMS.md` with rebase-retry, which protects against two *concurrent* sessions racing the same number, but does not check `TODO_NEXT.md` for a task header already using that number registered by a *prior*, already-closed session (T-517 registered the T-518 EXP-026 entry as a forward-looking unstaffed task, not a live claim row at registration time). |
| Impact | LOW — no work was lost or conflated; both tasks' content is fully intact and independently correct. Risk is purely narrative confusion for a future session trying to resolve "T-518" from context (e.g., TODO_NEXT.md vs. SESSION_CLAIMS.md vs. DECISION_LOG.md would each point to a different task under the same number). |
| Discovery | 2026-09-04, this session, during `/session-end` Step 2 (about to update TODO_NEXT.md for T-518) — found the existing T-518 header referred to EXP-026, not the ADR re-recording this session performed. Registered per Hard Rule 11 (register and stop on discovery) — renumbering either task is out of scope for this session's declared deliverable. |
| Resolution | Not started. Future task: renumber one of the two T-518s (likely the EXP-026 entry, since it is still OPEN/unstaffed and has no commits/closure rows yet, vs. this session's T-518 which is already CLOSED with full commit history under that number) to the next free T-number, and update its TODO_NEXT.md header accordingly. Consider whether `claim_session.sh` should also grep `TODO_NEXT.md` task headers for the candidate number before assigning it, to close this specific gap in the atomic-claim mechanism. |
| Status | OPEN. |

</details>

---

### GG-253 — No NFL C1 ingestion module exists; the only generic `team_stats_store.py` is NBA-shaped (`plus_minus`-derived) and not usable as an NFL feature source

**Status:** PARTIALLY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-253 |
| Category | Missing sport-specific C1 layer — per CLAUDE.md's own architecture description, C1/C2 are the only layers a new sport is supposed to require; NFL has neither. |
| What was found | `c1_signal_ingestion/` contains `mlb_ingestion.py`, `mlb_team_stats_store.py`, `mlb_pitcher_stats_store.py`, `ds02_nba_live.py` — no NFL module of any kind. The one plausibly-reusable generic file, `c1_signal_ingestion/team_stats_store.py`, is NBA-shaped throughout on direct read: its docstring states "Phase 7 (Strategy B — opponent defensive rating feature, T-075)", it is built from `NBAIngestionClient.fetch_team_game_log()`, and its core computation (`pts_allowed = pts - plus_minus`) is an NBA box-score derivation with no NFL analogue (`plus_minus` is not a standard NFL per-game stat). An LR moneyline forecast for NFL needs, at minimum: team offensive/defensive efficiency (rolling, recency-weighted), rest days, home/away, and ideally strength-of-schedule. Public sources cover this (`nflverse`/`nflfastR`-derived play-by-play and schedule data, or ESPN's public NFL endpoints — the same class of public source `ds02_nba_live.py` already demonstrates this codebase knows how to consume, for a different sport) — the data exists publicly; the ingestion module to pull and shape it into C2-ready features does not. |
| When it should have been caught | At any point NFL was discussed as a coverage-expansion target (COVERAGE_TARGET_MATRIX.md, ADR-0062) without a corresponding C1 module existing or being scoped. |
| Phases it survived | All NFL-related work to date (market-type registry seeding, ADR-0062 ExecutionBand scaffolding, GG-245's price-archiver addition) has operated at the market/execution-band layer; none of it required or built a C1 feature-ingestion layer. |
| Why it survived | NFL coverage work so far has been schedulable independent of C1 (registry entries, price archiving, T4 band scaffolding) — none of those tasks required team-level statistics, so the absence never blocked anything until a pregame *forecast* was actually attempted, which this audit is the first to trace end-to-end. |
| Impact | HIGH — this is Step 2 of the six-step trace (Model input) and a hard blocker: no NFL LR forecast can be trained or run without team-level input features, and none exist today in any usable form. |
| Discovery | 2026-09-07, T-525 (this session), NFL pregame-moneyline readiness audit, Step 2 of the six-step trace — confirmed via direct listing of `c1_signal_ingestion/` and full read of `team_stats_store.py`. Register-and-stop per Hard Rule 11. |
| Resolution | PARTIALLY RESOLVED, 2026-09-07, T-526 (this session, worktree `session/20260907T234557Z-nfl-c1-ingestion`). Built the C1 half only, scope-fenced per this session's claim (HYP-011/EXP-026 pre-registration; C2 wiring and model fitting are explicitly out of scope here). Added `c1_signal_ingestion/nfl_ingestion.py` (`NFLIngestionClient`: `fetch_schedule`/`fetch_team_stats`/`fetch_team_stats_bulk`, modeled on `mlb_ingestion.py`'s fetch/cache/throttle-retry shape) and `c1_signal_ingestion/nfl_team_stats_store.py` (`NFLTeamStatsStore`, modeled on `mlb_team_stats_store.py`'s build-from-source/TI-01/to-from-cache-dict shape). Source: `nflverse/nflverse-data` (MIT-licensed) `schedules` and `stats_team_week_<season>` releases — chosen over ESPN's public NFL endpoints. Minimum feature set only, per this session's scope: team off_epa/def_epa_allowed (recency-weighted exponential-decay rolling mean, `DEFAULT_DECAY=0.85`, half-life ≈4.3 games — a deliberate deviation from MLB's plain rolling mean, since NFL's 17-game season makes recency matter more over an 8-game window), rest days, home/away. Strength-of-schedule explicitly deferred, not built — follow-on only. Cold start (Week 1, zero current-season games) handled with no special-case branch: query methods take no `season` parameter, filter strictly on `game_date < as_of_date` (TI-01) across all loaded seasons, so `tail(window)` naturally pulls prior-season carryover; a team with zero games anywhere returns `None`. Dedicated `TestColdStartCarryover` tests cover this, including a structural assertion via `inspect.signature` that no `season` parameter exists on the query methods. 42 new tests added in `tests/test_t526_nfl_c1.py`; full suite 3057 passed / 28 skipped / 0 failed. Ran `check_feature_column_health.py` against the new module's output: exits clean (0) but does not meaningfully exercise it — the script's real purpose is validating a materialized C2 feature matrix, which does not yet exist for NFL; this is an unresolved C1/C2 boundary tension, noted in `DECISION_LOG.md` but not separately registered as its own gap (a fresh GG-number collision check across branches was not performed for it in this scope-fenced session). Still open, unresolved by this session: the C2 feature-derivation wiring this gap's original resolution text also called for — that remains a separate follow-on task, not built here. See `DECISION_LOG.md` 2026-09-07 (T-526/GG-253 entry) for full narrative, and GG-256 for a concurrent, disjoint-scope T-526 claim-number collision discovered by a sibling session during this same window. |
| Status | PARTIALLY RESOLVED — C1 ingestion module built and tested; C2 feature-derivation wiring and model fitting (EXP-026) remain separate, unbuilt follow-on work. |

</details>

---

### GG-254 — No moneyline/categorical-outcome settlement logic exists anywhere in `src/`, for any sport; `paper_trader.py::settle_position()`'s threshold-crossing model cannot express a game-winner outcome

**Status:** PARTIALLY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-254 |
| Category | Missing outcome-representation concept in the shared settlement path — sport-agnostic in the sense that it blocks every sport's game-market cells identically, not an NFL-specific absence. |
| What was found | MLB settlement uses the MLB Stats API; there is no NFL equivalent, but the deeper gap is upstream of any data source. `paper_trader.py::settle_position()` (line 915, read in full) implements `yes_won = actual_stat >= threshold` — a numeric threshold-crossing pattern designed for stat-threshold markets (NBA points, MLB hits). This is structurally incompatible with a moneyline/game-winner categorical outcome ("did team X win," not "did a stat cross a number") for **any** sport, not merely NFL — MLB's own ADR-0058 T1 game-market cells (moneyline/spread/total/team-total, defined in `measurement_stake.py`'s `T1_GAME_MARKET_TYPES`) are equally blocked by this same absence and have never resolved a single bet through it. A concrete NFL data source is not the hard part: ESPN's public NFL scoreboard/summary endpoints or `nflverse` schedule+result data both return final score/winner directly. The missing piece is entirely the settlement code path — a generalized categorical-outcome resolver (covering moneyline, spread-with-line, and total-with-line) that plugs into the existing ledger/audit-log machinery the way `settle_position()` does today for threshold markets. |
| When it should have been caught | At the point ADR-0058 defined the nine T1 game-market cells (MLB's five, NFL's four) without a corresponding settlement path being built or scoped alongside them — the cells were specified in the risk/execution registry layer without confirming the settlement layer could resolve them. |
| Phases it survived | All sessions since ADR-0058's cell definitions were written; `measurement_stake.py`'s frozenset has existed with these market types listed the entire time, unexercised by any live pipeline (see GG-255), which is part of why this absence never surfaced as a live failure. |
| Why it survived | The only settlement function that exists (`settle_position()`) has worked correctly for every market this bot has actually traded to date (NBA points props, MLB hit props) — both are stat-threshold shaped, so the function's assumption was never falsified until a genuinely categorical-outcome market (moneyline) was traced end-to-end against it, which this audit is the first to do. |
| Impact | HIGH — this is Step 6 of the six-step trace (Resolution) and, per this audit's own analysis, the single largest-leverage gap found: building a fix here unblocks NFL's entire pregame moneyline/spread/total path AND simultaneously activates MLB's own currently-dormant ADR-0058 T1 game-market cells, which today sit fully defined in `measurement_stake.py` but never resolve because of this exact same absence. No other gap in this trace has that dual leverage. |
| Discovery | 2026-09-07, T-525 (this session), NFL pregame-moneyline readiness audit, Step 6 of the six-step trace — confirmed via full read of `paper_trader.py::settle_position()`. Register-and-stop per Hard Rule 11. |
| Resolution | Not started. Requires designing and building a generalized categorical-outcome settlement path (moneyline/spread/total), wiring a public NFL result source into it, and testing against real completed games. Estimated 12-18 hours (see `04_EXECUTION/NFL_PREGAME_MONEYLINE_READINESS_AUDIT_2026-09-07.md`, Step 6). |
| Status | **PARTIALLY RESOLVED, 2026-09-08, T-529 (this session, worktree `session/20260908T235534Z-land-wave20-nfl-settlement-and-c1`).** Landed `session/20260907T234611Z-nfl-game-market-settlement` (T-527, built prior session) into `main` (merge commit `c272dec`). What is now actually in the tree: `c5_execution/game_market_settlement.py` (`derive_actual_stat()` / `check_settlement_ambiguity()`) — a pure-computation adapter that derives `(actual_stat, stat_label)` for all four NFL game-market types (moneyline, spread, game total, team total) from a completed game's final score plus the position's ticker-embedded team code, then hands off to the existing, **unmodified** `paper_trader.py::settle_position()` primitive (GG-034 file-lock invariant preserved — the boolean threshold-crossing model itself was not touched, this module works around it rather than extending it). `c1_signal_ingestion/nfl_espn_results.py` supplies the final-score data source (ESPN). `scripts/apply_resolved_nfl_game_markets.py` is the resolver entry point, modeled on the existing `apply_resolved_hits.py` MLB pattern, dry-run by default. 41 tests across the three new test files, all passing; full suite after merge 3113 passed / 28 skipped / 0 failed. Discovered a genuine settlement-primitive gap in the process — a moneyline exact-tie has no representation in `settle_position()`'s boolean win/loss model (Kalshi splits tie payouts $0.50/$0.50; per Kalshi's NFLGAME.pdf Tie provision) — rather than silently mis-settling, `check_settlement_ambiguity()` raises `SettlementAmbiguityError` and the resolver refuses the position; registered separately as [[GG-257]] (OPEN), not fixed here. **What is NOT resolved, and this entry is deliberately not closed:** nothing wires this settlement path into any live or scheduled pipeline — `deploy/cron.conf` was confirmed (grep, this session) to contain zero entries invoking `apply_resolved_nfl_game_markets.py` or `game_market_settlement`, only the pre-existing NFL price-archiver cadence; `apply_resolved_nfl_game_markets.py` has been run only against a synthetic test portfolio, never a real one (explicit scope fence, both the building session and this landing session). This wiring absence is [[GG-255]]'s exact subject and GG-255 remains fully OPEN and unaffected by this landing — a working, tested settlement *module* existing is necessary but not sufficient for GG-255's "nothing is wired" finding to close. Net effect on this gap's original claim: the sentence "no settlement logic exists anywhere in `src/`, for any sport" is now factually false — settlement derivation logic exists, is tested, and is merged to `main`. The sentence "cannot express a game-winner outcome" is now false for the moneyline non-tie case and true only for the tie edge case (GG-257). What remains true and unresolved: this logic is not exercised by any live pipeline, and MLB's own dormant ADR-0058 T1 game-market cells (this gap's other stated beneficiary) are not activated by this landing either — activating them still requires the GG-255 wiring work, which is separate, unbuilt, out of scope here, and not attempted. |

</details>

---

### GG-255 — `measurement_stake.py` defines all nine ADR-0058 T1 game-market cells but has exactly one real importer codebase-wide (an audit tool); no run script or cron entry exists for any T1 game-market cell, NFL or MLB

**Status:** LIKELY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-255 |
| Category | Defined-but-unwired execution path — the cells exist in code and in the risk/execution registry but nothing in any live pipeline ever calls the module that would act on them. |
| What was found | `c5_execution/measurement_stake.py`'s `T1_GAME_MARKET_TYPES` frozenset (line 80-83) includes all four NFL market types (`nfl_moneyline`, `nfl_spread`, `nfl_game_total`, `nfl_team_total`) alongside MLB's five — the full ADR-0058 nine-cell T1 set is present in code. A precise import-statement grep (`^from.*measurement_stake import\|^import.*measurement_stake\|c5_execution\.measurement_stake`) — corrected from an initial false-positive grep that matched an unrelated locally-defined function name (`measurement_stake_and_stratum()` in `run_t4_mlb_live.py`, not an import of this module) — confirms the module's **only real importer anywhere in `src/`/`scripts/` is `scripts/assert_ledger_invariants.py`**, an audit tool, not a live trading pipeline. This confirms and extends the already-known ADR-0059 finding ("nothing wired") to all nine cells, not NFL's four specifically. There is also no NFL-specific run script (no analogue to `run_t1_mlb.py`) and no NFL entry in `deploy/cron.conf`'s scheduled pipeline invocations (distinct from GG-245, which covers only the price-archiver's capture cron, not a bet-execution pipeline). |
| When it should have been caught | At the point ADR-0059 first found "nothing wired" for measurement_stake's cells — that finding should have prompted either wiring the module into a live path or explicitly flagging every one of the nine defined cells (not just noting the general absence) as individually blocked pending that work. |
| Phases it survived | All sessions since ADR-0058/ADR-0059; the frozenset's cell definitions have existed unexercised the entire time this gap has been latent, re-confirmed but not previously itemized per-cell in this audit's terms. |
| Why it survived | `measurement_stake.py` having comprehensive cell definitions gives the appearance of readiness at the data-structure level; nothing forced a check of whether any live code path actually calls into it until this audit's explicit Step 5 instruction to check "is anything wired to call it." |
| Impact | HIGH — this is Step 5 of the six-step trace (Execution) and a hard blocker independent of Steps 1/2/3/6: even a fully-parsed NFL market, a complete NFL forecast, and a working settlement path would still have no live pipeline to route a resulting bet through, absent a run script and cron entry that actually calls `measurement_stake`. |
| Discovery | 2026-09-07, T-525 (this session), NFL pregame-moneyline readiness audit, Step 5 of the six-step trace — confirmed via corrected import-statement grep (the initial grep's false positive is itself noted here so a future session does not repeat it). Register-and-stop per Hard Rule 11. |
| Resolution | Not started. Requires wiring `measurement_stake` into a live pipeline path, writing an NFL run script modeled on the MLB T1 pattern, adding a cron entry, and an end-to-end smoke test. Estimated 8-12 hours (see `04_EXECUTION/NFL_PREGAME_MONEYLINE_READINESS_AUDIT_2026-09-07.md`, Step 5). |
| Status | OPEN. |
| Update 2026-09-08 (T-530) | Built and paper-tested the NFL half of this gap: `src/prediction_market_bot/run_t1_nfl_game_market.py`, a new run script covering all four NFL T1 game-market cells (`nfl_moneyline`/`nfl_spread`/`nfl_game_total`/`nfl_team_total`). Pipeline wired end to end: `KalshiMarketClient.fetch_game_markets()` → an INJECTABLE model interface (default `StubNFLForecastModel` — explicitly NOT a trained model; no NFL C2/C3 layer exists) → `RiskEngine.evaluate_forecast()` (ADR-0050 `fixed_stake_usd` bypass, `kelly_fraction` untouched) → `t1_measurement_stake_and_stratum()` (live-measured haircut via `GameMarket.half_spread`, not a hardcoded figure) → `PaperTrader.open_position()`, with `PaperTrader` constructed `kalshi_client=None` unconditionally as the sole mechanical guard against a live-order path. `market_type_registry.resolve_kill_switch_state()` wired as a READ-side check ahead of every per-market evaluation; `halt_cell()` remains uncalled by any shipped path — the write side of the cell-tier kill switch is still unwired, unchanged from before this session. Four refusal-path tests added (`tests/test_run_t1_nfl_game_market.py`): kill switch active, no model available, GG-252 unparsed-market snapshot, GG-257 exact-tie NFL moneyline settlement ambiguity. Full suite: 3117 passed, 28 skipped, 0 failed. **What remains open, explicitly out of this session's scope fence:** no cron entry was added (`deploy/cron.conf` untouched — this script is manually invoked only); the MLB half of the nine-cell set (`mlb_moneyline`/`mlb_run_line`/`mlb_game_total`/`mlb_team_total`/`mlb_partial_game`) still has no run script; no cell was promoted out of `NOT_IMPLEMENTED`; the model wired by default is a stub, not a trained forecaster, so no real forecast has ever flowed through this path. See DECISION_LOG.md 2026-09-08 for the session's full DO-NOT constraint list. |
| Update 2026-09-11 (T-538) | Built and paper-tested the MLB half of this gap, mirroring T-530's NFL disposition exactly: `src/prediction_market_bot/run_t1_mlb_game_market.py`, a new run script covering all five MLB T1 game-market cells (`mlb_moneyline`/`mlb_run_line`/`mlb_game_total`/`mlb_team_total`/`mlb_partial_game`). `KalshiMarketClient.fetch_game_markets()` generalized to MLB's series (`KXMLBGAME`/`KXMLBSPREAD`/`KXMLBTOTAL`/`KXMLBTEAMTOTAL`/`KXMLBF3`/`KXMLBF5`/`KXMLBF7`) with **zero functional code changes** — confirmed by direct read that the method delegates entirely to `_parse_market()`'s series dispatch; only a docstring correction landed (commit `8d097d2`). Zero-regression re-verified on the one band currently trading live: `KXMLBHIT` prop parsing held at 477/477 before and after, identical in kind to T-526's original 286/286 precedent. `PaperTrader` constructed `kalshi_client=None` unconditionally, same structural guard as the NFL script. This script's three-way approval branch (KILL_SWITCH / REJECTED / APPROVED) explicitly avoids `run_t4_mlb_live.py:1364`'s defect (which collapses KILL_SWITCH into the same `!= "APPROVED"` check as an ordinary rejection and keeps evaluating subsequent markets after a kill switch has fired) by self-halting distinctly on KILL_SWITCH. Five refusal-path tests added (`tests/test_run_t1_mlb_game_market.py`): kill switch active, no model available, GG-252/GG-255 unparsed-market snapshot, settlement ambiguity (`check_settlement_ambiguity()` correctly raises plain `ValueError` for MLB market types, since `game_market_settlement.py`'s `_SUPPORTED_MARKET_TYPES` is NFL-only and out of this session's scope to extend), plus a fifth MLB-specific test proving via a `builtins.open` monkeypatch guard that the script never opens `paper_portfolio_mlb.json` or `paper_portfolio_mlb_t4.json` (the two live MLB ledgers). Full suite post-rebase onto `origin/main`: 3148 passed, 28 skipped, 0 failed. **What remains open, explicitly out of this session's scope fence:** no cron entry was added; no cell was promoted out of `NOT_IMPLEMENTED`; the model wired by default is `StubMLBGameMarketForecastModel`, not a trained forecaster; `game_market_settlement.py` was not extended to support MLB settlement (MLB's partial-game TIE semantics genuinely differ from NFL's tie-as-split and need their own scoped design, not an incidental extension here) — MLB game-market positions, if ever opened live, cannot yet be settled through this path. **All nine ADR-0058 T1 game-market cells now have a paper-only run script (NFL: T-530; MLB: T-538). Reclassifying the "no run script exists" finding specifically from PARTIALLY RESOLVED to LIKELY RESOLVED** — the remaining open surface (no cron wiring, no live model, no MLB settlement path, cell-tier kill switch write-side still unwired) is now cron/model/settlement work, each its own scoped follow-on, not a continuation of this gap's original "script doesn't exist" finding. See DECISION_LOG.md 2026-09-11 for this session's DO-NOT constraint list and settlement-ambiguity test design reasoning. |

</details>

### GG-256 — `scripts/claim_session.sh`'s rebase-retry did not prevent a duplicate T-number claim; two concurrent sessions both claimed T-526 one second apart

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** scripts/claim_session.sh already runs check_id_collision pre-claim (l.55-62) and fetches all origin branches (GG-236), but no atomic reservation exists, so two pushes one second apart can still both pass. **Next:** Add a push-time re-check after rebase, failing the claim on duplicate.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-256 |
| Category | Concurrent-session claim-atomicity gap (T-number analogue of GG-162, which covers the equivalent GG-number gap). |
| What was found | `04_EXECUTION/SESSION_CLAIMS.md` on `origin/main` shows `2026-09-07T23:46:36Z \| T-526, GG-252 \| ...fix GG-252...` immediately followed by `2026-09-07T23:46:37Z \| T-526, GG-253 (resolving) \| ...NFL C1 ingestion module...` — two different concurrent sessions both claimed the literal number T-526 for two unrelated deliverables, one second apart. Per this file's own documentation, `claim_session.sh` is supposed to append-commit-push with rebase-retry specifically to prevent this (the 2026-07-07 T-247 race this mechanism was built to close). It did not prevent it here — most likely both sessions read the last-used number before either had pushed its own claim commit, so the retry only protects the commit landing, not the number-selection read. No data was lost (`SESSION_CLAIMS.md` is `merge=union`, both rows persist) and no file collision resulted (the two sessions' actual work — `kalshi_client.py` vs. a new C1 ingestion module — does not overlap), so this is a labeling/traceability defect, not a destructive one. |
| When it should have been caught | At claim time, by the rebase-retry logic itself, before either session began substantive work under the ambiguous number. |
| Phases it survived | N/A — first observed instance of this specific race for T-numbers; the analogous GG-number race (GG-162/GG-199) was already known and documented, but this file did not previously record a T-number instance. |
| Why it survived | The rebase-retry protects the push of the claim row, not the read of "what is the next free number" — two sessions starting within the same ~1s window can both compute the same next number before either's push lands, identically to the root cause already described for GG-162. |
| Impact | LOW — no work was lost or overwritten; this session (T-526/GG-252) and the concurrent one (T-526/GG-253) touch disjoint files. Purely a traceability/audit-log ambiguity: `SESSION_CLAIMS.md` and any future `git log`/`grep T-526` search will show two unrelated deliverables under one number. |
| Discovery | 2026-09-07, this session (T-526/GG-252, worktree `session/20260907T234550Z-gg252-nfl-parser`), noticed while fetching `origin/main` before push and diffing `SESSION_CLAIMS.md`. Register-and-stop per Hard Rule 11 — not fixed in this session, out of this session's scope fence (`kalshi_client.py` and its tests only). |
| Resolution | Not started. Same class of fix as GG-162's stated remaining work: atomic T-number reservation (e.g. a lock file or server-side counter) rather than read-then-append-then-push, would need to close both the GG- and T- number races together since they share the same root cause. |
| Status | OPEN. |

</details>

---

### GG-257 — `settle_position()`'s boolean win/loss model cannot express Kalshi's $0.50/$0.50 split payout for an NFL moneyline exact tie

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** paper_trader.py settle_position still computes boolean yes_won (l.912, 1009, 1101); no split-payout path. **Next:** Add a split-payout settlement path.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-257 |
| Category | Settlement-primitive expressiveness gap — narrow and sport-agnostic in principle (would apply identically to a hypothetical MLB extra-innings-suspended tie), found while building the T-527 game-market settlement adapter. |
| What was found | `paper_trader.py::settle_position()` (line ~915/954) computes `yes_won = actual_stat >= threshold` — a strict boolean win/loss payout. Kalshi's KXNFLGAME contract terms (`NFLGAME.pdf`, "Tie" provision — see below) state that a tied NFL game settles the moneyline market as a $0.50/$0.50 split payout on each side, not a single winner. A boolean `>=` model has no way to express a split payout: under `>=`, an exact tie (point margin == 0) would settle moneyline YES, which is wrong per Kalshi's actual rule. This is a genuine, narrow expressiveness gap in the settlement primitive itself, not something T-527 needed to fix to deliver its scope (a derivation module + NFL result fetcher + resolver script, all of which stop short of calling `settle_position()` on an ambiguous case). |
| When it should have been caught | At the point `settle_position()`'s boolean model was first extended toward any categorical/game-winner market type (ADR-0058's T1 game-market cell definitions) rather than remaining scoped to stat-threshold markets (NBA points, MLB hits), where a tie is not a possible outcome and this gap cannot surface. |
| Phases it survived | ADR-0058's nine T1 game-market cell definitions (`measurement_stake.py`) have existed unexercised the entire time (see GG-255) — this gap was latent and never triggered because nothing has ever called `settle_position()` for a moneyline-shaped market until this build's tests. |
| Why it survived | `settle_position()` has worked correctly for every market type actually settled to date (NBA points props, MLB hit props) — both are stat-threshold shaped with no tie/push concept, so the boolean assumption was never falsified until a categorical moneyline settlement path was built and traced against a real tied game (DAL 40 - GB 40, 2025 season) during T-527. |
| Impact | LOW — the gap is fully contained and does not silently mis-settle anything: `c5_execution/game_market_settlement.py::check_settlement_ambiguity()` (lines 206-215) detects the exact-tie case (`actual_stat == 0` for NFL_MONEYLINE) and raises `SettlementAmbiguityError` rather than allowing the resolver script to call `settle_position()` on it — see `scripts/apply_resolved_nfl_game_markets.py`'s REFUSED path, tested in `tests/test_apply_resolved_nfl_game_markets.py::test_main_moneyline_tie_refused_even_under_apply`. Impact would rise to HIGH only if a future caller invoked `settle_position()` directly on a tied moneyline position without going through this ambiguity check. |
| Discovery | 2026-09-07, T-527 (this session), NFL game-market settlement build — confirmed via direct read of `paper_trader.py::settle_position()` (line ~915/954) and Kalshi's official `NFLGAME.pdf` contract-terms PDF, "Tie" provision (split $0.50/$0.50 payout on a tied game). Register-and-stop per Hard Rule 11 — T-527's scope explicitly excludes modifying `settle_position()` itself absent a genuine defect requiring a STOP-and-report; this is registered rather than fixed in-session for that reason. |
| Resolution | Not started. Would require extending `settle_position()` (or adding a sibling primitive) to accept a non-boolean, split-payout outcome — a change to the ledger-mutation code under the GG-034 file-lock invariant, requiring its own scoped review rather than an incidental fix inside T-527. Until then, the correct behavior is exactly what T-527 built: detect and refuse (`check_settlement_ambiguity()`), never guess a side. An NFL regular-season tie is rare but real (~1/season), so this is a live, if infrequent, real-money-shaped gap once a live NFL portfolio exists (T-527 explicitly does not settle any real position; wiring to live data is task 21.1). |
| Status | OPEN. |

</details>

---

### GG-261 — T-528's capture-fidelity "zero coverage gaps" verdict tested kickoff-instant coverage only, not pregame-window coverage; missed the day-3 (Wed UTC) NFL price-archive gap

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** deploy/cron.conf l.352-385 documents the NFL archiver and a Thu 0-3Z window added 2026-09-05 after a schedule audit; that audit checked kickoff instants only. No pregame-window coverage re-audit found. **Next:** Re-audit pregame-window coverage of the NFL archive against actual archive timestamps.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-261 |
| Category | Audit-methodology gap — the underlying kickoff timestamp used was correct; the check's *definition of coverage* was too narrow for what the task actually needed. |
| What was found | T-533 (this session) was tasked with verifying the day-of-week field of every NFL price-archive cron line in `deploy/cron.conf` against a 6-hour-pregame + 1-hour-post-kickoff capture requirement (kickoff-6h through kickoff+1h). The task brief itself assumed the opener's kickoff was 2026-09-10T00:20:00Z and that T-528's capture-fidelity audit (`04_EXECUTION/NFL_WEEK1_CAPTURE_FIDELITY_2026-09-08.md`) had computed its GO verdict from a *wrong* 03:20:00Z timestamp. Direct verification against a live source (re-queried `GET /trade-api/v2/markets?tickers=KXNFLGAME-26SEP09NESEA-NE`, the same `occurrence_datetime` field/method T-521 and T-528 both used) returned **2026-09-10T03:20:00Z**, confirming T-528's timestamp was correct all along and the task brief's own 00:20Z assumption was the error (most likely a 3-hour operator transcription slip: 20:20 Pacific written as 17:20 Pacific — 20:20 Pacific = 03:20 UTC Thursday exactly, and 20:20 minus 17:20 is exactly the 3-hour discrepancy the task flagged). So the real finding is not a wrong-clock audit: T-528's Deliverable 4 verdict ("32/32 events fall inside a scheduled window, zero coverage gaps found") is accurate on the narrower question it actually tested — does the kickoff instant fall inside some firing window — but that is not the same question as "is there full pregame price history before kickoff," which is what this task's 6-hour-pregame framing, and T-528's own stated task deadline framing ("before kickoff... the actual opener"), care about. Testing only the kickoff instant left a real, confirmed gap invisible: no day-3 (Wednesday UTC) cron line existed at all (`grep -n "KXNFL" deploy/cron.conf` before this session's edit showed day-of-week fields exactly 0,1,2,4,5 — no 3), so the Wed 21:20Z-23:59Z portion of the opener's pregame window (kickoff-6h through kickoff, i.e. 2026-09-09T21:20Z through 2026-09-10T03:20Z) was entirely uncaptured. |
| Why it matters | This is exactly the un-backfillable-data failure mode both GG-245/T-521 and T-528 itself were built to prevent — once a day passes, its price history cannot be reconstructed. T-528 returned GO on 2026-09-08, one day before the affected window, and the gap would have run through the actual opener with nobody the wiser, because the audit's own "zero coverage gaps" language reads as if it answers the pregame-history question when it only answers the kickoff-instant question. A GO verdict whose scope is narrower than its own stated framing implies is a governance-audit-quality gap, not just a missed cron line. |
| Discovery | 2026-09-09, T-533 (this session), Deliverable 1 — direct `grep -n "KXNFL" deploy/cron.conf` audit plus a fresh live Kalshi API query, cross-checked against both `deploy/cron.conf`'s own comment block (lines 374-377, already stated 03:20Z) and T-528's audit doc (which also independently derived and stated 03:20Z at its own Deliverable 4). All three sources agree; only the task brief's own framing and this session's own earlier (pre-compaction) WebSearch-based conclusion disagreed, and both were wrong. |
| Resolution | This session (T-533) added a 6th NFL price-archive cron line, `5,25,45 17-23 * * 3` (Wed 17:00-23:59Z, comfortably spanning the required 21:20-23:59Z window with several bonus pregame hours), matching the four existing KXNFL series, `--out exp_output/PRICE_ARCHIVE`, and log target, with `--depth-sample-per-family 1` applied directly (consistent with this session's separate GG-259 depth-capture change). See `deploy/cron.conf`'s GG-261 addendum comment (immediately above the NFL cron lines) for the full evidentiary note. The Thu 04:00-04:20Z tail (kickoff+40m to +1h, also uncovered by the existing `0-3 * * 4` window) is assessed but deliberately NOT changed under this gap — recommend extending that window to `0-4` in a future session. |
| Cross-references | [[GG-260]] (same-session, different drift condition — stale `ACTIVE_QUEUE.md`, not conflated with this). [[GG-259]] (NFL depth-sampling gap, closed same session — see its own entry for the `--depth-sample-per-family 1` verification). T-528's audit doc and GG-245/T-521 are cited as sources, not re-opened — their timestamp and series-coverage findings were correct; only the pregame-window scope of "coverage" was the gap. |
| Status | OPEN — the day-3 line lands with this session's Deliverable 1 commit; OPEN reflects that the audit-methodology gap (narrow "coverage" definition) itself is not structurally fixed — a future capture-fidelity audit could repeat the same narrow framing on a different sport/window without a definitional correction to what "coverage" must mean for a pregame-history capture task. |

</details>

### GG-262 — Live VPS crontab's `run_mlb_pregame.py` schedule (`20 21 * * *`) diverges from repo `deploy/cron.conf`'s value (`30 16 * * *`); origin/cause not determined

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Drift persists and has moved: live crontab has run_mlb_pregame at 45 18 * * * (read-only crontab -l, 2026-10-08) vs deploy/cron.conf 30 16 * * *. Tracked for fix as GG-498. **Next:** Handled under GG-498 (Part C, not done in this session).

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-262 |
| Category | Deploy-drift — live infra vs. repo source of truth. |
| What was found | While deploying T-533's NFL price-archive cron changes to the VPS, a full `crontab -l` vs. `deploy/cron.conf` diff surfaced one unrelated divergence: `run_mlb_pregame.py` is scheduled `20 21 * * *` on the live VPS crontab but `30 16 * * *` in the repo's `deploy/cron.conf`. Origin (stale VPS, stale repo, or an intentional un-synced hand-edit) not investigated. |
| Why it matters | MLB pregame cron timing affects T1 MLB signal freshness; an unexplained live/repo mismatch on an ACTIVE-pool cron line warrants a look even though this session's scope explicitly excluded MLB changes. |
| Discovery | 2026-09-09, T-533 (this session), VPS deploy step — full crontab diff during targeted NFL line replacement. |
| Resolution | Not investigated or touched — explicitly out of this session's "no MLB line changes" scope fence. Register-and-stop per Hard Rule 11. |
| Status | OPEN — needs a future session to determine which value (VPS live or repo) is correct and reconcile. |

</details>

---

### GG-266 — Local dev machine's system Python (3.9.6/LibreSSL 2.8.3) cannot TLS-handshake with ESPN's scoreboard endpoint; affects every existing `integration`-marked live-network test, not just this session's new one

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Local Python is still 3.9.6; TLS limitation not re-tested. **Next:** Use a newer interpreter for integration tests.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-266 |
| Category | Local dev-environment limitation, not a code defect. |
| What was found | T-535 (this session) added a new `@pytest.mark.integration` test (`tests/test_nfl_espn_results.py::test_fetch_final_score_live_real_game_2025_10_05`) making a genuine, unmocked network call against ESPN's real scoreboard endpoint. It fails on this machine with `SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol'))` after the full 5s/10s/30s retry+give-up schedule. Root cause confirmed: `/usr/bin/python3` on this machine is Python 3.9.6 linked against **LibreSSL 2.8.3** (`python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"`), which cannot complete a TLS handshake with ESPN's current server-side TLS configuration; `curl` against the identical URL succeeds because it uses a different/newer TLS stack. No project `.venv`/`venv` exists in this worktree to route around the system interpreter. This is not new or specific to the new test: re-running the 5 pre-existing `integration`-marked live-network tests already in this repo (`tests/integration/test_mlb_api_connectivity.py`'s 14 network-touching cases, both MLB Stats API and ESPN) shows the identical `SSLEOFError` on every one of them (14 failed / 7 skipped in that file alone). |
| Why it matters | `pyproject.toml`'s `addopts` has no `-m "not integration"` exclusion, so a bare `pytest` invocation on this machine already silently fails ~14+ pre-existing integration tests before this session touched anything — a standing, previously-undocumented condition. Anyone running the full suite locally (not on the VPS/CI) will see these failures and could mistake them for a real regression if the cause isn't on record. |
| Discovery | 2026-09-09, T-535 (this session), Deliverable 3 — discovered while verifying the new live-network test; confirmed cross-cutting (not novel to this session's code) by running `tests/integration/test_mlb_api_connectivity.py` directly and observing the identical failure signature. |
| Resolution | Not attempted — out of this session's scope fence (game_market_settlement.py / nfl_espn_results.py / apply_resolved_nfl_game_markets.py / their tests only). Fixing this machine's Python/LibreSSL linkage (e.g. installing a `.venv` against a Homebrew Python built against OpenSSL 1.1.1+/3.x) is a local-environment task, not a repo code change. Register-and-stop per Hard Rule 11. |
| Status | OPEN — needs a future session (or the operator, out-of-band) to provision a working local Python/TLS stack (or document that `integration`-marked tests are VPS/CI-only in this environment) if local `integration` runs are expected to pass on this machine. |

</details>

---

### GG-275 — `lib_chain_archive.py` silently discards the prior "Last reviewed" line on every single-entry chain collapse (regression in the GG-176 fix)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified in scripts/lib_chain_archive.py l.84-128: archiving runs only when n_entries > 1; on a single-entry chain the span is replaced by the new line with no archive write, so the prior Last-reviewed text is dropped. **Next:** Archive the lone prior line too, then add a regression test.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-275 |
| Category | Tooling defect — silent data loss in a shared nav-file mechanism |
| What was missed | `scripts/lib_chain_archive.py`'s `archive_chain()` (called by `scripts/generate_session_artifacts.py` at every `/session-end` Step 6-gen, for all three of `MEMORY_BANK.md`/`TODO_NEXT.md`/`PLAN.md`) only writes the displaced "Last reviewed" line(s) to the matching `*_ARCHIVE.md` file when `n_entries > 1`. Every real nav file reaches exactly `n_entries == 1` after its first collapse — the normal, expected steady state — so this branch is the one that runs almost every session-end, not an edge case. When it runs, `archived` stays `False` (no archive write) but the nav file's single line is still unconditionally overwritten with the new current line: the old line is discarded, not archived, violating ADR-0044's "nothing is deleted" / "lossless and verifiable" guarantee. |
| When it should have been caught | At the GG-176 fix's own review/close-out — a fix that changes an unconditional-overwrite's data-loss profile should have been checked against the archive file immediately after landing, not left to a later session to discover empirically. |
| Phases it survived | GG-176 fix landed and was marked RESOLVED (Severity LOW) → an unknown number of subsequent real session-ends (confirmed: at least T-538 and T-541 on `PLAN.md`, both pre-dating this merge) each hit the `n_entries==1` path and silently dropped the prior line → surfaced only now (T-544/GG-267 merge-conflict resolution, 2026-09-11) while manually verifying PLAN_ARCHIVE.md against PLAN.md's own git history. |
| Why it survived | GG-176's own "Impact" field states "No data loss, no incorrect archival" — true of GG-176's *original* bug (a pure no-op that only caused staleness) but never re-verified against the *fixed* code's actual behavior, which now actively discards data instead of merely going stale. No test or scan checks archive-file completeness against nav-file git history. |
| Impact | Confirmed via `git log -p --follow -- 04_EXECUTION/PLAN.md` cross-checked against `git show HEAD:04_EXECUTION/PLAN_ARCHIVE.md` (this branch's own committed state, pre-merge — the loss is independent of this merge): T-538's and T-541's "Last reviewed" narrative lines are completely absent from `PLAN_ARCHIVE.md`. Same pattern independently confirmed for `TODO_NEXT_ARCHIVE.md` (missing T-538/T-541/T-543, last real entry is T-537) and `MEMORY_BANK_ARCHIVE.md` (same check, same result) during this session's merge-conflict resolution. Not permanently unrecoverable — each nav file's own git history still holds every line via `git log -p` — but the intended archive location (the file ADR-0044 designates as the durable record) is missing them, and every future session-end will keep silently dropping the next one until the code is fixed. |
| Discovery | 2026-09-11, T-544/GG-267 merge-conflict resolution (this session), while manually verifying whether T-541's/T-543's "Last reviewed" entries already existed in `PLAN_ARCHIVE.md` before resolving a real merge conflict between T-543's and T-544's competing "Last reviewed" lines on `main`. |
| Resolution | Not fixed in this session — out of scope per Hard Rule 11 (register and stop; this session's deliverable is merge-conflict resolution, not tooling repair). This session's own merge-conflict resolution works around the defect manually: T-543's displaced line is being hand-appended (not via the generator) into `PLAN_ARCHIVE.md`/`TODO_NEXT_ARCHIVE.md`/`MEMORY_BANK_ARCHIVE.md` as part of resolving this merge, specifically to avoid repeating this exact loss on the very entry that exposed it. The underlying code defect in `lib_chain_archive.py` remains unfixed and will recur on every future single-entry collapse until a follow-up task changes `archive_chain()` to archive on `n_entries >= 1` (not `> 1`) while leaving the "no archive-file write needed" console messaging judgment to that fix, not this entry. |
| Cross-references | GG-176 (RESOLVED, Severity LOW — the original staleness bug whose fix introduced this regression); ADR-0044 (Governance-Entry Splitting — the "nothing is deleted" / "lossless and verifiable" invariant this defect violates); T-538, T-541, T-543 (PLAN.md/TODO_NEXT.md/MEMORY_BANK.md "Last reviewed" entries confirmed missing from their respective archive files). |
| Status | OPEN — registered 2026-09-11 (T-544 merge-conflict resolution session). Needs a follow-up T-NNN to fix `lib_chain_archive.py`'s `n_entries > 1` condition and to backfill the confirmed-missing T-538/T-541/T-543 lines (and any others found) into all three archive files from git history, verified complete against each nav file's full commit log. |

</details>

---

### GG-279 — A code fix landing (and even fully migrating on-disk state) in a long-running service's source is not activated in that service's own running memory until it is restarted; neither session-start nor session-close-out protocol checks process-level activation vs. mere code-landing

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** grep of .claude/commands/session-end.md finds no restart or ActiveEnterTimestamp activation check; protocol gap persists. **Next:** Add a process-activation check (service ActiveEnterTimestamp later than deploy commit time) to session-end.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-279 |
| Category | Process/protocol gap — deploy-completeness blind spot, discovered while root-causing GG-271's stale "RESOLVED" disposition. |
| What was found | GG-271's 2026-09-11 fix (`MAX_REJECTED_POSITIONS=2000` ring buffer in `PaperTrader._save()`) was committed, tested, and its live migration script was run successfully against the on-disk VPS file — all real, all correct. But `t4-mlb` is a long-running Python systemd service that does not hot-reload: it kept executing the pre-fix `PaperTrader` class already loaded into its process memory. The GG-271 close-out explicitly recorded "No service was restarted" as a *positive* fact (proof the migration needed no risky action), without recognizing that the same fact meant the running process's own subsequent `_save()` calls, from stale in-memory bytecode, would not enforce the newly-added cap at all. Consequence: `rejected_positions` silently regrew from the migrated 2,000 back to 7,654 entries (15.58MB) over the following ~77h — a full recurrence of the exact defect GG-271 believed it had closed, on the exact same file, discovered only by a later strategic-window pass (2026-09-15T00:24Z) noticing the live count didn't match the "RESOLVED" narrative. |
| Why it matters | This is not specific to GG-271 — it is a structural gap in how "deployed" is verified across this project generally. Any future fix to code inside `t4-mlb`, `pmbot-web-dashboard.service`, or any other long-running process can land cleanly in git, pass all tests, even correctly migrate on-disk state, and still not be active in the running process — and nothing in the mandatory session-start protocol (Step 4's operational health check) or session-close-out currently distinguishes "code merged + on-disk state migrated" from "the live process is actually running this code." A close-out that reports RESOLVED on the former basis alone can be wrong about the latter for an arbitrarily long time, exactly as GG-271 was for ~77 hours here. |
| Discovery | 2026-09-15T00:24Z, a strategic-window queue-management pass (`04_EXECUTION/ACTIVE_QUEUE.md` rewrite, commit `fff04d0`) noticed the live `rejected_positions` count (7,654) contradicted GG-271's RESOLVED narrative and flagged it into the session queue as this session's (T-548's) task. |
| Resolution | Not fixed in this session — this session's scope (per its own claim/briefing) was to diagnose and correct GG-271's disposition, not to build new tooling; a structural fix (e.g., a Step 4 sub-check comparing each long-running service's `ActiveEnterTimestamp` against the git-commit-timestamp of its most recently merged source change, flagging any commit newer than the process's last start as "landed but not yet activated") is registered here and left for a future session to design and build. This session's own corrective action was narrowly scoped: verified (without itself restarting anything, since `t4-mlb` had already been incidentally restarted by T-542's own unrelated PR #129 close-out deploy at 2026-09-15T00:12:01Z) that the now-running process genuinely carries and enforces the GG-271 fix — via process-identity confirmation (`/proc/<PID>/cwd`+`cmdline` matching the checked-out source tree), a module re-import using the live process's own venv+cwd resolving to `MAX_REJECTED_POSITIONS=2000`, and a hold-through-a-write-cycle proof (5,680 real rejection events between 2026-09-15T00:12:42Z and 2026-09-15T04:00:08Z with `rejected_positions` held at exactly 2000 throughout) — plus took and verified a fresh backup (`paper_portfolio_mlb_t4.gg279_verify.20260915T045755Z.json.bak`). See GG-271's corrective Note for the full narrative of the incident this gap generalizes from. |
| Cross-references | GG-271 (the specific incident this gap generalizes from — its RESOLVED status was corrected in-place with a Note pointing here). GG-163 (a related but distinct process-liveness blind spot — T4's cycle-log going stale while `systemctl is-active` reported healthy; that gap is about a process silently *stopping useful work* while still running, this one is about a process silently *running stale code* while still doing useful work — different failure shapes, same root theme of `systemctl is-active`/"code merged" being insufficient proxies for "is this fix actually live"). |
| Status | OPEN — registered 2026-09-15 (T-548). Needs a follow-up T-NNN to design and build a structural Step 4 (or close-out) check comparing each long-running service's process start time against its source's most recent relevant commit, so a landed-but-not-activated fix is caught automatically rather than by chance during an unrelated queue-review pass. |

</details>

---

### GG-282 — Investigation: do the two new T1 game-market run scripts inherit the live $10 `min_bet_usd` floor instead of the paper $1.00 floor their sibling runners pass, and is T4 MLB's `kalshi_client=None` demo-order path (GG-203) load-bearing or optional?

**Status:** PARTIALLY RESOLVED (2026-09-15, T-551) — Floor A fixed and verified; Floor B investigated, decision requested via APR-0034, not decided · **Severity:** MEDIUM

**Note (T-551, 2026-09-15):** both candidate floors named at registration were confirmed real and distinct. **Floor A** (`RiskEngine` construction) was confirmed unintended and fixed same-session. **Floor B** (`paper_trader.py`'s demo-order gate, GG-203) was confirmed real but was *not* fixed in-session — Hard Rule 3 requires a superseding ADR to change a `kalshi_client=None` construction against ADR-0008, and this task's own DO NOT list forbade constructing `PaperTrader` with any `kalshi_client` at all, live or otherwise. Floor B's disposition is therefore "investigated and decision-requested," not "resolved" — see the drafted `APR-0034` and the `Resolution`/`Status` rows below for the full findings this Note summarizes.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-282 |
| Category | Registration-at-claim-time — this entry is being opened before investigation, per the gap-log invariant (register before remediation work begins), to track the session's two open questions independently of whatever the findings turn out to be. |
| What was found | **(A) CONFIRMED and FIXED.** Every `RiskEngine` construction site was quoted and read directly, not taken on trust: `run_t1_nfl_game_market.py`'s `main()` and `run_t1_mlb_game_market.py`'s `main()` both constructed `RiskEngine(logger=..., snapshot_id=..., bankroll=...)` with **no `min_bet_usd` argument at all**, silently inheriting the live default `MIN_BET_USD=10.0` (`risk.py:118`) against this task's ADR-0050 `T1_MEASUREMENT_STAKE_USD=1.00` flat stake — while every sibling runner (`run_paper_trade.py`, `run_t4_mlb_live.py`, `run_mlb_paper_trade.py`, `run_t2_mlb_sameday.py`) explicitly passes `min_bet_usd=1.0` (or `0.01`). Checked against `DECISION_LOG.md`'s T-530/T-538 entries (the sessions that wrote these two scripts): neither mentions `min_bet_usd` at all — the omission traces to no deliberate decision, ADR, or DECISION_LOG entry; it is an unreviewed gap, not a considered design choice. T-546/GG-277's empirical anchor (24/1,185 real evaluations refused `min_bet_floor`, 2026-09-15) is exactly this defect firing in production against live NFL markets. **(B) CONFIRMED, not a bug — a real, documented, but consequential design tradeoff.** `paper_trader.py`'s `open_position()` demo-order gate (`if self._kalshi and self._kalshi.has_signing_key() and kalshi_ticker:`) is exactly as ADR-0008 (ACCEPTED, 2026-05-31) designed it: demo-order submission is explicitly non-load-bearing ("Local ledger is authoritative"), degraded mode (`kalshi_client=None`) is an intentional, named operating mode with its own rollback clause (unset `VENUE_PRIVATE_KEY_PATH`, no code change required), and ADR-0008 explicitly states it does not change G6 gate criteria. Full reader census of `kalshi_order_id`/`kalshi_order_status` (whole-repo grep, not assumption): sole writer is `paper_trader.py::open_position()`; readers are `monitor.py::check_failed_order_rate` (GG-098, warn-only alarm, no auto-halt) and `scripts/assert_ledger_invariants.py` (alarm-only, gates nothing without `--strict`, which remains off). MLB's live G6 `clean_n` sample-adequacy gate — `run_band_monitor.py`'s `filter_clean()` → `logic_epoch.py:686`'s `is_clean_for_band()` — has **zero** reference to Kalshi order status anywhere in that call path; it is purely `logic_epoch`-derived. GG-203 (T4M-PROJ blocked at this exact step) is independently confirmed **IN PROGRESS (T-547) · HIGH**, root cause conclusively external (Kalshi-side), 32+ days running, with an alarm-only detector already wired into `.claude/hooks/governance_scan.sh`. |
| When it should have been caught | (A) At the point the two new T1 game-market run scripts were written, if their `RiskEngine` construction had been reviewed against their sibling runners' explicit `min_bet_usd` overrides before merge — confirmed via DECISION_LOG re-read: it was not. (B) Not a catchable defect in the same sense — ADR-0008 designed this behavior deliberately and documented the tradeoff at acceptance time; the open question was never "was this a mistake" but "given GG-203's now-32-day real-world cost, does the tradeoff still hold" — which is a live operator decision, not a historical miss. |
| Phases it survived | (A) Survived from initial authorship of both scripts (predating this session) through at least one full production run (T-546/GG-277, 2026-09-15) before this session's Deliverable 1 read every construction site directly. (B) N/A — not a defect that "survived" phases; it is working as designed, per (A) above. |
| Why it survived | (A) No sibling-runner diff check was run against these two scripts at authorship or at merge; `min_bet_usd` has no test asserting its presence, so a silent inherited-default omission produced no failure signal until refusals were read at the `rejection_reason` level. (B) N/A. |
| Impact | (A, now resolved) Confirmed: every T1 game-market evaluation whose computed size sat between $0 and $10 was being refused at C4 purely on the inherited live floor, indistinguishable in the audit log from a genuine floor refusal unless read against the calling script's actual `RiskEngine` construction — this is precisely what happened in T-546's 24/1,185 `min_bet_floor` run. (B, open) Every day GG-203 remains unresolved, T4M-PROJ either submits orders known in advance to fail against an externally-caused fault (pure loss, per APR-0034's analysis) or runs `kalshi_client=None` and forgoes ADR-0008's demo-order validation value — a real cost, but a bounded and already-adjudicated-as-optional one per the reader census above. |
| Discovery | Operator-directed STANDARD task, 2026-09-15, claimed as T-551/GG-282: "Two independent things stop a bet reaching a venue right now, and neither has been examined." |
| Resolution | **Floor A: RESOLVED.** `min_bet_usd=1.0` added to both `run_t1_nfl_game_market.py`'s and `run_t1_mlb_game_market.py`'s `RiskEngine` construction, aligned explicitly to existing sibling-runner precedent — no new pattern introduced. Two tests added per script (mirrored pairs): one proving a $1.00 measurement stake now clears end-to-end (`OPENED`) with the override in place, one proving the same stake is still refused `min_bet_floor` with no override (i.e., the live `MIN_BET_USD=10.0` default itself was never touched, per this task's explicit DO NOT constraint). Re-run of the same live-model evaluation methodology (current market slate, not a literal T-546 replay — the slate differs day-to-day): NFL run produced `{'OPENED': 41, 'REJECTED': 6, 'REFUSED_NO_EDGE': 9, 'REFUSED_NO_MODEL': 1161}` — **zero** `min_bet_floor` rejections, the 6 `REJECTED` are the distinct `insufficient_edge` gate, versus the original T-546 run's 0 `OPENED` / 24 `min_bet_floor`. Committed `92bd8e8` (post-rebase). **Floor B: NOT fixed — investigated and decision-requested, per Hard Rule 11 (register-and-stop) and this task's explicit DO NOT (must not construct `PaperTrader` with a non-None `kalshi_client`, must not submit any order).** Drafted (not implemented, not decided) `00_ADMIN/APR-0034_t4-mlb-kalshi-client-none-while-gg203-unresolved-decision-request.md`, recommending non-bindingly that T4 MLB run with `kalshi_client=None` until GG-203 resolves, since the reader census above shows zero load-bearing dependency on Kalshi order status in MLB's live G6 gate today, and continuing to submit orders known in advance to fail against a confirmed-external GG-203 fault is pure loss with no offsetting confirmation value. Per Hard Rule 3, adopting this recommendation would require a superseding ADR to ADR-0008 — this session did not write one; the operator decides. Committed `2e387b2` (post-rebase). |
| Cross-references | GG-203 (T4M-PROJ blocked 33+ days at the demo-order step — Floor B's subject, confirmed still IN PROGRESS/HIGH/externally-caused this session), T-546/GG-277 (real-model NFL open-attempt, 24/1,185 `min_bet_floor` refusals — the empirical anchor for Floor A, now cleared post-fix), ADR-0050 (measurement-stake sizing), ADR-0058 (per-contract stake cap / `MeasurementStakeRefused` — the refusal this task explicitly distinguishes from `min_bet_floor`), ADR-0008 (Kalshi demo-order submission — Floor B's governing ADR, confirmed non-load-bearing by design), APR-0034 (this session's drafted, undecided decision request for Floor B). |
| Status | **PARTIALLY RESOLVED** — Floor A fixed, tested, and re-verified live 2026-09-15 (T-551, commit `92bd8e8`). Floor B investigated in full (Deliverable 2) and a non-binding recommendation drafted as APR-0034 (commit `2e387b2`); the operator decision itself remains OPEN and is not this session's to make (Hard Rule 11 / scope fence). This entry should not be closed as fully RESOLVED until the operator acts on APR-0034 one way or the other. |

**Pickup (2026-09-17, T-556):** Floor A's branch (`origin/session/20260915T235119Z-why-no-bet-can-be-placed`, tip `73cd8eb`) merged to `origin/main` this session — `git merge-base --is-ancestor 73cd8eb origin/main` confirmed (exit 0) post-merge, and `min_bet_usd=1.0` re-confirmed via direct grep of both T1 game-market run scripts on `main` (`run_t1_nfl_game_market.py:430`, `run_t1_mlb_game_market.py:395`). A fresh live re-run against the real EXP-027 model on the VPS (see GG-274's matching Pickup addendum, same date) reproduced zero `min_bet_floor` rejections and opened 42 positions for the first time — independent confirmation, on a third data point (T-551's in-session run, then this session's post-merge run), that Floor A's fix holds on `main` as deployed, not just on the fix's own branch. Floor B's disposition (APR-0034, awaiting operator decision) is unchanged by this session — not touched, not decided.

</details>

### GG-285 — At observed effect sizes, APR-0024's per-band P&L n* is 10-11 NFL seasons (NFL moneyline) and ~1.6 MLB seasons (T4M-PROJ) from clearing; the P&L gate as currently written may not close within any practical operating horizon for signals whose sd/mean ratio is ~15-28x

**Status:** RESOLVED · **Severity:** MEDIUM

**RESOLVED 2026-10-28 (W91.1 Part C, T-1343).** The operator's 2026-10-21 19:15 PT call ("G6 re-defined by a superseding ADR, per book and sport, WINS at judged n") is now ADR-0076 (ACCEPTED 2026-10-27 17:30 PT). G6 no longer waits on APR-0024's per-band P&L n*, so the finding that the n* gate cannot close in a practical horizon no longer blocks anything. Nothing is left to fix; APR-0024 still governs commercial-validation sample adequacy (unchanged), and the reopen conditions are void.

Re-filed 2026-10-21 under the operator's observation rule. Reopens if: the operator adopts a practicable G6 gate or APR-0024's n* or the observed effect size changes.

**Current state (2026-10-08, W59.1):** No ADR after APR-0024 supersedes the n* P&L gate (ADR list through ADR-0071 has none; ADR-0057 is cell-scoped G6 rescope only); grep shows GG-285 still listed OPEN in OPERATOR_CONSOLE.md line 272; analysis finding awaiting operator decision. **Next:** Operator decision on a practicable gate (e.g. calibration-based or sequential test) via a decision-request ADR.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-285 |
| Category | Gate-design analysis — APR-0024's variance-derived `n*` standard, applied to signals with the sd/mean ratios actually observed, produces a sample-size requirement that is not reachable within a practical horizon at real bet cadence |
| What was found | Fresh per-cell power calc (`scripts/run_power_calc.py`, live VPS data pulled 2026-09-17): T4M-PROJ `clean_n=765`, `mean=$0.05193/bet`, `sd=$1.4628/bet` (ratio 28.2x), `n*=8587`, cadence=198.4 clean bets/week (27-day measured span) → total `n*` at this cadence ≈ 43.3 weeks ≈ 10.0 months ≈ 1.6 MLB regular seasons (season ≈ 27 weeks). T1/T2/T3 all `clean_n=0` (T1 `raw_n=466` but zero clean — epoch contamination per GG-124's known pattern; T2 `raw_n=2`; T3 `raw_n=0`, never traded) — variance not estimable, no `n*` computable at all. NFL moneyline (EXP-027/HYP-012, T-550 re-run): `clean_n=14`, `mean=$0.03214/bet`, `sd=$0.49920/bet` (ratio 15.5x), `n*=2610.35`; at the observed Week-1 clean rate (14/16 = 87.5% of `n_prospective_scheduled=272` games/season ⇒ ≈238 clean games/season ⇒ ≈13.2 clean games/week over an 18-week season), total `n*` at this cadence ≈ 197 weeks ≈ 45.6 months ≈ 11.0 NFL seasons. Full per-cell table, calibration-vs-P&L sample-size comparison, and cell-by-cell strategic-consequence statement in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T554_nstar_wall_analysis.md` (this session). |
| Why it matters | APR-0024 governs G6 sample-adequacy system-wide. If the two cells with any resolved cohort at all (T4M-PROJ, NFL moneyline) both require single-digit-to-double-digit years of continuous, uninterrupted cadence at their *current* measured rate to clear `clean_n >= n*` on P&L-per-bet alone, then G6 cannot close on P&L evidence within any practical horizon for those cells as things stand, and the ~25-cell coverage target (`COVERAGE_TARGET_MATRIX.md`) compounds the problem rather than diluting it — each new cell starts its own multi-year P&L clock from zero. This is an analysis/decision request, not a proposed fix: no gate, threshold, or pre-registered verdict is changed by this entry. EXP-027's UNDERPOWERED verdict stands unmodified. |
| Discovery | 2026-09-17, T-554 (this session), STANDARD-tier analysis task per explicit operator framing: "Nobody has stated the implication." |
| Resolution | Not resolved — this is a decision request. APR drafted at `00_ADMIN/APR-0035_pnl_gate_reachability_decision_request.md` (this session; corrected from an earlier-typed `APR-0026`, which was already taken by a different session — confirmed via full-history search before the APR was actually written), presenting options (keep P&L gate and accept horizon / add a calibration-based interim cell-promotion gate while P&L stays the live-capital gate / re-derive n* under different power-alpha / other) without selecting one. Recommendation, not decision, per task framing. |
| Cross-references | APR-0024 (the standard under analysis); APR-0035 (this session's drafted, undecided decision request); ADR-0057 (in force, unaffected); GG-004 (commercial-validation gap, parent); GG-124 (T1/T2/T3 transient-to-persistent clean_n=0 pattern, still live for T1 at this measurement); T-550/GG-281/GG-283/GG-284 (EXP-027 re-run this analysis builds on, none of which are relabeled or reopened here). |
| Status | OPEN — registered 2026-09-17 (T-554). Resolution path is APR-0035's operator decision, not a code or data fix. Closes when the operator selects an option and any required superseding ADR/APR is accepted. |

</details>

---

### GG-289 — Auto-mode classifier's Self-Modification block on `.claude/commands/session-end.md` + `scripts/close_session_claim.sh` + `scripts/sweep_stray_branches.sh` is a structural, repeatable barrier — confirmed twice independently — and is the likely actual root cause of T-554's silent closure-row push failure, not mere git divergence

**Status:** OPEN · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Operator disposition: apply the three self-modifying edits (`.claude/commands/session-end.md`, `scripts/close_session_claim.sh`, `scripts/sweep_stray_branches.sh`) by hand, once; no permission rule widened. Stays OPEN until the operator applies them. Severity UNSPECIFIED -> LOW.

**Current state (2026-10-08, W59.1):** Commits 580e9c9 and 1e097e0 (session-end.md / close_session_claim.sh / sweep_stray_branches.sh) ARE ancestors of worktree HEAD, and later edits landed (4874db4, 2365cc7 GG-451), so the files are changeable in git; the classifier denial is a permission-layer behavior that git history cannot disprove, and GG-288's root-cause question is not shown fixed. **Next:** Operator to decide how classifier-flagged self-modifying scripts get approved (allowlist or operator-run cherry-pick); re-test one cherry-pick under current permissions.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-289 |
| Category | Tooling/process — a hard permission-layer boundary, not a code defect, but one that invalidates a prior diagnostic hypothesis (GG-288) and blocks that gap's own remediation path as specified. |
| What was found | `git cherry-pick 44b7fb5 580e9c9` (T-557, this session) was denied outright by the Claude Code auto-mode classifier, `Reason: [Self-Modification]`, before touching any file. This is the second independent occurrence against the identical commit pair: T-555's own branch recorded an earlier denial (`Self-Modification` + `Untrusted Code Integration`) for the same cherry-pick, logged in that branch's DECISION_LOG close-out addendum, predating this session. Both commits touch `.claude/commands/session-end.md` (a Claude Code command-configuration file) and introduce/modify `scripts/close_session_claim.sh` / `scripts/sweep_stray_branches.sh` (scripts that govern Claude Code's own session-close automation) — content squarely inside what "Self-Modification" plausibly targets, independent of which git verb (cherry-pick, and very plausibly push or merge too) is used to move it. |
| Why this matters for GG-288 | GG-288's entering hypothesis for why T-554's closure-row push failed was git-mechanical: local `main` far behind `origin/main`, rebase-retry loop failing/timing out against a large divergence. Direct inspection this session of `close_session_claim.sh` as it exists on local `main` (`git show main:scripts/close_session_claim.sh`) shows the script's actual push call is a plain `git push --quiet origin HEAD:main` with a 5-attempt fetch+rebase retry loop on rejection — mechanically reasonable and does not obviously explain a full silent failure on its own. The closure-row commit it produced (`1431cdd`, parent `580e9c9`) sits directly on top of the two flagged commits in local `main`'s history; pushing that HEAD to `origin/main` necessarily carries `44b7fb5`/`580e9c9`'s content along with it. Given this session's confirmed, repeatable classifier denial on moving that exact content via `cherry-pick`, the better-evidenced hypothesis is that the T-554 session's push attempts were also denied by the same classifier (a permission-layer block, not a git-level rejection) — which the script's retry loop has no way to detect or distinguish from an ordinary transient rejection, so it would retry 5 times against a wall and exhaust its attempts, or the denial may have prevented the `Bash` push call from executing at all. This has NOT been confirmed by directly reproducing a push of that content (doing so risks the identical block for no new information, and was judged not worth attempting given two independent cherry-pick denials already establish the pattern for this exact content). |
| Impact | Any script-level "harden the retry loop" fix to `close_session_claim.sh` (e.g., detached-ref push, pre-rebase before first attempt — the mechanics the operator task brief suggested) will not resolve the actual failure if the root cause is a content-based permission denial rather than a git-mechanical one: the fixed script would still carry the same flagged content and would plausibly still be denied. The deeper fix is either (a) operator adds a Bash permission rule authorizing this class of action, as the classifier's own denial message suggests, or (b) the flagged files are never allowed to accumulate on shared `main` outside of an operator-authorized push in the first place (a process constraint, not a script fix) — GG-101's worktree-isolation default already points this direction but does not by itself solve authorization. |
| Discovery | 2026-09-18, T-557 (this session), while investigating GG-288/Deliverable 3. |
| Resolution | Not resolved — requires an operator decision on how to authorize landing self-modifying session-tooling changes (Bash permission rule, manual operator-side apply, or an explicitly scoped one-time authorization). No fix has been attempted against `scripts/close_session_claim.sh` itself, since editing it is in the same flagged file class and would risk a third identical denial without operator direction first. |
| Cross-references | GG-288 (the entry this corrects/supersedes the working hypothesis for), GG-101 (worktree isolation), T-555's branch DECISION_LOG close-out addendum (first occurrence of this exact denial, predating this session). |

</details>

---

### GG-295 — Live NFL T1 portfolio's `kalshi_threshold` backfill (all 42 positions) has no corresponding commit anywhere in repo history and is misattributed to an unrelated session (T-562)

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** HIGH governance issue on a ledger mutation with no commit; not re-derived. **Next:** Operator review of provenance.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-295 |
| Category | Governance process failure — an undocumented, unattributable direct mutation of a live, real-money-adjacent ledger file (Hard Rule 7 violation), discovered during T-563/GG-291's Deliverable 1 census |
| What was found | GG-291 (OPEN, HIGH) documented that all 42 real open `nfl_moneyline` positions carried `kalshi_threshold: null`, which would crash `settle_position()` on first real settlement. This session (T-563), tasked with fixing that defect, first re-verified the live portfolio directly (per the runbook's own step 3.1 instruction to check whether another session had already fixed it) and found all 42 positions already carry `kalshi_threshold: 0.0`, each stamped `repaired_at: "2026-09-18T19:04:05.324231+00:00"` and `repair_ref: "GG-291 / T-562"` — uniformly, across every position. Diffed against the pre-backfill snapshot (`paper_portfolio_t1_nfl_game_market.pre_gg291_backfill_20260918T190405Z.json`): exactly 42 rows changed, only the three fields `kalshi_threshold`/`repaired_at`/`repair_ref` touched on each, nothing else — structurally this is a clean, correctly-scoped repair, the exact shape GG-291's own resolution path called for. The problem is entirely provenance: (1) `DECISION_LOG.md` has no entry describing this mutation anywhere; (2) the `repair_ref` cites T-562, but T-562's own logged DECISION_LOG entry (2026-09-21, "merged diverged local main into origin/main") explicitly describes an unrelated git-merge task touching only `ACTIVE_QUEUE.md`/`SESSION_CLAIMS.md`/`close_session_claim.sh`/`sweep_stray_branches.sh`/`session-end.md`, and states in its own text "no GG-log/DECISION_LOG overlap" — T-562 did not do this; (3) `git log --all` across the full repository history returns zero commits in any branch touching `paper_portfolio_t1_nfl_game_market.json`'s `kalshi_threshold` field, and zero commits at all in the `2026-09-18T18:30–20:00 UTC` window bracketing the stamped `repaired_at` timestamp; (4) `grep -rn "repair_ref"` across `src/` and `scripts/` finds only two unrelated MLB repair scripts (`t503_repair_d1_d3_epoch12.py`, `t502_repair_d2_stuck_open.py`), neither referencing GG-291, T-562, or the NFL portfolio. No checked-in script produced this repair. |
| Why this matters | The live NFL portfolio — the ledger this project's first-ever real settlement will run against — was mutated directly (almost certainly via an ad hoc interactive session against the VPS, not through any tracked code path), with a plausible-looking but false attribution baked into the data itself. The mutation's *content* is correct (matches exactly what GG-291 asked for), which is precisely what makes this dangerous to skip: a structurally-correct-looking repair with a fabricated provenance trail sets a precedent that "looks right" is being treated as sufficient without anyone checking "is the citation real." Had this session not independently verified the census instead of trusting the brief and the stamped `repair_ref`, the false attribution would have propagated into this session's own DECISION_LOG entry, compounding it. |
| Impact | HIGH. Two live concerns: (a) an unknown actor or process has direct, untracked write access to the live financial ledger and used it, with no audit trail beyond the data's own self-reported (and false) stamp; (b) `repair_ref`/`repaired_at` provenance stamps — a pattern this project treats as trustworthy (ADR-0055 precedent, cited explicitly in T-563's own task brief as the standard to follow) — can apparently be written without the work they claim to document actually having happened under that identity. This weakens the evidentiary value of every `repair_ref` stamp elsewhere in the codebase unless each is independently re-verified. |
| Discovery | 2026-09-22 (session-clock; operator wall-clock 2026-09-21), T-563 (this session), Deliverable 1 census — found by following the task brief's own explicit instruction to verify the defect's current state directly rather than trust the brief's claim that all 42 positions were still null. |
| Resolution | Not resolved. This session did NOT re-run or alter the backfill (it is already data-correct; re-touching it would only compound the provenance confusion) and did NOT attempt to identify who/what performed the mutation (out of this session's scope and tooling — no VPS shell-history audit was performed). Recommend: (1) operator review of VPS shell/SSH access logs around 2026-09-18T19:04 UTC if available, to identify the actual actor; (2) an ADR or standing rule that no `repair_ref` may cite a session ID without that session's own DECISION_LOG entry independently corroborating the specific mutation (not just existing) before the stamp is trusted; (3) audit other `repair_ref`-stamped mutations in the codebase (the two MLB repair scripts noted above, and ADR-0055's own precedent case) for the same corroboration gap, since this session did not check whether GG-295's pattern is unique to this one incident. |
| Cross-references | GG-291 (the defect this undocumented mutation fixed the data for, but not the code for — GG-291 remains OPEN until the write-path fix lands), T-562 (falsely cited as the actor), ADR-0055 (the provenance-stamp precedent this mutation's format imitates), Hard Rule 7 (every strategic decision must be logged immediately — this was a ledger-mutating decision with real financial-adjacent consequence and was not logged at all). |
| Update (2026-09-23, T-571) | A separate task this session (ledger-integrity audit Deliverable 3: establish which model wrote the 42 NFL rows' forecasts) independently confirmed `model_identity` is stamped `"EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"` on all 42 rows, traced code-side via `EXP027NFLForecastModel.PROVENANCE` (`src/prediction_market_bot/nfl_exp027_adapter.py:115`) through the `_model_identity()`/dict-spread propagation mechanism GG-267 built (RESOLVED). **This is MODEL provenance (which forecasting code produced the number) — a separate question from this gap's ACTOR provenance (who/what process wrote `kalshi_threshold`/`repair_ref` and when).** The two must not be conflated: this update does not resolve, narrow, or bear on GG-295's open actor-provenance question, which remains exactly as described above. No mutation, edit, or repair was made to this portfolio file by this update. |
| Update (2026-09-23, T-571, cross-reference only) | The same Deliverable 3 work registered **GG-302** (OPEN, HIGH): all 42 NFL rows trace to one unlogged manual paper-trader invocation (`PT-T1-NFLGM-22640C8C`, 2026-09-17T00:25:48–00:27:00Z) whose human actor is also unrecoverable, and quarantines all 42 rows from G6 evidence/calibration/`clean_n` on that basis. GG-302 and GG-295 are two independent actor-provenance gaps on the same 42 rows (one for the threshold-backfill mutation, one for the original position-opening run) — resolving either does not resolve or narrow the other. A reader following up on either gap should check both. |

</details>

---

### GG-296 — T4M-PROJ's shard-3 demand figure (~2,000 approvals/$1,907.85 stake, 2026-09-20) is a ring-buffer ceiling artifact, not a measured count, and any collateral-funded accrual night risks non-randomly truncating the project's only clean G6 cohort

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Verified: paper_trader.py l.86 MAX_REJECTED_POSITIONS=2000 and the live T4 portfolio holds exactly 2000 rejected_positions (VPS, this session) - the figure is a ring-buffer ceiling. **Next:** Persist rejections to an append-only file before funding accrual.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-296 |
| Category | Measurement-validity risk compounding a known execution defect — GG-203's root cause (shard-3 collateral unallocated, confirmed OPEN as of T-560/2026-09-18, `balance_breakdown[3].balance = "0.0000"`) is being remediated this wave (T-568) via operator-pre-authorized demo-collateral funding, but the number used to size that funding and the cohort it will feed both carry unverified assumptions that must be resolved *before* accrual, not discovered after. |
| What was missed | Two distinct open questions, neither yet checked as of this entry: (1) The "~2,000 approvals, $1,907.85 intended stake in 6.8 hours on 2026-09-20" figure driving this wave's funding target comes from GG-271's `rejected_positions` array, which is a **bounded ring buffer capped at 2,000 entries** (activated 2026-09-15) — 2,000 is consistent with the buffer having simply filled and wrapped, not with 2,000 being the true count of approvals that day. If true demand exceeds 2,000, funding shard 3 to "2,000 + 50% headroom" would still under-fund the actual night, reproducing GG-203's `insufficient_shard_balance` failure mid-accrual rather than solving it. (2) T4M-PROJ's `clean_n=765` cohort (frozen since 2026-08-13, the project's only ACTIVE-band cell with a real G6 sample toward APR-0024's `n*` target) has never absorbed a night where collateral ran out partway through — if shard-3 funding is set below true per-night demand, the resulting accrual would fill early-inning/early-game rows preferentially (collateral present) and systematically drop late-game rows (collateral exhausted), a non-random truncation that would bias the cohort's inning/`ab_remaining_at_entry` distribution in a way no prior 765 rows exhibit, since T4M-PROJ has been `kelly_fraction=0.0`/flat-stake (ADR-0050) and never collateral-constrained before this wave. |
| Why this matters | This is the precise failure mode the task's own guardrails were written to prevent ("a collateral-truncated night would inject early-inning selection bias into the project's only clean cohort" — explicit in this wave's brief) and ("DO NOT accrue on a balance shown to truncate the night"). Funding to a ceiling-artifact number rather than a true measured count is the most likely way to violate that guardrail by accident rather than by choice: the funding could look adequate against the only number available (2,000) while still being inadequate against the true count, and the resulting bias would not be visible until Deliverable 4's post hoc inning-distribution comparison — after the contamination has already happened. |
| Impact | HIGH if unaddressed before funding: T4M-PROJ is the sole cell with a real sample toward the G6 gate; contaminating even part of it forces either a costly exclusion (losing accrued rows) or a silent bias in the only commercial-validation evidence this project has. LOW once addressed: the true count is recoverable from `audit_mlb_t4.jsonl`'s `risk_eval_approved` events directly (the same field GG-203's own `gg203_order_write_detector.py` already reads per-day), independent of the bounded buffer, so this is a measurement-order problem, not a missing-data problem. |
| Discovery | 2026-09-23, T-568 (this session), pre-Deliverable-1 review of the wave brief against GG-203's full history (T-560's confirmed `$0.0000` shard-3 balance as of 2026-09-18, and GG-271's documented 2,000-entry ring-buffer cap) before beginning any funding action. |
| Resolution | Not yet resolved — this is the entry point to this session's own Deliverable 1 (recover true approval demand per game-day from `audit_mlb_t4.jsonl`, not `rejected_positions`) and Deliverable 2 (fund shard 3 against that measured true count with ≥50% headroom, only after Deliverable 1 completes; STOP and report rather than proceed if the demo account cannot reach that level). Deliverable 4 will report whether any night truncated in practice and flag (not unilaterally exclude) any contaminated day. This entry is filed before any SSH write, balance read, or funding action in this session per the wave's own instruction to register the gap-log entry as the first pushed commit. |
| Cross-references | GG-203 (shard-3 collateral unallocated; T-560 last confirmed `$0.0000`, remediation was explicitly outside that session's authorization and is this wave's pre-authorized task), GG-271 (bounded `rejected_positions` ring buffer, cap=2000, activated 2026-09-15), APR-0024/GG-004 (G6 sample-adequacy standard T4M-PROJ's `clean_n` feeds), ADR-0050 (T4M-PROJ's flat measurement stake, the sizing regime this wave must not alter), T-556 (`kalshi_client.py::_get()` `authenticated=False` defaults to production — must pass `authenticated=True` explicitly on every balance read this wave performs, per T-558/T-560's own established pattern). |

</details>

---

### GG-298 — `rejected_positions` field name implies risk-engine declines but actually holds post-approval exchange-side order-submission failures, making it unusable as a holdout/decline cohort under its documented name

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified: paper_trader.py still names the field rejected_positions (l.205, 217) while its own comments (l.20, 76) say it holds post-approval exchange rejections; live VPS T4 portfolio holds 2000 rejected_positions (ring-buffer ceiling). **Next:** Rename or alias the field (e.g. exchange_rejected_positions) with a migration.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-298 |
| Category | Naming/framing mismatch discovered by a separate, already-merged session (T-565, commit `2d3321d`, 2026-09-22) and left explicitly unregistered pending this wave's GG/DECISION_LOG ownership split ("31.2 owns them this wave" — this session is 31.2/T-568). Registered here per this wave's Deliverable 5. |
| What was missed | T-565's Deliverable 4 found: all 2,000 rows in `rejected_positions` (the GG-271 bounded ring buffer) are same-day (2026-09-20) exchange-side `insufficient_shard_balance` order-submission failures on positions the risk engine had **already approved** — not risk-engine declines. Zero ticker overlap exists with the only outcome store available (covers 2026-07-02 through 2026-08-03). The field name and its place in the schema (alongside `open_positions`/`closed_positions`) reads as "positions the risk engine rejected," which would make it a natural holdout/counterfactual cohort for comparing approved-vs-declined edge; it is instead a log of post-approval execution failures, concentrated entirely on one incident day tied to GG-203's shard-3 collateral fault. |
| Why this matters | Any future session or analysis that reaches for `rejected_positions` expecting risk-engine declines (a reasonable inference from the name alone) will draw a wrong or unusable comparison — the field cannot answer "what did the model correctly decline" because it contains no declines, only same-incident execution failures on approved bets. This wave's own GG-296 already had to work around this exact confusion when establishing the true 2026-09-20 demand figure. |
| Impact | MEDIUM: not a data-loss or correctness risk to the live pipeline, but a standing trap for any future analysis session that trusts the field name without checking contents first — as T-565 did check, but as a prior wave (the one that produced this wave's own brief, which cited the ring-buffer's raw count as "approvals" without initially distinguishing declines from execution failures) did not. |
| Discovery | 2026-09-22, T-565 (separate session, commit `2d3321d`), found during a calibration-model-vs-market comparability task; left as an unregistered gap candidate for this wave's GG/DECISION_LOG owner (31.2) per explicit task-ownership split. Registered 2026-09-23 by T-568 (this session) per Deliverable 5. |
| Resolution | Not resolved — recommend either renaming the field (e.g. `post_approval_execution_failures`) or adding an explicit `failure_reason`/`stage` discriminator so future readers can distinguish true risk-engine declines (if that concept is ever logged) from execution-layer failures without re-deriving it by hand each time, as both T-565 and this wave's GG-296 had to. No code change made in this session (out of scope — this is a registration-only deliverable). |
| Cross-references | GG-271 (the bounded ring buffer itself, cap=2000, activated 2026-09-15), GG-296 (this wave's own cohort-truncation-bias entry, which had to independently work around this same naming confusion), GG-203 (the shard-3 collateral fault that produced the 2026-09-20 `insufficient_shard_balance` failures populating this field). |
| Update (2026-09-23, T-571) | A separate task this session ran `scripts/t565_calibration_model_vs_market.py` unchanged against the current live ledger (both `paper_portfolio_mlb_t4.json`'s 2,000-row `rejected_positions` and `paper_portfolio_mlb.json`'s 16-row `rejected_positions`, 2,016 total). Confirms this gap's finding structurally rather than just by inspection: `build_rows()` requires `actual_hits`/`outcome`/`pnl`, which no `rejected_positions` row carries (script comment, lines 242-244), so the script's own `deliverable_4_rejected_cohort` output computes to `n=0` for all 2,016 rows — an independent, code-level confirmation that this field is structurally unscorable under the project's own calibration methodology, not merely mislabeled. No code change made. |

</details>

---

### GG-299 — ADR-0046's ECE baseline (0.0680, n=261) drifts +22% relative (to 0.0832) when its own exact methodology is re-applied to a later live pull of its own source file (n=468); Brier holds steady (0.2190→0.2200) over the same re-pull

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Not re-derived this session; ADR-0046 constants unchanged and no fixed-snapshot re-derivation found; the claim is a historical measurement (n=261 to n=468 re-pull, ECE 0.0680 to 0.0832). **Next:** Re-derive ECE with ADR-0046 methodology on a frozen snapshot of the current ledger and bootstrap CI to separate binning noise from drift.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-299 |
| Category | Calibration-metric instability discovered by a separate, already-merged session (T-565, commit `2d3321d`, 2026-09-22) and left explicitly unregistered pending this wave's GG/DECISION_LOG ownership split ("31.2 owns them this wave" — this session is 31.2/T-568). Registered here per this wave's Deliverable 5. ADR-0046's constants themselves are explicitly out of scope to change (per T-565's own task instruction and this wave's brief) — this is a registration of the drift, not a proposed fix. |
| What was missed | T-565 re-ran ADR-0046's own calibration methodology, unmodified, against a later live pull of the identical source file ADR-0046 was originally computed from: original computation was n=261 (2026-07-16), ECE=0.0680, Brier=0.2190; re-pull was n=468 (2026-08-06), ECE=0.0832 (+22% relative), Brier=0.2200 (materially unchanged). The metric that moved (ECE) is more sensitive to bin-edge/sample-composition shifts than Brier by construction, so this is consistent with — but does not by itself prove — genuine calibration drift as the underlying cohort grew from 261 to 468 rows, rather than a purely a mechanical artifact of ECE's binning. T-565's own task explicitly ruled ADR-0046's constants out of scope to change, so this was logged as a finding, not corrected. |
| Why this matters | ADR-0046's ECE figure has been cited in prior sessions as a live reference point for calibration health. This finding shows that figure is not stable under its own exact re-computation as more data accumulates — a session citing ADR-0046's 0.0680 as current without re-deriving it would be working from a value already 22% stale relative to a same-methodology re-pull from over six weeks ago (2026-08-06), and materially more stale by now (2026-09-23). |
| Impact | LOW as filed: T-565's own Deliverable 3 already established that ADR-0046's baseline constants are NOT COMPARABLE to T4M-PROJ's current real ledger on several independent grounds (clean filter, directional convention, band/threshold scope, epoch window all mismatch) — so this drift compounds an already-established non-comparability rather than being the sole reason to distrust the figure. Would become HIGHER impact only if a future session leans on ADR-0046's ECE as a current, standalone reference without first re-deriving it. |
| Discovery | 2026-08-06 data / 2026-09-22 analysis, T-565 (separate session, commit `2d3321d`), a supplementary check during a calibration-model-vs-market comparability task; left as an unregistered gap candidate for this wave's GG/DECISION_LOG owner (31.2) per explicit task-ownership split. Registered 2026-09-23 by T-568 (this session) per Deliverable 5. |
| Resolution | Not resolved — no ADR-0046 change made or proposed (out of scope per both T-565's and this session's task instructions). Recommend a future session re-derive ADR-0046's ECE/Brier figures against the current live cohort before citing either as a standing reference, and consider whether ECE's bin-edge sensitivity to growing n warrants a documented re-derivation cadence rather than treating ADR-0046's original constants as fixed indefinitely. |
| Cross-references | ADR-0046 (the calibration baseline itself, constants unchanged), T-565 (`2d3321d`, `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_RESULTS_calibration_model_vs_market.md` — full source analysis and script `scripts/t565_calibration_model_vs_market.py`). |

</details>

---

### GG-301 — T4M-PROJ's calibration headline reverses sign and turns net-negative when restricted to Kalshi-confirmed-filled rows only (n=34 of 765)

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Sign reversal rests on n=34 / 9 days and is unverified; fill confirmation has not expanded (GG-300 still open, no re-polling code). For context, current VPS ledger T4M-PROJ epoch-12 n=1898 has total mean pnl/bet -0.0481, post-outage bucket -0.0875, so the full-cohort positive P&L has itself eroded. **Next:** Re-run t571 Variant B after fill-confirmation coverage expands (blocked on GG-300).

<details>
<summary>Full record</summary>

| Field | Value |
|---|---|
| Gap ID | GG-301 |
| Category | Ledger integrity / calibration validity |
| What was found | T-571 Deliverable 2 recomputed T-565's committed calibration script (`scripts/t565_calibration_model_vs_market.py`, unmodified — imported and called, never edited) against a subset of the original 765-row T4M-PROJ clean cohort (2026-07-31..2026-08-13) restricted to the 34 rows GG-300/GG-297's phantom-fill test confirms as Kalshi-FILLED. Two variants: **Variant A** (exclude only confirmed-CANCELED in-window) finds zero such rows in-window and therefore reproduces the original 765-row figures exactly, unchanged (model_brier=0.2191, market_brier=0.1890, paired diff bet-level +0.0301/t=5.66, day-clustered +0.0593/t=2.87/n_days=11) — this is expected, not a new finding, since GG-300's own Update row already established 0 CANCELED rows exist inside this window. **Variant B** (confirmed-FILLED-only, n=34, n_days=9) is the new finding: model_brier=0.2730 (worse, not better), market_brier=0.1415 (market improves), paired diff bet-level **+0.1314** (se 0.0267, t=4.92, df=33) and day-clustered **+0.1115** (se 0.0358, t=3.12, df=8, n_days=9) — both *larger* gaps against the model than the full-cohort figures, not smaller; skill_vs_climatology=**-0.156** (negative — the model is worse than a constant base-rate prediction on this subset); win_rate=0.176 (vs. 0.405 on the full 765); total_pnl=**-$6.78** (vs. +$39.73 on the full 765) — the confirmed-real subset is a net LOSS, not the modest net gain the full 765-row cohort shows. |
| Why this matters | T-565's headline claim — the project's one demonstrated calibration finding, feeding the G6 evidence record and APR-0024's sample-adequacy standard — is computed on 765 rows of which only 34 (4.4%) are independently confirmed to have actually been filled at Kalshi (per GG-300). On exactly that 34-row confirmed-real subset, the finding does not merely weaken — it reverses direction (model worse than market, worse than climatology, net P&L loss). This does not prove the full-cohort finding is wrong: n=34/n_days=9 is a small, likely underpowered sample on its own, and Variant B is drawn non-randomly (only rows where a FILLED order happened to be retrievable) — this could easily be a selection artifact rather than a true reversal. But it means the honest current state is: **the only subset of the calibration cohort independently verified as real trades shows the opposite of what the project's headline claim states.** |
| Impact | HIGH. No clean_n restated, no cell status/kelly_fraction changed, no ledger row edited/excluded — this is a scratch recompute (`scripts/t571_deliverable2_confirmed_only_recompute.py`, new file, does not modify `t565_calibration_model_vs_market.py`) reported as a delta only, per this session's explicit scope fence. It does mean any operator-facing claim that "T4M-PROJ shows real calibration edge" should be read as resting on the 765-row cohort's aggregate, not on independently-verified trades specifically — and that the one subset where independent verification exists points the other way. Whether this is noise (n=34, non-random selection into "retrievable") or signal is not resolved by this session and requires either a larger confirmed-FILLED sample (as more Kalshi retention/order data becomes checkable) or an operator decision on evidentiary standard — this gap does not make that call. |
| Discovery | 2026-09-23, T-571 (ledger-integrity-audit wave, worktree `session/20260923T234404Z-ledger-integrity-audit`), Deliverable 2. Read-only throughout. |
| Resolution | Not resolved — diagnosis only. Two things NOT done, disclosed rather than silently assumed: (1) no statistical correction for the non-random selection into "confirmed FILLED" was attempted (rows are FILLED because their order_id happened to still be retrievable at check time, not because of any property of the bet itself — but this has not been positively ruled out as correlated with, e.g., earlier game_dates or particular players/thresholds); (2) no power analysis was run on whether n=34/n_days=9 could produce this magnitude of reversal by chance alone under the null that the true effect matches the full-765 figure — a `scripts/run_power_calc.py`-style check would clarify this and is the natural next step, not performed here per this session's scope fence (analysis-script territory belongs to session "33.1"). |
| Cross-references | GG-300 (the phantom-fill sizing this recompute is built on), GG-297/GG-295 (the underlying ledger-integrity findings), GG-004 (G6 sample-adequacy standard this bears on directly), T-565 (`2d3321d`, the committed script this recompute reuses unmodified), GG-228 (repair-decision authority — operator only; this gap makes no repair recommendation). |
| Update (2026-09-24, T-573) | This wave's block 34.2, Deliverable 3, directly tests the "selection artifact" alternative this entry's Resolution row flagged as untested. **Pre-registered 8 observables before running any test** (`scripts/t573_selection_bias_test.py`, docstring states the pre-registration): 5 continuous (`mid_price_at_entry`, `gross_edge`, `h_so_far_at_entry`, `ab_remaining_at_entry`, `size_usd`) via two-sided Mann-Whitney U (hand-implemented, normal approximation with tie correction — no scipy on the VPS), Bonferroni-corrected alpha=0.05/5=0.01; 2 categorical (`kalshi_threshold`, `game_date`) reported descriptively. **Result: 3 of 5 continuous observables are significant surviving Bonferroni correction** — `mid_price_at_entry` (FILLED mean 0.6527 vs NR mean 0.3950, p<0.00001), `gross_edge` (FILLED −0.1913 vs NR −0.0340, p=0.00203), `size_usd` (FILLED 0.6271 vs NR 0.9123, p=0.00001). Not significant: `h_so_far_at_entry` (p=0.364), `ab_remaining_at_entry` (p=0.868). `game_date` is also visibly skewed: 42.9% of FILLED rows fall on a single date (2026-08-10) vs only 18.1% of NR rows on that date. **This confirms the selection-artifact hypothesis rather than ruling it out: the 34-row confirmed-FILLED subset is not a random draw from the 765-row cohort — it differs systematically on entry price, edge, and order size, and clusters non-randomly by date.** Direct consequence for this gap's own headline: **the correct standing claim is not "the confirmed-real subset reverses the finding" — it is that the confirmed-real subset is a different, non-random sample answering a different question, so the project's calibration headline is UNKNOWN, not reversed.** Neither the original 765-row positive finding nor this gap's 34-row negative finding can be trusted alone as the project's answer until the cohort is scorable on a random or exhaustive basis (see GG-300/GG-303 for why it currently is not). No ledger row edited, excluded, or re-stamped; no statistical correction applied to either headline — this is a diagnostic finding, not a repair. Cross-reference: GG-300, GG-303. |

</details>

---

### GG-302
**Status:** OPEN · **Severity:** HIGH

<details>
<summary>Full record</summary>

**Gap ID:** GG-302
**Category:** Ledger integrity / evidence quarantine (T-571 Deliverable 3)
**What was found:** All 42 live NFL T1 game-market rows (20 closed + 22 open, `paper_portfolio_t1_nfl_game_market.json` on the VPS) trace to exactly ONE paper-trader process invocation: internal `session_id=PT-T1-NFLGM-22640C8C`, `audit_t1_nfl_game_market.jsonl` timestamps 2026-09-17T00:25:48.188Z through 2026-09-17T00:27:00.978Z (a ~72-second run), 46 risk evals / 42 approved / 42 `paper_order_opened` — an exact match to the ledger's 42-row count. All 42 rows carry `model_identity = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"`, matching `EXP027NFLForecastModel.PROVENANCE` in `nfl_exp027_adapter.py` exactly — **not** the `StubNFLForecastModel` default GG-255 warned about. A second, earlier session (`PT-T1-NFLGM-4B36EB7E`, 2026-09-15T04:41:48–04:43:21Z, 24 risk evals, 0 approvals, 0 positions opened) produced nothing and is consistent with GG-263's "one logged run produced zero positions" finding.

This resolves MODEL provenance definitively (the EXP-027 LR model, not the stub, produced these rows) and resolves RUN-EVENT provenance to a specific ~72-second window and internal session_id. It does **not** resolve ACTOR provenance: no cron entry exists for NFL (confirmed T-571 Deliverable 3 investigation), no `DECISION_LOG.md` entry references an NFL run around 2026-09-17, and the `approval_commit` field recorded on every row (`66bb0d3c6fff57b2dd75ffc2241ece102fac78f5`, dated 2026-07-31, GG-149's T4-MLB commit — unrelated to NFL) was verified by code read (`logic_epoch.py` `CURRENT_APPROVAL_COMMIT = _BOUNDARIES[-1].commit_sha`) to be a static epoch-boundary marker baked into the source tree, not a live git-HEAD-at-runtime capture — it does not and cannot identify which commit or session actually executed the 2026-09-17 manual invocation. No artifact examined (ledger fields, audit log, DECISION_LOG, cron config, git history) identifies who ran this, from where, or under what review.

**Why this matters:** a manual, undocumented, unreviewed production run against live paper-trading risk approval (C4) produced 42 real approved positions using a model whose own embedded verdict string is "UNDERPOWERED" (EXP-027/HYP-012), with zero `DECISION_LOG.md` trail — a direct gap against Hard Rule 7 ("every strategic decision made in a session goes into DECISION_LOG.md immediately"). Whether this run was an authorized test, an accidental invocation, or something else cannot be determined from any artifact in this repo or on the VPS.

**Impact:** per this session's task instruction, since actor/authorization provenance is unrecoverable, all 42 NFL T1 rows (20 settled + 22 open) are QUARANTINED from G6 evidence, calibration benchmarks, and `clean_n` counts as a standing constraint — not a one-session note. Any future session scoring, citing, or aggregating NFL T1 results must first re-check this entry's status. This quarantine is orthogonal to and does not resolve GG-295 (NFL threshold-backfill actor provenance, a separate 42-row defect on the same band) — the two are not to be conflated or jointly "resolved" by addressing only one.

**Discovery:** T-571 Deliverable 3, via direct ledger field inspection (`model_identity`, `approval_commit`) cross-referenced against `audit_t1_nfl_game_market.jsonl` session_id grouping and `nfl_exp027_adapter.py`/`logic_epoch.py` source.

**Resolution:** Not resolved. Registering the quarantine as the resolution to Deliverable 3's mandate ("if unrecoverable, quarantine and register as a standing constraint") — actor identity is the specific unrecoverable element; model and run-event provenance are resolved and stated above for the record. No ledger row edited, excluded, or re-stamped. No `clean_n` restated.

**Cross-references:** GG-295 (NFL threshold-backfill actor provenance — separate, not resolved by this entry), GG-255 (stub-default pipeline-wiring risk — ruled out as the cause here), GG-263 (RESOLVED — T-534's logged run produced zero positions, consistent with the 2026-09-15 session found here), GG-267 (PROVENANCE field mechanism that made this finding possible), T-571.

</details>

---

### GG-304 — `kalshi_order_status` field reads `"submitted"` uniformly across both confirmed-FILLED and confirmed-unretrievable T4M-PROJ rows, making it non-discriminating for any downstream fill-status inference

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Still true 2026-10-07: VPS paper_portfolio_mlb_t4.json closed_positions kalshi_order_status = 'submitted' for 4169 of 4181 rows (rest 'failed: HTTP 410'); paper_trader.py sets it only at submission (lines 660/676) with no re-poll. **Next:** Document the field as submission-acceptance-only in schema docs, or add a periodic order-status re-poll writing a separate kalshi_fill_status field.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-304 |
| Category | Ledger field reliability — `paper_portfolio_mlb_t4.json`. Adjacent to GG-297's finding that `kalshi_order_status` is set once at submission-acceptance time and never re-polled. |
| What was found | Across this wave's verification work (T-571's original 905-row per-order check, reused by T-573 this session), the locally-cached `kalshi_order_status` field reads `"submitted"` for 100% of both the 35 confirmed-FILLED rows and the 731 confirmed-NOT_RETRIEVABLE rows — the field carries no information distinguishing a row later confirmed real from a row that could never be confirmed at all. This is consistent with GG-297's root-cause finding (the field is set once from `submit_order()`'s acceptance-time return value and never re-polled) but had not previously been stated as a direct consequence: any future session or script that filters, scores, or reasons about this ledger using `kalshi_order_status` as a fill-confidence signal will get zero discriminative value from it. |
| Why this matters | A field named `kalshi_order_status` reads as authoritative fill-status information to anyone encountering the schema without first reading GG-297. It is not — it is a submission-acceptance marker that never changes. This is the same naming-vs-behavior trap GG-298 already registered for `rejected_positions`; this is the second field in the same ledger schema found to have this property this wave. |
| Impact | MEDIUM: no data-loss or scoring-corruption risk on its own (no script currently observed relies on this field for a fill-confidence decision), but a standing trap for the next session that reaches for it expecting real status, exactly as GG-298 already documented for a different field in the same file. |
| Discovery | 2026-09-24, T-573 (this wave, block 34.2), Deliverable 3 observation while building the selection-bias test's field list — noted as a byproduct, not the deliverable's primary target. |
| Resolution | Not resolved — recommend either re-polling real order status periodically (as GG-297's Resolution row already recommends for a related reason) or renaming/documenting the field explicitly as submission-acceptance-only, not fill-status, so it stops reading as authoritative. No code change made (out of scope this session). |
| Cross-references | GG-297 (root cause: field set once at submission, never re-polled), GG-298 (same naming-vs-behavior defect class, different field), GG-300 (the independent per-order verification that surfaced this field's non-discriminating behavior). |

</details>

---

### GG-307 — `build_t4mlb_cohorts`'s edge-reconstruction formula has never been tested against T4M_ARITH/T4M_FLOW inputs, only against T4M-PROJ — a disclosed scope boundary on this wave's scoring-harness work, not a defect

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Premise holds: build_t4mlb_cohorts (scripts/clv_harness.py:315) exists, T4M_ARITH/FLOW remain BLOCKED per EXECUTION_BANDS.md; no test or reference to ARITH/FLOW in clv_harness.py (grep empty). Prospective scope boundary only. **Next:** No action until ARITH/FLOW activation is proposed; then validate the edge-reconstruction formula on that band's schema.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-307 |
| Category | Scope boundary / untested code path, surfaced by this wave's block 34.1 (T-572) and registered here per this wave's Deliverable 5 GG/DECISION_LOG ownership split. Not a confirmed defect — this entry documents an untested path so it is not silently assumed to work when T4M_ARITH/T4M_FLOW are eventually activated. |
| What was found | `build_t4mlb_cohorts`'s edge-reconstruction formula (part of this wave's block 34.1 scoring-harness build) was written and validated only against T4M-PROJ ledger rows — the sole ACTIVE T4M-band cell. T4M_ARITH and T4M_FLOW are built-but-BLOCKED per `EXECUTION_BANDS.md`'s Live Registry and were not exercised by this wave's harness at all; whether the same formula produces correct edge values for their (structurally different, per CLAUDE.md's band-description) inputs is unknown. |
| Why this matters | If a future session activates T4M_ARITH or T4M_FLOW and reuses `build_t4mlb_cohorts` unmodified, assuming it "already works" because it was validated this wave, that assumption would be unverified — the formula's correctness on those bands' input shape has never been checked. |
| Impact | LOW as filed: purely prospective, since T4M_ARITH/T4M_FLOW are currently BLOCKED and not contributing to any live cohort or gate calculation. Would become material only at the point either band is activated. |
| Discovery | 2026-09-24, T-572 (Wave 34 block 34.1, this wave), disclosed as an explicit scope boundary in its own results; handed to block 34.2 (this session) for registration per this wave's explicit task split. |
| Resolution | Not resolved — no action needed until T4M_ARITH/T4M_FLOW activation is proposed; at that point, the formula should be validated against that band's actual input schema before being trusted. No code change made this session (out of scope). |
| Cross-references | T-572 (discovering/building session), `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` § Live Registry (T4M_ARITH/T4M_FLOW BLOCKED status). |

</details>

---

### GG-312 — Register-parity failure class: 36 accepted ADRs accumulated with no `APPROVALS_REGISTER.md` row of their own, `check_register_parity.py` sees only 7 of them, and write-back is still manual

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Verified counts: 70 ADR-*.md files in 03_DECISIONS vs 42 ADR mentions in 00_ADMIN/APPROVALS_REGISTER.md; scripts/check_register_parity.py exists but write-back remains manual. **Next:** Backfill missing register rows and wire parity check to all ADRs.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-312 |
| Category | Governance / audit-trail integrity — the fifth recurrence of the GG-126 class (GG-108, GG-122, GG-126, GG-126-recurrence 2026-07-17, and now this) |
| What was found | A governance audit on 2026-09-29 found accepted ADRs with no `| ADR-NNNN |` row in `00_ADMIN/APPROVALS_REGISTER.md`. Re-derived from the files by T-582 (block 37.3): **36** accepted ADRs whose own decision has no register row (42 resolved ADRs lack a row literally named for them; 6 of those — ADR-0003, -0004, -0018, -0026, -0027, -0028 — are the subject of an APR row, e.g. APR-0011/0012/0018/0020/0021/0022, and are excluded). The 36 include load-bearing decisions: **ADR-0010** (band Kelly / reserve mandate), **ADR-0024** (stop-pivot criterion), **ADR-0001** (Compass OS), **ADR-0006** (exposure-based risk framework). The register-parity population is not a small legacy tail: ADR-0040 through ADR-0046 were accepted July 2026, after the convention of writing every accepted decision back to the register was already in force. |
| Why the existing checker did not catch it | `scripts/check_register_parity.py` (GG-126, extended with rule 5 in T-570) currently reports 15 mismatches and **detects 7 of the 36** (ADR-0001, -0010, -0015, -0024, -0032, -0045, -0046 via rule 5). The other 29 are invisible for two separate reasons: (a) **27 are on `00_ADMIN/REGISTER_PARITY_EXEMPTIONS.txt`** (ADR-0002, -0008, -0009, -0011, -0012, -0013, -0014, -0016, -0017, -0019, -0020, -0021, -0022, -0023, -0025, -0029, -0031, -0033, -0034, -0036, -0037, -0038, -0039, -0040, -0041, -0043, -0044) — the file's stated rationale is that these "predate the convention", which is not true of the July-2026 entries, and the file suppresses rules 2 and 5 for exactly this population; (b) **2 are invisible to the parser** (ADR-0006, -0007) — the checker reads only a line beginning `**Status`, and ADRs written with a `## Status` heading return None and hit the `no parseable Status header` skip (ADR-0004 has the same format). Rule 5 also produces false positives: it flags ADR-0003, -0018, -0026, -0027, -0028, which ARE registered as the subject of an APR row. So: rule 5 (the reverse direction, added 33.3/34.3) **does catch the class in principle but only for ADRs not on the exemption list and with a parseable Status line — it does not catch the class as it actually occurred.** |
| Why this matters | Founding-period decisions that govern sizing and stop criteria have no record of who approved them or when. The operator ratified them wholesale on 2026-09-29 (`APPROVALS_REGISTER.md`, T-582 entry); original sign-off dates are unrecoverable. Nothing prevents the next accepted ADR from being missed the same way: the write-back from "ADR accepted" to "register row" is a manual step with no forcing function, and the checker that would flag it is defeated by an exemption list plus a format assumption. |
| Impact | HIGH as filed: audit-trail gap on load-bearing decisions, recurred five times, with the detector demonstrably blind to ~80% of the current instance. No effect on live sizing (`kelly_fraction` values are governed by ADR-0048 and are unchanged by this gap or by the ratification). |
| Discovery | 2026-09-29 strategic-window governance audit; re-derived and characterised by T-582 (block 37.3). |
| Proposed remediation (NOT done in this block — recording only) | (1) Make `check_register_parity.py` parse `## Status` sections; (2) retire the exemption list for ADR ≥ 0040 and re-baseline the rest against the T-582 ratification entry (adding or removing an exemption is an adjudication and needs its own DECISION_LOG note); (3) exclude ADRs that are the subject of an APR row from rule 5; (4) a structural write-back: the ADR-acceptance path should emit the register row rather than rely on the author remembering. Each is separately scoped. |
| Cross-references | GG-126 (parent class), T-570 (rule 5), T-582 (this registration and the ratification entry), `00_ADMIN/REGISTER_PARITY_EXEMPTIONS.txt`, `00_ADMIN/APPROVALS_REGISTER.md`. |

</details>

---

---

### GG-316 — A T1 NFL run cannot be attributed to an actor: `approval_commit` is a static epoch marker, not a runtime capture, and no run/trigger/host field exists on any row or audit event — scheduling anything before fixing this reproduces GG-302 at higher frequency

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** Code grep (src, scripts): approval_commit is set by approval_commit_for_epoch / backfill_logic_epoch.py as a static epoch marker; no run/host/trigger field found on rows. **Next:** Add run_id/host/trigger fields to NFL T1 rows and audit events before scheduling.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-316 |
| Category | Run provenance / attribution — root-cause class behind GG-302 (T-587, wave 38.1) |
| What was found | `approval_commit` on every position row is `logic_epoch.CURRENT_APPROVAL_COMMIT = _BOUNDARIES[-1].commit_sha` (`paper_trader.py`, T-320): a constant baked into the source tree. It is identical for every run of every checkout at a given epoch, so it identifies neither the code that ran, nor how it was launched, nor where. Beyond `model_identity` (GG-267) and an internal `session_id` (a fresh uuid per process), no field on a T1 NFL position row or audit event records the deployed git sha, the trigger (cron vs manual), a run id linked to the row, or the host. `deploy/cron.conf` has no NFL entry (T-575/T-566), so every NFL run to date was manual. |
| Why this matters | GG-302's 42 rows are unattributable to any actor because of exactly this. A cron entry added on top of the same schema would produce scheduled rows indistinguishable from a hand-run, making the next quarantine decision equally unrecoverable at higher volume. Attribution has to exist before accrual does. |
| Impact | HIGH. Blocks admitting any NFL T1 row as evidence. Does not by itself invalidate MLB rows, which have their own provenance paths. |
| Discovery | Wave 38.1 brief, verified in source by T-587: `logic_epoch.py:603`, `paper_trader.py` position-row construction. |
| Resolution (code, this session) | **Chose "add a distinct runtime field beside `approval_commit`"; `approval_commit` is deliberately left unchanged** because backfill, band-monitor and replay tooling read it as an epoch marker. New `run_provenance.py` captures at runtime: `runtime_git_sha` (+ `runtime_git_dirty`), `run_trigger` (`cron`\|`manual`), `run_trigger_attested`, `run_id`, `run_host`, `run_started_at`, `run_pid`, and tty/ssh evidence. Every audit event is stamped via `ProvenanceAuditLogger` (including RiskEngine/PaperTrader events); position rows carry `runtime_git_sha`, `run_trigger`, `run_id`, `run_host`. **Trigger is attested, not inferred:** a scheduled entry must export `PMBOT_RUN_TRIGGER=cron`; anything else records `manual`. Absent provenance writes the literal `UNKNOWN`, never a static marker. Status stays OPEN until the fix is deployed AND a row written by the deployed process is read back with the fields populated. A merge is not a deployment (GG-279). |
| Known limits | The `cron` trigger is a self-attestation; the tty/ssh evidence fields make a false attestation checkable but do not prevent it. The `paper_trader.py` opt-in pass-through sits slightly outside the wave's stated scope fence; it is the only way for position rows to carry the fields. Rows written before deployment have no such fields. |
| Cross-references | GG-302 (the incident), GG-267 (model-identity precedent), GG-279, GG-262 (VPS crontab diverges from repo), T-320, T-575, T-587. |

</details>

---

### GG-317 — The T1 NFL run script defaults to the fixed-p STUB model and will open one paper row on every market with a nominal edge: one hand-run on 2026-09-29 wrote 802 STUB-labeled rows into the NFL pool (66% of evaluated markets), inflating the pool with rows that are pipeline-shape evidence only

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified: run_t1_nfl_game_market.py l.19 states the default wired model is StubNFLForecastModel (PROVENANCE 'STUB ... GG-255', l.171); live NFL pool has 4 open, all STUB. **Next:** Refuse to run the stub model without an explicit flag.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-317 |
| Category | Evidence hygiene / sample inflation (T-587 D2 finding) |
| What was found | `main()` in `run_t1_nfl_game_market.py` defaults to `StubNFLForecastModel` (fixed p=0.55, no NFL C2/C3 exists, GG-255). The D2 hand-run (run_id `PT-T1-NFLGM-71208CC5`, sha `1d65b9b`, trigger `manual`, host `earlgrey`) evaluated 1,209 markets over 18 games: OPENED 802, REJECTED 288, REFUSED_NO_MODEL 50, REFUSED_NO_EDGE 40, REFUSED_STAKE 29. Pool `open_positions` went 22 to 824. All 802 rows carry `model_identity` = STUB and $1 measurement stakes. Approval is driven by the constant p versus each quote, so the 66% rate is a property of the stub, not of any model. |
| Why this matters | Row counts in this pool now overstate usable evidence by about 36x. Any band monitor or n-count that counts NFL T1 rows without filtering `model_identity` will read a large clean_n that means nothing. The rows are attributable (D1) but not model evidence. Re-running the script re-opens new rows; whether it de-duplicates against still-open tickers is UNVERIFIED. |
| Not done here | Nothing was quarantined, deleted or reclassified (out of scope; changing pool contents is an operator call). The 42 GG-302 rows remain quarantined and were not used. A pre-run backup of the pool exists on the VPS: `logs/paper_portfolio_t1_nfl_game_market.pre_t587_handrun_20260929.json`. |
| Suggested resolution | Operator decides: (a) quarantine all `model_identity` STUB rows from every n-count, keyed on `runtime_git_sha`/`run_id`; (b) require an explicit flag for STUB runs; (c) verify re-run de-duplication before any schedule. |
| Census (T-588, 2026-09-30) | Read-only census of the six live VPS pool files (copies; sha256 recorded). Only one pool contains any STUB row: NFL T1 game-market, open_positions 824 = 802 STUB + 22 EXP-027 LR; closed 20 = all EXP-027 LR. Every other pool row is UNATTRIBUTED (model_identity absent or literal UNKNOWN): MLB T1 `paper_portfolio_mlb.json` 468 closed / 17 open / 16 rejected, all absent, epochs 1-8; MLB T4 `paper_portfolio_mlb_t4.json` closed 3,923 = 2,994 absent + 929 UNKNOWN, open 63 UNKNOWN, rejected 2,000 UNKNOWN; NBA T1 158 closed and NBA T4 2,895 closed, all absent. Rows carrying a real run_id: 802 (the STUB rows); zero anywhere else, including the 20 closed EXP-027 rows. Full tables in the T-588 results summary. |
| Mechanism confirmed (T-588) | A STUB row with a valid `logic_epoch` passes `is_clean_for_band()` because that predicate reads only the stamped epoch. Fix path is the new unwired predicate `is_countable_evidence()` in `logic_epoch.py`; nothing counts with it yet. Status stays OPEN. |
| Cross-references | GG-316 (provenance that makes these rows identifiable), GG-302, GG-255, GG-267, T-587. |

</details>

---

### GG-320 — T4M-PROJ fails ADR-0068 criterion C5: a stripped three-scalar tree is filed in a band whose measured cadence (~60s) does not pay for the stripping, and the latency thesis that licensed it measured NOT SUPPORTED

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** ADR-0068 criterion C5 finding stands; T-569 latency NOT SUPPORTED. Operator decision on refiling. **Next:** Operator decision on T4M-PROJ band placement.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-320 |
| Category | Band misfiling — shallow without fast (C5, ADR-0068 PROPOSED) |
| What was found | T4M-PROJ (the only ACTIVE cell in the registry) evaluates `p_hits_gte_threshold(h_so_far, ab_remaining, ba_l10, threshold)`: three scalar inputs plus the threshold, no pitcher, park, weather, lineup, score or leverage input. Its stripping was licensed by the EXECUTION_BANDS.md clause that sub-second execution is the edge. The pipeline polls on a ~60s cycle; BAND_ASSIGNMENT_FRAMEWORK.md § P3 independently records the T5 kill-switch SLA as 60s, "12x too slow". T-569 tested the latency premise and returned NOT SUPPORTED (current feature set). |
| Why it matters | The cell's tree depth was justified by an assumed speed advantage that was never measured and, when measured, was not found. A cell that is shallow without being fast is misfiled, not optimized. |
| Scope of this entry | Registered by T-592 at the start of the run so the number is reserved. The full 92-cell C5 table (which other cells share this mechanism, and how many are UNKNOWN because unbuilt) is in the T-592 results summary; a follow-up entry will be added there only for further distinct misfiled mechanisms. |
| Not done here | No cell reassigned, demoted, activated or deactivated. No sizing or kelly_fraction touched. T-569's verdict is not relabeled: it is a statement about the current feature set, not a permanent property of the band. |
| Suggested resolution | Operator decision, with DECISION_LOG entry + DS sign-off: either refile T4M-PROJ to the band its cadence supports and deepen the tree accordingly (ADR-0068 corollary: more structure, not automatically more speed), or produce a measured execution advantage. Blocked on ADR-0068 sign-off. |
| Cross-references | ADR-0068 (PROPOSED), ADR-0014, T-569, T-583, GG-318, GG-319, T-592. |

</details>

---

### GG-323 — T4 cycle log carries game-state fields on 0.9% of rows; the T-583 harness admits only a pre-epoch-12 window of ~210 games; September cycle rows have no decoupled outcomes

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Claim is stale as a number but premise holds: VPS cycle log 2026-10-08 has 456,964 rows, 31 keys; home_score/away_score/inning_half/outs/on_base fields non-null on 24,057 rows (5.3%, first 2026-09-29T18:16Z), pitcher fields on 19,176; ~95% of rows (all pre-09-29) lack them. The prior sample only saw non-null inning/h_so_far/ab_so_far, which are not the fields claimed. **Next:** Update entry figures (0.9% -> 5.3% and rising ~daily); state fields accrue forward only, so no backfill is possible; re-measure at harness decision time and register September decoupled-outcome fill separately.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-323 |
| Category | Evidence adequacy: a scoreable T4 structure candidate is constrained by logged inputs, cohort labels, and outcome coverage (T-598, GG-320) |
| What was found | (1) `t4_mlb_cycle_log.jsonl` (436,747 rows, 31 distinct keys, not 30) carries `home_score, away_score, inning_half, outs, on_first/second/third, current_pitcher_*, pitcher_pitch_count` on 3,840 rows (0.9%), all from 2026-09-29. A candidate using base/out/score/pitcher state cannot reach the harness minimum of 30 train and 30 test games. (2) `ba_l10_shrunk`, the input the live incumbent uses, exists only from 2026-07-18. (3) Rows timestamped 2026-07-31 or later label as logic epoch 12; the harness refuses T4M-PROJ epoch 12 by label, and 879 manifest tickers are refused by ticker. The clean window is therefore 2026-07-02 to 2026-07-30 by ticker-derived date, about 210 games, of which about 113 (07-18 to 07-30) have the shrunk input. (4) Decoupled outcomes (T-421, T-503) cover cycle tickers only through 2026-08-19; 2026-08-20 to 2026-09-29 (about 40 game-days) has none. (5) `game_date` in the cycle log is wrong on a majority of rows (GG-164); ticker-derived date is used throughout. |
| Why it matters | Any T4 structure result is conditioned on a summer-only, early-season-of-logging window, and cannot test state-dependent structure until state accrues. A null there is a statement about this window, not about the band. |
| Done | Field coverage, window counts and outcome coverage measured read-only from a scratchpad copy (sha256 440df62c...66b4) and recorded in the T-598 pre-registration. |
| Not done | No resolution of September outcomes; no state-field backfill. Not in scope for T-598 (Hard Rule 11). |
| Cross-references | GG-164, GG-170, GG-320, T-583, T-598. |

</details>

### GG-326 — The price archive has a 6-12h-to-close capture hole and ~20-minute resolution; policy (c) fill evidence and the 6-12h cost cells depend on it

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** EXP-032 results line 93 confirms 6-12h capture hole (HIT 1,717 vs 44,926 snapshots at 12-24h) with fix owned by 44.3; archive still writing (prices_2026-10-08.jsonl on VPS). Did not verify whether 44.3 changed capture cadence or whether the hole persists in recent days. **Next:** Count snapshots per hours-to-close bucket for the last 7 days of PRICE_ARCHIVE to see whether the hole is closed; resolve if so.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-326 |
| Category | Data capture adequacy (T-603 / EXP-032) |
| What was found | Snapshots at 6-12h to close are in the low thousands against tens of thousands in neighbouring buckets (e.g. KXMLBHIT 1,717 vs 44,926 at 12-24h). Snapshot spacing (~20 min) means a resting-order fill between snapshots is invisible, so policy (c) fill rates are lower bounds and its E is conservative by construction. Archive `close_time == expiration_time` on all 2.125M rows, so the archive cannot supply a settlement clock; EXP-032 used the EXP-031 settlement cache. |
| Why it matters | The cheapest-point search and the fill evidence cannot be finer than the capture. |
| Done | Reported in EXP-032 results section 6. |
| Not done | Fix owned by 44.3 (archive self-sufficiency); not touched here. |
| Cross-references | GG-325, EXP-032, T-603 |

</details>

### GG-327 — EXP-032 clock sanity gate range [2.0, 4.5]h is mis-sized for partial-game families; F3/F5/F5SPREAD/F5TOTAL could not be re-priced by hours-to-start

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** EXP-032 results gate table confirms F3/F5/F5SPREAD/F5TOTAL FAIL the frozen [2.0,4.5]h clock gate (close 1.0-1.7h after start), policy (b)/drift UNMEASURED; no follow-up experiment with a per-family gate found in 05_RESEARCH_EXPERIMENTS. **Next:** Pre-register a new experiment with per-family clock gates for the four partial-game families.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-327 |
| Category | Pre-registration design defect (found after the freeze, not edited) |
| What was found | The frozen gate required median(close - start) in [2.0, 4.5]h. F3/F5/F5SPREAD/F5TOTAL markets close 1.0-1.7h after start (>99% inside (0, 8]h), so they failed the gate and fell back to the close clock: policy (b) and drift UNMEASURED for them. Their policy (a) and (c) results stand. |
| Why it matters | Four of the families EXP-031 killed by H alone are exactly the ones whose cost-by-time surface was not measured. |
| Done | Reported as-is; threshold not changed after seeing results. |
| Not done | A follow-up pre-registered experiment with a corrected per-family gate (a NEW experiment, not an edit). |
| Cross-references | GG-325, EXP-032, EXP-031 |

</details>

### GG-328 — Archive books are exactly complementary (no_ask = 1 - yes_bid); YES/NO cost asymmetry exists only in availability, contradicting the "separate side costs" premise

**Status:** WATCH ITEM · **Severity:** LOW

Re-filed 2026-10-21 under the operator's observation rule. Reopens if: the archive books stop being exactly complementary (no_ask != 1 - yes_bid).

**Current state (2026-10-08, W59.1):** Finding only; books exactly complementary. **Next:** Drop the separate-side-cost premise from future designs.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-328 |
| Category | Finding / measurement premise (T-603 / EXP-032) |
| What was found | Zero residual on 2.125M rows for both identities, so the two-sided toll is side-symmetric. Availability is not: KXMLBHIT NO-side buyable 64.0% vs YES 90.8% of snapshots; `yes_bid == 0` on 9.3% of rows. Worth knowing whether the archive derives one side from the other (capture-time construction) rather than recording both books. |
| Why it matters | If the NO book is derived, side-specific depth and fill evidence are not independent observations. |
| Done | Measured and reported. |
| Not done | Check the capture path with 44.3's owner. |
| Cross-references | GG-325, GG-326, EXP-032 |

</details>

### GG-330 — Q7 ledger-invariant check is vacuously green in a fresh worktree (SOURCE_UNAVAILABLE x3, exit 0)

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Verified: scripts/assert_ledger_invariants.py run in this fresh worktree reports SOURCE_UNAVAILABLE 3 times and exits 0. **Next:** Make a fresh worktree fail loudly (or resolve sources via an env path) when sources are unavailable.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-330 |
| Category | Monitor honesty (session-start protocol Q7) |
| What was found | `scripts/assert_ledger_invariants.py` in a new isolated worktree reports 0 violations because its logs/cache inputs are absent (SOURCE_UNAVAILABLE x3). Alarm-only exit 0 makes this indistinguishable from a clean pass. |
| Why it matters | Isolation (Step 0a) is the default, so the default session runs Q7 against nothing and reads green. |
| Disposition | Register only (HR11). Fix belongs to a separate task: print an explicit "NOT EVALUATED" line when every source is unavailable. |

</details>

### GG-331 — PRICE_ARCHIVE exists only in the shared main tree (gitignored); isolated worktrees cannot reproduce archive-based results without an absolute path

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** .gitignore l.111 ignores exp_output/PRICE_ARCHIVE/; archive therefore exists only in the shared main tree (verified this session). **Next:** Support a PRICE_ARCHIVE_DIR env var in archive-reading scripts and document it.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-331 |
| Category | Reproducibility (EXP-031/032/033 inputs) |
| What was found | `exp_output/PRICE_ARCHIVE/` (1.1G) is gitignored and present only under the main checkout. A worktree has none, so `market_efficiency_survey.py` needs `--archive <absolute main-tree path>`. |
| Why it matters | Results are reproducible only on the one machine and only while the shared tree is intact; the archive is the sole copy of snapshot data that candles may not replace. |
| Disposition | Register only. This block reads it read-only by absolute path. |

</details>

### GG-332 — Kalshi fee schedule PDF unreachable (HTTP 429) from every source tried; ADR-0016 divergence cannot be confirmed from the primary document

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Re-probed this session: kalshi.com/regulatory/fee-schedule returns HTTP 429 and the S3 PDF URL returns 404. **Next:** Operator downloads the PDF by hand and commits it, or confirm via support.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-332 |
| Category | Premise verification (D1c) |
| What was found | `https://kalshi.com/docs/kalshi-fee-schedule.pdf` returned 429 via WebFetch and curl (with and without a browser UA, plus a web.archive.org copy) on 2026-10-02. Published API docs (openapi.yaml, 2026-10-02) state series carry `fee_type` (quadratic, quadratic_with_maker_fees, quadratic_with_combo_maker_fees, flat) and `fee_multiplier`, and that `quadratic` is described by the PDF's General Trading Fees Table. KXMLBTEAMTOTAL reports `quadratic`, multiplier 0.5. Fee Rounding doc (2026-10-02): trade fee is rounded UP to $0.000001; rounding fee and rebate align balances to $0.0001 (direct) or $0.01 (non-direct). |
| Why it matters | ADR-0016 uses 0.07*P*(1-P) with no multiplier and no rounding. A 0.5 series multiplier would halve it for MLB series. The formula itself is unconfirmed. |
| Disposition | Do not assert the venue formula until the PDF text is read. Carry both fee models with the series multiplier as a stated sensitivity. |
| Update 2026-10-02 (W47.1, from EXP-035 D2(e)) | Series API (retrieved 2026-10-02): KXMLBHIT and KXMLBTEAMTOTAL `fee_type=quadratic`, `fee_multiplier=0.5`; KXMLBGAME `quadratic_with_maker_fees`, 0.5. Fee-rounding doc defers the model; get-series-fee-changes lists fee types with no formula; `getting_started/fee_schedule` is 404. Coefficient still NOT established. Re-score of published E at k=0.07 vs inferred 0.035 left both published NO verdicts unchanged (fee only subtracts). Policy (c) E not re-scored (maker/fill fee treatment unestablished). The divergence is carried here, not as a separate gap. |

</details>

### GG-333 — EXP-035 Part 1 correctness gate FAILED (G2, G3, G4, G5, G7): hourly candles do not reproduce the archive's B/H; candle numbers VOID

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** EXP035_RESULTS_board_survey_sports_2026-10-02.md l.1-5: Part 1 FAILED (G2 0.335 vs 0.80, G3 0.472 vs 0.95, G4, G5, G7), candle numbers VOID; verdict standing and unrescued. **Next:** Run the pre-registered D3 on a fresh family; do not reuse candle numbers.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-333 |
| Category | Instrument validity (D1b) |
| What was found | Gate run 2026-10-02 against the frozen Part 1 pre-registration (e28166a), no rescue. Passed: G1 (ticker coverage 1.000; usable candle coverage 0.9976), G6 (sign agrees; E_candle -0.0678 vs ref -0.02403). FAILED: G2 share 0.335 (need >=0.80, n=1988); G3 share 0.472 (need >=0.95); G4 B_candle 0.03193 vs 0.02572 (tol 0.003, n=10675); G5 H_candle 0.090 vs 0.04 (tol 0.005); G7 tau bucket [24,48) median half-spread 0.065 vs 0.03 (other buckets ok). Artifact: exp_output/EXP-035-BOARD-SURVEY-SPORTS/gate_result.json. |
| Why it matters | Per pre-registration, any failure voids every candle-derived number. EXP-035 stops after D1; no D2-D7 outcome statistic may be computed from candles. The candle-based E is more negative than the archive's (-0.068 vs -0.024) but is VOID and must not be cited as evidence either way. |
| Disposition | Hand back to operator. Do not alter G1-G7 thresholds. Open questions (not tested): whether hourly OHLC close is a different object from the archive's first-seen quote (a design issue the pre-registration did not anticipate), vs a code defect in evaluate. Both need operator decision before any re-registration via AMENDMENT. Candle-vs-archive discrepancy also bears on the archiver docstring correction (GG-329): history is reachable but not equivalent to the archive, so the docstring edit was NOT made. |

</details>

### GG-340 — Frozen gate pre-registrations can leave a lookback/window unspecified, so a 'none exists' outcome is implementable as a window artifact

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** No pre-registration template in 05_RESEARCH_EXPERIMENTS or 08_MODEL_RISK_GOVERNANCE requires a lookback/no-data rule; DECISION_LOG 2026-10 retains it as an open concern (item 4). Disposition is a process rule, not yet encoded. **Next:** Add mandatory lookback bounds and no-data rule field to the pre-registration template/checklist.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-340 |
| Category | Instrument validity (pre-registration drafting) |
| What was found | EXP-034 D1(b) frozen text did not fix the candle lookback; the runner chose 1 hour and 28/84 pairs came back UNMATCHED. A post-hoc 30-day hourly lookback (diagnostic only, verdict unchanged) made the prevailing close equal the live read for all four thin tickers. Source: EXP034_NONSPORTS_CONTROL_RESULTS_2026-10-02.md item 1. |
| Why it matters | A gate whose pass/fail depends on an unstated window is decided by the implementer, not the pre-registration. Thin books go 10-25h without a candle, so the default matters. |
| Disposition | Every future gate pre-registration must state lookback bounds and the no-data rule explicitly. EXP-034's original FAIL stays on record; the corrected re-test is a new amendment (W47.1 D3). Not a code fix. |

</details>

### GG-341 — exp_output raw stores are gitignored, so experiment quote/candle files are not reproducible from git (hash in manifest only)

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** .gitignore l.101-111 ignores exp_output CSVs, exp_output/MLB/ and PRICE_ARCHIVE/; only selected results JSONs are un-ignored (l.126-135). **Next:** Commit manifest hashes for every experiment input store.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-341 |
| Category | Reproducibility |
| What was found | EXP-034's quote file is gitignored; D1B_SAMPLE_MANIFEST.md carries only its sha256. Related to but distinct from GG-331, which is PRICE_ARCHIVE specifically. Source: EXP034_NONSPORTS_CONTROL_RESULTS_2026-10-02.md item 3. |
| Why it matters | A reviewer cannot re-run a comparison from a clone; the hash proves a file existed, not what it contained. |
| Disposition | Decide per experiment which raw stores are committed (small) vs hashed and archived elsewhere. Not decided here. |

</details>

### GG-342 — Remote branch hygiene: a stale pre-rebase branch, 33 unmerged remote branches, ~8 of them content-landed under other SHAs and unlandable by ancestry

**Status:** OPEN · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Operator approved a diff-confirmed prune. `04_EXECUTION/GG342_branch_prune_list.md` lists 36 unmerged remote branches by patch-id check (`git cherry`): 16 content-landed (delete candidates), 20 carry unlanded commits (keep). Nothing deleted; awaiting the operator OK on list A.

**Current state (2026-10-08, W59.1):** Counts changed: git branch -r shows 84 remote branches, 47 not merged into origin/main (this session); earlier entry said 33. **Next:** Triage the 47 unmerged branches; delete content-landed ones after confirming by diff.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-342 |
| Category | Repository hygiene |
| What was found | Remote branch session/...-kalshi-nonsports-control holds a stale pre-rebase line (0f5de4e); EXP-034 work was pushed to the -w46 branch instead of force-pushing (EXP034_NONSPORTS_CONTROL_RESULTS_2026-10-02.md item 5). 33 unmerged remote branches, ~8 landed under other SHAs and so read unlanded forever (WAVE45_land_the_record_results.md item 11). |
| Why it matters | Merge-confirmation by ancestry (claim_session.sh) reports content-landed work as unlanded, so closure state is unreliable for those branches. |
| Disposition | Needs a content-equivalence landed check and an operator-approved prune. No branch deleted here. |

</details>

### GG-344 — audit_mlb_t4.jsonl CONTAMINATION_HALT count (162,168) is unusable as a health signal

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** VPS audit_mlb_t4.jsonl CONTAMINATION_HALT count is 164,048 on 2026-10-08 (162,168 at registration, still growing) while recency-windowed game_state_fresh failures in tail -500 are 0, so the raw count carries no health signal. **Next:** Replace the raw-count line in CLAUDE.md Step 4 / governance_scan.sh with the tail-windowed game_state_fresh count only, or retire it.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-344 |
| Category | Monitoring validity |
| What was found | Step 4's CONTAMINATION_HALT count was 162,168 on 2026-10-02; the protocol itself calls non-zero 'expected at game-end', so the number cannot distinguish healthy from broken. Source: W45_462_sync_and_diagnose_results.md item 5. |
| Why it matters | A signal that is always non-zero carries no information; a real contamination event would be invisible in it. |
| Disposition | Replace with a recency-windowed, non-game-end count or retire the line. Not changed here. |

</details>

### GG-345 — Step 4 has no season awareness and will false-alarm through the off-season (0-player T1 runs, T4 cycle-log age, feature CSV stuck at 2026-09-27)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** CLAUDE.md Step 4 text mentions 'during MLB season' only as prose (l.290); no code/hook gates the checks by season. **Next:** Add a season flag to the session-start health probe.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-345 |
| Category | Monitoring validity |
| What was found | 2026-10-02: T1 MLB shows 0 players on recent runs, T4 cycle-log last row 2026-10-02T02:53Z (age 19h), feature CSV stuck at 2026-09-27 post regular season. 46.2 diagnosed these as EXPECTED (season end) but the protocol cannot tell expected from broken. Source: W45_462_sync_and_diagnose_results.md items 6 and 8; EXP034_NONSPORTS_CONTROL_RESULTS_2026-10-02.md item 6; WAVE45_land_the_record_results.md item 4. Diagnosis of those anomalies is dispositioned there, not re-done. |
| Why it matters | The protocol says 0 players in season is a signal failure; with no calendar it either cries wolf all winter or trains sessions to ignore it, which is how GG-049 stayed hidden. |
| Disposition | Add a schedule-aware expectation (games on slate yes/no) to Step 4. Not changed here. |

</details>

### GG-346 — PIPE-08 schedule validator fails with HTTP 406: 110 occurrences since 2026-07-03

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified: run_schedule_validator_mlb.py:100 sends date as %m/%d/%Y; repair_stuck_mlb_positions.py:122 and fetch_hits_unblocked_network.py:12 document the schedule endpoint 406s on some URL shapes. **Next:** Switch validator to the ISO-date URL shape and add a regression test.

**Current state (2026-10-22, GA-5):** Fix landed in repo, pending deploy and verification. Box read-only test: statsapi `date=2026-10-20` → 200, `date=10/20/2026` → 406. `run_schedule_validator_mlb.py` and `run_t4_mlb_live.py` (the only two `%m/%d/%Y` sites in src/scripts) now send ISO dates; regression test `test_fetch_schedule_uses_iso_date_gg346` added (28 passed). Closes after a clean box run post-deploy.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-346 |
| Category | Pipeline integrity |
| What was found | MM/DD/YYYY date URL returns 406, ISO date returns 200, per 46.2's diagnosis. Source: W45_462_sync_and_diagnose_results.md item 1. |
| Why it matters | A validator that fails 110 times and does not stop the pipeline is either dead or unread; both mean a guard is not guarding. |
| Disposition | Register only; fix is out of this block (Rule 11). |

</details>

### GG-347 — Unattributed manual restarts of t4-mlb (and dashboard), plus an ssh poller from 73.231.159.158

**Status:** OPEN · **Severity:** MEDIUM

**Operator answer (2026-10-21 19:15 PT):** "I'm almost always working on this at home (about 95% of the time) so yes it's probably my home connection". The dashboard restarts match his old `Reload Dashboard.command` (it ran `systemctl restart` over SSH; retired to `_to_delete/` 2026-10-21). Next: the gap agent closes this as the operator's own access, unless a login appears from another address.

**Current state (2026-10-08, W59.1):** VPS journalctl 2026-10-03 to 10-07 shows 8 more t4-mlb Stopping/Started pairs (6 on Oct 3 01:12-01:33 UTC, 2 on Oct 5 07:57, 1 on Oct 7 06:13); last -i shows root login from 73.231.159.158 Sep 22 04:35-06:51 and auth.log shows many publickey root logins from the same IP on Oct 8 01:25-01:27 UTC (likely this session's own operator IP, so poller attribution is probable but unconfirmed). No manual-service-action log exists; restarts remain unattributed. **Next:** Operator confirms 73.231.159.158 and the restart bursts are theirs, then add a manual-service-action log or restart note and close.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-347 |
| Category | Operational provenance |
| What was found | t4-mlb manually restarted 10/2 at 19:42, 21:09, 21:17, 21:45 UTC and 10/1 01:35-02:52 UTC by an unidentified actor (W45_462_sync_and_diagnose_results.md item 2). Manual dashboard restarts unrecorded; ssh poller from 73.231.159.158 seen (WAVE45_land_the_record_results.md item 6). |
| Why it matters | Restarts reset session_id and counters and can change what a process reads; unrecorded ones break attribution of any T4 result window (compare GG-321). |
| Disposition | Needs the operator to say whether these were theirs, and a place to log manual service actions. Not investigated further here. |

</details>

### GG-348 — t4-mlb.timer is inactive with no NEXT; last fired 2026-07-04

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Verified on VPS: t4-mlb.timer 'inactive (dead) since Sun 2026-07-05 08:23:30 UTC'. The t4-mlb service itself is active (ActiveEnter 2026-10-07 06:13 UTC). **Next:** Decide whether the timer is retired (then delete unit) or must be re-armed.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-348 |
| Category | Operational integrity |
| What was found | systemd shows the timer inactive since 2026-07-04 while t4-mlb.service is active. Source: W45_462_sync_and_diagnose_results.md item 3. |
| Why it matters | If the timer was meant to run something, it has not for three months; if not, it is dead config. |
| Disposition | Register only; owner to confirm intent. |

</details>

### GG-349 — Stale .git/index.lock held open by a Virtualization XPC host process blocks all shared-tree git writes; recurrence unknown

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** No .git/index.lock present in the shared tree today (ls, this session); recurrence still unknown. **Next:** Log lock occurrences in session_guard.sh to establish recurrence.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-349 |
| Category | Tooling |
| What was found | WAVE45_land_the_record_results.md item 1; W45_462_sync_and_diagnose_results.md item 7. Lock removed by 46.2; cause is a VM host process, not a git session. |
| Why it matters | A silently held lock blocks every concurrent session in the shared tree and tempts a blind lock delete. |
| Disposition | Register only; recurrence unmonitored. |

</details>

### GG-353 — Claim rows with open-ended or TBD ID ranges give no collision protection and block later claims

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** SESSION_CLAIMS.md contains 66 lines mentioning TBD (grep -ci, this session). **Next:** Make claim_session.sh reject TBD/open-ended ranges.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-353 |
| Category | Concurrent-session safety |
| What was found | WAVE45_land_the_record_results.md item 9. Observed at this session: T-605's unclosed claim 'GG-334+' made claim_session.sh refuse a GG-334 claim, and concurrent T-607/T-608 claims landed while this block claimed, forcing a re-claim at T-615/GG-340. Related: GG-322, GG-162. |
| Why it matters | TBD ranges do not reserve anything, and open-ended ranges reserve everything. |
| Disposition | Require explicit closed ranges at claim time; not changed here. |

</details>

### GG-354 — Full test suite exceeds 10 minutes in the foreground and there is no documented fast subset

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Only a 'unit' marker is defined in pyproject.toml (l.81); no documented fast-subset command found in CLAUDE.md. **Next:** Define and document a <2 min smoke subset.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-354 |
| Category | Tooling |
| What was found | Source: WAVE45_land_the_record_results.md item 10. |
| Why it matters | Sessions either skip tests or burn context waiting. |
| Disposition | Document a fast subset per area; not done here. |

</details>

### GG-355 — Nothing checks that a closing session produced Q1-Q7 evidence

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** grep for Q1/Q7 in scripts/close_session_claim.sh and .claude/commands/session-end.md returns nothing; no closing-session evidence check exists. **Next:** Have close_session_claim.sh require a Q1-Q7 evidence file.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-355 |
| Category | Protocol enforcement |
| What was found | 46.2 closed without running or showing Q1-Q7; its own summary lists this. Source: W45_462_sync_and_diagnose_results.md item 10. |
| Why it matters | Session-start protocol exists because model assertions of 'clean' are not evidence (GG-001); closure is not gated on it. |
| Disposition | Register only. |

</details>

### GG-356 — Transient GitHub push failure ('unable to write file ...pack') with no retry guidance

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** claim_session.sh and close_session_claim.sh retry on rebase/push rejection only; no handling of 'unable to write file ... pack' errors. **Next:** Add a generic push retry with backoff and a gc hint.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-356 |
| Category | Tooling |
| What was found | Single transient occurrence. Source: WAVE45_land_the_record_results.md item 7. Not shown to be recurring. |
| Why it matters | Low unless it recurs; a push that fails mid-close-out risks an unpushed handoff. |
| Disposition | Observation only; registered because the item was listed, not because a defect is established. |

</details>

### GG-402 — Shadow runner hardcodes fee_multiplier=1

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Verified: pregame_shadow/fees.py l.4 states the fee coefficient is INFERRED (0.07*0.5*q*(1-q)), not sourced from the venue schedule. **Next:** Pull the Kalshi fee schedule and replace the inferred coefficient or cite it.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-402 |
| Category | Correctness |
| What was found | fee_multiplier=1 was verified 2026-10-02 but is hardcoded; must be re-read from the series endpoint before any CANDIDATE call. |
| Source | EXP036 results GAP 4 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-403 — NHL Kalshi OT/SO settlement treatment and TEAM_ALIASES unverified

**Status:** PARTIALLY RESOLVED (2026-10-03, 51.2: VERIFIED — Kalshi uses SJ/TB/LA/NJ; aliases + 2/3-letter parser + tests fixed on branch session/20261003T201919Z-w51-nhl-team-codes, NOT merged/deployed; close on deploy. OT/SO half: scoring uses Kalshi result, no change needed.) · **Severity:** MEDIUM

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-403 |
| Category | Data |
| What was found | OT/SO treatment for ML/puck line is assumed to follow the official final result; TEAM_ALIASES is empty (Kalshi code assumed = NHL abbreviation). Unverified; wrong mapping silently drops or mis-settles rows. |
| Source | EXP036 results GAP 5 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-404 — Live Kalshi quotes can be very wide; shadow scoring must filter on half_spread

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified: runner.py l.74 records half_spread; scoring.py has no half_spread filter (grep this session). **Next:** Add a half_spread cap to shadow scoring and pre-register it.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-404 |
| Category | Scoring |
| What was found | Observed live quote bid 0.01 / ask 0.35; mid-based Brier on such quotes is meaningless. Scoring must filter on half_spread. |
| Source | EXP036 results GAP 6 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-405 — NHL shadow: T1 abstentions uninvestigated, T3 cron-window coverage and 2026 schedule match unverified, travel not modelled

**Status:** OPEN (2026-10-03, 51.2: abstention-counter half DONE on the same unmerged branch; matinee cron-window half and travel remain open. GG-403's parser drop is a plausible cause of the 195-vs-240 shortfall, unproven.) · **Severity:** LOW

**Current state (2026-10-08, W59.1):** scripts/nhl_shadow_eval.py:204 now bumps forecast_none:<last_abstain> counters (abstention counter half done); BANDS T3 = (0.25,1.0) window defined at line 33; no travel feature found in nhl_features.py/nhl_pregame.py. Matinee cron-window coverage and schedule match not verified. **Next:** Read arm_shadow_crons NHL T3 cron vs matinee start times and report abstention counter output from a real run.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-405 |
| Category | Coverage |
| What was found | Three unverified coverage/feature assumptions in the NHL shadow, none investigated. |
| Source | EXP036 results GAP 7 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-406 — Shadow code on VPS is not auto-pulled on later pushes

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** VPS /opt/prediction-market-bot is on branch main at 85004525 and is 1 commit behind origin/main (ssh, this session); no auto-pull is configured. **Next:** Add a deploy step or cron git pull for shadow code.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-406 |
| Category | Deployment |
| What was found | VPS is only updated by a manual pull; landed shadow code does nothing until a local session runs scripts/arm_shadow_crons.sh. Silent gap between 'landed' and 'running'. |
| Source | EXP036 results GAP 8; 48.1 handoff |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-408 — EXP-027 NFL incumbent has no persisted artifact and is moneyline-only: no head-to-head possible

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** exp_output/NFL/exp027_hyp012_result.json and exp027_epa_splits_candidate_result.json are tracked (result JSONs only); src nfl_exp027_adapter.py and scripts/exp027_hyp012_nfl_moneyline_backtest.py exist, but no persisted model artifact found (models/ has nfl_pregame_v1*.json only, which is the ADR-0070 candidate). Moneyline-only scope unchanged. Not exhaustively checked for an incumbent artifact. **Next:** Decide: persist incumbent artifact via adapter refit, or drop head-to-head claim in ADR-0070.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-408 |
| Category | Model governance |
| What was found | ADR-0070's candidate cannot be compared against the incumbent because the incumbent was never saved and covers one market family only. |
| Source | EXP037 D0 harvest report §4 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-409 — EXP-037 brief's five-branch list was not recoverable from session context

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Process finding about a past brief; nothing in code to verify. No evidence of a brief-template change requiring explicit branch lists was found. **Next:** Add explicit branch list requirement to the brief template, then close.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-409 |
| Category | Process |
| What was found | The harvest could not enumerate the five branches the brief named; recovery depended on session memory. Fork-A git cherry list was also guessed. |
| Source | EXP037 D0 §4; SESSION_HANDOFF_20261002_2357 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-410 — NFL/MLB shadow T1, T2 and T3 use identical features

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** NFL: pregame_shadow/nfl_forecaster.py:120 builds one row via builder.row(home,away,as_of,rest) with no band-specific inputs, so T1/T2/T3 differ only by as_of. MLB: mlb_forecaster.py docstring says confirmed starter differs T1 vs T3, so the entry's claim is only partly true for MLB. **Next:** Correct entry scope to NFL (and MLB where starter unconfirmed); treat bands as one evidence stream in scoring.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-410 |
| Category | Model design |
| What was found | Frozen model v1 uses the same feature vector at every band; bands differ only by window, so T1/T2/T3 rows are not independent evidence. |
| Source | SESSION_HANDOFF_20261002_2357 (47.2) |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-415 — players_2026.json is stale

**Status:** WATCH ITEM · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Operator disposition: retire at season end. The file is a regenerable cache (`scripts/generate_mlb_features.py` l.210-216 rewrites `exp_output/MLB/cache/players_{season}.json` on demand), so no cron step or deletion is needed. Re-check at 2027 pre-season; re-open only if the generator no longer rewrites it.

**Current state (2026-10-08, W59.1):** Verified on VPS: players_2026.json exists only at exp_output/MLB/cache/players_2026.json, mtime 2026-06-24 (>3 months stale). **Next:** Add a refresh step to the cron or retire the file.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-415 |
| Category | Data |
| What was found | Player reference file used by the MLB feature path was not refreshed for the 2026 season end. |
| Source | SESSION_HANDOFF_20261002_2357 (47.2) |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-416 — Gate 2 / G7 passed on one family and by a floating-point margin on a 0.005 tick grid

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** archive_market_prices.py docstring (lines ~20-30) now bounds Gate 2 PASS 7/7 to KXMLBTOTAL only; no script enforcing the bound found (only board_survey_sports_gate2.py exists). Float-margin/tick-grid claim not re-run. **Next:** Add a check or assertion that rejects equivalence claims for series other than KXMLBTOTAL.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-416 |
| Category | Interpretation risk |
| What was found | Reading Gate 2 PASS 7/7 or G7 as broad price-equivalence overreaches; archive_market_prices.py docstring now bounds it but no check enforces the bound. |
| Source | 47.1 DECISION_LOG 'Q6 concerns' (3) |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-417 — Cowork strategic window sandbox can create but not delete files in the shared tree, leaving .git/index.lock behind

**Status:** OPEN · **Severity:** HIGH

**Current state (2026-10-08, W59.1):** 2026-10-08: git grep for no-optional-locks/index.lock in scripts/.claude/src finds no guard code; mitigation is operator convention only (Cowork window read-only git), no recurrence guard for other sandboxed windows. **Next:** Add a session_guard.sh check that flags a stale .git/index.lock (age>10min, no live git process) so a sandbox-left lock is surfaced at session start.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-417 |
| Category | Tooling |
| What was found | Root cause of the 3-day stale lock that blocked Wave 45 (see GG-349): the Cowork window's `git status` took an optional index lock and its sandbox could not remove it. Window now uses read-only git (--no-optional-locks). Recurrence guard for any other sandboxed window is not in place. |
| Source | Operator, 2026-10-03; GG-349 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-418 — VPS HEAD and branch SHAs recorded in handoffs drift between sessions

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** 2026-10-08: .claude/hooks/session_guard.sh checks local HEAD vs origin/main and the checkpoint SHA only; nothing re-verifies VPS HEAD or fly-branch SHAs quoted in a handoff. VPS HEAD now 417c9424. **Next:** Add a /session-start step that diffs handoff-quoted VPS/branch SHAs against `ssh ... git rev-parse HEAD` and warns on mismatch.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-418 |
| Category | Process |
| What was found | 48.1 found VPS HEAD f7959d6 where the 47.2 handoff said 1e097e0, and fly-branch tip be65872 where it said 574b85e. Handoff SHAs are not re-verified at session start. |
| Source | SESSION_HANDOFF_20261003_0020 (48.1) |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-421 — vps_job --rate-cap is recorded and cross-checked, not enforced by the runner

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** Verified from code: scripts/vps_job* check_command cross-checks only against the command's own --rate; --rate-cap is recorded but not enforced. **Next:** Enforce --rate-cap in check_command.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-421 |
| Category | Safeguard |
| What was found | A detached read-only VPS job can exceed its stated rate cap; the runner only cross-checks the cap against the command's own --rate. |
| Source | SESSION_HANDOFF_20261003_W48_2 |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-422 — Claim ranges that share an endpoint or overlap collide; 47.1 and 48.2 held overlapping GG ranges

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W59.1):** scripts/lib/check_id_collision.sh extracts only literal T-/GG-/ADR- tokens from the range string (grep -oE), so a range 'GG-340..GG-399' checks just its two endpoints; interior overlap is invisible and an in-use endpoint hard-refuses. Premise still true at worktree HEAD. **Next:** Expand A..B ranges to numeric intervals and compare interval overlap against SESSION_CLAIMS.md rows (reject true overlap, tolerate a shared endpoint explicitly).

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-422 |
| Category | Process control |
| What was found | T-615's GG-340..GG-399 and T-632's GG-357..GG-398 overlap, and claim_session.sh refuses any range containing an in-use endpoint (GG-357, GG-398), so 49.3 could not carry 48.2's range and claimed GG-400..GG-429. Related: GG-353, GG-162. |
| Source | SESSION_HANDOFF_20261003_W48_2; 49.3 claim refusal |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-423 — Live Terminal T1 freshness shows red at 58 days under a zero-Kelly book

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** scripts/web_dashboard.py _freshness() sets t1_mlb level red/amber purely from paper_portfolio_mlb.json age vs season thresholds, with no kelly_fraction==0 awareness. VPS file now logs/paper_portfolio_mlb.json mtime 2026-10-05 23:05 (~2d), so the 58d figure is stale but the operator question stands. **Next:** Operator decision; if staleness is irrelevant at zero Kelly, render the t1_mlb chip grey with 'zero-Kelly, sizing off' in _freshness()/paintFresh.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-423 |
| Category | UX |
| What was found | With kelly_fraction=0.0 no T1 sizing occurs, yet freshness renders red; ambiguous whether staleness matters for the operator. |
| Source | SESSION_HANDOFF_20261003_0020 (48.3) |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-425 — /project governance-gap Age column shows '—' when a block has no date; ADR titles render '— —'

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** scripts/generate_project_state.py:154 takes the first date regex match in the block as first_date, and the W59.1 'Current state (2026-10-08...)' stamp now makes it wrong (age ~0) instead of '—'; line 178 regex r'# (ADR-\d+)[:\s]+(.*)' leaves the leading '— ' of titles like 'ADR-0070 — Probit...', rendering '— —'. **Next:** Strip leading em-dash in ADR title regex and derive gap age from the Gap-ID/Source date or the Registered-by wave, not the first date in the block.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-425 |
| Category | UX |
| What was found | Gap entries without a dated field show no age; ADR title parsing leaves '— —' for several rows. |
| Source | SESSION_HANDOFF_20261003_0020 (48.3); 49.2 screenshot |
| Disposition | Registered by 49.3 (registration only, no investigation). |

</details>

### GG-1080 — Install gate waved W83.2's install through on a RED surface budget

**Status:** RESOLVED · **Severity:** HIGH

`passyds_install.py` / `nba_lineup_window_install.py` exempted any red reason containing the job name as a substring (e.g. `SILENT ARM nfl_passyds_snap`), and passed RED with an empty reasons list. Fixed: `thin_capture_install.gate()` exempts only the exact `STALE cron|…|<script>: no write found` reason; RED with no reasons blocks. Tests added in both install test files. Pattern sweep: no other substring-filter instance in scripts/, src/, .claude/, deploy/.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-1080 |
| Source | W85.3 (2026-10-22), PR #325 |

</details>

### GG-1081 — Three NBA preseason registry entries retired

**Status:** RESOLVED · **Severity:** LOW

`run_nba_player_points_shadow.py --preseason`, `remove_nba_preseason_cron.py --auto`, `run_nba_pregame_shadow.py --preseason` marked `status = retired` in RUNTIME_REGISTRY.toml (budget_read 2026-10-22T22:22Z: mirrored but not installed). Mirror lines in deploy/ left in place.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-1081 |
| Source | W85.3 (2026-10-22), PR #325 |

</details>

### GG-1082 — Exposure gate not yet on the order path; settled-ticker feed missing

**Status:** RESOLVED · **Severity:** HIGH

**Resolution (W89.1):** W89.1 2026-10-27 05:1xZ: PRs #342 (prereqs) + #346 (flip, merge bb03fd4), CI green on the merged head. Box HEAD 5efdf913 (contains it) shows GATE_MODE="enforce". Drill on the box against a temp state dir (live state untouched): missing state file -> `exposure_state_missing`; tripped book -> `exposure_gate_breach:MLB_T1,SYSTEM`; unmapped band -> `exposure_band_unmapped:None` (all REFUSED). Live state: MLB_T1 feeding, SHADOW advisory=True, breaches []. CAVEAT: no LOG-ONLY game day preceded the flip (operator directed it 2026-10-26; the time gate was waived), so the fix was prerequisite-driven (GG-1240, GG-1241), not would-halt-data-driven; 13 test files assuming log default were adjusted.

W85.3 built `c4_risk_engine/exposure_gate.py` (GG-441) and wired it into the T1 MLB drawdown input only. Not done: (a) `KalshiMarketClient.submit_order` calling `exposure_gate.check_before_order` (needs a state writer on every book first, else fail-closed bricks demo orders); (b) a feed of settled tickers so `settled_unresolved_stake` is nonzero in production (positions carry no settled flag today); (c) T4/NFL/NHL books do not call `update`. Next: writer per book, then order-path check.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-1082 |
| Source | W85.3 (2026-10-22), PR #325 |

</details>

### GG-441 — Kill switch is realized-loss-only and in-memory: with resolution dark, settled-but-unresolved stake is invisible to it (breach scenario corrected 2026-10-03: ~11-12%, not 26.6%)

**Status:** RESOLVED · **Severity:** HIGH

**Resolution (W89.1):** kill switch/exposure gate now enforcing on the order path. W89.1 2026-10-27 05:1xZ: PRs #342 (prereqs) + #346 (flip, merge bb03fd4), CI green on the merged head. Box HEAD 5efdf913 (contains it) shows GATE_MODE="enforce". Drill on the box against a temp state dir (live state untouched): missing state file -> `exposure_state_missing`; tripped book -> `exposure_gate_breach:MLB_T1,SYSTEM`; unmapped band -> `exposure_band_unmapped:None` (all REFUSED). Live state: MLB_T1 feeding, SHADOW advisory=True, breaches []. CAVEAT: no LOG-ONLY game day preceded the flip (operator directed it 2026-10-26; the time gate was waived), so the fix was prerequisite-driven (GG-1240, GG-1241), not would-halt-data-driven; 13 test files assuming log default were adjusted.

**Current state (2026-10-08, W59.1):** c7_monitoring/monitor.py l.34-35 alerts on realized loss only (5%/10% of initial bankroll); only stale-open detection (7-day threshold, l.122) touches unresolved stake. Unchanged in code. **Next:** Add settled-but-unresolved stake to the kill-switch drawdown input; persist state.

**Update (W55.1, 2026-10-05):** the 17 settled-but-unresolved T1 positions are now booked (live write, T1 realized drawdown 12.44%); the in-memory/realized-only kill-switch gap itself remains open.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-441 |
| Category | Risk-control blind spot |
| What was found | Kill switch input is `max(0,-total_realized_pnl)/initial` (`run_mlb_paper_trade.py:670-671`), recomputed from the file each run; no kill-switch state is persisted for T1 (only the T4 file flag `logs/t4_mlb_kill_switch.flag`, absent). Current: realized -106.0099 / 1000 = 10.60% (<20%), not tripped, last cron 2026-10-03 prints `Drawdown 10.6%`. Open stake is $160.243 on markets already finalized. **CORRECTION 2026-10-03 (W51.1 follow-up):** the original text here said a full loss of all 17 would put realized loss at 26.6% (> 20%). That scenario is not reachable: Kalshi's historical records show 16 of the 17 (stake $153.09) are *cancelled* markets (`expiration_value` 'Cancelled' or blank, result `scalar`, settled at 0.25-0.80), not losses; only Gunnar Henderson 1+ hits (stake $7.16, NO) settled `yes` as a real loss. Approximate realized after resolution (fees/vig ignored): ~11.3% if the 16 are voided, ~12.0% if marked to Kalshi's settlement value. Both are well under 20%; the breach is not reachable from these 17. See GG-450. The structural blind spot below (kill switch cannot see settled-unresolved stake, and reads a 58-day-stale number) is unchanged. |
| Why it matters | Under GG-440 the control reads a number that is 58 days stale by construction, and the metric excludes exactly the exposure that has already settled. Not a trip today and, per the correction above, not a latent trip from these 17 either; the blind spot would matter for a future book with real unresolved losses. Mitigant: Kelly is 0.0 (ADR-0048), so no new stake is added. |
| Source | W51.1 (2026-10-03); results: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W51_1_killswitch_truth_results.md` |
| Disposition | Registered only; no limit or definition changed (out of scope). Operator decision: whether settled-unresolved stake should count toward the kill-switch quantity. |

</details>

### GG-452 — DEPENDENCY_LOCKS requirements files disagree with pyproject.toml bounds; CI installs from the locks

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-08, W59.1):** Verified: requirements-base.txt pins scikit-learn==1.4.2, scipy==1.13.0; pyproject.toml requires scikit-learn>=1.8.0,<2.0 and scipy>=1.12.0,<1.13 (scipy lock violates the pyproject bound). **Next:** Regenerate locks from pyproject and run the test suite.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-452 |
| Category | Reproducibility |
| What was found | `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-base.txt` (dated 2026-05-22/23) pins scikit-learn==1.4.2 and scipy==1.13.0 while pyproject.toml requires scikit-learn>=1.8.0 and scipy<1.13. tests.yml and deploy.yml's approval gate install requirements-dev.txt then `pip install -e .`, so the effective CI environment is whatever resolves on top of a stale lock; the VPS venv's actual versions are not recorded in the repo. |
| Source | 50.1 GG-427 work (2026-10-03), recorded in SESSION_HANDOFF_20261003_0250.md |
| Disposition | Registered by Wave 52 CC (T-659), registration only. Next step: `pip freeze` on the VPS venv (terminal), then regenerate the locks from it. Model-affecting versions change only by ADR. |

</details>

### GG-453 — EXP-037 MLB postseason shadow arm has no cron: 12 MLB game-market cells never log, queue says armed

**Status:** PARTIALLY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-453 |
| Category | Operational / documentation-vs-reality |
| What was found | 2026-10-05 04:13 UTC read-only audit (W53.2): `crontab -l` EXP-037 block runs only `scripts/run_pregame_shadow.py` (NFL model) and the NFL settle. `scripts/run_mlb_pregame_shadow.py` exists on the VPS but is in no cron line. `exp_output/PREGAME_SHADOW/` holds 12 NFL ledgers and zero `MLB_*` files. `04_EXECUTION/ACTIVE_QUEUE.md` records "NFL + MLB postseason shadow: Armed" and "33 pre-game cells now log unattended" (12 NFL + 12 MLB + 9 NHL). Only 21 do. |
| Why it matters | MLB postseason pre-game markets are live now; every day unscheduled is permanent loss of T1/T2/T3 rows for EXP-037's MLB half. |
| Source | `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W53_2_shadow_audit_results.md` |
| Disposition | Registered only (read-only wave). Next step: operator authorizes an MLB cron block (terminal); correct the ACTIVE_QUEUE "Armed" line meanwhile. **2026-10-05 W54.2 update:** operator authorization already stands (2026-10-02 15:22 PT, new lines only), but arming is blocked by GG-470 (VPS cannot build/refresh the games cache) and GG-471 (helper rejects MLB lines). Still unarmed; no rows exist. |

**2026-10-05 W54.2 later update:** 7-line EXP-037 block now installed on the VPS (3 MLB lines added; crontab diff = 7 added lines, backup `/root/crontab.bak.20261005T072628Z`; NFL lines byte-identical). By hand: T2 and T3 exit 0, wrote nothing (no event inside their windows at 07:30 UTC); T1 `--refresh` failed closed twice on Stats API 406 (GG-470). **Zero MLB ledger rows exist, so this gap stays OPEN** (resolution criterion: MLB_* ledgers contain rows).


**2026-10-05 W55.3b update:** all three bands now have a working path: T1 wrote 69 rows by hand run (see GG-470); T2/T3 had written rows earlier the same day from the seed cache (last Final 2026-10-04). Same daily-sync dependency as GG-470 (GG-482). Not marked resolved until the sync runs unattended.
</details>


### GG-470 — MLB pregame shadow cannot run on the VPS: games cache absent and unbuildable/unrefreshable (statsapi 406 on range queries)

**Status:** PARTIALLY RESOLVED · **Severity:** HIGH

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-470 |
| Category | Operational / arming blocker (blocks GG-453) |
| What was found | 2026-10-05 W54.2. `scripts/run_mlb_pregame_shadow.py --dry-run` on the VPS exits `exp_output/MLB_GAME/cache_w47/games.parquet missing`. The cache is gitignored (`*.parquet`) and exists neither on the VPS nor in the operator checkout. `scripts/fetch_mlb_game_history.py` builds it from `statsapi.mlb.com/api/v1/schedule?startDate=..&endDate=..`; from the VPS that range query returns HTTP 406 for any range, any season (2024 and 2026 tested; python requests and curl). Single-date queries (`?date=YYYY-MM-DD`) return 200 from the VPS; the same range query returns 200 locally. The runner's `--refresh` calls the same fetcher and aborts ("refusing to run on stale data"), so an MLB cron with `--refresh` writes zero rows, and one without it would log rows from a frozen cache with stale results and probable starters. |
| Why it matters | Arming the 12 MLB cells now would either log nothing or pollute the EXP-037 MLB ledgers with stale-feature rows. W54.2 therefore did NOT install the MLB cron lines. |
| Source | W54.2 VPS read-only tests; `W54_2_gg432_mlb_arm_results.md` |
| Disposition | **PARTIAL 2026-10-05 (W54.2):** seed `games.parquet` (28,122 rows, 2015-2026, sha256 d6dc0adf...) built locally, copied to the VPS, loads; per-date refresh path (`fetch_day`/`refresh_recent`, retry+backoff, fail-closed, window starts at last Final game) merged in PRs #162/#163, values verified identical to the range path on 7 spot-check dates. **NOT solved:** the VPS edge answers 406 *intermittently and per-IP*, not per date or per range: the same date flipped 200->406 within minutes, `gameType=` and multi-day ranges 406 more often, and by-hand `--refresh --bands T1` failed closed twice (406 for 2026-09-30, then 2026-10-03, 4 retries each, ~2.5 min). Fail-closed means no stale rows are written, but T1 MLB will log nothing until a refresh gets through. Open options for the operator: (1) let the 6-hourly T1 cron prove or disprove reliability over a few days; (2) refresh `games_current.parquet` from a machine that is not throttled (local) and sync it to the VPS before each T1 window; (3) a non-DigitalOcean egress/proxy for statsapi.mlb.com. My own probing may have worsened the throttle; the sample is not clean. |


**2026-10-05 W55.3b update:** ESPN ruled out as a source (scoreboard lacks MLBAM starter ids; ESPN athlete ids are a different namespace, no MLBAM crosswalk field). Option 1 landed (PR #164, bf1afb0): `scripts/sync_mlb_games_cache.sh` refreshes `games_current.parquet` on the Mac (Stats API 200 there) and scp+atomic-mv's it with a `.meta.json` stamp to the VPS; the runner without `--refresh` now fails closed on a missing or >26h-old stamp; VPS T1 cron no longer passes `--refresh` (backup `/root/crontab.bak.W55_3b.20261005T225931Z`). Manual T1 run: 69 rows written (ML 8, RL 12, TOTAL 21, TEAM_TOTAL 28). **Remaining:** sustained operation needs the sync run at least daily from a machine that is on; nothing schedules it (GG-482). If it lapses, all MLB shadow cells write nothing (fail-closed, not stale).
</details>

### GG-514 — NHL judged n=2,500 unreachable this season; NFL first-look date rests on one week of coverage

**Status:** ACCEPTED UNCERTAINTY · **Severity:** MEDIUM

**Operator decision (2026-10-07 19:03 PT, recorded 2026-10-08 W60.2 Part B):** keep EXP-036 as written (judged n 2,473; NHL stays PRELIMINARY in 2026-27; the 500-game climatology check still applies). The NFL first-look date (2026-11-02, one slate of coverage) remains a projection to re-derive as weeks accumulate.

**Current state (2026-10-08, W59.2):** Projection (W59.2): NHL needs 2,470-2,484 more games, expects 573-968 from 1,290 left, so n=2,500 is not reachable on the published schedule; NHL can only stay PRELIMINARY in 2026-27. NFL date 2026-11-02 uses coverage measured on 15 games (one slate). **Next:** Operator to decide whether EXP-036's n=2,500 stands (a multi-season horizon) or is revised by a superseding document; re-derive NFL date after more weeks.

<details>

| Field | Detail |
|---|---|
| Gap ID | GG-514 |
| Category | Calibration engine / pre-registration |
| What was found | Projection (W59.2): NHL needs 2,470-2,484 more games, expects 573-968 from 1,290 left, so n=2,500 is not reachable on the published schedule; NHL can only stay PRELIMINARY in 2026-27. NFL date 2026-11-02 uses coverage measured on 15 games (one slate). |
| Why it matters | NHL may never reach a verdict on the registered threshold; an early NFL date could slip by a slate or more. |
| Source | W59.2 (`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W59_2_calibration_correctness_results.md`) |
| Resolution | Not fixed in-session (register-and-stop). Pre-registrations are not edited; a superseding document is needed. |

</details>

### GG-538 — The only pre-2026 Kalshi price history lived in one untracked agent worktree (single copy, no manifest)

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-09, W62.2):** MITIGATED, awaiting the operator's acceptance to close: `raw/` + rebuilt `candles/`/`markets/` copied to the VPS with sha256 verified; manifest at `12_EXPLORATORY/KALSHI_HISTORY_MANIFEST.md`. **Next:** operator decides whether to refresh the tracked `exp_output/KALSHI_HISTORY/{markets,VALIDATION.json}` (still the stale 862/415 build) and whether a scheduled VPS copy of `raw/` is wanted.

<details>
<summary>Full record ▸</summary>

Found W61.3: `candles/` and `raw/` existed only in `.claude/worktrees/agent-a622a0ccc3aead20c/` (untracked, not in git, not on the VPS); the tracked README claimed STATUS PARTIAL / fetch killed. Pre-2026 prices cannot be re-fetched on demand at a known cost, and they are the only price series that predates the NFL pre-registration. W62.2 completed the KXNFLGAME fetch (892/892), rebuilt derived files from `raw/` in a scratch store, and made the VPS copy. (GG-533 was reserved by W61.3 but never registered; this gap takes GG-538.)

</details>

### GG-529 — EXP-038 second-look date trigger ('or 2027-01-31, whichever first') is undefined

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-08, W60.2):** EXP-038 says the second look is at judged n=400 or 2027-01-31, whichever is first, but defines neither the games scored nor the n at the date, and sec. 1 'judged on whatever n they reach' conflicts with sec. 4 (no scoring before judged n). The engine releases only n=150 and n=400, lists the item in each NBA cell's `undefined_rules`, and emits no verdict for it. **Next:** Operator/DS to define the date-triggered look by superseding document before 2027-01-31.

<details>

| Field | Detail |
|---|---|
| Gap ID | GG-529 |
| Category | Calibration engine / pre-registration |
| What was found | See current state. |
| Source | W60.2 Part A (`W60_2_nba_engine_addenda_results.md`) |
| Resolution | Not fixed in-session (register-and-stop). |

</details>

### GG-536 — T1 MLB paper book: 17.5% of closed positions were filled on demo; the 83 settled fills lose $1.50/bet while the unfilled remainder is flat

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-09, W62.3):** T1 MLB (`paper_portfolio_mlb.json`) submits real demo orders like T4. Of 485 closed positions, 85 CONFIRMED_FILLED, 400 CONFIRMED_NOT_FILLED (346 no match inside the fills horizon, 54 never accepted), 0 UNVERIFIABLE. Settled: all 469 rows -$113.17 (-$0.241/bet, game-clustered 95% CI -1.365..+0.915); fills n=83 -$124.73 (-$1.503/bet, CI -3.666..+0.631, 28.9% win); non-fills n=386 +$11.56 (+$0.030/bet, 52.1% win). The ledger's 12.44% paper drawdown is therefore mostly a calibration figure. **Next (operator's call, nothing changed):** whether T1 counting/G6/dashboards should use fills only as T4M-PROJ now does (GG-527 decision covered T4M-PROJ only). Sidecar `logs/t1_mlb_fill_status.jsonl` (own book, append-only) is the evidence.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-536 |
| Category | Ledger integrity / sample adequacy |
| What was found | Same mechanism as GG-527: a position is recorded `submitted` and settled by market outcome whether or not the venue filled the order. For T1 MLB 82.5% of closed positions never filled. |
| Why it matters | Any T1 MLB claim (win rate, P&L, drawdown, calibration-as-edge) rests mostly on unexecuted orders; the executed part lost money and is not interchangeable with the rest. |
| Source | W62.3 Part A (`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W62_3_gate_t1_fills_nba_results.md`) |
| Resolution | Not resolved: no counting, status or ledger change for T1 (operator decision). Classifier generalized (`--book t1_mlb`). |
| Cross-references | GG-527, GG-300, GG-004, GG-071 |

</details>

### GG-562 — Archived NFL game-market paper book holds 4 OPEN positions entered by StubNFLForecastModel (not a trained model); two are past their game date and unresolved

**Status:** OPEN · **Severity:** LOW

**Current state (2026-10-10, W65.3 step 0, read-only):** `logs/paper_portfolio_t1_nfl_game_market.json` on the VPS (file last written 2026-10-07 01:56 UTC) has 4 positions, all `OPEN`, `size_usd` 1.0, `kalshi_order_status` `local_only`, entered 2026-09-29 05:36:39Z, `forecast_id` prefix `T1-NFLGM-PT-`. These are real ledger rows. They are what the Live Terminal showed as "STUB, model P 0.0000": `run_t1_nfl_game_market.py` carries `StubNFLForecastModel` with `PROVENANCE = "STUB (... NOT a trained model, GG-255)"`, and `logic_epoch.py` classifies that text as `EVIDENCE_STUB`. Game dates seen: 2026-10-08 (TB/DAL, past, still OPEN) and 2026-10-11 (CIN/MIA). Nothing was changed.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-562 |
| Category | Ledger integrity / provenance |
| What was found | The archived NFL book contains open positions whose probability came from a stub, so they carry no model information. At least one is past its game date and still unresolved, so the book is not being settled while archived. |
| Why it matters | Low dollar impact ($1 each, local_only), but any dashboard figure that counts open NFL positions shows stub-sourced exposure as if modelled. Not evidence for any NFL claim; the real NFL evidence is the EXP-037 shadow ledger. |
| Disposition | Registered only (Hard Rule 11; W65.3 step 0 said do not fix). Operator decision needed: leave archived and filter STUB from the Live Terminal, or resolve and close the 4 rows. |
| Source | W65.3 step 0 (VPS read of `logs/paper_portfolio_t1_nfl_game_market.json`) |
| Resolution | Not resolved. |
| Cross-references | GG-255, GG-291 |

</details>

### GG-564 — Kalshi demo lists only a subset of production markets; the bot sends orders for tickers demo does not carry, so they can never be accepted

**Status:** OPEN · **Severity:** MEDIUM

**Current state (2026-10-11, W66.2):** On 2026-10-10 t4-mlb attempted 40 distinct KXMLBHIT tickers for CWS@CLE: 17 accepted orders (demo-listed players), 23 tickers 404 not_found (762 events), because demo carried 18 of production's 55 tickers for that game. Demo-fill statistics (E1, ADR-0072 arms) therefore describe only the demo-listed subset, and the failed attempts inflate `kalshi_order_failed` counts. **Next:** decide whether to (a) pre-check demo listing before ordering (changes order behavior - operator/ADR) or (b) just stratify E1 by demo-listed vs not. Not changed in W66.2.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-564 |
| Category | Measurement validity - E1 denominator includes orders that cannot be placed |
| Evidence | audit_mlb_t4.jsonl 2026-10-11: paper_order_opened with kalshi_order_id x17 vs kalshi_order_failed not_found x762 over 23 tickers; demo vs prod event listing 18 vs 55; GET demo/markets/<ticker> 404 vs prod 200 |
| Source | W66.2 Part A |
| Resolution | Not resolved. |
| Cross-references | GG-560, GG-203, ADR-0072 |

</details>

### GG-560 — Kalshi DEMO order writes return HTTP 404 not_found for every order (bot and canary alike) as of 2026-10-11; W65.2 cancel path untestable, forward test cannot start

**Status:** PARTIALLY RESOLVED · **Severity:** MEDIUM

**Current state (2026-10-11, W66.2 Part A):** ROOT CAUSE FOUND - not an endpoint outage. The demo host lists only a SUBSET of production markets (CWS@CLE 10-10: 18 demo vs 55 production tickers; identical on both documented demo hosts); orders on a ticker absent from demo return 404 not_found. t4-mlb had 17 orders accepted that same game/window. 65.2's canary picked tickers from PRODUCTION, so 12/12 404'd. Canary fixed to select from the demo listing and PASSED on the VPS (placed, cancelled, GET status canceled, order 01a1299b-19e8-7715-8795-09ae94337432). Remaining: fixed canary merged+deployed (PR in flight). Evidence: W65_2_forward_test_on_results.md.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-560 |
| Category | Execution-path dependency — the W65.2 stop rule (cancel must be proven before ON) cannot be satisfied because order placement itself fails. |
| Evidence | Canary run 4 (VPS HEAD cd0f4b62, 2026-10-11T03:2xZ): 12 candidates, all 404. Earlier runs 1-3 failed on market selection (fixed in PRs #212/#214/#215/#216). Audit: KXMLBHIT-26OCT1020 failed 325/283/154 per hour, opened 0 on Kalshi. |
| Disposition | Registered; switches OFF; no order was accepted, so no cancel was attempted. |
| Source | W65.2 Part A step 1 |
| Resolution | Not resolved. |
| Cross-references | GG-203, GG-536, ADR-0072 |

</details>

### GG-570 — NBA shadow pregame cron lines are pinned credential-free (EXP-038), so SHADOW_FLAT_STAKE cannot reach NBA shadow cells without an operator decision

**Status:** OPEN · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Read-back 2026-10-26 on the box: NBA pregame shadow files exist (15 cells, 416-7904 rows each) but `grep -c shadow_order` is 0 in every one, so the 10-21 read-back this entry waited on has NOT shown NBA shadow_order rows. Premise (W68.2 demo staking on the NBA lines) is not borne out by the rows. Stays OPEN; needs a separate look at why make_on_row does not stage NBA orders.

**W73.1 2026-10-15T00:20Z:** premise stale. Since W68.2 (#228) the NBA game and player-points T1-T3 cron lines already load `deploy/demo_fill.env` with `BOT_ENV=paper` and stake demo-only through `make_on_row` (box crontab read over ssh); the guard test was changed to a demo-only guard. A second runner would double-place the same rows, so none was built (see DECISION_LOG W73.1). Stays OPEN until the 10-21 read-back shows NBA shadow_order rows.

**Current state (2026-10-11, W67.2):** W67.2 wired `deploy/demo_fill.env` into the NFL and MLB shadow pregame cron lines only. The NBA lines (`run_nba_pregame_shadow.py --bands T1/T2/T3`) were left unchanged because `tests/test_nba_shadow_safety.py::test_cron_block_markers_and_scripts_only_nba` asserts they carry no `.env` and no kelly (the EXP-038 NBA shadow is deliberately credential-free). Loading demo_fill.env there would give those jobs order-placing credentials. NBA is also DARK/FROZEN per the standing directive, regular season starts ~2026-10-21. Operator decision needed: keep NBA shadow credential-free (no flat stakes on NBA shadow cells) or amend that guard by ADR/test change.

<details>
<summary>Full record ▸</summary>

| Field | Detail |
|---|---|
| Gap ID | GG-570 |
| Category | Coverage - shadow-cell stakes (E1/E2/E3 breadth) absent for NBA by design guard |
| Evidence | Full-suite run on the first W67.2 attempt: 1 failed (test_nba_shadow_safety), caused by adding `.env` export to NBA lines; reverted. |
| Disposition | Registered; NBA lines unchanged; operator decision. |
| Source | W67.2 Part B step 4 |
| Resolution | Not resolved. |
| Cross-references | GG-564, ADR-0072, EXP-038 |

</details>

### GG-587 — Forward-report turn-off edits tracked deploy/demo_fill.env on the VPS and would trip vps_deploy.sh's dirty-tree guard

**Status:** OPEN · **Severity:** MEDIUM

`scripts/demo_fill_forward_report.py` comments out the switches in `deploy/demo_fill.env` when an ADR-0072 condition trips. On the VPS that is a tracked-file edit, which `vps_deploy.sh` `heal_dirty_tree` aborts on (or reverts, re-arming the switches). Fix: commit the turn-off to main, or move the switch to an untracked override file. Also: 30-min markout and non-demo-host conditions are not evaluable by the job. Found by T-822 (W68.2).

### GG-596 — Forward-report cancel_fail_rate counts HTTP 404 (order already terminal) as a cancel failure, so the ADR-0072 turn-off can trip on a healthy cancel path

**Status:** OPEN · **Severity:** MEDIUM

First on-box forward report (W69.1, 2026-10-13T00:09Z) tripped `cancel_fail_rate_gt_10pct_in_a_day` at rate 1.0. Cells: MLB treatment 0 ok / 380 failed; NFL 906 ok / 229 failed (79.8% ok). The logged failures are `HTTP 404 not_found` on the cancel call (`unfilled_after_N` 17, `sweep_overdue` 383): the order was already terminal (filled/expired) when the cancel arrived, so cancel never had anything to cancel. NFL shows the cancel path works on resting orders. The metric conflates "already terminal" with "cancel API failed". Fix: classify 404 as `already_terminal`, exclude it from the failure rate, report it separately. Not fixed in W69.1 (Hard Rule 11). Until fixed the turn-off can re-trip on every report run. Found by W69.1.

### GG-610 — EXP-040 injury-report history has no coverage for Jan–Apr 2026

**Status:** OPEN · **Severity:** MEDIUM

W69.3 (2026-10-12) found no official NBA injury-report PDFs retrievable for Jan–Apr 2026, so fold-B test coverage of the `minutes_inj` arm is ~34% and the rest is scored with `inj_missing=1`. The EXP-040 result is therefore a lower bound on the injury feature's value and its test fold is partly a `minutes_box` evaluation. Not fixed in-session (Rule 11). Remedy: locate an alternate archive for the gap window, or accept and state the coverage in any EXP-040 verdict.

### GG-611 — EXP-040 live shadow logging not wired or deployed

**Status:** OPEN · **Severity:** HIGH

The EXP-040 artifact is frozen (sha256 `c47cbac7…8527`) and `NBAPlayerPointsMinutesModel` exists, but no forecaster, runner, registry cell, runtime injury-report fetch, or VPS deploy exists. Until a shadow row carrying the sha is logged before its game, no row counts toward the pre-registration. Deferred because it touches the EXP-039 runner that W69.2 is working on for NBA opening night and requires a VPS deploy outside this session's permissions. Needs its own claim and an operator deploy step.

### GG-588 — KXNBATEAMTOTAL has never listed and the archive cannot date last season's KXNBAPTS listing, so 3 NBA_TEAM_TOTAL cells (and possibly the 10-20 player-points cells) may stay at zero rows

**Status:** OPEN · **Severity:** LOW

W69.2 Part A (2026-10-12): the Kalshi series list shows KXNBAGAME/SPREAD/TOTAL, but KXNBATEAMTOTAL has never listed in any archive. This season's preseason KXNBAPTS markets existed only 10-05 to 10-09 and are closed; the price archive holds no last-season KXNBAPTS data, so it cannot say when they listed. Runners handle an empty board without error, and NBA_TEAM_TOTAL cells only flip on a valid row (nba_cell_autoflip), so nothing is claimed that the data does not support. Action: read the 10-20/10-21 ledgers; if TEAM_TOTAL is still empty after ~2 weeks, mark those cells with a measured-date ruling via ADR rather than leave them NOT_IMPLEMENTED indefinitely.

### GG-630 — Post-Game Resolve (NBA T1/T4 auto-resolve) is paused; nothing proves the VPS can resolve the old NBA book when NBA reopens 2026-10-20

**Status:** OPEN · **Severity:** MEDIUM

W70.3 (T-860) investigated the "dark ~75 days" workflows. Not an accident: T-399 (2026-07-29) deliberately commented out the `schedule:` of `post_game_resolve.yml` and `tss_daily_sync.yml` because the old NBA book was dark; last scheduled success 2026-07-28. State read 2026-10-12: VPS crons for the old NBA pipeline are LIVE (`run_pregame.py` 17:55/01:25, `run_paper_trade.py` 18:00/01:30 `PAPER_YES_ONLY`, `run_resolve.py` 06:00). `paper_early_cron.log` = "No KXNBAPTS markets available"; `resolve_cron.log` = 0 open positions. Nothing is stuck today. Risk: when KXNBAPTS markets return (2026-10-20) `run_paper_trade.py` can open positions in the old NBA paper book, and resolving them was moved to GitHub Actions in June 2026 (Session 44) because `nba_api` was 403-blocked from the VPS (GG-013). Unverified: whether the VPS `run_resolve.py` can still resolve (the T-140 `build_tss_cache.py` runs fine on the VPS daily, so the block may be gone, but resolve uses other endpoints). If it cannot, positions sit open and NBA book drawdown reads go stale. Touches the old NBA paper book only (frozen per ADR-0035/37), not MLB. Not fixed here. Before 2026-10-20: (a) confirm VPS `run_resolve.py` can reach its data endpoint, or (b) uncomment the `schedule:` in `post_game_resolve.yml`, or (c) confirm the old NBA `run_paper_trade.py` crons are meant to stay on. The 2026-27 NBA arm (EXP-038) is shadow-only and does not depend on this.

### GG-620 — GG-610's "34% injury coverage" was a URL rename (2025-12-22), not missing data

**Status:** OPEN · **Severity:** MEDIUM

W70.2 (T-850), 2026-10-13. The NBA injury-report PDFs were renamed on 2025-12-22 (`..._{HH}_{MM}{AM|PM}.pdf`, 15-min grid); the old name 403s after that date. PR #241 fixes the live fetch (`url_for`) only. The EXP-040 study's coverage figure and code are untouched, so the injury-increment test is still run on 34% coverage. Next: re-fetch Jan-Apr 2026 with the new names and re-run the single pre-specified contrast over `minutes_box` (W69.3 "Next mechanism"). Preseason has no published reports (403), so preseason rows carry `inj_missing=1`.

### GG-621 — VPS lacked 2025-26 NBA player box scores; EXP-039/EXP-040 would have logged nothing

**Status:** OPEN · **Severity:** LOW

W70.2 (T-850), 2026-10-13. `data/raw/nba/players_2026.json` was missing on the VPS; backfilled by hand (1231 box scores, `logs/nba_player_points_backfill_2026_w70.log`). The daily cron (`nba_player_box_backfill.py --seasons 2027`) never refreshes 2026, and the 2027 store is empty until games are played, so early-season rows depend on that static file. Not yet in deploy or any checklist; if the VPS is rebuilt the arm goes silent again.

### GG-624 — NFL shadow fills' settle-minus-price (+0.39) rests on ~4 correlated games; must not be cited as E2

**Status:** WATCH ITEM · **Severity:** LOW

Re-filed 2026-10-21 under the operator's observation rule. Reopens if: NFL shadow fills span enough independent games to report E2 with game-clustered CIs.

W70.1 (T-853) audit: 0 of 231 fills after kickoff, so no timing artifact. But all fills are YES-side taker crosses on ladder rungs of totals/spreads that resolve together; first-fill-per-position +0.394 on 58 settled positions across 4 settled games (BUFLAR pending). Report E2 for NFL only with game-clustered CIs.

### GG-670 — No log rotation or disk alarm on the VPS (logs 1.9G, exp_output 2.6G, journal 1.1G; disk 51%)

**Status:** OPEN · **Severity:** MEDIUM

W71.H1 L4. audit_mlb_t4.jsonl 700MB, edge_decisions 259MB, cycle_log 228MB, 8518 files in logs/; no app logrotate entry. Fix: logrotate copytruncate for *_cron.log, monthly archive for audit jsonl, 80% disk alarm; never rotate ledgers without epoch-aware tooling. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-671 — Local-time `date.today()` used where UTC is documented (correct only because the VPS is UTC)

**Status:** OPEN · **Severity:** MEDIUM

W71.H1 L2. run_t4_mlb_live.py:1921,1969 (comment says UTC), 531, 570, 2051; paper_trader.py:150 `_today()`; run_resolve_mlb.py:592; run_t4_live.py:102/486/831; market_type_registry.py:1080 naive `datetime.utcnow()`. VPS `date` = UTC. Any Mac run or TZ change mis-keys game_date and the daily-loss reset. game_date meaning also differs by sport (UTC date MLB T4, ET NBA, gameday NFL); related GG-170. Fix: one `utc_today()` helper, tz-aware halted_at. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-673 — Kalshi fee formula hand-inlined at 7+ src sites and ~12 scripts copies

**Status:** OPEN · **Severity:** MEDIUM

W71.H1 L5. `0.07*mid*(1-mid)` in run_mlb_paper_trade.py:915, run_paper_trade.py:589, run_t2_mlb_sameday.py:450, run_mlb_pregame.py:434, run_pregame.py:369, run_t4_mlb_live.py:1459, run_t4_live.py:666; separate pregame_shadow/fees.py:13-17. Realised cost: GG-119/122 fee-sign bugs. Pillar EXECUTION/PROOF (E2, net edge). Fix: one `c5_execution/fees.py` plus a parity test. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-674 — Sport defaults and registry dependence: venue layer defaults to NBA, C7 drift baselines NBA/MLB only, NBA registry cells flip from a mutable data file at import

**Status:** OPEN · **Severity:** MEDIUM

W71.H1 L5. venue_adapter.py:105,173,375,510 and venue_router.py:132 `sport='NBA'` default, Polymarket tag hardcoded 'nba'; monitor.py:17-18,80-83 default NBA Brier/ECE baselines for NFL/NHL; market_type_registry.py ~957-980 reads exp_output/PREGAME_SHADOW/nba_promotions.jsonl at import (non-hermetic; B1 undercounts until flip on 2026-10-20); c3_forecasting/nhl_pregame.py:43 imports pregame_shadow.contract (layering inverted). Fix: required sport, baselines keyed (sport, band), explicit dated promotion, move contract to c3. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-675 — demo_fill_policy swallows audit-row write errors and never retries a failed cancel

**Status:** OPEN · **Severity:** MEDIUM

W71.H1 L1. demo_fill_policy.py append_log `except OSError: pass` drops E1/E3 evidence rows silently; CANCEL_DONE_EVENTS includes cancel_failed so a failed cancel is not retried and the order may rest (GG-623 covers the 404 cause, not this design). kalshi_client.py:897-915 pagination returns a partial board as ok=True on a mid-page failure. Fix: stderr log plus counter alarm; bounded cancel retry; return ok=False on partial. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-676 — deploy/cron.conf mirror drifts from the live crontab (run_mlb_pregame 22:45 live vs 18:45 mirror); crontab is installed by hand

**Status:** OPEN · **Severity:** LOW

W71.H1 L6. 69/70 lines match. Nothing applies the mirror, so drift is silent. Fix: cron-diff in governance_scan; correct the mirror. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-677 — Hygiene/CI findings: /hygiene command stale, ruff F-class and swallow sites, unpinned deps, root-run services, legacy NBA run_t4_live cron outside restart policy

**Status:** OPEN · **Severity:** LOW

W71.H1 A+L4. /hygiene expects FeatureStore.FEATURE_VERSION (absent), baseline 329 tests, 5 bands (22 defined), models/prod_model.joblib (gitignored). requirements-base.txt unpinned (`nba_api>=1.5.0`) so pip-audit cannot run on it. Services run as root (t4-mlb no hardening); ufw inactive. Dead t4-mlb.timer. Legacy run_t4_live.py cron (BOT_C4_ACTIVE=true) outside the restart policy; verify GG-630 freeze. Swallow sites: scripts/nhl_shadow_eval.py:166, distance_to_optimum.py:47 (verdict/measure scripts), run_mlb_dashboard.py:199 (only bare except). Full list in report. Evidence and context: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/HYGIENE_AUDIT_20261013.md`.

### GG-690 — 3,495 MLB ledger records carry no market_type, so cell-scoped invariants (G, K, I2, J2) report NO_FORMULA for them

**Status:** OPEN · **Severity:** MEDIUM

W72.3 Part B. `assert_ledger_invariants.py` on read-only VPS copies (2026-10-14): `paper_portfolio_mlb` (485 closed) has market_type None on all 485; `paper_portfolio_mlb_t4` has None on 2,994 of 4,297 (1,311 tagged `mlb_player_prop_hits`). Invariants group these under UNKNOWN_MARKET_TYPE and evaluate 0 of 4 cell assertions, so the fee/edge formulas were never checked on 3,495 rows. Likely legacy rows from before the registry; unconfirmed. Register-only: no backfill (live-ledger rewrite is out of scope). Fix options for a later block: a read-only derivation from ticker prefix (KXMLBHIT) inside the invariants script, not a ledger edit.

### GG-680 — Remaining non-atomic state/cache writers in src/ and scripts/ (W72.2 follow-up audit)

**Status:** PARTIALLY RESOLVED · **Severity:** MEDIUM

W72.2 follow-up audit (2026-10-13) of `write_text` / `open("w")` / `json.dump` on durable state read back later. CONVERTED to `prediction_market_bot.atomic_io` (tests: `tests/test_atomic_state_writers.py`): `reset_paper_portfolio.py:78` (portfolio reset, state); `c1_signal_ingestion/validators.py:397` (`_save_row_count`, contract row-count state); `nba_ingest.py:125` and `nba_player_ingest.py:90` (raw stores, previously tmp+replace without fsync); `nhl_ingest.py:215,234` (boxscore + schedule raw store; a torn file made `load_games` raise on every later run); `nba_injury_reports.py:97` (cache, torn file raises on next `json.loads`); `run_pregame.py:311` (TEAM_STATS_CACHE read by PIPE-03); `pregame_shadow/calibration_engine.py:484` (`persist_release`, write-once look manifest: a torn file would be skipped by the reader yet block rewrite via `if p.exists()`).

LEFT OPEN (not converted, by design or risk):
- READ-SIDE policy: `validators._load_state` returns `{}` on JSONDecodeError/OSError (silent reset of row-count baseline); `nba/nhl` raw-store loaders raise on a torn file (now only reachable from pre-fix files). Quarantine+halt not applied: needs an owner decision on whether these gate trading. `calibration_engine` reader skips ValueError manifests (now unreachable from new writes).
- Frozen/one-shot artifacts: `train_and_save_model.py:200` META_PATH, `scripts/train_*`, `freeze_nfl_qb_challenger.py`, `nhl_train.py`, `nfl_ingestion.py:550` capture manifest (timestamped, write-once, not gating).
- Script caches (offline, re-derivable): `scripts/generate_mlb_features.py:216,404`, `scripts/run_t367_ab_window_repull.py:122`, `scripts/build_tss_cache.py:116`.
- Risky one-off live-ledger rewrites, not touched: `scripts/t477_dryrun_epoch12_repair.py:189`, `scripts/t437_task3_rederive_outcomes.py:224`, `scripts/correct_t4_game_dates.py:133`.
- Not state: `tag_locked_pairs_t4_mlb.py:117` (writes a `.tagged.json` copy), `replay_harness_t427.py:210` (tmpdir), `c5_execution/paper_trader.py:319` (lock file), `run_t4_mlb_live.py:394` (log handle), `analytics/clean_dataset.py:241` (CSV output), report writers in `run_exp0xx.py`, `run_t2_*`, `run_t3_*`, `run_*_paper_trade.py`, `run_sensitivity_tests.py`.
Pillar: PLUMBING. Closes when the read-side policy for validators/raw stores is decided.

### GG-800 — No free field holds pre-snap motion DIRECTION or boundary side (F6 granularity gap)

**Status:** OPEN · **Severity:** MEDIUM

W75.2 Part A. Checked every free nflverse field for the 2022-2025 plays: FTN carries `is_motion` (boolean) and `starting_hash` (L/R/M/0 -- the ball's hash, not the motion man's direction), `n_offense_backfield`, `qb_location`; participation carries `offense_positions`, `route`, `offense_formation` with no alignment coordinates or motion path; pbp carries nothing pre-snap. None says which way the motion went or whether it ended at the boundary. The operator's "motioned to the boundary" cannot be answered; the factor is built on motion yes/no and a direction is never inferred. Likely paid-only (charting vendors / tracking data). Pillar: DEPTH. Closes when a free source with motion direction is found, or the paid-only status is confirmed and the cell is recorded as not buildable.

### GG-801 — Coverage shell is known on only 55-61% of scrimmage plays, and motion on none before 2022

**Status:** OPEN · **Severity:** LOW

W75.2 Part A. `defense_coverage_type` is populated for 53-61% of run+pass plays in every season 2018-2025 (the rest are runs and non-dropbacks); FTN `is_motion` exists 2022+ only (99.7-100% fill there). Any shell x motion cell therefore has at most four seasons of history, and 2026 has no participation file (GAP-1/GG-730). Cell-level EPA (unit x shell x personnel x motion) is at single-season n a noise measurement (Part A YoY r about 0.0-0.1), so the buildable signal is the shell MIX, not team-specific cell success. Pillar: DEPTH. Closes when a longer motion history or in-season 2026 participation exists.

### GG-850 — W76.3 pattern-sweep remainder: unclassified write sites in src/ and scripts/ (follow-up to GG-748)

**Status:** OPEN · **Severity:** LOW

W76.3 Part A (2026-10-16) swept src/ and scripts/ for `open(...,"w")` / `write_text` (174 hits, raw list not committed). The five live-ledger or portfolio writers (the four GG-748 scripts + `t437_task3_rederive_outcomes.py`) are converted to `atomic_io` (PR #265, tests `tests/test_w76_3_script_writers.py`, which also pins them against regression). The remaining hits overlap the GG-680 inventory (frozen artifacts, caches, report writers, tmpdir files) and were NOT re-classified one by one in this block. Closes when a re-run of the sweep is diffed against GG-680 and each unlisted hit is converted or listed as not-state. Also noted: `t4_fill_status.py:310` is an append-mode log (O_APPEND, not a rewrite). `backfill_*` scripts use tmp+replace without fsync (crash-durability only, not tear risk). Pillar: PLUMBING.

### GG-842 — t4-mlb armed message names only the legacy flag path

**Status:** WATCH ITEM · **Severity:** LOW

**W89.6 2026-10-26 (operator-approved disposition):** Operator disposition: bundle into the next planned t4-mlb restart; no restart for a cosmetic message. Fix `run_t4_mlb_live.py` (~l.2051) to name the one-switch set, with a test, at that time.

W76.1, 2026-10-16. `T4-MLB kill switch armed` prints `t4_mlb_kill_switch.flag` although any flag in the one-switch set halts it. Cosmetic; found in the drill.

### GG-885 — W77.3 pattern-sweep remainder: archive/diagnostic readers that silently skip unparseable lines (GG-764 follow-up)

**Status:** OPEN · **Severity:** LOW

W77.3 sweep (2026-10-16, heuristic grep of json.load(s) inside try/except that continues/passes, 19 hits). Fixed in W77.3: `scripts/nba_cell_autoflip.py` (reads cell ledgers; torn row shrank the n deciding a flip). Already safe: `build_t4_resolved_ledger.py` (returns reason), `t4_fill_status.py` (logs warning). Remaining silent skips, none read a live ledger: `capture_settlements.py:108`, `kalshi_settlement_crosscheck.py:17`, `gg157_fill_haircut_analysis.py:54`, `t507_gg157_haircut_rerun.py:40` (price/depth archives; torn line = quietly smaller sample in a one-off analysis), `run_t4_budget_sim.py:92,197,279` (falls back to DEFAULT_BANKROLL on any error), plus dashboard/aggregator readers (`cron_log_aggregator.py`, `live_terminal.py`, `run_mlb_dashboard.py`, `project_ops.py`) not classified. Heuristic, not exhaustive. Pillar: PROOF. Fix: shared `read_jsonl_reporting()` helper that counts and prints torn lines; adopt per site.

### GG-970 — Foundation-doc staleness review (GG-074 monthly cadence) lapsed; doc registry + alarm now exist, most LIVING docs still unverified

**Status:** OPEN · **Severity:** MEDIUM

W80.4, 2026-10-20. GG-074's monthly grounding-doc review ran once (2026-07-23) and lapsed. Five months of drift followed: the kill-switch runbook described `python -m bot.kill_switch`, which does not exist. W80.4 classified 77 files in `00_ADMIN/DOC_REGISTRY.toml`, rewrote RUNBOOK_kill-switch, ACCESS_CONTROL_MATRIX and VENDOR_RISK against code and box, archived two superseded docs, and wired `scripts/doc_registry.py check` (alarm-only) into the governance scan. **Remaining:** LIVING docs with blank `last_verified` (01_SPEC, 08_MODEL_RISK_GOVERNANCE, the bannered 06/10 docs) are registered, not verified. The gap agent owns the cadence. Close when every LIVING doc has a `last_verified` or is converted to a pointer.

### GG-971 — Security posture gaps recorded in ACCESS_CONTROL_MATRIX, unregistered until now

**Status:** OPEN · **Severity:** MEDIUM

W80.4, 2026-10-20. Services run as root on the box; a single shared root SSH key (`VPS_SSH_KEY`) serves deploy, the box bridge and sync workflows; no vault (OQ-009). Recorded in `09_SECURITY_PRIVACY_COMPLIANCE/ACCESS_CONTROL_MATRIX.md` § known gaps. Not fixed in W80.4 (docs-only block). No real capital is at risk (Hard Rule 2).

### GG-985 — KXNBAPTS price history cannot be joined to absence announcement times (lineup cross part 5)

**Status:** OPEN · **Severity:** MEDIUM

W81.2, 2026-10-20. Of 100 candle-bearing KXNBAPTS markets (all 2025-26), 12 have a rule-defined single rotation-player absence; the 2-hourly injury-report snapshots observe the absent player in 2, and both reports precede market creation (markets open 1-20h before tip, mostly before the day's first 11:30 ET slot). No market has a before/after-news price, so the lineup-cross pricing share cannot be computed; the time was not approximated. Part 5 withheld, entry 2 stays interpreted. Fix: a prospective capture of KXNBAPTS prices around each report from the 2026-27 season (plumbing, not started). Evidence: `12_EXPLORATORY/20261020_nba_lineup_cross/results.md`, `price_join_markets.csv`.

### GG-990 — Installer gate treats any red reason that is not its own as a blocker, and the daily healthcheck line holds the budget RED for up to 24h after a transient fault

**Status:** OPEN · **Severity:** MEDIUM

<details><summary>Full record</summary>

W82.1, 2026-10-21. `scripts/passyds_install.py install` refused because the surface budget was RED with (a) its own job's `STALE ... no write found` (expected: a newly registered component is stale until installed) and (b) `healthcheck: UNHEALTHY: 1 fault(s)`. The installer exempts only reasons containing "passyds", so (b) blocked it. (b) was a transient `Kalshi DEMO API unreachable (2 tries)` in the 17:00Z daily run; `logs/health.log` summary stays UNHEALTHY until the next daily run (up to 24h), so one network blip blocks every installer and, by Hard Rule 14, every new component. Worked around by re-running `deploy/healthcheck.sh` by hand as cron does (not a code change).
Pattern sweep to do (Hard Rule 13): `scripts/thin_capture_install.py` gates outright on `budget != GREEN`; check each other installer for the same shape. Fix options: healthcheck re-run on a retry/short cadence or a freshness rule on the summary line; installers filter only reasons that are the registered component's own "no write found". The "newly registered component turns the budget red before it can be installed" catch-22 is only half-handled by the passyds substring filter. Not fixed here (Hard Rule 11).

</details>

### GG-1010 — NHL engine: confirmed pre-game starting goalie not available free

**Status:** OPEN · **Severity:** HIGH

W83.3 GAP-1 (NHL-2). The event store has the starter only post-game (box_players). A pre-game confirmed starter is not in a free structured feed with timestamps; W52.D verdict was "cannot tell" (GG-401). Without it the goalie factor cannot be used point-in-time at the pre-game horizon. Pillar: DEPTH (D1/D5 NHL). Proposed fix: capture lines/probable-starter pages on a schedule from the free NHL endpoints and timestamp them (forward only; no history).

### GG-1011 — NHL engine: travel and venue geometry factor not built

**Status:** OPEN · **Severity:** LOW

W83.3 GAP-2 (NHL-8). Arena coordinates, time zones and travel distance between consecutive games are derivable from free data (venue names in the store plus a public arena table) but not built. Pillar: DEPTH. Proposed fix: small static arena table plus a rest/travel feature in the engine.

### GG-1012 — NHL engine: officials, head coaches and scratches are free but not in the store

**Status:** OPEN · **Severity:** MEDIUM

W83.3 GAP-3 (NHL-9, NHL-10). `GET /v1/gamecenter/<id>/right-rail` exposes gameInfo.referees, linesmen, headCoach and scratches (verified on 2015-16 and 2024-25 games). Not fetched in W83.3: it needs a fourth fetch kind (~14.7k files, ~25 min). Pillar: DEPTH. Proposed fix: add the `rail` fetch kind to nhl_event_store, compile to a table, extend the point-in-time contract (T-1061).

### GG-1013 — NHL engine: no free injury or availability history

**Status:** OPEN · **Severity:** MEDIUM

W83.3 GAP-4 (NHL-11). Scratches are post-game only and there is no free structured injury history. Pillar: DEPTH. Proposed fix: forward-only daily snapshots of the public injury pages once a refresh job is registered; history cannot be backfilled for free.

### GG-1014 — NHL engine: PAM-derived and structured qualitative factors not piped into the engine

**Status:** OPEN · **Severity:** MEDIUM

W83.3 GAP-5 (NHL-12). No free structured historical qualitative feed; PAM (DS-01) is not yet read by any NHL engine. Pillar: DEPTH (D2 qualitative count 0). Proposed fix: a PAM-to-engine adapter, separate block; NFL and NBA first per operator directive 2026-10-14.

### GG-1030 — The box IP is blocked by the NBA CDN (Akamai 403 on all of ak-static.cms.nba.com), so the injury-report half of the W83.2 lineup-window capture cannot run on the VPS

**Status:** OPEN · **Severity:** HIGH

W83.2, 2026-10-22 00:36Z. `curl` of `https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-10-21_05_00PM.pdf` returns 403 (AkamaiGHost) from the box with and without a browser User-Agent, and the host root also 403s; the same URLs return 200 from the operator's Mac. The installed cron `nba_lineup_window` therefore records `report: none` and only the KXNBAPTS book snapshots (control_books); no report-time/book-before/after pair can form. Not worked around (no proxy, no paid service). Fix options for the next window: (a) capture the PDF from a non-datacenter free path (e.g. a scheduled GitHub Actions run, which needs its own permission and registry entry); (b) fetch a free mirror of the same report (nba_api / stats endpoints are likely blocked the same way: test first). Until fixed the frozen pre-registration (PREREG_lineup_window.md) accrues zero scored games; the first look (30 games) cannot be reached. Related: GG-985.

### GG-1031 — NBA play-type frequencies have no definition or event-store labels, so Muse's play-type class is gradeable by ordering against proxies only

**Status:** OPEN · **Severity:** LOW

W83.2. pbp carries no play-type labels and NBA.com publishes no definitions; the grade (PARTIAL, 4 of 7 classes hold at Spearman >= 0.5 against fixed proxies) cannot test the frequencies themselves. Needs a labelled source or a derivation rule; free only.

### GG-1032 — Python 3.9 on the operator's Mac cannot collect tests/test_seat_interface.py and scripts/render_seat.py (tomllib); /usr/local/bin/python3.11 works

**Status:** OPEN · **Severity:** LOW

W83.2. A stale NBA_SEAT.md render passed locally and failed in CI because the local default python lacks tomllib. Worked around with python3.11; the fix is a pinned local interpreter or a pre-push render check.

### GG-1060 — NBA PAM mass tier: archetypes and modifiers with no free signal at all stay UNSCORED

**Status:** OPEN · **Severity:** MEDIUM

W84.2 Part A. No free source gives a scorable clause for PRF-10, PRF-11 and modifiers M-1, M-7, M-8, M-9, M-10, M-11, M-12, M-15, M-16, M-19, M-20 (plus others listed UNSCORED in `12_EXPLORATORY/nba_pam_mass_tier/results_W84.md`); Muse's R-027 map marks PRF-10 and M-1/7-12/15/16/19/20/23/32 as NONE. All 420 qualified 2026 player-seasons are UNSCORED for each; never proxied. Pillar: DEPTH D5(b). Proposed fix: a source registered per row (tracking, defensive-matchup, or manual panel from the seat), or a v5 taxonomy decision that drops the row.

### GG-1061 — NBA PAM mass tier: the event store lacks height, age, years, hustle, catch-and-shoot, contested rebounds and deflections

**Status:** OPEN · **Severity:** MEDIUM

W84.2 Part A. Clauses needing those fields are unscored, so PRF-1…4, 8, 9, 12, 14, 15 can only reach MET_PARTIAL, never MET. stats.nba.com is unreachable and is not scraped around. Pillar: DEPTH D5(b). Proposed fix: add free height/age/experience (roster pages) and any free hustle source to the event store as a registered job; re-run `12_EXPLORATORY/nba_pam_mass_tier/run.py`.

### GG-1062 — NBA PAM taxonomy v4 clauses that cannot be scored as written

**Status:** OPEN · **Severity:** LOW

W84.2 Part A. PRF-14's volatility clause has no defined metric, and PRF-1's 40%-of-possessions clause has no definition; both left unscored rather than interpreted. Pillar: DEPTH D5(b). Proposed fix: Muse/seat define the metric in v5; `taxonomy.json` was not edited here.

### GG-1063 — Muse's NBA 2026 play-type games-played values appear to predate season end; 2024 values differ from the store

**Status:** OPEN · **Severity:** LOW

W84.2 Muse grade. Of 21,249 graded GP records, play-type 2026 exact rate is 15.4% (Muse lower by 1–5, mean −2.29), tracking 2024 65.4%, 2025 92.6%; only play-type 2025 (99.1%) and tracking 2026 (99.3%) reach the 99% VERIFIED bar. Cause for 2026 play-type is likely snapshot timing, not proven. Muse values are used for season-end assignment only and kept out of the point-in-time table. Proposed fix: Muse refreshes or dates its snapshots (TO_MUSE.md entry).

### GG-1064 — NBA player-points shadow rows cannot settle the PRF-1 cross: no outcome field and no 2026-27 games in the store

**Status:** OPEN · **Severity:** LOW

W84.2 Part B cross not run (n = 0): PREGAME_SHADOW NBA_PLAYER_POINTS rows (since ~2026-10-18) carry p_yes and the market mid but no actual points, and the store holds no 2026-27 games. Also `12_EXPLORATORY/CHARTER.md` rule 2 (no exploratory reads of PREGAME_SHADOW) conflicts with the block text that names them. Proposed fix: refresh the event store with 2026-27 games, then run the cross as a pre-registered read once a few hundred player-games settle; resolve the charter conflict explicitly.

### GG-1090 — No Kalshi candle history for NFL spread, total or team-total markets, nor for the 2026 season: the market-anchored test could only measure the anchor-timing gap on moneyline 2025

**Status:** OPEN · **Severity:** MEDIUM

W85.1 Part A. `exp_output/KALSHI_HISTORY/candles/KXNFLGAME.jsonl` holds 411 one-minute sets (188 games, 2025 season to Jan 2026). There is none for the spread, total or team-total series and none for 2026, so the T1/T2/T3 anchor-versus-close gap (SD 0.026/0.021/0.015 at ko-36h/-24h/-6h vs 0.010 at ko-30min) is measured on moneyline only, and the historical test anchors every family on the de-vigged close. EXP-041's live anchor is the mid at decision time. Proposed fix: archive the three ladder series' candles forward and backfill what the public API serves; free data only. Owner: next DEPTH wave.

### GG-1100 — distance_to_optimum D3 undercounts pre-registered challengers (EXP-041 not counted)

**Status:** RESOLVED (W87.1, d3() reads the pre-registration files; D3 1 -> 3) · **Severity:** LOW

W86.1 Part B. `scripts/distance_to_optimum.py` `d3()` counts `.md` files under `12_EXPLORATORY/` or `03_DECISIONS/` whose filename contains "challenger" and carry `**Status:** PROPOSED|ACCEPTED`. EXP-041 (`05_RESEARCH_EXPERIMENTS/EXP041_NFL_MARKET_ANCHORED_PREREGISTRATION_2026-10-22.md`, `**Status:** FROZEN`) fails all three tests, so D3 reports 1 where 2 are expected. Not fixed in W86.1 (reconcile-only). Fix: define challengers from a registry, not a filename/dir/status pattern.


### GG-1180 — Monitor ECE bins by np.linspace edges; every pre-registered ECE bins by int(p*n)

**Status:** OPEN · **Severity:** LOW

W87.1 Part A (`12_EXPLORATORY/quant_core_reconcile/results_W87.md`). `c7_monitoring/monitor.py::_compute_ece` puts p=0.3, 0.7 etc. one bin lower than `quant.ece` (linspace(0,1,11)[3] = 0.30000000000000004). Snapshot ECE 0.1107 vs 0.1134. Matters for probabilities rounded to 0.1/0.01. Not re-pointed: live ADR-0004 drift ladder (T-281 deferred), c7 not owned by 87.1. Fix = one ADR-0004 amendment + threshold re-derivation.


### GG-1181 — irls_logistic differs from quant.slope_intercept by 1.8e-5 / 1.3e-4

**Status:** OPEN · **Severity:** LOW

W87.1 Part A. Clamp and stopping tolerance differ on p=0/1 rows. Pre-registrations use the core's. Not re-pointed.


### GG-1182 — scoring._best_side_e_net chooses the side by gross edge; core net_edge by net edge

**Status:** OPEN · **Severity:** LOW

W87.1 Part A. Differs on 2 of 4,000 snapshot quote/outcome pairs. EXP-036/037 pre-registered realised E_net uses the gross choice, so it is kept; any change is a new pre-registration, not an edit. Registered so a future reader does not treat it as a bug.


### GG-1183 — Forward-test CI is analytic (Z=1.645 one-sided); the core and every other look use a percentile bootstrap

**Status:** OPEN · **Severity:** LOW

W87.1 Part A. Means identical; half-widths differ 0.16 vs 0.17 on the snapshot. The forward-test rule uses the analytic one; kept. Registered as a definition difference.


### GG-1190 — T4 `cache_bankroll` is flat at $1,000 against realized −$140.93

**Status:** OPEN · **Severity:** MEDIUM

W88.1 Part A. Any drawdown or exposure limit expressed as a fraction of bankroll reads a bankroll that does not move with realized P&L on the T4 book (cache $1,000; ledger realized −$140.93 on 4,316 paper bets). Percent-of-bankroll limits are therefore not measuring what they say for T4. Needs an owner decision on which bankroll the limits read. Not fixed here (Hard Rule 11).

### GG-1191 — Shadow books have no fill-priced per-game P&L

**Status:** OPEN · **Severity:** MEDIUM

W88.1 Part A. Tails for the NFL/NHL/NBA/MLB-postseason shadow arms cannot be fit: those rows are evaluations without fills, so no fill-priced per-game loss exists. ADR-0076 qualifies per (book, sport) on real fills only (GG-527), so these sports have no tail evidence until fills exist.

### GG-1192 — Per-event cap `max_single_event_exposure_usd` (500) has a stale depth rationale

**Status:** OPEN · **Severity:** LOW

W88.1 Part B. The 500 figure was justified by book depth, which GG-155 showed is volatile (10-100x intraday) and not citable. ADR-0076 section 4 leaves the cap BLANK and flagged rather than re-deriving it, because no positive Kelly is authorized (ADR-0048).

### GG-1230 — MLB games-cache sync seeded from the frozen season seed, not its own previous output; the MLB game-market shadow went silent 31h+

**Status:** OPEN · **Severity:** HIGH

W88.2 Part 0 (RED surface budget). Cause, read on the box and in the run log: `mlb_games_cache_sync.yml` seeded only `games.parquet` (last Final 2026-10-04) and `refresh_recent` measures its 21-day gap from the last Final in whatever it patches. Every run from 2026-10-25 05:16Z failed `REFRESH FAILED: cache last Final 2026-10-04 is >21d behind` (4 consecutive scheduled failures); the box's `games_current.parquet` stayed at 2026-10-24T16:16Z, the runner's 26h stamp check refused to log, and the arm wrote nothing after 2026-10-25 18:07Z. Fix: seed the previous `games_current.parquet` from the VPS too (workflow and `scripts/sync_mlb_games_cache.sh`); regression test `test_refresh_chains_from_previous_output_not_the_frozen_seed`. Stays OPEN until a post-merge sync run is green and a new shadow row is read back on the box.


### GG-1231 — A failing cache-sync workflow raised no alarm; only the downstream silent-arm check caught it, ~31h later

**Status:** OPEN · **Severity:** MEDIUM

W88.2 Part 0. Four scheduled `MLB Games Cache Sync` failures (2026-10-25 05:17Z to 2026-10-26 18:52Z) were visible only in the Actions tab. The runner's own refusal ("refusing to log on stale data") goes to a log nobody reads. Silent-arm detection works but is the last line, after >12h of lost shadow rows. Candidate: have the silent-arm block print the cache stamp age and the last sync run status beside any arm that reads the games cache. Registered, not fixed in this block (Rule 11).

### GG-1232 — Kalshi list payload has no usable quote time: market.updated_time is static, so shadow rows could not be checked for stale quotes

**Status:** OPEN · **Severity:** MEDIUM

W88.2 Part B. Three reads of `GET /markets?series_ticker=KXMLBGAME` 20s apart (2026-10-27 01:31Z) returned an unchanged `updated_time` (2026-10-20T03:41:00Z, the open time) on a live market whose bid/ask differed from `previous_yes_bid/ask`. W87.3's stale-quote check on NHL_GAME_TOTAL_T1 was NOT MEASURABLE for this reason. Fix shipped (PR for W88.2 Part B): rows now carry `quote_ts_utc` / `quote_age_s` / `quote_ts_source` from the list response's HTTP `Date` header (exchange clock; age includes skew + latency). **Limit, stated plainly:** this is when the book was read, not when the quote last changed; time-since-last-change still needs the orderbook or trades endpoint (last trade `created_time`, one extra request per market) and is not built. Stays OPEN until a box row is read back carrying the fields.

### GG-1240 — SHADOW exposure book can never settle: its stakes accrue as open forever, and a settled-feed hit would count them as unresolved against a $1,000 notional

**Status:** RESOLVED · **Severity:** HIGH

**Resolution (W89.1, PR #342):** SHADOW book flagged `advisory: True`; excluded from breaches/system sums like frozen books, still reported and still needs a live writer. Box state confirms SHADOW advisory=True, system drawdown MLB_T1 only (12.444%).

W89.1, 2026-10-27 04:10Z, read on the box. `logs/exposure_gate_state.json`: SHADOW `open_stake_usd` 86,548.35 against `SHADOW_NOTIONAL_USD` 1000, drawdown 0.0. Open stake is not in the drawdown, so nothing trips today. `shadow_flat_stake.py:114` only READS the settled set (`load_settled()[0]`); `refresh_settled` is called only from `paper_trader.py:388`. So no shadow ticker is ever fed to the settled set by the shadow path. If any shadow ticker reaches it (another book's order on the same market), `settled_unresolved_stake_usd` rises, and since shadow stakes never resolve (GG-1175) the SYSTEM worst-case drawdown reaches 20% and the global halt is written. In ENFORCE that halts every book. Block before the enforce flip: either give SHADOW a resolution path or exclude it from the system drawdown. Registered, not fixed here (Hard Rule 11; the fix is a design choice about what the shadow book's exposure means).

### GG-1241 — The exposure gate has no read-back that every book feeds: MLB_T4 absent from the state file and the settled-feed cache file does not exist

**Status:** PARTIALLY RESOLVED · **Severity:** MEDIUM

**Update (W89.1, PR #342):** `PaperTrader.__init__` now seeds its book at construction, so MLB_T4 exists before any T4 order (no `exposure_book_no_writer:MLB_T4` deadlock). OPEN remainder: MLB_T4 key absent from the state file until a game goes live and T4 constructs its trader; the settled-feed cache file still not observed. Read back after the next MLB game day.

W89.1, 2026-10-27 04:10Z. `exposure_gate_state.json` holds MLB_T1 and SHADOW only. No MLB_T4 key (t4-mlb restarted 03:13Z; no order since). `exposure_gate_settled.json` does not exist, so the settled feed has never run. `logs/exposure_gate_logonly.jsonl` does not exist: zero would-halts recorded, but no book has yet been through a game day. In ENFORCE, `exposure_book_no_writer:MLB_T4` would refuse the first T4 order if the key is still missing. Part B needs a game day in which T4 writes its book; this is the read-back that proves it.

### GG-1250 — NHL, NBA and every parlay/multi-leg Kalshi family are not in the price archive, so none can be calibration-tested

**Status:** OPEN · **Severity:** MEDIUM

W89.2, 2026-10-27. The archive covers MLB game-market families, KXMLBHIT and NFL GAME/SPREAD/TOTAL/TEAMTOTAL only. W89.2 BREADTH of the calibration test is capped there. Fix: add the NHL/NBA series and the parlay families to the archiver, then re-run `12_EXPLORATORY/longshot_bias/run_w89_2.py`.

### GG-1251 — Candle history is partial and local-only, so price paths between archive snapshots cannot be rebuilt

**Status:** OPEN · **Severity:** LOW

W89.2, 2026-10-27. KXNFLGAME holds 415 of 862 tickers; EXP-035 candle numbers are VOID. Part B of W89.2 used ~20-min archive snapshots, which cannot see sub-snapshot overreaction.

### GG-1252 — NFL tickers carry the date only, so a D0 first snapshot may be in-play

**Status:** OPEN · **Severity:** MEDIUM

W89.2, 2026-10-27. KXNFLTOTAL D0 5-10c NO passed BH and the net filter but is excluded as possibly contaminated by in-play prices. Fix: join NFL kickoff times (free schedule feed) and re-tier by hours to kickoff.

### GG-1253 — MLB ticker HHMM is read as Eastern time without a per-family check

**Status:** RESOLVED · **Severity:** LOW

**RESOLVED 2026-10-28 (W91.1, T-1340).** Checked against each market's `rules_primary` clock for all 8 families: ticker HHMM read as ET matches on 100% of F5TOTAL, F5, F7, SPREAD, TEAMTOTAL, TOTAL and 125,511/126,057 (99.57%) of KXMLBHIT. `occurrence_datetime - 3h` matches 0% for F5/F7, so HHMM-as-ET is the right rule. Evidence: `12_EXPLORATORY/ride_cells/results_W91_1.md`.

W89.2, 2026-10-27. Consistent with run_ts on a known game, not proven for every family. A wrong offset would mis-tier T0-2h cells (the KXMLBHIT candidate sits in T0-2h). Check against the ESPN start time for a sample of games.

### GG-1254 — The W89.2 survivors have no out-of-sample window

**Status:** OPEN · **Severity:** MEDIUM

W89.2, 2026-10-27. 11 cells survive BH + split-half sign + net-of-fee lower bound > 0, all in-sample over 2026-08-01 to 2026-10-26. No hold-out exists; pre-registration must fix price band, tier, side and a forward window before any further row is read.

### GG-1280 — KXNBAPTS mid-quote anchor can sit days before tip

**Status:** OPEN · **Severity:** LOW

W89.5, 2026-10-27. 2,156 of 2,369 KXNBAPTS markets open before tip (median about 19h); the first usable quote is a median 16h early, so "price at the row's time" needs a stated anchor. Part B reports both first-usable and last-pre-tip. Any later points-prop cell must pre-register its anchor.

### GG-1281 — Joined KXNBAPTS data shows zero DNP rows

**Status:** OPEN · **Severity:** LOW

W89.5, 2026-10-27. dnp_rows=0 across 2,409 joined strikes; either Kalshi lists only players who played or the ESPN didNotPlay flag is not populated. Not verified. Matters before any "player did not play" treatment.

### GG-1282 — 2026-27 rookies and new signings have no PAM role

**Status:** OPEN · **Severity:** MEDIUM

W89.5, 2026-10-27. 14 players with KXNBAPTS strikes (e.g. Cameron Boozer, Kyrie Irving, Tyrese Haliburton) have no 2025-26 season-end PAM record, about 6.8% of usable strikes. Needs a 2026-27 season-to-date PAM refresh (free data) before roles cover the whole board.

### GG-1283 — Two preseason KXNBAPTS events not joined

**Status:** OPEN · **Severity:** LOW

W89.5, 2026-10-27. KXNBAPTS-26OCT08PHIBKN and KXNBAPTS-26OCT05NYKPHI are preseason-dated and were excluded by the 2026-10-20 window; not investigated. GG-1064 (the sealed-store conflict) is superseded for this cross: W89.5 joined from public Kalshi and ESPN data and read no shadow file.

### GG-1284 — Other Kalshi candlestick callers not audited for the window-400 limit

**Status:** OPEN · **Severity:** LOW

W89.5, 2026-10-27. A wide start_ts..end_ts at period_interval=1 returns HTTP 400 (candle-count limit); w89_join.py caps its window at 6h. Nine other callers (listed in the W89.5 handoff pattern_sweep) were not checked for the same span problem.

### GG-1290 — W89.7 backfill writes outside the EXPLORATORY fence (renumbered from GG-1260, which W89.3 already held)
**Status:** RESOLVED (W90.1) · **Severity:** MEDIUM

2026-10-27, T-1290; W90.1 2026-10-27. PR #349 CI failed on w89_7_backfill.py:86 (datetime .replace) and :277 (.write_text). Fixed in W90.1: et_date parses with %z (no .replace), the tracked MANIFEST.json files are written through safe_out() into 12_EXPLORATORY/market_history/manifests/w89_7/<sport>/, and exp_output/KALSHI_HISTORY/w89_7/ is gitignored (untracked 800 MB cache). The same-id collision with W89.3's GG-1260 is the GG-162 class; this entry takes GG-1290.

### GG-1291 — The exploratory fence scan does not see Path.open("w") / method-form writes, so bulk-cache writers sit outside the fence unflagged
**Status:** OPEN · **Severity:** LOW

W90.1, 2026-10-27. tests/test_exploratory_isolation.py polices builtin open() and a WRITE_ATTRS set, not `path.open("w"|"a")`. w89_7_backfill.py (schedule, events, markets, candles) and market_history/fetch_game_hourly.py write under exp_output/ that way and pass. CHARTER rule 3 says every write goes through safe_out(). Either the scan gains `.open` with a write mode (then these two move their cache inside 12_EXPLORATORY or into src/), or the charter gets a dated addendum naming an untracked-cache exemption. Not fixed in W90.1 (Hard Rule 11).

### GG-1330 — NBA and NHL have no price archive, so the router cannot be replayed for them

**Status:** OPEN · **Severity:** MEDIUM

W90.2, 2026-10-27. The archiver covers MLB and NFL series only; add KXNBA*/KXNHL* series to the archive (free public data).

### GG-1331 — News timing is not a measured routing condition

**Status:** OPEN · **Severity:** LOW

W90.2, 2026-10-27. No measurement of price reaction to news timing exists, so the router ignores it. A news-timestamp feed plus a pre-registered reaction study would be needed.

### GG-1332 — No measured momentum transition table exists

**Status:** OPEN · **Severity:** MEDIUM

W90.2, 2026-10-27. MOMENTUM trees get zero traffic. W89.2 Part B found 0 survivors; Wave 90.3 owns the momentum measurement.

### GG-1333 — FADE not replayed against shadow ledgers

**Status:** OPEN · **Severity:** LOW

W90.2, 2026-10-27. Ledgers are on the box and unsettled locally; FADE is gated to 0 by W88.3 skill regardless. Replay once any (sport, family) shows a positive CI lower bound.

### GG-1334 — RIDE replay is in-sample

**Status:** OPEN · **Severity:** MEDIUM

W90.2, 2026-10-27. The stub ride table is the W89.2 survivor list drawn from the same archive; the replay is not evidence. Out-of-sample forward window is 90.1's pre-registration.

### GG-1300 — No archive of observed news-report timestamps; the W90.3 news/no-news split is a calendar proxy
**Status:** OPEN · **Severity:** MEDIUM

W90.3, 2026-10-27, T-1310. Strategy J's "news-driven vs unexplained" split needs the time a lineup, injury report, inactives list or practice report was actually published. None is archived (the NBA injury-report relay branch is recent-only; MLB lineup and NFL report times were never captured). 12_EXPLORATORY/momentum_j/core.py `news_intervals` substitutes scheduled windows (MLB start-4h..start-1.5h, NFL Wed-Fri 17:00-18:30 ET + inactives, NBA/NHL game-day windows), so 98% of MLB signals read as "quiet" and the one BH-positive cell (MLB news-window settle-fade, n=53/41 games) rests on the proxy. Needs a free source of real publish times captured going forward (MLB lineup posts from the stats API, NFL/NBA/NHL official reports) before any news-conditioned cell is pre-registered.

### GG-1301 — MLB game start taken from the ticker HHMM read as ET is unverified for the W90.3 time-to-start tiers
**Status:** OPEN · **Severity:** LOW

W90.3, 2026-10-27, T-1310. run_w90_3.py `mlb_start` reads the event-ticker HHMM as US/Eastern, the same assumption as GG-1253, and no join to a schedule source confirms it for the 52,474-ticker archive. It only drives the time-to-start tier and the news-window proxy, not the move or the cost; a wrong offset would shift tier boundaries. Closes with GG-1253.

### GG-1302 — NBA and NHL pre-game history is one hourly-candle season-start window (n<=119 signals), too thin to carry a router decision
**Status:** OPEN · **Severity:** LOW

W90.3, 2026-10-27, T-1310. The follow/fade grid for NBA (91 signals) and NHL (117) comes from the 89.7 hourly game-market candles only; no spread, total or prop candles exist and the cadence (1 h) is coarser than the MLB/NFL archive (20 min). Their cells are mostly untestable (<30 games) and the NBA settle-follow cell that clears BH is a single marginal split. Re-run W90.3 when the shadow arms have logged a season of two-sided pre-game quotes.

### GG-1292 — The ride hold-out scan is underpowered: 52-121 games per family, 1 of 1,850 discovery cells testable

**Status:** OPEN · **Severity:** MEDIUM

**Update 2026-10-28 (W91.1):** the same limit recurred in the backward test (GG-1341); see also GG-1340.

W90.1, 2026-10-27. The candle sample (4 strikes/event, 3-minute fetch budget per family) gives ~67 games per spread/total/team-total family; after the median split a cell cannot reach calib.MIN_EVENTS = 30. Result is "cannot detect", not "no edge" (results_W90_1.md). Fix: longer fetch per family (newest first, one sport at a time) and/or coarser buckets pre-registered before the next scan.

### GG-1293 — W90.1 Part A undone items

**Status:** OPEN · **Severity:** MEDIUM

**Update 2026-10-28 (W91.1):** item (2), the GG-1253 HHMM-as-ET check, is done and GG-1253 is RESOLVED; the other items remain.

W90.1, 2026-10-27. Not done: (1) re-test of 89.2's three named MLB candidates after its window and on 2025 history (MLB PRICE_ARCHIVE is box-only); (2) GG-1253 MLB HHMM-as-ET check against the schedule; (3) prop-family candles; (4) one residual unmatched NFL event (LACDET, no_team_pair); (5) GG-1254 still open. Ride.py (Part B) not started.

### GG-1340 — Hourly-candle method fails the overlap bucket-agreement bar against the 20-min snapshot method, so the W91.1 backward test is VOID

**Status:** OPEN · **Severity:** MEDIUM

W91.1, 2026-10-28, T-1340. EXP-042 overlap check (2026-08-01..10-27, 1,902 matched (ticker, tier) observations): 83.8% same 5c bucket vs the >=85% bar; mean entry-price diff -0.0002 passes. Weakest: KXMLBTEAMTOTAL 73.2%, KXMLBF5 77.8%, KXMLBF5TOTAL 79.3%. Per the pre-registration the backward test is VOID and no pre-August date was scored. Not re-tuned. Fix: a new EXP with a finer-than-hourly source (the 20-min archive is box-only from 2026-08) or a bar re-derived before seeing data; do not relax the bar post hoc.

### GG-1341 — Kalshi public market-data rate limit (~4 req/s global, 429s) makes every-strike candle fetch infeasible in one block

**Status:** OPEN · **Severity:** MEDIUM

W91.1, 2026-10-28, T-1341. 8 parallel fetch processes shared ~4 req/s with frequent 429s; one family's every-strike window is tens of thousands of markets. The overlap sample was wall-clock-capped (~100-400 calls per family), so no cell reached 30 games; coverage is partial. Fix: a resumable low-rate background collector over several days, newest first, one sport at a time (also serves GG-1292).

### GG-1342 — Ride cells have no scored look until MLB resumes: forward looks start 2027-04

**Status:** WATCH ITEM · **Severity:** LOW

W91.1, 2026-10-28, T-1342. All 11 cells stay IN_SAMPLE (backward UNTESTED). MLB accrues nothing between the World Series and ~2027-03-25. Earliest full-effect looks: cell 6 ~2026-12-21 (NFL); 3 2027-04-11; 10 04-15; 5 04-28; 2 04-29; 4 05-06; 1 05-18; 9 06-07; 8 06-11; 7 06-17; 11 06-25. PASS needs the half-effect judged n (EXP-042 section 3). Reopens if a look date is reached or the operator changes the ride rule.
