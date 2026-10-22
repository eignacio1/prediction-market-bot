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

## Sweep lists
- GS-3 class P (closed with evidence): GG-233, GG-258, GG-292, GG-420.
- GS-3 class O (WATCH ITEM): GG-285, GG-328, GG-624, GG-078.
- GS-3 skipped: GG-234/243/256/353/422 (C, claim_session/check_id_collision code), GG-342 (31 unmerged remote branches, none provably on main), GG-195/260/349/350/417 (shared-tree drift, retirement not authorized), GG-409/418/312/763/299/327/041/266/045/410/423/330/331/691 (C, L or operator), E-class engine gaps untouched.
- GS-3 follow-up: GG-349/GG-417 (index.lock, session_guard.sh check) remain OPEN, class C, not drift.
