# ADR-0074 — Process integrity: one owned map of the running system, fixes swept everywhere, a surface budget, and an accountable strategic window

**Status:** ACCEPTED (operator directive, 2026-10-14 17:01 PT: "These are big - project schema changes. I'm gonna have you take care of as much of the fixes right now since you have full context of this window - work institutionally ... Maintain high-fidelity - this touches a lot.") · **Date:** 2026-10-14 · **Gaps:** GG-740 (slice failure), GG-741 (window accountability) · **Rules:** CLAUDE.md Hard Rules 13–15

## Context — the two failure modes, named by the operator

On 2026-10-14 the operator asked why so many components were "loose/broken/non-functioning" that calibration was hard, and
whether it was his fault. The window's answer named two structural causes; he asked what exists to document and track them
and to prevent future oscillation. What the window found when it checked the repo:

**FM-1 — the slice failure (GG-740).** Hundreds of short sessions, each seeing a slice; a fix lands in one place and the same
bug survives in another; nobody owns the whole running system end to end. Evidence:

- GG-122 → GG-144: the same broken OPEN-gap grep was fixed in the hook (07-16) and left in CLAUDE.md's mandatory Step 3 for 13 days.
- GG-532: the MLB postseason arm was silent ~23 h, found by hand. GG-163: T4 wrote nothing for 43.5 h while `systemctl` said active.
- GG-661: deploys skipped restarts during live games and never retried, so t4-mlb ran pre-fix code with nothing flagging it.
- GG-203: the only evidence-producing cell was dark 38 days. Calibration data sat unread 39 days (MILESTONE_REFLECTIONS § V).
- 2026-10-14: building the registry found five cron jobs mirrored only in arm fragments and not in `deploy/cron.conf`, the file
  the audit treated as the live mirror.

What existed: session claims, handoffs, the governance scan, the silent-arm alarm (W62.1), the running-SHA alarm and healthcheck
(W72.3), and a fix-every-consumer rule scoped to data-contract HALTs only (GG-072). What did not: any single list of what runs,
or any rule that a fix searches for the same defect elsewhere.

**FM-2 — the unaccountable strategic window (GG-741).** Windows planned what was asked without pushing back ("this adds surface
faster than we can make it reliable"), escalated plumbing to the operator, asked him what their notes already held, and issued
blocks that collided. Evidence: `04_EXECUTION/WINDOW_ERROR_LOG.md` rows W1–W12 (seeded from this window, 2026-10-09 → 10-14).
What existed: the drift rule (Hard Rule 12, fired correctly at Wave 71) and a "What this window got wrong" section in each
carry-forward. What did not: a running, tallied record that the next window must read, or any rule tying breadth to reliability.

Not the operator's fault: his directives (expand to the whole board, integrate every bucket, $0) are the owner's to set. The
failure was that the windows did not state their cost in surface and did not build reliability as fast as surface.

## Decision

1. **Runtime registry (FM-1).** `02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml` lists every running component — each cron line
   in `deploy/cron.conf`, `deploy/cron.<name>`, `deploy/cron_*.conf` (only inside BEGIN/END install blocks for fragments),
   each systemd unit, each GitHub Actions workflow — with purpose, pillar, what it writes, the alarm that fires if it stops,
   status (live / paused / retired) and whether a human reviewed the entry. `scripts/runtime_registry.py` discovers components
   from the mirrors; `tests/test_runtime_registry.py` fails CI on any unregistered component, any live entry gone from the
   mirrors, or a stale `RUNTIME_MAP.md`. **A new running piece cannot land without an owner-readable entry.** Live columns
   (code SHA running, last write, alarm state) are added by the governance scan where it reaches the VPS.
2. **Pattern sweep (FM-1) — Hard Rule 13.** Every fix searches the repo for the same defect (src/, scripts/, tests/, deploy/,
   .claude/, the docs that restate commands) and reports it in the handoff's `pattern_sweep:` key — required by
   `generate_session_artifacts.py` for handoffs after 2026-10-15T12:00Z. GG-072's consumer rule becomes the general case.
3. **Surface budget (FM-1 + FM-2) — Hard Rule 14.** Surface = live components in the registry. Every wave states its surface
   delta. **No wave adds a live component while the health signals are red** — healthcheck faults, a silent arm while its sport
   had games, a running-SHA mismatch older than 6 h, or a registry entry with no alarm on a component the new one depends on —
   unless the wave's first block fixes the red. The sitrep carries a Surface row (live · unreviewed · with no alarm).
4. **Accountable window (FM-2) — Hard Rule 15.** The strategic window:
   - logs its own mistakes in `04_EXECUTION/WINDOW_ERROR_LOG.md` when it learns of them (append-only, tagged by pattern), and
     every incoming window reads it first and names the pattern it is most at risk of;
   - searches memory, project docs and the repo before asking the operator anything;
   - writes every wave with a **Pushback** line (the strongest reason not to run it as planned), a **Surface** line (delta and
     current red signals) and a **Dependencies** line (no block's merge or input may depend on another block of the same wave);
   - routes to the operator only pre-registration changes, frozen artifacts or books, real capital, and the open strategic
     questions — never demo/paper/shadow plumbing, never a command to run.

## Consequences

- CI now refuses a running component without a registry entry; 75 live components were registered on 2026-10-14 with
  auto-classified pillar and alarm (`reviewed = false`) — reviewing them is a terminal block (queue backlog, ADR-0074 block).
- Handoffs gain `pattern_sweep:` and `surface_delta:`; the template and `/session-end` say how.
- `/strategic-handoff` and the window paste-in now open with the error log and require the three wave lines.
- On 2026-10-14 the registry reported 21 live components with no alarm. That number is the first Surface debt to burn down.
- Not done in this window (needs a terminal with ssh and hook access): governance-scan integration of the registry, surface
  budget and live columns; review of the 75 auto entries against the live crontab; reconciling the five fragment-only jobs
  with `deploy/cron.conf`.
