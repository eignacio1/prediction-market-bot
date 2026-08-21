# ADR-0054 — Segmented-Pool Isolation (Phase 3 Box 3.1)

**Status:** PROPOSED. Item (c) only is operator-signed (2026-08-17, verbatim instruction reproduced in §5). The document as a whole is not accepted — items (a), (b), (d) are resolved here on their merits and await operator sign-off.
**Date:** 2026-08-19
**Author:** Session T-467 (`phase3-isolation-adr` worktree)
**Registers/depends on:** `ADR-0053` (ACCEPTED, 2026-08-14) §2.5/§6.3 item 6 explicitly deferred the correlation-group decision to "its own ADR" and stated "This delta authorizes items 1–5. It does not authorize building the correlation-group mechanism... Anyone reading this acceptance as covering item 6 is reading it wrong." **This is that ADR.** Builds on T-456 (CLOSED 2026-08-16, commit `6173f3f`), which shipped ADR-0053 §6.3 items 1–3 (ticker→market_type lookup, `market_type` persisted on the ledger, per-cell `clean_n`/`n_star` via `run_power_calc.py::run_all_cells()`) ahead of this document. References `GG-183` (OPEN/LOW — per-cell kill-switch store, unwired), `GG-184` (OPEN/LOW — `open_position()`'s `market_type` silent default).
**Scope:** Architecture design only. No `src/` changes. Does not implement Phase 3 boxes 3.2–3.8. Does not touch sizing, `kelly_fraction` values, the live kill switch, or `logic_epoch` values. Does not touch GG-170 or GG-185.

---

## 1. Context

Phase 3 (segmented-pool build) cannot start until box 3.1 — the isolation boundary — is decided. `02_ARCHITECTURE_DESIGN/SEGMENTED_POOL_ARCHITECTURE.md` (DRAFT, 2026-07-30) named the load-bearing seam: `risk.py::evaluate_forecast()` is shared and unconditional across every `(market_type, band)` cell, with no gate on which cell it is evaluating. `ADR-0053` (ACCEPTED) separately established that a cell is a first-class object (`MarketTypeCell`, `market_type_registry.py`) and shipped a sequenced 6-item delta — items 1–5 build the cell's data shape; item 6, the correlation-group mechanism, was explicitly named and explicitly withheld from that acceptance. This ADR resolves the isolation boundary (§2) and all four items the assigning task named as non-deferrable: ledger design (a), epoch scoping (b), correlated exposure (c), and per-cell kill switches (d).

---

## 2. Isolation boundary — options considered

`SEGMENTED_POOL_ARCHITECTURE.md` §3 names three options, not one:

- **Option 1 — Accept coupled resets at the shared gate.** Any C4 fix zeroes `clean_n` for every family/cell simultaneously. Simplest; explicitly "not recommended" in the source document, and independently disqualified here by evidence: across 12 epochs, no cohort has clearly reached `n*` under exactly this coupling, so continuing it is continuing the failure mode, not a neutral default.
- **Option 2 — Per-family epoch scoping at the C4 seam.** Extend `LogicEpochBoundary.bands_affected` so a C4 change is scoped, diff-verified, to only the cells it actually altered — not defaulted to the `ALL_BANDS` sentinel. Two live precedents, confirmed by direct read of `logic_epoch.py`: epoch 11 (GG-046/ADR-0050, `bands_affected={"T4M-PROJ"}`) and epoch 12 (GG-149, same scoping) both landed 2026-07-31, both touched `risk.py`'s shared `evaluate_forecast()` signature, neither reset any other band's floor. A **third, more recent and stronger precedent** exists that the source document predates: T-456 (2026-08-16) already extends the identical scoping discipline one axis further — `run_power_calc.py::run_all_cells()` groups by `(market_type, band)`, not band alone, and persists results per-cell via `market_type_registry.py::set_measurement()`. The pattern this ADR needs is already running in production for the measurement side; it is missing only on the epoch-boundary side (§4).
- **Option 3 — Separate `RiskEngine` instance per family.** Full isolation; cost is duplicating a component that is currently correct and market-agnostic, with divergence risk over time. Source document: "only justified if Option 2 proves unworkable." No evidence gathered in this session suggests Option 2 is unworkable — the opposite: T-456 shows it already extends cleanly to the cell axis.

**Decision: Option 2, extended to the cell axis.** Not "per-family" as the plan's box 3.1 language literally says, but per-`(market_type, band)` cell — consistent with `ADR-0053`'s cell-object decision and with T-456's shipped precedent. §4 states the mechanism.

---

## 3. Item (a) — Per-family ledger files (box 3.2)

**One file, one `market_type` column — not one file per family.** This is not an open design choice for this ADR to make; it is already built and running, per `ADR-0053` §6.3 item 2 / T-456: `paper_trader.py::open_position()` persists `market_type` into the ledger `pos` dict (comment: "ADR-0053 §6.3 item 2: persist the cell key's market_type axis"), defaulting silently to `MLB_PLAYER_PROP_HITS` when unset (this default is `GG-184`, OPEN/LOW, named not fixed here). This ADR ratifies that shape as the answer and states what each consumer named by the task still needs:

- **`assert_ledger_invariants.py`** — confirmed via direct grep: zero `market_type` hits, only two `band ==` hits (lines 404, 406). Zero cell-awareness today. Must be extended to assert per-cell invariants once a second cell is ACTIVE; named as a follow-on (§8), not built here.
- **`run_power_calc.py`** — already cell-aware. `run_all_cells()` (line 296) plus helpers `_market_type_for_record()`/`_regroup_by_cell()`/`_persist_cell_measurement()` regroup the ledger by `(market_type, band)` and call `analyze_band_power()` per cell; `main()` invokes it unconditionally. The remaining gap is not in this file — it's that `.claude/hooks/governance_scan.sh` still imports only `run_all_bands` (lines 367, 422), so cell-scoped `clean_n`/`n*` is computed but invisible to routine session-start reporting. Named as a follow-on (§8).
- **`run_band_monitor.py`** — confirmed via direct grep: `BOOK_BANDS = ("T1", "T2", "T3")` hardcoded (line 126), `by_band` regroup (line 147). Has **not** received the T-456-style treatment. Needs the equivalent cell-aware regroup. Named as a follow-on (§8).
- **Replay harness (`replay_harness_t427.py`)** — confirmed via direct grep: calls `open_position()` (line 106) without `market_type=`. Inherits `GG-184`'s silent-default risk directly — a replay run today is silently attributing every position to `MLB_PLAYER_PROP_HITS` regardless of what it actually replayed. Harmless while one cell is live; becomes a real mislabeling risk the moment a second cell is ACTIVE. Named as a follow-on (§8).

---

## 4. Item (b) — `clean_n` / `logic_epoch` scoping — THE LOAD-BEARING ITEM (box 3.8's gate)

**Decision: yes, epochs become per-cell, not merely per-band.**

Confirmed by direct read of `logic_epoch.py`: `LogicEpochBoundary` is a `NamedTuple` whose `bands_affected: frozenset[str] = frozenset({ALL_BANDS})` field is keyed on bare band strings today (`ALL_BANDS = "*"` is the all-bands sentinel). `clean_epoch_floor_for_band(band)` (line 560) and `is_clean_for_band(stamped_epoch, band)` (line 576) both consume that string key. This machinery is zero-aware of `market_type` — it cannot distinguish "this fix touched T4M-PROJ's hit-prop logic" from "this fix touched T4M-PROJ's moneyline logic," because both are just `"T4M-PROJ"` to it today. That collapse is exactly why one fix to one family's edge formula would zero `clean_n` for every cell sharing that band, permanently, the moment a second cell goes live — box 3.8's gate ("a synthetic C4 change resets only intended families' `clean_n`") is unachievable while the key is band-only.

**Required change:** `bands_affected` becomes a frozenset of `(MarketType, band)` cell keys (or an equivalent `CellKey`-typed tuple), with `ALL_BANDS`'s role generalized to an explicit "all cells" sentinel for genuinely universal C4/ledger-shape changes (a real category — e.g. epoch 3/GG-077, where `paper_trader.py::open_position()` changed unconditionally before any band gate existed at all, would still need an all-cells marking under the new scheme). `clean_epoch_floor_for_band`/`is_clean_for_band` get renamed/extended to `..._for_cell(market_type, band)` variants.

**Cost:** a key-type change plus call-site update, not a redesign — the machinery already generalizes cleanly (confirmed by direct inspection of every accessor). The real cost is re-auditing every existing `_BOUNDARIES` entry against its actual diff to determine which cells (not just bands) it truly touched — the same "verified from diff, never assumed" discipline already used for the existing entries (e.g. epoch 2/GG-087 and epoch 4/GG-113 both diff-verified to `{"T4M-PROJ"}` specifically, not assumed). That re-audit is real work across 12 epochs' worth of history and is named as a follow-on (§8), not performed in this ADR.

---

## 5. Item (c) — Cross-family correlated exposure (box 3.7) — OPERATOR-SIGNED 2026-08-17

**Operator decision (verbatim instruction, reproduced for record):**

> OPERATOR DECISION — ADR-0054 item (c), correlated exposure. SIGNED OFF 2026-08-17. DECISION: EXPOSURE CAP on the correlated group. NOT a hard block. Stacking is not a signal defect — every leg that independently clears the edge gate is legitimate and none should be refused; the problem is that Kelly sizes each leg as if independent, so three correlated legs on one game outcome behave like one ~3x bet in disguise. Connects to GG-135 (real-variance-alone ruin geometry already driving four bands to `kelly_fraction=0.0`). The concern is solvency, not edge.

This ADR resolves the five points the operator specified, satisfying the assigning task's "may not defer" instruction:

**5.1 — Check first, paste the result.** Confirmed by direct read of `risk.py`:
```
135:    "max_single_event_exposure_usd": 500.0,    # $500 per event; caps Kelly output
166:def _compute_kelly_size(
196:    return float(min(f_live * bankroll, _HARD_LIMITS["max_single_event_exposure_usd"]))
352:    def evaluate_forecast(
735:            # CHECK 6 — Single-event exposure limit
736:            if approved_size > _HARD_LIMITS["max_single_event_exposure_usd"]:
737:                approved_size = _HARD_LIMITS["max_single_event_exposure_usd"]
```
`max_single_event_exposure_usd` resolves **per call / per bet-evaluation** — effectively per-ticker. There is no game-key or family-key grouping anywhere in `_compute_kelly_size()` or CHECK 6. Confirmed further: the *other* exposure figure C4 consumes, `current_open_exposure_usd` (CHECK 8, ADR-0026 aggregate-deployment invariant), is supplied by `paper_trader.py::exposure_snapshot()` (lines 250–274) as a **portfolio-wide** sum — Σ `size_usd` across *all* open non-isolated positions, regardless of game or family. So today there is exposure tracking at exactly two granularities — single event ($500) and whole portfolio (ADR-0026 cap) — and **nothing in between**. A per-game aggregate cap is a new grouping dimension, not a reuse of existing plumbing. Per the operator's framing: three correlated families on one game today can produce ~$1,500 of exposure to a single outcome against the stated $500-per-event cap, because that cap was never designed with cross-family grouping in mind.

**5.2 — Correlation key.** *[AMENDED 2026-08-21/T-475 — original text below is true but its implicit generalization was false; amendment follows it.]*

Original (2026-08-19): The game-level identifier is the ticker's date+time+away+home segment — e.g. `KXMLBTOTAL-26AUG021410TEXHOU` → `26AUG021410TEXHOU`. Confirmed identical in format across the 6 families sampled in prior verification work: `KXMLBGAME`, `KXMLBSPREAD`, `KXMLBTEAMTOTAL`, `KXMLBTOTAL`, `KXMLBHIT`, `KXMLBF5`. This is a sampled confirmation across the families currently in scope, not an exhaustive future-proof guarantee — any new family added later must be checked against this format before being folded into the correlation group.

**Amendment (T-475, 2026-08-21):** All 6 sampled families were MLB. Verified directly against the live NBA ledger cache (`logs/.vps_portfolio_cache_nba.json`, 158 tickers, all format `KXNBAPTS-YYMONDD-AWAYHOME[...]`, e.g. `KXNBAPTS-26JUN05NYKSAS-...`): a 13-character date+team segment with **no HHMM component**, versus MLB's 17-character date+HHMM+away+home shape. The failure this produces is silent and permissive, not loud: a fixed-width slice or an MLB-shaped regex applied to an NBA ticker does not raise — it returns a shorter but structurally plausible string that never collides with any other leg's key. The correlated-exposure cap (§5.3–5.4) then degrades to a **no-op** for that family — three full-size correlated legs pass through uncapped, exactly the outcome item (c) was operator-signed to prevent (§5).

**Corrected specification:** the correlation key is derived via the per-series `TickerGrammar` registry already landed in `market_type_registry.py` (`_TICKER_GRAMMAR_BY_MARKET_TYPE`, T-472/GG-191, 2026-08-20) — not a hand-rolled regex local to the correlation-cap code; reused here rather than defining a second grammar. `parse_ticker_date(ticker)` returns `ParsedTicker(game_date, teams_raw)`; the correlation key is the pair `(game_date, teams_raw)`. `teams_raw` alone carries the away+home identity jointly and is sufficient for group membership — two tickers on the same game produce an identical key under one shared grammar, and no further split into separate `away`/`home` tokens is required for correlation-grouping to work correctly. This inherits `parse_ticker_date`'s **refusal-only contract**: it raises `TickerDateParseError` on an unparseable tail or `KeyError` on an unregistered series, never a fallback value. **No fallback is permitted anywhere in the correlation-key derivation path — not a default date, not a truncated slice, not a best-effort partial match.** This is not a new principle for this codebase; it is GG-166 → GG-170 → GG-185's lesson already paid for once (a silent fallback in a date-derivation path corrupted ~44% of a clean cohort's outcomes before an independent decoupled path caught it), which T-472 already generalized the fix for in the exact parser this key reuses. A market_type with no `TickerGrammar` entry registered must refuse to be folded into a correlation group — never default to ungrouped/uncapped exposure or a best-effort key.

**5.3 — Control shape: aggregate cap per game key.** Every leg that clears the edge gate remains eligible; the cap governs total dollars on that game key, not which legs may be taken.

**Decision: a leg that would breach the cap is sized down to remaining headroom, not rejected outright.** Justification, two independent grounds: (i) this is already the codebase's established idiom for cap enforcement — CHECK 6 itself (lines 736–737) clamps `approved_size` down to the cap rather than rejecting the position outright, so sizing-down is consistent with existing precedent rather than a new enforcement pattern; (ii) it is the only shape consistent with the operator's own stated rationale — "every leg that independently clears the edge gate is legitimate and none should be refused." Outright rejection of a third leg would contradict that framing directly; sizing it down to headroom keeps the signal live while fixing the actual complaint (uncapped correlated dollars), which is a sizing problem, not a selection problem.

**5.4 — Initial value: provisional, not derived.** $1,000 — between one-leg ($500) and three-leg ($1,500) exposure, reflecting real-but-partial correlation rather than treating the group as either independent (no cap needed) or perfectly correlated (cap = one leg). Per explicit operator instruction, this value is **not measured** and must not be presented as such. It is a provisional choice, revisable by a superseding ADR once the price archive can answer the actual correlation magnitude empirically — that measurement is named as a follow-on task (§8), not performed here.

**5.5 — Relationship to ADR-0053.** Per the operator's completed instruction: `ADR-0053` §6.3 item 6 deferred the correlation-group mechanism to "its own ADR" and stated it "may not be deferred again." This is that ADR. Item (c) is resolved above, non-deferred, satisfying that requirement in full.

---

## 6. Item (d) — Per-family kill switches (box 3.5)

The foundation already exists and was deliberately left unwired: `CellKillSwitchState`/`resolve_kill_switch_state()`/`halt_cell()` in `market_type_registry.py` (lines 480, 490, 500–506), built by T-453 per `ADR-0053` §2.3/§6.3 item 4. This is `GG-183` (OPEN/LOW) — an explicit, scoped deferral ("DO NOT REWIRE C4/C7'S LIVE KILL-SWITCH PATH... Leave a seam, register the wiring as its own task"), zero live consequence today because only one cell (T4M-PROJ × player-prop-hits) is ACTIVE.

**Decision:** Phase 3 must wire this, not redesign it. C4/C7's live halt-check path must resolve `(market_type, band)` for the incoming bet via `resolve_kill_switch_state()` **before** enforcing halt state, and must call `halt_cell()` — not only today's whole-portfolio halt — from whatever path currently trips the drawdown kill switch. The two kill-switch tiers are not alternatives: a family/cell-level halt must set state only for that cell, while the system-level (ADR-0026/GG-035, portfolio-wide) switch remains a separate, always-active, all-cells-halting mechanism layered on top — exactly the "both tiers active simultaneously, independently, without coupling" requirement CLAUDE.md already states for T1–T5 bands, generalized one axis further to cells. This is a wiring task on an already-correctly-shaped store, not a design question; the wiring itself is named as the Phase 3 box 3.5 follow-on (§8), not built here.

---

## 7. What this ADR deliberately does not decide

- Phase 3 boxes 3.2–3.8 implementation — design only.
- Any `kelly_fraction` value, including for correlation-cap headroom sizing.
- The live kill switch itself — only its per-cell wiring path is specified (§6), not built.
- `logic_epoch` values or retroactive per-boundary re-annotation — required per §4, not performed.
- `GG-170`, `GG-185` — untouched, out of scope.
- The precise correlated-exposure cap dollar value — explicitly provisional (§5.4), not measured, per direct operator instruction.
- An `APPROVALS_REGISTER.md` row — not needed while Status is PROPOSED. Confirmed by direct precedent: `ADR-0051` (DRAFT) and `ADR-0052` (PROPOSED) both currently carry zero rows in that register; only ACCEPTED ADRs receive one, frequently retroactively.

---

## 8. Follow-on tasks named, not staffed here (Hard Rule 11)

1. `assert_ledger_invariants.py` — extend to per-cell invariant assertions.
2. `run_band_monitor.py` — cell-aware regroup, mirroring `run_power_calc.py::run_all_cells()`.
3. `.claude/hooks/governance_scan.sh` — wire in `run_all_cells()` output so cell-scoped `clean_n`/`n*` surfaces at routine session start.
4. `replay_harness_t427.py` — pass `market_type=` explicitly (closes one of `GG-184`'s 7 call sites).
5. `logic_epoch.py` — re-type `bands_affected` to cell keys; re-audit all 12 existing boundaries against their actual diffs for true per-cell blast radius.
6. C4/C7 — wire `resolve_kill_switch_state()`/`halt_cell()` into the live drawdown halt path (resolves `GG-183`).
7. Empirical correlation measurement from the price archive, to replace the provisional $1,000 cap (§5.4) with a measured value via a superseding ADR.
8. `GG-184` full resolution — explicit `market_type=` at all 7 production call sites; becomes load-bearing the moment a second cell is promoted ACTIVE.

---

## 9. Sign-off

Item (c): operator-signed 2026-08-17 (§5). Items (a), (b), (d): resolved on their merits in this document; PROPOSED, awaiting operator sign-off. **Document status overall: PROPOSED — not ACCEPTED.**
