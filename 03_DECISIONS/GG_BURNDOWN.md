# GG burn-down ledger (`/gap-agent`)

Purpose: PLUMBING, scored — OPEN gaps before → after, per tick. Procedure: `.claude/commands/gap-agent.md`.

## Per-tick totals
| Tick | Time (UTC) | OPEN before → after | Closed A / B / C | Triaged | PRs |
|---|---|---|---|---|---|
| 1 | 2026-10-16T00:25Z | log 186 → 185 exact-OPEN (GG-429 resolved); governance-scan count was 164, re-read next tick | 1 / 0 / 0 | 7 | branch session/20261016T000911Z-gap-agent; also retired 23 resolved-class entries to archive (211 retained; parity 212=212, uniqueness OK) |
| 2 | 2026-10-16T01:00Z | log 185 → 185 exact-OPEN (no A/B found among the 25 triaged); scan count not re-read this tick | 0 / 0 / 0 | 25 (15 HIGH bucketed + 10 UNSPECIFIED severities filled) | branch session/20261016T000911Z-gap-agent |
| 3 | 2026-10-16T02:00Z | log 185 → 185 exact-OPEN (no A/B yet; GG-156/158 queued as A-candidates pending read-only ssh) | 0 / 0 / 0 | 24 (10 severities filled + 14 bucketed) | branch session/20261016T000911Z-gap-agent |
| 4 (GA-5 tick 1) | 2026-10-22T02:40Z | grep-exact OPEN 207 → 206 (GG-890 A; 6 other resolved-class entries retired, no OPEN change) | 1 / 0 / 0 | 9 (all 28 HIGH + CRITICAL carry an owner; 4 new HIGH bucketed; 3 box-read candidates tested) | session/20261022T021353Z-gap-agent |

## Ledger
| GG | Sev | Class | Evidence / reason | Next owner | Tick |
|---|---|---|---|---|---|
| GG-429 | HIGH | A → RESOLVED | Fix is in `Live Terminal.html` (49.2 `1594b36`); box at `0a44b8f5` carries it (lines 334/340/341/383); dashboard active since 00:08Z, NRestarts=0 | — | 1 |
| GG-170 | CRITICAL | L | External MLB gameLog date instability; fix touches live resolver `run_resolve_mlb.py` (pin dated query + cross-check) — not a ≤20-min safe fix | Window block | 1 |
| GG-417 | HIGH | O | Fix is a `session_guard.sh` stale-lock check = hook file (never-list). Recommend operator-approved add | Operator | 1 |
| GG-611 | HIGH | L | EXP-040 forecaster/runner/registry cell/deploy; touches EXP-039 NBA runner | Window block | 1 |
| GG-740 | HIGH | L | Needs registry wired into governance scan + review of 75 auto-classified entries vs live crontab | Window block | 1 |
| GG-741 | HIGH | O | Close condition (two waves in new format + handoff extends log) is a window judgement; W75/W76 appear in format and log has W19/W20. Recommend window closes it | Window | 1 |
| GG-038 | HIGH | W | Kill-switch latency (ADR-0060) verification overlaps W76.1 kill-switch drill (GG-745) | W76.1 | 2 |
| GG-046 | HIGH | O | T4 independent validation track; already marked Blocked-On-Operator | Operator | 2 |
| GG-172 | HIGH | O | Band-activation boxes for MARKET_EXPANSION_ACTION_PLAN = strategy/plan decision | Operator/window | 2 |
| GG-189 | HIGH | L | 46 stuck-open T4M-PROJ positions need live-ledger row corrections (never-list) | Window block | 2 |
| GG-190 | HIGH | L | Root-cause investigation of game_date corruption onset; no new evidence | Window block | 2 |
| GG-204 | HIGH | O | Needs superseding ADR for ADR-0028 G6 closure condition (ADRs immutable) | Operator | 2 |
| GG-295 | HIGH | O | Provenance review of undocumented live-ledger backfill (42 NFL rows) | Operator | 2 |
| GG-296 | HIGH | W | Persisting rejections touches paper_trader/ledger writers (W76.3 ownership) | W76.3 | 2 |
| GG-301 | HIGH | L | Re-run t571 Variant B once fill confirmation expands; blocked on GG-300 | Window block | 2 |
| GG-312 | HIGH | L | Backfill ~36 APPROVALS_REGISTER rows: needs per-ADR research, risk of misattributing approvals | Window block | 2 |
| GG-316 | HIGH | L | Add run_id/host/trigger to NFL T1 rows and audit events (ledger writer change) | Window block | 2 |
| GG-320 | HIGH | O | T4M-PROJ band placement (ADR-0068 C5) | Operator | 2 |
| GG-333 | HIGH | O | Run pre-registered D3 on fresh family (pre-registration) | Operator | 2 |
| GG-441 | HIGH | W | Kill switch input/persistence overlaps W76.1 drill | W76.1 | 2 |
| GG-745 | HIGH | W | Kill switch single-switch work = W76.1 (drill on running processes) | W76.1 | 2 |
| GG-004 | HIGH (was UNSPECIFIED) | L | G6 sample-adequacy blocker; accrues with data, re-run run_power_calc.py | Window | 2 |
| GG-027 | LOW (was UNSPECIFIED) | L | Entry impact says LOW now; NBA dark | NBA preseason | 2 |
| GG-037 | HIGH (was UNSPECIFIED) | L | Anti-predictive edge (alpha half unexplained); fold into NBA preseason | NBA preseason | 2 |
| GG-039 | MEDIUM (was UNSPECIFIED) | L | Entry impact says MEDIUM (design gap) | NBA preseason | 2 |
| GG-040 | LOW (was UNSPECIFIED) | L | Entry impact: LOW now (HIGH pre-Phase 8) | NBA preseason | 2 |
| GG-041 | LOW (was UNSPECIFIED) | L | Entry impact says LOW; data not recoverable | NBA season capture | 2 |
| GG-066 | MEDIUM (was UNSPECIFIED) | O | Blocks event-driven T4 sub-bands; needs a C1 feed decision | Operator | 2 |
| GG-078 | LOW (was UNSPECIFIED) | L | Moot while kelly_fraction is 0.0 (ADR-0048); reopens on reactivation | At reactivation | 2 |
| GG-094 | HIGH (was UNSPECIFIED) | L | MLB has no qualitative layer: the DEPTH pillar gap | Window block | 2 |
| GG-105 | HIGH (was UNSPECIFIED) | L | Significant anti-predictive tercile in the only ACTIVE band; retest on clean_n=1898 | Window block | 2 |
| GG-133 | LOW (was UNSPECIFIED) | C-later | CHANGELOG stale ~6wk; doc-only, window-owned nav | Window | 3 |
| GG-134 | MEDIUM (was UNSPECIFIED) | L | MC report limitations section | Window block | 3 |
| GG-137 | LOW (was UNSPECIFIED) | L | Depends on GG-105 retest | GG-105 | 3 |
| GG-140 | MEDIUM (was UNSPECIFIED) | L | Depends on GG-105 retest | GG-105 | 3 |
| GG-150 | LOW (was UNSPECIFIED) | O | Blocking control for cross-book conflicts is an operator decision | Operator | 3 |
| GG-151 | LOW (was UNSPECIFIED) | C-later | Post-merge duplicate-row check; touches hooks/claims, needs care | Later tick | 3 |
| GG-156 | HIGH (was UNSPECIFIED) | A-candidate | Needs read-only ssh check of PRICE_ARCHIVE continuity before close | Next tick | 3 |
| GG-157 | HIGH (was UNSPECIFIED) | L | paper_trader fill/depth validation; EXECUTION pillar | Window block | 3 |
| GG-158 | MEDIUM (was UNSPECIFIED) | A-candidate | Needs read-only check of off-VPS archive copy recency | Next tick | 3 |
| GG-160 | MEDIUM (was UNSPECIFIED) | L | Citation resolver build | Window block | 3 |
| GG-098/154/161/164/192/196/224 | - | L | Same-file or multi-session work (161 shares run_resolve_mlb.py with GG-170; 224 has no service-side ADR-0061 enforcement) | Waves | 3 |
| GG-153/168/174/202/206/216 | - | O | Need operator/window call (206: sibling outcome store is laptop-only and git-ignored) | Operator | 3 |
| GG-209 | - | W | Wave-owned | Wave | 3 |
| GG-890 | HIGH | A → RESOLVED | Box read-only 2026-10-21/22: `nba_autoflip.log` 8 + 4 promotions = 12/12 NBA game cells; `nba_pregame_shadow_t1.log` run 20261022T001104Z wrote all four NBA game families; box HEAD ff415aca | — | 4 |
| GG-302 | HIGH | L | NFL T1 42-row actor provenance (ledger forensics, live-ledger adjacent); pairs with GG-295/316 | Window block | 4 |
| GG-1010 | HIGH | L | NHL pre-game starting goalie: forward-only timestamped capture of NHL lines/probable-starter pages; a new cron = new running component (never-list for this agent) | Window (NHL depth lane) | 4 |
| GG-1030 | HIGH | W | NBA CDN 403 from box = 84.1 owned (`nba_lineup_window_capture.py`, injury-report route) | W84.1 | 4 |
| GG-038 | HIGH | O | ADR-0060 ACCEPTED as target architecture only, "not authorized to build now"; W76.1 drill (GG-745) shows 29.5 s worst-case halt, inside NFR-03 60 s but not the ≤5 s T4 target. Stays OPEN; operator owns the build trigger | Operator | 4 |
| GG-441 | HIGH | L | monitor.py l.34-35 still realized-loss-only, in-memory (W59.1 note, code unchanged); needs kill-switch input + persistence change in C4/C7 | Window block | 4 |
| GG-346 | MEDIUM | tested, NOT moot | schedule_validator_mlb.log still logs HTTP 406 as of 2026-10-21 08:30Z (128 occurrences); fix = request headers in the validator, class C candidate next tick | Next tick (C) | 4 |
| GG-348 | LOW | tested, NOT moot | t4-mlb.timer still inactive, last fired 2026-07-04; t4-mlb.service active. Still true | Later (C: doc/unit cleanup) | 4 |
| GG-262/676 | LOW/MED | tested, NOT moot | live crontab `run_mlb_pregame` 22:15 vs repo mirror 18:45; drift persists. Season end does not change it | Window (cron mirror) | 4 |

## Operator lines
- GG-417: approve adding a stale `.git/index.lock` check (age>10min, no live git) to `.claude/hooks/session_guard.sh` — hook edits are outside this agent's remit.
- GG-741: recommend the strategic window verify the format condition and resolve.
- GG-046, GG-172, GG-204, GG-295, GG-320, GG-333, GG-066, GG-150, GG-153, GG-168, GG-174, GG-202, GG-206, GG-216: each needs an operator/window call (see ledger rows).
- Intake note: handoffs mention tensions registered without GG ids (W76 NFL/NBA tension registers); the window may assign ids if wanted.

## Operator lines (tick 4 add)
- GG-038: ADR-0060 build trigger is yours; the drill shows 29.5 s worst-case halt, so NFR-03 holds today. Recommend leaving OPEN until T4M-PROJ is reactivated.

## Large (for waves)
- GG-170 — pin `run_resolve_mlb.py` gameLog query to dated split + cross-check totals; ~1 session; PROOF integrity.
- GG-611 — wire EXP-040 shadow logging (forecaster, runner, registry cell, injury fetch, deploy); ~1 session; BREADTH/DEPTH.
- GG-740 — registry into governance scan + review 75 entries; ~1 session; PLUMBING.
- GG-189/190 (live-ledger fixes, game_date root cause), GG-301, GG-312 (register backfill), GG-316 (NFL run provenance), GG-094/105 (MLB depth/anti-predictive): each ~1 session.
- GG-302, GG-441, GG-1010 — see ledger rows (tick 4); each ~1 session.

## Tick 5 (manual burn-through, 2026-10-22)
- GG-765 RESOLVED: register rows for ADR-0070..0075 + APR-0034..0036 added, APR-0007/0016 evidence repointed; `check_register_parity.py` CLEAN (93 docs).
- GG-346 stays OPEN: ISO-date fix + regression test landed in repo (box read-only test: ISO 200, MM/DD/YYYY 406); closes after deploy and a clean box run.
- OPEN 206 -> 205.

## Sweep tally
| Sweep | OPEN before -> after | Ids closed / re-filed |
|---|---|---|
| GS-3 (2026-10-22) | 210 -> 199 | Closed: GG-233, GG-258, GG-292, GG-420, GG-195, GG-260, GG-350 (shared-folder protocol). Re-filed WATCH ITEM: GG-285, GG-328, GG-624, GG-078 |
| W89.6 batch 1 (2026-10-26) | 213 -> 210 | Closed with evidence: GG-229, GG-426, GG-352; closed on PR #341 merge: GG-430, GG-691 |
| W89.6 batch 2 (2026-10-26, operator-decision) | 210 -> 205 | Closed: GG-309, GG-306 (CLAUDE.md edits). Re-filed WATCH ITEM: GG-415, GG-842, GG-216. Notes only, still OPEN: GG-289 (LOW), GG-342 (prune list awaits OK), GG-570 (0 NBA shadow_order rows), GG-153, GG-204 (ADR-0057 s4 is the operator choice). Pending PR #347: GG-452 |

## Sweep lists
- GS-3 class P (closed with evidence): GG-233, GG-258, GG-292, GG-420.
- GS-3 class O (WATCH ITEM): GG-285, GG-328, GG-624, GG-078.
- GS-3 skipped: GG-234/243/256/353/422 (C, claim_session/check_id_collision code), GG-342 (31 unmerged remote branches, none provably on main), GG-195/260/349/350/417 (shared-tree drift, retirement not authorized), GG-409/418/312/763/299/327/041/266/045/410/423/330/331/691 (C, L or operator), E-class engine gaps untouched.
- GS-3 follow-up: GG-349/GG-417 (index.lock, session_guard.sh check) remain OPEN, class C, not drift.
- W89.6 class C worked: GG-229, GG-426 (already fixed), GG-352 (doc line), GG-430, GG-691 (PR #341). Skipped: GG-842 (live runner message), GG-309 (CLAUDE.md edit needs operator), GG-452 (needs VPS pip freeze), GG-415 (cron/box change). E-class engine gaps untouched.

## Tick GA-6.1 (2026-11-18)
OPEN 272 -> 270. Closed A: GG-230 (check script reads 73 chars, was 5159). Closed B: GG-1452 (duplicate of GG-1462).
Triaged, not closed: GG-1939/1940/1935/1942/1952 are W118-wave-owned (class W; fixes in flight, box trace pending). GG-1480 NOT moot (DOCS_ONLY_ROOTS still omits 12_EXPLORATORY/; vps_deploy.sh is a running component, so class L/window). GG-133 NOT moot (CHANGELOG last entry 2026-05-30). GG-1032 NOT moot (local python 3.9.6, no tomllib).
Large add: GG-1480 (one-line roots edit in vps_deploy.sh plus a box read-back; window).

## Tick GA-6.2 (2026-11-18)
OPEN 270 -> 268. Closed A: GG-1440 (start_grace_h=0.5, 152f076 ancestor of box HEAD 53c83e86), GG-757 (invariants moved into tests/test_nfl_engine_v0.py). GG-759 left: the BOT_ENV comment cannot be checked without reading the box .env (blocked by permissions); next tick can read it via a box task.

## Tick GA-6.3 (2026-11-18)
OPEN 268 -> 266. Closed A: GG-892 (PR #275 ancestor of box HEAD 53c83e86), GG-891 (12/12 NBA game cells flipped, GG-890 box read). Still true, not closed: GG-1774 (2 flock -w 240 lines in deploy/cron.conf, no log on timeout; cron.conf is a running component, window), GG-1001, GG-1231, GG-406 (needs box read).


## GA-6 bulk pass (2026-11-18, OPEN 266 at start)

Mechanical pass: files exist, PRs merged, SHAs ancestors of origin/main. Class counts: C 160 · O 72 · W 21 · L 9 · A 1 (GG-452 closed). The C rows have NO closure proof yet: the pass only shows what each names. Classes are rule-based (id range, wave) and are not read-verified except GG-452.

| id | sev | first date | class | evidence |
|---|---|---|---|---|
| GG-004 | H | 26-06-01 | C | no mechanical closure signal; needs manual read |
| GG-007 | L | 26-06-02 | C | no mechanical closure signal; needs manual read |
| GG-027 | L | 26-05-28 | C | no mechanical closure signal; needs manual read |
| GG-037 | H | 26-06-16 | C | no mechanical closure signal; needs manual read |
| GG-038 | H | 26-07-15 | C | no mechanical closure signal; needs manual read |
| GG-039 | M | 26-07-15 | C | no mechanical closure signal; needs manual read |
| GG-040 | L | 26-07-15 | C | no mechanical closure signal; needs manual read |
| GG-041 | L | 26-06-02 | C | no mechanical closure signal; needs manual read |
| GG-045 | L | 26-06-26 | C | no mechanical closure signal; needs manual read |
| GG-046 | H | 26-06-26 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-066 | M | 26-07-02 | C | no mechanical closure signal; needs manual read |
| GG-094 | H | 26-07-06 | C | no mechanical closure signal; needs manual read |
| GG-098 | M | 26-07-06 | C | no mechanical closure signal; needs manual read |
| GG-105 | H | 26-07-10 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-133 | L | 26-05-30 | C | no mechanical closure signal; needs manual read |
| GG-134 | M | 26-07-22 | C | no mechanical closure signal; needs manual read |
| GG-137 | L | 26-07-22 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-140 | M | 26-07-16 | C | no mechanical closure signal; needs manual read |
| GG-150 | L | 26-07-31 | C | no mechanical closure signal; needs manual read |
| GG-151 | L | 26-07-15 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-153 | M | 26-07-15 | C | no mechanical closure signal; needs manual read |
| GG-154 | M | 26-07-29 | C | no mechanical closure signal; needs manual read |
| GG-156 | H | 26-07-30 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-157 | H | 26-07-31 | C | no mechanical closure signal; needs manual read |
| GG-158 | M | 26-08-01 | C | no mechanical closure signal; needs manual read |
| GG-160 | M | 26-07-30 | C | no mechanical closure signal; needs manual read |
| GG-161 | M | 26-08-04 | C | no mechanical closure signal; needs manual read |
| GG-162 | L | 26-07-07 | C | no mechanical closure signal; needs manual read |
| GG-164 | M | 26-07-02 | C | no mechanical closure signal; needs manual read |
| GG-165 | L | 26-08-05 | C | no mechanical closure signal; needs manual read |
| GG-167 | L | 26-08-07 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-168 | M | 26-08-07 | C | no mechanical closure signal; needs manual read |
| GG-170 | C | 26-08-03 | C | no mechanical closure signal; needs manual read |
| GG-172 | H | 26-06-04 | C | no mechanical closure signal; needs manual read |
| GG-174 | M | 26-08-13 | C | no mechanical closure signal; needs manual read |
| GG-177 | L | 26-08-14 | C | no mechanical closure signal; needs manual read |
| GG-183 | L | 26-08-15 | C | no mechanical closure signal; needs manual read |
| GG-187 | L | 26-07-05 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-189 | H | 26-07-02 | C | no mechanical closure signal; needs manual read |
| GG-192 | M | 26-05-29 | C | no mechanical closure signal; needs manual read |
| GG-196 | M | 26-08-04 | C | no mechanical closure signal; needs manual read |
| GG-190 | H | 26-08-02 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-202 | M | 26-08-21 | C | no mechanical closure signal; needs manual read |
| GG-206 | M | 26-08-17 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-209 | M | 26-08-26 | C | no mechanical closure signal; needs manual read |
| GG-224 | M | 26-08-28 | C | no mechanical closure signal; needs manual read |
| GG-234 | L | 26-09-01 | C | no mechanical closure signal; needs manual read |
| GG-487 | L | 26-10-07 | C | no mechanical closure signal; needs manual read |
| GG-730 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-731 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-732 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-733 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-734 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-740 | H | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-741 | H | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-747 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-748 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-749 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-750 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-752 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-754 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-755 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-756 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-758 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-759 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-760 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-761 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-762 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-763 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-764 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-766 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-775 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-776 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-777 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-778 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-779 | L | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-910 | M | 26-09-08 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-911 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-912 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-913 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-914 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1000 | L | 26-10-21 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1001 | L | 26-10-22 | C | no mechanical closure signal; needs manual read |
| GG-1260 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1261 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1895 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-243 | L | 26-07-07 | C | no mechanical closure signal; needs manual read |
| GG-256 | L | 26-07-07 | C | no mechanical closure signal; needs manual read |
| GG-257 | L | 26-09-07 | C | no mechanical closure signal; needs manual read |
| GG-261 | M | 26-09-05 | C | no mechanical closure signal; needs manual read |
| GG-262 | L | 26-09-09 | C | no mechanical closure signal; needs manual read |
| GG-266 | L | 26-09-09 | C | no mechanical closure signal; needs manual read |
| GG-275 | M | 26-09-11 | C | no mechanical closure signal; needs manual read |
| GG-279 | M | 26-09-11 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-289 | L | 26-09-18 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-295 | H | 26-09-17 | C | no mechanical closure signal; needs manual read |
| GG-296 | H | 26-08-13 | C | no mechanical closure signal; needs manual read |
| GG-298 | M | 26-07-02 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-299 | L | 26-07-16 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-301 | H | 26-07-31 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-304 | M | 26-09-24 | C | no mechanical closure signal; needs manual read |
| GG-307 | L | 26-09-24 | C | no mechanical closure signal; needs manual read |
| GG-312 | H | 26-07-17 | C | no mechanical closure signal; needs manual read |
| GG-316 | H | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-317 | M | 26-09-29 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-320 | H | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-323 | M | 26-07-02 | C | no mechanical closure signal; needs manual read |
| GG-326 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-327 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-330 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-331 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-332 | M | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-333 | H | 26-10-02 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-340 | M | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-341 | L | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-342 | L | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-344 | M | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-345 | M | 26-09-27 | C | no mechanical closure signal; needs manual read |
| GG-346 | M | 26-07-03 | C | no mechanical closure signal; needs manual read |
| GG-347 | M | 26-10-03 | C | no mechanical closure signal; needs manual read |
| GG-348 | L | 26-07-04 | C | no mechanical closure signal; needs manual read |
| GG-349 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-353 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-354 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-355 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-356 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-402 | L | 26-10-02 | C | no mechanical closure signal; needs manual read |
| GG-404 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-406 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-408 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-409 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-410 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-416 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-417 | H | 26-10-03 | C | no mechanical closure signal; needs manual read |
| GG-418 | L | 26-10-08 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-421 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-422 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-423 | L | 26-10-05 | C | no mechanical closure signal; needs manual read |
| GG-425 | L | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-452 | L | 26-05-22 | A | requirements-base.txt aligned to pyproject (sklearn 1.8.0, scipy 1.12.0) 2026-10-26; line 8 cites GG-452 |
| GG-538 | M | 26-10-09 | C | no mechanical closure signal; needs manual read |
| GG-529 | M | 26-10-08 | C | no mechanical closure signal; needs manual read |
| GG-1750 | M | 26-11-02 | C | no mechanical closure signal; needs manual read |
| GG-536 | M | 26-10-09 | C | no mechanical closure signal; needs manual read |
| GG-562 | L | 26-09-29 | C | no mechanical closure signal; needs manual read |
| GG-564 | M | 26-10-10 | C | no mechanical closure signal; needs manual read |
| GG-570 | L | 26-10-11 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-587 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-596 | M | 26-10-13 | C | no mechanical closure signal; needs manual read |
| GG-610 | M | 26-10-12 | C | no mechanical closure signal; needs manual read |
| GG-611 | H | ? | C | no mechanical closure signal; needs manual read |
| GG-588 | L | 26-10-12 | C | no mechanical closure signal; needs manual read |
| GG-630 | M | 26-07-28 | C | no mechanical closure signal; needs manual read |
| GG-620 | M | 26-10-13 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-621 | L | 26-10-13 | C | no mechanical closure signal; needs manual read |
| GG-670 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-671 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-673 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-674 | M | 26-10-20 | C | no mechanical closure signal; needs manual read |
| GG-675 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-676 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-677 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-690 | M | 26-10-14 | C | no mechanical closure signal; needs manual read |
| GG-800 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-801 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-850 | L | 26-10-16 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-885 | L | 26-10-16 | C | no mechanical closure signal; needs manual read |
| GG-970 | M | 26-07-23 | C | no mechanical closure signal; needs manual read |
| GG-971 | M | 26-10-20 | C | no mechanical closure signal; needs manual read |
| GG-985 | M | 26-10-20 | C | no mechanical closure signal; needs manual read |
| GG-990 | M | 26-10-21 | C | no mechanical closure signal; needs manual read |
| GG-1010 | H | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1011 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1012 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1013 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1014 | M | 26-10-14 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1030 | H | 26-10-21 | C | no mechanical closure signal; needs manual read |
| GG-1031 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1032 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1060 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1061 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1062 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1063 | L | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1064 | L | 26-10-18 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1090 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-1180 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-1181 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-1182 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-1183 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-1190 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-1191 | M | ? | C | no mechanical closure signal; needs manual read |
| GG-1192 | L | ? | C | no mechanical closure signal; needs manual read |
| GG-1230 | H | 26-10-04 | C | no mechanical closure signal; needs manual read |
| GG-1231 | M | 26-10-25 | C | no mechanical closure signal; needs manual read |
| GG-1232 | M | 26-10-20 | C | no mechanical closure signal; needs manual read |
| GG-1251 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1252 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1254 | M | 26-08-01 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1280 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1281 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1282 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1283 | L | 26-10-20 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1284 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1291 | L | 26-10-27 | C | no mechanical closure signal; needs manual read |
| GG-1331 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1332 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1333 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1334 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1300 | M | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1301 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1302 | L | 26-10-27 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1292 | M | 26-10-27 | C | no mechanical closure signal; needs manual read |
| GG-1293 | M | 26-10-27 | C | no mechanical closure signal; needs manual read |
| GG-1340 | M | 26-08-01 | C | no mechanical closure signal; needs manual read |
| GG-1341 | M | 26-10-28 | C | no mechanical closure signal; needs manual read |
| GG-1441 | L | 26-10-06 | C | no mechanical closure signal; needs manual read |
| GG-1460 | L | 26-10-29 | C | no mechanical closure signal; needs manual read |
| GG-1450 | M | 26-10-29 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-1451 | M | ? | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1461 | L | 26-10-29 | C | no mechanical closure signal; needs manual read |
| GG-1462 | L | 26-10-16 | C | no mechanical closure signal; needs manual read |
| GG-1420 | M | 26-10-28 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1390 | M | 26-10-28 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1393 | M | 26-10-28 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1394 | M | 26-10-28 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1395 | L | 26-10-28 | O | registered data/factor gap (doctrine: paid-only or absent factor stays a registered gap) |
| GG-1430 | L | 26-10-29 | C | no mechanical closure signal; needs manual read |
| GG-1431 | L | 26-10-29 | C | no mechanical closure signal; needs manual read |
| GG-1480 | L | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1481 | M | 26-10-12 | C | names merged PR/commit; fix present, closure evidence (box read or test) still needed |
| GG-1470 | M | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1471 | L | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1472 | L | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1520 | M | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1521 | M | 26-10-30 | C | no mechanical closure signal; needs manual read |
| GG-1522 | L | 26-10-30 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1580 | L | 26-11-03 | C | no mechanical closure signal; needs manual read |
| GG-1581 | H | 26-11-03 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1582 | L | 26-07-10 | C | no mechanical closure signal; needs manual read |
| GG-1600 | L | ? | L | needs box task / runtime change (never-list or >1 session) |
| GG-1690 | L | 26-11-04 | C | no mechanical closure signal; needs manual read |
| GG-1720 | M | 26-11-05 | L | needs box task / runtime change (never-list or >1 session) |
| GG-1773 | M | 26-11-05 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1774 | M | 26-11-05 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1896 | L | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1897 | M | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1898 | M | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1930 | L | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1931 | M | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1932 | L | 26-11-12 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1933 | M | 26-11-13 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1935 | M | 26-11-13 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1939 | H | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1940 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1951 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1952 | L | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1953 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1936 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1937 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1938 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1942 | H | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1943 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |
| GG-1944 | M | 26-11-17 | W | W113-W117 wave-owned (COMMON_RULES_W118) |

### GA-6 tick 5 (2026-11-18)
Closed GG-1462 (A). Checked, left open: GG-1581 (flock now on 6 box T3 lines, but OOM kills continued 2026-11-15, 9 in the kernel journal since 11-10, so the cause is not fully fixed), GG-1460 and GG-1461 (`_fence.py`/scan unchanged).

### GA-6 tick 6 (2026-11-18): read-all-C pass
Read all 151 C gaps individually. Closed GG-587, GG-596 (fix commits on box HEAD). Left open after check: GG-611 (box NBA player-points rows carry no EXP-040 sha c47cbac7 in the last 400KB), GG-348 (t4-mlb.timer still inactive on box; retire-or-rearm is a decision), GG-1230 (fix on box; no post-fix successful run visible in off-season). OPEN 264 -> 262.
