# T-566 Results — Vig grounding from the price archive

**Task:** Replace assumption with measurement for the C4 gate's `vig` term
(`model_p > market_implied_probability + vig`), per series family, without
changing the gate itself. No code/constant changes made — measurement only.

**Session:** worktree `20260923T005837Z-vig-grounding-from-archive`
**Script:** `scripts/measure_archive_spread_by_series.py` (`spread` and
`flip-analysis` subcommands)
**Data:** `exp_output/PRICE_ARCHIVE/prices_*.jsonl` on the VPS (54 files,
2026-08-01..2026-09-23, 1,824,195 rows seen, 170,915 (9.4%) excluded for
missing live quotes); `paper_portfolio_mlb_t4.json` pulled 2026-09-23
(2,994 closed positions all-epoch; 765 in the T4M-PROJ epoch-12 clean
cohort, independently re-derived via `logic_epoch.is_clean_for_band()` and
cross-validated exactly against T-565's reported n=765)

---

## Deliverable 1 — code inventory (summary; full detail reported in-session)

Three genuinely distinct conventions exist for the same `vig` concept:

| Family | File | Series | Cost term in gate | Status |
|---|---|---|---|---|
| T4 MLB | `run_t4_mlb_live.py` | `KXMLBHIT` | **full live-fetched spread** (`yes_ask - yes_bid`) | measured live, not assumed |
| T2 MLB | `run_t2_mlb_sameday.py` | `KXMLBHIT` | **half live-fetched spread** | measured live, not assumed |
| T1 MLB/NFL game markets | `run_t1_mlb_game_market.py`, `run_t1_nfl_game_market.py` | `KXMLBGAME/SPREAD/TOTAL/TEAMTOTAL/F3/F5/F7`, `KXNFLGAME/SPREAD/TOTAL/TEAMTOTAL` | **none — implicit vig = 0.00** | assumed, unmeasured |

`kalshi_fee = 0.07 * price * (1 - price)` (ADR-0016) is applied identically
downstream of the vig term in T2 and T4; hand-verified against a real
closed-position record to 5 decimal places.

**Only T1 has an assumption-vs-measurement gap on the cost term itself.**
T2 and T4 already fetch and apply a real quote-derived spread every cycle —
the open question for those two is not "is the constant right" (there is no
constant) but "how thin is the margin by which the live-fetch mechanism
does its job," which Deliverable 3 answers directly for T4.

---

## Deliverable 2 — measured spread distributions, per series

All 14 `series_ticker` values seen in the archive, `half_spread` in
probability points (0.01 = 1 cent = 1pp). n excludes rows with no live
quote (`yes_bid<=0` or `yes_ask<=0`, 170,915 rows / 9.4% of all rows seen).

| series | n | days | span | hs median | hs p25 | hs p75 | hs p90 |
|---|---:|---:|---|---:|---:|---:|---:|
| KXMLBF3 | 52,111 | 54 | 08-01..09-23 | 0.0200 | 0.0100 | 0.0800 | 0.1950 |
| KXMLBF5 | 55,028 | 54 | 08-01..09-23 | 0.0100 | 0.0050 | 0.0200 | 0.1250 |
| KXMLBF5SPREAD | 73,345 | 54 | 08-01..09-23 | 0.0150 | 0.0050 | 0.0250 | 0.2300 |
| KXMLBF5TOTAL | 127,324 | 54 | 08-01..09-23 | 0.0100 | 0.0050 | 0.0200 | 0.1850 |
| KXMLBF7 | 55,055 | 54 | 08-01..09-23 | 0.0200 | 0.0150 | 0.1300 | 0.2950 |
| KXMLBGAME | 108,998 | 54 | 08-01..09-23 | 0.0050 | 0.0050 | 0.0150 | 0.0250 |
| KXMLBHIT | 312,843 | 54 | 08-01..09-23 | 0.0100 | 0.0050 | 0.0200 | 0.0650 |
| KXMLBSPREAD | 128,664 | 54 | 08-01..09-23 | 0.0050 | 0.0050 | 0.0100 | 0.0150 |
| KXMLBTEAMTOTAL | 284,906 | 54 | 08-01..09-23 | 0.0150 | 0.0050 | 0.0200 | 0.1050 |
| KXMLBTOTAL | 222,640 | 54 | 08-01..09-23 | 0.0050 | 0.0050 | 0.0100 | 0.0150 |
| KXNFLGAME | 13,870 | 17 | 09-05..09-22 | 0.0050 | 0.0050 | 0.0100 | 0.0150 |
| KXNFLSPREAD | 93,075 | 17 | 09-05..09-22 | 0.0100 | 0.0050 | 0.0150 | 0.0250 |
| KXNFLTEAMTOTAL | 56,716 | 17 | 09-05..09-22 | 0.0200 | 0.0150 | 0.0300 | 0.0850 |
| KXNFLTOTAL | 68,705 | 17 | 09-05..09-22 | 0.0100 | 0.0050 | 0.0150 | 0.0200 |

`KXMLBF5SPREAD`/`KXMLBF5TOTAL` are archived (the archiver crawls all live
Kalshi series) but are not among the series any current run script trades,
per the confirmed series lists in Deliverable 1 — included here for
completeness, excluded from the Deliverable 3 gap table below.

**Tails widen materially relative to the median** — this holds across every
series. The ratio of p90 to median half_spread ranges from ~3x
(`KXMLBHIT`, `KXNFLTOTAL`) to ~15x (`KXMLBF3`, `KXMLBF7`, `KXMLBF5SPREAD`).
Full `yes_mid`-bucketed breakdowns are in
`exp_output/T566-VIG-GROUNDING/spread_summary.json` per series
(`half_spread_by_yes_mid_bucket`).

**`.BROKEN_FIRSTRUN` exclusion:** `prices_2026-08-01.jsonl.BROKEN_FIRSTRUN`
(2,162 rows) is excluded. Confirmed by direct row inspection to be missing
every price/spread field (only static market metadata present) — an
aborted first archiver invocation on 2026-08-01, superseded same-day by a
normal `prices_2026-08-01.jsonl`. Excluded structurally by the
`prices_*.jsonl` glob + explicit `.jsonl`-suffix filter, not just by
convention (see script docstring).

**Time-to-close bucketing — unanswerable from this archive as populated.**
Every row across all 14 series fell into the `>24h` bucket; 0% in any
tighter bucket. Root-caused by direct row inspection: a real `KXMLBHIT` row
captured `run_ts=2026-09-15T00:00:06Z` carries
`close_time=2026-09-18T01:40:00Z` — three days *after* capture — despite
the ticker embedding a game date (`26SEP14`) one day *before* capture. The
archive's `close_time`/`expiration_time` fields do not reliably track
real-world game closing time. This is consistent with, and a corroborating
data point for, **already-registered OPEN gap GG-170** (CLAUDE.md Q7:
"ticker-embedded date vs. stored `game_date`... 69.9% violations within
epoch 12") — not a new gap; flagged here as a candidate corroborating
observation for session 32.3 to fold into GG-170 if useful, not to be
separately registered.

---

## Deliverable 3 — quantified gap per family, and the headline flip count

**Classification convention:** *permissive* = the code's assumed cost is
lower than the measured market cost (under-charges, over-approves edge).
*Conservative* = the reverse.

### T1 MLB/NFL game markets — the one genuine assumption gap (PERMISSIVE)

T1's gate (`edge_yes = p_estimate - market_implied_prob`, threshold
`EDGE_THRESHOLD = 0.02`) subtracts no cost term at all — an implicit
assumption of `vig = 0.00`. The measured `half_spread` (the economically
correct one-sided entry cost, per the convention already used in T2 and
documented in `kalshi_client.py`) is real and nonzero for every series T1
trades:

| series | hs median (permissive gap, typical) | hs p90 (permissive gap, tail) | gap vs. `EDGE_THRESHOLD=0.02` |
|---|---:|---:|---|
| KXMLBGAME | 0.0050 | 0.0250 | tail = 1.25x threshold |
| KXMLBSPREAD | 0.0050 | 0.0150 | tail < threshold |
| KXMLBTOTAL | 0.0050 | 0.0150 | tail < threshold |
| KXMLBTEAMTOTAL | 0.0150 | 0.1050 | median = 0.75x threshold; tail = 5.25x |
| KXMLBF3 | 0.0200 | 0.1950 | median = threshold; tail = 9.75x |
| KXMLBF5 | 0.0100 | 0.1250 | median = 0.5x; tail = 6.25x |
| KXMLBF7 | 0.0200 | 0.2950 | median = threshold; tail = 14.75x |
| KXNFLGAME | 0.0050 | 0.0150 | tail < threshold |
| KXNFLSPREAD | 0.0100 | 0.0250 | median = 0.5x; tail = 1.25x |
| KXNFLTOTAL | 0.0100 | 0.0200 | median = 0.5x; tail = threshold |
| KXNFLTEAMTOTAL | 0.0200 | 0.0850 | median = threshold; tail = 4.25x |

For the partial-game and team-total series (`KXMLBF3/F5/F7`,
`KXMLBTEAMTOTAL`, `KXNFLTEAMTOTAL`), the *typical* (median) unmeasured cost
is already comparable to the entire edge threshold, and the *tail* cost is
4-15x the threshold — meaning a bet approved at exactly the edge margin in
those series, under real median-to-tail spread conditions, would not have
cleared a spread-aware gate at all. This is the clearest, most direct
answer to "is the assumption conservative or permissive, and by how much":
**permissive, by a magnitude that rivals or exceeds the gate's own
threshold in the sparser series.**

### T2 MLB (KXMLBHIT, same-day) — no assumption gap; documentation-accuracy note only

T2's `half_spread` cost is live-fetched from real quotes every cycle, not a
hardcoded constant — there is no assumption-vs-measurement gap on the cost
term itself to quantify. One in-code comment claims the half-spread
convention "matches T1's own formula"; T1 subtracts no spread term at all,
so this claim is factually inaccurate (T-566 does not fix it — flagged as a
documentation-accuracy observation for session 32.3, not a numeric gap).

### T4 MLB (KXMLBHIT, live) — no assumption gap on the cost term; `VIG_CEILING` re-derivation and the flip-count stress test

T4's `vig` cost is also live-fetched from real quotes every cycle
(`gross_edge = p_t4 - mip - vig`, direction-aware per GG-087, netted
against `kalshi_fee`, gated at `MIN_EDGE_TO_APPROVE = 0.04`) — again, no
assumption-vs-measurement gap on the cost term itself.

The one true hardcoded constant in T4's vig path is `VIG_CEILING = 0.30`
(`run_t4_mlb_live.py:203`), a pre-filter that skips evaluation entirely
when live vig exceeds it — not a cost term. Re-derived against the full
54-day/312,843-row `KXMLBHIT` archive: **3.15%** of rows exceed 0.30 full
spread (vs. the original single-day 2026-07-02 derivation of ~9.6%, n=4,971
cycles) — the ceiling is looser relative to the larger sample, and among
all 2,629 T4M-PROJ closed positions (all epochs), observed `vig_at_entry`
ranges min=0.01, median=0.04, p90=0.13, **max=exactly 0.30** — the ceiling
binds the boundary exactly once and never rejects an otherwise-approved
bet. Confirms the ceiling remains non-binding on approvals; not a live
concern, reported as a secondary finding per the task brief's interest in
checking thin-n-derived thresholds against larger data.

**Headline finding — 765-decision flip count.** Re-ran the T4M-PROJ
epoch-12 clean cohort's 765 real gate decisions (`fee_net_edge` reconstructed
exactly from each closed position's stored `vig_at_entry`, `mid_price_at_entry`,
`model_p`, `direction`), substituting each row's real `vig_at_entry` for an
archive-measured `KXMLBHIT` half_spread (bucketed by `yes_mid` at entry, to
respect the tails-widen behavior in Deliverable 2), holding direction fixed,
and recomputing against the same `MIN_EDGE_TO_APPROVE = 0.04`:

| substituted vig | n evaluated | flip approved→rejected | avg net_edge delta (measured − stored) |
|---|---:|---:|---:|
| archive **median** half_spread × 2, by `yes_mid` bucket | 765 | **87 (11.4%)** | +0.0104 |
| archive **p90** half_spread × 2, by `yes_mid` bucket | 765 | **547 (71.5%)** | −0.0874 |

**Interpretation (reported as evidence, not a recommendation — no
cross-family conclusion drawn):** at typical (median) market spread
conditions, T4's real live-fetched vig readings ran close to or modestly
tighter than the broader `KXMLBHIT` distribution for the same price
regime — only 11.4% of approvals would not have cleared a "typical
conditions" gate. At tail (p90, "bad but not unprecedented") spread
conditions, 71.5% would flip to rejected. This quantifies, without
asserting a verdict on it, how load-bearing the live per-cycle fetch is:
T4's approval rate depends on catching momentarily favorable spread windows
relative to the full distribution for that price regime, and the margin
between "typical" and "tail" outcomes is wide (11.4% → 71.5%).

---

## Gap candidates for session 32.3 to register (NOT registered here — this session does not own GOVERNANCE_GAP_LOG.md this wave)

1. **T1 game markets (7 MLB + 4 NFL series) gate on an implicit `vig=0.00`
   assumption**, unlike T2/T4 which both live-measure. Measured gap:
   median 0.005-0.02pp, p90 tail 0.015-0.295pp depending on series — largest
   and most threshold-relevant in `KXMLBF3`, `KXMLBF5`, `KXMLBF7`,
   `KXMLBTEAMTOTAL`, `KXNFLTEAMTOTAL`. See Deliverable 3 table above.
2. **T2's in-code comment inaccuracy**: claims its half-spread convention
   "matches T1's own formula"; T1 has no spread term in its gate at all.
   Documentation-accuracy only, not a numeric/behavioral gap.
3. **Price archive `close_time`/`expiration_time` fields do not reliably
   track real game closing time** (all 1.65M quote-bearing rows landed in
   the `>24h` time-to-close bucket; a sampled row's `close_time` was 3 days
   *after* capture while the ticker-embedded game date was 1 day *before*
   capture). This corroborates already-OPEN GG-170, not a new gap — flagged
   as a candidate cross-reference, not a new registration.

---

## Artifacts

- Script: `scripts/measure_archive_spread_by_series.py` (`spread` and
  `flip-analysis` subcommands)
- `exp_output/T566-VIG-GROUNDING/spread_summary.json` — full per-series
  Deliverable 2 output (all 14 series, all bucket breakdowns)
- `exp_output/T566-VIG-GROUNDING/flip_analysis.json` — full Deliverable 3
  flip-count output
- This file
