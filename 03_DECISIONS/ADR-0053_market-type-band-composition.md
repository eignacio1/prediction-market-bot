# ADR-0053 — Market-Type × Band Composition Model (Design Only)

**Status:** PROPOSED — drafted this session (T-441) under explicit task instruction: design only, no `src/` change, not to be marked ACCEPTED by this session. Awaiting operator sign-off (Earl Ignacio). Treat as a proposed design, not a closed decision, until sign-off is recorded here.
**Date:** 2026-08-12
**Author:** Session `20260812T045755Z-phase1-band-dimension` (T-441)
**Registers:** GG-172 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`) — this ADR is the composition-design response to that gap, not its closure; see GG-172's Resolution field.
**Depends on / potential overlap:** T-439 (`04_EXECUTION/SESSION_CLAIMS.md`, claimed, open at drafting time) — "Phase 1 boxes 1.1+1.3 -- market-type registry (keyed market_type x band) + kalshi_client.py series constants registry-driven." T-439's own claim description names a market_type×band keying scheme and is **unmerged and unread by this session** (no registry files existed in `src/` at drafting time). This is a real, named overlap risk — see §5 Judgment Call 1.
**Scope:** Architecture design only. No code, no `src/` change, no kelly_fraction values, no reopening of T1/GG-037/GG-105, no unparking of `SCALING_MANDATE_PARKED.md`. Governs how a (market_type, band) cell should be represented once Phase 3 needs to build it — does not implement anything.

---

## 1. Context

`02_ARCHITECTURE_DESIGN/COVERAGE_TARGET_MATRIX.md` frames the operator's directive as a grid: ~5-6 market-type families × 5 execution bands, up to ~25-30 cells, of which exactly one (player-prop hits × T4M-PROJ) is live today. GG-172 (this session) registers that `04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 address only the market-type axis of that grid — nothing in the current plan or codebase represents a *cell* (a specific market-type/band pair) as an object with its own state.

The two axes exist today as separate, asymmetric structures:

- **Band axis** (`src/prediction_market_bot/execution_bands.py`): `ExecutionBand` enum, `BandConfig` frozen dataclass, `BAND_CONFIGS: dict[ExecutionBand, BandConfig]`. Fields are entirely execution-mechanics: `model_class, max_compute_ms, execution_sla_s, kelly_fraction, pipeline_id, cron_schedule, requires_realtime, phase_active`. **No `market_type` field exists anywhere in this file.**
- **Market-type axis**: does not yet formally exist in `src/`. Ticker families are referenced ad hoc (`KXMLBHIT`, `KXMLBGAME`, `KXMLBSPREAD`, `KXMLBTOTAL`, `KXMLBTEAMTOTAL`) across `market_mapper.py`, `kalshi_client.py`, and the coverage matrix doc. Phase 1 boxes 1.1/1.3 (market-type registry, `kalshi_client.py` series constants registry-driven) are the work item that formalizes this — currently in progress under T-439, unmerged.

Neither structure, alone or combined by simple composition, can hold what APR-0024 and Phase 3 (boxes 3.3-3.7) require: per-cell `clean_n`/`n*` (not per-band, not per-family), a per-cell kill switch that does not halt sibling cells, a way to mark a cell RULED_OUT so Phase 4 doesn't re-litigate it, and a named mechanism for cross-family correlated exposure that `BandConfig` and a market-type registry, independently, have no natural home for.

## 2. Decision

**A (market_type, band) cell is a first-class object — not a field added to `BandConfig`, and not a field added to a future market-type config.**

### 2.1 — Why not a field on either existing structure

**Rejected: `market_type` as a field on `BandConfig`.** `BandConfig`'s existing fields (`max_compute_ms`, `execution_sla_s`, `cron_schedule`, `requires_realtime`) are band-invariant execution mechanics — a T4M-PROJ poll cycle runs the same 45s cadence and the same compute budget whether it is evaluating a hit-prop or a moneyline market. Adding `market_type` would force one `BandConfig` row per (band, market_type) pair, duplicating every band-invariant field across every market type that band ever touches, with no mechanism to keep the duplicates in sync. That is a real, avoidable maintenance and consistency cost for data that doesn't actually vary along the axis being added.

**Rejected: `band` as a field on a market-type config.** The mirror-image problem: a market-type config's natural fields (ticker pattern/series ID, depth-gate floor, settlement/resolution logic) are market-invariant — `KXMLBSPREAD`'s ticker pattern and settlement rule do not change depending on which band is evaluating it. Adding `band` would force the same one-row-per-cell duplication in the other direction.

**Accepted: a new `MarketBandCell` object, keyed by `(market_type, band)`, that references a `BandConfig` and a market-type config by key rather than duplicating either.** The things that genuinely vary per cell — `clean_n`, `n*`, the cell's own `kelly_fraction` (if and when sizing is authorized — this ADR does not propose a value), kill-switch state, activation status, RULED_OUT reason — are composition-layer concerns that belong on their own object, not bolted onto either axis's existing, already-load-bearing config.

### 2.2 — Where per-cell `clean_n` / `n*` lives

On the cell object itself: `MarketBandCell.clean_n`, `MarketBandCell.n_star`, computed by `scripts/run_power_calc.py` scoped to `(market_type, band)` rather than to band alone (today's scoping, since only one cell is live, makes band-scoped and cell-scoped indistinguishable — that collapse is exactly why this hasn't surfaced as a forced design decision until a second cell is contemplated). This requires the resolved-bet ledger itself to carry a `market_type` field per row so `run_power_calc.py` can group by cell instead of by band — a real Phase 3.3/3.4 dependency. **Named here, not built.**

### 2.3 — Per-cell kill switch isolation (Phase 3 box 3.5)

The cell object carries its own kill-switch state (e.g., `ACTIVE` / `HALTED`, with a halt reason and timestamp), keyed to `(market_type, band)`. C4/C7's kill-switch check must resolve which cell an incoming bet belongs to *before* checking halt state, so that halting cell `(run_line, T4M-PROJ)` does not touch cell `(hits, T4M-PROJ)` even though both share the T4M-PROJ band's execution mechanics. This is a real change to how C4/C7 currently check kill-switch state (today implicitly band-scoped, again because only one cell exists) — **named as a requirement, not designed in implementation detail, not built.**

### 2.4 — RULED_OUT representation (so Phase 4 doesn't re-litigate)

Add a status field to the cell object: `CellStatus ∈ {SCOPING, SHADOW, ACTIVE, BLOCKED, RULED_OUT}`. A `RULED_OUT` cell carries a required reason string and a citing decision reference (ADR / GG / DECISION_LOG entry — e.g., a cell ruled out because its market-type failed the Phase 0 depth gate cites that finding directly). Any tooling that walks the cell registry for Phase 4 activation work should refuse to move a `RULED_OUT` cell to `SHADOW`/`ACTIVE` without an explicit superseding decision reference — the same immutability discipline Hard Rule 3 applies to ADRs, applied here at the cell-status level so a future session cannot silently re-open a cell someone already investigated and closed. **Named as a requirement; the enum and guard behavior are proposed, not implemented.**

### 2.5 — Cross-family correlated exposure (Phase 3 box 3.7) — name the mechanism only

The problem, restated precisely: moneyline, run line, and game total on a single MLB game are economically correlated (same underlying event, correlated outcomes) but are three distinct Kalshi tickers under three distinct series (`KXMLBGAME`, `KXMLBSPREAD`, `KXMLBTOTAL`). GG-149's existing correlated-exposure guard keys on identical-ticker opposite-direction detection — it cannot see this correlation at all, because there is no shared ticker to key on.

**Proposed mechanism (named, not built): a game-key correlation group.** Rather than grouping open exposure by ticker (GG-149's existing check, kept as-is), add a second, orthogonal exposure check in C4 that groups open exposure by a derived `(game_id, date)` key shared across every market-type ticker referencing the same underlying game — an aggregate-exposure cap across the group, checked at position-open time, independent of and in addition to the ticker-identical check. The `ticker → game_id` mapping this requires should already exist for settlement purposes (a resolution process must know which game a ticker resolves against), so this is intended to reuse an existing data path rather than add new ingestion. **This section names the mechanism and its data dependency; it does not specify the cap's threshold, does not touch `src/`, and does not implement anything.**

## 3. What this ADR explicitly does not decide

- **No `kelly_fraction` value, for any cell.** Sizing requires its own ADR per this session's explicit instruction; nothing here proposes or implies a number.
- **Does not reopen T1 modelling, GG-037, or GG-105.** T1's `kelly_fraction=0.0` and dead status (GG-135/GG-153) are unchanged and out of scope here.
- **Does not unpark `04_EXECUTION/SCALING_MANDATE_PARKED.md`.** That file is gated on Phase 2's verdict per its own text; this ADR does not touch it or its gating condition.
- **Does not close the intent-vs-implementation reconciliation gap `SCALING_MANDATE_PARKED.md` names.** That file records 70 days passing with no session asking what bet types were originally envisioned — a wrong *premise* held confidently, not a wrong value or an unverified resolution. The invariant suite (T-432/ADR-0052) catches a wrong value; ADR-0052 itself catches an unverified resolution claim; **the cell-composition model in this ADR catches neither** — a `MarketBandCell`'s own `clean_n`/status can be perfectly correctly measured while the entire cell inventory itself silently drifts from what the operator actually intended months earlier. A periodic intent-vs-implementation reconciliation process is the obvious structural answer and remains unbuilt and unauthorized. **Not proposed, scoped, or built here** — noted only so this ADR is not later read as having covered it.
- **Does not mark itself ACCEPTED.** Per Hard Rule 3, only the operator's sign-off (§6) can do that.

## 4. Consequences if adopted

- Phase 3 gains a concrete object to build toward (`MarketBandCell`) instead of inventing per-cell state ad hoc when the second cell is scoped.
- `BandConfig` and the market-type registry (once T-439 lands) both stay clean of duplication — each remains the single source of truth for its own invariant axis.
- The RULED_OUT guard (§2.4) gives Phase 4 a structural defense against re-litigating a cell someone already closed, mirroring the ADR-immutability pattern the project already trusts.
- The correlation-group mechanism (§2.5) gives Phase 3 box 3.7 a named target instead of leaving it as an acknowledged-but-unaddressed gap indefinitely.
- New governance surface: a cell registry is a new artifact someone must maintain, review, and keep consistent — an accepted tradeoff for making per-cell state representable at all.

## 5. Judgment calls flagged for operator decision

**1. T-439 overlap — needs reconciliation before either is treated as settled.** T-439's claim in `SESSION_CLAIMS.md` describes work "keyed market_type x band," which sounds adjacent to or possibly overlapping with this ADR's `MarketBandCell` proposal. T-439 was open and unmerged throughout this session; no registry files existed in `src/` at drafting time, so this ADR was written without seeing T-439's actual implementation choices. **Do not treat this ADR's design as final until it has been checked against whatever T-439 actually ships** — there is a real risk two sessions independently designed the same composition layer differently, and one should defer to or amend the other.

**2. Where the cell registry physically lives.** A new module (e.g. `execution_bands_cells.py`) versus an extension of the existing `execution_bands.py` (already 1340 lines and, per §2.1, band-invariant by design). This session leans toward a new module to keep the band-invariant/cell-composition separation the design argues for, but this is a file-organization call, not an architecturally forced one — flagging rather than deciding.

**3. Default status for an unscoped cell.** Should a cell default to `RULED_OUT` until someone actively promotes it to `SCOPING` (safer default, but risks quietly burying a genuinely viable cell if nobody revisits it), or default to some active-scoping state until someone actively rules it out (risks a cell being treated as live/available when no one has actually evaluated it)? This is a real fork with real safety and coverage-completeness consequences on both sides. Not decided here — flagged for operator judgment.

## 6. Operator Sign-off

Pending. Recorded here (not fabricated) — this ADR is `PROPOSED` until Earl Ignacio signs off in a future session or turn.
