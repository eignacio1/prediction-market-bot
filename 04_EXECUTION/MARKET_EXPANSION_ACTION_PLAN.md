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
- [x] **0.9** Depth sample per family (`phase0_market_survey.py depth`) — 8 families × 20 markets sampled live via VPS (`exp_output/PHASE0_SURVEY/depth_sample.json`, `2026-07-31T20:13:03Z`). **PRE-SLATE — superseded as the sole basis for any verdict.** A mid-slate resample (`depth/depth_midslate_20260803T233850Z.json`, `2026-08-03T23:40:53Z`, T4M-PROJ live) plus a targeted `KXMLBHIT`-only resample now exist; see `exp_output/PHASE0_SURVEY/MIDSLATE_VERDICT.md` (Phase 0-G, T-411).
- [x] **0.10** §2.7 gate verdict per family, at **$10.00 floor (10 × $1.00 stake)** — corrected: this checkbox previously read "$1,000 floor," which is arithmetically wrong (10 × $1.00 = $10.00, not $1,000) and never matched the implemented gate (`DEPTH_GATE_MULTIPLE=10.0 × DEFAULT_INTENDED_STAKE_USD=1.00`) or the reported results. Verdict per family in `exp_output/PHASE0_SURVEY/SURVEY_TABLES.md` Table 3, **as measured pre-slate**: PASS — `GAME_WINNER`, `PARTIAL_GAME_WINNER`, `TEAM_TOTAL`, `UNCLASSIFIED`; **FAIL** — `GAME_TOTAL`, `PLAYER_PROP` (incl. KXMLBHIT/HR/RBI/KS — see GG-155), `RUN_LINE`, `SEASON_WIN_TOTAL`. **CORRECTION (Phase 0-G, T-411, 2026-08-03):** the pre-slate `PLAYER_PROP` sample never actually contained `KXMLBHIT` — both this run and the mid-slate resample independently pulled the identical 20 `KXLEADERMLBHITS-26-*` tickers (a season leaderboard series) and zero `KXMLBHIT` tickers, a per-family sampling gap in `cmd_depth()` (no per-series balancing; `KXLEADERMLBHITS` alone exceeds the 20-per-family cap). A direct targeted sample of `KXMLBHIT` itself (20/20 currently-open markets, 2026-08-03) is 20/20 usable, 0.5-1.0c half-spreads, **$4,313.72 median depth — 431x the gate floor, PASS**. `KXLEADERMLBHITS`'s FAIL stands on its own thin-book merits but is not a KXMLBHIT verdict. Mid-slate also flipped `GAME_WINNER`, `PARTIAL_GAME_WINNER`, `TEAM_TOTAL` from PASS to FAIL — not settled from one point each in either direction; see `MIDSLATE_VERDICT.md` for the full delta table and FAIL-NOBOOK/FAIL-WIDE split. **Third sample point (00:04Z, same session):** a second targeted `KXMLBHIT` run confirms PASS (20/20 usable, 0 NOBOOK/WIDE) but median depth dropped ~14x to $304.685 — still 30x the floor, but the magnitude is volatile, not stable. `GAME_WINNER`/`PARTIAL_GAME_WINNER` now FAIL on 2/3 points (most recent two agree); `TEAM_TOTAL` is 2 PASS/1 FAIL with the two PASS points disagreeing ~67x — unsettled. Full 3-point table in `MIDSLATE_VERDICT.md`.
- [x] **0.11** `VENUE_REGISTRY.md` updated — tier (marked demo-sourced), $25,000/contract position limit, measured depth by family; corrects CLAUDE.md's unsourced "$500-$2,000" KXMLBHIT depth claim (GG-155, OPEN — CLAUDE.md itself still not corrected as of Phase 0-G/T-411: two targeted `KXMLBHIT` resamples now exist, ~14 min apart — $4,313.72 then $304.685, a ~14x swing — both decisively PASS (30x/431x the floor) but not stable in magnitude. Per the operating instruction for this box, a fixed dollar figure is not swapped in unless stable across two runs — it is confirmed-PASS but not stable, so CLAUDE.md remains uncorrected; flagged for operator review with both figures in hand, see GG-155 and `MIDSLATE_VERDICT.md`)
- [x] **0.12** Phase 0-A branch `session/20260731T152256Z-phase0a-raw-capture` merged to main
- [x] **0.13** Q1–Q6 "ARE WE COMPROMISED" adversarial review (owed from the Phase 0-A session) — completed 2026-07-31; Q1/Q4/Q5 confirmed limits and interfaces trace cleanly to current source (GG-144's fixes hold); Q2 stub scan CLEAN; top Q6 concerns registered as GG-152/153/154/155 (see `GOVERNANCE_GAP_LOG.md`)

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

## Phase 0-C — Unattended depth accumulation (weekend cron)

**Context:** GG-155's 0.9 sample (`2026-07-31T20:13:03Z`) was taken pre-slate, not during T4M-PROJ's live in-play window (~23:00-04:00Z) — a timing confound, not a dead-venue finding. This phase resolves that with a mid-slate-weighted cron. **Reprioritized mid-session 2026-07-31: T4's live cohort accrual (the only band placing bets, first out-of-sample GG-142 test) outranks the survey this weekend — confirming the cron/sampler cannot degrade T4 came first, ahead of building the cron itself.**

- [x] **0C.1** Precondition: `session/20260731T194108Z-phase0b-depth` merged to main (fast-forward, `b080e57`→`6fe40ed`) — both schema fixes (markets_by_series nesting, orderbook_fp decimal-dollar shape) on `main` before any cron references the script
- [x] **0C.2** Sampler paced to ≤4 req/s — `REQUEST_PAUSE_S` 0.12→0.30 (~8.3→~3.3 req/s), half of 0-B's rate per the safety directive
- [x] **0C.3** Confirmed sampler cannot touch T4 portfolio/ledger/logic_epoch files — `cmd_depth()`'s only I/O is its `--in`/`--out` CLI args under `exp_output/PHASE0_SURVEY/`; `kalshi_client.py`'s unauthenticated market-data path (`_get(..., authenticated=False)`, the sampler's default) sends no auth headers and its only filesystem access anywhere in the file is a *read* of the RSA PEM on the authenticated path, which the sampler never exercises
- [x] **0C.4** One manual `depth` run against live Kalshi from the VPS (`2026-07-31T20:59:31Z`) — non-empty, schema-valid output (8/8 families, 55.8KB); T4 showed 0 rate-limit hits, 0 staleness failures, 0 restarts, no journal errors during/after — confirms the fixed pacing doesn't degrade T4 in practice, not just on paper. Still pre-slate (21:00Z start); does **not** resolve the GG-155 timing confound by itself.
- [ ] **0C.5** `--refresh-markets` flag (or equivalent) — `markets_sample.json` is a frozen 2026-07-31 ticker list; over a weekend, markets resolve and re-sampling a stale list silently degrades. **Monday work.**
- [ ] **0C.6** Timestamped output accumulation (`depth/depth_<UTC>.json`, never overwrite) + running one-line-per-run index. **Monday work.**
- [ ] **0C.7** Crontab installed at mid-slate-weighted schedule (suggested 21:00/23:30/01:30/03:30 UTC), bounded (run cap or end time), verified via `crontab -l` + a confirmed first-fire. **Monday work — do not leave unbounded past Monday.**
- [x] **0C.8** Mid-slate sample (23:00–04:00Z) obtained and GG-155 updated against real in-play depth — done Phase 0-G (T-411), 2026-08-03T23:38-23:41Z. Single manual run (no cron built); superseded the pre-slate confound and, more consequentially, found the original sample never measured `KXMLBHIT` at all — see `MIDSLATE_VERDICT.md`. GG-155 updated, not fully closed (recommends operator review before any CLAUDE.md edit — see 0.11 below).

**Do not** (standing for this phase): do not start Phase 1/Phase 2; do not edit CLAUDE.md's $500–$2,000 depth figure until mid-slate data exists (0C.8); do not touch `execution_bands.py`, `risk.py`, `paper_trader.py`, or any sizing.

**Review follow-ups from 0-B (deprioritized to Monday, no decay):**
- [ ] **0C.9** Register new gap: `paper_trader.py` has zero orderbook/depth/liquidity references — fills assumed at mid, never validated against the book. Applies to the live T4 flat-$1 cohort now accruing. G6 precondition: no live-capital authorization while fill assumptions are unvalidated against production depth. Larger than GG-155 — GG-155 is a symptom of it.
- [x] **0C.10** Split `SURVEY_TABLES.md`/`VENUE_REGISTRY.md`'s FAIL column: FAIL-WIDE (book exists, spread wider than a nickel — e.g. GAME_TOTAL, 20/20 usable at $0.00 median) vs FAIL-NOBOOK (book largely absent — e.g. PLAYER_PROP, 3/20 usable). Different diseases, different fixes. — done Phase 0-G (T-411), applied to both pre-slate and mid-slate in `MIDSLATE_VERDICT.md`.
- [x] **0C.11** Drop UNCLASSIFIED from the depth-gate verdict table — heterogeneous bucket (NCAA basketball, esports leakage); reporting it as PASS is noise. — done Phase 0-G (T-411), excluded from `MIDSLATE_VERDICT.md`'s delta table per this instruction.
- [ ] **0C.12** Note in the gate table itself (not just the spec) that the $10.00 floor derives from the $1.00 ADR-0050 measurement stake and is not the live-capital floor — every verdict recomputes when sizing changes.

**Flagged for operator, Monday, analysis only — no action taken:** the families passing the depth gate (`GAME_WINNER` at $1,646 median) are exactly the ones the efficiency-gradient doctrine warns against, while the family the bot actually trades (`PLAYER_PROP`) fails a $10 bar. If mid-slate data (0C.8) confirms this shape, it may be the most consequential result Phase 0 has produced and needs an operator decision before Phase 1 commits to a build order.

---

## Phase 0-D — Mid-slate depth run (T-410, GG-155 timing confound)

**Context:** resolves 0C.5/0C.6/0C.8 above — same objective (mid-slate depth to distinguish TIMING ARTIFACT from STRUCTURAL FINDING for GG-155), executed 2026-08-01 rather than left for "Monday."

- [x] **0D.1** `scripts/phase0_refresh_markets.py` built + validated — `markets_sample.json` (2026-07-31 frozen capture) confirmed stale (125 KXMLBHIT open in the frozen file vs 606 refetched live 2026-08-01T22:38Z); re-fetches current `status=open` markets for all 220 known MLB-family series, full cursor pagination, same 0.30s pacing floor as the survey script. Committed `98834e4`.
- [x] **0D.2** Fresh refresh + `phase0_market_survey.py depth --per-family 20` run — completed Phase 0-G (T-411), 2026-08-03T23:38-23:41Z, T4M-PROJ live window. Market list refreshed to `markets_open_20260803T233850Z.json` (6,564 open markets, verified tonight's date substrings present before sampling); depth sample written to `depth/depth_midslate_20260803T233850Z.json`; t4-mlb confirmed active before/after, 0 anchored 429s.
- [x] **0D.3** Comparison table (0-B 20:13Z pre-slate vs mid-slate vs delta) + explicit TIMING ARTIFACT vs STRUCTURAL FINDING verdict for `PLAYER_PROP` — done, see `exp_output/PHASE0_SURVEY/MIDSLATE_VERDICT.md`. Verdict: the pre-slate `PLAYER_PROP`-family result was never a KXMLBHIT measurement at all (both runs sampled `KXLEADERMLBHITS` exclusively, a sampling-methodology gap, not a timing effect); a targeted `KXMLBHIT`-only resample is 20/20 usable at $4,313.72 median depth (431x gate).
- [x] **0D.4** FAIL-NOBOOK vs FAIL-WIDE breakdown applied to the mid-slate result (see 0C.10) — done, per-family split in `MIDSLATE_VERDICT.md`'s Table.

---

## Phase 0-E — Forward price archiver deployed (T-410, GG-156)

**Context:** no forward price archive existed for any MLB market family before this session (see GG-156). Phase 2's 2.7/2.8 gate needs historical Kalshi prices for `KXMLBGAME`/`KXMLBSPREAD`/`KXMLBTOTAL` that were never captured; MLB's regular season ends in early October, so any day this is not running is permanently lost input. Treated as the one irreversible-cost item on the board this session — deployed ahead of/alongside 0-D rather than deferred to Monday.

- [x] **0E.1** `scripts/archive_market_prices.py` read before deployment (was found untracked in the shared `main` tree, not the worktree, contradicting the initiating prompt's claim — verified directly per project's "verify external claims" rule before acting). Read-only, append-only, one JSONL/UTC day, hard 0.30s pacing floor enforced in-code (`SystemExit` if violated), zero-result GG-049 guard (exit 2 + stderr warning if all series return 0 markets).
- [x] **0E.2** Field-name bug found and fixed before trusting the archive: first manual run (2026-08-01T22:55Z, 2162 snapshots) had `yes_mid` populated in **0/2162** rows. Root cause: `SNAPSHOT_FIELDS` used plain names (`yes_bid`, `yes_ask`, ...); the live `/markets` response uses `*_dollars`/`*_fp` keys (confirmed via direct API read against KXMLBHIT) — the `if field in market` guard silently dropped every quote field. Fixed same-session (commit `6b687bf`), re-verified: 2170/2170 rows with `yes_mid` populated (100%), spot-checked non-degenerate (real bid/ask spreads, not 0.00/1.00 placeholders). Broken first-run file preserved as `prices_2026-08-01.jsonl.BROKEN_FIRSTRUN`, not deleted.
- [x] **0E.3** Deployed to `main` (`ada06eb`, `6b687bf`, `93efca2`) and pulled onto the VPS (`/opt/prediction-market-bot`).
- [x] **0E.4** Cron installed: `*/20 22-23,0-5 * * *` (two blocks, midnight-wrap), all 10 MLB families (`KXMLBGAME`, `KXMLBSPREAD`, `KXMLBTOTAL`, `KXMLBTEAMTOTAL`, `KXMLBF3`, `KXMLBF5`, `KXMLBF7`, `KXMLBF5SPREAD`, `KXMLBF5TOTAL`, `KXMLBHIT` as control). Registered in git-tracked `deploy/cron.conf` (commit `93efca2`) and installed to the live crontab (confirmed via `crontab -l`). First scheduled fire: 2026-08-01T23:20Z.
- [x] **0E.5** First scheduled cron fire confirmed (2026-08-01T23:20:02Z log line): `wrote 2170 snapshots -> exp_output/PRICE_ARCHIVE/prices_2026-08-01.jsonl`, file grew to 4340 total lines (2170 manual-verification run + 2170 this fire). Confirmed live on VPS 2026-08-01T23:28:31Z.
- [x] **0E.6** T4 safety checked before deploy AND after the first scheduled fire (2026-08-01T23:28Z): `t4-mlb` active, `NRestarts=0`, 0 recent (`tail -500`) `game_state_fresh` staleness failures, 0 anchored `"status_code": 429` hits in the same window, audit log timestamps current (23:27:40Z, post-fire). No degradation observed — archiver confirmed non-interfering with T4 in practice, not just by source-code inspection.
- [x] **0E.7** Governance gap registered — GG-156 (no forward price archive existed for any family as of 2026-08-01; Phase 2 gate input source never existed and cannot be backfilled; same absence limits GG-142 counterfactual analysis on bets not taken).

**Do not** (standing for this phase, per operator instruction): do not start Phase 1 or Phase 2; do not edit CLAUDE.md's depth figure; do not touch `execution_bands.py`, `risk.py`, `paper_trader.py`, or any sizing.

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
- [x] **S.2** Register `_kalshi_base_url()` misrouting bug — `BOT_ENV=ENV-03` silently routes to demo. **G6 precondition.** Registered as GG-152 (OPEN, unstaffed — fix requires operator sign-off, touches live-capital path).
- [ ] **S.3** Resolve `.env.example` inconsistency — venue keys documented as "ENV-02/ENV-03 only", capture ran under ENV-01 with keys set. Noted inside GG-152's entry as an unresolved sub-finding; **not itself resolved**, only documented.
- [x] **S.4** Register the frozen-span trap — T1's cohort is not "13 days from maturity," it is `clean_n=0` and structurally cannot self-heal under ADR-0048's zeroing + epoch-10 reset. Registered as GG-153 (OPEN, unstaffed).
- [x] **S.5** Register the Cowork Step-4 blind spot — no SSH route, protocol step silently skipped. Registered as GG-154 (OPEN, unstaffed).
- [x] **S.6** Register the protocol's inability to verify CLAUDE.md's architectural claims against source (3rd instance of the class). Registered as GG-154 (same entry as S.5 — the two are one combined finding).
- [ ] **S.7** Commit pending: `SEGMENTED_POOL_ARCHITECTURE.md` (modified), `scripts/phase0_market_survey.py`, `SURVEY_TABLES.md`, this file
