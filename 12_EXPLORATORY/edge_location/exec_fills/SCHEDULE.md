# H-EXEC-4 look schedule (W124.3) - COLLECTING, no forward look run

**Last reviewed:** 2026-11-23. Status: **COLLECTING**. Part C gate (>= 1 week of forward fills) is not met: the forward population starts
2026-11-20T20:00Z and no forward fill row has been read. Per PREREG.md the look is not run early.

## Look dates (weekly, Tue 10:00Z, O'Brien-Fleming, one-sided alpha 0.05)
First eligible: **2026-12-01**. Then every Tuesday. A look is held only with >= 7 days of forward fills; the n of the cell sets `t`.
| t = fills / n_target | 0.1 | 0.25 | 0.5 | 0.75 | 1.0 |
|---|---|---|---|---|---|
| OBF cumulative spend | 0 | 0.00009 | 0.0056 | 0.0236 | 0.05 |
| Pocock (not chosen) | 0.0079 | 0.0179 | 0.031 | 0.0414 | 0.05 |

## n_target and estimated date (ESTIMATES: rate from W123.4's 157 fills / 8 days, not measured forward; 124.1 ledger not on main)
| Target | n_target | Estimated reached |
|---|---|---|
| Named lead 2-6 h, +0.10 | 310 | about 2026-12-26 |
| Any arm x family, +0.05 | 1,238 | beyond 2027-02 |
| All fills pooled, +0.03 | 3,436 | about 2027-05-14 |
Earliest a cell can be SUPPORTED is the look where t >= about 0.5 for the lead (~155 fills, about 2026-12-12 to 12-15).

## Part B - pre-cut fills, DESCRIPTIVE only
Not reproducible net of fee with an interval from this machine: per-fill join records are on the box only; the evidence copy
ends 2026-11-19T04:23Z and has order events without fills or fees; `result_gap35.json` carries gross aggregates only.
What is known (W123.2 / W123.4, gross, descriptive): CLV all orders RIDE +1.43c, FADE +0.75c; fills at 2-6 h +10.1c settle edge, 68 fills /
20 games. **Variance reduction from each tool: not measurable without rows**; it will be reported at the first look from the post-cut
fit. Needed: a read-only box export of per-fill join records (arm, series, hours, fill_price, fee_per_contract, won, markout.close,
fill_ts, event_ticker; no ids) as a new allowlisted task in `scripts/box_tasks.py` - a code change, window to scope.
