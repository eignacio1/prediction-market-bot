# GG Ledger Triage — 2026-09-30 (T-590, PROPOSAL ONLY)

**Tier:** STANDARD. **Deliverable:** one triage proposal. Nothing here edits, archives, restatuses or acts on any gap entry. Read at origin/main 27f576a. Ambiguous entries are CARRIED by rule.

## D0 — Sync: BLOCKED
Shared-tree fast-forward of local main (before SHA 9f2b837; target origin/main, since moved from f293c0e to 27f576a) failed:
`Unable to create '.git/index.lock': File exists`. The lock is 0 bytes and held open by PID 25860 (macOS Virtualization XPC service), so it is live. I did not remove it. After SHA is unchanged (9f2b837). All reads used this worktree at origin/main. Needs the holder released, then `git merge --ff-only origin/main` in the shared tree.

## Counts (verified)
127 live entries. 108 carry Status token OPEN (includes GG-166, "OPEN — code fixed, ledger repair open"). 19 other: 9 PARTIALLY RESOLVED (7 plain, 2 with a suffix), 1 PARTIAL RESOLVE, 4 IN PROGRESS, 2 LIKELY RESOLVED, 1 ACCEPTED UNCERTAINTY, 1 PLAN ACCEPTED, 1 WATCH ITEM.
Classes: **BLOCKING 10 · CARRIED 111 · NOTED 6**.

## D1 — All 127 entries
| GG | Title | Status | Class | Reason |
|---|---|---|---|---|
| GG-004 | EV Validation Benchmark Was Never the Commercial Question | OPEN | CARRIED | G6 sample-adequacy blocker; per-band n* standard (APR-0024) not yet met. Real, unresolved. |
| GG-007 | T4/T5 Threshold Constants (T4_MIN_DELTA_P, T5_YES_CERTAINTY, T5_NO_CERTAINTY) Ar… | OPEN | CARRIED | T4/T5 threshold constants uncalibrated; low severity, nothing scheduled. |
| GG-014 | Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode | PARTIALLY RESOLVED | CARRIED | Partially resolved; residual 429 rate-limit behaviour still open. |
| GG-020 | Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts | ACCEPTED UNCERTAINTY | NOTED | ACCEPTED UNCERTAINTY; sole re-open trigger T-151 is gated on post-G6 real capital. Record-only. Nothing supersedes it. |
| GG-027 | PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Envi… | OPEN | CARRIED | PAM wiring absent for T2/T3/T5; no scheduled wave. |
| GG-037 | Calibration Collapse + Inverted Edge Realization: the Model's Edge Signal Is Ant… | OPEN | CARRIED | Anti-predictive edge finding; live methodology question, not gating a scheduled wave. |
| GG-038 | T4 Kill Switch SLA: 60s NFR-03 Is 12× Too Slow for Continuous T4 Evaluation | OPEN | CARRIED | Kill-switch SLA 12x too slow for T4; actively broken, no operator decision pending. |
| GG-039 | T4 Price Cache / Staleness Check Architecture | OPEN | CARRIED | T4 price-cache/staleness architecture open; design work unscheduled. |
| GG-040 | T4 Real-Time Data Sources: Required Feeds Not in Current C1 Architecture | OPEN | CARRIED | T4 real-time feeds absent from C1; unscheduled. |
| GG-041 | KXNBAPTS Orderbook Depth Data: Finals Window Missed; ADR-0005 Limit Empirical Ba… | OPEN | CARRIED | Finals depth window missed, NBA dark; unscheduled. |
| GG-045 | Maximum Effective Bankroll Constrained by Kalshi Market Depth: Capital Ceiling U… | OPEN | BLOCKING | Blocked-On-Operator flag: capital ceiling must be set before G6 live-bankroll/ADR-0005 limit revision. |
| GG-046 | T4 Commercial Validation: Independent Alpha Hypothesis Untested and Unregistered | OPEN | BLOCKING | Blocked-On-Operator flag: T4 commercial-validation track needs operator registration before any T4 verdict. |
| GG-056 | NBA Main Pool Dormant at 24.9% Drawdown; No Reactivation Plan Before October Res… | PLAN ACCEPTED | CARRIED | NBA reactivation plan accepted; due ~1 month before 2026-27 season, not scheduled now. |
| GG-060 | Silent Success Indistinguishability: Zero Bets from "No Edge" Looks Identical to… | IN PROGRESS | CARRIED | Silent-success indistinguishability; in progress, actively broken, not blocking a wave. |
| GG-064 | Kalshi DEMO Market open_time Lags LIVE for Same Ticker (Discovered During GG-063… | LIKELY RESOLVED | CARRIED | LIKELY RESOLVED but closure needs one confirmed post-fix T1 order; unverified, so CARRIED. |
| GG-066 | MLB C1 Has No Real-Time/Sub-Poll-Interval Event Feed (Blocks Event-Driven T4 Sub… | OPEN | CARRIED | No sub-poll MLB event feed; blocks only unbuilt event-driven T4 sub-bands. |
| GG-072 | T1 MLB (PIPE-05) HALTed by the Same GG-068 Bug On the Same Day, But Was Never Cr… | OPEN | NOTED | Own text records the data loss as permanently closed and the rule as landed in CLAUDE.md (incident-response section); Status token stale. Superseded by that rule. |
| GG-078 | T4 MLB's Real ~341-Bet/Day Cadence Means Kill-Switch Fate Is Decided Within ~15 … | OPEN | CARRIED | Kill-switch timing note; entry keeps both regimes live as a watch item, not superseded. |
| GG-091 | mypy --strict Full-Tree Baseline: 365 Pre-Existing Errors in 57 Files, Not Yet R… | PARTIAL RESOLVE | CARRIED | mypy --strict baseline debt partly remediated; ongoing. |
| GG-094 | MLB Has No Qualitative/PRF-Analogue Feature Layer Despite Being the Sole ACTIVE … | OPEN | CARRIED | MLB lacks qualitative feature layer; unscheduled. |
| GG-098 | MLB T1 Aggregate EV Metrics Are Cited as Milestones While Still Variance-Dominat… | OPEN | CARRIED | T1 EV milestones cited while variance-dominated; reporting discipline still open. |
| GG-105 | T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercil… | OPEN | CARRIED | T4M-PROJ tercile-monotonic anti-predictive pattern; APR-0025 proposal pending DS. |
| GG-121 | 2026-07-11 T1 MLB SemanticFloorViolation (games_fetched=16, matched_players=0) s… | WATCH ITEM | NOTED | WATCH ITEM; entry states no further action, recurrences get a fresh gap number. Record-only. |
| GG-124 | All four active MLB bands simultaneously clean_n=0/UNDERPOWERED, monitoring-cove… | OPEN | CARRIED | clean_n=0 dip believed self-resolved after epoch reset; not re-verified this wave. |
| GG-125 | C7 SystemMonitor's Brier/ECE drift-alarm ladder is never invoked from any produc… | OPEN | BLOCKING | Blocked-On-Operator flag: C7 drift-alarm wiring needs operator go-ahead. |
| GG-127 | 00_ADMIN/README.md (designated nav hub, ADR-0001) went ~7 weeks with zero update… | IN PROGRESS | CARRIED | Nav-hub README process gap; in progress. |
| GG-132 | MEMORY_BANK.md **Last reviewed:** narrative chain regrew unchecked 9→52 entries … | OPEN | CARRIED | MEMORY_BANK review chain regrowth; unresolved doc debt. |
| GG-133 | CHANGELOG.md has not been updated since 2026-05-30 despite ~2 months of major ch… | OPEN | CARRIED | CHANGELOG stale since 2026-05-30; unresolved doc debt. |
| GG-134 | mc_empirical_bootstrap.py's forward-risk projection has four unmodeled scope gap… | OPEN | CARRIED | Monte Carlo scope gaps undisclosed; open. |
| GG-136 | No standing archival cadence exists for 04_EXECUTION/TODO_NEXT.md's own ## T-NNN… | IN PROGRESS | CARRIED | No archival cadence for TODO_NEXT; in progress. |
| GG-137 | A1's holdout-Brier-optimal K=400 shrinkage candidate gives only ~7% weight to ac… | OPEN | CARRIED | K=400 shrinkage puts ~7% weight on player data; open modelling concern (renumbered twice). |
| GG-140 | GG-105 remediation exhausted the entire class of monotonic-transform recalibrati… | OPEN | CARRIED | GG-105 monotonic-transform class exhausted; open. |
| GG-143 | T4 MLB live engine goes silently blind to all in-progress games after any proces… | OPEN | CARRIED | T4 MLB blind after process restart; actively broken, HIGH. |
| GG-145 | park_factor_hits is hardcoded 1.0 across all 20,943 rows of the historical C2 fe… | OPEN | CARRIED | park_factor_hits hardcoded 1.0; open feature defect. |
| GG-146 | 8 pre-existing test failures in test_exp015_t3_simulation.py, traced to ADR-0048… | OPEN | CARRIED | 8 test failures from ADR-0048 zeroing; open. |
| GG-150 | Cross-book (T1 vs T4) opposite-direction conflicts are alarmed, not blocked; a b… | OPEN | CARRIED | T1/T4 opposite-direction conflicts alarmed not blocked; open. |
| GG-151 | merge=union does not guarantee dedup: identical content reaching both merge side… | OPEN | CARRIED | merge=union dedup not guaranteed; open. |
| GG-153 | T1's clean cohort is permanently frozen at clean_n=0 by the interaction of ADR-0… | OPEN | BLOCKING | Blocked-On-Operator flag: T1 clean cohort frozen at 0 by ADR-0048; needs operator reactivation decision. |
| GG-154 | Session-start protocol cannot verify CLAUDE.md's architectural claims against li… | OPEN | CARRIED | Session-start cannot verify CLAUDE.md claims against source; actively broken. |
| GG-156 | No forward price archive existed for any MLB market family before 2026-08-01; Ph… | OPEN | CARRIED | No forward price archive before 2026-08-01; historical, unrecoverable, still constrains Phase 2. |
| GG-157 | paper_trader.py has zero orderbook/depth/fill validation; every paper fill (incl… | OPEN | CARRIED | paper_trader has no depth/fill validation; open. |
| GG-158 | Price archive had zero off-VPS copies for 3+ sessions despite repeated "verified… | OPEN | CARRIED | Price archive off-VPS copy gap; open. |
| GG-160 | Four file:line citations across three Phase 0/1 docs had drifted from source wit… | OPEN | CARRIED | Four drifted file:line citations; open. |
| GG-159 | PROJECT_ASSESSMENT_2026-07-30's T4M-PROJ headline reconstruction didn't match th… | OPEN | CARRIED | Assessment headline did not match code; open. |
| GG-161 | 22 stuck T1/T2 aged_open positions: OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md's … | OPEN | CARRIED | 22 stuck T1/T2 positions; actively broken. |
| GG-162 | GG-NNN numbers picked mid-session have no atomic reservation, unlike T-/ADR- ran… | OPEN | CARRIED | No atomic GG-number reservation; three logged collisions (GG-187, GG-197 and one more). |
| GG-164 | T4 MLB cycle log's game_date field is wrong on 70% of all rows (45,217/64,396): … | OPEN | CARRIED | Cycle-log game_date wrong on 70% of rows; open. |
| GG-165 | 38/46 live gap entries carry no explicit Severity (UNSPECIFIED); full backfill d… | OPEN | CARRIED | Severity backfill deferred; title count stale. |
| GG-166 | run_resolve_mlb.py consumes the same corrupted game_date field GG-164 documented… | OPEN — code fixed, l | CARRIED | CRITICAL; code fixed, ledger repair open. |
| GG-167 | deploy.yml's dirty-tree guard only inspects tracked files; an untracked-file col… | OPEN | CARRIED | deploy.yml dirty-tree guard ignores untracked files; low. |
| GG-168 | Step 4's T4 cycle-log write-recency probe (GG-163/T-429) has no exemption for "d… | OPEN | CARRIED | Step 4 probe lacks budget-exhaustion exemption; false-alarm risk. |
| GG-170 | MLB Stats API gameLog date-label is transiently unstable in near-real-time; a de… | OPEN | CARRIED | CRITICAL; MLB gameLog date-label instability; open. |
| GG-172 | MARKET_EXPANSION_ACTION_PLAN.md Phases 1-4 are written entirely in market-type t… | OPEN | CARRIED | Action plan Phases 1-4 in market-type terms only; HIGH, open. |
| GG-174 | PolymarketVenueAdapter._parse_market()'s CLOB query hardcodes "tag": "nba" (KI-0… | OPEN | CARRIED | Polymarket adapter hardcodes nba tag; latent until KYC. |
| GG-177 | session_end_prep.sh's Step 0 SESSION_CLAIMS.md lookup matches on the worktree br… | OPEN | CARRIED | session_end_prep claim lookup mismatch; low. |
| GG-182 | Session-end token/time cost is unaddressed by Hard Rule 8's 60% trigger — second… | OPEN | CARRIED | Session-end cost unaddressed; open. |
| GG-183 | Per-cell kill-switch state (ADR-0053 §2.3/§6.3 item 4) has a store and a resolut… | OPEN | CARRIED | Per-cell kill-switch state lacks wiring; low. |
| GG-184 | open_position()'s market_type parameter defaults silently; 100% of live call sit… | PARTIALLY RESOLVED | CARRIED | market_type default silent; partially resolved. |
| GG-185 | 532 closed T4M-PROJ epoch-12 positions carry a ticker-vs-game_date mismatch desp… | PARTIALLY RESOLVED | CARRIED | 532 positions with date mismatch; partially resolved, CRITICAL. |
| GG-186 | SESSION_CLAIMS.md closure rows for T-458 and T-460 asserted "CLOSED" from local … | PARTIALLY RESOLVED | CARRIED | Closure rows asserted from local state; partially resolved. |
| GG-187 | T2's gross-edge formula is known but epoch-conditional; unsafe to backfill into … | OPEN | CARRIED | T2 gross-edge formula epoch-conditional; low. |
| GG-188 | T-463 (team runs-scored outcome store for archived KXMLBTOTAL game-events, Phase… | PARTIALLY RESOLVED | CARRIED | Outcome store for archived totals; partially resolved. |
| GG-189 | T-465 register-and-stop: 46 stuck-open T4M-PROJ epoch-12 positions, 76 rejected-… | OPEN | CARRIED | 46 stuck-open positions, 76 rejected; HIGH, open. |
| GG-192 | C4 tracks exposure at exactly two granularities (single bet-evaluation, whole po… | OPEN | BLOCKING | Blocks ADR-0053 §2.5 correlation-group authorization (queue "Needs your decision"): concurrent bets modelled independent. |
| GG-195 | 14 untracked nav-adjacent files sitting in the shared main working tree, unclaim… | OPEN | CARRIED | 14 untracked nav-adjacent files in shared tree; low. |
| GG-196 | Outage-window (08-04..08-07) sub-bucket of the repaired epoch-12 cohort shows an… | OPEN | CARRIED | Outage-window P&L anomaly; unexplained. |
| GG-190 | T-471: the step-function onset of GG-185's game_date corruption (0/77 mismatched… | OPEN | CARRIED | Onset of game_date corruption unexplained; HIGH. |
| GG-198 | Three sport-axis questions are unanswered ahead of Phase 3's cell-key work: no s… | OPEN | CARRIED | Three sport-axis questions ahead of Phase 3; open. |
| GG-200 | ACTIVE_QUEUE.md Block G cites GG-194 as its tracking gap; no GG-194 exists in th… | OPEN | CARRIED | Queue cites nonexistent GG-194; needs fix. |
| GG-202 | T4's 45s poll cadence was tuned against MLB/NBA's near-continuous state progress… | OPEN | CARRIED | 45s poll cadence vs NFL; unscheduled. |
| GG-203 | T4M-PROJ has approved zero bets to execution since 2026-08-15T00:06:20Z: every K… | PARTIALLY RESOLVED ( | CARRIED | T4M-PROJ zero approvals since 2026-08-15; partially resolved. |
| GG-206 | t4_mlb_totals_outcome_store.jsonl (and its sibling t4_mlb_outcome_store.jsonl) a… | OPEN | CARRIED | Outcome stores gitignored; open. |
| GG-204 | ADR-0028's G6 closure condition is unclosable as written: it is scoped to T1, an… | OPEN | BLOCKING | Blocks G6 closure: ADR-0028 condition unclosable as written; needs operator re-scope/supersession. |
| GG-216 | Venue registry tracked "CA eligibility" but never account-level geo/IP jurisdict… | OPEN | CARRIED | Kalshi account-level geo/IP jurisdiction untracked; open. |
| GG-217 | No Kalshi series exists for an NHL team-total market; the four-family coverage t… | OPEN | CARRIED | No NHL team-total Kalshi series; coverage target cannot close that cell. |
| GG-218 | T1 has no automated alarm for a position stuck OPEN past a plausible resolution … | OPEN | CARRIED | No stuck-open alarm for T1; low. |
| GG-209 | MLB T1 has no force-close/flatten mechanism for open positions; a kill-switch tr… | OPEN | CARRIED | No force-close for T1 positions; open. |
| GG-221 | HYP-010 Phase 2 plan defines a reroute for FALSIFIED and none for INCONCLUSIVE; … | OPEN | CARRIED | HYP-010 lacks INCONCLUSIVE reroute; low. |
| GG-224 | Live systemd services holding an in-memory ledger copy silently revert external … | OPEN | CARRIED | Services revert external ledger repairs; open. |
| GG-228 | Scheduled batch regeneration of a derived ledger file silently overwrites an ext… | OPEN | CARRIED | Batch regeneration overwrites repairs (header holds GG-226 body, anomaly). |
| GG-226 | NFL/NHL T4 sub-band decomposition blocked by SCOPE FENCE: no namespace-valid Exe… | OPEN | CARRIED | NFL/NHL T4 decomposition blocked by scope fence; unscheduled. |
| GG-229 | TestPromoteCellStatus RULED_OUT fixtures leak global registry state via del inst… | OPEN | CARRIED | Test fixtures leak registry state; low. |
| GG-234 | Task assignment named T-508 / GG-231 for new work; both IDs were already consume… | OPEN | CARRIED | Brief used consumed T-508/GG-231; proposes a planning-side check, so an action remains. |
| GG-230 | MEMORY_BANK.md's "Compass OS Health" single-line field is 5159 chars, 1.7x the s… | OPEN | CARRIED | MEMORY_BANK health line 5159 chars; low. |
| GG-233 | Task briefing restated ADR-0056 D2 as adopting the superseded T4N- convention, n… | OPEN | CARRIED | Brief misstated ADR-0056 D2; not verified as fully corrected. |
| GG-232 | ADR-0054(a) staffing gap: three named-not-staffed follow-ons (replay-harness mar… | IN PROGRESS | CARRIED | ADR-0054(a) three unstaffed follow-ons; in progress. |
| GG-235 | 04_EXECUTION/LEDGER_INVARIANT_SUITE.md's documented VPS-fetch commands reference… | OPEN | CARRIED | LEDGER_INVARIANT_SUITE fetch commands stale filenames; low. |
| GG-240 | ADR-0062's T-512 sign-off is recorded only on an unlanded branch; three merge ro… | OPEN | BLOCKING | Blocks ADR-0062 citation: sign-off only on an unlanded branch; operator must route it. |
| GG-243 | T-number collision: "T-518" independently claimed by two unrelated tasks (TODO_N… | OPEN | CARRIED | T-518 collision; proposes claim_session check, so an action remains. |
| GG-244 | Operator task brief's T4-segment count (11 segments / eight kelly_fraction regim… | OPEN | NOTED | Entry states "No further action needed"; corrected 13/6 figures already in ADR-0063 §2 Tier 3. |
| GG-253 | No NFL C1 ingestion module exists; the only generic team_stats_store.py is NBA-s… | PARTIALLY RESOLVED | CARRIED | No NFL C1 ingestion module; partially resolved, HIGH. |
| GG-254 | No moneyline/categorical-outcome settlement logic exists anywhere in src/, for a… | PARTIALLY RESOLVED | CARRIED | No moneyline settlement logic; partially resolved, HIGH. |
| GG-255 | measurement_stake.py defines all nine ADR-0058 T1 game-market cells but has exac… | LIKELY RESOLVED | NOTED | Entry itself says LIKELY RESOLVED; remaining surface split into separate scoped follow-ons (cron/model/settlement). |
| GG-256 | scripts/claim_session.sh's rebase-retry did not prevent a duplicate T-number cla… | OPEN | CARRIED | claim_session rebase-retry did not prevent duplicate claim; open defect. |
| GG-257 | settle_position()'s boolean win/loss model cannot express Kalshi's $0.50/$0.50 s… | OPEN | CARRIED | Boolean settle cannot express $0.50 split payout; low. |
| GG-258 | Task brief pre-assigned EXP-026/HYP-011 to a new NFL moneyline-LR experiment, bu… | OPEN | CARRIED | No atomic reservation for EXP-/HYP- numbers; systemic gap remains. |
| GG-260 | Shared main working tree carries uncommitted ACTIVE_QUEUE.md drift invisible to … | OPEN | CARRIED | Shared main tree carries uncommitted ACTIVE_QUEUE drift. |
| GG-261 | T-528's capture-fidelity "zero coverage gaps" verdict tested kickoff-instant cov… | OPEN | CARRIED | Capture-fidelity verdict tested kickoff instant only. |
| GG-262 | Live VPS crontab's run_mlb_pregame.py schedule (20 21 * * *) diverges from repo … | OPEN | CARRIED | VPS crontab diverges from repo deploy config; low. |
| GG-266 | Local dev machine's system Python (3.9.6/LibreSSL 2.8.3) cannot TLS-handshake wi… | OPEN | CARRIED | Local Python cannot TLS to ESPN; low, dev-only. |
| GG-269 | pmbot-web-dashboard.service is in an active OOM crash-loop under its 128MB cgrou… | OPEN | CARRIED | Dashboard OOM crash-loop; HIGH, open. |
| GG-275 | lib_chain_archive.py silently discards the prior "Last reviewed" line on every s… | OPEN | CARRIED | lib_chain_archive discards prior Last-reviewed line; open. |
| GG-279 | A code fix landing (and even fully migrating on-disk state) in a long-running se… | OPEN | CARRIED | Landed fix not active in long-running service; open. |
| GG-281 | EXP-027/HYP-012 re-run (2026-09-15): still UNDERPOWERED; task premise of "Weeks … | OPEN | NOTED | Entry states "No follow-up action required… closes on read". Disclosure only. |
| GG-282 | Investigation: do the two new T1 game-market run scripts inherit the live $10 mi… | PARTIALLY RESOLVED ( | CARRIED | min_bet_usd inheritance investigation; partially resolved. |
| GG-285 | At observed effect sizes, APR-0024's per-band P&L n* is 10-11 NFL seasons (NFL m… | OPEN | CARRIED | n* is 10-11 NFL seasons; gate unreachable at observed effect; open, not blocking a wave. |
| GG-288 | session-end close-out fix (closure-row-push + stray-branch-sweep) sat on local m… | OPEN | CARRIED | Close-out fix sat unpushed; resolution not verified. |
| GG-289 | Auto-mode classifier's Self-Modification block on .claude/commands/session-end.m… | OPEN | CARRIED | Classifier block on session-end.md; a permission control, must not be worked around. |
| GG-292 | 14 stray remote session branches (2026-08-24 through 2026-09-15) unlanded; sweep… | OPEN | BLOCKING | Blocks branch routing: nine of the stray branches need operator keep/kill (queue item "17-branch routing"). |
| GG-295 | Live NFL T1 portfolio's kalshi_threshold backfill (all 42 positions) has no corr… | OPEN | CARRIED | NFL kalshi_threshold backfill has no provenance record; HIGH. |
| GG-296 | T4M-PROJ's shard-3 demand figure (~2,000 approvals/$1,907.85 stake, 2026-09-20) … | OPEN | CARRIED | Shard-3 demand figure is ring-buffer artefact; HIGH. |
| GG-297 | 139 of 140 T4M-PROJ "OPEN" positions in paper_portfolio_mlb_t4.json (all dated 2… | OPEN | CARRIED | 139/140 T4M-PROJ OPEN positions stale; HIGH. |
| GG-298 | rejected_positions field name implies risk-engine declines but actually holds po… | OPEN | CARRIED | rejected_positions name misleads; medium. |
| GG-299 | ADR-0046's ECE baseline (0.0680, n=261) drifts +22% relative (to 0.0832) when it… | OPEN | CARRIED | ECE baseline drifts +22% on exact recompute; low. |
| GG-300 | 731 of 765 rows (95.6%) in T4M-PROJ epoch-12's clean cohort — the project's sole… | OPEN | BLOCKING | Blocks APR-0035: sole G6 calibration cohort 95.6% unverified; operator must choose what to accrue toward. |
| GG-301 | T4M-PROJ's calibration headline reverses sign and turns net-negative when restri… | OPEN | CARRIED | T4M-PROJ headline reverses sign on Kalshi-confirmed subset; HIGH. |
| GG-302 | (headerless title) | OPEN | CARRIED | Headerless-title entry; HIGH cohort-integrity item. |
| GG-303 | 395 of 731 T4M-PROJ NOT_RETRIEVABLE rows (54.0%) share a kalshi_ticker with anot… | OPEN | CARRIED | Fabricated-id rows; forward fix authorised 2026-09-28, existing 395 rows unrepaired. |
| GG-304 | kalshi_order_status field reads "submitted" uniformly across both confirmed-FILL… | OPEN | CARRIED | kalshi_order_status reads submitted uniformly; medium. |
| GG-305 | session_guard.sh's Compass OS Health length-threshold check has been failing aga… | OPEN | CARRIED | session_guard length check failing; low. |
| GG-306 | CLAUDE.md's coverage-target framing ("~25/30 cells") is never reconciled against… | OPEN | CARRIED | Coverage-target framing unreconciled with registry; low. |
| GG-307 | build_t4mlb_cohorts's edge-reconstruction formula has never been tested against … | OPEN | CARRIED | Edge reconstruction untested on T4M_ARITH; low. |
| GG-308 | scripts/close_session_claim.sh pushes the entire branch tip to origin/main via g… | OPEN | CARRIED | close_session_claim pushes whole branch tip to main; medium. |
| GG-309 | CLAUDE.md Step 4's SemanticFloorViolation grep (T1 MLB silent-failure detector) … | OPEN | CARRIED | Step 4 SemanticFloorViolation grep lacks recency window; medium. |
| GG-312 | Register-parity failure class: 36 accepted ADRs accumulated with no APPROVALS_RE… | OPEN | BLOCKING | Blocks ADR-0063: accepted ADRs lack APPROVALS_REGISTER signature rows; operator signature pending. |
| GG-316 | A T1 NFL run cannot be attributed to an actor: approval_commit is a static epoch… | OPEN | CARRIED | NFL run not attributable to an actor; HIGH. |
| GG-317 | The T1 NFL run script defaults to the fixed-p STUB model and will open one paper… | OPEN | CARRIED | NFL script defaults to fixed-p stub model; medium. |

Anomalies observed, not fixed: GG-228's header holds a GG-226 body; GG-137 was renumbered twice; GG-302 has no title in its header; GG-165's title carries a stale "38/46" count; GG-072's own text says closed while Status is OPEN.
Caveat: reasons are drawn from titles, status lines, flags and the tails of entries, not a fresh re-verification of each claim against live data.

## D2 — Section 0 reconciliation (169 overdue)
Section 0 sums seven buckets: `retirement_debt + landed_branches + prunable_wt + no_row_findings + open_claims + shared_behind_n + wave_fences`. Console snapshot: 0 + 31 + 0 + 5 + 132 + 1 + 0 = 169.
- **open_claims (132) is the inflated bucket.** In my live read it was 134. The detector uses `startswith("CLOSED")`, so bold `**CLOSED` rows read as unclosed. 34 are definite false positives (32 bold CLOSED rows, plus T-562 and T-580). 25 more are probable false positives. 72 are unknown. 3 are genuinely in flight. So roughly 34 to 59 of the 132 are not debt, and about 72 cannot be judged from the claims file alone.
- **landed_branches (31 in snapshot, 34 live):** real debt. Three claim-and-branch pairs overlap open_claims (T-566, T-573, T-580), a small double count.
- **no_row_findings 5, shared_behind_n 1:** real. shared_behind is the same condition as D0.
- **retirement_debt, prunable_wt, wave_fences: 0.**
- Sections 1-3 total 124 against 127 live entries; Section 0 is a snapshot and lags.
Conclusion: 169 overstates debt mainly through the claims detector. The console was not regenerated or patched.

## D3 — Branch sweep
Report-only first: 33 landed local branches listed, 21 unlanded remote branches listed, current branch skipped. Confirmed `git branch -d` only, ancestors of origin/main only. No non-ancestor was touched, so no sweep bug to report. Then `--execute`.
- **Deleted: 1** — session/20260929T052119Z-absent-attribute-pricing.
- **Left standing: 32 of the 33.** 28 are checked out in other worktrees, so git refused. 4 are refused because they are not merged to their own upstream: land-b, nfl-capture-rebase, session/20260826T045926Z-t497-t1-flat-stake-wrapper, session/20260923T005823Z-efficiency-gradient-ranking. I did not use -D.
- This worktree's branch was skipped as current. No unmerged branch was deleted, merged, rebased or cherry-picked. The unmerged branches remain for operator keep/kill.
- Most of the sweep is blocked by worktrees. The 28 need `git worktree remove` by their owners first, which I did not do.

## D4 — The rate
Method: first appearance of each `### GG-N` header in the live log (registered) or the archive (archived), by commit date on origin/main. "Wave" is approximated by active commit day, since the history has no wave marker I can rely on.
- Last 10 active days (2026-09-14 to 2026-09-28): **32 registered, 27 archived**, ratio 1.19 registered per archived. Registration is about 3.2 per day.
- Archival is one lump: 25 of the 27 landed in the single 2026-09-28 burndown. Outside it: 32 registered, 2 archived.
- All time: 270 registered, 153 archived, 127 live. 270 minus 153 is 117, not 127, so 10 ids do not reconcile by header count. Not resolved here.
- **Time to clear:** at the observed net rate the log does not clear. Registration has run at or above archival. With zero new registrations, 127 at the observed 2.7 archived per day would take about 47 active days, and that rate is driven by one batch.

## D5 — What I would ask the operator to sign off on (NOTED, approve or reject each)
Approving archives nothing by itself. It only authorises a later status change by the owner of the log.
1. GG-020 — ACCEPTED UNCERTAINTY; re-open trigger T-151 is post-G6.
2. GG-072 — own text records closure; rule landed in CLAUDE.md.
3. GG-121 — WATCH ITEM; entry says no further action.
4. GG-244 — entry says no further action needed.
5. GG-255 — entry says LIKELY RESOLVED; remainder split into follow-ons.
6. GG-281 — entry says closes on read.

BLOCKING list for decision: GG-045, 046, 125, 153, 192, 204, 240, 292, 300, 312.
