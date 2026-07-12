# Execution Plan — Prediction Market Trading Bot

**Purpose:** The authoritative, actionable delivery plan. Maps work to phases, owners, and milestones. Updated at each gate and weekly during active phases.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-07-12 (Window 3 "Readiness debt" CLOSED — T-346/GG-092 (missing incident runbooks) + T-347/GG-093 (threat model re-expansion) both DONE, worktree `session/20260712T095020Z-gg092-gg093-readiness-debt`, PR #14 open not yet merged) — T-346: wrote the 4 CRITICAL/HIGH incident runbooks `RESILIENCE_FAILURE_MODES.md` had flagged as missing since GG-074 (ingestion-failure, data-contamination, order-duplication, audit-log), each honest about detection gaps (FM-02 has no production runtime detector; FM-07's kill-switch-on-write-failure contract is unenforced); redacted an unplanned leaked Kalshi API-key-ID finding (rotation/history-scrub still open operator action). T-347: re-expanded `THREAT_MODEL.md` TH-02/Out-of-Scope for live Kalshi RSA credentials, re-verified 2 known findings, surfaced 1 new `SECRETS_HANDLING.md` rotation-gap finding. A GG-113 numbering collision with a concurrent session's unrelated, still-OPEN gap resolved by renumbering to GG-114, then a second rebase-collision (a different concurrent session's own, unrelated GG-114 for an orphaned-branch finding reached `origin/main` first) required a further renumbering to **GG-116** — content unchanged across both renumberings, ID only. Full suite 2672/29/0 post-rebase (later re-verified 2685/29/0 after a further rebase during the close-out re-audit below). An operator close-out challenge ("did you complete the task list + all auxiliary tasks") caught that (a) origin/main had moved past this branch's stale rebase point and (b) three items GG-093/GG-116 had only flagged in Resolution-field prose (GG-116 rotation/history-scrub decision, `SECRETS_HANDLING.md` rotation-cadence gap, `t4-mlb.service` hardening-parity evaluation) were never registered as discrete T-NNN tasks — fixed same window via T-351/T-352/T-353. This session then ran CLAUDE.md's full formal session-start protocol post-completion (operator instruction) — clean across doc-debt/stub/20 OPEN gaps; one `SemanticFloorViolation` traced to already-RESOLVED GG-110. **No deliverables-table impact — readiness/governance debt work, not a new Phase 6 milestone line item.** No capital-affecting action, no live bankroll figures re-pulled. Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-12 headers, DECISION_LOG.md 2026-07-12 (T-346/T-347 rows), GOVERNANCE_GAP_LOG.md GG-092/GG-093 (RESOLVED)/GG-116, TODO_NEXT.md T-351/T-352/T-353.

**Last reviewed (prior):** 2026-07-12 (Iteration Plan v3 Window 1 CLOSED — T-344 (GG-105 decomposition, diagnose-only) + T-345 (GG-020 fee verification) both DONE, worktree `20260712T095029Z-t344-t345-gg105-decomposition`, merged as PR #13) — GG-105's anti-predictive T4M-PROJ finding reconfirmed at clean_n=412 (sharper: p 0.0464 vs 0.0563), all four candidate mechanisms decomposed, leading mechanism is model miscalibration/overconfidence, no recalibration ADR this window per scope. New governance gap GG-113 (OPEN, vig-sign-flip bug in `run_t4_mlb_live.py`, does not explain GG-105) registered after a GG-112 ID collision with a concurrent session was resolved on merge. **No deliverables-table impact — diagnostic/governance work, not a new Phase 6 milestone line item.** Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-12 headers, DECISION_LOG.md 2026-07-12 (T-344/T-345 rows), GOVERNANCE_GAP_LOG.md GG-105/GG-113.

**Last reviewed (prior):** 2026-07-11/12 (Window 3 CLOSED — T-341 (N-06) + T-342 (N-07) both DONE, worktree `session/20260711T225758Z-t341-t342-monitor-cron-flat-mc`) — T-341: `SystemMonitor.report_band_monitor_verdicts()` wires per-band anti-predictive/calibration-breach verdicts into C7 as warn-only WARNING alarms; `run_band_monitor.py` writes dated JSON verdict artifacts; confirmed the existing VPS cron already satisfies the "schedule the monitor" requirement — ✅ COMPLETE (80/80 `test_c7_monitor.py`). T-342: added `stake_mode={"proportional","flat"}` to `mc_forward_projection.py` so the forward-ruin MC can model T4M-PROJ's empirically flat-clustering dollar stakes (confirmed via code read the live mechanism is actually `KELLY_T4=0.10` proportional Kelly — flat mode models an empirical regime property, not an architectural guarantee); froze dated `T4M_PROJ_*` operational constants from clean_n=338; live run shows flat-dollar sizing carries materially lower forward ruin risk than T1's proportional-Kelly regime at comparable edge — explicitly flagged not to be read apart from GG-105's anti-predictive caveat, which is now surfaced directly inside `build_ledger_report()`'s T4M-PROJ output text. Added 17 dedicated `stake_mode="flat"` tests (33→50 in `test_mc_forward_projection.py`). Also found and fixed an unrelated pre-existing test fragility in `test_cron_log_aggregator.py` (a date-relative bare-substring assertion coincidentally collided with a hardcoded historical date embedded in the script's own output text) — ✅ COMPLETE. GG-111 (local-vs-UTC date mismatch in an unrelated T-343 test) additionally found during the pre-merge rebase against a further-advanced `origin/main`, registered and fixed same session. Full suite green post-rebase: 2672 passed, 29 skipped, 0 failed. **No deliverables-table impact — monitoring/risk-tooling hardening, not a new Phase 6 milestone line item.** No capital-affecting action, no live bankroll figures re-pulled. Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-11/12 headers, DECISION_LOG.md 2026-07-11 (T-341, T-342 rows) + 2026-07-12 (GG-111/rebase row).

**Last reviewed (prior):** 2026-07-12 (Window 2 close-out — T-339's APR-0024 ACCEPTED, DS sign-off Earl Ignacio, session-end) — Earl reviewed and approved APR-0024 in full ("you have my operator sign off... proceed with addressing in full"). Implemented across `CLAUDE.md` (§ "commercial validation gap"/"Gate structure"), `00_ADMIN/APR-0024_g6-sample-adequacy-n-star-rebase.md` (Review Checklist fully checked, sign-off block filled), `00_ADMIN/APPROVALS_REGISTER.md` (ACCEPTED), `MEMORY_BANK.md`, `DECISION_LOG.md`, `TODO_NEXT.md`, and `GOVERNANCE_GAP_LOG.md` (GG-004 cross-referenced, no verdict retracted). Review Checklist item 5 (superseding-ADR question for ADR-0024 itself) explicitly **DEFERRED, not resolved** — Earl's sign-off did not elect that branch; the APR's own "acceptable to defer" default was taken instead. Committed `7a32719`, checkpoint advanced `2c7d8b3`, pushed to `main`, CI green (Deploy + Test Suite both `success`). **No deliverables-table impact — governance/gate-language amendment, not a Phase 6 milestone line item.** No production `src/` behavior changed, no capital-affecting action, no live bankroll figures re-pulled by this segment (last pull: MLB bankroll $1014.31, resolved 232/30 G6, P&L +$65.80; NBA dark $751.10, resolved 158/30, P&L −$248.90 — from governance hook, unchanged this segment). Full detail: `DECISION_LOG.md` 2026-07-12, `MEMORY_BANK.md`/`TODO_NEXT.md` 2026-07-12 addenda.

**Last reviewed (prior):** 2026-07-11 (Window 2 — T-338/T-339/T-340 "Convert tooling into a decision," session-end) — T-338 ran `scripts/run_power_calc.py` (T-323) live against a fresh VPS pull and published `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md` (T1 clean_n=81/n*=2,322 ~15.8wk ETA; T4M-PROJ clean_n=338/n*=787 ~0.95wk ETA; both provisional, cadence <14d immature), plus a "SAMPLE ADEQUACY" line in `.claude/hooks/governance_scan.sh`. T-339 drafted `00_ADMIN/APR-0024_g6-sample-adequacy-n-star-rebase.md` (`Status: PENDING — DS sign-off required`) proposing G6 gate language move to per-band `clean_n ≥ n*`, replacing the flat ADR-0024 30/150/500 heuristic; explicitly does not supersede ADR-0024 itself (Hard Rule 3) or retract GG-004's n=151 verdict — awaiting Earl's review. T-340 checked GG-105 Component A's calendar gate (epoch age ~6.0d vs ~14d required) — not yet triggerable, re-check ~2026-07-19/20, logged in GOVERNANCE_GAP_LOG.md GG-105. **No deliverables-table impact — governance/sample-adequacy tooling, not a Phase 6 milestone line item, same treatment as prior sessions' infra/analysis entries.** No production `src/` behavior changed, no capital-affecting action, no live bankroll figures re-pulled, GG-110 not touched (concurrent-session owned). Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-11 headers, DECISION_LOG.md 2026-07-11 (T-338/T-339/T-340 rows).

**Last reviewed (prior):** 2026-07-11 (Window 1 — T-336/T-337 "Green the board," session-end) — T-336 fixed `TestT1RegressionAnchor`'s live-data-anchor anti-pattern (GG-106 RESOLVED) via a frozen `SNAP-2026-07-11-001` fixture + verdict/tolerance-band assertions replacing the drift-prone live-data comparison. T-337 discovered no pytest CI job existed at all (every prior session's "full suite green" claim was manually run, never enforced) and added `.github/workflows/tests.yml`, verified green twice in production (PR #6 checks + post-merge `main` run). Full suite certified 2,465 passed / 29 skipped / 0 failed (2,494 collected, 120.75s) — this count supersedes all other in-flight counts cited elsewhere this session. Merged via PR #6 (`0d6244c`). Mid-merge, a genuine GG-ID collision surfaced (this session's GG-109 registration collided with a concurrent "Window B" session's separately-registered, unrelated GG-109) — resolved entirely by the other session's reconciliation commit (`3e8b9d8`, verified via direct grep), renumbered to **GG-110**, which remains OPEN/uninvestigated (a concurrent session has since claimed it per `SESSION_CLAIMS.md` — do not duplicate). **No deliverables-table impact — test-infrastructure + CI hardening, not a Phase 6 milestone line item, same treatment as prior sessions' infra/hygiene entries.** No production `src/` behavior changed, no capital-affecting action, no live bankroll figures re-pulled. Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-11 headers, DECISION_LOG.md 2026-07-11 (T-336/T-337 rows), GOVERNANCE_GAP_LOG.md GG-106 (RESOLVED)/GG-110 (OPEN).

**Prior — 2026-07-11** (GG-108 session-start-protocol fix, session-end) — Found and fixed GG-108: CLAUDE.md's own Step 4 NBA operational-health check grepped `logs/paper_cron.log`, a filename that no longer exists on the VPS (NBA's single-window cron was split into `paper_early_cron.log`/`paper_late_cron.log` at some point without the reference being updated), making the check a silent no-op for NBA specifically for an unknown number of prior sessions. Fixed CLAUDE.md to grep both real files and match the actual off-season log line; PR #5 merged (`f1808c4`), VPS deploy verified green (`gh run` `29144874469`). Also fixed a live GG-082-class recurrence (2 same-day duplicate "Last reviewed" headers in MEMORY_BANK.md), archived the superseded lines verbatim to `MEMORY_BANK_ARCHIVE.md`. **No deliverables-table impact — a doc/governance-hygiene fix, not a Phase 6 milestone line item.** No capital-affecting action, no code/test changes, no live bankroll figures re-pulled. Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-11 headers, DECISION_LOG.md 2026-07-11 (GG-108 scoping decision row). *(Previous, T-328 + T-333 Component B: PR #3 merged to `main`, `f547a2f`, session-end)* — Committed, pushed, and merged the already-investigated T-333 Component B work (GG-105 edge-formula audit — H2 confirmed by code read, H5 headline vig-omission finding, reconfirms the anti-predictive verdict rather than overturning it) alongside T-328 (deploy.yml permanent restart+freshness fix, GG-104 RESOLVED). Confirmed PR #3 `CLEAN`/`MERGEABLE`, squash-merged, polled `deploy.yml` (`gh run` `29144129199`) to `success`, retired the worktree/branch, fast-forwarded local `main`. **No deliverables-table impact — a merge/close-out event, not a new Phase 6 milestone line item, same treatment as prior sessions' infra/merge entries.** No new strategic decisions this closeout segment (already logged in the prior segment's DECISION_LOG.md row); no capital-affecting action, no live bankroll figures re-pulled. Full detail: MEMORY_BANK.md/TODO_NEXT.md 2026-07-11 headers, DECISION_LOG.md 2026-07-11 ("T-333 Component B DONE" row).

**Last reviewed (prior):** 2026-07-10 (Window B, isolated worktree `session/20260709T000817Z-window-b-math-rigor`, session-end, merged to `main` 2026-07-11 via GG-107 remediation) — **T-280 "Math rigor hardening" is now FULLY COMPLETE — B1 through B6 all closed.** B5 added `tests/test_t280_golden_analytic_invariants.py` (17 hand-derived closed-form golden tests: Kelly sizing, temperature scaling, `monitor.py` Brier/ECE, binomial PMF, `p_hits_gte_threshold`, and the full 9-field Murphy decomposition) plus a centralized `tests/conftest.py` (single-source Hypothesis determinism profile + global `random` seed). B6 re-ran the full suite as the final gate — **2580 passed / 30 skipped / 0 failed**, identical to B5's own count, confirming zero commit drift — registered T-284 (compute-endpoint for calibration diagnostics, scoping-only, explicitly not built) and carried forward T-283 (stale GG-004/CLAUDE.md figures, deferred). No production `src/` behavior changed in B5/B6. All work committed (`af66442`, `8ed1ef8`) and pushed to `origin session/20260709T000817Z-window-b-math-rigor`; merged to `main` 2026-07-11 during GG-107 remediation (untracked-iteration-plan cleanup). **Merge-time renumbering:** Window B's GG-104 (worktree isolation doesn't cover Python import resolution) collided with an independently-assigned, unrelated GG-104 already merged to `main` from the Window A/T-320-321 track (`deploy.yml` never restarts persistent systemd services) — a live recurrence of the same numbering-race class GG-101 targets. Window B's GG-104 renumbered to **GG-109** throughout (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, session handoffs, `tests/conftest.py`, `tests/test_t280_cross_implementation_invariants.py`) as part of the merge; content unchanged, ID only. Full detail: DECISION_LOG.md 2026-07-10 B5/B6 entries and 2026-07-11 merge/renumbering entry, MEMORY_BANK.md "Last major milestone." *(Previous, same-day, superseded — partial state before B5/B6:)* T-280 B1-B4(partial) done; GG-109 (renumbered from a same-session GG-103 ID collision with Window A's own GG-103 — see GOVERNANCE_GAP_LOG.md; further renumbered from GG-104 at main-merge time, see above) found and closed via T-282. B1 closed with corrected scope: briefed to convert a sequential multiplicative Bayesian-update chain to log-space, but verified the premise against the actual code first and found no such chain exists (NBA's Gamma-Poisson update is additive/closed-form, MLB's binomial PMF is already `math.lgamma`-based log-space); operator selected "Corrected scope" instead — delivered `risk.py` `_MIP_EPSILON=1e-6` Kelly boundary clamp + cross-check tests, and binomial-PMF log-space regression tests. B2 found a real ECE bin-edge divergence between `monitor.py` and the EXP-017C script (documented, deferred as T-281). B3 (Hypothesis property tests) found a real float64 sigmoid-saturation edge case in `temperature_scale` under T<1.0 (unreached in production, all live `CALIBRATION_TEMPERATURE` entries are ≥1.0). B4 (partial) lifted calibration diagnostics to a shared module (`calibration_diagnostics.py`) and discovered GG-109 (worktree isolation doesn't cover Python import resolution). See DECISION_LOG.md 2026-07-09/10, TODO_NEXT.md T-280/T-282, MEMORY_BANK.md.

**Last reviewed (prior):** 2026-07-11 (T-333 branch merged to `main` via PR #1, `563c31d`, session-end) — Closed out T-333 (GG-105 diagnostic (3) scope + edge-formula audit scope) across a mid-session `/session-end` interrupt and resume. PR #1 briefly went `CONFLICTING` when a concurrent T-324-audit session merged first; re-merged `origin/main`, resolved three conflicts (`DECISION_LOG.md` keep-both, `.last_session_checkpoint`, add/add `SESSION_HANDOFF`), pushed, merged PR #1, verified `deploy.yml` success (`gh run` `29143007476`), retired worktree/branch. Net diff was scope-doc-only (zero source code) — T-333 was scoping, not implementation. A separate concurrent worktree already claims T-328 + T-333 Component B — do not duplicate. **No deliverables-table impact — a merge/close-out event, not a new Phase 6 milestone line item, same treatment as prior sessions' infra/merge entries.** No capital-affecting action, no live bankroll figures re-pulled this session. Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-11, DECISION_LOG.md 2026-07-11 (T-333 merge entry), TODO_NEXT.md T-333 (✅ MERGED TO MAIN).

**Last reviewed (prior):** 2026-07-11 (Workstream D — T-330/T-331 merge-to-`main`, session-end) — Merged `session/20260711T013132Z-workstream-d-mc-forward-projection` (ledger-driven MC forward-projection + bootstrap CI, T-330/T-331) into `main` via `--no-ff` at `81cfb20`, with a concurrent GG-105 (Diagnostic 2) session active in parallel the whole time. Applied Hard Rule 10 across three separate re-fetches of `origin/main` during the merge window, catching two additional waves of concurrent GG-105-session work (a T-332 completion, then a T-333 claim) before they could be silently overwritten; the actual T-330/T-331 code never conflicted with any of it. Conflicts in `TODO_NEXT.md`/`DECISION_LOG.md` were resolved by keeping both sections (most-recent-dated entry first), with one deliberate exception where origin/main's newer, complete T-332 content was taken wholesale over a stale local note. Post-merge full suite: 2464 passed / 29 skipped / 1 pre-existing GG-106 failure (unrelated, already logged). Pushed (`1006867..81cfb20`), VPS auto-deploy verified (`gh run` `29136139235`, success), worktree/branch retired. **No deliverables-table impact — a merge/integration event closing an already-built Workstream D, not a new Phase 6 milestone line item, same treatment as prior sessions' infra/analysis entries.** No capital-affecting action, no live bankroll figures re-pulled this session. Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-11, DECISION_LOG.md 2026-07-11 (merge judgment-call row), TODO_NEXT.md T-330/T-331 (✅ MERGED TO MAIN).

**Last reviewed (prior):** 2026-07-10 (Workstream B — T-322/T-323/T-324 close-out, session-end) — Resolved the edge-sign question to a new, more specific finding: extended `scripts/run_band_monitor.py` (T-322) to run the GG-100 edge-monotonicity Fisher test + calibration reliability curve per band on `clean_n` only; found **T4M-PROJ ANTI-PREDICTIVE on clean data (Fisher p=0.024, registered GG-105, OPEN HIGH)** while **T1 reads INCONCLUSIVE** (underpowered, `clean_n=65`, not confirmed-negative). T-323 built `scripts/run_power_calc.py` computing `n*` (clean bets needed for 95%-power edge>0-vs-edge=0 discrimination) per band, feeding GG-004 directly — T4M-PROJ's higher cadence puts it materially closer to an adequately-powered verdict than T1. T-324 (analysis-only memo) traced the T1/T4M-PROJ sign divergence to cadence/window-length/power differences, not a modeling contradiction. Also registered GG-106 (`TestT1RegressionAnchor` drift, not yet investigated). **No deliverables-table impact — a methodology/monitoring finding, not a Phase 6 milestone line item, same treatment as prior sessions' infra/analysis entries.** Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-10 (Workstream B), DECISION_LOG.md 2026-07-10 (Workstream B row), GOVERNANCE_GAP_LOG.md GG-105/GG-106, TODO_NEXT.md T-322/T-323/T-324.

**Last reviewed (prior):** 2026-07-10 (T-320/T-321 close-out, session-end) — T-320 (logic-epoch write-path register) + T-321 (backfill + `clean_n`/`raw_n` reporting) both DONE end-to-end: merged, deployed, backfilled both live MLB portfolios (`MLB T1: raw_n=214 clean_n=65, MLB T2: raw_n=2 clean_n=0, MLB T4M-PROJ: raw_n=159 clean_n=159`), governance hook + C8 dashboard confirmed live. Discovered and mitigated **GG-104** (`deploy.yml` never restarts persistent systemd services `t4-mlb`/`pmbot-web-dashboard`, leaving T4M-PROJ silently running stale write-path code ~2 days post-merge); permanent fix registered as T-328 (not yet built; renumbered same-session from an initially-assigned T-322 after a concurrent-session claim collision was caught pre-push — see DECISION_LOG.md). **No deliverables-table impact — a governance/data-provenance infra build, not a Phase 6 milestone line item, same treatment as prior sessions' infra/bug-fix entries.** Full detail: MEMORY_BANK.md Current State Snapshot 2026-07-10, DECISION_LOG.md 2026-07-10 (three rows), GOVERNANCE_GAP_LOG.md GG-104, TODO_NEXT.md T-320/T-321/T-328. *(Previous, GG-102/T-261 closeout, session-end):* RESOLVED: `deploy.yml`'s dirty-tree guard regression (GG-073 whack-a-mole recurrence, `git status --porcelain` was blocking on ANY untracked file, not just modified tracked ones) fixed to `--untracked-files=no`, plus 3 VPS-live-regenerated tracked result files (`EXP-ARITH-MLB-01_results.json`, `EXP-FLOW-MLB-01_results.json`, `band_monitor_results.json`) untracked per operator direction (same shape as T-171). Self-caught and corrected a `git commit <pathspec>` no-op mid-fix (`b918f4b`→`9b06a31`). VPS content preserved/restored byte-identical. Confirmed fully green via manual `gh workflow run deploy.yml` (run `28984294745`, `success`) — first clean pass since the GG-073 regression. Committed `41e46b2`/`b918f4b`/`9b06a31`/`a53d65e`/`ffb56b3`, pushed. **No deliverables-table impact — a CI/git-hygiene fix, not a Phase 6 milestone line item, consistent with prior sessions' bug-fix entries.** No code, test, gate, phase, or bankroll changes. Full detail: GOVERNANCE_GAP_LOG.md GG-102 (RESOLVED), DECISION_LOG.md 2026-07-09, TODO_NEXT.md T-261 row. *(Previous, Terminal 2, session-end:)* T-255/T-257/T-258 DONE, GG-099's per-band monitor chain code-complete: `scripts/run_band_monitor.py` runs the GG-037/GG-077-safe Fisher edge-monotonicity + calibration-slope/CI/ECE checks per band (T1/T2/T3 from the band-tagged book, T4M-PROJ from the T-254 ledger), gated by `MIN_N=30` (GG-098). Live: T1 n=167 INCONCLUSIVE p=0.2462, T4M-PROJ n=273 INCONCLUSIVE p=0.2582 (first-ever T4M-PROJ coverage), no alarm. `tests/test_band_monitor.py` 19/19 passing, incl. the T-258 guardrail proving a synthetic NO-majority fixture cannot fool the monitor into repeating the GG-100 inversion. T-257: weekly cron entry added to `deploy/cron.conf` (warn-only, no auto-kill) — **not yet installed on the live VPS crontab**, flagged for next session. Committed `5da8a24`, pushed; no deliverables-table impact (a monitoring build, not a milestone line item). *(Previous, cowork Terminal 1 session, session-end:)* GG-100 (false ANTI-PREDICTIVE Fisher finding, n=169, p=0.0236) RESOLVED as a GG-077 sign-bug artifact, not a genuine no-alpha signal: `run_t177_edge_monitor.py` was loading each closed position's stored, YES-framed `fee_net_edge` field without correcting sign for NO-direction bets. Hardened the loader to recompute edge direction-aware via a new `_recompute_edge()` helper delegating to the audited `run_exp017_mlb.compute_fee_net_edge()`, added an `edge_source` field (`recomputed` vs `stored_fallback`) with a stderr warning on any fallback, added 3 regression tests (32/32 passing on `test_t177_edge_monitor.py`, including a permanent guard reproducing the old false-positive on the raw-stored-edge path), and re-ran live: verdict flips ANTI-PREDICTIVE (p=0.0236) → INCONCLUSIVE (p=0.2468). Explicitly did **not** touch the underlying negative P&L (real, variance-driven, unchanged) — only the mislabeled monotonicity verdict was the bug. GG-004 refreshed in the same pass: n=169, aggregate P&L −$44.76 (sign-flipped from +$15.23 at n=151), win rate 47.9%, framed as an open variance/sample question (GG-004 remains OPEN), not a re-litigated no-alpha verdict. Committed `016357e`, pushed, VPS deployed (manually-invoked script, no service restart required). No production `src/` files touched — this was a monitoring-script + governance-doc fix, so the full pytest suite count is unchanged from SESSION 127's 2,376 passed / 7 skipped / 1 pre-existing unrelated failure. T-255 (per-band anti-predictive + calibration monitor) remains the next item in the GG-099/GG-100 chain, unaffected by this fix since it already specs the direction-aware `compute_fee_net_edge()` helper. See MEMORY_BANK.md and TODO_NEXT.md SESSION 2026-07-08 (cowork Terminal 1) entries, DECISION_LOG.md 2026-07-08, and GOVERNANCE_GAP_LOG.md GG-100/GG-004 for full detail. *(Previous, SESSION 127 (session-end):)* T-253 DONE: added an explicit `band` field to `PaperTrader.open_position()`, threaded through all six write-path callers (T1/T2/T4/T4M-PROJ MLB + NBA T4 legacy), and backfilled the live MLB book from `forecast_id` prefix (`FCST-M`→T1, `T2-MLB`→T2, etc.) via `scripts/backfill_band_field.py`. This closes the last open item in GG-099's fix set — T-253/T-254/T-256 are now all DONE, GG-099 fully RESOLVED — and clears confound (b) (missing band-tagging) on GG-100's anti-predictive finding; confound (a) (GG-077 fee-sign no-op) remains open. No deliverables-table impact (a schema addition + backfill enabling per-band monitoring, not a new milestone line item, consistent with prior sessions' bug-fix entries). Committed `aa68437` (code) + `b99957c` (docs), pushed. VPS deployed: fast-forward to `aa68437` after clearing a content-verified-identical untracked leftover script; `t4-mlb.service` restarted with explicit operator confirmation (live-trading-interruption risk). Full test suite: 2,376 passed / 7 skipped / 1 pre-existing unrelated failure, up from 2,374 (2 new band-field tests). T-255 (per-band anti-predictive + calibration monitor) is now unblocked and is next in the GG-099/GG-100 chain. GG-004's n=151/n=169 baseline still needs a fresh refresh — not done this session. See MEMORY_BANK.md and TODO_NEXT.md SESSION 127 entries, DECISION_LOG.md 2026-07-08, and GOVERNANCE_GAP_LOG.md GG-099/GG-100 for full detail. *(Previous, SESSION 125 (session-end):)* T-256 fix (`run_t177_edge_monitor.py` repointed from the legacy NBA book to the live MLB book, GG-099 item 3 RESOLVED) surfaced a new ANTI-PREDICTIVE finding on the ACTIVE MLB book (n=169, Fisher p=0.0236, OR=0.350), registered as GG-100. Committed `691a978`, pushed. *(Previous, SESSION 124 (session-end):)* GG-095 (Brier drift ladder mismatch near the kill switch, `monitor.py` firing `ALERT_L4_KILL` instead of `ALERT_L3_PAUSE` at the `BRIER_L3_DELTA` crossing) RESOLVED via T-247. No deliverables-table impact (a C7 monitoring bug fix confirming the module's own already-intended 3-tier design, not a new milestone line item, same treatment as prior sessions' bug-fix entries). Full suite: 2,374 passed / 7 skipped / 1 pre-existing unrelated failure, up from 2,370. Committed `d854fd3`, pushed. VPS: `t4-mlb.service` needed no restart (doesn't import `monitor.py`); `pmbot-web-dashboard.service` restarted and confirmed healthy. Non-blocking follow-up surfaced to Earl (not built): whether `ALERT_L3_PAUSE` should gain real C4-enforced position-halt behavior. T-247 numbering briefly collided with a concurrent Opus-driven strategic session (EXP-017B/C/D + GG-098/ADR-0042); resolved via `SESSION_CLAIMS.md` reconciliation note, self-corrected by that session before this one closed. Operator noted (verbal, session close) a separate parallel strategic review is underway focused on calibrating the model math for edge extraction rather than continued infra/ops work — check for its output before defaulting to the existing governance-gap backlog. See MEMORY_BANK.md and TODO_NEXT.md SESSION 124 entries, DECISION_LOG.md 2026-07-07, and GOVERNANCE_GAP_LOG.md GG-095 for full detail.
**Next review:** Weekly; update on any milestone slip > 3 days; update at each gate  
**Staleness triggers:** Milestone complete; milestone slips; scope change; resource change  
**Upstream links:** ROADMAP_MILESTONES.md, REQUIREMENTS.md, ARCHITECTURE_OVERVIEW.md  
**Downstream links:** TODO_NEXT.md, RID_LOG.md, STATUS_REPORTS/  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Confidence:** 8/10 — G4 CLOSED 2026-05-28; Phase 5 Operational Readiness active; later phases planned at lower fidelity

---

## Phase 0 — Directory Scaffolding + Governance Spine ✅ COMPLETE

**Gate:** G0 Intent | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0002 signed 2026-05-22

### Phase 0 Work Plan

| # | Task | Owner | Due | Status | Blocker |
|---|------|-------|-----|--------|---------|
| 0.1 | Full directory skeleton | DS | 2026-05-21 | ✅ Done | — |
| 0.2 | 00_ADMIN complete (all 9 files + templates) | DS/PO | 2026-05-22 | ✅ Done | — |
| 0.3 | 01_SPEC complete (all 8 artifacts) | PO | 2026-05-22 | ✅ Done | — |
| 0.4 | 02_ARCHITECTURE_DESIGN complete | AO | 2026-05-22 | ✅ Done | — |
| 0.5 | 03_DECISIONS complete (ADR-0001, ADR-0002, registers) | DS | 2026-05-22 | ✅ Done | — |
| 0.6 | 04_EXECUTION complete (PLAN, TODO, RID) | EL | 2026-05-22 | ✅ Done | — |
| 0.7 | 05_RESEARCH_EXPERIMENTS complete | RL | 2026-05-22 | ✅ Done | — |
| 0.8 | 06_CODE_EXECUTION_REPRODUCIBILITY complete | AO | 2026-05-22 | ✅ Done | — |
| 0.9 | 07–10 modules complete | Multiple | 2026-05-22 | ✅ Done | — |
| 0.10 | 11_MEMORY_HANDOFF: MEMORY_BANK.md + baseline CP | DS | 2026-05-22 | ✅ Done | — |
| 0.11 | First DIR; health report | DS | 2026-05-22 | ✅ Done | — |
| 0.12 | G0 exit checklist complete | DS/PO | 2026-05-22 | ✅ Done | — |

### G0 Exit Criteria

- [x] Charter frozen (PROJECT_CHARTER.md — FROZEN status)
- [x] All 00_ADMIN artifacts in CANONICAL or FROZEN state
- [x] MEMORY_BANK.md initialized with all canonical links
- [x] Baseline Context Pack produced (CP-2026-05-22_baseline-handoff.md)
- [x] First DIR completed — M1 all artifacts stamped 2026-05-22 ✅
- [x] ADR-0001 and ADR-0002 accepted; APR-0002 signed 2026-05-22

---

## Phase 1 — Spec + Research Framing ✅ COMPLETE

**Gate:** G1 Spec | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0003 signed 2026-05-22

### Phase 1 Work Plan

| # | Task | Owner | Due | Status |
|---|------|-------|-----|--------|
| 1.1 | REQUIREMENTS.md frozen (all FR/NFR complete) | PO | 2026-05-31 | ✅ Done — FROZEN 2026-05-22 (T-010) |
| 1.2 | ACCEPTANCE_CRITERIA.md frozen | EO | 2026-06-01 | ✅ Done — FROZEN 2026-05-22 (T-011) |
| 1.3 | RESEARCH_QUESTIONS.md confirmed CANONICAL | RL | 2026-06-01 | ✅ Done (written at G0) |
| 1.4 | HYPOTHESES.md confirmed CANONICAL | RL | 2026-06-03 | ✅ Done (written at G0) |
| 1.5 | Player_Attribute_Matrix staged in 05_RESEARCH/ with snapshot header | RL | 2026-06-03 | ✅ Done — SNAP-001 registered 2026-05-22 |
| 1.6 | ADR-0002 confirmed (APR-0002 signed) | DS | 2026-05-22 | ✅ Done |
| 1.7 | ASSUMPTIONS_REGISTER.md populated (≥5 assumptions) | RL/AO | 2026-06-05 | ✅ Done (7 at G0) |
| 1.8 | OQ-001 resolved (Player_Attribute_Matrix provenance) | RL | 2026-06-03 | ✅ Done — resolved 2026-05-22; DATA_PROVENANCE.md updated |
| 1.9 | OQ-003 resolved (target market category) | RL/PO | 2026-06-01 | ✅ Done — NBA, dynamically agnostic, Kalshi primary; resolved 2026-05-22 |
| 1.10 | G1 exit checklist | PO/DS | 2026-06-07 | ✅ Done — all 5 criteria met; APR-0003 signed 2026-05-22 |

### G1 Exit Criteria

- [x] Requirements are testable (all FR/NFR have measurable acceptance criteria — REQUIREMENTS.md FROZEN)
- [x] Priorities are explicit (P0/P1/P2 designations confirmed — REQUIREMENTS.md FROZEN)
- [x] ASSUMPTIONS_REGISTER.md has ≥5 research assumptions (ASM-001 through ASM-007)
- [x] Target market category confirmed (OQ-003 resolved 2026-05-22 — NBA, dynamically agnostic, Kalshi primary)
- [x] Player_Attribute_Matrix provenance documented (OQ-001 resolved 2026-05-22 — DATA_PROVENANCE.md; SNAP-001)

---

## Phase 2 — Architecture + Infrastructure Design ✅ COMPLETE

**Gates:** G2 Architecture | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0004 signed 2026-05-22

### Phase 2 Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| ARCHITECTURE_OVERVIEW.md reviewed + promoted | AO | 2026-06-11 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| INTERFACES_CONTRACTS.md reviewed + promoted | AO | 2026-06-13 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| RESILIENCE_FAILURE_MODES.md reviewed + promoted | AO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| THREAT_MODEL.md reviewed + promoted; RCO sign-off | AO/RCO | 2026-06-15 | G2 | ✅ Done — CANONICAL 2026-05-22 |
| G2 gate signed (APR-0004) | AO | 2026-06-15 | G2 | ✅ Done — 2026-05-22 |

### G2 Exit Criteria

- [x] All core architecture artifacts CANONICAL (ARCHITECTURE_OVERVIEW, INTERFACES_CONTRACTS, RESILIENCE_FAILURE_MODES, THREAT_MODEL)
- [x] C4/C5 naming consistent across all architecture artifacts (C4=Risk Engine, C5=Execution Engine)
- [x] Interface contracts versioned and downstream-acknowledged
- [x] Technology stack confirmed (Python 3.11, JSON Lines logging, pip/pyproject.toml)
- [x] APR-0004 signed 2026-05-22

---

## Phase 2 (G3) — Execution Infrastructure Design ✅ COMPLETE

**Gate:** G3 Execution | **Completed:** 2026-05-22 | **Status:** ✅ Complete — APR-0005 signed 2026-05-22

### Phase 2/G3 Key Deliverables

| Deliverable | Owner | Due | Gate | Status |
|------------|-------|-----|------|--------|
| RUN_INSTRUCTIONS.md + ENVIRONMENTS.md reviewed + promoted | EL | 2026-06-17 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-026) |
| DEPENDENCY_LOCKS/ confirmed | EL | 2026-06-17 | G3 | ✅ Done — confirmed at G3 |
| PLAN.md + RID_LOG.md baselined | EL | 2026-06-19 | G3 | ✅ Done — CANONICAL 2026-05-22 (T-027) |
| ADR-0003 formal acceptance (pending OQ-006) | AO | 2026-06-21 | G3 | ⚠️ Excepted — OQ-006 operator action; gate closed with exception |
| G3 gate signed (APR-0005) | EL/DS | 2026-06-21 | G3 | ✅ Done — 2026-05-22 |

### G3 Exit Criteria

- [x] RUN_INSTRUCTIONS.md CANONICAL — environment setup and pipeline run commands documented (Python 3.11, venv, requirements-dev.txt, pre-commit)
- [x] ENVIRONMENTS.md CANONICAL — ENV-01/02/03 defined; environment variables confirmed; health checks documented
- [x] RID_LOG.md baselined at G3 — RID-D002/D003 archived (OQ-001/003 resolved); RID-D001 updated (ADR-0003 skeleton); RID-003 partially mitigated
- [x] PLAN.md baselined for Phase 3 entry
- [⚠️] ADR-0003 formal acceptance — skeleton CANONICAL PENDING; OQ-006 excepted per standing operator authorization; must resolve before Phase 3 data integration

---

## Phases 3–4 — ✅ COMPLETE (2026-05-22 – 2026-05-28)

**Phase 3 (Research Build):** G3 CLOSED 2026-05-22 — C1–C6 implemented; ADR-0003 accepted  
**Phase 4 (Evidence Capture):** G4 CLOSED 2026-05-28 — TEST Brier +0.0084/ECE 0.0247; ADR-0004 ACCEPTED (APR-0012)

| Deliverable | Owner | Status |
|------------|-------|--------|
| ADR-0003 formal acceptance | AO | ✅ 2026-05-23 — APR-0011 |
| C1–C6 implementation | EL | ✅ 2026-05-26 — T-032/033/034 |
| EXP-001/002/003 (50-player, SNAP-2026-05-28-001) | RL | ✅ 2026-05-28 — T-043; G4 criteria MET |
| FEATURE_VERSION 1.2.0 (31 features, HYP-005 falsified) | EL | ✅ 2026-05-28 — T-046 |
| ADR-0004 (LR+Platt model class confirmation) | AO | ✅ 2026-05-28 — T-047; APR-0012 ACCEPTED |
| G4 TEST set evaluation | MV | ✅ 2026-05-28 — T-048; Brier +0.0084/ECE 0.0247/AUC 0.6062 |

## Phase 5 — Operational Readiness ✅ COMPLETE

**Gate:** G5 Operational | **Closed:** 2026-05-28 | **Status:** ✅ APR-0007 ACCEPTED

| Deliverable | Owner | Status |
|------------|-------|--------|
| C7 Monitoring + Kill Switch (T-049) | EL | ✅ 0.340ms drill; APR-0013 |
| C8 Visual Dashboard (T-050) | EL | ✅ 3 panels; CLI |
| Kill switch drill TC-007 (T-051) | EL/DS | ✅ KS-C8D7D90AF942 |
| EXP-004 HYP-003 Parts A+B (T-052) | RL | ✅ EV +$0.0855/bet; CONFIRMED |
| Sensitivity tests ST-001–004 (T-053) | MV | ✅ All PASS |

---

## Current Phase: Phase 6 — Paper Trading

**Gate:** G6 Release (live capital) | **Started:** 2026-05-29 | **Status:** 🟢 Active

### Phase 6 Key Deliverables

| Deliverable | Owner | Priority | Status |
|------------|-------|----------|--------|
| Model data refresh 5 seasons (T-058) | EL | HIGH | ✅ 2026-05-28 — EXP-005; Brier +0.0024; v1-9939a6a5 |
| Qualitative pipeline (QS + EXP-006–008) | RL | HIGH | ✅ 2026-05-28/29 — EXP-007 +0.0017 Brier CONFIRMED |
| Gradient boosting experiment (T-065/EXP-011) | EL | MED | ✅ 2026-05-29 — LR RETAINED; ADR-0004 unchanged |
| EV re-estimation (T-069/EXP-010) | RL | HIGH | ✅ 2026-05-29 — +$0.0958/bet; 61.1% win rate |
| VPS provisioning (T-059) | IO | HIGH | ✅ 2026-05-29 — 157.230.91.33; cron active |
| Paper trading pipeline PIPE-03 (T-060) | EL | HIGH | ✅ 2026-05-29 — $1,000 bankroll; running |
| Accumulate paper evidence ≥66 bets / ≥5 nights (T-110, APR-0017) | DS | HIGH | 🟡 IN PROGRESS — T1: 114+29(G5 open)/66 bets ✓; G5 closes 5/5 game nights ✓; GG-004 OPEN (EXP-017B DIRECTIONAL_NEGATIVE, -$0.0361/bet vs Kalshi prices); GG-014 BREACHED (9/29=31% G5 order failures, T-164 registered); VPS bankroll $285.27; ADR-0023 deployed |
| PIPE-07 T4 in-play paper trading (PIPE-07) | EL | HIGH | ✅ 2026-06-08 SESSION 37 — portfolio isolation fix, cron.conf 23:00 UTC, PIPE-07R-LOCAL script |
| ADR-0005 live capital authorization (T-061) | AO/DS | LOW | 🔲 After paper evidence |

---

## Phases 3–9 — High-Level Plan

| Phase | Key Work | Gate | Target |
|-------|----------|------|--------|
| 3 Research Build | C1–C3 pipeline; first experiment; backtesting framework | — | **2026-06-21** (compressed — NBA playoffs end) |
| 4 Validation | G4 evidence collection; model card; drift thresholds confirmed | G4 | 2026-08-23 |
| 5 Operational Readiness | C7 wired; kill switch drilled; secrets vault; G5 ops gate | G5 | 2026-09-13 |
| 6 Paper Trading | Full simulated cycle; N events; paper results collected | — | 2026-10-25 |
| 7 Promotion Gate | Paper evidence reviewed; G6 readiness checklist | G6 | 2026-12-06 |
| 8 Live Capital | Real orders; drawdown tracking; governance in steady state | — | 2027-Q1 |
| 9 Self-Service Governance | Automated DIR; quarterly retrieval drills; continuous ops | — | From Phase 8 |

---

## Planning Assumptions

1. Single operator (Earl Ignacio) across all roles
2. Timeline contingent on Player_Attribute_Matrix validation (if falsified at Phase 3, G4 date shifts)
3. Venue selection (ADR-0003) could shift Phase 3 start by 1–2 weeks
4. All dates assume no major operational incident requiring remediation
