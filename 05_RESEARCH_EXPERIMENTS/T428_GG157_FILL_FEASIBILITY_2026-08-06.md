# T-428 / GG-157 — Fill-Feasibility Overlap Check + Sampling Requirement

**Date:** 2026-08-06
**Session:** T-428 (claimed as T-427; collided with a concurrent session's unrelated claim on that ID at claim time)
**Scope:** Read-only, analysis-only. No `src/` change. No depth capture added to the execution path.
**Data sources:** `logs/.vps_portfolio_cache_mlb_t4.json` (fresh VPS pull, synced within 1 min of session start), `exp_output/PRICE_ARCHIVE/depth_2026-08-04.jsonl` / `depth_2026-08-05.jsonl` / `depth_2026-08-06.jsonl` (all depth archive data that exists — capture began 2026-08-04T00:46:22Z per T-412; nothing exists before that date, GG-156, permanently unbackfillable).

## Task 1 — overlap between epoch-12 paper positions and archived depth

Epoch-12 (T4M-PROJ, the live flat-$1 measurement cohort) actually spans **2026-07-31T19:38:19Z to 2026-08-04T03:28:17Z** — later than the task brief's "2026-07-31 to 2026-08-02" estimate; the tail continues into 2026-08-04, which is the same UTC date depth capture began.

- 187 epoch-12 positions total, 113 unique `kalshi_ticker` values.
- 173 entered before depth capture started (2026-08-04T00:46:22Z) — zero possible overlap for these, GG-156 applies.
- **14 entries (10 unique tickers) were entered *after* depth capture started**, all on 2026-08-04 between 00:50:31Z and 03:28:17Z — a genuine temporal window where overlap was structurally possible.
- Checked all 10 of those tickers against every depth sample ever captured (all three days, 69 cron fires, 247 unique tickers seen total): **exact-ticker matches = 0.**

**Overlap is zero.** Not near-zero — zero, at the exact-ticker granularity a fill-validation check requires. This is a real, decision-relevant finding: no version of Task 2 (slippage measurement) can be performed for any real paper position placed to date. The historical ledger and the depth archive do not intersect.

**Root cause of the miss, not just its existence:** the archiver samples 2 tickers per family per run (12 tickers/run across 6 families, ~20-min cadence). A single-hour scan of the raw price archive (`prices_2026-08-04.jsonl`, 01:xx UTC) found **425 concurrently-live `KXMLBHIT` tickers** in that hour alone — one family. The depth sampler covers roughly 0.5-3% of the live `KXMLBHIT` universe per pass. Even during the 14 temporally-overlapping bets, the odds the sampler's 2-per-run pick happened to land on the exact ticker+threshold the bot traded were near-nil. Zero overlap is the expected outcome of this sampling design, not a coincidence.

## Task 2 — slippage measurement

Not performed. Task 1 found zero usable overlap; there is nothing to measure. Stating this plainly per the task's own instruction: a null Task 1 result makes Task 2 vacuous, not something to route around by loosening the match criterion.

## Task 3 — sampling requirement to close GG-157

Two independent resolution gaps, not one:

1. **Ticker coverage.** The archiver samples 2/family/run against a live universe of hundreds of tickers/family/hour. Closing GG-157 by cross-referencing an independent cron archive against the real bet ledger requires either (a) full-universe capture (every live ticker, every run) or (b) targeted capture keyed to exactly the tickers the bot is evaluating — (b) is far cheaper and is what a real fill-validation check actually needs.
2. **Temporal resolution.** GG-155/T-411 already established depth swings 10-100x intraday — 14x in 14 minutes on a single `KXMLBHIT` series, 67x between two consecutive `TEAM_TOTAL` reads. The archiver's ~20-minute cadence is roughly 10-20x coarser than the window in which depth was already shown to move an order of magnitude. Even a sample that happens to hit the right ticker cannot be trusted to represent book state at entry unless it falls within a few minutes of the entry timestamp — well inside the bot's own 45-90 second T4 re-evaluation cadence, not the archiver's.

Both gaps point the same direction: **closing GG-157 to a standard that would satisfy a G6 sign-off requires depth to be captured by the bot itself at decision time — the ticker it is about to fill, at the moment it evaluates the position — not reconstructed after the fact from an independent, family-sampled, minutes-coarse cron.** A denser or full-universe cron archiver would raise the odds of future incidental overlap and is worth doing regardless (it's cheap), but it is a proxy, not a substitute: it still measures depth for tickers the archiver happened to pick, at times the archiver happened to run, not depth for the ticker the bot happened to fill, at the moment it filled it. Only co-located, decision-time capture answers the actual G6 question ("was the assumed mid-price fill realistic for this specific bet").

**This is a Phase 3/4 design requirement, not a Phase 0/1 measurement task** — it means adding an orderbook read to `run_t4_mlb_live.py`'s (and eventually `paper_trader.py`'s) live evaluation path, logged alongside the existing forecast/risk fields per position, so every future position carries its own true depth-at-entry rather than depending on a second system's independent sampling luck. Recording this now, per the operator's instruction, rather than waiting to discover it later: **no amount of tuning the current cron archiver's sample rate closes GG-157 on its own.**

## Disposition

GG-157 remains **OPEN**. This session adds the empirical answer to its own "Recommended next step" (cross-reference resolved paper-bet timestamps against nearest depth sample) — the honest answer is that no such cross-reference is currently possible, and the reason why is now on the record along with the concrete design requirement to fix it.
