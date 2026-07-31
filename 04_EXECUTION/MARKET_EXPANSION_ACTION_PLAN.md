# Market Expansion — Action Plan (checkbox-tracked)

**Owner:** Operator (Earl) | **Started:** 2026-07-30 | **Last updated:** 2026-07-31
**Specs:** `02_ARCHITECTURE_DESIGN/MARKET_UNIVERSE_SURVEY_SPEC.md` · `02_ARCHITECTURE_DESIGN/SEGMENTED_POOL_ARCHITECTURE.md`
**Rule:** a box is checked only when the artifact exists and is committed. "Done in a session" is not done.

---

## Phase 0 — Market universe survey (BLOCKS everything downstream)

- [x] **0.1** Desk confirmation that Kalshi lists ML / run line / totals for MLB
- [x] **0.2** Venue compliance validation — rate limits, tiers, position limit, bot-use rules
- [x] **0.3** Survey spec written (`MARKET_UNIVERSE_SURVEY_SPEC.md`)
- [x] **0.4** Survey tooling written + validated (`scripts/phase0_market_survey.py`, syntax/CLI/stub-scan clean)
- [x] **0.5** Raw capture — `/series` unfiltered (12,355 series), `/markets` (220 MLB-looking, 226 paginated calls), `/account/limits`, manifest
- [x] **0.6** Environment routing resolved — market data is production-routed regardless of `BOT_ENV`; only `/account/limits` is demo-scoped
- [x] **0.7** Classifier run — Tables 1, 2, 4 generated (`exp_output/PHASE0_SURVEY/SURVEY_TABLES.md`)
- [x] **0.8** Hand review of the 103 unclassified MLB series (see § Findings below)
- [ ] **0.9** Depth sample per family (`phase0_market_survey.py depth`) — **VPS, needs auth**
- [ ] **0.10** §2.7 gate verdict per family, at $1,000 floor (10 × $1.00 stake)
- [ ] **0.11** `VENUE_REGISTRY.md` updated — tier (marked demo-sourced), $25,000/contract position limit, measured depth
- [ ] **0.12** Phase 0-A branch `session/20260731T152256Z-phase0a-raw-capture` merged to main
- [ ] **0.13** Q1–Q6 "ARE WE COMPROMISED" adversarial review (owed from the Phase 0-A session)

### Findings from 0.8 — hand review

**Target families confirmed, with tickers:**

| Family | Ticker(s) |
|---|---|
| Moneyline (full game) | `KXMLBGAME` |
| Run line | `KXMLBSPREAD` |
| Game total | `KXMLBTOTAL` |
| Team total | `KXMLBTEAMTOTAL` |

**New family the classifier missed — partial-game derivatives.** `KXMLBF3` / `KXMLBF5` / `KXMLBF7` (First 3/5/7 Innings Winner) carry no `GAME`/`WIN` substring and fell into UNCLASSIFIED. With `KXMLBF5SPREAD` and `KXMLBF5TOTAL` already classified, this is a complete winner/spread/total set at three innings cutoffs.

**Why this matters strategically:** partial-game lines are plausibly thinner and less attended than the full-game market — the efficiency-gradient target — while preserving the short-feedback-loop property that makes prediction markets the laboratory. **Add F3/F5/F7 to the depth sample (0.9) and treat them as first-class Phase 2 candidates, not an afterthought.**

**Also surfaced:** `KXMLBEXTRAS` (extra innings), `KXMLB500` (teams at .500), `KXMLBKS` (strikeouts — a player prop the `PLAYER_PROP` regex missed; `KS` is not in the pattern).

**Out of scope, correctly:** ~60 awards/futures series (MVP, Cy Young, ROTY, Gold Glove, division winners, World Series). Months-long resolution breaks the short-feedback-loop property. Do not add.

**Classifier leakage, both directions:** `KXNCAABBGAME` / `KXNCAABBSPREAD` / `KXNCAABBTOTAL` (NCAA basketball) and `KXEWCMLBB` (Mobile Legends esports) were caught by the MLB sport matcher. `KXWBC*` (World Baseball Classic) is real baseball but not MLB. The "220 MLB-looking" figure is a superset — treat it as a search space, never as a count.

---

## Phase 1 — Abstraction repair (no new markets)

- [ ] **1.1** Market-type registry built (`market_mapper.py` currently has no such thing)
- [ ] **1.2** `VenueAdapter` protocol generalized off `fetch_player_points_markets()`
- [ ] **1.3** `kalshi_client.py` series constants → registry-driven
- [ ] **1.4** `paper_trader.open_position()` signature generalized off `player_name`/`player_id`/`kalshi_threshold`
- [ ] **1.5** Per-band vig cascade (L460/462/464) extracted to per-market-type config
- [ ] **1.6** **GATE: bit-identical replay** — existing ledger replayed through refactored path produces byte-identical positions
- [ ] **1.7** Full suite green (baseline 2,757 passed / 17 known-failed / 28 skipped)
- [ ] **1.8** CLAUDE.md corrected — the market-type-registry claim and the efficiency-gradient departure

---

## Phase 2 — Team model, offline only — **RESEQUENCED 2026-07-31, see 2.1**

- [x] **2.1** EXP-013 verdict on `scoring_distribution.py` confirmed — **HYP-007 FALSIFIED, 2026-05-29**

  NB Brier **0.2671** vs LR **0.2461**, Δ=0.0210 against a 0.005 threshold. *"NB is NOT a drop-in replacement for LR on calibration."* Secondary finding retained it for **multi-line pricing from one distribution fit**, not primary forecasting. ADR-0004 (LR production) upheld.

  **Does the falsification transfer to team-level?** Not directly — EXP-013 tested *NBA player points*, a lumpy overdispersed individual count. Team runs aggregate over nine innings and nine-plus batters, a materially different distributional object plausibly better-behaved under Poisson/NB. **But it is a warning, not a green light**, and the burden is now on Phase 2 to demonstrate the transfer rather than assume it.

  **The binding consequence is a sequencing violation in this plan's own Phase 2.** `DECISION_LOG.md` 2026-05-29 (LL-009) records a standing rule created *by this exact experiment*: *"EXP-012 and EXP-013 falsified HYP-006 and HYP-007 after full infrastructure was built (TeamStatsStore, ScoringDistributionModel). Cost: ~3-5 hours stranded build. Rule: confirm hypothesis with minimal experiment before building supporting component."*

  Phase 2 as originally written (build C2 matrix → fit → score) built infrastructure before confirming the hypothesis — the precise pattern LL-009 forbids, against the precise component it was written about. Resequenced below.

- [ ] **2.2** **MINIMAL EXPERIMENT FIRST (LL-009).** Register a hypothesis (HYP-0NN: team run distributions are NB/Poisson-tractable and beat market-implied totals). Fit NB/Poisson to team runs-scored using `MLBTeamStatsStore`'s **existing** `get_opp_runs_scored`/`get_opp_runs_allowed` series — no new C2 matrix, no new ingestion. Score Brier against a historical `KXMLBTOTAL` price sample.
- [ ] **2.3** **GATE: does the minimal fit beat market-implied on Brier?** If FALSIFIED — stop. Phase 2 ends, no C2 build, ~zero cost. Record it as a real result.
- [ ] **2.4** Only if 2.3 passes: team-game C2 matrix from `MLBTeamStatsStore` + `MLBPitcherStatsStore`
- [ ] **2.5** `check_feature_column_health.py` wired in **before** first matrix generated (GG-141/GG-145 precedent)
- [ ] **2.6** Full team-level distribution fit
- [ ] **2.7** Scored offline against historical Kalshi prices via D1-style what-if harness
- [ ] **2.8** **GATE: does it beat historical closing prices offline?** If no — stop, zero live risk spent

**Note on model class:** if 2.3 falsifies NB/Poisson for team totals, that does not kill Phase 2 — moneyline is a binary target where LR (the production class, ADR-0004) applies directly and needs no distribution fit at all. A falsified 2.3 should reroute to moneyline-first, not terminate the phase.

---

## Phase 3 — Segmented pool infrastructure

- [ ] **3.1** Isolation option chosen in an ADR (Option 2 recommended — two live precedents at epochs 11/12)
- [ ] **3.2** Per-family ledger files
- [ ] **3.3** `execution_bands.BAND_CONFIGS` + `logic_epoch.bands_affected` entries
- [ ] **3.4** `run_band_monitor.BOOK_BANDS` + `run_power_calc.py` enumeration extended
- [ ] **3.5** Per-family kill switches (band-level must not halt other families)
- [ ] **3.6** Family-specific semantic oracles (`semantic_contracts.py`, 13 player-shaped refs)
- [ ] **3.7** **Cross-family correlated-exposure control** — GG-149's guard keys on identical ticker; ML/run-line/total on one game correlate with no string match
- [ ] **3.8** **GATE: isolation proven** — synthetic C4 change resets only intended families' `clean_n`

---

## Phase 4 — Activation

- [ ] **4.1** Shadow mode per family
- [ ] **4.2** Flat-stake measurement (ADR-0050 pattern)
- [ ] **4.3** Own `clean_n ≥ n*` per family

---

## Standing items (not phase-bound)

- [ ] **S.1** Epoch-12 live verification — `size_usd == $1.00` for entry price ≥ $0.10, `10 × entry_price` below; `t4_offsetting_suppressed` counts. **Clock-bound: needs a resolved slate.**
- [ ] **S.2** Register `_kalshi_base_url()` misrouting bug — `BOT_ENV=ENV-03` silently routes to demo. **G6 precondition.**
- [ ] **S.3** Resolve `.env.example` inconsistency — venue keys documented as "ENV-02/ENV-03 only", capture ran under ENV-01 with keys set
- [ ] **S.4** Register the frozen-span trap — T1's 13-day cadence span can never reach `MATURE_CADENCE_SPAN_DAYS=14` at zero sizing
- [ ] **S.5** Register the Cowork Step-4 blind spot — no SSH route, protocol step silently skipped
- [ ] **S.6** Register the protocol's inability to verify CLAUDE.md's architectural claims against source (3rd instance of the class)
- [ ] **S.7** Commit pending: `SEGMENTED_POOL_ARCHITECTURE.md` (modified), `scripts/phase0_market_survey.py`, `SURVEY_TABLES.md`, this file
