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

### KI-011 — Injury Blindness: Model Generates Fake Alpha on Injured/Questionable Players

| Field | Detail |
|-------|--------|
| Issue ID | KI-011 |
| Severity | HIGH |
| Category | Model validity / systematic false signal |
| Description | The model has no access to injury or availability information. Kalshi market makers do. When a player is injured or questionable, Kalshi prices in a dramatically reduced probability of performance (e.g., mid_price = 0.085 for a player who averages 15+ points). The model, blind to this information, produces a p_estimate based on historical performance and assigns a large positive edge (e.g., +0.46). This is not alpha — it is the model being systematically wrong in exactly the situations where the market has publicly available information the model lacks. **The injury blindness failure mode does not just eliminate markets: it generates the largest apparent edge signals in the entire system, and those signals are reliably wrong.** A model that places bets on injured/questionable players will lose nearly every time on those bets, and the loss magnitude scales with the apparent edge — which is highest precisely when the player is injured. |
| Impact | Systematic source of capital drain masquerading as alpha. Any paper bet placed on a questionable player is a contaminated G6 evidence data point. This is the primary risk to positive P&L in paper trading. |
| Workaround | Manual: check Kalshi mid-prices before each session; any market priced below 0.15 for a historically high-usage player is a likely injury signal. Do not bet into these. Automated fix requires DS-04 injury feed (T2 overlay). |
| Blocks gate | G6 — paper P&L reliability is compromised by injury-blind bets; injuries can drain bankroll while generating misleading high-edge signals |
| Resolution path | (1) T2 injury overlay (run_t2_sameday.py stub, T-075): implement DS-04 injury feed check before bet placement — if player is OUT or QUESTIONABLE, remove from t2_forecasts or reduce kelly_fraction to 0.05. (2) Interim: add a market price filter — reject bets where Kalshi mid_price deviates >0.25 from model p_estimate as a likely injury/information signal. (3) EXP-017 must control for this when backtesting edge vs actual Kalshi prices. |
| Open question | OQ-023 — does the model generate positive EV against actual Kalshi prices once injury signals are excluded? |
| Registered | 2026-05-29 (updated 2026-06-01 — severity escalated; failure mode corrected) |
| Status | OPEN — HIGH severity; injury overlay is the fix; required before G6 |

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
| Status | ✅ RESOLVED 2026-06-01 — T-091 complete. `check_portfolio_pnl()` added to `SystemMonitor`. L1 (5% of initial bankroll) → INFO `pnl_alert_l1_watch`; L2 (10%) → WARNING `pnl_alert_l2_loss`. Wired into PIPE-03 (`run_paper_trade.py`) and PIPE-03R (`run_resolve.py`). DS sign-off: Earl Ignacio 2026-06-01. 589/589 VPS tests pass. |

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

### KI-014 — Idempotency Check Failure: Duplicate Open Positions Per Ticker

| Field | Detail |
|-------|--------|
| Issue ID | KI-014 |
| Severity | HIGH |
| Category | Paper trading / position integrity |
| Description | PIPE-03 placed 3 open positions on the same Kalshi ticker in one session (Fox YES 15+ and SGA NO 30+, all for 2026-05-30 SAS vs OKC). The idempotency check reads `trader.get_state().get("open_positions", [])` and skips any ticker already in the set. Despite the first run placing Fox and SGA at 17:40 UTC, the 22:00 UTC and 01:30 UTC cron runs also placed positions on identical tickers. Root cause is unknown — likely a cron working-directory mismatch causing `_load_or_init()` to fall back to a fresh empty state, or a ticker representation mismatch between stored string and Kalshi API response. |
| Impact | 3× intended exposure on De'Aaron Fox ($154.07 staked vs ~$56 intended) and SGA ($83.77 vs ~$28 intended). $237.84 total at-risk for one game. Inflated apparent drawdown (23.78%). If all positions lose, realized loss is 3× expected. |
| Workaround | Monitor `logs/paper_portfolio.json` after each PIPE-03 run. If duplicate tickers appear, resolve manually. Add diagnostic logging at startup to confirm portfolio file path and loaded state count. |
| Blocks gate | G6 indirectly — inflated position size distorts paper P&L evidence quality |
| Resolution path | (1) Add startup logging in `run_paper_trade.py`: log `portfolio_path.resolve()` and `len(open_positions)` before the inference loop. (2) Reproduce on VPS to confirm whether state file was being read correctly. (3) Fix root cause once identified. |
| Registered | 2026-05-30 |
| Status | ✅ RESOLVED 2026-05-30 — T-101 complete; root cause confirmed: relative LOG_DIR caused each cron run to start with a fresh portfolio; fixed to absolute path; idempotency now working correctly; 3× legacy positions remain open and will close naturally |

---

### KI-015 — Drawdown Includes Open Position Stakes (Not Realized Losses Only)

| Field | Detail |
|-------|--------|
| Issue ID | KI-015 |
| Severity | HIGH (operational blocker) |
| Category | Risk engine / paper trading |
| Description | `current_drawdown_pct` is computed as `1.0 - bankroll / initial_bankroll` where `bankroll` is the cash balance AFTER deducting open position stakes. This means placing bets causes apparent drawdown even if no losses have been realized. With $237.84 in open stakes (Bug G inflated this 3×), apparent drawdown = 23.78%, which exceeds the 20% kill switch threshold. PIPE-03 will KILL_SWITCH at 22:00 UTC tonight. This bug was latent until Bug C was fixed (which made drawdown evaluation active). |
| Impact | PIPE-03 halted every run until: (a) open positions resolve and bankroll recovers below 80% of initial, or (b) Bug H is fixed. G6 bet accumulation (T-070) is blocked during this window. |
| Workaround | Wait for PIPE-03R (06:00 UTC 2026-05-31) to resolve the 6 open positions. If bankroll recovers above $800 (drawdown < 20%), PIPE-03 can resume. If all positions lose, bankroll stays at $762.16 and permanent fix is required. |
| Blocks gate | G6 — paper bet accumulation blocked while kill switch fires |
| Resolution path | Fix: compute drawdown from realized losses only. `Option A (preferred)`: `realized_loss = max(0.0, -_state.get("total_realized_pnl", 0.0))` / `initial_bankroll`. `Option B`: add open stakes back to effective bankroll before computing ratio. This is a Class A change (kill switch behavior) — requires DS sign-off before deployment. Register as a new fix task. |
| Registered | 2026-05-30 |
| Status | ✅ RESOLVED 2026-05-30 — T-100 complete; drawdown now uses `total_realized_pnl` only; DS sign-off granted; deployed to VPS; kill switch confirmed cold at 0.00% realized drawdown |

---

### KI-016 — max_concurrent_positions: 10 Is an Unresolved G4 Stub ✓ RESOLVED

| Field | Detail |
|-------|--------|
| Issue ID | KI-016 |
| Severity | HIGH |
| Category | Risk engine / architectural gap |
| Description | `_HARD_LIMITS["max_concurrent_positions"]` was set to `10.0` in `risk.py` with the comment `# 10 concurrent open (stub)`. This value was never resolved at G4 and was architecturally wrong for an 80-player, multi-band, multi-game system. |
| Impact | Portfolio reached 9/10 positions; Finals G2 bets would have been silently rejected. Regular season would routinely hit limit and suppress bet accumulation. |
| Resolution | ADR-0006 (2026-06-01): count gate deleted entirely. No replacement count primitive. Pipeline filtering → Kelly sizing → $500/event cap → $1,000 daily loss → 20% drawdown kill switch are the complete risk framework. `max_concurrent_positions` removed from `_HARD_LIMITS`, `evaluate_forecast()` signature, CHECK 3 block, `run_paper_trade.py`, and 2 tests. `RISK_APPETITE_CONSTRAINTS.md` and `EXECUTION_ARCHITECTURE.md` updated. |
| Registered | 2026-05-31 |
| Status | RESOLVED — 2026-06-01 (ADR-0006; T-102 complete) |

---

### KI-017 — EV Validation Is Against a Coin Flip, Not Kalshi Market Prices

| Field | Detail |
|-------|--------|
| Issue ID | KI-017 |
| Severity | HIGH |
| Category | Model validity / commercial question unanswered |
| Description | Every EV figure produced by this project — `+$0.0958/bet` (EXP-010), `+$0.0855/bet` (EXP-004), `59% win rate` — was computed using `mip = 0.50` as the market implied probability. See `run_exp010.py:164`: `mip = 0.50  # market_implied_prob = 0.50 (conservative null)`. This means the system has validated "model beats a coin flip." It has not validated "model beats an informed professional Kalshi market." These are categorically different questions. EXP-004 Part B and EXP-010 Part B used live prices, but only spot-checked 2 players on a single day — this is a sanity check, not statistical validation. All 16 experiments completed; zero of them answer the commercial question the project is built to answer. |
| Impact | The core commercial claim of this system — that the model generates positive expected value when competing against real Kalshi prices — is unvalidated. G6 paper trading results will show real P&L against real prices, which will be the first real evidence. But this should have been a backtest question answered at G4. |
| Workaround | None — this is a measurement gap, not a code bug. Paper trading is accumulating real-world evidence, but variance over 30 bets is too high to be conclusive. |
| Blocks gate | G6 indirectly — if EXP-017 shows negative EV vs real prices, G6 evidence is compromised |
| Resolution path | EXP-017: backtest edge against actual historical Kalshi prices (not 0.50). Pull historical mid-prices for test-set games, re-run edge computation as `edge = model_p - kalshi_mid_price`, re-compute EV distribution. Requires historical Kalshi price data for the TEST period (2023-24 season). Register as T-105. |
| Open question | OQ-023 |
| Registered | 2026-06-01 |
| Status | OPEN — HIGH; EXP-017 required before G6 gate can be cleared with confidence |

---

### KI-018 — Zombie Daily Loss Limit: max_daily_loss_usd Cannot Fire at Current Bankroll

| Field | Detail |
|-------|--------|
| Issue ID | KI-018 |
| Severity | MEDIUM |
| Category | Risk engine / risk communication |
| Description | `_HARD_LIMITS["max_daily_loss_usd"] = 1000.0` was calibrated to a $1,000 starting bankroll. Current bankroll is $683.41. The 20% drawdown kill switch fires at ~$136.68 of realized loss. The daily loss limit requires $1,000 of loss in a single day — which cannot occur without losing more than the entire bankroll. The code presents two independent financial kill switches; there is effectively one. Anyone reading the risk configuration sees "$1,000 daily protection" — the real protection is $137. This is a risk communication failure that will matter when live capital is deployed. |
| Impact | No immediate operational risk — the drawdown % kill switch is the real guard and works correctly. Risk is that future operators or the live capital ADR process treats the daily loss limit as a meaningful independent constraint when it is not, leading to underestimation of daily risk. |
| Workaround | Drawdown % kill switch is operative. Document in risk.py that daily loss limit is currently inactive and will be recalibrated at G6. |
| Blocks gate | G6 (live capital ADR must address this) |
| Resolution path | At G6, when live bankroll is set: update `max_daily_loss_usd` to `live_bankroll * 0.10` (10% of bankroll as daily floor) or equivalent justified value via ADR. Until then, add a comment in `_HARD_LIMITS` noting the limit is inactive at current paper bankroll scale. |
| Registered | 2026-06-01 |
| Status | OPEN — MEDIUM; non-blocking for paper trading; must be addressed in G6 live capital ADR |

---

### KI-019 — Polymarket Tag Stub: Silent Empty Market Return on Wrong NBA Tag

| Field | Detail |
|-------|--------|
| Issue ID | KI-019 |
| Severity | MEDIUM |
| Category | Execution / silent failure |
| Description | `c5_execution/venue_adapter.py:251` has `"tag": "nba"` hardcoded as the Polymarket market filter with a `# TODO: confirm Polymarket's NBA tag name` comment. Polymarket's actual API tag structure for NBA player props is unconfirmed — it may be `"sports"`, `"basketball"`, `"nba-player-props"`, or another value. When T-077 (Polymarket KYC) is completed and Polymarket is activated, a wrong tag returns an empty market list with no error, no exception, and no log warning. The pipeline proceeds, finds no opportunities, and the operator has no signal that anything is wrong. This is the same class of silent suppression as the count gate (KI-016). |
| Impact | Polymarket integration silently non-functional at activation. All bets route to Kalshi only with no indication that line shopping is failing. EXP-014 line shopping benefit (+7.8% EV) cannot be realized. |
| Workaround | None until T-077 is attempted. At T-077 activation time: test VenueAdapter directly, confirm market list is non-empty, verify tag before enabling VENUE_ROUTER_MODE=best_price. |
| Blocks gate | Non-blocking until T-077; blocks line shopping strategy (Strategy E) benefit |
| Resolution path | Before activating Polymarket (T-077): (1) confirm actual NBA player props tag via Polymarket API documentation or test call; (2) update `venue_adapter.py:251` with confirmed tag; (3) add assertion: if adapter returns 0 markets on a day with known NBA games, raise VenueAdapterError, do not silently return empty. |
| Registered | 2026-06-01 |
| Status | OPEN — MEDIUM; non-blocking until T-077; must be resolved before Polymarket activation |

---

### KI-020 — Kalshi Authenticated Endpoints Require RSA Signing — Not Configured

| Field | Detail |
|-------|--------|
| Issue ID | KI-020 |
| Severity | MEDIUM |
| Category | Infrastructure / authentication gap |
| Description | `VENUE_API_KEY` in `.env` is the Kalshi API key ID (36 chars). Kalshi's authenticated endpoints (`/portfolio/balance`, order submission, etc.) require RSA request signing: `KALSHI-ACCESS-KEY` header + `KALSHI-ACCESS-SIGNATURE` (RSA-SHA256 over timestamp+method+path). No private key file exists in the project. Current `KalshiMarketClient` uses Bearer token auth which works for public endpoints (`/exchange/status`) but returns HTTP 401 + `"signature is missing from headers"` on authenticated endpoints. |
| Impact | (1) Cannot programmatically confirm Kalshi portfolio balance. (2) Order submission to Kalshi (live or demo) requires RSA infrastructure that does not exist. (3) `paper_trader.py` is LOCAL-ONLY — no Kalshi demo integration — so this is non-blocking for paper trading. Becomes blocking when live order submission is required at G6+. |
| Workaround | Confirm Kalshi account balance via web UI. Paper trading operates entirely locally via `paper_portfolio.json`. |
| Blocks gate | Non-blocking for G6 (paper trading is local). Blocks live order submission — must be resolved before any real-money execution. |
| Resolution path | (1) Generate RSA key pair via Kalshi dashboard; store private key outside VCS, reference via `VENUE_PRIVATE_KEY_PATH` env var. (2) Add RSA signing middleware to `KalshiMarketClient`. (3) Add `get_balance()` and `submit_order()` methods. New ADR required before order submission is wired into any pipeline. |
| Registered | 2026-05-31 |
| Status | RESOLVED 2026-05-31 — T-111/T-112 complete. Root cause was wrong base URL (`api.elections.kalshi.com` → `external-api.demo.kalshi.co` for demo). RSA-PSS signing was correct throughout. `_kalshi_base_url()` now reads BOT_ENV; private key at `VENUE_PRIVATE_KEY_PATH` on VPS. First live demo order executed (Order 363c5f5b). Balance confirmed: `$1,000.00`. |

---

### KI-021 — sklearn Version Mismatch: Trained 1.4.2 / Inference 1.8.0

| Field | Detail |
|-------|--------|
| Issue ID | KI-021 |
| Severity | LOW |
| Category | Infrastructure / version drift |
| Description | Model `v1-28483b21` was trained with scikit-learn 1.4.2. VPS venv runs sklearn 1.8.0. Health check flags this as a WARN. The mismatch is real — training and inference environments differ. |
| Investigation | 2026-06-01: Direct probability comparison run. 205 test vectors (200 random + 5 boundary cases) generated locally (1.4.2) and scored on VPS (1.8.0) using the same serialized pipeline. Results: max_abs_delta = 0.00106 (< 0.1% probability point); median_abs_delta = 0.00022; zero cases where \|delta\| > 0.02 (MIN_EDGE threshold); zero bet direction flips at realistic mid-prices (0.45–0.60). The LogisticRegression+Platt pipeline is numerically stable across this version gap. Differences are floating-point implementation noise, not calibration drift. |
| Impact | Negligible. No bet would change direction or cross the edge approval threshold due to the version gap. ECE 0.0342 calibration guarantee from ADR-0004 is not materially affected. |
| Workaround | None required at current severity. VPS venv should be pinned to 1.4.2 at next infrastructure refresh to eliminate the gap entirely. |
| Blocks gate | Non-blocking. |
| Resolution path | Pin `scikit-learn==1.4.2` in VPS venv at next deployment or model refresh. Requires no code change — venv rebuild only. T-072 (model refresh before 2026-27) is the natural resolution point. |
| Registered | 2026-06-01 |
| Status | LOW risk — investigated and cleared 2026-06-01. Resolve at T-072. |

---

### KI-022 — Single Threshold Per Player: run_paper_trade.py Suppresses ~7-8× Throughput vs. Design Intent

| Field | Detail |
|-------|--------|
| Issue ID | KI-022 |
| Severity | MEDIUM |
| Category | Throughput / architecture |
| Description | `run_paper_trade.py` line 290: `closest = min(player_mkts, key=lambda m: abs(m.threshold - pts_mean))` selects ONE market per player — the threshold closest to the player's rolling average. All other available threshold markets for that player are ignored. Kalshi offers ~7–8 threshold markets per player per game (confirmed: 38 markets fetched for 5 matched players in Finals pregame_20260531.json = 7.6 thresholds/player). The bot currently evaluates 1/7.6 of available market depth. |
| Impact | At current single-threshold behavior: Finals game yields 3–5 bets; regular season game yields ~3–10 bets. If all thresholds were evaluated: Finals game ~11–12 bets; regular season ~25–40 bets from T1 alone. This is a ~7-8× throughput suppression vs. design intent. At full design (all thresholds + T2/T3 + multi-stat), the gap grows to 100×. The 66-bet G6 floor is not crossed in regular season operation with single-threshold behavior; it is trivially crossed with all-threshold behavior. |
| Workaround | None — Finals constraint means low throughput is tolerable until regular season. Do not mask: this issue directly determines how quickly G6 evidence accumulates. |
| Blocks gate | Non-blocking for Finals. **Must resolve before 2026-27 regular season paper trading begins** — G6 evidence accumulation depends on it. |
| Resolution path | Replace line 290 single-select with a loop: evaluate EACH `player_mkts` entry as an independent signal. Idempotency check already uses `closest.ticker` per market — the pattern extends cleanly. Estimated change: ~15 lines. Requires test update. Designate as T-115. |
| Registered | 2026-06-01 |
| Status | ✅ RESOLVED 2026-06-01 — T-115 complete. `closest = min(...)` replaced with `for mkt in player_mkts:` loop. All thresholds evaluated as independent signals. 438/438 tests pass. |

---

## Resolved Issues

*Populated as issues are resolved.*

| Issue ID | Resolution Date | Resolution Summary |
|----------|----------------|-------------------|
| KI-008 | 2026-05-29 | EXP-016 run; HYP-009 CONFIRMED; Δ Brier = -0.0010 (gate < 0.012); playoff paper bets = full G6 evidence |
| KI-009 | 2026-05-29 | APR-0016 signed; G6 threshold revised 50 → 30 resolved bets; seasonal constraint formally acknowledged |
| KI-014 | 2026-05-30 | T-101 complete — root cause was relative `LOG_DIR` path causing cron to start fresh each run; fixed to `_SRC_ROOT / "logs"` absolute in `run_paper_trade.py` + `run_resolve.py`; idempotency logging added; deployed VPS; 3× legacy positions remain open and will resolve naturally |
| KI-015 | 2026-05-30 | T-100 complete — drawdown now computed from `total_realized_pnl` only, not bankroll depletion; DS sign-off granted same session; deployed VPS; kill switch confirmed cold at 0.00% realized drawdown |
| KI-016 | 2026-06-01 | ADR-0006: count gate deleted entirely — `max_concurrent_positions` removed from `_HARD_LIMITS`, `evaluate_forecast()` signature, CHECK 3 block, `run_paper_trade.py`, 2 tests, `RISK_APPETITE_CONSTRAINTS.md`, `EXECUTION_ARCHITECTURE.md`. Pipeline + Kelly + kill switch are the complete risk framework. No count primitive anywhere in the codebase. |
| KI-020 | 2026-05-31 | T-111/T-112 complete. Root cause was wrong base URL, not missing RSA infrastructure — RSA-PSS signing was correctly implemented. `_kalshi_base_url()` reads BOT_ENV; private key at `VENUE_PRIVATE_KEY_PATH=/root/.ssh/kalshi_bot.pem` on VPS; cryptography==43.0.3 installed. Balance confirmed $1,000.00. First live demo order executed (Order 363c5f5b). |
| KI-022 | 2026-06-01 | T-115 complete. `closest = min(player_mkts, ...)` replaced with `for mkt in player_mkts:` loop in `run_paper_trade.py`. Features computed once per player; all available Kalshi thresholds evaluated as independent signals through idempotency + C4 + PaperTrader. Restores ~25–40 bets/game regular season T1. 438/438 tests pass. |
| KI-012 | 2026-06-01 | T-091 complete. `check_portfolio_pnl()` added to `SystemMonitor`. L1 (≥5% loss of initial bankroll) → C6 INFO `pnl_alert_l1_watch`; L2 (≥10%) → C6 WARNING `pnl_alert_l2_loss`. Percentage-based thresholds scale correctly as bankroll changes. Wired into PIPE-03 and PIPE-03R. 8 new tests; 589/589 VPS tests pass. |

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
