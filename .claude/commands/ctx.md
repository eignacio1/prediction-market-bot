# /ctx — Full Project Context Restore

You are working on the **Prediction Market Trading Bot** (Kalshi venue; MLB, NFL, NHL, NBA). This command restores context
**from the files that carry live state** — it no longer embeds a snapshot, because the embedded one (2026-05-29) went four
months stale and was still being served as "full context" (archived: `11_MEMORY_HANDOFF/CTX_COMMAND_SNAPSHOT_2026-05-29.md`).

Read, in this order, then say "Context loaded." and give a five-line summary of where the project is:

1. `CLAUDE.md` — already in context if you are in Claude Code. Hold § "What winning looks like" (the operator's north star,
   four pillars) and the hard rules.
2. `04_EXECUTION/ACTIVE_QUEUE.md` — the **RUNNING SITREP** at the top (bottom line, pillar scoreboard, calendar, the operator's
   open calls), then **NOW** (the wave in flight) and **Needs your decision** (every authorization, as blockquotes).
3. `11_MEMORY_HANDOFF/MEMORY_BANK.md` — the "Where we are" box and the **Current State Snapshot** (dated).
4. If you are the strategic window: `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` in full.
5. Live counts, never from memory: run `.claude/hooks/governance_scan.sh` (gap log OPEN count, sample adequacy, SILENT ARMS),
   and read `MARKET_TYPE_REGISTRY` for cell status.

Treat every number in any document as a claim to verify against code, data or GitHub. If two sources disagree, the code and
the data win, and the disagreement is a finding to report.
