# T-572 — Closing-Line-Value (CLV) Instrument: Pre-Registration

**Status: PRE-REGISTERED, IMMUTABLE ONCE PUSHED.** This document is written and pushed
*before* any CLV statistic, regression slope, or bootstrap CI has been computed. Do not
edit the CLV definition, entry/closing rules, cohort construction, confound designs, or
verdict thresholds below after this commit lands — if a design flaw is found during
execution, stop and file a superseding document with its own timestamp; do not silently
relabel this one. Only §0 (instrument calibration: row/ticker/game counts, null rates,
ticker-granularity) was computed before this document was written, matching the discipline
established by `T569_t4_latency_thesis_PREREGISTRATION.md` — calibration facts about the
data's shape are not thesis-relevant and are reported here for transparency.

## Why this instrument, and why now

Two prior measurement paths on T4M-PROJ are either exhausted or unusable this wave:
**T-569** measured the latency thesis directly (does `mip` move toward the model after a
state change) and found it **NOT SUPPORTED** — the forward slope of `delta_mip` on
`gross_edge` was negative at k=1..4, and the backward placebo ran 5.1-6.4x the forward
magnitude, i.e. whatever correlation exists is dominated by a mechanical/pre-existing-trend
artifact, not forward prediction. **T-571** found only 34 of 765 approval rows are
Kalshi-confirmed against GG-300's retrieval ceiling, and the headline reverses on that
34-row subset per GG-301 — the P&L-based measurement path is not currently usable at
adequate n.

CLV is proposed as a third, independent instrument: it needs only the price archive
(`t4_mlb_cycle_log.jsonl`'s `mip` series), not settlement/outcome data, and it answers a
different question than either prior path — not "did the market move after a state change"
(T-569) and not "did the resolved bet make money" (T-571/GG-300), but **"did the price the
model entered at beat the price the market later settled on, for the side taken."** This is
the standard sports-betting-analytics construct: a trader can have negative expected value
on outcome yet still show it beat the closing line, or vice versa, so the two questions are
genuinely separable and neither substitutes for the other.

**Honest prior, stated explicitly per operator instruction:** T-569 found the WRONG SIGN
on the mechanism this bot's entries are supposed to exploit. There is no reason CLV should
come back positive, and it is expected to be **negative**. A cleanly measured negative CLV
is a needed finding — confirmation, via an independent instrument, that T4M-PROJ's edge
claim does not survive contact with the market's own later price. It must not be softened
into "inconclusive" if it comes back negative and statistically real. INCONCLUSIVE is
reserved for genuine ambiguity (CI includes zero, or the two clustering schemes disagree in
sign) — not for a clean negative result that is simply unwelcome.

---

## 0. Instrument characteristics (measured before any CLV statistic — calibration only)

Fresh pull from the VPS (`/opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl`, pulled
2026-09-24 ~04:20 UTC via `scp` into this worktree's `logs/` — not the stale local mirror
`.vps_t4_mlb_cycle_log_cache.jsonl`, which stops 2026-08-07 and is excluded):

- **Row count:** 404,634
- **Date span:** 2026-07-02T19:09:34Z → 2026-09-24T04:20:48Z (77 distinct `game_date` values)
- **Distinct tickers:** 8,377
- **Distinct games** (tickers grouped by their second `-`-delimited segment, e.g.
  `26JUL021410CINMIL`, which encodes date+time+matchup and is shared by every
  player/threshold ticker in that game — see §1): **808**
- **Null fields:** `gross_edge` (and `p_t4`, `net_edge`, `ba_l10` — same rows, per T-569's
  finding) null on 28,787 rows (7.11%) — model could not price, insufficient `ba_l10`
  history. `mip` is never null in this pull (0/404,634).
- **Ticker granularity:** rows-per-ticker median 46, p10 7, p90 92. **208 tickers (2.48% of
  8,377) have exactly 1 row** — these cannot supply a closing observation distinct from any
  entry drawn from them and are excluded outright from cohort construction (§2).

None of the above bears on CLV's sign or magnitude — it is schema/coverage description
only, in the same spirit as T-569 §0.

---

## 1. Data preparation (fixed before computation)

- Source: fresh pull only, `logs/t4_mlb_cycle_log.jsonl` in this worktree (gitignored,
  not committed — same convention as T-569's `t4_mlb_cycle_log_fresh.jsonl`).
- Group rows by `ticker`, sort ascending by `ts` within each ticker.
- **Game identifier** (needed for the by-game clustering scheme in §4 and the control
  cohort's within-game time-strata matching in §3): `ticker.split("-")[1]`, e.g.
  `26JUL021410CINMIL` — this segment is shared by every player/threshold ticker belonging
  to the same game and is not independently re-verified beyond the sampling check in §0
  (this is the same "ticker encodes game" assumption T-569 made, applied one level up).
- Tickers with exactly 1 row are dropped before any cohort construction (208 tickers,
  §0) — logged by count, not silently.
- Non-monotonic or duplicate-timestamp adjacent pairs within a ticker (`dt <= 0`) are
  dropped from that ticker's usable sequence before entry/closing selection, mirroring
  T-569 §1's handling (T-569 found 9/390,549 such pairs — negligible, not re-investigated
  here; re-counted fresh on this pull and reported in the results file, not pre-committed
  to a number here).

## 2. CLV definition (fixed before computation)

For a candidate entry on ticker `t` at row `T` with resolved `side ∈ {YES, NO}`:

- `entry_mip = mip(T)`; `entry_price_side = entry_mip` if `side == YES` else
  `1.0 - entry_mip` (ADR-0050 addendum §B/§C convention, matching
  `run_t4_mlb_live.py:1328`'s live `entry_price` computation exactly).
- `closing_mip = mip(T_close)`, where `T_close` is the **last row in that ticker's
  time-ordered sequence** (the "last pre-resolution sample" — see justification below).
  `closing_price_side = closing_mip` if `side == YES` else `1.0 - closing_mip`.
- `side_sign = +1` if `side == YES` else `-1`.
- **`CLV = side_sign * (closing_mip - entry_mip)`**, algebraically identical to
  `closing_price_side - entry_price_side`. Positive CLV means the market moved, between
  entry and close, toward confirming the side taken (the entry beat where the market's own
  later consensus settled); negative CLV means the market moved away from the side taken
  after entry.

**Why "last row" as the closing reference, not a fixed time-before-resolution horizon:**
T4 markets resolve continuously as the game itself progresses (a hit either happens or the
at-bat/game ends) — there is no fixed "close" the way a pregame line has one. The last
logged row before the market stops being polled (game end / market inactive) is the best
available proxy for "the market's final settled view," and it is what the instrument can
actually observe. This has a known failure mode, addressed structurally rather than
ignored: rows very close to resolution can show mechanical convergence toward 0/1 as the
outcome becomes near-certain, which would inflate |CLV| in either direction for reasons
having nothing to do with early-entry skill. This is why §5's mean-reversion /
model-convergence confound check exists, and why a **second-row-from-last robustness
variant** of `T_close` is also computed (§6) and reported alongside the primary result, not
substituted for it.

**Missing-closing-observation policy (refuse loudly, do not impute):** if a candidate entry
row `T` for ticker `t` is itself the last usable row in `t`'s sequence (no `T_close` exists
strictly after `T`), that ticker contributes **no observation** to any cohort and is
excluded with a logged reason (`ticker`, `entry_ts`, `reason=no_closing_observation`) — the
harness module (Deliverable 2) raises on this condition at the row level; cohort-building
code catches and logs the exclusion rather than letting one bad ticker abort the whole run.
This is a designed, tested behavior (§7), not an edge case discovered at execution time.

## 3. Cohort construction (fixed before computation)

**(a) Approvals cohort — the model's own reconstructed entries.** The cycle log persists
only raw, non-directional `gross_edge`/`net_edge` (GG-067) — the live pipeline's directional
approval decision is not itself logged and must be recomputed exactly as
`run_t4_mlb_live.py` computes it (lines 1165, 1259-1269, 1328, confirmed by direct read this
session):

```
kalshi_fee = 0.07 * mip * (1.0 - mip)
if gross_edge > 0:      direction = YES; directional_gross_edge = gross_edge
elif gross_edge < 0:    direction = NO;  directional_gross_edge = (mip - p_t4) - vig
else:                    skip row (no signal)
directional_net_edge = directional_gross_edge - kalshi_fee
entry_price = mip if direction == YES else (1.0 - mip)
qualifies  = (directional_net_edge >= 0.04)  and  (entry_price > 0.0)   # MIN_EDGE_TO_APPROVE, risk.py
```

For each ticker (with >1 usable row, §1), the entry is the **first row in time order**
where `qualifies` is true. Rows with null `gross_edge`/`p_t4` (7.11%, §0) never qualify and
are skipped when scanning for the first crossing. `side = direction` at that row.

This is a simplification versus the live pipeline in one respect, stated explicitly: the
live system also applies intra-book/cross-book offsetting-position suppression (GG-149) and
per-event exposure caps (C4) after the edge gate, which can block or resize an
edge-qualifying signal. This instrument tests the **edge gate's own price-timing quality**,
not the fully-gated live execution path — a scope simplification, not an oversight. Noted
here so a reader does not mistake "approvals cohort" for "identical to what actually
fired."

**(b) Control cohort — matched random directional entry, same tickers, same time strata.**
For every ticker contributing an approvals-cohort entry at inning bucket `b` (early 1-3,
mid 4-6, late 7+, by `inning` at the approval row), draw one row uniformly at random (fixed
seed `572`, one draw per ticker, reproducible) from that same ticker's usable rows,
excluding the approval-entry row itself and the ticker's last row (a control entry also
needs its own distinct closing observation), preferring rows whose `inning` falls in the
same bucket `b`. If no such row exists in that ticker, fall back to any eligible row in the
ticker and flag the observation `bucket_fallback=true` in the per-row output (reported as a
count, not silently absorbed). Side for the control entry is assigned by the **same
directional sign convention** as the approvals cohort (`YES` if `gross_edge>0` at that row,
`NO` if `<0`, skip if `gross_edge==0` or null and redraw once, then drop the ticker from the
control cohort if still unresolved) — **no edge-magnitude gate is applied**. This isolates
whether the *magnitude* threshold (`>=0.04`) adds anything beyond the *directional
sign convention* itself, which by construction already points toward whichever side the
model currently favors.

Both cohorts therefore have (at most) one observation per ticker, are matched on ticker
identity, and are approximately matched on innings-elapsed-at-entry.

## 4. Aggregation and clustering (fixed before computation)

- **Primary statistic per cohort:** mean CLV, equal-weighted across tickers (all
  `size_or_none` values in this dataset are `None` — T4M_PROJ's `kelly_fraction=0.0` per
  ADR-0048 means no real position was ever sized, confirmed via `execution_bands.py` this
  session — so a size-weighted aggregate is not computable and is not reported as anything
  other than "not applicable" for this run; the harness module still implements the
  size-weighted path, since it is a reusable instrument other cells may supply sizes to).
- **Difference statistic:** mean(approvals CLV) − mean(control CLV), on the matched-ticker
  pairs.
- **Clustering:** cluster-robust SE via block bootstrap, 1,000 resamples, resampled
  **by ticker** (primary — each ticker contributes exactly one observation per cohort here,
  so this is equivalent to an ordinary i.i.d. bootstrap over tickers; still labeled
  by-ticker for consistency with the harness's general case where a ticker can contribute
  multiple rows) and **by game** (secondary — resample the 808 games, taking all
  ticker-observations belonging to a resampled game as a block), matching T-569's
  dual-clustering precedent. Both are reported for every statistic in §3-§6; a sign
  disagreement between them downgrades the verdict to INCONCLUSIVE regardless of what the
  by-ticker CI alone shows (§7).
- 95% CI throughout, percentile method on the bootstrap distribution.

## 5. Confound checks (mandatory — no CLV number is reported without both)

Per operator instruction: *"A CLV number that has not passed (a) is not a result. Do not
report one without it."* Both checks below are run and reported alongside every headline
CLV number (approvals, control, and the difference) — they are reporting requirements for
every number, not just a gate applied to a positive result before it is allowed to be
called positive.

**(a) Mean-reversion vs. model-convergence.** Define, for each entry `T`:
`own_dislocation(T) = entry_mip - trailing_mean_mip(T)`, where `trailing_mean_mip(T)` is the
expanding mean of `mip` over that ticker's rows strictly before `T` (minimum 3 prior rows
required; entries without enough history are excluded from this specific check only, count
reported). Let `signal(T) = directional_net_edge(T) * side_sign` (the signed, fee-adjusted
edge magnitude at entry — for the control cohort this is simply the signed `gross_edge`
recomputed the same way, since no gate was applied). Run three OLS regressions of the
signed forward move `side_sign * (closing_mip - entry_mip)` [== CLV]:
(i) on `signal(T)` alone, (ii) on `own_dislocation(T)` alone, (iii) on both together.
Report all three slopes with cluster-robust SE (both clusterings, §4). If `signal(T)`'s
coefficient in (iii) keeps its sign and its CI still excludes 0, that is evidence CLV is not
purely explained by reversion to the ticker's own trailing mean. If it does not survive,
reversion is reported as the explanation, plainly, not folded into a vaguer "mixed" label.

**(b) Backward placebo.** Define the pre-entry signed move
`backward(T) = side_sign * (entry_mip - open_mip(t))`, where `open_mip(t)` is `mip` at that
ticker's **first** usable row (structurally symmetric to CLV itself: CLV measures
entry→close, `backward` measures open→entry). Regress `backward(T)` on `signal(T)` (same
predictor used in §5(a)) and compare the slope to the forward regression from §5(a)(i).
**Pre-registered threshold, identical to T-569's:** the forward result survives this
placebo if the backward slope's magnitude is **less than 50%** of the forward slope's
magnitude, **or** the backward 95% cluster-robust CI includes 0 while the forward CI does
not. If the backward slope is comparable to or larger than the forward slope, the forward
result is presumptively a mechanical/pre-existing-trend artifact, not evidence that entry
timing itself added value — reported as such, at whatever ratio it comes out to (the ratio
itself, backward/forward, is a headline number per the report-back requirements).

## 6. Robustness variant (reported alongside the primary result, not substituted for it)

Recompute §2's CLV using `T_close` = the **second-to-last** row in each ticker's sequence
instead of the last, for tickers with ≥3 usable rows (so a distinct second-to-last exists).
This checks whether the primary result is sensitive to mechanical near-resolution
convergence. Both variants are reported; a material sign flip between them is called out
explicitly in the results write-up, not averaged away.

## 7. Harness testing requirements (Deliverable 2, specified here so the build has a fixed
target before it starts)

The module's row-level function must `raise` (not return `None`/`0`/silently drop) on:
1. An entry whose ticker has no row with `ts` strictly after `entry_ts` (no closing
   observation — §2's policy).
2. A ticker argument not present in the source data at all.
3. `side` not in `{"YES", "NO"}`.
4. `entry_price` that is `None`, `NaN`, `<= 0`, or `>= 1`.
Cohort-building code must catch these per-row and log exclusions with counts and reasons
(never let one bad row abort a cohort computation); the row-level function itself must not
swallow them. Tests exercise all four conditions against deliberately malformed synthetic
cohorts before the harness is run against the real archive.

## 8. Verdict criteria (fixed in advance — apply mechanically, do not adjust post hoc)

**CLV POSITIVE** requires **all** of:
1. Approvals-cohort mean CLV > 0, by-ticker cluster-robust 95% CI excludes 0.
2. (Approvals − Control) difference > 0, by-ticker CI excludes 0 — approvals beat blind
   directional entry, not merely "any directional pick tends to show positive CLV."
3. Survives the §5(b) backward placebo (ratio < 50%, or backward CI includes 0 while
   forward does not).
4. `signal(T)`'s coefficient survives §5(a)'s multiple regression (same sign, CI excludes 0
   with `own_dislocation` included).
5. By-game clustering CI agrees in sign with by-ticker on criterion 1.

**CLV NEGATIVE** requires **all** of:
1. Approvals-cohort mean CLV < 0, by-ticker cluster-robust 95% CI excludes 0.
2. By-game clustering CI agrees in sign (both exclude 0, both negative).
A NEGATIVE verdict is **not** additionally gated on surviving §5's confound checks — those
are run and reported regardless (§5's mandatory-reporting requirement applies to every
number), and they explain *why* a negative result looks the way it does, but a
statistically real, cross-clustering-consistent negative measurement stands as NEGATIVE on
its own; there is no "artifact" story that converts a genuine negative measurement into a
non-result. This asymmetry is intentional, not an oversight: POSITIVE is the extraordinary
claim here (it would mean an edge signal that T-569 already found the wrong sign for is
nonetheless timing entries well against the market's own later price) and carries the
higher evidentiary bar; NEGATIVE is the prior.

**INCONCLUSIVE** applies if:
- Either cohort's by-ticker CI includes 0, or
- By-ticker and by-game clusterings disagree in sign, or
- Fewer than 30 qualifying tickers survive into the approvals cohort (`INSUFFICIENT_N`,
  matching T-569's 30-event floor precedent) — not expected given 8,377 tickers, but stated
  as a floor regardless, or
- §6's robustness variant flips sign relative to the primary result (reported as
  INCONCLUSIVE-ROBUSTNESS, a distinct sub-label, rather than silently preferring one
  variant).

**What no verdict here establishes:** CLV is a price-timing measure, not a P&L measure —
positive CLV does not imply the bet was profitable net of fees/vig, and negative CLV here is
a second, independent line of evidence alongside T-569 (mechanism) and T-571/GG-300
(realized outcomes on a thin confirmed subset), not a replacement for either. This
distinction is stated in the results write-up (Deliverable 3-5) and not resolved by this
instrument.

## 9. Deliverable 5 scope note

The cell-registry enumeration (which of the `(MarketType, ExecutionBand)` cells this
instrument can/cannot score today) is a documentation/coverage task against
`market_type_registry.py`'s live state, not a statistical hypothesis test — no
pre-registration criteria apply to it. It is produced from direct inspection of the
registry alongside this instrument's own data requirements (a ticker-keyed, timestamped
`mip` series plus a defined entry rule) and reported separately in the results file.

---

**Pre-registered by:** T-572, 2026-09-24, prior to computing any §2-§8 statistic. §0 only
(row/ticker/game counts, null rates, ticker-granularity — pure calibration) was computed
before this document was written.
