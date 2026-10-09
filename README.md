# Prediction Market Trading Bot

A calibration engine for probabilistic reasoning, structured as a trading bot. Prediction markets on Kalshi (MLB, NFL, NHL,
NBA) are the laboratory: binary outcomes, short feedback loops, and the market's own price as the benchmark. The question every
part of this repository serves: **does the model know something the market doesn't?** Paper and demo only — no real capital
until the G6 gate is cleared.

## Before you do anything here

Know what it is for. Every task in this project — a terminal block, a review, an outside model's audit, a reminder — names,
before it starts, which **distance-to-optimum** measure it is meant to move (breadth, depth, execution or proof; defined in
[`CLAUDE.md`](CLAUDE.md) § "What winning looks like", current values at the top of the RUNNING SITREP), or says plainly that it
is plumbing. If you cannot say what your task is for, stop and ask.

## If you are picking this up

1. **Where the project is right now:** the RUNNING SITREP at the top of [`04_EXECUTION/ACTIVE_QUEUE.md`](04_EXECUTION/ACTIVE_QUEUE.md)
   — bottom line, pillar scoreboard, calendar, the operator's open calls, and the wave in flight.
2. **What winning looks like:** [`CLAUDE.md`](CLAUDE.md) § "What winning looks like" — the operator's north star in four
   pillars (BREADTH, DEPTH, EXECUTION, PROOF). The same file holds the hard rules and the mandatory session-start protocol.
3. **Navigation:** [`00_ADMIN/README.md`](00_ADMIN/README.md) (where everything lives) and
   [`11_MEMORY_HANDOFF/MEMORY_BANK.md`](11_MEMORY_HANDOFF/MEMORY_BANK.md) (module index + dated state snapshot).
4. **Why things are the way they are:** [`03_DECISIONS/DECISION_LOG/DECISION_LOG.md`](03_DECISIONS/DECISION_LOG/DECISION_LOG.md)
   (newest at the bottom), the ADRs in `03_DECISIONS/`, and open gaps in
   [`03_DECISIONS/GOVERNANCE_GAP_LOG.md`](03_DECISIONS/GOVERNANCE_GAP_LOG.md).

Live counts (open gaps, sample adequacy, silent arms) come from `.claude/hooks/governance_scan.sh`, and cell status from
`MARKET_TYPE_REGISTRY` in `src/prediction_market_bot/c5_execution/market_type_registry.py` — never from a number written in a
document.

## How it is run

The operator directs; a strategic window (a Claude session) writes waves of three blocks into the active queue; terminal
sessions execute them and push to `main`. CI (`.github/workflows/`) runs the tests and deploys to the VPS; scheduled GitHub
Actions and VPS crons do anything that has to wait.
