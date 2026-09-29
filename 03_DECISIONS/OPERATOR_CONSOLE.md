# Operator Console

> **GENERATED FILE — do not hand-patch.** Produced by `scripts/generate_operator_console.py` from `GOVERNANCE_GAP_LOG.md`'s live entries on every governance scan. Regenerated 124 open/in-progress entries into three sections, ranked by **blocks operator**, not severity. To change what appears here, fix the entry in GOVERNANCE_GAP_LOG.md or the classification regex in the generator script — never this file directly.

> **Severity debt:** 32/124 live entries have no explicit severity (`UNSPECIFIED`) — sort order below is unreliable wherever it relies on severity for entries not in this backfill's scope. See GG-165.

---

## 0. Overdue for retirement (175)

Artifact CREATION (session claims, gap registration) is mechanical and enforced. Artifact RETIREMENT (archiving resolved gaps, deleting merged branches, closing register rows) is manual and gets forgotten -- it does not scale across a growing gap log and, per direct enumeration (`ls -d [0-9][0-9]_*`), **13** top-level department directories -- not the 12 this rollup's originating task assumed; `09_INTEGRATION_PATCHES` and `09_SECURITY_PRIVACY_COMPLIANCE` share the `09_` prefix. This section is filing, never adjudication: everything below is something already marked done elsewhere that hasn't been filed away yet. Nothing here is deleted or archived by generating this file (T-570, 2026-09-23).

**Unarchived resolved gaps (0)** -- RESOLVED/CLOSED-AS-ARTIFACT entries still in the live GOVERNANCE_GAP_LOG.md instead of the archive (`scripts/retire_resolved_gaps.py`):
_None currently detected._

**Merged-but-undeleted local branches (26)** -- ancestors of origin/main, safe to `git branch -d` (`scripts/sweep_stray_branches.sh --execute`):
- `land-b`
- `nfl-capture-rebase`
- `session/20260811T043030Z-invariant-policy`
- `session/20260814T144536Z-replay-gate-band-coverage`
- `session/20260818T044631Z-phase2-team-outcomes`
- `session/20260820T005627Z-gg185-restart-trigger`
- `session/20260826T000519Z-t495-nhl-skeleton`
- `session/20260826T045926Z-t497-t1-flat-stake-wrapper`
- `session/20260827T013319Z-t499-phase-closeout`
- `session/20260828T002227Z-t502-adr0055-d2-stuck-open`
- `session/20260829T190241Z-t503-adr0055-d1-d3-repair`
- `session/20260903T184908Z-apr0033-accept-and-reroute`
- `session/20260907T234550Z-gg252-nfl-parser`
- `session/20260922T235033Z-gg291-live-settlement`
- `session/20260922T235038Z-calibration-model-vs-market`
- `session/20260923T005823Z-efficiency-gradient-ranking`
- `session/20260923T005826Z-mlb-final-week-accrual`
- `session/20260923T005837Z-vig-grounding-from-archive`
- `session/20260923T234404Z-ledger-integrity-audit`
- `session/20260923T234421Z-t4-latency-thesis`
- `session/20260924T045012Z-clv-harness`
- `session/20260924T045058Z-cohort-verification`
- `session/20260925T015621Z-feature-space-audit`
- `session/20260929T001556Z-t4-game-state-signal`
- `session/20260929T002124Z-gg303-activate-section0`
- `t493-closeout-push`

**Prunable worktree metadata (0)** -- `git worktree prune -v` dry-run output:
_None currently detected._

**ADRs/APRs missing register accountability (15)** -- `scripts/check_register_parity.py` rules 1, 2, and 5. Rule 1 requires EVERY APR to have its own row regardless of status (so a non-ACCEPTED APR like APR-0034/0035/0036, still DECISION REQUEST, correctly appears below); rules 2/5 apply only to resolved (ACCEPTED-class) ADRs, requiring their own dedicated row, not just a mention. Stale-PENDING/premature-ACCEPTED drift findings (rules 3/4) are excluded, out of scope for a "missing entirely" rollup:
- APR-0034: no APPROVALS_REGISTER.md row at all (doc status: **Status:** DECISION REQUEST — not adjudicated at drafting time; presents option)
- APR-0035: no APPROVALS_REGISTER.md row at all (doc status: **Status:** DECISION REQUEST — not adjudicated at drafting time; presented optio)
- APR-0036: no APPROVALS_REGISTER.md row at all (doc status: **Status:** DECISION REQUEST — not adjudicated at drafting time; presented optio)
- ADR-0001: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED)
- ADR-0003: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** **ACCEPTED — 2026-05-23** — OQ-006 resolved; Polymarket US CA-legal )
- ADR-0010: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — 2026-06-02)
- ADR-0015: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED)
- ADR-0018: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — APR-0018 signed 2026-06-09)
- ADR-0024: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED)
- ADR-0026: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — 2026-06-16)
- ADR-0027: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — 2026-06-16)
- ADR-0028: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — DS sign-off Earl Ignacio, 2026-06-22 SESSION 72 (initial )
- ADR-0032: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED)
- ADR-0045: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — DS sign-off Earl Ignacio 2026-07-15.)
- ADR-0046: resolved and mentioned in APPROVALS_REGISTER.md, but has no OWN dedicated row (only an incidental mention, e.g. inside another row's evidence cell) (doc status: **Status:** ACCEPTED — Earl Ignacio, in-session directive, 2026-07-16.)

**Session claims with no closure row (134)** -- `04_EXECUTION/SESSION_CLAIMS.md` T-NNN tokens with a claim row but no row whose text starts "CLOSED" (includes work that is genuinely still in flight, not only forgotten closures -- this is a filing signal, not a verdict). **Known noise (T-570):** the literal "CLOSED —" prefix is a convention that hardened over time -- older rows often record closure in free text that doesn't start with that word (e.g. T-224's row ends "...T-224 close (...)" rather than opening with CLOSED), so this list over-reports for anything claimed before the convention was consistent. Treat entries below the most recent ~50 rows as needing a manual skim, not a trusted count, until a follow-on tightens the detection or the older rows are normalized:
- `T-224`
- `T-243`
- `T-247`
- `T-250`
- `T-253`
- `T-254`
- `T-255`
- `T-256`
- `T-257`
- `T-258`
- `T-259`
- `T-261`
- `T-280`
- `T-300`
- `T-320`
- `T-321`
- `T-322`
- `T-323`
- `T-324`
- `T-325`
- `T-326`
- `T-327`
- `T-328`
- `T-329`
- `T-330`
- `T-331`
- `T-332`
- `T-333`
- `T-334`
- `T-335`
- `T-336`
- `T-337`
- `T-338`
- `T-339`
- `T-340`
- `T-341`
- `T-342`
- `T-343`
- `T-344`
- `T-345`
- `T-346`
- `T-347`
- `T-348`
- `T-349`
- `T-350`
- `T-351`
- `T-352`
- `T-353`
- `T-354`
- `T-355`
- `T-356`
- `T-357`
- `T-361`
- `T-362`
- `T-363`
- `T-365`
- `T-366`
- `T-367`
- `T-368`
- `T-369`
- `T-371`
- `T-372`
- `T-373`
- `T-374`
- `T-375`
- `T-376`
- `T-377`
- `T-378`
- `T-379`
- `T-380`
- `T-381`
- `T-382`
- `T-383`
- `T-385`
- `T-388`
- `T-389`
- `T-390`
- `T-391`
- `T-392`
- `T-393`
- `T-394`
- `T-396`
- `T-397`
- `T-398`
- `T-399`
- `T-400`
- `T-403`
- `T-405`
- `T-409`
- `T-410`
- `T-411`
- `T-412`
- `T-413`
- `T-414`
- `T-415`
- `T-417`
- `T-418`
- `T-419`
- `T-420`
- `T-421`
- `T-422`
- `T-423`
- `T-426`
- `T-427`
- `T-428`
- `T-429`
- `T-449`
- `T-463`
- `T-474`
- `T-476`
- `T-481`
- `T-492`
- `T-497`
- `T-509`
- `T-512`
- `T-522`
- `T-527`
- `T-536`
- `T-539`
- `T-540`
- `T-545`
- `T-547`
- `T-551`
- `T-552`
- `T-553`
- `T-555`
- `T-561`
- `T-562`
- `T-566`
- `T-573`
- `T-580`
- `T-581`
- `T-582`
- `T-583`

**Shared main tree behind origin/main (0)** -- a session that skips the launch-isolated default (Step 0a) and works directly in the shared checkout can drift behind origin unnoticed (T-574):
_None currently detected._

**Closed-wave fences still in ACTIVE_QUEUE.md (0)** -- pasteable code fences left under a header for a wave the Sequencing track already marks CLOSED, in violation of this file's own stated rule (T-574, found by hand during Wave 33 recovery):
_None currently detected._

---

## 1. Decisions blocked on Earl (4)

Nothing else in this project moves on these until the operator decides. Detected via explicit operator/Earl/sign-off/awaiting-direction language already present in the entry's own text.

- **[GG-046]** T4 Commercial Validation: Independent Alpha Hypothesis Untested and Unregistered — `OPEN` · severity `HIGH`
- **[GG-125]** C7 `SystemMonitor`'s Brier/ECE drift-alarm ladder is never invoked from any production pipeline, for either sport — `OPEN` · severity `MEDIUM`
- **[GG-153]** T1's clean cohort is permanently frozen at clean_n=0 by the interaction of ADR-0048's zeroing and the epoch-10 ALL_BANDS reset; cannot self-heal under the current regime — `OPEN` · severity `MEDIUM`
- **[GG-045]** Maximum Effective Bankroll Constrained by Kalshi Market Depth: Capital Ceiling Unanalyzed — `OPEN` · severity `LOW`

---

## 2. What is actually broken (6)

Something is silently wrong right now — a HALT, an undetected blind spot, a contradiction between claim and code, or HIGH/CRITICAL severity.

- **[GG-038]** T4 Kill Switch SLA: 60s NFR-03 Is 12× Too Slow for Continuous T4 Evaluation — `OPEN` · severity `HIGH`
- **[GG-143]** T4 MLB live engine goes silently blind to all in-progress games after any process restart that lands after 00:00 UTC; GG-058 fixed the in-loop rollover but left the cold-start path unprotected — `OPEN` · severity `HIGH`
- **[GG-060]** Silent Success Indistinguishability: Zero Bets from "No Edge" Looks Identical to Zero Bets from Pipeline Failure — `IN PROGRESS` · severity `MEDIUM`
- **[GG-091]** `mypy --strict` Full-Tree Baseline: 365 Pre-Existing Errors in 57 Files, Not Yet Remediated — `PARTIAL RESOLVE` · severity `MEDIUM`
- **[GG-154]** Session-start protocol cannot verify CLAUDE.md's architectural claims against live source, and Step 4 silently no-ops without SSH access — `OPEN` · severity `MEDIUM`
- **[GG-161]** 22 stuck T1/T2 aged_open positions: OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md's "not an API-outage signal" claim is contradicted by direct evidence; retries genuinely happen daily but a cron-window-correlated 406 failure mode was never surfaced — `OPEN` · severity `MEDIUM`

---

## 3. What is accruing and its clock (114)

Open, tracked, not currently blocking Earl and not flagged as actively broken — but still open, and the clock (epoch resets, n* thresholds, re-check triggers) keeps running. Default bucket: absence of blocked/broken signal, not absence of importance.

- **[GG-170]** MLB Stats API `gameLog` date-label is transiently unstable in near-real-time; a delayed/retried resolution query can bind to `game_date+1`'s true hit total instead of `game_date`'s, root-causing the second B5 disagreement source GG-166 left unexplained — `OPEN` · severity `CRITICAL`
- **[GG-185]** 532 closed T4M-PROJ epoch-12 positions carry a ticker-vs-`game_date` mismatch despite the GG-166 guard, which should have refused every one of them, being confirmed deployed and unconditional at their `resolved_at` time — `PARTIALLY RESOLVED` · severity `CRITICAL`
- **[GG-172]** `MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 are written entirely in market-type terms and contain zero boxes addressing band activation, even though the operator's coverage directive is explicitly "all five bands" and three of five bands have essentially no trading history — `OPEN` · severity `HIGH`
- **[GG-186]** SESSION_CLAIMS.md closure rows for T-458 and T-460 asserted "CLOSED" from local branch/commit state alone, with no check that either branch had actually reached `origin/main` — 4th occurrence of the same pattern (T-456 x2, T-458, T-460) — `PARTIALLY RESOLVED` · severity `HIGH`
- **[GG-189]** T-465 register-and-stop: 46 stuck-open T4M-PROJ epoch-12 positions, 76 rejected-position mismatches, and outcome-store coverage gap block any GG-185/GG-170 backfill — `OPEN` · severity `HIGH`
- **[GG-190]** T-471: the step-function onset of GG-185's game_date corruption (0/77 mismatched under commit `cbd09ae`, 532/532 under `687bf9e`) is not explained by any source-code, deploy, or environment difference found between the two commits — root cause NOT found, evidence bounded and next steps specified — `OPEN` · severity `HIGH`
- **[GG-203]** T4M-PROJ has approved zero bets to execution since 2026-08-15T00:06:20Z: every Kalshi order submission has failed, 1:1 with approvals, for 10 consecutive days, while every liveness signal in Step 4 short of the order-outcome audit trail reports healthy — `PARTIALLY RESOLVED (T-568 — first confirmed real fill)` · severity `HIGH`
- **[GG-204]** ADR-0028's G6 closure condition is unclosable as written: it is scoped to T1, and T1 is permanently `clean_n=0` — `OPEN` · severity `HIGH`
- **[GG-253]** No NFL C1 ingestion module exists; the only generic `team_stats_store.py` is NBA-shaped (`plus_minus`-derived) and not usable as an NFL feature source — `PARTIALLY RESOLVED` · severity `HIGH`
- **[GG-254]** No moneyline/categorical-outcome settlement logic exists anywhere in `src/`, for any sport; `paper_trader.py::settle_position()`'s threshold-crossing model cannot express a game-winner outcome — `PARTIALLY RESOLVED` · severity `HIGH`
- **[GG-255]** `measurement_stake.py` defines all nine ADR-0058 T1 game-market cells but has exactly one real importer codebase-wide (an audit tool); no run script or cron entry exists for any T1 game-market cell, NFL or MLB — `LIKELY RESOLVED` · severity `HIGH`
- **[GG-269]** `pmbot-web-dashboard.service` is in an active OOM crash-loop under its 128MB cgroup memory cap; `systemctl is-active`-style checks do not reliably show it — `OPEN` · severity `HIGH`
- **[GG-295]** Live NFL T1 portfolio's `kalshi_threshold` backfill (all 42 positions) has no corresponding commit anywhere in repo history and is misattributed to an unrelated session (T-562) — `OPEN` · severity `HIGH`
- **[GG-296]** T4M-PROJ's shard-3 demand figure (~2,000 approvals/$1,907.85 stake, 2026-09-20) is a ring-buffer ceiling artifact, not a measured count, and any collateral-funded accrual night risks non-randomly truncating the project's only clean G6 cohort — `OPEN` · severity `HIGH`
- **[GG-297]** 139 of 140 T4M-PROJ "OPEN" positions in `paper_portfolio_mlb_t4.json` (all dated 2026-09-22) are `status: "canceled"`/zero-fill at Kalshi, not live open bets — the local ledger's open-position status is unreliable and, if resolved as-is, would inject fabricated trades into the G6 cohort — `OPEN` · severity `HIGH`
- **[GG-300]** 731 of 765 rows (95.6%) in T4M-PROJ epoch-12's clean cohort — the project's sole G6 calibration cohort — have no independent Kalshi confirmation of ever being filled; only 34 (4.4%) are confirmed real — `OPEN` · severity `HIGH`
- **[GG-301]** T4M-PROJ's calibration headline reverses sign and turns net-negative when restricted to Kalshi-confirmed-filled rows only (n=34 of 765) — `OPEN` · severity `HIGH`
- **[GG-303]** 395 of 731 T4M-PROJ NOT_RETRIEVABLE rows (54.0%) share a `kalshi_ticker` with another ledger row under a distinct, non-existent `kalshi_order_id` — a ledger-write defect independent of the retention/non-submission question GG-300 already raised — `OPEN` · severity `HIGH`
- **[GG-312]** Register-parity failure class: 36 accepted ADRs accumulated with no `APPROVALS_REGISTER.md` row of their own, `check_register_parity.py` sees only 7 of them, and write-back is still manual — `OPEN` · severity `HIGH`
- **[GG-056]** NBA Main Pool Dormant at 24.9% Drawdown; No Reactivation Plan Before October Resume — `PLAN ACCEPTED` · severity `MEDIUM`
- **[GG-098]** MLB T1 Aggregate EV Metrics Are Cited as Milestones While Still Variance-Dominated (Small-n Subset Structure Masked; Aggregate Sign-Flipped n=151→169) — `OPEN` · severity `MEDIUM`
- **[GG-159]** PROJECT_ASSESSMENT_2026-07-30's T4M-PROJ headline reconstruction didn't match the code it claimed to match — verified figure is n=388/+9.65%, not n=344/+10.99% — `OPEN` · severity `MEDIUM`
- **[GG-168]** Step 4's T4 cycle-log write-recency probe (GG-163/T-429) has no exemption for "daily T4 budget exhausted" — a legitimate zero-new-rows state indistinguishable from a real outage by the probe's own logic — `OPEN` · severity `MEDIUM`
- **[GG-174]** `PolymarketVenueAdapter._parse_market()`'s CLOB query hardcodes `"tag": "nba"` (KI-019), unconfirmed against Polymarket's real tag taxonomy, and silently returns an empty market set for any other value — `OPEN` · severity `MEDIUM`
- **[GG-182]** Session-end token/time cost is unaddressed by Hard Rule 8's 60% trigger — second remediation attempt (T-434 fixed WHEN close-out starts, not WHAT IT COSTS); 2026-08-14 session-end consumed 53% context / ran 52m41s — `OPEN` · severity `MEDIUM`
- **[GG-188]** T-463 (team runs-scored outcome store for archived `KXMLBTOTAL` game-events, Phase 2 unblock) was claimed and never implemented, closed, or explained; Phase 2 remains blocked exactly where HYP010's Finding 5 left it — `PARTIALLY RESOLVED` · severity `MEDIUM`
- **[GG-192]** C4 tracks exposure at exactly two granularities (single bet-evaluation, whole portfolio) with nothing in between; a per-game correlation-group cap is a new grouping dimension, not a reuse of existing plumbing — `OPEN` · severity `MEDIUM`
- **[GG-196]** Outage-window (08-04..08-07) sub-bucket of the repaired epoch-12 cohort shows anomalous P&L nearly matching the pre-repair corruption artifact — `OPEN` · severity `MEDIUM`
- **[GG-198]** Three sport-axis questions are unanswered ahead of Phase 3's cell-key work: no `sport` attribute on `MarketType`, no decided NFL band-naming convention, no decided NFL epoch-inheritance rule — `OPEN` · severity `MEDIUM`
- **[GG-202]** T4's 45s poll cadence was tuned against MLB/NBA's near-continuous state progression; NFL's drive-level, dead-period-clustered structure breaks that assumption, and NFL game markets sit at the efficient end of the venue's own gradient — `OPEN` · severity `MEDIUM`
- **[GG-206]** `t4_mlb_totals_outcome_store.jsonl` (and its sibling `t4_mlb_outcome_store.jsonl`) are gitignored under a rule documented for CAT-04 audit logs, but the files are CAT-03 resolution data with no backup/sync path — single-laptop-copy risk for an irreplaceable, StatsAPI-cost dataset — `OPEN` · severity `MEDIUM`
- **[GG-209]** MLB T1 has no force-close/flatten mechanism for open positions; a kill-switch trip or operator halt can only stop new bets, not exit existing exposure early — `OPEN` · severity `MEDIUM`
- **[GG-216]** Venue registry tracked "CA eligibility" but never account-level geo/IP jurisdiction; a Kalshi-side account classification flip is a live-capital blocker with no structural check — `OPEN` · severity `MEDIUM`
- **[GG-224]** Live systemd services holding an in-memory ledger copy silently revert external file-level repairs on their next flush cycle — `OPEN` · severity `MEDIUM`
- **[GG-226]** NFL/NHL T4 sub-band decomposition blocked by SCOPE FENCE: no namespace-valid `ExecutionBand` member exists for those sports — `OPEN` · severity `MEDIUM`
- **[GG-228]** Scheduled batch regeneration of a derived ledger file silently overwrites an external repair applied only to the derived artifact, not its source of record (distinct from GG-224/ADR-0061's live-service in-memory-flush hazard) — `OPEN` · severity `MEDIUM`
- **[GG-232]** ADR-0054(a) staffing gap: three named-not-staffed follow-ons (replay-harness `market_type=`, cell-unaware ledger/monitor tooling) sat unstaffed from sign-off to this entry — `IN PROGRESS` · severity `MEDIUM`
- **[GG-240]** ADR-0062's T-512 sign-off is recorded only on an unlanded branch; three merge routes to `origin/main` were refused, leaving the ADR PROPOSED in the canonical record despite an operator-confirmed accept decision — `OPEN` · severity `MEDIUM`
- **[GG-260]** Shared `main` working tree carries uncommitted `ACTIVE_QUEUE.md` drift invisible to worktree-isolated sessions; recurrence of the condition T-505 fixed in Wave 10 — `OPEN` · severity `MEDIUM`
- **[GG-261]** T-528's capture-fidelity "zero coverage gaps" verdict tested kickoff-instant coverage only, not pregame-window coverage; missed the day-3 (Wed UTC) NFL price-archive gap — `OPEN` · severity `MEDIUM`
- **[GG-275]** `lib_chain_archive.py` silently discards the prior "Last reviewed" line on every single-entry chain collapse (regression in the GG-176 fix) — `OPEN` · severity `MEDIUM`
- **[GG-279]** A code fix landing (and even fully migrating on-disk state) in a long-running service's source is not activated in that service's own running memory until it is restarted; neither session-start nor session-close-out protocol checks process-level activation vs. mere code-landing — `OPEN` · severity `MEDIUM`
- **[GG-282]** Investigation: do the two new T1 game-market run scripts inherit the live $10 `min_bet_usd` floor instead of the paper $1.00 floor their sibling runners pass, and is T4 MLB's `kalshi_client=None` demo-order path (GG-203) load-bearing or optional? — `PARTIALLY RESOLVED (2026-09-15, T-551) — Floor A fixed and verified; Floor B investigated, decision requested via APR-0034, not decided` · severity `MEDIUM`
- **[GG-285]** At observed effect sizes, APR-0024's per-band P&L n* is 10-11 NFL seasons (NFL moneyline) and ~1.6 MLB seasons (T4M-PROJ) from clearing; the P&L gate as currently written may not close within any practical operating horizon for signals whose sd/mean ratio is ~15-28x — `OPEN` · severity `MEDIUM`
- **[GG-298]** `rejected_positions` field name implies risk-engine declines but actually holds post-approval exchange-side order-submission failures, making it unusable as a holdout/decline cohort under its documented name — `OPEN` · severity `MEDIUM`
- **[GG-304]** `kalshi_order_status` field reads `"submitted"` uniformly across both confirmed-FILLED and confirmed-unretrievable T4M-PROJ rows, making it non-discriminating for any downstream fill-status inference — `OPEN` · severity `MEDIUM`
- **[GG-308]** `scripts/close_session_claim.sh` pushes the entire branch tip to `origin/main` via `git push origin HEAD:main` instead of isolating just the closure row, contradicting its own GG-186-follow-on docstring intent — `OPEN` · severity `MEDIUM`
- **[GG-309]** CLAUDE.md Step 4's `SemanticFloorViolation` grep (T1 MLB silent-failure detector) has no recency window, so a single 2.5-month-old hit reads identically to a live-today failure — `OPEN` · severity `MEDIUM`
- **[GG-007]** T4/T5 Threshold Constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) Are Uncalibrated Skeleton Values — `OPEN` · severity `LOW`
- **[GG-162]** GG-NNN numbers picked mid-session have no atomic reservation, unlike T-/ADR- ranges claimed at session start; two concurrent sessions independently registered GG-159 on 2026-08-04 — `OPEN` · severity `LOW`
- **[GG-165]** 38/46 live gap entries carry no explicit Severity (UNSPECIFIED); full backfill deliberately deferred out of T-423's XS scope — `OPEN` · severity `LOW`
- **[GG-167]** `deploy.yml`'s dirty-tree guard only inspects tracked files; an untracked-file collision on the VPS silently blocked `git pull --ff-only` during GG-163's deploy, sibling gap shape to the already-resolved GG-130 — `OPEN` · severity `LOW`
- **[GG-177]** `session_end_prep.sh`'s Step 0 SESSION_CLAIMS.md lookup matches on the worktree branch's timestamp, but `claim_session.sh` stamps its row at actual claim-command time — the two are seconds-to-minutes apart, so the exact-string match fails on effectively every session even when the claim genuinely exists — `OPEN` · severity `LOW`
- **[GG-183]** Per-cell kill-switch state (ADR-0053 §2.3/§6.3 item 4) has a store and a resolution helper but is not wired into C4/C7's live kill-switch check — `OPEN` · severity `LOW`
- **[GG-184]** `open_position()`'s `market_type` parameter defaults silently; 100% of live call sites rely on the default rather than passing it explicitly — `PARTIALLY RESOLVED` · severity `LOW`
- **[GG-187]** T2's gross-edge formula is known but epoch-conditional; unsafe to backfill into assert_ledger_invariants.py's flat multiplier — `OPEN` · severity `LOW`
- **[GG-195]** 14 untracked nav-adjacent files sitting in the shared main working tree, unclaimed and unregistered, outside any session's explicit scope — `OPEN` · severity `LOW`
- **[GG-200]** `ACTIVE_QUEUE.md` Block G cites `GG-194` as its tracking gap; no `GG-194` exists in the log or its archive — `OPEN` · severity `LOW`
- **[GG-217]** No Kalshi series exists for an NHL team-total market; the four-family coverage target cannot be fully seeded for NHL as it was for NFL — `OPEN` · severity `LOW`
- **[GG-218]** T1 has no automated alarm for a position stuck OPEN past a plausible resolution window (postponed/rescheduled game, no `apply_resolved_hits.py` match) — `OPEN` · severity `LOW`
- **[GG-221]** HYP-010 Phase 2 plan defines a reroute for FALSIFIED and none for INCONCLUSIVE; two independent model fits have now both landed there — `OPEN` · severity `LOW`
- **[GG-229]** `TestPromoteCellStatus` RULED_OUT fixtures leak global registry state via `del` instead of restore — `OPEN` · severity `LOW`
- **[GG-230]** `MEMORY_BANK.md`'s "Compass OS Health" single-line field is 5159 chars, 1.7x the script's own 3000-char anti-blob threshold, flagged and never registered — `OPEN` · severity `LOW`
- **[GG-233]** Task briefing restated ADR-0056 D2 as adopting the superseded `T4N-` convention, not the actually-signed `T4MLB-`/`T4NBA-`/`T4NFL-`/`T4NHL-` form — `OPEN` · severity `LOW`
- **[GG-234]** Task assignment named `T-508 / GG-231` for new work; both IDs were already consumed by unrelated, already-closed sessions by the time the assigned session actually started — `OPEN` · severity `LOW`
- **[GG-235]** `04_EXECUTION/LEDGER_INVARIANT_SUITE.md`'s documented VPS-fetch commands reference filenames that no longer exist on the VPS — `OPEN` · severity `LOW`
- **[GG-243]** T-number collision: "T-518" independently claimed by two unrelated tasks (TODO_NEXT.md's EXP-026 entry vs. this session's ADR-0060/0061/0062 re-recording) — `OPEN` · severity `LOW`
- **[GG-244]** Operator task brief's T4-segment count (11 segments / eight `kelly_fraction` regimes) does not match source (13 segments / six distinct values) — `OPEN` · severity `LOW`
- **[GG-256]** `scripts/claim_session.sh`'s rebase-retry did not prevent a duplicate T-number claim; two concurrent sessions both claimed T-526 one second apart — `OPEN` · severity `LOW`
- **[GG-257]** `settle_position()`'s boolean win/loss model cannot express Kalshi's $0.50/$0.50 split payout for an NFL moneyline exact tie — `OPEN` · severity `LOW`
- **[GG-258]** Task brief pre-assigned `EXP-026`/`HYP-011` to a new NFL moneyline-LR experiment, but those IDs are already canonically registered to a different, pre-existing MLB moneyline experiment — `OPEN` · severity `LOW`
- **[GG-262]** Live VPS crontab's `run_mlb_pregame.py` schedule (`20 21 * * *`) diverges from repo `deploy/cron.conf`'s value (`30 16 * * *`); origin/cause not determined — `OPEN` · severity `LOW`
- **[GG-266]** Local dev machine's system Python (3.9.6/LibreSSL 2.8.3) cannot TLS-handshake with ESPN's scoreboard endpoint; affects every existing `integration`-marked live-network test, not just this session's new one — `OPEN` · severity `LOW`
- **[GG-281]** EXP-027/HYP-012 re-run (2026-09-15): still UNDERPOWERED; task premise of "Weeks 1 and 2 resolved" was factually wrong at run time (only Week 1 had resolved) — `OPEN` · severity `LOW`
- **[GG-292]** 14 stray remote session branches (2026-08-24 through 2026-09-15) unlanded; `sweep_stray_branches.sh` unavailable on origin/main to sweep them — `OPEN` · severity `LOW`
- **[GG-299]** ADR-0046's ECE baseline (0.0680, n=261) drifts +22% relative (to 0.0832) when its own exact methodology is re-applied to a later live pull of its own source file (n=468); Brier holds steady (0.2190→0.2200) over the same re-pull — `OPEN` · severity `LOW`
- **[GG-305]** `session_guard.sh`'s Compass OS Health length-threshold check has been failing against `MEMORY_BANK.md` line 1111 (5159 chars vs. a 3000-char threshold) for at least 41 days without remediation — `OPEN` · severity `LOW`
- **[GG-306]** CLAUDE.md's coverage-target framing ("~25/30 cells") is never reconciled against `market_type_registry.py`'s actual 92-cell granularity, understating the registry's real scope by roughly 3x wherever the coarse figure is read on its own — `OPEN` · severity `LOW`
- **[GG-307]** `build_t4mlb_cohorts`'s edge-reconstruction formula has never been tested against T4M_ARITH/T4M_FLOW inputs, only against T4M-PROJ — a disclosed scope boundary on this wave's scoring-harness work, not a defect — `OPEN` · severity `LOW`
- **[GG-004]** EV Validation Benchmark Was Never the Commercial Question — `OPEN` · severity `UNSPECIFIED`
- **[GG-014]** Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode — `PARTIALLY RESOLVED` · severity `UNSPECIFIED`
- **[GG-020]** Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts — `ACCEPTED UNCERTAINTY` · severity `UNSPECIFIED`
- **[GG-027]** PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Environment Classifier Not Built — `OPEN` · severity `UNSPECIFIED`
- **[GG-037]** Calibration Collapse + Inverted Edge Realization: the Model's Edge Signal Is Anti-Predictive — `OPEN` · severity `UNSPECIFIED`
- **[GG-039]** T4 Price Cache / Staleness Check Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-040]** T4 Real-Time Data Sources: Required Feeds Not in Current C1 Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-041]** KXNBAPTS Orderbook Depth Data: Finals Window Missed; ADR-0005 Limit Empirical Basis Absent — `OPEN` · severity `UNSPECIFIED`
- **[GG-064]** Kalshi DEMO Market `open_time` Lags LIVE for Same Ticker (Discovered During GG-063 Verification, Unconfirmed as Structural) — `LIKELY RESOLVED` · severity `UNSPECIFIED`
- **[GG-066]** MLB C1 Has No Real-Time/Sub-Poll-Interval Event Feed (Blocks Event-Driven T4 Sub-Bands) — `OPEN` · severity `UNSPECIFIED`
- **[GG-072]** T1 MLB (PIPE-05) HALTed by the Same GG-068 Bug On the Same Day, But Was Never Cross-Checked or Recovered — 2026-07-02 Betting Day Permanently Lost — `OPEN` · severity `UNSPECIFIED`
- **[GG-078]** T4 MLB's Real ~341-Bet/Day Cadence Means Kill-Switch Fate Is Decided Within ~15 Days Regardless of True Edge Sign; Long-Horizon Projections for T4 Are Not Meaningful at Any Stake Cap — `OPEN` · severity `UNSPECIFIED`
- **[GG-094]** MLB Has No Qualitative/PRF-Analogue Feature Layer Despite Being the Sole ACTIVE Pool — `OPEN` · severity `UNSPECIFIED`
- **[GG-105]** T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship between its own computed edge and realized win rate, on clean data (Workstream B / T-322/T-323/T-324 discovery) — `OPEN` · severity `UNSPECIFIED`
- **[GG-121]** 2026-07-11 T1 MLB `SemanticFloorViolation` (games_fetched=16, matched_players=0) surfaced by GG-049's own heartbeat but never logged — `WATCH ITEM` · severity `UNSPECIFIED`
- **[GG-124]** All four active MLB bands simultaneously clean_n=0/UNDERPOWERED, monitoring-coverage blackout from rapid-fire epoch boundaries — `OPEN` · severity `UNSPECIFIED`
- **[GG-127]** 00_ADMIN/README.md (designated nav hub, ADR-0001) went ~7 weeks with zero updates while the project moved through multiple phase transitions — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-132]** MEMORY_BANK.md `**Last reviewed:**` narrative chain regrew unchecked 9→52 entries since T-334's 2026-07-11 fix; the 2026-07-15 ADR-0044 re-application consolidated only the sibling `## Current State Snapshot` chain, not this one — `OPEN` · severity `UNSPECIFIED`
- **[GG-133]** CHANGELOG.md has not been updated since 2026-05-30 despite ~2 months of major changes, violating its own staleness trigger — `OPEN` · severity `UNSPECIFIED`
- **[GG-134]** `mc_empirical_bootstrap.py`'s forward-risk projection has four unmodeled scope gaps not disclosed as limitations at commit time — `OPEN` · severity `UNSPECIFIED`
- **[GG-136]** No standing archival cadence exists for `04_EXECUTION/TODO_NEXT.md`'s own `## T-NNN` task sections (same class as GG-127) — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-137]** A1's holdout-Brier-optimal K=400 shrinkage candidate gives only ~7% weight to actual player data; may trade calibration for discrimination — `OPEN` · severity `UNSPECIFIED`
- **[GG-140]** GG-105 remediation exhausted the entire class of monotonic-transform recalibration candidates without a structural check ruling that class out first (temperature scaling, LR+Platt refit, isotonic — all tested serially, all failed the same way) — `OPEN` · severity `UNSPECIFIED`
- **[GG-145]** `park_factor_hits` is hardcoded 1.0 across all 20,943 rows of the historical C2 feature matrix; second, independent instance of GG-141's failure shape, found live by GG-141's own preventive fix — `OPEN` · severity `UNSPECIFIED · **Assertion:** LANDED(scripts/check_feature_column_health.py) — detection assertion exists and is exactly how this gap was found; the underlying `park_factor_hits` bug itself remains unfixed (ADR-0052/T-433)`
- **[GG-146]** 8 pre-existing test failures in `test_exp015_t3_simulation.py`, traced to ADR-0048's `T1_MULTI_DAY.kelly_fraction=0.0` propagating into `run_exp015.py`'s Monte Carlo simulation as a division-by-zero; first surfaced by a full-suite run on an unrelated branch — `OPEN` · severity `UNSPECIFIED`
- **[GG-150]** Cross-book (T1 vs T4) opposite-direction conflicts are alarmed, not blocked; a blocking control is an unstaffed gap — `OPEN` · severity `UNSPECIFIED`
- **[GG-151]** `merge=union` does not guarantee dedup: identical content reaching both merge sides via different commit paths can be duplicated, not deduplicated — `OPEN` · severity `UNSPECIFIED`
- **[GG-156]** No forward price archive existed for any MLB market family before 2026-08-01; Phase 2's market-comparison gate had no input source and the same absence limits GG-142 counterfactual analysis — `OPEN` · severity `UNSPECIFIED`
- **[GG-157]** `paper_trader.py` has zero orderbook/depth/fill validation; every paper fill (including the live epoch-12 flat-$1 cohort) is assumed at mid, and GG-155/T-411 shows that assumption sits against a quantity that swings 10-100x intraday — `OPEN` · severity `UNSPECIFIED`
- **[GG-158]** Price archive had zero off-VPS copies for 3+ sessions despite repeated "verified"/"deployed" reports; same failure class as GG-144's unanchored grep — `OPEN` · severity `UNSPECIFIED`
- **[GG-160]** Four `file:line` citations across three Phase 0/1 docs had drifted from source with nothing catching it; no mechanism exists that resolves a doc's code citations against current source — `OPEN` · severity `UNSPECIFIED`
- **[GG-164]** T4 MLB cycle log's `game_date` field is wrong on 70% of all rows (45,217/64,396): stamped from UTC wall-clock "today" at write time, not the game's actual date; `(player_id, game_date, threshold)` is not a valid join key without correction, and doubleheaders break it further — `OPEN` · severity `MEDIUM · **Assertion:** PENDING(T-432, assertion A) — RESOLVED is not eligible until this lands (ADR-0052); this entry's original "Why it survived" field asserted an unverified negative ("isn't used as a resolution join key anywhere") that GG-166 directly contradicted — the motivating case for ADR-0052`
- **[GG-166]** `run_resolve_mlb.py` consumes the same corrupted `game_date` field GG-164 documented, and silently resolves T4M-PROJ positions against the wrong day's box score for ~44% of the epoch-12 clean cohort — corrupting live paper-trading WIN/LOSS/pnl, not just a future-risk join key — `OPEN — code fixed, ledger `game_date` corrected, GG-170 authority settled and 1,127/1,220 (92.4%) of the stale outcome/pnl population re-derived (T-437, 2026-08-11/12); 93 positions still outstanding pending outcome-store coverage; T4M-PROJ power-calc baseline now flips TARGET MET → NOT MET post-correction` · severity `CRITICAL · **Assertion:** PENDING(T-432, assertion A) — shared with GG-164 (same defect, write-site vs. read-site); B2's per-resolution `game_date_ticker_mismatch` refusal is a point check at resolution time, not a standing suite-level invariant, so this remains PENDING not LANDED (ADR-0052); also the concrete G6 precondition example (ADR-0052 §2.3) — Kelly sizing and the drawdown kill switch both read this same ledger`
- **[GG-288]** session-end close-out fix (closure-row-push + stray-branch-sweep) sat on local `main` unpushed across a full session and was squash-merged over by PR #138, and T-554's own closure row failed to reach `origin/main` despite the script reporting an honest failure — `OPEN` · severity `UNSPECIFIED`
- **[GG-289]** Auto-mode classifier's Self-Modification block on `.claude/commands/session-end.md` + `scripts/close_session_claim.sh` + `scripts/sweep_stray_branches.sh` is a structural, repeatable barrier — confirmed twice independently — and is the likely actual root cause of T-554's silent closure-row push failure, not mere git divergence — `OPEN` · severity `UNSPECIFIED`

---

**Full record for every entry above:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md`. **Resolved/closed history:** `03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md`.

