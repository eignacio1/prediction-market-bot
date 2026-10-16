# GG burn-down ledger (`/gap-agent`)

Purpose: PLUMBING, scored — OPEN gaps before → after, per tick. Procedure: `.claude/commands/gap-agent.md`.

## Per-tick totals
| Tick | Time (UTC) | OPEN before → after | Closed A / B / C | Triaged | PRs |
|---|---|---|---|---|---|
| 1 | 2026-10-16T00:25Z | log 186 → 185 exact-OPEN (GG-429 resolved); governance-scan count was 164, re-read next tick | 1 / 0 / 0 | 7 | branch session/20261016T000911Z-gap-agent; also retired 23 resolved-class entries to archive (211 retained; parity 212=212, uniqueness OK) |

## Ledger
| GG | Sev | Class | Evidence / reason | Next owner | Tick |
|---|---|---|---|---|---|
| GG-429 | HIGH | A → RESOLVED | Fix is in `Live Terminal.html` (49.2 `1594b36`); box at `0a44b8f5` carries it (lines 334/340/341/383); dashboard active since 00:08Z, NRestarts=0 | — | 1 |
| GG-170 | CRITICAL | L | External MLB gameLog date instability; fix touches live resolver `run_resolve_mlb.py` (pin dated query + cross-check) — not a ≤20-min safe fix | Window block | 1 |
| GG-417 | HIGH | O | Fix is a `session_guard.sh` stale-lock check = hook file (never-list). Recommend operator-approved add | Operator | 1 |
| GG-611 | HIGH | L | EXP-040 forecaster/runner/registry cell/deploy; touches EXP-039 NBA runner | Window block | 1 |
| GG-740 | HIGH | L | Needs registry wired into governance scan + review of 75 auto-classified entries vs live crontab | Window block | 1 |
| GG-741 | HIGH | O | Close condition (two waves in new format + handoff extends log) is a window judgement; W75/W76 appear in format and log has W19/W20. Recommend window closes it | Window | 1 |

## Operator lines
- GG-417: approve adding a stale `.git/index.lock` check (age>10min, no live git) to `.claude/hooks/session_guard.sh` — hook edits are outside this agent's remit.
- GG-741: recommend the strategic window verify the format condition and resolve.

## Large (for waves)
- GG-170 — pin `run_resolve_mlb.py` gameLog query to dated split + cross-check totals; ~1 session; PROOF integrity.
- GG-611 — wire EXP-040 shadow logging (forecaster, runner, registry cell, injury fetch, deploy); ~1 session; BREADTH/DEPTH.
- GG-740 — registry into governance scan + review 75 entries; ~1 session; PLUMBING.
