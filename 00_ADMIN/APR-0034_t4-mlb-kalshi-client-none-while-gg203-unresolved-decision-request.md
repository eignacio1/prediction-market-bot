# APR-0034 — Should T4 MLB run with `kalshi_client=None` while GG-203 is unresolved?

**Status:** DECISION REQUEST — not adjudicated at drafting time; presents options, does not select one.
**Touches (if accepted):** the T4 MLB run entrypoint's `PaperTrader(...)` construction (the call site that
currently passes a live-signing-key `kalshi_client` for T4M-PROJ). No file is modified by this document
itself.
**Drafted:** 2026-09-15, T-551/GG-282 (Deliverable 4)
**Prior context:** GG-203 (T4M-PROJ zero-bets-to-execution incident) and its remediation task T-547.

---

## The gap

GG-203 documents that every `risk_eval_approved` event T4 MLB has produced since 2026-08-15T00:06:20Z has
been followed 1:1 by a failed Kalshi order submission — a sustained 100% order-write failure, now 32+ days
running at roughly 1,600 rejected positions/day. `paper_trader.py`'s `open_position()` routes a failed
Kalshi order to `rejected_positions`, never `open_positions` — confirmed directly by reading the function —
so there is no live-capital or exposure leak from this failure mode. But it does mean every approved T4 MLB
bet for 32+ days has been discarded at the order-submission step rather than recorded as an open paper
position, which is the opposite of what T4M-PROJ's G6 sample-accumulation purpose requires.

T-547 (2026-09-15, same day as this document) ran the full remediation sequence GG-203 called for: root
cause re-confirmed, a genuine RSA key rotation performed (new key ID, old key deleted), Kalshi support
escalated. The fresh-key reproduction is the load-bearing fact here — it failed identically, on its first
order attempt, with the same `insufficient_shard_balance` / "Exchange user not found" error, which
conclusively rules out credential age, key corruption, or any explanation tied to the specific key material.
The fault is external: a Kalshi-side account/exchange-user provisioning defect, not a bug in this repo's
`kalshi_client.py`, `paper_trader.py`, or ticker construction. Kalshi's support reply was generic
sandbox-instability boilerplate that did not engage with the specific reproduction (100% failure rate,
sustained 32 days, reproduced on a brand-new key created minutes before testing). **GG-203's Status line
reads `IN PROGRESS (T-547) · Severity: HIGH` as of this document — not RESOLVED, and with no ETA**, pending
either a Kalshi-side account fix or some other externally-driven change. A detector
(`scripts/gg203_order_write_detector.py`, alarm-only) is now wired into `.claude/hooks/governance_scan.sh`
so any recurrence or resolution is caught going forward rather than requiring another 32-day silent run to
notice.

This document asks the question GG-203's remediation did not: **given the fault is external and open-ended,
should T4 MLB continue submitting doomed Kalshi orders every cycle, or should it run with `kalshi_client=None`
until GG-203 resolves?** This is presented as a decision request, not resolved here — Hard Rule 11 (register
and stop on discovery) and this task's own DO NOT list (no `PaperTrader` construction with a non-None
`kalshi_client`, no order submission) both apply; that constraint governs this session's own conduct, not
what T4 MLB's production entrypoint should do going forward, which is exactly the question being escalated.

---

## What's actually true right now, verified this session (not assumed)

**ADR-0008 itself frames Kalshi demo-order submission as a non-load-bearing confirmation layer, not a gate.**
Quoting directly:

> **Local ledger is authoritative**: `paper_portfolio.json` is the G6 evidence source. Kalshi demo balance is
> a confirmation, not a replacement.
>
> **Degraded mode**: if Kalshi order fails, local position is recorded and `kalshi_order_status = "failed:
> <reason>"`. The bot does not halt. This is intentional — the kill switch governs risk, not venue
> connectivity.
>
> This does NOT change the G6 gate criteria (30 resolved bets, positive P&L, ADR-0005). It strengthens the
> evidence quality.

ADR-0008 also carries its own rollback clause, written at acceptance time, before GG-203 existed:

> If Kalshi demo order submission causes unexpected behavior: Remove or unset `VENUE_PRIVATE_KEY_PATH` from
> `.env`. Bot reverts to local-only mode automatically — no code change required. All prior paper positions
> remain valid in `paper_portfolio.json`.

This is direct textual evidence that local-only operation is an anticipated, blessed fallback state under
ADR-0008 as written — not a foreign mode requiring new authorization from scratch. What it does not address:
whether local-only mode may be scoped to *one band* (T4 MLB) while other bands keep `kalshi_client` live —
the rollback text describes a global env-var unset, not a per-script/per-band construction choice like
`kalshi_client=None` passed only in T4 MLB's own entrypoint.

**The reader census (T-542-style, run this session) confirms MLB's live G6 gate does not depend on Kalshi
order status at all.** Every reader of `kalshi_order_id`/`kalshi_order_status` was enumerated:

- `paper_trader.py` — sole writer.
- `run_paper_trade.py`, `monitor.py`, `bet_record_contract.py` — informational/schema readers only (surface
  the field; do not gate on it).
- `analytics/clean_dataset.py` — the one reader with real gating logic (`CONTAM_KALSHI_FAILED`,
  `CONTAM_LOCAL_ONLY`, feeding `is_clean`/`n_clean`/`n_contaminated`). Its own module docstring scopes it
  explicitly: "Clean Dataset Extraction — NBA Paper-Trading Ledger (T-174 WS2, GG-034)." Every one of its five
  real consumers (`bet_record_contract.py`, `exp_retrospective_core.py`, `derive_calibration.py`,
  `run_exp017c_calibration_mlb.py`, `build_clean_dataset.py`, `run_t177_edge_monitor.py`) was checked
  directly for actual contamination-flag usage against MLB data — zero matches. The two MLB-named scripts
  either don't use the flags at all or reference `data/nba_finals_clean_dataset.csv` in their own docstrings.

MLB's actual live G6/`clean_n` gate is computed by `scripts/run_band_monitor.py`'s `filter_clean()`, which
calls `logic_epoch.py:686`'s `is_clean_for_band()` — a per-band write-path-epoch check (T-320/T-321/GG-124)
with **zero reference to `kalshi_order_status` or Kalshi order submission anywhere in its logic.**

**The one caveat**: `bet_record_contract.py` line 27 states, in future tense, "MLB extraction will populate
`sport=\"MLB\"`..." — i.e., the NBA-derived `CONTAM_KALSHI_FAILED`/`CONTAM_LOCAL_ONLY` taxonomy is *planned*
to extend to MLB at some future point, even though it does not apply today. Running `kalshi_client=None` now
costs nothing against the gate that actually exists, but if that planned extraction lands before GG-203
resolves, this window's T4 MLB bets would need to be explicitly scoped (e.g. tagged as `order_local_only` by
policy, not by omission) rather than silently swept into whatever the future schema's default classification
turns out to be.

---

## Options (presented, not selected)

**Option 1 — Leave T4 MLB constructing a live `kalshi_client` as-is, continue absorbing the 100% order-write
failure rate until GG-203 resolves.** No code change, no new ADR needed. Cost: ~1,600 rejected positions/day
continue accumulating for however long GG-203's external fault takes to resolve (no ETA); every one of those
approved bets is discarded at the order-submission step rather than contributing anywhere. The detector
(D5) means this is now a *monitored* cost rather than a silent one, but it is still a cost with no offsetting
benefit identified this session — the "external confirmation" ADR-0008 describes literally cannot succeed
under the current fault, so continuing to attempt it buys nothing beyond what the detector already logs on
its own (failure count, timing).

**Option 2 — Run T4 MLB with `kalshi_client=None` until GG-203 resolves, resuming live-client construction
once a Kalshi-side fix is confirmed (verified by the detector, D5, or a manual order-success check).**
Approved T4 MLB bets stop being discarded at the order-submission step and instead land in `open_positions`
as local-only records — which, per the reader census above, costs nothing against MLB's live G6 `clean_n`
gate today. This is also the mode ADR-0008's own rollback clause anticipates (see quote above), scoped here
to one band rather than globally. Cost: the "external confirmation" layer ADR-0008 designed is absent for
this window specifically (T4 MLB only; other bands' Kalshi submission, if any, is unaffected); and per the
one caveat above, if the NBA-style contamination taxonomy is later extended to MLB, this window's bets need
an explicit, deliberate tag rather than a default one.

**Option 3 — Hold at Option 1, but stop routing T4 MLB orders once the detector fires a fresh same-day
alarm (i.e., let the existing detector become the trigger for a future ad hoc `kalshi_client=None` toggle,
rather than deciding now).** This defers the decision rather than making it, on the theory that GG-203 might
resolve on its own timeline and this document's premise (open-ended, no ETA) might not hold. Cost: this is
functionally Option 1 today (nothing changes) with a promise to revisit later that has no owner or trigger
condition more concrete than "the detector fired," which is already true today (100% failure) — this option
does not actually change anything about the status quo unless a concrete revisit condition is written down
elsewhere.

---

## What superseding ADR would be needed (Hard Rule 3)

ADR-0008 is ACCEPTED and immutable per Hard Rule 3. Its own rollback clause already contemplates a full
revert to local-only mode (unset `VENUE_PRIVATE_KEY_PATH`, no code change) — so Option 2, taken at that
literal scope, may not require a superseding ADR at all, only an operator invocation of the rollback
ADR-0008 already authorizes. What ADR-0008 does *not* address, and what would need a superseding ADR if the
operator wants this scoped rather than global, is: **per-band** `kalshi_client=None` (T4 MLB only, other
bands' Kalshi submission unaffected) rather than the account-wide unset the rollback clause describes. A
superseding ADR for that narrower case would need to: (a) state the GG-203 external-fault finding as the
trigger condition, (b) scope the `kalshi_client=None` construction to T4 MLB's own entrypoint only, (c) state
the reversal condition (Kalshi-side fix confirmed via the D5 detector or a manual probe), and (d) confirm —
as this document does — that G6 gate criteria are unaffected, since ADR-0008 itself already states demo-order
submission does not change G6 gate criteria.

---

## Not decided here

This document does not choose among the three options above, does not modify `PaperTrader` construction
anywhere, does not construct a `PaperTrader` with a non-None `kalshi_client`, and does not submit any order,
live or demo. T4 MLB's entrypoint is unchanged by this document. Per Hard Rule 11, resolving this is out of
scope for T-551/GG-282 — registered and stopped here for the operator.

**Recommendation (non-binding): Option 2.** The fresh-key reproduction under T-547 rules out every internal
explanation for GG-203, Kalshi's own support reply did not engage with the specific failure mode, and the
reader census confirms MLB's live G6 gate has zero dependency on Kalshi order status today — so the cost of
continuing to submit doomed orders (Option 1) is a pure loss (rejected bets, no offsetting confirmation
value) against a gate that doesn't need that confirmation to advance, while Option 2's one real cost (the
future-taxonomy caveat) is deferrable and tractable if/when that taxonomy is actually extended to MLB.
