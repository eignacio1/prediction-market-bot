# ADR-0063 — A Kill Switch Is Meaningless Unless Tied to the Kelly Alignment of What It Halts: Five-Tier Hierarchy (Decision Framework, Draft)

**Status:** PROPOSED — drafted 2026-09-05 (session `20260905T162339Z-adr-kill-switch-kelly-tiers`,
T-520) under explicit operator task instruction, dated 2026-09-03. Not yet ACCEPTED. This document
does not change a `kelly_fraction`, a cell status, an `ExecutionBand` member, any service source,
or any ledger row. It establishes a hierarchy and a derivation discipline; it does not implement
anything inside that hierarchy.

**Depends on / builds on:** `ADR-0060` (band-tier NFR-03 latency remedy; option (c) target
architecture — **not reopened here**, see §5). `ADR-0029` (T4 sub-band architecture; Tier A froze
a ≤5s band-level kill-switch requirement, 2026-06-22 — see §2 Tier 2). `ADR-0048`
(edge-conditional sizing; the reactivation gate that determines when a moot tier stops being
moot — see §3). `ADR-0026` (full-book two-tier deployment invariant). `ADR-0053`/`ADR-0057` (cell
registry, `(MarketType, ExecutionBand)` keying). `GG-038` (T4 kill-switch SLA gap, OPEN, HIGH —
this ADR absorbs TASK 2 and TASK 3 of its 2026-08-26 T-489 addendum, see §4). `GG-054`/ADR-0054
(cell-level kill-switch wiring, part (d) specifically — **not implemented here**, see §6).
`GG-209` (OPEN, MEDIUM — T1 force-close/flatten gap, unaffected by this ADR).

**Registers:** `GG-244` (documentation-accuracy gap: the operator's originating task brief stated
the T4 segment tier as "11 segments / eight distinct kelly_fraction regimes"; re-verification
against `execution_bands.py` this session found 13 segments and 6 distinct values — see §2 Tier 3
and the Discrepancies appendix, §7). No other new gap opened — GG-038 already carries the full
factual record this ADR reasons from for tiers 2–4's kill-switch mechanisms.

**Author:** Session `20260905T162339Z-adr-kill-switch-kelly-tiers` (T-520)

**Scope:** `03_DECISIONS/` only. No code change, no `kelly_fraction`/`ExecutionBand`/cell-status
edit, no service source edit, no ledger row. This ADR is not authorized to implement ADR-0054(d),
does not reopen ADR-0060 option (c) or its deferral, and is not marked ACCEPTED.

---

## 0. Central claim

A kill switch's required latency is not a free variable — it is derived from the capital
velocity of the thing it protects: `required_halt_latency ∝ equity_buffer / (kelly_fraction ×
bet_cadence × avg_stake)`. This system decides sizing at **five distinct granularities**, each
with its own `kelly_fraction` (or fixed-stake equivalent) and its own bet cadence. A single
latency bar — NFR-03's 60s, or any other single number — cannot be correct for all five, because
the tiers do not share a capital-velocity profile. Some are currently zero-velocity (kelly=0,
moot today); some are unwired entirely; one is protected by a structural cap rather than a
detection mechanism at all. This ADR states what each tier's requirement actually is, re-derives
it from that tier's own exposure rather than from what today's loop happens to measure, and
folds in two defects (GG-038 TASK 2/3) that sit at the seams between tiers and belong nowhere
else.

---

## 1. Why this is not ADR-0060 again

ADR-0060 answers one question: given NFR-03's 60s figure and T4M_PROJ's measured ~67s real
cadence, what remedy closes that one gap at the band tier? It recommends option (c) (decouple
halt from the evaluation cycle via an out-of-band interrupt) as target architecture, and defers
building it until T4M_PROJ's `kelly_fraction` is next considered for reactivation under ADR-0048
— because current exposure at that tier is zero, so the fix has no live capital benefit yet.

That scoping was correct for the question ADR-0060 was asked. But NFR-03 is written as if there
is one band-level kill-switch latency requirement. There are five sizing tiers, not one, and the
operator's 2026-09-03 directive is explicit: a halt requirement derived from *one* tier's
observed cadence and then applied uniformly is "indistinguishable from weakening a control to
make a red measurement green" when it is silently generalized to tiers it was never measured
against. This ADR is the document that states the hierarchy ADR-0060's option (c) slots into. It
does not relitigate which remedy the band tier gets.

---

## 2. The five tiers, re-verified against source

Every figure below was re-read from source this session, not carried over from the operator's
brief or from memory. Two discrepancies were found in that process and are disclosed in full in
§7 rather than silently corrected.

### Tier 1 — Full book (aggregate solvency / policy deployment)

`src/prediction_market_bot/c4_risk_engine/risk.py`:
- `RESERVE_MANDATE_PCT = 0.40` (L122)
- `MAX_PORTFOLIO_DEPLOYMENT_PCT: float = 1.0 - RESERVE_MANDATE_PCT  # 0.60` (L130)
- CHECK 8, two-tier: **8a** solvency KILL — aggregate open stake projected > 100% equity, implicit
  at 1.0, no separate named constant (L787-871, comment at L138); **8b** policy REJECT — aggregate
  open stake > 60% equity (`approved_size > self._bankroll * (1.0 - RESERVE_MANDATE_PCT)`, L863).
- Governing ADR: ADR-0026.

Confirmed exactly as stated in the operator's brief. No discrepancy at this tier.

**Mechanism available at this tier:** `SystemMonitor.trigger_kill_switch()` / `is_kill_switch_active`
(C7) — measured sub-millisecond (T-489, GG-038 TASK 2: p50 ≈ 0.027ms). This is, by a wide margin,
the fastest kill-switch mechanism anywhere in the system. **It is read by zero MLB pipelines** —
see §4.

### Tier 2 — Band (5 `ExecutionBand` members)

`src/prediction_market_bot/execution_bands.py`, `kelly_fraction=` / `execution_sla_s=` pairs:

| Band | `kelly_fraction` | `execution_sla_s` | Line |
|---|---|---|---|
| T1_MULTI_DAY | 0.0 | 3600 | L141-142 |
| T2_SAME_DAY | 0.0 | 1800 | L152-153 |
| T3_PRE_TIP | 0.0 | 300 | L163-164 |
| T4_IN_PLAY | 0.20 | 5 | L177-178 |
| T5_LATE_GAME | 0.25 | 1 | L188-189 |

Confirmed exactly as stated. One addition the brief did not mention, material to this ADR:
**each band already carries its own `execution_sla_s` field in the schema.** T4_IN_PLAY's is 5s
— which is not a coincidence relative to ADR-0029 Tier A's frozen "≤5s" kill-switch requirement
(2026-06-22, still binding, immutable without a superseding ADR) — and T5_LATE_GAME's is 1s,
tighter still, consistent with its higher `kelly_fraction` and shorter time-to-resolution. The
schema already encodes the principle this ADR argues for (tighter SLA where capital velocity is
higher); it is simply not wired to an enforcement mechanism for the live MLB book (§4).

Note the NFR-03 60s figure is not this tier's `execution_sla_s` at all — see §7 for the resulting
three-numbers-in-one-slot finding.

### Tier 3 — T4 segment (13 segments, not 11; 6 distinct `kelly_fraction` values, not 8)

`src/prediction_market_bot/execution_bands.py`, `T4SubBandSpec` entries:

**NBA (10, all Phase 8+ blocked, zero live exposure):**

| Segment | `kelly_fraction` | Line |
|---|---|---|
| T4_STAGED | 0.07 | L212 |
| T4_EVENT | 0.05 | L223 |
| T4_LINEUP | 0.05 | L234 |
| T4_FLOW | 0.08 | L245 |
| T4_SENTIMENT | 0.05 | L256 |
| T4_PROJ | 0.167 | L267 |
| T4_ARITH | 0.167 | L281 |
| T4_BOUNDARY | 0.167 | L294 |
| T4_CORR | 0.0 | L305 |
| T4_EXIT | 0.0 | L316 |

**MLB (3; T4M_PROJ is the sole live/Phase-6 entry, T4M_ARITH/T4M_FLOW PROVISIONAL/BLOCKED):**

| Segment | `kelly_fraction` | Line |
|---|---|---|
| T4M_PROJ | 0.0 | L332 |
| T4M_ARITH | 0.10 | L343 |
| T4M_FLOW | 0.08 | L355 |

Distinct `kelly_fraction` values across all 13: `{0.0, 0.05, 0.07, 0.08, 0.10, 0.167}` = **6**, not
8. Governing ADR: ADR-0029 (Tier A/B model, §2 Tier 2 above).

### Tier 4 — Cell (78 cells, `(MarketType, ExecutionBand)` registry)

`src/prediction_market_bot/c5_execution/market_type_registry.py`:
- `resolve_kill_switch_state()` — L875
- `halt_cell(market_type, band, reason)` — L885

Confirmed: both defined, **zero external callers** in `src/`. Built and never wired. This is
ADR-0054(d), already noted in `DECISION_LOG.md` (L1237: "ADR-0054(a) (T-509's) or (d) (blocked on
ADR-0060)") as blocked pending ADR-0060's resolution.

### Tier 5 — Individual bet

`src/prediction_market_bot/c5_execution/measurement_stake.py`:
- `T1_MEASUREMENT_STAKE_USD = 1.00` (L54)
- `T1_MEASUREMENT_MAX_CONTRACTS = 10` (L55)
- `T1_MAX_HAIRCUT_PER_CONTRACT_USD = 0.10` (L70)

Confirmed exactly. Additional parallel structure found, not in the operator's brief:
`src/prediction_market_bot/run_t4_mlb_live.py` carries its own T4-specific pair —
`T4_MEASUREMENT_STAKE_USD = 1.00` (L168), `T4_MEASUREMENT_MAX_CONTRACTS = 10` (L181), both feeding
`min(T4_MEASUREMENT_STAKE_USD, T4_MEASUREMENT_MAX_CONTRACTS * entry_price)` (L227) — the same cap
structure as T1's, independently defined for the T4 pipeline.

---

## 3. Per-tier derivation approach

Following APR-0024's discipline (variance/exposure-derived, never fit-to-current-behavior) and
ADR-0060 §3's precedent: for each tier, `required_halt_latency` is derived from that tier's own
`equity_buffer / (kelly_fraction × bet_cadence × avg_stake)` — never from what today's loop
happens to measure. Applying this per tier:

- **Tier 1 (full book):** the breach here is systemic — every band/cell firing simultaneously
  against the aggregate 60%/100% lines. The relevant cadence is the *combined* max order rate
  across the whole system, not any one band's cadence. This is exactly why the fastest mechanism
  in the system (`SystemMonitor`, sub-ms) sits at this tier — a systemic breach must be caught
  fastest because it is uncapped by any single band's own limits. The mechanism's latency budget
  is already satisfied by three orders of magnitude; the defect at this tier is not speed, it is
  that the mechanism is inert for MLB (§4).

- **Tier 2 (band):** required latency scales inversely with `kelly_fraction × cadence`. For
  T1/T2/T3 (`kelly_fraction=0.0`), the derived requirement is **moot** — zero stake per bet means
  zero capital-derived latency requirement regardless of how fast a halt lands. This is an honest
  conclusion, not a gap: these bands have no capital exposure to protect today. It becomes live
  again only when ADR-0048's reactivation gate fires for one of them, at which point the
  derivation must be redone against that band's *then-current* cadence and stake — never assumed
  to still hold from this document. T4_IN_PLAY/T5_LATE_GAME carry nonzero `kelly_fraction` but are
  NBA-scoped and Phase-8+-blocked — same moot-today, must-rederive-at-activation conclusion.

- **Tier 3 (T4 segment):** identical logic, segment by segment. T4M_PROJ, the one live segment, is
  at `kelly_fraction=0.0` — moot on capital-exposure grounds alone, today. But this is precisely
  the point the operator's directive is making, generalized: ADR-0060 already sequences its option
  (c) build to "whenever T4M_PROJ's `kelly_fraction` is next considered for reactivation" rather
  than to a calendar date, and this ADR states the same discipline for all 13 segments — **no
  segment's halt-latency requirement may be treated as satisfied by a stale derivation once its
  `kelly_fraction` leaves 0.0.** Reactivation review under ADR-0048 must include re-deriving this
  segment's own halt requirement as an explicit line item, not an assumed carry-forward.

- **Tier 4 (cell):** no live mechanism exists (§2 Tier 4), so no latency can be derived — the
  finding at this tier is that a requirement cannot even be formulated until `resolve_kill_switch_
  state()`/`halt_cell()` are wired to a caller (ADR-0054(d), out of scope here). When that wiring
  is built, its own derivation must follow the same discipline: keyed off the cell's effective
  `kelly_fraction` (currently inherited from its band per the registry's `(MarketType,
  ExecutionBand)` keying — whether a cell may override its band's inherited value is an
  ADR-0053/0057 question this ADR does not decide).

- **Tier 5 (individual bet):** structurally different in kind from the other four. The position-
  size caps (`min(stake_usd, max_contracts * entry_price)`) already bound the maximum loss from a
  *single* bet to a known ceiling, independent of detection speed — $1.00 or 10 contracts ×
  entry price (whichever binds), for both T1 and T4. This tier's safety is achieved by size
  bounding, not by halt latency, and its protection does not substitute for the other four tiers'
  — a system that only bounds per-bet loss can still be ruined by an undetected run of many such
  bets, which is exactly what tiers 1-4 exist to catch.

---

## 4. GG-038 TASK 2/3, absorbed

ADR-0060 §6 explicitly names both of the following as things none of its three band-tier options
solve. They sit at the seams between tiers 1 and 2/3, not inside any one tier, which is why they
belong here rather than in a second document that would contradict this one.

**TASK 2 — Tier 1's fastest mechanism is inert for the live book.** `is_kill_switch_active` /
`SystemMonitor.trigger_kill_switch()` is read by zero MLB pipelines (confirmed: the only reader in
`src/` is the NBA `t4_live_runner.py`, itself Phase-8+-blocked). Tier 1's sub-millisecond
mechanism — architecturally the correct answer for a systemic breach — currently protects
nothing on the pool that is actually live.

**TASK 3(c) — the tier-1-to-tier-2/3 handoff is asymmetric.** C4's `evaluate_forecast()` computes
a tier-1 aggregate judgment and returns `approval_status`. Two live pipelines receive it and
handle it differently:

- `run_mlb_paper_trade.py` (T1, L980-991): branches explicitly —
  `if status == "KILL_SWITCH": logger.critical(...); sys.exit(1)` — self-halts the process.
- `run_t4_mlb_live.py` (T4, L1364): `if approval.get("approval_status") != "APPROVED": continue` —
  treats `KILL_SWITCH` identically to an ordinary per-bet `REJECTED`. Skip this ticker, keep
  looping.

The live band-level pipeline does not respect the aggregate solvency/policy judgment computed at
tier 1 at all. This is the literal missing plumbing between where the kill decision is made
(tier 1) and where capital is actually committed on the live book (tier 2/3, T4M_PROJ) — not a
latency problem, a wiring problem, and a different defect in kind from either TASK 2 or ADR-0060's
band-cadence gap.

**A fourth mechanism, for completeness of the map.** Counting what GG-038 itself already
enumerates plus tier 4's stub, four distinct kill-switch-adjacent mechanisms exist system-wide:

| # | Mechanism | Intended tier | Status |
|---|---|---|---|
| 1 | `run_t4_mlb_live.py` filesystem flag (`KILL_SWITCH_PATH`/`kill_switch_armed()`, L242-296, checked at L1539/1719/1815) | 2/3 (band/segment) | Wired; latency gap is ADR-0060's subject (not reopened here) — checked top-of-loop/per-game only, never mid-cycle or during the 45s post-cycle sleep |
| 2 | `SystemMonitor.trigger_kill_switch()` / `is_kill_switch_active` | 1 (full book) | Sub-ms, but inert for MLB (TASK 2, above) |
| 3 | `RiskEngine.evaluate_forecast()`'s `approval_status=="KILL_SWITCH"` | 1→2/3 handoff | Generated at tier 1; consumed asymmetrically (TASK 3(c), above) |
| 4 | `resolve_kill_switch_state()`/`halt_cell()` | 4 (cell) | Never wired (ADR-0054(d)) |

No mechanism exists for tier 5 — by design, per §3's structural-cap argument, not as a gap.

---

## 5. Relationship to ADR-0060 — explicitly not reopened

ADR-0060's option (c) (decouple halt from the evaluation cycle) remains the accepted target
architecture for the band tier (tier 2/3), deferred until T4M_PROJ's `kelly_fraction` is next
considered for reactivation under ADR-0048. This ADR does not evaluate options (a)/(b)/(c) again,
does not change the deferral, and does not revise NFR-03's 60s text. This ADR's contribution is
the layer above that decision: it states that tier 2/3 is one of five tiers, that each tier's
`execution_sla_s` (where one exists) must be independently derived rather than inherited from
NFR-03's single figure, and it folds in TASK 2/3 (§4), which ADR-0060 §6 named but explicitly left
unsolved because they are not band-cadence problems.

**Authority note on ADR-0060's own status.** ADR-0060's acceptance was operator-granted
2026-09-03 (commit `03ca889`, T-512: option (c) target architecture accepted, implementation
deferred; same-day `DECISION_LOG.md`/`APPROVALS_REGISTER.md` entries `bee176c`/`edecc35`). That
branch has not merged to `origin/main`, where ADR-0060's Status line still reads PROPOSED as of
this session. Re-recording attempts (`T-518`, commits `e6611a5`/`0fb0938`/`854c520`) remain
unmerged per `TODO_NEXT.md`. This ADR draws on ADR-0060's content and recommendation regardless of
where its formal acceptance currently sits — drafting does not require citing authority to change
anything — but this document does not itself claim ADR-0060 is ACCEPTED-of-record on
`origin/main`, and does not treat that stranding as resolved. See §7 for a related, narrower
disclosure about GG-240's own registered text.

---

## 6. What this ADR does not solve, stated plainly

- Does not implement ADR-0054(d) — no caller is wired to `resolve_kill_switch_state()`/
  `halt_cell()`. It states that when that wiring is built, its latency requirement must follow
  this ADR's derivation discipline; it does not build the wiring.
- Does not fix TASK 2 or TASK 3(c) themselves. It states where each defect sits in the hierarchy
  and which tiers it spans; the code changes (routing `is_kill_switch_active` into MLB pipelines;
  making `run_t4_mlb_live.py` branch on `KILL_SWITCH` the way T1 does) are separate implementation
  work, out of this session's scope fence.
- Does not revise NFR-03's 60s text — that is ADR-0060 option (b), not reopened.
- Does not decide among ADR-0060's options (a)/(b)/(c) — already decided, (c), not reopened here.
- Does not resolve GG-209 (T1 force-close/flatten path) — a separate, adjacent gap, unaffected by
  this document, exactly as ADR-0060 §6 already noted.
- Does not resolve GG-240's stranding of ADR-0060/0061/0062's sign-offs — that is a separate
  merge/authority action, not a drafting one.
- Does not change any `kelly_fraction`, cell status, `ExecutionBand` member, service source, or
  ledger row, and is not marked ACCEPTED.

---

## 7. Discrepancies found during re-verification (disclosed, not silently corrected)

Per the operator's explicit instruction to re-verify every figure against source rather than
trust the brief, two discrepancies surfaced. Neither was fixed in-session (Hard Rule 11 — register
and stop on discovery); both are stated here so this ADR is not read as quietly smoothing over
what the brief said.

**1. T4-segment count and Kelly-regime count (registered as GG-244).** The operator's brief stated
"11 segments" and "EIGHT distinct regimes." Source (`execution_bands.py`, §2 Tier 3 above) shows
**13** `T4SubBandSpec` entries (10 NBA + 3 MLB) and **6** distinct `kelly_fraction` values
(`{0.0, 0.05, 0.07, 0.08, 0.10, 0.167}`). This does not change this ADR's argument — the argument
is that segment-level derivation must be independent per segment regardless of how many segments
or distinct values there are — but the count itself is corrected here against source, not
assumed.

**2. GG-240's registered scope names only ADR-0062, not ADR-0060.** The operator's directive
states ADR-0060's acceptance is "stranded on an unlanded branch (GG-240)." Cross-referencing git
history confirms the *substantive* claim: ADR-0060 was accepted via commit `03ca889` (T-512,
2026-09-03) on a branch that has never merged to `origin/main`. However, `GOVERNANCE_GAP_LOG.md`'s
GG-240 entry, as currently written, titles and bodies itself around **ADR-0062's** stranding
specifically (T-512's PR #126, three refused merge routes) and does not name ADR-0060 anywhere in
its text. The later `T-518` commits that re-recorded ADR-0060/0061/0062's sign-offs together, on a
branch citing "GG-240 stranding" as the reason, applied the same pattern to all three ADRs — but
that application is visible only in the commit trail, not in GG-240's own registered scope. This
is a real but narrow documentation-precision gap: the substantive stranding-pattern claim about
ADR-0060 is true; the specific gap ID cited for it does not, as written, cover it. Not fixed here
— widening GG-240's scope text (or opening a distinct gap for ADR-0060/0061 specifically) is a
gap-log edit outside this ADR's scope fence and is left for the operator/next session to decide
which is correct.

---

## 8. Summary table — the hierarchy this ADR establishes

| Tier | Governing constant(s) | Live `kelly_fraction`(s) | Kill mechanism | Latency status |
|---|---|---|---|---|
| 1. Full book | `MAX_PORTFOLIO_DEPLOYMENT_PCT=0.60`, ADR-0026 | N/A (aggregate) | `SystemMonitor` (sub-ms) | Fast enough; inert for MLB (TASK 2) |
| 2. Band (5) | `execution_bands.py` `kelly_fraction`/`execution_sla_s` | 0.0 (T1-T3, live pools); 0.20/0.25 (T4/T5, NBA-blocked) | Filesystem flag (mechanism 1) + risk-engine field (mechanism 3) | Moot today (kelly=0); ADR-0060 governs T4_IN_PLAY's cadence gap when reactivated |
| 3. T4 segment (13) | `T4SubBandSpec.kelly_fraction`, 6 distinct values | 0.0 (T4M_PROJ, sole live) | Same as tier 2, per-segment | Moot today; re-derive at each segment's own reactivation |
| 4. Cell (78) | Registry inheritance from band | N/A | `resolve_kill_switch_state()`/`halt_cell()` — unwired | Undefined until ADR-0054(d) wiring exists |
| 5. Individual bet | `T1_MEASUREMENT_STAKE_USD`/`T4_MEASUREMENT_STAKE_USD`, `MAX_CONTRACTS`, `MAX_HAIRCUT` | N/A | Position-size cap, not a switch | Not latency-governed by design |

---

**This document is PROPOSED. It authorizes no code change, no ADR-0054(d) implementation, and no
supersession of ADR-0060, ADR-0029, or ADR-0048. Operator review and acceptance decision required
before any tier's derivation becomes binding.**
