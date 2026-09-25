# T-573 Results — Cohort Verification (Wave 34, Block 34.2)

**Session:** `session/20260924T045058Z-cohort-verification` · **Date:** 2026-09-24 · **Tier:** STANDARD
**Deliverable:** does the project currently hold any scorable evidence? Follow-on to T-571's ledger-integrity audit, which left three unruled-out explanations for the 731-of-765 (95.6%) NOT_RETRIEVABLE T4M-PROJ epoch-12 rows and an un-tested selection-bias question on the 34/35 confirmed-FILLED subset.
**Scope:** read-only. No ledger row edited, excluded, or re-stamped. No `clean_n` restated. No cell status, `kelly_fraction`, or constant changed. Did not build a scoring harness (34.1/T-572's territory), did not modify `generate_operator_console.py` or `.claude/hooks/` (34.3/T-574's territory), did not re-run T-571's original verification of the 34.

---

## 0. What this session inherited from T-571

- **GG-300**: 731/765 (95.6%) T4M-PROJ epoch-12 clean rows have no independent Kalshi confirmation of ever being filled; 34 (4.4%) confirmed real. Full current ledger (905 rows): 35 FILLED / 139 CANCELED / 731 NOT_RETRIEVABLE.
- **GG-301**: calibration headline reverses sign on the 34 confirmed rows (model_brier 0.2730 vs market 0.1415, skill −0.156, win_rate 0.176, P&L −$6.78) vs. the full-765 headline (model_brier 0.2191, market 0.1890, positive skill/P&L +$39.73).
- **GG-302**: 42 NFL T1 rows traced to a single unlogged manual run; quarantined (not this session's concern).
- T-571 explicitly left open: (a) a lookup-key/ticker-normalization explanation for the 731 was not excluded, only leaned-against on a 30-row sample; (b) no test for selection bias in "which orders retrieve cleanly" was attempted.

This session's four deliverables close both gaps and reconcile the 731 to full granularity.

---

## 1. Deliverable 1b — exclude the lookup-key explanation before trusting the retrieval ceiling

`scripts/t573_lookup_key_exclusion.py`, read-only, run on the VPS.

**Part A — is the ledger's `kalshi_ticker` field trustworthy at all?** For all 35 confirmed-FILLED rows, compared the ledger's `kalshi_ticker` against the `ticker` field Kalshi's own `GET /portfolio/orders/{order_id}` response returns for that same order.

**Result: 35/35 exact character-for-character match.** The ledger's ticker field is not corrupted or mis-normalized on the rows we can independently verify.

**Part B — do any of the 731 resolve under a different key form?** Sampled 30 NOT_RETRIEVABLE rows (3 per date, 10 dates) and probed each under three alternate forms beyond the original single-order-by-id lookup: event-level (`event_ticker=`), series+date-window (`series_ticker=` + `min_ts`/`max_ts`), and an unfiltered date-window query with no ticker/series filter at all (to catch a ticker malformed enough that no substring of it is a valid key).

**Result: 0/30 resolved under any alternate key.** The script's own STOP condition (any row resolving) did not fire.

**Conclusion:** the 731 figure is not an artifact of a lookup-key bug. Proceeding to treat it as a genuine retrieval/submission signal is warranted, subject to the 30-row sample-size caveat — this is a sample, not a census (Deliverable 2 extends this to the full 731).

---

## 2. Deliverable 1 — characterize the retrieval ceiling

No dedicated script; derived from Deliverables 1b/2's own API traffic (90+ live calls, zero rate-limit errors). Same-date FILLED orders remain retrievable roughly 54 days post-game-date in this dataset (oldest confirmed-FILLED `game_date` vs. 2026-09-24). This is corroborating evidence that the 731/95.6% figure reflects genuine non-submission or unresolvable status rather than a retention-window or throttling artifact — it is not dispositive; no deliberate retention-boundary probe (requesting a known-old order to find where retrieval actually stops) was attempted, out of scope for this deliverable.

---

## 3. Deliverable 2 — reconcile all 731 into buckets; the duplicate-ledger-row finding (GG-303)

`scripts/t573_duplicate_ticker_full_join.py` (pure local join on ledger `kalshi_ticker`, no API calls) partitions all 731 NOT_RETRIEVABLE rows into four **mutually exclusive** buckets:

| Bucket | Definition | Count |
|---|---|---|
| **A** | Ticker collides with a FILLED row's ticker, no NR sibling | 5 |
| **B** | Ticker shared by ≥2 NR rows, no FILLED collision | 386 (172 distinct groups; size dist `{2: 129, 3: 40, 4: 3}`) |
| **C** | 3-way: ticker has 1 FILLED + ≥2 NR rows | 4 (2 distinct tickers) |
| **D** | Unique ticker within NR, no FILLED collision | 336 |
| **Total** | | **731** (exact) |

**395 of 731 rows (54.0%)** — A+B+C — carry a ledger `kalshi_ticker` implicated in some duplication anomaly: either colliding with a confirmed-real FILLED order, or sharing a ticker with 1-3 other NR rows, each carrying a distinct, non-existent `kalshi_order_id`. This was not the originally-hypothesized mechanism (a lookup-key bug, excluded in Deliverable 1b) — it is a separate, larger, and previously unquantified defect in how the ledger writes `kalshi_order_id` values.

**Reconciling the census-9 figure.** `scripts/t573_full_census.py` independently ran the full-731 version of Deliverable 1b's Part B probe (event-level + account-wide date-window queries, deduplicated to ~50-80 unique API calls rather than 731×2) and found `n_resolved_under_alternate_key=9`. Cross-checked against the join above: **these 9 rows are exactly buckets A(5)+C(4)**. This is not 9 rows of new evidence that trades were real — it is the mechanical consequence of a sibling row's genuine order sharing the same ticker, which an event/date-window query (unlike a strict per-order lookup) cannot help but surface. The two probes are not in tension; the census confirms the join.

**Governance record:** GG-303 (OPEN, HIGH) — duplicate-ledger-row / fabricated-`kalshi_order_id` pattern, 395/731 rows. A mechanism hypothesis (retry-writes-new-order_id-without-clearing-prior-attempt) is flagged for the owning session to investigate in `kalshi_client.py`'s submission/retry path; not investigated or repaired here (Hard Rule 11). GG-304 (MEDIUM) registered separately for the `kalshi_order_status` field's non-discriminating "submitted"-for-everyone behavior across both FILLED and NR populations, noted as a byproduct of this deliverable.

---

## 4. Deliverable 3 — selection-bias test on the 34/35 confirmed-FILLED rows (GG-301 update)

`scripts/t573_selection_bias_test.py`. 8 observables pre-registered in the script's own docstring before any statistic was computed: 5 continuous (`mid_price_at_entry`, `gross_edge`, `h_so_far_at_entry`, `ab_remaining_at_entry`, `size_usd`) tested via a hand-implemented two-sided Mann-Whitney U (normal approximation, tie correction — no scipy on the VPS), Bonferroni-corrected alpha = 0.05/5 = 0.01; 2 categorical (`kalshi_threshold`, `game_date`) reported descriptively.

| Observable | mean, FILLED | mean, NOT_RETRIEVABLE | p-value | Survives Bonferroni (α=0.01)? |
|---|---|---|---|---|
| mid_price_at_entry | 0.6527 | 0.3950 | <0.00001 | **YES** |
| gross_edge | −0.1913 | −0.0340 | 0.00203 | **YES** |
| size_usd | 0.6271 | 0.9123 | 0.00001 | **YES** |
| h_so_far_at_entry | — | — | 0.364 | no |
| ab_remaining_at_entry | — | — | 0.868 | no |

**3 of 5 continuous observables are significant surviving correction.** `game_date` is also visibly skewed: 42.9% of FILLED rows fall on a single date (2026-08-10) vs. 18.1% of NR rows on that date.

**Verdict:** the 34-row confirmed-FILLED subset is not a random draw from the 765-row cohort — it systematically differs on entry price, edge, and order size, and clusters heavily on one date. **GG-301's sign-reversed headline is not a correction to T-565's original positive finding; it is a different, non-random sample answering a different question.** Neither the positive full-cohort headline nor the negative confirmed-subset headline can be treated as *the* project's calibration answer. The honest statement is that the project's calibration headline is **UNKNOWN**, not reversed.

---

## 5. Deliverable 5 — gap registration

Registered per this wave's explicit GG-log/DECISION_LOG ownership assignment to block 34.2:

- **GG-303** (OPEN, HIGH) — duplicate-ledger-row / fabricated-`kalshi_order_id` pattern, this session's own finding, Deliverable 2.
- **GG-304** (OPEN, MEDIUM) — `kalshi_order_status` non-discriminating field, this session's own finding, byproduct of Deliverable 2.
- **GG-305** (OPEN, LOW) — `session_guard.sh` length-threshold breach in `MEMORY_BANK.md` (5159 chars vs. 3000 threshold), handed off from 34.1/T-572.
- **GG-306** (OPEN, LOW) — CLAUDE.md "~25/30 cells" framing vs. `market_type_registry.py`'s actual 92-cell granularity, never reconciled, handed off from 34.1/T-572.
- **GG-307** (OPEN, LOW/scope-boundary) — `build_t4mlb_cohorts` untested against T4M_ARITH/T4M_FLOW, handed off from 34.1/T-572.
- **GG-308** (OPEN, MEDIUM) — `close_session_claim.sh` pushes the entire branch (`git push origin HEAD:main`) despite its own docstring claiming it isolates only the closure row, handed off from 34.1/T-572.
- **GG-309** (OPEN, MEDIUM) — `SemanticFloorViolation` grep in CLAUDE.md Step 4 has the same cumulative-counter/recency-window defect class as already-fixed GG-085; one ~2.5-month-stale hit found, handed off from 34.3/T-574.
- **GG-310** (CLOSED-AS-ARTIFACT) — `ACTIVE_QUEUE.md` Wave 33 archival lapse; already recovered (commit `4a00b8e`) and structurally prevented going forward by T-574's `closed_wave_fences()` detector (commit `c849eae`), handed off from 34.3/T-574.

Plus Update rows on GG-297, GG-300, and GG-301 consolidating this session's findings against the gaps they extend (see those entries directly for the update text).

All 8 new entries and 3 updates registered per Hard Rule 11 — register-and-stop, no code or document repair attempted in this session beyond the governance-log entries themselves.

---

## 6. Bottom line — does the project currently hold any scorable evidence?

**No, not as things stand today.** Three independent findings compound against each other:

1. **95.6% of the claimed clean T4M-PROJ cohort (731/765 rows) cannot be independently confirmed at Kalshi**, and this is not a lookup-key artifact (Deliverable 1b) — it is corroborated by a genuine ledger defect: 54.0% of those unconfirmed rows (395/731) carry a `kalshi_ticker` that collides with either a confirmed-real order or another unconfirmed row, under distinct fabricated `kalshi_order_id` values (Deliverable 2, GG-303). The ledger is not merely silent on these rows — it shows a specific, characterizable failure mode in how it wrote them.
2. **The 34/35 rows that *are* confirmed real are not a representative sample** of the 765-row cohort — they differ significantly on entry price, edge, and size, and cluster heavily on a single date (Deliverable 3, GG-301 update). A calibration figure computed only on this subset is not a corrected version of the full-cohort figure; it is an answer to a different, narrower, selection-biased question.
3. Consequently, **neither of the two calibration headlines currently in the project's history is trustworthy as the project's answer**: the full-765 headline (positive, T-565) is computed over a cohort that is 95.6% unconfirmed and partly duplicated; the confirmed-34 headline (negative, GG-301) is computed over a cohort that is real but demonstrably non-random.

**The operator-facing verdict:** the project does not currently have a clean, confirmed, representative cohort large enough to answer "does the model beat the market?" one way or the other. Recovering one requires either (a) resolving the 731 NOT_RETRIEVABLE rows to a real disposition — which first requires repairing the ledger-write defect behind GG-303, since a fixed retry path may itself change which of the 731 are recoverable — or (b) a properly-powered, bias-corrected re-analysis that accounts for the selection effect found in Deliverable 3. Neither is in scope for this session (Hard Rule 11); both are registered as open, not deferred silently.

Repair, exclusion, or any change to what counts as the project's live cohort remains the operator's decision — this session diagnoses only.
