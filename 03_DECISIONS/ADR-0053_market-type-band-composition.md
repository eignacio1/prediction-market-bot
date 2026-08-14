# ADR-0053 — Market-Type × Band Composition Model (Design Only)

**Status:** ACCEPTED (as amended by T-448) — see §6 for the amendment and §7 for sign-off.
**Date:** 2026-08-12 (drafted); amended and accepted 2026-08-14 (T-448)
**Author:** Session `20260812T045755Z-phase1-band-dimension` (T-441); amended by session `20260814T144527Z-adr0053-accept` (T-448)
**Registers:** GG-172 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`) — this ADR is the composition-design response to that gap, not its closure; GG-172 remains OPEN — see GG-172's Resolution field for why.
**Depends on / potential overlap:** T-439 (`04_EXECUTION/SESSION_CLAIMS.md`) — "Phase 1 boxes 1.1+1.3 -- market-type registry (keyed market_type x band) + kalshi_client.py series constants registry-driven." T-439 has since shipped `src/prediction_market_bot/c5_execution/market_type_registry.py`. **This overlap is now reconciled — see §6.** §5 Judgment Call 1 (below, preserved verbatim as originally drafted) is resolved, not still open; do not re-litigate it without reading §6 first.
**Scope:** Architecture design only, amended (§6) to defer to already-shipped code where it exists. No code, no `src/` change in this session, no kelly_fraction values, no reopening of T1/GG-037/GG-105, no unparking of `SCALING_MANDATE_PARKED.md`. Governs how a (market_type, band) cell should be represented and what Phase 3 must build on top of `market_type_registry.py` — does not itself implement Phase 3.

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

## 6. Amendment (T-448, 2026-08-14) — reconciliation against T-439's shipped code, and accepted delta

§5 Judgment Call 1 required this ADR's design to be checked against whatever T-439 actually shipped before either was treated as settled. Both T-441 (this ADR) and T-439 have since shipped. This section runs that reconciliation, resolves all three §5 judgment calls on the record, and specifies the accepted delta between what T-439 shipped and what §2 of this ADR requires. §1–§5 above are preserved verbatim as originally drafted and are historical context for how this ADR arrived at its decision, not the operative design — §6 is.

### 7.1 — Two-direction delta

Compared `git show origin/main:03_DECISIONS/ADR-0053_market-type-band-composition.md` (pre-amendment, i.e. §1–§5 above) against `git show origin/main:src/prediction_market_bot/c5_execution/market_type_registry.py`, field-by-field and enum-member-by-enum-member.

**What the ADR (§2) has that the shipped code lacks — i.e., the real accepted delta, specified in §6.3:**

| ADR §2 item | Shipped in `market_type_registry.py`? |
|---|---|
| §2.2 per-cell `clean_n` / `n_star` fields | No — `MarketTypeCell` has no such fields |
| §2.2 `market_type` on the resolved-bet ledger | No — confirmed by direct read of `paper_trader.py::open_position()`: `market_type` is an accepted parameter (used transiently for vig-sign correction via `_directional_edge()`), but the `pos` dict written to the ledger has no `market_type` key (verified: `awk` over the dict literal, zero matches) |
| §2.3 per-cell kill-switch state (halt status/reason/timestamp) | No — no kill-switch fields anywhere on `MarketTypeCell` or in the registry module |
| §2.4 `SHADOW` cell status | No — shipped `CellStatus` has no `SHADOW` member (recommended addition — see §6.2's SCOPING vs. SHADOW discussion below) |
| §2.4 `RULED_OUT` citing-decision reference + promotion guard | Partially — `MarketTypeCell.__post_init__` requires `reason` and `measured_date` when `status is RULED_OUT`, but there is no citing-decision-reference field (a `DECISION_LOG`/`GG`/`ADR` pointer, distinct from a free-text reason) and no guard anywhere preventing a `RULED_OUT` cell from being silently reseeded to `SHADOW`/`ACTIVE` in `MARKET_TYPE_REGISTRY` |
| §2.5 game-key correlation group | No — out of accepted scope regardless (§6.3 item 6); not evaluated further here |

**What the shipped code has that the ADR never considered — the ADR was wrong here, not merely incomplete:**

| Shipped in `market_type_registry.py` | ADR §2.4 anticipated? |
|---|---|
| `CellStatus.NOT_IMPLEMENTED` — a third default state distinct from both `RULED_OUT` (evaluated, rejected) and an active-scoping state (being evaluated now) | No. §5 Judgment Call 3 posed the default-status question as a binary fork (RULED_OUT-default vs. active-scoping-default) and did not consider a third "never evaluated" state. `NOT_IMPLEMENTED` answers JC3 outright — see §6.2. |
| `CellStatus.DARK` — used for NBA_PLAYER_POINTS (a cell that exists, was live, and is now deliberately paused, distinct from `RULED_OUT`/`NOT_IMPLEMENTED`) | No. Not named or anticipated anywhere in §2. Matches this project's existing NBA-dark framing (`[[project_nba_deferred]]`) rather than inventing new vocabulary — correct to keep. |
| `MarketTypeCell` is `@dataclass(frozen=True)`, keyed by `CellKey = tuple[MarketType, ExecutionBand]` in a module-level `MARKET_TYPE_REGISTRY: dict[CellKey, MarketTypeCell]`, with `get_cell()`/`cells_by_status()`/`cells_for_market_type()` accessors | §2.2 named "the cell object" abstractly; the ADR did not specify frozen-dataclass-plus-dict-registry as the concrete shape. No conflict — the shipped shape satisfies §2's requirement; nothing to reconcile. |
| `MarketTypeCell.series_ticker` property, delegating to `series_ticker_for()` | Not anticipated; a market-type-axis concern (ticker pattern), not a composition-layer one per §2.1's own reasoning. No conflict. |
| Already three real consumers: `paper_trader.py`, `kalshi_client.py`, `venue_adapter.py` (confirmed via `grep -rln`) import from `market_type_registry.py` today | The ADR was drafted before T-439 merged and could not have known this. Directly relevant to §6.2 JC1/JC2 below — this object is already load-bearing, not merely proposed. |

### 7.2 — Judgment call resolutions

**JC1 (overlap, was §5 item 1):** **Resolved as the operator's proposed reading — T-439's shipped `MarketTypeCell`/`MARKET_TYPE_REGISTRY` IS the cell object this ADR calls for. One object, one file, one enum.** Evidence: it is already wired into three real consumers (`paper_trader.py`, `kalshi_client.py`, `venue_adapter.py`); it already satisfies §2's core requirement (a first-class (market_type, band)-keyed object, composed by reference rather than duplicating either axis's config); and its only material gap against §2 is the field list in §6.1, not a structural redesign. Drafting a second, competing cell object would fork state that already has three real readers. No disagreement with the operator's framing found.

**JC2 (location, was §5 item 2):** **Resolved as the operator's proposed reading — `src/prediction_market_bot/c5_execution/market_type_registry.py`, not a new `execution_bands_cells.py`.** This is answered by shipped code, not a fresh file-organization judgment call: the object already lives there, already has consumers importing from that path, and §2.1's band-invariant/cell-composition separation argument is satisfied by the module boundary that already exists (`market_type_registry.py` is not `execution_bands.py` — the two are already separate files). No disagreement found.

**JC3 (default status, was §5 item 3):** **Resolved — `NOT_IMPLEMENTED`, a third option neither §5 alternative considered, is better than either horn of the original fork.** §5 posed RULED_OUT-default (safe but risks quietly burying a viable cell) against active-scoping-default (risks treating an unevaluated cell as live). `NOT_IMPLEMENTED` is neither: it does not claim a cell was evaluated and rejected (that is what `RULED_OUT` is for, and `RULED_OUT` requires a citing reason per §2.4/the dataclass guard), and it does not claim a cell is live or being actively scoped. It matches `COVERAGE_TARGET_MATRIX.md`'s own distinction between "never evaluated" and "evaluated and rejected." Confirmed as the shipped default for every seeded MLB cell outside the one live (market_type, band) pair and the two blocked T4M sub-bands. No disagreement with the operator's framing found — this is the one JC where the operator's proposed reading is stronger than either option the original ADR draft offered itself.

**SCOPING vs. SHADOW, per the operator's explicit instruction to assess whether SCOPING is still needed given `NOT_IMPLEMENTED` exists:** Recommend dropping `SCOPING` from the target `CellStatus` set and keeping it at `{NOT_IMPLEMENTED, SHADOW, ACTIVE, BLOCKED, RULED_OUT, DARK}` (six members, `DARK` retained per §6.1's second table). Reasoning: §2.4's original `SCOPING` and the shipped `NOT_IMPLEMENTED` are answering the same question — "this cell has not been evaluated yet" — and `NOT_IMPLEMENTED` is already shipped, already seeded across every unscoped MLB cell, and already has real consumers reading it. Adding `SCOPING` back as a second, near-synonymous "not yet" state would reintroduce exactly the two-structures-for-one-concept duplication §2.1 argues against, just one level down (cell-status enum instead of cell object). `SHADOW`, by contrast, is not redundant with anything shipped: Phase 4 box 4.1 is explicitly "shadow mode per family," and shadow mode (paper-evaluate without betting) is a genuinely distinct state from `NOT_IMPLEMENTED` (never evaluated), `ACTIVE` (live betting), and `BLOCKED` (implemented but currently halted) — none of the five shipped members can represent it. `SHADOW` must be added; `SCOPING` should not be.

### 7.3 — Sequenced accepted delta

Six items, in dependency order. Item 2 gates items 1 and 3 in practice — without it, per-cell `clean_n` (item 1) has no ledger data to group by, and per-cell kill-switch resolution (item 3) has no field to resolve which cell a live position belongs to.

1. **Reverse ticker→market_type lookup (new sub-dependency, not named in the original ADR draft).** `market_type_registry.py` currently only maps `market_type → series_ticker` (`series_ticker_for()`); nothing maps a resolved position's ticker back to a `MarketType`. Item 2 needs this to backfill/derive `market_type` for ledger rows written before the field existed. Depends on: nothing (buildable against shipped code as-is). Feeds: item 2.
2. **`market_type` on the resolved-bet ledger (§2.2) — THE LOAD-BEARING DEPENDENCY.** `paper_trader.py::open_position()` already accepts `market_type: MarketType | None` as a parameter; it is used transiently (`_directional_edge()`) and then discarded — never written to the `pos` dict. Add it as a persisted ledger field. Required by Phase 3.3/3.4 (`run_power_calc.py` scoped to `(market_type, band)` instead of band alone). Depends on: item 1 (for backfilling pre-existing rows) if historical cells are to be grouped correctly; not required to start writing it forward on new positions. Gates: items 1 and 3 below.
3. **Per-cell `clean_n` / `n_star` fields on `MarketTypeCell` (§2.2).** Computed by `scripts/run_power_calc.py` scoped to `(market_type, band)`. Depends on: item 2 (cannot group ledger rows by cell without the field to group on).
4. **Per-cell kill-switch state (§2.3, Phase 3 box 3.5) — halt status, reason, timestamp.** C4/C7 must resolve which cell a bet belongs to before checking halt state. Depends on: item 2 (C4/C7 cannot resolve "which cell" for a position that doesn't record its market_type).
5. **`SHADOW` added to `CellStatus`; `RULED_OUT` promotion guard (§2.4).** Two sub-items: (a) add `SHADOW` per §6.2's recommendation — no ledger dependency, buildable independently; (b) add a citing-decision-reference field to `RULED_OUT` cells (distinct from the existing free-text `reason`) plus a first-ever registry mutation/promotion API — `MARKET_TYPE_REGISTRY` today is a static module-level dict with no write path at all, so "guard against RULED_OUT → SHADOW/ACTIVE without a superseding reference" requires building the mutation path itself before the guard has anything to guard. New sub-dependency not named in the original ADR draft. Depends on: nothing blocking (independent of items 1–4); sequenced last among the buildable items because it's the most-scoped, least-load-bearing piece of the delta.
6. **Game-key correlation group (§2.5, Phase 3 box 3.7) — NAMED ONLY, explicitly OUT of accepted implementation scope.** This delta authorizes items 1–5. It does not authorize building the correlation-group mechanism. That needs its own ADR (a threshold/cap decision, per §2.5's own text) — accepting this ADR does not authorize it. Anyone reading this acceptance as covering item 6 is reading it wrong.

## 7. Operator Sign-off

**The operator (Earl Ignacio) has approved ADR-0053 with expanded scope as of 2026-08-14.** Accepted **as amended by this session (T-448)** — i.e., as reconciled against T-439's shipped `market_type_registry.py` in §6 — not as originally drafted in §1–§5. §6's sequenced six-item delta (§6.3) is the accepted implementation scope; item 6 (game-key correlation group) is explicitly named out of that scope and requires its own ADR. No `kelly_fraction` value is authorized by this acceptance for any cell.
