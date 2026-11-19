# Architecture Overview — Prediction Market Trading Bot

> **Binding text: `02_ARCHITECTURE_DESIGN/DOCTRINE.md`.** Where this file disagrees with it, DOCTRINE.md wins. This file maps the system
> components onto the doctrine; it does not restate it. State (numbers, what is running) lives in the RUNNING SITREP at the top of
> `04_EXECUTION/ACTIVE_QUEUE.md`; what runs on the box is `RUNTIME_REGISTRY.toml` → `RUNTIME_MAP.md`.

**Purpose:** the map of the system's components, what each is responsible for, and where the router sits among them.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL since the G2 Architecture Gate (2026-05-22); changes need an ADR or a formal Change Class A/B record.
**Last reviewed:** 2026-11-18 (W120.4, body rewritten to DOCTRINE.md; ADR-0077)
**Next review:** every wave close, with the Doctrine stack (RED after 14 days)
**Upstream links:** `DOCTRINE.md`, `STRATEGY_OVERVIEW.md`, `01_SPEC/REQUIREMENTS.md`, `01_SPEC/NON_FUNCTIONAL_REQUIREMENTS.md`
**Downstream links:** `DECISION_ROUTING.md`, `DATA_FLOWS_LINEAGE.md`, `INTERFACES_CONTRACTS.md`, `EXECUTION_ARCHITECTURE.md`,
`RESILIENCE_FAILURE_MODES.md`
**Decision references:** ADR-0001, ADR-0002, ADR-0068, ADR-0072, ADR-0073, ADR-0075, ADR-0076, ADR-0077
**History:** the previous body (a pipeline that ends in a single probability forecast, Phase 0–8 gating text, the Phase 6 idle-build
table, the G2 technology table) is preserved verbatim at `00_ADMIN/ARCHITECTURE_OVERVIEW_ARCHIVE_2026-11-18.md`.

---

## 1. What the system is

A **calibration engine for probabilistic reasoning, structured as a trading bot** (CLAUDE.md). Prediction markets are the laboratory;
P&L is the score; the methodology is the asset. Kalshi is the venue; MLB, NFL, NBA and NHL are the sports.

The architecture is **layered multi-arm decision trees** (ADR-0077, DOCTRINE §1). For every market a tree picks the arm — ride the
market, fade it, momentum, pot of gold, or no bet. The forecast is **one input** to that tree, never the bet by itself. The operator
(2026-11-10 21:35 PT): depth is "meant to ENHANCE OUR DECISION TREES WHICH COULD VERY WELL MEAN RIDE THE WAVE."

## 2. The pipeline C1–C8

C1 ingestion and C2 features are the only sport-specific layers. Everything after them is shared across sports.

| Component | Responsibility | Where it meets the router |
|---|---|---|
| **C1 — Signal ingestion** | Ingest, validate and version-stamp all input data (Snapshot IDs). | Supplies the market state (router layer 1) and the raw inputs for the factors. |
| **C2 — Feature store** | Turn signals into model-ready features, point in time, with traceability to source fields. No future data in any feature. | Builds the depth factors the layer-2 filters use (matchup, lineup / usage, rest / travel, refs, weather, PAM, qualitative). |
| **C3 — Forecasting** | Per-sport engines and per-cell models produce calibrated probabilities; models are frozen in production (Hard Rule 4). | The simulated probability: an input to the tree. Its entry rule on the fade arm is `model_p > market + vig`. |
| **Router** (`src/prediction_market_bot/decision_trees/`) | Layered trees, one per cell, choosing the arm per leaf; a factor is applied only as a tested split, scored per leaf per arm on net after costs, held out. Per-sport factor seats: `SEATS/<sport>.toml`. | Layer 3 — the point where depth enters. Spec: `DECISION_ROUTING.md`. |
| **C4 — Risk** | Kelly sizing per band (`execution_bands.py`, `kelly_fraction`), exposure cap, drawdown kill switch; approve or reject before execution. | Sizing and risk after the arm is chosen. Kelly is 0 on every live band until G6. |
| **C5 — Execution** | Orders through `VenueAdapter` (Kalshi only); order lifecycle; fills measured. Cells in `c5_execution/market_type_registry.py`. | Execution — fills that keep the edge (ADR-0072). No real orders before G6. |
| **C6 — Audit** | Append-only structured log (JSON Lines) of forecasts, routed rows, orders, risk decisions, errors. | Every routed row and arm decision is logged, including shadow cells. |
| **C7 — Monitoring + kill switch** | Health, risk metrics, alerts; the kill switch halts every component within 60 seconds (NFR-03, Hard Rule 6). | Independent of the router; kill switches per band and system-wide. |
| **C8 — Dashboards** | Read-only view of state. No execution path through C8. | Surfaces what C6 / C7 emit. |

Interface contracts for each hand-off: `INTERFACES_CONTRACTS.md`. Data lineage: `DATA_FLOWS_LINEAGE.md`.

## 3. Cells, bands and arms

- **Cells** are keyed (MarketType, ExecutionBand) in `market_type_registry.py`. A new market type arrives as a set of cells, one per
  band. A cell is ACTIVE, SHADOW (no orders; logs when its sport is in season), BLOCKED, DARK, or registered-not-built. Counts are in
  the CLAUDE.md "Right now" block, generated from the code — not here.
- **Bands** T1–T5 (T4 with sub-bands) are the horizon axis; the live registry is `EXECUTION_BANDS.md` § Live Registry and
  `execution_bands.py`.
- **Arms** are the router's choices per leaf. A cell that loses a pre-registered look closes that hypothesis, not the cell
  (DOCTRINE §1b).
- **Adding a sport:** a C1 module, a C2 feature set, an engine, and cells in the registry. If it takes more, surface it before building.

## 4. Scale and design stance

One deep engine per sport at Syndicate32-level granularity or deeper, every factor class built once and point in time, one game
simulation pricing the whole board (ADR-0073, DOCTRINE §2). Design for hundreds to ~1,000 evaluations per game, routed per bet, capital-
ceiling agnostic (Hard Rule 9); anything that only works for a handful of bets per night is architecturally wrong.

## 5. Deployment modes

| Mode | What runs | Capital |
|---|---|---|
| Research / backtest | C1, C2, C3, C6 and the router on stored data | None |
| Shadow | A cell's router logs every forecast and arm choice; no orders | None |
| Demo | Arm orders from the router, flat demo stakes, real fills measured (ADR-0072); `kelly_fraction` 0 | Demo only |
| Live capital | All components | Real — **not permitted until G6 (ADR-0076)** |

## 6. Guardrails (DOCTRINE §8, unchanged)

No real capital; Kelly 0; the hard limits in `risk.py` are programmatic with no bypass path without an ADR; pre-registration before a
cell's first row; secrets by env-var / vault only (NFR-05); `arb/` is reference only until APR-0010; no Polymarket build work.

## 7. Technology

Python, pinned dependencies (`06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/`), JSON Lines logging (NFR-02, NFR-06). The
full G2 technology table is in the archive file named above; the pinned versions in the lock files are the source of truth.
