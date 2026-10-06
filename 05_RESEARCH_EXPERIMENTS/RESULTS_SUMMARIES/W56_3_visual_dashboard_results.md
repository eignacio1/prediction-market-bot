# W56.3 — Visual Dashboard operational review (results)

**Status:** DONE · PR #168 merged, CI green · Deploy success (run 37393002195)
**t4-mlb restart decision (Deploy job summary, GG-432):** `not_needed -- no file imported by t4-mlb changed in this push`. Only `pmbot-web-dashboard` restarted.

## What shipped (live `/project`)
Health strip (one pill per area, each links to its section) plus five sections: Operations (cron arms, last run / last success), Data feeds (MLB games-cache stamp vs 26h limit), Services (t4-mlb and dashboard restarts, kernel OOM kills 7d, VPS HEAD vs origin/main, deploy-decision row), Books & risk (realized drawdown vs 20% kill switch, open positions, last write), Evidence clocks (rows and settled games vs pre-registered judged n; counts only). New code: `scripts/project_ops.py`; wiring in `scripts/generate_project_state.py`; tests `tests/test_project_ops.py` (17; full suite 3723 passed, 43 skipped).
Design bar: every row shows source and age; stale rows dimmed; missing = "no data"; colour = state only; monospace tabular numerals; phone breakpoint; SHADOW labelled as shadow, $0 stake stated.

## Before / after
- Before: `/Users/earlignacio/.claude/tmp/w56shots/project.before.png`
- After: `/Users/earlignacio/.claude/tmp/w56shots/project.after.png` (browser check: no console/page errors, no failed requests on `/` or `/project`).

## Findings surfaced by the new panels (not fixed here, per Hard Rule 11)
1. T1 MLB paper cron's last run ends in `DataContractViolation: PIPE-05 mlb_feature_csv staleness_halt: 8 days stale (halt threshold 7)`. The Operations row shows warn, last success "no data". Needs a GG/T registration.
2. Two real kernel OOM kills in 7d (2026-10-04T01:31Z, 2026-10-05T01:30Z) — GG-477 context.
3. NFL game-market paper book last written ~162h ago with 824 open positions; shown dimmed, not alarmed.
4. The deploy's t4-mlb decision exists only in the GitHub job summary; the row is honestly "no data" on the VPS.

## Not verified
Phone-width rendering was not re-screenshotted; the CSS breakpoint is in place and tested only by render tests.
